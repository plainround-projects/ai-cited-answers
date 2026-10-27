-- The queries the service and the lesson's checks run, each with a line on what it shows.
-- Parameters in :name form are psql variables: psql -v question_vector="'[...]'" -f sql/003_queries.sql

-- 1. What is indexed and what is not: retired pages have a row in pages and none in chunks.
SELECT p.status, count(DISTINCT p.id) AS pages, count(c.id) AS chunks
FROM pages p LEFT JOIN chunks c ON c.page_id = p.id
GROUP BY p.status ORDER BY p.status;

-- 2. The skipped pages by id (the log line "retired page left out of the index" says the same).
SELECT p.id, p.title, p.updated FROM pages p WHERE p.status = 'retired' ORDER BY p.id;

-- 3. A search for the old return window finds no retired chunk, whatever the vector is: none can exist.
SELECT count(*) AS retired_chunks FROM chunks WHERE status <> 'current';

-- 4. Every chunk carries a page id, a heading path, an updated date and a status; none is empty.
SELECT count(*) AS incomplete_chunks FROM chunks
WHERE page_id IS NULL OR heading_path = '' OR updated IS NULL OR status IS NULL;

-- 5. No chunk spans two pages: a chunk id starts with exactly its page id.
SELECT count(*) AS chunks_with_a_foreign_id FROM chunks WHERE split_part(id, ':', 1) <> page_id;

-- 6. The five nearest chunks to a query vector, with cosine similarity (what the service runs for the vector list).
-- SELECT id, 1 - (embedding <=> :question_vector::vector) AS similarity
-- FROM chunks ORDER BY embedding <=> :question_vector::vector, id LIMIT 5;

-- 7. Chunk sizes, to confirm the 300-token limit (about 1.3 tokens per word).
SELECT max(array_length(string_to_array(body, ' '), 1)) AS longest_chunk_in_words,
       round(avg(array_length(string_to_array(body, ' '), 1)), 1) AS average_words
FROM chunks;
