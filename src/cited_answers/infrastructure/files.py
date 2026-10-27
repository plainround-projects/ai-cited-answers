"""Readers for the page files, the question files, the prompt files and the threshold file."""

from __future__ import annotations

import json
import re
from pathlib import Path

from cited_answers.domain.evaluation import InvalidQuestions, Question, QuestionType
from cited_answers.domain.pages import Page, parse_page
from cited_answers.domain.prompts import Prompt, PromptNotFound

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


class FilePageSource:
    """Every `*.md` file in a folder is a page."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def pages(self) -> list[Page]:
        return [parse_page(path.read_text(encoding="utf-8")) for path in sorted(self._folder.glob("*.md"))]


class FileQuestionSource:
    """`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def load(self, split: str) -> list[Question]:
        path = self._folder / f"{split}.jsonl"
        questions: list[Question] = []
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    questions.append(
                        Question(
                            row["id"],
                            QuestionType(row["type"]),
                            row["question"],
                            row["gold_page"],
                            row["fact"],
                            bool(row.get("near_miss", False)),
                        )
                    )
                except (json.JSONDecodeError, KeyError, ValueError) as error:
                    raise InvalidQuestions(f"{path}:{number}: {error!r}") from error
        return questions


class FilePromptStore:
    """Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def load(self, name: str, version: str) -> Prompt:
        path = self._root / name / f"{version}.md"
        if not path.exists():
            raise PromptNotFound(f"no prompt file {path}")
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            raise PromptNotFound(f"{path} has no front matter with a version line")
        header = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
        if header.get("version", "").strip() != version:
            raise PromptNotFound(
                f"{path}: the version line says {header.get('version', '').strip()!r}, not {version!r}"
            )
        return Prompt(name, version, match.group(2).strip())


def read_threshold(path: Path) -> float | None:
    """The tuned refusal threshold, if `evals/threshold.json` exists."""
    if not path.exists():
        return None
    return float(json.loads(path.read_text(encoding="utf-8"))["threshold"])
