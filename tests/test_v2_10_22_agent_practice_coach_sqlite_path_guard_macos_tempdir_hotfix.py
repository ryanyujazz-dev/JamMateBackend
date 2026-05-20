from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import (
    PRACTICE_COACH_SQLITE_PATH_GUARD_MACOS_TEMPDIR_HOTFIX_VERSION,
    is_allowed_practice_coach_sqlite_path,
)

ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"


def test_sqlite_path_guard_allows_current_system_tempdir_resolved_root(monkeypatch) -> None:
    macos_temp_root = "/private/var/folders/mock/T"
    monkeypatch.setattr("tempfile.gettempdir", lambda: macos_temp_root)

    assert is_allowed_practice_coach_sqlite_path(
        "/private/var/folders/mock/T/pytest-of-user/test-case/practice_coach.sqlite3"
    )


def test_sqlite_path_guard_still_rejects_unsafe_absolute_paths(monkeypatch) -> None:
    monkeypatch.setattr("tempfile.gettempdir", lambda: "/private/var/folders/mock/T")

    assert not is_allowed_practice_coach_sqlite_path("/private/var/folders/mock/not-temp/practice_coach.sqlite3")
    assert not is_allowed_practice_coach_sqlite_path("/tmp/../etc/practice_coach.sqlite3")
    assert not is_allowed_practice_coach_sqlite_path("/tmp/jammate_api_key.sqlite3")
    assert not is_allowed_practice_coach_sqlite_path("/tmp/practice_coach.txt")


def test_unified_message_endpoint_accepts_sqlite_path_under_resolved_tempdir(monkeypatch, tmp_path: Path) -> None:
    client = TestClient(app)
    temp_root = tmp_path / "system-temp-root"
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(temp_root))

    payload = {
        "userId": "local-dev-user",
        "sessionId": "v2-10-22-tempdir",
        "deviceId": "harmonyos-device-local",
        "userMessage": "今天20分钟想练Bossa",
        "sqliteDbPath": str(temp_root / "pytest-of-user" / "practice_coach.sqlite3"),
        "llmActionDecisionResult": {
            "responseType": "ask_clarifying_question",
            "message": "你今天想重点练 Bossa 的节奏稳定还是换和弦衔接？",
            "missingFields": ["practice_detail"],
            "suggestedReplies": ["节奏稳定", "换和弦衔接"],
        },
    }

    response = client.post(ROUTE, json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["responseType"] == "ask_clarifying_question"
    assert body["debug"]["sqlitePathGuardMacOSTempdirHotfixVersion"] == PRACTICE_COACH_SQLITE_PATH_GUARD_MACOS_TEMPDIR_HOTFIX_VERSION
    assert body["debug"]["practiceCoachStateStoreIo"]["write"]["blockedReasons"] == []
    assert body["safety"]["startsRoutine"] is False
    assert body["safety"]["callsEngineAdapter"] is False


def test_v2_10_22_docs_record_macos_tempdir_guard_hotfix() -> None:
    root = Path(__file__).resolve().parents[1]
    dev_doc = root / "docs" / "AGENT_PRACTICE_COACH_SQLITE_PATH_GUARD_MACOS_TEMPDIR_HOTFIX_V2_10_22.md"
    changelog = root / "docs" / "CHANGELOG_AGENT.md"
    api_doc = root / "docs" / "API_CONTRACT_V2.md"

    for path in (dev_doc, changelog, api_doc):
        text = path.read_text(encoding="utf-8")
        assert "v2_10_22" in text
        assert "macOS" in text or "/private/var/folders" in text
        assert "tempfile.gettempdir" in text
        assert "sqlite" in text.lower()
