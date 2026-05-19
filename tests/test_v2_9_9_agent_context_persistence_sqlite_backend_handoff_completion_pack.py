from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_HANDOFF_COMPLETION_PACK_VERSION,
    build_context_persistence_sqlite_backend_handoff_completion_pack_payload,
    build_context_persistence_sqlite_backend_handoff_completion_pack_summary,
    context_persistence_sqlite_backend_handoff_completion_pack_contract,
)
from jammate_api.app import app


def _handoff_args(db_path: Path) -> dict:
    return {
        "handoffId": "agent_v2_9_sqlite_backend_persistence_handoff_test",
        "traceId": "trace_sqlite_handoff_completion_test",
        "sqliteDbPath": str(db_path),
        "regressionResults": {
            "v2_9_regression_count": 75,
            "v2_8_v2_9_regression_count": 238,
        },
    }


def test_sqlite_backend_handoff_completion_pack_contract() -> None:
    spec = context_persistence_sqlite_backend_handoff_completion_pack_contract()

    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_HANDOFF_COMPLETION_PACK_VERSION == "v2_9_9"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-handoff-completion-pack/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-handoff-completion-pack/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-handoff-completion-pack"
    assert spec["short_terminal_command"] == "/sqlite-handoff-completion-pack"
    assert spec["execution_status"]["sqlite_backend_handoff_completion_pack_implemented"] is True
    assert spec["execution_status"]["handoff_preview_only"] is True
    assert spec["execution_status"]["database_connection_created"] is False
    assert spec["execution_status"]["frontend_fixtures_directory_write_enabled"] is False
    assert spec["guards"]["payload_writes_sqlite"] is False
    assert spec["guards"]["payload_reads_sqlite"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert set(spec["uses_contracts"]) >= {
        "sqlite_backend_store",
        "sqlite_backend_readback_context_recovery",
        "sqlite_backend_today_guidance_recovery_e2e",
        "sqlite_backend_harmonyos_error_fixture_pack",
    }


def test_sqlite_backend_handoff_completion_pack_payload_is_preview_only(tmp_path: Path) -> None:
    db_path = tmp_path / "handoff_should_not_exist.sqlite"
    payload_obj = build_context_persistence_sqlite_backend_handoff_completion_pack_payload(_handoff_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_handoff_completion_pack_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_9"
    assert payload["handoff_status"] == "sqlite_backend_handoff_completion_pack_ready"
    assert payload["validation"]["status"] == "sqlite_backend_handoff_completion_pack_ready"
    assert payload["validation"]["handoff_preview_only"] is True
    assert payload["validation"]["milestone_count"] == 9
    assert [item["version"] for item in payload["completed_milestones"]] == [f"v2_9_{idx}" for idx in range(9)]
    assert payload["api_route_handoff_pack"]["only_route_with_backend_write_capability"] == "POST /agent/context/persistence-sqlite-backend-store/execute"
    assert payload["api_route_handoff_pack"]["backend_write_requires_explicit_gate"] is True
    assert payload["terminal_handoff_pack"]["terminal_memory_scope"] == "current process only"
    assert payload["harmonyos_handoff_pack"]["frontend_fixture_files_modified_in_agent_line"] is False
    assert payload["error_fixture_handoff_pack"]["idempotent_replay_is_success_like"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["fixture_files_written"] is False
    assert payload["frontend_fixtures_directory_written"] is False
    assert payload["terminal_session_memory_loaded_by_cli"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_backend_handoff_completion_pack_ready"
    assert summary["milestone_count"] == 9
    assert summary["api_route_count"] == 10
    assert summary["terminal_command_count"] == 10
    assert summary["harmonyos_handoff_ready"] is True
    assert summary["error_fixture_handoff_ready"] is True
    assert "handoff_completion_pack_preview_only_no_routes_executed" in summary["warnings"]
    assert not db_path.exists()


def test_sqlite_backend_handoff_completion_pack_contains_integration_checklist_and_regression_commands(tmp_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_handoff_completion_pack_payload(_handoff_args(tmp_path / "handoff.sqlite")).to_dict()

    checklist = payload["integration_handoff_checklist"]
    assert len(checklist) == 5
    assert checklist[0]["owner_track"] == "integration"
    assert all(item["agent_branch_file_write_required"] is False for item in checklist)
    commands = payload["regression_handoff"]["recommended_commands"]
    assert "PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py" in commands
    assert "PYTHONPATH=src python tools/check_development_harness.py" in commands
    next_phase = payload["next_phase_recommendation"]
    assert next_phase["phase_status_after_v2_9_9"] == "ready_for_integration_handoff_or_v2_10_persistence_policy_hardening"
    assert next_phase["do_not_add_post_practice_recommendation_card"] is True


def test_api_sqlite_backend_handoff_completion_pack_preview_is_no_side_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "api_handoff.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-handoff-completion-pack/spec").json()
    assert spec["spec"]["version"] == "v2_9_9"

    response = client.post("/agent/context/persistence-sqlite-backend-handoff-completion-pack/preview", json=_handoff_args(db_path)).json()

    assert response["context_persistence_sqlite_backend_handoff_completion_pack_version"] == "v2_9_9"
    summary = response["context_persistence_sqlite_backend_handoff_completion_pack_summary"]
    assert summary["validation_status"] == "sqlite_backend_handoff_completion_pack_ready"
    assert summary["handoff_preview_only"] is True
    assert summary["milestone_count"] == 9
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


def test_terminal_sqlite_backend_handoff_completion_pack_command_prints_compact_status(tmp_path: Path) -> None:
    command = "/sqlite-handoff-completion-pack " + json.dumps(_handoff_args(tmp_path / "terminal_handoff.sqlite"), ensure_ascii=False)
    output = io.StringIO()

    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)

    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendHandoffCompletionPack>" in out
    assert "version: v2_9_9" in out
    assert "validation_status: sqlite_backend_handoff_completion_pack_ready" in out
    assert "handoff_preview_only: true" in out
    assert "milestone_count: 9" in out
    assert "api_route_count: 10" in out
    assert "terminal_command_count: 10" in out
    assert "harmonyos_handoff_ready: true" in out
    assert "error_fixture_handoff_ready: true" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "frontend_fixtures_directory_written: false" in out
    assert "routine_start_enabled: false" in out


def test_terminal_session_sqlite_backend_handoff_completion_pack_response_has_no_memory_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "session_handoff.sqlite"
    session = TerminalChatSession()
    response = session.context_persistence_sqlite_backend_handoff_completion_pack(_handoff_args(db_path))

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


def test_context_and_runtime_manifests_advertise_sqlite_backend_handoff_completion_pack() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_sqlite_backend_handoff_completion_pack_spec_route"] == "GET /agent/context/persistence-sqlite-backend-handoff-completion-pack/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_handoff_completion_pack"] == "POST /agent/context/persistence-sqlite-backend-handoff-completion-pack/preview"
    assert runtime["context_persistence_sqlite_backend_handoff_completion_pack"]["version"] == "v2_9_9"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_handoff_completion_pack"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_handoff_completion_pack_version"] == "v2_9_9"


def test_sqlite_backend_handoff_completion_pack_does_not_modify_shared_frontend_fixtures_or_music_runtime() -> None:
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
    assert not Path("frontend_fixtures/harmonyos/AGENT_SQLITE_CONTEXT_PERSISTENCE_HANDOFF_COMPLETION_V2_9_9.json").exists()
