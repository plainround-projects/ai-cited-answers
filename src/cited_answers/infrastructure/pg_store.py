"""The chunk store on Postgres with the pgvector extension (see sql/001_schema.sql)."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from cited_answers.domain.chunking import Chunk
from cited_answers.domain.errors import TransientModelError
from cited_answers.domain.pages import PageStatus


def vector_literal(vector: Sequence[float]) -> str:
    """pgvector's text form of a vector: `[0.1,0.2,...]`."""
    return "[" + ",".join(f"{x:.8g}" for x in vector) + "]"


class PgVectorChunkStore:
    """Chunks with their embeddings in one table; cosine distance in SQL, ordered by an HNSW index."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self) -> psycopg.Connection:
        try:
            return psycopg.connect(self._dsn, connect_timeout=5)
        except psycopg.OperationalError as error:
            raise TransientModelError(f"database unavailable: {error}") from error

    def ping(self) -> bool:
        """True when the database answers a trivial query."""
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except (TransientModelError, psycopg.Error):
            return False

    def replace_all(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("one vector per chunk")
        with self._connect() as connection, connection.transaction():
            connection.execute("DELETE FROM chunks")
            with connection.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO chunks (id, page_id, heading_path, body, updated, status, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s::vector)",
                    [
                        (c.id, c.page_id, c.heading_path, c.text, c.updated, c.status.value, vector_literal(v))
                        for c, v in zip(chunks, vectors, strict=True)
                    ],
                )

    def chunks(self) -> list[Chunk]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, page_id, heading_path, body, updated, status FROM chunks ORDER BY id"
            ).fetchall()
        return [Chunk(r[0], r[1], r[2], r[3], r[4], PageStatus(r[5])) for r in rows]

    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        literal = vector_literal(vector)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) AS similarity FROM chunks "
                "ORDER BY embedding <=> %s::vector, id LIMIT %s",
                (literal, literal, k),
            ).fetchall()
        return [(str(r[0]), float(r[1])) for r in rows]

    def similarities(self, vector: Sequence[float], chunk_ids: Sequence[str]) -> dict[str, float]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) FROM chunks WHERE id = ANY(%s)",
                (vector_literal(vector), list(chunk_ids)),
            ).fetchall()
        return {str(r[0]): float(r[1]) for r in rows}
