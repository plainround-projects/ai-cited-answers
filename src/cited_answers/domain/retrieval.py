"""Keyword search (BM25), vector similarity and the fusion of ranked lists."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Sequence

from cited_answers.domain.chunking import Chunk

_WORD = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "do",
        "does",
        "did",
        "i",
        "you",
        "we",
        "it",
        "my",
        "your",
        "our",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "and",
        "or",
        "but",
        "if",
        "as",
        "at",
        "by",
        "from",
        "this",
        "that",
        "can",
        "how",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "not",
        "no",
    ]
)


def tokenize(text: str) -> list[str]:
    """Lowercase words split on anything that is not a letter or a digit, so `PR-E2091` becomes `pr` and `e2091`."""
    return [word for word in _WORD.findall(text.lower()) if word not in STOPWORDS]


def whitespace_tokenize(text: str) -> list[str]:
    """The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it."""
    return [word.strip(".,;:!?()\"'") for word in text.lower().split() if word.strip(".,;:!?()\"'") not in STOPWORDS]


class Bm25Index:
    """Okapi BM25 over chunk text (heading path included)."""

    def __init__(
        self,
        chunks: Sequence[Chunk],
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Callable[[str], list[str]] = tokenize,
    ) -> None:
        self._ids = [c.id for c in chunks]
        self._tokenizer = tokenizer
        self._k1, self._b = k1, b
        self._documents = [Counter(tokenizer(c.for_search())) for c in chunks]
        self._lengths = [sum(d.values()) for d in self._documents]
        self._average = sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        frequency: Counter[str] = Counter()
        for document in self._documents:
            frequency.update(document.keys())
        count = len(chunks)
        self._idf = {t: math.log(1 + (count - n + 0.5) / (n + 0.5)) for t, n in frequency.items()}

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        """The `k` best chunk ids with their scores; chunks that share no term with the query are not returned."""
        terms = self._tokenizer(query)
        scored: list[tuple[str, float]] = []
        for chunk_id, document, length in zip(self._ids, self._documents, self._lengths, strict=True):
            score = 0.0
            for term in terms:
                tf = document.get(term, 0)
                if tf:
                    norm = tf + self._k1 * (1 - self._b + self._b * length / self._average)
                    score += self._idf[term] * tf * (self._k1 + 1) / norm
            if score > 0:
                scored.append((chunk_id, score))
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:k]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors (0.0 if either is all zeros)."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], k: int = 60, top: int = 5) -> list[tuple[str, float]]:
    """Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top]
