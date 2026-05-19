from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
    build_context_persistence_dev_sqlite_write_gate_payload,
    build_context_persistence_dev_sqlite_write_gate_summary,
    context_persistence_dev_sqlite_write_gate_contract,
)
from jammate_api.app import app


def test_dev_sqlite_write_gate_contract_is_explicit_and_side_effect_free() -> None:
    spec = context_persistence_dev_sqlite_write_gate_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION == "v2_8_12"
    assert spec["spec_route"] == "GET /agent/context/persistence-dev-sqlite-write-gate/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-dev-sqlite-write-gate/preview"
    assert spec["terminal_command"] == "/context-persistence-dev-sqlite-write-gate"
    assert spec["execution_status"]["explicit_dev_write_gate_defined"] is True
    assert spec["execution_status"]["real_sqlite_write_enabled"] is False
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["sqlite_connection_created"] is False
    assert "sqliteConfigPath present" in spec["required_future_write_checks"]


def test_dev_sqlite_write_gate_preview_ready_when_all_future_checks_are_present_but_does_not_write() -> None:
    payload_obj = build_context_persistence_dev_sqlite_write_gate_payload(
        {
            "devWriteEnabled": True,
            "userDecision": "approved",
            "confirmationStatus": "user_approved_future_executor_required",
            "sqliteConfigPath": "./.jammate/dev_sqlite_context.json",
            "sqliteDbPath": "./.jammate/dev_context.sqlite3",
            "environment": "dev",
            "candidateKind": "practice_plan_persistence_candidate",
            "candidateId": "candidate_001",
            "confirmationId": "confirmation_001",
            "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        },
        trace_id="trace_dev_sqlite_gate",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_dev_sqlite_write_gate_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_12"
    assert payload["adapter_mode"] == "explicit_dev_sqlite_write_gate_no_write"
    assert payload["validation"]["status"] == "dev_sqlite_write_gate_ready_future_executor_required"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["dev_write_enabled_for_future_executor"] is True
    assert payload["required_checks"]["all_required_checks_passed"] is True
    assert payload["idempotency_gate"]["idempotency_key"]
    assert payload["trace_link_gate"]["trace_id"] == "trace_dev_sqlite_gate"
    assert payload["dev_sqlite_config_contract"]["sqlite_config_path"] == "./.jammate/dev_sqlite_context.json"
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["sqlite_write_enabled"] is False
    assert payload["future_executor_implemented"] is False
    assert summary["validation_status"] == "dev_sqlite_write_gate_ready_future_executor_required"
    assert summary["dev_write_enabled_for_future_executor"] is True
    assert summary["storage_written"] is False


def test_dev_sqlite_write_gate_blocks_missing_confirmation_config_or_redaction() -> None:
    payload = build_context_persistence_dev_sqlite_write_gate_payload(
        {
            "devWriteEnabled": True,
            "userDecision": "pending",
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
        }
    ).to_dict()
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "dev_sqlite_write_gate_blocked"
    assert "user_decision_must_be_approved_before_future_dev_write" in payload["validation"]["blocked_reasons"]
    assert "explicit_dev_write_requires_sqlite_config_path" in payload["validation"]["blocked_reasons"]
    assert "redaction_check_failed_or_forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


def test_context_and_runtime_manifests_advertise_dev_sqlite_write_gate() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_dev_sqlite_write_gate_spec_route"] == "GET /agent/context/persistence-dev-sqlite-write-gate/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_dev_sqlite_write_gate"] == "POST /agent/context/persistence-dev-sqlite-write-gate/preview"
    assert runtime["context_persistence_dev_sqlite_write_gate"]["version"] == "v2_8_12"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_dev_sqlite_write_gate"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_dev_sqlite_write_gate_version"] == "v2_8_12"


def test_api_dev_sqlite_write_gate_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-dev-sqlite-write-gate/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_12"

    response = client.post(
        "/agent/context/persistence-dev-sqlite-write-gate/preview",
        json={
            "devWriteEnabled": True,
            "userDecision": "approved",
            "sqliteConfigPath": "./.jammate/dev_sqlite_context.json",
            "traceId": "trace_api_gate",
        },
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_write_gate_version"] == "v2_8_12"
    assert response["context_persistence_dev_sqlite_write_gate_summary"]["validation_status"] == "dev_sqlite_write_gate_ready_future_executor_required"
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["sqlite_write_enabled"] is False
    assert response["future_executor_implemented"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_dev_sqlite_write_gate_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_dev_sqlite_write_gate(
        {"devWriteEnabled": True, "userDecision": "approved", "sqliteConfigPath": "./.jammate/dev_sqlite_context.json", "traceId": "trace_terminal_gate"}
    )
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_write_gate_summary"]["validation_status"] == "dev_sqlite_write_gate_ready_future_executor_required"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-dev-sqlite-write-gate " + json.dumps(
            {"devWriteEnabled": True, "userDecision": "approved", "sqliteConfigPath": "./.jammate/dev_sqlite_context.json", "traceId": "trace_terminal_gate"},
            ensure_ascii=False,
        ),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceDevSqliteWriteGate>" in out
    assert "version: v2_8_12" in out
    assert "sqlite_connection_created: false" in out
    assert "storage_written: false" in out


def test_dev_sqlite_write_gate_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_V2_8_12.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
