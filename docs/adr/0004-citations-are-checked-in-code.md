# 0004. Citations are checked in code against what was retrieved

Date: 2026-10-27. Status: accepted.

## Context

A prompt asks a model to cite; it does not make it cite, and it does not make the citation real. A reader who clicks a citation to a chunk that was never part of the answer's evidence has been misled.

## Decision

After the model answers, `check_citations` requires at least one `[id]` and requires every id to be one of the chunks retrieved for this request (not any chunk in the index). A citation that names a page instead of a chunk is read as that page's chunk when exactly one chunk of the page was retrieved. An answer that fails is replaced by the fixed refusal; the failure reason (`no_citation`, `citation_not_retrieved`) is logged and kept for the report; the raw text is kept for debugging but never shown. The prompts show the format with a real id from the corpus.

## Consequences

- Every answer a reader sees either cites retrieved chunks or is the refusal message, and a test walks all 120 test results to prove it.
- A small model that writes correct sentences without citing produces refusals, not unsourced answers. Prompt v1 showed the size of the effect: all 90 answerable test questions refused.
- The check cannot tell whether a cited chunk supports the sentence; the judge measures that separately.
