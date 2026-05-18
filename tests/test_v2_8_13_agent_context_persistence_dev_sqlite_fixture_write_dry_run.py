from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
    build_context_persistence_dev_sqlite_fixture_write_dry_run_payload,
    build_context_persistence_dev_sqlite_fixture_write_dry_run_summary,
    context_persistence_dev_sqlite_fixture_write_dry_run_contract,
)
from jammate_api.app import app


def test_dev_sqlite_fixture_write_dry_run_contract_is_side_effect_free() -> None:
    spec = context_persistence_dev_sqlite_fixture_write_dry_run_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION == "v2_8_13"
    assert spec["spec_route"] == "GET /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview"
    assert spec["terminal_command"] == "/context-persistence-dev-sqlite-fixture-write-dry-run"
    assert spec["execution_status"]["fixture_write_dry_run_defined"] is True
    assert spec["execution_status"]["real_sqlite_write_enabled"] is False
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["sqlite_connection_created"] is False
    assert spec["guards"]["durable_backend_write_executed"] is False
    assert "simulate transaction begin" in spec["dry_run_flow"]


def test_dev_sqlite_fixture_write_dry_run_prepares_transaction_plan_but_does_not_write() -> None:
    payload_obj = build_context_persistence_dev_sqlite_fixture_write_dry_run_payload(
        {
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
        trace_id="trace_fixture_dry_run",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_dev_sqlite_fixture_write_dry_run_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_13"
    assert payload["adapter_mode"] == "fixture_write_dry_run_no_sqlite_connection_no_durable_write"
    assert payload["validation"]["status"] == "fixture_write_dry_run_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["transaction_preview"]["transaction_simulated"] is True
    assert payload["transaction_preview"]["transaction_committed"] is False
    assert payload["fixture_write_plan"]["planned_row_count"] >= 4
    assert payload["idempotency_preview"]["idempotency_key"]
    assert payload["trace_link_preview"]["trace_id"] == "trace_fixture_dry_run"
    assert payload["read_back_preview"]["read_back_simulated"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["fixture_write_executed"] is False
    assert payload["durable_backend_write_executed"] is False
    assert payload["transaction_committed"] is False
    assert summary["validation_status"] == "fixture_write_dry_run_ready"
    assert summary["transaction_simulated"] is True
    assert summary["read_back_simulated"] is True
    assert summary["storage_written"] is False


def test_dev_sqlite_fixture_write_dry_run_blocks_unapproved_or_sensitive_payload() -> None:
    payload = build_context_persistence_dev_sqlite_fixture_write_dry_run_payload(
        {
            "userDecision": "pending",
            "environment": "prod",
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
        }
    ).to_dict()
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "fixture_write_dry_run_blocked"
    assert "user_decision_must_be_approved_before_fixture_write_dry_run" in payload["validation"]["blocked_reasons"]
    assert "fixture_write_dry_run_only_allows_dev_or_test_environment" in payload["validation"]["blocked_reasons"]
    assert "redaction_check_failed_or_forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


def test_context_and_runtime_manifests_advertise_dev_sqlite_fixture_write_dry_run() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_dev_sqlite_fixture_write_dry_run_spec_route"] == "GET /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_dev_sqlite_fixture_write_dry_run"] == "POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview"
    assert runtime["context_persistence_dev_sqlite_fixture_write_dry_run"]["version"] == "v2_8_13"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_dev_sqlite_fixture_write_dry_run"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_dev_sqlite_fixture_write_dry_run_version"] == "v2_8_13"


def test_api_dev_sqlite_fixture_write_dry_run_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_13"

    response = client.post(
        "/agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview",
        json={
            "userDecision": "approved",
            "sqliteConfigPath": "./.jammate/dev_sqlite_context.json",
            "traceId": "trace_api_fixture_dry_run",
        },
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_fixture_write_dry_run_version"] == "v2_8_13"
    assert response["context_persistence_dev_sqlite_fixture_write_dry_run_summary"]["validation_status"] == "fixture_write_dry_run_ready"
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["fixture_write_executed"] is False
    assert response["durable_backend_write_executed"] is False
    assert response["transaction_committed"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_dev_sqlite_fixture_write_dry_run_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_dev_sqlite_fixture_write_dry_run(
        {"userDecision": "approved", "sqliteConfigPath": "./.jammate/dev_sqlite_context.json", "traceId": "trace_terminal_fixture_dry_run"}
    )
    assert response["ok"] is True
    assert response["context_persistence_dev_sqlite_fixture_write_dry_run_summary"]["validation_status"] == "fixture_write_dry_run_ready"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-dev-sqlite-fixture-write-dry-run " + json.dumps(
            {"userDecision": "approved", "sqliteConfigPath": "./.jammate/dev_sqlite_context.json", "traceId": "trace_terminal_fixture_dry_run"},
            ensure_ascii=False,
        ),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceDevSqliteFixtureWriteDryRun>" in out
    assert "version: v2_8_13" in out
    assert "transaction_simulated: True" in out
    assert "sqlite_connection_created: false" in out
    assert "fixture_write_executed: false" in out
    assert "storage_written: false" in out


def test_dev_sqlite_fixture_write_dry_run_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_V2_8_13.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
