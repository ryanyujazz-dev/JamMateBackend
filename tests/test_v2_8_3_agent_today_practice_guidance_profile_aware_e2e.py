from __future__ import annotations

import json

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
    build_today_practice_guidance_profile_aware_e2e_payload,
    build_today_practice_guidance_profile_aware_e2e_summary,
    build_today_practice_guidance_prompt_contract_payload,
    today_practice_guidance_profile_aware_e2e_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_001",
        "currentGoal": "提高 jazz comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 145]},
        "avoid": ["too_fast_tempo", "too_many_new_concepts_in_one_session"],
        "practiceModePreference": "follow_plan_with_flexible_adjustment",
        "apiKey": "SHOULD_NOT_LEAK",
        "midiBase64": "SHOULD_NOT_LEAK",
    }


def _active_plan() -> dict:
    return {
        "planId": "plan_profile_aware",
        "title": "Profile Aware Comping Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "done_bossa", "title": "Blue Bossa", "style": "bossa_nova", "tempo": 118, "durationMinutes": 20, "completed": True},
            {"blockId": "next_swing", "title": "ii-V-I Swing Comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 20, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "s1", "style": "bossa_nova", "tuneTitle": "Blue Bossa", "actualSeconds": 1200, "completed": True, "planBlockId": "done_bossa"},
    ]


def _provider_result() -> dict:
    return {
        "content": {
            "guidance_mode": "continue_original_plan",
            "summary": "继续推进 Medium Swing ii-V-I comping，时间和速度都适合今天。",
            "recommended_focus": "ii-V-I comping 稳定性",
            "recommended_blocks": [
                {"title": "ii-V-I Swing Comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 20, "goal": "稳定 guide-tone voice leading"},
            ],
            "routine_candidates": [
                {"routineName": "Medium Swing comping routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 20, "practiceGoal": "稳定 comping"},
            ],
            "profile_considerations": "匹配用户 Medium Swing 偏好、ii-V-I focus 和 90-120 bpm 舒适速度区间。",
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }


def _args() -> dict:
    return {
        "activePracticePlan": _active_plan(),
        "routineHistoryRecords": _history(),
        "userPracticeProfile": _profile(),
        "availableMinutes": 20,
        "userInput": "今天该练什么？",
        "providerResult": _provider_result(),
    }


def test_profile_aware_contract_is_candidate_only() -> None:
    spec = today_practice_guidance_profile_aware_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION == "v2_8_3"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/profile-aware/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/profile-aware/e2e-preview"
    assert spec["terminal_command"] == "/today-practice-guidance-profile-aware"
    assert spec["profile_policy"]["profile_is_soft_context_not_rule_engine"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["writes_storage"] is False


def test_prompt_contract_includes_profile_context_as_soft_policy() -> None:
    payload = build_today_practice_guidance_prompt_contract_payload(_args()).to_dict()
    assert payload["validation"]["has_user_practice_profile_context"] is True
    assert payload["prompt_policy"]["profile_aware_policy"]["profile_context_available"] is True
    assert payload["prompt_policy"]["profile_aware_policy"]["profile_is_soft_context_not_rule_engine"] is True
    assert "user_practice_profile_context" in payload["prompt_policy"]["context_priority_order"]
    assert "profile_considerations" in payload["output_schema"]["fields"]
    assert payload["assembled_practice_context"]["user_practice_profile_context"]["section_name"] == "user_practice_profile_context"
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized


def test_profile_aware_payload_bridges_profile_to_validated_action_card_without_execution() -> None:
    payload_obj = build_today_practice_guidance_profile_aware_e2e_payload(_args(), trace_id="trace_profile_e2e")
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_profile_aware_e2e_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_3"
    assert payload["validation"]["profile_context_available"] is True
    assert payload["validation"]["profile_used_as_soft_context"] is True
    assert payload["profile_guidance_bridge"]["preferred_styles"] == ["medium_swing", "bossa_nova"]
    assert payload["profile_alignment_preview"]["preferred_style_match_count"] >= 1
    assert payload["profile_alignment_preview"]["tempo_range_match_count"] >= 1
    assert payload["action_card_payload"]["validation"]["is_valid"] is True
    assert payload["action_card_payload"]["normalized_guidance_output"]["profile_considerations"]
    assert summary["profile_context_available"] is True
    assert summary["routine_candidate_count"] == 1
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["accompaniment_generate_call_enabled"] is False
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)


def test_context_builder_and_manifests_advertise_profile_aware_guidance() -> None:
    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        active_practice_plan=_active_plan(),
        routine_history_records=_history(),
        user_practice_profile=_profile(),
        available_minutes=20,
        client_context={"entry_point": "test"},
    ).to_dict()
    assert packet["routing_hints"]["today_practice_guidance_profile_aware_e2e_version"] == "v2_8_3"
    assert packet["capabilities"]["supports_today_practice_guidance_profile_aware_e2e"] is True
    assert packet["learner_context"]["assembled_practice_context"]["user_practice_profile_context"]["section_name"] == "user_practice_profile_context"

    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_profile_aware_e2e_spec_route"] == "GET /agent/context/today-practice-guidance/profile-aware/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_profile_aware_e2e_preview"] == "POST /agent/context/today-practice-guidance/profile-aware/e2e-preview"
    assert runtime["today_practice_guidance_profile_aware_e2e_boundary"]["version"] == "v2_8_3"


def test_api_profile_aware_routes_are_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/profile-aware/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_3"

    response = client.post("/agent/context/today-practice-guidance/profile-aware/e2e-preview", json=_args()).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_profile_aware_e2e_version"] == "v2_8_3"
    assert response["today_practice_guidance_profile_aware_e2e_summary"]["profile_context_available"] is True
    assert response["today_practice_guidance_profile_aware_e2e_summary"]["routine_candidate_count"] == 1
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["accompaniment_generate_call_enabled"] is False


def test_terminal_profile_aware_command(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.today_practice_guidance_profile_aware(_args())
    assert response["ok"] is True
    assert response["today_practice_guidance_profile_aware_e2e_summary"]["profile_context_available"] is True
    assert response["routine_start_enabled"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/today-practice-guidance-profile-aware " + json.dumps(_args(), ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "TodayPracticeGuidanceProfileAwareE2E>" in out
    assert "profile_context_available: true" in out
    assert "routine_start_enabled: false" in out
