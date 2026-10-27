"""The boundaries the use cases depend on. Adapters in `infrastructure` implement them."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.evaluation import Question
from cited_answers.domain.llm import ChatRequest, ChatResponse
from cited_answers.domain.pages import Page
from cited_answers.domain.prompts import Prompt


class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""

    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...

    @property
    def supports_sampling(self) -> bool:
        """False when the provider rejects `temperature` and `top_p` (the request then says so)."""
        ...

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...


class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
        ...


class Clock(Protocol):
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class ChunkStore(Protocol):
    """Where chunks and their vectors live: memory in tests, Postgres with pgvector in the service."""

    def replace_all(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Replace the whole index with these chunks and vectors, in one transaction."""
        ...

    def chunks(self) -> list[Chunk]:
        """Every indexed chunk."""
        ...

    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        """The `k` nearest chunk ids with their cosine similarity, best first."""
        ...

    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        """Cosine similarity of the vector to each named chunk."""
        ...


class PageSource(Protocol):
    """Reads the help-center pages."""

    def pages(self) -> list[Page]: ...


class QuestionSource(Protocol):
    """Reads an evaluation set."""

    def load(self, split: str) -> list[Question]: ...


class PromptStore(Protocol):
    """Versioned prompt files."""

    def load(self, name: str, version: str) -> Prompt:
        """The prompt `name` at `version`; raises `PromptNotFound`."""
        ...
