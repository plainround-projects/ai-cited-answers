from fastapi.testclient import TestClient

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.domain.errors import TransientModelError
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.interfaces.http import create_app
from tests.conftest import PAGES, PROMPT, HashingEmbedder, MemoryPages, ScriptedModel


def client(answer, count=lambda: 4, threshold=0.0):
    embedder, store = HashingEmbedder(), InMemoryChunkStore()
    ingest(MemoryPages(PAGES), embedder, store)
    service = AnswerService(HybridRetriever(store, embedder), ScriptedModel(answer), PROMPT, threshold)
    return TestClient(create_app(service, count))


def test_health_is_ok_with_chunks_and_not_ready_without():
    assert client(lambda r: "x").get("/health").json() == {"status": "ok", "chunks": 4}
    empty = client(lambda r: "x", count=lambda: 0).get("/health")
    assert empty.status_code == 503
    assert empty.json()["status"] == "not ready"


def test_a_cited_answer_returns_its_citations_with_page_and_heading():
    body = (
        client(lambda r: "Thirty days [p-return-window:0].")
        .post("/ask", json={"question": "How many days to return?"})
        .json()
    )
    assert body["status"] == "answered"
    assert body["citations"] == [
        {"chunk_id": "p-return-window:0", "page_id": "p-return-window", "heading_path": "Return window > 30 days"}
    ]
    assert body["reason"] == "none"


def test_the_fixed_refusal_comes_back_with_its_reason():
    body = client(lambda r: "no citation here").post("/ask", json={"question": "How many days to return?"}).json()
    assert (body["status"], body["reason"], body["citations"]) == ("refused", "no_citation", [])
    assert body["answer"].startswith("I don't have information")


def test_bad_requests_are_rejected_before_any_work():
    c = client(lambda r: "x")
    assert c.post("/ask", json={"question": "hi"}).status_code == 422
    assert c.post("/ask", json={"question": "x" * 501}).status_code == 422
    assert c.post("/ask", json={"question": "a fine question", "extra": 1}).status_code == 422
    assert c.post("/ask", json={}).status_code == 422


def test_a_model_outage_is_a_503_not_a_stack_trace():
    def fail(request):
        raise TransientModelError("down")

    response = client(fail).post("/ask", json={"question": "How many days to return?"})
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_info_logs_carry_a_hash_of_the_question_never_its_text(caplog):
    import logging

    with caplog.at_level(logging.INFO):
        client(lambda r: "Thirty days [p-return-window:0].").post(
            "/ask", json={"question": "my private question about returns"}
        )
    assert "private" not in caplog.text
    record = next(r for r in caplog.records if r.getMessage() == "question answered")
    assert len(record.fields["question_sha"]) == 10
