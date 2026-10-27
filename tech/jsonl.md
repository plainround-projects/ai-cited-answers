# JSON Lines (JSONL)

## What it is

**JSON Lines** is JSON with one rule added: a file holds **one complete JSON value per line** (almost always an object), with no commas between lines and no enclosing brackets. A file of 450 records is simply 450 lines. A reader can process it one line at a time without loading the whole file.

## Why this repository uses it

Two properties matter here. First, **appending is safe**: adding a record is writing one line at the end, so a recording that is interrupted keeps every complete line, and a restarted recording resumes from there. Second, **diffs and tools work line by line**: `wc -l` counts records and `grep` finds one. The recordings (answers saved from a real local model so that tests and demos can replay them) are JSON Lines for exactly this reason.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `data/questions/dev.jsonl` | records, one per line |
| `data/questions/test.jsonl` | records, one per line |
| `evals/hand_grades.jsonl` | records, one per line |
| `tests/fixtures/embeddings/nomic-embed-text.jsonl` | records, one per line |
| `tests/fixtures/recordings/qwen2.5-1.5b.jsonl` | records, one per line |

## How it works underneath

To read a JSON Lines file, split the text on newline characters and parse each non-empty line with an ordinary JSON parser. To write one, serialize each record with no line breaks inside (JSON escapes a newline inside text as `\n`, so a record never spans lines) and add one newline. If a process dies in the middle of writing a line, the last line is incomplete; a careful reader skips or cuts it.

A **recording** here is keyed by a SHA-256 fingerprint of the request (model, messages, settings). Replaying means: compute the fingerprint of the new request, look it up, and return the saved answer. The same request therefore always gets the same answer, offline, which is what makes the test numbers repeatable.

## Walkthrough of this repository's use

### Every JSON Lines file in this repository

| File | Shape | Keys (first ones) |
| --- | --- | --- |
| `data/questions/dev.jsonl` | one JSON object per line, 30 lines | `id`, `type`, `question`, `gold_page`, `fact`, `near_miss` |
| `data/questions/test.jsonl` | one JSON object per line, 120 lines | `id`, `type`, `question`, `gold_page`, `fact`, `near_miss` |
| `evals/hand_grades.jsonl` | one JSON object per line, 30 lines | `question_id`, `correct`, `grader`, `prompt` |
| `tests/fixtures/embeddings/nomic-embed-text.jsonl` | one JSON object per line, 218 lines | `key`, `model`, `vector` |
| `tests/fixtures/recordings/qwen2.5-1.5b.jsonl` | one JSON object per line, 302 lines | `key`, `tag`, `recorded_with`, `response` |

### The files, key by key

`data/questions/dev.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "id": "q-d001",
  "type": "answerable",
  "question": "How do I place an order without creating an account?",
  "gold_page": "p-order-place",
  "fact": "you can check out as a guest and create an account afterwards",
  "near_miss": false
}
```

What each key means:

- `id` (text): a short unique id for this record.
- `type` (text): `answerable` or `unanswerable`.
- `question` (text): the customer's question.
- `gold_page` (text): the id of the help page that holds the answer.
- `fact` (text): the short fact the answer must contain.
- `near_miss` (true or false): true if the question is built to sound like a page that does not answer it.

`evals/hand_grades.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "question_id": "q-d001",
  "correct": true,
  "grader": "author, by reading the answer against the fact",
  "prompt": "answer-v2"
}
```

What each key means:

- `question_id` (text): which question this grade is for.
- `correct` (true or false): whether a person judged the answer correct (or, in a result, whether the answer matched).
- `grader` (text): who graded it.
- `prompt` (text): which prompt version this configuration (or grade) used.

`tests/fixtures/embeddings/nomic-embed-text.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "key": "3d185d0da1593e3603cad3d98970e19b01214d8988e640807920f67da37dea7d",
  "model": "nomic-embed-text",
  "vector": "GfIlPIpQujydXjS+uMpku27Swz0tZ6u9rKsHPX3TLz2fqu08L4+LvRRWub3uyxw9usT1PK..."
}
```

What each key means:

- `key` (text): a fingerprint (SHA-256) of the request, used to look the answer up.
- `model` (text): the model id (a name the provider or the local server knows).
- `vector` (text): the embedding, as base64 text of 32-bit floating-point numbers.

`tests/fixtures/recordings/qwen2.5-1.5b.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "key": "23a6eed7818f385e5f63bd59f095a2a78595caa78aaf05f4deb0f2458c431bf7",
  "tag": "q-d001|answer-v1",
  "recorded_with": {
    "provider": "openai-compatible",
    "requested_model": "qwen2.5:1.5b",
    "model": "qwen2.5:1.5b"
  },
  "response": {
    "text": "You can check out without an account. Create one afterwards from the c...",
    "stop_reason": "stop",
    "usage": {
      "input_tokens": 481,
      "output_tokens": 21
    },
    "latency_seconds": 3.5292,
    "model": "qwen2.5:1.5b",
    "tool_calls": []
  }
}
```

What each key means:

- `key` (text): a fingerprint (SHA-256) of the request, used to look the answer up.
- `tag` (text): an id for the call, used to find the same call in a recording.
- `recorded_with` (object): which provider and model produced the answer.
- `recorded_with.provider` (text): the kind of provider (`openai-compatible` for a local server).
- `recorded_with.requested_model` (text): the model name the request asked for.
- `recorded_with.model` (text): the model id (a name the provider or the local server knows).
- `response` (object): the recorded answer.
- `response.text` (text): the text of the record.
- `response.stop_reason` (text): why the model stopped (`stop`, `length`, ...).
- `response.usage` (object): the token counts the provider reported.
- `response.usage.input_tokens` (whole number): tokens sent to the model.
- `response.usage.output_tokens` (whole number): tokens the model produced.
- `response.latency_seconds` (decimal number): how long the call took.
- `response.model` (text): the model id (a name the provider or the local server knows).
- `response.tool_calls` (list): how many tool calls were made.

### Embedding vectors

A vector is a list of numbers (768 of them for `nomic-embed-text`). Written as JSON numbers it would take about 20 characters each. The files that hold vectors store them as **base64 text of 32-bit floats** (4 bytes per number, 3072 bytes per vector, then base64 encoded to plain letters and digits). Reading one back is `struct.unpack` of the decoded bytes. This keeps those files smaller and exact (a float32 round-trips without loss).

## Try it yourself

1. A JSON Lines file's record count is its line count.

```bash
wc -l data/questions/dev.jsonl
```

What you should see (captured from this repository):

```text
      30 data/questions/dev.jsonl
```

2. The first record, as stored: one line.

```bash
head -c 300 data/questions/dev.jsonl
```

What you should see (captured from this repository):

```text
{"id": "q-d001", "type": "answerable", "question": "How do I place an order without creating an account?", "gold_page": "p-order-place", "fact": "you can check out as a guest and create an account afterwards", "near_miss": false}
{"id": "q-d002", "type": "answerable", "question": "The address is loc
```

3. Parse every line and list the keys of the first record.

```bash
.venv/bin/python -c "import json; rows = [json.loads(x) for x in open('data/questions/dev.jsonl') if x.strip()]; print(len(rows), sorted(rows[0]))"
```

What you should see (captured from this repository):

```text
30 ['fact', 'gold_page', 'id', 'near_miss', 'question', 'type']
```

4. A well-formed file ends with a newline.

```bash
tail -c 1 data/questions/dev.jsonl | od -c | head -1
```

What you should see (captured from this repository):

```text
0000000   \n                                                            
```

## Mistakes people make

- **Wrapping the records in `[ ]` or adding commas.** That is plain JSON, not JSON Lines.
- **A record with a real line break inside.** JSON escapes it as `\n`; a writer must use a JSON serializer, never hand-built text.
- **Assuming the last line is complete.** After a crash it may be cut off.
- **Re-sorting a recording.** Order does not matter to the replay, but a changed order makes a diff noisy.
- **Loading a huge file at once.** Read it line by line.

## Check yourself

1. What distinguishes JSON Lines from JSON?

   *Answer:* One complete JSON value per line; no commas or outer brackets.

2. Why does append-only suit recordings?

   *Answer:* An interrupted run keeps every finished line and can resume.

3. How is a request matched to its recorded answer?

   *Answer:* By a SHA-256 fingerprint of the request.

4. How are embedding vectors stored here?

   *Answer:* As base64 text of 32-bit floats.

5. How do you count the records?

   *Answer:* Count the lines (`wc -l`).

## Further reading

- JSON Lines, https://jsonlines.org/ (the format is a convention on top of RFC 8259 JSON; examples were run locally).
