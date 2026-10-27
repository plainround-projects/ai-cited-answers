"""Help-center pages: a title, an updated date, a status and sections under headings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from cited_answers.domain.errors import DomainError

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_HEADING = re.compile(r"^(#{1,3}) +(.+?) *$", re.MULTILINE)


class InvalidPage(DomainError):
    """A page file is missing its front matter or one of its fields."""


class PageStatus(StrEnum):
    """Only `current` pages are indexed. A `retired` page may contradict a current one."""

    CURRENT = "current"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class Section:
    """Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title."""

    path: str
    text: str


@dataclass(frozen=True, slots=True)
class Page:
    """One help-center page."""

    id: str
    title: str
    updated: date
    status: PageStatus
    sections: tuple[Section, ...]


def parse_page(source: str) -> Page:
    """Parse a page file: front matter (id, title, updated, status) and a body split on its headings."""
    match = _FRONT_MATTER.match(source)
    if not match:
        raise InvalidPage("page has no front matter")
    header = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    values = {key.strip(): value.strip() for key, value in header.items()}
    for name in ("id", "title", "updated", "status"):
        if not values.get(name):
            raise InvalidPage(f"front matter is missing {name!r}")
    try:
        status = PageStatus(values["status"])
        updated = date.fromisoformat(values["updated"])
    except ValueError as error:
        raise InvalidPage(f"{values['id']}: {error}") from error
    return Page(values["id"], values["title"], updated, status, _sections(values["title"], match.group(2)))


def _sections(title: str, body: str) -> tuple[Section, ...]:
    headings = list(_HEADING.finditer(body))
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []
    for index, heading in enumerate(headings):
        level, name = len(heading.group(1)), heading.group(2)
        stack = [(lv, nm) for lv, nm in stack if lv < level] + [(level, name)]
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        text = body[heading.end() : end].strip()
        if text:
            names = [nm for _, nm in stack if nm != title]
            sections.append(Section(" > ".join([title, *names]), text))
    if not sections:
        raise InvalidPage(f"{title}: no section with text")
    return tuple(sections)
