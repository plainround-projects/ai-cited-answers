"""A decorator that retries transient model failures with backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from cited_answers.application.ports import ChatModel
from cited_answers.domain.errors import TransientModelError
from cited_answers.domain.llm import ChatRequest, ChatResponse
from cited_answers.infrastructure.logging import fields
from cited_answers.infrastructure.retry import retry

_log = logging.getLogger(__name__)


class RetryingChatModel:
    """Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."""

    def __init__(
        self,
        inner: ChatModel,
        *,
        attempts: int = 3,
        base_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._base_delay = base_delay_seconds
        self._sleep = sleep
        self._rng = rng

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        def log_retry(attempt: int, error: BaseException) -> None:
            _log.warning(
                "model call failed, retrying", extra=fields(tag=request.tag, attempt=attempt, error=str(error))
            )

        return retry(
            lambda: self._inner.complete(request),
            attempts=self._attempts,
            base_delay_seconds=self._base_delay,
            retry_on=(TransientModelError,),
            sleep=self._sleep,
            rng=self._rng,
            on_retry=log_retry,
        )
