"""The HTTP interface: POST /ask and GET /health."""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from cited_answers.application.answer import AnswerService
from cited_answers.domain.errors import ModelError

_log = logging.getLogger("cited.http")


class AskRequest(BaseModel):
    """The body of POST /ask."""

    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, Field(min_length=3, max_length=500)]


class CitationOut(BaseModel):
    """One cited chunk, with what a reader needs to open it."""

    chunk_id: str
    page_id: str
    heading_path: str


class AskResponse(BaseModel):
    """The answer, or the fixed refusal and why."""

    status: str
    answer: str
    reason: str
    citations: list[CitationOut]
    best_similarity: float


def create_app(service: AnswerService, chunk_count: Callable[[], int]) -> FastAPI:
    """Build the app around an answer service. `chunk_count` is the readiness probe: zero chunks means not ready."""
    app = FastAPI(title="cited-answers", version="0.1.0")

    @app.get("/health")
    def health(response: Response) -> dict[str, object]:
        count = chunk_count()
        if count == 0:
            response.status_code = 503
            return {"status": "not ready", "chunks": 0}
        return {"status": "ok", "chunks": count}

    @app.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest) -> AskResponse:
        request_id = uuid.uuid4().hex[:12]
        digest = hashlib.sha256(body.question.encode()).hexdigest()[:10]
        try:
            answer = service.ask(body.question, request_id)
        except ModelError as error:
            _log.warning(
                "model unavailable", extra={"fields": {"request_id": request_id, "error": type(error).__name__}}
            )
            raise HTTPException(status_code=503, detail="the model is unavailable, try again shortly") from error
        by_id = {c.id: c for c in answer.retrieval.chunks}
        citations = [
            CitationOut(chunk_id=cid, page_id=by_id[cid].page_id, heading_path=by_id[cid].heading_path)
            for cid in answer.citations
            if cid in by_id
        ]
        _log.info(
            "question answered",
            extra={
                "fields": {
                    "request_id": request_id,
                    "question_sha": digest,
                    "chars": len(body.question),
                    "status": answer.status.value,
                    "reason": answer.reason.value,
                    "citations": len(citations),
                }
            },
        )
        return AskResponse(
            status=answer.status.value,
            answer=answer.text,
            reason=answer.reason.value,
            citations=citations,
            best_similarity=round(answer.retrieval.best_similarity, 4),
        )

    return app
