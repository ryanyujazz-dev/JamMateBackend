from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
    build_context_persistence_sqlite_backend_readback_context_recovery_payload,
    build_context_persistence_sqlite_backend_readback_context_recovery_summary,
    build_context_persistence_sqlite_backend_store_payload,
    context_persistence_sqlite_backend_readback_context_recovery_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_sqlite_recovery_001",
        "currentGoal": "提高 Medium Swing ii-V-I comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120]},
        "avoid": ["too_fast_tempo"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_sqlite_recovery_001",
        "title": "SQLite Recovery Practice Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_sqlite_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "session_sqlite_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True},
    ]


def _approved_store_args(db_path: Path, *, idempotency_key: str = "idem_sqlite_recovery_001", trace_id: str = "trace_sqlite_recovery_store") -> dict:
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
        "candidateId": "candidate_sqlite_recovery_001",
        "confirmationId": "confirmation_sqlite_recovery_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
    }


def _readback_args(db_path: Path, *, idempotency_key: str = "idem_sqlite_recovery_001") -> dict:
    return {
        "backendReadbackEnabled": True,
        "executeBackendReadback": True,
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "idempotencyKey": idempotency_key,
        "userId": "dev_user",
        "limit": 3,
    }


def _write_store(db_path: Path, *, idempotency_key: str = "idem_sqlite_recovery_001") -> None:
    payload = build_context_persistence_sqlite_backend_store_payload(_approved_store_args(db_path, idempotency_key=idempotency_key)).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["backend_database_written"] is True


def test_sqlite_backend_readback_context_recovery_contract_is_read_only() -> None:
    spec = context_persistence_sqlite_backend_readback_context_recovery_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION == "v2_9_1"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-readback-context-recovery/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-readback-context-recovery"
    assert spec["execution_status"]["sqlite_backend_readback_implemented"] is True
    assert spec["execution_status"]["database_write_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_sqlite_backend_readback_blocks_without_explicit_gate_and_does_not_create_db(tmp_path: Path) -> None:
    db_path = tmp_path / "blocked_recovery.sqlite"
    payload = build_context_persistence_sqlite_backend_readback_context_recovery_payload({"sqliteDbPath": str(db_path), "environment": "test"}).to_dict()

    assert payload["validation"]["status"] == "sqlite_backend_readback_context_recovery_blocked"
    assert "backend_readback_enabled_must_be_true" in payload["validation"]["blocked_reasons"]
    assert "execute_backend_readback_must_be_true" in payload["validation"]["blocked_reasons"]
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["storage_written"] is False
    assert not db_path.exists()


def test_sqlite_backend_readback_recovers_context_packet_from_persisted_record(tmp_path: Path) -> None:
    db_path = tmp_path / "agent_context_recovery.sqlite"
    _write_store(db_path)

    payload_obj = build_context_persistence_sqlite_backend_readback_context_recovery_payload(
        _readback_args(db_path),
        trace_id="trace_sqlite_recovery_readback",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_readback_context_recovery_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_1"
    assert payload["validation"]["status"] == "sqlite_backend_readback_context_recovery_ready"
    assert payload["backend_database_read"] is True
    assert payload["sqlite_connection_created"] is True
    assert payload["sqlite_rows_read"] == 1
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["recovered_context_summary"]["profile_context_present"] is True
    assert payload["recovered_context_summary"]["active_plan_context_present"] is True
    assert payload["recovered_context_summary"]["routine_history_context_present"] is True
    assert payload["recovery_packet_preview"]["context_packet_section_ready"] is True
    assert summary["profile_context_recovered"] is True
    assert summary["active_plan_context_recovered"] is True
    assert summary["routine_history_context_recovered"] is True
    assert summary["backend_database_read"] is True
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)

    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        context_persistence_snapshot_context_intake=payload["recovered_context_packet_section"],
    )
    assert packet.learner_context["user_practice_profile_context"]["profile"]["current_goal"] == "提高 Medium Swing ii-V-I comping 稳定性"
    assert packet.learner_context["active_practice_plan_context"]["active_plan"]["title"] == "SQLite Recovery Practice Plan"
    assert packet.learner_context["routine_history_context"]["section_name"] == "practice_history_context"


def test_sqlite_backend_readback_can_filter_latest_record_by_user_without_duplicate_write(tmp_path: Path) -> None:
    db_path = tmp_path / "agent_context_recovery_latest.sqlite"
    _write_store(db_path, idempotency_key="idem_latest_001")
    _write_store(db_path, idempotency_key="idem_latest_002")

    payload = build_context_persistence_sqlite_backend_readback_context_recovery_payload(
        {**_readback_args(db_path, idempotency_key=""), "userId": "dev_user", "limit": 2},
        trace_id="trace_sqlite_recovery_latest",
    ).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_readback_context_recovery_ready"
    assert payload["sqlite_rows_read"] == 2
    assert payload["sqlite_rows_written"] is False
    assert payload["durable_backend_write_executed"] is False
    assert len(payload["recovered_records"]) == 2


def test_sqlite_backend_readback_missing_db_is_blocked_without_creation(tmp_path: Path) -> None:
    db_path = tmp_path / "missing_backend.sqlite"
    payload = build_context_persistence_sqlite_backend_readback_context_recovery_payload(_readback_args(db_path)).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_readback_context_recovery_blocked"
    assert "sqlite_backend_readback_failed:sqlite_db_path_not_found" in payload["validation"]["blocked_reasons"]
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_read"] == 0
    assert not db_path.exists()


def test_context_and_runtime_manifests_advertise_sqlite_backend_readback_recovery() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_sqlite_backend_readback_context_recovery_spec_route"] == "GET /agent/context/persistence-sqlite-backend-readback-context-recovery/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_sqlite_backend_readback_context_recovery"] == "POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview"
    assert runtime["context_persistence_sqlite_backend_readback_context_recovery"]["version"] == "v2_9_1"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_readback_context_recovery"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_sqlite_backend_readback_context_recovery_version"] == "v2_9_1"


def test_api_sqlite_backend_readback_context_recovery_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "api_backend_recovery.sqlite"
    _write_store(db_path, idempotency_key="idem_api_recovery")
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-readback-context-recovery/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_9_1"

    response = client.post(
        "/agent/context/persistence-sqlite-backend-readback-context-recovery/preview",
        json=_readback_args(db_path, idempotency_key="idem_api_recovery"),
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_sqlite_backend_readback_context_recovery_version"] == "v2_9_1"
    assert response["context_persistence_sqlite_backend_readback_context_recovery_summary"]["validation_status"] == "sqlite_backend_readback_context_recovery_ready"
    assert response["backend_database_read"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_rows_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_sqlite_backend_readback_context_recovery_command(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    db_path = tmp_path / "terminal_backend_recovery.sqlite"
    _write_store(db_path, idempotency_key="idem_terminal_recovery")
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_readback_context_recovery(_readback_args(db_path, idempotency_key="idem_terminal_recovery"))
    assert response["ok"] is True
    assert response["context_persistence_sqlite_backend_readback_context_recovery_summary"]["profile_context_recovered"] is True
    assert response["storage_written"] is False
    assert response["routine_start_enabled"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-sqlite-backend-readback-context-recovery " + json.dumps(_readback_args(db_path, idempotency_key="idem_terminal_recovery"), ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceSqliteBackendReadbackContextRecovery>" in out
    assert "validation_status: sqlite_backend_readback_context_recovery_ready" in out
    assert "profile_context_recovered: True" in out
    assert "sqlite_rows_written: false" in out
    assert "routine_start_enabled: false" in out


def test_sqlite_backend_readback_recovery_does_not_import_engine_or_modify_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_V2_9_1.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
