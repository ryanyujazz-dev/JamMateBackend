from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
    build_context_persistence_sqlite_dev_preview_payload,
    build_context_persistence_sqlite_dev_preview_summary,
    context_persistence_sqlite_dev_preview_contract,
)
from jammate_api.app import app


def test_sqlite_dev_preview_contract_is_preview_only_no_connection() -> None:
    spec = context_persistence_sqlite_dev_preview_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION == "v2_8_11"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-dev-preview/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-dev-preview/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-dev-preview"
    assert spec["execution_status"]["sqlite_schema_preview_enabled"] is True
    assert spec["execution_status"]["real_sqlite_write_enabled"] is False
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["sqlite_connection_created"] is False
    assert "active_practice_plans" in spec["schema_preview_tables"]


def test_sqlite_dev_preview_payload_exposes_schema_idempotency_trace_and_snapshot_without_writes() -> None:
    payload_obj = build_context_persistence_sqlite_dev_preview_payload(
        {
            "userId": "user_001",
            "candidateKind": "practice_plan_persistence_candidate",
            "candidateId": "candidate_001",
            "confirmationId": "confirmation_001",
            "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/nope.mid",
        },
        trace_id="trace_sqlite_dev_preview",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_dev_preview_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_11"
    assert payload["adapter_kind"] == "sqlite_dev_adapter"
    assert payload["adapter_mode"] == "sqlite_dev_fixture_preview_no_database_connection"
    assert payload["sqlite_schema_preview"]["dialect"] == "sqlite"
    assert payload["sqlite_schema_preview"]["sqlite_connection_created"] is False
    assert "user_practice_profiles" in payload["sqlite_schema_preview"]["tables"]
    assert "active_practice_plans" in payload["sqlite_schema_preview"]["tables"]
    assert payload["idempotency_preview"]["idempotency_key"]
    assert payload["idempotency_preview"]["idempotency_record_written"] is False
    assert payload["trace_link_preview"]["trace_id"] == "trace_sqlite_dev_preview"
    assert payload["trace_link_preview"]["trace_link_written"] is False
    assert payload["read_snapshot_preview"]["read_executed"] is False
    assert payload["fixture_snapshot_preview"]["source"] == "sqlite_dev_fixture_preview"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["status"] == "sqlite_dev_preview_ready_no_write"
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_dev_preview_ready_no_write"
    assert summary["schema_table_count"] >= 5
    assert summary["storage_written"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized


def test_sqlite_dev_preview_blocks_requested_write_but_stays_side_effect_free() -> None:
    payload = build_context_persistence_sqlite_dev_preview_payload({"devWriteEnabled": True}).to_dict()
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "sqlite_dev_preview_blocked"
    assert "dev_write_requested_but_v2_8_11_is_preview_only" in payload["validation"]["blocked_reasons"]
    assert payload["write_preview_gate"]["real_write_enabled"] is False
    assert payload["storage_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False


def test_context_and_runtime_manifests_advertise_sqlite_dev_preview() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_sqlite_dev_preview_spec_route"] == "GET /agent/context/persistence-sqlite-dev-preview/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_sqlite_dev_preview"] == "POST /agent/context/persistence-sqlite-dev-preview/preview"
    assert runtime["context_persistence_sqlite_dev_preview"]["version"] == "v2_8_11"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_sqlite_dev_preview"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_sqlite_dev_preview_version"] == "v2_8_11"


def test_api_sqlite_dev_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-dev-preview/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_11"

    response = client.post(
        "/agent/context/persistence-sqlite-dev-preview/preview",
        json={"userId": "user_001", "entities": ["active_practice_plan", "routine_history_summary"]},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_sqlite_dev_preview_version"] == "v2_8_11"
    assert response["context_persistence_sqlite_dev_preview_summary"]["validation_status"] == "sqlite_dev_preview_ready_no_write"
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_sqlite_dev_preview_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_dev_preview({"userId": "user_001"})
    assert response["ok"] is True
    assert response["context_persistence_sqlite_dev_preview_summary"]["validation_status"] == "sqlite_dev_preview_ready_no_write"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-sqlite-dev-preview " + json.dumps({"userId": "user_001"}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceSqliteDevPreview>" in out
    assert "version: v2_8_11" in out
    assert "sqlite_connection_created: false" in out
    assert "storage_written: false" in out


def test_sqlite_dev_preview_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_V2_8_11.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
