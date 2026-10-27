# 0001. Hybrid retrieval by reciprocal rank fusion

Date: 2026-10-27. Status: accepted.

## Context

Vector search finds paraphrases and can miss exact codes; keyword search finds exact terms and misses paraphrases. Their scores are on different scales, so adding them needs calibration that a small corpus cannot support.

## Decision

Run both searches (20 results each), and combine the ranked lists with reciprocal rank fusion: a chunk scores `1 / (60 + rank)` in each list it appears in, the scores add, the top five are kept. The keyword side is BM25 in the process, with a tokenizer that splits on anything that is not a letter or digit so `PR-E2091` becomes `pr` and `e2091`. A whitespace tokenizer is kept in the code only so a test can show it failing on a bare code.

## Consequences

- No score calibration, and either list alone can put the right chunk in the top five.
- On this corpus fusion is not better than vector search alone (68/70 against 69/70 on answerable test questions). The report prints all three modes so the choice can be revisited with data.
- The fused score carries no information about quality, which is why the refusal threshold does not use it ([0003](0003-refusal-threshold-on-cosine-tuned-on-dev.md)).
