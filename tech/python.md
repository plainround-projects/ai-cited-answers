# Python

## What it is

**Python** is a programming language. A **program** is a text file of instructions; a **programming language** is the set of rules for writing them. Python is easy to read: it uses indentation (spaces at the start of a line) to show which lines belong together, and plain words for most operations.

The program that reads and runs Python code is the **interpreter**, also called `python`. It reads the file, turns each line into simple internal steps (called *bytecode*), and carries them out one by one. You do not compile first.

Python code is split into **modules** (files ending in `.py`) and **packages** (folders of modules). A **variable** is a name for a value (`count = 3`). A **function** is named, reusable code (`def add(a, b): return a + b`). A **class** is a blueprint for objects that bundle data with behavior. A **type** says what kind of value something is: whole number (`int`), decimal number (`float`), text (`str`), true or false (`bool`), list, dictionary.

## Why this repository uses it

Python is the language of the AI ecosystem: the Claude SDK, the model-serving tools and the test tools are all Python libraries. It reads close to plain English, which suits a learning repository whose goal is that you understand the code.

The project asks for Python 3.12 or newer (`requires-python = ">=3.12"`). The Makefile uses 3.13 when it is installed. Newer syntax used here includes the `X | None` type form, `StrEnum` and `@dataclass(slots=True)`.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/` | 39 Python files: the program itself |
| `tests/` | 16 Python files: automated tests |
| `scripts/` | 3 Python helper script(s) that generate the committed data files |
| `pyproject.toml` | declares the Python version and the command-line programs |
| `Makefile` | starts every Python program through `.venv/bin` |

## How it works underneath

**Objects everywhere.** Every value in Python is an *object*: a chunk of memory with a type and some data. A variable is a label attached to an object. `a = b` makes a second label on the same object; it does not copy.

**Mutable and immutable.** Numbers, strings, tuples and frozen dataclasses cannot be changed after creation (they are *immutable*). Lists, dictionaries and sets can (they are *mutable*). Code that shares data between threads or between layers prefers immutable objects.

**The import system.** `import a.b` looks for a folder `a` with a file `b.py` on the module search path `sys.path`, runs the file once, and keeps the result in `sys.modules` so later imports reuse it.

**Type hints are not checked at run time.** The interpreter ignores them. The separate tool mypy reads them and reports mismatches (see `mypy.md`).

**Exceptions and the call stack.** Each running function has a frame on the stack. When an exception is raised, Python unwinds the stack frame by frame until an `except` matches; if none does, the program ends and prints a *traceback*, the list of frames.

**Threads and the GIL.** The standard interpreter lets only one thread run Python bytecode at a time (the *global interpreter lock*). Threads are therefore good for waiting on the network, not for heavy calculation. The test helpers and servers here use them for waiting.

**Garbage collection.** Python counts the labels attached to each object and frees it when the count reaches zero.

## Walkthrough of this repository's use

### A first tour of the language (every snippet was run; the output is real)

#### Values, names and types

A **value** is a piece of data. A **name** (variable) is a label you attach to a value with `=`. Every value has a **type**: `int` (whole number), `float` (decimal number), `str` (text), `bool` (`True` or `False`). `print(...)` shows values on the screen; `type(x)` tells you the type.

```python
price = 12.5
name = "meter"
count = 3
print(name, price * count, type(count), type(price), type(name), count > 2)
```

It prints:

```text
meter 37.5 <class 'int'> <class 'float'> <class 'str'> True
```

#### Text

Text is written in quotes. An *f-string* (`f"..."`) fills in values written between braces. Text has methods you call with a dot.

```python
who = "world"
print(f"hello {who}, {len(who)} letters", who.upper(), who.replace("o", "0"))
```

It prints:

```text
hello world, 5 letters WORLD w0rld
```

#### Lists and loops

A **list** is an ordered collection in square brackets. `for item in list:` repeats the indented lines once for each item. A list comprehension builds a new list in one line.

```python
prompts = ["a", "bb", "ccc"]
for p in prompts:
    print(p, len(p))
print([len(p) for p in prompts])
```

It prints:

```text
a 1
bb 2
ccc 3
[1, 2, 3]
```

#### Dictionaries

A **dictionary** (dict) is a collection of `key: value` pairs in braces. You look a value up by its key; `.get(key, default)` gives a default when the key is missing instead of raising an error.

```python
row = {"id": "p01", "kind": "short"}
row["tokens"] = 12
print(row["id"], row.get("missing", "none"), list(row))
```

It prints:

```text
p01 none ['id', 'kind', 'tokens']
```

#### Decisions

`if`, `elif` and `else` choose which indented block runs. Indentation (four spaces) is the grammar: it marks what belongs to what.

```python
n = 7
if n < 5:
    print("small")
elif n < 10:
    print("medium")
else:
    print("large")
```

It prints:

```text
medium
```

#### Functions

`def name(parameters):` defines reusable code. `return` hands a value back. A function with a docstring (a text in triple quotes as its first line) documents itself.

```python
def cost(tokens, per_thousand):
    """Dollars for a number of tokens."""
    return tokens / 1000 * per_thousand
print(cost(2500, 0.0005), cost.__doc__)
```

It prints:

```text
0.00125 Dollars for a number of tokens.
```

#### Classes and dataclasses

A **class** bundles data with the functions that use it. A dataclass writes the boring parts for you.

```python
from dataclasses import dataclass
@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
u = Usage(10, 4)
print(u, u.input_tokens + u.output_tokens)
```

It prints:

```text
Usage(input_tokens=10, output_tokens=4) 14
```

#### Errors

When something goes wrong Python *raises an exception*. `try`/`except` catches it so the program can respond instead of stopping.

```python
try:
    int("twelve")
except ValueError as error:
    print("caught:", error)
```

It prints:

```text
caught: invalid literal for int() with base 10: 'twelve'
```

### How the code is laid out

All code of the program lives in the package `cited_answers` under `src/`. It has four sub-packages that form layers: `domain` (the core ideas, with no outside technology), `application` (the use cases that combine them), `infrastructure` (adapters to files, databases, networks and vendor SDKs) and `interfaces` (the command line, the web server). The rule is: outer layers may import inner ones, never the other way. `import-linter` enforces it (see `import-linter.md`).

| File | What the file says it is (its own first docstring line) |
| --- | --- |
| `scripts/make_pages.py` | Write data/pages/*.md: the 60 pages of the sample help center (57 current, 3 retired). |
| `scripts/make_questions.py` | Write data/questions/dev.jsonl (30) and data/questions/test.jsonl (120, frozen). |
| `scripts/make_seed_sql.py` | Write sql/002_seed.sql: one INSERT per help-center page, generated from data/pages so the two never drift apart. |
| `src/cited_answers/__init__.py` | A question-answering service over a help center: hybrid retrieval, cited answers or a fixed refusal. |
| `src/cited_answers/application/__init__.py` | Use cases and the ports they need. Depends on the domain only. |
| `src/cited_answers/application/answer.py` | Answer a question from the retrieved chunks, cite every claim, or refuse. |
| `src/cited_answers/application/evaluate.py` | Evaluate retrieval and answers on a question set, and grade the two halves apart. |
| `src/cited_answers/application/judge.py` | A model grades whether an answer states the fact it should; its agreement with hand grades is measured. |
| `src/cited_answers/application/ports.py` | The boundaries the use cases depend on. Adapters in `infrastructure` implement them. |
| `src/cited_answers/application/retrieve.py` | Ingest the pages and retrieve chunks by vector, by keyword or by both fused. |
| `src/cited_answers/application/threshold.py` | Tune the refusal threshold on the development questions only. |
| `src/cited_answers/domain/__init__.py` | Pure domain logic. Depends on nothing outside the standard library. |
| `src/cited_answers/domain/answering.py` | Answer rules: the fixed refusal, the citation check and the tuning of the refusal threshold. |
| `src/cited_answers/domain/chunking.py` | Split pages into chunks on their headings, each carrying the metadata a search result needs. |
| `src/cited_answers/domain/errors.py` | Named errors. Callers catch these, never a vendor SDK's exception types. |
| `src/cited_answers/domain/evaluation.py` | Questions, the two grades (retrieval and answer), intervals and the split of misses by stage. |
| `src/cited_answers/domain/llm.py` | Vendor-neutral value objects for one chat-model call. No SDK is imported here. |
| `src/cited_answers/domain/pages.py` | Help-center pages: a title, an updated date, a status and sections under headings. |
| `src/cited_answers/domain/prompts.py` | A prompt file: its name, its version line and its text. |
| `src/cited_answers/domain/retrieval.py` | Keyword search (BM25), vector similarity and the fusion of ranked lists. |
| `src/cited_answers/infrastructure/__init__.py` | Adapters that implement the ports: model clients, files, settings, logging. |
| `src/cited_answers/infrastructure/anthropic_chat.py` | A chat model on the Anthropic Messages API, through the official SDK. |
| `src/cited_answers/infrastructure/clock.py` | The real clock, behind the `Clock` port. |
| `src/cited_answers/infrastructure/embeddings.py` | Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording. |
| `src/cited_answers/infrastructure/env.py` | Helpers that read and validate environment variables (twelve-factor configuration). |
| `src/cited_answers/infrastructure/files.py` | Readers for the page files, the question files, the prompt files and the threshold file. |
| `src/cited_answers/infrastructure/logging.py` | Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`). |
| `src/cited_answers/infrastructure/memory_store.py` | An in-memory chunk store: the test double and the default for offline runs. |
| `src/cited_answers/infrastructure/model_factory.py` | Builds the configured chat model from the environment: recorded, local server or Claude. |
| `src/cited_answers/infrastructure/openai_compatible.py` | A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted). |
| `src/cited_answers/infrastructure/pg_store.py` | The chunk store on Postgres with the pgvector extension (see sql/001_schema.sql). |
| `src/cited_answers/infrastructure/recording.py` | Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures. |
| `src/cited_answers/infrastructure/resilient.py` | A decorator that retries transient model failures with backoff and jitter. |
| `src/cited_answers/infrastructure/retry.py` | Retry with exponential backoff and jitter for calls that cross the network. |
| `src/cited_answers/infrastructure/settings.py` | Configuration from the environment, validated once at startup (twelve-factor). |
| `src/cited_answers/infrastructure/shutdown.py` | Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work. |
| `src/cited_answers/infrastructure/wiring.py` | Build the embedder and the chunk store the settings ask for. |
| `src/cited_answers/interfaces/__init__.py` | Command-line programs. They wire adapters into use cases and own exit codes. |
| `src/cited_answers/interfaces/cli.py` | The `cited` command: ingest, ask, serve, evaluate retrieval and answers, tune the refusal threshold. |
| `src/cited_answers/interfaces/http.py` | The HTTP interface: POST /ask and GET /health. |
| `src/cited_answers/interfaces/render.py` | Plain-text rendering of the retrieval and answer reports. |
| `src/cited_answers/interfaces/server.py` | Run the HTTP service with uvicorn: SIGTERM finishes in-flight requests, then the process exits. |

The tests under `tests/` use pytest (see `pytest.md`):

| Test file | What it contains |
| --- | --- |
| `tests/conftest.py` | Shared builders for tests: a fixed clock, a scripted model, a hashing embedder and small pages. |
| `tests/e2e/test_lesson_scenario.py` | The lesson's scenario on recorded embeddings (nomic-embed-text) and recorded answers (qwen2.5:1.5b). 10 test functions, for example `test_step_1_retired_pages_are_left_out_logged_by_id_and_every_chunk_has_its_four_fields`, `test_steps_2_and_3_hit_rate_at_five_per_type_for_vectors_keywords_and_both_with_intervals`, `test_the_keyword_index_finds_a_bare_error_code_only_because_the_tokenizer_splits_on_hyphens`, .... |
| `tests/integration/test_pgvector.py` | The Postgres adapter and the HTTP service against the real pgvector container (`make up` first). 5 test functions, for example `test_ingest_writes_the_current_pages_chunks_and_no_retired_one`, `test_the_database_itself_refuses_a_retired_chunk_and_a_chunk_of_an_unknown_page`, `test_vector_search_in_sql_ranks_like_the_in_memory_scan`, .... |
| `tests/live/test_live_models.py` | Opt-in tests that call real models. Run with `make test-live`; skipped in every other run. 2 test functions, for example `test_claude_answers_from_the_passage_and_cites_its_id`, `test_the_local_embedding_model_returns_768_dimensional_vectors_and_paraphrases_land_close`. |
| `tests/unit/application/test_retrieve_answer_evaluate.py` | 22 test functions, for example `test_ingest_indexes_current_pages_only_and_names_the_retired_ones`, `test_ingest_logs_each_skipped_page`, `test_a_search_for_the_old_return_window_returns_no_retired_chunk`, .... |
| `tests/unit/domain/test_answering_and_evaluation.py` | 16 test functions, for example `test_citations_are_read_in_order_without_repeats`, `test_an_answer_that_cites_only_retrieved_chunks_passes`, `test_a_planted_citation_to_a_chunk_that_was_not_retrieved_fails`, .... |
| `tests/unit/domain/test_llm.py` | 5 test functions, for example `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, .... |
| `tests/unit/domain/test_pages_chunking_retrieval.py` | 13 test functions, for example `test_a_page_file_is_parsed_into_metadata_and_sections_with_heading_paths`, `test_a_broken_page_file_is_refused_with_the_reason`, `test_every_chunk_carries_page_id_heading_path_date_and_status_and_ids_are_per_page`, .... |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 11 test functions, for example `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, .... |
| `tests/unit/infrastructure/test_embeddings_stores_files.py` | 16 test functions, for example `test_the_embedder_posts_the_texts_and_returns_vectors_in_input_order`, `test_rate_limits_and_server_errors_are_transient`, `test_a_client_error_a_dropped_connection_and_a_bad_shape_are_told_apart`, .... |
| `tests/unit/infrastructure/test_openai_compatible.py` | 12 test functions, for example `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, .... |
| `tests/unit/infrastructure/test_recording.py` | 6 test functions, for example `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, .... |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 15 test functions, for example `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, .... |
| `tests/unit/interfaces/test_cli.py` | 5 test functions, for example `test_a_missing_recording_is_reported_not_raised`, `test_a_bad_environment_value_is_a_configuration_error`, `test_a_missing_prompt_is_a_configuration_error`, .... |
| `tests/unit/interfaces/test_cli_commands.py` | 7 test functions, for example `test_ingest_reports_pages_chunks_and_the_skipped_retired_pages`, `test_a_known_question_is_answered_from_its_recording_with_citations`, `test_a_question_far_from_every_page_is_refused_before_the_model`, .... |
| `tests/unit/interfaces/test_http.py` | 6 test functions, for example `test_health_is_ok_with_chunks_and_not_ready_without`, `test_a_cited_answer_returns_its_citations_with_page_and_heading`, `test_the_fixed_refusal_comes_back_with_its_reason`, .... |

### The language features this code uses, with a real example of each

#### Imports

An *import* brings code from another file or package into this one. `import json` makes the module available as `json.something`. `from json import loads` brings in just the name `loads`. A **module** is one `.py` file; a **package** is a folder of modules with an `__init__.py` file. Imports that start with the project's own package name (for example `from cited_answers.domain...`) are the project's own code; the rest come from the standard library or from installed packages.

From this repository, `src/cited_answers/application/answer.py`, lines 8 to 11:

```python
from cited_answers.application.ports import ChatModel
from cited_answers.application.retrieve import HybridRetriever, Mode, Retrieval
from cited_answers.domain.answering import (
    REFUSAL_MESSAGE,
```

#### `from __future__ import annotations`

Makes Python store type annotations as text instead of evaluating them when the function or class is defined. A class can then name itself in an annotation, and imports used only for types cost nothing at run time. Every module of this repository starts with it.

From this repository, `src/cited_answers/application/answer.py`, lines 3 to 4:

```python
from __future__ import annotations

```

#### Functions with type hints

`def name(a: int, b: str = "x") -> bool:` defines a function. After each parameter, `: int` is a *type hint*: a note for people and for the mypy checker that says what kind of value is expected (Python itself does not enforce it). `= "x"` gives a *default value* used when the caller leaves the argument out. `-> bool` says what the function returns.

From this repository, `src/cited_answers/application/threshold.py`, lines 12 to 19:

```python
def dev_scores(service: AnswerService, questions: Sequence[Question]) -> tuple[list[float], list[float]]:
    """Best retrieval score of each answerable (gold-page) question and of each unanswerable one."""
    answerable: list[float] = []
    unanswerable: list[float] = []
    for question in questions:
        score = service.retrieve(question.question).best_similarity
        (unanswerable if question.type is QuestionType.UNANSWERABLE else answerable).append(score)
    return answerable, unanswerable
```

#### Classes and `self`

A **class** is a blueprint for objects that bundle data and behavior. `__init__` runs when an object is created; its first parameter, `self`, is the object being built, and `self.x = value` stores data on it. A **method** is a function defined inside a class; every method receives `self` first.

From this repository, `src/cited_answers/infrastructure/files.py`, lines 16 to 23:

```python
class FilePageSource:
    """Every `*.md` file in a folder is a page."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def pages(self) -> list[Page]:
        return [parse_page(path.read_text(encoding="utf-8")) for path in sorted(self._folder.glob("*.md"))]
```

#### Dataclasses

`@dataclass` is a *decorator* (a line starting with `@` above a definition that changes it). It reads the annotated names in the class body and writes `__init__`, `__repr__` and `__eq__` for you. `frozen=True` forbids changing an object after creation, so it can be shared safely and used as a dictionary key. `slots=True` stores fields in a compact fixed layout.

From this repository, `src/cited_answers/application/evaluate.py`, lines 17 to 22:

```python
@dataclass(frozen=True, slots=True)
class RetrievalReport:
    """Hit rate at five per question type and retrieval mode."""

    rates: dict[tuple[str, str], Rate]
    misses: dict[tuple[str, str], list[str]]
```

#### Enums

An **enum** is a fixed set of named values. `StrEnum` makes each member also a string (`Role.USER == "user"`), which is convenient for JSON and logs.

From this repository, `src/cited_answers/application/retrieve.py`, lines 18 to 23:

```python
class Mode(StrEnum):
    """How to find chunks."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    FUSED = "fused"
```

#### Protocols (structural typing)

A `Protocol` lists methods an object must have. Any class that has those methods is accepted wherever the protocol is asked for, without inheriting from it. This repository uses protocols as *ports*: the use cases ask for a `ChatModel` or a `Clock`, and the real adapter, the recording adapter and a test fake all fit.

From this repository, `src/cited_answers/application/ports.py`, lines 16 to 31:

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

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...
```

#### Properties

`@property` turns a method into something read like a field: `model.name` instead of `model.name()`. The value is worked out each time.

From this repository, `src/cited_answers/application/answer.py`, lines 38 to 40:

```python
    @property
    def refused(self) -> bool:
        return self.status is Status.REFUSED
```

#### Class methods

`@classmethod` defines a method that receives the class (`cls`) instead of an object. It is used here as a named constructor: `ChatMessage.user("hi")`.

From this repository, `src/cited_answers/domain/llm.py`, lines 58 to 60:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)
```

#### Exceptions: raise, try, except

An **exception** is an object that signals a problem and jumps out of the running code until something catches it. `raise X(...)` throws one. `try:` ... `except X:` runs the second block if the first threw an `X`. `raise Y from X` throws a new exception while keeping the original as its cause. `finally:` runs whatever happens.

From this repository, `src/cited_answers/domain/pages.py`, lines 57 to 61:

```python
        status = PageStatus(values["status"])
        updated = date.fromisoformat(values["updated"])
    except ValueError as error:
        raise InvalidPage(f"{values['id']}: {error}") from error
    return Page(values["id"], values["title"], updated, status, _sections(values["title"], match.group(2)))
```

#### Custom exception classes

A class that inherits from `Exception` is a new kind of error. Giving errors their own names lets callers catch exactly the failures they know how to handle.

From this repository, `src/cited_answers/domain/errors.py`, lines 6 to 7:

```python
class DomainError(Exception):
    """Base class for every error this package raises on purpose."""
```

#### `try` / `except` blocks

Code that might fail is placed under `try:`; the matching `except` names the error it handles.

From this repository, `src/cited_answers/domain/pages.py`, lines 56 to 60:

```python
    try:
        status = PageStatus(values["status"])
        updated = date.fromisoformat(values["updated"])
    except ValueError as error:
        raise InvalidPage(f"{values['id']}: {error}") from error
```

#### `with` blocks

`with thing as name:` is a *context manager*: it runs setup code on entry and cleanup code on exit, even if an error happens inside. Files, locks, database connections and temporary folders all use it.

From this repository, `src/cited_answers/infrastructure/embeddings.py`, lines 88 to 93:

```python
        with self._lock:
            self._vectors[key] = list(vector)
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "model": model, "vector": _pack(vector)}) + "\n")
                handle.flush()
```

#### f-strings

A string starting with `f"` can hold `{expression}` parts that are replaced by their values: `f"{count} rows"`. After the expression, `:` begins a format (`{price:.4f}` means four decimals).

From this repository, `src/cited_answers/application/answer.py`, line 45:

```python
    return "\n\n".join(f"[{c.id}] {c.heading_path} (updated {c.updated})\n{c.text}" for c in chunks)
```

#### List and dict comprehensions

`[x * 2 for x in items if x > 0]` builds a list by looping. `{k: v for k, v in pairs}` builds a dictionary. Written inside `sum(...)` or `any(...)` without brackets, it is a *generator expression* that produces values one at a time.

From this repository, `src/cited_answers/application/evaluate.py`, line 96:

```python
    gradable = [r for r in results if r.question.has_gold]
```

#### Lambdas

`lambda x: x + 1` is a small unnamed function written inline. It is used for a sort key or a callback.

From this repository, `src/cited_answers/application/evaluate.py`, lines 77 to 78:

```python
    stop_requested: Callable[[], bool] = lambda: False,
) -> AnswerReport:
```

#### Union types and `None`

`X | None` means "an X or nothing". `list[str]`, `dict[str, int]` and `tuple[int, ...]` describe collections and what is inside them. `Mapping`, `Sequence` and `Callable` (from `collections.abc`) describe *anything that behaves like* a dictionary, a list, or a function.

From this repository, `src/cited_answers/application/evaluate.py`, line 49:

```python
    correct: bool | None
```

#### Paths

`pathlib.Path` represents a file location as an object. The `/` operator joins parts (`root / "data" / "x.json"`), and methods such as `read_text()` read the file.

From this repository, `src/cited_answers/infrastructure/files.py`, lines 22 to 24:

```python
    def pages(self) -> list[Page]:
        return [parse_page(path.read_text(encoding="utf-8")) for path in sorted(self._folder.glob("*.md"))]

```

#### `Literal` and `Final`

`Literal["a", "b"]` as a type says the value must be exactly one of those. `Final` says a name is assigned once and never changed.

From this repository, `src/cited_answers/infrastructure/anthropic_chat.py`, lines 18 to 19:

```python
Thinking = Literal["omit", "disabled", "between_tools"]

```

#### `isinstance` and `getattr`

`isinstance(x, T)` asks whether `x` is a `T`. `getattr(obj, "name", default)` reads an attribute by a name held in a variable.

From this repository, `src/cited_answers/infrastructure/anthropic_chat.py`, lines 34 to 36:

```python
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
```

#### Threads

A **thread** is a second line of execution inside one program. Threads share memory, so code that changes shared data protects it with a *lock*. See `python-standard-library.md` for `threading`.

From this repository, `src/cited_answers/infrastructure/embeddings.py`, lines 69 to 73:

```python
        self._path = path
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
```

#### Generic functions with type parameters (Python 3.12)

`def name[T](...)` declares a *type parameter*: a stand-in for "whatever type the caller uses", so a function can promise "returns the same kind of thing it was given". `**P` declares a *parameter specification*, which stands for a whole list of parameters, used with `Concatenate` to describe a decorator that adds one argument. This is syntax new in Python 3.12, which is why the project requires 3.12.

From this repository, `src/cited_answers/infrastructure/retry.py`, lines 10 to 22:

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.

```

#### `if __name__ == "__main__"`

When a file is run directly, Python sets the special variable `__name__` to `"__main__"`. The guard makes some code run only in that case and not when the file is imported.

From this repository, `src/cited_answers/interfaces/cli.py`, lines 238 to 240:

```python
if __name__ == "__main__":
    sys.exit(main())

```

### Running the code

You never type `python src/...` in this repository. The Makefile calls the programs that pip installed into `.venv/bin`, such as `.venv/bin/cited`, or runs `.venv/bin/python -m pytest`. `python -m NAME` means "run the module called NAME as a program". The `[project.scripts]` table of `pyproject.toml` (see `pyproject-toml.md`) says which function each installed program calls.

## Try it yourself

1. Which Python the project uses.

```bash
.venv/bin/python --version
```

What you should see (captured from this repository):

```text
Python 3.13.12
```

2. Two names, one list: appending through `y` changes what `x` sees, because `y = x` copies the label, not the list.

```bash
.venv/bin/python -c "x = [1, 2, 3]; y = x; y.append(4); print(x, x is y)"
```

What you should see (captured from this repository):

```text
[1, 2, 3, 4] True
```

3. Why money uses `Decimal`: binary floating point cannot store 0.1 exactly.

```bash
.venv/bin/python -c "print(0.1 + 0.2); from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

What you should see (captured from this repository):

```text
0.30000000000000004
0.3
```

4. Type hints are not enforced when the program runs. The error here comes from the `+`, not from the hint.

```bash
.venv/bin/python -c "def f(a: int) -> int: return a + 1
print(f('x'))" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
TypeError: can only concatenate str (not "int") to str
```

5. The project is an ordinary package that Python finds through the editable install.

```bash
.venv/bin/python -c "import cited_answers; print(cited_answers.__file__)"
```

What you should see (captured from this repository):

```text
src/cited_answers/__init__.py
```

## Mistakes people make

- **Thinking `=` copies.** `b = a` makes a second label; changing a list through one name changes it for both. The code copies explicitly (`list(x)`, `dict(x)`, `dataclasses.replace`) when it needs a separate object.
- **Using `float` for money.** Prices here are `Decimal` so the totals add up exactly.
- **A mutable default argument.** `def f(x=[])` shares one list across all calls. Defaults here are `None` or immutable values.
- **Catching every exception.** A bare `except:` hides bugs. The code names the exceptions it can handle.
- **Confusing indentation.** Mixed spaces and tabs break Python. `.editorconfig` sets four spaces for `.py` files.
- **Importing the wrong direction.** An inner layer importing an outer one makes cycles and drags technology into the core. `import-linter` fails the build if that happens.

## Check yourself

1. What does `-> bool` after a function signature say?

   *Answer:* That the function returns a `bool`. It is a hint for tools and readers.

2. What does `@dataclass(frozen=True)` give you?

   *Answer:* A class with generated `__init__`, `__repr__` and `__eq__`, whose objects cannot be changed after creation.

3. Why is a `Protocol` used for `ChatModel`?

   *Answer:* So any class with the right methods (real adapter, recording, test fake) is accepted without inheriting from a base class.

4. What does `raise B from A` record?

   *Answer:* That `B` was caused by `A`, so the traceback shows both.

5. What does `if __name__ == "__main__":` do?

   *Answer:* Runs the indented code only when the file is run directly, not when imported.

## Further reading

- The Python Tutorial and Language Reference, https://docs.python.org/3.13/tutorial/ and https://docs.python.org/3.13/reference/ (the project requires Python 3.12 or newer; examples here were run on Python 3.13).
