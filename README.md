# ai-cited-answers

A question-answering service over a help center: it indexes the current pages, retrieves chunks with keyword and vector search fused together, writes an answer in which every claim cites a chunk a reader can open, and says so with a fixed refusal when the pages do not hold the answer. Retrieval and answer quality are graded apart, with intervals.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-cited-answers`, "Cited answers over a help center" (`data-structure-explainer/src/content/tracks/ai/97-project-cited-answers.md` in the Plainround app) |
| **Planned hours** | 12 |
| **Level** | Intermediate |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions in [docs/adr](docs/adr) |
| **Technology notes** | [tech/README.md](tech/README.md), 42 notes that teach every technology used here from zero |

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13; CI uses 3.12) | the program and the tests |
| Docker with Compose v2 | 24 or newer (tested with 24.0.6) | Postgres 17 with pgvector, for `make up` and `make run` |
| GNU Make | 3.81 or newer (the one on macOS works) | every command below |
| Postgres image | `pgvector/pgvector:pg17` | pulled by Docker on first `make up` |
| Python packages | `fastapi` 0.162.0, `uvicorn` 0.54.0, `psycopg` 3.3.6, `pydantic` 2.14.1, `anthropic` 2.3.0, `httpx` 0.28.1 at run time; pytest, pytest-cov, ruff, mypy, import-linter, pip-audit for development. All pinned with hashes in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| ollama (optional) | any recent version, with `qwen2.5:1.5b` and `nomic-embed-text` | only for `make serve`, `make record` and `make test-live`; the recordings make it unnecessary for everything else |
| Anthropic API key (optional) | none needed for any default command | only for the opt-in Claude live test |

No cloud account and no secrets. The database password in `docker-compose.yml` is a local development value. A model key is read from your shell's `ANTHROPIC_API_KEY` and nowhere else.

## Setup, run, test, stop

```bash
make up                 # start Postgres with pgvector, create the tables (sql/), load the pages, build the index
make run                # retrieval on dev and test, then answers on dev and test with prompt v1 (before) and v2 (after)
make ask Q="Do you ship to Antarctica?"   # one question against the pgvector index (recorded: dataset questions only)
make retrieval          # hit rate at 5 for vectors, keywords and both fused (test questions)
make tune-threshold     # choose the refusal threshold from the 30 development questions only
make test               # every offline test with coverage (unit and end to end, in-memory index, no Docker needed)
make test-integration   # the Postgres adapter and the HTTP service against the pgvector container (make up first)
make lint               # ruff check, ruff format check, mypy --strict, import-linter
make audit              # known-vulnerability check of the locked dependencies
make down               # stop Postgres and delete its data
```

`make help` lists every target. `make run` replays recorded embeddings (`tests/fixtures/embeddings`, 218 vectors from `nomic-embed-text`) and recorded answers and judge verdicts (`tests/fixtures/recordings`, 302 calls of `qwen2.5:1.5b`), so it needs no model server, network or key and prints the same numbers every time. The index is the real thing: pgvector, queried with SQL.

To run against real models:

```bash
make models             # ollama pull qwen2.5:1.5b and nomic-embed-text (the weights stay in ollama's store, never in this repo)
make serve              # the HTTP service on :8080 on the pgvector index, with the local models
curl -s localhost:8080/ask -H 'content-type: application/json' -d '{"question": "How long do I have to return an item?"}'
curl -s localhost:8080/health
make docker-up          # the same service in a container next to the database (needs ollama on the host)
make record             # rewrite the fixtures from the local models (resumes if interrupted)
make test-live          # opt in: calls the local models, and Claude if ANTHROPIC_API_KEY is set; skipped by default
```

Variables are listed in `env.example` (copy it to `.env`). Logs are one logfmt line per event on standard error (`ts=... level=... logger=... msg=... key=value`). They carry ids, scores and counts; the HTTP service logs a hash and the length of a question, never its text, and never an answer.

## Results on the recorded run

Retrieval, hit at five (a chunk of the gold page is among the top five), 95% Wilson intervals:

| Question type | Mode | Dev | Test (frozen) |
| --- | --- | --- | --- |
| answerable | vector | 17/17 | 69/70 = 0.99 (0.92-1.00) |
| answerable | keyword | 13/17 | 66/70 = 0.94 (0.86-0.98) |
| answerable | fused | 15/17 | 68/70 = 0.97 (0.90-0.99) |
| exact code or number | vector | 5/5 | 20/20 = 1.00 (0.84-1.00) |
| exact code or number | keyword | 5/5 | 20/20 = 1.00 (0.84-1.00) |
| exact code or number | fused | 5/5 | 20/20 = 1.00 (0.84-1.00) |

Answers, with `qwen2.5:1.5b` generating and judging, refusal threshold 0.648 (tuned on dev):

| | dev, prompt v1 | dev, prompt v2 | test, prompt v1 | test, prompt v2 |
| --- | --- | --- | --- | --- |
| retrieval hit rate (answerable and exact) | 20/22 | 20/22 | 88/90 = 0.98 (0.92-0.99) | 88/90 = 0.98 (0.92-0.99) |
| answer correct (judge) | 0/22 | 14/22 = 0.64 (0.43-0.80) | 0/90 = 0.00 (0.00-0.04) | 57/90 = 0.63 (0.53-0.73) |
| unanswerable refused | 8/8 | 6/8 = 0.75 | 29/30 = 0.97 | 26/30 = 0.87 (0.70-0.95) |
| answerable wrongly refused | 22/22 | 4/22 = 0.18 | 90/90 | 28/90 = 0.31 (0.22-0.41) |
| misses: retrieval / generation | 2 / 20 | 2 / 6 | 2 / 88 | 1 / 32 |

What this says, in plain words:

- **Search is not the problem; the small model is.** The right page is among the top five for 98% of the gradable test questions. The answers go wrong after that: with prompt v1 the model wrote correct sentences with no citations, the citation check replaced every one with the refusal, and 0 of 90 answers survived. That is the check doing its job, and it is the larger group of misses (88 against 2), so it was fixed first.
- **Prompt v2 is the fix**: the rule moved to the first lines and one worked example with real ids from the corpus. 57 of 90 are now correct. 32 gradable test questions are still generation misses (a refusal where the page answers, a wrong citation, a claim the page does not make).
- **Not every unanswerable question was refused.** 26 of 30 on the frozen test set and 6 of 8 on dev. The four test slips are near-misses the small model answers confidently from an unrelated page (`q-t103` "physical gift cards", `q-t106` "how long do you keep my order data", `q-t107` "refund on a pre-order after it shipped", `q-t108` "Sunday delivery"). Of the 30, the threshold refused 20 before the model, the model refused 4, and the citation check replaced 2. One slip fails the lesson's bar; this build does not meet it, and the next lever is a larger model or a second-pass verifier, not a lower number.
- **The threshold has a price**, stated up front: tuned on dev to wrongly refuse at most 10% of answerable questions (it refuses 9.1% there); on the test set the same threshold wrongly refuses 11 of 90 answerable questions (12%) before the model is called.
- **The judge** (`qwen2.5:1.5b`, prompt `judge/v1`) agrees with 30 hand grades on 29 (97%; 21 of 22 on dev and 8 of 8 on the first eight gradable test questions). It called `q-d009` correct when the answer said the opposite of the page ("You pay to send something back"). The hand grades were written by the author of this build, by reading each answer against its fact; re-grade ten of them before trusting the 97%.

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | Every chunk carries page id, heading path, updated date and status; no chunk spans two pages; a search for the old return window returns no retired chunk. | `make test` (`tests/e2e`), `make test-integration`, `sql/003_queries.sql` | 57 current pages become 68 chunks, each with the four fields, ids of the form `<page>:<n>`, none over 300 tokens. The three retired pages (`p-return-fee-old`, `p-return-window-old`, `p-ship-costs-old`) are left out and logged by id. In Postgres the `chunks` table has `CHECK (status = 'current')`, so a retired chunk cannot exist, and a test shows the database refusing one. A question for the return window finds only `p-return-window` in all three modes. |
| 2 | The report shows hit rate at five for answerable and exact-code questions, each with its interval. | `make run` (`cited retrieval`) | The table above, printed with Wilson intervals; the intervals are wide for the 17 and 20 exact and dev questions and the report says so by printing them. |
| 3 | Hit rate for vectors alone and for the fused lists, side by side, per type with intervals, and whether the exact-code gap closed. | `make run` | Side by side above. There was **no gap to close** in this corpus: vectors already find all 20 exact-code and number questions (20/20, same as fused). Fusion did not help overall: on answerable questions it is slightly below vectors alone (68/70 against 69/70) because the keyword list sometimes pushes a wrong chunk into the top five. The lesson's tokenizer finding is still reproduced: a keyword index that splits on spaces cannot find the bare code in "What's E2091 about?" (it returns nothing); this build's tokenizer splits `PR-E2091` into `pr` and `e2091` and finds it (`tests/e2e`). |
| 4 | A planted citation to a chunk that was not retrieved fails the check, and every answer in the run cites at least one retrieved chunk or is the refusal message. | `make test` | `test_step_4_a_planted_citation...` sends an answer citing `[p-gift-cards:0]` for a return-window question and gets the refusal with reason `citation_not_retrieved`; another test walks all 120 test results and asserts each answer either cites only retrieved chunk ids or is exactly the refusal message. The prompt shows the format with a real id (`[p-return-window:0]`), never a placeholder. |
| 5 | On the development set no unanswerable question gets an answer, and the threshold and the false-refusal rate it costs on answerable questions are written down. | `make tune-threshold`, `make run` | **Not met.** Threshold 0.648 and its cost are written down (`evals/threshold.json`: false refusal 9.1% by threshold alone; refuses 6 of the 8 unanswerable dev questions before the model). With prompt v2 two dev questions still got an answer (`q-d024` "add an item to an order I already placed", `q-d029` "track a pre-order before it ships"), both near-misses of a real page. |
| 6 | Retrieval hit rate and answer correctness as two numbers with intervals, the judge's agreement with hand grades, and all unanswerable questions refused. | `make run` | The first two and the agreement (97%) are in the report. **All refused: not met**, 26 of 30 (see above). |
| 7 | A two-row table (retrieval misses, generation misses) before and after the fix. | `make run` | Test: retrieval 2 to 1, generation 88 to 32 (dev 2/20 to 2/6). The whole frozen set was rerun after the fix, not only the cases that were wrong. |
| 8 | The Java version's hit rate and correctness fall inside the Python intervals, and every unanswerable question is refused there too. | not built | See "Stretch goals and what is not built". |

## Stretch goals and what is not built

| Item (from the lesson) | Built? |
| --- | --- |
| The Java version on Spring AI with its `VectorStore` and `ChatClient` (the lesson's "build it in Python and in Java" and step 8) | **No.** The Python service is the whole build. The pages, questions, chunking rules, fusion constant and threshold are plain files and numbers a Java port can reuse. Step 8 compares two clients on the same live models; no model key is available to this build and the Spring AI version the track pins is not downloaded here. |
| A cross-encoder reranker over the top 20 | No. |
| Access scopes on chunks (staff-only pages) with a test that a customer never retrieves one | No. |
| Edit one page, re-index only that page, show the next answer cites the new version | No. `cited ingest` rebuilds the whole index in one transaction (68 chunks, a few seconds); a per-page upsert is a small change to `ChunkStore`. |

## What is simplified for teaching

Only what the lesson scopes out, plus where this build differs from the lesson's text:

- The lesson used about 16 pages in its measured runs; this build has all 60. Recordings are from two small local models, so the numbers are theirs.
- **The refusal threshold applies to cosine similarity, not to the fused score.** Reciprocal rank fusion scores depend only on ranks, so the best fused score is nearly the same for every question and cannot tell a good match from a poor one. The threshold uses the highest cosine similarity among the fused top five chunks, which is the number the lesson's expected output prints.
- Chunk ids are `<page id>:<n>` (the lesson's example used the page id). A citation that names only a page is accepted when exactly one chunk of that page was retrieved.
- The judge and the generator are the same small model. A larger judge would be a stronger check; the hand grades exist to show how much to trust this one.
- The hand grades are the author's, not a second person's.
- No retries on the HTTP service beyond the model client's backoff; no authentication or rate limiting on `/ask`.

## Project structure

```text
src/cited_answers/
  domain/            pages, chunking (heading split, 300-token cap), BM25 and fusion, citation check, refusal rules,
                     threshold tuning, evaluation maths (Wilson, hit at k, stages), llm value objects, named errors.
                     Depends on nothing outside the standard library.
  application/       ingest, hybrid retrieval, the answer service (threshold, model, citations), the judge, the evaluator
                     and the ports (ChatModel, Embedder, ChunkStore, PageSource, QuestionSource, PromptStore, Clock).
                     Depends on domain only.
  infrastructure/    pgvector and in-memory chunk stores, recorded/recording/local/Claude model clients, embedding clients,
                     retry, prompt/page/question files, validated settings, logfmt logging, signals.
                     Depends on application and domain.
  interfaces/        the `cited` command (ingest, ask, serve, retrieval, tune-threshold, evaluate), the FastAPI app
                     (/ask, /health), the uvicorn entry point and the report text.
                     Depends on everything below; nothing depends on it.
tests/
  unit/              domain, application (scripted model, hashing embedder), infrastructure (mock HTTP transports), CLI, HTTP.
  e2e/               the lesson's scenario on recorded embeddings and answers, reproducing the committed reports.
  integration/       the Postgres adapter and the service against the pgvector container.
  live/              opt-in tests against real models (make test-live).
  fixtures/          embeddings/ (218 vectors) and recordings/ (302 model calls), about 1 MB together.
data/                pages/ (60 markdown files), questions/ (dev.jsonl 30, test.jsonl 120).
prompts/             answer/v1.md, v2.md, judge/v1.md and CHANGELOG.md.
evals/               threshold.json (tuned on dev), hand_grades.jsonl (30), reports/ (four answer reports).
sql/                 001_schema.sql (DDL), 002_seed.sql (the pages, generated), 003_queries.sql (the checks).
scripts/             make_pages.py, make_questions.py, make_seed_sql.py (regenerate the data), pull_model.sh.
docs/adr/            decision records.
tech/                one note per technology, from zero (start at tech/README.md).
docker-compose.yml   Postgres + pgvector, and the service under the `api` profile.   Dockerfile  the service image.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter. A second contract forbids `domain` and `application` from importing `anthropic`, `httpx`, `openai`, `psycopg`, `fastapi` or `uvicorn`.

## Troubleshooting

- **`RecordingMissing: no recorded embedding for a text ...`:** you asked something that was never recorded (an ad-hoc question, with the recorded models). Use a question from `data/questions`, or run `make models` and `make serve` for live models.
- **`connection refused` on port 55432:** `make up` has not run, or Docker is stopped. `make down && make up` starts clean.
- **`network ... is ambiguous (2 matches found on name)`:** a half-finished `docker compose up` left two networks; `docker network rm` both ids shown by `docker network ls --filter name=ai-cited-answers`.
- **`container ... is unhealthy` or `the database system is in recovery mode` during `make up`:** the first start of a fresh volume runs `initdb`, which takes a few minutes when Docker is short of memory or disk (several dozen containers on an 8 GB machine will do it). The health check waits about five minutes and `make db` waits until the database answers a query; if Docker itself is unresponsive, restart it and run `make down && make up`.
- **Port 55432 or 8080 is in use:** change the port mapping in `docker-compose.yml` and `DATABASE_URL` or `HTTP_PORT`.

## Verification notes

Verified on 2026-10-27 with `make up`, `make run`, `make test`, `make lint`, `make audit` and `make down`, in the repository and again in a fresh clone.

- **Timing figures** (latencies, durations, the cost-versus-latency ratios) were recorded or measured on a machine whose load average was between 35 and 180, so they support ratios, not service levels. Rerun for clean figures: `make record`.
- **Docker:** the Postgres container, the image build and the `make docker-up` service all completed on 2026-10-27, before the Docker engine's disk became read-only. Nothing is pending. After a Docker Desktop restart, `make down && make up && make run` repeats the check; the first start of a fresh volume can take minutes on a busy machine.

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
