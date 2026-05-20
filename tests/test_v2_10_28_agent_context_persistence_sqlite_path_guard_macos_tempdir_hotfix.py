from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core import tool_invocation


COMPLETION_ROUTE = "/agent/harmonyos/routine-completion-record/execute"


def _completion_payload() -> dict:
    return {
        "userId": "local-dev-user",
        "sessionId": "practice-session-macos-tempdir-hotfix",
        "deviceId": "harmonyos-device-local",
        "routineCompletionRecord": {
            "routineId": "routine-macos-tempdir-hotfix",
            "routineTitle": "macOS Tempdir Hotfix Practice",
            "completedAt": "2026-05-20T20:30:00+08:00",
            "durationSeconds": 1200,
            "status": "completed",
            "items": [
                {
                    "itemId": "item-1",
                    "title": "Bossa core rhythm",
                    "type": "technical_practice",
                    "durationSeconds": 300,
                    "status": "completed",
                }
            ],
            "notes": "Verify context persistence guard accepts system tempdir.",
        },
    }


def test_context_persistence_guard_accepts_current_system_tempdir(tmp_path: Path, monkeypatch) -> None:
    fake_system_tempdir = tmp_path / "macos_like_system_tempdir"
    fake_system_tempdir.mkdir()
    candidate = fake_system_tempdir / "pytest-context-persistence.sqlite3"

    monkeypatch.setattr(tool_invocation.tempfile, "gettempdir", lambda: str(fake_system_tempdir))

    assert tool_invocation._is_allowed_context_persistence_sqlite_path(str(candidate)) is True


def test_context_persistence_guard_accepts_macos_private_var_tempdir_shape(monkeypatch) -> None:
    monkeypatch.setattr(tool_invocation.tempfile, "gettempdir", lambda: "/private/var/folders/abc123/T")

    assert (
        tool_invocation._is_allowed_context_persistence_sqlite_path(
            "/private/var/folders/abc123/T/pytest-123/context.sqlite3"
        )
        is True
    )


def test_context_persistence_guard_still_rejects_dangerous_paths(monkeypatch) -> None:
    monkeypatch.setattr(tool_invocation.tempfile, "gettempdir", lambda: "/private/var/folders/abc123/T")

    assert tool_invocation._is_allowed_context_persistence_sqlite_path("/etc/jammate/context.sqlite3") is False
    assert tool_invocation._is_allowed_context_persistence_sqlite_path("/tmp/prod-secrets/context.sqlite3") is False
    assert tool_invocation._is_allowed_context_persistence_sqlite_path("/tmp/context.txt") is False
    assert tool_invocation._is_allowed_context_persistence_sqlite_path("/tmp/../context.sqlite3") is False


def test_routine_completion_route_can_persist_to_current_system_tempdir(tmp_path: Path, monkeypatch) -> None:
    fake_system_tempdir = tmp_path / "route_system_tempdir"
    fake_system_tempdir.mkdir()
    sqlite_path = fake_system_tempdir / "routine-completion-context.sqlite3"

    monkeypatch.setattr(tool_invocation.tempfile, "gettempdir", lambda: str(fake_system_tempdir))
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(sqlite_path))

    body = TestClient(app).post(COMPLETION_ROUTE, json=_completion_payload()).json()

    assert body["ok"] is True
    assert body["code"] == "routine_completion_record_persisted"
    assert body["data"]["completionRecordPersisted"] is True
    assert body["debug"]["backendDatabaseWritten"] is True
    assert body["debug"]["sqliteRowsWritten"] is True
    assert "sqlite_db_path_not_allowed_for_practice_coach_state_store" not in body.get("debug", {}).get("blockedReasons", [])
    assert sqlite_path.exists()
