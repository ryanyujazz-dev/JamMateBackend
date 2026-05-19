from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION,
    build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload,
    build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary,
    context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_sqlite_smoke_001",
        "currentGoal": "提高 Medium Swing ii-V-I comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 140]},
        "avoid": ["too_fast_tempo"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_sqlite_smoke_001",
        "title": "SQLite Smoke Practice Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_smoke_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_smoke_002", "title": "Blue Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "session_sqlite_smoke_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True},
    ]


def _provider_result() -> dict:
    return {
        "content": {
            "guidance_mode": "continue_original_plan",
            "summary": "SQLite smoke 已完成上下文写入和终端 memory autoload，今天继续练 Medium Swing ii-V-I comping。",
            "recommended_focus": "ii-V-I comping 稳定性",
            "recommended_blocks": [
                {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 guide-tone voice leading"},
            ],
            "routine_candidates": [
                {"routineName": "SQLite smoke Medium Swing routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"},
            ],
            "profile_considerations": "匹配 SQLite 后端恢复出的 medium_swing 偏好、ii-V-I focus 和 90-120 bpm 舒适速度区间。",
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }


def _smoke_args(db_path: Path, *, idempotency_key: str = "idem_sqlite_smoke_001", trace_id: str = "trace_sqlite_smoke") -> dict:
    return {
        "backendPersistenceEnabled": True,
        "executeBackendPersistence": True,
        "backendReadbackEnabled": True,
        "executeBackendReadback": True,
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "traceId": trace_id,
        "idempotencyKey": idempotency_key,
        "userId": "dev_user",
        "candidateKind": "practice_plan_persistence_candidate",
        "candidateId": "candidate_sqlite_smoke_001",
        "confirmationId": "confirmation_sqlite_smoke_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
        "availableMinutes": 25,
        "providerResult": _provider_result(),
    }


def test_sqlite_backend_terminal_memory_to_guidance_smoke_contract() -> None:
    spec = context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION == "v2_9_4"
    assert spec["spec_route"] == "GET /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview"
    assert spec["terminal_command"] == "/context-persistence-sqlite-backend-terminal-memory-to-guidance-smoke"
    assert spec["short_terminal_command"] == "/sqlite-memory-guidance-smoke"
    assert spec["execution_status"]["sqlite_backend_terminal_memory_to_guidance_smoke_implemented"] is True
    assert spec["execution_status"]["guidance_preview_display_only"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_creates_midi_asset"] is False


def test_sqlite_backend_terminal_memory_to_guidance_smoke_blocks_without_write_and_readback_gates(tmp_path: Path) -> None:
    db_path = tmp_path / "blocked_smoke.sqlite"
    payload = build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload({"sqliteDbPath": str(db_path), "environment": "test"}).to_dict()

    assert payload["validation"]["status"] == "sqlite_backend_terminal_memory_to_guidance_smoke_blocked"
    assert "sqlite_backend_store_not_accepted" in payload["validation"]["blocked_reasons"]
    assert "terminal_memory_autoload_not_ready" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["backend_database_read"] is False
    assert payload["guidance_preview_ready"] is False
    assert not db_path.exists()


def test_sqlite_backend_terminal_memory_to_guidance_smoke_core_payload_writes_reads_and_builds_guidance(tmp_path: Path) -> None:
    db_path = tmp_path / "agent_context_smoke.sqlite"
    payload_obj = build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload(
        _smoke_args(db_path),
        trace_id="trace_sqlite_smoke_core",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_9_4"
    assert payload["validation"]["status"] == "sqlite_backend_terminal_memory_to_guidance_smoke_ready"
    assert payload["storage_written"] is True
    assert payload["backend_database_written"] is True
    assert payload["backend_database_read"] is True
    assert payload["sqlite_connection_created"] is True
    assert payload["sqlite_tables_created"] is True
    assert payload["sqlite_rows_written"] is True
    assert payload["sqlite_rows_read"] == 1
    assert payload["terminal_session_memory_write_previewed"] is True
    assert payload["terminal_session_memory_loaded_by_core"] is False
    assert payload["guidance_preview_ready"] is True
    assert payload["routine_candidate_count"] == 1
    assert payload["llm_called"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "sqlite_backend_terminal_memory_to_guidance_smoke_ready"
    assert summary["deterministic_provider_result_used"] is True
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)


def test_terminal_smoke_loads_memory_and_returns_guidance_preview(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_smoke.sqlite"
    session = TerminalChatSession()

    response = session.context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke(_smoke_args(db_path, idempotency_key="idem_terminal_smoke"))

    assert response["ok"] is True
    assert response["storage_written"] is True
    assert response["backend_database_written"] is True
    assert response["backend_database_read"] is True
    assert response["memory_loaded"] is True
    assert response["terminal_session_memory_loaded_by_cli"] is True
    assert session.persisted_context_show()["memory_loaded"] is True
    assert response["persisted_context_terminal_memory_used"] is True
    assert response["guidance_preview_ready"] is True
    assert response["routine_candidate_count"] == 1
    assert response["guidance_response_preview"]["payload_kind"] == "persisted_context_recovery_e2e"
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_api_smoke_preview_exposes_summary_without_server_session_memory(tmp_path: Path) -> None:
    db_path = tmp_path / "api_smoke.sqlite"
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec").json()
    assert spec["spec"]["version"] == "v2_9_4"

    response = client.post(
        "/agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview",
        json=_smoke_args(db_path, idempotency_key="idem_api_smoke"),
    ).json()

    assert response["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_version"] == "v2_9_4"
    assert response["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary"]["validation_status"] == "sqlite_backend_terminal_memory_to_guidance_smoke_ready"
    assert response["storage_written"] is True
    assert response["backend_database_written"] is True
    assert response["backend_database_read"] is True
    assert response["terminal_session_memory_write_previewed"] is True
    assert response["terminal_session_memory_loaded_by_api"] is False
    assert response["guidance_preview_ready"] is True
    assert response["routine_candidate_count"] == 1
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_smoke_command_prints_compact_status(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    db_path = tmp_path / "terminal_command_smoke.sqlite"
    command = "/sqlite-memory-guidance-smoke " + json.dumps(_smoke_args(db_path, idempotency_key="idem_terminal_command_smoke"), ensure_ascii=False)

    output = io.StringIO()
    exit_code = run_interactive_chat(argv=["--once", command], stdout=output)
    assert exit_code == 0
    out = output.getvalue()
    assert "ContextPersistenceSqliteBackendTerminalMemoryToGuidanceSmoke>" in out
    assert "version: v2_9_4" in out
    assert "validation_status: sqlite_backend_terminal_memory_to_guidance_smoke_ready" in out
    assert "storage_written: true" in out
    assert "memory_loaded: true" in out
    assert "guidance_preview_ready: true" in out
    assert "routine_start_enabled: false" in out


def test_context_and_runtime_manifests_advertise_sqlite_backend_terminal_memory_to_guidance_smoke() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()
    assert manifest["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_spec_route"] == "GET /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec"
    assert runtime["routes"]["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke"] == "POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview"
    assert runtime["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke"]["version"] == "v2_9_4"
    assert CapabilityManifest().to_dict()["supports_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么")
    assert packet.routing_hints["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_version"] == "v2_9_4"


def test_sqlite_backend_terminal_memory_to_guidance_smoke_does_not_import_engine_or_modify_shared_docs() -> None:
    import jammate_agent.core.tool_invocation as tool_invocation_module

    source_file = Path(tool_invocation_module.__file__).read_text(encoding="utf-8")
    assert "jammate_engine" not in source_file
    assert Path("src/jammate_engine").exists()
    assert Path("frontend_fixtures/harmonyos").exists()
