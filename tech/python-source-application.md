# Python source, the application layer

## What it is

This note walks through every Python file of the `application` layer of `cited_answers`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **application** layer holds the *use cases*: the steps that combine domain objects to do one job (run the meter, answer a question, resume an agent run). It talks to the outside only through *ports*, small interfaces (protocols) that the infrastructure layer implements.

## Why this repository uses it

Because use cases depend on ports and not on real services, the tests can run them with in-memory fakes, and the same use case works with a recorded model, a local model or Claude.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/application/__init__.py` | 1 non-blank lines |
| `src/cited_answers/application/answer.py` | 89 non-blank lines |
| `src/cited_answers/application/evaluate.py` | 92 non-blank lines |
| `src/cited_answers/application/judge.py` | 28 non-blank lines |
| `src/cited_answers/application/ports.py` | 60 non-blank lines |
| `src/cited_answers/application/retrieve.py` | 87 non-blank lines |
| `src/cited_answers/application/threshold.py` | 20 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/cited_answers/application/__init__.py`

In its own words: "Use cases and the ports they need. Depends on the domain only."

1 non-blank lines.

`src/cited_answers/application/__init__.py`, lines 1 to 1:

```python
"""Use cases and the ports they need. Depends on the domain only."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/cited_answers/application/answer.py`

In its own words: "Answer a question from the retrieved chunks, cite every claim, or refuse."

89 non-blank lines; it defines `Answer`, `format_context`, `AnswerService`.

`src/cited_answers/application/answer.py`, lines 1 to 9:

```python
"""Answer a question from the retrieved chunks, cite every claim, or refuse."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from cited_answers.application.ports import ChatModel
from cited_answers.application.retrieve import HybridRetriever, Mode, Retrieval
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `cited_answers.application.ports`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `Mode` (How to find chunks.), `Retrieval` (The chunks found for a question, best first, and how close the best of them is to the question's vector.) from the project module `cited_answers.application.retrieve`.

`src/cited_answers/application/answer.py`, lines 10 to 21:

```python
from cited_answers.domain.answering import (
    REFUSAL_MESSAGE,
    Reason,
    Status,
    check_citations,
    is_model_refusal,
)
from cited_answers.domain.chunking import Chunk
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.domain.prompts import Prompt

_log = logging.getLogger(__name__)
```

- Brings in `REFUSAL_MESSAGE`, `Reason` (Why a question was refused (or `none` when it was answered).), `Status` (What the reader gets: a cited answer or the fixed refusal.), `check_citations` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.), `is_model_refusal` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).) from the project module `cited_answers.domain.answering`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `cited_answers.domain.llm`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `cited_answers.domain.prompts`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.

`src/cited_answers/application/answer.py`, lines 24 to 35:

```python
@dataclass(frozen=True, slots=True)
class Answer:
    """The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text."""

    question_id: str
    status: Status
    text: str
    reason: Reason
    citations: tuple[str, ...]
    retrieval: Retrieval
    raw_text: str
    input_tokens: int
```

- Defines the class `Answer`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `question_id` as text; it has no default, so a value must be given when the object is made.
- Declares `status` as the project type `Status`; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `reason` as the project type `Reason`; it has no default, so a value must be given when the object is made.
- Declares `citations` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `retrieval` as the project type `Retrieval`; it has no default, so a value must be given when the object is made.
- Declares `raw_text` as text; it has no default, so a value must be given when the object is made.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.

`src/cited_answers/application/answer.py`, lines 36 to 49:

```python
    output_tokens: int

    @property
    def refused(self) -> bool:
        return self.status is Status.REFUSED


def format_context(chunks: tuple[Chunk, ...]) -> str:
    """The passages as the model sees them, each under its id in square brackets."""
    return "\n\n".join(f"[{c.id}] {c.heading_path} (updated {c.updated})\n{c.text}" for c in chunks)


class AnswerService:
    """Retrieve, refuse early below the threshold, ask the model, check the citations."""
```

- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `refused`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back whether `self.status is Status.REFUSED` holds to the caller.
  - `is` means the very same object.
- Defines the function `format_context`. It returns text. The author's own description: "The passages as the model sees them, each under its id in square brackets."
- Its parameters:
    - `chunks` holds a fixed list of the project type `Chunk` (any length).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `'\n\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the class `AnswerService`. The author's own description: "Retrieve, refuse early below the threshold, ask the model, check the citations."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/answer.py`, lines 51 to 63:

```python
    def __init__(
        self,
        retriever: HybridRetriever,
        model: ChatModel,
        prompt: Prompt,
        threshold: float,
        max_output_tokens: int = 300,
    ) -> None:
        self._retriever = retriever
        self._model = model
        self._prompt = prompt
        self._threshold = threshold
        self._max_output_tokens = max_output_tokens
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `retriever` holds the project type `HybridRetriever`.
    - `model` holds the project type `ChatModel`.
    - `prompt` holds the project type `Prompt`.
    - `threshold` holds a decimal number.
    - `max_output_tokens` holds a whole number; if the caller leaves it out it is the number `300`.
- Stores the value named `retriever` under the name `self._retriever` (as an attribute of this object, so other methods can use it).
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `prompt` under the name `self._prompt` (as an attribute of this object, so other methods can use it).
- Stores the value named `threshold` under the name `self._threshold` (as an attribute of this object, so other methods can use it).
- Stores the value named `max_output_tokens` under the name `self._max_output_tokens` (as an attribute of this object, so other methods can use it).

`src/cited_answers/application/answer.py`, lines 65 to 76:

```python
    @property
    def threshold(self) -> float:
        return self._threshold

    def retrieve(self, question: str) -> Retrieval:
        """Fused retrieval only (used by the threshold tuning, which needs no model)."""
        return self._retriever.retrieve(question, Mode.FUSED)

    def ask(self, question: str, question_id: str = "q") -> Answer:
        """Answer one question. Below the threshold the model is never called."""
        retrieval = self._retriever.retrieve(question, Mode.FUSED)
        if retrieval.best_similarity < self._threshold:
```

- Defines the method `threshold`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_threshold` of this object to the caller.
- Defines the method `retrieve`. It returns the project type `Retrieval`. The author's own description: "Fused retrieval only (used by the threshold tuning, which needs no model)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `question` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `self._retriever.retrieve` to the caller.
  - The method `retrieve` of `self._retriever`.
- Defines the method `ask`. It returns the project type `Answer`. The author's own description: "Answer one question. Below the threshold the model is never called."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `question` holds text.
    - `question_id` holds text; if the caller leaves it out it is the text `q`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._retriever.retrieve` under the name `retrieval`.
  - The method `retrieve` of `self._retriever`.
- Decision: the indented lines below run only when `retrieval.best_similarity < self._threshold` is true.
  - `<` means less than.

`src/cited_answers/application/answer.py`, lines 77 to 90:

```python
            _log.info(
                "refused before the model",
                extra={"fields": {"question_id": question_id, "score": round(retrieval.best_similarity, 3)}},
            )
            return Answer(question_id, Status.REFUSED, REFUSAL_MESSAGE, Reason.BELOW_THRESHOLD, (), retrieval, "", 0, 0)
        request = ChatRequest(
            messages=(ChatMessage.user(f"Passages:\n\n{format_context(retrieval.chunks)}\n\nQuestion: {question}"),),
            system=self._prompt.text,
            max_output_tokens=self._max_output_tokens,
            temperature=0.0 if self._model.supports_sampling else None,
            tag=f"{question_id}|{self._prompt.name}-{self._prompt.version}",
        )
        response = self._model.complete(request)
        usage = (response.usage.input_tokens, response.usage.output_tokens)
```

- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
  - `round` rounds a number.
- Ends the function and gives back the result of calling `Answer` to the caller.
  - `Answer`, a class of this project (The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text.).
- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `user` of `ChatMessage`.
  - `format_context`, a function defined in this file or passed in.
- Stores the result of calling `self._model.complete` under the name `response`.
  - The method `complete` of `self._model`.
- Stores a tuple of 2 item(s) under the name `usage`.

`src/cited_answers/application/answer.py`, lines 91 to 104:

```python
        text = response.text.strip()
        if is_model_refusal(text):
            return Answer(
                question_id, Status.REFUSED, REFUSAL_MESSAGE, Reason.MODEL_REFUSED, (), retrieval, text, *usage
            )
        check = check_citations(text, retrieval.chunks)
        if not check.ok:
            _log.info(
                "answer replaced by the refusal",
                extra={"fields": {"question_id": question_id, "reason": check.reason.value}},
            )
            return Answer(
                question_id, Status.REFUSED, REFUSAL_MESSAGE, check.reason, check.cited, retrieval, text, *usage
            )
```

- Stores the result of calling `response.text.strip` under the name `text`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Decision: the indented lines below run only when `is_model_refusal(text)` is true.
  - `is_model_refusal` from the project's `cited_answers.domain.answering` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).).
- Ends the function and gives back the result of calling `Answer` to the caller.
  - `Answer`, a class of this project (The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text.).
  - `*name` inside a call passes every item of a collection as a separate argument.
- Stores the result of calling `check_citations` under the name `check`.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Decision: the indented lines below run only when `not check.ok` is true.
  - `not` flips true and false.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back the result of calling `Answer` to the caller.
  - `Answer`, a class of this project (The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text.).
  - `*name` inside a call passes every item of a collection as a separate argument.

`src/cited_answers/application/answer.py`, lines 105 to 105:

```python
        return Answer(question_id, Status.ANSWERED, text, Reason.NONE, check.cited, retrieval, text, *usage)
```

- Ends the function and gives back the result of calling `Answer` to the caller.
  - `Answer`, a class of this project (The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text.).
  - `*name` inside a call passes every item of a collection as a separate argument.

### `src/cited_answers/application/evaluate.py`

In its own words: "Evaluate retrieval and answers on a question set, and grade the two halves apart."

92 non-blank lines; it defines `RetrievalReport`, `evaluate_retrieval`, `QuestionResult`, `AnswerReport`, `evaluate_answers`, `summarize`.

`src/cited_answers/application/evaluate.py`, lines 1 to 14:

```python
"""Evaluate retrieval and answers on a question set, and grade the two halves apart."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from cited_answers.application.answer import Answer, AnswerService
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode
from cited_answers.domain.evaluation import Question, QuestionType, Rate, Stage, classify_miss, hit_at_k

_log = logging.getLogger(__name__)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Answer` (The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text.), `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `Judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.) from the project module `cited_answers.application.judge`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `Mode` (How to find chunks.) from the project module `cited_answers.application.retrieve`.
- Brings in `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.), `Rate` (A count out of a total with its Wilson interval.), `Stage` (Where a wrong answer went wrong.), `classify_miss` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.), `hit_at_k` (True when a chunk of the gold page is among the first `k` retrieved.) from the project module `cited_answers.domain.evaluation`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.

`src/cited_answers/application/evaluate.py`, lines 17 to 28:

```python
@dataclass(frozen=True, slots=True)
class RetrievalReport:
    """Hit rate at five per question type and retrieval mode."""

    rates: dict[tuple[str, str], Rate]
    misses: dict[tuple[str, str], list[str]]


def evaluate_retrieval(retriever: HybridRetriever, questions: Sequence[Question]) -> RetrievalReport:
    """For answerable and exact questions, count a hit when a chunk of the gold page is in the top five."""
    hits: dict[tuple[str, str], list[bool]] = {}
    misses: dict[tuple[str, str], list[str]] = {}
```

- Defines the class `RetrievalReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Hit rate at five per question type and retrieval mode."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `rates` as a dictionary from a fixed list of text, text to the project type `Rate`; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `misses` as a dictionary from a fixed list of text, text to a list of text; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `evaluate_retrieval`. It returns the project type `RetrievalReport`. The author's own description: "For answerable and exact questions, count a hit when a chunk of the gold page is in the top five."
- Its parameters:
    - `retriever` holds the project type `HybridRetriever`.
    - `questions` holds anything that behaves like a list of the project type `Question`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `hits` as a dictionary from a fixed list of text, text to a list of true or false and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `misses` as a dictionary from a fixed list of text, text to a list of text and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/application/evaluate.py`, lines 29 to 39:

```python
    for question in questions:
        if not question.has_gold:
            continue
        for mode in Mode:
            found = hit_at_k(retriever.retrieve(question.question, mode).page_ids, question.gold_page)
            key = (question.type.value, mode.value)
            hits.setdefault(key, []).append(found)
            if not found:
                misses.setdefault(key, []).append(question.id)
    rates = {key: Rate(sum(values), len(values)) for key, values in hits.items()}
    return RetrievalReport(rates, misses)
```

- Loop: the indented lines below run once for each item of `questions`; `question` names the current item.
- Decision: the indented lines below run only when `not question.has_gold` is true.
  - `not` flips true and false.
- Skips the rest of this round of the loop and starts the next.
- Loop: the indented lines below run once for each item of `Mode`; `mode` names the current item.
- Stores the result of calling `hit_at_k` under the name `found`.
  - `hit_at_k` from the project's `cited_answers.domain.evaluation` (True when a chunk of the gold page is among the first `k` retrieved.).
  - The method `retrieve` of `retriever`.
- Stores a tuple of 2 item(s) under the name `key`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.setdefault(...)` reads a dictionary entry, creating it with a default when missing.
- Decision: the indented lines below run only when `not found` is true.
  - `not` flips true and false.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.setdefault(...)` reads a dictionary entry, creating it with a default when missing.
- Stores a dictionary built by looping under the name `rates`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `Rate` from the project's `cited_answers.domain.evaluation` (A count out of a total with its Wilson interval.).
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - `.items(...)` gives the key and value pairs of a dictionary.
- Ends the function and gives back the result of calling `RetrievalReport` to the caller.
  - `RetrievalReport`, a class of this project (Hit rate at five per question type and retrieval mode.).

`src/cited_answers/application/evaluate.py`, lines 42 to 53:

```python
@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question through the whole pipeline."""

    question: Question
    answer: Answer
    hit: bool
    correct: bool | None


@dataclass(frozen=True, slots=True)
class AnswerReport:
```

- Defines the class `QuestionResult`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One question through the whole pipeline."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `question` as the project type `Question`; it has no default, so a value must be given when the object is made.
- Declares `answer` as the project type `Answer`; it has no default, so a value must be given when the object is made.
- Declares `hit` as true or false; it has no default, so a value must be given when the object is made.
- Declares `correct` as true or false, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Defines the class `AnswerReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Retrieval and answer quality as separate numbers, the refusal record and the misses by stage."

`src/cited_answers/application/evaluate.py`, lines 54 to 67:

```python
    """Retrieval and answer quality as separate numbers, the refusal record and the misses by stage."""

    results: tuple[QuestionResult, ...]
    retrieval_hit: Rate
    answer_correct: Rate
    unanswerable_refused: Rate
    false_refusals: Rate
    misses_by_stage: dict[Stage, int]
    input_tokens: int
    output_tokens: int

    @property
    def unanswered_slips(self) -> list[str]:
        """Ids of unanswerable questions that got an answer instead of the refusal."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `results` as a fixed list of the project type `QuestionResult` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `retrieval_hit` as the project type `Rate`; it has no default, so a value must be given when the object is made.
- Declares `answer_correct` as the project type `Rate`; it has no default, so a value must be given when the object is made.
- Declares `unanswerable_refused` as the project type `Rate`; it has no default, so a value must be given when the object is made.
- Declares `false_refusals` as the project type `Rate`; it has no default, so a value must be given when the object is made.
- Declares `misses_by_stage` as a dictionary from the project type `Stage` to a whole number; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `unanswered_slips`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a list of text. The author's own description: "Ids of unanswerable questions that got an answer instead of the refusal."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/evaluate.py`, lines 68 to 81:

```python
        return [
            r.question.id for r in self.results if r.question.type is QuestionType.UNANSWERABLE and not r.answer.refused
        ]


def evaluate_answers(
    service: AnswerService,
    judge: Judge,
    questions: Sequence[Question],
    stop_requested: Callable[[], bool] = lambda: False,
) -> AnswerReport:
    """Run every question through retrieval, the model and the judge, then grade retrieval and answers apart."""
    results: list[QuestionResult] = []
    for question in questions:
```

- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `not` flips true and false.
- Defines the function `evaluate_answers`. It returns the project type `AnswerReport`. The author's own description: "Run every question through retrieval, the model and the judge, then grade retrieval and answers apart."
- Its parameters:
    - `service` holds the project type `AnswerService`.
    - `judge` holds the project type `Judge`.
    - `questions` holds anything that behaves like a list of the project type `Question`.
    - `stop_requested` holds a function; if the caller leaves it out it is a small function.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `results` as a list of the project type `QuestionResult` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `questions`; `question` names the current item.

`src/cited_answers/application/evaluate.py`, lines 82 to 95:

```python
        if stop_requested():
            break
        answer = service.ask(question.question, question.id)
        hit = hit_at_k(answer.retrieval.page_ids, question.gold_page)
        correct = None
        if question.has_gold:
            correct = (not answer.refused) and judge.grade(question, answer.text)
        results.append(QuestionResult(question, answer, hit, correct))
        _log.info("question answered", extra={"fields": {"question_id": question.id, "status": answer.status.value}})
    return summarize(results)


def summarize(results: Sequence[QuestionResult]) -> AnswerReport:
    """Fold per-question results into the report's numbers."""
```

- Decision: the indented lines below run only when `stop_requested()` is true.
  - `stop_requested`, a function defined in this file or passed in.
- Leaves the loop at once.
- Stores the result of calling `service.ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
- Stores the result of calling `hit_at_k` under the name `hit`.
  - `hit_at_k` from the project's `cited_answers.domain.evaluation` (True when a chunk of the gold page is among the first `k` retrieved.).
- Stores nothing (`None`) under the name `correct`.
- Decision: the indented lines below run only when `question.has_gold` is true.
- Stores the result of combining conditions: `not answer.refused and judge.grade(question, answer.text)` under the name `correct`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - The method `grade` of the project's `Judge` (True when the judge calls the answer correct.).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `QuestionResult`, a class of this project (One question through the whole pipeline.).
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back the result of calling `summarize` to the caller.
  - `summarize`, a function of this file (Fold per-question results into the report's numbers.).
- Defines the function `summarize`. It returns the project type `AnswerReport`. The author's own description: "Fold per-question results into the report's numbers."
- Its parameters:
    - `results` holds anything that behaves like a list of the project type `QuestionResult`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/evaluate.py`, lines 96 to 102:

```python
    gradable = [r for r in results if r.question.has_gold]
    unanswerable = [r for r in results if not r.question.has_gold]
    stages: dict[Stage, int] = {Stage.RETRIEVAL: 0, Stage.GENERATION: 0}
    for r in gradable:
        stage = classify_miss(r.hit, bool(r.correct))
        if stage is not None:
            stages[stage] += 1
```

- Stores a list built by looping under the name `gradable`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores a list built by looping under the name `unanswerable`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not` flips true and false.
- Declares `stages` as a dictionary from the project type `Stage` to a whole number and sets it to a dictionary with 2 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `gradable`; `r` names the current item.
- Stores the result of calling `classify_miss` under the name `stage`.
  - `classify_miss` from the project's `cited_answers.domain.evaluation` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.).
  - `bool` turns a value into true or false.
- Decision: the indented lines below run only when `stage is not None` is true.
  - `is not` means not the same object.
- Updates `stages[stage]` in place: `+=` applies `+` with the number `1` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/application/evaluate.py`, lines 103 to 112:

```python
    return AnswerReport(
        results=tuple(results),
        retrieval_hit=Rate(sum(r.hit for r in gradable), len(gradable)),
        answer_correct=Rate(sum(bool(r.correct) for r in gradable), len(gradable)),
        unanswerable_refused=Rate(sum(r.answer.refused for r in unanswerable), len(unanswerable)),
        false_refusals=Rate(sum(r.answer.refused for r in gradable), len(gradable)),
        misses_by_stage=stages,
        input_tokens=sum(r.answer.input_tokens for r in results),
        output_tokens=sum(r.answer.output_tokens for r in results),
    )
```

- Ends the function and gives back the result of calling `AnswerReport` to the caller.
  - `AnswerReport`, a class of this project (Retrieval and answer quality as separate numbers, the refusal record and the misses by stage.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `Rate` from the project's `cited_answers.domain.evaluation` (A count out of a total with its Wilson interval.).
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `bool` turns a value into true or false.

### `src/cited_answers/application/judge.py`

In its own words: "A model grades whether an answer states the fact it should; its agreement with hand grades is measured."

28 non-blank lines; it defines `Judge`.

`src/cited_answers/application/judge.py`, lines 1 to 14:

```python
"""A model grades whether an answer states the fact it should; its agreement with hand grades is measured."""

from __future__ import annotations

import hashlib

from cited_answers.application.ports import ChatModel
from cited_answers.domain.evaluation import Question, parse_verdict
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.domain.prompts import Prompt


class Judge:
    """Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `cited_answers.application.ports`.
- Brings in `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `parse_verdict` (Read a judge's reply: True for correct, False for incorrect, None when it says neither.) from the project module `cited_answers.domain.evaluation`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `cited_answers.domain.llm`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `cited_answers.domain.prompts`.
- Defines the class `Judge`. The author's own description: "Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/judge.py`, lines 16 to 21:

```python
    def __init__(self, model: ChatModel, prompt: Prompt) -> None:
        self._model = model
        self._prompt = prompt

    def grade(self, question: Question, answer_text: str) -> bool:
        """True when the judge calls the answer correct."""
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `model` holds the project type `ChatModel`.
    - `prompt` holds the project type `Prompt`.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `prompt` under the name `self._prompt` (as an attribute of this object, so other methods can use it).
- Defines the method `grade`. It returns true or false. The author's own description: "True when the judge calls the answer correct."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `question` holds the project type `Question`.
    - `answer_text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/judge.py`, lines 22 to 35:

```python
        request = ChatRequest(
            messages=(
                ChatMessage.user(
                    f"Question: {question.question}\n"
                    f"The answer must state: {question.fact}\n"
                    f"Answer to grade: {answer_text}"
                ),
            ),
            system=self._prompt.text,
            max_output_tokens=20,
            temperature=0.0 if self._model.supports_sampling else None,
            tag=f"{question.id}|judge-{self._prompt.version}|{hashlib.sha256(answer_text.encode()).hexdigest()[:8]}",
        )
        return parse_verdict(self._model.complete(request).text) is True
```

- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `user` of `ChatMessage`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Ends the function and gives back whether `parse_verdict(self._model.complete(request).text) is True` holds to the caller.
  - `is` means the very same object.
  - `parse_verdict` from the project's `cited_answers.domain.evaluation` (Read a judge's reply: True for correct, False for incorrect, None when it says neither.).
  - The method `complete` of `self._model`.

### `src/cited_answers/application/ports.py`

In its own words: "The boundaries the use cases depend on. Adapters in `infrastructure` implement them."

60 non-blank lines; it defines `ChatModel`, `Embedder`, `Clock`, `ChunkStore`, `PageSource`, `QuestionSource`, `PromptStore`.

`src/cited_answers/application/ports.py`, lines 1 to 13:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime` from the standard library module `datetime`.
- Brings in `Protocol` from the standard library module `typing`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Brings in `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.) from the project module `cited_answers.domain.evaluation`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `cited_answers.domain.llm`.
- Brings in `Page` (One help-center page.) from the project module `cited_answers.domain.pages`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `cited_answers.domain.prompts`.

`src/cited_answers/application/ports.py`, lines 16 to 27:

```python
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
```

- Defines the class `ChatModel`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "One chat model behind one interface: a vendor, a local server or a recording."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text. The author's own description: "The model id the responses come from."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false. The author's own description: "False when the provider rejects `temperature` and `top_p` (the request then says so)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

`src/cited_answers/application/ports.py`, lines 29 to 41:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...


class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
```

- Defines the method `complete`. It returns the project type `ChatResponse`. The author's own description: "Send one request. Raises `TransientModelError` or `PermanentModelError`."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Embedder`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Turns texts into vectors."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `embed`. It returns a list of a list of a decimal number. The author's own description: "One vector per text, in order."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/ports.py`, lines 42 to 55:

```python
        ...


class Clock(Protocol):
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class ChunkStore(Protocol):
```

- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Clock`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Time, injected so tests are deterministic."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `ChunkStore`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Where chunks and their vectors live: memory in tests, Postgres with pgvector in the service."

`src/cited_answers/application/ports.py`, lines 56 to 68:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `replace_all`. It returns nothing (None). The author's own description: "Replace the whole index with these chunks and vectors, in one transaction."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `chunks` holds anything that behaves like a list of the project type `Chunk`.
    - `vectors` holds anything that behaves like a list of anything that behaves like a list of a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `chunks`. It returns a list of the project type `Chunk`. The author's own description: "Every indexed chunk."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `vector_search`. It returns a list of a fixed list of text, a decimal number. The author's own description: "The `k` nearest chunk ids with their cosine similarity, best first."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `k` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

`src/cited_answers/application/ports.py`, lines 70 to 82:

```python
    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        """Cosine similarity of the vector to each named chunk."""
        ...


class PageSource(Protocol):
    """Reads the help-center pages."""

    def pages(self) -> list[Page]: ...


class QuestionSource(Protocol):
    """Reads an evaluation set."""
```

- Defines the method `similarities`. It returns a dictionary from text to a decimal number. The author's own description: "Cosine similarity of the vector to each named chunk."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `chunk_ids` holds anything that behaves like a list of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `PageSource`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Reads the help-center pages."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `pages`. It returns a list of the project type `Page`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `QuestionSource`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Reads an evaluation set."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/ports.py`, lines 84 to 92:

```python
    def load(self, split: str) -> list[Question]: ...


class PromptStore(Protocol):
    """Versioned prompt files."""

    def load(self, name: str, version: str) -> Prompt:
        """The prompt `name` at `version`; raises `PromptNotFound`."""
        ...
```

- Defines the method `load`. It returns a list of the project type `Question`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `split` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `PromptStore`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Versioned prompt files."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `load`. It returns the project type `Prompt`. The author's own description: "The prompt `name` at `version`; raises `PromptNotFound`."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
    - `version` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

### `src/cited_answers/application/retrieve.py`

In its own words: "Ingest the pages and retrieve chunks by vector, by keyword or by both fused."

87 non-blank lines; it defines `Mode`, `IngestReport`, `ingest`, `Retrieval`, `HybridRetriever`, `describe`.

`src/cited_answers/application/retrieve.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `ChunkStore` (Where chunks and their vectors live: memory in tests, Postgres with pgvector in the service.), `Embedder` (Turns texts into vectors.), `PageSource` (Reads the help-center pages.) from the project module `cited_answers.application.ports`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.), `chunk_current_pages` (Chunk every current page; return the chunks and the ids of the retired pages that were left out.) from the project module `cited_answers.domain.chunking`.
- Brings in `Bm25Index` (Okapi BM25 over chunk text (heading path included).), `reciprocal_rank_fusion` (Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up.) from the project module `cited_answers.domain.retrieval`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.

`src/cited_answers/application/retrieve.py`, lines 15 to 28:

```python
EMBED_BATCH = 32


class Mode(StrEnum):
    """How to find chunks."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    FUSED = "fused"


@dataclass(frozen=True, slots=True)
class IngestReport:
    """What indexing did: current pages indexed, chunks written, retired pages left out."""
```

- Stores the number `32` under the name `EMBED_BATCH`.
- Defines the class `Mode`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "How to find chunks."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `vector` under the name `VECTOR`.
- Stores the text `keyword` under the name `KEYWORD`.
- Stores the text `fused` under the name `FUSED`.
- Defines the class `IngestReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What indexing did: current pages indexed, chunks written, retired pages left out."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/retrieve.py`, lines 30 to 42:

```python
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
```

- Declares `pages_indexed` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `chunks` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `skipped_retired` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `ingest`. It returns the project type `IngestReport`. The author's own description: "Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged."
- Its parameters:
    - `source` holds the project type `PageSource`.
    - `embedder` holds the project type `Embedder`.
    - `store` holds the project type `ChunkStore`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `source.pages` under the name `pages`.
  - The method `pages` of `source`.
- Stores the result of calling `chunk_current_pages` under the name `(chunks, skipped)`.
  - `chunk_current_pages` from the project's `cited_answers.domain.chunking` (Chunk every current page; return the chunks and the ids of the retired pages that were left out.).
- Loop: the indented lines below run once for each item of `skipped`; `page_id` names the current item.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Stores a list built by looping under the name `texts`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `for_search` of the project's `Chunk` (The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat.).
- Declares `vectors` as a list of a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/application/retrieve.py`, lines 43 to 55:

```python
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
```

- Loop: the indented lines below run once for each item of `range(0, len(texts), EMBED_BATCH)`; `start` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `len` counts the items in a collection (or the characters in text).
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - The method `embed` of `embedder`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `+` is add.
- Calls the method `replace_all` of `store` with 2 argument(s); the result is not kept.
  - The method `replace_all` of `store`.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
  - `-` is subtract.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the result of calling `IngestReport` to the caller.
  - `IngestReport`, a class of this project (What indexing did: current pages indexed, chunks written, retired pages left out.).
  - `-` is subtract.
  - `len` counts the items in a collection (or the characters in text).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
- Defines the class `Retrieval`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The chunks found for a question, best first, and how close the best of them is to the question's vector."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/application/retrieve.py`, lines 57 to 69:

```python
    mode: Mode
    chunks: tuple[Chunk, ...]
    best_similarity: float

    @property
    def page_ids(self) -> list[str]:
        return [c.page_id for c in self.chunks]


class HybridRetriever:
    """Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion."""

    def __init__(self, store: ChunkStore, embedder: Embedder, k: int = 5, depth: int = 20, rrf_k: int = 60) -> None:
```

- Declares `mode` as the project type `Mode`; it has no default, so a value must be given when the object is made.
- Declares `chunks` as a fixed list of the project type `Chunk` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `best_similarity` as a decimal number; it has no default, so a value must be given when the object is made.
- Defines the method `page_ids`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a list of text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the class `HybridRetriever`. The author's own description: "Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `ChunkStore`.
    - `embedder` holds the project type `Embedder`.
    - `k` holds a whole number; if the caller leaves it out it is the number `5`.
    - `depth` holds a whole number; if the caller leaves it out it is the number `20`.
    - `rrf_k` holds a whole number; if the caller leaves it out it is the number `60`.

`src/cited_answers/application/retrieve.py`, lines 70 to 81:

```python
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
```

- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Stores the value named `embedder` under the name `self._embedder` (as an attribute of this object, so other methods can use it).
- Stores a tuple of 3 item(s) under the name `(self._k, self._depth, self._rrf_k)`.
- Declares `self._by_id` as a dictionary from text to the project type `Chunk` and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `Bm25Index` under the name `self._bm25` (as an attribute of this object, so other methods can use it).
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
- Calls the method `reload` of this object (Read the chunks again, for example after a page was re-indexed.); the result is not kept.
  - The method `reload` of this object (Read the chunks again, for example after a page was re-indexed.).
- Defines the method `reload`. It returns nothing (None). The author's own description: "Read the chunks again, for example after a page was re-indexed."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._store.chunks` under the name `chunks`.
  - The method `chunks` of `self._store`.
- Stores a dictionary built by looping under the name `self._by_id` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `Bm25Index` under the name `self._bm25` (as an attribute of this object, so other methods can use it).
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).

`src/cited_answers/application/retrieve.py`, lines 83 to 95:

```python
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
```

- Defines the method `chunk_count`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `retrieve`. It returns the project type `Retrieval`. The author's own description: "The top chunks for a question; `best_similarity` is the highest cosine among them."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `question` holds text.
    - `mode` holds the project type `Mode`; if the caller leaves it out it is the `FUSED` of `Mode`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._embedder.embed` under the name `(vector,)`.
  - The method `embed` of `self._embedder`.
- Stores the result of calling `self._store.vector_search` under the name `vector_hits`.
  - The method `vector_search` of `self._store`.
- Stores the result of calling `dict` under the name `similarities`.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `mode is Mode.VECTOR` is true.
  - `is` means the very same object.
- Stores the part of `[chunk_id for chunk_id, _ i...` picked by `:self._k` under the name `ids`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores a list built by looping under the name `keyword_ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `search` on the stored object `self._bm25`: it looks for a regular expression anywhere in text.

`src/cited_answers/application/retrieve.py`, lines 96 to 109:

```python
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
```

- Decision: the indented lines below run only when `mode is Mode.KEYWORD` is true.
  - `is` means the very same object.
- Stores the part of `keyword_ids` picked by `:self._k` under the name `ids`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores a list of 2 item(s) under the name `rankings`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `reciprocal_rank_fusion` from the project's `cited_answers.domain.retrieval` (Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up.).
- Stores a list built by looping under the name `missing`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not in` means is not contained in.
- Decision: the indented lines below run only when `missing` is true.
- Calls `.update(...)` merges another collection into this one with 1 argument(s); the result is not kept.
  - `.update(...)` merges another collection into this one.
  - The method `similarities` of `self._store`.
- Stores the result of calling `tuple` under the name `chunks`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `max` under the name `best`.
  - `max` picks the largest value.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `Retrieval` to the caller.
  - `Retrieval`, a class of this project (The chunks found for a question, best first, and how close the best of them is to the question's vector.).
- Defines the function `describe`. It returns text. The author's own description: "One line per chunk, for logs: ids only."
- Its parameters:
    - `chunks` holds anything that behaves like a list of the project type `Chunk`.

`src/cited_answers/application/retrieve.py`, lines 110 to 111:

```python
    """One line per chunk, for logs: ids only."""
    return ",".join(c.id for c in chunks)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `','.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

### `src/cited_answers/application/threshold.py`

In its own words: "Tune the refusal threshold on the development questions only."

20 non-blank lines; it defines `dev_scores`, `choose_threshold`.

`src/cited_answers/application/threshold.py`, lines 1 to 14:

```python
"""Tune the refusal threshold on the development questions only."""

from __future__ import annotations

from collections.abc import Sequence

from cited_answers.application.answer import AnswerService
from cited_answers.domain.answering import ThresholdChoice, tune_threshold
from cited_answers.domain.evaluation import Question, QuestionType


def dev_scores(service: AnswerService, questions: Sequence[Question]) -> tuple[list[float], list[float]]:
    """Best retrieval score of each answerable (gold-page) question and of each unanswerable one."""
    answerable: list[float] = []
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `ThresholdChoice` (A refusal threshold and what it costs: the share of answerable questions it would wrongly refuse.), `tune_threshold` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.) from the project module `cited_answers.domain.answering`.
- Brings in `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.) from the project module `cited_answers.domain.evaluation`.
- Defines the function `dev_scores`. It returns a fixed list of a list of a decimal number, a list of a decimal number. The author's own description: "Best retrieval score of each answerable (gold-page) question and of each unanswerable one."
- Its parameters:
    - `service` holds the project type `AnswerService`.
    - `questions` holds anything that behaves like a list of the project type `Question`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `answerable` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/application/threshold.py`, lines 15 to 27:

```python
    unanswerable: list[float] = []
    for question in questions:
        score = service.retrieve(question.question).best_similarity
        (unanswerable if question.type is QuestionType.UNANSWERABLE else answerable).append(score)
    return answerable, unanswerable


def choose_threshold(
    service: AnswerService, dev_questions: Sequence[Question], max_false_refusal: float = 0.10
) -> ThresholdChoice:
    """The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate."""
    answerable, unanswerable = dev_scores(service, dev_questions)
    return tune_threshold(answerable, unanswerable, max_false_refusal)
```

- Declares `unanswerable` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `questions`; `question` names the current item.
- Stores the `best_similarity` of `service.retrieve(question.question)` under the name `score`.
  - The method `retrieve` of `service`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Defines the function `choose_threshold`. It returns the project type `ThresholdChoice`. The author's own description: "The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate."
- Its parameters:
    - `service` holds the project type `AnswerService`.
    - `dev_questions` holds anything that behaves like a list of the project type `Question`.
    - `max_false_refusal` holds a decimal number; if the caller leaves it out it is the number `0.1`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `dev_scores` under the name `(answerable, unanswerable)`.
  - `dev_scores`, a function of this file (Best retrieval score of each answerable (gold-page) question and of each unanswerable one.).
- Ends the function and gives back the result of calling `tune_threshold` to the caller.
  - `tune_threshold` from the project's `cited_answers.domain.answering` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import cited_answers.application.__init__; print(cited_answers.application.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Use cases and the ports they need. Depends on the domain only.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/cited_answers/application').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
answer.py 3
evaluate.py 6
judge.py 1
ports.py 7
retrieve.py 6
threshold.py 2
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

- **Common mistakes with this layer.** Calling a concrete adapter directly from a use case (the layering contract would fail), hiding state in module-level variables, or doing slow input/output inside a loop without a way to stop it. Here the ports are protocols and long loops check a shutdown flag.

## Check yourself

1. What is the job of `src/cited_answers/application/__init__.py`?

   *Answer:* Use cases and the ports they need. Depends on the domain only.

2. What is the job of `src/cited_answers/application/answer.py`?

   *Answer:* Answer a question from the retrieved chunks, cite every claim, or refuse.

3. What is the job of `src/cited_answers/application/evaluate.py`?

   *Answer:* Evaluate retrieval and answers on a question set, and grade the two halves apart.

4. What is the job of `src/cited_answers/application/judge.py`?

   *Answer:* A model grades whether an answer states the fact it should; its agreement with hand grades is measured.

5. What is the job of `src/cited_answers/application/ports.py`?

   *Answer:* The boundaries the use cases depend on. Adapters in `infrastructure` implement them.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
