"""Tune the refusal threshold on the development questions only."""

from __future__ import annotations

from collections.abc import Sequence

from cited_answers.application.answer import AnswerService
from cited_answers.domain.answering import ThresholdChoice, tune_threshold
from cited_answers.domain.evaluation import Question, QuestionType


def dev_scores(service: AnswerService, questions: Sequence[Question]) -> tuple[list[float], list[float]]:
    """Best retrieval score of each answerable (gold-page) question and of each unanswerable one."""
    answerable: list[float] = []
    unanswerable: list[float] = []
    for question in questions:
        score = service.retrieve(question.question).best_similarity
        (unanswerable if question.type is QuestionType.UNANSWERABLE else answerable).append(score)
    return answerable, unanswerable


def choose_threshold(
    service: AnswerService, dev_questions: Sequence[Question], max_false_refusal: float = 0.10
) -> ThresholdChoice:
    """The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate."""
    answerable, unanswerable = dev_scores(service, dev_questions)
    return tune_threshold(answerable, unanswerable, max_false_refusal)
