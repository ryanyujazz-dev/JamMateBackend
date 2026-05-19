from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
    build_today_practice_guidance_prompt_contract_payload,
    build_today_practice_guidance_prompt_contract_summary,
    context_engineering_skeleton_contract,
    today_practice_guidance_prompt_contract,
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


def test_today_practice_guidance_prompt_contract_is_prompt_only() -> None:
    spec = today_practice_guidance_prompt_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION == "v2_7_4"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/prompt-preview"
    assert spec["execution_status"]["prompt_preview_enabled"] is True
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["guidance_response_created"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_calls_llm"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_guidance_prompt_payload_builds_messages_schema_and_policy_without_llm_call() -> None:
    payload_obj = build_today_practice_guidance_prompt_contract_payload(
        {
            "activePracticePlan": _active_plan(),
            "routineHistoryRecords": _history_records(),
            "availableMinutes": 15,
            "userInput": "今天该练什么？",
        },
        trace_id="trace_prompt",
    )
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_4"
    assert payload["validation"]["ready_for_future_llm_provider_call"] is True
    assert payload["output_schema"]["schema_name"] == "TodayPracticeGuidanceOutput"
    assert "guidance_mode" in payload["output_schema"]["required_fields"]
    assert len(payload["prompt_messages"]) == 4
    assert payload["prompt_messages"][0]["role"] == "system"
    assert payload["prompt_messages"][-1]["role"] == "context"
    assert payload["prompt_messages"][-1]["content_json"]["derived_progress"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert payload["prompt_policy"]["client_decides_presentation"] is True
    assert payload["prompt_policy"]["routine_start_requires_user_confirmation"] is True
    assert payload["llm_called"] is False
    assert payload["guidance_response_created"] is False
    assert payload["recommendation_created"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/blue_bossa.mid" not in serialized

    summary = build_today_practice_guidance_prompt_contract_summary(payload=payload_obj)
    assert summary["next_candidate_block_id"] == "day2_swing"
    assert summary["output_schema_name"] == "TodayPracticeGuidanceOutput"
    assert summary["llm_called"] is False
    assert summary["guidance_response_created"] is False


def test_context_builder_advertises_today_practice_guidance_output_contract() -> None:
    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        active_practice_plan=_active_plan(),
        routine_history_records=_history_records(),
        available_minutes=15,
        client_context={"entry_point": "test"},
    )
    data = packet.to_dict()
    assert data["output_contract"]["schema"] == "TodayPracticeGuidanceOutput"
    assert data["routing_hints"]["today_practice_guidance_prompt_contract_version"] == "v2_7_4"
    assert data["runtime_policy"]["llm_required"] is True
    assert data["runtime_policy"]["tool_execution_enabled"] is False


def test_api_today_practice_guidance_prompt_routes_are_preview_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_4"

    response = client.post(
        "/agent/context/today-practice-guidance/prompt-preview",
        json={"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15},
    ).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_prompt_contract_version"] == "v2_7_4"
    assert response["today_practice_guidance_prompt_summary"]["next_candidate_block_id"] == "day2_swing"
    assert response["llm_called"] is False
    assert response["guidance_response_created"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_today_practice_guidance_prompt_command_traces_preview(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.today_practice_guidance_prompt(
        {"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15}
    )
    assert response["ok"] is True
    assert response["today_practice_guidance_prompt_summary"]["next_candidate_block_id"] == "day2_swing"
    assert response["llm_called"] is False
    assert response["guidance_response_created"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_today_practice_guidance_prompt" for item in traces)


def test_context_engineering_skeleton_includes_prompt_contract_and_no_engine_dependency() -> None:
    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["today_practice_guidance_prompt_contract"]["version"] == "v2_7_4"
    assert skeleton["guards"]["llm_called"] is False
    assert skeleton["guards"]["guidance_response_created"] is False
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_V2_7_4.md"
    assert "from jammate_engine" not in tool_invocation
    assert docs_path.exists()
