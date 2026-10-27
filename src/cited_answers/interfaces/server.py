"""Run the HTTP service with uvicorn: SIGTERM finishes in-flight requests, then the process exits."""

from __future__ import annotations

import uvicorn

from cited_answers.application.answer import AnswerService
from cited_answers.application.retrieve import HybridRetriever, ingest
from cited_answers.domain.errors import DomainError
from cited_answers.infrastructure.clock import SystemClock
from cited_answers.infrastructure.files import FilePageSource, FilePromptStore, read_threshold
from cited_answers.infrastructure.model_factory import ModelSettings, build_chat_model
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.wiring import build_embedder, build_store
from cited_answers.interfaces.http import create_app


def serve(settings: AppSettings) -> int:
    """Build the service from the settings and run it until it is told to stop."""
    embedder, store = build_embedder(settings), build_store(settings)
    if settings.index_backend == "memory":
        ingest(FilePageSource(settings.pages_dir), embedder, store)
    retriever = HybridRetriever(store, embedder)
    model = build_chat_model(ModelSettings.from_env(), SystemClock())
    threshold = settings.refusal_threshold or read_threshold(settings.threshold_path) or 0.5
    prompt = FilePromptStore(settings.prompts_dir).load("answer", settings.answer_prompt)
    app = create_app(AnswerService(retriever, model, prompt, threshold), lambda: retriever.chunk_count)
    try:
        uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, timeout_graceful_shutdown=10)
    except DomainError:
        return 1
    return 0
