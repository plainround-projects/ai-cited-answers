# Python source, the interfaces layer

## What it is

This note walks through every Python file of the `interfaces` layer of `cited_answers`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **interfaces** layer is the outermost: the command-line program and, where present, the HTTP service. It reads the command line or a request, builds the adapters, calls a use case and turns the result into output and an exit code.

## Why this repository uses it

It is the only layer allowed to know about everything below it, and nothing depends on it. That keeps start-up wiring in one place.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/interfaces/__init__.py` | 1 non-blank lines |
| `src/cited_answers/interfaces/cli.py` | 204 non-blank lines |
| `src/cited_answers/interfaces/http.py` | 76 non-blank lines |
| `src/cited_answers/interfaces/render.py` | 51 non-blank lines |
| `src/cited_answers/interfaces/server.py` | 27 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/cited_answers/interfaces/__init__.py`

In its own words: "Command-line programs. They wire adapters into use cases and own exit codes."

1 non-blank lines.

`src/cited_answers/interfaces/__init__.py`, lines 1 to 1:

```python
"""Command-line programs. They wire adapters into use cases and own exit codes."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/cited_answers/interfaces/cli.py`

In its own words: "The `cited` command: ingest, ask, serve, evaluate retrieval and answers, tune the refusal threshold."

204 non-blank lines; it defines `build_parser`, `_retriever`, `_threshold`, `_service`, `_questions`, `_hand_grades`, `_dump`, `_evaluate`, `_judge_env`, `_tune`, `_known_id`, `_ask`, ....

`src/cited_answers/interfaces/cli.py`, lines 1 to 14:

```python
"""The `cited` command: ingest, ask, serve, evaluate retrieval and answers, tune the refusal threshold."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from cited_answers.application.answer import AnswerService
from cited_answers.application.evaluate import AnswerReport, evaluate_answers, evaluate_retrieval
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `argparse` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `os` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `AnswerReport` (Retrieval and answer quality as separate numbers, the refusal record and the misses by stage.), `evaluate_answers` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.), `evaluate_retrieval` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.) from the project module `cited_answers.application.evaluate`.

`src/cited_answers/interfaces/cli.py`, lines 15 to 28:

```python
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.application.threshold import choose_threshold
from cited_answers.domain.errors import DomainError
from cited_answers.domain.evaluation import InvalidQuestions, Question, agreement, validate_questions
from cited_answers.domain.pages import InvalidPage
from cited_answers.domain.prompts import PromptNotFound
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.env import ConfigurationError
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, FileQuestionSource, read_threshold
from cited_answers.infrastructure.logging import configure_logging
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.shutdown import ShutdownSignal
```

- Brings in `Judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.) from the project module `cited_answers.application.judge`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `choose_threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.) from the project module `cited_answers.application.threshold`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `cited_answers.domain.errors`.
- Brings in `InvalidQuestions` (The question file breaks a rule of the lesson.), `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `agreement` (How many verdicts the judge shares with the hand grades, and how many were compared.), `validate_questions` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) from the project module `cited_answers.domain.evaluation`.
- Brings in `InvalidPage` (A page file is missing its front matter or one of its fields.) from the project module `cited_answers.domain.pages`.
- Brings in `PromptNotFound` (No prompt file for that name and version, or the file's version line does not match.) from the project module `cited_answers.domain.prompts`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `cited_answers.infrastructure.clock`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `cited_answers.infrastructure.env`.
- Brings in `FilePageSource` (Every `*.md` file in a folder is a page.), `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.), `FileQuestionSource` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.), `read_threshold` (The tuned refusal threshold, if `evals/threshold.json` exists.) from the project module `cited_answers.infrastructure.files`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) from the project module `cited_answers.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `cited_answers.infrastructure.model_factory`.
- Brings in `AppSettings` (Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable.) from the project module `cited_answers.infrastructure.settings`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `cited_answers.infrastructure.shutdown`.

`src/cited_answers/interfaces/cli.py`, lines 29 to 42:

```python
from cited_answers.infrastructure.wiring import build_embedder, build_store
from cited_answers.interfaces.render import render_answers, render_ingest, render_retrieval

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_INTERRUPTED = 0, 1, 2, 4
SPLIT_MIX = {"dev": (17, 5, 8), "test": (70, 20, 30)}
DEFAULT_THRESHOLD = 0.5
_log = logging.getLogger("cited")


def build_parser() -> argparse.ArgumentParser:
    """The `cited` argument parser."""
    parser = argparse.ArgumentParser(prog="cited", description="Cited answers over a help center.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="chunk the current pages, embed them and fill the index (needed once for pgvector)")
```

- Brings in `build_embedder` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).), `build_store` (The in-memory store, or Postgres with pgvector.) from the project module `cited_answers.infrastructure.wiring`.
- Brings in `render_answers` (The answer report: retrieval and answer correctness as two numbers, refusals, the stage table and the cost.), `render_ingest` (One line: pages and chunks indexed, retired pages skipped by id.), `render_retrieval` (Hit rate at five per question type and retrieval mode, each with its Wilson interval.) from the project module `cited_answers.interfaces.render`.
- Stores a tuple of 4 item(s) under the name `(EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EX...`.
- Stores a dictionary with 2 entries under the name `SPLIT_MIX`.
- Stores the number `0.5` under the name `DEFAULT_THRESHOLD`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the function `build_parser`. It returns `argparse.ArgumentParser`. The author's own description: "The `cited` argument parser."
- It takes no parameters.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `argparse.ArgumentParser` under the name `parser`.
  - `argparse.ArgumentParser` from the standard library module `argparse`.
- Stores the result of calling `parser.add_subparsers` under the name `sub`.
  - The method `add_subparsers` of `parser`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.

`src/cited_answers/interfaces/cli.py`, lines 43 to 56:

```python
    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    sub.add_parser("serve", help="run the HTTP service (POST /ask, GET /health)")
    retrieval = sub.add_parser("retrieval", help="hit rate at 5 for vectors, keywords and both fused")
    retrieval.add_argument("--split", choices=sorted(SPLIT_MIX), required=True)
    sub.add_parser("tune-threshold", help="choose the refusal threshold on the development questions only")
    answers = sub.add_parser("evaluate", help="grade retrieval and answers apart on a question set")
    answers.add_argument("--split", choices=sorted(SPLIT_MIX), required=True)
    answers.add_argument("--prompt", help="answer prompt version (default: ANSWER_PROMPT_VERSION)")
    answers.add_argument(
        "--hand-grades", type=Path, help="JSON Lines of {question_id, correct} to measure the judge against"
    )
    answers.add_argument("--dump", type=Path, help="write every question, answer and verdict to this JSON Lines file")
    answers.add_argument("--write-report", action="store_true", help="write evals/reports/<split>-answer-<prompt>.txt")
```

- Stores the result of calling `sub.add_parser` under the name `ask`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `ask` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `ask`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Stores the result of calling `sub.add_parser` under the name `retrieval`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `retrieval` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `retrieval`.
  - `sorted` returns a new list with the items in order.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Stores the result of calling `sub.add_parser` under the name `answers`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `answers` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `answers`.
  - `sorted` returns a new list with the items in order.
- Calls the method `add_argument` of `answers` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `answers`.
- Calls the method `add_argument` of `answers` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `answers`.
- Calls the method `add_argument` of `answers` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `answers`.
- Calls the method `add_argument` of `answers` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `answers`.

`src/cited_answers/interfaces/cli.py`, lines 57 to 70:

```python
    return parser


def _retriever(settings: AppSettings) -> tuple[HybridRetriever, str]:
    embedder = build_embedder(settings)
    store = build_store(settings)
    report = ingest(FilePageSource(settings.pages_dir), embedder, store) if settings.index_backend == "memory" else None
    retriever = HybridRetriever(store, embedder)
    return retriever, (
        render_ingest(report) if report else f"using the existing index ({retriever.chunk_count} chunks)"
    )


def _threshold(settings: AppSettings) -> float:
```

- Ends the function and gives back the value named `parser` to the caller.
- Defines the function `_retriever`. It returns a fixed list of the project type `HybridRetriever`, text.
- Its parameters:
    - `settings` holds the project type `AppSettings`.
- Stores the result of calling `build_embedder` under the name `embedder`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
- Stores the result of calling `build_store` under the name `store`.
  - `build_store` from the project's `cited_answers.infrastructure.wiring` (The in-memory store, or Postgres with pgvector.).
- Stores one of two values, chosen by a condition under the name `report`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
- Stores the result of calling `HybridRetriever` under the name `retriever`.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `render_ingest` from the project's `cited_answers.interfaces.render` (One line: pages and chunks indexed, retired pages skipped by id.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_threshold`. It returns a decimal number.
- Its parameters:
    - `settings` holds the project type `AppSettings`.

`src/cited_answers/interfaces/cli.py`, lines 71 to 84:

```python
    if settings.refusal_threshold is not None:
        return settings.refusal_threshold
    return read_threshold(settings.threshold_path) or DEFAULT_THRESHOLD


def _service(settings: AppSettings, retriever: HybridRetriever, version: str | None = None) -> AnswerService:
    prompts = FilePromptStore(settings.prompts_dir)
    model = build_chat_model(ModelSettings.from_env(), SystemClock())
    prompt = prompts.load("answer", version or settings.answer_prompt)
    return AnswerService(retriever, model, prompt, _threshold(settings))


def _questions(settings: AppSettings, split: str) -> list[Question]:
    questions = FileQuestionSource(settings.questions_dir).load(split)
```

- Decision: the indented lines below run only when `settings.refusal_threshold is not None` is true.
  - `is not` means not the same object.
- Ends the function and gives back the `refusal_threshold` of `settings` to the caller.
- Ends the function and gives back the result of combining conditions: `read_threshold(settings.threshold_path) or DEFAULT_THRESHOLD` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
- Defines the function `_service`. It returns the project type `AnswerService`.
- Its parameters:
    - `settings` holds the project type `AppSettings`.
    - `retriever` holds the project type `HybridRetriever`.
    - `version` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `FilePromptStore` under the name `prompts`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Stores the result of calling `prompts.load` under the name `prompt`.
  - The method `load` of `prompts`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Ends the function and gives back the result of calling `AnswerService` to the caller.
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - `_threshold`, a function of this file.
- Defines the function `_questions`. It returns a list of the project type `Question`.
- Its parameters:
    - `settings` holds the project type `AppSettings`.
    - `split` holds text.
- Stores the result of calling `FileQuestionSource(settings.questions_dir).load` under the name `questions`.
  - The method `load` of `FileQuestionSource(settings.questions...`.
  - `FileQuestionSource` from the project's `cited_answers.infrastructure.files` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.).

`src/cited_answers/interfaces/cli.py`, lines 85 to 96:

```python
    answerable, exact, unanswerable = SPLIT_MIX[split]
    validate_questions(questions, answerable, exact, unanswerable)
    return questions


def _hand_grades(path: Path) -> dict[str, bool]:
    grades: dict[str, bool] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            grades[row["question_id"]] = bool(row["correct"])
    return grades
```

- Stores the part of `SPLIT_MIX` picked by `split` under the name `(answerable, exact, unanswerable)`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
- Ends the function and gives back the value named `questions` to the caller.
- Defines the function `_hand_grades`. It returns a dictionary from text to true or false.
- Its parameters:
    - `path` holds a file path.
- Declares `grades` as a dictionary from text to true or false and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `path.read_text(encoding='utf-8').splitlines()`; `line` names the current item.
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `row`.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `bool` under the name `grades[row['question_id']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `bool` turns a value into true or false.
- Ends the function and gives back the value named `grades` to the caller.

`src/cited_answers/interfaces/cli.py`, lines 99 to 102:

```python
def _dump(path: Path, report: AnswerReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for r in report.results:
```

- Defines the function `_dump`. It returns nothing (None).
- Its parameters:
    - `path` holds a file path.
    - `report` holds the project type `AnswerReport`.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
- A `with` block: it sets up `path.open('w', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `path`.
- Loop: the indented lines below run once for each item of `report.results`; `r` names the current item.

`src/cited_answers/interfaces/cli.py`, lines 103 to 123:

```python
            handle.write(
                json.dumps(
                    {
                        "question_id": r.question.id,
                        "type": r.question.type.value,
                        "question": r.question.question,
                        "fact": r.question.fact,
                        "status": r.answer.status.value,
                        "reason": r.answer.reason.value,
                        "answer": r.answer.text,
                        "raw": r.answer.raw_text,
                        "gold_page": r.question.gold_page,
                        "retrieved": [c.id for c in r.answer.retrieval.chunks],
                        "hit": r.hit,
                        "judge_correct": r.correct,
                        "best_similarity": round(r.answer.retrieval.best_similarity, 4),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
```

- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `round` rounds a number.

`src/cited_answers/interfaces/cli.py`, lines 126 to 137:

```python
def _evaluate(args: argparse.Namespace, settings: AppSettings, shutdown: ShutdownSignal) -> int:
    retriever, note = _retriever(settings)
    print(note)
    service = _service(settings, retriever, args.prompt)
    prompts = FilePromptStore(settings.prompts_dir)
    judge = Judge(
        build_chat_model(ModelSettings.from_env({**_judge_env()}), SystemClock()),
        prompts.load("judge", settings.judge_prompt),
    )
    questions = _questions(settings, args.split)
    report = evaluate_answers(service, judge, questions, stop_requested=lambda: shutdown.requested)
    verdicts = None
```

- Defines the function `_evaluate`. It returns a whole number.
- Its parameters:
    - `args` holds `argparse.Namespace`.
    - `settings` holds the project type `AppSettings`.
    - `shutdown` holds the project type `ShutdownSignal`.
- Stores the result of calling `_retriever` under the name `(retriever, note)`.
  - `_retriever`, a function of this file.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Stores the result of calling `_service` under the name `service`.
  - `_service`, a function of this file.
- Stores the result of calling `FilePromptStore` under the name `prompts`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `load` of `prompts`.
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
  - `_judge_env`, a function of this file (The environment for the judge's model: `JUDGE_MODEL_NAME` overrides `MODEL_NAME`.).
- Stores the result of calling `_questions` under the name `questions`.
  - `_questions`, a function of this file.
- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores nothing (`None`) under the name `verdicts`.

`src/cited_answers/interfaces/cli.py`, lines 138 to 151:

```python
    if args.hand_grades:
        grades = _hand_grades(args.hand_grades)
        shared = [r for r in report.results if r.question.id in grades and r.correct is not None]
        verdicts = agreement([bool(r.correct) for r in shared], [grades[r.question.id] for r in shared])
    label = f"{args.split} set, answer prompt {args.prompt or settings.answer_prompt}"
    text = render_answers(label, report, service.threshold, verdicts)
    print(text)
    if args.dump:
        _dump(args.dump, report)
    if args.write_report:
        settings.reports_dir.mkdir(parents=True, exist_ok=True)
        name = f"{args.split}-answer-{args.prompt or settings.answer_prompt}.txt"
        (settings.reports_dir / name).write_text(text + "\n", encoding="utf-8")
    return EXIT_INTERRUPTED if shutdown.requested else EXIT_OK
```

- Decision: the indented lines below run only when `args.hand_grades` is true.
- Stores the result of calling `_hand_grades` under the name `grades`.
  - `_hand_grades`, a function of this file.
- Stores a list built by looping under the name `shared`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `is not` means not the same object.
- Stores the result of calling `agreement` under the name `verdicts`.
  - `agreement` from the project's `cited_answers.domain.evaluation` (How many verdicts the judge shares with the hand grades, and how many were compared.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `bool` turns a value into true or false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a text built from pieces (an f-string) under the name `label`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Stores the result of calling `render_answers` under the name `text`.
  - `render_answers` from the project's `cited_answers.interfaces.render` (The answer report: retrieval and answer correctness as two numbers, refusals, the stage table and the cost.).
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Decision: the indented lines below run only when `args.dump` is true.
- Calls `_dump`, a function of this file with 2 argument(s); the result is not kept.
  - `_dump`, a function of this file.
- Decision: the indented lines below run only when `args.write_report` is true.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
- Stores a text built from pieces (an f-string) under the name `name`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `+` is add.
  - `/` is divide.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.

`src/cited_answers/interfaces/cli.py`, lines 154 to 165:

```python
def _judge_env() -> dict[str, str]:
    """The environment for the judge's model: `JUDGE_MODEL_NAME` overrides `MODEL_NAME`."""
    env = dict(os.environ)
    env["MODEL_NAME"] = os.environ.get("JUDGE_MODEL_NAME", os.environ.get("MODEL_NAME", "qwen2.5:1.5b"))
    return env


def _tune(settings: AppSettings) -> int:
    retriever, note = _retriever(settings)
    print(note)
    choice = choose_threshold(_service(settings, retriever), _questions(settings, "dev"))
    settings.threshold_path.parent.mkdir(parents=True, exist_ok=True)
```

- Defines the function `_judge_env`. It returns a dictionary from text to text. The author's own description: "The environment for the judge's model: `JUDGE_MODEL_NAME` overrides `MODEL_NAME`."
- It takes no parameters.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `dict` under the name `env`.
  - `dict` makes a dictionary (a copy when given one).
- Stores the result of calling `os.environ.get` under the name `env['MODEL_NAME']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `os.environ.get` from the standard library module `os`.
- Ends the function and gives back the value named `env` to the caller.
- Defines the function `_tune`. It returns a whole number.
- Its parameters:
    - `settings` holds the project type `AppSettings`.
- Stores the result of calling `_retriever` under the name `(retriever, note)`.
  - `_retriever`, a function of this file.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Stores the result of calling `choose_threshold` under the name `choice`.
  - `choose_threshold` from the project's `cited_answers.application.threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.).
  - `_service`, a function of this file.
  - `_questions`, a function of this file.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.

`src/cited_answers/interfaces/cli.py`, lines 166 to 177:

```python
    record = {
        "threshold": choice.threshold,
        "tuned_on": "dev",
        "false_refusal_rate_on_dev": round(choice.false_refusal_rate, 4),
        "unanswerable_refused_rate_on_dev": round(choice.unanswerable_refused_rate, 4),
    }
    settings.threshold_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        f"threshold {choice.threshold}: wrongly refuses {choice.false_refusal_rate:.0%} of answerable dev questions, "
        f"refuses {choice.unanswerable_refused_rate:.0%} of the unanswerable ones"
    )
    return EXIT_OK
```

- Stores a dictionary with 4 entries under the name `record`.
  - `round` rounds a number.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_OK` to the caller.

`src/cited_answers/interfaces/cli.py`, lines 180 to 191:

```python
def _known_id(settings: AppSettings, question: str) -> str:
    """The id of a dev or test question with this exact text (so its recorded answer is found), else `adhoc`."""
    source = FileQuestionSource(settings.questions_dir)
    for split in SPLIT_MIX:
        for known in source.load(split):
            if known.question == question:
                return known.id
    return "adhoc"


def _ask(settings: AppSettings, question: str) -> int:
    retriever, _ = _retriever(settings)
```

- Defines the function `_known_id`. It returns text. The author's own description: "The id of a dev or test question with this exact text (so its recorded answer is found), else `adhoc`."
- Its parameters:
    - `settings` holds the project type `AppSettings`.
    - `question` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `FileQuestionSource` under the name `source`.
  - `FileQuestionSource` from the project's `cited_answers.infrastructure.files` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.).
- Loop: the indented lines below run once for each item of `SPLIT_MIX`; `split` names the current item.
- Loop: the indented lines below run once for each item of `source.load(split)`; `known` names the current item.
  - The method `load` of `source`.
- Decision: the indented lines below run only when `known.question == question` is true.
  - `==` means equal.
- Ends the function and gives back the `id` of `known` to the caller.
- Ends the function and gives back the text `adhoc` to the caller.
- Defines the function `_ask`. It returns a whole number.
- Its parameters:
    - `settings` holds the project type `AppSettings`.
    - `question` holds text.
- Stores the result of calling `_retriever` under the name `(retriever, _)`.
  - `_retriever`, a function of this file.

`src/cited_answers/interfaces/cli.py`, lines 192 to 205:

```python
    answer = _service(settings, retriever).ask(question, _known_id(settings, question))
    cited = ", ".join(answer.citations) or "nothing"
    print(answer.text)
    score = f"best similarity {answer.retrieval.best_similarity:.3f}"
    print(f"[{answer.status.value}: {answer.reason.value}; {score}; cited {cited}]")
    return EXIT_OK


def _run(args: argparse.Namespace, settings: AppSettings, shutdown: ShutdownSignal) -> int:
    if args.command == "serve":
        from cited_answers.interfaces.server import serve

        return serve(settings)
    if args.command == "ingest":
```

- Stores the result of calling `_service(settings, retriever).ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `_known_id`, a function of this file (The id of a dev or test question with this exact text (so its recorded answer is found), else `adhoc`.).
  - `_service`, a function of this file.
- Stores the result of combining conditions: `', '.join(answer.citations) or 'nothing'` under the name `cited`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Stores a text built from pieces (an f-string) under the name `score`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Defines the function `_run`. It returns a whole number.
- Its parameters:
    - `args` holds `argparse.Namespace`.
    - `settings` holds the project type `AppSettings`.
    - `shutdown` holds the project type `ShutdownSignal`.
- Decision: the indented lines below run only when `args.command == 'serve'` is true.
  - `==` means equal.
- Brings in `serve` (Build the service from the settings and run it until it is told to stop.) from the project module `cited_answers.interfaces.server`.
- Ends the function and gives back the result of calling `serve` to the caller.
  - `serve` from the project's `cited_answers.interfaces.server` (Build the service from the settings and run it until it is told to stop.).
- Decision: the indented lines below run only when `args.command == 'ingest'` is true.
  - `==` means equal.

`src/cited_answers/interfaces/cli.py`, lines 206 to 218:

```python
        embedder, store = build_embedder(settings), build_store(settings)
        print(render_ingest(ingest(FilePageSource(settings.pages_dir), embedder, store)))
        return EXIT_OK
    if args.command == "retrieval":
        retriever, note = _retriever(settings)
        print(note)
        print(render_retrieval(evaluate_retrieval(retriever, _questions(settings, args.split))))
        return EXIT_OK
    if args.command == "tune-threshold":
        return _tune(settings)
    if args.command == "ask":
        return _ask(settings, args.question)
    return _evaluate(args, settings, shutdown)
```

- Stores a tuple of 2 item(s) under the name `(embedder, store)`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
  - `build_store` from the project's `cited_answers.infrastructure.wiring` (The in-memory store, or Postgres with pgvector.).
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `render_ingest` from the project's `cited_answers.interfaces.render` (One line: pages and chunks indexed, retired pages skipped by id.).
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Decision: the indented lines below run only when `args.command == 'retrieval'` is true.
  - `==` means equal.
- Stores the result of calling `_retriever` under the name `(retriever, note)`.
  - `_retriever`, a function of this file.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `render_retrieval` from the project's `cited_answers.interfaces.render` (Hit rate at five per question type and retrieval mode, each with its Wilson interval.).
  - `evaluate_retrieval` from the project's `cited_answers.application.evaluate` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.).
  - `_questions`, a function of this file.
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Decision: the indented lines below run only when `args.command == 'tune-threshold'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `_tune` to the caller.
  - `_tune`, a function of this file.
- Decision: the indented lines below run only when `args.command == 'ask'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `_ask` to the caller.
  - `_ask`, a function of this file.
- Ends the function and gives back the result of calling `_evaluate` to the caller.
  - `_evaluate`, a function of this file.

`src/cited_answers/interfaces/cli.py`, lines 221 to 232:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted)."""
    args = build_parser().parse_args(argv)
    try:
        settings = AppSettings.from_env()
        configure_logging(settings.log_level)
        shutdown = ShutdownSignal()
        shutdown.install()
        return _run(args, settings, shutdown)
    except (ConfigurationError, InvalidQuestions, InvalidPage, PromptNotFound) as error:
        print(f"cited: {error}", file=sys.stderr)
        return EXIT_CONFIG
```

- Defines the function `main`. It returns a whole number. The author's own description: "Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted)."
- Its parameters:
    - `argv` holds anything that behaves like a list of text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `build_parser().parse_args` under the name `args`.
  - The method `parse_args` of `build_parser()`.
  - `build_parser`, a function of this file (The `cited` argument parser.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `AppSettings.from_env` under the name `settings`.
  - The method `from_env` of `AppSettings`.
- Calls `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 1 argument(s); the result is not kept.
  - `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `cited_answers.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Ends the function and gives back the result of calling `_run` to the caller.
  - `_run`, a function of this file.
- `except` handler: it runs when the `try` block raised `(ConfigurationError, InvalidQuestions, InvalidPage, PromptNotFound)`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_CONFIG` to the caller.

`src/cited_answers/interfaces/cli.py`, lines 233 to 239:

```python
    except DomainError as error:
        print(f"cited: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
```

- `except` handler: it runs when the `try` block raised the project type `DomainError`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_ERROR` to the caller.
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `sys.exit` from the standard library module `sys` with 1 argument(s); the result is not kept.
  - `sys.exit` from the standard library module `sys`.
  - `main`, a function of this file (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).

### `src/cited_answers/interfaces/http.py`

In its own words: "The HTTP interface: POST /ask and GET /health."

76 non-blank lines; it defines `AskRequest`, `CitationOut`, `AskResponse`, `create_app`.

`src/cited_answers/interfaces/http.py`, lines 1 to 14:

```python
"""The HTTP interface: POST /ask and GET /health."""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from cited_answers.application.answer import AnswerService
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `uuid` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `Annotated` from the standard library module `typing`.
- Brings in `FastAPI`, `HTTPException`, `Response` from the installed package module `fastapi`.
- Brings in `BaseModel`, `ConfigDict`, `Field` from the installed package module `pydantic`.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.

`src/cited_answers/interfaces/http.py`, lines 15 to 28:

```python
from cited_answers.domain.errors import ModelError

_log = logging.getLogger("cited.http")


class AskRequest(BaseModel):
    """The body of POST /ask."""

    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, Field(min_length=3, max_length=500)]


class CitationOut(BaseModel):
    """One cited chunk, with what a reader needs to open it."""
```

- Brings in `ModelError` (A model call failed.) from the project module `cited_answers.domain.errors`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `AskRequest`. It builds on pydantic's `BaseModel` (a class whose fields are validated). The author's own description: "The body of POST /ask."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `ConfigDict` under the name `model_config`.
  - `ConfigDict` from the installed package module `pydantic`.
- Declares `question` as text with extra rules.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `Field` from the installed package module `pydantic`.
- Defines the class `CitationOut`. It builds on pydantic's `BaseModel` (a class whose fields are validated). The author's own description: "One cited chunk, with what a reader needs to open it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/interfaces/http.py`, lines 30 to 42:

```python
    chunk_id: str
    page_id: str
    heading_path: str


class AskResponse(BaseModel):
    """The answer, or the fixed refusal and why."""

    status: str
    answer: str
    reason: str
    citations: list[CitationOut]
    best_similarity: float
```

- Declares `chunk_id` as text.
- Declares `page_id` as text.
- Declares `heading_path` as text.
- Defines the class `AskResponse`. It builds on pydantic's `BaseModel` (a class whose fields are validated). The author's own description: "The answer, or the fixed refusal and why."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `status` as text.
- Declares `answer` as text.
- Declares `reason` as text.
- Declares `citations` as a list of the project type `CitationOut`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `best_similarity` as a decimal number.

`src/cited_answers/interfaces/http.py`, lines 45 to 55:

```python
def create_app(service: AnswerService, chunk_count: Callable[[], int]) -> FastAPI:
    """Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready."""
    app = FastAPI(title="cited-answers", version="0.1.0")

    @app.get("/health")
    def health(response: Response) -> dict[str, object]:
        count = chunk_count()
        if count == 0:
            response.status_code = 503
            return {"status": "not ready", "chunks": 0}
        return {"status": "ok", "chunks": count}
```

- Defines the function `create_app`. It returns `FastAPI`. The author's own description: "Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready."
- Its parameters:
    - `service` holds the project type `AnswerService`.
    - `chunk_count` holds a function.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `FastAPI` under the name `app`.
  - `FastAPI` from the installed package module `fastapi`.
- Defines the function `health`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a dictionary from text to any object.
- Its parameters:
    - `response` holds `Response`.
- Stores the result of calling `chunk_count` under the name `count`.
  - `chunk_count`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `count == 0` is true.
  - `==` means equal.
- Stores the number `503` under the name `response.status_code`.
- Ends the function and gives back a dictionary with 2 entries to the caller.
- Ends the function and gives back a dictionary with 2 entries to the caller.

`src/cited_answers/interfaces/http.py`, lines 57 to 68:

```python
    @app.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest) -> AskResponse:
        request_id = uuid.uuid4().hex[:12]
        digest = hashlib.sha256(body.question.encode()).hexdigest()[:10]
        try:
            answer = service.ask(body.question, request_id)
        except ModelError as error:
            _log.warning(
                "model unavailable", extra={"fields": {"request_id": request_id, "error": type(error).__name__}}
            )
            raise HTTPException(status_code=503, detail="the model is unavailable, try again shortly") from error
        by_id = {c.id: c for c in answer.retrieval.chunks}
```

- Defines the function `ask`. `@app.post(...)` registers the function as the handler of HTTP POST requests for that path. It returns the project type `AskResponse`.
- Its parameters:
    - `body` holds the project type `AskRequest`.
- Stores the part of `uuid.uuid4().hex` picked by `:12` under the name `request_id`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `uuid.uuid4` makes a random unique id.
- Stores the part of `hashlib.sha256(body.questio...` picked by `:10` under the name `digest`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `service.ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
- `except` handler: it runs when the `try` block raised the project type `ModelError`; `error` names the error object.
- Calls the method `warning` of `_log` with 2 argument(s); the result is not kept.
  - The method `warning` of `_log`.
  - `type` gives the type (class) of a value.
- Raises an error: the result of calling `HTTPException`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `HTTPException` from the installed package module `fastapi`.
- Stores a dictionary built by looping under the name `by_id`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`src/cited_answers/interfaces/http.py`, lines 69 to 73:

```python
        citations = [
            CitationOut(chunk_id=cid, page_id=by_id[cid].page_id, heading_path=by_id[cid].heading_path)
            for cid in answer.citations
            if cid in by_id
        ]
```

- Stores a list built by looping under the name `citations`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `CitationOut`, a class of this project (One cited chunk, with what a reader needs to open it.).
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/interfaces/http.py`, lines 74 to 86:

```python
        _log.info(
            "question answered",
            extra={
                "fields": {
                    "request_id": request_id,
                    "question_sha": digest,
                    "chars": len(body.question),
                    "status": answer.status.value,
                    "reason": answer.reason.value,
                    "citations": len(citations),
                }
            },
        )
```

- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
  - `len` counts the items in a collection (or the characters in text).

`src/cited_answers/interfaces/http.py`, lines 87 to 95:

```python
        return AskResponse(
            status=answer.status.value,
            answer=answer.text,
            reason=answer.reason.value,
            citations=citations,
            best_similarity=round(answer.retrieval.best_similarity, 4),
        )

    return app
```

- Ends the function and gives back the result of calling `AskResponse` to the caller.
  - `AskResponse`, a class of this project (The answer, or the fixed refusal and why.).
  - `round` rounds a number.
- Ends the function and gives back the value named `app` to the caller.

### `src/cited_answers/interfaces/render.py`

In its own words: "Plain-text rendering of the retrieval and answer reports."

51 non-blank lines; it defines `render_ingest`, `render_retrieval`, `_rate`, `render_answers`.

`src/cited_answers/interfaces/render.py`, lines 1 to 12:

```python
"""Plain-text rendering of the retrieval and answer reports."""

from __future__ import annotations

from cited_answers.application.evaluate import AnswerReport, RetrievalReport
from cited_answers.application.retrieve import IngestReport, Mode
from cited_answers.domain.evaluation import Rate, Stage


def render_ingest(report: IngestReport) -> str:
    """One line: pages and chunks indexed, retired pages skipped by id."""
    skipped = ", ".join(report.skipped_retired) or "none"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `AnswerReport` (Retrieval and answer quality as separate numbers, the refusal record and the misses by stage.), `RetrievalReport` (Hit rate at five per question type and retrieval mode.) from the project module `cited_answers.application.evaluate`.
- Brings in `IngestReport` (What indexing did: current pages indexed, chunks written, retired pages left out.), `Mode` (How to find chunks.) from the project module `cited_answers.application.retrieve`.
- Brings in `Rate` (A count out of a total with its Wilson interval.), `Stage` (Where a wrong answer went wrong.) from the project module `cited_answers.domain.evaluation`.
- Defines the function `render_ingest`. It returns text. The author's own description: "One line: pages and chunks indexed, retired pages skipped by id."
- Its parameters:
    - `report` holds the project type `IngestReport`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of combining conditions: `', '.join(report.skipped_retired) or 'none'` under the name `skipped`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.

`src/cited_answers/interfaces/render.py`, lines 13 to 26:

```python
    return (
        f"indexed {report.pages_indexed} current pages as {report.chunks} chunks; "
        f"skipped {len(report.skipped_retired)} retired pages: {skipped}"
    )


def render_retrieval(report: RetrievalReport) -> str:
    """Hit rate at five per question type and retrieval mode, each with its Wilson interval."""
    lines = ["--- hit rate at 5: a chunk of the gold page is among the top five ---"]
    types = sorted({kind for kind, _ in report.rates})
    for kind in types:
        for mode in Mode:
            rate = report.rates[(kind, mode.value)]
            missed = report.misses.get((kind, mode.value), [])
```

- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `render_retrieval`. It returns text. The author's own description: "Hit rate at five per question type and retrieval mode, each with its Wilson interval."
- Its parameters:
    - `report` holds the project type `RetrievalReport`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list of 1 item(s) under the name `lines`.
- Stores the result of calling `sorted` under the name `types`.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Loop: the indented lines below run once for each item of `types`; `kind` names the current item.
- Loop: the indented lines below run once for each item of `Mode`; `mode` names the current item.
- Stores the part of `report.rates` picked by `(kind, mode.value)` under the name `rate`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `report.misses.get` under the name `missed`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/cited_answers/interfaces/render.py`, lines 27 to 37:

```python
            tail = f"   missed: {', '.join(missed)}" if missed else ""
            lines.append(f"{kind:<10} {mode.value:<8} {rate}{tail}")
    return "\n".join(lines)


def _rate(label: str, rate: Rate) -> str:
    return f"{label:<34} {rate}"


def render_answers(title: str, report: AnswerReport, threshold: float, agreement: tuple[int, int] | None) -> str:
    """The answer report: retrieval and answer correctness as two numbers, refusals, the stage table and the cost."""
```

- Stores one of two values, chosen by a condition under the name `tail`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `'\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `_rate`. It returns text.
- Its parameters:
    - `label` holds text.
    - `rate` holds the project type `Rate`.
- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `render_answers`. It returns text. The author's own description: "The answer report: retrieval and answer correctness as two numbers, refusals, the stage table and the cost."
- Its parameters:
    - `title` holds text.
    - `report` holds the project type `AnswerReport`.
    - `threshold` holds a decimal number.
    - `agreement` holds a fixed list of a whole number, a whole number, or nothing (None).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/interfaces/render.py`, lines 38 to 50:

```python
    lines = [
        f"== {title} (refusal threshold {threshold}) ==",
        _rate("retrieval hit rate (answerable+exact)", report.retrieval_hit),
        _rate("answer correct (judge)", report.answer_correct),
        _rate("unanswerable refused", report.unanswerable_refused),
        _rate("answerable wrongly refused", report.false_refusals),
    ]
    slips = report.unanswered_slips
    lines.append(
        "every unanswerable question was refused."
        if not slips
        else f"NOT every unanswerable question was refused; answered: {', '.join(slips)}"
    )
```

- Stores a list of 5 item(s) under the name `lines`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_rate`, a function of this file.
- Stores the `unanswered_slips` of `report` under the name `slips`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `not` flips true and false.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.

`src/cited_answers/interfaces/render.py`, lines 51 to 61:

```python
    lines += [
        "misses by stage:",
        f"  retrieval misses:  {report.misses_by_stage[Stage.RETRIEVAL]}",
        f"  generation misses: {report.misses_by_stage[Stage.GENERATION]}",
    ]
    if agreement is not None:
        lines.append(
            f"judge agreement with hand grades: {agreement[0]}/{agreement[1]} = {agreement[0] / agreement[1]:.0%}"
        )
    lines.append(f"tokens: {report.input_tokens} in, {report.output_tokens} out")
    return "\n".join(lines)
```

- Updates `lines` in place: `+=` applies `+` with a list of 3 item(s) and stores the result back.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `agreement is not None` is true.
  - `is not` means not the same object.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `/` is divide.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `'\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.

### `src/cited_answers/interfaces/server.py`

In its own words: "Run the HTTP service with uvicorn: SIGTERM finishes in-flight requests, then the process exits."

27 non-blank lines; it defines `serve`.

`src/cited_answers/interfaces/server.py`, lines 1 to 14:

```python
"""Run the HTTP service with uvicorn: SIGTERM finishes in-flight requests, then the process exits."""

from __future__ import annotations

import uvicorn

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.domain.errors import DomainError
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, read_threshold
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.wiring import build_embedder, build_store
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `uvicorn` (installed package) available.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `cited_answers.domain.errors`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `cited_answers.infrastructure.clock`.
- Brings in `FilePageSource` (Every `*.md` file in a folder is a page.), `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.), `read_threshold` (The tuned refusal threshold, if `evals/threshold.json` exists.) from the project module `cited_answers.infrastructure.files`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `cited_answers.infrastructure.model_factory`.
- Brings in `AppSettings` (Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable.) from the project module `cited_answers.infrastructure.settings`.
- Brings in `build_embedder` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).), `build_store` (The in-memory store, or Postgres with pgvector.) from the project module `cited_answers.infrastructure.wiring`.

`src/cited_answers/interfaces/server.py`, lines 15 to 28:

```python
from cited_answers.interfaces.http import create_app


def serve(settings: AppSettings) -> int:
    """Build the service from the settings and run it until it is told to stop."""
    embedder, store = build_embedder(settings), build_store(settings)
    if settings.index_backend == "memory":
        ingest(FilePageSource(settings.pages_dir), embedder, store)
    retriever = HybridRetriever(store, embedder)
    model = build_chat_model(ModelSettings.from_env(), SystemClock())
    threshold = settings.refusal_threshold or read_threshold(settings.threshold_path) or 0.5
    prompt = FilePromptStore(settings.prompts_dir).load("answer", settings.answer_prompt)
    app = create_app(AnswerService(retriever, model, prompt, threshold), lambda: retriever.chunk_count)
    try:
```

- Brings in `create_app` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.) from the project module `cited_answers.interfaces.http`.
- Defines the function `serve`. It returns a whole number. The author's own description: "Build the service from the settings and run it until it is told to stop."
- Its parameters:
    - `settings` holds the project type `AppSettings`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a tuple of 2 item(s) under the name `(embedder, store)`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
  - `build_store` from the project's `cited_answers.infrastructure.wiring` (The in-memory store, or Postgres with pgvector.).
- Decision: the indented lines below run only when `settings.index_backend == 'memory'` is true.
  - `==` means equal.
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
- Stores the result of calling `HybridRetriever` under the name `retriever`.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Stores the result of combining conditions: `settings.refusal_threshold or read_threshold(settings.thr...` under the name `threshold`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
- Stores the result of calling `FilePromptStore(settings.prompts_dir).load` under the name `prompt`.
  - The method `load` of `FilePromptStore(settings.prompts_dir)`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
- Stores the result of calling `create_app` under the name `app`.
  - `create_app` from the project's `cited_answers.interfaces.http` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.).
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - `lambda args: expression` is a small unnamed function written inline.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.

`src/cited_answers/interfaces/server.py`, lines 29 to 32:

```python
        uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, timeout_graceful_shutdown=10)
    except DomainError:
        return 1
    return 0
```

- Calls `uvicorn.run` starts the web server and keeps running with 5 argument(s); the result is not kept.
  - `uvicorn.run` starts the web server and keeps running.
- `except` handler: it runs when the `try` block raised the project type `DomainError`.
- Ends the function and gives back the number `1` to the caller.
- Ends the function and gives back the number `0` to the caller.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import cited_answers.interfaces.__init__; print(cited_answers.interfaces.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Command-line programs. They wire adapters into use cases and own exit codes.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/cited_answers/interfaces').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
cli.py 14
http.py 4
render.py 4
server.py 1
```

3. The rule that keeps this layer in its place: both contracts must be KEPT.

```bash
.venv/bin/lint-imports --no-logo 2>&1 | grep -E 'KEPT|BROKEN'
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT
```

## Mistakes people make

- **Common mistakes with this layer.** Putting rules in the command-line code, forgetting to return the right exit code, or printing instead of returning values so tests cannot check them. Here each command returns an exit code and prints through small render helpers.

## Check yourself

1. What is the job of `src/cited_answers/interfaces/__init__.py`?

   *Answer:* Command-line programs. They wire adapters into use cases and own exit codes.

2. What is the job of `src/cited_answers/interfaces/cli.py`?

   *Answer:* The `cited` command: ingest, ask, serve, evaluate retrieval and answers, tune the refusal threshold.

3. What is the job of `src/cited_answers/interfaces/http.py`?

   *Answer:* The HTTP interface: POST /ask and GET /health.

4. What is the job of `src/cited_answers/interfaces/render.py`?

   *Answer:* Plain-text rendering of the retrieval and answer reports.

5. What is the job of `src/cited_answers/interfaces/server.py`?

   *Answer:* Run the HTTP service with uvicorn: SIGTERM finishes in-flight requests, then the process exits.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
