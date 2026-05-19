from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
    build_context_persistence_dev_sqlite_fixture_store_payload,
    build_context_persistence_dev_sqlite_fixture_store_summary,
    context_persistence_dev_sqlite_fixture_store_contract,
)
from jammate_api.app import app


def _approved_args(path: Path) -> dict:
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
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
    }


def test_dev_sqlite_fixture_store_contract_is_explicit_opt_in() -> None:
    spec = context_persistence_dev_sqlite_fixture_store_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION == "v2_8_14"
    assert spec["spec_route"] == "GET /agent/context/persistence-dev-sqlite-fixture-store/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-dev-sqlite-fixture-store/preview"
    assert spec["terminal_command"] == "/context-persistence-dev-sqlite-fixture-store"
    assert spec["execution_status"]["explicit_fixture_store_defined"] is True
    assert spec["execution_status"]["fixture_store_can_append_dev_jsonl_when_explicitly_enabled"] is True
    assert spec["execution_status"]["real_sqlite_write_enabled"] is False
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["payload_writes_backend_database"] is False
    assert spec["guards"]["sqlite_connection_created"] is False
    assert spec["guards"]["durable_backend_write_executed"] is False
    assert "fixtureStoreWriteEnabled=true" in spec["required_gates"]


def test_dev_sqlite_fixture_store_blocks_without_explicit_opt_in(tmp_path: Path) -> None:
    fixture_path = tmp_path / "blocked_store.jsonl"
    payload = build_context_persistence_dev_sqlite_fixture_store_payload(
        {
            "userDecision": "approved",
            "fixtureStorePath": str(fixture_path),
            "environment": "test",
            "traceId": "trace_blocked_fixture_store",
        }
    ).to_dict()

    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "fixture_store_blocked"
    assert "fixture_store_write_enabled_must_be_true" in payload["validation"]["blocked_reasons"]
    assert "execute_fixture_store_must_be_true_for_actual_fixture_store" in payload["validation"]["blocked_reasons"]
    assert payload["fixture_store_result"]["fixture_store_write_executed"] is False
    assert fixture_path.exists() is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["backend_database_written"] is False


def test_dev_sqlite_fixture_store_writes_dev_fixture_jsonl_only_with_all_gates(tmp_path: Path) -> None:
    fixture_path = tmp_path / "agent_fixture_store.jsonl"
    payload_obj = build_context_persistence_dev_sqlite_fixture_store_payload(
        _approved_args(fixture_path),
        trace_id="trace_fixture_store",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_dev_sqlite_fixture_store_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_14"
    assert payload["adapter_mode"] == "explicit_opt_in_fixture_jsonl_store_no_sqlite_no_backend_database"
    assert payload["validation"]["status"] == "fixture_store_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["fixture_store_result"]["fixture_store_write_executed"] is True
    assert payload["fixture_store_result"]["line_count_appended"] == 1
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["durable_backend_write_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert summary["validation_status"] == "fixture_store_ready"
    assert summary["fixture_store_write_executed"] is True
    assert summary["backend_database_written"] is False

    lines = fixture_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["record_contract_version"] == "v2_8_14"
    assert record["trace_id"] == "trace_fixture_store"
    assert record["idempotency_key"]
    assert "routine_history_summary" in record["entities"]


def test_dev_sqlite_fixture_store_blocks_sensitive_or_non_dev_payload(tmp_path: Path) -> None:
    fixture_path = tmp_path / "sensitive_store.jsonl"
    payload = build_context_persistence_dev_sqlite_fixture_store_payload(
        {
            **_approved_args(fixture_path),
            "environment": "prod",
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
        },
        trace_id="trace_sensitive_fixture_store",
    ).to_dict()

    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "fixture_store_blocked"
    assert "fixture_store_only_allows_dev_or_test_environment" in payload["validation"]["blocked_reasons"]
    assert "redaction_check_failed_or_forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    assert payload["fixture_store_result"]["fixture_store_write_executed"] is False
    assert fixture_path.exists() is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


def test_context_and_runtime_manifests_advertise_dev_sqlite_fixture_store() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_dev_sqlite_fixture_store_spec_route"] == "GET /agent/context/persistence-dev-sqlite-fixture-store/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_dev_sqlite_fixture_store"] == "POST /agent/context/persistence-dev-sqlite-fixture-store/preview"
    assert runtime["context_persistence_dev_sqlite_fixture_store"]["version"] == "v2_8_14"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_dev_sqlite_fixture_store"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_dev_sqlite_fixture_store_version"] == "v2_8_14"


def test_api_dev_sqlite_fixture_store_explicit_opt_in(tmp_path: Path) -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-dev-sqlite-fixture-store/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_14"

    fixture_path = tmp_path / "api_fixture_store.jsonl"
    response = client.post(
        "/agent/context/persistence-dev-sqlite-fixture-store/preview",
        json={**_approved_args(fixture_path), "traceId": "trace_api_fixture_store"},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_fixture_store_version"] == "v2_8_14"
    assert response["context_persistence_dev_sqlite_fixture_store_summary"]["validation_status"] == "fixture_store_ready"
    assert response["fixture_store_write_executed"] is True
    assert fixture_path.exists() is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["durable_backend_write_executed"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_dev_sqlite_fixture_store_command_and_once_output(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    fixture_path = tmp_path / "terminal_fixture_store.jsonl"
    session = TerminalChatSession()
    response = session.context_persistence_dev_sqlite_fixture_store({**_approved_args(fixture_path), "traceId": "trace_terminal_fixture_store"})
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_fixture_store_summary"]["validation_status"] == "fixture_store_ready"
    assert response["context_persistence_dev_sqlite_fixture_store_summary"]["fixture_store_write_executed"] is True
    assert fixture_path.exists() is True

    fixture_path_once = tmp_path / "terminal_once_fixture_store.jsonl"
    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-dev-sqlite-fixture-store " + json.dumps(
            {**_approved_args(fixture_path_once), "traceId": "trace_terminal_once_fixture_store"},
            ensure_ascii=False,
        ),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceDevSqliteFixtureStore>" in out
    assert "version: v2_8_14" in out
    assert "fixture_store_write_executed: True" in out
    assert "sqlite_connection_created: false" in out
    assert "backend_database_written: false" in out
    assert fixture_path_once.exists() is True


def test_dev_sqlite_fixture_store_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_V2_8_14.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
