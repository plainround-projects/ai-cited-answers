# Python source, shared test helpers and the process, end-to-end and live tests

## What it is

These tests are the larger ones: `conftest.py` (shared builders and fakes used by many tests), the **integration** tests (the program or a service as a real process, with real signals), the **end-to-end** tests (the lesson's scenario from input to report on recorded answers) and the **live** tests (opt-in, call a real model).

This note walks through every file, line by line: 4 files with 17 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/conftest.py` | 96 non-blank lines |
| `tests/e2e/test_lesson_scenario.py` | 136 non-blank lines |
| `tests/integration/test_pgvector.py` | 81 non-blank lines |
| `tests/live/test_live_models.py` | 36 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/conftest.py`

In its own words: "Shared builders for tests: a fixed clock, a scripted model, a hashing embedder and small pages."

96 non-blank lines; it defines `FixedClock`, `ScriptedModel`, `HashingEmbedder`, `page`, `chunk`, `MemoryPages`, `clock`.

`tests/conftest.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `cited_answers.domain.llm`.
- Brings in `Page` (One help-center page.), `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.), `Section` (Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title.) from the project module `cited_answers.domain.pages`.

`tests/conftest.py`, lines 15 to 27:

```python
from cited_answers.domain.prompts import Prompt


class FixedClock:
    """A clock that only moves when a test says so."""

    def __init__(self, today: date = date(2026, 10, 27)) -> None:
        self._today = today
        self._ticks = 0.0

    def monotonic(self) -> float:
        self._ticks += 0.25
        return self._ticks
```

- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `cited_answers.domain.prompts`.
- Defines the class `FixedClock`. The author's own description: "A clock that only moves when a test says so."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `today` holds a calendar date; if the caller leaves it out it is the result of calling `date`.
- Stores the value named `today` under the name `self._today` (as an attribute of this object, so other methods can use it).
- Stores the number `0.0` under the name `self._ticks` (as an attribute of this object, so other methods can use it).
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Updates `self._ticks` in place: `+=` applies `+` with the number `0.25` and stores the result back.
- Ends the function and gives back the attribute `_ticks` of this object to the caller.

`tests/conftest.py`, lines 29 to 41:

```python
    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""

    def __init__(
        self, answer: Callable[[ChatRequest], str | tuple[str, int, int]] | None = None, sampling: bool = True
    ) -> None:
```

- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_today` of this object to the caller.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime` to the caller.
  - `datetime` from the standard library module `datetime`.
- Defines the class `ScriptedModel`. The author's own description: "Answers every request from a function, and remembers the requests it saw."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `answer` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `sampling` holds true or false; if the caller leaves it out it is the value `True`.

`tests/conftest.py`, lines 42 to 55:

```python
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
```

- Declares `self.requests` as a list of the project type `ChatRequest` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of combining conditions: `answer or (lambda request: 'ok')` under the name `self._answer` (as an attribute of this object, so other methods can use it).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the value named `sampling` under the name `self._sampling` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `scripted` to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Calls `append` on the stored object `self.requests`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self.requests`: it adds one item at the end of a list.

`tests/conftest.py`, lines 56 to 68:

```python
        result = self._answer(request)
        text, tokens_in, tokens_out = (result, 30, 8) if isinstance(result, str) else result
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class HashingEmbedder:
    """A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."""

    name = "hashing"

    def __init__(self, dimensions: int = 64) -> None:
        self._dimensions = dimensions
        self.calls: list[list[str]] = []
```

- Stores the result of calling `self._answer` under the name `result`.
  - The method `_answer` of `self`.
- Stores one of two values, chosen by a condition under the name `(text, tokens_in, tokens_out)`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `cited_answers.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `cited_answers.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the class `HashingEmbedder`. The author's own description: "A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `hashing` under the name `name`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `dimensions` holds a whole number; if the caller leaves it out it is the number `64`.
- Stores the value named `dimensions` under the name `self._dimensions` (as an attribute of this object, so other methods can use it).
- Declares `self.calls` as a list of a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/conftest.py`, lines 70 to 82:

```python
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
```

- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- Calls `append` on the stored object `self.calls`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self.calls`: it adds one item at the end of a list.
  - `list` makes a list (a copy when given a collection).
- Stores an empty list under the name `out`.
- Loop: the indented lines below run once for each item of `texts`; `text` names the current item.
- Stores the result of `[0.0] * self._dimensions` under the name `vector`.
  - `*` is multiply.
- Loop: the indented lines below run once for each item of `re.findall('[a-z0-9]+', text.lower())`; `word` names the current item.
  - `re.findall` lists all matches.
  - `.lower(...)` turns text into lower case.
- Updates `vector[int(hashlib.md5(word.encode())...` in place: `+=` applies `+` with the number `1.0` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `%` is remainder.
  - `int` turns a value into a whole number.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.md5` from the standard library module `hashlib`.
  - `.encode(...)` turns text into bytes.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the function `page`. It returns the project type `Page`.
- Its parameters:
    - `page_id` holds text.
    - `title` holds text.
    - `sections` holds a list of a fixed list of text, text.
    - `status` holds the project type `PageStatus`; if the caller leaves it out it is the `CURRENT` of `PageStatus`.
- Ends the function and gives back the result of calling `Page` to the caller.
  - `Page` from the project's `cited_answers.domain.pages` (One help-center page.).
  - `date` from the standard library module `datetime`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `Section` from the project's `cited_answers.domain.pages` (Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`tests/conftest.py`, lines 85 to 96:

```python
def chunk(chunk_id: str, text: str, heading: str = "Title > Heading") -> Chunk:
    page_id = chunk_id.split(":")[0]
    return Chunk(chunk_id, page_id, heading, text, date(2026, 9, 1), PageStatus.CURRENT)


class MemoryPages:
    """A page source over a list."""

    def __init__(self, pages: list[Page]) -> None:
        self._pages = pages

    def pages(self) -> list[Page]:
```

- Defines the function `chunk`. It returns the project type `Chunk`.
- Its parameters:
    - `chunk_id` holds text.
    - `text` holds text.
    - `heading` holds text; if the caller leaves it out it is the text `Title > Heading`.
- Stores the part of `chunk_id.split(':')` picked by `0` under the name `page_id`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Ends the function and gives back the result of calling `Chunk` to the caller.
  - `Chunk` from the project's `cited_answers.domain.chunking` (A passage a reader can open: the page it came from, its heading path, its date and its status.).
  - `date` from the standard library module `datetime`.
- Defines the class `MemoryPages`. The author's own description: "A page source over a list."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `pages` holds a list of the project type `Page`.
- Stores the value named `pages` under the name `self._pages` (as an attribute of this object, so other methods can use it).
- Defines the method `pages`. It returns a list of the project type `Page`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`tests/conftest.py`, lines 97 to 100:

```python
        return list(self._pages)


PROMPT = Prompt("answer", "v1", "Answer from the passages.")
```

- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
- Stores the result of calling `Prompt` under the name `PROMPT`.
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).

`tests/conftest.py`, lines 102 to 125:

```python
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
```

- Stores a list of 5 item(s) under the name `PAGES`.
  - `page`, a function of this file.

`tests/conftest.py`, lines 128 to 130:

```python
@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()
```

- Defines the function `clock`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter. It returns the project type `FixedClock`.
- It takes no parameters.
- Ends the function and gives back the result of calling `FixedClock` to the caller.
  - `FixedClock`, a class of this project (A clock that only moves when a test says so.).

### `tests/e2e/test_lesson_scenario.py`

In its own words: "The lesson's scenario on recorded embeddings (nomic-embed-text) and recorded answers (qwen2.5:1.5b)."

136 non-blank lines; it defines `world`, `questions`, `service`, `judge`, `test_step_1_retired_pages_are_left_out_logged_by_id_and_every_chunk_has_its_four_fields`, `test_steps_2_and_3_hit_rate_at_five_per_type_for_vectors_keywords_and_both_with_intervals`, `test_the_keyword_index_finds_a_bare_error_code_only_because_the_tokenizer_splits_on_hyphens`, `test_step_4_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal`, `reports`, `test_steps_5_to_7_the_recorded_runs_reproduce_the_committed_reports`, `test_every_answer_in_the_final_run_cites_a_retrieved_chunk_or_is_the_refusal_message`, `test_the_two_stage_table_before_and_after_the_fix`, ....

`tests/e2e/test_lesson_scenario.py`, lines 1 to 14:

```python
"""The lesson's scenario on recorded embeddings (nomic-embed-text) and recorded answers (qwen2.5:1.5b)."""

import json
from pathlib import Path

import pytest

from cited_answers.application.answer import AnswerService
from cited_answers.application.evaluate import evaluate_answers, evaluate_retrieval
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.application.threshold import choose_threshold
from cited_answers.domain.answering import REFUSAL_MESSAGE, Reason
from cited_answers.domain.chunking import MAX_CHUNK_TOKENS
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `json` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `evaluate_answers` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.), `evaluate_retrieval` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.) from the project module `cited_answers.application.evaluate`.
- Brings in `Judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.) from the project module `cited_answers.application.judge`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `Mode` (How to find chunks.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `choose_threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.) from the project module `cited_answers.application.threshold`.
- Brings in `REFUSAL_MESSAGE`, `Reason` (Why a question was refused (or `none` when it was answered).) from the project module `cited_answers.domain.answering`.
- Brings in `MAX_CHUNK_TOKENS` from the project module `cited_answers.domain.chunking`.

`tests/e2e/test_lesson_scenario.py`, lines 15 to 26:

```python
from cited_answers.domain.evaluation import QuestionType, Stage, agreement, validate_questions
from cited_answers.domain.pages import PageStatus
from cited_answers.domain.retrieval import Bm25Index, whitespace_tokenize
from cited_answers.infrastructure.embeddings import EmbeddingStore, RecordedEmbedder
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, FileQuestionSource, read_threshold
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingStore
from tests.conftest import ScriptedModel

pytestmark = pytest.mark.e2e

REPO = Path(__file__).resolve().parents[2]
```

- Brings in `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.), `Stage` (Where a wrong answer went wrong.), `agreement` (How many verdicts the judge shares with the hand grades, and how many were compared.), `validate_questions` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) from the project module `cited_answers.domain.evaluation`.
- Brings in `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.) from the project module `cited_answers.domain.pages`.
- Brings in `Bm25Index` (Okapi BM25 over chunk text (heading path included).), `whitespace_tokenize` (The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it.) from the project module `cited_answers.domain.retrieval`.
- Brings in `EmbeddingStore` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.), `RecordedEmbedder` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.) from the project module `cited_answers.infrastructure.embeddings`.
- Brings in `FilePageSource` (Every `*.md` file in a folder is a page.), `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.), `FileQuestionSource` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.), `read_threshold` (The tuned refusal threshold, if `evals/threshold.json` exists.) from the project module `cited_answers.infrastructure.files`.
- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `cited_answers.infrastructure.recording`.
- Brings in `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Stores the `e2e` of `pytest.mark` under the name `pytestmark`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `2` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.

`tests/e2e/test_lesson_scenario.py`, lines 29 to 40:

```python
@pytest.fixture(scope="module")
def world():
    embedder = RecordedEmbedder(EmbeddingStore(REPO / "tests" / "fixtures" / "embeddings"), "nomic-embed-text")
    store = InMemoryChunkStore()
    report = ingest(FilePageSource(REPO / "data" / "pages"), embedder, store)
    return embedder, store, report, HybridRetriever(store, embedder)


@pytest.fixture(scope="module")
def questions():
    source = FileQuestionSource(REPO / "data" / "questions")
    dev, test = source.load("dev"), source.load("test")
```

- Defines the function `world`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Stores the result of calling `RecordedEmbedder` under the name `embedder`.
  - `RecordedEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
  - `/` is divide.
- Stores the result of calling `InMemoryChunkStore` under the name `store`.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Stores the result of calling `ingest` under the name `report`.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
  - `/` is divide.
- Ends the function and gives back a tuple of 4 item(s) to the caller.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Defines the function `questions`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Stores the result of calling `FileQuestionSource` under the name `source`.
  - `FileQuestionSource` from the project's `cited_answers.infrastructure.files` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.).
  - `/` is divide.
- Stores a tuple of 2 item(s) under the name `(dev, test)`.
  - The method `load` of `source`.

`tests/e2e/test_lesson_scenario.py`, lines 41 to 54:

```python
    validate_questions(dev, 17, 5, 8)
    validate_questions(test, 70, 20, 30)
    return dev, test


def service(retriever, version, model=None):
    prompts = FilePromptStore(REPO / "prompts")
    chat = model or RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    return AnswerService(
        retriever, chat, prompts.load("answer", version), read_threshold(REPO / "evals" / "threshold.json") or 0.5
    ), chat


def judge():
```

- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Defines the function `service`.
- Its parameters:
    - `retriever`.
    - `version`.
    - `model`; if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `FilePromptStore` under the name `prompts`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
  - `/` is divide.
- Stores the result of combining conditions: `model or RecordedChatModel(RecordingStore(REPO / 'tests' ...` under the name `chat`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - The method `load` of `prompts`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
  - `/` is divide.
- Defines the function `judge`.
- It takes no parameters.

`tests/e2e/test_lesson_scenario.py`, lines 55 to 68:

```python
    chat = RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    return Judge(chat, FilePromptStore(REPO / "prompts").load("judge", "v1"))


def test_step_1_retired_pages_are_left_out_logged_by_id_and_every_chunk_has_its_four_fields(world):
    _, store, report, retriever = world
    assert report.skipped_retired == ("p-return-fee-old", "p-return-window-old", "p-ship-costs-old")
    chunks = store.chunks()
    assert report.pages_indexed == 57
    assert len(chunks) == 68
    assert all(c.status is PageStatus.CURRENT for c in chunks)
    assert all(c.page_id and c.heading_path and c.updated and c.status for c in chunks)
    assert all(c.id.startswith(c.page_id + ":") for c in chunks)
    assert max(c.tokens for c in chunks) <= MAX_CHUNK_TOKENS
```

- Stores the result of calling `RecordedChatModel` under the name `chat`.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Ends the function and gives back the result of calling `Judge` to the caller.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - The method `load` of `FilePromptStore(REPO / 'prompts')`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
  - `/` is divide.
- Defines the function `test_step_1_retired_pages_are_left_out_logged_by_id_and_every_chunk_has_its_four_fields`.
- Its parameters:
    - `world`.
- Stores the value named `world` under the name `(_, store, report, retriever)`.
- Checks that `report.skipped_retired == ('p-return-fee-old', 'p-return-window-old', 'p-ship...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Stores the result of calling `store.chunks` under the name `chunks`.
  - The method `chunks` of `store`.
- Checks that `report.pages_indexed == 57` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `len(chunks) == 68` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `all((c.status is PageStatus.CURRENT for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.
- Checks that `all((c.page_id and c.heading_path and c.updated and c.status for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Checks that `all((c.id.startswith(c.page_id + ':') for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.startswith(...)` asks whether text begins with the given text.
  - `+` is add.
- Checks that `max((c.tokens for c in chunks)) <= MAX_CHUNK_TOKENS` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `max` picks the largest value.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`tests/e2e/test_lesson_scenario.py`, lines 69 to 82:

```python
    for mode in Mode:
        found = retriever.retrieve("How many days do I have to return an item?", mode)
        assert not {"p-return-window-old", "p-ship-costs-old", "p-return-fee-old"} & set(found.page_ids)


def test_steps_2_and_3_hit_rate_at_five_per_type_for_vectors_keywords_and_both_with_intervals(world, questions):
    _, test = questions[0], questions[1]
    report = evaluate_retrieval(world[3], test)
    rates = {key: (rate.successes, rate.trials) for key, rate in report.rates.items()}
    assert rates[("answerable", "vector")] == (69, 70)
    assert rates[("answerable", "keyword")] == (66, 70)
    assert rates[("answerable", "fused")] == (68, 70)
    for mode in ("vector", "keyword", "fused"):
        assert rates[("exact", mode)] == (20, 20)
```

- Loop: the indented lines below run once for each item of `Mode`; `mode` names the current item.
- Stores the result of calling `retriever.retrieve` under the name `found`.
  - The method `retrieve` of `retriever`.
- Checks that `not {'p-return-window-old', 'p-ship-costs-old', 'p-return-fee-old'} & set(fou...` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `&` is and.
  - `set` makes a set: a collection with no repeated items.
- Defines the function `test_steps_2_and_3_hit_rate_at_five_per_type_for_vectors_keywords_and_both_with_intervals`.
- Its parameters:
    - `world`.
    - `questions`.
- Stores a tuple of 2 item(s) under the name `(_, test)`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `evaluate_retrieval` under the name `report`.
  - `evaluate_retrieval` from the project's `cited_answers.application.evaluate` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a dictionary built by looping under the name `rates`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Checks that `rates['answerable', 'vector'] == (69, 70)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `rates['answerable', 'keyword'] == (66, 70)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `rates['answerable', 'fused'] == (68, 70)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `('vector', 'keyword', 'fused')`; `mode` names the current item.
- Checks that `rates['exact', mode] == (20, 20)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/e2e/test_lesson_scenario.py`, lines 83 to 96:

```python
    low, high = report.rates[("exact", "fused")].interval
    assert 0.8 < low < high <= 1.0


def test_the_keyword_index_finds_a_bare_error_code_only_because_the_tokenizer_splits_on_hyphens(world):
    _, store, _, retriever = world
    assert retriever.retrieve("What's E2091 about?", Mode.KEYWORD).page_ids[0] == "p-error-e2091"
    naive = Bm25Index(store.chunks(), tokenizer=whitespace_tokenize)
    assert naive.search("What's E2091 about?", 5) == []


def test_step_4_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal(world):
    svc, _ = service(world[3], "v2", ScriptedModel(lambda r: "Thirty days [p-gift-cards:0]."))
    answer = svc.ask("How many days do I have to return an item?", "planted")
```

- Stores the `interval` of `report.rates['exact', 'fused']` under the name `(low, high)`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `0.8 < low < high <= 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `<=` means less than or equal.
- Defines the function `test_the_keyword_index_finds_a_bare_error_code_only_because_the_tokenizer_splits_on_hyphens`.
- Its parameters:
    - `world`.
- Stores the value named `world` under the name `(_, store, _, retriever)`.
- Checks that `retriever.retrieve("What's E2091 about?", Mode.KEYWORD).page_ids[0] == 'p-err...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `retrieve` of `retriever`.
- Stores the result of calling `Bm25Index` under the name `naive`.
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
  - The method `chunks` of `store`.
- Checks that `naive.search("What's E2091 about?", 5) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.search(...)` looks for a regular expression anywhere in text.
- Defines the function `test_step_4_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal`.
- Its parameters:
    - `world`.
- Stores the result of calling `service` under the name `(svc, _)`.
  - `service`, a function of this file.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `svc.ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).

`tests/e2e/test_lesson_scenario.py`, lines 97 to 110:

```python
    assert answer.refused
    assert answer.reason is Reason.CITATION_NOT_RETRIEVED
    assert answer.text == REFUSAL_MESSAGE


@pytest.fixture(scope="module")
def reports(world, questions):
    """The four recorded answer runs (dev and test, prompts v1 and v2), computed once."""
    dev, test = questions
    out = {}
    for split, items in (("dev", dev), ("test", test)):
        for version in ("v1", "v2"):
            out[(split, version)] = evaluate_answers(service(world[3], version)[0], judge(), items)
    return out
```

- Checks that `answer.refused` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `answer.reason is Reason.CITATION_NOT_RETRIEVED` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `answer.text == REFUSAL_MESSAGE` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `reports`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter. The author's own description: "The four recorded answer runs (dev and test, prompts v1 and v2), computed once."
- Its parameters:
    - `world`.
    - `questions`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the value named `questions` under the name `(dev, test)`.
- Stores an empty dictionary under the name `out`.
- Loop: the indented lines below run once for each item of `(('dev', dev), ('test', test))`; `(split, items)` names the current item.
- Loop: the indented lines below run once for each item of `('v1', 'v2')`; `version` names the current item.
- Stores the result of calling `evaluate_answers` under the name `out[split, version]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `judge`, a function of this file.
  - `service`, a function of this file.
- Ends the function and gives back the value named `out` to the caller.

`tests/e2e/test_lesson_scenario.py`, lines 113 to 124:

```python
def test_steps_5_to_7_the_recorded_runs_reproduce_the_committed_reports(reports):
    for (split, version), report in reports.items():
        committed = (REPO / "evals" / "reports" / f"{split}-answer-{version}.txt").read_text()
        assert f"{'retrieval hit rate (answerable+exact)':<34} {report.retrieval_hit}" in committed
        assert f"{'answer correct (judge)':<34} {report.answer_correct}" in committed
        assert f"{'unanswerable refused':<34} {report.unanswerable_refused}" in committed
        assert f"retrieval misses:  {report.misses_by_stage[Stage.RETRIEVAL]}" in committed
        assert f"generation misses: {report.misses_by_stage[Stage.GENERATION]}" in committed


def test_every_answer_in_the_final_run_cites_a_retrieved_chunk_or_is_the_refusal_message(reports):
    for result in reports[("test", "v2")].results:
```

- Defines the function `test_steps_5_to_7_the_recorded_runs_reproduce_the_committed_reports`.
- Its parameters:
    - `reports`.
- Loop: the indented lines below run once for each item of `reports.items()`; `((split, version), report)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Stores the result of calling `(REPO / 'evals' / 'reports' / f'{split}-answer-...` under the name `committed`.
  - `.read_text(...)` reads a whole file as text.
  - `/` is divide.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `f"{'retrieval hit rate (answerable+exact)':<34} {report.retrieval_hit}" in co...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `f"{'answer correct (judge)':<34} {report.answer_correct}" in committed` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `f"{'unanswerable refused':<34} {report.unanswerable_refused}" in committed` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `f'retrieval misses: {report.misses_by_stage[Stage.RETRIEVAL]}' in committed` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `f'generation misses: {report.misses_by_stage[Stage.GENERATION]}' in committed` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_every_answer_in_the_final_run_cites_a_retrieved_chunk_or_is_the_refusal_message`.
- Its parameters:
    - `reports`.
- Loop: the indented lines below run once for each item of `reports['test', 'v2'].results`; `result` names the current item.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/e2e/test_lesson_scenario.py`, lines 125 to 138:

```python
        answer = result.answer
        if answer.refused:
            assert answer.text == REFUSAL_MESSAGE
        else:
            retrieved = {c.id for c in answer.retrieval.chunks}
            assert answer.citations
            assert set(answer.citations) <= retrieved


def test_the_two_stage_table_before_and_after_the_fix(reports):
    before = reports[("test", "v1")].misses_by_stage
    after = reports[("test", "v2")].misses_by_stage
    stage = {s.value: n for s, n in before.items()}
    assert stage == {"retrieval miss": 2, "generation miss": 88}
```

- Stores the `answer` of `result` under the name `answer`.
- Decision: the indented lines below run only when `answer.refused` is true.
- Checks that `answer.text == REFUSAL_MESSAGE` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores a set built by looping under the name `retrieved`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `answer.citations` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `set(answer.citations) <= retrieved` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `set` makes a set: a collection with no repeated items.
- Defines the function `test_the_two_stage_table_before_and_after_the_fix`.
- Its parameters:
    - `reports`.
- Stores the `misses_by_stage` of `reports['test', 'v1']` under the name `before`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the `misses_by_stage` of `reports['test', 'v2']` under the name `after`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a dictionary built by looping under the name `stage`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Checks that `stage == {'retrieval miss': 2, 'generation miss': 88}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/e2e/test_lesson_scenario.py`, lines 139 to 152:

```python
    assert {s.value: n for s, n in after.items()} == {"retrieval miss": 1, "generation miss": 32}


def test_the_threshold_comes_from_the_development_questions_only(world, questions):
    svc, _ = service(world[3], "v2")
    choice = choose_threshold(svc, questions[0])
    assert choice.threshold == read_threshold(REPO / "evals" / "threshold.json")
    assert choice.false_refusal_rate <= 0.10
    written = json.loads((REPO / "evals" / "threshold.json").read_text())
    assert written["tuned_on"] == "dev"


def test_unanswerable_questions_below_the_threshold_never_reach_the_model(world, questions):
    spy = ScriptedModel(lambda r: "should not be called")
```

- Checks that `{s.value: n for s, n in after.items()} == {'retrieval miss': 1, 'generation m...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Defines the function `test_the_threshold_comes_from_the_development_questions_only`.
- Its parameters:
    - `world`.
    - `questions`.
- Stores the result of calling `service` under the name `(svc, _)`.
  - `service`, a function of this file.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `choose_threshold` under the name `choice`.
  - `choose_threshold` from the project's `cited_answers.application.threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `choice.threshold == read_threshold(REPO / 'evals' / 'threshold.json')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
  - `/` is divide.
- Checks that `choice.false_refusal_rate <= 0.1` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
- Stores the result of calling `json.loads` under the name `written`.
  - `json.loads` turns JSON text into Python data.
  - `.read_text(...)` reads a whole file as text.
  - `/` is divide.
- Checks that `written['tuned_on'] == 'dev'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_unanswerable_questions_below_the_threshold_never_reach_the_model`.
- Its parameters:
    - `world`.
    - `questions`.
- Stores the result of calling `ScriptedModel` under the name `spy`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.

`tests/e2e/test_lesson_scenario.py`, lines 153 to 166:

```python
    svc, _ = service(world[3], "v2", spy)
    for question in (q for q in questions[1] if q.type is QuestionType.UNANSWERABLE):
        answer = svc.ask(question.question, question.id)
        if answer.reason is Reason.BELOW_THRESHOLD:
            assert answer.input_tokens == 0
    assert all("should not be called" not in r.messages[0].content for r in spy.requests)


def test_the_judge_agrees_with_thirty_hand_grades_on_at_least_nine_in_ten(reports):
    grades = {}
    for line in (REPO / "evals" / "hand_grades.jsonl").read_text().splitlines():
        row = json.loads(line)
        grades[row["question_id"]] = row["correct"]
    assert len(grades) == 30
```

- Stores the result of calling `service` under the name `(svc, _)`.
  - `service`, a function of this file.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `(q for q in questions[1] if q.type is QuestionType.UNANSW...`; `question` names the current item.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `is` means the very same object.
- Stores the result of calling `svc.ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
- Decision: the indented lines below run only when `answer.reason is Reason.BELOW_THRESHOLD` is true.
  - `is` means the very same object.
- Checks that `answer.input_tokens == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `all(('should not be called' not in r.messages[0].content for r in spy.requests))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_the_judge_agrees_with_thirty_hand_grades_on_at_least_nine_in_ten`.
- Its parameters:
    - `reports`.
- Stores an empty dictionary under the name `grades`.
- Loop: the indented lines below run once for each item of `(REPO / 'evals' / 'hand_grades.jsonl').read_text().splitl...`; `line` names the current item.
  - `.splitlines(...)` cuts text into a list of lines.
  - `/` is divide.
- Stores the result of calling `json.loads` under the name `row`.
  - `json.loads` turns JSON text into Python data.
- Stores the part of `row` picked by `'correct'` under the name `grades[row['question_id']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `len(grades) == 30` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).

`tests/e2e/test_lesson_scenario.py`, lines 167 to 171:

```python
    results = [*reports[("dev", "v2")].results, *reports[("test", "v2")].results]
    shared = [r for r in results if r.question.id in grades and r.correct is not None]
    matched, total = agreement([bool(r.correct) for r in shared], [grades[r.question.id] for r in shared])
    assert total == 30
    assert matched / total >= 0.9
```

- Stores a list of 2 item(s) under the name `results`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a list built by looping under the name `shared`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `is not` means not the same object.
- Stores the result of calling `agreement` under the name `(matched, total)`.
  - `agreement` from the project's `cited_answers.domain.evaluation` (How many verdicts the judge shares with the hand grades, and how many were compared.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `bool` turns a value into true or false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `total == 30` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `matched / total >= 0.9` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `/` is divide.

### `tests/integration/test_pgvector.py`

In its own words: "The Postgres adapter and the HTTP service against the real pgvector container (`make up` first)."

81 non-blank lines; it defines `embedder`, `stores`, `test_ingest_writes_the_current_pages_chunks_and_no_retired_one`, `test_the_database_itself_refuses_a_retired_chunk_and_a_chunk_of_an_unknown_page`, `test_vector_search_in_sql_ranks_like_the_in_memory_scan`, `test_similarities_match_and_the_old_return_window_cannot_be_retrieved`, `test_the_http_service_answers_a_recorded_question_from_the_pgvector_index`.

`tests/integration/test_pgvector.py`, lines 1 to 14:

```python
"""The Postgres adapter and the HTTP service against the real pgvector container (`make up` first)."""

import os
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.infrastructure.embeddings import EmbeddingStore, RecordedEmbedder
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `os` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `psycopg` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `TestClient` from the installed package module `fastapi.testclient`.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `Mode` (How to find chunks.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `EmbeddingStore` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.), `RecordedEmbedder` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.) from the project module `cited_answers.infrastructure.embeddings`.
- Brings in `FilePageSource` (Every `*.md` file in a folder is a page.), `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.) from the project module `cited_answers.infrastructure.files`.
- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.

`tests/integration/test_pgvector.py`, lines 15 to 27:

```python
from cited_answers.infrastructure.pg_store import PgVectorChunkStore
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingStore
from cited_answers.interfaces.http import create_app

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[2]
DSN = os.environ.get("DATABASE_URL", "postgresql://cited:cited@localhost:55432/cited")


@pytest.fixture(scope="module")
def embedder():
    return RecordedEmbedder(EmbeddingStore(REPO / "tests" / "fixtures" / "embeddings"), "nomic-embed-text")
```

- Brings in `PgVectorChunkStore` (Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index.) from the project module `cited_answers.infrastructure.pg_store`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `cited_answers.infrastructure.recording`.
- Brings in `create_app` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.) from the project module `cited_answers.interfaces.http`.
- Stores the `integration` of `pytest.mark` under the name `pytestmark`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `2` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Stores the result of calling `os.environ.get` under the name `DSN`.
  - `os.environ.get` from the standard library module `os`.
- Defines the function `embedder`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Ends the function and gives back the result of calling `RecordedEmbedder` to the caller.
  - `RecordedEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
  - `/` is divide.

`tests/integration/test_pgvector.py`, lines 30 to 41:

```python
@pytest.fixture(scope="module")
def stores(embedder):
    pg = PgVectorChunkStore(DSN)
    assert pg.ping(), "start the database first: make up"
    pages = FilePageSource(REPO / "data" / "pages")
    ingest(pages, embedder, pg)
    memory = InMemoryChunkStore()
    ingest(pages, embedder, memory)
    return pg, memory


def test_ingest_writes_the_current_pages_chunks_and_no_retired_one(stores):
```

- Defines the function `stores`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- Its parameters:
    - `embedder`.
- Stores the result of calling `PgVectorChunkStore` under the name `pg`.
  - `PgVectorChunkStore` from the project's `cited_answers.infrastructure.pg_store` (Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index.).
- Checks that `pg.ping()` is true; if it is not, the test fails with an `AssertionError` and the message `'start the database first: make up'`.
  - The method `ping` of the project's `PgVectorChunkStore` (True when the database answers a trivial query.).
- Stores the result of calling `FilePageSource` under the name `pages`.
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
  - `/` is divide.
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
- Stores the result of calling `InMemoryChunkStore` under the name `memory`.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Defines the function `test_ingest_writes_the_current_pages_chunks_and_no_retired_one`.
- Its parameters:
    - `stores`.

`tests/integration/test_pgvector.py`, lines 42 to 55:

```python
    pg, _ = stores
    with psycopg.connect(DSN) as connection:
        rows: dict[str, int] = dict(
            connection.execute(
                "SELECT p.status::text, count(c.id) FROM pages p LEFT JOIN chunks c ON c.page_id = p.id GROUP BY 1"
            ).fetchall()
        )
    assert rows["retired"] == 0
    assert rows["current"] == len(pg.chunks()) == 68


def test_the_database_itself_refuses_a_retired_chunk_and_a_chunk_of_an_unknown_page(stores):
    zero = "[" + ",".join(["0"] * 768) + "]"
    with psycopg.connect(DSN) as connection, pytest.raises(psycopg.errors.CheckViolation):
```

- Stores the value named `stores` under the name `(pg, _)`.
- A `with` block: it sets up `psycopg.connect(DSN)` as `connection`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `psycopg.connect` opens a connection to PostgreSQL.
- Declares `rows` as a dictionary from text to a whole number and sets it to the result of calling `dict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
  - `.fetchall(...)` reads all rows of a query result.
  - `.execute(...)` runs one SQL statement.
- Checks that `rows['retired'] == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `rows['current'] == len(pg.chunks()) == 68` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `len` counts the items in a collection (or the characters in text).
  - The method `chunks` of `pg`.
- Defines the function `test_the_database_itself_refuses_a_retired_chunk_and_a_chunk_of_an_unknown_page`.
- Its parameters:
    - `stores`.
- Stores the result of `'[' + ','.join(['0'] * 768) + ']'` under the name `zero`.
  - `+` is add.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `*` is multiply.
- A `with` block: it sets up `psycopg.connect(DSN)` as `connection`, `pytest.raises(psycopg.errors.CheckViolation)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `psycopg.connect` opens a connection to PostgreSQL.
  - `pytest.raises` passes if the code inside raises the given error.

`tests/integration/test_pgvector.py`, lines 56 to 69:

```python
        connection.execute(
            "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
            "VALUES ('x:0', 'p-return-window-old', 'h', 'b', DATE '2025-01-01', 'retired', %s::vector)",
            (zero,),
        )
    with psycopg.connect(DSN) as connection, pytest.raises(psycopg.errors.ForeignKeyViolation):
        connection.execute(
            "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
            "VALUES ('x:0', 'no-such-page', 'h', 'b', DATE '2026-01-01', 'current', %s::vector)",
            (zero,),
        )


def test_vector_search_in_sql_ranks_like_the_in_memory_scan(stores, embedder):
```

- Calls `.execute(...)` runs one SQL statement with 2 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- A `with` block: it sets up `psycopg.connect(DSN)` as `connection`, `pytest.raises(psycopg.errors.ForeignKeyViolation)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `psycopg.connect` opens a connection to PostgreSQL.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `.execute(...)` runs one SQL statement with 2 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Defines the function `test_vector_search_in_sql_ranks_like_the_in_memory_scan`.
- Its parameters:
    - `stores`.
    - `embedder`.

`tests/integration/test_pgvector.py`, lines 70 to 83:

```python
    pg, memory = stores
    for question in (
        "How many days do I have to return an item?",
        "What does error PR-E1042 mean?",
        "Do gift cards expire?",
    ):
        (vector,) = embedder.embed([question])
        sql_top = [chunk_id for chunk_id, _ in pg.vector_search(vector, 5)]
        scan_top = [chunk_id for chunk_id, _ in memory.vector_search(vector, 5)]
        assert sql_top == scan_top


def test_similarities_match_and_the_old_return_window_cannot_be_retrieved(stores, embedder):
    pg, memory = stores
```

- Stores the value named `stores` under the name `(pg, memory)`.
- Loop: the indented lines below run once for each item of `('How many days do I have to return an item?', 'What does...`; `question` names the current item.
- Stores the result of calling `embedder.embed` under the name `(vector,)`.
  - The method `embed` of `embedder`.
- Stores a list built by looping under the name `sql_top`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `vector_search` of `pg`.
- Stores a list built by looping under the name `scan_top`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `vector_search` of `memory`.
- Checks that `sql_top == scan_top` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_similarities_match_and_the_old_return_window_cannot_be_retrieved`.
- Its parameters:
    - `stores`.
    - `embedder`.
- Stores the value named `stores` under the name `(pg, memory)`.

`tests/integration/test_pgvector.py`, lines 84 to 97:

```python
    (vector,) = embedder.embed(["How many days do I have to return an item?"])
    ids = [c.id for c in memory.chunks()[:5]]
    for chunk_id, score in pg.similarities(vector, ids).items():
        assert score == pytest.approx(memory.similarities(vector, [chunk_id])[chunk_id], abs=1e-4)
    found = HybridRetriever(pg, embedder).retrieve("How many days do I have to return an item?", Mode.FUSED)
    assert "p-return-window-old" not in found.page_ids


def test_the_http_service_answers_a_recorded_question_from_the_pgvector_index(stores, embedder):
    pg, _ = stores
    model = RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    prompt = FilePromptStore(REPO / "prompts").load("answer", "v1")
    retriever = HybridRetriever(pg, embedder)
    client = TestClient(create_app(AnswerService(retriever, model, prompt, 0.648), lambda: retriever.chunk_count))
```

- Stores the result of calling `embedder.embed` under the name `(vector,)`.
  - The method `embed` of `embedder`.
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - The method `chunks` of `memory`.
- Loop: the indented lines below run once for each item of `pg.similarities(vector, ids).items()`; `(chunk_id, score)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - The method `similarities` of `pg`.
- Checks that `score == pytest.approx(memory.similarities(vector, [chunk_id])[chunk_id], abs...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `similarities` of `memory`.
- Stores the result of calling `HybridRetriever(pg, embedder).retrieve` under the name `found`.
  - The method `retrieve` of `HybridRetriever(pg, embedder)`.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Checks that `'p-return-window-old' not in found.page_ids` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Defines the function `test_the_http_service_answers_a_recorded_question_from_the_pgvector_index`.
- Its parameters:
    - `stores`.
    - `embedder`.
- Stores the value named `stores` under the name `(pg, _)`.
- Stores the result of calling `RecordedChatModel` under the name `model`.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Stores the result of calling `FilePromptStore(REPO / 'prompts').load` under the name `prompt`.
  - The method `load` of `FilePromptStore(REPO / 'prompts')`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
  - `/` is divide.
- Stores the result of calling `HybridRetriever` under the name `retriever`.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Stores the result of calling `TestClient` under the name `client`.
  - `TestClient` from the installed package module `fastapi.testclient`.
  - `create_app` from the project's `cited_answers.interfaces.http` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.).
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - `lambda args: expression` is a small unnamed function written inline.

`tests/integration/test_pgvector.py`, lines 98 to 100:

```python
    assert client.get("/health").json() == {"status": "ok", "chunks": 68}
    body = client.post("/ask", json={"question": "Do you ship to Antarctica?"}).json()
    assert (body["status"], body["reason"]) == ("refused", "below_threshold")
```

- Checks that `client.get('/health').json() == {'status': 'ok', 'chunks': 68}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Stores the result of calling `client.post('/ask', json={'question': 'Do you s...` under the name `body`.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.post(...)` sends an HTTP POST request.
- Checks that `(body['status'], body['reason']) == ('refused', 'below_threshold')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/live/test_live_models.py`

In its own words: "Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."

36 non-blank lines; it defines `local_server_up`, `test_claude_answers_from_the_passage_and_cites_its_id`, `test_the_local_embedding_model_returns_768_dimensional_vectors_and_paraphrases_land_close`.

`tests/live/test_live_models.py`, lines 1 to 13:

```python
"""Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from cited_answers.domain.chunking import chunk_page
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.embeddings import OpenAICompatibleEmbedder
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from tests.conftest import PAGES
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `os` (standard library) available.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `chunk_page` (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.) from the project module `cited_answers.domain.chunking`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `cited_answers.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `cited_answers.infrastructure.clock`.
- Brings in `OpenAICompatibleEmbedder` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.) from the project module `cited_answers.infrastructure.embeddings`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `cited_answers.infrastructure.model_factory`.
- Brings in `PAGES` from the project module `tests.conftest`.

`tests/live/test_live_models.py`, lines 15 to 27:

```python
pytestmark = pytest.mark.live


def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_answers_from_the_passage_and_cites_its_id():
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"}), SystemClock())
```

- Stores the `live` of `pytest.mark` under the name `pytestmark`.
- Defines the function `local_server_up`. It returns true or false.
- It takes no parameters.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back whether `httpx.get('http://localhost:11434/api/tags', timeout=2).s...` holds to the caller.
  - `==` means equal.
  - `httpx.get` sends an HTTP GET request.
- `except` handler: it runs when the `try` block raised `httpx.HTTPError`.
- Ends the function and gives back the value `False` to the caller.
- Defines the function `test_claude_answers_from_the_passage_and_cites_its_id`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/live/test_live_models.py`, lines 28 to 40:

```python
    (chunk,) = chunk_page(PAGES[0])
    prompt = f"Passages:\n\n[{chunk.id}] {chunk.text}\n\nQuestion: How many days do I have to return an item?"
    system = "Answer only from the passages and cite the passage id in square brackets after each fact."
    response = model.complete(ChatRequest((ChatMessage.user(prompt),), system=system, max_output_tokens=200))
    assert "30" in response.text
    assert f"[{chunk.id}]" in response.text


@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_embedding_model_returns_768_dimensional_vectors_and_paraphrases_land_close():
    from cited_answers.domain.retrieval import cosine
```

- Stores the result of calling `chunk_page` under the name `(chunk,)`.
  - `chunk_page` from the project's `cited_answers.domain.chunking` (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a text built from pieces (an f-string) under the name `prompt`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the text `Answer only from the passages and cite the pass...` under the name `system`.
- Stores the result of calling `model.complete` under the name `response`.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Checks that `'30' in response.text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `f'[{chunk.id}]' in response.text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `test_the_local_embedding_model_returns_768_dimensional_vectors_and_paraphrases_land_close`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Brings in `cosine` (Cosine similarity of two vectors (0.0 if either is all zeros).) from the project module `cited_answers.domain.retrieval`.

`tests/live/test_live_models.py`, lines 42 to 47:

```python
    embedder = OpenAICompatibleEmbedder(httpx.Client(timeout=60), "http://localhost:11434/v1", "nomic-embed-text")
    a, b, c = embedder.embed(
        ["How long do I have to return a purchase?", "You can return items within 30 days.", "Gift cards never expire."]
    )
    assert len(a) == 768
    assert cosine(a, b) > cosine(a, c)
```

- Stores the result of calling `OpenAICompatibleEmbedder` under the name `embedder`.
  - `OpenAICompatibleEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.).
  - `httpx.Client` makes an HTTP client.
- Stores the result of calling `embedder.embed` under the name `(a, b, c)`.
  - The method `embed` of `embedder`.
- Checks that `len(a) == 768` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `cosine(a, b) > cosine(a, c)` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/integration --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text

no tests collected (5 deselected) in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/integration -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text

5 deselected in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/integration -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text

no tests collected (5 deselected) in N.NNs
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/conftest.py` test?

   *Answer:* Shared builders for tests: a fixed clock, a scripted model, a hashing embedder and small pages.

2. What does `tests/e2e/test_lesson_scenario.py` test?

   *Answer:* The lesson's scenario on recorded embeddings (nomic-embed-text) and recorded answers (qwen2.5:1.5b).

3. What does `tests/integration/test_pgvector.py` test?

   *Answer:* The Postgres adapter and the HTTP service against the real pgvector container (`make up` first).

4. What does `tests/live/test_live_models.py` test?

   *Answer:* Opt-in tests that call real models. Run with `make test-live`; skipped in every other run.

5. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
