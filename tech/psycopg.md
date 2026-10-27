# psycopg (the PostgreSQL driver)

## What it is

A **driver** is a library that lets a program talk to a particular database. **psycopg** (version 3) is the PostgreSQL driver for Python: you open a **connection** with the server's address, send SQL text with **parameters**, and read **rows** back as Python tuples. The `[binary]` extra of the package (`psycopg[binary]`) installs `psycopg-binary`, a prebuilt compiled helper, so no compiler or PostgreSQL development files are needed.

## Why this repository uses it

The store for `ai-cited-answers` is the only code that imports it (import-linter forbids it in `domain` and `application`). Parameters are passed separately from the SQL, so the question vector or a chunk's text can never alter the statement.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/cited_answers/infrastructure/pg_store.py` | connections, the transaction that replaces all chunks, the queries |
| `tests/integration/` | tests that run the store against the container |
| `pyproject.toml` | `psycopg[binary]==3.3.6` |
| `requirements.lock` | `psycopg`, `psycopg-binary`, `tzdata` (on Windows) |

## How it works underneath

**Placeholders.** `%s` marks where a parameter goes. psycopg sends the SQL text and the values to the server separately (server-side binding), so values are never pasted into the text. A literal percent sign is written `%%`.

**Connections and transactions.** `with psycopg.connect(dsn) as connection:` closes the connection at the end of the block, committing if no error happened and rolling back otherwise. `connection.transaction()` makes an explicit transaction block. A *DSN* (data source name) is the connection string.

**Cursors.** `connection.execute(sql, params)` returns a cursor; `.fetchall()` returns a list of tuples. `cursor.executemany(sql, rows)` runs one statement for many parameter tuples efficiently.

**Errors.** `psycopg.OperationalError` is raised for connection problems; `psycopg.Error` is the base class of all database errors.

## Walkthrough of this repository's use

`src/cited_answers/infrastructure/pg_store.py`, lines 25 to 29:

```python
    def _connect(self) -> psycopg.Connection:
        try:
            return psycopg.connect(self._dsn, connect_timeout=5)
        except psycopg.OperationalError as error:
            raise TransientModelError(f"database unavailable: {error}") from error
```

`psycopg.connect(dsn, connect_timeout=5)` opens a connection, waiting up to 5 seconds. An `OperationalError` (server unreachable) is converted to the project's `TransientModelError`, which callers treat as retryable.

`src/cited_answers/infrastructure/pg_store.py`, lines 31 to 38:

```python
    def ping(self) -> bool:
        """True when the database answers a trivial query."""
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except (TransientModelError, psycopg.Error):
            return False
```

`with self._connect() as connection:` closes the connection when the block ends. `connection.execute("SELECT 1")` is the cheapest possible query: if it works, the server is up.

`src/cited_answers/infrastructure/pg_store.py`, lines 40 to 53:

```python
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
```

- `with self._connect() as connection, connection.transaction():` opens the connection and a transaction together. If anything inside raises, the transaction rolls back and the old chunks stay.
- `DELETE FROM chunks` then the inserts happen in one transaction, so a reader sees either the old index or the new one, never half.
- `cursor.executemany(...)` inserts all rows; each row's last value is cast with `::vector`.
- `zip(chunks, vectors, strict=True)` raises if the lists have different lengths.

## Try it yourself

1. The installed driver.

```bash
.venv/bin/python -c "import psycopg; print(psycopg.__version__)"
```

What you should see (captured from this repository):

```text
3.3.6
```

2. What a connection failure looks like (nothing listens on port 1): an `OperationalError`, which the store converts to a retryable error.

```bash
.venv/bin/python -c "import psycopg; psycopg.connect('postgresql://x:y@127.0.0.1:1/z', connect_timeout=1)" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 1 failed: could not receive data from server: Connection refused
```

3. The version of `libpq`, PostgreSQL's client library, that the binary package carries.

```bash
.venv/bin/python -c "import psycopg; print(psycopg.pq.version())"
```

What you should see (captured from this repository):

```text
180006
```

## Mistakes people make

- **Formatting values into the SQL text.** That is how SQL injection happens. Parameters are always passed in the second argument.
- **Leaving connections open.** `with` blocks close them.
- **Forgetting the transaction around multi-step writes.** `replace_all` deletes and inserts inside one.
- **Passing a Python list where a vector is expected.** The text form `[...]` and `::vector` cast are required.
- **A literal `%` in SQL.** Write `%%` when parameters are used.

## Check yourself

1. What does `%s` do?

   *Answer:* Marks a parameter; the value is sent to the server separately from the SQL.

2. What does leaving a `with connection:` block normally do?

   *Answer:* Commits and closes (it rolls back if an error occurred).

3. Why is `replace_all` one transaction?

   *Answer:* So readers never see a half-replaced index.

4. What does `psycopg[binary]` add?

   *Answer:* A precompiled helper so no compiler is needed.

5. Which exception means the server could not be reached?

   *Answer:* `psycopg.OperationalError`.

## Further reading

- psycopg 3 documentation, https://www.psycopg.org/psycopg3/docs/ (psycopg 3.3.6 is pinned; connection-failure and version commands were run locally, queries against the server were not because Docker was unavailable).
