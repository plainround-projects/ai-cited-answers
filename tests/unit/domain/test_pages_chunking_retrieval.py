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
    chunks, skipped = chunk_current_pages(PAGES)
    assert skipped == ["p-return-window-old"]
    assert all(c.status is PageStatus.CURRENT for c in chunks)
    assert "p-return-window-old" not in {c.page_id for c in chunks}


def test_token_estimate_is_words_times_one_point_three():
    assert estimate_tokens("one two three four five six seven eight nine ten") == 13


def test_tokenizer_splits_codes_on_hyphens_so_the_bare_code_matches():
    assert tokenize("Error PR-E2091 means") == ["error", "pr", "e2091", "means"]
    assert whitespace_tokenize("Error PR-E2091 means") == ["error", "pr-e2091", "means"]


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


def test_the_whitespace_tokenizer_misses_the_bare_code_that_the_hyphen_aware_one_finds():
    chunks = [chunk("b:0", "Error PR-E2091 means no label could be created."), chunk("c:0", "Other text here.")]
    assert Bm25Index(chunks, tokenizer=whitespace_tokenize).search("What's E2091 about?", 5) == []
    assert Bm25Index(chunks).search("What's E2091 about?", 5)[0][0] == "b:0"


def test_an_empty_index_returns_nothing():
    assert Bm25Index([]).search("anything", 5) == []


def test_cosine_of_parallel_orthogonal_and_zero_vectors():
    assert cosine([1, 2], [2, 4]) == pytest.approx(1.0)
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
