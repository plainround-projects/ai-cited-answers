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

-include .env
export

# The service and the evaluation use the pgvector index; the unit and end-to-end tests use the in-memory one.
PG := INDEX_BACKEND=pgvector
REPLAY := MODEL_PROVIDER=recorded EMBEDDER_PROVIDER=recorded RECORDINGS_PATH=$(RECORDINGS) EMBEDDINGS_PATH=$(EMBEDDINGS)

.PHONY: help install up db ingest ask serve docker-up run retrieval tune-threshold evaluate models record lint format \
        test test-integration test-e2e test-live audit check down clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the lock file

up: $(STAMP) ## start Postgres with pgvector, create the tables, load the pages and build the index
	docker compose up -d --wait db
	$(MAKE) --no-print-directory db
	$(MAKE) --no-print-directory ingest

db: ## apply sql/001_schema.sql and sql/002_seed.sql (safe to repeat)
	@for i in $$(seq 1 180); do docker compose exec -T db psql -U cited -d cited -qc 'select 1' >/dev/null 2>&1 && break || sleep 1; done
	$(PSQL) < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql

ingest: $(STAMP) ## chunk the current pages, embed them (recorded vectors) and fill the pgvector index
	$(REPLAY) $(PG) $(CITED) ingest

# make ask Q="What is your return window?"
Q ?= How many days do I have to return an item?
ask: $(STAMP) ## ask one question against the pgvector index with the recorded model (only recorded questions work offline)
	$(REPLAY) $(PG) $(CITED) ask "$(Q)"

serve: $(STAMP) ## run the HTTP service on :8080 against the pgvector index (live local model; make models first)
	$(PG) MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible $(CITED) serve

docker-up: ## build and start the service in a container next to the database (needs a model server on the host)
	docker compose --profile api up -d --build --wait

retrieval: $(STAMP) ## hit rate at 5 for vectors, keywords and both fused, test questions
	$(REPLAY) $(PG) $(CITED) retrieval --split test

tune-threshold: $(STAMP) ## choose the refusal threshold on the 30 development questions only
	$(REPLAY) $(PG) $(CITED) tune-threshold

evaluate: $(STAMP) ## retrieval and answers graded apart on the frozen test set, judge checked against hand grades
	$(REPLAY) $(PG) $(CITED) evaluate --split test --hand-grades evals/hand_grades.jsonl

run: up ## the lesson's scenario with recorded models: retrieval, then answers with prompt v1 (before) and v2 (after)
	$(REPLAY) $(PG) $(CITED) retrieval --split dev
	$(REPLAY) $(PG) $(CITED) retrieval --split test
	$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v1
	$(REPLAY) $(PG) $(CITED) evaluate --split dev --prompt v2 --hand-grades evals/hand_grades.jsonl
	$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v1
	$(REPLAY) $(PG) $(CITED) evaluate --split test --prompt v2 --hand-grades evals/hand_grades.jsonl

models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(GEN_MODEL)
	scripts/pull_model.sh $(EMBED_MODEL)

# Calls the local models for real and writes their vectors and answers into tests/fixtures (needs make models).
# Requests already in the files are replayed, so an interrupted recording resumes where it stopped.
LIVE := MODEL_PROVIDER=openai-compatible MODEL_NAME=$(GEN_MODEL) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) \
  RECORD=on RECORDINGS_PATH=$(RECORDINGS)/qwen2.5-1.5b.jsonl EMBEDDINGS_PATH=$(EMBEDDINGS)/nomic-embed-text.jsonl
record: $(STAMP) ## record embeddings, answers and judge verdicts for dev and test, prompts v1 and v2, against the local models
	$(LIVE) $(CITED) evaluate --split dev --prompt v1 --dump out/answers-dev-v1.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split dev --prompt v2 --dump out/answers-dev-v2.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split test --prompt v1 --dump out/answers-test-v1.jsonl --write-report
	$(LIVE) $(CITED) evaluate --split test --prompt v2 --dump out/answers-test-v2.jsonl --write-report

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

# Offline and deterministic: unit and end-to-end tests on the in-memory index and the recorded models.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=cited_answers --cov-report=term
	$(PY) -m coverage report --include='src/cited_answers/domain/*,src/cited_answers/application/*' --fail-under=95

test-integration: $(STAMP) ## the Postgres adapter and the HTTP service against the pgvector container (make up first)
	$(PY) -m pytest tests/integration -m integration -o addopts="-ra --strict-markers"

test-e2e: $(STAMP) ## the lesson's scenario on the recorded models
	$(PY) -m pytest tests/e2e -m e2e

test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

check: lint test ## format check, lint, types, import rules and every offline test

down: ## stop Postgres and delete its data and the run output
	docker compose --profile api down -v
	rm -rf out

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
