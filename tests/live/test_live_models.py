"""Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from cited_answers.domain.chunking import chunk_page
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.embeddings import OpenAICompatibleEmbedder
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from tests.conftest import PAGES

pytestmark = pytest.mark.live


def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_answers_from_the_passage_and_cites_its_id():
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"}), SystemClock())
    (chunk,) = chunk_page(PAGES[0])
    prompt = f"Passages:\n\n[{chunk.id}] {chunk.text}\n\nQuestion: How many days do I have to return an item?"
    system = "Answer only from the passages and cite the passage id in square brackets after each fact."
    response = model.complete(ChatRequest((ChatMessage.user(prompt),), system=system, max_output_tokens=200))
    assert "30" in response.text
    assert f"[{chunk.id}]" in response.text


@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_embedding_model_returns_768_dimensional_vectors_and_paraphrases_land_close():
    from cited_answers.domain.retrieval import cosine

    embedder = OpenAICompatibleEmbedder(httpx.Client(timeout=60), "http://localhost:11434/v1", "nomic-embed-text")
    a, b, c = embedder.embed(
        ["How long do I have to return a purchase?", "You can return items within 30 days.", "Gift cards never expire."]
    )
    assert len(a) == 768
    assert cosine(a, b) > cosine(a, c)
