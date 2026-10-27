# 0006. Recorded models, and a judge checked against hand grades

Date: 2026-10-27. Status: accepted.

## Context

Tests and reports must be repeatable offline, and no model key is available while the repository is built. A language-model judge is an unverified assumption until a human has graded some of the same answers.

## Decision

Embeddings (`nomic-embed-text`, 218 vectors) and answers and verdicts (`qwen2.5:1.5b`, 302 calls) are recorded through ollama's OpenAI-compatible endpoints and replayed by recorded adapters keyed by request content. The Claude adapter is the second real adapter and is covered by mock-transport tests and an opt-in live test. The judge's prompt is checked against 30 hand grades (all 22 gradable dev answers and the first 8 gradable test answers) written by reading each answer against its fact; the agreement is a reported number (29 of 30).

## Consequences

- `make run` prints the same numbers on any machine, and a test replays each committed report.
- A different model needs `make record` and produces different numbers; that is the intended use of the harness.
- The hand grades are one person's. A second grader would make the agreement figure more trustworthy.
