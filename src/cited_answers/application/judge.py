"""A model grades whether an answer states the fact it should; its agreement with hand grades is measured."""

from __future__ import annotations

import hashlib

from cited_answers.application.ports import ChatModel
from cited_answers.domain.evaluation import Question, parse_verdict
from cited_answers.domain.llm import ChatMessage, ChatRequest
from cited_answers.domain.prompts import Prompt


class Judge:
    """Asks a model to say `correct` or `incorrect` for one answer. A reply that says neither counts as incorrect."""

    def __init__(self, model: ChatModel, prompt: Prompt) -> None:
        self._model = model
        self._prompt = prompt

    def grade(self, question: Question, answer_text: str) -> bool:
        """True when the judge calls the answer correct."""
        request = ChatRequest(
            messages=(
                ChatMessage.user(
                    f"Question: {question.question}\n"
                    f"The answer must state: {question.fact}\n"
                    f"Answer to grade: {answer_text}"
                ),
            ),
            system=self._prompt.text,
            max_output_tokens=20,
            temperature=0.0 if self._model.supports_sampling else None,
            tag=f"{question.id}|judge-{self._prompt.version}|{hashlib.sha256(answer_text.encode()).hexdigest()[:8]}",
        )
        return parse_verdict(self._model.complete(request).text) is True
