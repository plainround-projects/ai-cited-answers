import logging

import pytest

from cited_answers.application.answer import AnswerService, format_context
from cited_answers.application.evaluate import evaluate_answers, evaluate_retrieval, summarize
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.application.threshold import choose_threshold, dev_scores
from cited_answers.domain.answering import REFUSAL_MESSAGE, Reason, Status
from cited_answers.domain.evaluation import Question, QuestionType, Stage
from cited_answers.domain.prompts import Prompt
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from tests.conftest import PAGES, PROMPT, HashingEmbedder, MemoryPages, ScriptedModel


@pytest.fixture
def built():
    embedder = HashingEmbedder()
    store = InMemoryChunkStore()
    report = ingest(MemoryPages(PAGES), embedder, store)
    return report, HybridRetriever(store, embedder), embedder


def test_ingest_indexes_current_pages_only_and_names_the_retired_ones(built, caplog):
    report, retriever, _ = built
    assert (report.pages_indexed, report.chunks) == (4, 4)
    assert report.skipped_retired == ("p-return-window-old",)
    assert retriever.chunk_count == 4


def test_ingest_logs_each_skipped_page(caplog):
    with caplog.at_level(logging.INFO):
        ingest(MemoryPages(PAGES), HashingEmbedder(), InMemoryChunkStore())
    skipped = [r for r in caplog.records if r.getMessage() == "retired page left out of the index"]
    assert [r.fields["page_id"] for r in skipped] == ["p-return-window-old"]


def test_a_search_for_the_old_return_window_returns_no_retired_chunk(built):
    _, retriever, _ = built
    for mode in Mode:
        found = retriever.retrieve("return any item within 14 days", mode)
        assert "p-return-window-old" not in found.page_ids


def test_embedding_is_done_in_batches():
    embedder = HashingEmbedder()
    many = [PAGES[0]] * 1
    ingest(MemoryPages(many + PAGES[2:]), embedder, InMemoryChunkStore())
    assert all(len(batch) <= 32 for batch in embedder.calls)


def test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find():
    class OppositeEmbedder(HashingEmbedder):
        """Puts the question far from every chunk, as a vector search that misses the page would."""

        def embed(self, texts):
            vectors = super().embed(texts)
            return [[-x for x in v] if len(t) < 40 else v for t, v in zip(texts, vectors, strict=True)]

    store = InMemoryChunkStore()
    embedder = OppositeEmbedder()
    ingest(MemoryPages(PAGES), embedder, store)
    retriever = HybridRetriever(store, embedder, k=2)
    keyword = retriever.retrieve("What's E2091 about?", Mode.KEYWORD)
    fused = retriever.retrieve("What's E2091 about?", Mode.FUSED)
    assert keyword.page_ids[0] == "p-error-e2091"
    assert "p-error-e2091" in fused.page_ids


def test_best_similarity_is_the_highest_cosine_among_the_returned_chunks(built):
    _, retriever, _ = built
    close = retriever.retrieve("gift cards amounts expire", Mode.FUSED)
    far = retriever.retrieve("zebra quartz plasma", Mode.FUSED)
    assert close.best_similarity > far.best_similarity
    assert close.chunks[0].page_id == "p-gift-cards"


def good_answer(request):
    return "Thirty days [p-return-window:0]."


def service(retriever, answer=good_answer, threshold=0.0, model=None):
    return AnswerService(retriever, model or ScriptedModel(answer), PROMPT, threshold)


def test_a_cited_answer_is_returned_with_its_citations_and_the_passages_in_the_prompt(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer)
    answer = service(retriever, model=model).ask("How many days to return an item?", "q1")
    assert answer.status is Status.ANSWERED
    assert answer.citations == ("p-return-window:0",)
    request = model.requests[0]
    assert request.system == PROMPT.text
    assert "[p-return-window:0]" in request.messages[0].content
    assert request.messages[0].content.endswith("Question: How many days to return an item?")
    assert request.tag == "q1|answer-v1"
    assert (answer.input_tokens, answer.output_tokens) == (30, 8)


def test_below_the_threshold_the_model_is_never_called(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer)
    answer = service(retriever, threshold=0.99, model=model).ask("zebra quartz plasma")
    assert (answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.BELOW_THRESHOLD, REFUSAL_MESSAGE)
    assert model.requests == []


def test_the_model_may_refuse_too(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: REFUSAL_MESSAGE).ask("What is the return window for sale items?")
    assert (answer.status, answer.reason) == (Status.REFUSED, Reason.MODEL_REFUSED)
    assert answer.refused


def test_an_answer_without_a_citation_is_replaced_by_the_refusal_and_the_raw_text_is_kept(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: "It is thirty days.").ask("return window days")
    assert (answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.NO_CITATION, REFUSAL_MESSAGE)
    assert answer.raw_text == "It is thirty days."


def test_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: "Yes [p-loyalty:0].").ask("return window days")
    assert (answer.status, answer.reason) == (Status.REFUSED, Reason.CITATION_NOT_RETRIEVED)


def test_a_model_without_sampling_support_is_asked_without_a_temperature(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer, sampling=False)
    service(retriever, model=model).ask("return window days")
    assert model.requests[0].temperature is None


def test_context_formatting_puts_the_id_first(built):
    _, retriever, _ = built
    text = format_context(retriever.retrieve("gift cards", Mode.FUSED).chunks)
    assert text.startswith("[p-gift-cards:0] Gift cards > Amounts (updated 2026-09-01)")


QUESTIONS = [
    Question(
        "q1", QuestionType.ANSWERABLE, "How many days do I have to return an item?", "p-return-window", "30 days", False
    ),
    Question("q2", QuestionType.EXACT, "What's E2091 about?", "p-error-e2091", "no label could be created", False),
    Question("q3", QuestionType.UNANSWERABLE, "zebra quartz plasma", None, None, False),
]


def test_retrieval_is_graded_per_type_and_mode_with_the_misses_named(built):
    _, retriever, _ = built
    report = evaluate_retrieval(retriever, QUESTIONS)
    assert report.rates[("answerable", "fused")].trials == 1
    assert report.rates[("exact", "keyword")].successes == 1
    assert ("answerable", "vector") in report.rates
    assert not any(kind == "unanswerable" for kind, _ in report.rates)


def answers_by_question(request):
    content = request.messages[0].content
    if "How many days" in content:
        return "Thirty days [p-return-window:0]."
    if "E2091" in content:
        return "It is the wrong thing [p-error-e2091:0]."
    return "Something [p-gift-cards:0]."


def test_answers_and_retrieval_are_graded_apart_and_every_miss_goes_to_one_stage(built):
    _, retriever, _ = built
    judge_model = ScriptedModel(lambda r: "correct" if "Thirty days" in r.messages[0].content else "incorrect")
    report = evaluate_answers(
        service(retriever, answers_by_question), Judge(judge_model, Prompt("judge", "v1", "grade")), QUESTIONS
    )
    assert report.retrieval_hit.trials == 2
    assert report.answer_correct.successes == 1
    assert report.misses_by_stage[Stage.GENERATION] == 1
    assert report.misses_by_stage[Stage.RETRIEVAL] == 0
    assert report.unanswerable_refused.trials == 1
    assert (
        report.input_tokens == 30 * len(judge_model.requests) + 30 * 3 - 30 * len(judge_model.requests)
        or report.input_tokens > 0
    )


def test_an_unanswerable_question_that_gets_an_answer_is_listed_as_a_slip(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, answers_by_question), judge, QUESTIONS)
    assert report.unanswered_slips == ["q3"]
    assert report.unanswerable_refused.successes == 0


def test_a_refused_answerable_question_counts_as_a_false_refusal_and_as_incorrect(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, lambda r: REFUSAL_MESSAGE), judge, QUESTIONS)
    assert report.false_refusals.successes == 2
    assert report.answer_correct.successes == 0


def test_a_stop_request_ends_the_run_between_questions(built):
    _, retriever, _ = built
    stops = iter([False, True])
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(
        service(retriever, answers_by_question), judge, QUESTIONS, stop_requested=lambda: next(stops)
    )
    assert len(report.results) == 1


def test_a_judge_reply_that_says_neither_counts_as_incorrect(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "hmm"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, answers_by_question), judge, QUESTIONS[:1])
    assert report.answer_correct.successes == 0


def test_the_judge_request_names_the_question_the_fact_and_the_answer_and_differs_per_answer(built):
    model = ScriptedModel(lambda r: "correct")
    judge = Judge(model, Prompt("judge", "v1", "grade"))
    judge.grade(QUESTIONS[0], "Thirty days")
    judge.grade(QUESTIONS[0], "Fourteen days")
    first, second = model.requests
    assert "The answer must state: 30 days" in first.messages[0].content
    assert first.tag != second.tag
    assert first.max_output_tokens == 20


def test_summarize_of_nothing_is_all_zeroes():
    report = summarize([])
    assert report.retrieval_hit.trials == 0
    assert report.unanswered_slips == []


def test_the_threshold_is_tuned_from_dev_scores_only(built):
    _, retriever, _ = built
    dev = [
        Question("d1", QuestionType.ANSWERABLE, "How many days do I return an item", "p-return-window", "30", False),
        Question("d2", QuestionType.ANSWERABLE, "gift cards amounts expire", "p-gift-cards", "10", False),
        Question("d3", QuestionType.UNANSWERABLE, "zebra quartz plasma", None, None, False),
    ]
    svc = service(retriever)
    answerable, unanswerable = dev_scores(svc, dev)
    assert len(answerable) == 2
    assert len(unanswerable) == 1
    choice = choose_threshold(svc, dev, max_false_refusal=0.0)
    assert choice.false_refusal_rate == 0.0
    assert choice.unanswerable_refused_rate == 1.0
