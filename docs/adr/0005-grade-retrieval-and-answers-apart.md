# 0005. Grade retrieval and answers apart, and split every miss by stage

Date: 2026-10-27. Status: accepted.

## Context

One accuracy number cannot say whether search never found the page or the model misused a page it had. The fixes are different, and effort should go to the larger group.

## Decision

The evaluator reports hit rate at five per question type and retrieval mode, answer correctness for the answerable and exact questions, and refusals for the unanswerable ones, each with a 95% Wilson interval. Every wrong answer goes to exactly one of two buckets: retrieval miss (the gold page was not among the five) or generation miss (it was, and the answer is still wrong or refused). The runs before and after a fix are reported side by side on the whole frozen set, not only on the cases that were wrong.

## Consequences

- Prompt v1 gave 2 retrieval misses and 88 generation misses; the fix targeted the larger group and left 1 and 32.
- Refusal is a binary check on the unanswerable questions and is never folded into correctness.
- The test set is run once per prompt version; tuning stays on dev.
