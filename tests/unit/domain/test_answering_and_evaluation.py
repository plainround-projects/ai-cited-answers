import pytest

from cited_answers.domain.answering import (
    REFUSAL_MESSAGE,
    Reason,
    check_citations,
    extract_citations,
    is_model_refusal,
    tune_threshold,
)
from cited_answers.domain.evaluation import (
    InvalidQuestions,
    Question,
    QuestionType,
    Rate,
    Stage,
    agreement,
    classify_miss,
    hit_at_k,
    parse_verdict,
    validate_questions,
    wilson_interval,
)
from tests.conftest import chunk

RETRIEVED = [
    chunk("p-return-window:0", "x"),
    chunk("p-gift-cards:0", "y"),
    chunk("p-ship-times:0", "z"),
    chunk("p-ship-times:1", "w"),
]


def test_citations_are_read_in_order_without_repeats():
    assert extract_citations("A [p-a:0]. B [p-b:1] and again [p-a:0].") == ["p-a:0", "p-b:1"]
    assert extract_citations("no brackets, [two words] don't count") == []


def test_an_answer_that_cites_only_retrieved_chunks_passes():
    check = check_citations("Thirty days [p-return-window:0].", RETRIEVED)
    assert check.ok
    assert check.cited == ("p-return-window:0",)


def test_a_planted_citation_to_a_chunk_that_was_not_retrieved_fails():
    check = check_citations("Maybe [p-gift-cards:0] and [p-loyalty:0].", RETRIEVED)
    assert not check.ok
    assert check.reason is Reason.CITATION_NOT_RETRIEVED


def test_an_answer_with_no_citation_fails_for_its_own_reason():
    check = check_citations("It is thirty days.", RETRIEVED)
    assert (check.ok, check.reason) == (False, Reason.NO_CITATION)


def test_a_literal_placeholder_citation_is_rejected_like_any_unretrieved_id():
    assert not check_citations("Thirty days [chunk-id] [p-return-window:0]", RETRIEVED).ok


def test_a_page_level_citation_is_read_as_its_one_retrieved_chunk_but_not_when_ambiguous():
    assert check_citations("Yes [p-return-window]", RETRIEVED).cited == ("p-return-window:0",)
    assert not check_citations("Yes [p-ship-times]", RETRIEVED).ok  # two chunks of that page were retrieved


def test_the_fixed_refusal_is_recognized_even_with_trailing_text():
    assert is_model_refusal(REFUSAL_MESSAGE)
    assert is_model_refusal("I don't have information about that in our help center")
    assert is_model_refusal(REFUSAL_MESSAGE + " [p-a:0]")
    assert not is_model_refusal("Returns take 30 days [p-a:0]")


def test_the_threshold_allows_the_stated_false_refusal_rate_and_reports_what_it_costs():
    answerable = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.3]
    unanswerable = [0.2, 0.25, 0.4, 0.52, 0.6]
    choice = tune_threshold(answerable, unanswerable, max_false_refusal=0.10)
    assert choice.threshold == 0.5
    assert choice.false_refusal_rate == pytest.approx(0.1)
    assert choice.unanswerable_refused_rate == pytest.approx(3 / 5)


def test_tuning_needs_scores_for_both_kinds():
    with pytest.raises(ValueError, match=r"answerable"):
        tune_threshold([], [0.1])


def test_wilson_stays_inside_zero_and_one_and_widens_for_small_n():
    low, high = wilson_interval(6, 6)
    assert 0.5 < low < 1.0
    assert high == pytest.approx(1.0)
    assert wilson_interval(0, 0) == (0.0, 1.0)
    assert (wilson_interval(10, 10)[0]) < wilson_interval(100, 100)[0]


def test_a_rate_prints_with_its_interval():
    assert str(Rate(70, 70)).startswith("70/70 = 1.00 (Wilson 0.9")
    assert Rate(0, 0).value == 0.0


def test_hit_at_k_looks_at_the_first_k_pages_only():
    assert hit_at_k(["a", "b", "c"], "c", k=3)
    assert not hit_at_k(["a", "b", "c"], "c", k=2)
    assert not hit_at_k(["a"], None)


@pytest.mark.parametrize(
    ("text", "verdict"),
    [
        ("correct", True),
        ("Correct.", True),
        ("incorrect", False),
        ("The answer is incorrect", False),
        ("maybe", None),
        ("", None),
    ],
)
def test_a_judge_reply_is_read_as_correct_incorrect_or_neither(text, verdict):
    assert parse_verdict(text) is verdict


def test_a_wrong_answer_is_a_retrieval_miss_when_the_gold_page_was_not_found_and_a_generation_miss_otherwise():
    assert classify_miss(hit=False, correct=False) is Stage.RETRIEVAL
    assert classify_miss(hit=True, correct=False) is Stage.GENERATION
    assert classify_miss(hit=True, correct=True) is None


def test_agreement_counts_shared_verdicts_and_refuses_unequal_lengths():
    assert agreement([True, False, True], [True, True, True]) == (2, 3)
    with pytest.raises(ValueError, match="same length"):
        agreement([True], [True, False])


def question(i, kind, gold="p", fact="f"):
    return Question(
        f"q{i}",
        kind,
        "what?",
        gold if kind is not QuestionType.UNANSWERABLE else None,
        fact if kind is not QuestionType.UNANSWERABLE else None,
        False,
    )


def test_a_question_set_must_have_the_mix_unique_ids_and_a_fact_for_every_gradable_question():
    ok = [question(1, QuestionType.ANSWERABLE), question(2, QuestionType.EXACT), question(3, QuestionType.UNANSWERABLE)]
    validate_questions(ok, 1, 1, 1)
    with pytest.raises(InvalidQuestions, match="expected"):
        validate_questions(ok, 2, 1, 1)
    with pytest.raises(InvalidQuestions, match="unique"):
        validate_questions([ok[0], ok[0]], 1, 0, 0)
    bad = [Question("q1", QuestionType.ANSWERABLE, "what?", "p", None, False)]
    with pytest.raises(InvalidQuestions, match="gold page and a fact"):
        validate_questions(bad, 1, 0, 0)
