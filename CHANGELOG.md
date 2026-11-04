# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Drawn architecture and flow figures in `docs/diagrams/`, light and dark, shown in the README.

### Fixed

- ARCHITECTURE.md and README now match the code where they disagreed (see the drawn figures).

## [0.1.0] - 2026-10-27

### Added

- A help center of 60 pages (57 current, three retired pages that contradict a current one, ten pages that each explain one error code), each with a title, an updated date and a status.
- Ingestion: split on headings into chunks of at most about 300 tokens carrying page id, heading path, updated date and status; retired pages are left out of the index and logged by id.
- Retrieval by vector (Postgres with pgvector, or in memory), by keyword (BM25 with a hyphen-aware tokenizer) and by both fused with reciprocal rank fusion.
- Cited answers: every answer cites retrieved chunks or is replaced by the fixed refusal; a refusal before the model when the best similarity is below a threshold tuned on the development questions only.
- Evaluation: hit rate at five per question type and retrieval mode with Wilson intervals; answer correctness by a judge checked against 30 hand grades; refusals; misses split by stage, before and after the fix.
- An HTTP service (`POST /ask`, `GET /health`) with graceful shutdown, a Dockerfile and `docker-compose.yml` with pgvector.
- 150 evaluation questions (30 development, 120 frozen test), two answer prompts and a judge prompt with a changelog, recorded embeddings of `nomic-embed-text` and recorded answers of `qwen2.5:1.5b`.
- Model port with recorded, local and Claude adapters; layered package with the dependency rule enforced by import-linter; unit, end-to-end, integration and opt-in live tests; ruff, mypy, hash-pinned locks and a CI workflow with a pgvector service.
