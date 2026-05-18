from __future__ import annotations

import json

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
    build_practice_context_assembly_policy_payload,
    build_practice_context_assembly_policy_summary,
    build_user_practice_profile_context_intake_payload,
    build_user_practice_profile_context_intake_summary,
    user_practice_profile_context_intake_contract,
)
from jammate_api.app import app


def _profile_payload() -> dict:
    return {
        "userId": "user_001",
        "currentGoal": "提高 jazz comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping", "ballad voicing"],
        "skillFocus": ["voice leading"],
        "commonTunes": ["Autumn Leaves", "Blue Bossa"],
        "comfortableTempoRanges": {
            "medium_swing": [130, 90],
            "bossa_nova": {"min": 100, "max": 145},
            "bad_style": ["fast", 120],
        },
        "preferredSessionMinutes": [20, "30", -5],
        "avoid": ["too_fast_tempo", "too_many_new_concepts_in_one_session"],
        "practiceModePreference": "follow_plan_with_flexible_adjustment",
        "savedRoutinePreferences": {
            "defaultLoopCount": 3,
            "localMidiPath": "/tmp/should_not_leak.mid",
            "nested": {"apiKey": "SHOULD_NOT_LEAK"},
        },
        "updatedAt": "2026-05-18T00:00:00Z",
        "apiKey": "SHOULD_NOT_LEAK",
        "token": "SHOULD_NOT_LEAK",
        "midiBase64": "SHOULD_NOT_LEAK",
        "preciseLocation": "SHOULD_NOT_LEAK",
        "hiddenChainOfThought": "SHOULD_NOT_LEAK",
        "unknownField": "discard me",
    }


def _active_plan() -> dict:
    return {
        "planId": "plan_profile_aware",
        "title": "Profile Aware Plan",
        "planBlocks": [
            {"blockId": "swing_comping", "title": "Swing Comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 20, "completed": False},
        ],
    }


def _history_records() -> list[dict]:
    return [
        {"sessionId": "session_1", "style": "bossa_nova", "tuneTitle": "Blue Bossa", "actualSeconds": 900, "completed": True},
    ]


def test_user_practice_profile_contract_is_context_intake_only() -> None:
    spec = user_practice_profile_context_intake_contract()
    assert spec["version"] == USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION == "v2_8_1"
    assert spec["spec_route"] == "GET /agent/context/user-practice-profile/spec"
    assert spec["intake_route"] == "POST /agent/context/user-practice-profile/intake"
    assert spec["terminal_command"] == "/user-practice-profile-context"
    assert spec["execution_status"]["user_practice_profile_context_payload_enabled"] is True
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert "UserPracticeProfile is context" in spec["rules"][0]


def test_user_practice_profile_payload_normalizes_camel_and_snake_case_safely() -> None:
    payload_obj = build_user_practice_profile_context_intake_payload({"inputProfile": _profile_payload()}, trace_id="trace_profile")
    payload = payload_obj.to_dict()
    normalized = payload["normalized_profile_context"]
    assert payload["payload_contract_version"] == "v2_8_1"
    assert normalized["profile_status"] == "available"
    assert normalized["current_goal"] == "提高 jazz comping 稳定性"
    assert normalized["preferred_styles"] == ["medium_swing", "bossa_nova"]
    assert normalized["focus_areas"] == ["ii-V-I", "comping", "ballad voicing"]
    assert normalized["comfortable_tempo_ranges"]["medium_swing"] == {"min": 90, "max": 130}
    assert normalized["comfortable_tempo_ranges"]["bossa_nova"] == {"min": 100, "max": 145}
    assert "bad_style" not in normalized["comfortable_tempo_ranges"]
    assert normalized["preferred_session_minutes"] == [20, 30]
    assert payload["context_packet_section"]["section_name"] == "user_practice_profile_context"
    assert payload["context_packet_section"]["summary_for_llm"]
    assert payload["storage_boundary"]["writes_to_backend"] is False
    assert payload["storage_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/should_not_leak.mid" not in serialized
    assert "apiKey" in payload["validation"]["discarded_fields"]["sensitive_or_client_only_fields"]
    assert "unknownField" in payload["validation"]["discarded_fields"]["disallowed_or_unrecognized_fields"]
    assert "comfortable_tempo_range_medium_swing_min_max_swapped" in payload["validation"]["warnings"]


def test_user_practice_profile_summary_and_context_assembly_include_profile() -> None:
    profile_payload = build_user_practice_profile_context_intake_payload({"inputProfile": _profile_payload()})
    summary = build_user_practice_profile_context_intake_summary(payload=profile_payload)
    assert summary["profile_status"] == "available"
    assert summary["comfortable_tempo_style_count"] == 2
    assert "Medium" not in summary["summary_for_llm"] or isinstance(summary["summary_for_llm"], str)

    assembly_obj = build_practice_context_assembly_policy_payload(
        {
            "activePracticePlan": _active_plan(),
            "routineHistoryRecords": _history_records(),
            "userPracticeProfile": _profile_payload(),
            "availableMinutes": 20,
            "userInput": "今天该练什么？",
        }
    )
    assembly = assembly_obj.to_dict()
    assert assembly["validation"]["has_user_practice_profile_context"] is True
    assert assembly["assembled_context"]["user_practice_profile_context"]["section_name"] == "user_practice_profile_context"
    assert assembly["assembled_context"]["profile_summary"]
    assert assembly["assembled_context"]["llm_decision_inputs"]["user_practice_profile_input_available"] is True
    assert assembly["llm_called"] is False
    assert assembly["recommendation_created"] is False
    assert assembly["midi_asset_created"] is False

    assembly_summary = build_practice_context_assembly_policy_summary(payload=assembly_obj)
    assert assembly_summary["has_user_practice_profile_context"] is True
    assert assembly_summary["llm_called"] is False


def test_context_builder_injects_user_practice_profile_context_into_learner_context() -> None:
    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        active_practice_plan=_active_plan(),
        routine_history_records=_history_records(),
        user_practice_profile=_profile_payload(),
        available_minutes=20,
        client_context={"entry_point": "test"},
    )
    data = packet.to_dict()
    learner = data["learner_context"]
    assert "user_practice_profile_context" in learner
    assert learner["user_practice_profile_context"]["section_name"] == "user_practice_profile_context"
    assert learner["assembled_practice_context"]["user_practice_profile_context"]["section_name"] == "user_practice_profile_context"
    assert learner["assembled_practice_context"]["profile_summary"]
    assert data["routing_hints"]["user_practice_profile_context_present"] is True
    assert data["routing_hints"]["user_practice_profile_context_intake_version"] == "v2_8_1"
    assert "user_practice_profile_context" in data["selected_context_layers"]
    assert data["runtime_policy"]["tool_execution_enabled"] is False


def test_api_user_practice_profile_context_routes_are_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/user-practice-profile/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_1"

    response = client.post("/agent/context/user-practice-profile/intake", json={"inputProfile": _profile_payload()}).json()
    assert response["ok"] is True
    assert response["user_practice_profile_context_intake_version"] == "v2_8_1"
    assert response["user_practice_profile_context_payload"]["context_packet_section"]["section_name"] == "user_practice_profile_context"
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["storage_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_user_practice_profile_context_command_and_manifests(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.user_practice_profile_context_intake({"inputProfile": _profile_payload()})
    assert response["ok"] is True
    assert response["user_practice_profile_context_intake_summary"]["profile_status"] == "available"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        '/user-practice-profile-context {"currentGoal":"提高 comping 稳定性","preferredStyles":["medium_swing"],"comfortableTempoRanges":{"medium_swing":[90,120]}}',
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "UserPracticeProfileContext>" in out
    assert "profile_status: available" in out
    assert "storage_written: false" in out

    context_manifest = context_profile_manifest()
    assert context_manifest["user_practice_profile_context_intake_spec_route"] == "GET /agent/context/user-practice-profile/spec"
    runtime_contract = llm_context_runtime_contract()
    assert runtime_contract["routes"]["user_practice_profile_context_intake"] == "POST /agent/context/user-practice-profile/intake"
    assert runtime_contract["user_practice_profile_context_intake_boundary"]["version"] == "v2_8_1"
