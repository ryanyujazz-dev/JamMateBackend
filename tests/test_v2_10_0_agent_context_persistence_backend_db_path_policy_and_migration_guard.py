from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_BACKEND_DB_PATH_POLICY_AND_MIGRATION_GUARD_VERSION,
    CONTEXT_PERSISTENCE_BACKEND_SQLITE_SCHEMA_VERSION,
    build_context_persistence_backend_db_path_policy_and_migration_guard_payload,
    build_context_persistence_backend_db_path_policy_and_migration_guard_summary,
    context_persistence_backend_db_path_policy_and_migration_guard_contract,
)
from jammate_api.app import app


def _valid_args(db_path: Path) -> dict:
    return {
        "guardId": "ctx_backend_policy_guard_test",
        "traceId": "trace_backend_policy_guard_test",
        "environment": "integration_dev",
        "sqliteDbPath": str(db_path),
        "declaredSchemaVersion": CONTEXT_PERSISTENCE_BACKEND_SQLITE_SCHEMA_VERSION,
        "migrationMode": "create_if_missing_dev_only",
        "migrationPlanId": "migration_plan_v2_10_0_dev_create_if_missing",
    }


def test_backend_db_path_policy_and_migration_guard_contract() -> None:
    spec = context_persistence_backend_db_path_policy_and_migration_guard_contract()

    assert spec["version"] == CONTEXT_PERSISTENCE_BACKEND_DB_PATH_POLICY_AND_MIGRATION_GUARD_VERSION == "v2_10_0"
    assert spec["spec_route"] == "GET /agent/context/persistence-backend-db-path-policy-migration-guard/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-backend-db-path-policy-migration-guard/preview"
    assert spec["terminal_command"] == "/context-persistence-backend-db-path-policy-migration-guard"
    assert spec["short_terminal_command"] == "/sqlite-db-policy-guard"
    assert spec["execution_status"]["backend_db_path_policy_and_migration_guard_implemented"] is True
    assert spec["execution_status"]["preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["execution_status"]["migration_execution_enabled"] is False
    assert spec["path_policy"]["production_path_enabled"] is False
    assert spec["schema_policy"]["current_schema_version"] == "agent_context_sqlite_schema_v1"
    assert spec["migration_policy"]["destructive_migration_allowed"] is False
    assert spec["guards"]["payload_opens_sqlite"] is False
    assert spec["guards"]["payload_writes_sqlite"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_backend_db_path_policy_and_migration_guard_accepts_safe_integration_dev_path_without_side_effects(tmp_path: Path) -> None:
    db_path = tmp_path / "jammate_agent_context.sqlite"
    payload_obj = build_context_persistence_backend_db_path_policy_and_migration_guard_payload(_valid_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_backend_db_path_policy_and_migration_guard_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_10_0"
    assert payload["validation"]["status"] == "backend_db_path_policy_and_migration_guard_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["db_path_policy_passed"] is True
    assert payload["validation"]["schema_guard_passed"] is True
    assert payload["validation"]["migration_guard_passed"] is True
    assert payload["schema_policy"]["expected_schema_version"] == "agent_context_sqlite_schema_v1"
    assert payload["migration_policy"]["schema_creation_allowed_by_intent"] is True
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["migration_policy"]["migration_execution_performed"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "backend_db_path_policy_and_migration_guard_ready"
    assert summary["migration_mode"] == "create_if_missing_dev_only"
    assert summary["schema_creation_allowed_by_intent"] is True
    assert not db_path.exists()


def test_backend_db_path_policy_and_migration_guard_blocks_prod_secret_or_bad_path() -> None:
    payload = build_context_persistence_backend_db_path_policy_and_migration_guard_payload(
        {
            "environment": "production",
            "sqliteDbPath": "/prod/secrets/jammate_agent_context.sqlite",
            "migrationMode": "force_drop_tables",
            "declaredSchemaVersion": "legacy_schema_v0",
        }
    ).to_dict()

    reasons = set(payload["validation"]["blocked_reasons"])
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "backend_db_path_policy_and_migration_guard_blocked"
    assert "environment_must_be_dev_local_dev_test_or_integration_dev_for_v2_10_0" in reasons
    assert "production_backend_path_policy_not_enabled_in_agent_track" in reasons
    assert "sqlite_db_path_must_not_contain_prod_secret_or_token_terms" in reasons
    assert "migration_mode_must_be_disabled_preview_read_only_existing_or_create_if_missing_dev_only" in reasons
    assert "destructive_or_force_migration_modes_are_forbidden" in reasons
    assert "declared_schema_version_must_match_agent_context_sqlite_schema_v1" in reasons
    assert payload["sqlite_connection_created"] is False
    assert payload["storage_written"] is False


def test_backend_db_path_policy_and_migration_guard_blocks_parent_traversal_and_bad_extension() -> None:
    payload = build_context_persistence_backend_db_path_policy_and_migration_guard_payload(
        {"environment": "dev", "sqliteDbPath": "../outside/jammate_agent_context.txt"}
    ).to_dict()
    reasons = set(payload["validation"]["blocked_reasons"])

    assert "sqlite_db_path_must_not_contain_parent_traversal" in reasons
    assert "sqlite_db_path_must_end_with_db_sqlite_or_sqlite3" in reasons
    assert payload["validation"]["db_path_policy_passed"] is False
    assert payload["backend_database_written"] is False
    assert payload["sqlite_connection_created"] is False


def test_api_backend_db_path_policy_and_migration_guard_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_jammate_agent_context.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-backend-db-path-policy-migration-guard/spec").json()
    assert spec["spec"]["version"] == "v2_10_0"

    response = client.post("/agent/context/persistence-backend-db-path-policy-migration-guard/preview", json=_valid_args(db_path)).json()

    assert response["context_persistence_backend_db_path_policy_and_migration_guard_version"] == "v2_10_0"
    summary = response["context_persistence_backend_db_path_policy_and_migration_guard_summary"]
    assert summary["validation_status"] == "backend_db_path_policy_and_migration_guard_ready"
    assert summary["db_path_policy_passed"] is True
    assert summary["schema_guard_passed"] is True
    assert summary["migration_guard_passed"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["migration_execution_performed"] is False
    assert response["frontend_fixtures_directory_written"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert not db_path.exists()


def test_terminal_backend_db_path_policy_guard_command_prints_status(tmp_path: Path) -> None:
    command = "/sqlite-db-policy-guard " + json.dumps(_valid_args(tmp_path / "terminal_jammate_agent_context.sqlite"), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceBackendDbPathPolicyAndMigrationGuard>" in out
    assert "version: v2_10_0" in out
    assert "validation_status: backend_db_path_policy_and_migration_guard_ready" in out
    assert "db_path_policy_passed: true" in out
    assert "schema_guard_passed: true" in out
    assert "migration_guard_passed: true" in out
    assert "expected_schema_version: agent_context_sqlite_schema_v1" in out
    assert "migration_mode: create_if_missing_dev_only" in out
    assert "sqlite_connection_created: false" in out
    assert "migration_execution_performed: false" in out
    assert "routine_start_enabled: false" in out


def test_terminal_session_backend_db_path_policy_guard_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_jammate_agent_context.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_backend_db_path_policy_and_migration_guard(_valid_args(db_path))

    assert response["ok"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["migration_execution_performed"] is False
    assert response["terminal_session_memory_loaded_by_cli"] is False
    assert session.persisted_context_show()["memory_loaded"] is False
    assert not db_path.exists()


def test_context_and_runtime_manifests_advertise_backend_db_path_policy_guard() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_backend_db_path_policy_and_migration_guard_spec_route"] == "GET /agent/context/persistence-backend-db-path-policy-migration-guard/spec"
    assert runtime["routes"]["context_persistence_backend_db_path_policy_and_migration_guard"] == "POST /agent/context/persistence-backend-db-path-policy-migration-guard/preview"
    assert runtime["context_persistence_backend_db_path_policy_and_migration_guard"]["version"] == "v2_10_0"
    assert CapabilityManifest().to_dict()["supports_context_persistence_backend_db_path_policy_and_migration_guard"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_backend_db_path_policy_and_migration_guard_version"] == "v2_10_0"


def test_backend_db_path_policy_guard_does_not_modify_shared_frontend_or_engine() -> None:
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_BACKEND_DB_PATH_POLICY_GUARD_V2_10_0.json").exists()
