# Python source, the domain layer

## What it is

This note walks through every Python file of the `domain` layer of `cited_answers`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **domain** is the core of the program: plain Python objects and functions that hold the rules of the problem (prices, estimates, state changes, validation). It imports nothing from outside the standard library except small helpers, so it can be understood and tested without a network, a database or a web framework.

## Why this repository uses it

The domain is where the project's decisions live, and import-linter forbids it from importing a vendor SDK, an HTTP client, a web framework or a database driver. Reading it first shows what the program *means*; the other layers only connect it to the world.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/__init__.py` | 2 non-blank lines |
| `src/cited_answers/domain/__init__.py` | 1 non-blank lines |
| `src/cited_answers/domain/answering.py` | 80 non-blank lines |
| `src/cited_answers/domain/chunking.py` | 58 non-blank lines |
| `src/cited_answers/domain/errors.py` | 14 non-blank lines |
| `src/cited_answers/domain/evaluation.py` | 83 non-blank lines |
| `src/cited_answers/domain/llm.py` | 114 non-blank lines |
| `src/cited_answers/domain/pages.py` | 59 non-blank lines |
| `src/cited_answers/domain/prompts.py` | 12 non-blank lines |
| `src/cited_answers/domain/retrieval.py` | 109 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/cited_answers/__init__.py`

In its own words: "A question-answering service over a help center: hybrid retrieval, cited answers or a fixed refusal."

2 non-blank lines.

`src/cited_answers/__init__.py`, lines 1 to 3:

```python
"""A question-answering service over a help center: hybrid retrieval, cited answers or a fixed refusal."""

__version__ = "0.1.0"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `0.1.0` under the name `__version__`.

### `src/cited_answers/domain/__init__.py`

In its own words: "Pure domain logic. Depends on nothing outside the standard library."

1 non-blank lines.

`src/cited_answers/domain/__init__.py`, lines 1 to 1:

```python
"""Pure domain logic. Depends on nothing outside the standard library."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/cited_answers/domain/answering.py`

In its own words: "Answer rules: the fixed refusal, the citation check and the tuning of the refusal threshold."

80 non-blank lines; it defines `Status`, `Reason`, `CitationCheck`, `extract_citations`, `check_citations`, `is_model_refusal`, `ThresholdChoice`, `tune_threshold`.

`src/cited_answers/domain/answering.py`, lines 1 to 14:

```python
"""Answer rules: the fixed refusal, the citation check and the tuning of the refusal threshold."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from cited_answers.domain.chunking import Chunk

REFUSAL_MESSAGE = "I don't have information about that in our help center."
_CITATION = re.compile(r"\[([^\[\]\s]+)\]")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Stores the text `I don't have information about that in our help...` under the name `REFUSAL_MESSAGE`.
- Stores the result of calling `re.compile` under the name `_CITATION`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/domain/answering.py`, lines 17 to 28:

```python
class Status(StrEnum):
    """What the reader gets: a cited answer or the fixed refusal."""

    ANSWERED = "answered"
    REFUSED = "refused"


class Reason(StrEnum):
    """Why a question was refused (or `none` when it was answered)."""

    NONE = "none"
    BELOW_THRESHOLD = "below_threshold"
```

- Defines the class `Status`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "What the reader gets: a cited answer or the fixed refusal."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `answered` under the name `ANSWERED`.
- Stores the text `refused` under the name `REFUSED`.
- Defines the class `Reason`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Why a question was refused (or `none` when it was answered)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `none` under the name `NONE`.
- Stores the text `below_threshold` under the name `BELOW_THRESHOLD`.

`src/cited_answers/domain/answering.py`, lines 29 to 40:

```python
    MODEL_REFUSED = "model_refused"
    NO_CITATION = "no_citation"
    CITATION_NOT_RETRIEVED = "citation_not_retrieved"


@dataclass(frozen=True, slots=True)
class CitationCheck:
    """The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved."""

    ok: bool
    cited: tuple[str, ...]
    reason: Reason
```

- Stores the text `model_refused` under the name `MODEL_REFUSED`.
- Stores the text `no_citation` under the name `NO_CITATION`.
- Stores the text `citation_not_retrieved` under the name `CITATION_NOT_RETRIEVED`.
- Defines the class `CitationCheck`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `ok` as true or false; it has no default, so a value must be given when the object is made.
- Declares `cited` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `reason` as the project type `Reason`; it has no default, so a value must be given when the object is made.

`src/cited_answers/domain/answering.py`, lines 43 to 51:

```python
def extract_citations(text: str) -> list[str]:
    """Every `[id]` in the text, in order of first appearance, without repeats."""
    seen: dict[str, None] = {}
    for match in _CITATION.finditer(text):
        seen.setdefault(match.group(1), None)
    return list(seen)


def check_citations(text: str, retrieved: Sequence[Chunk]) -> CitationCheck:
```

- Defines the function `extract_citations`. It returns a list of text. The author's own description: "Every `[id]` in the text, in order of first appearance, without repeats."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `seen` as a dictionary from text to nothing (None) and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `_CITATION.finditer(text)`; `match` names the current item.
  - `.finditer(...)` yields every match of a regular expression.
- Calls `.setdefault(...)` reads a dictionary entry, creating it with a default when missing with 2 argument(s); the result is not kept.
  - `.setdefault(...)` reads a dictionary entry, creating it with a default when missing.
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
- Defines the function `check_citations`. It returns the project type `CitationCheck`. The author's own description: "An answer must cite at least one chunk, and only chunks that were retrieved for this request."
- Its parameters:
    - `text` holds text.
    - `retrieved` holds anything that behaves like a list of the project type `Chunk`.

`src/cited_answers/domain/answering.py`, lines 52 to 65:

```python
    """An answer must cite at least one chunk, and only chunks that were retrieved for this request.

    A citation that names a page instead of a chunk (`p-return-window`) is read as that page's chunk when exactly one
    chunk of the page was retrieved. Anything else that is not a retrieved id fails the check.
    """
    known = {chunk.id for chunk in retrieved}
    by_page: dict[str, list[str]] = {}
    for chunk in retrieved:
        by_page.setdefault(chunk.page_id, []).append(chunk.id)
    cited = extract_citations(text)
    if not cited:
        return CitationCheck(False, (), Reason.NO_CITATION)
    normalized: list[str] = []
    bad: list[str] = []
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a set built by looping under the name `known`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Declares `by_page` as a dictionary from text to a list of text and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `retrieved`; `chunk` names the current item.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.setdefault(...)` reads a dictionary entry, creating it with a default when missing.
- Stores the result of calling `extract_citations` under the name `cited`.
  - `extract_citations`, a function of this file (Every `[id]` in the text, in order of first appearance, without repeats.).
- Decision: the indented lines below run only when `not cited` is true.
  - `not` flips true and false.
- Ends the function and gives back the result of calling `CitationCheck` to the caller.
  - `CitationCheck`, a class of this project (The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved.).
- Declares `normalized` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `bad` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/domain/answering.py`, lines 66 to 79:

```python
    for item in cited:
        if item in known:
            normalized.append(item)
        elif len(by_page.get(item, [])) == 1:
            normalized.append(by_page[item][0])
        else:
            bad.append(item)
    if bad:
        return CitationCheck(False, tuple(cited), Reason.CITATION_NOT_RETRIEVED)
    return CitationCheck(True, tuple(dict.fromkeys(normalized)), Reason.NONE)


def is_model_refusal(text: str) -> bool:
    """True when the model answered with the fixed refusal message (it may add a trailing citation or spacing)."""
```

- Loop: the indented lines below run once for each item of `cited`; `item` names the current item.
- Decision: the indented lines below run only when `item in known` is true.
  - `in` means is contained in.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `len(by_page.get(item, [])) == 1` is true.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `bad` is true.
- Ends the function and gives back the result of calling `CitationCheck` to the caller.
  - `CitationCheck`, a class of this project (The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
- Ends the function and gives back the result of calling `CitationCheck` to the caller.
  - `CitationCheck`, a class of this project (The ids an answer cites (as chunk ids) and whether they pass: at least one, all of them retrieved.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - The method `fromkeys` of `dict`.
- Defines the function `is_model_refusal`. It returns true or false. The author's own description: "True when the model answered with the fixed refusal message (it may add a trailing citation or spacing)."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/answering.py`, lines 80 to 89:

```python
    return REFUSAL_MESSAGE.lower().rstrip(".") in text.lower()


@dataclass(frozen=True, slots=True)
class ThresholdChoice:
    """A refusal threshold and what it costs: the share of answerable questions it would wrongly refuse."""

    threshold: float
    false_refusal_rate: float
    unanswerable_refused_rate: float
```

- Ends the function and gives back whether `REFUSAL_MESSAGE.lower().rstrip('.') in text.lower()` holds to the caller.
  - `in` means is contained in.
  - `.rstrip(...)` removes spaces from the end of text.
  - `.lower(...)` turns text into lower case.
- Defines the class `ThresholdChoice`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A refusal threshold and what it costs: the share of answerable questions it would wrongly refuse."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `threshold` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `false_refusal_rate` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `unanswerable_refused_rate` as a decimal number; it has no default, so a value must be given when the object is made.

`src/cited_answers/domain/answering.py`, lines 92 to 103:

```python
def tune_threshold(
    answerable: Sequence[float], unanswerable: Sequence[float], max_false_refusal: float = 0.10
) -> ThresholdChoice:
    """The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.

    A question is refused when its best score is below the threshold. Tune on the development set only.
    """
    if not answerable or not unanswerable:
        raise ValueError("tuning needs scores for answerable and for unanswerable questions")
    ordered = sorted(answerable)
    allowed = math.floor(max_false_refusal * len(ordered))
    threshold = math.floor(ordered[allowed] * 1000) / 1000
```

- Defines the function `tune_threshold`. It returns the project type `ThresholdChoice`. The author's own description: "The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions."
- Its parameters:
    - `answerable` holds anything that behaves like a list of a decimal number.
    - `unanswerable` holds anything that behaves like a list of a decimal number.
    - `max_false_refusal` holds a decimal number; if the caller leaves it out it is the number `0.1`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `not answerable or not unanswerable` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Stores the result of calling `sorted` under the name `ordered`.
  - `sorted` returns a new list with the items in order.
- Stores the result of calling `math.floor` under the name `allowed`.
  - `math.floor` rounds down.
  - `*` is multiply.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of `math.floor(ordered[allowed] * 1000) / 1000` under the name `threshold`.
  - `/` is divide.
  - `math.floor` rounds down.
  - `*` is multiply.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/domain/answering.py`, lines 104 to 106:

```python
    false_refusal = sum(score < threshold for score in answerable) / len(answerable)
    refused = sum(score < threshold for score in unanswerable) / len(unanswerable)
    return ThresholdChoice(threshold, false_refusal, refused)
```

- Stores the result of `sum((score < threshold for score in answerable)) / len(an...` under the name `false_refusal`.
  - `/` is divide.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<` means less than.
- Stores the result of `sum((score < threshold for score in unanswerable)) / len(...` under the name `refused`.
  - `/` is divide.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<` means less than.
- Ends the function and gives back the result of calling `ThresholdChoice` to the caller.
  - `ThresholdChoice`, a class of this project (A refusal threshold and what it costs: the share of answerable questions it would wrongly refuse.).

### `src/cited_answers/domain/chunking.py`

In its own words: "Split pages into chunks on their headings, each carrying the metadata a search result needs."

58 non-blank lines; it defines `Chunk`, `estimate_tokens`, `_split_long`, `chunk_page`, `chunk_current_pages`.

`src/cited_answers/domain/chunking.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `re` (standard library) available.
- Brings in `Iterable` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `date` from the standard library module `datetime`.
- Brings in `Page` (One help-center page.), `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.) from the project module `cited_answers.domain.pages`.
- Stores the number `300` under the name `MAX_CHUNK_TOKENS`.
- Stores the number `1.3` under the name `_TOKENS_PER_WORD`.
- Stores the result of calling `re.compile` under the name `_SENTENCE`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/domain/chunking.py`, lines 17 to 26:

```python
@dataclass(frozen=True, slots=True)
class Chunk:
    """A passage a reader can open: the page it came from, its heading path, its date and its status."""

    id: str
    page_id: str
    heading_path: str
    text: str
    updated: date
    status: PageStatus
```

- Defines the class `Chunk`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A passage a reader can open: the page it came from, its heading path, its date and its status."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `page_id` as text; it has no default, so a value must be given when the object is made.
- Declares `heading_path` as text; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `updated` as a calendar date; it has no default, so a value must be given when the object is made.
- Declares `status` as the project type `PageStatus`; it has no default, so a value must be given when the object is made.

`src/cited_answers/domain/chunking.py`, lines 28 to 39:

```python
    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)

    def for_search(self) -> str:
        """The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat."""
        return f"{self.heading_path}. {self.text}"


def estimate_tokens(text: str) -> int:
    """Rough token count for a size limit: words times 1.3."""
    return round(len(text.split()) * _TOKENS_PER_WORD)
```

- Defines the method `tokens`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `estimate_tokens` to the caller.
  - `estimate_tokens`, a function defined in this file or passed in.
- Defines the method `for_search`. It returns text. The author's own description: "The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `estimate_tokens`. It returns a whole number. The author's own description: "Rough token count for a size limit: words times 1.3."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `round` to the caller.
  - `round` rounds a number.
  - `*` is multiply.
  - `len` counts the items in a collection (or the characters in text).
  - `.split(...)` cuts text into a list of pieces at a separator.

`src/cited_answers/domain/chunking.py`, lines 42 to 52:

```python
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
```

- Defines the function `_split_long`. It returns a list of text.
- Its parameters:
    - `text` holds text.
    - `max_tokens` holds a whole number.
- Declares `parts` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `current` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `_SENTENCE.split(text)`; `sentence` names the current item.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Decision: the indented lines below run only when `current and estimate_tokens(' '.join([*current, sentence])) > max_t...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `>` means greater than.
  - `estimate_tokens`, a function of this file (Rough token count for a size limit: words times 1.3.).
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Stores an empty list under the name `current`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `current` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Ends the function and gives back the value named `parts` to the caller.

`src/cited_answers/domain/chunking.py`, lines 55 to 64:

```python
def chunk_page(page: Page, max_tokens: int = MAX_CHUNK_TOKENS) -> list[Chunk]:
    """One chunk per section, split at sentence ends when a section is longer than `max_tokens`.

    A chunk never spans two sections, so it never spans two pages. Ids are `<page id>:<n>`.
    """
    chunks: list[Chunk] = []
    for section in page.sections:
        for text in _split_long(section.text, max_tokens):
            chunks.append(Chunk(f"{page.id}:{len(chunks)}", page.id, section.path, text, page.updated, page.status))
    return chunks
```

- Defines the function `chunk_page`. It returns a list of the project type `Chunk`. The author's own description: "One chunk per section, split at sentence ends when a section is longer than `max_tokens`."
- Its parameters:
    - `page` holds the project type `Page`.
    - `max_tokens` holds a whole number; if the caller leaves it out it is the value named `MAX_CHUNK_TOKENS`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `chunks` as a list of the project type `Chunk` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `page.sections`; `section` names the current item.
- Loop: the indented lines below run once for each item of `_split_long(section.text, max_tokens)`; `text` names the current item.
  - `_split_long`, a function of this file.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `Chunk`, a class of this project (A passage a reader can open: the page it came from, its heading path, its date and its status.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the value named `chunks` to the caller.

`src/cited_answers/domain/chunking.py`, lines 67 to 76:

```python
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
```

- Defines the function `chunk_current_pages`. It returns a fixed list of a list of the project type `Chunk`, a list of text. The author's own description: "Chunk every current page; return the chunks and the ids of the retired pages that were left out."
- Its parameters:
    - `pages` holds anything you can loop over of the project type `Page`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `chunks` as a list of the project type `Chunk` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `skipped` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `pages`; `page` names the current item.
- Decision: the indented lines below run only when `page.status is PageStatus.CURRENT` is true.
  - `is` means the very same object.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - `chunk_page`, a function of this file (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.).
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back a tuple of 2 item(s) to the caller.

### `src/cited_answers/domain/errors.py`

In its own words: "Named errors. Callers catch these, never a vendor SDK's exception types."

14 non-blank lines; it defines `DomainError`, `ModelError`, `TransientModelError`, `PermanentModelError`, `RecordingMissing`, `UnsupportedParameter`.

`src/cited_answers/domain/errors.py`, lines 1 to 14:

```python
"""Named errors. Callers catch these, never a vendor SDK's exception types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error this package raises on purpose."""


class ModelError(DomainError):
    """A model call failed."""


class TransientModelError(ModelError):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Defines the class `DomainError`. It builds on `Exception` (the base of ordinary errors). The author's own description: "Base class for every error this package raises on purpose."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `ModelError`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "A model call failed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `TransientModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."

`src/cited_answers/domain/errors.py`, lines 15 to 27:

```python
    """The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."""


class PermanentModelError(ModelError):
    """Repeating the call cannot help: a bad request, a bad key, a refusal to parse."""


class RecordingMissing(PermanentModelError):
    """The recorded adapter has no response for this request. Re-record with `make record`."""


class UnsupportedParameter(PermanentModelError):
    """The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `PermanentModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "Repeating the call cannot help: a bad request, a bad key, a refusal to parse."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `RecordingMissing`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The recorded adapter has no response for this request. Re-record with `make record`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `UnsupportedParameter`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/cited_answers/domain/evaluation.py`

In its own words: "Questions, the two grades (retrieval and answer), intervals and the split of misses by stage."

83 non-blank lines; it defines `InvalidQuestions`, `QuestionType`, `Question`, `validate_questions`, `wilson_interval`, `Rate`, `hit_at_k`, `parse_verdict`, `Stage`, `classify_miss`, `agreement`.

`src/cited_answers/domain/evaluation.py`, lines 1 to 12:

```python
"""Questions, the two grades (retrieval and answer), intervals and the split of misses by stage."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from cited_answers.domain.errors import DomainError

_VERDICT = re.compile(r"\b(incorrect|correct)\b", re.IGNORECASE)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `cited_answers.domain.errors`.
- Stores the result of calling `re.compile` under the name `_VERDICT`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/domain/evaluation.py`, lines 15 to 24:

```python
class InvalidQuestions(DomainError):
    """The question file breaks a rule of the lesson."""


class QuestionType(StrEnum):
    """Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable."""

    ANSWERABLE = "answerable"
    EXACT = "exact"
    UNANSWERABLE = "unanswerable"
```

- Defines the class `InvalidQuestions`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The question file breaks a rule of the lesson."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `QuestionType`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `answerable` under the name `ANSWERABLE`.
- Stores the text `exact` under the name `EXACT`.
- Stores the text `unanswerable` under the name `UNANSWERABLE`.

`src/cited_answers/domain/evaluation.py`, lines 27 to 36:

```python
@dataclass(frozen=True, slots=True)
class Question:
    """One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable."""

    id: str
    type: QuestionType
    question: str
    gold_page: str | None
    fact: str | None
    near_miss: bool
```

- Defines the class `Question`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `type` as the project type `QuestionType`; it has no default, so a value must be given when the object is made.
- Declares `question` as text; it has no default, so a value must be given when the object is made.
- Declares `gold_page` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `fact` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `near_miss` as true or false; it has no default, so a value must be given when the object is made.

`src/cited_answers/domain/evaluation.py`, lines 38 to 50:

```python
    @property
    def has_gold(self) -> bool:
        return self.type is not QuestionType.UNANSWERABLE


def validate_questions(questions: list[Question], answerable: int, exact: int, unanswerable: int) -> None:
    """Check a question set has the lesson's mix and that every gradable question has a gold page and a fact."""
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise InvalidQuestions("question ids must be unique")
    counts = {t: sum(q.type is t for q in questions) for t in QuestionType}
    want = {QuestionType.ANSWERABLE: answerable, QuestionType.EXACT: exact, QuestionType.UNANSWERABLE: unanswerable}
    if counts != want:
```

- Defines the method `has_gold`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back whether `self.type is not QuestionType.UNANSWERABLE` holds to the caller.
  - `is not` means not the same object.
- Defines the function `validate_questions`. It returns nothing (None). The author's own description: "Check a question set has the lesson's mix and that every gradable question has a gold page and a fact."
- Its parameters:
    - `questions` holds a list of the project type `Question`.
    - `answerable` holds a whole number.
    - `exact` holds a whole number.
    - `unanswerable` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Decision: the indented lines below run only when `len(set(ids)) != len(ids)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
  - `set` makes a set: a collection with no repeated items.
- Raises an error: the result of calling `InvalidQuestions`. Execution jumps out to the nearest matching `except`.
  - `InvalidQuestions`, a class of this project (The question file breaks a rule of the lesson.).
- Stores a dictionary built by looping under the name `counts`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `sum` adds up all the numbers.
  - `is` means the very same object.
- Stores a dictionary with 3 entries under the name `want`.
- Decision: the indented lines below run only when `counts != want` is true.
  - `!=` means not equal.

`src/cited_answers/domain/evaluation.py`, lines 51 to 64:

```python
        raise InvalidQuestions(f"expected {dict(want)}, found {dict(counts)}")
    for question in questions:
        if question.has_gold and not (question.gold_page and question.fact):
            raise InvalidQuestions(f"{question.id}: a gradable question needs a gold page and a fact")


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not."""
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    denominator = 1 + z**2 / trials
    center = p + z**2 / (2 * trials)
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2))
```

- Raises an error: the result of calling `InvalidQuestions`. Execution jumps out to the nearest matching `except`.
  - `InvalidQuestions`, a class of this project (The question file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `dict` makes a dictionary (a copy when given one).
- Loop: the indented lines below run once for each item of `questions`; `question` names the current item.
- Decision: the indented lines below run only when `question.has_gold and (not (question.gold_page and question.fact))` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
- Raises an error: the result of calling `InvalidQuestions`. Execution jumps out to the nearest matching `except`.
  - `InvalidQuestions`, a class of this project (The question file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `wilson_interval`. It returns a fixed list of a decimal number, a decimal number. The author's own description: "The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not."
- Its parameters:
    - `successes` holds a whole number.
    - `trials` holds a whole number.
    - `z` holds a decimal number; if the caller leaves it out it is the number `1.96`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `trials == 0` is true.
  - `==` means equal.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Stores the result of `successes / trials` under the name `p`.
  - `/` is divide.
- Stores the result of `1 + z ** 2 / trials` under the name `denominator`.
  - `+` is add.
  - `/` is divide.
  - `**` is power.
- Stores the result of `p + z ** 2 / (2 * trials)` under the name `center`.
  - `+` is add.
  - `/` is divide.
  - `**` is power.
  - `*` is multiply.
- Stores the result of `z * math.sqrt(p * (1 - p) / trials + z ** 2 / (4 * trials...` under the name `half`.
  - `*` is multiply.
  - `math.sqrt` square root.
  - `+` is add.
  - `/` is divide.
  - `**` is power.
  - `-` is subtract.

`src/cited_answers/domain/evaluation.py`, lines 65 to 77:

```python
    return (max(0.0, (center - half) / denominator), min(1.0, (center + half) / denominator))


@dataclass(frozen=True, slots=True)
class Rate:
    """A count out of a total with its Wilson interval."""

    successes: int
    trials: int

    @property
    def value(self) -> float:
        return self.successes / self.trials if self.trials else 0.0
```

- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `max` picks the largest value.
  - `min` picks the smallest value.
  - `/` is divide.
  - `-` is subtract.
  - `+` is add.
- Defines the class `Rate`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A count out of a total with its Wilson interval."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `successes` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `trials` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `value`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.

`src/cited_answers/domain/evaluation.py`, lines 79 to 90:

```python
    @property
    def interval(self) -> tuple[float, float]:
        return wilson_interval(self.successes, self.trials)

    def __str__(self) -> str:
        low, high = self.interval
        return f"{self.successes}/{self.trials} = {self.value:.2f} (Wilson {low:.2f}-{high:.2f})"


def hit_at_k(retrieved_pages: list[str], gold_page: str | None, k: int = 5) -> bool:
    """True when a chunk of the gold page is among the first `k` retrieved."""
    return gold_page is not None and gold_page in retrieved_pages[:k]
```

- Defines the method `interval`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a fixed list of a decimal number, a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `wilson_interval` to the caller.
  - `wilson_interval`, a function defined in this file or passed in.
- Defines the method `__str__`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the attribute `interval` of this object under the name `(low, high)`.
- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `hit_at_k`. It returns true or false. The author's own description: "True when a chunk of the gold page is among the first `k` retrieved."
- Its parameters:
    - `retrieved_pages` holds a list of text.
    - `gold_page` holds text, or nothing (None).
    - `k` holds a whole number; if the caller leaves it out it is the number `5`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of combining conditions: `gold_page is not None and gold_page in retrieved_pages[:k]` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
  - `in` means is contained in.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.

`src/cited_answers/domain/evaluation.py`, lines 93 to 103:

```python
def parse_verdict(text: str) -> bool | None:
    """Read a judge's reply: True for correct, False for incorrect, None when it says neither."""
    match = _VERDICT.search(text)
    return None if match is None else match.group(1).lower() == "correct"


class Stage(StrEnum):
    """Where a wrong answer went wrong."""

    RETRIEVAL = "retrieval miss"
    GENERATION = "generation miss"
```

- Defines the function `parse_verdict`. It returns true or false, or nothing (None). The author's own description: "Read a judge's reply: True for correct, False for incorrect, None when it says neither."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `_VERDICT.search` under the name `match`.
  - `.search(...)` looks for a regular expression anywhere in text.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
  - `==` means equal.
  - `.lower(...)` turns text into lower case.
  - `.group(...)` reads a captured part of a regular-expression match.
- Defines the class `Stage`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Where a wrong answer went wrong."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `retrieval miss` under the name `RETRIEVAL`.
- Stores the text `generation miss` under the name `GENERATION`.

`src/cited_answers/domain/evaluation.py`, lines 106 to 117:

```python
def classify_miss(hit: bool, correct: bool) -> Stage | None:
    """A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss."""
    if correct:
        return None
    return Stage.GENERATION if hit else Stage.RETRIEVAL


def agreement(judge: list[bool], human: list[bool]) -> tuple[int, int]:
    """How many verdicts the judge shares with the hand grades, and how many were compared."""
    if len(judge) != len(human):
        raise ValueError("judge and hand grades must have the same length")
    return sum(a == b for a, b in zip(judge, human, strict=True)), len(judge)
```

- Defines the function `classify_miss`. It returns the project type `Stage`, or nothing (None). The author's own description: "A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss."
- Its parameters:
    - `hit` holds true or false.
    - `correct` holds true or false.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `correct` is true.
- Ends the function and gives back nothing (`None`) to the caller.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Defines the function `agreement`. It returns a fixed list of a whole number, a whole number. The author's own description: "How many verdicts the judge shares with the hand grades, and how many were compared."
- Its parameters:
    - `judge` holds a list of true or false.
    - `human` holds a list of true or false.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `len(judge) != len(human)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - `zip` walks several collections side by side, item by item.

### `src/cited_answers/domain/llm.py`

In its own words: "Vendor-neutral value objects for one chat-model call. No SDK is imported here."

114 non-blank lines; it defines `Role`, `StopReason`, `ToolSpec`, `ToolCall`, `ChatMessage`, `Usage`, `ChatRequest`, `ChatResponse`.

`src/cited_answers/domain/llm.py`, lines 1 to 14:

```python
"""Vendor-neutral value objects for one chat-model call. No SDK is imported here."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Who wrote a message."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass`, `field` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Defines the class `Role`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Who wrote a message."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/llm.py`, lines 16 to 28:

```python
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StopReason(StrEnum):
    """Why the model stopped writing."""

    END = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    REFUSAL = "refusal"
    OTHER = "other"
```

- Stores the text `user` under the name `USER`.
- Stores the text `assistant` under the name `ASSISTANT`.
- Stores the text `tool` under the name `TOOL`.
- Defines the class `StopReason`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Why the model stopped writing."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `stop` under the name `END`.
- Stores the text `length` under the name `LENGTH`.
- Stores the text `tool_calls` under the name `TOOL_CALLS`.
- Stores the text `refusal` under the name `REFUSAL`.
- Stores the text `other` under the name `OTHER`.

`src/cited_answers/domain/llm.py`, lines 31 to 42:

```python
@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool the model may call: a name, a description and a JSON Schema for the arguments."""

    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call the model asked for."""
```

- Defines the class `ToolSpec`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool the model may call: a name, a description and a JSON Schema for the arguments."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `description` as text; it has no default, so a value must be given when the object is made.
- Declares `parameters` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ToolCall`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool call the model asked for."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/llm.py`, lines 44 to 56:

```python
    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One message of a conversation. A tool result carries the id of the call it answers."""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
```

- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `arguments` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ChatMessage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One message of a conversation. A tool result carries the id of the call it answers."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `role` as the project type `Role`; it has no default, so a value must be given when the object is made.
- Declares `content` as text and sets it to empty text.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tool_call_id` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/cited_answers/domain/llm.py`, lines 58 to 68:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)


@dataclass(frozen=True, slots=True)
class Usage:
    """Tokens the provider billed for one call, read from its usage block, never recomputed."""

    input_tokens: int
    output_tokens: int
```

- Defines the method `user`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatMessage`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `content` holds text.
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
- Defines the class `Usage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Tokens the provider billed for one call, read from its usage block, never recomputed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.

`src/cited_answers/domain/llm.py`, lines 71 to 82:

```python
@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Everything that defines one call.

    `tag` names the call for recordings and logs (for example `p01/t07/2`); it is never sent to a vendor.
    `model` overrides the adapter's default model and is not part of the recording key.
    """

    messages: tuple[ChatMessage, ...]
    system: str | None = None
    max_output_tokens: int = 1024
    temperature: float | None = None
```

- Defines the class `ChatRequest`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything that defines one call."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a fixed list of the project type `ChatMessage` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `system` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `max_output_tokens` as a whole number and sets it to the number `1024`.
- Declares `temperature` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/cited_answers/domain/llm.py`, lines 83 to 90:

```python
    top_p: float | None = None
    response_schema: Mapping[str, Any] | None = None
    tools: tuple[ToolSpec, ...] = ()
    tag: str = ""
    model: str | None = None

    def fingerprint(self) -> str:
        """A stable hash of the request, used to find its recording. The model name is excluded."""
```

- Declares `top_p` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `response_schema` as anything that behaves like a dictionary from text to any value, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tools` as a fixed list of the project type `ToolSpec` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tag` as text and sets it to empty text.
- Declares `model` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the method `fingerprint`. It returns text. The author's own description: "A stable hash of the request, used to find its recording. The model name is excluded."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/llm.py`, lines 91 to 108:

```python
        body = {
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_calls": [[c.id, c.name, dict(c.arguments)] for c in m.tool_calls],
                    "tool_call_id": m.tool_call_id,
                }
                for m in self.messages
            ],
            "system": self.system,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_schema": self.response_schema,
            "tools": [[t.name, t.description, dict(t.parameters)] for t in self.tools],
            "tag": self.tag,
        }
```

- Stores a dictionary with 8 entries under the name `body`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).

`src/cited_answers/domain/llm.py`, lines 109 to 122:

```python
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """What came back: the text or the tool calls, why it stopped, the billed usage and the latency."""

    text: str
    stop_reason: StopReason
    usage: Usage
    latency_seconds: float
    model: str
    tool_calls: tuple[ToolCall, ...] = field(default=())
```

- Stores the result of calling `json.dumps` under the name `canonical`.
  - `json.dumps` turns Python data into JSON text.
- Ends the function and gives back the result of calling `hashlib.sha256(canonical.encode('utf-8')).hexdi...` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Defines the class `ChatResponse`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What came back: the text or the tool calls, why it stopped, the billed usage and the latency."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `stop_reason` as the project type `StopReason`; it has no default, so a value must be given when the object is made.
- Declares `usage` as the project type `Usage`; it has no default, so a value must be given when the object is made.
- Declares `latency_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to the result of calling `field`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `field` from the standard library module `dataclasses`.

`src/cited_answers/domain/llm.py`, lines 124 to 135:

```python
    def to_json(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "stop_reason": self.stop_reason.value,
            "usage": {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens},
            "latency_seconds": self.latency_seconds,
            "model": self.model,
            "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in self.tool_calls],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ChatResponse:
```

- Defines the method `to_json`. It returns a dictionary from text to any value.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a dictionary with 6 entries to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `from_json`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatResponse`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `data` holds anything that behaves like a dictionary from text to any value.

`src/cited_answers/domain/llm.py`, lines 136 to 145:

```python
        return cls(
            text=str(data["text"]),
            stop_reason=StopReason(data["stop_reason"]),
            usage=Usage(int(data["usage"]["input_tokens"]), int(data["usage"]["output_tokens"])),
            latency_seconds=float(data["latency_seconds"]),
            model=str(data["model"]),
            tool_calls=tuple(
                ToolCall(str(c["id"]), str(c["name"]), dict(c["arguments"])) for c in data.get("tool_calls", [])
            ),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `str` turns a value into text.
  - `StopReason`, a class of this project (Why the model stopped writing.).
  - `Usage`, a class of this project (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `float` turns a value into a decimal number.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `int` turns a value into a whole number.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall`, a class of this project (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/cited_answers/domain/pages.py`

In its own words: "Help-center pages: a title, an updated date, a status and sections under headings."

59 non-blank lines; it defines `InvalidPage`, `PageStatus`, `Section`, `Page`, `parse_page`, `_sections`.

`src/cited_answers/domain/pages.py`, lines 1 to 13:

```python
"""Help-center pages: a title, an updated date, a status and sections under headings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from cited_answers.domain.errors import DomainError

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_HEADING = re.compile(r"^(#{1,3}) +(.+?) *$", re.MULTILINE)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `re` (standard library) available.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `date` from the standard library module `datetime`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `cited_answers.domain.errors`.
- Stores the result of calling `re.compile` under the name `_FRONT_MATTER`.
  - `re.compile` prepares a regular expression.
- Stores the result of calling `re.compile` under the name `_HEADING`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/domain/pages.py`, lines 16 to 24:

```python
class InvalidPage(DomainError):
    """A page file is missing its front matter or one of its fields."""


class PageStatus(StrEnum):
    """Only `current` pages are indexed. A `retired` page may contradict a current one."""

    CURRENT = "current"
    RETIRED = "retired"
```

- Defines the class `InvalidPage`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "A page file is missing its front matter or one of its fields."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `PageStatus`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Only `current` pages are indexed. A `retired` page may contradict a current one."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `current` under the name `CURRENT`.
- Stores the text `retired` under the name `RETIRED`.

`src/cited_answers/domain/pages.py`, lines 27 to 37:

```python
@dataclass(frozen=True, slots=True)
class Section:
    """Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title."""

    path: str
    text: str


@dataclass(frozen=True, slots=True)
class Page:
    """One help-center page."""
```

- Defines the class `Section`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `path` as text; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Defines the class `Page`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One help-center page."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/pages.py`, lines 39 to 51:

```python
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
```

- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `title` as text; it has no default, so a value must be given when the object is made.
- Declares `updated` as a calendar date; it has no default, so a value must be given when the object is made.
- Declares `status` as the project type `PageStatus`; it has no default, so a value must be given when the object is made.
- Declares `sections` as a fixed list of the project type `Section` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `parse_page`. It returns the project type `Page`. The author's own description: "Parse a page file: front matter (id, title, updated, status) and a body split on its headings."
- Its parameters:
    - `source` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `_FRONT_MATTER.match` under the name `match`.
  - `.match(...)` tries a regular expression at the start of text.
- Decision: the indented lines below run only when `not match` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `InvalidPage`. Execution jumps out to the nearest matching `except`.
  - `InvalidPage`, a class of this project (A page file is missing its front matter or one of its fields.).
- Stores the result of calling `dict` under the name `header`.
  - `dict` makes a dictionary (a copy when given one).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `.splitlines(...)` cuts text into a list of lines.
  - `in` means is contained in.
  - `.group(...)` reads a captured part of a regular-expression match.

`src/cited_answers/domain/pages.py`, lines 52 to 65:

```python
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
```

- Stores a dictionary built by looping under the name `values`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Loop: the indented lines below run once for each item of `('id', 'title', 'updated', 'status')`; `name` names the current item.
- Decision: the indented lines below run only when `not values.get(name)` is true.
  - `not` flips true and false.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `InvalidPage`. Execution jumps out to the nearest matching `except`.
  - `InvalidPage`, a class of this project (A page file is missing its front matter or one of its fields.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `PageStatus` under the name `status`.
  - `PageStatus`, a class of this project (Only `current` pages are indexed. A `retired` page may contradict a current one.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `date.fromisoformat` under the name `updated`.
  - `date.fromisoformat` reads a date from ISO text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `InvalidPage`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidPage`, a class of this project (A page file is missing its front matter or one of its fields.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `Page` to the caller.
  - `Page`, a class of this project (One help-center page.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_sections`, a function of this file.
  - `.group(...)` reads a captured part of a regular-expression match.
- Defines the function `_sections`. It returns a fixed list of the project type `Section` (any length).
- Its parameters:
    - `title` holds text.
    - `body` holds text.
- Stores the result of calling `list` under the name `headings`.
  - `list` makes a list (a copy when given a collection).
  - `.finditer(...)` yields every match of a regular expression.

`src/cited_answers/domain/pages.py`, lines 66 to 78:

```python
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
```

- Declares `sections` as a list of the project type `Section` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `stack` as a list of a fixed list of a whole number, text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `enumerate(headings)`; `(index, heading)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Stores a tuple of 2 item(s) under the name `(level, name)`.
  - `len` counts the items in a collection (or the characters in text).
  - `.group(...)` reads a captured part of a regular-expression match.
- Stores the result of `[(lv, nm) for lv, nm in stack if lv < level] + [(level, n...` under the name `stack`.
  - `+` is add.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<` means less than.
- Stores one of two values, chosen by a condition under the name `end`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `<` means less than.
  - `.start(...)` starts a thread or process.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `body[heading.end():end].strip` under the name `text`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - The method `end` of `heading`.
- Decision: the indented lines below run only when `text` is true.
- Stores a list built by looping under the name `names`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `!=` means not equal.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `Section`, a class of this project (Text under one heading. `path` is the headings above it joined with ' > ', starting with the page title.).
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Decision: the indented lines below run only when `not sections` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `InvalidPage`. Execution jumps out to the nearest matching `except`.
  - `InvalidPage`, a class of this project (A page file is missing its front matter or one of its fields.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `tuple` to the caller.
  - `tuple` makes a tuple: a fixed list that cannot be changed.

### `src/cited_answers/domain/prompts.py`

In its own words: "A prompt file: its name, its version line and its text."

12 non-blank lines; it defines `PromptNotFound`, `Prompt`.

`src/cited_answers/domain/prompts.py`, lines 1 to 11:

```python
"""A prompt file: its name, its version line and its text."""

from __future__ import annotations

from dataclasses import dataclass

from cited_answers.domain.errors import DomainError


class PromptNotFound(DomainError):
    """No prompt file for that name and version, or the file's version line does not match."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `cited_answers.domain.errors`.
- Defines the class `PromptNotFound`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "No prompt file for that name and version, or the file's version line does not match."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/prompts.py`, lines 14 to 20:

```python
@dataclass(frozen=True, slots=True)
class Prompt:
    """A prompt as sent to the model, with the version that produced a given result."""

    name: str
    version: str
    text: str
```

- Defines the class `Prompt`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A prompt as sent to the model, with the version that produced a given result."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `version` as text; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.

### `src/cited_answers/domain/retrieval.py`

In its own words: "Keyword search (BM25), vector similarity and the fusion of ranked lists."

109 non-blank lines; it defines `tokenize`, `whitespace_tokenize`, `Bm25Index`, `cosine`, `reciprocal_rank_fusion`.

`src/cited_answers/domain/retrieval.py`, lines 1 to 12:

```python
"""Keyword search (BM25), vector similarity and the fusion of ranked lists."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Sequence

from cited_answers.domain.chunking import Chunk

_WORD = re.compile(r"[a-z0-9]+")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Counter` from the standard library module `collections`.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Stores the result of calling `re.compile` under the name `_WORD`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/domain/retrieval.py`, lines 13 to 61:

```python
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
```

- Stores the result of calling `frozenset` under the name `STOPWORDS`.
  - `frozenset` makes a set that cannot be changed.

`src/cited_answers/domain/retrieval.py`, lines 64 to 75:

```python
def tokenize(text: str) -> list[str]:
    """Lowercase words split on anything that is not a letter or a digit, so `PR-E2091` becomes `pr` and `e2091`."""
    return [word for word in _WORD.findall(text.lower()) if word not in STOPWORDS]


def whitespace_tokenize(text: str) -> list[str]:
    """The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it."""
    return [word.strip(".,;:!?()\"'") for word in text.lower().split() if word.strip(".,;:!?()\"'") not in STOPWORDS]


class Bm25Index:
    """Okapi BM25 over chunk text (heading path included)."""
```

- Defines the function `tokenize`. It returns a list of text. The author's own description: "Lowercase words split on anything that is not a letter or a digit, so `PR-E2091` becomes `pr` and `e2091`."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.findall(...)` lists every match of a regular expression.
  - `not in` means is not contained in.
  - `.lower(...)` turns text into lower case.
- Defines the function `whitespace_tokenize`. It returns a list of text. The author's own description: "The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `not in` means is not contained in.
  - `.lower(...)` turns text into lower case.
- Defines the class `Bm25Index`. The author's own description: "Okapi BM25 over chunk text (heading path included)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/domain/retrieval.py`, lines 77 to 89:

```python
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
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `chunks` holds anything that behaves like a list of the project type `Chunk`.
    - `k1` holds a decimal number; if the caller leaves it out it is the number `1.5`.
    - `b` holds a decimal number; if the caller leaves it out it is the number `0.75`.
    - `tokenizer` holds a function; if the caller leaves it out it is the value named `tokenize`.
- Stores a list built by looping under the name `self._ids` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the value named `tokenizer` under the name `self._tokenizer` (as an attribute of this object, so other methods can use it).
- Stores a tuple of 2 item(s) under the name `(self._k1, self._b)`.
- Stores a list built by looping under the name `self._documents` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `Counter` from the standard library module `collections`.
  - `tokenizer`, a function defined in this file or passed in.
  - The method `for_search` of the project's `Chunk` (The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat.).
- Stores a list built by looping under the name `self._lengths` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `sum` adds up all the numbers.
  - `.values(...)` gives the values of a dictionary.
- Stores one of two values, chosen by a condition under the name `self._average` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).

`src/cited_answers/domain/retrieval.py`, lines 90 to 103:

```python
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
```

- Declares `frequency` as Counter of text and sets it to the result of calling `Counter`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `Counter` from the standard library module `collections`.
- Loop: the indented lines below run once for each item of `self._documents`; `document` names the current item.
- Calls `.update(...)` merges another collection into this one with 1 argument(s); the result is not kept.
  - `.update(...)` merges another collection into this one.
  - `.keys(...)` gives the keys of a dictionary.
- Stores the result of calling `len` under the name `count`.
  - `len` counts the items in a collection (or the characters in text).
- Stores a dictionary built by looping under the name `self._idf` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `math.log` from the standard library module `math`.
  - `+` is add.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `/` is divide.
  - `-` is subtract.
- Defines the method `search`. It returns a list of a fixed list of text, a decimal number. The author's own description: "The `k` best chunk ids with their scores; chunks that share no term with the query are not returned."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `query` holds text.
    - `k` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._tokenizer` under the name `terms`.
  - The method `_tokenizer` of `self`.
- Declares `scored` as a list of a fixed list of text, a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `zip(self._ids, self._documents, self._lengths, strict=True)`; `(chunk_id, document, length)` names the current item.
  - `zip` walks several collections side by side, item by item.
- Stores the number `0.0` under the name `score`.
- Loop: the indented lines below run once for each item of `terms`; `term` names the current item.
- Stores the result of calling `document.get` under the name `tf`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/cited_answers/domain/retrieval.py`, lines 104 to 116:

```python
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
```

- Decision: the indented lines below run only when `tf` is true.
- Stores the result of `tf + self._k1 * (1 - self._b + self._b * length / self._a...` under the name `norm`.
  - `+` is add.
  - `*` is multiply.
  - `-` is subtract.
  - `/` is divide.
- Updates `score` in place: `+=` applies `+` with the result of `self._idf[term] * tf * (self._k1 + 1) / norm` and stores the result back.
  - `/` is divide.
  - `*` is multiply.
  - `+` is add.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `score > 0` is true.
  - `>` means greater than.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the part of `sorted(scored, key=lambda i...` picked by `:k` to the caller.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `sorted` returns a new list with the items in order.
  - `lambda args: expression` is a small unnamed function written inline.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `cosine`. It returns a decimal number. The author's own description: "Cosine similarity of two vectors (0.0 if either is all zeros)."
- Its parameters:
    - `a` holds anything that behaves like a list of a decimal number.
    - `b` holds anything that behaves like a list of a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `sum` under the name `dot`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `*` is multiply.
  - `zip` walks several collections side by side, item by item.
- Stores the result of `math.sqrt(sum((x * x for x in a))) * math.sqrt(sum((y * y...` under the name `norm`.
  - `*` is multiply.
  - `math.sqrt` square root.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.

`src/cited_answers/domain/retrieval.py`, lines 119 to 125:

```python
def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], k: int = 60, top: int = 5) -> list[tuple[str, float]]:
    """Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top]
```

- Defines the function `reciprocal_rank_fusion`. It returns a list of a fixed list of text, a decimal number. The author's own description: "Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up."
- Its parameters:
    - `rankings` holds anything that behaves like a list of anything that behaves like a list of text.
    - `k` holds a whole number; if the caller leaves it out it is the number `60`.
    - `top` holds a whole number; if the caller leaves it out it is the number `5`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `scores` as a dictionary from text to a decimal number and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `rankings`; `ranking` names the current item.
- Loop: the indented lines below run once for each item of `enumerate(ranking, start=1)`; `(rank, chunk_id)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Stores the result of `scores.get(chunk_id, 0.0) + 1.0 / (k + rank)` under the name `scores[chunk_id]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `+` is add.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `/` is divide.
- Ends the function and gives back the part of `sorted(scores.items(), key=...` picked by `:top` to the caller.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `sorted` returns a new list with the items in order.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `lambda args: expression` is a small unnamed function written inline.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import cited_answers.__init__; print(cited_answers.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
A question-answering service over a help center: hybrid retrieval, cited answers or a fixed refusal.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/cited_answers/domain').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
answering.py 8
chunking.py 5
errors.py 6
evaluation.py 11
llm.py 8
pages.py 6
prompts.py 2
retrieval.py 5
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

- **Common mistakes with this layer.** Importing a vendor library "just for a type" into the domain (the build fails: see `import-linter.md`), putting input/output (files, network) in a domain function, or letting a domain function read an environment variable. Here the domain takes everything it needs as arguments and returns values.

## Check yourself

1. What is the job of `src/cited_answers/__init__.py`?

   *Answer:* A question-answering service over a help center: hybrid retrieval, cited answers or a fixed refusal.

2. What is the job of `src/cited_answers/domain/__init__.py`?

   *Answer:* Pure domain logic. Depends on nothing outside the standard library.

3. What is the job of `src/cited_answers/domain/answering.py`?

   *Answer:* Answer rules: the fixed refusal, the citation check and the tuning of the refusal threshold.

4. What is the job of `src/cited_answers/domain/chunking.py`?

   *Answer:* Split pages into chunks on their headings, each carrying the metadata a search result needs.

5. What is the job of `src/cited_answers/domain/errors.py`?

   *Answer:* Named errors. Callers catch these, never a vendor SDK's exception types.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
