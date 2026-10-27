# Python source, the unit tests (part 2 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 4 files with 33 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 134 non-blank lines |
| `tests/unit/interfaces/test_cli.py` | 43 non-blank lines |
| `tests/unit/interfaces/test_cli_commands.py` | 78 non-blank lines |
| `tests/unit/interfaces/test_http.py` | 53 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/infrastructure/test_resilience_logging_factory.py`

134 non-blank lines; it defines `Flaky`, `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, `test_retry_needs_at_least_one_attempt_and_caps_the_delay`, `test_log_lines_are_logfmt_with_fields_and_quote_spaces`, `test_an_exception_is_logged_on_the_same_line`, `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`, `test_the_system_clock_moves_forward`, `test_the_default_provider_is_the_recorded_model`, `test_the_local_provider_builds_a_retrying_openai_compatible_model`, `test_record_mode_wraps_a_live_model_in_a_recorder`, ....

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 1 to 14:

```python
import io
import logging
import random
import signal

import pytest

from cited_answers.domain.errors import PermanentModelError, TransientModelError
from cited_answers.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, Usage
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.env import ConfigurationError
from cited_answers.infrastructure.logging import configure_logging, fields
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingChatModel
```

- Makes the module `io` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `cited_answers.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `cited_answers.infrastructure.clock`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `cited_answers.infrastructure.env`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.), `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `cited_answers.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `cited_answers.infrastructure.model_factory`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.) from the project module `cited_answers.infrastructure.recording`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 15 to 28:

```python
from cited_answers.infrastructure.resilient import RetryingChatModel
from cited_answers.infrastructure.retry import retry
from cited_answers.infrastructure.shutdown import ShutdownSignal

REQUEST = ChatRequest((ChatMessage.user("hi"),), tag="r")


class Flaky:
    name = "flaky"
    supports_sampling = True

    def __init__(self, failures, error=TransientModelError):
        self.calls = 0
        self._failures = failures
```

- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `cited_answers.infrastructure.resilient`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `cited_answers.infrastructure.retry`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `cited_answers.infrastructure.shutdown`.
- Stores the result of calling `ChatRequest` under the name `REQUEST`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the class `Flaky`.
- Stores the text `flaky` under the name `name`.
- Stores the value `True` under the name `supports_sampling`.
- Defines the method `__init__`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `failures`.
    - `error`; if the caller leaves it out it is the value named `TransientModelError`.
- Stores the number `0` under the name `self.calls` (as an attribute of this object, so other methods can use it).
- Stores the value named `failures` under the name `self._failures` (as an attribute of this object, so other methods can use it).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 29 to 42:

```python
        self._error = error

    def complete(self, request):
        self.calls += 1
        if self.calls <= self._failures:
            raise self._error("boom")
        return ChatResponse("ok", StopReason.END, Usage(1, 1), 0.1, "flaky")


def test_a_transient_failure_is_retried_with_backoff_and_then_succeeds():
    pauses: list[float] = []
    flaky = Flaky(2)
    model = RetryingChatModel(flaky, attempts=3, base_delay_seconds=1.0, sleep=pauses.append, rng=random.Random(1))
    assert model.complete(REQUEST).text == "ok"
```

- Stores the value named `error` under the name `self._error` (as an attribute of this object, so other methods can use it).
- Defines the method `complete`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request`.
- Updates `self.calls` in place: `+=` applies `+` with the number `1` and stores the result back.
- Decision: the indented lines below run only when `self.calls <= self._failures` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `self._error`. Execution jumps out to the nearest matching `except`.
  - The method `_error` of `self`.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `cited_answers.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `cited_answers.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the function `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`.
- It takes no parameters.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `RetryingChatModel` under the name `model`.
  - `RetryingChatModel` from the project's `cited_answers.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Checks that `model.complete(REQUEST).text == 'ok'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `model`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 43 to 54:

```python
    assert flaky.calls == 3
    assert 0.5 <= pauses[0] <= 1.0
    assert 1.0 <= pauses[1] <= 2.0
    assert model.name == "flaky"
    assert model.supports_sampling


def test_the_last_transient_failure_is_raised_after_the_attempts_run_out():
    flaky = Flaky(9)
    with pytest.raises(TransientModelError):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 2
```

- Checks that `flaky.calls == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `0.5 <= pauses[0] <= 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `1.0 <= pauses[1] <= 2.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `model.name == 'flaky'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
- Defines the function `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `cited_answers.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 57 to 67:

```python
def test_a_permanent_failure_is_not_retried():
    flaky = Flaky(9, PermanentModelError)
    with pytest.raises(PermanentModelError):
        RetryingChatModel(flaky, attempts=5, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 1


def test_retry_needs_at_least_one_attempt_and_caps_the_delay():
    with pytest.raises(ValueError, match=r"at least 1"):
        retry(lambda: 1, attempts=0, base_delay_seconds=1, retry_on=(ValueError,))
    pauses: list[float] = []
```

- Defines the function `test_a_permanent_failure_is_not_retried`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=5, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=5, ...`.
  - `RetryingChatModel` from the project's `cited_answers.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_retry_needs_at_least_one_attempt_and_caps_the_delay`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(ValueError, match='at least 1')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `cited_answers.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 4 argument(s); the result is not kept.
  - `retry` from the project's `cited_answers.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 69 to 81:

```python
    def fail() -> int:
        raise ValueError

    with pytest.raises(ValueError, match=r"^$"):
        retry(fail, attempts=6, base_delay_seconds=4, retry_on=(ValueError,), sleep=pauses.append, max_delay_seconds=5)
    assert max(pauses) <= 5


def test_log_lines_are_logfmt_with_fields_and_quote_spaces():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("t").info("two words", extra=fields(count=3, note="a b", empty=""))
    line = stream.getvalue().strip()
```

- Defines the function `fail`. It returns a whole number.
- It takes no parameters.
- Raises an error: the value named `ValueError`. Execution jumps out to the nearest matching `except`.
- A `with` block: it sets up `pytest.raises(ValueError, match='^$')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `cited_answers.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 6 argument(s); the result is not kept.
  - `retry` from the project's `cited_answers.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
- Checks that `max(pauses) <= 5` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `max` picks the largest value.
- Defines the function `test_log_lines_are_logfmt_with_fields_and_quote_spaces`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Calls the method `info` of `logging.getLogger('t')` with 2 argument(s); the result is not kept.
  - The method `info` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.
  - `fields` from the project's `cited_answers.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
- Stores the result of calling `stream.getvalue().strip` under the name `line`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - The method `getvalue` of `stream`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 82 to 95:

```python
    assert 'msg="two words"' in line
    assert "count=3" in line
    assert 'note="a b"' in line
    assert 'empty=""' in line
    assert line.startswith("ts=")


def test_an_exception_is_logged_on_the_same_line():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    try:
        raise RuntimeError("bad")
    except RuntimeError:
        logging.getLogger("t").exception("failed")
```

- Checks that `'msg="two words"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'count=3' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'note="a b"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'empty=""' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `line.startswith('ts=')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
- Defines the function `test_an_exception_is_logged_on_the_same_line`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `cited_answers.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Raises an error: the result of calling `RuntimeError`. Execution jumps out to the nearest matching `except`.
  - `RuntimeError` a general error raised while running.
- `except` handler: it runs when the `try` block raised `RuntimeError`.
- Calls the method `exception` of `logging.getLogger('t')` with 1 argument(s); the result is not kept.
  - The method `exception` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 96 to 109:

```python
    assert "exc=" in stream.getvalue()


def test_shutdown_flag_is_set_by_a_request_and_by_a_signal():
    shutdown = ShutdownSignal()
    assert not shutdown.requested
    shutdown.install()
    signal.raise_signal(signal.SIGTERM)
    assert shutdown.requested
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    other = ShutdownSignal()
    other.request()
    assert other.requested
```

- Checks that `'exc=' in stream.getvalue()` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `getvalue` of `stream`.
- Defines the function `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`.
- It takes no parameters.
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `cited_answers.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Checks that `not shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Calls `signal.raise_signal` from the standard library module `signal` with 1 argument(s); the result is not kept.
  - `signal.raise_signal` from the standard library module `signal`.
- Checks that `shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Stores the result of calling `ShutdownSignal` under the name `other`.
  - `ShutdownSignal` from the project's `cited_answers.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `request` of `other`; the result is not kept.
  - The method `request` of `other`.
- Checks that `other.requested` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 112 to 123:

```python
def test_the_system_clock_moves_forward():
    clock = SystemClock()
    assert clock.monotonic() <= clock.monotonic()
    assert clock.now().date() == clock.today()


def test_the_default_provider_is_the_recorded_model(tmp_path):
    settings = ModelSettings.from_env({"RECORDINGS_PATH": str(tmp_path)})
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)


def test_the_local_provider_builds_a_retrying_openai_compatible_model():
```

- Defines the function `test_the_system_clock_moves_forward`.
- It takes no parameters.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `clock.monotonic() <= clock.monotonic()` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - The method `monotonic` of `clock`.
- Checks that `clock.now().date() == clock.today()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `date` of `clock.now()`.
  - The method `today` of `clock`.
  - The method `now` of `clock`.
- Defines the function `test_the_default_provider_is_the_recorded_model`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_local_provider_builds_a_retrying_openai_compatible_model`.
- It takes no parameters.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 124 to 135:

```python
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"})
    model = build_chat_model(settings, SystemClock(), {})
    assert isinstance(model, RetryingChatModel)
    assert model.name == "qwen2.5:0.5b"
    assert settings.openai_base_url == "http://localhost:11434/v1"


def test_record_mode_wraps_a_live_model_in_a_recorder(tmp_path):
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "openai-compatible", "RECORD": "on", "RECORDINGS_PATH": str(tmp_path / "r.jsonl")}
    )
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)
```

- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `model.name == 'qwen2.5:0.5b'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.openai_base_url == 'http://localhost:11434/v1'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_record_mode_wraps_a_live_model_in_a_recorder`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
  - `/` is divide.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 138 to 149:

```python
def test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"})
    assert settings.model == "claude-haiku-5-5"
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings, SystemClock(), {})


def test_the_anthropic_provider_builds_when_a_key_is_present():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic", "ANTHROPIC_THINKING": "omit"})
    model = build_chat_model(settings, SystemClock(), {"ANTHROPIC_API_KEY": "present-but-not-real"})
    assert isinstance(model, RetryingChatModel)
    assert not model.supports_sampling
```

- Defines the function `test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Checks that `settings.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match='ANTHROPIC_API_KEY')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) with 3 argument(s); the result is not kept.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_anthropic_provider_builds_when_a_key_is_present`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `cited_answers.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `cited_answers.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 152 to 163:

```python
@pytest.mark.parametrize(
    "environ",
    [
        {"MODEL_PROVIDER": "carrier-pigeon"},
        {"RECORD": "maybe"},
        {"MODEL_ATTEMPTS": "0"},
        {"MODEL_TIMEOUT_SECONDS": "0"},
    ],
)
def test_bad_model_settings_name_the_variable(environ):
    with pytest.raises(ConfigurationError, match=next(iter(environ))):
        ModelSettings.from_env(environ)
```

- Defines the function `test_bad_model_settings_name_the_variable`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `environ`.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match=next(iter(environ)))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `next` takes the next item from an iterator.
  - `iter` makes an iterator over a collection.
- Calls the method `from_env` of `ModelSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `ModelSettings`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 166 to 173:

```python
def test_info_logs_of_a_failed_call_never_carry_the_prompt_text(caplog):
    flaky = Flaky(1)
    secret = ChatRequest((ChatMessage.user("my card number is 4111"),), tag="p1/t0/0")
    with caplog.at_level(logging.INFO):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(secret)
    assert caplog.records
    assert "4111" not in caplog.text
    assert "4111" not in " ".join(str(r.__dict__.get("fields", "")) for r in caplog.records)
```

- Defines the function `test_info_logs_of_a_failed_call_never_carry_the_prompt_text`.
- Its parameters:
    - `caplog`.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `ChatRequest` under the name `secret`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `cited_answers.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `caplog.records` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `'4111' not in caplog.text` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'4111' not in ' '.join((str(r.__dict__.get('fields', '')) for r in caplog.rec...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `tests/unit/interfaces/test_cli.py`

43 non-blank lines; it defines `workspace`, `test_a_missing_recording_is_reported_not_raised`, `test_a_bad_environment_value_is_a_configuration_error`, `test_a_missing_prompt_is_a_configuration_error`, `test_hand_grades_are_read_as_question_id_to_verdict`, `test_the_threshold_comes_from_the_override_then_the_file_then_the_default`.

`tests/unit/interfaces/test_cli.py`, lines 1 to 14:

```python
import json
from pathlib import Path

import pytest

from cited_answers.infrastructure.settings import AppSettings
from cited_answers.interfaces import cli
from cited_answers.interfaces.cli import EXIT_CONFIG, EXIT_OK, main

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
```

- Makes the module `json` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Brings in `AppSettings` (Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable.) from the project module `cited_answers.infrastructure.settings`.
- Brings in `cli` from the project module `cited_answers.interfaces`.
- Brings in `EXIT_CONFIG`, `EXIT_OK`, `main` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).) from the project module `cited_answers.interfaces.cli`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `3` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Defines the function `workspace`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- Its parameters:
    - `tmp_path`.
    - `monkeypatch`.

`tests/unit/interfaces/test_cli.py`, lines 15 to 28:

```python
    monkeypatch.setenv("PAGES_DIR", str(REPO / "data" / "pages"))
    monkeypatch.setenv("QUESTIONS_DIR", str(REPO / "data" / "questions"))
    monkeypatch.setenv("PROMPTS_DIR", str(REPO / "prompts"))
    monkeypatch.setenv("THRESHOLD_PATH", str(tmp_path / "threshold.json"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("EMBEDDER_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(REPO / "tests" / "fixtures" / "recordings"))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(REPO / "tests" / "fixtures" / "embeddings"))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path


def test_a_missing_recording_is_reported_not_raised(workspace, monkeypatch, capsys):
```

- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Ends the function and gives back the value named `tmp_path` to the caller.
- Defines the function `test_a_missing_recording_is_reported_not_raised`.
- Its parameters:
    - `workspace`.
    - `monkeypatch`.
    - `capsys`.

`tests/unit/interfaces/test_cli.py`, lines 29 to 42:

```python
    monkeypatch.setenv("EMBEDDINGS_PATH", str(workspace / "none"))
    assert main(["retrieval", "--split", "dev"]) != EXIT_OK
    assert "no recorded embedding" in capsys.readouterr().err


def test_a_bad_environment_value_is_a_configuration_error(workspace, monkeypatch, capsys):
    monkeypatch.setenv("INDEX_BACKEND", "redis")
    assert main(["retrieval", "--split", "dev"]) == EXIT_CONFIG
    assert "INDEX_BACKEND" in capsys.readouterr().err


def test_a_missing_prompt_is_a_configuration_error(workspace, monkeypatch, capsys):
    monkeypatch.setenv("ANSWER_PROMPT_VERSION", "v99")
    assert main(["ask", "How many days do I have to return an item?"]) == EXIT_CONFIG
```

- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Checks that `main(['retrieval', '--split', 'dev']) != EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Checks that `'no recorded embedding' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_a_bad_environment_value_is_a_configuration_error`.
- Its parameters:
    - `workspace`.
    - `monkeypatch`.
    - `capsys`.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Checks that `main(['retrieval', '--split', 'dev']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Checks that `'INDEX_BACKEND' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_a_missing_prompt_is_a_configuration_error`.
- Its parameters:
    - `workspace`.
    - `monkeypatch`.
    - `capsys`.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Checks that `main(['ask', 'How many days do I have to return an item?']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).

`tests/unit/interfaces/test_cli.py`, lines 43 to 56:

```python
    assert "no prompt file" in capsys.readouterr().err


def test_hand_grades_are_read_as_question_id_to_verdict(tmp_path):
    path = tmp_path / "g.jsonl"
    path.write_text('{"question_id": "q1", "correct": true}\n\n{"question_id": "q2", "correct": false}\n')
    assert cli._hand_grades(path) == {"q1": True, "q2": False}


def test_the_threshold_comes_from_the_override_then_the_file_then_the_default(workspace, monkeypatch):
    settings = AppSettings.from_env()
    assert cli._threshold(settings) == cli.DEFAULT_THRESHOLD
    (workspace / "threshold.json").write_text(json.dumps({"threshold": 0.61}))
    assert cli._threshold(AppSettings.from_env()) == 0.61
```

- Checks that `'no prompt file' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_hand_grades_are_read_as_question_id_to_verdict`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'g.jsonl'` under the name `path`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- Checks that `cli._hand_grades(path) == {'q1': True, 'q2': False}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `_hand_grades` of `cli`.
- Defines the function `test_the_threshold_comes_from_the_override_then_the_file_then_the_default`.
- Its parameters:
    - `workspace`.
    - `monkeypatch`.
- Stores the result of calling `AppSettings.from_env` under the name `settings`.
  - The method `from_env` of `AppSettings`.
- Checks that `cli._threshold(settings) == cli.DEFAULT_THRESHOLD` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `_threshold` of `cli`.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `json.dumps` turns Python data into JSON text.
  - `/` is divide.
- Checks that `cli._threshold(AppSettings.from_env()) == 0.61` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `_threshold` of `cli`.
  - The method `from_env` of `AppSettings`.

`tests/unit/interfaces/test_cli.py`, lines 57 to 58:

```python
    monkeypatch.setenv("REFUSAL_THRESHOLD", "0.7")
    assert cli._threshold(AppSettings.from_env()) == 0.7
```

- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Checks that `cli._threshold(AppSettings.from_env()) == 0.7` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `_threshold` of `cli`.
  - The method `from_env` of `AppSettings`.

### `tests/unit/interfaces/test_cli_commands.py`

78 non-blank lines; it defines `replay`, `test_ingest_reports_pages_chunks_and_the_skipped_retired_pages`, `test_a_known_question_is_answered_from_its_recording_with_citations`, `test_a_question_far_from_every_page_is_refused_before_the_model`, `test_retrieval_prints_a_row_per_type_and_mode_with_intervals`, `test_tuning_writes_the_threshold_from_the_dev_questions_only`, `test_evaluate_prints_both_grades_dumps_every_answer_and_writes_a_report`, `test_serve_builds_the_app_and_hands_it_to_uvicorn`.

`tests/unit/interfaces/test_cli_commands.py`, lines 1 to 14:

```python
import json
from pathlib import Path
from typing import Any

import pytest

from cited_answers.interfaces import server
from cited_answers.interfaces.cli import EXIT_OK, main

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def replay(tmp_path, monkeypatch):
```

- Makes the module `json` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `pytest` (installed package) available.
- Brings in `server` from the project module `cited_answers.interfaces`.
- Brings in `EXIT_OK`, `main` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).) from the project module `cited_answers.interfaces.cli`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `3` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Defines the function `replay`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- Its parameters:
    - `tmp_path`.
    - `monkeypatch`.

`tests/unit/interfaces/test_cli_commands.py`, lines 15 to 26:

```python
    monkeypatch.setenv("PAGES_DIR", str(REPO / "data" / "pages"))
    monkeypatch.setenv("QUESTIONS_DIR", str(REPO / "data" / "questions"))
    monkeypatch.setenv("PROMPTS_DIR", str(REPO / "prompts"))
    monkeypatch.setenv("THRESHOLD_PATH", str(tmp_path / "threshold.json"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("EMBEDDER_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(REPO / "tests" / "fixtures" / "recordings"))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(REPO / "tests" / "fixtures" / "embeddings"))
    monkeypatch.setenv("REFUSAL_THRESHOLD", "0.648")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path
```

- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Ends the function and gives back the value named `tmp_path` to the caller.

`tests/unit/interfaces/test_cli_commands.py`, lines 29 to 40:

```python
def test_ingest_reports_pages_chunks_and_the_skipped_retired_pages(replay, capsys):
    assert main(["ingest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "indexed 57 current pages as 68 chunks" in out
    assert "p-return-window-old" in out


def test_a_known_question_is_answered_from_its_recording_with_citations(replay, capsys):
    assert main(["ask", "How many days do I have to return an item?"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "[p-return-window:0]" in out
    assert "answered: none" in out
```

- Defines the function `test_ingest_reports_pages_chunks_and_the_skipped_retired_pages`.
- Its parameters:
    - `replay`.
    - `capsys`.
- Checks that `main(['ingest']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'indexed 57 current pages as 68 chunks' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'p-return-window-old' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_a_known_question_is_answered_from_its_recording_with_citations`.
- Its parameters:
    - `replay`.
    - `capsys`.
- Checks that `main(['ask', 'How many days do I have to return an item?']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'[p-return-window:0]' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'answered: none' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/interfaces/test_cli_commands.py`, lines 43 to 54:

```python
def test_a_question_far_from_every_page_is_refused_before_the_model(replay, capsys):
    assert main(["ask", "Do you ship to Antarctica?"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "I don't have information about that" in out
    assert "below_threshold" in out


def test_retrieval_prints_a_row_per_type_and_mode_with_intervals(replay, capsys):
    assert main(["retrieval", "--split", "dev"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "answerable vector" in out
    assert "exact      fused" in out
```

- Defines the function `test_a_question_far_from_every_page_is_refused_before_the_model`.
- Its parameters:
    - `replay`.
    - `capsys`.
- Checks that `main(['ask', 'Do you ship to Antarctica?']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `"I don't have information about that" in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'below_threshold' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_retrieval_prints_a_row_per_type_and_mode_with_intervals`.
- Its parameters:
    - `replay`.
    - `capsys`.
- Checks that `main(['retrieval', '--split', 'dev']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'answerable vector' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'exact fused' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/interfaces/test_cli_commands.py`, lines 55 to 68:

```python
    assert "Wilson" in out


def test_tuning_writes_the_threshold_from_the_dev_questions_only(replay, monkeypatch, capsys):
    monkeypatch.delenv("REFUSAL_THRESHOLD")
    assert main(["tune-threshold"]) == EXIT_OK
    written = json.loads((replay / "threshold.json").read_text())
    assert written["tuned_on"] == "dev"
    assert written["threshold"] == 0.648
    assert "wrongly refuses" in capsys.readouterr().out


def test_evaluate_prints_both_grades_dumps_every_answer_and_writes_a_report(replay, capsys):
    dump = replay / "answers.jsonl"
```

- Checks that `'Wilson' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_tuning_writes_the_threshold_from_the_dev_questions_only`.
- Its parameters:
    - `replay`.
    - `monkeypatch`.
    - `capsys`.
- Calls `.delenv(...)` removes an environment variable for one test with 1 argument(s); the result is not kept.
  - `.delenv(...)` removes an environment variable for one test.
- Checks that `main(['tune-threshold']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Stores the result of calling `json.loads` under the name `written`.
  - `json.loads` turns JSON text into Python data.
  - `.read_text(...)` reads a whole file as text.
  - `/` is divide.
- Checks that `written['tuned_on'] == 'dev'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `written['threshold'] == 0.648` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'wrongly refuses' in capsys.readouterr().out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_evaluate_prints_both_grades_dumps_every_answer_and_writes_a_report`.
- Its parameters:
    - `replay`.
    - `capsys`.
- Stores the result of `replay / 'answers.jsonl'` under the name `dump`.
  - `/` is divide.

`tests/unit/interfaces/test_cli_commands.py`, lines 69 to 82:

```python
    code = main(
        [
            "evaluate",
            "--split",
            "dev",
            "--prompt",
            "v2",
            "--dump",
            str(dump),
            "--write-report",
            "--hand-grades",
            str(REPO / "evals" / "hand_grades.jsonl"),
        ]
    )
```

- Stores the result of calling `main` under the name `code`.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
  - `str` turns a value into text.
  - `/` is divide.

`tests/unit/interfaces/test_cli_commands.py`, lines 83 to 96:

```python
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "answer correct (judge)" in out
    assert "judge agreement with hand grades: 21/22" in out
    assert len(dump.read_text().splitlines()) == 30
    assert (replay / "reports" / "dev-answer-v2.txt").read_text().startswith("== dev set, answer prompt v2")


def test_serve_builds_the_app_and_hands_it_to_uvicorn(replay, monkeypatch):
    captured: dict[str, Any] = {}
    monkeypatch.setattr(server.uvicorn, "run", lambda app, **kw: captured.update(app=app, **kw))  # type: ignore[attr-defined]
    assert main(["serve"]) == EXIT_OK
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8080
```

- Checks that `code == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'answer correct (judge)' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'judge agreement with hand grades: 21/22' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `len(dump.read_text().splitlines()) == 30` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Checks that `(replay / 'reports' / 'dev-answer-v2.txt').read_text().startswith('== dev set...` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
  - `/` is divide.
- Defines the function `test_serve_builds_the_app_and_hands_it_to_uvicorn`.
- Its parameters:
    - `replay`.
    - `monkeypatch`.
- Declares `captured` as a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls the method `setattr` of `monkeypatch` with 3 argument(s); the result is not kept.
  - The method `setattr` of `monkeypatch`.
  - `lambda args: expression` is a small unnamed function written inline.
  - `.update(...)` merges another collection into this one.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- Checks that `main(['serve']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `cited_answers.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 4 interrupted).).
- Checks that `captured['host'] == '127.0.0.1'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `captured['port'] == 8080` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/interfaces/test_cli_commands.py`, lines 97 to 97:

```python
    assert captured["timeout_graceful_shutdown"] == 10
```

- Checks that `captured['timeout_graceful_shutdown'] == 10` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/unit/interfaces/test_http.py`

53 non-blank lines; it defines `client`, `test_health_is_ok_with_chunks_and_not_ready_without`, `test_a_cited_answer_returns_its_citations_with_page_and_heading`, `test_the_fixed_refusal_comes_back_with_its_reason`, `test_bad_requests_are_rejected_before_any_work`, `test_a_model_outage_is_a_503_not_a_stack_trace`, `test_info_logs_carry_a_hash_of_the_question_never_its_text`.

`tests/unit/interfaces/test_http.py`, lines 1 to 14:

```python
from fastapi.testclient import TestClient

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.domain.errors import TransientModelError
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.interfaces.http import create_app
from tests.conftest import PAGES, PROMPT, HashingEmbedder, MemoryPages, ScriptedModel


def client(answer, count=lambda: 4, threshold=0.0):
    embedder, store = HashingEmbedder(), InMemoryChunkStore()
    ingest(MemoryPages(PAGES), embedder, store)
    service = AnswerService(HybridRetriever(store, embedder), ScriptedModel(answer), PROMPT, threshold)
```

- Brings in `TestClient` from the installed package module `fastapi.testclient`.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.) from the project module `cited_answers.application.answer`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.
- Brings in `create_app` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.) from the project module `cited_answers.interfaces.http`.
- Brings in `PAGES`, `PROMPT`, `HashingEmbedder` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.), `MemoryPages` (A page source over a list.), `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Defines the function `client`.
- Its parameters:
    - `answer`.
    - `count`; if the caller leaves it out it is a small function.
    - `threshold`; if the caller leaves it out it is the number `0.0`.
- Stores a tuple of 2 item(s) under the name `(embedder, store)`.
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `MemoryPages` from the project's `tests.conftest` (A page source over a list.).
- Stores the result of calling `AnswerService` under the name `service`.
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).

`tests/unit/interfaces/test_http.py`, lines 15 to 25:

```python
    return TestClient(create_app(service, count))


def test_health_is_ok_with_chunks_and_not_ready_without():
    assert client(lambda r: "x").get("/health").json() == {"status": "ok", "chunks": 4}
    empty = client(lambda r: "x", count=lambda: 0).get("/health")
    assert empty.status_code == 503
    assert empty.json()["status"] == "not ready"


def test_a_cited_answer_returns_its_citations_with_page_and_heading():
```

- Ends the function and gives back the result of calling `TestClient` to the caller.
  - `TestClient` from the installed package module `fastapi.testclient`.
  - `create_app` from the project's `cited_answers.interfaces.http` (Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready.).
- Defines the function `test_health_is_ok_with_chunks_and_not_ready_without`.
- It takes no parameters.
- Checks that `client(lambda r: 'x').get('/health').json() == {'status': 'ok', 'chunks': 4}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `client(lambda r: 'x', count=lambda: 0).get` under the name `empty`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `empty.status_code == 503` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `empty.json()['status'] == 'not ready'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the function `test_a_cited_answer_returns_its_citations_with_page_and_heading`.
- It takes no parameters.

`tests/unit/interfaces/test_http.py`, lines 26 to 39:

```python
    body = (
        client(lambda r: "Thirty days [p-return-window:0].")
        .post("/ask", json={"question": "How many days to return?"})
        .json()
    )
    assert body["status"] == "answered"
    assert body["citations"] == [
        {"chunk_id": "p-return-window:0", "page_id": "p-return-window", "heading_path": "Return window > 30 days"}
    ]
    assert body["reason"] == "none"


def test_the_fixed_refusal_comes_back_with_its_reason():
    body = client(lambda r: "no citation here").post("/ask", json={"question": "How many days to return?"}).json()
```

- Stores the result of calling `client(lambda r: 'Thirty days [p-return-window:...` under the name `body`.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `body['status'] == 'answered'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['citations'] == [{'chunk_id': 'p-return-window:0', 'page_id': 'p-return-...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['reason'] == 'none'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_the_fixed_refusal_comes_back_with_its_reason`.
- It takes no parameters.
- Stores the result of calling `client(lambda r: 'no citation here').post('/ask...` under the name `body`.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.

`tests/unit/interfaces/test_http.py`, lines 40 to 53:

```python
    assert (body["status"], body["reason"], body["citations"]) == ("refused", "no_citation", [])
    assert body["answer"].startswith("I don't have information")


def test_bad_requests_are_rejected_before_any_work():
    c = client(lambda r: "x")
    assert c.post("/ask", json={"question": "hi"}).status_code == 422
    assert c.post("/ask", json={"question": "x" * 501}).status_code == 422
    assert c.post("/ask", json={"question": "a fine question", "extra": 1}).status_code == 422
    assert c.post("/ask", json={}).status_code == 422


def test_a_model_outage_is_a_503_not_a_stack_trace():
    def fail(request):
```

- Checks that `(body['status'], body['reason'], body['citations']) == ('refused', 'no_citati...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['answer'].startswith("I don't have information")` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_bad_requests_are_rejected_before_any_work`.
- It takes no parameters.
- Stores the result of calling `client` under the name `c`.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `c.post('/ask', json={'question': 'hi'}).status_code == 422` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Checks that `c.post('/ask', json={'question': 'x' * 501}).status_code == 422` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
  - `*` is multiply.
- Checks that `c.post('/ask', json={'question': 'a fine question', 'extra': 1}).status_code ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Checks that `c.post('/ask', json={}).status_code == 422` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Defines the function `test_a_model_outage_is_a_503_not_a_stack_trace`.
- It takes no parameters.
- Defines the function `fail`.
- Its parameters:
    - `request`.

`tests/unit/interfaces/test_http.py`, lines 54 to 67:

```python
        raise TransientModelError("down")

    response = client(fail).post("/ask", json={"question": "How many days to return?"})
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_info_logs_carry_a_hash_of_the_question_never_its_text(caplog):
    import logging

    with caplog.at_level(logging.INFO):
        client(lambda r: "Thirty days [p-return-window:0].").post(
            "/ask", json={"question": "my private question about returns"}
        )
```

- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `cited_answers.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
- Stores the result of calling `client(fail).post` under the name `response`.
  - `.post(...)` sends an HTTP POST request.
  - `client`, a function of this file.
- Checks that `response.status_code == 503` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'unavailable' in response.json()['detail']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the function `test_info_logs_carry_a_hash_of_the_question_never_its_text`.
- Its parameters:
    - `caplog`.
- Makes the module `logging` (standard library) available.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Calls `.post(...)` sends an HTTP POST request with 2 argument(s); the result is not kept.
  - `.post(...)` sends an HTTP POST request.
  - `client`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.

`tests/unit/interfaces/test_http.py`, lines 68 to 70:

```python
    assert "private" not in caplog.text
    record = next(r for r in caplog.records if r.getMessage() == "question answered")
    assert len(record.fields["question_sha"]) == 10
```

- Checks that `'private' not in caplog.text` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Stores the result of calling `next` under the name `record`.
  - `next` takes the next item from an iterator.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - The method `getMessage` of `r`.
- Checks that `len(record.fields['question_sha']) == 10` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/unit --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/interfaces/test_http.py::test_info_logs_carry_a_hash_of_the_question_never_its_text

153 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/unit -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
........................................................................ [ 94%]
.........                                                                [100%]
153 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/unit/application/test_retrieve_answer_evaluate.py::test_ingest_indexes_current_pages_only_and_names_the_retired_ones
tests/unit/application/test_retrieve_answer_evaluate.py::test_ingest_logs_each_skipped_page
tests/unit/application/test_retrieve_answer_evaluate.py::test_a_search_for_the_old_return_window_returns_no_retired_chunk
tests/unit/application/test_retrieve_answer_evaluate.py::test_embedding_is_done_in_batches
tests/unit/application/test_retrieve_answer_evaluate.py::test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/unit/infrastructure/test_resilience_logging_factory.py` test?

   *Answer:* It holds the tests for `resilience logging factory`.

2. What does `tests/unit/interfaces/test_cli.py` test?

   *Answer:* It holds the tests for `cli`.

3. What does `tests/unit/interfaces/test_cli_commands.py` test?

   *Answer:* It holds the tests for `cli commands`.

4. What does `tests/unit/interfaces/test_http.py` test?

   *Answer:* It holds the tests for `http`.

5. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
