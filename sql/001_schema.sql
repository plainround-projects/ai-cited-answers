-- DDL for the cited-answers index: pages (with their status) and chunks (with their embedding).
-- Run order: 001_schema.sql, 002_seed.sql, 003_queries.sql. `make db` applies the first two.

CREATE EXTENSION IF NOT EXISTS vector;

DO $$ BEGIN
    CREATE TYPE page_status AS ENUM ('current', 'retired');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS pages (
    id       text        PRIMARY KEY,
    title    text        NOT NULL,
    updated  date        NOT NULL,
    status   page_status NOT NULL
);
COMMENT ON TABLE pages IS 'Every help-center page, including retired ones; only current pages are chunked.';

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
COMMENT ON COLUMN chunks.embedding IS 'Cosine distance is the operator <=>; similarity = 1 - distance.';

CREATE INDEX IF NOT EXISTS chunks_page_idx ON chunks (page_id);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
