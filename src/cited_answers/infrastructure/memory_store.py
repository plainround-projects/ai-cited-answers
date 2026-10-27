"""An in-memory chunk store: the test double and the default for offline runs."""

from __future__ import annotations

from collections.abc import Sequence

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.retrieval import cosine


class InMemoryChunkStore:
    """Chunks and vectors in lists; search is a linear scan, which is plenty for a help center."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._vectors: dict[str, list[float]] = {}

    def replace_all(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("one vector per chunk")
        self._chunks = list(chunks)
        self._vectors = {c.id: list(v) for c, v in zip(chunks, vectors, strict=True)}

    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        scored = [(chunk_id, cosine(vector, stored)) for chunk_id, stored in self._vectors.items()]
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:k]

    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        return {
            chunk_id: cosine(vector, self._vectors[chunk_id]) for chunk_id in chunk_ids if chunk_id in self._vectors
        }
