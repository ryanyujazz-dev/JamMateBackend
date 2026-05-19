from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_ERROR_FIXTURE_PACK_VERSION,
    build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload,
    build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary,
    context_persistence_sqlite_backend_harmonyos_error_fixture_pack_contract,
)
from jammate_api.app import app


def _fixture_args(db_path: Path) -> dict:
    return {
        "baseUrl": "http://127.0.0.1:8000",
        "targetClient": "harmonyos",
        "sqliteDbPath": str(db_path),
        "missingReadbackSqliteDbPath": str(db_path.parent / "missing_error_fixture.sqlite"),
        "traceId": "trace_harmonyos_error_fixture_pack_test",
    }


def test_sqlite_backend_harmonyos_error_fixture_pack_contract() -> None:
    spec = context_persistence_sqlite_backend_harmonyos_error_fixture_pack_contract()

    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_ERROR_FIXTURE_PACK_VERSION == "v2_9_8"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-harmonyos-error-fixture-pack"
    assert spec["short_terminal_command"] == "/sqlite-harmonyos-error-fixture-pack"
    assert spec["execution_status"]["sqlite_backend_harmonyos_error_fixture_pack_implemented"] is True
    assert spec["execution_status"]["error_fixture_pack_preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["execution_status"]["frontend_fixtures_directory_write_enabled"] is False
    assert spec["guards"]["fixture_pack_calls_existing_routes"] is False
    assert spec["guards"]["fixture_pack_writes_frontend_fixtures"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert set(spec["covered_scenarios"]) >= {"missing_write_gate", "invalid_sqlite_db_path", "empty_readback", "idempotent_replay", "malformed_payload"}


def test_sqlite_backend_harmonyos_error_fixture_pack_core_payload_is_preview_only(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_error_fixture_should_not_exist.sqlite"
    missing_db = tmp_path / "missing_error_fixture.sqlite"
    payload_obj = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload(_fixture_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_8"
    assert payload["validation"]["status"] == "sqlite_backend_harmonyos_error_fixture_pack_ready"
    assert payload["validation"]["error_fixture_pack_preview_only"] is True
    assert payload["validation"]["scenario_count"] == 5
    assert payload["validation"]["bad_request_example_count"] == 5
    assert payload["validation"]["fixture_pack_calls_existing_routes"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["fixture_files_written"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_backend_harmonyos_error_fixture_pack_ready"
    assert summary["contains_missing_write_gate_fixture"] is True
    assert summary["contains_invalid_sqlite_db_path_fixture"] is True
    assert summary["contains_empty_readback_fixture"] is True
    assert summary["contains_idempotent_replay_fixture"] is True
    assert summary["contains_malformed_payload_fixture"] is True
    assert "harmonyos_error_fixture_pack_preview_only_no_routes_executed" in summary["warnings"]
    assert not db_path.exists()
    assert not missing_db.exists()


def test_sqlite_backend_harmonyos_error_fixture_pack_contains_bad_request_examples_and_ui_policy(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload(_fixture_args(tmp_path / "fixture.sqlite")).to_dict()

    examples = {item["scenario_key"]: item for item in payload["bad_request_examples"]}
    assert set(examples) == {"missing_write_gate", "invalid_sqlite_db_path", "empty_readback", "idempotent_replay", "malformed_payload"}
    assert examples["missing_write_gate"]["path"] == "/agent/context/persistence-sqlite-backend-store/execute"
    assert examples["missing_write_gate"]["expected_validation_status"] == "sqlite_backend_store_blocked"
    assert "backend_persistence_enabled_must_be_true" in examples["missing_write_gate"]["expected_blocked_reasons"]
    assert examples["invalid_sqlite_db_path"]["body"]["sqliteDbPath"] == "/prod/secrets.sqlite"
    assert examples["empty_readback"]["path"] == "/agent/context/persistence-sqlite-backend-readback-context-recovery/preview"
    assert examples["idempotent_replay"]["client_treats_as_success"] is True
    assert examples["malformed_payload"]["expected_http_status_hint"] == 422
    assert examples["malformed_payload"]["body"]["rawPayloadKind"] == "array_or_string_instead_of_json_object"

    ui_messages = {item["scenario_key"]: item for item in payload["expected_ui_debug_messages"]}
    assert "backendPersistenceEnabled" in ui_messages["missing_write_gate"]["message"]
    assert "普通“今天该练什么”" in ui_messages["empty_readback"]["message"]
    assert ui_messages["idempotent_replay"]["severity"] == "info"
    retry = {item["scenario_key"]: item for item in payload["retry_policy_catalog"]}
    assert retry["idempotent_replay"]["continue_pipeline_after_response"] is True
    assert retry["malformed_payload"]["retry_kind"] == "after_client_schema_fix"


def test_sqlite_backend_harmonyos_error_fixture_pack_contains_harmonyos_copyable_pack(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload(_fixture_args(tmp_path / "fixture.sqlite")).to_dict()
    pack = payload["harmonyos_error_fixture_pack"]

    assert pack["packContractVersion"] == "v2_9_8"
    assert pack["sourceMatrixVersion"] == "v2_9_7"
    assert len(pack["badRequestExamples"]) == 5
    assert len(pack["curlBadRequestExamples"]) == 5
    assert all("curl -s -X POST" in item for item in pack["curlBadRequestExamples"])
    sketch = pack["arktsHandlingSketch"]
    assert "camelCase" in sketch["requestCasePolicy"]
    assert "snake_case" in sketch["requestCasePolicy"]
    assert "sqlite_backend_store_idempotent_replay" in sketch["successLikeStatuses"]
    notes = "\n".join(pack["frontendSafeContractNotes"])
    assert "does not call" in notes
    assert "does not write frontend_fixtures/harmonyos" in notes
    assert "idempotent replay" in notes


def test_api_sqlite_backend_harmonyos_error_fixture_pack_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_error_fixture_pack.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec").json()
    assert spec["spec"]["version"] == "v2_9_8"

    response = client.post("/agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview", json=_fixture_args(db_path)).json()

    assert response["context_persistence_sqlite_backend_harmonyos_error_fixture_pack_version"] == "v2_9_8"
    summary = response["context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary"]
    assert summary["validation_status"] == "sqlite_backend_harmonyos_error_fixture_pack_ready"
    assert summary["scenario_count"] == 5
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["fixture_files_written"] is False
    assert response["frontend_fixtures_directory_written"] is False
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert not db_path.exists()


def test_terminal_sqlite_backend_harmonyos_error_fixture_pack_command_prints_compact_status(tmp_path: Path) -> None:
    command = "/sqlite-harmonyos-error-fixture-pack " + json.dumps(_fixture_args(tmp_path / "terminal_error_fixture.sqlite"), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendHarmonyOSErrorFixturePack>" in out
    assert "version: v2_9_8" in out
    assert "validation_status: sqlite_backend_harmonyos_error_fixture_pack_ready" in out
    assert "error_fixture_pack_preview_only: true" in out
    assert "contains_missing_write_gate_fixture: true" in out
    assert "contains_invalid_sqlite_db_path_fixture: true" in out
    assert "contains_empty_readback_fixture: true" in out
    assert "contains_idempotent_replay_fixture: true" in out
    assert "contains_malformed_payload_fixture: true" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "frontend_fixtures_directory_written: false" in out
    assert "routine_start_enabled: false" in out


def test_terminal_session_sqlite_backend_harmonyos_error_fixture_pack_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_error_fixture_pack.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_harmonyos_error_fixture_pack(_fixture_args(db_path))

    assert response["ok"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["fixture_files_written"] is False
    assert response["frontend_fixtures_directory_written"] is False
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["terminal_session_memory_loaded_by_cli"] is False
    assert session.persisted_context_show()["memory_loaded"] is False
    assert not db_path.exists()


def test_context_and_runtime_manifests_advertise_sqlite_backend_harmonyos_error_fixture_pack() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_sqlite_backend_harmonyos_error_fixture_pack_spec_route"] == "GET /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_harmonyos_error_fixture_pack"] == "POST /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview"
    assert runtime["context_persistence_sqlite_backend_harmonyos_error_fixture_pack"]["version"] == "v2_9_8"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_harmonyos_error_fixture_pack"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_harmonyos_error_fixture_pack_version"] == "v2_9_8"


def test_sqlite_backend_harmonyos_error_fixture_pack_does_not_import_engine_or_modify_shared_frontend_fixtures() -> None:
    import jammate_agent.core.tool_invocation as tool_invocation_module

    source_file = Path(tool_invocation_module.__file__).read_text(encoding="utf-8")
    assert "jammate_engine" not in source_file
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_SQLITE_CONTEXT_PERSISTENCE_ERROR_FIXTURE_V2_9_8.json").exists()
