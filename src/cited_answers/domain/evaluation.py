"""Questions, the two grades (retrieval and answer), intervals and the split of misses by stage."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from cited_answers.domain.errors import DomainError

_VERDICT = re.compile(r"\b(incorrect|correct)\b", re.IGNORECASE)


class InvalidQuestions(DomainError):
    """The question file breaks a rule of the lesson."""


class QuestionType(StrEnum):
    """Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable."""

    ANSWERABLE = "answerable"
    EXACT = "exact"
    UNANSWERABLE = "unanswerable"


@dataclass(frozen=True, slots=True)
class Question:
    """One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable."""

    id: str
    type: QuestionType
    question: str
    gold_page: str | None
    fact: str | None
    near_miss: bool

    @property
    def has_gold(self) -> bool:
        return self.type is not QuestionType.UNANSWERABLE


def validate_questions(questions: list[Question], answerable: int, exact: int, unanswerable: int) -> None:
    """Check a question set has the lesson's mix and that every gradable question has a gold page and a fact."""
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise InvalidQuestions("question ids must be unique")
    counts = {t: sum(q.type is t for q in questions) for t in QuestionType}
    want = {QuestionType.ANSWERABLE: answerable, QuestionType.EXACT: exact, QuestionType.UNANSWERABLE: unanswerable}
    if counts != want:
        raise InvalidQuestions(f"expected {dict(want)}, found {dict(counts)}")
    for question in questions:
        if question.has_gold and not (question.gold_page and question.fact):
            raise InvalidQuestions(f"{question.id}: a gradable question needs a gold page and a fact")


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not."""
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    denominator = 1 + z**2 / trials
    center = p + z**2 / (2 * trials)
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2))
    return (max(0.0, (center - half) / denominator), min(1.0, (center + half) / denominator))


@dataclass(frozen=True, slots=True)
class Rate:
    """A count out of a total with its Wilson interval."""

    successes: int
    trials: int

    @property
    def value(self) -> float:
        return self.successes / self.trials if self.trials else 0.0

    @property
    def interval(self) -> tuple[float, float]:
        return wilson_interval(self.successes, self.trials)

    def __str__(self) -> str:
        low, high = self.interval
        return f"{self.successes}/{self.trials} = {self.value:.2f} (Wilson {low:.2f}-{high:.2f})"


def hit_at_k(retrieved_pages: list[str], gold_page: str | None, k: int = 5) -> bool:
    """True when a chunk of the gold page is among the first `k` retrieved."""
    return gold_page is not None and gold_page in retrieved_pages[:k]


def parse_verdict(text: str) -> bool | None:
    """Read a judge's reply: True for correct, False for incorrect, None when it says neither."""
    match = _VERDICT.search(text)
    return None if match is None else match.group(1).lower() == "correct"


class Stage(StrEnum):
    """Where a wrong answer went wrong."""

    RETRIEVAL = "retrieval miss"
    GENERATION = "generation miss"


def classify_miss(hit: bool, correct: bool) -> Stage | None:
    """A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss."""
    if correct:
        return None
    return Stage.GENERATION if hit else Stage.RETRIEVAL


def agreement(judge: list[bool], human: list[bool]) -> tuple[int, int]:
    """How many verdicts the judge shares with the hand grades, and how many were compared."""
    if len(judge) != len(human):
        raise ValueError("judge and hand grades must have the same length")
    return sum(a == b for a, b in zip(judge, human, strict=True)), len(judge)
