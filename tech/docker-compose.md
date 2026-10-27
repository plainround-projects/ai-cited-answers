# Docker Compose

## What it is

**Docker Compose** describes and runs a set of related containers with one file and one command. Instead of typing a long `docker run` with ports, volumes and variables for each container, you write them once in `docker-compose.yml` (a YAML file, see `yaml.md`) and run `docker compose up`. The file defines **services** (the containers), **volumes** (storage that outlives containers) and the **network** the containers share (created automatically).

## Why this repository uses it

It turns "start the database, wait until it is ready, then start the service" into a declared fact with a health check and a dependency, instead of a README paragraph. The file also records the exact image, the ports and the credentials of the local setup, so a new machine reproduces it.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | the whole file |
| `Makefile` | the targets that call `docker compose` |
| `Dockerfile` | `build: .` uses it |

## How it works underneath

**Project, network, names.** Compose gives the project a name (the `name:` key), creates a network `<project>_default` that all services join, and names containers `<project>-<service>-<n>`. Services reach each other by service name: the `api` service connects to the database at the host name `db`.

**`up` and `down`.** `docker compose up -d --wait SERVICE` creates and starts the containers (detached, `-d`) and waits for their health checks. `docker compose down` stops and removes them; `-v` also removes the named volumes, deleting their data.

**Interpolation.** `${NAME:-default}` inside the file is replaced from the shell environment or a `.env` file next to the compose file.

**Profiles.** A service with `profiles: [...]` starts only when one of its profiles is activated.

**Host vs. container ports.** In `"55432:5432"` the left number is the port on your computer, the right one the port inside the container.

**Validation without an engine.** `docker compose config` parses and checks the file and prints the resolved result; it does not need the Docker engine to be running.

## Walkthrough of this repository's use

`docker-compose.yml`, the whole file, block by block. Under each block, every line is explained.

```yaml
# Postgres 17 with the pgvector extension for the chunk index, and the service itself (profile "api").
name: ai-cited-answers
```

- `# Postgres 17 with the pgvector extension for the chunk index, and the service itself (profile "api").`: A comment (YAML ignores text after `#`).
- `name: ai-cited-answers`: The project name. Compose prefixes the names of containers, networks and volumes with it (for example `ai-cited-answers-db-1`).

```yaml
services:
  db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: cited
      POSTGRES_PASSWORD: cited       # local development only; real deployments inject a secret
      POSTGRES_DB: cited
    ports:
      - "55432:5432"
    volumes:
      - dbdata:/var/lib/postgresql/data
    healthcheck:
      # TCP, not the socket: while the image initializes a fresh volume, a temporary server listens on the socket only
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U cited -d cited"]
      interval: 3s
      timeout: 5s
      retries: 100        # about five minutes: initializing a fresh volume is slow on a busy machine
```

- `services:`: Starts the mapping of services. A **service** is one container definition (one program that runs).
- `db:`: A service named `db`.
- `image: pgvector/pgvector:pg17`: Run this ready-made image from Docker Hub: `pgvector/pgvector:pg17`. PostgreSQL 17 with the pgvector extension installed.
- `environment:`: Environment variables for the container.
- `POSTGRES_USER: cited`: `POSTGRES_USER`: the database user the image creates on first start.
- `POSTGRES_PASSWORD: cited`: (The comment on this line says: local development only; real deployments inject a secret.) `POSTGRES_PASSWORD`: its password (a local test value).
- `POSTGRES_DB: cited`: `POSTGRES_DB`: the database the image creates on first start.
- `ports:`: Port mappings between the machine and the container.
- `- "55432:5432"`: Publish the container's port 5432 on the machine's port 55432 (`HOST:CONTAINER`). The program is then reachable at `localhost:55432`.
- `volumes:`: Starts a list (inside a service) of mounts, or the top-level definition of named volumes.
- `- dbdata:/var/lib/postgresql/data`: Mount the **named volume** `dbdata` at `/var/lib/postgresql/data` inside the container. A named volume is storage managed by Docker that outlives the container, so the data survives a restart (`down -v` deletes it).
- `healthcheck:`: How to test the container's health (overrides any check in the image).
- `# TCP, not the socket: while the image initializes a fresh volume, a temporary server listens on the socket only`: A comment (YAML ignores text after `#`).
- `test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U cited -d cited"]`: The check, run through the container's shell (`CMD-SHELL`): `pg_isready -h 127.0.0.1 -U cited -d cited`. `pg_isready` asks PostgreSQL whether it accepts connections; `-h 127.0.0.1` makes it use TCP.
- `interval: 3s`: Run the check every 3s.
- `timeout: 5s`: A check that takes longer than 5s counts as failed.
- `retries: 100`: (The comment on this line says: about five minutes: initializing a fresh volume is slow on a busy machine.) Mark the container unhealthy after 100 failures in a row.

```yaml
  api:
    profiles: ["api"]
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      INDEX_BACKEND: pgvector
      DATABASE_URL: postgresql://cited:cited@db:5432/cited
      MODEL_PROVIDER: ${MODEL_PROVIDER:-openai-compatible}
      EMBEDDER_PROVIDER: ${EMBEDDER_PROVIDER:-openai-compatible}
      OPENAI_BASE_URL: ${OPENAI_BASE_URL:-http://host.docker.internal:11434/v1}
      MODEL_NAME: ${MODEL_NAME:-qwen2.5:1.5b}
      HTTP_HOST: 0.0.0.0
    ports:
      - "8080:8080"
```

- `api:`: A service named `api`.
- `profiles: ["api"]`: Only start this service when the profile `api` is switched on (`docker compose --profile api up`). Without the profile, `up` starts `db` alone.
- `build: .`: Build the image from the Dockerfile in this folder instead of pulling one.
- `depends_on:`: Start order: this service waits for the services listed below.
- `db:`: A service named `db`.
- `condition: service_healthy`: Wait not just for the database container to exist but for its health check to report healthy.
- `environment:`: Environment variables for the container.
- `INDEX_BACKEND: pgvector`: `INDEX_BACKEND`: `memory` keeps the search index in the program, `pgvector` keeps it in PostgreSQL.
- `DATABASE_URL: postgresql://cited:cited@db:5432/cited`: `DATABASE_URL`: how to reach PostgreSQL: user, password, host, port and database name in one address.
- `MODEL_PROVIDER: ${MODEL_PROVIDER:-openai-compatible}`: `MODEL_PROVIDER`: which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos. `${NAME:-default}` means: use the shell variable `NAME` if set, otherwise `default`.
- `EMBEDDER_PROVIDER: ${EMBEDDER_PROVIDER:-openai-compatible}`: `EMBEDDER_PROVIDER`: which embedding model turns text into vectors: `recorded` replays saved vectors, `openai-compatible` calls a local server. `${NAME:-default}` means: use the shell variable `NAME` if set, otherwise `default`.
- `OPENAI_BASE_URL: ${OPENAI_BASE_URL:-http://host.docker.internal:11434/v1}`: `OPENAI_BASE_URL`: the web address of an OpenAI-compatible server (ollama listens on `http://localhost:11434/v1`). `${NAME:-default}` means: use the shell variable `NAME` if set, otherwise `default`.
- `MODEL_NAME: ${MODEL_NAME:-qwen2.5:1.5b}`: `MODEL_NAME`: the model id to ask for (for example `qwen2.5:0.5b`); each provider has a default. `${NAME:-default}` means: use the shell variable `NAME` if set, otherwise `default`.
- `HTTP_HOST: 0.0.0.0`: `HTTP_HOST`: the network address the HTTP server listens on (`127.0.0.1` means this computer only).
- `ports:`: Port mappings between the machine and the container.
- `- "8080:8080"`: Publish the container's port 8080 on the machine's port 8080 (`HOST:CONTAINER`). The program is then reachable at `localhost:8080`.

```yaml
volumes:
  dbdata:
```

- `volumes:`: Starts a list (inside a service) of mounts, or the top-level definition of named volumes.
- `dbdata:`: Declares the named volume `dbdata` (Docker creates it on first use).

### The compose commands this repository uses

- `docker compose --profile api down -v`
- `docker compose --profile api up -d --build --wait`
- `docker compose exec -T db psql -U cited -d cited -qc 'select 1'`
- `docker compose exec -T db psql -U cited -d cited -v ON_ERROR_STOP=1 -q`
- `docker compose up -d --wait db`

## Try it yourself

1. The installed Compose.

```bash
docker compose version
```

What you should see (captured from this repository):

```text
Docker Compose version v2.23.0-desktop.1
```

2. Parse and validate the file; no engine needed. Nothing is printed on success except our message.

```bash
docker compose config -q && echo 'docker-compose.yml is valid'
```

What you should see (captured from this repository):

```text
docker-compose.yml is valid
```

3. The file after Compose resolved it: defaults filled in, paths made absolute, short forms expanded.

```bash
docker compose config | sed -n 1,25p
```

What you should see (captured from this repository):

```text
name: ai-cited-answers
services:
  db:
    environment:
      POSTGRES_DB: cited
      POSTGRES_PASSWORD: cited
      POSTGRES_USER: cited
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -h 127.0.0.1 -U cited -d cited
      timeout: 5s
      interval: 3s
      retries: 100
    image: pgvector/pgvector:pg17
    networks:
      default: null
    ports:
      - mode: ingress
        target: 5432
        published: "55432"
        protocol: tcp
    volumes:
      - type: volume
        source: dbdata
```

4. Start the services and wait for them to be healthy. Not run in this session (the machine's Docker engine had no free disk space).

```bash
docker compose up -d --wait
```

5. Stop everything and delete the volumes. Not run here.

```bash
docker compose down -v
```

## Mistakes people make

- **Using `depends_on` without a health check.** It only orders start-up; the service may start before the database accepts connections. Here the condition is `service_healthy`.
- **Expecting `down` to keep data.** `down -v` removes volumes by design for a clean demo.
- **Real secrets in the file.** The credentials here are local test values for a throwaway container.
- **Mixing up host and container ports.** `HOST:CONTAINER`; services on the same network use the container port.
- **Binding a service to `127.0.0.1` inside the container.** Then the published port cannot reach it. Services in containers listen on `0.0.0.0` (`HTTP_HOST=0.0.0.0`).

## Check yourself

1. What does `docker compose up -d --wait db` do?

   *Answer:* Starts the `db` service in the background and waits until it is healthy.

2. What does `55432:5432` mean?

   *Answer:* Machine port 55432 forwards to container port 5432.

3. What is a named volume?

   *Answer:* Storage managed by Docker that survives container removal until `down -v`.

4. How does one service reach another?

   *Answer:* By its service name on the shared network.

5. How can you check the file with no running engine?

   *Answer:* `docker compose config -q`.

## Further reading

- Compose file reference, https://docs.docker.com/reference/compose-file/ (the file was validated here with `docker compose config`, Compose v2.23; containers were not started because the machine's Docker engine had no free disk).
