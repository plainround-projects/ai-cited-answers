# Python source, the infrastructure layer

## What it is

This note walks through every Python file of the `infrastructure` layer of `cited_answers`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **infrastructure** layer is the adapters: the code that touches the world. Files, databases, HTTP calls to a model server, the Claude SDK, the clock, signals, logging and settings all live here. Each adapter implements a port from the application layer.

## Why this repository uses it

Keeping every contact with the outside in one layer makes it easy to swap (recorded answers instead of a live model) and to test (a fake HTTP transport instead of a network).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/infrastructure/__init__.py` | 1 non-blank lines |
| `src/cited_answers/infrastructure/anthropic_chat.py` | 102 non-blank lines |
| `src/cited_answers/infrastructure/clock.py` | 12 non-blank lines |
| `src/cited_answers/infrastructure/embeddings.py` | 105 non-blank lines |
| `src/cited_answers/infrastructure/env.py` | 53 non-blank lines |
| `src/cited_answers/infrastructure/files.py` | 63 non-blank lines |
| `src/cited_answers/infrastructure/logging.py` | 40 non-blank lines |
| `src/cited_answers/infrastructure/memory_store.py` | 24 non-blank lines |
| `src/cited_answers/infrastructure/model_factory.py` | 72 non-blank lines |
| `src/cited_answers/infrastructure/openai_compatible.py` | 109 non-blank lines |
| `src/cited_answers/infrastructure/pg_store.py` | 63 non-blank lines |
| `src/cited_answers/infrastructure/recording.py` | 79 non-blank lines |
| `src/cited_answers/infrastructure/resilient.py` | 48 non-blank lines |
| `src/cited_answers/infrastructure/retry.py` | 33 non-blank lines |
| `src/cited_answers/infrastructure/settings.py` | 53 non-blank lines |
| `src/cited_answers/infrastructure/shutdown.py` | 20 non-blank lines |
| `src/cited_answers/infrastructure/wiring.py` | 36 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/cited_answers/infrastructure/__init__.py`

In its own words: "Adapters that implement the ports: model clients, files, settings, logging."

1 non-blank lines.

`src/cited_answers/infrastructure/__init__.py`, lines 1 to 1:

```python
"""Adapters that implement the ports: model clients, files, settings, logging."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/cited_answers/infrastructure/anthropic_chat.py`

In its own words: "A chat model on the Anthropic Messages API, through the official SDK."

102 non-blank lines; it defines `_messages_payload`, `AnthropicChatModel`.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 1 to 14:

```python
"""A chat model on the Anthropic Messages API, through the official SDK.

The Messages API rejects `temperature`, `top_p` and `top_k` from API version 2026-10-21 on, so this adapter
reports `supports_sampling = False` and raises `UnsupportedParameter` if a request asks for them. Structured
output uses `output_config.format`; forced `tool_choice` is not used (newer models answer it with a 400).
"""

from __future__ import annotations

from typing import Any, Literal

import anthropic

from cited_answers.application.ports import Clock
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Any`, `Literal` from the standard library module `typing`.
- Makes the module `anthropic` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `cited_answers.application.ports`.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 15 to 26:

```python
from cited_answers.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from cited_answers.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage

Thinking = Literal["omit", "disabled", "between_tools"]

_STOP = {
    "end_turn": StopReason.END,
    "stop_sequence": StopReason.END,
    "max_tokens": StopReason.LENGTH,
    "tool_use": StopReason.TOOL_CALLS,
    "refusal": StopReason.REFUSAL,
}
```

- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `cited_answers.domain.llm`.
- Stores the part of `Literal` picked by `('omit', 'disabled', 'betwe...` under the name `Thinking`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a dictionary with 5 entries under the name `_STOP`.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 29 to 40:

```python
def _messages_payload(messages: tuple[ChatMessage, ...]) -> list[dict[str, Any]]:
    """Map neutral messages to Messages API turns; consecutive tool results share one user turn."""
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role is Role.TOOL:
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif message.role is Role.ASSISTANT and message.tool_calls:
            blocks: list[dict[str, Any]] = [{"type": "text", "text": message.content}] if message.content else []
```

- Defines the function `_messages_payload`. It returns a list of a dictionary from text to any value. The author's own description: "Map neutral messages to Messages API turns; consecutive tool results share one user turn."
- Its parameters:
    - `messages` holds a fixed list of the project type `ChatMessage` (any length).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `out` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `messages`; `message` names the current item.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Stores a dictionary with 3 entries under the name `block`.
- Decision: the indented lines below run only when `out and out[-1]['role'] == 'user' and isinstance(out[-1]['content']...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `isinstance` asks whether a value is of a given type.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `message.role is Role.ASSISTANT and message.tool_calls` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
- Declares `blocks` as a list of a dictionary from text to any value and sets it to one of two values, chosen by a condition.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `A if condition else B` gives A when the condition is true and B otherwise.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 41 to 54:

```python
            blocks.extend(
                {"type": "tool_use", "id": c.id, "name": c.name, "input": dict(c.arguments)} for c in message.tool_calls
            )
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": message.role.value, "content": message.content})
    return out


class AnthropicChatModel:
    """Calls Claude. Build the SDK client with your key from the environment; this class never reads it."""

    def __init__(self, client: anthropic.Anthropic, model: str, clock: Clock, thinking: Thinking = "disabled") -> None:
        self._client = client
```

- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `AnthropicChatModel`. The author's own description: "Calls Claude. Build the SDK client with your key from the environment; this class never reads it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `client` holds `anthropic.Anthropic`.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `thinking` holds `Thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the value named `client` under the name `self._client` (as an attribute of this object, so other methods can use it).

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 55 to 68:

```python
        self._model = model
        self._clock = clock
        self._thinking = thinking

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return False

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The keyword arguments for `messages.create` (public so tests can assert on them)."""
```

- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores the value named `thinking` under the name `self._thinking` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `False` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The keyword arguments for `messages.create` (public so tests can assert on them)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 69 to 82:

```python
        if request.temperature is not None or request.top_p is not None:
            raise UnsupportedParameter("the Messages API rejects temperature and top_p; leave them unset")
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_output_tokens,
            "messages": _messages_payload(request.messages),
        }
        if request.system:
            payload["system"] = request.system
        if self._thinking != "omit":
            payload["thinking"] = {"type": self._thinking}
        if request.response_schema is not None:
            payload["output_config"] = {"format": {"type": "json_schema", "schema": dict(request.response_schema)}}
        if request.tools:
```

- Decision: the indented lines below run only when `request.temperature is not None or request.top_p is not None` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
- Raises an error: the result of calling `UnsupportedParameter`. Execution jumps out to the nearest matching `except`.
  - `UnsupportedParameter` from the project's `cited_answers.domain.errors` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).).
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 3 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `_messages_payload`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `request.system` is true.
- Stores the `system` of `request` under the name `payload['system']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `self._thinking != 'omit'` is true.
  - `!=` means not equal.
- Stores a dictionary with 1 entry under the name `payload['thinking']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.
- Stores a dictionary with 1 entry under the name `payload['output_config']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 83 to 96:

```python
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
                for t in request.tools
            ]
        return payload

    def complete(self, request: ChatRequest) -> ChatResponse:
        payload = self.build_payload(request)
        started = self._clock.monotonic()
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
```

- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._client.messages.create` under the name `message`.
  - The method `create` of `self._client.messages`.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- `except` handler: it runs when the `try` block raised `anthropic.APIConnectionError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- `except` handler: it runs when the `try` block raised `anthropic.APIStatusError`; `error` names the error object.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 97 to 104:

```python
            if error.status_code in (408, 409, 429) or error.status_code >= 500:
                raise TransientModelError(f"HTTP {error.status_code}: {error.message}") from error
            raise PermanentModelError(f"HTTP {error.status_code}: {error.message}") from error
        elapsed = self._clock.monotonic() - started
        text = "".join(block.text for block in message.content if block.type == "text")
        calls = tuple(
            ToolCall(block.id, block.name, dict(block.input)) for block in message.content if block.type == "tool_use"
        )
```

- Decision: the indented lines below run only when `error.status_code in (408, 409, 429) or error.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Stores the result of calling `''.join` under the name `text`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `==` means equal.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 105 to 118:

```python
        return ChatResponse(
            text=text,
            stop_reason=_STOP.get(message.stop_reason or "", StopReason.OTHER),
            usage=Usage(message.usage.input_tokens, message.usage.output_tokens),
            latency_seconds=round(elapsed, 4),
            model=message.model,
            tool_calls=calls,
        )

    def count_tokens(self, request: ChatRequest) -> int:
        """Ask the provider how many input tokens a request would use (no generation, no charge)."""
        payload = self.build_payload(request)
        for unused in ("max_tokens", "thinking", "output_config"):
            payload.pop(unused, None)
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `cited_answers.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `Usage` from the project's `cited_answers.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `count_tokens`. It returns a whole number. The author's own description: "Ask the provider how many input tokens a request would use (no generation, no charge)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Loop: the indented lines below run once for each item of `('max_tokens', 'thinking', 'output_config')`; `unused` names the current item.
- Calls `.pop(...)` removes and returns an item with 2 argument(s); the result is not kept.
  - `.pop(...)` removes and returns an item.

`src/cited_answers/infrastructure/anthropic_chat.py`, lines 119 to 119:

```python
        return int(self._client.messages.count_tokens(**payload).input_tokens)
```

- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `**name` inside a call passes every entry of a dictionary as a named argument.

### `src/cited_answers/infrastructure/clock.py`

In its own words: "The real clock, behind the `Clock` port."

12 non-blank lines; it defines `SystemClock`.

`src/cited_answers/infrastructure/clock.py`, lines 1 to 13:

```python
"""The real clock, behind the `Clock` port."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime


class SystemClock:
    """Wall-clock and monotonic time from the operating system."""

    def monotonic(self) -> float:
        return time.monotonic()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `time` (standard library) available.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Defines the class `SystemClock`. The author's own description: "Wall-clock and monotonic time from the operating system."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `time.monotonic` to the caller.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.

`src/cited_answers/infrastructure/clock.py`, lines 15 to 19:

```python
    def today(self) -> date:
        return datetime.now(UTC).date()

    def now(self) -> datetime:
        return datetime.now(UTC)
```

- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now(UTC).date` to the caller.
  - The method `date` of `datetime.now(UTC)`.
  - `datetime.now` the current date and time.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now` to the caller.
  - `datetime.now` the current date and time.

### `src/cited_answers/infrastructure/embeddings.py`

In its own words: "Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording."

105 non-blank lines; it defines `text_key`, `_pack`, `_unpack`, `OpenAICompatibleEmbedder`, `EmbeddingStore`, `RecordedEmbedder`, `RecordingEmbedder`.

`src/cited_answers/infrastructure/embeddings.py`, lines 1 to 13:

```python
"""Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording."""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import threading
from collections.abc import Sequence
from pathlib import Path

import httpx
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `base64` (standard library) available.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `struct` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `httpx` (installed package) available.

`src/cited_answers/infrastructure/embeddings.py`, lines 15 to 25:

```python
from cited_answers.application.ports import Embedder
from cited_answers.domain.errors import PermanentModelError, RecordingMissing, TransientModelError


def text_key(text: str) -> str:
    """The recording key of a text: its SHA-256. The model name is not part of it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pack(vector: Sequence[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")
```

- Brings in `Embedder` (Turns texts into vectors.) from the project module `cited_answers.application.ports`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Defines the function `text_key`. It returns text. The author's own description: "The recording key of a text: its SHA-256. The model name is not part of it."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `hashlib.sha256(text.encode('utf-8')).hexdigest` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Defines the function `_pack`. It returns text.
- Its parameters:
    - `vector` holds anything that behaves like a list of a decimal number.
- Ends the function and gives back the result of calling `base64.b64encode(struct.pack(f'<{len(vector)}f'...` to the caller.
  - `.decode(...)` turns bytes into text.
  - `base64.b64encode` turns bytes into base64 text.
  - `struct.pack` packs numbers into bytes.
  - `*name` inside a call passes every item of a collection as a separate argument.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).

`src/cited_answers/infrastructure/embeddings.py`, lines 28 to 39:

```python
def _unpack(blob: str) -> list[float]:
    raw = base64.b64decode(blob)
    return list(struct.unpack(f"<{len(raw) // 4}f", raw))


class OpenAICompatibleEmbedder:
    """Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, api_key: str | None = None) -> None:
        self._http = http
        self._url = f"{base_url.rstrip('/')}/embeddings"
        self._model = model
```

- Defines the function `_unpack`. It returns a list of a decimal number.
- Its parameters:
    - `blob` holds text.
- Stores the result of calling `base64.b64decode` under the name `raw`.
  - `base64.b64decode` turns base64 text into bytes.
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
  - `struct.unpack` unpacks bytes into numbers.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `//` is divide and drop the fraction.
  - `len` counts the items in a collection (or the characters in text).
- Defines the class `OpenAICompatibleEmbedder`. The author's own description: "Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `model` holds text.
    - `api_key` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores a text built from pieces (an f-string) under the name `self._url` (as an attribute of this object, so other methods can use it).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).

`src/cited_answers/infrastructure/embeddings.py`, lines 40 to 53:

```python
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            reply = self._http.post(self._url, json={"model": self._model, "input": list(texts)}, headers=self._headers)
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
```

- Stores one of two values, chosen by a condition under the name `self._headers` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.post` under the name `reply`.
  - `post` on the stored object `self._http`: it sends an HTTP POST request.
  - `list` makes a list (a copy when given a collection).
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Decision: the indented lines below run only when `reply.status_code == 429 or reply.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.

`src/cited_answers/infrastructure/embeddings.py`, lines 54 to 66:

```python
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
        try:
            data = sorted(reply.json()["data"], key=lambda item: item["index"])
            vectors = [[float(x) for x in item["embedding"]] for item in data]
        except (KeyError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected embeddings response: {error!r}") from error
        if len(vectors) != len(texts):
            raise PermanentModelError(f"asked for {len(texts)} embeddings, got {len(vectors)}")
        return vectors


class EmbeddingStore:
    """A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded."""
```

- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `sorted` under the name `data`.
  - `sorted` returns a new list with the items in order.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `lambda args: expression` is a small unnamed function written inline.
- Stores a list built by looping under the name `vectors`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `float` turns a value into a decimal number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, TypeError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `len(vectors) != len(texts)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the value named `vectors` to the caller.
- Defines the class `EmbeddingStore`. The author's own description: "A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/embeddings.py`, lines 68 to 79:

```python
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._vectors[entry["key"]] = _unpack(entry["vector"])
        self._append_to = path / "embeddings.jsonl" if path.is_dir() else path
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.Lock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.Lock` makes a lock.
- Declares `self._vectors` as a dictionary from text to a list of a decimal number and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `files`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `.exists(...)` asks whether the path exists.
- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- A `with` block: it sets up `file.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `file`.
- Loop: the indented lines below run once for each item of `handle`; `line` names the current item.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `_unpack` under the name `self._vectors[entry['key']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_unpack`, a function defined in this file or passed in.
- Stores one of two values, chosen by a condition under the name `self._append_to` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `/` is divide.

`src/cited_answers/infrastructure/embeddings.py`, lines 81 to 93:

```python
    def __len__(self) -> int:
        return len(self._vectors)

    def get(self, key: str) -> list[float] | None:
        return self._vectors.get(key)

    def put(self, key: str, vector: Sequence[float], model: str) -> None:
        with self._lock:
            self._vectors[key] = list(vector)
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "model": model, "vector": _pack(vector)}) + "\n")
                handle.flush()
```

- Defines the method `__len__`. It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `get`. It returns a list of a decimal number, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
- Ends the function and gives back the result of calling `self._vectors.get` to the caller.
  - `get` on the stored object `self._vectors`: it reads a dictionary entry, giving a default when the key is missing.
- Defines the method `put`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `vector` holds anything that behaves like a list of a decimal number.
    - `model` holds text.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `list` under the name `self._vectors[key]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `list` makes a list (a copy when given a collection).
- Calls `mkdir` on the stored object `self._append_to.parent`: it creates a folder with 2 argument(s); the result is not kept.
  - `mkdir` on the stored object `self._append_to.parent`: it creates a folder.
- A `with` block: it sets up `self._append_to.open('a', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._append_to`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
  - `_pack`, a function defined in this file or passed in.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.

`src/cited_answers/infrastructure/embeddings.py`, lines 96 to 107:

```python
class RecordedEmbedder:
    """Replays recorded vectors. A text nobody embedded raises `RecordingMissing`."""

    def __init__(self, store: EmbeddingStore, name: str = "recorded") -> None:
        self._store = store
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
```

- Defines the class `RecordedEmbedder`. The author's own description: "Replays recorded vectors. A text nobody embedded raises `RecordingMissing`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `EmbeddingStore`.
    - `name` holds text; if the caller leaves it out it is the text `recorded`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Stores the value named `name` under the name `self._name` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_name` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.

`src/cited_answers/infrastructure/embeddings.py`, lines 108 to 121:

```python
        out: list[list[float]] = []
        for text in texts:
            vector = self._store.get(text_key(text))
            if vector is None:
                raise RecordingMissing(
                    f"no recorded embedding for a text of {len(text)} characters starting {text[:40]!r}; "
                    "run `make record` against the embedding model to refresh the fixtures"
                )
            out.append(vector)
        return out


class RecordingEmbedder:
    """Wraps a live embedder and writes each new vector into the recording; known texts are replayed."""
```

- Declares `out` as a list of a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `texts`; `text` names the current item.
- Stores the result of calling `self._store.get` under the name `vector`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `vector is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `RecordingMissing`. Execution jumps out to the nearest matching `except`.
  - `RecordingMissing` from the project's `cited_answers.domain.errors` (The recorded adapter has no response for this request. Re-record with `make record`.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `RecordingEmbedder`. The author's own description: "Wraps a live embedder and writes each new vector into the recording; known texts are replayed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/embeddings.py`, lines 123 to 135:

```python
    def __init__(self, inner: Embedder, store: EmbeddingStore) -> None:
        self._inner = inner
        self._store = store

    @property
    def name(self) -> str:
        return self._inner.name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        unknown = [t for t in dict.fromkeys(texts) if self._store.get(text_key(t)) is None]
        if unknown:
            for text, vector in zip(unknown, self._inner.embed(unknown), strict=True):
                self._store.put(text_key(text), vector, self._inner.name)
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `Embedder`.
    - `store` holds the project type `EmbeddingStore`.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- Stores a list built by looping under the name `unknown`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `fromkeys` of `dict`.
  - `is` means the very same object.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `unknown` is true.
- Loop: the indented lines below run once for each item of `zip(unknown, self._inner.embed(unknown), strict=True)`; `(text, vector)` names the current item.
  - `zip` walks several collections side by side, item by item.
  - The method `embed` of `self._inner`.
- Calls `put` on the stored object `self._store`: it sends an HTTP PUT request with 3 argument(s); the result is not kept.
  - `put` on the stored object `self._store`: it sends an HTTP PUT request.
  - `text_key`, a function defined in this file or passed in.

`src/cited_answers/infrastructure/embeddings.py`, lines 136 to 136:

```python
        return [self._store.get(text_key(t)) or [] for t in texts]
```

- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.

### `src/cited_answers/infrastructure/env.py`

In its own words: "Helpers that read and validate environment variables (twelve-factor configuration)."

53 non-blank lines; it defines `ConfigurationError`, `text`, `optional_text`, `positive_int`, `non_negative_int`, `positive_float`, `non_negative_float`, `choice`.

`src/cited_answers/infrastructure/env.py`, lines 1 to 14:

```python
"""Helpers that read and validate environment variables (twelve-factor configuration)."""

from __future__ import annotations

from collections.abc import Collection, Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def text(environ: Mapping[str, str], name: str, default: str) -> str:
    """A non-empty string, or `default` when the variable is unset."""
    value = environ.get(name, default).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Collection`, `Mapping` from the standard library module `collections.abc`.
- Defines the class `ConfigurationError`. It builds on `ValueError`. The author's own description: "An environment variable is missing or has an unusable value."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the function `text`. It returns text. The author's own description: "A non-empty string, or `default` when the variable is unset."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, default).strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/cited_answers/infrastructure/env.py`, lines 15 to 28:

```python
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value


def optional_text(environ: Mapping[str, str], name: str) -> str | None:
    """The variable's text, or None when it is unset or blank."""
    value = environ.get(name, "").strip()
    return value or None


def positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 1 or more."""
    raw = environ.get(name, str(default)).strip()
```

- Decision: the indented lines below run only when `not value` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `optional_text`. It returns text, or nothing (None). The author's own description: "The variable's text, or None when it is unset or blank."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, '').strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of combining conditions: `value or None` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the function `positive_int`. It returns a whole number. The author's own description: "An integer of 1 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/cited_answers/infrastructure/env.py`, lines 29 to 42:

```python
    if not raw.isdigit() or int(raw) < 1:
        raise ConfigurationError(f"{name} must be a positive integer, got {raw!r}")
    return int(raw)


def non_negative_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 0 or more."""
    raw = environ.get(name, str(default)).strip()
    if not raw.isdigit():
        raise ConfigurationError(f"{name} must be a non-negative integer, got {raw!r}")
    return int(raw)


def positive_float(environ: Mapping[str, str], name: str, default: float) -> float:
```

- Decision: the indented lines below run only when `not raw.isdigit() or int(raw) < 1` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `<` means less than.
  - `.isdigit(...)` asks whether text is only digits.
  - `int` turns a value into a whole number.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `non_negative_int`. It returns a whole number. The author's own description: "An integer of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- Decision: the indented lines below run only when `not raw.isdigit()` is true.
  - `not` flips true and false.
  - `.isdigit(...)` asks whether text is only digits.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `positive_float`. It returns a decimal number. The author's own description: "A number greater than zero."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.

`src/cited_answers/infrastructure/env.py`, lines 43 to 56:

```python
    """A number greater than zero."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero, got {raw!r}")
    return value


def non_negative_float(environ: Mapping[str, str], name: str, default: float) -> float:
    """A number of 0 or more."""
    raw = environ.get(name, str(default)).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value <= 0` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `non_negative_float`. It returns a decimal number. The author's own description: "A number of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/cited_answers/infrastructure/env.py`, lines 57 to 70:

```python
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value < 0:
        raise ConfigurationError(f"{name} must not be negative, got {raw!r}")
    return value


def choice(environ: Mapping[str, str], name: str, default: str, allowed: Collection[str]) -> str:
    """One of the `allowed` strings."""
    value = text(environ, name, default)
    if value not in allowed:
        raise ConfigurationError(f"{name} must be one of {sorted(allowed)}, got {value!r}")
```

- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value < 0` is true.
  - `<` means less than.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `choice`. It returns text. The author's own description: "One of the `allowed` strings."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
    - `allowed` holds a collection with a size of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `text` under the name `value`.
  - `text`, a function of this file (A non-empty string, or `default` when the variable is unset.).
- Decision: the indented lines below run only when `value not in allowed` is true.
  - `not in` means is not contained in.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sorted` returns a new list with the items in order.

`src/cited_answers/infrastructure/env.py`, lines 71 to 71:

```python
    return value
```

- Ends the function and gives back the value named `value` to the caller.

### `src/cited_answers/infrastructure/files.py`

In its own words: "Readers for the page files, the question files, the prompt files and the threshold file."

63 non-blank lines; it defines `FilePageSource`, `FileQuestionSource`, `FilePromptStore`, `read_threshold`.

`src/cited_answers/infrastructure/files.py`, lines 1 to 13:

```python
"""Readers for the page files, the question files, the prompt files and the threshold file."""

from __future__ import annotations

import json
import re
from pathlib import Path

from cited_answers.domain.evaluation import InvalidQuestions, Question, QuestionType
from cited_answers.domain.pages import Page, parse_page
from cited_answers.domain.prompts import Prompt, PromptNotFound

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `InvalidQuestions` (The question file breaks a rule of the lesson.), `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.) from the project module `cited_answers.domain.evaluation`.
- Brings in `Page` (One help-center page.), `parse_page` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.) from the project module `cited_answers.domain.pages`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.), `PromptNotFound` (No prompt file for that name and version, or the file's version line does not match.) from the project module `cited_answers.domain.prompts`.
- Stores the result of calling `re.compile` under the name `_FRONT_MATTER`.
  - `re.compile` prepares a regular expression.

`src/cited_answers/infrastructure/files.py`, lines 16 to 27:

```python
class FilePageSource:
    """Every `*.md` file in a folder is a page."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def pages(self) -> list[Page]:
        return [parse_page(path.read_text(encoding="utf-8")) for path in sorted(self._folder.glob("*.md"))]


class FileQuestionSource:
    """`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number."""
```

- Defines the class `FilePageSource`. The author's own description: "Every `*.md` file in a folder is a page."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `folder` holds a file path.
- Stores the value named `folder` under the name `self._folder` (as an attribute of this object, so other methods can use it).
- Defines the method `pages`. It returns a list of the project type `Page`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `parse_page` from the project's `cited_answers.domain.pages` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.).
  - `.read_text(...)` reads a whole file as text.
  - `sorted` returns a new list with the items in order.
  - `glob` on the stored object `self._folder`: it finds files whose names match a pattern.
- Defines the class `FileQuestionSource`. The author's own description: "`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/files.py`, lines 29 to 40:

```python
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
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `folder` holds a file path.
- Stores the value named `folder` under the name `self._folder` (as an attribute of this object, so other methods can use it).
- Defines the method `load`. It returns a list of the project type `Question`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `split` holds text.
- Stores the result of `self._folder / f'{split}.jsonl'` under the name `path`.
  - `/` is divide.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Declares `questions` as a list of the project type `Question` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- A `with` block: it sets up `path.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `path`.
- Loop: the indented lines below run once for each item of `enumerate(handle, start=1)`; `(number, line)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Decision: the indented lines below run only when `not line.strip()` is true.
  - `not` flips true and false.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Skips the rest of this round of the loop and starts the next.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `json.loads` under the name `row`.
  - `json.loads` turns JSON text into Python data.

`src/cited_answers/infrastructure/files.py`, lines 41 to 53:

```python
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
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `Question` from the project's `cited_answers.domain.evaluation` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `QuestionType` from the project's `cited_answers.domain.evaluation` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.).
  - `bool` turns a value into true or false.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- `except` handler: it runs when the `try` block raised `(json.JSONDecodeError, KeyError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `InvalidQuestions`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidQuestions` from the project's `cited_answers.domain.evaluation` (The question file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `questions` to the caller.

`src/cited_answers/infrastructure/files.py`, lines 56 to 67:

```python
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
```

- Defines the class `FilePromptStore`. The author's own description: "Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `root` holds a file path.
- Stores the value named `root` under the name `self._root` (as an attribute of this object, so other methods can use it).
- Defines the method `load`. It returns the project type `Prompt`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
    - `version` holds text.
- Stores the result of `self._root / name / f'{version}.md'` under the name `path`.
  - `/` is divide.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `not path.exists()` is true.
  - `not` flips true and false.
  - `.exists(...)` asks whether the path exists.
- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `cited_answers.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `_FRONT_MATTER.match` under the name `match`.
  - `.match(...)` tries a regular expression at the start of text.
  - `.read_text(...)` reads a whole file as text.
- Decision: the indented lines below run only when `not match` is true.
  - `not` flips true and false.

`src/cited_answers/infrastructure/files.py`, lines 68 to 81:

```python
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
```

- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `cited_answers.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `dict` under the name `header`.
  - `dict` makes a dictionary (a copy when given one).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `.splitlines(...)` cuts text into a list of lines.
  - `in` means is contained in.
  - `.group(...)` reads a captured part of a regular-expression match.
- Decision: the indented lines below run only when `header.get('version', '').strip() != version` is true.
  - `!=` means not equal.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `cited_answers.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `Prompt` to the caller.
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.group(...)` reads a captured part of a regular-expression match.
- Defines the function `read_threshold`. It returns a decimal number, or nothing (None). The author's own description: "The tuned refusal threshold, if `evals/threshold.json` exists."
- Its parameters:
    - `path` holds a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `not path.exists()` is true.
  - `not` flips true and false.
  - `.exists(...)` asks whether the path exists.
- Ends the function and gives back nothing (`None`) to the caller.
- Ends the function and gives back the result of calling `float` to the caller.
  - `float` turns a value into a decimal number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
  - `.read_text(...)` reads a whole file as text.

### `src/cited_answers/infrastructure/logging.py`

In its own words: "Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`)."

40 non-blank lines; it defines `_quote`, `LogfmtFormatter`, `fields`, `configure_logging`.

`src/cited_answers/infrastructure/logging.py`, lines 1 to 13:

```python
"""Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`).

Prompt and completion text never goes into an INFO line. Log sizes, ids, hashes and counts; a DEBUG line may
carry text for a developer who asked for it.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `UTC`, `datetime` from the standard library module `datetime`.
- Brings in `Any`, `TextIO` from the standard library module `typing`.

`src/cited_answers/infrastructure/logging.py`, lines 16 to 25:

```python
def _quote(value: object) -> str:
    text = str(value)
    return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text


class LogfmtFormatter(logging.Formatter):
    """Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
```

- Defines the function `_quote`. It returns text.
- Its parameters:
    - `value` holds any object.
- Stores the result of calling `str` under the name `text`.
  - `str` turns a value into text.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `json.dumps` turns Python data into JSON text.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.
- Defines the class `LogfmtFormatter`. It builds on the logging `Formatter` (turns a record into text). The author's own description: "Format a log record as one logfmt line, with the record's extra fields as key=value pairs."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `format`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `record` holds `logging.LogRecord`.
- Stores the result of calling `datetime.fromtimestamp(record.created, tz=UTC)....` under the name `timestamp`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `datetime.fromtimestamp` from the standard library module `datetime`.

`src/cited_answers/infrastructure/logging.py`, lines 26 to 39:

```python
        parts = [
            f"ts={timestamp}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={_quote(record.getMessage())}",
        ]
        parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
        if record.exc_info:
            parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


def fields(**values: Any) -> dict[str, Any]:
    """Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."""
```

- Stores a list of 4 item(s) under the name `parts`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `getMessage` of `record`.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `_quote`, a function defined in this file or passed in.
  - `getattr` reads an attribute whose name is held in a variable.
- Decision: the indented lines below run only when `record.exc_info` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `formatException` of `self`.
- Ends the function and gives back the result of calling `' '.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `fields`. It returns a dictionary from text to any value. The author's own description: "Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."
- Its parameters:
    - `**values` collects any extra named arguments into a dictionary.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/logging.py`, lines 40 to 52:

```python
    return {"fields": values}


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    """Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(LogfmtFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    quiet = max(logging.getLevelName(level), logging.WARNING)
    for noisy in ("httpx", "httpx2", "httpcore", "httpcore2", "anthropic"):
        logging.getLogger(noisy).setLevel(quiet)
```

- Ends the function and gives back a dictionary with 1 entry to the caller.
- Defines the function `configure_logging`. It returns nothing (None). The author's own description: "Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."
- Its parameters:
    - `level` holds text.
    - `stream` holds an open text file, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `logging.StreamHandler` under the name `handler`.
  - `logging.StreamHandler` from the standard library module `logging`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Calls the method `setFormatter` of `handler` with 1 argument(s); the result is not kept.
  - The method `setFormatter` of `handler`.
  - `LogfmtFormatter`, a class of this project (Format a log record as one logfmt line, with the record's extra fields as key=value pairs.).
- Stores the result of calling `logging.getLogger` under the name `root`.
  - `logging.getLogger` gets the logger with the given name.
- Stores a list of 1 item(s) under the name `root.handlers[:]`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Calls the method `setLevel` of `root` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `root`.
- Stores the result of calling `max` under the name `quiet`.
  - `max` picks the largest value.
  - `logging.getLevelName` from the standard library module `logging`.
- Loop: the indented lines below run once for each item of `('httpx', 'httpx2', 'httpcore', 'httpcore2', 'anthropic')`; `noisy` names the current item.
- Calls the method `setLevel` of `logging.getLogger(noisy)` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `logging.getLogger(noisy)`.
  - `logging.getLogger` gets the logger with the given name.

### `src/cited_answers/infrastructure/memory_store.py`

In its own words: "An in-memory chunk store: the test double and the default for offline runs."

24 non-blank lines; it defines `InMemoryChunkStore`.

`src/cited_answers/infrastructure/memory_store.py`, lines 1 to 14:

```python
"""An in-memory chunk store: the test double and the default for offline runs."""

from __future__ import annotations

from collections.abc import Sequence

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.retrieval import cosine


class InMemoryChunkStore:
    """Chunks and vectors in lists; search is a linear scan, which is plenty for a help center."""

    def __init__(self) -> None:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Brings in `cosine` (Cosine similarity of two vectors (0.0 if either is all zeros).) from the project module `cited_answers.domain.retrieval`.
- Defines the class `InMemoryChunkStore`. The author's own description: "Chunks and vectors in lists; search is a linear scan, which is plenty for a help center."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/cited_answers/infrastructure/memory_store.py`, lines 15 to 28:

```python
        self._chunks: list[Chunk] = []
        self._vectors: dict[str, list[float]] = {}

    def replace_all(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("one vector per chunk")
        self._chunks = list(chunks)
        self._vectors = {c.id: list(v) for c, v in zip(chunks, vectors, strict=True)}

    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        scored = [(chunk_id, cosine(vector, stored)) for chunk_id, stored in self._vectors.items()]
```

- Declares `self._chunks` as a list of the project type `Chunk` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `self._vectors` as a dictionary from text to a list of a decimal number and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `replace_all`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `chunks` holds anything that behaves like a list of the project type `Chunk`.
    - `vectors` holds anything that behaves like a list of anything that behaves like a list of a decimal number.
- Decision: the indented lines below run only when `len(chunks) != len(vectors)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Stores the result of calling `list` under the name `self._chunks` (as an attribute of this object, so other methods can use it).
  - `list` makes a list (a copy when given a collection).
- Stores a dictionary built by looping under the name `self._vectors` (as an attribute of this object, so other methods can use it).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `list` makes a list (a copy when given a collection).
  - `zip` walks several collections side by side, item by item.
- Defines the method `chunks`. It returns a list of the project type `Chunk`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
- Defines the method `vector_search`. It returns a list of a fixed list of text, a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `k` holds a whole number.
- Stores a list built by looping under the name `scored`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
  - `items` on the stored object `self._vectors`: it gives the key and value pairs of a dictionary.

`src/cited_answers/infrastructure/memory_store.py`, lines 29 to 34:

```python
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:k]

    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        return {
            chunk_id: cosine(vector, self._vectors[chunk_id]) for chunk_id in chunk_ids if chunk_id in self._vectors
        }
```

- Ends the function and gives back the part of `sorted(scored, key=lambda i...` picked by `:k` to the caller.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `sorted` returns a new list with the items in order.
  - `lambda args: expression` is a small unnamed function written inline.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `similarities`. It returns a dictionary from text to a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `chunk_ids` holds anything that behaves like a list of text.
- Ends the function and gives back a dictionary built by looping to the caller.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `in` means is contained in.

### `src/cited_answers/infrastructure/model_factory.py`

In its own words: "Builds the configured chat model from the environment: recorded, local server or Claude."

72 non-blank lines; it defines `ModelSettings`, `build_chat_model`.

`src/cited_answers/infrastructure/model_factory.py`, lines 1 to 14:

```python
"""Builds the configured chat model from the environment: recorded, local server or Claude."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import anthropic
import httpx

from cited_answers.application.ports import ChatModel, Clock
from cited_answers.infrastructure.anthropic_chat import AnthropicChatModel, Thinking
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx` (installed package) available.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `Clock` (Time, injected so tests are deterministic.) from the project module `cited_answers.application.ports`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.), `Thinking` from the project module `cited_answers.infrastructure.anthropic_chat`.

`src/cited_answers/infrastructure/model_factory.py`, lines 15 to 27:

```python
from cited_answers.infrastructure.env import (
    ConfigurationError,
    choice,
    optional_text,
    positive_float,
    positive_int,
    text,
)
from cited_answers.infrastructure.openai_compatible import OpenAICompatibleChatModel
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from cited_answers.infrastructure.resilient import RetryingChatModel

PROVIDERS = ("recorded", "anthropic", "openai-compatible")
```

- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_float` (A number greater than zero.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `cited_answers.infrastructure.env`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `cited_answers.infrastructure.openai_compatible`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `cited_answers.infrastructure.recording`.
- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `cited_answers.infrastructure.resilient`.
- Stores a tuple of 3 item(s) under the name `PROVIDERS`.

`src/cited_answers/infrastructure/model_factory.py`, lines 30 to 41:

```python
@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Which model to call and how. See .env.example for every variable."""

    provider: str
    model: str
    recordings: Path
    record: bool
    openai_base_url: str
    openai_api_key: str | None
    anthropic_thinking: Thinking
    timeout_seconds: float
```

- Defines the class `ModelSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Which model to call and how. See .env.example for every variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `provider` as text; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `recordings` as a file path; it has no default, so a value must be given when the object is made.
- Declares `record` as true or false; it has no default, so a value must be given when the object is made.
- Declares `openai_base_url` as text; it has no default, so a value must be given when the object is made.
- Declares `openai_api_key` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `anthropic_thinking` as `Thinking`; it has no default, so a value must be given when the object is made.
- Declares `timeout_seconds` as a decimal number; it has no default, so a value must be given when the object is made.

`src/cited_answers/infrastructure/model_factory.py`, lines 42 to 51:

```python
    attempts: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ModelSettings:
        env = os.environ if environ is None else environ
        provider = choice(env, "MODEL_PROVIDER", "recorded", PROVIDERS)
        default_model = {"recorded": "recorded", "anthropic": "claude-haiku-5-5", "openai-compatible": "qwen2.5:0.5b"}[
            provider
        ]
        thinking = choice(env, "ANTHROPIC_THINKING", "disabled", ("omit", "disabled", "between_tools"))
```

- Declares `attempts` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ModelSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of calling `choice` under the name `provider`.
  - `choice` from the project's `cited_answers.infrastructure.env` (One of the `allowed` strings.).
- Stores the part of `{'recorded': 'recorded', 'a...` picked by `provider` under the name `default_model`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `choice` under the name `thinking`.
  - `choice` from the project's `cited_answers.infrastructure.env` (One of the `allowed` strings.).

`src/cited_answers/infrastructure/model_factory.py`, lines 52 to 65:

```python
        return cls(
            provider=provider,
            model=text(env, "MODEL_NAME", default_model),
            recordings=Path(text(env, "RECORDINGS_PATH", "tests/fixtures/recordings")),
            record=choice(env, "RECORD", "off", ("on", "off")) == "on",
            openai_base_url=text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
            openai_api_key=optional_text(env, "OPENAI_API_KEY"),
            anthropic_thinking=thinking,  # type: ignore[arg-type]
            timeout_seconds=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0),
            attempts=positive_int(env, "MODEL_ATTEMPTS", 3),
        )


def build_chat_model(settings: ModelSettings, clock: Clock, environ: Mapping[str, str] | None = None) -> ChatModel:
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `text` from the project's `cited_answers.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `==` means equal.
  - `optional_text` from the project's `cited_answers.infrastructure.env` (The variable's text, or None when it is unset or blank.).
  - `positive_float` from the project's `cited_answers.infrastructure.env` (A number greater than zero.).
  - `positive_int` from the project's `cited_answers.infrastructure.env` (An integer of 1 or more.).
  - `choice` from the project's `cited_answers.infrastructure.env` (One of the `allowed` strings.).
- Defines the function `build_chat_model`. It returns the project type `ChatModel`. The author's own description: "Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."
- Its parameters:
    - `settings` holds the project type `ModelSettings`.
    - `clock` holds the project type `Clock`.
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).

`src/cited_answers/infrastructure/model_factory.py`, lines 66 to 79:

```python
    """Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."""
    env = os.environ if environ is None else environ
    if settings.provider == "recorded":
        return RecordedChatModel(RecordingStore(settings.recordings))
    live: ChatModel
    if settings.provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY must be set in the environment to use the anthropic provider")
        client = anthropic.Anthropic(timeout=settings.timeout_seconds, max_retries=0)
        live = AnthropicChatModel(client, settings.model, clock, settings.anthropic_thinking)
    else:
        http = httpx.Client(timeout=settings.timeout_seconds)
        live = OpenAICompatibleChatModel(http, settings.openai_base_url, settings.model, clock, settings.openai_api_key)
    live = RetryingChatModel(live, attempts=settings.attempts)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Decision: the indented lines below run only when `settings.provider == 'recorded'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `RecordedChatModel` to the caller.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Declares `live` as the project type `ChatModel`.
- Decision: the indented lines below run only when `settings.provider == 'anthropic'` is true.
  - `==` means equal.
- Decision: the indented lines below run only when `not env.get('ANTHROPIC_API_KEY')` is true.
  - `not` flips true and false.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `cited_answers.infrastructure.env` (An environment variable is missing or has an unusable value.).
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
- Stores the result of calling `AnthropicChatModel` under the name `live`.
  - `AnthropicChatModel` from the project's `cited_answers.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
- Stores the result of calling `OpenAICompatibleChatModel` under the name `live`.
  - `OpenAICompatibleChatModel` from the project's `cited_answers.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
- Stores the result of calling `RetryingChatModel` under the name `live`.
  - `RetryingChatModel` from the project's `cited_answers.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).

`src/cited_answers/infrastructure/model_factory.py`, lines 80 to 83:

```python
    if settings.record:
        note = {"provider": settings.provider, "requested_model": settings.model}
        return RecordingChatModel(live, RecordingStore(settings.recordings), note)
    return live
```

- Decision: the indented lines below run only when `settings.record` is true.
- Stores a dictionary with 2 entries under the name `note`.
- Ends the function and gives back the result of calling `RecordingChatModel` to the caller.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Ends the function and gives back the value named `live` to the caller.

### `src/cited_answers/infrastructure/openai_compatible.py`

In its own words: "A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."

109 non-blank lines; it defines `_message_payload`, `OpenAICompatibleChatModel`, `_arguments`.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 1 to 12:

```python
"""A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from cited_answers.application.ports import Clock
from cited_answers.domain.errors import PermanentModelError, TransientModelError
from cited_answers.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `cited_answers.application.ports`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `cited_answers.domain.llm`.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 14 to 26:

```python
_FINISH = {
    "stop": StopReason.END,
    "length": StopReason.LENGTH,
    "tool_calls": StopReason.TOOL_CALLS,
    "content_filter": StopReason.REFUSAL,
}


def _message_payload(message: ChatMessage) -> dict[str, Any]:
    if message.role is Role.TOOL:
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
    payload: dict[str, Any] = {"role": message.role.value, "content": message.content}
    if message.tool_calls:
```

- Stores a dictionary with 4 entries under the name `_FINISH`.
- Defines the function `_message_payload`. It returns a dictionary from text to any value.
- Its parameters:
    - `message` holds the project type `ChatMessage`.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Ends the function and gives back a dictionary with 3 entries to the caller.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 2 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `message.tool_calls` is true.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 27 to 40:

```python
        payload["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(dict(c.arguments))}}
            for c in message.tool_calls
        ]
    return payload


class OpenAICompatibleChatModel:
    """Talks to any server that implements `POST {base_url}/chat/completions`."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, clock: Clock, api_key: str | None = None) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._model = model
```

- Stores a list built by looping under the name `payload['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `json.dumps` turns Python data into JSON text.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the class `OpenAICompatibleChatModel`. The author's own description: "Talks to any server that implements `POST {base_url}/chat/completions`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `api_key` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `base_url.rstrip` under the name `self._base_url` (as an attribute of this object, so other methods can use it).
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).

`src/cited_answers/infrastructure/openai_compatible.py`, lines 41 to 54:

```python
        self._clock = clock
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return True

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The JSON body for a request (public so tests can assert on it)."""
        messages: list[dict[str, Any]] = []
```

- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores one of two values, chosen by a condition under the name `self._headers` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The JSON body for a request (public so tests can assert on it)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 55 to 68:

```python
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(_message_payload(m) for m in request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_schema is not None:
```

- Decision: the indented lines below run only when `request.system` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `_message_payload`, a function defined in this file or passed in.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Decision: the indented lines below run only when `request.temperature is not None` is true.
  - `is not` means not the same object.
- Stores the `temperature` of `request` under the name `payload['temperature']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.top_p is not None` is true.
  - `is not` means not the same object.
- Stores the `top_p` of `request` under the name `payload['top_p']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 69 to 81:

```python
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": dict(request.response_schema), "strict": True},
            }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": dict(t.parameters)},
                }
                for t in request.tools
            ]
        return payload
```

- Stores a dictionary with 2 entries under the name `payload['response_format']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.
- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 83 to 95:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        started = self._clock.monotonic()
        try:
            reply = self._http.post(
                f"{self._base_url}/chat/completions", json=self.build_payload(request), headers=self._headers
            )
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        elapsed = self._clock.monotonic() - started
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
```

- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.post` under the name `reply`.
  - `post` on the stored object `self._http`: it sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `build_payload` of this object (The JSON body for a request (public so tests can assert on it).).
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Decision: the indented lines below run only when `reply.status_code == 429 or reply.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 96 to 107:

```python
        return self._parse(reply.json(), elapsed)

    def _parse(self, body: dict[str, Any], elapsed: float) -> ChatResponse:
        try:
            choice = body["choices"][0]
            message = choice["message"]
            usage = body["usage"]
            calls = tuple(
                ToolCall(str(c.get("id", f"call_{i}")), c["function"]["name"], _arguments(c["function"]["arguments"]))
                for i, c in enumerate(message.get("tool_calls") or [])
            )
            stop = StopReason.TOOL_CALLS if calls else _FINISH.get(choice.get("finish_reason") or "", StopReason.OTHER)
```

- Ends the function and gives back the result of calling `self._parse` to the caller.
  - The method `_parse` of this object.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the method `_parse`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `body` holds a dictionary from text to any value.
    - `elapsed` holds a decimal number.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the part of `body['choices']` picked by `0` under the name `choice`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `choice` picked by `'message'` under the name `message`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `body` picked by `'usage'` under the name `usage`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_arguments`, a function defined in this file or passed in.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores one of two values, chosen by a condition under the name `stop`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/cited_answers/infrastructure/openai_compatible.py`, lines 108 to 121:

```python
            return ChatResponse(
                text=message.get("content") or "",
                stop_reason=stop,
                usage=Usage(int(usage["prompt_tokens"]), int(usage["completion_tokens"])),
                latency_seconds=round(elapsed, 4),
                model=str(body.get("model", self._model)),
                tool_calls=calls,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected response shape: {error!r}") from error


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `cited_answers.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `Usage` from the project's `cited_answers.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `int` turns a value into a whole number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, IndexError, TypeError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `cited_answers.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_arguments`. It returns a dictionary from text to any value.
- Its parameters:
    - `raw` holds any value.
- Decision: the indented lines below run only when `isinstance(raw, dict)` is true.
  - `isinstance` asks whether a value is of a given type.

`src/cited_answers/infrastructure/openai_compatible.py`, lines 122 to 126:

```python
        return raw
    parsed = json.loads(raw) if raw else {}
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed
```

- Ends the function and gives back the value named `raw` to the caller.
- Stores one of two values, chosen by a condition under the name `parsed`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `json.loads` turns JSON text into Python data.
- Decision: the indented lines below run only when `not isinstance(parsed, dict)` is true.
  - `not` flips true and false.
  - `isinstance` asks whether a value is of a given type.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Ends the function and gives back the value named `parsed` to the caller.

### `src/cited_answers/infrastructure/pg_store.py`

In its own words: "The chunk store on Postgres with the pgvector extension (see sql/001_schema.sql)."

63 non-blank lines; it defines `vector_literal`, `PgVectorChunkStore`.

`src/cited_answers/infrastructure/pg_store.py`, lines 1 to 14:

```python
"""The chunk store on Postgres with the pgvector extension (see sql/001_schema.sql)."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.errors import TransientModelError
from cited_answers.domain.pages import PageStatus


def vector_literal(vector: Sequence[float]) -> str:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Makes the module `psycopg` (installed package) available.
- Brings in `Chunk` (A passage a reader can open: the page it came from, its heading path, its date and its status.) from the project module `cited_answers.domain.chunking`.
- Brings in `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.) from the project module `cited_answers.domain.pages`.
- Defines the function `vector_literal`. It returns text. The author's own description: "pgvector's text form of a vector: `[0.1,0.2,...]`."
- Its parameters:
    - `vector` holds anything that behaves like a list of a decimal number.

`src/cited_answers/infrastructure/pg_store.py`, lines 15 to 28:

```python
    """pgvector's text form of a vector: `[0.1,0.2,...]`."""
    return "[" + ",".join(f"{x:.8g}" for x in vector) + "]"


class PgVectorChunkStore:
    """Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self) -> psycopg.Connection:
        try:
            return psycopg.connect(self._dsn, connect_timeout=5)
        except psycopg.OperationalError as error:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of `'[' + ','.join((f'{x:.8g}' for x in vector)) + ']'` to the caller.
  - `+` is add.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the class `PgVectorChunkStore`. The author's own description: "Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `dsn` holds text.
- Stores the value named `dsn` under the name `self._dsn` (as an attribute of this object, so other methods can use it).
- Defines the method `_connect`. It returns `psycopg.Connection`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `psycopg.connect` to the caller.
  - `psycopg.connect` opens a connection to PostgreSQL.
- `except` handler: it runs when the `try` block raised `psycopg.OperationalError`; `error` names the error object.

`src/cited_answers/infrastructure/pg_store.py`, lines 29 to 42:

```python
            raise TransientModelError(f"database unavailable: {error}") from error

    def ping(self) -> bool:
        """True when the database answers a trivial query."""
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except (TransientModelError, psycopg.Error):
            return False

    def replace_all(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("one vector per chunk")
```

- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `ping`. It returns true or false. The author's own description: "True when the database answers a trivial query."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- A `with` block: it sets up `self._connect()` as `connection`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `_connect` of this object.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Ends the function and gives back the value `True` to the caller.
- `except` handler: it runs when the `try` block raised `(TransientModelError, psycopg.Error)`.
- Ends the function and gives back the value `False` to the caller.
- Defines the method `replace_all`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `chunks` holds anything that behaves like a list of the project type `Chunk`.
    - `vectors` holds anything that behaves like a list of anything that behaves like a list of a decimal number.
- Decision: the indented lines below run only when `len(chunks) != len(vectors)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.

`src/cited_answers/infrastructure/pg_store.py`, lines 43 to 56:

```python
        with self._connect() as connection, connection.transaction():
            connection.execute("DELETE FROM chunks")
            with connection.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s::vector)",
                    [
                        (c.id, c.page_id, c.heading_path, c.text, c.updated, c.status.value, vector_literal(v))
                        for c, v in zip(chunks, vectors, strict=True)
                    ],
                )

    def chunks(self) -> list[Chunk]:
        with self._connect() as connection:
```

- A `with` block: it sets up `self._connect()` as `connection`, `connection.transaction()`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `_connect` of this object.
  - The method `transaction` of `connection`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- A `with` block: it sets up `connection.cursor()` as `cursor`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `cursor` of `connection`.
- Calls `.executemany(...)` runs one SQL statement for a list of parameter sets with 2 argument(s); the result is not kept.
  - `.executemany(...)` runs one SQL statement for a list of parameter sets.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `vector_literal`, a function defined in this file or passed in.
  - `zip` walks several collections side by side, item by item.
- Defines the method `chunks`. It returns a list of the project type `Chunk`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `with` block: it sets up `self._connect()` as `connection`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `_connect` of this object.

`src/cited_answers/infrastructure/pg_store.py`, lines 57 to 70:

```python
            rows = connection.execute(
                "SELECT id, page_id, heading_path, body, updated, status FROM chunks ORDER BY id"
            ).fetchall()
        return [Chunk(r[0], r[1], r[2], r[3], r[4], PageStatus(r[5])) for r in rows]

    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        literal = vector_literal(vector)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) AS similarity FROM chunks "
                "ORDER BY embedding <=> %s::vector, id LIMIT %s",
                (literal, literal, k),
            ).fetchall()
        return [(str(r[0]), float(r[1])) for r in rows]
```

- Stores the result of calling `connection.execute('SELECT id, page_id, heading...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `.execute(...)` runs one SQL statement.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `Chunk` from the project's `cited_answers.domain.chunking` (A passage a reader can open: the page it came from, its heading path, its date and its status.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `PageStatus` from the project's `cited_answers.domain.pages` (Only `current` pages are indexed. A `retired` page may contradict a current one.).
- Defines the method `vector_search`. It returns a list of a fixed list of text, a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `k` holds a whole number.
- Stores the result of calling `vector_literal` under the name `literal`.
  - `vector_literal`, a function defined in this file or passed in.
- A `with` block: it sets up `self._connect()` as `connection`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `_connect` of this object.
- Stores the result of calling `connection.execute('SELECT id, 1 - (embedding <...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `.execute(...)` runs one SQL statement.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `float` turns a value into a decimal number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/cited_answers/infrastructure/pg_store.py`, lines 72 to 78:

```python
    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) FROM chunks WHERE id = ANY(%s)",
                (vector_literal(vector), list(chunk_ids)),
            ).fetchall()
        return {str(r[0]): float(r[1]) for r in rows}
```

- Defines the method `similarities`. It returns a dictionary from text to a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `vector` holds anything that behaves like a list of a decimal number.
    - `chunk_ids` holds anything that behaves like a list of text.
- A `with` block: it sets up `self._connect()` as `connection`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `_connect` of this object.
- Stores the result of calling `connection.execute('SELECT id, 1 - (embedding <...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `.execute(...)` runs one SQL statement.
  - `vector_literal`, a function defined in this file or passed in.
  - `list` makes a list (a copy when given a collection).
- Ends the function and gives back a dictionary built by looping to the caller.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `float` turns a value into a decimal number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `src/cited_answers/infrastructure/recording.py`

In its own words: "Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures."

79 non-blank lines; it defines `RecordingStore`, `RecordedChatModel`, `RecordingChatModel`.

`src/cited_answers/infrastructure/recording.py`, lines 1 to 13:

```python
"""Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

A recording is a JSON Lines file. Each line holds the request fingerprint, the call's tag, a note about what
produced it and the response. Fixtures hold synthetic data only (no credentials, no personal data).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `Any` from the standard library module `typing`.

`src/cited_answers/infrastructure/recording.py`, lines 15 to 27:

```python
from cited_answers.application.ports import ChatModel
from cited_answers.domain.errors import RecordingMissing
from cited_answers.domain.llm import ChatRequest, ChatResponse


class RecordingStore:
    """An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
```

- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `cited_answers.application.ports`.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `cited_answers.domain.llm`.
- Defines the class `RecordingStore`. The author's own description: "An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.Lock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.Lock` makes a lock.
- Declares `self._entries` as a dictionary from text to a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `files`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `.exists(...)` asks whether the path exists.

`src/cited_answers/infrastructure/recording.py`, lines 28 to 41:

```python
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._entries[entry["key"]] = entry
        self._append_to = path / "recorded.jsonl" if path.is_dir() else path

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: str) -> ChatResponse | None:
        with self._lock:
            entry = self._entries.get(key)
```

- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- A `with` block: it sets up `file.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `file`.
- Loop: the indented lines below run once for each item of `handle`; `line` names the current item.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
- Stores the value named `entry` under the name `self._entries[entry['key']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `self._append_to` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `/` is divide.
- Defines the method `__len__`. It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `get`. It returns the project type `ChatResponse`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._entries.get` under the name `entry`.
  - `get` on the stored object `self._entries`: it reads a dictionary entry, giving a default when the key is missing.

`src/cited_answers/infrastructure/recording.py`, lines 42 to 55:

```python
        return ChatResponse.from_json(entry["response"]) if entry else None

    def put(self, key: str, tag: str, response: ChatResponse, recorded_with: Mapping[str, Any]) -> None:
        entry = {"key": key, "tag": tag, "recorded_with": dict(recorded_with), "response": response.to_json()}
        with self._lock:
            self._entries[key] = entry
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()


class RecordedChatModel:
    """Replays recorded responses. A request nobody recorded raises `RecordingMissing`."""
```

- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - The method `from_json` of `ChatResponse`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `put`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `tag` holds text.
    - `response` holds the project type `ChatResponse`.
    - `recorded_with` holds anything that behaves like a dictionary from text to any value.
- Stores a dictionary with 4 entries under the name `entry`.
  - `dict` makes a dictionary (a copy when given one).
  - The method `to_json` of `response`.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the value named `entry` under the name `self._entries[key]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `mkdir` on the stored object `self._append_to.parent`: it creates a folder with 2 argument(s); the result is not kept.
  - `mkdir` on the stored object `self._append_to.parent`: it creates a folder.
- A `with` block: it sets up `self._append_to.open('a', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._append_to`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.
- Defines the class `RecordedChatModel`. The author's own description: "Replays recorded responses. A request nobody recorded raises `RecordingMissing`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/recording.py`, lines 57 to 69:

```python
    def __init__(self, store: RecordingStore) -> None:
        self._store = store

    @property
    def name(self) -> str:
        return "recorded"

    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        response = self._store.get(request.fingerprint())
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `RecordingStore`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `recorded` to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._store.get` under the name `response`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).

`src/cited_answers/infrastructure/recording.py`, lines 70 to 83:

```python
        if response is None:
            raise RecordingMissing(
                f"no recording for request tag={request.tag!r} fingerprint={request.fingerprint()[:12]}; "
                "run `make record` against a live model to refresh the fixtures"
            )
        return response


class RecordingChatModel:
    """Wraps a live model and writes each answer into a recording. A request already recorded is replayed."""

    def __init__(self, inner: ChatModel, store: RecordingStore, note: Mapping[str, Any]) -> None:
        self._inner = inner
        self._store = store
```

- Decision: the indented lines below run only when `response is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `RecordingMissing`. Execution jumps out to the nearest matching `except`.
  - `RecordingMissing` from the project's `cited_answers.domain.errors` (The recorded adapter has no response for this request. Re-record with `make record`.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Ends the function and gives back the value named `response` to the caller.
- Defines the class `RecordingChatModel`. The author's own description: "Wraps a live model and writes each answer into a recording. A request already recorded is replayed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `store` holds the project type `RecordingStore`.
    - `note` holds anything that behaves like a dictionary from text to any value.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).

`src/cited_answers/infrastructure/recording.py`, lines 84 to 97:

```python
        self._note = dict(note)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        key = request.fingerprint()
        cached = self._store.get(key)
        if cached is not None:
```

- Stores the result of calling `dict` under the name `self._note` (as an attribute of this object, so other methods can use it).
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `request.fingerprint` under the name `key`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Stores the result of calling `self._store.get` under the name `cached`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `cached is not None` is true.
  - `is not` means not the same object.

`src/cited_answers/infrastructure/recording.py`, lines 98 to 101:

```python
            return cached
        response = self._inner.complete(request)
        self._store.put(key, request.tag, response, {**self._note, "model": response.model})
        return response
```

- Ends the function and gives back the value named `cached` to the caller.
- Stores the result of calling `self._inner.complete` under the name `response`.
  - The method `complete` of `self._inner`.
- Calls `put` on the stored object `self._store`: it sends an HTTP PUT request with 4 argument(s); the result is not kept.
  - `put` on the stored object `self._store`: it sends an HTTP PUT request.
- Ends the function and gives back the value named `response` to the caller.

### `src/cited_answers/infrastructure/resilient.py`

In its own words: "A decorator that retries transient model failures with backoff and jitter."

48 non-blank lines; it defines `RetryingChatModel`.

`src/cited_answers/infrastructure/resilient.py`, lines 1 to 14:

```python
"""A decorator that retries transient model failures with backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from cited_answers.application.ports import ChatModel
from cited_answers.domain.errors import TransientModelError
from cited_answers.domain.llm import ChatRequest, ChatResponse
from cited_answers.infrastructure.logging import fields
from cited_answers.infrastructure.retry import retry
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `cited_answers.application.ports`.
- Brings in `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `cited_answers.domain.llm`.
- Brings in `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `cited_answers.infrastructure.logging`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `cited_answers.infrastructure.retry`.

`src/cited_answers/infrastructure/resilient.py`, lines 16 to 20:

```python
_log = logging.getLogger(__name__)


class RetryingChatModel:
    """Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."""
```

- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `RetryingChatModel`. The author's own description: "Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/resilient.py`, lines 22 to 34:

```python
    def __init__(
        self,
        inner: ChatModel,
        *,
        attempts: int = 3,
        base_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._base_delay = base_delay_seconds
        self._sleep = sleep
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `attempts` holds a whole number; if the caller leaves it out it is the number `3`; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `0.5`; it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `attempts` under the name `self._attempts` (as an attribute of this object, so other methods can use it).
- Stores the value named `base_delay_seconds` under the name `self._base_delay` (as an attribute of this object, so other methods can use it).
- Stores the value named `sleep` under the name `self._sleep` (as an attribute of this object, so other methods can use it).

`src/cited_answers/infrastructure/resilient.py`, lines 35 to 46:

```python
        self._rng = rng

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        def log_retry(attempt: int, error: BaseException) -> None:
```

- Stores the value named `rng` under the name `self._rng` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Defines the function `log_retry`. It returns nothing (None).
- Its parameters:
    - `attempt` holds a whole number.
    - `error` holds `BaseException`.

`src/cited_answers/infrastructure/resilient.py`, lines 47 to 59:

```python
            _log.warning(
                "model call failed, retrying", extra=fields(tag=request.tag, attempt=attempt, error=str(error))
            )

        return retry(
            lambda: self._inner.complete(request),
            attempts=self._attempts,
            base_delay_seconds=self._base_delay,
            retry_on=(TransientModelError,),
            sleep=self._sleep,
            rng=self._rng,
            on_retry=log_retry,
        )
```

- Calls the method `warning` of `_log` with 2 argument(s); the result is not kept.
  - The method `warning` of `_log`.
  - `fields` from the project's `cited_answers.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
  - `str` turns a value into text.
- Ends the function and gives back the result of calling `retry` to the caller.
  - `retry` from the project's `cited_answers.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `complete` of `self._inner`.

### `src/cited_answers/infrastructure/retry.py`

In its own words: "Retry with exponential backoff and jitter for calls that cross the network."

33 non-blank lines; it defines `retry`.

`src/cited_answers/infrastructure/retry.py`, lines 1 to 7:

```python
"""Retry with exponential backoff and jitter for calls that cross the network."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.

`src/cited_answers/infrastructure/retry.py`, lines 10 to 20:

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
```

- Defines the function `retry`. It returns `T`. The author's own description: "Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`."
- Its parameters:
    - `operation` holds a function.
    - `attempts` holds a whole number; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; it must be passed by name.
    - `retry_on` holds a fixed list of type of `BaseException` (any length); it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
    - `max_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `10.0`; it must be passed by name.
    - `on_retry` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.

`src/cited_answers/infrastructure/retry.py`, lines 21 to 34:

```python
    """Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.

    The pause is `base * 2**(attempt - 1)` capped at `max_delay_seconds`, then scaled by a random
    factor in [0.5, 1.0] so many clients do not retry in step. The last failure is raised.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    jitter = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on as error:
            if attempt == attempts:
                raise
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `attempts < 1` is true.
  - `<` means less than.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Stores the result of combining conditions: `rng or random.Random()` under the name `jitter`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Loop: the indented lines below run once for each item of `range(1, attempts + 1)`; `attempt` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `+` is add.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `operation` to the caller.
  - `operation`, a function defined in this file or passed in.
- `except` handler: it runs when the `try` block raised `retry_on`; `error` names the error object.
- Decision: the indented lines below run only when `attempt == attempts` is true.
  - `==` means equal.
- Raises an error again (the one being handled). Execution jumps out to the nearest matching `except`.

`src/cited_answers/infrastructure/retry.py`, lines 35 to 38:

```python
            if on_retry:
                on_retry(attempt, error)
            sleep(min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1)) * jitter.uniform(0.5, 1.0))
    raise AssertionError("unreachable")  # pragma: no cover
```

- Decision: the indented lines below run only when `on_retry` is true.
- Calls `on_retry`, a function defined in this file or passed in with 2 argument(s); the result is not kept.
  - `on_retry`, a function defined in this file or passed in.
- Calls `sleep`, a function defined in this file or passed in with 1 argument(s); the result is not kept.
  - `sleep`, a function defined in this file or passed in.
  - `*` is multiply.
  - `min` picks the smallest value.
  - The method `uniform` of `jitter`.
  - `**` is power.
  - `-` is subtract.
- Raises an error: the result of calling `AssertionError`. Execution jumps out to the nearest matching `except`.
  - `AssertionError` the error an `assert` raises.

### `src/cited_answers/infrastructure/settings.py`

In its own words: "Configuration from the environment, validated once at startup (twelve-factor)."

53 non-blank lines; it defines `AppSettings`.

`src/cited_answers/infrastructure/settings.py`, lines 1 to 12:

```python
"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from cited_answers.infrastructure.env import ConfigurationError, choice, optional_text, positive_int, text

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `cited_answers.infrastructure.env`.
- Stores a tuple of 4 item(s) under the name `_LEVELS`.

`src/cited_answers/infrastructure/settings.py`, lines 15 to 26:

```python
@dataclass(frozen=True, slots=True)
class AppSettings:
    """Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable."""

    pages_dir: Path
    questions_dir: Path
    prompts_dir: Path
    threshold_path: Path
    reports_dir: Path
    index_backend: str
    database_url: str
    embedder_provider: str
```

- Defines the class `AppSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `pages_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `questions_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `prompts_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `threshold_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `reports_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `index_backend` as text; it has no default, so a value must be given when the object is made.
- Declares `database_url` as text; it has no default, so a value must be given when the object is made.
- Declares `embedder_provider` as text; it has no default, so a value must be given when the object is made.

`src/cited_answers/infrastructure/settings.py`, lines 27 to 40:

```python
    embed_model: str
    embeddings_path: Path
    answer_prompt: str
    judge_prompt: str
    refusal_threshold: float | None
    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AppSettings:
        env = os.environ if environ is None else environ
        override = optional_text(env, "REFUSAL_THRESHOLD")
        try:
```

- Declares `embed_model` as text; it has no default, so a value must be given when the object is made.
- Declares `embeddings_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `answer_prompt` as text; it has no default, so a value must be given when the object is made.
- Declares `judge_prompt` as text; it has no default, so a value must be given when the object is made.
- Declares `refusal_threshold` as a decimal number, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `host` as text; it has no default, so a value must be given when the object is made.
- Declares `port` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `log_level` as text; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `AppSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of calling `optional_text` under the name `override`.
  - `optional_text` from the project's `cited_answers.infrastructure.env` (The variable's text, or None when it is unset or blank.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.

`src/cited_answers/infrastructure/settings.py`, lines 41 to 43:

```python
            threshold = float(override) if override else None
        except ValueError as error:
            raise ConfigurationError(f"REFUSAL_THRESHOLD must be a number, got {override!r}") from error
```

- Stores one of two values, chosen by a condition under the name `threshold`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `cited_answers.infrastructure.env` (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/cited_answers/infrastructure/settings.py`, lines 44 to 61:

```python
        return cls(
            pages_dir=Path(text(env, "PAGES_DIR", "data/pages")),
            questions_dir=Path(text(env, "QUESTIONS_DIR", "data/questions")),
            prompts_dir=Path(text(env, "PROMPTS_DIR", "prompts")),
            threshold_path=Path(text(env, "THRESHOLD_PATH", "evals/threshold.json")),
            reports_dir=Path(text(env, "REPORTS_DIR", "evals/reports")),
            index_backend=choice(env, "INDEX_BACKEND", "memory", ("memory", "pgvector")),
            database_url=text(env, "DATABASE_URL", "postgresql://cited:cited@localhost:55432/cited"),
            embedder_provider=choice(env, "EMBEDDER_PROVIDER", "recorded", ("recorded", "openai-compatible")),
            embed_model=text(env, "EMBED_MODEL", "nomic-embed-text"),
            embeddings_path=Path(text(env, "EMBEDDINGS_PATH", "tests/fixtures/embeddings")),
            answer_prompt=text(env, "ANSWER_PROMPT_VERSION", "v2"),
            judge_prompt=text(env, "JUDGE_PROMPT_VERSION", "v1"),
            refusal_threshold=threshold,
            host=text(env, "HTTP_HOST", "127.0.0.1"),
            port=positive_int(env, "HTTP_PORT", 8080),
            log_level=choice({"LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `choice` from the project's `cited_answers.infrastructure.env` (One of the `allowed` strings.).
  - `text` from the project's `cited_answers.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `positive_int` from the project's `cited_answers.infrastructure.env` (An integer of 1 or more.).
  - `.upper(...)` turns text into upper case.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/cited_answers/infrastructure/shutdown.py`

In its own words: "Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."

20 non-blank lines; it defines `ShutdownSignal`.

`src/cited_answers/infrastructure/shutdown.py`, lines 1 to 14:

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `signal` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `FrameType` from the standard library module `types`.
- Defines the class `ShutdownSignal`. The author's own description: "A flag that SIGINT and SIGTERM set, which work loops check between units of work."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the result of calling `threading.Event` under the name `self._requested` (as an attribute of this object, so other methods can use it).
  - `threading.Event` makes a flag shared between threads.

`src/cited_answers/infrastructure/shutdown.py`, lines 16 to 28:

```python
    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        self._requested.set()

    @property
    def requested(self) -> bool:
```

- Defines the method `install`. It returns nothing (None). The author's own description: "Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `(signal.SIGINT, signal.SIGTERM)`; `number` names the current item.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Defines the method `_handle`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `_number` holds a whole number.
    - `_frame` holds a stack frame, or nothing (None).
- Calls the method `request` of this object; the result is not kept.
  - The method `request` of this object.
- Defines the method `request`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Calls `set` on the stored object `self._requested`: it raises a flag (an Event); the result is not kept.
  - `set` on the stored object `self._requested`: it raises a flag (an Event).
- Defines the method `requested`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/cited_answers/infrastructure/shutdown.py`, lines 29 to 29:

```python
        return self._requested.is_set()
```

- Ends the function and gives back the result of calling `self._requested.is_set` to the caller.
  - `is_set` on the stored object `self._requested`: it asks whether a flag is raised.

### `src/cited_answers/infrastructure/wiring.py`

In its own words: "Build the embedder and the chunk store the settings ask for."

36 non-blank lines; it defines `build_embedder`, `build_store`.

`src/cited_answers/infrastructure/wiring.py`, lines 1 to 10:

```python
"""Build the embedder and the chunk store the settings ask for."""

from __future__ import annotations

import os
from collections.abc import Mapping

import httpx

from cited_answers.application.ports import ChunkStore, Embedder
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Makes the module `httpx` (installed package) available.
- Brings in `ChunkStore` (Where chunks and their vectors live: memory in tests, Postgres with pgvector in the service.), `Embedder` (Turns texts into vectors.) from the project module `cited_answers.application.ports`.

`src/cited_answers/infrastructure/wiring.py`, lines 11 to 24:

```python
from cited_answers.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
)
from cited_answers.infrastructure.env import choice, optional_text, positive_float, text
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.pg_store import PgVectorChunkStore
from cited_answers.infrastructure.settings import AppSettings


def build_embedder(settings: AppSettings, environ: Mapping[str, str] | None = None) -> Embedder:
    """`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."""
```

- Brings in `EmbeddingStore` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.), `OpenAICompatibleEmbedder` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.), `RecordedEmbedder` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.), `RecordingEmbedder` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.) from the project module `cited_answers.infrastructure.embeddings`.
- Brings in `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_float` (A number greater than zero.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `cited_answers.infrastructure.env`.
- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.
- Brings in `PgVectorChunkStore` (Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index.) from the project module `cited_answers.infrastructure.pg_store`.
- Brings in `AppSettings` (Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable.) from the project module `cited_answers.infrastructure.settings`.
- Defines the function `build_embedder`. It returns the project type `Embedder`. The author's own description: "`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."
- Its parameters:
    - `settings` holds the project type `AppSettings`.
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/cited_answers/infrastructure/wiring.py`, lines 25 to 37:

```python
    env = os.environ if environ is None else environ
    if settings.embedder_provider == "recorded":
        return RecordedEmbedder(EmbeddingStore(settings.embeddings_path), settings.embed_model)
    http = httpx.Client(timeout=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0))
    live = OpenAICompatibleEmbedder(
        http,
        text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
        settings.embed_model,
        optional_text(env, "OPENAI_API_KEY"),
    )
    if choice(env, "RECORD", "off", ("on", "off")) == "on":
        return RecordingEmbedder(live, EmbeddingStore(settings.embeddings_path))
    return live
```

- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Decision: the indented lines below run only when `settings.embedder_provider == 'recorded'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `RecordedEmbedder` to the caller.
  - `RecordedEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
  - `positive_float` from the project's `cited_answers.infrastructure.env` (A number greater than zero.).
- Stores the result of calling `OpenAICompatibleEmbedder` under the name `live`.
  - `OpenAICompatibleEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.).
  - `text` from the project's `cited_answers.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `optional_text` from the project's `cited_answers.infrastructure.env` (The variable's text, or None when it is unset or blank.).
- Decision: the indented lines below run only when `choice(env, 'RECORD', 'off', ('on', 'off')) == 'on'` is true.
  - `==` means equal.
  - `choice` from the project's `cited_answers.infrastructure.env` (One of the `allowed` strings.).
- Ends the function and gives back the result of calling `RecordingEmbedder` to the caller.
  - `RecordingEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Ends the function and gives back the value named `live` to the caller.

`src/cited_answers/infrastructure/wiring.py`, lines 40 to 44:

```python
def build_store(settings: AppSettings) -> ChunkStore:
    """The in-memory store, or Postgres with pgvector."""
    if settings.index_backend == "pgvector":
        return PgVectorChunkStore(settings.database_url)
    return InMemoryChunkStore()
```

- Defines the function `build_store`. It returns the project type `ChunkStore`. The author's own description: "The in-memory store, or Postgres with pgvector."
- Its parameters:
    - `settings` holds the project type `AppSettings`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `settings.index_backend == 'pgvector'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `PgVectorChunkStore` to the caller.
  - `PgVectorChunkStore` from the project's `cited_answers.infrastructure.pg_store` (Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index.).
- Ends the function and gives back the result of calling `InMemoryChunkStore` to the caller.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import cited_answers.infrastructure.__init__; print(cited_answers.infrastructure.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Adapters that implement the ports: model clients, files, settings, logging.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/cited_answers/infrastructure').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
anthropic_chat.py 2
clock.py 1
embeddings.py 7
env.py 8
files.py 4
logging.py 4
memory_store.py 1
model_factory.py 2
openai_compatible.py 3
pg_store.py 2
recording.py 3
...
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

- **Common mistakes with this layer.** Letting an adapter decide business rules (they belong in the domain), reading environment variables in many places instead of the one settings module, or swallowing errors. Adapters here turn vendor errors into the project's own named errors.

## Check yourself

1. What is the job of `src/cited_answers/infrastructure/__init__.py`?

   *Answer:* Adapters that implement the ports: model clients, files, settings, logging.

2. What is the job of `src/cited_answers/infrastructure/anthropic_chat.py`?

   *Answer:* A chat model on the Anthropic Messages API, through the official SDK.

3. What is the job of `src/cited_answers/infrastructure/clock.py`?

   *Answer:* The real clock, behind the `Clock` port.

4. What is the job of `src/cited_answers/infrastructure/embeddings.py`?

   *Answer:* Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording.

5. What is the job of `src/cited_answers/infrastructure/env.py`?

   *Answer:* Helpers that read and validate environment variables (twelve-factor configuration).

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
