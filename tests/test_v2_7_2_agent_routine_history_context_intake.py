from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
    build_routine_history_context_intake_payload,
    build_routine_history_context_intake_summary,
    routine_history_context_intake_contract,
)
from jammate_api.app import app


def _history_records() -> list[dict]:
    return [
        {
            "sessionId": "session_blue_bossa_001",
            "routineId": "routine_blue_bossa_001",
            "title": "Blue Bossa Bossa Comping",
            "tuneTitle": "Blue Bossa",
            "style": "bossa_nova",
            "tempo": 120,
            "plannedDurationMinutes": 20,
            "actualSeconds": 1180,
            "completed": True,
            "practiceGoal": "Bossa comping stability",
            "planId": "plan_week_1",
            "planBlockId": "day1_bossa",
            "finishedAt": "2026-05-18T20:30:00",
            "localMidiPath": "/tmp/blue_bossa.mid",
            "midiBase64": "SHOULD_NOT_LEAK",
            "currentPositionMs": 12345,
            "remainingSeconds": 0,
        },
        {
            "sessionId": "session_swing_002",
            "title": "ii-V-I Swing Drill",
            "style": "medium_swing",
            "tempo": 104,
            "durationMinutes": 15,
            "completed": True,
            "goal": "Guide-tone voice leading",
            "planBlockId": "day2_swing",
            "endedAt": "2026-05-17T18:00:00",
        },
        {
            "sessionId": "session_misty_003",
            "title": "Misty Ballad Voicing",
            "tune": "Misty",
            "style": "jazz_ballad",
            "tempo": 72,
            "durationMinutes": 20,
            "actualSeconds": 600,
            "completed": False,
            "practiceGoal": "Ballad voicing continuity",
            "finishedAt": "2026-05-16T21:00:00",
        },
    ]


def test_routine_history_context_contract_is_context_intake_only() -> None:
    spec = routine_history_context_intake_contract()
    assert spec["version"] == ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION == "v2_7_2"
    assert spec["spec_route"] == "GET /agent/context/routine-history/spec"
    assert spec["intake_route"] == "POST /agent/context/routine-history/intake"
    assert spec["execution_status"]["routine_history_context_payload_enabled"] is True
    assert spec["execution_status"]["post_session_recommendation_card_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_creates_post_session_recommendation_card"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_payload_normalizes_records_and_drops_client_only_playback_fields() -> None:
    payload = build_routine_history_context_intake_payload({"routineHistoryRecords": _history_records()}, trace_id="trace_history").to_dict()
    assert payload["payload_contract_version"] == "v2_7_2"
    assert len(payload["practice_history_context_items"]) == 3
    first = payload["practice_history_context_items"][0]
    assert first["history_item_id"] == "session_blue_bossa_001"
    assert first["tune_title"] == "Blue Bossa"
    assert first["style"] == "bossa_nova"
    assert first["duration_minutes"] == 19.67
    assert first["plan_block_id"] == "day1_bossa"
    assert payload["aggregate_summary"]["completed_count"] == 2
    assert payload["aggregate_summary"]["incomplete_count"] == 1
    assert payload["aggregate_summary"]["total_practice_minutes"] == 44.67
    assert "Blue Bossa" in payload["aggregate_summary"]["recent_tunes"]
    assert "bossa_nova" in payload["aggregate_summary"]["recent_styles"]
    assert payload["validation"]["contains_midi_base64"] is False
    assert payload["validation"]["contains_local_midi_path"] is False
    assert payload["validation"]["contains_playback_position"] is False
    dropped = payload["validation"]["dropped_client_only_fields"]["routine_blue_bossa_001"]
    assert "midiBase64" in dropped
    assert "localMidiPath" in dropped
    assert "currentPositionMs" in dropped
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)
    assert "/tmp/blue_bossa.mid" not in json.dumps(payload, ensure_ascii=False)
    assert payload["recommendation_card_created"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False


def test_context_builder_can_include_routine_history_context_section() -> None:
    payload = build_routine_history_context_intake_payload({"routineHistoryRecords": _history_records()}).to_dict()
    packet = ContextBuilder().build(
        "practice_plan_generation",
        "今天该练什么？",
        routine_history_context=payload,
        client_context={"entry_point": "test"},
    )
    data = packet.to_dict()
    history_context = data["learner_context"]["routine_history_context"]
    assert "routine_history_context" in data["selected_context_layers"]
    assert history_context["section_name"] == "practice_history_context"
    assert history_context["context_usage_policy"]["do_not_create_post_session_recommendation_card"] is True
    assert history_context["aggregate_summary"]["completed_count"] == 2
    assert data["routing_hints"]["routine_history_context_present"] is True


def test_terminal_routine_history_context_command_traces_payload(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.routine_history_context_intake({"routineHistoryRecords": _history_records()})
    assert response["ok"] is True
    assert response["routine_history_context_intake_version"] == "v2_7_2"
    assert response["routine_history_context_payload"]["aggregate_summary"]["context_item_count"] == 3
    assert response["recommendation_card_created"] is False
    assert response["midi_asset_created"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    matches = [item for item in traces if item["task_type"] == "terminal_routine_history_context_intake"]
    assert len(matches) == 1
    step_names = [step["name"] for step in matches[0]["steps"]]
    assert "terminal_routine_history_context_payload_built" in step_names
    assert matches[0]["final_response_summary"]["routine_history_context_intake_summary"]["recommendation_card_created"] is False


def test_api_routine_history_context_intake_route_returns_context_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/routine-history/spec").json()["spec"]
    assert spec["version"] == "v2_7_2"
    assert spec["execution_status"]["database_persistence_implemented"] is False

    response = client.post(
        "/agent/context/routine-history/intake",
        json={"routineHistoryRecords": _history_records(), "traceId": "trace_api_history"},
    ).json()
    assert response["ok"] is True
    assert response["routine_history_context_payload"]["payload_contract_version"] == "v2_7_2"
    assert response["routine_history_context_payload"]["aggregate_summary"]["completed_count"] == 2
    assert response["recommendation_card_created"] is False
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_no_engine_or_accompaniment_route_dependency_in_routine_history_context_intake() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs = (root / "docs" / "AGENT_ROUTINE_HISTORY_CONTEXT_INTAKE_V2_7_2.md").read_text(encoding="utf-8")
    assert "from jammate_engine" not in tool_invocation
    assert "POST /accompaniment/generate" in docs
    assert "不调用 `/accompaniment/generate`" in docs
