from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
    build_today_practice_guidance_action_card_payload,
    build_today_practice_guidance_action_card_summary,
    context_engineering_skeleton_contract,
    today_practice_guidance_action_card_contract,
)
from jammate_api.app import app


def _safe_guidance_output() -> dict:
    return {
        "guidance_mode": "adjust_based_on_history",
        "summary": "你最近已经练过 Bossa comping，今天建议回到 Medium Swing ii-V-I，先练 15 分钟。",
        "recommended_focus": "Medium Swing guide-tone voice leading",
        "recommended_blocks": [
            {
                "blockId": "day2_swing",
                "title": "ii-V-I Medium Swing",
                "goal": "Guide-tone voice leading",
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
            }
        ],
        "routine_candidates": [
            {
                "candidateId": "routine_day2_swing",
                "routineName": "ii-V-I Medium Swing",
                "tuneTitle": "Autumn Leaves",
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
                "loopEnabled": True,
            }
        ],
        "adjustment_reason": "最近 Bossa 练习已完成，今天回到原计划的 Swing block。",
        "user_confirmation_required": True,
        "next_client_actions": ["show_guidance", "present_routine_candidate"],
    }


def _provider_result() -> dict:
    return {"ok": True, "provider_name": "fixture", "content": json.dumps(_safe_guidance_output(), ensure_ascii=False)}


def test_today_practice_guidance_action_card_contract_is_display_only() -> None:
    spec = today_practice_guidance_action_card_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION == "v2_7_8"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/action-card/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/action-card/preview"
    assert spec["execution_status"]["action_card_payload_enabled"] is True
    assert spec["execution_status"]["card_display_only"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["card_executes_tool"] is False
    assert spec["uses_contracts"]["provider_boundary_e2e"] == "v2_7_7"
    assert spec["uses_contracts"]["output_validation"] == "v2_7_6"


def test_valid_guidance_becomes_routine_display_action_card_without_execution() -> None:
    payload_obj = build_today_practice_guidance_action_card_payload({"providerResult": _provider_result()}, trace_id="trace_card")
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_8"
    assert payload["validation"]["is_valid"] is True
    assert payload["validation"]["status"] == "ready_for_client_display"
    assert payload["action_card"]["action_type"] == "routine_guidance_display_card"
    assert payload["action_card"]["side_effect_level"] == "none"
    assert payload["action_card"]["requires_user_confirmation"] is False
    assert payload["action_card"]["requires_user_confirmation_before_routine_start"] is True
    assert payload["action_card"]["client_decides_presentation"] is True
    assert payload["action_card"]["frontend_flow_assumption"] is False
    assert payload["routine_candidate_cards"][0]["requires_user_confirmation_before_start"] is True
    assert payload["routine_candidate_cards"][0]["does_start_playback"] is False
    assert payload["routine_candidate_cards"][0]["does_call_accompaniment_generate"] is False
    assert payload["next_client_actions"] == ["show_guidance", "present_routine_candidate", "dismiss", "view_trace"]
    assert payload["tool_executed"] is False
    assert payload["route_called"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["accompaniment_generate_call_enabled"] is False

    summary = build_today_practice_guidance_action_card_summary(payload=payload_obj)
    assert summary["is_valid"] is True
    assert summary["routine_candidate_count"] == 1
    assert summary["card_display_only"] is True
    assert summary["routine_start_enabled"] is False


def test_unsafe_guidance_output_produces_blocked_non_executable_card() -> None:
    unsafe = _safe_guidance_output()
    unsafe.update(
        {
            "user_confirmation_required": False,
            "next_client_actions": ["start_playback", "call_accompaniment_generate"],
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/secret.mid",
            "startRoutine": True,
        }
    )
    payload = build_today_practice_guidance_action_card_payload({"todayPracticeGuidanceOutput": unsafe}).to_dict()
    assert payload["validation"]["is_valid"] is False
    assert payload["validation"]["status"] == "blocked_by_guidance_validator"
    assert payload["action_card"]["preview_status"] == "blocked_by_guidance_validator"
    assert payload["routine_candidate_cards"] == []
    assert payload["routine_start_enabled"] is False
    assert payload["midi_asset_created"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/secret.mid" not in serialized


def test_api_today_practice_guidance_action_card_routes() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/action-card/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_8"

    response = client.post(
        "/agent/context/today-practice-guidance/action-card/preview",
        json={"providerResult": _provider_result(), "traceId": "api_trace"},
    ).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_action_card_version"] == "v2_7_8"
    assert response["today_practice_guidance_action_card_summary"]["is_valid"] is True
    assert response["today_practice_guidance_action_card_summary"]["routine_candidate_count"] == 1
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_today_practice_guidance_action_card_command_traces(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.today_practice_guidance_action_card({"providerResult": _provider_result()})
    assert response["ok"] is True
    assert response["today_practice_guidance_action_card_summary"]["is_valid"] is True
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_today_practice_guidance_action_card" for item in traces)


def test_context_builder_and_skeleton_reference_action_card_without_engine_dependency() -> None:
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    data = packet.to_dict()
    assert data["capabilities"]["supports_today_practice_guidance_action_card"] is True
    assert data["routing_hints"]["today_practice_guidance_action_card_version"] == "v2_7_8"

    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["today_practice_guidance_action_card"]["version"] == "v2_7_8"
    assert skeleton["guards"]["llm_called"] is False
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_ACTION_CARD_V2_7_8.md"
    assert "from jammate_engine" not in tool_invocation
    assert docs_path.exists()
