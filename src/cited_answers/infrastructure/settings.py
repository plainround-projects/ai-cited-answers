"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from cited_answers.infrastructure.env import ConfigurationError, choice, optional_text, positive_int, text

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Paths, the index backend, the embedding model and the HTTP server. See env.example for each variable."""

    pages_dir: Path
    questions_dir: Path
    prompts_dir: Path
    threshold_path: Path
    reports_dir: Path
    index_backend: str
    database_url: str
    embedder_provider: str
    embed_model: str
    embeddings_path: Path
    answer_prompt: str
    judge_prompt: str
    refusal_threshold: float | None
    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AppSettings:
        env = os.environ if environ is None else environ
        override = optional_text(env, "REFUSAL_THRESHOLD")
        try:
            threshold = float(override) if override else None
        except ValueError as error:
            raise ConfigurationError(f"REFUSAL_THRESHOLD must be a number, got {override!r}") from error
        return cls(
            pages_dir=Path(text(env, "PAGES_DIR", "data/pages")),
            questions_dir=Path(text(env, "QUESTIONS_DIR", "data/questions")),
            prompts_dir=Path(text(env, "PROMPTS_DIR", "prompts")),
            threshold_path=Path(text(env, "THRESHOLD_PATH", "evals/threshold.json")),
            reports_dir=Path(text(env, "REPORTS_DIR", "evals/reports")),
            index_backend=choice(env, "INDEX_BACKEND", "memory", ("memory", "pgvector")),
            database_url=text(env, "DATABASE_URL", "postgresql://cited:cited@localhost:55432/cited"),
            embedder_provider=choice(env, "EMBEDDER_PROVIDER", "recorded", ("recorded", "openai-compatible")),
            embed_model=text(env, "EMBED_MODEL", "nomic-embed-text"),
            embeddings_path=Path(text(env, "EMBEDDINGS_PATH", "tests/fixtures/embeddings")),
            answer_prompt=text(env, "ANSWER_PROMPT_VERSION", "v2"),
            judge_prompt=text(env, "JUDGE_PROMPT_VERSION", "v1"),
            refusal_threshold=threshold,
            host=text(env, "HTTP_HOST", "127.0.0.1"),
            port=positive_int(env, "HTTP_PORT", 8080),
            log_level=choice({"LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )
