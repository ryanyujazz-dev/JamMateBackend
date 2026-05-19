from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
    build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload,
    build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary,
    build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload,
    today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract,
)
from jammate_api.app import app


def _provider_result() -> dict:
    return {
        "content": {
            "guidance_mode": "continue_original_plan",
            "summary": "从已恢复的长期计划继续，今天优先练 Medium Swing ii-V-I comping。",
            "recommended_focus": "ii-V-I comping 稳定性",
            "recommended_blocks": [
                {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 guide-tone voice leading"},
            ],
            "routine_candidates": [
                {"routineName": "Persisted Medium Swing comping routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"},
            ],
            "profile_considerations": "匹配已恢复用户画像中的 medium_swing 偏好、ii-V-I focus 和 90-120 bpm 舒适速度区间。",
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }


def _args() -> dict:
    return {
        "userInput": "今天该练什么？",
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
        "providerResult": _provider_result(),
    }


def test_roundtrip_contract_exposes_route_command_and_guards() -> None:
    spec = today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION == "v2_8_20"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview"
    assert spec["terminal_command"] == "/harmonyos-debug-fixture-roundtrip [json_payload]"
    assert spec["execution_status"]["roundtrip_preview_enabled"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["client_decides_presentation"] is True
    assert spec["guards"]["frontend_flow_assumption"] is False


def test_roundtrip_from_harmonyos_debug_fixture_to_recovery_guidance() -> None:
    fixture_payload = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(_args()).to_dict()
    fixture = fixture_payload["harmonyos_debug_fixture"]
    payload_obj = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload({"harmonyosDebugFixture": fixture, "providerResult": _provider_result()})
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_20"
    assert summary["accepted"] is True
    assert summary["roundtrip_ready"] is True
    assert summary["agent_preview_route_matches_expected"] is True
    assert summary["profile_context_recovered"] is True
    assert summary["active_plan_context_recovered"] is True
    assert summary["routine_history_context_recovered"] is True
    assert summary["guidance_action_card_is_valid"] is True
    assert summary["routine_candidate_count"] == 1
    assert payload["recovery_payload"]["guidance_payload"]["action_card_payload"]["validation"]["is_valid"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False


def test_terminal_memory_roundtrip_command_uses_loaded_context() -> None:
    session = TerminalChatSession()
    loaded = session.persisted_context_load(_args())
    assert loaded["ok"] is True
    response = session.harmonyos_debug_fixture_roundtrip({})
    assert response["ok"] is True
    assert response["memory_loaded"] is True
    summary = response["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary"]
    assert summary["roundtrip_ready"] is True
    assert summary["profile_context_recovered"] is True
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_api_roundtrip_preview_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_20"
    fixture_payload = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(_args()).to_dict()
    response = client.post(
        "/agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
        json={"harmonyosDebugFixture": fixture_payload["harmonyos_debug_fixture"], "providerResult": _provider_result()},
    ).json()
    assert response["ok"] is True
    summary = response["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary"]
    assert summary["roundtrip_ready"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_cli_roundtrip_command_is_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    exit_code = run_interactive_chat(["--once", "/harmonyos-debug-fixture-roundtrip " + json.dumps(_args(), ensure_ascii=False)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "HarmonyOSDebugFixtureRoundtripE2E>" in out
    assert "roundtrip_ready: True" in out
    assert "routine_start_enabled: false" in out


def test_roundtrip_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_spec_route"] == "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e"] == "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview"
    assert runtime["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e"]["version"] == "v2_8_20"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_version"] == "v2_8_20"


def test_roundtrip_does_not_import_engine_or_touch_frontend_fixture_files() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_V2_8_20.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
