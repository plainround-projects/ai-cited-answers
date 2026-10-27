"""The Postgres adapter and the HTTP service against the real pgvector container (`make up` first)."""

import os
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, Mode, ingest
from cited_answers.infrastructure.embeddings import EmbeddingStore, RecordedEmbedder
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.pg_store import PgVectorChunkStore
from cited_answers.infrastructure.recording import RecordedChatModel, RecordingStore
from cited_answers.interfaces.http import create_app

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[2]
DSN = os.environ.get("DATABASE_URL", "postgresql://cited:cited@localhost:55432/cited")


@pytest.fixture(scope="module")
def embedder():
    return RecordedEmbedder(EmbeddingStore(REPO / "tests" / "fixtures" / "embeddings"), "nomic-embed-text")


@pytest.fixture(scope="module")
def stores(embedder):
    pg = PgVectorChunkStore(DSN)
    assert pg.ping(), "start the database first: make up"
    pages = FilePageSource(REPO / "data" / "pages")
    ingest(pages, embedder, pg)
    memory = InMemoryChunkStore()
    ingest(pages, embedder, memory)
    return pg, memory


def test_ingest_writes_the_current_pages_chunks_and_no_retired_one(stores):
    pg, _ = stores
    with psycopg.connect(DSN) as connection:
        rows: dict[str, int] = dict(
            connection.execute(
                "SELECT p.status::text, count(c.id) FROM pages p LEFT JOIN chunks c ON c.page_id = p.id GROUP BY 1"
            ).fetchall()
        )
    assert rows["retired"] == 0
    assert rows["current"] == len(pg.chunks()) == 68


def test_the_database_itself_refuses_a_retired_chunk_and_a_chunk_of_an_unknown_page(stores):
    zero = "[" + ",".join(["0"] * 768) + "]"
    with psycopg.connect(DSN) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
            "VALUES ('x:0', 'p-return-window-old', 'h', 'b', DATE '2025-01-01', 'retired', %s::vector)",
            (zero,),
        )
    with psycopg.connect(DSN) as connection, pytest.raises(psycopg.errors.ForeignKeyViolation):
        connection.execute(
            "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
            "VALUES ('x:0', 'no-such-page', 'h', 'b', DATE '2026-01-01', 'current', %s::vector)",
            (zero,),
        )


def test_vector_search_in_sql_ranks_like_the_in_memory_scan(stores, embedder):
    pg, memory = stores
    for question in (
        "How many days do I have to return an item?",
        "What does error PR-E1042 mean?",
        "Do gift cards expire?",
    ):
        (vector,) = embedder.embed([question])
        sql_top = [chunk_id for chunk_id, _ in pg.vector_search(vector, 5)]
        scan_top = [chunk_id for chunk_id, _ in memory.vector_search(vector, 5)]
        assert sql_top == scan_top


def test_similarities_match_and_the_old_return_window_cannot_be_retrieved(stores, embedder):
    pg, memory = stores
    (vector,) = embedder.embed(["How many days do I have to return an item?"])
    ids = [c.id for c in memory.chunks()[:5]]
    for chunk_id, score in pg.similarities(vector, ids).items():
        assert score == pytest.approx(memory.similarities(vector, [chunk_id])[chunk_id], abs=1e-4)
    found = HybridRetriever(pg, embedder).retrieve("How many days do I have to return an item?", Mode.FUSED)
    assert "p-return-window-old" not in found.page_ids


def test_the_http_service_answers_a_recorded_question_from_the_pgvector_index(stores, embedder):
    pg, _ = stores
    model = RecordedChatModel(RecordingStore(REPO / "tests" / "fixtures" / "recordings"))
    prompt = FilePromptStore(REPO / "prompts").load("answer", "v1")
    retriever = HybridRetriever(pg, embedder)
    client = TestClient(create_app(AnswerService(retriever, model, prompt, 0.648), lambda: retriever.chunk_count))
    assert client.get("/health").json() == {"status": "ok", "chunks": 68}
    body = client.post("/ask", json={"question": "Do you ship to Antarctica?"}).json()
    assert (body["status"], body["reason"]) == ("refused", "below_threshold")
