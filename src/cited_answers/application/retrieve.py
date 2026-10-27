"""Ingest the pages and retrieve chunks by vector, by keyword or by both fused."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from cited_answers.application.ports import ChunkStore, Embedder, PageSource
from cited_answers.domain.chunking import Chunk, chunk_current_pages
from cited_answers.domain.retrieval import Bm25Index, reciprocal_rank_fusion

_log = logging.getLogger(__name__)
EMBED_BATCH = 32


class Mode(StrEnum):
    """How to find chunks."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    FUSED = "fused"


@dataclass(frozen=True, slots=True)
class IngestReport:
    """What indexing did: current pages indexed, chunks written, retired pages left out."""

    pages_indexed: int
    chunks: int
    skipped_retired: tuple[str, ...]


def ingest(source: PageSource, embedder: Embedder, store: ChunkStore) -> IngestReport:
    """Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged."""
    pages = source.pages()
    chunks, skipped = chunk_current_pages(pages)
    for page_id in skipped:
        _log.info("retired page left out of the index", extra={"fields": {"page_id": page_id}})
    texts = [chunk.for_search() for chunk in chunks]
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        vectors.extend(embedder.embed(texts[start : start + EMBED_BATCH]))
    store.replace_all(chunks, vectors)
    _log.info(
        "index built",
        extra={"fields": {"pages": len(pages) - len(skipped), "chunks": len(chunks), "skipped": len(skipped)}},
    )
    return IngestReport(len(pages) - len(skipped), len(chunks), tuple(skipped))


@dataclass(frozen=True, slots=True)
class Retrieval:
    """The chunks found for a question, best first, and how close the best of them is to the question's vector."""

    mode: Mode
    chunks: tuple[Chunk, ...]
    best_similarity: float

    @property
    def page_ids(self) -> list[str]:
        return [c.page_id for c in self.chunks]


class HybridRetriever:
    """Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion."""

    def __init__(self, store: ChunkStore, embedder: Embedder, k: int = 5, depth: int = 20, rrf_k: int = 60) -> None:
        self._store = store
        self._embedder = embedder
        self._k, self._depth, self._rrf_k = k, depth, rrf_k
        self._by_id: dict[str, Chunk] = {}
        self._bm25 = Bm25Index([])
        self.reload()

    def reload(self) -> None:
        """Read the chunks again, for example after a page was re-indexed."""
        chunks = self._store.chunks()
        self._by_id = {c.id: c for c in chunks}
        self._bm25 = Bm25Index(chunks)

    @property
    def chunk_count(self) -> int:
        return len(self._by_id)

    def retrieve(self, question: str, mode: Mode = Mode.FUSED) -> Retrieval:
        """The top chunks for a question; `best_similarity` is the highest cosine among them."""
        (vector,) = self._embedder.embed([question])
        vector_hits = self._store.vector_search(vector, self._depth)
        similarities = dict(vector_hits)
        if mode is Mode.VECTOR:
            ids = [chunk_id for chunk_id, _ in vector_hits][: self._k]
        else:
            keyword_ids = [chunk_id for chunk_id, _ in self._bm25.search(question, self._depth)]
            if mode is Mode.KEYWORD:
                ids = keyword_ids[: self._k]
            else:
                rankings = [keyword_ids, [chunk_id for chunk_id, _ in vector_hits]]
                ids = [chunk_id for chunk_id, _ in reciprocal_rank_fusion(rankings, self._rrf_k, self._k)]
        missing = [chunk_id for chunk_id in ids if chunk_id not in similarities]
        if missing:
            similarities.update(self._store.similarities(vector, missing))
        chunks = tuple(self._by_id[chunk_id] for chunk_id in ids)
        best = max((similarities.get(chunk_id, 0.0) for chunk_id in ids), default=0.0)
        return Retrieval(mode, chunks, best)


def describe(chunks: Sequence[Chunk]) -> str:
    """One line per chunk, for logs: ids only."""
    return ",".join(c.id for c in chunks)
