from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
    build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload,
    build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary,
    today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract,
)
from jammate_api.app import app


def _args() -> dict:
    return {
        "availableMinutes": 25,
        "userPracticeProfile": {
            "userId": "user_debug_001",
            "currentGoal": "提高 jazz comping 稳定性",
            "preferredStyles": ["medium_swing", "bossa_nova"],
            "focusAreas": ["ii-V-I", "comping"],
            "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 145]},
        },
        "practicePlan": {
            "planId": "plan_debug_001",
            "title": "Persisted Medium Swing Comping Plan",
            "status": "active",
            "planBlocks": [
                {"blockId": "block_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15},
            ],
        },
        "routineHistoryRecords": [
            {"sessionId": "session_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True},
        ],
    }


def test_contract_exposes_harmonyos_debug_fixture_preview_and_guards() -> None:
    spec = today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION == "v2_8_19"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview"
    assert spec["terminal_command"] == "/persisted-context-harmonyos-debug-fixture [json_payload]"
    assert spec["execution_status"]["debug_fixture_preview_enabled"] is True
    assert spec["execution_status"]["local_device_write_enabled_by_agent"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["frontend_flow_assumption"] is False
    assert spec["guards"]["client_decides_presentation"] is True


def test_payload_builds_harmonyos_debug_fixture_from_direct_context() -> None:
    payload = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(_args())
    data = payload.to_dict()
    summary = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary(payload=payload)
    assert summary["accepted"] is True
    assert summary["debug_fixture_ready"] is True
    assert summary["profile_context_present"] is True
    assert summary["active_plan_context_present"] is True
    assert summary["routine_history_context_present"] is True
    assert summary["agent_preview_route"] == "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview"
    fixture = data["harmonyos_debug_fixture"]
    assert fixture["fixtureContractVersion"] == "v2_8_19"
    assert fixture["clientDecidesPresentation"] is True
    assert fixture["frontendFlowAssumption"] is False
    assert fixture["expectedGuards"]["engineAdapterCalled"] is False
    assert fixture["agentRequestPreview"]["path"] == "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview"
    assert data["storage_written"] is False
    assert data["llm_called"] is False
    assert data["routine_start_enabled"] is False


def test_terminal_memory_can_be_exported_to_harmonyos_debug_fixture() -> None:
    session = TerminalChatSession()
    loaded = session.persisted_context_load(_args())
    assert loaded["ok"] is True
    response = session.persisted_context_harmonyos_debug_fixture({})
    assert response["ok"] is True
    assert response["memory_loaded"] is True
    summary = response["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary"]
    assert summary["accepted"] is True
    assert summary["source_kind"] == "terminal_persisted_context_memory_guidance_arguments"
    assert summary["debug_fixture_ready"] is True
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_api_debug_fixture_preview_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_19"
    response = client.post("/agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview", json=_args()).json()
    assert response["ok"] is True
    summary = response["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary"]
    assert summary["debug_fixture_ready"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_cli_debug_fixture_command_is_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    exit_code = run_interactive_chat(["--once", "/persisted-context-harmonyos-debug-fixture " + json.dumps(_args(), ensure_ascii=False)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PersistedContextHarmonyOSDebugFixture>" in out
    assert "debug_fixture_ready: True" in out
    assert "routine_start_enabled: false" in out


def test_debug_fixture_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_spec_route"] == "GET /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture"] == "POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview"
    assert runtime["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture"]["version"] == "v2_8_19"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_version"] == "v2_8_19"


def test_debug_fixture_does_not_import_engine_or_touch_frontend_fixture_files() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_V2_8_19.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
