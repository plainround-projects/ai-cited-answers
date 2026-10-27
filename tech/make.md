# Make and the Makefile

## What it is

**make** is a program that runs named recipes. You give it a file called `Makefile`. In that file you write *targets* (a name, followed by a colon), the *prerequisites* the target needs (other targets or files), and a *recipe* (the shell commands that make the target). When you type `make test` in a terminal, make finds the target `test`, first brings its prerequisites up to date, then runs its commands one by one.

A **terminal** is the text window where you type commands. A **shell** is the program inside the terminal that reads what you type and starts other programs. A **command** is one line you give the shell. A **target** is the thing you ask make to produce, such as `test`. A **recipe** is the list of commands under a target. A **prerequisite** is something that must exist or be current before the recipe runs.

make was written in 1976 to rebuild programs from source files, and it is still used because it is small and installed almost everywhere. In this repository it does not compile anything. It is a *menu of commands*: it gives every task a short, memorable name.

## Why this repository uses it

A new person cannot guess which ten commands to type, in which order, with which flags. The Makefile writes them down once, so `make up`, `make run`, `make test`, `make lint` and `make down` mean the same thing on every computer and in the continuous-integration job. It also encodes *order*: `make test` first makes sure the virtual environment exists, because the target depends on a stamp file; you cannot forget the install step.

The Makefile also keeps the long environment settings (which model to use, where recordings live, which port) in one place, so the commands in the README stay short.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | the whole file: 24 targets that wrap every command in the project |
| `.github/workflows/ci.yml` | runs `make check` and `make audit` on every push |
| `.editorconfig` | tells editors to use real tab characters in the Makefile (`[Makefile]` section) |
| `README.md` | tells the reader to run `make up`, `make run`, `make test` |

## How it works underneath

**How make reads the file.** make reads the whole Makefile first. It builds a graph: each target points at its prerequisites. Then it walks the graph from the target you asked for. For a target that is the *name of a file*, it compares modification times: if the file exists and is newer than every prerequisite, nothing needs doing; if it is missing or older, the recipe runs. This is what the stamp rule in this repository uses: `.venv/.installed` is rebuilt only when `requirements-dev.lock` or `pyproject.toml` has changed since it was last touched.

**Phony targets.** `test`, `lint` and `down` are not files. The `.PHONY` line says so; make then always runs their recipes.

**Each recipe line is its own shell.** make starts a new `/bin/sh -c "..."` for every line of a recipe. A `cd` on one line is forgotten by the next line. That is why long jobs in this Makefile are written on one line with `;` or `&&` between the parts, or with a trailing backslash that joins physical lines.

**Variables.** `NAME = value` is looked up lazily every time it is used. `NAME := value` is worked out once, right away. `NAME ?= value` sets it only if it is not already set (from the command line or the environment). `$(NAME)` pastes the value. Inside a recipe a single `$` belongs to make, so a `$` meant for the shell is written `$$`.

**Special characters in front of a recipe line.** `@` means do not print the command before running it. `-` means ignore a failure and keep going.

**Exit codes.** Every program ends with a number: `0` means success, anything else means failure. make stops at the first recipe line that returns non-zero and returns failure itself, which is how `make check` makes a build go red.

**The required tab.** A recipe line must start with a real tab character, not spaces. If it does not, GNU Make says `missing separator`. This repository's `.editorconfig` has `[Makefile]` / `indent_style = tab` so editors keep the tabs.

## Walkthrough of this repository's use

`Makefile`, the whole file, block by block. Under each block, every line is explained.

```make
# make up | run | serve | record | test | test-integration | test-live | lint | down      (make help lists everything)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
CITED := $(VENV)/bin/cited
STAMP := $(VENV)/.installed
PSQL := docker compose exec -T db psql -U cited -d cited -v ON_ERROR_STOP=1 -q
GEN_MODEL ?= qwen2.5:1.5b
EMBED_MODEL ?= nomic-embed-text
RECORDINGS := tests/fixtures/recordings
EMBEDDINGS := tests/fixtures/embeddings
```

- `# make up | run | serve | record | test | test-integration | test-live | lint | down      (make help lists everything)`: A comment. make ignores everything after a `#`.
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: Sets `PYTHON` to the Python program used to make the virtual environment. `?=` means "set this only if it is not already set", so you can override it (`make PYTHON=python3.12 up`). `$(shell ...)` runs a shell command while make reads the file and pastes in what it prints. `command -v NAME` prints the full path of `NAME` if it exists and prints nothing (and fails) if not. The `||` means "if the left side failed, try the right side", so the line tries Python 3.13, then 3.12, then plain `python3`.
- `VENV := .venv`: Sets `VENV` to the name of the virtual-environment folder. `:=` means "work out the value now, once".
- `PY := $(VENV)/bin/python`: Sets `PY` to the Python program inside the virtual environment. `$(VENV)` is replaced by `.venv`, so this is `.venv/bin/python`.
- `CITED := $(VENV)/bin/cited`: Sets `CITED` to `.venv/bin/cited`, the command-line program of this project that pip installed into the virtual environment (it is declared under `[project.scripts]` in `pyproject.toml`).
- `STAMP := $(VENV)/.installed`: Sets `STAMP` to `.venv/.installed`, an empty file that the install rule creates when it finishes. Its modification time records "the environment was installed at this moment".
- `PSQL := docker compose exec -T db psql -U cited -d cited -v ON_ERROR_STOP=1 -q`: Sets `PSQL` to the command that runs the PostgreSQL command-line client `psql` inside the already-running `db` container: `docker compose exec` runs a command in a running container; `-T` turns off the interactive terminal so input can be piped in; `-U cited -d cited` names the database user and the database; `-v ON_ERROR_STOP=1` makes psql stop at the first SQL error instead of carrying on; `-q` keeps psql quiet.
- `GEN_MODEL ?= qwen2.5:1.5b`: Sets `GEN_MODEL` to `qwen2.5:1.5b` unless you already set it. This is the name of a small open-weight model that `ollama` can download (the part before the colon is the model family, the part after it is the size variant).
- `EMBED_MODEL ?= nomic-embed-text`: Sets `EMBED_MODEL` to `nomic-embed-text` unless you already set it. This is the name of a small open-weight model that `ollama` can download (the part before the colon is the model family, the part after it is the size variant).
- `RECORDINGS := tests/fixtures/recordings`: Sets `RECORDINGS` to the path `tests/fixtures/recordings`. Naming a path once means every target that needs it uses the same text.
- `EMBEDDINGS := tests/fixtures/embeddings`: Sets `EMBEDDINGS` to the path `tests/fixtures/embeddings`. Naming a path once means every target that needs it uses the same text.

```make
-include .env
export
```

- `-include .env`: Reads the file `.env` if it exists (a plain `include` would stop with an error when it is missing; the leading `-` means "if it is missing, carry on"). The file holds `NAME=value` lines you copied from `env.example`.
- `export`: Passes every make variable to the programs that make starts, as environment variables. Together with the line above, a value written in `.env` reaches the Python program.

```make
# The service and the evaluation use the pgvector index; the unit and end-to-end tests use the in-memory one.
PG := INDEX_BACKEND=pgvector
REPLAY := MODEL_PROVIDER=recorded EMBEDDER_PROVIDER=recorded RECORDINGS_PATH=$(RECORDINGS) EMBEDDINGS_PATH=$(EMBEDDINGS)
```

- `# The service and the evaluation use the pgvector index; the unit and end-to-end tests use the in-memory one.`: A comment. make ignores everything after a `#`.
- `PG := INDEX_BACKEND=pgvector`: Sets `PG` to the text `INDEX_BACKEND=pgvector`, which later lines put in front of a command so that command keeps its search index in PostgreSQL.
- `REPLAY := MODEL_PROVIDER=recorded EMBEDDER_PROVIDER=recorded RECORDINGS_PATH=$(RECORDINGS) EMBEDDINGS_PATH=$(EMBEDDINGS)`: Sets `REPLAY` to a list of NAME=value pairs that make the program replay recorded model answers and recorded vectors instead of calling a model. The words of the form NAME=value in front of the program name set environment variables for that one command only: MODEL_PROVIDER (which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos); EMBEDDER_PROVIDER (which embedding model turns text into vectors: `recorded` replays saved vectors, `openai-compatible` calls a local server); RECORDINGS_PATH (the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`)); EMBEDDINGS_PATH (the file or folder holding the recorded vectors).

```make
.PHONY: help install up db ingest ask serve docker-up run retrieval tune-threshold evaluate models record lint format \
        test test-integration test-e2e test-live audit check down clean
```

- `.PHONY: help install up db ingest ask serve docker-up run retrieval tune-threshold evaluate models record lint format test test-integration test-e2e test-live audit check down clean`: Declares these names "phony": they are the names of actions, not of files. Without this, a file or folder that happens to be called `test` or `clean` would make make think the target was already up to date and skip it.

```make
help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- `help: ## list the targets`: Defines the target `help`. It has no prerequisites. The text after `##` (`list the targets`) is the help text that `make help` prints.
- `grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: The leading `@` tells make not to print the command before running it. Prints the help list. `grep -E` searches for lines matching a pattern: here, lines that start with a target name made of lowercase letters and hyphens, then a colon, and contain `## `. `$(MAKEFILE_LIST)` is the name of this Makefile. The `|` (pipe) hands grep's output to `sed -E 's/:.*## /\t/'`, which replaces everything from the colon through `## ` with a tab character, leaving `target<TAB>help text`. The next `|` hands that to `sort`, which puts the lines in alphabetical order.

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(STAMP): requirements-dev.lock pyproject.toml`: Defines a rule whose target is a file, the stamp (`.venv/.installed`). Its prerequisites, which make brings up to date before running the recipe: the file `requirements-dev.lock`; the file `pyproject.toml`. If the stamp is missing, or older than either file, make runs the recipe below; otherwise it does nothing, which makes every later `make` command start fast.
- `$(PYTHON) -m venv $(VENV)`: Creates the virtual environment: a private folder `.venv` holding its own copy of the Python program and its own empty place for installed packages. `-m venv` means "run the module named `venv` that ships with Python".
- `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`: Installs every package named in `requirements-dev.lock` into the virtual environment. `-q` is quiet. `--require-hashes` makes pip refuse any file whose fingerprint (a sha256 hash) is not listed in the lock file, and also refuse any package that is not pinned to an exact version. `-r FILE` means "read the list of packages from this file".
- `$(VENV)/bin/pip install -q --no-deps -e .`: Installs this project itself. `.` means "the project in this folder". `-e` (editable) links the code in `src/` instead of copying it, so editing a file takes effect at once. `--no-deps` stops pip from looking for dependencies again: the lock file already installed exactly the versions wanted.
- `touch $@`: Creates the stamp file, or updates its modification time. `$@` is make's automatic name for "the target of this rule", here `.venv/.installed`. The stamp is only touched if every line above succeeded, because make stops at the first failing line.

```make
install: $(STAMP) ## create .venv from the lock file
```

- `install: $(STAMP) ## create .venv from the lock file`: Defines the target `install`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`create .venv from the lock file`) is the help text that `make help` prints.

```make
up: $(STAMP) ## start Postgres with pgvector, create the tables, load the pages and build the index
	docker compose up -d --wait db
	$(MAKE) --no-print-directory db
	$(MAKE) --no-print-directory ingest
```

- `up: $(STAMP) ## start Postgres with pgvector, create the tables, load the pages and build the index`: Defines the target `up`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`start Postgres with pgvector, create the tables, load the pages and build the index`) is the help text that `make help` prints.
- `docker compose up -d --wait db`: Starts only the service named `db` from `docker-compose.yml`. `-d` (detached) returns to the prompt instead of staying attached to the container's output; `--wait` makes the command wait until the container reports healthy.
- `$(MAKE) --no-print-directory db`: Runs make again for the target `db`. `--no-print-directory` stops make from printing "Entering directory ..." lines.
- `$(MAKE) --no-print-directory ingest`: Runs make again for the target `ingest`, which loads the pages into the search index.

```make
db: ## apply sql/001_schema.sql and sql/002_seed.sql (safe to repeat)
	@for i in $$(seq 1 180); do docker compose exec -T db psql -U cited -d cited -qc 'select 1' >/dev/null 2>&1 && break || sleep 1; done
	$(PSQL) < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql
```

- `db: ## apply sql/001_schema.sql and sql/002_seed.sql (safe to repeat)`: Defines the target `db`. It has no prerequisites. The text after `##` (`apply sql/001_schema.sql and sql/002_seed.sql (safe to repeat)`) is the help text that `make help` prints.
- `for i in $$(seq 1 180); do docker compose exec -T db psql -U cited -d cited -qc 'select 1' >/dev/null 2>&1 && break || sleep 1; done`: The leading `@` tells make not to print the command before running it. Waits until the database answers. `seq 1 180` prints the numbers 1 to 180, so the loop runs at most 180 times. Each time it tries to run the SQL `select 1` inside the container; `>/dev/null 2>&1` throws away both the normal output and the error output. If the command works (`&&`) the loop stops (`break`); if not (`||`) it waits one second (`sleep 1`) and tries again.
- `$(PSQL) < sql/001_schema.sql`: Feeds the SQL file `sql/001_schema.sql` to `psql` through its standard input (`<`), which creates the tables.
- `$(PSQL) < sql/002_seed.sql`: Feeds `sql/002_seed.sql` to `psql`, which loads the starting data.

```make
ingest: $(STAMP) ## chunk the current pages, embed them (recorded vectors) and fill the pgvector index
	$(REPLAY) $(PG) $(CITED) ingest
```

- `ingest: $(STAMP) ## chunk the current pages, embed them (recorded vectors) and fill the pgvector index`: Defines the target `ingest`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`chunk the current pages, embed them (recorded vectors) and fill the pgvector index`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) ingest`: Runs `cited ingest` with the replay variables and the PostgreSQL index switch in front. It cuts the help pages into chunks, takes their vectors from the recordings and fills the index.

```make
# make ask Q="What is your return window?"
Q ?= How many days do I have to return an item?
ask: $(STAMP) ## ask one question against the pgvector index with the recorded model (only recorded questions work offline)
	$(REPLAY) $(PG) $(CITED) ask "$(Q)"
```

- `# make ask Q="What is your return window?"`: A comment. make ignores everything after a `#`.
- `Q ?= How many days do I have to return an item?`: Sets `Q`, the question `make ask` sends, unless you set it yourself (`make ask Q="..."`).
- `ask: $(STAMP) ## ask one question against the pgvector index with the recorded model (only recorded questions work offline)`: Defines the target `ask`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`ask one question against the pgvector index with the recorded model (only recorded questions work offline)`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) ask "$(Q)"`: Runs `cited ask` with the question in `Q`. The double quotes keep the question as one argument even though it holds spaces.

```make
serve: $(STAMP) ## run the HTTP service on :8080 against the pgvector index (live local model; make models first)
	$(PG) MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible $(CITED) serve
```

- `serve: $(STAMP) ## run the HTTP service on :8080 against the pgvector index (live local model; make models first)`: Defines the target `serve`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`run the HTTP service on :8080 against the pgvector index (live local model; make models first)`) is the help text that `make help` prints.
- `$(PG) MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible $(CITED) serve`: Starts the HTTP service in the foreground against the PostgreSQL index and the local models. It keeps running until you press Ctrl-C.

```make
docker-up: ## build and start the service in a container next to the database (needs a model server on the host)
	docker compose --profile api up -d --build --wait
```

- `docker-up: ## build and start the service in a container next to the database (needs a model server on the host)`: Defines the target `docker-up`. It has no prerequisites. The text after `##` (`build and start the service in a container next to the database (needs a model server on the host)`) is the help text that `make help` prints.
- `docker compose --profile api up -d --build --wait`: Builds the service image and starts the service next to the database. `--profile api` switches on the services that the compose file marks with the profile `api`; `--build` builds the image first.

```make
retrieval: $(STAMP) ## hit rate at 5 for vectors, keywords and both fused, test questions
	$(REPLAY) $(PG) $(CITED) retrieval --split test
```

- `retrieval: $(STAMP) ## hit rate at 5 for vectors, keywords and both fused, test questions`: Defines the target `retrieval`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`hit rate at 5 for vectors, keywords and both fused, test questions`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) retrieval --split test`: Runs `cited retrieval` on the test questions: it measures how often the right page is among the top five results.

```make
tune-threshold: $(STAMP) ## choose the refusal threshold on the 30 development questions only
	$(REPLAY) $(PG) $(CITED) tune-threshold
```

- `tune-threshold: $(STAMP) ## choose the refusal threshold on the 30 development questions only`: Defines the target `tune-threshold`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`choose the refusal threshold on the 30 development questions only`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) tune-threshold`: Runs `cited tune-threshold`, which picks the refusal threshold using only the development questions.

```make
evaluate: $(STAMP) ## retrieval and answers graded apart on the frozen test set, judge checked against hand grades
	$(REPLAY) $(PG) $(CITED) evaluate --split test --hand-grades evals/hand_grades.jsonl
```

- `evaluate: $(STAMP) ## retrieval and answers graded apart on the frozen test set, judge checked against hand grades`: Defines the target `evaluate`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`retrieval and answers graded apart on the frozen test set, judge checked against hand grades`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) evaluate --split test --hand-grades evals/hand_grades.jsonl`: Runs `cited evaluate` on the test questions and compares the automatic judge with grades a person wrote by hand.

```make
run: up ## the lesson's scenario with recorded models: retrieval, then answers with prompt v1 (before) and v2 (after)
	$(REPLAY) $(PG) $(CITED) retrieval --split dev
	$(REPLAY) $(PG) $(CITED) retrieval --split test
	$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v1
	$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v2 --hand-grades evals/hand_grades.jsonl
	$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v1
	$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v2 --hand-grades evals/hand_grades.jsonl
```

- `run: up ## the lesson's scenario with recorded models: retrieval, then answers with prompt v1 (before) and v2 (after)`: Defines the target `run`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`the lesson's scenario with recorded models: retrieval, then answers with prompt v1 (before) and v2 (after)`) is the help text that `make help` prints.
- `$(REPLAY) $(PG) $(CITED) retrieval --split dev`: Measures retrieval on the dev questions.
- `$(REPLAY) $(PG) $(CITED) retrieval --split test`: Runs `cited retrieval` on the test questions: it measures how often the right page is among the top five results.
- `$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v1`: Grades the answers to the dev questions with answer prompt v1 (`--prompt` picks the prompt version); a `--hand-grades` file also checks the judge against a person's grades.
- `$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v2 --hand-grades evals/hand_grades.jsonl`: Grades the answers to the dev questions with answer prompt v2 (`--prompt` picks the prompt version); a `--hand-grades` file also checks the judge against a person's grades.
- `$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v1`: Grades the answers to the test questions with answer prompt v1 (`--prompt` picks the prompt version); a `--hand-grades` file also checks the judge against a person's grades.
- `$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v2 --hand-grades evals/hand_grades.jsonl`: Grades the answers to the test questions with answer prompt v2 (`--prompt` picks the prompt version); a `--hand-grades` file also checks the judge against a person's grades.

```make
models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(GEN_MODEL)
	scripts/pull_model.sh $(EMBED_MODEL)
```

- `models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)`: Defines the target `models`. It has no prerequisites. The text after `##` (`download the pinned small open-weight models for recording and live-local runs (needs ollama)`) is the help text that `make help` prints.
- `scripts/pull_model.sh $(GEN_MODEL)`: Runs the download script for the answering model.
- `scripts/pull_model.sh $(EMBED_MODEL)`: Runs the download script for the embedding model.

```make
# Calls the local models for real and writes their vectors and answers into tests/fixtures (needs make models).
# Requests already in the files are replayed, so an interrupted recording resumes where it stopped.
LIVE := MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) \
  RECORD=on RECORDINGS_PATH=$(RECORDINGS)/qwen2.5-1.5b.jsonl EMBEDDINGS_PATH=$(EMBEDDINGS)/nomic-embed-text.jsonl
record: $(STAMP) ## record embeddings, answers and judge verdicts for dev and test, prompts v1 and v2, against the local models
	$(LIVE) $(CITED) evaluate --split dev --prompt v1 --dump out/answers-dev-v1.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split dev --prompt v2 --dump out/answers-dev-v2.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split test --prompt v1 --dump out/answers-test-v1.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split test --prompt v2 --dump out/answers-test-v2.jsonl --write-report
```

- `# Calls the local models for real and writes their vectors and answers into tests/fixtures (needs make models).`: A comment. make ignores everything after a `#`.
- `# Requests already in the files are replayed, so an interrupted recording resumes where it stopped.`: A comment. make ignores everything after a `#`.
- `LIVE := MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) RECORD=on RECORDINGS_PATH=$(RECORDINGS)/qwen2.5-1.5b.jsonl EMBEDDINGS_PATH=$(EMBEDDINGS)/nomic-embed-text.jsonl`: Sets `LIVE` (continued on the next line) to the NAME=value pairs that make the program call the local models for real and record what they say. The words of the form NAME=value in front of the program name set environment variables for that one command only: MODEL_PROVIDER (which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos); MODEL_NAME (the model id to ask for (for example `qwen2.5:0.5b`); each provider has a default); EMBEDDER_PROVIDER (which embedding model turns text into vectors: `recorded` replays saved vectors, `openai-compatible` calls a local server); EMBED_MODEL (the embedding model id (`nomic-embed-text` makes 768-number vectors)); RECORD (`on` makes every live answer also get written into the recordings file, so the next run can replay it); RECORDINGS_PATH (the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`)); EMBEDDINGS_PATH (the file or folder holding the recorded vectors).
- `record: $(STAMP) ## record embeddings, answers and judge verdicts for dev and test, prompts v1 and v2, against the local models`: Defines the target `record`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`record embeddings, answers and judge verdicts for dev and test, prompts v1 and v2, against the local models`) is the help text that `make help` prints.
- `$(LIVE) $(CITED) evaluate --split dev --prompt v1 --dump out/answers-dev-v1.jsonl --write-report`: Runs the dev questions with prompt v1 against the live local models and records them (`LIVE` supplies the variables), saving every answer to `out/answers-dev-v1.jsonl` (`--dump`) and writing the report (`--write-report`).
- `$(LIVE) $(CITED) evaluate --split dev --prompt v2 --dump out/answers-dev-v2.jsonl --write-report`: Runs the dev questions with prompt v2 against the live local models and records them (`LIVE` supplies the variables), saving every answer to `out/answers-dev-v2.jsonl` (`--dump`) and writing the report (`--write-report`).
- `$(LIVE) $(CITED) evaluate --split test --prompt v1 --dump out/answers-test-v1.jsonl --write-report`: Runs the test questions with prompt v1 against the live local models and records them (`LIVE` supplies the variables), saving every answer to `out/answers-test-v1.jsonl` (`--dump`) and writing the report (`--write-report`).
- `$(LIVE) $(CITED) evaluate --split test --prompt v2 --dump out/answers-test-v2.jsonl --write-report`: Runs the test questions with prompt v2 against the live local models and records them (`LIVE` supplies the variables), saving every answer to `out/answers-test-v2.jsonl` (`--dump`) and writing the report (`--write-report`).

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- `lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter`: Defines the target `lint`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`ruff check, ruff format check, mypy, import-linter`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check .`: Runs the ruff linter on every Python file under the current folder (`.`). A linter reads code without running it and reports mistakes and style problems. Exit code 0 means no problems.
- `$(VENV)/bin/ruff format --check .`: Asks ruff's formatter whether every file is already formatted the way it would format it. `--check` means "report, do not change anything"; a file that would change makes the command fail.
- `$(VENV)/bin/mypy`: Runs the mypy type checker. It needs no arguments because `pyproject.toml` lists the folders to check (`files = ["src", "tests"]`).
- `$(VENV)/bin/lint-imports`: Runs import-linter, which reads the contracts in `pyproject.toml` and fails if any module imports something it must not.

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `format: $(STAMP) ## apply ruff's formatting and safe fixes`: Defines the target `format`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`apply ruff's formatting and safe fixes`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check --fix .`: Runs the linter and lets it repair the problems that have a safe automatic fix (`--fix`).
- `$(VENV)/bin/ruff format .`: Rewrites every Python file into ruff's standard layout.

```make
# Offline and deterministic: unit and end-to-end tests on the in-memory index and the recorded models.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=cited_answers --cov-report=term
	$(PY) -m coverage report --include='src/cited_answers/domain/*,src/cited_answers/application/*' --fail-under=95
```

- `# Offline and deterministic: unit and end-to-end tests on the in-memory index and the recorded models.`: A comment. make ignores everything after a `#`.
- `test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)`: Defines the target `test`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`every offline test, with coverage (domain and application must stay at 95% or more)`) is the help text that `make help` prints.
- `$(PY) -m pytest --cov=cited_answers --cov-report=term`: Runs pytest as a module of the project's Python. `--cov=cited_answers` turns on coverage measurement for the package `cited_answers` and `--cov-report=term` prints the table in the terminal.
- `$(PY) -m coverage report --include='src/cited_answers/domain/*,src/cited_answers/application/*' --fail-under=95`: Prints the coverage table again, but only for the `domain` and `application` folders, and fails (non-zero exit code) if the total is under 95 percent. The quotes stop the shell from expanding the `*` itself.

```make
test-integration: $(STAMP) ## the Postgres adapter and the HTTP service against the pgvector container (make up first)
	$(PY) -m pytest tests/integration -m integration -o addopts="-ra --strict-markers"
```

- `test-integration: $(STAMP) ## the Postgres adapter and the HTTP service against the pgvector container (make up first)`: Defines the target `test-integration`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the Postgres adapter and the HTTP service against the pgvector container (make up first)`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/integration -m integration -o addopts="-ra --strict-markers"`: Runs only the tests in `tests/integration`, and only those marked `integration` (`-m` selects by marker). `-o addopts=...` replaces the default options from `pyproject.toml` for this run, so the marker filter that normally leaves out the integration tests is not applied.

```make
test-e2e: $(STAMP) ## the lesson's scenario on the recorded models
	$(PY) -m pytest tests/e2e -m e2e
```

- `test-e2e: $(STAMP) ## the lesson's scenario on the recorded models`: Defines the target `test-e2e`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the lesson's scenario on the recorded models`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/e2e -m e2e`: Runs only the tests in `tests/e2e`, and only those marked `e2e` (`-m` selects by marker).

```make
test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"
```

- `test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`: Defines the target `test-live`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"`: Runs only the live tests, which call a real model. The default options exclude them (`-m 'not live'`), so `-o addopts="..."` replaces the default options for this run.

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: Defines the target `audit`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`check the locked dependencies for known vulnerabilities`) is the help text that `make help` prints.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Checks every locked package against a database of known security problems. `--no-deps` means "do not work out dependencies again, trust the file"; `--disable-pip` means "do not run pip in a temporary environment"; `-r FILE` names the list to check.

```make
check: lint test ## format check, lint, types, import rules and every offline test
```

- `check: lint test ## format check, lint, types, import rules and every offline test`: Defines the target `check`. Its prerequisites, which make brings up to date before running the recipe: the target `lint`; the target `test`. The text after `##` (`format check, lint, types, import rules and every offline test`) is the help text that `make help` prints.

```make
down: ## stop Postgres and delete its data and the run output
	docker compose --profile api down -v
	rm -rf out
```

- `down: ## stop Postgres and delete its data and the run output`: Defines the target `down`. It has no prerequisites. The text after `##` (`stop Postgres and delete its data and the run output`) is the help text that `make help` prints.
- `docker compose --profile api down -v`: Stops and removes the containers of the project. `-v` also deletes the named volumes, so the database content goes too.
- `rm -rf out`: Deletes the `out` folder and everything in it. `-r` means "including folders", `-f` means "no error if it is missing".

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
```

- `clean: down`: Defines the target `clean`. Its prerequisites, which make brings up to date before running the recipe: the target `down`.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage`: Deletes the virtual environment and the cache files the tools wrote. Everything here can be built again.

## Try it yourself

1. List every target with its help text. This prints the `##` comments; nothing is run.

```bash
make help
```

What you should see (captured from this repository):

```text
ask	ask one question against the pgvector index with the recorded model (only recorded questions work offline)
audit	check the locked dependencies for known vulnerabilities
check	format check, lint, types, import rules and every offline test
db	apply sql/001_schema.sql and sql/002_seed.sql (safe to repeat)
docker-up	build and start the service in a container next to the database (needs a model server on the host)
down	stop Postgres and delete its data and the run output
evaluate	retrieval and answers graded apart on the frozen test set, judge checked against hand grades
format	apply ruff's formatting and safe fixes
help	list the targets
ingest	chunk the current pages, embed them (recorded vectors) and fill the pgvector index
install	create .venv from the lock file
lint	ruff check, ruff format check, mypy, import-linter
models	download the pinned small open-weight models for recording and live-local runs (needs ollama)
record	record embeddings, answers and judge verdicts for dev and test, prompts v1 and v2, against the local models
retrieval	hit rate at 5 for vectors, keywords and both fused, test questions
run	the lesson's scenario with recorded models: retrieval, then answers with prompt v1 (before) and v2 (after)
serve	run the HTTP service on :8080 against the pgvector index (live local model; make models first)
test	every offline test, with coverage (domain and application must stay at 95% or more)
test-integration	the Postgres adapter and the HTTP service against the pgvector container (make up first)
test-live	opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
tune-threshold	choose the refusal threshold on the 30 development questions only
up	start Postgres with pgvector, create the tables, load the pages and build the index
```

2. Dry run. `-n` prints the commands make *would* run for `make check`, without running any of them. Use it whenever you are not sure what a target does.

```bash
make -n check
```

What you should see (captured from this repository):

```text
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python -m pytest --cov=cited_answers --cov-report=term
.venv/bin/python -m coverage report --include='src/cited_answers/domain/*,src/cited_answers/application/*' --fail-under=95
```

3. Shows what the install rule would do. If the stamp file is already up to date make prints nothing, which proves the stamp logic works.

```bash
make -n install
```

What you should see (captured from this repository):

```text
make: Nothing to be done for `install'.
```

4. Shows which make you have. macOS ships GNU Make 3.81; the Makefile only uses features that exist in 3.81, so it works there and on newer versions.

```bash
make --version | head -1
```

What you should see (captured from this repository):

```text
GNU Make 3.81
```

## Mistakes people make

- **Spaces instead of a tab.** A recipe line indented with spaces gives `*** missing separator. Stop.` The repository's `.editorconfig` forces tabs for this file.
- **Forgetting `.PHONY`.** If someone creates a folder named `test`, `make test` would say "nothing to be done". Every action target is listed under `.PHONY`.
- **Writing `$` where `$$` is needed.** `$(wc -l < file)` is read by make as a make variable and comes out empty. Shell substitutions in recipes are written `$$(wc -l < file)`.
- **Expecting `cd` to carry over.** Each line is a fresh shell. This Makefile never uses `cd`; it passes paths instead.
- **Re-running slow setup every time.** Installing packages on every `make test` would be slow. The stamp file `.venv/.installed` makes the install run only when the lock file or `pyproject.toml` changed.
- **Hiding failures.** `-` in front of a command ignores its failure. It is used only where failure is expected and harmless, and the walkthrough above says where.

## Check yourself

1. What is the difference between `A = 1`, `A := 1` and `A ?= 1`?

   *Answer:* `=` is looked up each time it is used, `:=` is computed once when make reads the line, `?=` only sets the variable if nothing set it before.

2. Why does the Makefile write `$$(cat out/x.pid)` instead of `$(cat out/x.pid)`?

   *Answer:* make reads `$(...)` as its own syntax. `$$` becomes a single `$`, so the shell sees `$(cat out/x.pid)` and runs the command.

3. What does `touch $@` do at the end of the install rule, and why is it the last line?

   *Answer:* It creates or refreshes the stamp file, so make remembers the install finished. It is last so that a failure in an earlier line leaves no stamp and the install runs again next time.

4. What would happen if `test` were not listed under `.PHONY` and a folder named `test` existed?

   *Answer:* make would see a file called `test` with no newer prerequisites and would say "`test` is up to date" without running the recipe.

5. How can you see what `make down` would do without doing it?

   *Answer:* `make -n down` prints the commands without running them.

## Further reading

- GNU Make manual, https://www.gnu.org/software/make/manual/make.html (checked locally against GNU Make 3.81 with `make -n` and `make help`; the manual describes the newest release).
