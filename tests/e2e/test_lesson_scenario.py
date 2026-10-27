"""The lesson's scenario on recorded embeddings (nomic-embed-text) and recorded answers (qwen2.5:1.5b)."""

import json
from pathlib import Path

import pytest

from cited_answers.application.answer import AnswerService
from cited_answers.application.evaluate import evaluate_answers, evaluate_retrieval
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.application.threshold import choose_threshold
from cited_answers.domain.answering import REFUSAL_MESSAGE, Reason
from cited_answers.domain.chunking import MAX_CHUNK_TOKENS
from cited_answers.domain.evaluation import QuestionType, Stage, agreement, validate_questions
from cited_answers.domain.pages import PageStatus
from cited_answers.domain.retrieval import Bm25Index, whitespace_tokenize
from cited_answers.infrastructure.embeddings import EmbeddingStore, RecordedEmbedder
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, FileQuestionSource, read_threshold
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingStore
from tests.conftest import ScriptedModel

pytestmark = pytest.mark.e2e

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def world():
    embedder = RecordedEmbedder(EmbeddingStore(REPO / "tests" / "fixtures" / "embeddings"), "nomic-embed-text")
    store = InMemoryChunkStore()
    report = ingest(FilePageSource(REPO / "data" / "pages"), embedder, store)
    return embedder, store, report, HybridRetriever(store, embedder)


@pytest.fixture(scope="module")
def questions():
    source = FileQuestionSource(REPO / "data" / "questions")
    dev, test = source.load("dev"), source.load("test")
    validate_questions(dev, 17, 5, 8)
    validate_questions(test, 70, 20, 30)
    return dev, test


def service(retriever, version, model=None):
    prompts = FilePromptStore(REPO / "prompts")
    chat = model or RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    return AnswerService(
        retriever, chat, prompts.load("answer", version), read_threshold(REPO / "evals" / "threshold.json") or 0.5
    ), chat


def judge():
    chat = RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    return Judge(chat, FilePromptStore(REPO / "prompts").load("judge", "v1"))


def test_step_1_retired_pages_are_left_out_logged_by_id_and_every_chunk_has_its_four_fields(world):
    _, store, report, retriever = world
    assert report.skipped_retired == ("p-return-fee-old", "p-return-window-old", "p-ship-costs-old")
    chunks = store.chunks()
    assert report.pages_indexed == 57
    assert len(chunks) == 68
    assert all(c.status is PageStatus.CURRENT for c in chunks)
    assert all(c.page_id and c.heading_path and c.updated and c.status for c in chunks)
    assert all(c.id.startswith(c.page_id + ":") for c in chunks)
    assert max(c.tokens for c in chunks) <= MAX_CHUNK_TOKENS
    for mode in Mode:
        found = retriever.retrieve("How many days do I have to return an item?", mode)
        assert not {"p-return-window-old", "p-ship-costs-old", "p-return-fee-old"} & set(found.page_ids)


def test_steps_2_and_3_hit_rate_at_five_per_type_for_vectors_keywords_and_both_with_intervals(world, questions):
    _, test = questions[0], questions[1]
    report = evaluate_retrieval(world[3], test)
    rates = {key: (rate.successes, rate.trials) for key, rate in report.rates.items()}
    assert rates[("answerable", "vector")] == (69, 70)
    assert rates[("answerable", "keyword")] == (66, 70)
    assert rates[("answerable", "fused")] == (68, 70)
    for mode in ("vector", "keyword", "fused"):
        assert rates[("exact", mode)] == (20, 20)
    low, high = report.rates[("exact", "fused")].interval
    assert 0.8 < low < high <= 1.0


def test_the_keyword_index_finds_a_bare_error_code_only_because_the_tokenizer_splits_on_hyphens(world):
    _, store, _, retriever = world
    assert retriever.retrieve("What's E2091 about?", Mode.KEYWORD).page_ids[0] == "p-error-e2091"
    naive = Bm25Index(store.chunks(), tokenizer=whitespace_tokenize)
    assert naive.search("What's E2091 about?", 5) == []


def test_step_4_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal(world):
    svc, _ = service(world[3], "v2", ScriptedModel(lambda r: "Thirty days [p-gift-cards:0]."))
    answer = svc.ask("How many days do I have to return an item?", "planted")
    assert answer.refused
    assert answer.reason is Reason.CITATION_NOT_RETRIEVED
    assert answer.text == REFUSAL_MESSAGE


@pytest.fixture(scope="module")
def reports(world, questions):
    """The four recorded answer runs (dev and test, prompts v1 and v2), computed once."""
    dev, test = questions
    out = {}
    for split, items in (("dev", dev), ("test", test)):
        for version in ("v1", "v2"):
            out[(split, version)] = evaluate_answers(service(world[3], version)[0], judge(), items)
    return out


def test_steps_5_to_7_the_recorded_runs_reproduce_the_committed_reports(reports):
    for (split, version), report in reports.items():
        committed = (REPO / "evals" / "reports" / f"{split}-answer-{version}.txt").read_text()
        assert f"{'retrieval hit rate (answerable+exact)':<34} {report.retrieval_hit}" in committed
        assert f"{'answer correct (judge)':<34} {report.answer_correct}" in committed
        assert f"{'unanswerable refused':<34} {report.unanswerable_refused}" in committed
        assert f"retrieval misses:  {report.misses_by_stage[Stage.RETRIEVAL]}" in committed
        assert f"generation misses: {report.misses_by_stage[Stage.GENERATION]}" in committed


def test_every_answer_in_the_final_run_cites_a_retrieved_chunk_or_is_the_refusal_message(reports):
    for result in reports[("test", "v2")].results:
        answer = result.answer
        if answer.refused:
            assert answer.text == REFUSAL_MESSAGE
        else:
            retrieved = {c.id for c in answer.retrieval.chunks}
            assert answer.citations
            assert set(answer.citations) <= retrieved


def test_the_two_stage_table_before_and_after_the_fix(reports):
    before = reports[("test", "v1")].misses_by_stage
    after = reports[("test", "v2")].misses_by_stage
    stage = {s.value: n for s, n in before.items()}
    assert stage == {"retrieval miss": 2, "generation miss": 88}
    assert {s.value: n for s, n in after.items()} == {"retrieval miss": 1, "generation miss": 32}


def test_the_threshold_comes_from_the_development_questions_only(world, questions):
    svc, _ = service(world[3], "v2")
    choice = choose_threshold(svc, questions[0])
    assert choice.threshold == read_threshold(REPO / "evals" / "threshold.json")
    assert choice.false_refusal_rate <= 0.10
    written = json.loads((REPO / "evals" / "threshold.json").read_text())
    assert written["tuned_on"] == "dev"


def test_unanswerable_questions_below_the_threshold_never_reach_the_model(world, questions):
    spy = ScriptedModel(lambda r: "should not be called")
    svc, _ = service(world[3], "v2", spy)
    for question in (q for q in questions[1] if q.type is QuestionType.UNANSWERABLE):
        answer = svc.ask(question.question, question.id)
        if answer.reason is Reason.BELOW_THRESHOLD:
            assert answer.input_tokens == 0
    assert all("should not be called" not in r.messages[0].content for r in spy.requests)


def test_the_judge_agrees_with_thirty_hand_grades_on_at_least_nine_in_ten(reports):
    grades = {}
    for line in (REPO / "evals" / "hand_grades.jsonl").read_text().splitlines():
        row = json.loads(line)
        grades[row["question_id"]] = row["correct"]
    assert len(grades) == 30
    results = [*reports[("dev", "v2")].results, *reports[("test", "v2")].results]
    shared = [r for r in results if r.question.id in grades and r.correct is not None]
    matched, total = agreement([bool(r.correct) for r in shared], [grades[r.question.id] for r in shared])
    assert total == 30
    assert matched / total >= 0.9
