from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
    build_today_practice_guidance_provider_boundary_e2e_payload,
    build_today_practice_guidance_provider_boundary_e2e_summary,
    context_engineering_skeleton_contract,
    today_practice_guidance_provider_boundary_e2e_contract,
)
from jammate_api.app import app


def _active_plan() -> dict:
    return {
        "planId": "plan_four_week_comping",
        "title": "4 Week Jazz Comping Plan",
        "status": "active",
        "goal": "Build stable Bossa, Swing, and Ballad comping habits",
        "planBlocks": [
            {
                "blockId": "day1_bossa",
                "title": "Blue Bossa comping",
                "goal": "Bossa comping stability",
                "durationMinutes": 20,
                "tuneTitle": "Blue Bossa",
                "style": "bossa_nova",
                "tempo": 118,
                "completed": True,
            },
            {
                "blockId": "day2_swing",
                "title": "ii-V-I Medium Swing",
                "goal": "Guide-tone voice leading",
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
                "completed": False,
            },
        ],
    }


def _history_records() -> list[dict]:
    return [
        {
            "sessionId": "session_blue_bossa_001",
            "title": "Blue Bossa Bossa Comping",
            "tuneTitle": "Blue Bossa",
            "style": "bossa_nova",
            "tempo": 118,
            "actualSeconds": 1200,
            "completed": True,
            "planId": "plan_four_week_comping",
            "planBlockId": "day1_bossa",
            "finishedAt": "2026-05-18T20:30:00",
            "localMidiPath": "/tmp/blue_bossa.mid",
            "midiBase64": "SHOULD_NOT_LEAK",
        }
    ]


def _safe_provider_result() -> dict:
    return {
        "ok": True,
        "provider_name": "fixture",
        "model": "fixture-model",
        "content": json.dumps(
            {
                "guidance_mode": "continue_original_plan",
                "summary": "今天建议继续原计划里的 Medium Swing ii-V-I，保持 15 分钟稳定时间感。",
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
            },
            ensure_ascii=False,
        ),
    }


def test_today_practice_guidance_provider_boundary_e2e_contract_is_candidate_only() -> None:
    spec = today_practice_guidance_provider_boundary_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION == "v2_7_7"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/provider-boundary/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview"
    assert spec["execution_status"]["provider_boundary_enabled"] is True
    assert spec["execution_status"]["llm_call_default_enabled"] is False
    assert spec["execution_status"]["tool_execution_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["creates_midi_asset"] is False
    assert spec["uses_contracts"]["today_practice_guidance_output_validation"] == "v2_7_6"


def test_provider_result_fixture_runs_prompt_to_validation_without_execution() -> None:
    payload_obj = build_today_practice_guidance_provider_boundary_e2e_payload(
        {
            "activePracticePlan": _active_plan(),
            "routineHistoryRecords": _history_records(),
            "availableMinutes": 15,
            "userInput": "今天该练什么？",
            "providerResult": _safe_provider_result(),
        },
        trace_id="trace_e2e",
    )
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_7"
    assert payload["validation"]["provider_result_present"] is True
    assert payload["validation"]["provider_content_parsed"] is True
    assert payload["validation"]["output_validation_is_valid"] is True
    assert payload["e2e_summary"]["candidate_only_guidance_ready"] is True
    normalized = payload["e2e_summary"]["normalized_guidance_output"]
    assert normalized["guidance_mode"] == "continue_original_plan"
    assert normalized["routine_start_allowed_now"] is False
    assert normalized["accompaniment_generate_allowed_now"] is False
    assert normalized["routine_candidates"][0]["requires_user_confirmation_before_start"] is True
    assert payload["tool_executed"] is False
    assert payload["route_called"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/blue_bossa.mid" not in serialized

    summary = build_today_practice_guidance_provider_boundary_e2e_summary(payload=payload_obj)
    assert summary["provider_content_parsed"] is True
    assert summary["output_validation_is_valid"] is True
    assert summary["routine_candidate_count"] == 1
    assert summary["routine_start_enabled"] is False


def test_unsafe_provider_output_is_blocked_after_provider_boundary() -> None:
    unsafe = _safe_provider_result()
    unsafe["content"] = json.dumps(
        {
            "guidance_mode": "continue_original_plan",
            "summary": "Unsafe direct action should be blocked.",
            "recommended_focus": "Blocked action",
            "user_confirmation_required": False,
            "next_client_actions": ["start_playback", "call_accompaniment_generate"],
            "midiBase64": "SHOULD_NOT_LEAK",
            "startRoutine": True,
        },
        ensure_ascii=False,
    )
    payload = build_today_practice_guidance_provider_boundary_e2e_payload({"providerResult": unsafe}).to_dict()
    assert payload["validation"]["output_validation_is_valid"] is False
    assert payload["e2e_summary"]["candidate_only_guidance_ready"] is False
    assert "forbidden_fields_present" in payload["validation"]["blocked_reasons"]
    assert "forbidden_direct_action_requested" in payload["validation"]["blocked_reasons"]
    assert payload["routine_start_enabled"] is False
    assert payload["midi_asset_created"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


class _FakeProvider:
    def status(self) -> dict:
        return {"provider_class": "FakeProvider", "terminal_chat_enabled": True, "api_key_value": "SECRET_SHOULD_NOT_LEAK"}

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001 - protocol-style fake for tests.
        assert envelope.runtime_policy["tool_execution_enabled"] is False
        return LLMProviderResult(ok=True, content=_safe_provider_result()["content"], provider_name="fake", model="fake-model")


def test_explicit_injected_provider_call_is_validated_and_redacted() -> None:
    payload = build_today_practice_guidance_provider_boundary_e2e_payload(
        {"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15, "callProvider": True},
        provider=_FakeProvider(),
    ).to_dict()
    assert payload["llm_called"] is True
    assert payload["validation"]["output_validation_is_valid"] is True
    assert payload["e2e_summary"]["provider_call_requested"] is True
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SECRET_SHOULD_NOT_LEAK" not in serialized


def test_api_today_practice_guidance_provider_boundary_e2e_routes() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/provider-boundary/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_7"

    response = client.post(
        "/agent/context/today-practice-guidance/provider-boundary/e2e-preview",
        json={"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15, "providerResult": _safe_provider_result()},
    ).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_provider_boundary_e2e_version"] == "v2_7_7"
    assert response["today_practice_guidance_provider_boundary_e2e_summary"]["output_validation_is_valid"] is True
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_today_practice_guidance_e2e_command_traces(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.today_practice_guidance_e2e({"providerResult": _safe_provider_result()})
    assert response["ok"] is True
    assert response["today_practice_guidance_provider_boundary_e2e_summary"]["output_validation_is_valid"] is True
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_today_practice_guidance_provider_boundary_e2e" for item in traces)


def test_context_builder_and_skeleton_reference_provider_boundary_without_engine_dependency() -> None:
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    data = packet.to_dict()
    assert data["routing_hints"]["today_practice_guidance_provider_boundary_e2e_version"] == "v2_7_7"
    assert data["capabilities"]["supports_today_practice_guidance_provider_boundary_e2e"] is True

    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["today_practice_guidance_provider_boundary_e2e"]["version"] == "v2_7_7"
    assert skeleton["guards"]["provider_boundary_e2e_enabled"] is True
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_V2_7_7.md"
    assert "from jammate_engine" not in tool_invocation
    assert docs_path.exists()
