"""Build the embedder and the chunk store the settings ask for."""

from __future__ import annotations

import os
from collections.abc import Mapping

import httpx

from cited_answers.application.ports import ChunkStore, Embedder
from cited_answers.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
)
from cited_answers.infrastructure.env import choice, optional_text, positive_float, text
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.pg_store import PgVectorChunkStore
from cited_answers.infrastructure.settings import AppSettings


def build_embedder(settings: AppSettings, environ: Mapping[str, str] | None = None) -> Embedder:
    """`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."""
    env = os.environ if environ is None else environ
    if settings.embedder_provider == "recorded":
        return RecordedEmbedder(EmbeddingStore(settings.embeddings_path), settings.embed_model)
    http = httpx.Client(timeout=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0))
    live = OpenAICompatibleEmbedder(
        http,
        text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
        settings.embed_model,
        optional_text(env, "OPENAI_API_KEY"),
    )
    if choice(env, "RECORD", "off", ("on", "off")) == "on":
        return RecordingEmbedder(live, EmbeddingStore(settings.embeddings_path))
    return live


def build_store(settings: AppSettings) -> ChunkStore:
    """The in-memory store, or Postgres with pgvector."""
    if settings.index_backend == "pgvector":
        return PgVectorChunkStore(settings.database_url)
    return InMemoryChunkStore()
