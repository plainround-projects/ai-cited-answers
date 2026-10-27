# SQL

## What it is

A **database** stores data so it can be searched and changed safely. A **relational** database keeps data in **tables**: a table is a grid in which every **row** is one thing (one order, one meeting) and every **column** is one fact about it (the total, the start time). **SQL** (Structured Query Language, said "sequel" or "S-Q-L") is the language you use to talk to such a database. A statement is a sentence ending in a semicolon: `CREATE TABLE` makes a table, `INSERT` adds rows, `SELECT` reads rows, `UPDATE` changes rows, `DELETE` removes rows.

Tables are linked by **keys**. A **primary key** is the column (or columns) that uniquely names each row. A **foreign key** is a column that holds another table's primary key, so each meeting attendee row points at a real meeting. **Constraints** are rules the database itself enforces: `NOT NULL`, `UNIQUE`, `CHECK (...)`, `REFERENCES`.

## Why this repository uses it

Some facts must be right even if the application code has a bug. A refund ledger that can never exceed the order total, a meeting that can never overlap another for the same person, a retry that can never apply a write twice: the repository puts these rules into the **schema** (the table definitions), where the database enforces them on every write, whoever writes. The numbered files under `sql/` are the schema (`001`), the sample data (`002`) and the checking queries (`003`).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `sql/001_schema.sql` | schema |
| `sql/002_seed.sql` | sample data |
| `sql/003_queries.sql` | queries that check the data |
| `Makefile` | `sqlite3 ... < sql/...` / `$(PSQL) < sql/...` run these files |

## How it works underneath

**Declarative language.** In SQL you say *what* you want, not how to get it. The database's **query planner** chooses the steps (which index, which join order).

**Reading a SELECT.** The clauses run in a fixed logical order, not the order written: `FROM` and `JOIN` (build the rows), `WHERE` (filter rows), `GROUP BY` (form groups), `HAVING` (filter groups), `SELECT` (choose columns), `ORDER BY` (sort), `LIMIT` (cut). That is why `WHERE` cannot use an aggregate like `sum(...)` but `HAVING` can.

**Joins.** `a JOIN b ON a.x = b.y` builds every pair of rows that satisfies the condition. `LEFT JOIN` keeps unmatched left rows, filling the right columns with null.

**Null.** Null means "unknown or absent", and it is not equal to anything, not even to another null. Test with `IS NULL`.

**Transactions.** A group of statements that succeed or fail together. Constraints are checked inside the transaction, so a rule violation cancels the whole group.

**Idempotent scripts.** `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS` make a schema file safe to run twice, which `make db` relies on.

## Walkthrough of this repository's use

Dialect: PostgreSQL (with pgvector).

`sql/001_schema.sql`, statement by statement.

```sql
-- DDL for the cited-answers index: pages (with their status) and chunks (with their embedding).
-- Run order: 001_schema.sql, 002_seed.sql, 003_queries.sql. `make db` applies the first two.
CREATE EXTENSION IF NOT EXISTS vector;
```

Loads the **pgvector** extension into the database, which adds the `vector` type, distance operators and vector indexes (see `pgvector.md`). `IF NOT EXISTS` makes the command safe to repeat.

```sql
DO $$ BEGIN
    CREATE TYPE page_status AS ENUM ('current', 'retired');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
```

`DO $$ ... $$` runs a block of PostgreSQL's procedural language once. Here: try to create the enum type `page_status`; if it already exists (`duplicate_object`), do nothing. PostgreSQL has no `CREATE TYPE IF NOT EXISTS`, so this is the way to make the script safe to repeat. An `ENUM` type holds exactly one of a fixed list of words; storing any other word is an error.

```sql
CREATE TABLE IF NOT EXISTS pages (
    id       text        PRIMARY KEY,
    title    text        NOT NULL,
    updated  date        NOT NULL,
    status   page_status NOT NULL
);
```

Creates the table `pages` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `id`: type `text`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null.
- Column `title`: type `text`: text of any length; `NOT NULL`: the column must always have a value.
- Column `updated`: type `date`: a calendar date (year, month, day); `NOT NULL`: the column must always have a value.
- Column `status`: type `page_status`: a value from the enum type `page_status` (a fixed list of allowed words, created above); `NOT NULL`: the column must always have a value.

```sql
COMMENT ON TABLE pages IS 'Every help-center page, including retired ones; only current pages are chunked.';
```

Attaches a description to a table or column inside the database itself (visible in `\d+` in psql).

```sql
-- A chunk belongs to exactly one page and only current pages are indexed: the CHECK makes a retired chunk impossible,
-- so a missing filter at query time can never serve a contradicted answer.
CREATE TABLE IF NOT EXISTS chunks (
    id           text         PRIMARY KEY,                       -- <page id>:<n>, the id a citation carries
    page_id      text         NOT NULL REFERENCES pages (id),
    heading_path text         NOT NULL,                          -- Title > Heading
    body         text         NOT NULL,
    updated      date         NOT NULL,
    status       page_status  NOT NULL CHECK (status = 'current'),
    embedding    vector(768)  NOT NULL                           -- nomic-embed-text
);
```

Creates the table `chunks` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `id`: type `text`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null. The author's note: &lt;page id&gt;:&lt;n&gt;, the id a citation carries.
- Column `page_id`: type `text`: text of any length; `NOT NULL`: the column must always have a value; `REFERENCES pages (id)`: a *foreign key*; the value must exist in `pages.id`.
- Column `heading_path`: type `text`: text of any length; `NOT NULL`: the column must always have a value. The author's note: Title &gt; Heading.
- Column `body`: type `text`: text of any length; `NOT NULL`: the column must always have a value.
- Column `updated`: type `date`: a calendar date (year, month, day); `NOT NULL`: the column must always have a value.
- Column `status`: type `page_status`: a value from the enum type `page_status` (a fixed list of allowed words, created above); `NOT NULL`: the column must always have a value; `CHECK (status = 'current')`: the database rejects any row for which this is false.
- Column `embedding`: type `vector(768)`: a pgvector vector with 768 numbers (see `pgvector.md`); `NOT NULL`: the column must always have a value. The author's note: nomic-embed-text.

```sql
COMMENT ON COLUMN chunks.embedding IS 'Cosine distance is the operator <=>; similarity = 1 - distance.';
```

Attaches a description to a table or column inside the database itself (visible in `\d+` in psql).

```sql
CREATE INDEX IF NOT EXISTS chunks_page_idx ON chunks (page_id);
```

Creates an index named `chunks_page_idx` on `chunks(page_id)`. An index is a sorted side structure that lets the database find rows by these columns without reading the whole table.

```sql
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
```

Creates an index named `chunks_embedding_idx` on `chunks(embedding vector_cosine_ops)` using the `hnsw` method. An index is a sorted side structure that lets the database find rows by these columns without reading the whole table. `hnsw` is an approximate nearest-neighbor index for vectors (Hierarchical Navigable Small World graph); `vector_cosine_ops` makes it use cosine distance.

`sql/002_seed.sql`, statement by statement.

```sql
-- DML: the pages of the sample help center (generated by scripts/make_seed_sql.py from data/pages).
-- The chunks and their embeddings are written by `cited ingest`, which leaves retired pages out.
INSERT INTO pages (id, title, updated, status) VALUES
    ('p-account-2fa', 'Two-factor sign-in', DATE '2026-07-07', 'current'),
    ('p-account-addresses', 'Saved addresses', DATE '2026-05-20', 'current'),
    ('p-account-change-email', 'Change your email address', DATE '2026-06-01', 'current'),
    ... (58 more rows)
```

Adds 60 row(s) to the table `pages`. The column list `(id, title, updated, status)` names the columns; each parenthesized line after `VALUES` is one row whose values are in the same order. Text is in single quotes; `DATE '2026-07-07'` is a date literal; numbers have no quotes.

`sql/003_queries.sql`, statement by statement.

```sql
-- The queries the service and the lesson's checks run, each with a line on what it shows.
-- Parameters in :name form are psql variables: psql -v question_vector="'[...]'" -f sql/003_queries.sql
-- 1. What is indexed and what is not: retired pages have a row in pages and none in chunks.
SELECT p.status, count(DISTINCT p.id) AS pages, count(c.id) AS chunks
FROM pages p LEFT JOIN chunks c ON c.page_id = p.id
GROUP BY p.status ORDER BY p.status;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `p.status`: the column `status` of the table (or alias) `p`.
  - `count(DISTINCT p.id)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS pages` names this result column `pages`.
  - `count(c.id)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS chunks` names this result column `chunks`.
- **`FROM`** names the table the rows come from: `pages p` (`p` is a short alias for it).
- **`LEFT JOIN`** `chunks c ON c.page_id = p.id`: `LEFT JOIN` also keeps the rows of the left table that have no match on the right (the right-hand columns are then null).
- **`GROUP BY`** `p.status`: rows with the same value(s) form one group, and aggregate functions (`count`, `sum`, ...) are worked out per group.
- **`ORDER BY`** `p.status`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 2. The skipped pages by id (the log line "retired page left out of the index" says the same).
SELECT p.id, p.title, p.updated FROM pages p WHERE p.status = 'retired' ORDER BY p.id;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `p.id`: the column `id` of the table (or alias) `p`.
  - `p.title`: the column `title` of the table (or alias) `p`.
  - `p.updated`: the column `updated` of the table (or alias) `p`.
- **`FROM`** names the table the rows come from: `pages p` (`p` is a short alias for it).
- **`WHERE`** keeps only the rows for which the condition is true: `p.status = 'retired'`.
- **`ORDER BY`** `p.id`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 3. A search for the old return window finds no retired chunk, whatever the vector is: none can exist.
SELECT count(*) AS retired_chunks FROM chunks WHERE status <> 'current';
```

- **`SELECT`** chooses what to return, one result column per item:
  - `count(*)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS retired_chunks` names this result column `retired_chunks`.
- **`FROM`** names the table the rows come from: `chunks`.
- **`WHERE`** keeps only the rows for which the condition is true: `status <> 'current'`. Here `<>` not equal to.

```sql
-- 4. Every chunk carries a page id, a heading path, an updated date and a status; none is empty.
SELECT count(*) AS incomplete_chunks FROM chunks
WHERE page_id IS NULL OR heading_path = '' OR updated IS NULL OR status IS NULL;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `count(*)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS incomplete_chunks` names this result column `incomplete_chunks`.
- **`FROM`** names the table the rows come from: `chunks`.
- **`WHERE`** keeps only the rows for which the condition is true: `page_id IS NULL OR heading_path = '' OR updated IS NULL OR status IS NULL`. Here `IS NULL` has no value (is null; `= NULL` would not work, because null is never equal to anything).

```sql
-- 5. No chunk spans two pages: a chunk id starts with exactly its page id.
SELECT count(*) AS chunks_with_a_foreign_id FROM chunks WHERE split_part(id, ':', 1) <> page_id;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `count(*)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS chunks_with_a_foreign_id` names this result column `chunks_with_a_foreign_id`.
- **`FROM`** names the table the rows come from: `chunks`.
- **`WHERE`** keeps only the rows for which the condition is true: `split_part(id, ':', 1) <> page_id`. Here `<>` not equal to. `split_part`: splits text at a delimiter and returns the n-th piece (`split_part(id, ':', 1)` is the text before the first colon).

```sql
-- 6. The five nearest chunks to a query vector, with cosine similarity (what the service runs for the vector list).
-- SELECT id, 1 - (embedding <=> :question_vector::vector) AS similarity
-- FROM chunks ORDER BY embedding <=> :question_vector::vector, id LIMIT 5;
-- 7. Chunk sizes, to confirm the 300-token limit (about 1.3 tokens per word).
SELECT max(array_length(string_to_array(body, ' '), 1)) AS longest_chunk_in_words,
       round(avg(array_length(string_to_array(body, ' '), 1)), 1) AS average_words
FROM chunks;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `max(array_length(string_to_array(body, ' '), 1))`: `max`: the largest value in the group; `array_length`: the number of elements in an array; `string_to_array`: splits text into an array at a delimiter. `AS longest_chunk_in_words` names this result column `longest_chunk_in_words`.
  - `round(avg(array_length(string_to_array(body, ' '), 1)), 1)`: `round`: rounds a number to the given number of decimals; `avg`: the average of a column over the group of rows; `array_length`: the number of elements in an array; `string_to_array`: splits text into an array at a delimiter. `AS average_words` names this result column `average_words`.
- **`FROM`** names the table the rows come from: `chunks`.

## Try it yourself

1. The SQLite command-line shell that the Makefile uses (PostgreSQL files need `psql` in the container; see `postgresql.md`).

```bash
sqlite3 --version
```

What you should see (captured from this repository):

```text
3.51.0 2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl (64-bit)
```

2. Run a schema file against a throwaway in-memory database and list the tables it made.

```bash
sqlite3 :memory: "CREATE TABLE t (id INTEGER PRIMARY KEY, n TEXT NOT NULL CHECK (n <> ''))" ".tables"
```

What you should see (captured from this repository):

```text
t
```

3. A `CHECK` constraint at work: the second insert is refused by the database.

```bash
sqlite3 :memory: "CREATE TABLE t (n INTEGER CHECK (n > 0)); INSERT INTO t VALUES (5); INSERT INTO t VALUES (-1);" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
Error: stepping, CHECK constraint failed: n > 0 (19)
```

4. Small expressions: `+`, text joining `||`, `abs`, and the null rules (`NULL = NULL` is not true, `NULL IS NULL` is).

```bash
sqlite3 :memory: "SELECT 1 + 1, 'a' || 'b', abs(-3), NULL = NULL, NULL IS NULL"
```

What you should see (captured from this repository):

```text
2|ab|3||1
```

5. `GROUP BY` and `HAVING`: group `a` has total 3 and group `b` has total 5, both above 2.

```bash
sqlite3 :memory: "CREATE TABLE s (g TEXT, v INTEGER); INSERT INTO s VALUES ('a',1),('a',2),('b',5); SELECT g, count(*), sum(v) FROM s GROUP BY g HAVING sum(v) > 2 ORDER BY g;"
```

What you should see (captured from this repository):

```text
a|2|3
b|1|5
```

## Mistakes people make

- **Using `= NULL`.** Never true. Use `IS NULL`.
- **`WHERE` with an aggregate.** Use `HAVING` for conditions on `sum(...)` and `count(...)`.
- **Trusting only application code for rules.** Constraints and triggers hold even if some other program writes the table.
- **Building SQL by gluing text.** Values are passed as parameters (`?` in SQLite, `%s` in psycopg) so a value can never change the meaning of the statement.
- **Forgetting `IF NOT EXISTS`.** Running the schema twice would fail. The files are written to be repeatable.
- **Foreign keys in SQLite.** They are off by default; each connection runs `PRAGMA foreign_keys = ON`.

## Check yourself

1. What does a primary key guarantee?

   *Answer:* Each row has a unique, non-null identifier.

2. What is the difference between `WHERE` and `HAVING`?

   *Answer:* `WHERE` filters rows before grouping; `HAVING` filters groups after aggregates are computed.

3. What does `LEFT JOIN` keep that `JOIN` drops?

   *Answer:* Left rows with no match on the right.

4. Why is `NULL = NULL` not true?

   *Answer:* Null means unknown; two unknowns are not known to be equal.

5. How does a trigger protect the refund ledger?

   *Answer:* It runs before each insert, and aborts the insert if the total would exceed the order total.

## Further reading

- SQLite SQL reference, https://www.sqlite.org/lang.html; PostgreSQL 17 SQL commands, https://www.postgresql.org/docs/17/sql-commands.html (SQLite examples were run locally with sqlite3 3.51; the PostgreSQL files could not be run here because Docker was down, so they are explained but not executed in this session).
