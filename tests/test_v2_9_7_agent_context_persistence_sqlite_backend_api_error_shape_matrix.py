from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_ERROR_SHAPE_MATRIX_VERSION,
    build_context_persistence_sqlite_backend_api_error_shape_matrix_payload,
    build_context_persistence_sqlite_backend_api_error_shape_matrix_summary,
    context_persistence_sqlite_backend_api_error_shape_matrix_contract,
)
from jammate_api.app import app


def _matrix_args(tmp_path: Path) -> dict:
    return {
        "baseUrl": "http://127.0.0.1:8000",
        "targetClient": "harmonyos",
        "traceId": "trace_api_error_shape_matrix_test",
        "missingReadbackSqliteDbPath": str(tmp_path / "missing_readback_should_not_exist.sqlite"),
    }


def test_sqlite_backend_api_error_shape_matrix_contract() -> None:
    spec = context_persistence_sqlite_backend_api_error_shape_matrix_contract()

    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_ERROR_SHAPE_MATRIX_VERSION == "v2_9_7"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-api-error-shape-matrix"
    assert spec["short_terminal_command"] == "/sqlite-api-error-shape-matrix"
    assert spec["execution_status"]["sqlite_backend_api_error_shape_matrix_implemented"] is True
    assert spec["execution_status"]["error_shape_matrix_preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["matrix_executes_existing_routes"] is False
    assert spec["guards"]["matrix_opens_sqlite"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert set(spec["covered_scenarios"]) >= {"missing_write_gate", "invalid_sqlite_db_path", "empty_readback", "idempotent_replay", "malformed_payload"}


def test_sqlite_backend_api_error_shape_matrix_core_payload_is_preview_only(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing_readback_should_not_exist.sqlite"
    payload_obj = build_context_persistence_sqlite_backend_api_error_shape_matrix_payload(_matrix_args(tmp_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_api_error_shape_matrix_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_7"
    assert payload["validation"]["status"] == "sqlite_backend_api_error_shape_matrix_ready"
    assert payload["validation"]["error_shape_matrix_preview_only"] is True
    assert payload["validation"]["scenario_count"] == 5
    assert payload["validation"]["sampled_shape_count"] == 5
    assert payload["validation"]["matrix_executes_existing_routes"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["sqlite_rows_read"] == 0
    assert payload["fixture_files_written"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert summary["validation_status"] == "sqlite_backend_api_error_shape_matrix_ready"
    assert summary["contains_missing_write_gate_shape"] is True
    assert summary["contains_invalid_sqlite_db_path_shape"] is True
    assert summary["contains_empty_readback_shape"] is True
    assert summary["contains_idempotent_replay_shape"] is True
    assert summary["contains_malformed_payload_shape"] is True
    assert summary["idempotent_replay_treated_as_success"] is True
    assert not missing_db.exists()


def test_sqlite_backend_api_error_shape_matrix_samples_match_existing_blocked_shapes(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_api_error_shape_matrix_payload(_matrix_args(tmp_path)).to_dict()
    samples = payload["sampled_blocked_response_shapes"]

    missing_gate = samples["missing_write_gate"]
    assert missing_gate["accepted"] is False
    assert missing_gate["validation_status"] == "sqlite_backend_store_blocked"
    assert "backend_persistence_enabled_must_be_true" in missing_gate["blocked_reasons"]
    assert "execute_backend_persistence_must_be_true" in missing_gate["blocked_reasons"]
    assert missing_gate["sqlite_connection_created"] is False
    assert missing_gate["storage_written"] is False

    invalid_path = samples["invalid_sqlite_db_path"]
    assert invalid_path["validation_status"] == "sqlite_backend_store_blocked"
    assert "sqlite_db_path_must_be_relative_tmp_or_mnt_data_sqlite_file" in invalid_path["blocked_reasons"]
    assert invalid_path["sqlite_connection_created"] is False

    empty_readback = samples["empty_readback"]
    assert empty_readback["accepted"] is False
    assert empty_readback["validation_status"] == "sqlite_backend_readback_context_recovery_blocked"
    assert any(reason.startswith("sqlite_backend_readback_failed:") for reason in empty_readback["blocked_reasons"])
    assert empty_readback["sqlite_connection_created"] is False
    assert empty_readback["backend_database_read"] is False

    idempotent = samples["idempotent_replay"]
    assert idempotent["accepted"] is True
    assert idempotent["validation_status"] == "sqlite_backend_store_idempotent_replay"
    assert idempotent["idempotent_replay"] is True
    assert idempotent["client_treats_as_success"] is True
    assert idempotent["storage_written"] is False

    malformed = samples["malformed_payload"]
    assert malformed["accepted"] is False
    assert malformed["validation_status"] == "request_body_must_be_json_object"
    assert malformed["http_status_hint"] == 422
    assert "request_body_must_be_json_object" in malformed["blocked_reasons"]


def test_sqlite_backend_api_error_shape_matrix_contains_harmonyos_handling_notes(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_api_error_shape_matrix_payload(_matrix_args(tmp_path)).to_dict()

    handling = payload["harmonyos_client_handling"]
    assert handling["target_client"] == "harmonyos"
    assert handling["treat_idempotent_replay_as_success"] is True
    assert "普通 today-practice guidance" in handling["empty_readback_fallback"] or "ordinary guidance" in handling["empty_readback_fallback"]
    policy = handling["response_case_policy"]
    assert "camelCase" in policy["request_case"]
    assert "snake_case" in policy["response_case"]
    key_paths = policy["key_paths_to_check"]
    assert "*.validation.status" in key_paths
    assert "*.validation.blocked_reasons" in key_paths
    matrix_keys = {item["scenario_key"] for item in payload["error_shape_matrix"]}
    assert matrix_keys == {"missing_write_gate", "invalid_sqlite_db_path", "empty_readback", "idempotent_replay", "malformed_payload"}


def test_api_sqlite_backend_api_error_shape_matrix_preview_is_no_side_effect(tmp_path: Path) -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec").json()
    assert spec["spec"]["version"] == "v2_9_7"

    response = client.post("/agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview", json=_matrix_args(tmp_path)).json()

    assert response["context_persistence_sqlite_backend_api_error_shape_matrix_version"] == "v2_9_7"
    summary = response["context_persistence_sqlite_backend_api_error_shape_matrix_summary"]
    assert summary["validation_status"] == "sqlite_backend_api_error_shape_matrix_ready"
    assert summary["scenario_count"] == 5
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["sqlite_rows_read"] == 0
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_sqlite_backend_api_error_shape_matrix_command_prints_compact_status(tmp_path: Path) -> None:
    command = "/sqlite-api-error-shape-matrix " + json.dumps(_matrix_args(tmp_path), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendApiErrorShapeMatrix>" in out
    assert "version: v2_9_7" in out
    assert "validation_status: sqlite_backend_api_error_shape_matrix_ready" in out
    assert "error_shape_matrix_preview_only: true" in out
    assert "contains_missing_write_gate_shape: true" in out
    assert "contains_invalid_sqlite_db_path_shape: true" in out
    assert "contains_empty_readback_shape: true" in out
    assert "contains_idempotent_replay_shape: true" in out
    assert "contains_malformed_payload_shape: true" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "sqlite_connection_created: false" in out
    assert "routine_start_enabled: false" in out


def test_terminal_session_sqlite_backend_api_error_shape_matrix_response_has_no_memory_mutation(tmp_path: Path) -> None:
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_api_error_shape_matrix(_matrix_args(tmp_path))

    assert response["ok"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["sqlite_rows_written"] is False
    assert response["sqlite_rows_read"] == 0
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["terminal_session_memory_loaded_by_cli"] is False
    assert session.persisted_context_show()["memory_loaded"] is False


def test_context_and_runtime_manifests_advertise_sqlite_backend_api_error_shape_matrix() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()

    assert manifest["context_persistence_sqlite_backend_api_error_shape_matrix_spec_route"] == "GET /agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_api_error_shape_matrix"] == "POST /agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview"
    assert runtime["context_persistence_sqlite_backend_api_error_shape_matrix"]["version"] == "v2_9_7"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_api_error_shape_matrix"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_api_error_shape_matrix_version"] == "v2_9_7"


def test_sqlite_backend_api_error_shape_matrix_does_not_import_engine_or_write_frontend_fixtures() -> None:
    import jammate_agent.core.tool_invocation as tool_invocation_module

    source_file = Path(tool_invocation_module.__file__).read_text(encoding="utf-8")
    assert "jammate_engine" not in source_file
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_SQLITE_CONTEXT_PERSISTENCE_ERROR_SHAPE_MATRIX_V2_9_7.json").exists()
