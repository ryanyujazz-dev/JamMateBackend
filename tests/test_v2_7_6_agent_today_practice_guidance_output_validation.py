from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
    build_today_practice_guidance_output_validation_payload,
    build_today_practice_guidance_output_validation_summary,
    context_engineering_skeleton_contract,
    today_practice_guidance_output_validation_contract,
)
from jammate_api.app import app


def _safe_guidance_output() -> dict:
    return {
        "guidance_mode": "continue_original_plan",
        "summary": "今天建议继续原计划里的 Medium Swing ii-V-I，先保持 15 分钟稳定时间感。",
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
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
                "loopEnabled": True,
            }
        ],
        "user_confirmation_required": True,
        "next_client_actions": ["show_guidance", "present_routine_candidate"],
    }


def test_today_practice_guidance_output_validation_contract_is_no_execution_gate() -> None:
    spec = today_practice_guidance_output_validation_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION == "v2_7_6"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/output-validation/spec"
    assert spec["validate_route"] == "POST /agent/context/today-practice-guidance/output-validation/validate"
    assert spec["execution_status"]["output_validation_enabled"] is True
    assert spec["execution_status"]["tool_execution_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["validator_calls_llm"] is False
    assert spec["guards"]["validator_starts_playback"] is False


def test_safe_guidance_output_is_normalized_as_candidate_only() -> None:
    payload_obj = build_today_practice_guidance_output_validation_payload(
        {"todayPracticeGuidanceOutput": _safe_guidance_output()},
        trace_id="trace_validate",
    )
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_6"
    assert payload["validation"]["is_valid"] is True
    assert payload["validation"]["status"] == "accepted_candidate_guidance"
    normalized = payload["normalized_guidance_output"]
    assert normalized["guidance_mode"] == "continue_original_plan"
    assert normalized["user_confirmation_required"] is True
    assert normalized["client_decides_presentation"] is True
    assert normalized["routine_start_allowed_now"] is False
    assert normalized["accompaniment_generate_allowed_now"] is False
    assert normalized["routine_candidates"][0]["editable"] is True
    assert normalized["routine_candidates"][0]["requires_user_confirmation_before_start"] is True
    assert payload["blocked_reasons"] == []
    assert payload["llm_called"] is False
    assert payload["route_called"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False

    summary = build_today_practice_guidance_output_validation_summary(payload=payload_obj)
    assert summary["is_valid"] is True
    assert summary["routine_candidate_count"] == 1
    assert summary["routine_start_enabled"] is False


def test_unsafe_guidance_output_is_blocked_for_direct_execution_and_sensitive_fields() -> None:
    unsafe = _safe_guidance_output()
    unsafe.update(
        {
            "user_confirmation_required": False,
            "next_client_actions": ["show_guidance", "call_accompaniment_generate", "start_playback"],
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/secret.mid",
            "startRoutine": True,
        }
    )
    payload = build_today_practice_guidance_output_validation_payload(unsafe).to_dict()
    assert payload["validation"]["is_valid"] is False
    assert "user_confirmation_required_must_be_true" in payload["blocked_reasons"]
    assert "forbidden_fields_present" in payload["blocked_reasons"]
    assert "forbidden_direct_action_requested" in payload["blocked_reasons"]
    assert payload["normalized_guidance_output"]["routine_start_allowed_now"] is False
    assert payload["validation"]["midi_asset_created"] is False
    assert payload["playback_started"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/secret.mid" not in serialized


def test_api_today_practice_guidance_output_validation_routes() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/output-validation/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_6"

    response = client.post(
        "/agent/context/today-practice-guidance/output-validation/validate",
        json={"todayPracticeGuidanceOutput": _safe_guidance_output()},
    ).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_output_validation_version"] == "v2_7_6"
    assert response["today_practice_guidance_output_validation_summary"]["is_valid"] is True
    assert response["llm_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_today_practice_guidance_validate_command_traces(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.today_practice_guidance_validate({"todayPracticeGuidanceOutput": _safe_guidance_output()})
    assert response["ok"] is True
    assert response["today_practice_guidance_output_validation_summary"]["is_valid"] is True
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_today_practice_guidance_output_validation" for item in traces)


def test_context_builder_and_skeleton_reference_output_validation_without_engine_dependency() -> None:
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    data = packet.to_dict()
    assert data["routing_hints"]["today_practice_guidance_output_validation_version"] == "v2_7_6"

    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["today_practice_guidance_output_validation"]["version"] == "v2_7_6"
    assert skeleton["guards"]["llm_called"] is False
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_V2_7_6.md"
    assert "from jammate_engine" not in tool_invocation
    assert docs_path.exists()
