import json
from datetime import date
from typing import Any

import httpx
import pytest

from cited_answers.domain.errors import PermanentModelError, RecordingMissing, TransientModelError
from cited_answers.domain.evaluation import InvalidQuestions, QuestionType
from cited_answers.domain.pages import PageStatus
from cited_answers.domain.prompts import PromptNotFound
from cited_answers.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
    text_key,
)
from cited_answers.infrastructure.env import ConfigurationError
from cited_answers.infrastructure.files import (
    FilePageSource,
    FilePromptStore,
    FileQuestionSource,
    read_threshold,
)
from cited_answers.infrastructure.memory_store import InMemoryChunkStore
from cited_answers.infrastructure.pg_store import vector_literal
from cited_answers.infrastructure.settings import AppSettings
from cited_answers.infrastructure.wiring import build_embedder, build_store
from tests.conftest import PAGES, HashingEmbedder, chunk


def embedder(handler):
    return OpenAICompatibleEmbedder(
        httpx.Client(transport=httpx.MockTransport(handler)), "http://local/v1/", "nomic", "k"
    )


def reply(vectors):
    return httpx.Response(
        200, json={"data": [{"index": i, "embedding": v} for i, v in reversed(list(enumerate(vectors)))]}
    )


def test_the_embedder_posts_the_texts_and_returns_vectors_in_input_order():
    seen: dict[str, Any] = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return reply([[1.0, 0.0], [0.0, 1.0]])

    vectors = embedder(handler).embed(["a", "b"])
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert seen["url"] == "http://local/v1/embeddings"
    assert seen["body"] == {"model": "nomic", "input": ["a", "b"]}
    assert seen["auth"] == "Bearer k"
    assert embedder(handler).name == "nomic"


@pytest.mark.parametrize("status", [429, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        embedder(lambda r: httpx.Response(status)).embed(["a"])


def test_a_client_error_a_dropped_connection_and_a_bad_shape_are_told_apart():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        embedder(lambda r: httpx.Response(400, text="no")).embed(["a"])

    def refuse(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        embedder(refuse).embed(["a"])
    with pytest.raises(PermanentModelError, match="unexpected embeddings response"):
        embedder(lambda r: httpx.Response(200, json={"nope": 1})).embed(["a"])
    with pytest.raises(PermanentModelError, match="asked for 2"):
        embedder(lambda r: reply([[1.0]])).embed(["a", "b"])


def test_recorded_vectors_survive_a_round_trip_through_the_file(tmp_path):
    path = tmp_path / "e.jsonl"
    recorder = RecordingEmbedder(HashingEmbedder(8), EmbeddingStore(path))
    first = recorder.embed(["hello world", "hello world", "other"])
    assert first[0] == first[1]
    replay = RecordedEmbedder(EmbeddingStore(path), "nomic")
    again = replay.embed(["hello world", "other"])
    assert again[0] == pytest.approx(first[0], rel=1e-6)
    assert replay.name == "nomic"
    assert recorder.name == "hashing"
    assert len(EmbeddingStore(path)) == 2


def test_a_known_text_is_not_sent_to_the_live_embedder_again(tmp_path):
    live = HashingEmbedder(8)
    recorder = RecordingEmbedder(live, EmbeddingStore(tmp_path / "e.jsonl"))
    recorder.embed(["a", "b"])
    recorder.embed(["a", "c"])
    assert live.calls == [["a", "b"], ["c"]]


def test_an_unrecorded_text_names_itself_and_the_fix(tmp_path):
    with pytest.raises(RecordingMissing, match=r"starting 'zzz'.*make record"):
        RecordedEmbedder(EmbeddingStore(tmp_path / "none.jsonl")).embed(["zzz"])


def test_a_folder_of_embedding_files_is_one_store(tmp_path):
    for name, text in (("one.jsonl", "x"), ("two.jsonl", "y")):
        RecordingEmbedder(HashingEmbedder(4), EmbeddingStore(tmp_path / name)).embed([text])
    store = EmbeddingStore(tmp_path)
    assert store.get(text_key("x")) is not None
    assert store.get(text_key("y")) is not None


def test_the_memory_store_ranks_by_cosine_and_reports_similarities():
    store = InMemoryChunkStore()
    store.replace_all([chunk("a:0", "x"), chunk("b:0", "y")], [[1.0, 0.0], [0.0, 1.0]])
    assert store.vector_search([1.0, 0.1], 2)[0][0] == "a:0"
    assert store.similarities([1.0, 0.0], ["b:0", "a:0", "zzz"]) == {"b:0": 0.0, "a:0": 1.0}
    assert [c.id for c in store.chunks()] == ["a:0", "b:0"]
    with pytest.raises(ValueError, match="one vector per chunk"):
        store.replace_all([chunk("a:0", "x")], [])


def test_pgvectors_text_form_is_a_bracketed_comma_list():
    assert vector_literal([1.0, 0.25, -3.5]) == "[1,0.25,-3.5]"


def test_page_files_are_read_from_a_folder(tmp_path):
    (tmp_path / "a.md").write_text(
        "---\nid: a\ntitle: A\nupdated: 2026-01-02\nstatus: retired\n---\n# A\n\n## S\n\nText here.\n"
    )
    (page,) = FilePageSource(tmp_path).pages()
    assert (page.id, page.status, page.updated) == ("a", PageStatus.RETIRED, date(2026, 1, 2))


def test_the_real_help_center_has_sixty_pages_three_retired_and_ten_error_codes():
    from pathlib import Path

    pages = FilePageSource(Path(__file__).resolve().parents[3] / "data" / "pages").pages()
    assert len(pages) == 60
    assert sorted(p.id for p in pages if p.status is PageStatus.RETIRED) == [
        "p-return-fee-old",
        "p-return-window-old",
        "p-ship-costs-old",
    ]
    assert sum(p.id.startswith("p-error-") for p in pages) == 10
    assert all(p.sections for p in pages)


def test_questions_are_read_per_split_and_a_bad_line_is_reported_with_its_number(tmp_path):
    good = {"id": "q1", "type": "exact", "question": "What?", "gold_page": "p", "fact": "f", "near_miss": False}
    (tmp_path / "dev.jsonl").write_text(json.dumps(good) + "\n\n" + '{"id": "q2", "type": "nonsense"}\n')
    source = FileQuestionSource(tmp_path)
    with pytest.raises(InvalidQuestions, match=r"dev\.jsonl:3"):
        source.load("dev")
    (tmp_path / "dev.jsonl").write_text(json.dumps(good) + "\n")
    (question,) = source.load("dev")
    assert question.type is QuestionType.EXACT


def test_prompt_files_need_a_matching_version_line(tmp_path):
    folder = tmp_path / "answer"
    folder.mkdir()
    (folder / "v1.md").write_text("---\nversion: v1\n---\nBe brief.\n")
    (folder / "v2.md").write_text("---\nversion: v9\n---\nx\n")
    (folder / "v3.md").write_text("no front matter")
    store = FilePromptStore(tmp_path)
    assert store.load("answer", "v1").text == "Be brief."
    for version, message in (("v2", "says 'v9'"), ("v3", "front matter"), ("v4", "no prompt file")):
        with pytest.raises(PromptNotFound, match=message):
            store.load("answer", version)


def test_the_threshold_file_is_optional(tmp_path):
    assert read_threshold(tmp_path / "none.json") is None
    (tmp_path / "t.json").write_text('{"threshold": 0.61}')
    assert read_threshold(tmp_path / "t.json") == 0.61


def test_settings_have_defaults_and_validate(tmp_path):
    settings = AppSettings.from_env({})
    assert settings.index_backend == "memory"
    assert settings.port == 8080
    assert settings.refusal_threshold is None
    assert AppSettings.from_env({"REFUSAL_THRESHOLD": "0.6", "LOG_LEVEL": "debug"}).refusal_threshold == 0.6
    for bad, name in (
        ({"REFUSAL_THRESHOLD": "high"}, "REFUSAL_THRESHOLD"),
        ({"INDEX_BACKEND": "redis"}, "INDEX_BACKEND"),
        ({"HTTP_PORT": "0"}, "HTTP_PORT"),
        ({"EMBEDDER_PROVIDER": "x"}, "EMBEDDER_PROVIDER"),
    ):
        with pytest.raises(ConfigurationError, match=name):
            AppSettings.from_env(bad)


def test_wiring_builds_the_recorded_embedder_the_live_one_and_the_stores(tmp_path):
    from cited_answers.infrastructure.pg_store import PgVectorChunkStore

    recorded = build_embedder(AppSettings.from_env({"EMBEDDINGS_PATH": str(tmp_path)}), {})
    assert isinstance(recorded, RecordedEmbedder)
    live = build_embedder(AppSettings.from_env({"EMBEDDER_PROVIDER": "openai-compatible"}), {})
    assert isinstance(live, OpenAICompatibleEmbedder)
    recording = build_embedder(
        AppSettings.from_env({"EMBEDDER_PROVIDER": "openai-compatible", "EMBEDDINGS_PATH": str(tmp_path / "e.jsonl")}),
        {"RECORD": "on"},
    )
    assert isinstance(recording, RecordingEmbedder)
    assert isinstance(build_store(AppSettings.from_env({})), InMemoryChunkStore)
    assert isinstance(build_store(AppSettings.from_env({"INDEX_BACKEND": "pgvector"})), PgVectorChunkStore)
    assert PAGES
