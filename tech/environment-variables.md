# Environment variables

## What it is

Every running program receives a small set of named text values from whoever started it, called **environment variables**. They are the standard way to configure a program without changing its code: the same program behaves differently in a test, on your laptop and in production depending on a few variables. `HOME` and `PATH` are examples every shell sets. In a shell, `NAME=value command` starts `command` with `NAME` set for that run only; `export NAME=value` sets it for everything started afterwards.

Variables are always text. A program that wants a number or a yes/no must convert the text and check it.

## Why this repository uses it

The six sibling repositories follow the *twelve-factor* rule of keeping configuration in the environment: which model answers, where files live, which port to use, how patient to be. This makes the default behavior safe (replay recorded answers, no network, no key) and lets a person switch to a live model with one line. **Secrets** such as an API key must never be written into a file in the repository; `env.example` says so, and `.gitignore` excludes `.env`.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `env.example` | the documented list of every variable, with defaults (copy it to `.env` to change a value) |
| `.gitignore` | excludes `.env`, your private copy |
| `Makefile` | `-include .env` / `export`, and per-command prefixes such as `MODEL_PROVIDER=...` |
| `src/cited_answers/infrastructure/env.py` | typed readers for the variables |
| `src/cited_answers/infrastructure/settings.py` | builds the settings once at start-up |
| `tests/` | tests use `monkeypatch.setenv` to set variables for one test |

## How it works underneath

When a process starts, the operating system gives it a block of `NAME=value` strings. A child process inherits a copy of its parent's variables, which is why `make` can pass settings to the programs it starts. A change a program makes to its own variables does not affect its parent or siblings. In Python they are available as `os.environ`, a dictionary-like object of text values.

`env.example` is not read by the program. It is documentation in a format you can copy: `cp env.example .env`. (The harness this work was done in could not write the usual file name `.env.example`, so the repository uses `env.example`; see its first lines.)

## Walkthrough of this repository's use

`env.example`, the whole file, block by block. Under each block, every line is explained.

```text
# Copy to .env to change a value (cp env.example .env). Nothing here is a secret; real keys come from your
# shell, never from a file in the repository.
# (Template note: TEMPLATE.md names this file .env.example; this session's tooling could not write that name.)
```

- `# Copy to .env to change a value (cp env.example .env). Nothing here is a secret; real keys come from your`: A comment (lines starting with `#` are ignored).
- `# shell, never from a file in the repository.`: A comment (lines starting with `#` are ignored).
- `# (Template note: TEMPLATE.md names this file .env.example; this session's tooling could not write that name.)`: A comment (lines starting with `#` are ignored).

```text
# --- which models answer -------------------------------------------------------------------------------
# recorded            replay tests/fixtures (default for tests and make run; no network, no key)
# openai-compatible   a local server such as ollama or llama.cpp (make models), or any OpenAI-compatible endpoint
# anthropic           Claude through the official SDK; needs ANTHROPIC_API_KEY in your shell (never in this file)
MODEL_PROVIDER=recorded
# MODEL_NAME=qwen2.5:1.5b             # default per provider: qwen2.5:1.5b (local) or claude-haiku-5-5
# JUDGE_MODEL_NAME=qwen2.5:1.5b       # the model that grades answers
# RECORDINGS_PATH=tests/fixtures/recordings
# RECORD=off                          # on: write each live answer and vector into the fixtures (make record)
# OPENAI_BASE_URL=http://localhost:11434/v1
# ANTHROPIC_THINKING=disabled         # disabled | omit | between_tools; the right value depends on the Claude model
# MODEL_TIMEOUT_SECONDS=120
# MODEL_ATTEMPTS=3                    # tries per call for timeouts, rate limits and 5xx (backoff with jitter)
EMBEDDER_PROVIDER=recorded
# EMBED_MODEL=nomic-embed-text        # 768-dimensional; the sql/001_schema.sql column is vector(768)
# EMBEDDINGS_PATH=tests/fixtures/embeddings
```

- `# --- which models answer -------------------------------------------------------------------------------`: A comment (lines starting with `#` are ignored).
- `# recorded            replay tests/fixtures (default for tests and make run; no network, no key)`: A comment (lines starting with `#` are ignored).
- `# openai-compatible   a local server such as ollama or llama.cpp (make models), or any OpenAI-compatible endpoint`: A comment (lines starting with `#` are ignored).
- `# anthropic           Claude through the official SDK; needs ANTHROPIC_API_KEY in your shell (never in this file)`: A comment (lines starting with `#` are ignored).
- `MODEL_PROVIDER=recorded`: Sets `MODEL_PROVIDER` to `recorded` (active). which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos.
- `# MODEL_NAME=qwen2.5:1.5b             # default per provider: qwen2.5:1.5b (local) or claude-haiku-5-5`: Commented out, so the default applies. Uncomment it to set `MODEL_NAME`: the model id to ask for (for example `qwen2.5:0.5b`); each provider has a default. Note in the file: default per provider: qwen2.5:1.5b (local) or claude-haiku-5-5.
- `# JUDGE_MODEL_NAME=qwen2.5:1.5b       # the model that grades answers`: Commented out, so the default applies. Uncomment it to set `JUDGE_MODEL_NAME`: the model that grades answers. Note in the file: the model that grades answers.
- `# RECORDINGS_PATH=tests/fixtures/recordings`: Commented out, so the default applies. `RECORDINGS_PATH`: the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`).
- `# RECORD=off                          # on: write each live answer and vector into the fixtures (make record)`: Commented out, so the default applies. Uncomment it to set `RECORD`: `on` makes every live answer also get written into the recordings file, so the next run can replay it. Note in the file: on: write each live answer and vector into the fixtures (make record).
- `# OPENAI_BASE_URL=http://localhost:11434/v1`: Commented out, so the default applies. `OPENAI_BASE_URL`: the web address of an OpenAI-compatible server (ollama listens on `http://localhost:11434/v1`).
- `# ANTHROPIC_THINKING=disabled         # disabled | omit | between_tools; the right value depends on the Claude model`: Commented out, so the default applies. Uncomment it to set `ANTHROPIC_THINKING`: how the Claude adapter treats the model's optional thinking blocks (`disabled`, `omit` or `between_tools`). Note in the file: disabled | omit | between_tools; the right value depends on the Claude model.
- `# MODEL_TIMEOUT_SECONDS=120`: Commented out, so the default applies. `MODEL_TIMEOUT_SECONDS`: how long one model call may take before it counts as a timeout.
- `# MODEL_ATTEMPTS=3                    # tries per call for timeouts, rate limits and 5xx (backoff with jitter)`: Commented out, so the default applies. Uncomment it to set `MODEL_ATTEMPTS`: how many tries one model call gets when it fails with a timeout, a rate limit or a 5xx server error. Note in the file: tries per call for timeouts, rate limits and 5xx (backoff with jitter).
- `EMBEDDER_PROVIDER=recorded`: Sets `EMBEDDER_PROVIDER` to `recorded` (active). which embedding model turns text into vectors: `recorded` replays saved vectors, `openai-compatible` calls a local server.
- `# EMBED_MODEL=nomic-embed-text        # 768-dimensional; the sql/001_schema.sql column is vector(768)`: Commented out, so the default applies. Uncomment it to set `EMBED_MODEL`: the embedding model id (`nomic-embed-text` makes 768-number vectors). Note in the file: 768-dimensional; the sql/001_schema.sql column is vector(768).
- `# EMBEDDINGS_PATH=tests/fixtures/embeddings`: Commented out, so the default applies. `EMBEDDINGS_PATH`: the file or folder holding the recorded vectors.

```text
# --- the index and the service -------------------------------------------------------------------------
# INDEX_BACKEND=memory                # memory | pgvector (make up starts the database; the Makefile selects pgvector)
# DATABASE_URL=postgresql://cited:cited@localhost:55432/cited   # local development credentials only
# ANSWER_PROMPT_VERSION=v2
# JUDGE_PROMPT_VERSION=v1
# REFUSAL_THRESHOLD=                  # overrides evals/threshold.json (tuned on the development questions only)
# HTTP_HOST=127.0.0.1
# HTTP_PORT=8080
# PAGES_DIR=data/pages
# QUESTIONS_DIR=data/questions
# PROMPTS_DIR=prompts
# REPORTS_DIR=evals/reports
# LOG_LEVEL=INFO
```

- `# --- the index and the service -------------------------------------------------------------------------`: A comment (lines starting with `#` are ignored).
- `# INDEX_BACKEND=memory                # memory | pgvector (make up starts the database; the Makefile selects pgvector)`: Commented out, so the default applies. Uncomment it to set `INDEX_BACKEND`: `memory` keeps the search index in the program, `pgvector` keeps it in PostgreSQL. Note in the file: memory | pgvector (make up starts the database; the Makefile selects pgvector).
- `# DATABASE_URL=postgresql://cited:cited@localhost:55432/cited   # local development credentials only`: Commented out, so the default applies. Uncomment it to set `DATABASE_URL`: how to reach PostgreSQL: user, password, host, port and database name in one address. Note in the file: local development credentials only.
- `# ANSWER_PROMPT_VERSION=v2`: Commented out, so the default applies. `ANSWER_PROMPT_VERSION`: which version of the answer prompt to use.
- `# JUDGE_PROMPT_VERSION=v1`: Commented out, so the default applies. `JUDGE_PROMPT_VERSION`: which version of the grading prompt to use.
- `# REFUSAL_THRESHOLD=                  # overrides evals/threshold.json (tuned on the development questions only)`: Commented out, so the default applies. Uncomment it to set `REFUSAL_THRESHOLD`: overrides the refusal threshold stored in `evals/threshold.json`. Note in the file: overrides evals/threshold.json (tuned on the development questions only).
- `# HTTP_HOST=127.0.0.1`: Commented out, so the default applies. `HTTP_HOST`: the network address the HTTP server listens on (`127.0.0.1` means this computer only).
- `# HTTP_PORT=8080`: Commented out, so the default applies. `HTTP_PORT`: the port number the HTTP server listens on.
- `# PAGES_DIR=data/pages`: Commented out, so the default applies. `PAGES_DIR`: the folder of help-center pages.
- `# QUESTIONS_DIR=data/questions`: Commented out, so the default applies. `QUESTIONS_DIR`: the folder of evaluation questions.
- `# PROMPTS_DIR=prompts`: Commented out, so the default applies. `PROMPTS_DIR`: the folder holding the prompt text files.
- `# REPORTS_DIR=evals/reports`: Commented out, so the default applies. `REPORTS_DIR`: the folder where evaluation reports are written.
- `# LOG_LEVEL=INFO`: Commented out, so the default applies. `LOG_LEVEL`: how much the program logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
### How the program reads them

`src/cited_answers/infrastructure/env.py` is a set of small readers. Each takes the mapping of environment variables, a name and a default, checks the value and returns it as the right type, or raises `ConfigurationError` with a message that names the variable. The functions, with the docstring each carries:

- `text`: A non-empty string, or `default` when the variable is unset.
- `optional_text`: The variable's text, or None when it is unset or blank.
- `positive_int`: An integer of 1 or more.
- `non_negative_int`: An integer of 0 or more.
- `positive_float`: A number greater than zero.
- `non_negative_float`: A number of 0 or more.
- `choice`: One of the `allowed` strings.

For example (`src/cited_answers/infrastructure/env.py`):

`src/cited_answers/infrastructure/env.py`, lines 12 to 17:

```python
def text(environ: Mapping[str, str], name: str, default: str) -> str:
    """A non-empty string, or `default` when the variable is unset."""
    value = environ.get(name, default).strip()
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value
```

`src/cited_answers/infrastructure/settings.py` calls these readers once, at start-up, and builds one frozen settings object, so a bad value stops the program immediately with a clear message instead of failing later in the middle of a run. Nothing else in the program reads `os.environ`.

### How the Makefile helps

`-include .env` and `export` (see `make.md`) read a file named `.env`, if you made one, and pass its settings to every program `make` starts. Some targets also put variables in front of a command, such as `MODEL_PROVIDER=recorded RECORDINGS_PATH=... program`, which sets them for that one command only.

## Try it yourself

1. The first few variables of your own shell; each line is NAME=value.

```bash
env | head -3
```

What you should see (captured from this repository):

```text
CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES=false
CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL=true
NVM_INC=~/.nvm/versions/node/v24.14.1/include/node
```

2. A prefix sets a variable for one command only: the child sees `bar`, and your shell still has nothing.

```bash
FOO=bar sh -c 'echo $FOO'; echo "after: [$FOO]"
```

What you should see (captured from this repository):

```text
bar
after: []
```

3. How many optional variables are listed as commented-out lines.

```bash
grep -c '^# [A-Z_]*=' env.example
```

What you should see (captured from this repository):

```text
22
```

4. Python reads the variable as text, or a default when it is not set.

```bash
.venv/bin/python -c "import os; print(os.environ.get('MODEL_PROVIDER', 'unset'))"
```

What you should see (captured from this repository):

```text
unset
```

5. The same command with the variable set for just that run.

```bash
MODEL_PROVIDER=recorded .venv/bin/python -c "import os; print(os.environ.get('MODEL_PROVIDER', 'unset'))"
```

What you should see (captured from this repository):

```text
recorded
```

## Mistakes people make

- **Putting a secret in `.env` and committing it.** `.env` is ignored by git, and the keys are expected to come from your shell (`ANTHROPIC_API_KEY`).
- **Forgetting that values are text.** `'0'` and `'false'` are non-empty strings, hence true. The readers in `env.py` convert and validate.
- **Reading variables all over the code.** One module reads them all, once, at start-up.
- **Expecting `export` to survive the terminal.** It lasts only for that shell and its children.
- **Assuming a default.** Each variable's default is written in `env.example`; the program refuses unusable values.

## Check yourself

1. What is an environment variable?

   *Answer:* A named text value that the operating system hands to a program when it starts.

2. What does `NAME=value command` do?

   *Answer:* Runs the command with `NAME` set to `value` for that one run.

3. Why must secrets stay out of the repository?

   *Answer:* Anything committed is copied to every clone and is hard to remove from history.

4. Why does the program check variables at start-up?

   *Answer:* So a bad setting stops it at once with a clear message.

5. Where do you change a setting for every command?

   *Answer:* In `.env`, which the Makefile includes.

## Further reading

- The Twelve-Factor App, section III Config, https://12factor.net/config and Python `os.environ`, https://docs.python.org/3/library/os.html#os.environ (examples run locally).
