import json
from pathlib import Path
from typing import Any

import pytest

from cited_answers.interfaces import server
from cited_answers.interfaces.cli import EXIT_OK, main

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def replay(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGES_DIR", str(REPO / "data" / "pages"))
    monkeypatch.setenv("QUESTIONS_DIR", str(REPO / "data" / "questions"))
    monkeypatch.setenv("PROMPTS_DIR", str(REPO / "prompts"))
    monkeypatch.setenv("THRESHOLD_PATH", str(tmp_path / "threshold.json"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("EMBEDDER_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(REPO / "tests" / "fixtures" / "recordings"))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(REPO / "tests" / "fixtures" / "embeddings"))
    monkeypatch.setenv("REFUSAL_THRESHOLD", "0.648")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path


def test_ingest_reports_pages_chunks_and_the_skipped_retired_pages(replay, capsys):
    assert main(["ingest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "indexed 57 current pages as 68 chunks" in out
    assert "p-return-window-old" in out


def test_a_known_question_is_answered_from_its_recording_with_citations(replay, capsys):
    assert main(["ask", "How many days do I have to return an item?"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "[p-return-window:0]" in out
    assert "answered: none" in out


def test_a_question_far_from_every_page_is_refused_before_the_model(replay, capsys):
    assert main(["ask", "Do you ship to Antarctica?"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "I don't have information about that" in out
    assert "below_threshold" in out


def test_retrieval_prints_a_row_per_type_and_mode_with_intervals(replay, capsys):
    assert main(["retrieval", "--split", "dev"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "answerable vector" in out
    assert "exact      fused" in out
    assert "Wilson" in out


def test_tuning_writes_the_threshold_from_the_dev_questions_only(replay, monkeypatch, capsys):
    monkeypatch.delenv("REFUSAL_THRESHOLD")
    assert main(["tune-threshold"]) == EXIT_OK
    written = json.loads((replay / "threshold.json").read_text())
    assert written["tuned_on"] == "dev"
    assert written["threshold"] == 0.648
    assert "wrongly refuses" in capsys.readouterr().out


def test_evaluate_prints_both_grades_dumps_every_answer_and_writes_a_report(replay, capsys):
    dump = replay / "answers.jsonl"
    code = main(
        [
            "evaluate",
            "--split",
            "dev",
            "--prompt",
            "v2",
            "--dump",
            str(dump),
            "--write-report",
            "--hand-grades",
            str(REPO / "evals" / "hand_grades.jsonl"),
        ]
    )
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "answer correct (judge)" in out
    assert "judge agreement with hand grades: 21/22" in out
    assert len(dump.read_text().splitlines()) == 30
    assert (replay / "reports" / "dev-answer-v2.txt").read_text().startswith("== dev set, answer prompt v2")


def test_serve_builds_the_app_and_hands_it_to_uvicorn(replay, monkeypatch):
    captured: dict[str, Any] = {}
    monkeypatch.setattr(server.uvicorn, "run", lambda app, **kw: captured.update(app=app, **kw))  # type: ignore[attr-defined]
    assert main(["serve"]) == EXIT_OK
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8080
    assert captured["timeout_graceful_shutdown"] == 10
