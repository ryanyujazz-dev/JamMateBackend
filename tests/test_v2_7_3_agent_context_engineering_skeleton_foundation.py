from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
    CONTEXT_ENGINEERING_SKELETON_VERSION,
    PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
    TODAY_PRACTICE_CONTEXT_E2E_VERSION,
    active_practice_plan_context_intake_contract,
    build_active_practice_plan_context_intake_payload,
    build_active_practice_plan_context_intake_summary,
    build_practice_context_assembly_policy_payload,
    build_practice_context_assembly_policy_summary,
    build_today_practice_context_e2e_payload,
    build_today_practice_context_e2e_summary,
    context_engineering_skeleton_contract,
    practice_context_assembly_policy_contract,
    today_practice_context_e2e_contract,
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
            {
                "blockId": "day3_misty",
                "title": "Misty Ballad Voicing",
                "goal": "Ballad voicing continuity",
                "durationMinutes": 20,
                "tuneTitle": "Misty",
                "style": "jazz_ballad",
                "tempo": 72,
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


def test_active_practice_plan_context_contract_is_context_only() -> None:
    spec = active_practice_plan_context_intake_contract()
    assert spec["version"] == ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION == "v2_7_3"
    assert spec["spec_route"] == "GET /agent/context/active-practice-plan/spec"
    assert spec["intake_route"] == "POST /agent/context/active-practice-plan/intake"
    assert spec["execution_status"]["active_practice_plan_context_payload_enabled"] is True
    assert spec["execution_status"]["recommendation_card_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_creates_recommendation"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_active_practice_plan_payload_normalizes_plan_blocks() -> None:
    payload = build_active_practice_plan_context_intake_payload({"activePracticePlan": _active_plan()}, trace_id="trace_plan").to_dict()
    assert payload["payload_contract_version"] == "v2_7_3"
    assert payload["active_practice_plan"]["plan_id"] == "plan_four_week_comping"
    assert len(payload["active_plan_context_items"]) == 3
    assert payload["aggregate_summary"]["plan_block_count"] == 3
    assert payload["aggregate_summary"]["pending_block_count"] == 2
    assert payload["aggregate_summary"]["completed_block_count"] == 1
    assert payload["aggregate_summary"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert payload["context_packet_section"]["section_name"] == "active_practice_plan_context"
    assert payload["recommendation_created"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    summary = build_active_practice_plan_context_intake_summary(payload=build_active_practice_plan_context_intake_payload({"activePracticePlan": _active_plan()}))
    assert summary["next_candidate_block_id"] == "day2_swing"
    assert summary["routine_start_enabled"] is False


def test_practice_context_assembly_combines_active_plan_history_and_availability_without_recommending() -> None:
    payload = build_practice_context_assembly_policy_payload(
        {
            "activePracticePlan": _active_plan(),
            "routineHistoryRecords": _history_records(),
            "availableMinutes": 15,
            "userInput": "今天该练什么？",
        },
        trace_id="trace_assembly",
    ).to_dict()
    assembled = payload["assembled_context"]
    progress = assembled["derived_progress"]
    assert payload["payload_contract_version"] == PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION == "v2_7_3"
    assert payload["validation"]["has_active_practice_plan_context"] is True
    assert payload["validation"]["has_routine_history_context"] is True
    assert "day1_bossa" in progress["completed_plan_block_ids_from_history"]
    assert progress["next_candidate_block"]["block_id"] == "day2_swing"
    assert assembled["today_constraints"]["available_minutes"] == 15
    assert assembled["llm_decision_inputs"]["should_continue_original_plan_input_available"] is True
    assert payload["assembly_policy"]["frontend_flow_assumption"] is False
    assert payload["llm_called"] is False
    assert payload["recommendation_created"] is False
    assert payload["midi_asset_created"] is False
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)
    assert "/tmp/blue_bossa.mid" not in json.dumps(payload, ensure_ascii=False)

    summary = build_practice_context_assembly_policy_summary(payload=build_practice_context_assembly_policy_payload({"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records()}))
    assert summary["next_candidate_block_id"] == "day2_swing"
    assert summary["llm_called"] is False
    assert summary["recommendation_created"] is False


def test_today_practice_context_e2e_is_context_preview_not_answer() -> None:
    spec = today_practice_context_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_CONTEXT_E2E_VERSION == "v2_7_3"
    assert spec["execution_status"]["today_practice_context_preview_enabled"] is True
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["recommendation_created"] is False

    payload_obj = build_today_practice_context_e2e_payload({"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15})
    payload = payload_obj.to_dict()
    assert payload["assembled_context"]["today_constraints"]["user_input"] == "今天该练什么？"
    assert payload["assembled_context"]["derived_progress"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert payload["llm_called"] is False
    assert payload["recommendation_created"] is False
    summary = build_today_practice_context_e2e_summary(payload=payload_obj)
    assert summary["ready_for_future_llm_turn"] is True
    assert summary["recommendation_created"] is False


def test_context_builder_includes_active_plan_history_and_assembled_context() -> None:
    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        active_practice_plan=_active_plan(),
        routine_history_records=_history_records(),
        available_minutes=15,
        client_context={"entry_point": "test"},
    )
    data = packet.to_dict()
    learner = data["learner_context"]
    assert "active_practice_plan_context" in learner
    assert "routine_history_context" in learner
    assert "assembled_practice_context" in learner
    assert data["routing_hints"]["active_practice_plan_context_present"] is True
    assert data["routing_hints"]["routine_history_context_present"] is True
    assert data["routing_hints"]["assembled_practice_context_present"] is True
    assert learner["assembled_practice_context"]["derived_progress"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert data["runtime_policy"]["tool_execution_enabled"] is False


def test_api_context_engineering_routes_are_context_only() -> None:
    client = TestClient(app)
    skeleton = client.get("/agent/context/engineering-skeleton").json()
    assert skeleton["ok"] is True
    assert skeleton["context_engineering_skeleton"]["version"] == CONTEXT_ENGINEERING_SKELETON_VERSION

    active = client.post("/agent/context/active-practice-plan/intake", json={"activePracticePlan": _active_plan()}).json()
    assert active["ok"] is True
    assert active["active_practice_plan_context_payload"]["aggregate_summary"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert active["recommendation_created"] is False

    assembly = client.post(
        "/agent/context/practice-assembly/build",
        json={"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15},
    ).json()
    assert assembly["ok"] is True
    assert assembly["practice_context_assembly_payload"]["assembled_context"]["derived_progress"]["next_candidate_block"]["block_id"] == "day2_swing"
    assert assembly["llm_called"] is False
    assert assembly["recommendation_created"] is False
    assert assembly["engine_adapter_called"] is False
    assert assembly["midi_asset_created"] is False

    today = client.post(
        "/agent/context/today-practice/preview",
        json={"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15},
    ).json()
    assert today["ok"] is True
    assert today["today_practice_context_summary"]["ready_for_future_llm_turn"] is True
    assert today["llm_called"] is False
    assert today["recommendation_created"] is False


def test_terminal_context_engineering_commands_trace_payloads(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    active = session.active_practice_plan_context_intake({"activePracticePlan": _active_plan()})
    assembly = session.practice_context_assembly({"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15})
    today = session.today_practice_context({"activePracticePlan": _active_plan(), "routineHistoryRecords": _history_records(), "availableMinutes": 15})
    skeleton = session.context_engineering_skeleton()

    assert active["active_practice_plan_context_intake_summary"]["next_candidate_block_id"] == "day2_swing"
    assert assembly["practice_context_assembly_summary"]["next_candidate_block_id"] == "day2_swing"
    assert today["today_practice_context_summary"]["ready_for_future_llm_turn"] is True
    assert skeleton["context_engineering_skeleton"]["version"] == "v2_7_3"

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    task_types = {item["task_type"] for item in traces}
    assert "terminal_active_practice_plan_context_intake" in task_types
    assert "terminal_practice_context_assembly" in task_types
    assert "terminal_today_practice_context" in task_types


def test_context_engineering_has_no_engine_or_generation_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_CONTEXT_ENGINEERING_SKELETON_FOUNDATION_V2_7_3.md"
    assert "from jammate_engine" not in tool_invocation
    assert context_engineering_skeleton_contract()["guards"]["engine_adapter_called"] is False
    assert docs_path.exists()
