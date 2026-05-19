from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION,
    build_context_persistence_sqlite_backend_api_memory_debug_pack_payload,
    build_context_persistence_sqlite_backend_api_memory_debug_pack_summary,
    context_persistence_sqlite_backend_api_memory_debug_pack_contract,
)
from jammate_api.app import app


def _debug_args(db_path: Path) -> dict:
    return {
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "traceId": "trace_debug_pack_test",
        "idempotencyKey": "idem_debug_pack_test",
        "userId": "debug_user_001",
        "candidateId": "candidate_debug_pack_test",
        "confirmationId": "confirmation_debug_pack_test",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": {
            "userId": "debug_user_001",
            "preferredStyles": ["medium_swing"],
            "focusAreas": ["ii-V-I"],
            "api_key": "SHOULD_NOT_LEAK",
        },
        "practicePlan": {
            "planId": "plan_debug_pack_test",
            "status": "active",
            "planBlocks": [{"blockId": "block_debug_pack_test", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104}],
        },
        "routineHistoryRecords": [{"sessionId": "session_debug_pack_test", "completed": True, "style": "medium_swing"}],
        "providerResult": {
            "content": {
                "guidance_mode": "continue_original_plan",
                "summary": "debug pack deterministic guidance",
                "recommended_focus": "ii-V-I",
                "recommended_blocks": [{"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
                "routine_candidates": [{"routineName": "Debug routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
                "user_confirmation_required": True,
                "next_client_actions": ["show_guidance", "present_routine_candidate"],
            }
        },
    }


def test_sqlite_backend_api_memory_debug_pack_contract() -> None:
    spec = context_persistence_sqlite_backend_api_memory_debug_pack_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION == "v2_9_5"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-api-memory-debug-pack"
    assert spec["short_terminal_command"] == "/sqlite-api-memory-debug-pack"
    assert spec["execution_status"]["sqlite_backend_api_memory_debug_pack_implemented"] is True
    assert spec["execution_status"]["api_debug_pack_preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["execution_status"]["server_memory_mutation_enabled"] is False
    assert spec["guards"]["debug_pack_calls_existing_routes"] is False
    assert spec["guards"]["debug_pack_opens_sqlite"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_sqlite_backend_api_memory_debug_pack_core_payload_is_preview_only(tmp_path: Path) -> None:
    db_path = tmp_path / "debug_pack_should_not_exist.sqlite"
    args = _debug_args(db_path) | {"backendPersistenceEnabled": True, "executeBackendPersistence": True}
    payload_obj = build_context_persistence_sqlite_backend_api_memory_debug_pack_payload(args)
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_api_memory_debug_pack_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_5"
    assert payload["validation"]["status"] == "sqlite_backend_api_memory_debug_pack_ready"
    assert payload["validation"]["api_debug_pack_preview_only"] is True
    assert "debug_pack_preview_ignores_execution_flags_and_does_not_call_routes" in payload["validation"]["warnings"]
    assert len(payload["route_catalog"]) >= 6
    assert set(payload["request_examples"]) >= {
        "1_store_execute",
        "2_readback_preview",
        "3_today_guidance_recovery_preview",
        "4_terminal_memory_autoload_api_preview_only",
        "5_terminal_memory_to_guidance_smoke_preview",
    }
    assert payload["request_examples"]["1_store_execute"]["backendPersistenceEnabled"] is True
    assert payload["request_examples"]["2_readback_preview"]["backendReadbackEnabled"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["terminal_session_memory_loaded_by_api"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_backend_api_memory_debug_pack_ready"
    assert summary["route_count"] >= 6
    assert summary["request_example_count"] == 5
    assert not db_path.exists()
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)
    assert "[REDACTED]" in json.dumps(payload, ensure_ascii=False)


def test_sqlite_backend_api_memory_debug_pack_response_paths_include_frontend_safe_memory_notes(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_api_memory_debug_pack_payload(_debug_args(tmp_path / "notes.sqlite")).to_dict()

    route_keys = {item["key"] for item in payload["route_catalog"]}
    assert "sqlite_backend_store" in route_keys
    assert "sqlite_backend_terminal_memory_autoload_preview" in route_keys
    assert "api_memory_debug_pack" in route_keys
    all_paths = [path for item in payload["response_path_catalog"] for path in item["paths"]]
    assert "context_persistence_sqlite_backend_store_summary.storage_written" in all_paths
    assert "terminal_session_memory_loaded_by_api" in all_paths
    notes = "\n".join(payload["frontend_safe_contract_notes"])
    assert "display-only" in notes
    assert "API autoload preview does not mutate server memory" in notes
    assert "midiBase64" in notes


def test_api_sqlite_backend_api_memory_debug_pack_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_debug_pack.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec").json()
    assert spec["spec"]["version"] == "v2_9_5"

    response = client.post("/agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview", json=_debug_args(db_path)).json()

    assert response["context_persistence_sqlite_backend_api_memory_debug_pack_version"] == "v2_9_5"
    summary = response["context_persistence_sqlite_backend_api_memory_debug_pack_summary"]
    assert summary["validation_status"] == "sqlite_backend_api_memory_debug_pack_ready"
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert not db_path.exists()


def test_terminal_sqlite_backend_api_memory_debug_pack_command_prints_compact_status(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_debug_pack.sqlite"
    command = "/sqlite-api-memory-debug-pack " + json.dumps(_debug_args(db_path), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendApiMemoryDebugPack>" in out
    assert "version: v2_9_5" in out
    assert "validation_status: sqlite_backend_api_memory_debug_pack_ready" in out
    assert "api_debug_pack_preview_only: true" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "terminal_session_memory_loaded_by_api: false" in out
    assert "routine_start_enabled: false" in out
    assert not db_path.exists()


def test_terminal_session_sqlite_backend_api_memory_debug_pack_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_debug_pack.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_api_memory_debug_pack(_debug_args(db_path))

    assert response["ok"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["backend_database_read"] is False
    assert response["sqlite_connection_created"] is False
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["terminal_session_memory_loaded_by_cli"] is False
    assert session.persisted_context_show()["memory_loaded"] is False
    assert not db_path.exists()


def test_context_and_runtime_manifests_advertise_sqlite_backend_api_memory_debug_pack() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_sqlite_backend_api_memory_debug_pack_spec_route"] == "GET /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_api_memory_debug_pack"] == "POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview"
    assert runtime["context_persistence_sqlite_backend_api_memory_debug_pack"]["version"] == "v2_9_5"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_api_memory_debug_pack"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_api_memory_debug_pack_version"] == "v2_9_5"


def test_sqlite_backend_api_memory_debug_pack_does_not_import_engine_or_modify_shared_docs() -> None:
    import jammate_agent.core.tool_invocation as tool_invocation_module

    source_file = Path(tool_invocation_module.__file__).read_text(encoding="utf-8")
    assert "jammate_engine" not in source_file
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
