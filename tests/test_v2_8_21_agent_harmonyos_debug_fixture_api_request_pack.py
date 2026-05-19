from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
    build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload,
    build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary,
    today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract,
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
        "baseUrl": "http://127.0.0.1:8000",
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


def test_api_request_pack_contract_exposes_routes_command_and_guards() -> None:
    spec = today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION == "v2_8_21"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview"
    assert spec["terminal_command"] == "/harmonyos-debug-fixture-api-request-pack [json_payload]"
    assert spec["execution_status"]["api_request_pack_preview_enabled"] is True
    assert spec["execution_status"]["calls_routes"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["client_decides_presentation"] is True
    assert spec["guards"]["frontend_flow_assumption"] is False


def test_payload_builds_copyable_three_step_harmonyos_request_pack() -> None:
    payload_obj = build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload(_args())
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_21"
    assert summary["accepted"] is True
    assert summary["api_request_pack_ready"] is True
    assert summary["request_count"] == 3
    assert summary["roundtrip_ready"] is True
    assert summary["guidance_action_card_is_valid"] is True
    request_pack = payload["api_request_pack"]
    assert request_pack["baseUrl"] == "http://127.0.0.1:8000"
    assert [request["path"] for request in request_pack["requests"]] == [
        "/agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview",
        "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
        "/agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
    ]
    assert len(request_pack["curlExamples"]) == 3
    assert payload["response_shape_preview"]["run_persisted_context_recovery_guidance_preview"]["routine_start_enabled"] is False
    assert payload["storage_written"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["routine_start_enabled"] is False


def test_terminal_memory_can_generate_api_request_pack() -> None:
    session = TerminalChatSession()
    loaded = session.persisted_context_load(_args())
    assert loaded["ok"] is True
    response = session.harmonyos_debug_fixture_api_request_pack({})
    assert response["ok"] is True
    assert response["memory_loaded"] is True
    summary = response["today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary"]
    assert summary["api_request_pack_ready"] is True
    assert summary["request_count"] == 3
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_api_request_pack_preview_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_21"
    response = client.post("/agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview", json=_args()).json()
    assert response["ok"] is True
    summary = response["today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary"]
    assert summary["api_request_pack_ready"] is True
    assert summary["request_count"] == 3
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_cli_api_request_pack_command_is_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    exit_code = run_interactive_chat(["--once", "/harmonyos-debug-fixture-api-request-pack " + json.dumps(_args(), ensure_ascii=False)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "HarmonyOSDebugFixtureAPIRequestPack>" in out
    assert "api_request_pack_ready: True" in out
    assert "request_count: 3" in out
    assert "routine_start_enabled: false" in out


def test_api_request_pack_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_harmonyos_debug_fixture_api_request_pack_spec_route"] == "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_harmonyos_debug_fixture_api_request_pack"] == "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview"
    assert runtime["today_practice_guidance_harmonyos_debug_fixture_api_request_pack"]["version"] == "v2_8_21"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_harmonyos_debug_fixture_api_request_pack"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_harmonyos_debug_fixture_api_request_pack_version"] == "v2_8_21"


def test_api_request_pack_does_not_import_engine_or_touch_frontend_fixture_files() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_V2_8_21.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
