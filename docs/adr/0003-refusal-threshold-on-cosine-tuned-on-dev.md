# 0003. The refusal threshold is on cosine similarity and is tuned on dev only

Date: 2026-10-27. Status: accepted.

## Context

The lesson refuses before the model when the best fused score is below a threshold. A reciprocal-rank-fusion score depends on ranks only: the best chunk scores about the same for any question, good match or not. A threshold on it cannot separate "the pages cover this" from "nothing is close".

## Decision

The retrieval confidence is the highest cosine similarity between the question and any of the five fused chunks. `tune_threshold` takes the dev scores of answerable and unanswerable questions and returns the highest threshold that wrongly refuses at most 10% of the answerable ones. It runs once, on the 30 development questions, and the result is written to `evals/threshold.json` with the rates it cost on dev. The frozen test questions are measured with that number and never used to choose it.

## Consequences

- The cost is explicit: 9.1% of answerable dev questions refused by the threshold alone, and on the test set 11 of 90 (12%).
- A near-miss paraphrase scores above any workable threshold; that is the case the model's own refusal and the citation check are for, and in this run four such questions still got through.
- The rule is stated in `domain.answering.tune_threshold` and is tested with a small worked example.
