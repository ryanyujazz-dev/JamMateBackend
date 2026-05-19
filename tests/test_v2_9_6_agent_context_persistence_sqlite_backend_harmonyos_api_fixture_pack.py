from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
    build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload,
    build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary,
    context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract,
)
from jammate_api.app import app


def _fixture_args(db_path: Path) -> dict:
    return {
        "baseUrl": "http://127.0.0.1:8000",
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "traceId": "trace_harmonyos_fixture_pack_test",
        "idempotencyKey": "idem_harmonyos_fixture_pack_test",
        "userId": "harmonyos_user_001",
        "candidateId": "candidate_harmonyos_fixture_pack_test",
        "confirmationId": "confirmation_harmonyos_fixture_pack_test",
        "targetClient": "harmonyos",
        "writeToFrontendFixtures": True,
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": {
            "userId": "harmonyos_user_001",
            "preferredStyles": ["medium_swing"],
            "focusAreas": ["ii-V-I"],
            "api_key": "SHOULD_NOT_LEAK",
        },
        "practicePlan": {
            "planId": "plan_harmonyos_fixture_pack_test",
            "status": "active",
            "planBlocks": [{"blockId": "block_harmonyos_fixture_pack_test", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104}],
        },
        "routineHistoryRecords": [{"sessionId": "session_harmonyos_fixture_pack_test", "completed": True, "style": "medium_swing"}],
        "providerResult": {
            "content": {
                "guidance_mode": "continue_original_plan",
                "summary": "HarmonyOS fixture deterministic guidance",
                "recommended_focus": "ii-V-I",
                "recommended_blocks": [{"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
                "routine_candidates": [{"routineName": "HarmonyOS fixture routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
                "user_confirmation_required": True,
                "next_client_actions": ["show_guidance", "present_routine_candidate"],
            }
        },
    }


def test_sqlite_backend_harmonyos_api_fixture_pack_contract() -> None:
    spec = context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION == "v2_9_6"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-harmonyos-api-fixture-pack"
    assert spec["short_terminal_command"] == "/sqlite-harmonyos-api-fixture-pack"
    assert spec["execution_status"]["sqlite_backend_harmonyos_api_fixture_pack_implemented"] is True
    assert spec["execution_status"]["fixture_pack_preview_only"] is True
    assert spec["execution_status"]["frontend_fixtures_directory_write_enabled"] is False
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["guards"]["fixture_pack_calls_existing_routes"] is False
    assert spec["guards"]["fixture_pack_writes_frontend_fixtures"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_sqlite_backend_harmonyos_api_fixture_pack_core_payload_is_preview_only(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_fixture_pack_should_not_exist.sqlite"
    payload_obj = build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload(_fixture_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_6"
    assert payload["validation"]["status"] == "sqlite_backend_harmonyos_api_fixture_pack_ready"
    assert payload["validation"]["fixture_pack_preview_only"] is True
    assert payload["validation"]["request_count"] >= 6
    assert payload["validation"]["frontend_fixtures_directory_written"] is False
    assert payload["fixture_files_written"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_backend_harmonyos_api_fixture_pack_ready"
    assert summary["request_count"] >= 6
    assert summary["contains_store_execute_fixture"] is True
    assert summary["contains_today_guidance_fixture"] is True
    assert "fixture_pack_preview_ignores_file_write_flags_agent_track_does_not_touch_frontend_fixtures" in summary["warnings"]
    assert not db_path.exists()
    dumped = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in dumped
    assert "[REDACTED]" in dumped


def test_sqlite_backend_harmonyos_api_fixture_pack_contains_copyable_harmonyos_contract(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload(_fixture_args(tmp_path / "fixture.sqlite")).to_dict()

    routes = {item["route_key"]: item for item in payload["harmonyos_request_examples"]}
    assert "sqlite_backend_store" in routes
    assert "sqlite_backend_readback_context_recovery" in routes
    assert "sqlite_backend_today_guidance_recovery_e2e" in routes
    assert "sqlite_backend_api_memory_debug_pack" in routes
    assert routes["sqlite_backend_store"]["client_confirmation_required_before_write"] is True
    assert routes["sqlite_backend_today_guidance_recovery_e2e"]["fixture_pack_executes_request"] is False
    assert payload["arkts_client_sketch"]["responseCasePolicy"].startswith("Backend returns canonical snake_case")
    notes = "\n".join(payload["integration_boundary_notes"])
    assert "does not write frontend_fixtures/harmonyos" in notes
    assert "display-only" in notes
    assert "snake_case" in notes
    curl_examples = payload["harmonyos_api_fixture_pack"]["curlExamples"]
    assert len(curl_examples) == payload["validation"]["request_count"]
    assert all("curl -s -X POST" in item for item in curl_examples)


def test_api_sqlite_backend_harmonyos_api_fixture_pack_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_harmonyos_fixture_pack.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec").json()
    assert spec["spec"]["version"] == "v2_9_6"

    response = client.post("/agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview", json=_fixture_args(db_path)).json()

    assert response["context_persistence_sqlite_backend_harmonyos_api_fixture_pack_version"] == "v2_9_6"
    summary = response["context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary"]
    assert summary["validation_status"] == "sqlite_backend_harmonyos_api_fixture_pack_ready"
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


def test_terminal_sqlite_backend_harmonyos_api_fixture_pack_command_prints_compact_status(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_harmonyos_fixture_pack.sqlite"
    command = "/sqlite-harmonyos-api-fixture-pack " + json.dumps(_fixture_args(db_path), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendHarmonyOSApiFixturePack>" in out
    assert "version: v2_9_6" in out
    assert "validation_status: sqlite_backend_harmonyos_api_fixture_pack_ready" in out
    assert "fixture_pack_preview_only: true" in out
    assert "fixture_files_written: false" in out
    assert "frontend_fixtures_directory_written: false" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "routine_start_enabled: false" in out
    assert not db_path.exists()


def test_terminal_session_sqlite_backend_harmonyos_api_fixture_pack_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_harmonyos_fixture_pack.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_harmonyos_api_fixture_pack(_fixture_args(db_path))

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


def test_context_and_runtime_manifests_advertise_sqlite_backend_harmonyos_api_fixture_pack() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_sqlite_backend_harmonyos_api_fixture_pack_spec_route"] == "GET /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_harmonyos_api_fixture_pack"] == "POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview"
    assert runtime["context_persistence_sqlite_backend_harmonyos_api_fixture_pack"]["version"] == "v2_9_6"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_harmonyos_api_fixture_pack"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_harmonyos_api_fixture_pack_version"] == "v2_9_6"


def test_sqlite_backend_harmonyos_api_fixture_pack_does_not_import_engine_or_modify_shared_frontend_fixtures() -> None:
    import jammate_agent.core.tool_invocation as tool_invocation_module

    source_file = Path(tool_invocation_module.__file__).read_text(encoding="utf-8")
    assert "jammate_engine" not in source_file
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_SQLITE_CONTEXT_PERSISTENCE_FIXTURE_V2_9_6.json").exists()
