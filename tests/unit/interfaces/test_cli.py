import json
from pathlib import Path

import pytest

from cited_answers.infrastructure.settings import AppSettings
from cited_answers.interfaces import cli
from cited_answers.interfaces.cli import EXIT_CONFIG, EXIT_OK, main

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGES_DIR", str(REPO / "data" / "pages"))
    monkeypatch.setenv("QUESTIONS_DIR", str(REPO / "data" / "questions"))
    monkeypatch.setenv("PROMPTS_DIR", str(REPO / "prompts"))
    monkeypatch.setenv("THRESHOLD_PATH", str(tmp_path / "threshold.json"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("EMBEDDER_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(REPO / "tests" / "fixtures" / "recordings"))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(REPO / "tests" / "fixtures" / "embeddings"))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path


def test_a_missing_recording_is_reported_not_raised(workspace, monkeypatch, capsys):
    monkeypatch.setenv("EMBEDDINGS_PATH", str(workspace / "none"))
    assert main(["retrieval", "--split", "dev"]) != EXIT_OK
    assert "no recorded embedding" in capsys.readouterr().err


def test_a_bad_environment_value_is_a_configuration_error(workspace, monkeypatch, capsys):
    monkeypatch.setenv("INDEX_BACKEND", "redis")
    assert main(["retrieval", "--split", "dev"]) == EXIT_CONFIG
    assert "INDEX_BACKEND" in capsys.readouterr().err


def test_a_missing_prompt_is_a_configuration_error(workspace, monkeypatch, capsys):
    monkeypatch.setenv("ANSWER_PROMPT_VERSION", "v99")
    assert main(["ask", "How many days do I have to return an item?"]) == EXIT_CONFIG
    assert "no prompt file" in capsys.readouterr().err


def test_hand_grades_are_read_as_question_id_to_verdict(tmp_path):
    path = tmp_path / "g.jsonl"
    path.write_text('{"question_id": "q1", "correct": true}\n\n{"question_id": "q2", "correct": false}\n')
    assert cli._hand_grades(path) == {"q1": True, "q2": False}


def test_the_threshold_comes_from_the_override_then_the_file_then_the_default(workspace, monkeypatch):
    settings = AppSettings.from_env()
    assert cli._threshold(settings) == cli.DEFAULT_THRESHOLD
    (workspace / "threshold.json").write_text(json.dumps({"threshold": 0.61}))
    assert cli._threshold(AppSettings.from_env()) == 0.61
    monkeypatch.setenv("REFUSAL_THRESHOLD", "0.7")
    assert cli._threshold(AppSettings.from_env()) == 0.7
