"""Split pages into chunks on their headings, each carrying the metadata a search result needs."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from cited_answers.domain.pages import Page, PageStatus

MAX_CHUNK_TOKENS = 300
_TOKENS_PER_WORD = 1.3
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True, slots=True)
class Chunk:
    """A passage a reader can open: the page it came from, its heading path, its date and its status."""

    id: str
    page_id: str
    heading_path: str
    text: str
    updated: date
    status: PageStatus

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)

    def for_search(self) -> str:
        """The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat."""
        return f"{self.heading_path}. {self.text}"


def estimate_tokens(text: str) -> int:
    """Rough token count for a size limit: words times 1.3."""
    return round(len(text.split()) * _TOKENS_PER_WORD)


def _split_long(text: str, max_tokens: int) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    for sentence in _SENTENCE.split(text):
        if current and estimate_tokens(" ".join([*current, sentence])) > max_tokens:
            parts.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        parts.append(" ".join(current))
    return parts


def chunk_page(page: Page, max_tokens: int = MAX_CHUNK_TOKENS) -> list[Chunk]:
    """One chunk per section, split at sentence ends when a section is longer than `max_tokens`.

    A chunk never spans two sections, so it never spans two pages. Ids are `<page id>:<n>`.
    """
    chunks: list[Chunk] = []
    for section in page.sections:
        for text in _split_long(section.text, max_tokens):
            chunks.append(Chunk(f"{page.id}:{len(chunks)}", page.id, section.path, text, page.updated, page.status))
    return chunks


def chunk_current_pages(pages: Iterable[Page]) -> tuple[list[Chunk], list[str]]:
    """Chunk every current page; return the chunks and the ids of the retired pages that were left out."""
    chunks: list[Chunk] = []
    skipped: list[str] = []
    for page in pages:
        if page.status is PageStatus.CURRENT:
            chunks.extend(chunk_page(page))
        else:
            skipped.append(page.id)
    return chunks, skipped
