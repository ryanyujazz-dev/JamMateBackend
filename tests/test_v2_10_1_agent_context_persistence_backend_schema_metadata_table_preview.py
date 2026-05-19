from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_TABLE_PREVIEW_VERSION,
    CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_VERSION,
    CONTEXT_PERSISTENCE_BACKEND_SQLITE_SCHEMA_VERSION,
    build_context_persistence_backend_schema_metadata_table_preview_payload,
    build_context_persistence_backend_schema_metadata_table_preview_summary,
    context_persistence_backend_schema_metadata_table_preview_contract,
)
from jammate_api.app import app


def _valid_args(db_path: Path) -> dict:
    return {
        "previewId": "ctx_backend_schema_metadata_preview_test",
        "traceId": "trace_backend_schema_metadata_preview_test",
        "environment": "integration_dev",
        "sqliteDbPath": str(db_path),
        "declaredSchemaVersion": CONTEXT_PERSISTENCE_BACKEND_SQLITE_SCHEMA_VERSION,
        "metadataSchemaVersion": CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_VERSION,
        "migrationMode": "create_if_missing_dev_only",
        "migrationPlanId": "migration_plan_v2_10_1_metadata_preview",
        "metadataTablePreviewAccepted": True,
        "migrationRegistryPreviewAccepted": True,
        "schemaValidationEventPreviewAccepted": True,
    }


def test_backend_schema_metadata_table_preview_contract() -> None:
    spec = context_persistence_backend_schema_metadata_table_preview_contract()

    assert spec["version"] == CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_TABLE_PREVIEW_VERSION == "v2_10_1"
    assert spec["spec_route"] == "GET /agent/context/persistence-backend-schema-metadata-table-preview/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-backend-schema-metadata-table-preview/preview"
    assert spec["terminal_command"] == "/context-persistence-backend-schema-metadata-table-preview"
    assert spec["short_terminal_command"] == "/sqlite-schema-metadata-preview"
    assert spec["execution_status"]["backend_schema_metadata_table_preview_implemented"] is True
    assert spec["execution_status"]["preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["execution_status"]["schema_creation_enabled"] is False
    assert spec["execution_status"]["migration_execution_enabled"] is False
    assert spec["schema_policy"]["metadata_schema_version"] == "agent_context_sqlite_schema_metadata_v1"
    assert "context_persistence_schema_metadata" in spec["schema_policy"]["required_metadata_tables"]
    assert "context_persistence_migration_registry" in spec["schema_policy"]["required_metadata_tables"]
    assert spec["guards"]["payload_opens_sqlite"] is False
    assert spec["guards"]["payload_creates_sqlite_tables"] is False
    assert spec["guards"]["payload_runs_migration"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_backend_schema_metadata_table_preview_accepts_safe_guard_without_side_effects(tmp_path: Path) -> None:
    db_path = tmp_path / "jammate_agent_context.sqlite"
    payload_obj = build_context_persistence_backend_schema_metadata_table_preview_payload(_valid_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_backend_schema_metadata_table_preview_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_10_1"
    assert payload["validation"]["status"] == "backend_schema_metadata_table_preview_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["db_path_policy_passed"] is True
    assert payload["validation"]["metadata_table_preview_passed"] is True
    assert payload["validation"]["migration_registry_preview_passed"] is True
    assert payload["metadata_table_preview"]["table_would_be_created_by_this_surface"] is False
    assert payload["migration_registry_preview"]["table_would_be_created_by_this_surface"] is False
    assert "context_persistence_records" in payload["core_schema_tables"]
    assert "context_persistence_schema_metadata" in payload["validation"]["required_metadata_tables"]
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["migration_execution_performed"] is False
    assert payload["schema_creation_performed"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "backend_schema_metadata_table_preview_ready"
    assert summary["metadata_schema_version"] == "agent_context_sqlite_schema_metadata_v1"
    assert "context_persistence_migration_registry" in summary["required_metadata_tables"]
    assert not db_path.exists()


def test_backend_schema_metadata_table_preview_blocks_when_guard_or_metadata_contract_fails() -> None:
    payload = build_context_persistence_backend_schema_metadata_table_preview_payload(
        {
            "environment": "production",
            "sqliteDbPath": "/prod/secrets/jammate_agent_context.sqlite",
            "declaredSchemaVersion": "legacy_schema_v0",
            "metadataSchemaVersion": "metadata_schema_v0",
            "migrationMode": "force_drop_tables",
            "metadataTablePreviewAccepted": False,
        }
    ).to_dict()
    reasons = set(payload["validation"]["blocked_reasons"])

    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "backend_schema_metadata_table_preview_blocked"
    assert "backend_db_path_policy_and_migration_guard_must_be_ready" in reasons
    assert "metadata_schema_version_must_match_agent_context_sqlite_schema_metadata_v1" in reasons
    assert "metadata_table_preview_accepted_must_be_true" in reasons
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["storage_written"] is False


def test_api_backend_schema_metadata_table_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_jammate_agent_context.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-backend-schema-metadata-table-preview/spec").json()
    assert spec["spec"]["version"] == "v2_10_1"

    response = client.post("/agent/context/persistence-backend-schema-metadata-table-preview/preview", json=_valid_args(db_path)).json()

    assert response["context_persistence_backend_schema_metadata_table_preview_version"] == "v2_10_1"
    summary = response["context_persistence_backend_schema_metadata_table_preview_summary"]
    assert summary["validation_status"] == "backend_schema_metadata_table_preview_ready"
    assert summary["metadata_table_preview_passed"] is True
    assert summary["migration_registry_preview_passed"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["migration_execution_performed"] is False
    assert response["schema_creation_performed"] is False
    assert response["frontend_fixtures_directory_written"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert not db_path.exists()


def test_terminal_backend_schema_metadata_table_preview_command_prints_status(tmp_path: Path) -> None:
    command = "/sqlite-schema-metadata-preview " + json.dumps(_valid_args(tmp_path / "terminal_jammate_agent_context.sqlite"), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceBackendSchemaMetadataTablePreview>" in out
    assert "version: v2_10_1" in out
    assert "validation_status: backend_schema_metadata_table_preview_ready" in out
    assert "metadata_schema_version: agent_context_sqlite_schema_metadata_v1" in out
    assert "metadata_table_preview_passed: true" in out
    assert "migration_registry_preview_passed: true" in out
    assert "sqlite_connection_created: false" in out
    assert "migration_execution_performed: false" in out
    assert "schema_creation_performed: false" in out
    assert "routine_start_enabled: false" in out


def test_terminal_session_backend_schema_metadata_preview_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_jammate_agent_context.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_backend_schema_metadata_table_preview(_valid_args(db_path))

    assert response["ok"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_tables_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["migration_execution_performed"] is False
    assert response["schema_creation_performed"] is False
    assert response["terminal_session_memory_loaded_by_cli"] is False
    assert session.persisted_context_show()["memory_loaded"] is False
    assert not db_path.exists()


def test_context_and_runtime_manifests_advertise_backend_schema_metadata_preview() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_backend_schema_metadata_table_preview_spec_route"] == "GET /agent/context/persistence-backend-schema-metadata-table-preview/spec"
    assert runtime["routes"]["context_persistence_backend_schema_metadata_table_preview"] == "POST /agent/context/persistence-backend-schema-metadata-table-preview/preview"
    assert runtime["context_persistence_backend_schema_metadata_table_preview"]["version"] == "v2_10_1"
    assert CapabilityManifest().to_dict()["supports_context_persistence_backend_schema_metadata_table_preview"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_backend_schema_metadata_table_preview_version"] == "v2_10_1"


def test_backend_schema_metadata_preview_does_not_modify_shared_frontend_or_engine() -> None:
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_BACKEND_SCHEMA_METADATA_TABLE_PREVIEW_V2_10_1.json").exists()
