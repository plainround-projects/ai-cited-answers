# Prompt changelog

Each prompt lives in `prompts/<name>/<version>.md` with a `version:` line in its front matter. A prompt is never edited after it has been evaluated; a change is a new version and a line here.

## answer

- **v1** (2026-10-27): first version. Shows the citation format with a real chunk id from the corpus (`[p-return-window:0]`), never a placeholder, because a small model copies a placeholder literally. Tells the model to refuse with one exact sentence when the passages do not answer.

- **v2** (2026-10-27): the fix for the larger group of misses. With v1 the small model wrote correct sentences and no citations, so the citation check replaced every answer with the refusal (0 of 22 dev answers and 0 of 90 test answers survived). v2 puts the rule in the first lines ("every sentence ends with the id of its passage; an answer without an id is wrong") and adds one worked example with real ids from the corpus.

- **v2** (2026-10-27): the fix for the larger group of misses. With v1 the small model wrote correct sentences and no citations, so the citation check replaced every answer with the refusal (0 of 22 dev answers and 0 of 90 test answers survived). v2 puts the rule in the first lines ("every sentence ends with the id of its passage; an answer without an id is wrong") and adds one worked example with real ids from the corpus.

## judge

- **v1** (2026-10-27): one-word verdict, `correct` or `incorrect`, given the question, the fact the answer must state and the answer. Checked against 30 hand grades; see `evals/hand_grades.jsonl` and the README.
