"""Answer a question from the retrieved chunks, cite every claim, or refuse."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from cited_answers.application.ports import ChatModel
from cited_answers.application.retrieve import HybridRetriever, Mode, Retrieval
from cited_answers.domain.answering import (
    REFUSAL_MESSAGE,
    Reason,
    Status,
    check_citations,
    is_model_refusal,
)
from cited_answers.domain.chunking import Chunk
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.domain.prompts import Prompt

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Answer:
    """The reader's answer and everything needed to grade it: the status and reason, the chunks and the raw text."""

    question_id: str
    status: Status
    text: str
    reason: Reason
    citations: tuple[str, ...]
    retrieval: Retrieval
    raw_text: str
    input_tokens: int
    output_tokens: int

    @property
    def refused(self) -> bool:
        return self.status is Status.REFUSED


def format_context(chunks: tuple[Chunk, ...]) -> str:
    """The passages as the model sees them, each under its id in square brackets."""
    return "\n\n".join(f"[{c.id}] {c.heading_path} (updated {c.updated})\n{c.text}" for c in chunks)


class AnswerService:
    """Retrieve, refuse early below the threshold, ask the model, check the citations."""

    def __init__(
        self,
        retriever: HybridRetriever,
        model: ChatModel,
        prompt: Prompt,
        threshold: float,
        max_output_tokens: int = 300,
    ) -> None:
        self._retriever = retriever
        self._model = model
        self._prompt = prompt
        self._threshold = threshold
        self._max_output_tokens = max_output_tokens

    @property
    def threshold(self) -> float:
        return self._threshold

    def retrieve(self, question: str) -> Retrieval:
        """Fused retrieval only (used by the threshold tuning, which needs no model)."""
        return self._retriever.retrieve(question, Mode.FUSED)

    def ask(self, question: str, question_id: str = "q") -> Answer:
        """Answer one question. Below the threshold the model is never called."""
        retrieval = self._retriever.retrieve(question, Mode.FUSED)
        if retrieval.best_similarity < self._threshold:
            _log.info(
                "refused before the model",
                extra={"fields": {"question_id": question_id, "score": round(retrieval.best_similarity, 3)}},
            )
            return Answer(question_id, Status.REFUSED, REFUSAL_MESSAGE, Reason.BELOW_THRESHOLD, (), retrieval, "", 0, 0)
        request = ChatRequest(
            messages=(ChatMessage.user(f"Passages:\n\n{format_context(retrieval.chunks)}\n\nQuestion: {question}"),),
            system=self._prompt.text,
            max_output_tokens=self._max_output_tokens,
            temperature=0.0 if self._model.supports_sampling else None,
            tag=f"{question_id}|{self._prompt.name}-{self._prompt.version}",
        )
        response = self._model.complete(request)
        usage = (response.usage.input_tokens, response.usage.output_tokens)
        text = response.text.strip()
        if is_model_refusal(text):
            return Answer(
                question_id, Status.REFUSED, REFUSAL_MESSAGE, Reason.MODEL_REFUSED, (), retrieval, text, *usage
            )
        check = check_citations(text, retrieval.chunks)
        if not check.ok:
            _log.info(
                "answer replaced by the refusal",
                extra={"fields": {"question_id": question_id, "reason": check.reason.value}},
            )
            return Answer(
                question_id, Status.REFUSED, REFUSAL_MESSAGE, check.reason, check.cited, retrieval, text, *usage
            )
        return Answer(question_id, Status.ANSWERED, text, Reason.NONE, check.cited, retrieval, text, *usage)
