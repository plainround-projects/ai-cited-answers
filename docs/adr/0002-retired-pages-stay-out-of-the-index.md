# 0002. Retired pages stay out of the index, and the database enforces it

Date: 2026-10-27. Status: accepted.

## Context

Three retired pages contradict current ones (a 14-day return window, a flat $6.99 shipping fee, a $5 return fee). A page "marked retired" that is still searchable is one missing filter away from being served.

## Decision

`chunk_current_pages` chunks only current pages and returns the ids of the skipped ones, which `ingest` logs by id. In Postgres the `chunks` table has `status page_status NOT NULL CHECK (status = 'current')` and a foreign key to `pages`, which still lists the retired pages with their status. A retired chunk is therefore impossible to insert, whatever the application does.

## Consequences

- Bringing a page back is a status change in `pages` and a re-ingest, not a removal of a filter.
- The skip log answers "why can't I search the old return policy".
- The constraint is covered by an integration test that tries to insert one.
