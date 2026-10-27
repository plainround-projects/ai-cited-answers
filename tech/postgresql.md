# PostgreSQL

## What it is

**PostgreSQL** (often "Postgres") is a full database **server**: a program that runs all the time, owns the data files, and answers many clients at once over the network. Clients connect to it at an address and port (default 5432) with a user name, password and database name, then send SQL. Compared with SQLite (one file, no server) it adds many users at once, richer types (arrays, enums, JSON), extensions and tuning for large data.

A **client** is any program that connects (here: `psql`, the command-line client, and the Python driver psycopg). An **extension** adds features to a database; this project uses `vector` (see `pgvector.md`).

## Why this repository uses it

`ai-cited-answers` keeps its search index in a real database, as a production service would: help-page chunks and their vectors in one table, searched by SQL with an approximate nearest-neighbor index. PostgreSQL with the pgvector extension is the common choice. It runs in a container (`pgvector/pgvector:pg17`) started by Docker Compose, so nothing has to be installed on your computer.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | service `db`: the image, credentials, port, volume and health check |
| `sql/001_schema.sql` | extension, enum type, tables, indexes (PostgreSQL syntax) |
| `sql/002_seed.sql, sql/003_queries.sql` | data and checking queries |
| `Makefile` | `PSQL` runs `psql` inside the container; `up`, `db`, `down` |
| `src/cited_answers/infrastructure/pg_store.py` | the Python store that talks to it |
| `.github/workflows/ci.yml` | the `integration` job starts the same image as a service container |

## How it works underneath

**Processes and storage.** The server starts a process per connection, and keeps data in files on disk (here inside a Docker *volume*). Changes are written first to a write-ahead log, then to the data files, so a crash cannot corrupt committed data.

**Roles and databases.** One server holds many databases; a *role* (user) with a password connects to one of them. The image creates the role and database from the environment variables `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` the first time it starts with an empty volume.

**Connection string.** `postgresql://cited:cited@localhost:55432/cited` is user, password, host, port and database in one address (`DATABASE_URL`). The host port is 55432 and not the usual 5432 so it does not collide with a PostgreSQL you may already run; Docker maps host 55432 to container 5432.

**Readiness.** The server needs a moment to initialize a fresh volume. `pg_isready` asks whether it accepts connections; the compose health check and the Makefile's `db` loop both wait for it. During first-time initialization a temporary server listens on the Unix socket only, which is why the health check uses TCP (`-h 127.0.0.1`).

**Types and features used here.** `text`, `date`, a user-defined `ENUM`, `vector(768)`, `COMMENT ON`, `CREATE INDEX ... USING hnsw`, `split_part`, `string_to_array`, array parameters with `= ANY(%s)`.

## Walkthrough of this repository's use

The commands and files, in the order a run uses them:

1. `make up` runs `docker compose up -d --wait db` (explained in `docker-compose.md`): the container starts and the command waits until its health check passes.
2. `make db` runs `$(PSQL) < sql/001_schema.sql` and `< sql/002_seed.sql`. `$(PSQL)` is `docker compose exec -T db psql -U cited -d cited -v ON_ERROR_STOP=1 -q`: run `psql` inside the container, connect as user `cited` to database `cited`, stop at the first error, stay quiet. The SQL is explained statement by statement in `sql.md`.
3. `make ingest` fills the `chunks` table through `psycopg` (see `psycopg.md`).
4. `make down` runs `docker compose --profile api down -v`, which removes the container **and its volume**, deleting the data.

CI starts the same image as a *service container* and connects to `localhost:55432` (see `github-actions.md`).

The `psql` client commands you can use by hand once it runs: `docker compose exec db psql -U cited -d cited` opens an interactive prompt; inside it `\dt` lists tables, `\d chunks` describes a table, `\q` quits.

## Try it yourself

1. Start the database container (needs Docker running). Not run in this session: the machine's Docker engine had no free disk.

```bash
docker compose up -d --wait db
```

2. Ask the server which version it is (after `make up`).

```bash
docker compose exec db psql -U cited -d cited -c 'select version()'
```

3. List the tables (after `make db`).

```bash
docker compose exec db psql -U cited -d cited -c '\dt'
```

4. Check that the compose file parses; this needs no running engine.

```bash
docker compose config -q && echo 'docker-compose.yml is valid'
```

What you should see (captured from this repository):

```text
docker-compose.yml is valid
```

5. The comment at the top of the check queries.

```bash
sed -n 1,3p sql/003_queries.sql
```

What you should see (captured from this repository):

```text
-- The queries the service and the lesson's checks run, each with a line on what it shows.
-- Parameters in :name form are psql variables: psql -v question_vector="'[...]'" -f sql/003_queries.sql
```

## Mistakes people make

- **Using the superuser for the application.** The service connects as the project's own role. Real deployments inject a secret instead of the local value.
- **Committing credentials.** `cited`/`cited` is a local test value that exists only inside a throwaway container; the compose file says so.
- **Racing the server's start-up.** `make db` waits until a query works before applying the schema.
- **Forgetting that `down -v` deletes data.** That is the point for a demo; a real database would keep its volume.
- **Mixing SQL dialects.** The SQLite files and the PostgreSQL files are written for different engines.

## Check yourself

1. What is the difference between SQLite and PostgreSQL?

   *Answer:* SQLite is a library using one file; PostgreSQL is a server that many clients connect to.

2. Why is the host port 55432?

   *Answer:* To avoid a clash with a PostgreSQL already using 5432; Docker maps 55432 to the container's 5432.

3. What does `pg_isready` check?

   *Answer:* Whether the server accepts connections.

4. What does `-v ON_ERROR_STOP=1` do in `psql`?

   *Answer:* Stops at the first SQL error instead of continuing.

5. Where is the data stored?

   *Answer:* In a Docker volume named `dbdata`, removed by `make down`.

## Further reading

- PostgreSQL 17 documentation, https://www.postgresql.org/docs/17/ and the Docker image, https://hub.docker.com/_/postgres (not run in this session because the machine's Docker engine was unavailable; the compose file was validated with `docker compose config`).
