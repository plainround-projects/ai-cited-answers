# The service as an image. It reads its index from Postgres (INDEX_BACKEND=pgvector) and calls the model named by
# MODEL_PROVIDER; the key, if any, comes from the environment at run time.
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY prompts ./prompts
COPY evals/threshold.json ./evals/threshold.json

RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=180s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3).status == 200 else 1)"
CMD ["cited", "serve"]
