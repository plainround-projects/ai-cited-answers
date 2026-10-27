"""The `cited` command: ingest, ask, serve, evaluate retrieval and answers, tune the refusal threshold."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from cited_answers.application.answer import AnswerService
from cited_answers.application.evaluate import AnswerReport, evaluate_answers, evaluate_retrieval
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.application.threshold import choose_threshold
from cited_answers.domain.errors import DomainError
from cited_answers.domain.evaluation import InvalidQuestions, Question, agreement, validate_questions
from cited_answers.domain.pages import InvalidPage
from cited_answers.domain.prompts import PromptNotFound
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.env import ConfigurationError
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, FileQuestionSource, read_threshold
from cited_answers.infrastructure.logging import configure_logging
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.shutdown import ShutdownSignal
from cited_answers.infrastructure.wiring import build_embedder, build_store
from cited_answers.interfaces.render import render_answers, render_ingest, render_retrieval

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_INTERRUPTED = 0, 1, 2, 4
SPLIT_MIX = {"dev": (17, 5, 8), "test": (70, 20, 30)}
DEFAULT_THRESHOLD = 0.5
_log = logging.getLogger("cited")


def build_parser() -> argparse.ArgumentParser:
    """The `cited` argument parser."""
    parser = argparse.ArgumentParser(prog="cited", description="Cited answers over a help center.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="chunk the current pages, embed them and fill the index (needed once for pgvector)")
    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    sub.add_parser("serve", help="run the HTTP service (POST /ask, GET /health)")
    retrieval = sub.add_parser("retrieval", help="hit rate at 5 for vectors, keywords and both fused")
    retrieval.add_argument("--split", choices=sorted(SPLIT_MIX), required=True)
    sub.add_parser("tune-threshold", help="choose the refusal threshold on the development questions only")
    answers = sub.add_parser("evaluate", help="grade retrieval and answers apart on a question set")
    answers.add_argument("--split", choices=sorted(SPLIT_MIX), required=True)
    answers.add_argument("--prompt", help="answer prompt version (default: ANSWER_PROMPT_VERSION)")
    answers.add_argument(
        "--hand-grades", type=Path, help="JSON Lines of {question_id, correct} to measure the judge against"
    )
    answers.add_argument("--dump", type=Path, help="write every question, answer and verdict to this JSON Lines file")
    answers.add_argument("--write-report", action="store_true", help="write evals/reports/<split>-answer-<prompt>.txt")
    return parser


def _retriever(settings: AppSettings) -> tuple[HybridRetriever, str]:
    embedder = build_embedder(settings)
    store = build_store(settings)
    report = ingest(FilePageSource(settings.pages_dir), embedder, store) if settings.index_backend == "memory" else None
    retriever = HybridRetriever(store, embedder)
    return retriever, (
        render_ingest(report) if report else f"using the existing index ({retriever.chunk_count} chunks)"
    )


def _threshold(settings: AppSettings) -> float:
    if settings.refusal_threshold is not None:
        return settings.refusal_threshold
    return read_threshold(settings.threshold_path) or DEFAULT_THRESHOLD


def _service(settings: AppSettings, retriever: HybridRetriever, version: str | None = None) -> AnswerService:
    prompts = FilePromptStore(settings.prompts_dir)
    model = build_chat_model(ModelSettings.from_env(), SystemClock())
    prompt = prompts.load("answer", version or settings.answer_prompt)
    return AnswerService(retriever, model, prompt, _threshold(settings))


def _questions(settings: AppSettings, split: str) -> list[Question]:
    questions = FileQuestionSource(settings.questions_dir).load(split)
    answerable, exact, unanswerable = SPLIT_MIX[split]
    validate_questions(questions, answerable, exact, unanswerable)
    return questions


def _hand_grades(path: Path) -> dict[str, bool]:
    grades: dict[str, bool] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            grades[row["question_id"]] = bool(row["correct"])
    return grades


def _dump(path: Path, report: AnswerReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for r in report.results:
            handle.write(
                json.dumps(
                    {
                        "question_id": r.question.id,
                        "type": r.question.type.value,
                        "question": r.question.question,
                        "fact": r.question.fact,
                        "status": r.answer.status.value,
                        "reason": r.answer.reason.value,
                        "answer": r.answer.text,
                        "raw": r.answer.raw_text,
                        "gold_page": r.question.gold_page,
                        "retrieved": [c.id for c in r.answer.retrieval.chunks],
                        "hit": r.hit,
                        "judge_correct": r.correct,
                        "best_similarity": round(r.answer.retrieval.best_similarity, 4),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def _evaluate(args: argparse.Namespace, settings: AppSettings, shutdown: ShutdownSignal) -> int:
    retriever, note = _retriever(settings)
    print(note)
    service = _service(settings, retriever, args.prompt)
    prompts = FilePromptStore(settings.prompts_dir)
    judge = Judge(
        build_chat_model(ModelSettings.from_env({**_judge_env()}), SystemClock()),
        prompts.load("judge", settings.judge_prompt),
    )
    questions = _questions(settings, args.split)
    report = evaluate_answers(service, judge, questions, stop_requested=lambda: shutdown.requested)
    verdicts = None
    if args.hand_grades:
        grades = _hand_grades(args.hand_grades)
        shared = [r for r in report.results if r.question.id in grades and r.correct is not None]
        verdicts = agreement([bool(r.correct) for r in shared], [grades[r.question.id] for r in shared])
    label = f"{args.split} set, answer prompt {args.prompt or settings.answer_prompt}"
    text = render_answers(label, report, service.threshold, verdicts)
    print(text)
    if args.dump:
        _dump(args.dump, report)
    if args.write_report:
        settings.reports_dir.mkdir(parents=True, exist_ok=True)
        name = f"{args.split}-answer-{args.prompt or settings.answer_prompt}.txt"
        (settings.reports_dir / name).write_text(text + "\n", encoding="utf-8")
    return EXIT_INTERRUPTED if shutdown.requested else EXIT_OK


def _judge_env() -> dict[str, str]:
    """The environment for the judge's model: `JUDGE_MODEL_NAME` overrides `MODEL_NAME`."""
    env = dict(os.environ)
    env["MODEL_NAME"] = os.environ.get("JUDGE_MODEL_NAME", os.environ.get("MODEL_NAME", "qwen2.5:1.5b"))
    return env


def _tune(settings: AppSettings) -> int:
    retriever, note = _retriever(settings)
    print(note)
    choice = choose_threshold(_service(settings, retriever), _questions(settings, "dev"))
    settings.threshold_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "threshold": choice.threshold,
        "tuned_on": "dev",
        "false_refusal_rate_on_dev": round(choice.false_refusal_rate, 4),
        "unanswerable_refused_rate_on_dev": round(choice.unanswerable_refused_rate, 4),
    }
    settings.threshold_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        f"threshold {choice.threshold}: wrongly refuses {choice.false_refusal_rate:.0%} of answerable dev questions, "
        f"refuses {choice.unanswerable_refused_rate:.0%} of the unanswerable ones"
    )
    return EXIT_OK


def _known_id(settings: AppSettings, question: str) -> str:
    """The id of a dev or test question with this exact text (so its recorded answer is found), else `adhoc`."""
    source = FileQuestionSource(settings.questions_dir)
    for split in SPLIT_MIX:
        for known in source.load(split):
            if known.question == question:
                return known.id
    return "adhoc"


def _ask(settings: AppSettings, question: str) -> int:
    retriever, _ = _retriever(settings)
    answer = _service(settings, retriever).ask(question, _known_id(settings, question))
    cited = ", ".join(answer.citations) or "nothing"
    print(answer.text)
    score = f"best similarity {answer.retrieval.best_similarity:.3f}"
    print(f"[{answer.status.value}: {answer.reason.value}; {score}; cited {cited}]")
    return EXIT_OK


def _run(args: argparse.Namespace, settings: AppSettings, shutdown: ShutdownSignal) -> int:
    if args.command == "serve":
        from cited_answers.interfaces.server import serve

        return serve(settings)
    if args.command == "ingest":
        embedder, store = build_embedder(settings), build_store(settings)
        print(render_ingest(ingest(FilePageSource(settings.pages_dir), embedder, store)))
        return EXIT_OK
    if args.command == "retrieval":
        retriever, note = _retriever(settings)
        print(note)
        print(render_retrieval(evaluate_retrieval(retriever, _questions(settings, args.split))))
        return EXIT_OK
    if args.command == "tune-threshold":
        return _tune(settings)
    if args.command == "ask":
        return _ask(settings, args.question)
    return _evaluate(args, settings, shutdown)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted)."""
    args = build_parser().parse_args(argv)
    try:
        settings = AppSettings.from_env()
        configure_logging(settings.log_level)
        shutdown = ShutdownSignal()
        shutdown.install()
        return _run(args, settings, shutdown)
    except (ConfigurationError, InvalidQuestions, InvalidPage, PromptNotFound) as error:
        print(f"cited: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except DomainError as error:
        print(f"cited: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
