"""Answer rules: the fixed refusal, the citation check and the tuning of the refusal threshold."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from cited_answers.domain.chunking import Chunk

REFUSAL_MESSAGE = "I don't have information about that in our help center."
_CITATION = re.compile(r"\[([^\[\]\s]+)\]")


class Status(StrEnum):
    """What the reader gets: a cited answer or the fixed refusal."""

    ANSWERED = "answered"
    REFUSED = "refused"


class Reason(StrEnum):
    """Why a question was refused (or `none` when it was answered)."""

    NONE = "none"
    BELOW_THRESHOLD = "below_threshold"
    MODEL_REFUSED = "model_refused"
    NO_CITATION = "no_citation"
    CITATION_NOT_RETRIEVED = "citation_not_retrieved"


@dataclass(frozen=True, slots=True)
class CitationCheck:
    """The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved."""

    ok: bool
    cited: tuple[str, ...]
    reason: Reason


def extract_citations(text: str) -> list[str]:
    """Every `[id]` in the text, in order of first appearance, without repeats."""
    seen: dict[str, None] = {}
    for match in _CITATION.finditer(text):
        seen.setdefault(match.group(1), None)
    return list(seen)


def check_citations(text: str, retrieved: Sequence[Chunk]) -> CitationCheck:
    """An answer must cite at least one chunk, and only chunks that were retrieved for this request.

    A citation that names a page instead of a chunk (`p-return-window`) is read as that page's chunk when exactly one
    chunk of the page was retrieved. Anything else that is not a retrieved id fails the check.
    """
    known = {chunk.id for chunk in retrieved}
    by_page: dict[str, list[str]] = {}
    for chunk in retrieved:
        by_page.setdefault(chunk.page_id, []).append(chunk.id)
    cited = extract_citations(text)
    if not cited:
        return CitationCheck(False, (), Reason.NO_CITATION)
    normalized: list[str] = []
    bad: list[str] = []
    for item in cited:
        if item in known:
            normalized.append(item)
        elif len(by_page.get(item, [])) == 1:
            normalized.append(by_page[item][0])
        else:
            bad.append(item)
    if bad:
        return CitationCheck(False, tuple(cited), Reason.CITATION_NOT_RETRIEVED)
    return CitationCheck(True, tuple(dict.fromkeys(normalized)), Reason.NONE)


def is_model_refusal(text: str) -> bool:
    """True when the model answered with the fixed refusal message (it may add a trailing citation or spacing)."""
    return REFUSAL_MESSAGE.lower().rstrip(".") in text.lower()


@dataclass(frozen=True, slots=True)
class ThresholdChoice:
    """A refusal threshold and what it costs: the share of answerable questions it would wrongly refuse."""

    threshold: float
    false_refusal_rate: float
    unanswerable_refused_rate: float


def tune_threshold(
    answerable: Sequence[float], unanswerable: Sequence[float], max_false_refusal: float = 0.10
) -> ThresholdChoice:
    """The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.

    A question is refused when its best score is below the threshold. Tune on the development set only.
    """
    if not answerable or not unanswerable:
        raise ValueError("tuning needs scores for answerable and for unanswerable questions")
    ordered = sorted(answerable)
    allowed = math.floor(max_false_refusal * len(ordered))
    threshold = math.floor(ordered[allowed] * 1000) / 1000
    false_refusal = sum(score < threshold for score in answerable) / len(answerable)
    refused = sum(score < threshold for score in unanswerable) / len(unanswerable)
    return ThresholdChoice(threshold, false_refusal, refused)
