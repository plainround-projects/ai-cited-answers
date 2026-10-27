"""Evaluate retrieval and answers on a question set, and grade the two halves apart."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from cited_answers.application.answer import Answer, AnswerService
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode
from cited_answers.domain.evaluation import Question, QuestionType, Rate, Stage, classify_miss, hit_at_k

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetrievalReport:
    """Hit rate at five per question type and retrieval mode."""

    rates: dict[tuple[str, str], Rate]
    misses: dict[tuple[str, str], list[str]]


def evaluate_retrieval(retriever: HybridRetriever, questions: Sequence[Question]) -> RetrievalReport:
    """For answerable and exact questions, count a hit when a chunk of the gold page is in the top five."""
    hits: dict[tuple[str, str], list[bool]] = {}
    misses: dict[tuple[str, str], list[str]] = {}
    for question in questions:
        if not question.has_gold:
            continue
        for mode in Mode:
            found = hit_at_k(retriever.retrieve(question.question, mode).page_ids, question.gold_page)
            key = (question.type.value, mode.value)
            hits.setdefault(key, []).append(found)
            if not found:
                misses.setdefault(key, []).append(question.id)
    rates = {key: Rate(sum(values), len(values)) for key, values in hits.items()}
    return RetrievalReport(rates, misses)


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question through the whole pipeline."""

    question: Question
    answer: Answer
    hit: bool
    correct: bool | None


@dataclass(frozen=True, slots=True)
class AnswerReport:
    """Retrieval and answer quality as separate numbers, the refusal record and the misses by stage."""

    results: tuple[QuestionResult, ...]
    retrieval_hit: Rate
    answer_correct: Rate
    unanswerable_refused: Rate
    false_refusals: Rate
    misses_by_stage: dict[Stage, int]
    input_tokens: int
    output_tokens: int

    @property
    def unanswered_slips(self) -> list[str]:
        """Ids of unanswerable questions that got an answer instead of the refusal."""
        return [
            r.question.id for r in self.results if r.question.type is QuestionType.UNANSWERABLE and not r.answer.refused
        ]


def evaluate_answers(
    service: AnswerService,
    judge: Judge,
    questions: Sequence[Question],
    stop_requested: Callable[[], bool] = lambda: False,
) -> AnswerReport:
    """Run every question through retrieval, the model and the judge, then grade retrieval and answers apart."""
    results: list[QuestionResult] = []
    for question in questions:
        if stop_requested():
            break
        answer = service.ask(question.question, question.id)
        hit = hit_at_k(answer.retrieval.page_ids, question.gold_page)
        correct = None
        if question.has_gold:
            correct = (not answer.refused) and judge.grade(question, answer.text)
        results.append(QuestionResult(question, answer, hit, correct))
        _log.info("question answered", extra={"fields": {"question_id": question.id, "status": answer.status.value}})
    return summarize(results)


def summarize(results: Sequence[QuestionResult]) -> AnswerReport:
    """Fold per-question results into the report's numbers."""
    gradable = [r for r in results if r.question.has_gold]
    unanswerable = [r for r in results if not r.question.has_gold]
    stages: dict[Stage, int] = {Stage.RETRIEVAL: 0, Stage.GENERATION: 0}
    for r in gradable:
        stage = classify_miss(r.hit, bool(r.correct))
        if stage is not None:
            stages[stage] += 1
    return AnswerReport(
        results=tuple(results),
        retrieval_hit=Rate(sum(r.hit for r in gradable), len(gradable)),
        answer_correct=Rate(sum(bool(r.correct) for r in gradable), len(gradable)),
        unanswerable_refused=Rate(sum(r.answer.refused for r in unanswerable), len(unanswerable)),
        false_refusals=Rate(sum(r.answer.refused for r in gradable), len(gradable)),
        misses_by_stage=stages,
        input_tokens=sum(r.answer.input_tokens for r in results),
        output_tokens=sum(r.answer.output_tokens for r in results),
    )
