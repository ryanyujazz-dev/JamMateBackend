from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
    build_context_persistence_sqlite_backend_store_payload,
    build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload,
    build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary,
    context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_sqlite_terminal_memory_001",
        "currentGoal": "提高 Medium Swing ii-V-I comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 140]},
        "avoid": ["too_fast_tempo"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_sqlite_terminal_memory_001",
        "title": "SQLite Terminal Memory Practice Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_terminal_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_terminal_002", "title": "Blue Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "session_sqlite_terminal_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True},
    ]


def _provider_result() -> dict:
    return {
        "content": {
            "guidance_mode": "continue_original_plan",
            "summary": "终端已从 SQLite 后端自动加载上下文，今天继续练 Medium Swing ii-V-I comping。",
            "recommended_focus": "ii-V-I comping 稳定性",
            "recommended_blocks": [
                {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 guide-tone voice leading"},
            ],
            "routine_candidates": [
                {"routineName": "SQLite autoload Medium Swing routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"},
            ],
            "profile_considerations": "匹配 SQLite 后端恢复出的 medium_swing 偏好、ii-V-I focus 和 90-120 bpm 舒适速度区间。",
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }


def _approved_store_args(db_path: Path, *, idempotency_key: str = "idem_sqlite_terminal_memory_001", trace_id: str = "trace_sqlite_terminal_memory_store") -> dict:
    return {
        "backendPersistenceEnabled": True,
        "executeBackendPersistence": True,
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "traceId": trace_id,
        "idempotencyKey": idempotency_key,
        "userId": "dev_user",
        "candidateKind": "practice_plan_persistence_candidate",
        "candidateId": "candidate_sqlite_terminal_memory_001",
        "confirmationId": "confirmation_sqlite_terminal_memory_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
    }


def _autoload_args(db_path: Path, *, idempotency_key: str = "idem_sqlite_terminal_memory_001") -> dict:
    return {
        "backendReadbackEnabled": True,
        "executeBackendReadback": True,
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "idempotencyKey": idempotency_key,
        "userId": "dev_user",
        "limit": 3,
        "availableMinutes": 25,
        "providerResult": _provider_result(),
    }


def _write_store(db_path: Path, *, idempotency_key: str = "idem_sqlite_terminal_memory_001") -> None:
    payload = build_context_persistence_sqlite_backend_store_payload(_approved_store_args(db_path, idempotency_key=idempotency_key)).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["backend_database_written"] is True


def test_sqlite_backend_terminal_memory_autoload_contract_is_terminal_memory_only() -> None:
    spec = context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION == "v2_9_3"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview"
    assert spec["terminal_command"] == "/persisted-context-autoload-sqlite"
    assert spec["execution_status"]["sqlite_backend_terminal_memory_autoload_preview_implemented"] is True
    assert spec["execution_status"]["terminal_session_memory_can_be_loaded_by_cli"] is True
    assert spec["execution_status"]["database_write_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_sqlite_backend_terminal_memory_autoload_blocks_without_readback_gates_and_does_not_create_db(tmp_path: Path) -> None:
    db_path = tmp_path / "blocked_terminal_memory.sqlite"
    payload = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload({"sqliteDbPath": str(db_path), "environment": "test"}).to_dict()

    assert payload["validation"]["status"] == "sqlite_backend_terminal_memory_autoload_preview_blocked"
    assert "sqlite_backend_readback_context_recovery_not_accepted" in payload["validation"]["blocked_reasons"]
    assert payload["terminal_memory_preview"]["terminal_session_memory_ready"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["storage_written"] is False
    assert not db_path.exists()


def test_sqlite_backend_terminal_memory_autoload_preview_reads_backend_and_prepares_memory(tmp_path: Path) -> None:
    db_path = tmp_path / "agent_context_terminal_memory.sqlite"
    _write_store(db_path)

    payload_obj = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload(
        _autoload_args(db_path),
        trace_id="trace_sqlite_terminal_memory_autoload",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_3"
    assert payload["validation"]["status"] == "sqlite_backend_terminal_memory_autoload_preview_ready"
    assert payload["backend_database_read"] is True
    assert payload["sqlite_connection_created"] is True
    assert payload["sqlite_rows_read"] == 1
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["terminal_session_memory_loaded_by_core"] is False
    assert payload["terminal_memory_preview"]["terminal_session_memory_ready"] is True
    memory = payload["terminal_memory_preview"]["terminal_session_memory"]
    assert memory["loaded"] is True
    assert "guidance_arguments" in memory
    assert memory["guidance_arguments"]["snapshotContextIntakePayload"]["payload_contract_version"] == "v2_8_16"
    assert payload["validation"]["profile_context_recovered"] is True
    assert payload["validation"]["active_plan_context_recovered"] is True
    assert payload["validation"]["routine_history_context_recovered"] is True
    assert summary["validation_status"] == "sqlite_backend_terminal_memory_autoload_preview_ready"
    assert summary["will_inject_into_next_today_practice_guidance_turn"] is True
    assert summary["llm_called"] is False
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)


def test_terminal_autoload_sqlite_loads_session_memory_then_next_today_guidance_uses_it(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_autoload_session.sqlite"
    _write_store(db_path, idempotency_key="idem_terminal_autoload_session")
    session = TerminalChatSession()

    autoload = session.context_persistence_sqlite_backend_terminal_memory_autoload_preview(
        _autoload_args(db_path, idempotency_key="idem_terminal_autoload_session")
    )
    assert autoload["ok"] is True
    assert autoload["memory_loaded"] is True
    assert autoload["terminal_session_memory_loaded_by_cli"] is True
    assert autoload["storage_written"] is False
    assert session.persisted_context_show()["memory_loaded"] is True

    response = session.respond("今天该练什么")
    assert response["ok"] is True
    assert response["persisted_context_terminal_memory_used"] is True
    assert response["payload_kind"] == "persisted_context_recovery_e2e"
    assert response["today_practice_guidance_action_card_summary"]["routine_candidate_count"] == 1
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_api_sqlite_backend_terminal_memory_autoload_preview_does_not_load_server_session(tmp_path: Path) -> None:
    db_path = tmp_path / "api_terminal_memory_autoload.sqlite"
    _write_store(db_path, idempotency_key="idem_api_terminal_memory")
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_9_3"

    response = client.post(
        "/agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview",
        json={"arguments": _autoload_args(db_path, idempotency_key="idem_api_terminal_memory")},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_sqlite_backend_terminal_memory_autoload_preview_version"] == "v2_9_3"
    assert response["context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary"]["validation_status"] == "sqlite_backend_terminal_memory_autoload_preview_ready"
    assert response["context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary"]["terminal_session_memory_ready"] is True
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["backend_database_read"] is True
    assert response["storage_written"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_autoload_sqlite_command_is_available(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    db_path = tmp_path / "terminal_command_autoload.sqlite"
    _write_store(db_path, idempotency_key="idem_terminal_command_autoload")
    exit_code = run_interactive_chat([
        "--once",
        "/persisted-context-autoload-sqlite " + json.dumps(_autoload_args(db_path, idempotency_key="idem_terminal_command_autoload"), ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceSqliteBackendTerminalMemoryAutoloadPreview>" in out
    assert "validation_status: sqlite_backend_terminal_memory_autoload_preview_ready" in out
    assert "memory_loaded: true" in out
    assert "will_inject_into_next_today_practice_guidance_turn: true" in out
    assert "storage_written: false" in out
    assert "routine_start_enabled: false" in out


def test_context_and_runtime_manifests_advertise_sqlite_backend_terminal_memory_autoload() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_sqlite_backend_terminal_memory_autoload_preview_spec_route"] == "GET /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_sqlite_backend_terminal_memory_autoload_preview"] == "POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview"
    assert runtime["context_persistence_sqlite_backend_terminal_memory_autoload_preview"]["version"] == "v2_9_3"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_terminal_memory_autoload_preview"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_sqlite_backend_terminal_memory_autoload_preview_version"] == "v2_9_3"


def test_sqlite_backend_terminal_memory_autoload_does_not_import_engine_or_modify_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_V2_9_3.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
