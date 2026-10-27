# pgvector

## What it is

An **embedding** is a list of numbers (here 768 of them) that a model produces for a piece of text, so that texts with similar meaning get similar lists (`ollama.md`). A **vector database** stores such lists and answers the question "which stored vectors are closest to this one?" (nearest-neighbor search). **pgvector** is an extension for PostgreSQL that adds a `vector(n)` column type, distance operators, and indexes for fast approximate search, so the same database that holds your tables can search by meaning.

**Cosine distance** compares the direction of two vectors and ignores their length: 0 means the same direction, 2 the opposite. **Cosine similarity** is `1 - distance`.

## Why this repository uses it

`ai-cited-answers` answers questions about a help center. Retrieval finds the chunks of pages most relevant to a question, by meaning (vectors) and by words (BM25, a keyword score), and the answer cites those chunks. Keeping vectors in the same PostgreSQL table as the chunk text means one query can sort by similarity and return the text, and a `CHECK` constraint can make it impossible to index a retired page.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `sql/001_schema.sql` | `CREATE EXTENSION vector`, the `embedding vector(768)` column and the `hnsw` index |
| `src/cited_answers/infrastructure/pg_store.py` | builds vector literals, runs the nearest-neighbor query |
| `docker-compose.yml` | the image `pgvector/pgvector:pg17` already contains the extension |
| `tests/fixtures/embeddings/` | recorded vectors, stored as base64 |

## How it works underneath

**Exact search** compares the query with every stored vector: always correct, but the time grows with the table. **Approximate search** uses an index that finds *very likely* nearest neighbors much faster. pgvector offers two index types; this project uses **HNSW** (Hierarchical Navigable Small World): a layered graph in which each vector is linked to nearby ones, and a search walks from a coarse top layer down to the dense bottom layer, always moving to a closer neighbor. It trades a small chance of missing the true best match for speed.

**Operators.** `<->` Euclidean distance, `<#>` negative inner product, `<=>` cosine distance. The index is created for one operator class (`vector_cosine_ops`), and a query must use the same operator in its `ORDER BY` for the index to be used.

**Text form.** A vector is written as text `[0.1,0.2,0.3]` and cast with `::vector`. The Python store formats numbers with eight significant digits (`:.8g`), enough to round-trip a 32-bit float.

**Dimension.** The column is `vector(768)` because `nomic-embed-text` produces 768 numbers; a vector of another length is rejected.

## Walkthrough of this repository's use

The schema lines that matter, explained in `sql.md`:

`sql/001_schema.sql`, line 28:

```sql
    embedding    vector(768)  NOT NULL                           -- nomic-embed-text
```

`sql/001_schema.sql`, line 33:

```sql
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
```

Writing a vector from Python:

`src/cited_answers/infrastructure/pg_store.py`, lines 14 to 16:

```python
def vector_literal(vector: Sequence[float]) -> str:
    """pgvector's text form of a vector: `[0.1,0.2,...]`."""
    return "[" + ",".join(f"{x:.8g}" for x in vector) + "]"
```

`f"{x:.8g}"` formats each number in the shortest way that keeps eight significant digits; the pieces are joined with commas inside square brackets.

Searching:

`src/cited_answers/infrastructure/pg_store.py`, lines 62 to 70:

```python
    def vector_search(self, vector: Sequence[float], k: int) -> list[tuple[str, float]]:
        literal = vector_literal(vector)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) AS similarity FROM chunks "
                "ORDER BY embedding <=> %s::vector, id LIMIT %s",
                (literal, literal, k),
            ).fetchall()
        return [(str(r[0]), float(r[1])) for r in rows]
```

- `%s::vector` turns the text parameter into a vector.
- `embedding <=> %s::vector` is the cosine distance between each chunk's vector and the question's vector.
- `1 - (...) AS similarity` converts distance to similarity (1 means identical direction).
- `ORDER BY embedding <=> ..., id LIMIT %s` returns the `k` closest chunks; the HNSW index serves this ordering. `id` breaks ties so the order is deterministic.

## Try it yourself

1. How a vector is written for pgvector.

```bash
.venv/bin/python -c "from cited_answers.infrastructure.pg_store import vector_literal; print(vector_literal([0.1, 0.25, -1.5]))"
```

What you should see (captured from this repository):

```text
[0.1,0.25,-1.5]
```

2. Cosine distance by hand: perpendicular vectors are at distance 1, a vector at 45 degrees at about 0.293, the same vector at 0.

```bash
.venv/bin/python -c "import math; a=[1,0]; b=[0,1]; c=[1,1]; cos=lambda x,y: sum(i*j for i,j in zip(x,y))/math.sqrt(sum(i*i for i in x)*sum(j*j for j in y)); print(round(1-cos(a,b),3), round(1-cos(a,c),3), round(1-cos(a,a),3))"
```

What you should see (captured from this repository):

```text
1.0 0.293 0.0
```

3. The same arithmetic inside PostgreSQL (after `make up`). Not run here.

```bash
docker compose exec db psql -U cited -d cited -c "select 1 - ('[1,0]'::vector <=> '[1,1]'::vector) as similarity"
```

4. Every line of the schema that mentions the extension, the type or the index.

```bash
grep -n 'vector' sql/001_schema.sql
```

What you should see (captured from this repository):

```text
4:CREATE EXTENSION IF NOT EXISTS vector;
28:    embedding    vector(768)  NOT NULL                           -- nomic-embed-text
33:CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
```

## Mistakes people make

- **Mixing embedding models.** Vectors from different models are not comparable; the column is fixed at 768 and the recordings name the model.
- **Ordering with a different operator than the index.** The index is cosine; the query must use `<=>`.
- **Expecting exact answers from an approximate index.** HNSW can miss the true nearest neighbor in rare cases; the evaluation measures hit rate.
- **Indexing stale content.** `status` has `CHECK (status = 'current')`, so a retired page cannot be indexed.
- **Forgetting the cast.** A text parameter must be cast with `::vector`.

## Check yourself

1. What does `<=>` compute?

   *Answer:* Cosine distance between two vectors.

2. Why does the column say `vector(768)`?

   *Answer:* The embedding model produces 768 numbers per text.

3. What does HNSW trade away for speed?

   *Answer:* A small chance of not returning the true nearest neighbor.

4. How is similarity obtained from distance?

   *Answer:* `1 - distance`.

5. Why does the query also order by `id`?

   *Answer:* To make ties deterministic.

## Further reading

- pgvector README, https://github.com/pgvector/pgvector (the extension was not run in this session because Docker was unavailable; the cosine arithmetic above was checked in Python).
