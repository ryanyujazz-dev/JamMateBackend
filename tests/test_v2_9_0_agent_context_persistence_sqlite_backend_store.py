from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
    build_context_persistence_sqlite_backend_store_payload,
    build_context_persistence_sqlite_backend_store_summary,
    context_persistence_sqlite_backend_store_contract,
)
from jammate_api.app import app


def _approved_args(path: Path) -> dict:
    return {
        "backendPersistenceEnabled": True,
        "executeBackendPersistence": True,
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "sqliteDbPath": str(path),
        "environment": "test",
        "traceId": "trace_backend_store",
        "candidateKind": "practice_plan_persistence_candidate",
        "candidateId": "candidate_001",
        "confirmationId": "confirmation_001",
        "userId": "user_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": {"primaryGoal": "Comp Blue Bossa with steady Bossa piano"},
        "practicePlan": {"title": "Blue Bossa comping", "planBlocks": [{"blockId": "b1", "minutes": 10}]},
        "routineHistoryRecords": [{"routineId": "r1", "completedAt": "2026-05-19T10:00:00Z"}],
    }


def _sqlite_counts(path: Path) -> dict[str, int]:
    with sqlite3.connect(path) as conn:
        return {
            "records": conn.execute("select count(*) from context_persistence_records").fetchone()[0],
            "idempotency": conn.execute("select count(*) from context_persistence_idempotency_keys").fetchone()[0],
            "trace_links": conn.execute("select count(*) from context_persistence_trace_links").fetchone()[0],
        }


def test_sqlite_backend_store_contract_is_explicit_backend_write_surface() -> None:
    spec = context_persistence_sqlite_backend_store_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION == "v2_9_0"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-store/spec"
    assert spec["execute_route"] == "POST /agent/context/persistence-sqlite-backend-store/execute"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-store"
    assert spec["execution_status"]["sqlite_backend_store_implemented"] is True
    assert spec["execution_status"]["backend_persistence_can_write_when_explicitly_enabled"] is True
    assert spec["execution_status"]["database_connection_created_only_after_gates"] is True
    assert spec["execution_status"]["idempotency_enforced"] is True
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["guards"]["payload_may_write_backend_sqlite_only_after_explicit_opt_in"] is True
    assert spec["guards"]["local_device_written"] is False
    assert "backendPersistenceEnabled=true" in spec["required_gates"]
    assert "context_persistence_records" in spec["tables"]
    assert "context_persistence_idempotency_keys" in spec["tables"]
    assert "context_persistence_trace_links" in spec["tables"]


def test_sqlite_backend_store_blocks_without_explicit_opt_in(tmp_path: Path) -> None:
    db_path = tmp_path / "blocked_context.db"
    payload = build_context_persistence_sqlite_backend_store_payload(
        {
            "sqliteDbPath": str(db_path),
            "userDecision": "approved",
            "confirmationStatus": "user_approved_future_executor_required",
            "environment": "test",
            "traceId": "trace_blocked_backend_store",
        }
    ).to_dict()

    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "sqlite_backend_store_blocked"
    assert "backend_persistence_enabled_must_be_true" in payload["validation"]["blocked_reasons"]
    assert "execute_backend_persistence_must_be_true" in payload["validation"]["blocked_reasons"]
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert db_path.exists() is False


def test_sqlite_backend_store_writes_sqlite_only_with_all_gates(tmp_path: Path) -> None:
    db_path = tmp_path / "agent_context_store.db"
    payload_obj = build_context_persistence_sqlite_backend_store_payload(
        _approved_args(db_path),
        trace_id="trace_backend_store_write",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_store_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_0"
    assert payload["adapter_mode"] == "explicit_opt_in_backend_sqlite_store"
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["storage_written"] is True
    assert payload["backend_database_written"] is True
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is True
    assert payload["sqlite_tables_created"] is True
    assert payload["sqlite_rows_written"] is True
    assert payload["sqlite_row_count_written"] == 3
    assert payload["durable_backend_write_executed"] is True
    assert payload["transaction_committed"] is True
    assert payload["readback_preview"]["record_found"] is True
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert summary["validation_status"] == "sqlite_backend_store_ready"
    assert summary["backend_database_written"] is True
    assert summary["readback_record_found"] is True

    counts = _sqlite_counts(db_path)
    assert counts == {"records": 1, "idempotency": 1, "trace_links": 1}

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("select record_json, trace_id from context_persistence_records").fetchone()
    record = json.loads(row[0])
    assert row[1] == "trace_backend_store_write"
    assert record["record_contract_version"] == "v2_9_0"
    assert record["user_id"] == "user_001"
    assert record["context_snapshot"]["sections"]["user_practice_profile"]["primaryGoal"] == "Comp Blue Bossa with steady Bossa piano"


def test_sqlite_backend_store_enforces_idempotency(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent_context.db"
    args = {**_approved_args(db_path), "idempotencyKey": "idem_backend_store_001"}

    first = build_context_persistence_sqlite_backend_store_payload(args).to_dict()
    second = build_context_persistence_sqlite_backend_store_payload(args).to_dict()

    assert first["validation"]["status"] == "sqlite_backend_store_ready"
    assert first["sqlite_rows_written"] is True
    assert first["sqlite_row_count_written"] == 3
    assert first["idempotent_replay"] is False
    assert second["validation"]["status"] == "sqlite_backend_store_idempotent_replay"
    assert second["validation"]["accepted"] is True
    assert second["sqlite_connection_created"] is True
    assert second["sqlite_tables_created"] is True
    assert second["sqlite_rows_written"] is False
    assert second["sqlite_row_count_written"] == 0
    assert second["storage_written"] is False
    assert second["backend_database_written"] is False
    assert second["idempotent_replay"] is True
    assert second["readback_preview"]["record_found"] is True
    assert _sqlite_counts(db_path) == {"records": 1, "idempotency": 1, "trace_links": 1}


def test_sqlite_backend_store_blocks_sensitive_or_non_dev_payload(tmp_path: Path) -> None:
    db_path = tmp_path / "sensitive_context.db"
    payload = build_context_persistence_sqlite_backend_store_payload(
        {
            **_approved_args(db_path),
            "environment": "prod",
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
        },
        trace_id="trace_sensitive_backend_store",
    ).to_dict()

    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "sqlite_backend_store_blocked"
    assert "sqlite_backend_store_v2_9_0_only_allows_dev_local_dev_or_test" in payload["validation"]["blocked_reasons"]
    assert "redaction_check_failed_or_forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    assert payload["sqlite_connection_created"] is False
    assert payload["backend_database_written"] is False
    assert db_path.exists() is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


def test_context_and_runtime_manifests_advertise_sqlite_backend_store() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_sqlite_backend_store_spec_route"] == "GET /agent/context/persistence-sqlite-backend-store/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_sqlite_backend_store"] == "POST /agent/context/persistence-sqlite-backend-store/execute"
    assert runtime["context_persistence_sqlite_backend_store"]["version"] == "v2_9_0"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_sqlite_backend_store"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_sqlite_backend_store_version"] == "v2_9_0"


def test_api_sqlite_backend_store_execute(tmp_path: Path) -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-store/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_9_0"

    db_path = tmp_path / "api_context_store.db"
    response = client.post(
        "/agent/context/persistence-sqlite-backend-store/execute",
        json={**_approved_args(db_path), "traceId": "trace_api_backend_store"},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_sqlite_backend_store_version"] == "v2_9_0"
    assert response["context_persistence_sqlite_backend_store_summary"]["validation_status"] == "sqlite_backend_store_ready"
    assert response["storage_written"] is True
    assert response["backend_database_written"] is True
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is True
    assert response["sqlite_tables_created"] is True
    assert response["sqlite_rows_written"] is True
    assert response["sqlite_row_count_written"] == 3
    assert response["durable_backend_write_executed"] is True
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False
    assert _sqlite_counts(db_path) == {"records": 1, "idempotency": 1, "trace_links": 1}


def test_terminal_sqlite_backend_store_command_and_once_output(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    db_path = tmp_path / "terminal_context_store.db"
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_store({**_approved_args(db_path), "traceId": "trace_terminal_backend_store"})
    assert response["ok"] is True
    assert response["context_persistence_sqlite_backend_store_summary"]["validation_status"] == "sqlite_backend_store_ready"
    assert response["context_persistence_sqlite_backend_store_summary"]["backend_database_written"] is True
    assert _sqlite_counts(db_path) == {"records": 1, "idempotency": 1, "trace_links": 1}

    once_db_path = tmp_path / "terminal_once_context_store.db"
    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-sqlite-backend-store "
        + json.dumps({**_approved_args(once_db_path), "traceId": "trace_terminal_once_backend_store"}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceSqliteBackendStore>" in out
    assert "version: v2_9_0" in out
    assert "validation_status: sqlite_backend_store_ready" in out
    assert "backend_database_written: True" in out
    assert "sqlite_connection_created: True" in out
    assert "sqlite_rows_written: True" in out
    assert "local_device_written: false" in out
    assert _sqlite_counts(once_db_path) == {"records": 1, "idempotency": 1, "trace_links": 1}


def test_sqlite_backend_store_does_not_import_engine_or_modify_engine_docs_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    api_route = (root / "src" / "jammate_api" / "routes" / "agent_routes.py").read_text(encoding="utf-8")
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert "from jammate_engine" not in api_route
