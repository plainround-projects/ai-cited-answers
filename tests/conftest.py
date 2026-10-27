"""Shared builders for tests: a fixed clock, a scripted model, a hashing embedder and small pages."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime

import pytest

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.llm import ChatRequest, ChatResponse, StopReason, Usage
from cited_answers.domain.pages import Page, PageStatus, Section
from cited_answers.domain.prompts import Prompt


class FixedClock:
    """A clock that only moves when a test says so."""

    def __init__(self, today: date = date(2026, 10, 27)) -> None:
        self._today = today
        self._ticks = 0.0

    def monotonic(self) -> float:
        self._ticks += 0.25
        return self._ticks

    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""

    def __init__(
        self, answer: Callable[[ChatRequest], str | tuple[str, int, int]] | None = None, sampling: bool = True
    ) -> None:
        self.requests: list[ChatRequest] = []
        self._answer = answer or (lambda request: "ok")
        self._sampling = sampling

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def supports_sampling(self) -> bool:
        return self._sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        result = self._answer(request)
        text, tokens_in, tokens_out = (result, 30, 8) if isinstance(result, str) else result
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class HashingEmbedder:
    """A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."""

    name = "hashing"

    def __init__(self, dimensions: int = 64) -> None:
        self._dimensions = dimensions
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        out = []
        for text in texts:
            vector = [0.0] * self._dimensions
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % self._dimensions] += 1.0
            out.append(vector)
        return out


def page(page_id: str, title: str, sections: list[tuple[str, str]], status: PageStatus = PageStatus.CURRENT) -> Page:
    return Page(page_id, title, date(2026, 9, 1), status, tuple(Section(f"{title} > {h}", t) for h, t in sections))


def chunk(chunk_id: str, text: str, heading: str = "Title > Heading") -> Chunk:
    page_id = chunk_id.split(":")[0]
    return Chunk(chunk_id, page_id, heading, text, date(2026, 9, 1), PageStatus.CURRENT)


class MemoryPages:
    """A page source over a list."""

    def __init__(self, pages: list[Page]) -> None:
        self._pages = pages

    def pages(self) -> list[Page]:
        return list(self._pages)


PROMPT = Prompt("answer", "v1", "Answer from the passages.")

PAGES = [
    page(
        "p-return-window",
        "Return window",
        [("30 days", "You can return items within 30 days of delivery for a full refund.")],
    ),
    page(
        "p-return-window-old",
        "Return window (old)",
        [("14 days", "You can return any item within 14 days.")],
        PageStatus.RETIRED,
    ),
    page(
        "p-error-e2091",
        "Error PR-E2091",
        [("Meaning", "Error PR-E2091 means no shipping label could be created for the address.")],
    ),
    page("p-gift-cards", "Gift cards", [("Amounts", "Gift cards come in amounts from $10 to $200 and do not expire.")]),
    page(
        "p-ship-times",
        "Shipping times",
        [("Standard", "Standard shipping takes 3 to 5 business days inside the United States.")],
    ),
]


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()
