from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
    build_context_persistence_dev_fixture_readback_replay_payload,
    build_context_persistence_dev_fixture_readback_replay_summary,
    build_context_persistence_dev_sqlite_fixture_store_payload,
    context_persistence_dev_fixture_readback_replay_contract,
)
from jammate_api.app import app


def _approved_store_args(path: Path) -> dict:
    return {
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "fixtureStoreWriteEnabled": True,
        "executeFixtureStore": True,
        "fixtureStorePath": str(path),
        "environment": "test",
        "candidateKind": "practice_plan_persistence_candidate",
        "candidateId": "candidate_001",
        "confirmationId": "confirmation_001",
        "userId": "user_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
    }


def _write_fixture(path: Path, trace_id: str = "trace_readback_fixture") -> None:
    payload = build_context_persistence_dev_sqlite_fixture_store_payload(
        _approved_store_args(path),
        trace_id=trace_id,
    ).to_dict()
    assert payload["validation"]["accepted"] is True
    assert path.exists() is True


def test_dev_fixture_readback_replay_contract_is_read_only() -> None:
    spec = context_persistence_dev_fixture_readback_replay_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION == "v2_8_15"
    assert spec["spec_route"] == "GET /agent/context/persistence-dev-fixture-readback-replay/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-dev-fixture-readback-replay/preview"
    assert spec["terminal_command"] == "/context-persistence-dev-fixture-readback-replay"
    assert spec["execution_status"]["fixture_readback_preview_defined"] is True
    assert spec["execution_status"]["context_snapshot_previewed"] is True
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["sqlite_connection_created"] is False
    assert spec["guards"]["fixture_write_executed"] is False
    assert spec["guards"]["replay_execution_committed"] is False


def test_dev_fixture_readback_replay_reads_fixture_and_builds_snapshot(tmp_path: Path) -> None:
    fixture_path = tmp_path / "agent_fixture_store.jsonl"
    _write_fixture(fixture_path, trace_id="trace_readback_fixture")

    payload_obj = build_context_persistence_dev_fixture_readback_replay_payload(
        {
            "fixtureStorePath": str(fixture_path),
            "environment": "test",
            "userId": "user_001",
            "filterTraceId": "trace_readback_fixture",
        },
        trace_id="trace_readback_fixture",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_dev_fixture_readback_replay_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_15"
    assert payload["validation"]["status"] == "readback_replay_preview_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["fixture_read_result"]["file_exists"] is True
    assert payload["fixture_read_result"]["records_read"] == 1
    assert payload["fixture_read_result"]["matched_record_count"] == 1
    assert payload["context_snapshot_preview"]["snapshot_available"] is True
    assert payload["replay_preview"]["replayable"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["fixture_write_executed"] is False
    assert payload["replay_execution_committed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert summary["validation_status"] == "readback_replay_preview_ready"
    assert summary["snapshot_available"] is True
    assert summary["matched_record_count"] == 1
    assert summary["storage_written"] is False


def test_dev_fixture_readback_replay_missing_file_returns_empty_snapshot(tmp_path: Path) -> None:
    fixture_path = tmp_path / "missing_fixture_store.jsonl"
    payload = build_context_persistence_dev_fixture_readback_replay_payload(
        {"fixtureStorePath": str(fixture_path), "environment": "test"}
    ).to_dict()

    assert payload["validation"]["accepted"] is True
    assert payload["fixture_read_result"]["file_exists"] is False
    assert payload["fixture_read_result"]["records_read"] == 0
    assert payload["context_snapshot_preview"]["snapshot_available"] is False
    assert "fixture_store_path_not_found_readback_returns_empty_snapshot" in payload["validation"]["warnings"]
    assert payload["storage_written"] is False
    assert payload["sqlite_rows_written"] is False


def test_dev_fixture_readback_replay_blocks_prod_or_sensitive_payload(tmp_path: Path) -> None:
    fixture_path = tmp_path / "sensitive_readback.jsonl"
    fixture_path.write_text(json.dumps({"apiKey": "SHOULD_NOT_LEAK"}) + "\n", encoding="utf-8")
    payload = build_context_persistence_dev_fixture_readback_replay_payload(
        {
            "fixtureStorePath": str(fixture_path),
            "environment": "prod",
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
        }
    ).to_dict()

    assert payload["validation"]["accepted"] is False
    assert "readback_preview_only_allows_dev_or_test_environment" in payload["validation"]["blocked_reasons"]
    assert "redaction_check_failed_or_forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False


def test_context_and_runtime_manifests_advertise_dev_fixture_readback_replay() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_dev_fixture_readback_replay_spec_route"] == "GET /agent/context/persistence-dev-fixture-readback-replay/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_dev_fixture_readback_replay"] == "POST /agent/context/persistence-dev-fixture-readback-replay/preview"
    assert runtime["context_persistence_dev_fixture_readback_replay"]["version"] == "v2_8_15"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_dev_fixture_readback_replay"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_dev_fixture_readback_replay_version"] == "v2_8_15"


def test_api_dev_fixture_readback_replay_preview(tmp_path: Path) -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-dev-fixture-readback-replay/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_15"

    fixture_path = tmp_path / "api_fixture_store.jsonl"
    _write_fixture(fixture_path, trace_id="trace_api_readback")
    response = client.post(
        "/agent/context/persistence-dev-fixture-readback-replay/preview",
        json={"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_api_readback"},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_dev_fixture_readback_replay_version"] == "v2_8_15"
    assert response["context_persistence_dev_fixture_readback_replay_summary"]["validation_status"] == "readback_replay_preview_ready"
    assert response["context_persistence_dev_fixture_readback_replay_summary"]["matched_record_count"] == 1
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["fixture_write_executed"] is False
    assert response["replay_execution_committed"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False


def test_terminal_dev_fixture_readback_replay_command_and_once_output(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    fixture_path = tmp_path / "terminal_fixture_store.jsonl"
    _write_fixture(fixture_path, trace_id="trace_terminal_readback")
    session = TerminalChatSession()
    response = session.context_persistence_dev_fixture_readback_replay(
        {"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_terminal_readback"}
    )
    assert response["ok"] is True
    assert response["context_persistence_dev_fixture_readback_replay_summary"]["validation_status"] == "readback_replay_preview_ready"
    assert response["context_persistence_dev_fixture_readback_replay_summary"]["matched_record_count"] == 1

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-dev-fixture-readback-replay " + json.dumps(
            {"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_terminal_readback"},
            ensure_ascii=False,
        ),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceDevFixtureReadbackReplay>" in out
    assert "version: v2_8_15" in out
    assert "matched_record_count: 1" in out
    assert "sqlite_connection_created: false" in out
    assert "backend_database_written: false" in out


def test_dev_fixture_readback_replay_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_V2_8_15.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
