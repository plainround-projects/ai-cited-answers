# Python source, the unit tests (part 1 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 8 files with 101 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/application/test_retrieve_answer_evaluate.py` | 191 non-blank lines |
| `tests/unit/domain/test_answering_and_evaluation.py` | 116 non-blank lines |
| `tests/unit/domain/test_llm.py` | 22 non-blank lines |
| `tests/unit/domain/test_pages_chunking_retrieval.py` | 108 non-blank lines |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 124 non-blank lines |
| `tests/unit/infrastructure/test_embeddings_stores_files.py` | 169 non-blank lines |
| `tests/unit/infrastructure/test_openai_compatible.py` | 102 non-blank lines |
| `tests/unit/infrastructure/test_recording.py` | 45 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/application/test_retrieve_answer_evaluate.py`

191 non-blank lines; it defines `built`, `test_ingest_indexes_current_pages_only_and_names_the_retired_ones`, `test_ingest_logs_each_skipped_page`, `test_a_search_for_the_old_return_window_returns_no_retired_chunk`, `test_embedding_is_done_in_batches`, `test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find`, `test_best_similarity_is_the_highest_cosine_among_the_returned_chunks`, `good_answer`, `service`, `test_a_cited_answer_is_returned_with_its_citations_and_the_passages_in_the_prompt`, `test_below_the_threshold_the_model_is_never_called`, `test_the_model_may_refuse_too`, ....

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 1 to 14:

```python
import logging

import pytest

from cited_answers.application.answer import AnswerService, format_context
from cited_answers.application.evaluate import evaluate_answers, evaluate_retrieval, summarize
from cited_answers.application.judge import Judge
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.application.threshold import choose_threshold, dev_scores
from cited_answers.domain.answering import REFUSAL_MESSAGE, Reason, Status
from cited_answers.domain.evaluation import Question, QuestionType, Stage
from cited_answers.domain.prompts import Prompt
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from tests.conftest import PAGES, PROMPT, HashingEmbedder, MemoryPages, ScriptedModel
```

- Makes the module `logging` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `AnswerService` (Retrieve, refuse early below the threshold, ask the model, check the citations.), `format_context` (The passages as the model sees them, each under its id in square brackets.) from the project module `cited_answers.application.answer`.
- Brings in `evaluate_answers` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.), `evaluate_retrieval` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.), `summarize` (Fold per-question results into the report's numbers.) from the project module `cited_answers.application.evaluate`.
- Brings in `Judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.) from the project module `cited_answers.application.judge`.
- Brings in `HybridRetriever` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.), `Mode` (How to find chunks.), `ingest` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) from the project module `cited_answers.application.retrieve`.
- Brings in `choose_threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.), `dev_scores` (Best retrieval score of each answerable (gold-page) question and of each unanswerable one.) from the project module `cited_answers.application.threshold`.
- Brings in `REFUSAL_MESSAGE`, `Reason` (Why a question was refused (or `none` when it was answered).), `Status` (What the reader gets: a cited answer or the fixed refusal.) from the project module `cited_answers.domain.answering`.
- Brings in `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.), `Stage` (Where a wrong answer went wrong.) from the project module `cited_answers.domain.evaluation`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `cited_answers.domain.prompts`.
- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.
- Brings in `PAGES`, `PROMPT`, `HashingEmbedder` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.), `MemoryPages` (A page source over a list.), `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 17 to 28:

```python
@pytest.fixture
def built():
    embedder = HashingEmbedder()
    store = InMemoryChunkStore()
    report = ingest(MemoryPages(PAGES), embedder, store)
    return report, HybridRetriever(store, embedder), embedder


def test_ingest_indexes_current_pages_only_and_names_the_retired_ones(built, caplog):
    report, retriever, _ = built
    assert (report.pages_indexed, report.chunks) == (4, 4)
    assert report.skipped_retired == ("p-return-window-old",)
```

- Defines the function `built`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Stores the result of calling `HashingEmbedder` under the name `embedder`.
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
- Stores the result of calling `InMemoryChunkStore` under the name `store`.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Stores the result of calling `ingest` under the name `report`.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `MemoryPages` from the project's `tests.conftest` (A page source over a list.).
- Ends the function and gives back a tuple of 3 item(s) to the caller.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Defines the function `test_ingest_indexes_current_pages_only_and_names_the_retired_ones`.
- Its parameters:
    - `built`.
    - `caplog`.
- Stores the value named `built` under the name `(report, retriever, _)`.
- Checks that `(report.pages_indexed, report.chunks) == (4, 4)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.skipped_retired == ('p-return-window-old',)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 29 to 42:

```python
    assert retriever.chunk_count == 4


def test_ingest_logs_each_skipped_page(caplog):
    with caplog.at_level(logging.INFO):
        ingest(MemoryPages(PAGES), HashingEmbedder(), InMemoryChunkStore())
    skipped = [r for r in caplog.records if r.getMessage() == "retired page left out of the index"]
    assert [r.fields["page_id"] for r in skipped] == ["p-return-window-old"]


def test_a_search_for_the_old_return_window_returns_no_retired_chunk(built):
    _, retriever, _ = built
    for mode in Mode:
        found = retriever.retrieve("return any item within 14 days", mode)
```

- Checks that `retriever.chunk_count == 4` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_ingest_logs_each_skipped_page`.
- Its parameters:
    - `caplog`.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `MemoryPages` from the project's `tests.conftest` (A page source over a list.).
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Stores a list built by looping under the name `skipped`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - The method `getMessage` of `r`.
- Checks that `[r.fields['page_id'] for r in skipped] == ['p-return-window-old']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_search_for_the_old_return_window_returns_no_retired_chunk`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Loop: the indented lines below run once for each item of `Mode`; `mode` names the current item.
- Stores the result of calling `retriever.retrieve` under the name `found`.
  - The method `retrieve` of `retriever`.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 43 to 55:

```python
        assert "p-return-window-old" not in found.page_ids


def test_embedding_is_done_in_batches():
    embedder = HashingEmbedder()
    many = [PAGES[0]] * 1
    ingest(MemoryPages(many + PAGES[2:]), embedder, InMemoryChunkStore())
    assert all(len(batch) <= 32 for batch in embedder.calls)


def test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find():
    class OppositeEmbedder(HashingEmbedder):
        """Puts the question far from every chunk, as a vector search that misses the page would."""
```

- Checks that `'p-return-window-old' not in found.page_ids` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Defines the function `test_embedding_is_done_in_batches`.
- It takes no parameters.
- Stores the result of calling `HashingEmbedder` under the name `embedder`.
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
- Stores the result of `[PAGES[0]] * 1` under the name `many`.
  - `*` is multiply.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `MemoryPages` from the project's `tests.conftest` (A page source over a list.).
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
  - `+` is add.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Checks that `all((len(batch) <= 32 for batch in embedder.calls))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<=` means less than or equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find`.
- It takes no parameters.
- Defines the class `OppositeEmbedder`. It builds on the project's `HashingEmbedder` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.). The author's own description: "Puts the question far from every chunk, as a vector search that misses the page would."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 57 to 68:

```python
        def embed(self, texts):
            vectors = super().embed(texts)
            return [[-x for x in v] if len(t) < 40 else v for t, v in zip(texts, vectors, strict=True)]

    store = InMemoryChunkStore()
    embedder = OppositeEmbedder()
    ingest(MemoryPages(PAGES), embedder, store)
    retriever = HybridRetriever(store, embedder, k=2)
    keyword = retriever.retrieve("What's E2091 about?", Mode.KEYWORD)
    fused = retriever.retrieve("What's E2091 about?", Mode.FUSED)
    assert keyword.page_ids[0] == "p-error-e2091"
    assert "p-error-e2091" in fused.page_ids
```

- Defines the method `embed`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts`.
- Stores the result of calling `super().embed` under the name `vectors`.
  - The method `embed` of `super()`.
  - `super` refers to the parent class.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `<` means less than.
  - `zip` walks several collections side by side, item by item.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of calling `InMemoryChunkStore` under the name `store`.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Stores the result of calling `OppositeEmbedder` under the name `embedder`.
  - `OppositeEmbedder`, a function defined in this file or passed in.
- Calls `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.) with 3 argument(s); the result is not kept.
  - `ingest` from the project's `cited_answers.application.retrieve` (Chunk the current pages, embed the chunks and replace the index. Retired pages stay out and are logged.).
  - `MemoryPages` from the project's `tests.conftest` (A page source over a list.).
- Stores the result of calling `HybridRetriever` under the name `retriever`.
  - `HybridRetriever` from the project's `cited_answers.application.retrieve` (Keyword (BM25) and vector search over the same chunks, fused with reciprocal rank fusion.).
- Stores the result of calling `retriever.retrieve` under the name `keyword`.
  - The method `retrieve` of `retriever`.
- Stores the result of calling `retriever.retrieve` under the name `fused`.
  - The method `retrieve` of `retriever`.
- Checks that `keyword.page_ids[0] == 'p-error-e2091'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'p-error-e2091' in fused.page_ids` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 71 to 80:

```python
def test_best_similarity_is_the_highest_cosine_among_the_returned_chunks(built):
    _, retriever, _ = built
    close = retriever.retrieve("gift cards amounts expire", Mode.FUSED)
    far = retriever.retrieve("zebra quartz plasma", Mode.FUSED)
    assert close.best_similarity > far.best_similarity
    assert close.chunks[0].page_id == "p-gift-cards"


def good_answer(request):
    return "Thirty days [p-return-window:0]."
```

- Defines the function `test_best_similarity_is_the_highest_cosine_among_the_returned_chunks`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `retriever.retrieve` under the name `close`.
  - The method `retrieve` of `retriever`.
- Stores the result of calling `retriever.retrieve` under the name `far`.
  - The method `retrieve` of `retriever`.
- Checks that `close.best_similarity > far.best_similarity` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `close.chunks[0].page_id == 'p-gift-cards'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `good_answer`.
- Its parameters:
    - `request`.
- Ends the function and gives back the text `Thirty days [p-return-window:0].` to the caller.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 83 to 94:

```python
def service(retriever, answer=good_answer, threshold=0.0, model=None):
    return AnswerService(retriever, model or ScriptedModel(answer), PROMPT, threshold)


def test_a_cited_answer_is_returned_with_its_citations_and_the_passages_in_the_prompt(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer)
    answer = service(retriever, model=model).ask("How many days to return an item?", "q1")
    assert answer.status is Status.ANSWERED
    assert answer.citations == ("p-return-window:0",)
    request = model.requests[0]
    assert request.system == PROMPT.text
```

- Defines the function `service`.
- Its parameters:
    - `retriever`.
    - `answer`; if the caller leaves it out it is the value named `good_answer`.
    - `threshold`; if the caller leaves it out it is the number `0.0`.
    - `model`; if the caller leaves it out it is nothing (`None`).
- Ends the function and gives back the result of calling `AnswerService` to the caller.
  - `AnswerService` from the project's `cited_answers.application.answer` (Retrieve, refuse early below the threshold, ask the model, check the citations.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Defines the function `test_a_cited_answer_is_returned_with_its_citations_and_the_passages_in_the_prompt`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Stores the result of calling `service(retriever, model=model).ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
- Checks that `answer.status is Status.ANSWERED` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `answer.citations == ('p-return-window:0',)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Stores the part of `model.requests` picked by `0` under the name `request`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `request.system == PROMPT.text` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 95 to 106:

```python
    assert "[p-return-window:0]" in request.messages[0].content
    assert request.messages[0].content.endswith("Question: How many days to return an item?")
    assert request.tag == "q1|answer-v1"
    assert (answer.input_tokens, answer.output_tokens) == (30, 8)


def test_below_the_threshold_the_model_is_never_called(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer)
    answer = service(retriever, threshold=0.99, model=model).ask("zebra quartz plasma")
    assert (answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.BELOW_THRESHOLD, REFUSAL_MESSAGE)
    assert model.requests == []
```

- Checks that `'[p-return-window:0]' in request.messages[0].content` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `request.messages[0].content.endswith('Question: How many days to return an it...` is true; if it is not, the test fails with an `AssertionError`.
  - `.endswith(...)` asks whether text ends with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `request.tag == 'q1|answer-v1'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `(answer.input_tokens, answer.output_tokens) == (30, 8)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_below_the_threshold_the_model_is_never_called`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Stores the result of calling `service(retriever, threshold=0.99, model=model)...` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
- Checks that `(answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.BELOW_...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `model.requests == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 109 to 120:

```python
def test_the_model_may_refuse_too(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: REFUSAL_MESSAGE).ask("What is the return window for sale items?")
    assert (answer.status, answer.reason) == (Status.REFUSED, Reason.MODEL_REFUSED)
    assert answer.refused


def test_an_answer_without_a_citation_is_replaced_by_the_refusal_and_the_raw_text_is_kept(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: "It is thirty days.").ask("return window days")
    assert (answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.NO_CITATION, REFUSAL_MESSAGE)
    assert answer.raw_text == "It is thirty days."
```

- Defines the function `test_the_model_may_refuse_too`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `service(retriever, lambda r: REFUSAL_MESSAGE).ask` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `(answer.status, answer.reason) == (Status.REFUSED, Reason.MODEL_REFUSED)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `answer.refused` is true; if it is not, the test fails with an `AssertionError`.
- Defines the function `test_an_answer_without_a_citation_is_replaced_by_the_refusal_and_the_raw_text_is_kept`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `service(retriever, lambda r: 'It is thirty days...` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `(answer.status, answer.reason, answer.text) == (Status.REFUSED, Reason.NO_CIT...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `answer.raw_text == 'It is thirty days.'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 123 to 133:

```python
def test_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal(built):
    _, retriever, _ = built
    answer = service(retriever, lambda r: "Yes [p-loyalty:0].").ask("return window days")
    assert (answer.status, answer.reason) == (Status.REFUSED, Reason.CITATION_NOT_RETRIEVED)


def test_a_model_without_sampling_support_is_asked_without_a_temperature(built):
    _, retriever, _ = built
    model = ScriptedModel(good_answer, sampling=False)
    service(retriever, model=model).ask("return window days")
    assert model.requests[0].temperature is None
```

- Defines the function `test_a_planted_citation_to_a_chunk_that_was_not_retrieved_is_replaced_by_the_refusal`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `service(retriever, lambda r: 'Yes [p-loyalty:0]...` under the name `answer`.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `(answer.status, answer.reason) == (Status.REFUSED, Reason.CITATION_NOT_RETRIE...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_model_without_sampling_support_is_asked_without_a_temperature`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Calls the method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.) with 1 argument(s); the result is not kept.
  - The method `ask` of the project's `AnswerService` (Answer one question. Below the threshold the model is never called.).
  - `service`, a function of this file.
- Checks that `model.requests[0].temperature is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 136 to 139:

```python
def test_context_formatting_puts_the_id_first(built):
    _, retriever, _ = built
    text = format_context(retriever.retrieve("gift cards", Mode.FUSED).chunks)
    assert text.startswith("[p-gift-cards:0] Gift cards > Amounts (updated 2026-09-01)")
```

- Defines the function `test_context_formatting_puts_the_id_first`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `format_context` under the name `text`.
  - `format_context` from the project's `cited_answers.application.answer` (The passages as the model sees them, each under its id in square brackets.).
  - The method `retrieve` of `retriever`.
- Checks that `text.startswith('[p-gift-cards:0] Gift cards > Amounts (updated 2026-09-01)')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 142 to 153:

```python
QUESTIONS = [
    Question(
        "q1", QuestionType.ANSWERABLE, "How many days do I have to return an item?", "p-return-window", "30 days", False
    ),
    Question("q2", QuestionType.EXACT, "What's E2091 about?", "p-error-e2091", "no label could be created", False),
    Question("q3", QuestionType.UNANSWERABLE, "zebra quartz plasma", None, None, False),
]


def test_retrieval_is_graded_per_type_and_mode_with_the_misses_named(built):
    _, retriever, _ = built
    report = evaluate_retrieval(retriever, QUESTIONS)
```

- Stores a list of 3 item(s) under the name `QUESTIONS`.
  - `Question` from the project's `cited_answers.domain.evaluation` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.).
- Defines the function `test_retrieval_is_graded_per_type_and_mode_with_the_misses_named`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `evaluate_retrieval` under the name `report`.
  - `evaluate_retrieval` from the project's `cited_answers.application.evaluate` (For answerable and exact questions, count a hit when a chunk of the gold page is in the top five.).

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 154 to 166:

```python
    assert report.rates[("answerable", "fused")].trials == 1
    assert report.rates[("exact", "keyword")].successes == 1
    assert ("answerable", "vector") in report.rates
    assert not any(kind == "unanswerable" for kind, _ in report.rates)


def answers_by_question(request):
    content = request.messages[0].content
    if "How many days" in content:
        return "Thirty days [p-return-window:0]."
    if "E2091" in content:
        return "It is the wrong thing [p-error-e2091:0]."
    return "Something [p-gift-cards:0]."
```

- Checks that `report.rates['answerable', 'fused'].trials == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `report.rates['exact', 'keyword'].successes == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `('answerable', 'vector') in report.rates` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `not any((kind == 'unanswerable' for kind, _ in report.rates))` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Defines the function `answers_by_question`.
- Its parameters:
    - `request`.
- Stores the `content` of `request.messages[0]` under the name `content`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `'How many days' in content` is true.
  - `in` means is contained in.
- Ends the function and gives back the text `Thirty days [p-return-window:0].` to the caller.
- Decision: the indented lines below run only when `'E2091' in content` is true.
  - `in` means is contained in.
- Ends the function and gives back the text `It is the wrong thing [p-error-e2091:0].` to the caller.
- Ends the function and gives back the text `Something [p-gift-cards:0].` to the caller.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 169 to 179:

```python
def test_answers_and_retrieval_are_graded_apart_and_every_miss_goes_to_one_stage(built):
    _, retriever, _ = built
    judge_model = ScriptedModel(lambda r: "correct" if "Thirty days" in r.messages[0].content else "incorrect")
    report = evaluate_answers(
        service(retriever, answers_by_question), Judge(judge_model, Prompt("judge", "v1", "grade")), QUESTIONS
    )
    assert report.retrieval_hit.trials == 2
    assert report.answer_correct.successes == 1
    assert report.misses_by_stage[Stage.GENERATION] == 1
    assert report.misses_by_stage[Stage.RETRIEVAL] == 0
    assert report.unanswerable_refused.trials == 1
```

- Defines the function `test_answers_and_retrieval_are_graded_apart_and_every_miss_goes_to_one_stage`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `ScriptedModel` under the name `judge_model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `service`, a function of this file.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
- Checks that `report.retrieval_hit.trials == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.answer_correct.successes == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.misses_by_stage[Stage.GENERATION] == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `report.misses_by_stage[Stage.RETRIEVAL] == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `report.unanswerable_refused.trials == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 180 to 191:

```python
    assert (
        report.input_tokens == 30 * len(judge_model.requests) + 30 * 3 - 30 * len(judge_model.requests)
        or report.input_tokens > 0
    )


def test_an_unanswerable_question_that_gets_an_answer_is_listed_as_a_slip(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, answers_by_question), judge, QUESTIONS)
    assert report.unanswered_slips == ["q3"]
    assert report.unanswerable_refused.successes == 0
```

- Checks that `report.input_tokens == 30 * len(judge_model.requests) + 30 * 3 - 30 * len(jud...` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>` means greater than.
  - `-` is subtract.
  - `+` is add.
  - `*` is multiply.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_an_unanswerable_question_that_gets_an_answer_is_listed_as_a_slip`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `service`, a function of this file.
- Checks that `report.unanswered_slips == ['q3']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.unanswerable_refused.successes == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 194 to 205:

```python
def test_a_refused_answerable_question_counts_as_a_false_refusal_and_as_incorrect(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, lambda r: REFUSAL_MESSAGE), judge, QUESTIONS)
    assert report.false_refusals.successes == 2
    assert report.answer_correct.successes == 0


def test_a_stop_request_ends_the_run_between_questions(built):
    _, retriever, _ = built
    stops = iter([False, True])
    judge = Judge(ScriptedModel(lambda r: "correct"), Prompt("judge", "v1", "grade"))
```

- Defines the function `test_a_refused_answerable_question_counts_as_a_false_refusal_and_as_incorrect`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `service`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `report.false_refusals.successes == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.answer_correct.successes == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_stop_request_ends_the_run_between_questions`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `iter` under the name `stops`.
  - `iter` makes an iterator over a collection.
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `lambda args: expression` is a small unnamed function written inline.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 206 to 219:

```python
    report = evaluate_answers(
        service(retriever, answers_by_question), judge, QUESTIONS, stop_requested=lambda: next(stops)
    )
    assert len(report.results) == 1


def test_a_judge_reply_that_says_neither_counts_as_incorrect(built):
    _, retriever, _ = built
    judge = Judge(ScriptedModel(lambda r: "hmm"), Prompt("judge", "v1", "grade"))
    report = evaluate_answers(service(retriever, answers_by_question), judge, QUESTIONS[:1])
    assert report.answer_correct.successes == 0


def test_the_judge_request_names_the_question_the_fact_and_the_answer_and_differs_per_answer(built):
```

- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `service`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `next` takes the next item from an iterator.
- Checks that `len(report.results) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_judge_reply_that_says_neither_counts_as_incorrect`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `evaluate_answers` under the name `report`.
  - `evaluate_answers` from the project's `cited_answers.application.evaluate` (Run every question through retrieval, the model and the judge, then grade retrieval and answers apart.).
  - `service`, a function of this file.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Checks that `report.answer_correct.successes == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_the_judge_request_names_the_question_the_fact_and_the_answer_and_differs_per_answer`.
- Its parameters:
    - `built`.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 220 to 233:

```python
    model = ScriptedModel(lambda r: "correct")
    judge = Judge(model, Prompt("judge", "v1", "grade"))
    judge.grade(QUESTIONS[0], "Thirty days")
    judge.grade(QUESTIONS[0], "Fourteen days")
    first, second = model.requests
    assert "The answer must state: 30 days" in first.messages[0].content
    assert first.tag != second.tag
    assert first.max_output_tokens == 20


def test_summarize_of_nothing_is_all_zeroes():
    report = summarize([])
    assert report.retrieval_hit.trials == 0
    assert report.unanswered_slips == []
```

- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `Judge` under the name `judge`.
  - `Judge` from the project's `cited_answers.application.judge` (Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect.).
  - `Prompt` from the project's `cited_answers.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
- Calls the method `grade` of the project's `Judge` (True when the judge calls the answer correct.) with 2 argument(s); the result is not kept.
  - The method `grade` of the project's `Judge` (True when the judge calls the answer correct.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls the method `grade` of the project's `Judge` (True when the judge calls the answer correct.) with 2 argument(s); the result is not kept.
  - The method `grade` of the project's `Judge` (True when the judge calls the answer correct.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the `requests` of `model` under the name `(first, second)`.
- Checks that `'The answer must state: 30 days' in first.messages[0].content` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `first.tag != second.tag` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
- Checks that `first.max_output_tokens == 20` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_summarize_of_nothing_is_all_zeroes`.
- It takes no parameters.
- Stores the result of calling `summarize` under the name `report`.
  - `summarize` from the project's `cited_answers.application.evaluate` (Fold per-question results into the report's numbers.).
- Checks that `report.retrieval_hit.trials == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.unanswered_slips == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 236 to 247:

```python
def test_the_threshold_is_tuned_from_dev_scores_only(built):
    _, retriever, _ = built
    dev = [
        Question("d1", QuestionType.ANSWERABLE, "How many days do I return an item", "p-return-window", "30", False),
        Question("d2", QuestionType.ANSWERABLE, "gift cards amounts expire", "p-gift-cards", "10", False),
        Question("d3", QuestionType.UNANSWERABLE, "zebra quartz plasma", None, None, False),
    ]
    svc = service(retriever)
    answerable, unanswerable = dev_scores(svc, dev)
    assert len(answerable) == 2
    assert len(unanswerable) == 1
    choice = choose_threshold(svc, dev, max_false_refusal=0.0)
```

- Defines the function `test_the_threshold_is_tuned_from_dev_scores_only`.
- Its parameters:
    - `built`.
- Stores the value named `built` under the name `(_, retriever, _)`.
- Stores a list of 3 item(s) under the name `dev`.
  - `Question` from the project's `cited_answers.domain.evaluation` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.).
- Stores the result of calling `service` under the name `svc`.
  - `service`, a function of this file.
- Stores the result of calling `dev_scores` under the name `(answerable, unanswerable)`.
  - `dev_scores` from the project's `cited_answers.application.threshold` (Best retrieval score of each answerable (gold-page) question and of each unanswerable one.).
- Checks that `len(answerable) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `len(unanswerable) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of calling `choose_threshold` under the name `choice`.
  - `choose_threshold` from the project's `cited_answers.application.threshold` (The threshold that refuses the most unanswerable dev questions at an acceptable false-refusal rate.).

`tests/unit/application/test_retrieve_answer_evaluate.py`, lines 248 to 249:

```python
    assert choice.false_refusal_rate == 0.0
    assert choice.unanswerable_refused_rate == 1.0
```

- Checks that `choice.false_refusal_rate == 0.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `choice.unanswerable_refused_rate == 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

### `tests/unit/domain/test_answering_and_evaluation.py`

116 non-blank lines; it defines `test_citations_are_read_in_order_without_repeats`, `test_an_answer_that_cites_only_retrieved_chunks_passes`, `test_a_planted_citation_to_a_chunk_that_was_not_retrieved_fails`, `test_an_answer_with_no_citation_fails_for_its_own_reason`, `test_a_literal_placeholder_citation_is_rejected_like_any_unretrieved_id`, `test_a_page_level_citation_is_read_as_its_one_retrieved_chunk_but_not_when_ambiguous`, `test_the_fixed_refusal_is_recognized_even_with_trailing_text`, `test_the_threshold_allows_the_stated_false_refusal_rate_and_reports_what_it_costs`, `test_tuning_needs_scores_for_both_kinds`, `test_wilson_stays_inside_zero_and_one_and_widens_for_small_n`, `test_a_rate_prints_with_its_interval`, `test_hit_at_k_looks_at_the_first_k_pages_only`, ....

`tests/unit/domain/test_answering_and_evaluation.py`, lines 1 to 10:

```python
import pytest

from cited_answers.domain.answering import (
    REFUSAL_MESSAGE,
    Reason,
    check_citations,
    extract_citations,
    is_model_refusal,
    tune_threshold,
)
```

- Makes the module `pytest` (installed package) available.
- Brings in `REFUSAL_MESSAGE`, `Reason` (Why a question was refused (or `none` when it was answered).), `check_citations` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.), `extract_citations` (Every `[id]` in the text, in order of first appearance, without repeats.), `is_model_refusal` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).), `tune_threshold` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.) from the project module `cited_answers.domain.answering`.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 11 to 24:

```python
from cited_answers.domain.evaluation import (
    InvalidQuestions,
    Question,
    QuestionType,
    Rate,
    Stage,
    agreement,
    classify_miss,
    hit_at_k,
    parse_verdict,
    validate_questions,
    wilson_interval,
)
from tests.conftest import chunk
```

- Brings in `InvalidQuestions` (The question file breaks a rule of the lesson.), `Question` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.), `Rate` (A count out of a total with its Wilson interval.), `Stage` (Where a wrong answer went wrong.), `agreement` (How many verdicts the judge shares with the hand grades, and how many were compared.), `classify_miss` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.), `hit_at_k` (True when a chunk of the gold page is among the first `k` retrieved.), `parse_verdict` (Read a judge's reply: True for correct, False for incorrect, None when it says neither.), `validate_questions` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.), `wilson_interval` (The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not.) from the project module `cited_answers.domain.evaluation`.
- Brings in `chunk` from the project module `tests.conftest`.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 26 to 36:

```python
RETRIEVED = [
    chunk("p-return-window:0", "x"),
    chunk("p-gift-cards:0", "y"),
    chunk("p-ship-times:0", "z"),
    chunk("p-ship-times:1", "w"),
]


def test_citations_are_read_in_order_without_repeats():
    assert extract_citations("A [p-a:0]. B [p-b:1] and again [p-a:0].") == ["p-a:0", "p-b:1"]
    assert extract_citations("no brackets, [two words] don't count") == []
```

- Stores a list of 4 item(s) under the name `RETRIEVED`.
  - `chunk` from the project's `tests.conftest`.
- Defines the function `test_citations_are_read_in_order_without_repeats`.
- It takes no parameters.
- Checks that `extract_citations('A [p-a:0]. B [p-b:1] and again [p-a:0].') == ['p-a:0', 'p-...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `extract_citations` from the project's `cited_answers.domain.answering` (Every `[id]` in the text, in order of first appearance, without repeats.).
- Checks that `extract_citations("no brackets, [two words] don't count") == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `extract_citations` from the project's `cited_answers.domain.answering` (Every `[id]` in the text, in order of first appearance, without repeats.).

`tests/unit/domain/test_answering_and_evaluation.py`, lines 39 to 48:

```python
def test_an_answer_that_cites_only_retrieved_chunks_passes():
    check = check_citations("Thirty days [p-return-window:0].", RETRIEVED)
    assert check.ok
    assert check.cited == ("p-return-window:0",)


def test_a_planted_citation_to_a_chunk_that_was_not_retrieved_fails():
    check = check_citations("Maybe [p-gift-cards:0] and [p-loyalty:0].", RETRIEVED)
    assert not check.ok
    assert check.reason is Reason.CITATION_NOT_RETRIEVED
```

- Defines the function `test_an_answer_that_cites_only_retrieved_chunks_passes`.
- It takes no parameters.
- Stores the result of calling `check_citations` under the name `check`.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Checks that `check.ok` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `check.cited == ('p-return-window:0',)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_planted_citation_to_a_chunk_that_was_not_retrieved_fails`.
- It takes no parameters.
- Stores the result of calling `check_citations` under the name `check`.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Checks that `not check.ok` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Checks that `check.reason is Reason.CITATION_NOT_RETRIEVED` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 51 to 62:

```python
def test_an_answer_with_no_citation_fails_for_its_own_reason():
    check = check_citations("It is thirty days.", RETRIEVED)
    assert (check.ok, check.reason) == (False, Reason.NO_CITATION)


def test_a_literal_placeholder_citation_is_rejected_like_any_unretrieved_id():
    assert not check_citations("Thirty days [chunk-id] [p-return-window:0]", RETRIEVED).ok


def test_a_page_level_citation_is_read_as_its_one_retrieved_chunk_but_not_when_ambiguous():
    assert check_citations("Yes [p-return-window]", RETRIEVED).cited == ("p-return-window:0",)
    assert not check_citations("Yes [p-ship-times]", RETRIEVED).ok  # two chunks of that page were retrieved
```

- Defines the function `test_an_answer_with_no_citation_fails_for_its_own_reason`.
- It takes no parameters.
- Stores the result of calling `check_citations` under the name `check`.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Checks that `(check.ok, check.reason) == (False, Reason.NO_CITATION)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_literal_placeholder_citation_is_rejected_like_any_unretrieved_id`.
- It takes no parameters.
- Checks that `not check_citations('Thirty days [chunk-id] [p-return-window:0]', RETRIEVED).ok` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Defines the function `test_a_page_level_citation_is_read_as_its_one_retrieved_chunk_but_not_when_ambiguous`.
- It takes no parameters.
- Checks that `check_citations('Yes [p-return-window]', RETRIEVED).cited == ('p-return-windo...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).
- Checks that `not check_citations('Yes [p-ship-times]', RETRIEVED).ok` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `check_citations` from the project's `cited_answers.domain.answering` (An answer must cite at least one chunk, and only chunks that were retrieved for this request.).

`tests/unit/domain/test_answering_and_evaluation.py`, lines 65 to 76:

```python
def test_the_fixed_refusal_is_recognized_even_with_trailing_text():
    assert is_model_refusal(REFUSAL_MESSAGE)
    assert is_model_refusal("I don't have information about that in our help center")
    assert is_model_refusal(REFUSAL_MESSAGE + " [p-a:0]")
    assert not is_model_refusal("Returns take 30 days [p-a:0]")


def test_the_threshold_allows_the_stated_false_refusal_rate_and_reports_what_it_costs():
    answerable = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.3]
    unanswerable = [0.2, 0.25, 0.4, 0.52, 0.6]
    choice = tune_threshold(answerable, unanswerable, max_false_refusal=0.10)
    assert choice.threshold == 0.5
```

- Defines the function `test_the_fixed_refusal_is_recognized_even_with_trailing_text`.
- It takes no parameters.
- Checks that `is_model_refusal(REFUSAL_MESSAGE)` is true; if it is not, the test fails with an `AssertionError`.
  - `is_model_refusal` from the project's `cited_answers.domain.answering` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).).
- Checks that `is_model_refusal("I don't have information about that in our help center")` is true; if it is not, the test fails with an `AssertionError`.
  - `is_model_refusal` from the project's `cited_answers.domain.answering` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).).
- Checks that `is_model_refusal(REFUSAL_MESSAGE + ' [p-a:0]')` is true; if it is not, the test fails with an `AssertionError`.
  - `is_model_refusal` from the project's `cited_answers.domain.answering` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).).
  - `+` is add.
- Checks that `not is_model_refusal('Returns take 30 days [p-a:0]')` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `is_model_refusal` from the project's `cited_answers.domain.answering` (True when the model answered with the fixed refusal message (it may add a trailing citation or spacing).).
- Defines the function `test_the_threshold_allows_the_stated_false_refusal_rate_and_reports_what_it_costs`.
- It takes no parameters.
- Stores a list of 10 item(s) under the name `answerable`.
- Stores a list of 5 item(s) under the name `unanswerable`.
- Stores the result of calling `tune_threshold` under the name `choice`.
  - `tune_threshold` from the project's `cited_answers.domain.answering` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.).
- Checks that `choice.threshold == 0.5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 77 to 90:

```python
    assert choice.false_refusal_rate == pytest.approx(0.1)
    assert choice.unanswerable_refused_rate == pytest.approx(3 / 5)


def test_tuning_needs_scores_for_both_kinds():
    with pytest.raises(ValueError, match=r"answerable"):
        tune_threshold([], [0.1])


def test_wilson_stays_inside_zero_and_one_and_widens_for_small_n():
    low, high = wilson_interval(6, 6)
    assert 0.5 < low < 1.0
    assert high == pytest.approx(1.0)
    assert wilson_interval(0, 0) == (0.0, 1.0)
```

- Checks that `choice.false_refusal_rate == pytest.approx(0.1)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
- Checks that `choice.unanswerable_refused_rate == pytest.approx(3 / 5)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
  - `/` is divide.
- Defines the function `test_tuning_needs_scores_for_both_kinds`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(ValueError, match='answerable')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `tune_threshold` from the project's `cited_answers.domain.answering` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.) with 2 argument(s); the result is not kept.
  - `tune_threshold` from the project's `cited_answers.domain.answering` (The highest threshold that wrongly refuses at most `max_false_refusal` of the answerable questions.).
- Defines the function `test_wilson_stays_inside_zero_and_one_and_widens_for_small_n`.
- It takes no parameters.
- Stores the result of calling `wilson_interval` under the name `(low, high)`.
  - `wilson_interval` from the project's `cited_answers.domain.evaluation` (The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not.).
- Checks that `0.5 < low < 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
- Checks that `high == pytest.approx(1.0)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
- Checks that `wilson_interval(0, 0) == (0.0, 1.0)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `wilson_interval` from the project's `cited_answers.domain.evaluation` (The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not.).

`tests/unit/domain/test_answering_and_evaluation.py`, lines 91 to 102:

```python
    assert (wilson_interval(10, 10)[0]) < wilson_interval(100, 100)[0]


def test_a_rate_prints_with_its_interval():
    assert str(Rate(70, 70)).startswith("70/70 = 1.00 (Wilson 0.9")
    assert Rate(0, 0).value == 0.0


def test_hit_at_k_looks_at_the_first_k_pages_only():
    assert hit_at_k(["a", "b", "c"], "c", k=3)
    assert not hit_at_k(["a", "b", "c"], "c", k=2)
    assert not hit_at_k(["a"], None)
```

- Checks that `wilson_interval(10, 10)[0] < wilson_interval(100, 100)[0]` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `wilson_interval` from the project's `cited_answers.domain.evaluation` (The 95% Wilson score interval for a rate; sensible for small counts where the plain interval is not.).
- Defines the function `test_a_rate_prints_with_its_interval`.
- It takes no parameters.
- Checks that `str(Rate(70, 70)).startswith('70/70 = 1.00 (Wilson 0.9')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
  - `str` turns a value into text.
  - `Rate` from the project's `cited_answers.domain.evaluation` (A count out of a total with its Wilson interval.).
- Checks that `Rate(0, 0).value == 0.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `Rate` from the project's `cited_answers.domain.evaluation` (A count out of a total with its Wilson interval.).
- Defines the function `test_hit_at_k_looks_at_the_first_k_pages_only`.
- It takes no parameters.
- Checks that `hit_at_k(['a', 'b', 'c'], 'c', k=3)` is true; if it is not, the test fails with an `AssertionError`.
  - `hit_at_k` from the project's `cited_answers.domain.evaluation` (True when a chunk of the gold page is among the first `k` retrieved.).
- Checks that `not hit_at_k(['a', 'b', 'c'], 'c', k=2)` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `hit_at_k` from the project's `cited_answers.domain.evaluation` (True when a chunk of the gold page is among the first `k` retrieved.).
- Checks that `not hit_at_k(['a'], None)` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `hit_at_k` from the project's `cited_answers.domain.evaluation` (True when a chunk of the gold page is among the first `k` retrieved.).

`tests/unit/domain/test_answering_and_evaluation.py`, lines 105 to 116:

```python
@pytest.mark.parametrize(
    ("text", "verdict"),
    [
        ("correct", True),
        ("Correct.", True),
        ("incorrect", False),
        ("The answer is incorrect", False),
        ("maybe", None),
        ("", None),
    ],
)
def test_a_judge_reply_is_read_as_correct_incorrect_or_neither(text, verdict):
```

- Defines the function `test_a_judge_reply_is_read_as_correct_incorrect_or_neither`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `text`.
    - `verdict`.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 117 to 129:

```python
    assert parse_verdict(text) is verdict


def test_a_wrong_answer_is_a_retrieval_miss_when_the_gold_page_was_not_found_and_a_generation_miss_otherwise():
    assert classify_miss(hit=False, correct=False) is Stage.RETRIEVAL
    assert classify_miss(hit=True, correct=False) is Stage.GENERATION
    assert classify_miss(hit=True, correct=True) is None


def test_agreement_counts_shared_verdicts_and_refuses_unequal_lengths():
    assert agreement([True, False, True], [True, True, True]) == (2, 3)
    with pytest.raises(ValueError, match="same length"):
        agreement([True], [True, False])
```

- Checks that `parse_verdict(text) is verdict` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `parse_verdict` from the project's `cited_answers.domain.evaluation` (Read a judge's reply: True for correct, False for incorrect, None when it says neither.).
- Defines the function `test_a_wrong_answer_is_a_retrieval_miss_when_the_gold_page_was_not_found_and_a_generation_miss_otherwise`.
- It takes no parameters.
- Checks that `classify_miss(hit=False, correct=False) is Stage.RETRIEVAL` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `classify_miss` from the project's `cited_answers.domain.evaluation` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.).
- Checks that `classify_miss(hit=True, correct=False) is Stage.GENERATION` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `classify_miss` from the project's `cited_answers.domain.evaluation` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.).
- Checks that `classify_miss(hit=True, correct=True) is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `classify_miss` from the project's `cited_answers.domain.evaluation` (A wrong answer is a retrieval miss when the gold page was not retrieved, otherwise a generation miss.).
- Defines the function `test_agreement_counts_shared_verdicts_and_refuses_unequal_lengths`.
- It takes no parameters.
- Checks that `agreement([True, False, True], [True, True, True]) == (2, 3)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `agreement` from the project's `cited_answers.domain.evaluation` (How many verdicts the judge shares with the hand grades, and how many were compared.).
- A `with` block: it sets up `pytest.raises(ValueError, match='same length')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `agreement` from the project's `cited_answers.domain.evaluation` (How many verdicts the judge shares with the hand grades, and how many were compared.) with 2 argument(s); the result is not kept.
  - `agreement` from the project's `cited_answers.domain.evaluation` (How many verdicts the judge shares with the hand grades, and how many were compared.).

`tests/unit/domain/test_answering_and_evaluation.py`, lines 132 to 143:

```python
def question(i, kind, gold="p", fact="f"):
    return Question(
        f"q{i}",
        kind,
        "what?",
        gold if kind is not QuestionType.UNANSWERABLE else None,
        fact if kind is not QuestionType.UNANSWERABLE else None,
        False,
    )


def test_a_question_set_must_have_the_mix_unique_ids_and_a_fact_for_every_gradable_question():
```

- Defines the function `question`.
- Its parameters:
    - `i`.
    - `kind`.
    - `gold`; if the caller leaves it out it is the text `p`.
    - `fact`; if the caller leaves it out it is the text `f`.
- Ends the function and gives back the result of calling `Question` to the caller.
  - `Question` from the project's `cited_answers.domain.evaluation` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is not` means not the same object.
- Defines the function `test_a_question_set_must_have_the_mix_unique_ids_and_a_fact_for_every_gradable_question`.
- It takes no parameters.

`tests/unit/domain/test_answering_and_evaluation.py`, lines 144 to 152:

```python
    ok = [question(1, QuestionType.ANSWERABLE), question(2, QuestionType.EXACT), question(3, QuestionType.UNANSWERABLE)]
    validate_questions(ok, 1, 1, 1)
    with pytest.raises(InvalidQuestions, match="expected"):
        validate_questions(ok, 2, 1, 1)
    with pytest.raises(InvalidQuestions, match="unique"):
        validate_questions([ok[0], ok[0]], 1, 0, 0)
    bad = [Question("q1", QuestionType.ANSWERABLE, "what?", "p", None, False)]
    with pytest.raises(InvalidQuestions, match="gold page and a fact"):
        validate_questions(bad, 1, 0, 0)
```

- Stores a list of 3 item(s) under the name `ok`.
  - `question`, a function of this file.
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
- A `with` block: it sets up `pytest.raises(InvalidQuestions, match='expected')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
- A `with` block: it sets up `pytest.raises(InvalidQuestions, match='unique')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a list of 1 item(s) under the name `bad`.
  - `Question` from the project's `cited_answers.domain.evaluation` (One evaluation question. `fact` is what a correct answer must state; `near_miss` marks a close unanswerable.).
- A `with` block: it sets up `pytest.raises(InvalidQuestions, match='gold page and a fa...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.) with 4 argument(s); the result is not kept.
  - `validate_questions` from the project's `cited_answers.domain.evaluation` (Check a question set has the lesson's mix and that every gradable question has a gold page and a fact.).

### `tests/unit/domain/test_llm.py`

22 non-blank lines; it defines `request`, `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, `test_tools_and_schemas_change_the_fingerprint`, `test_a_response_survives_a_json_round_trip_with_tool_calls`.

`tests/unit/domain/test_llm.py`, lines 1 to 14:

```python
from cited_answers.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, ToolCall, ToolSpec, Usage


def request(**changes):
    base = {"messages": (ChatMessage.user("hello"),), "max_output_tokens": 50, "tag": "a"}
    return ChatRequest(**{**base, **changes})


def test_the_same_request_always_has_the_same_fingerprint():
    assert request().fingerprint() == request().fingerprint()


def test_the_model_name_is_not_part_of_the_fingerprint():
    assert request(model="a-model").fingerprint() == request(model="another").fingerprint()
```

- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `cited_answers.domain.llm`.
- Defines the function `request`.
- Its parameters:
    - `**changes` collects any extra named arguments into a dictionary.
- Stores a dictionary with 3 entries under the name `base`.
  - The method `user` of `ChatMessage`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- Defines the function `test_the_same_request_always_has_the_same_fingerprint`.
- It takes no parameters.
- Checks that `request().fingerprint() == request().fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_the_model_name_is_not_part_of_the_fingerprint`.
- It takes no parameters.
- Checks that `request(model='a-model').fingerprint() == request(model='another').fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.

`tests/unit/domain/test_llm.py`, lines 17 to 27:

```python
def test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint():
    base = request().fingerprint()
    assert request(tag="b").fingerprint() != base
    assert request(temperature=0.7).fingerprint() != base
    assert request(top_p=0.9).fingerprint() != base


def test_tools_and_schemas_change_the_fingerprint():
    base = request().fingerprint()
    assert request(response_schema={"type": "object"}).fingerprint() != base
    assert request(tools=(ToolSpec("t", "d", {"type": "object"}),)).fingerprint() != base
```

- Defines the function `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tag='b').fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(temperature=0.7).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(top_p=0.9).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_tools_and_schemas_change_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(response_schema={'type': 'object'}).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tools=(ToolSpec('t', 'd', {'type': 'object'}),)).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
  - `ToolSpec` from the project's `cited_answers.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).

`tests/unit/domain/test_llm.py`, lines 30 to 34:

```python
def test_a_response_survives_a_json_round_trip_with_tool_calls():
    response = ChatResponse(
        "text", StopReason.TOOL_CALLS, Usage(5, 7), 1.25, "m", (ToolCall("c1", "lookup", {"id": 4}),)
    )
    assert ChatResponse.from_json(response.to_json()) == response
```

- Defines the function `test_a_response_survives_a_json_round_trip_with_tool_calls`.
- It takes no parameters.
- Stores the result of calling `ChatResponse` under the name `response`.
  - `ChatResponse` from the project's `cited_answers.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `cited_answers.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
- Checks that `ChatResponse.from_json(response.to_json()) == response` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_json` of `ChatResponse`.
  - The method `to_json` of `response`.

### `tests/unit/domain/test_pages_chunking_retrieval.py`

108 non-blank lines; it defines `test_a_page_file_is_parsed_into_metadata_and_sections_with_heading_paths`, `test_a_broken_page_file_is_refused_with_the_reason`, `test_every_chunk_carries_page_id_heading_path_date_and_status_and_ids_are_per_page`, `test_a_long_section_is_split_at_sentence_ends_under_the_token_limit_and_never_spans_pages`, `test_retired_pages_are_left_out_and_reported_by_id`, `test_token_estimate_is_words_times_one_point_three`, `test_tokenizer_splits_codes_on_hyphens_so_the_bare_code_matches`, `test_bm25_finds_the_chunk_with_the_rare_term_and_ignores_chunks_without_any_query_term`, `test_the_whitespace_tokenizer_misses_the_bare_code_that_the_hyphen_aware_one_finds`, `test_an_empty_index_returns_nothing`, `test_cosine_of_parallel_orthogonal_and_zero_vectors`, `test_fusion_adds_reciprocal_ranks_so_a_chunk_in_both_lists_wins`, ....

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 1 to 14:

```python
from datetime import date

import pytest

from cited_answers.domain.chunking import MAX_CHUNK_TOKENS, chunk_current_pages, chunk_page, estimate_tokens
from cited_answers.domain.pages import InvalidPage, PageStatus, parse_page
from cited_answers.domain.retrieval import (
    Bm25Index,
    cosine,
    reciprocal_rank_fusion,
    tokenize,
    whitespace_tokenize,
)
from tests.conftest import PAGES, chunk, page
```

- Brings in `date` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `MAX_CHUNK_TOKENS`, `chunk_current_pages` (Chunk every current page; return the chunks and the ids of the retired pages that were left out.), `chunk_page` (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.), `estimate_tokens` (Rough token count for a size limit: words times 1.3.) from the project module `cited_answers.domain.chunking`.
- Brings in `InvalidPage` (A page file is missing its front matter or one of its fields.), `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.), `parse_page` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.) from the project module `cited_answers.domain.pages`.
- Brings in `Bm25Index` (Okapi BM25 over chunk text (heading path included).), `cosine` (Cosine similarity of two vectors (0.0 if either is all zeros).), `reciprocal_rank_fusion` (Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up.), `tokenize` (Lowercase words split on anything that is not a letter or a digit, so `PR-E2091` becomes `pr` and `e2091`.), `whitespace_tokenize` (The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it.) from the project module `cited_answers.domain.retrieval`.
- Brings in `PAGES`, `chunk`, `page` from the project module `tests.conftest`.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 16 to 33:

```python
SOURCE = """---
id: p-return-window
title: Return window
updated: 2026-09-01
status: current
---
# Return window

## 30 days

You can return items within 30 days.

## Condition

### Packaging

Keep the original box.
"""
```

- Stores the text `--- id: p-return-window title: Return window up...` under the name `SOURCE`.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 36 to 47:

```python
def test_a_page_file_is_parsed_into_metadata_and_sections_with_heading_paths():
    parsed = parse_page(SOURCE)
    assert (parsed.id, parsed.title, parsed.updated, parsed.status) == (
        "p-return-window",
        "Return window",
        date(2026, 9, 1),
        PageStatus.CURRENT,
    )
    assert [s.path for s in parsed.sections] == [
        "Return window > 30 days",
        "Return window > Condition > Packaging",
    ]
```

- Defines the function `test_a_page_file_is_parsed_into_metadata_and_sections_with_heading_paths`.
- It takes no parameters.
- Stores the result of calling `parse_page` under the name `parsed`.
  - `parse_page` from the project's `cited_answers.domain.pages` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.).
- Checks that `(parsed.id, parsed.title, parsed.updated, parsed.status) == ('p-return-window...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `date` from the standard library module `datetime`.
- Checks that `[s.path for s in parsed.sections] == ['Return window > 30 days', 'Return wind...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 48 to 61:

```python
    assert parsed.sections[0].text == "You can return items within 30 days."


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("no front matter", "front matter"),
        ("---\nid: a\ntitle: t\nupdated: 2026-01-01\n---\n# t\n\n## h\n\nx", "'status'"),
        ("---\nid: a\ntitle: t\nupdated: 2026-01-01\nstatus: draft\n---\n# t\n\n## h\n\nx", "draft"),
        ("---\nid: a\ntitle: t\nupdated: yesterday\nstatus: current\n---\n# t\n\n## h\n\nx", "yesterday"),
        ("---\nid: a\ntitle: t\nupdated: 2026-01-01\nstatus: current\n---\n# t\n", "no section"),
    ],
)
def test_a_broken_page_file_is_refused_with_the_reason(source, message):
```

- Checks that `parsed.sections[0].text == 'You can return items within 30 days.'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_broken_page_file_is_refused_with_the_reason`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `source`.
    - `message`.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 62 to 75:

```python
    with pytest.raises(InvalidPage, match=message):
        parse_page(source)


def test_every_chunk_carries_page_id_heading_path_date_and_status_and_ids_are_per_page():
    chunks = chunk_page(PAGES[0])
    assert [c.id for c in chunks] == ["p-return-window:0"]
    only = chunks[0]
    assert (only.page_id, only.heading_path, only.updated, only.status) == (
        "p-return-window",
        "Return window > 30 days",
        date(2026, 9, 1),
        PageStatus.CURRENT,
    )
```

- A `with` block: it sets up `pytest.raises(InvalidPage, match=message)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `parse_page` from the project's `cited_answers.domain.pages` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.) with 1 argument(s); the result is not kept.
  - `parse_page` from the project's `cited_answers.domain.pages` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.).
- Defines the function `test_every_chunk_carries_page_id_heading_path_date_and_status_and_ids_are_per_page`.
- It takes no parameters.
- Stores the result of calling `chunk_page` under the name `chunks`.
  - `chunk_page` from the project's `cited_answers.domain.chunking` (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[c.id for c in chunks] == ['p-return-window:0']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the part of `chunks` picked by `0` under the name `only`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `(only.page_id, only.heading_path, only.updated, only.status) == ('p-return-wi...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `date` from the standard library module `datetime`.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 76 to 89:

```python
    assert "Return window > 30 days" in only.for_search()


def test_a_long_section_is_split_at_sentence_ends_under_the_token_limit_and_never_spans_pages():
    sentence = "This sentence has exactly eight words in it. "
    long_page = page("p-long", "Long", [("Body", sentence * 80), ("Other", "Short text.")])
    chunks = chunk_page(long_page)
    assert len(chunks) > 2
    assert all(c.tokens <= MAX_CHUNK_TOKENS for c in chunks)
    assert all(c.page_id == "p-long" for c in chunks)
    assert [c.id for c in chunks] == [f"p-long:{i}" for i in range(len(chunks))]


def test_retired_pages_are_left_out_and_reported_by_id():
```

- Checks that `'Return window > 30 days' in only.for_search()` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `for_search` of the project's `Chunk` (The text that is embedded and keyword-indexed: the heading path carries words the body may not repeat.).
- Defines the function `test_a_long_section_is_split_at_sentence_ends_under_the_token_limit_and_never_spans_pages`.
- It takes no parameters.
- Stores the text `This sentence has exactly eight words in it. ` under the name `sentence`.
- Stores the result of calling `page` under the name `long_page`.
  - `page` from the project's `tests.conftest`.
  - `*` is multiply.
- Stores the result of calling `chunk_page` under the name `chunks`.
  - `chunk_page` from the project's `cited_answers.domain.chunking` (One chunk per section, split at sentence ends when a section is longer than `max_tokens`.).
- Checks that `len(chunks) > 2` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `all((c.tokens <= MAX_CHUNK_TOKENS for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<=` means less than or equal.
- Checks that `all((c.page_id == 'p-long' for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Checks that `[c.id for c in chunks] == [f'p-long:{i}' for i in range(len(chunks))]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_retired_pages_are_left_out_and_reported_by_id`.
- It takes no parameters.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 90 to 102:

```python
    chunks, skipped = chunk_current_pages(PAGES)
    assert skipped == ["p-return-window-old"]
    assert all(c.status is PageStatus.CURRENT for c in chunks)
    assert "p-return-window-old" not in {c.page_id for c in chunks}


def test_token_estimate_is_words_times_one_point_three():
    assert estimate_tokens("one two three four five six seven eight nine ten") == 13


def test_tokenizer_splits_codes_on_hyphens_so_the_bare_code_matches():
    assert tokenize("Error PR-E2091 means") == ["error", "pr", "e2091", "means"]
    assert whitespace_tokenize("Error PR-E2091 means") == ["error", "pr-e2091", "means"]
```

- Stores the result of calling `chunk_current_pages` under the name `(chunks, skipped)`.
  - `chunk_current_pages` from the project's `cited_answers.domain.chunking` (Chunk every current page; return the chunks and the ids of the retired pages that were left out.).
- Checks that `skipped == ['p-return-window-old']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `all((c.status is PageStatus.CURRENT for c in chunks))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.
- Checks that `'p-return-window-old' not in {c.page_id for c in chunks}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_token_estimate_is_words_times_one_point_three`.
- It takes no parameters.
- Checks that `estimate_tokens('one two three four five six seven eight nine ten') == 13` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `estimate_tokens` from the project's `cited_answers.domain.chunking` (Rough token count for a size limit: words times 1.3.).
- Defines the function `test_tokenizer_splits_codes_on_hyphens_so_the_bare_code_matches`.
- It takes no parameters.
- Checks that `tokenize('Error PR-E2091 means') == ['error', 'pr', 'e2091', 'means']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `tokenize` from the project's `cited_answers.domain.retrieval` (Lowercase words split on anything that is not a letter or a digit, so `PR-E2091` becomes `pr` and `e2091`.).
- Checks that `whitespace_tokenize('Error PR-E2091 means') == ['error', 'pr-e2091', 'means']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `whitespace_tokenize` from the project's `cited_answers.domain.retrieval` (The naive tokenizer: split on spaces only. `PR-E2091` stays one token and a bare `E2091` never matches it.).

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 105 to 114:

```python
def test_bm25_finds_the_chunk_with_the_rare_term_and_ignores_chunks_without_any_query_term():
    chunks = [
        chunk("a:0", "Standard shipping takes three days."),
        chunk("b:0", "Error PR-E2091 means no label could be created."),
        chunk("c:0", "Gift cards never expire."),
    ]
    index = Bm25Index(chunks)
    assert [i for i, _ in index.search("What's E2091 about?", 5)] == ["b:0"]
    assert index.search("zebra", 5) == []
    assert index.search("shipping gift cards", 2)[0][1] > 0
```

- Defines the function `test_bm25_finds_the_chunk_with_the_rare_term_and_ignores_chunks_without_any_query_term`.
- It takes no parameters.
- Stores a list of 3 item(s) under the name `chunks`.
  - `chunk` from the project's `tests.conftest`.
- Stores the result of calling `Bm25Index` under the name `index`.
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
- Checks that `[i for i, _ in index.search("What's E2091 about?", 5)] == ['b:0']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.search(...)` looks for a regular expression anywhere in text.
- Checks that `index.search('zebra', 5) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.search(...)` looks for a regular expression anywhere in text.
- Checks that `index.search('shipping gift cards', 2)[0][1] > 0` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.search(...)` looks for a regular expression anywhere in text.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 117 to 128:

```python
def test_the_whitespace_tokenizer_misses_the_bare_code_that_the_hyphen_aware_one_finds():
    chunks = [chunk("b:0", "Error PR-E2091 means no label could be created."), chunk("c:0", "Other text here.")]
    assert Bm25Index(chunks, tokenizer=whitespace_tokenize).search("What's E2091 about?", 5) == []
    assert Bm25Index(chunks).search("What's E2091 about?", 5)[0][0] == "b:0"


def test_an_empty_index_returns_nothing():
    assert Bm25Index([]).search("anything", 5) == []


def test_cosine_of_parallel_orthogonal_and_zero_vectors():
    assert cosine([1, 2], [2, 4]) == pytest.approx(1.0)
```

- Defines the function `test_the_whitespace_tokenizer_misses_the_bare_code_that_the_hyphen_aware_one_finds`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `chunks`.
  - `chunk` from the project's `tests.conftest`.
- Checks that `Bm25Index(chunks, tokenizer=whitespace_tokenize).search("What's E2091 about?"...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.search(...)` looks for a regular expression anywhere in text.
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
- Checks that `Bm25Index(chunks).search("What's E2091 about?", 5)[0][0] == 'b:0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.search(...)` looks for a regular expression anywhere in text.
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
- Defines the function `test_an_empty_index_returns_nothing`.
- It takes no parameters.
- Checks that `Bm25Index([]).search('anything', 5) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.search(...)` looks for a regular expression anywhere in text.
  - `Bm25Index` from the project's `cited_answers.domain.retrieval` (Okapi BM25 over chunk text (heading path included).).
- Defines the function `test_cosine_of_parallel_orthogonal_and_zero_vectors`.
- It takes no parameters.
- Checks that `cosine([1, 2], [2, 4]) == pytest.approx(1.0)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
  - `pytest.approx` compares numbers with a small tolerance.

`tests/unit/domain/test_pages_chunking_retrieval.py`, lines 129 to 142:

```python
    assert cosine([1, 0], [0, 1]) == 0.0
    assert cosine([0, 0], [1, 1]) == 0.0


def test_fusion_adds_reciprocal_ranks_so_a_chunk_in_both_lists_wins():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["c", "d"]], k=60, top=3)
    assert fused[0][0] == "c"
    assert fused[0][1] == pytest.approx(1 / 63 + 1 / 61)
    assert [i for i, _ in fused] == ["c", "a", "b"]


def test_fusion_keeps_a_chunk_that_only_one_list_found():
    ids = [i for i, _ in reciprocal_rank_fusion([["x"], ["y", "z"]], top=5)]
    assert set(ids) == {"x", "y", "z"}
```

- Checks that `cosine([1, 0], [0, 1]) == 0.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
- Checks that `cosine([0, 0], [1, 1]) == 0.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `cosine` from the project's `cited_answers.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
- Defines the function `test_fusion_adds_reciprocal_ranks_so_a_chunk_in_both_lists_wins`.
- It takes no parameters.
- Stores the result of calling `reciprocal_rank_fusion` under the name `fused`.
  - `reciprocal_rank_fusion` from the project's `cited_answers.domain.retrieval` (Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up.).
- Checks that `fused[0][0] == 'c'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `fused[0][1] == pytest.approx(1 / 63 + 1 / 61)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
  - `+` is add.
  - `/` is divide.
- Checks that `[i for i, _ in fused] == ['c', 'a', 'b']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_fusion_keeps_a_chunk_that_only_one_list_found`.
- It takes no parameters.
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `reciprocal_rank_fusion` from the project's `cited_answers.domain.retrieval` (Reciprocal rank fusion: a chunk scores 1 / (k + rank) in each list it appears in, and the scores add up.).
- Checks that `set(ids) == {'x', 'y', 'z'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `set` makes a set: a collection with no repeated items.

### `tests/unit/infrastructure/test_anthropic_chat.py`

124 non-blank lines; it defines `message`, `adapter`, `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, `test_a_schema_goes_into_output_config_format_not_a_forced_tool`, `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`, `test_tool_use_blocks_in_the_response_become_tool_calls`, `test_other_stop_reasons_are_mapped`, `test_rate_limits_and_server_errors_are_transient`, `test_a_bad_request_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 1 to 13:

```python
import json

import anthropic
import httpx2
import pytest

from cited_answers.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from cited_answers.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from cited_answers.infrastructure.anthropic_chat import AnthropicChatModel
from tests.conftest import FixedClock


def message(content, stop="end_turn", tokens_in=21, tokens_out=6):
```

- Makes the module `json` (standard library) available.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx2` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `cited_answers.domain.llm`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.) from the project module `cited_answers.infrastructure.anthropic_chat`.
- Brings in `FixedClock` (A clock that only moves when a test says so.) from the project module `tests.conftest`.
- Defines the function `message`.
- Its parameters:
    - `content`.
    - `stop`; if the caller leaves it out it is the text `end_turn`.
    - `tokens_in`; if the caller leaves it out it is the number `21`.
    - `tokens_out`; if the caller leaves it out it is the number `6`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 14 to 26:

```python
    return httpx2.Response(
        200,
        json={
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": content,
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out},
        },
    )
```

- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 29 to 39:

```python
def adapter(handler, thinking="disabled"):
    client = anthropic.Anthropic(
        api_key="test-key-not-real",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, "claude-haiku-5-5", FixedClock(), thinking)


def test_text_usage_stop_reason_and_model_come_from_the_response():
    seen = {}
```

- Defines the function `adapter`.
- Its parameters:
    - `handler`.
    - `thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
  - `anthropic.DefaultHttpxClient` from the installed package module `anthropic`.
  - `httpx2.MockTransport` from the installed package module `httpx2`.
- Ends the function and gives back the result of calling `AnthropicChatModel` to the caller.
  - `AnthropicChatModel` from the project's `cited_answers.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so.).
- Defines the function `test_text_usage_stop_reason_and_model_come_from_the_response`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 41 to 53:

```python
    def handler(request):
        seen["body"] = json.loads(request.content)
        return message([{"type": "text", "text": "hello"}])

    response = adapter(handler).complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=40)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 21, 6)
    assert response.stop_reason is StopReason.END
    assert response.model == "claude-haiku-5-5"
    assert seen["body"]["system"] == "be brief"
    assert seen["body"]["max_tokens"] == 40
    assert seen["body"]["thinking"] == {"type": "disabled"}
```

- Defines the function `handler`.
- Its parameters:
    - `request`.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `message` to the caller.
  - `message`, a function of this file.
- Stores the result of calling `adapter(handler).complete` under the name `response`.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['body']['system'] == 'be brief'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['max_tokens'] == 40` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['thinking'] == {'type': 'disabled'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 54 to 67:

```python
    assert "temperature" not in seen["body"]
    assert "top_p" not in seen["body"]


def test_sampling_is_refused_because_the_messages_api_rejects_it():
    model = adapter(lambda r: message([]))
    assert not model.supports_sampling
    with pytest.raises(UnsupportedParameter, match="temperature"):
        model.complete(ChatRequest((ChatMessage.user("hi"),), temperature=0.0))
    with pytest.raises(UnsupportedParameter):
        model.complete(ChatRequest((ChatMessage.user("hi"),), top_p=0.9))


def test_thinking_can_be_left_out_or_set_to_between_tools():
```

- Checks that `'temperature' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'top_p' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_sampling_is_refused_because_the_messages_api_rejects_it`.
- It takes no parameters.
- Stores the result of calling `adapter` under the name `model`.
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter, match='temperature')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the function `test_thinking_can_be_left_out_or_set_to_between_tools`.
- It takes no parameters.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 68 to 79:

```python
    assert "thinking" not in adapter(lambda r: message([]), "omit").build_payload(ChatRequest((ChatMessage.user("x"),)))
    payload = adapter(lambda r: message([]), "between_tools").build_payload(ChatRequest((ChatMessage.user("x"),)))
    assert payload["thinking"] == {"type": "between_tools"}


def test_a_schema_goes_into_output_config_format_not_a_forced_tool():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    payload = adapter(lambda r: message([])).build_payload(
        ChatRequest((ChatMessage.user("x"),), response_schema=schema)
    )
    assert payload["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "tool_choice" not in payload
```

- Checks that `'thinking' not in adapter(lambda r: message([]), 'omit').build_payload(ChatRe...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `build_payload` of `adapter(lambda r: message([]), 'omit')`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Stores the result of calling `adapter(lambda r: message([]), 'between_tools')...` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]), 'betwe...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['thinking'] == {'type': 'between_tools'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_goes_into_output_config_format_not_a_forced_tool`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['output_config'] == {'format': {'type': 'json_schema', 'schema': sche...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'tool_choice' not in payload` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 82 to 93:

```python
def test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks():
    history = (
        ChatMessage.user("book it"),
        ChatMessage(
            Role.ASSISTANT, "checking", (ToolCall("t1", "slots", {"day": "mon"}), ToolCall("t2", "get", {"id": 1}))
        ),
        ChatMessage(Role.TOOL, "free", tool_call_id="t1"),
        ChatMessage(Role.TOOL, "event", tool_call_id="t2"),
    )
    spec = ToolSpec("slots", "find slots", {"type": "object"})
    payload = adapter(lambda r: message([])).build_payload(ChatRequest(history, tools=(spec,)))
    assert payload["tools"] == [{"name": "slots", "description": "find slots", "input_schema": {"type": "object"}}]
```

- Defines the function `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`.
- It takes no parameters.
- Stores a tuple of 4 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `cited_answers.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `cited_answers.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `payload['tools'] == [{'name': 'slots', 'description': 'find slots', 'input_sc...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 94 to 107:

```python
    assistant = payload["messages"][1]["content"]
    assert [b["type"] for b in assistant] == ["text", "tool_use", "tool_use"]
    results = payload["messages"][2]
    assert results["role"] == "user"
    assert [b["tool_use_id"] for b in results["content"]] == ["t1", "t2"]
    assert len(payload["messages"]) == 3


def test_tool_use_blocks_in_the_response_become_tool_calls():
    content = [
        {"type": "text", "text": "ok"},
        {"type": "tool_use", "id": "tu1", "name": "slots", "input": {"day": "tue"}},
    ]
    response = adapter(lambda r: message(content, "tool_use")).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Stores the part of `payload['messages'][1]` picked by `'content'` under the name `assistant`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['type'] for b in assistant] == ['text', 'tool_use', 'tool_use']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `payload['messages']` picked by `2` under the name `results`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `results['role'] == 'user'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['tool_use_id'] for b in results['content']] == ['t1', 't2']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `len(payload['messages']) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_use_blocks_in_the_response_become_tool_calls`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `content`.
- Stores the result of calling `adapter(lambda r: message(content, 'tool_use'))...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message(content, 't...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 108 to 120:

```python
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("tu1", "slots", {"day": "tue"}),)


@pytest.mark.parametrize(
    ("stop", "expected"),
    [("max_tokens", StopReason.LENGTH), ("refusal", StopReason.REFUSAL), ("pause_turn", StopReason.OTHER)],
)
def test_other_stop_reasons_are_mapped(stop, expected):
    response = adapter(lambda r: message([{"type": "text", "text": "x"}], stop)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is expected
```

- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('tu1', 'slots', {'day': 'tue'}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
- Defines the function `test_other_stop_reasons_are_mapped`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `stop`.
    - `expected`.
- Stores the result of calling `adapter(lambda r: message([{'type': 'text', 'te...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message([{'type': '...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `response.stop_reason is expected` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 123 to 134:

```python
@pytest.mark.parametrize("status", [429, 500, 529])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        adapter(
            lambda r: httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "y"}})
        ).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_bad_request_is_permanent():
    body = {"type": "error", "error": {"type": "invalid_request_error", "message": "nope"}}
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        adapter(lambda r: httpx2.Response(400, json=body)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(sta...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(sta...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.
- Defines the function `test_a_bad_request_is_permanent`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `body`.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(400...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(400...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 137 to 148:

```python
def test_a_dropped_connection_is_transient():
    def handler(request):
        raise httpx2.ConnectError("refused", request=request)

    with pytest.raises(TransientModelError):
        adapter(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_count_tokens_asks_the_provider_without_generating():
    seen = {}

    def handler(request):
```

- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.
- Defines the function `handler`.
- Its parameters:
    - `request`.
- Raises an error: the result of calling `httpx2.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx2.ConnectError` from the installed package module `httpx2`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_count_tokens_asks_the_provider_without_generating`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.
- Defines the function `handler`.
- Its parameters:
    - `request`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 149 to 157:

```python
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json={"input_tokens": 17})

    count = adapter(handler).count_tokens(ChatRequest((ChatMessage.user("hi"),), system="s"))
    assert count == 17
    assert seen["path"].endswith("/messages/count_tokens")
    assert "max_tokens" not in seen["body"]
    assert "thinking" not in seen["body"]
```

- Stores the `path` of `request.url` under the name `seen['path']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.
- Stores the result of calling `adapter(handler).count_tokens` under the name `count`.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `count == 17` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['path'].endswith('/messages/count_tokens')` is true; if it is not, the test fails with an `AssertionError`.
  - `.endswith(...)` asks whether text ends with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'max_tokens' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'thinking' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/unit/infrastructure/test_embeddings_stores_files.py`

169 non-blank lines; it defines `embedder`, `reply`, `test_the_embedder_posts_the_texts_and_returns_vectors_in_input_order`, `test_rate_limits_and_server_errors_are_transient`, `test_a_client_error_a_dropped_connection_and_a_bad_shape_are_told_apart`, `test_recorded_vectors_survive_a_round_trip_through_the_file`, `test_a_known_text_is_not_sent_to_the_live_embedder_again`, `test_an_unrecorded_text_names_itself_and_the_fix`, `test_a_folder_of_embedding_files_is_one_store`, `test_the_memory_store_ranks_by_cosine_and_reports_similarities`, `test_pgvectors_text_form_is_a_bracketed_comma_list`, `test_page_files_are_read_from_a_folder`, ....

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 1 to 11:

```python
import json
from datetime import date
from typing import Any

import httpx
import pytest

from cited_answers.domain.errors import PermanentModelError, RecordingMissing, TransientModelError
from cited_answers.domain.evaluation import InvalidQuestions, QuestionType
from cited_answers.domain.pages import PageStatus
from cited_answers.domain.prompts import PromptNotFound
```

- Makes the module `json` (standard library) available.
- Brings in `date` from the standard library module `datetime`.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `InvalidQuestions` (The question file breaks a rule of the lesson.), `QuestionType` (Answerable (a gold page), exact (hinges on a code or number, a gold page) or unanswerable.) from the project module `cited_answers.domain.evaluation`.
- Brings in `PageStatus` (Only `current` pages are indexed. A `retired` page may contradict a current one.) from the project module `cited_answers.domain.pages`.
- Brings in `PromptNotFound` (No prompt file for that name and version, or the file's version line does not match.) from the project module `cited_answers.domain.prompts`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 12 to 25:

```python
from cited_answers.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
    text_key,
)
from cited_answers.infrastructure.env import ConfigurationError
from cited_answers.infrastructure.files import (
    FilePageSource,
    FilePromptStore,
    FileQuestionSource,
    read_threshold,
)
```

- Brings in `EmbeddingStore` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.), `OpenAICompatibleEmbedder` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.), `RecordedEmbedder` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.), `RecordingEmbedder` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.), `text_key` (The recording key of a text: its SHA-256. The model name is not part of it.) from the project module `cited_answers.infrastructure.embeddings`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `cited_answers.infrastructure.env`.
- Brings in `FilePageSource` (Every `*.md` file in a folder is a page.), `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.), `FileQuestionSource` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.), `read_threshold` (The tuned refusal threshold, if `evals/threshold.json` exists.) from the project module `cited_answers.infrastructure.files`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 26 to 39:

```python
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.pg_store import vector_literal
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.wiring import build_embedder, build_store
from tests.conftest import PAGES, HashingEmbedder, chunk


def embedder(handler):
    return OpenAICompatibleEmbedder(
        httpx.Client(transport=httpx.MockTransport(handler)), "http://local/v1/", "nomic", "k"
    )


def reply(vectors):
```

- Brings in `InMemoryChunkStore` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.) from the project module `cited_answers.infrastructure.memory_store`.
- Brings in `vector_literal` (pgvector's text form of a vector: `[0.1,0.2,...]`.) from the project module `cited_answers.infrastructure.pg_store`.
- Brings in `AppSettings` (Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable.) from the project module `cited_answers.infrastructure.settings`.
- Brings in `build_embedder` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).), `build_store` (The in-memory store, or Postgres with pgvector.) from the project module `cited_answers.infrastructure.wiring`.
- Brings in `PAGES`, `HashingEmbedder` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.), `chunk` from the project module `tests.conftest`.
- Defines the function `embedder`.
- Its parameters:
    - `handler`.
- Ends the function and gives back the result of calling `OpenAICompatibleEmbedder` to the caller.
  - `OpenAICompatibleEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.).
  - `httpx.Client` makes an HTTP client.
  - `httpx.MockTransport` from the installed package module `httpx`.
- Defines the function `reply`.
- Its parameters:
    - `vectors`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 40 to 52:

```python
    return httpx.Response(
        200, json={"data": [{"index": i, "embedding": v} for i, v in reversed(list(enumerate(vectors)))]}
    )


def test_the_embedder_posts_the_texts_and_returns_vectors_in_input_order():
    seen: dict[str, Any] = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return reply([[1.0, 0.0], [0.0, 1.0]])
```

- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `reversed` walks a sequence from the end to the start.
  - `list` makes a list (a copy when given a collection).
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Defines the function `test_the_embedder_posts_the_texts_and_returns_vectors_in_input_order`.
- It takes no parameters.
- Declares `seen` as a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `handler`.
- Its parameters:
    - `request`.
- Stores the result of calling `str` under the name `seen['url']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `str` turns a value into text.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Stores the part of `request.headers` picked by `'authorization'` under the name `seen['auth']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `reply` to the caller.
  - `reply`, a function of this file.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 54 to 65:

```python
    vectors = embedder(handler).embed(["a", "b"])
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert seen["url"] == "http://local/v1/embeddings"
    assert seen["body"] == {"model": "nomic", "input": ["a", "b"]}
    assert seen["auth"] == "Bearer k"
    assert embedder(handler).name == "nomic"


@pytest.mark.parametrize("status", [429, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        embedder(lambda r: httpx.Response(status)).embed(["a"])
```

- Stores the result of calling `embedder(handler).embed` under the name `vectors`.
  - The method `embed` of `embedder(handler)`.
  - `embedder`, a function of this file.
- Checks that `vectors == [[1.0, 0.0], [0.0, 1.0]]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['url'] == 'http://local/v1/embeddings'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body'] == {'model': 'nomic', 'input': ['a', 'b']}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['auth'] == 'Bearer k'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `embedder(handler).name == 'nomic'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `embedder`, a function of this file.
- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `embed` of `embedder(lambda r: httpx.Response(sta...` with 1 argument(s); the result is not kept.
  - The method `embed` of `embedder(lambda r: httpx.Response(sta...`.
  - `embedder`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.Response` from the installed package module `httpx`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 68 to 79:

```python
def test_a_client_error_a_dropped_connection_and_a_bad_shape_are_told_apart():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        embedder(lambda r: httpx.Response(400, text="no")).embed(["a"])

    def refuse(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        embedder(refuse).embed(["a"])
    with pytest.raises(PermanentModelError, match="unexpected embeddings response"):
        embedder(lambda r: httpx.Response(200, json={"nope": 1})).embed(["a"])
    with pytest.raises(PermanentModelError, match="asked for 2"):
```

- Defines the function `test_a_client_error_a_dropped_connection_and_a_bad_shape_are_told_apart`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `embed` of `embedder(lambda r: httpx.Response(400...` with 1 argument(s); the result is not kept.
  - The method `embed` of `embedder(lambda r: httpx.Response(400...`.
  - `embedder`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `refuse`.
- Its parameters:
    - `request`.
- Raises an error: the result of calling `httpx.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx.ConnectError` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match='ConnectError')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `embed` of `embedder(refuse)` with 1 argument(s); the result is not kept.
  - The method `embed` of `embedder(refuse)`.
  - `embedder`, a function of this file.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='unexpected embe...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `embed` of `embedder(lambda r: httpx.Response(200...` with 1 argument(s); the result is not kept.
  - The method `embed` of `embedder(lambda r: httpx.Response(200...`.
  - `embedder`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.Response` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='asked for 2')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 80 to 93:

```python
        embedder(lambda r: reply([[1.0]])).embed(["a", "b"])


def test_recorded_vectors_survive_a_round_trip_through_the_file(tmp_path):
    path = tmp_path / "e.jsonl"
    recorder = RecordingEmbedder(HashingEmbedder(8), EmbeddingStore(path))
    first = recorder.embed(["hello world", "hello world", "other"])
    assert first[0] == first[1]
    replay = RecordedEmbedder(EmbeddingStore(path), "nomic")
    again = replay.embed(["hello world", "other"])
    assert again[0] == pytest.approx(first[0], rel=1e-6)
    assert replay.name == "nomic"
    assert recorder.name == "hashing"
    assert len(EmbeddingStore(path)) == 2
```

- Calls the method `embed` of `embedder(lambda r: reply([[1.0]]))` with 1 argument(s); the result is not kept.
  - The method `embed` of `embedder(lambda r: reply([[1.0]]))`.
  - `embedder`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `reply`, a function of this file.
- Defines the function `test_recorded_vectors_survive_a_round_trip_through_the_file`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'e.jsonl'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `RecordingEmbedder` under the name `recorder`.
  - `RecordingEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.).
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Stores the result of calling `recorder.embed` under the name `first`.
  - The method `embed` of `recorder`.
- Checks that `first[0] == first[1]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `RecordedEmbedder` under the name `replay`.
  - `RecordedEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Stores the result of calling `replay.embed` under the name `again`.
  - The method `embed` of `replay`.
- Checks that `again[0] == pytest.approx(first[0], rel=1e-06)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
- Checks that `replay.name == 'nomic'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `recorder.name == 'hashing'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `len(EmbeddingStore(path)) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 96 to 106:

```python
def test_a_known_text_is_not_sent_to_the_live_embedder_again(tmp_path):
    live = HashingEmbedder(8)
    recorder = RecordingEmbedder(live, EmbeddingStore(tmp_path / "e.jsonl"))
    recorder.embed(["a", "b"])
    recorder.embed(["a", "c"])
    assert live.calls == [["a", "b"], ["c"]]


def test_an_unrecorded_text_names_itself_and_the_fix(tmp_path):
    with pytest.raises(RecordingMissing, match=r"starting 'zzz'.*make record"):
        RecordedEmbedder(EmbeddingStore(tmp_path / "none.jsonl")).embed(["zzz"])
```

- Defines the function `test_a_known_text_is_not_sent_to_the_live_embedder_again`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `HashingEmbedder` under the name `live`.
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
- Stores the result of calling `RecordingEmbedder` under the name `recorder`.
  - `RecordingEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
  - `/` is divide.
- Calls the method `embed` of `recorder` with 1 argument(s); the result is not kept.
  - The method `embed` of `recorder`.
- Calls the method `embed` of `recorder` with 1 argument(s); the result is not kept.
  - The method `embed` of `recorder`.
- Checks that `live.calls == [['a', 'b'], ['c']]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_an_unrecorded_text_names_itself_and_the_fix`.
- Its parameters:
    - `tmp_path`.
- A `with` block: it sets up `pytest.raises(RecordingMissing, match="starting 'zzz'.*ma...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `embed` of `RecordedEmbedder(EmbeddingStore(tmp_p...` with 1 argument(s); the result is not kept.
  - The method `embed` of `RecordedEmbedder(EmbeddingStore(tmp_p...`.
  - `RecordedEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
  - `/` is divide.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 109 to 120:

```python
def test_a_folder_of_embedding_files_is_one_store(tmp_path):
    for name, text in (("one.jsonl", "x"), ("two.jsonl", "y")):
        RecordingEmbedder(HashingEmbedder(4), EmbeddingStore(tmp_path / name)).embed([text])
    store = EmbeddingStore(tmp_path)
    assert store.get(text_key("x")) is not None
    assert store.get(text_key("y")) is not None


def test_the_memory_store_ranks_by_cosine_and_reports_similarities():
    store = InMemoryChunkStore()
    store.replace_all([chunk("a:0", "x"), chunk("b:0", "y")], [[1.0, 0.0], [0.0, 1.0]])
    assert store.vector_search([1.0, 0.1], 2)[0][0] == "a:0"
```

- Defines the function `test_a_folder_of_embedding_files_is_one_store`.
- Its parameters:
    - `tmp_path`.
- Loop: the indented lines below run once for each item of `(('one.jsonl', 'x'), ('two.jsonl', 'y'))`; `(name, text)` names the current item.
- Calls the method `embed` of `RecordingEmbedder(HashingEmbedder(4),...` with 1 argument(s); the result is not kept.
  - The method `embed` of `RecordingEmbedder(HashingEmbedder(4),...`.
  - `RecordingEmbedder` from the project's `cited_answers.infrastructure.embeddings` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.).
  - `HashingEmbedder` from the project's `tests.conftest` (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
  - `/` is divide.
- Stores the result of calling `EmbeddingStore` under the name `store`.
  - `EmbeddingStore` from the project's `cited_answers.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Checks that `store.get(text_key('x')) is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `text_key` from the project's `cited_answers.infrastructure.embeddings` (The recording key of a text: its SHA-256. The model name is not part of it.).
- Checks that `store.get(text_key('y')) is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `text_key` from the project's `cited_answers.infrastructure.embeddings` (The recording key of a text: its SHA-256. The model name is not part of it.).
- Defines the function `test_the_memory_store_ranks_by_cosine_and_reports_similarities`.
- It takes no parameters.
- Stores the result of calling `InMemoryChunkStore` under the name `store`.
  - `InMemoryChunkStore` from the project's `cited_answers.infrastructure.memory_store` (Chunks and vectors in lists; search is a linear scan, which is plenty for a help center.).
- Calls the method `replace_all` of `store` with 2 argument(s); the result is not kept.
  - The method `replace_all` of `store`.
  - `chunk` from the project's `tests.conftest`.
- Checks that `store.vector_search([1.0, 0.1], 2)[0][0] == 'a:0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `vector_search` of `store`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 121 to 134:

```python
    assert store.similarities([1.0, 0.0], ["b:0", "a:0", "zzz"]) == {"b:0": 0.0, "a:0": 1.0}
    assert [c.id for c in store.chunks()] == ["a:0", "b:0"]
    with pytest.raises(ValueError, match="one vector per chunk"):
        store.replace_all([chunk("a:0", "x")], [])


def test_pgvectors_text_form_is_a_bracketed_comma_list():
    assert vector_literal([1.0, 0.25, -3.5]) == "[1,0.25,-3.5]"


def test_page_files_are_read_from_a_folder(tmp_path):
    (tmp_path / "a.md").write_text(
        "---\nid: a\ntitle: A\nupdated: 2026-01-02\nstatus: retired\n---\n# A\n\n## S\n\nText here.\n"
    )
```

- Checks that `store.similarities([1.0, 0.0], ['b:0', 'a:0', 'zzz']) == {'b:0': 0.0, 'a:0': ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `similarities` of `store`.
- Checks that `[c.id for c in store.chunks()] == ['a:0', 'b:0']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `chunks` of `store`.
- A `with` block: it sets up `pytest.raises(ValueError, match='one vector per chunk')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `replace_all` of `store` with 2 argument(s); the result is not kept.
  - The method `replace_all` of `store`.
  - `chunk` from the project's `tests.conftest`.
- Defines the function `test_pgvectors_text_form_is_a_bracketed_comma_list`.
- It takes no parameters.
- Checks that `vector_literal([1.0, 0.25, -3.5]) == '[1,0.25,-3.5]'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `vector_literal` from the project's `cited_answers.infrastructure.pg_store` (pgvector's text form of a vector: `[0.1,0.2,...]`.).
- Defines the function `test_page_files_are_read_from_a_folder`.
- Its parameters:
    - `tmp_path`.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `/` is divide.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 135 to 148:

```python
    (page,) = FilePageSource(tmp_path).pages()
    assert (page.id, page.status, page.updated) == ("a", PageStatus.RETIRED, date(2026, 1, 2))


def test_the_real_help_center_has_sixty_pages_three_retired_and_ten_error_codes():
    from pathlib import Path

    pages = FilePageSource(Path(__file__).resolve().parents[3] / "data" / "pages").pages()
    assert len(pages) == 60
    assert sorted(p.id for p in pages if p.status is PageStatus.RETIRED) == [
        "p-return-fee-old",
        "p-return-window-old",
        "p-ship-costs-old",
    ]
```

- Stores the result of calling `FilePageSource(tmp_path).pages` under the name `(page,)`.
  - The method `pages` of `FilePageSource(tmp_path)`.
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
- Checks that `(page.id, page.status, page.updated) == ('a', PageStatus.RETIRED, date(2026, ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `date` from the standard library module `datetime`.
- Defines the function `test_the_real_help_center_has_sixty_pages_three_retired_and_ten_error_codes`.
- It takes no parameters.
- Brings in `Path` from the standard library module `pathlib`.
- Stores the result of calling `FilePageSource(Path(__file__).resolve().parents...` under the name `pages`.
  - The method `pages` of `FilePageSource(Path(__file__).resolve...`.
  - `FilePageSource` from the project's `cited_answers.infrastructure.files` (Every `*.md` file in a folder is a page.).
  - `/` is divide.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Checks that `len(pages) == 60` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `sorted((p.id for p in pages if p.status is PageStatus.RETIRED)) == ['p-return...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 149 to 161:

```python
    assert sum(p.id.startswith("p-error-") for p in pages) == 10
    assert all(p.sections for p in pages)


def test_questions_are_read_per_split_and_a_bad_line_is_reported_with_its_number(tmp_path):
    good = {"id": "q1", "type": "exact", "question": "What?", "gold_page": "p", "fact": "f", "near_miss": False}
    (tmp_path / "dev.jsonl").write_text(json.dumps(good) + "\n\n" + '{"id": "q2", "type": "nonsense"}\n')
    source = FileQuestionSource(tmp_path)
    with pytest.raises(InvalidQuestions, match=r"dev\.jsonl:3"):
        source.load("dev")
    (tmp_path / "dev.jsonl").write_text(json.dumps(good) + "\n")
    (question,) = source.load("dev")
    assert question.type is QuestionType.EXACT
```

- Checks that `sum((p.id.startswith('p-error-') for p in pages)) == 10` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.startswith(...)` asks whether text begins with the given text.
- Checks that `all((p.sections for p in pages))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_questions_are_read_per_split_and_a_bad_line_is_reported_with_its_number`.
- Its parameters:
    - `tmp_path`.
- Stores a dictionary with 6 entries under the name `good`.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `+` is add.
  - `/` is divide.
  - `json.dumps` turns Python data into JSON text.
- Stores the result of calling `FileQuestionSource` under the name `source`.
  - `FileQuestionSource` from the project's `cited_answers.infrastructure.files` (`<folder>/<split>.jsonl`, one question per line; a bad line is reported with its number.).
- A `with` block: it sets up `pytest.raises(InvalidQuestions, match='dev\\.jsonl:3')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `load` of `source` with 1 argument(s); the result is not kept.
  - The method `load` of `source`.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `+` is add.
  - `/` is divide.
  - `json.dumps` turns Python data into JSON text.
- Stores the result of calling `source.load` under the name `(question,)`.
  - The method `load` of `source`.
- Checks that `question.type is QuestionType.EXACT` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 164 to 174:

```python
def test_prompt_files_need_a_matching_version_line(tmp_path):
    folder = tmp_path / "answer"
    folder.mkdir()
    (folder / "v1.md").write_text("---\nversion: v1\n---\nBe brief.\n")
    (folder / "v2.md").write_text("---\nversion: v9\n---\nx\n")
    (folder / "v3.md").write_text("no front matter")
    store = FilePromptStore(tmp_path)
    assert store.load("answer", "v1").text == "Be brief."
    for version, message in (("v2", "says 'v9'"), ("v3", "front matter"), ("v4", "no prompt file")):
        with pytest.raises(PromptNotFound, match=message):
            store.load("answer", version)
```

- Defines the function `test_prompt_files_need_a_matching_version_line`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'answer'` under the name `folder`.
  - `/` is divide.
- Calls `.mkdir(...)` creates a folder; the result is not kept.
  - `.mkdir(...)` creates a folder.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `/` is divide.
- Stores the result of calling `FilePromptStore` under the name `store`.
  - `FilePromptStore` from the project's `cited_answers.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
- Checks that `store.load('answer', 'v1').text == 'Be brief.'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `load` of `store`.
- Loop: the indented lines below run once for each item of `(('v2', "says 'v9'"), ('v3', 'front matter'), ('v4', 'no ...`; `(version, message)` names the current item.
- A `with` block: it sets up `pytest.raises(PromptNotFound, match=message)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `load` of `store` with 2 argument(s); the result is not kept.
  - The method `load` of `store`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 177 to 188:

```python
def test_the_threshold_file_is_optional(tmp_path):
    assert read_threshold(tmp_path / "none.json") is None
    (tmp_path / "t.json").write_text('{"threshold": 0.61}')
    assert read_threshold(tmp_path / "t.json") == 0.61


def test_settings_have_defaults_and_validate(tmp_path):
    settings = AppSettings.from_env({})
    assert settings.index_backend == "memory"
    assert settings.port == 8080
    assert settings.refusal_threshold is None
    assert AppSettings.from_env({"REFUSAL_THRESHOLD": "0.6", "LOG_LEVEL": "debug"}).refusal_threshold == 0.6
```

- Defines the function `test_the_threshold_file_is_optional`.
- Its parameters:
    - `tmp_path`.
- Checks that `read_threshold(tmp_path / 'none.json') is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `/` is divide.
- Checks that `read_threshold(tmp_path / 't.json') == 0.61` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `read_threshold` from the project's `cited_answers.infrastructure.files` (The tuned refusal threshold, if `evals/threshold.json` exists.).
  - `/` is divide.
- Defines the function `test_settings_have_defaults_and_validate`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `AppSettings.from_env` under the name `settings`.
  - The method `from_env` of `AppSettings`.
- Checks that `settings.index_backend == 'memory'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.port == 8080` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.refusal_threshold is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `AppSettings.from_env({'REFUSAL_THRESHOLD': '0.6', 'LOG_LEVEL': 'debug'}).refu...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_env` of `AppSettings`.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 189 to 202:

```python
    for bad, name in (
        ({"REFUSAL_THRESHOLD": "high"}, "REFUSAL_THRESHOLD"),
        ({"INDEX_BACKEND": "redis"}, "INDEX_BACKEND"),
        ({"HTTP_PORT": "0"}, "HTTP_PORT"),
        ({"EMBEDDER_PROVIDER": "x"}, "EMBEDDER_PROVIDER"),
    ):
        with pytest.raises(ConfigurationError, match=name):
            AppSettings.from_env(bad)


def test_wiring_builds_the_recorded_embedder_the_live_one_and_the_stores(tmp_path):
    from cited_answers.infrastructure.pg_store import PgVectorChunkStore

    recorded = build_embedder(AppSettings.from_env({"EMBEDDINGS_PATH": str(tmp_path)}), {})
```

- Loop: the indented lines below run once for each item of `(({'REFUSAL_THRESHOLD': 'high'}, 'REFUSAL_THRESHOLD'), ({...`; `(bad, name)` names the current item.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match=name)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `from_env` of `AppSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `AppSettings`.
- Defines the function `test_wiring_builds_the_recorded_embedder_the_live_one_and_the_stores`.
- Its parameters:
    - `tmp_path`.
- Brings in `PgVectorChunkStore` (Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index.) from the project module `cited_answers.infrastructure.pg_store`.
- Stores the result of calling `build_embedder` under the name `recorded`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
  - The method `from_env` of `AppSettings`.
  - `str` turns a value into text.

`tests/unit/infrastructure/test_embeddings_stores_files.py`, lines 203 to 213:

```python
    assert isinstance(recorded, RecordedEmbedder)
    live = build_embedder(AppSettings.from_env({"EMBEDDER_PROVIDER": "openai-compatible"}), {})
    assert isinstance(live, OpenAICompatibleEmbedder)
    recording = build_embedder(
        AppSettings.from_env({"EMBEDDER_PROVIDER": "openai-compatible", "EMBEDDINGS_PATH": str(tmp_path / "e.jsonl")}),
        {"RECORD": "on"},
    )
    assert isinstance(recording, RecordingEmbedder)
    assert isinstance(build_store(AppSettings.from_env({})), InMemoryChunkStore)
    assert isinstance(build_store(AppSettings.from_env({"INDEX_BACKEND": "pgvector"})), PgVectorChunkStore)
    assert PAGES
```

- Checks that `isinstance(recorded, RecordedEmbedder)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Stores the result of calling `build_embedder` under the name `live`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
  - The method `from_env` of `AppSettings`.
- Checks that `isinstance(live, OpenAICompatibleEmbedder)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Stores the result of calling `build_embedder` under the name `recording`.
  - `build_embedder` from the project's `cited_answers.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
  - The method `from_env` of `AppSettings`.
  - `str` turns a value into text.
  - `/` is divide.
- Checks that `isinstance(recording, RecordingEmbedder)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `isinstance(build_store(AppSettings.from_env({})), InMemoryChunkStore)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_store` from the project's `cited_answers.infrastructure.wiring` (The in-memory store, or Postgres with pgvector.).
  - The method `from_env` of `AppSettings`.
- Checks that `isinstance(build_store(AppSettings.from_env({'INDEX_BACKEND': 'pgvector'})), ...` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_store` from the project's `cited_answers.infrastructure.wiring` (The in-memory store, or Postgres with pgvector.).
  - The method `from_env` of `AppSettings`.
- Checks that `PAGES` is true; if it is not, the test fails with an `AssertionError`.

### `tests/unit/infrastructure/test_openai_compatible.py`

102 non-blank lines; it defines `model`, `ok`, `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, `test_tool_specs_calls_and_results_use_the_function_calling_shape`, `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`, `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`, `test_a_length_finish_reason_is_kept`, `test_rate_limits_and_server_errors_are_transient`, `test_a_client_error_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_openai_compatible.py`, lines 1 to 14:

```python
import json
from typing import Any

import httpx
import pytest

from cited_answers.domain.errors import PermanentModelError, TransientModelError
from cited_answers.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from cited_answers.infrastructure.openai_compatible import OpenAICompatibleChatModel
from tests.conftest import FixedClock


def model(handler, api_key=None):
    http = httpx.Client(transport=httpx.MockTransport(handler))
```

- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `cited_answers.domain.llm`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `cited_answers.infrastructure.openai_compatible`.
- Brings in `FixedClock` (A clock that only moves when a test says so.) from the project module `tests.conftest`.
- Defines the function `model`.
- Its parameters:
    - `handler`.
    - `api_key`; if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
  - `httpx.MockTransport` from the installed package module `httpx`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 15 to 21:

```python
    return OpenAICompatibleChatModel(http, "http://local/v1/", "small-model", FixedClock(), api_key)


def ok(content="hello", finish="stop", tool_calls=None, prompt_tokens=11, completion_tokens=3):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
```

- Ends the function and gives back the result of calling `OpenAICompatibleChatModel` to the caller.
  - `OpenAICompatibleChatModel` from the project's `cited_answers.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so.).
- Defines the function `ok`.
- Its parameters:
    - `content`; if the caller leaves it out it is the text `hello`.
    - `finish`; if the caller leaves it out it is the text `stop`.
    - `tool_calls`; if the caller leaves it out it is nothing (`None`).
    - `prompt_tokens`; if the caller leaves it out it is the number `11`.
    - `completion_tokens`; if the caller leaves it out it is the number `3`.
- Stores a dictionary with 2 entries under the name `message`.
- Decision: the indented lines below run only when `tool_calls` is true.
- Stores the value named `tool_calls` under the name `message['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 22 to 35:

```python
    return httpx.Response(
        200,
        json={
            "model": "small-model-0",
            "choices": [{"message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        },
    )


def test_a_reply_becomes_text_usage_stop_reason_and_latency():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
```

- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_reply_becomes_text_usage_stop_reason_and_latency`.
- It takes no parameters.
- Declares `seen` as a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 36 to 49:

```python
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        return ok()  # type: ignore[no-any-return]

    response = model(handler, api_key="k").complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=50, temperature=0.7, top_p=0.9)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 11, 3)
    assert response.stop_reason is StopReason.END
    assert response.latency_seconds == 0.25
    assert response.model == "small-model-0"
    assert seen["url"] == "http://local/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
```

- Stores the result of calling `str` under the name `seen['url']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `str` turns a value into text.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `request.headers.get` under the name `seen['auth']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `ok` to the caller.
  - `ok`, a function of this file.
- Stores the result of calling `model(handler, api_key='k').complete` under the name `response`.
  - The method `complete` of `model(handler, api_key='k')`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.latency_seconds == 0.25` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.model == 'small-model-0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['url'] == 'http://local/v1/chat/completions'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['auth'] == 'Bearer k'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 50 to 63:

```python
    assert seen["body"]["messages"][0] == {"role": "system", "content": "be brief"}
    assert (seen["body"]["max_tokens"], seen["body"]["temperature"], seen["body"]["top_p"]) == (50, 0.7, 0.9)


def test_unset_sampling_is_left_out_of_the_body():
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),)))
    assert "temperature" not in body
    assert "top_p" not in body
    assert body["model"] == "small-model"


def test_a_schema_becomes_a_json_schema_response_format():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),), response_schema=schema))
```

- Checks that `seen['body']['messages'][0] == {'role': 'system', 'content': 'be brief'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `(seen['body']['max_tokens'], seen['body']['temperature'], seen['body']['top_p...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_unset_sampling_is_left_out_of_the_body`.
- It takes no parameters.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `'temperature' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'top_p' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `body['model'] == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_becomes_a_json_schema_response_format`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 64 to 77:

```python
    assert body["response_format"]["json_schema"]["schema"] == schema
    assert body["response_format"]["type"] == "json_schema"


def test_tool_specs_calls_and_results_use_the_function_calling_shape():
    spec = ToolSpec("lookup", "find one", {"type": "object"})
    history = (
        ChatMessage.user("find 4"),
        ChatMessage(Role.ASSISTANT, "", (ToolCall("c1", "lookup", {"id": 4}),)),
        ChatMessage(Role.TOOL, '{"ok": true}', tool_call_id="c1"),
    )
    body = model(lambda r: ok()).build_payload(ChatRequest(history, tools=(spec,)))
    assert body["tools"][0]["function"]["name"] == "lookup"
    assert body["messages"][1]["tool_calls"][0]["function"]["arguments"] == '{"id": 4}'
```

- Checks that `body['response_format']['json_schema']['schema'] == schema` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['response_format']['type'] == 'json_schema'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_specs_calls_and_results_use_the_function_calling_shape`.
- It takes no parameters.
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `cited_answers.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores a tuple of 3 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `cited_answers.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `body['tools'][0]['function']['name'] == 'lookup'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['messages'][1]['tool_calls'][0]['function']['arguments'] == '{"id": 4}'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 78 to 91:

```python
    assert body["messages"][2] == {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'}


def test_tool_calls_in_the_reply_are_parsed_with_json_arguments():
    calls = [{"id": "c9", "function": {"name": "lookup", "arguments": '{"id": 7}'}}]
    response = model(lambda r: ok(content=None, finish="stop", tool_calls=calls)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("c9", "lookup", {"id": 7}),)
    assert response.text == ""


def test_arguments_may_already_be_an_object_and_missing_ids_are_numbered():
```

- Checks that `body['messages'][2] == {'role': 'tool', 'tool_call_id': 'c1', 'content': '{"o...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`.
- It takes no parameters.
- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(content=None, finish='stop',...` under the name `response`.
  - The method `complete` of `model(lambda r: ok(content=None, fini...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('c9', 'lookup', {'id': 7}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `cited_answers.domain.llm` (A tool call the model asked for.).
- Checks that `response.text == ''` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 92 to 102:

```python
    calls = [{"function": {"name": "lookup", "arguments": {"id": 1}}}]
    response = model(lambda r: ok(tool_calls=calls)).complete(ChatRequest((ChatMessage.user("x"),)))
    assert response.tool_calls[0].id == "call_0"
    assert response.tool_calls[0].arguments == {"id": 1}


def test_a_length_finish_reason_is_kept():
    assert (
        model(lambda r: ok(finish="length")).complete(ChatRequest((ChatMessage.user("x"),))).stop_reason
        is StopReason.LENGTH
    )
```

- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(tool_calls=calls)).complete` under the name `response`.
  - The method `complete` of `model(lambda r: ok(tool_calls=calls))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.tool_calls[0].id == 'call_0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `response.tool_calls[0].arguments == {'id': 1}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_length_finish_reason_is_kept`.
- It takes no parameters.
- Checks that `model(lambda r: ok(finish='length')).complete(ChatRequest((ChatMessage.user('...` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `complete` of `model(lambda r: ok(finish='length'))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 105 to 116:

```python
@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError, match=str(status)):
        model(lambda r: httpx.Response(status)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_client_error_is_permanent():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        model(lambda r: httpx.Response(400, text="bad")).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_dropped_connection_is_transient():
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match=str(status))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `str` turns a value into text.
- Calls the method `complete` of `model(lambda r: httpx.Response(status))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(status))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_client_error_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(400, t...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(400, t...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 117 to 129:

```python
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        model(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_an_unexpected_shape_is_permanent():
    with pytest.raises(PermanentModelError, match="unexpected response shape"):
        model(lambda r: httpx.Response(200, json={"choices": []})).complete(ChatRequest((ChatMessage.user("x"),)))
    bad_args = [{"id": "c", "function": {"name": "t", "arguments": "[1]"}}]
    with pytest.raises(PermanentModelError):
        model(lambda r: ok(tool_calls=bad_args)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.
- Raises an error: the result of calling `httpx.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx.ConnectError` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match='ConnectError')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(handler)`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_an_unexpected_shape_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='unexpected resp...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(200, j...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(200, j...`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Stores a list of 1 item(s) under the name `bad_args`.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: ok(tool_calls=bad_args))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: ok(tool_calls=bad_args))`.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 132 to 135:

```python
def test_the_model_reports_its_name_and_that_it_accepts_sampling():
    adapter = model(lambda r: ok())
    assert adapter.name == "small-model"
    assert adapter.supports_sampling
```

- Defines the function `test_the_model_reports_its_name_and_that_it_accepts_sampling`.
- It takes no parameters.
- Stores the result of calling `model` under the name `adapter`.
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `adapter.name == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `adapter.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

### `tests/unit/infrastructure/test_recording.py`

45 non-blank lines; it defines `request`, `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`, `test_a_folder_of_recordings_is_loaded_as_one_store`, `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.

`tests/unit/infrastructure/test_recording.py`, lines 1 to 12:

```python
import json

import pytest

from cited_answers.domain.errors import RecordingMissing
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from tests.conftest import ScriptedModel


def request(text="hi", tag="a"):
    return ChatRequest((ChatMessage.user(text),), max_output_tokens=10, tag=tag)
```

- Makes the module `json` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `cited_answers.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `cited_answers.domain.llm`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `cited_answers.infrastructure.recording`.
- Brings in `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Defines the function `request`.
- Its parameters:
    - `text`; if the caller leaves it out it is the text `hi`.
    - `tag`; if the caller leaves it out it is the text `a`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `cited_answers.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.

`tests/unit/infrastructure/test_recording.py`, lines 15 to 26:

```python
def test_recording_then_replaying_returns_the_same_response(tmp_path):
    path = tmp_path / "r.jsonl"
    live = ScriptedModel(lambda r: ("live answer", 12, 4))
    recorder = RecordingChatModel(live, RecordingStore(path), {"provider": "test"})
    first = recorder.complete(request())
    replay = RecordedChatModel(RecordingStore(path))
    assert replay.complete(request()) == first
    assert len(live.requests) == 1


def test_a_request_already_recorded_is_not_sent_again(tmp_path):
    live = ScriptedModel()
```

- Defines the function `test_recording_then_replaying_returns_the_same_response`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `recorder.complete` under the name `first`.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Checks that `replay.complete(request()) == first` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_request_already_recorded_is_not_sent_again`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).

`tests/unit/infrastructure/test_recording.py`, lines 27 to 38:

```python
    recorder = RecordingChatModel(live, RecordingStore(tmp_path / "r.jsonl"), {})
    recorder.complete(request())
    recorder.complete(request())
    assert len(live.requests) == 1


def test_an_unrecorded_request_names_the_tag_and_the_fix(tmp_path):
    replay = RecordedChatModel(RecordingStore(tmp_path / "missing.jsonl"))
    with pytest.raises(RecordingMissing, match=r"tag='zzz'.*make record"):
        replay.complete(request(tag="zzz"))
    assert replay.name == "recorded"
    assert replay.supports_sampling
```

- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_an_unrecorded_request_names_the_tag_and_the_fix`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- A `with` block: it sets up `pytest.raises(RecordingMissing, match="tag='zzz'.*make re...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `replay` with 1 argument(s); the result is not kept.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `replay.name == 'recorded'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `replay.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_recording.py`, lines 41 to 52:

```python
def test_the_note_about_what_produced_the_answer_is_kept_in_the_file(tmp_path):
    path = tmp_path / "r.jsonl"
    RecordingChatModel(ScriptedModel(), RecordingStore(path), {"provider": "test"}).complete(request())
    entry = json.loads(path.read_text().splitlines()[0])
    assert entry["recorded_with"] == {"provider": "test", "model": "scripted"}
    assert entry["tag"] == "a"


def test_a_folder_of_recordings_is_loaded_as_one_store(tmp_path):
    for name, text in (("one.jsonl", "q1"), ("two.jsonl", "q2")):
        RecordingChatModel(ScriptedModel(), RecordingStore(tmp_path / name), {}).complete(request(text))
    store = RecordingStore(tmp_path)
```

- Defines the function `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Checks that `entry['recorded_with'] == {'provider': 'test', 'model': 'scripted'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `entry['tag'] == 'a'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_folder_of_recordings_is_loaded_as_one_store`.
- Its parameters:
    - `tmp_path`.
- Loop: the indented lines below run once for each item of `(('one.jsonl', 'q1'), ('two.jsonl', 'q2'))`; `(name, text)` names the current item.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Stores the result of calling `RecordingStore` under the name `store`.
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).

`tests/unit/infrastructure/test_recording.py`, lines 53 to 61:

```python
    assert len(store) == 2
    RecordedChatModel(store).complete(request("q1"))
    RecordedChatModel(store).complete(request("q2"))


def test_the_recorder_reports_the_wrapped_models_name_and_sampling_support(tmp_path):
    recorder = RecordingChatModel(ScriptedModel(sampling=False), RecordingStore(tmp_path / "r.jsonl"), {})
    assert recorder.name == "scripted"
    assert not recorder.supports_sampling
```

- Checks that `len(store) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `cited_answers.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Defines the function `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `cited_answers.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `cited_answers.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Checks that `recorder.name == 'scripted'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `not recorder.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/unit --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/interfaces/test_http.py::test_info_logs_carry_a_hash_of_the_question_never_its_text

153 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/unit -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
........................................................................ [ 94%]
.........                                                                [100%]
153 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/unit/application/test_retrieve_answer_evaluate.py::test_ingest_indexes_current_pages_only_and_names_the_retired_ones
tests/unit/application/test_retrieve_answer_evaluate.py::test_ingest_logs_each_skipped_page
tests/unit/application/test_retrieve_answer_evaluate.py::test_a_search_for_the_old_return_window_returns_no_retired_chunk
tests/unit/application/test_retrieve_answer_evaluate.py::test_embedding_is_done_in_batches
tests/unit/application/test_retrieve_answer_evaluate.py::test_fused_retrieval_recovers_an_exact_code_that_only_keywords_find
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/unit/application/test_retrieve_answer_evaluate.py` test?

   *Answer:* It holds the tests for `retrieve answer evaluate`.

2. What does `tests/unit/domain/test_answering_and_evaluation.py` test?

   *Answer:* It holds the tests for `answering and evaluation`.

3. What does `tests/unit/domain/test_llm.py` test?

   *Answer:* It holds the tests for `llm`.

4. What does `tests/unit/domain/test_pages_chunking_retrieval.py` test?

   *Answer:* It holds the tests for `pages chunking retrieval`.

5. What does `tests/unit/infrastructure/test_anthropic_chat.py` test?

   *Answer:* It holds the tests for `anthropic chat`.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
