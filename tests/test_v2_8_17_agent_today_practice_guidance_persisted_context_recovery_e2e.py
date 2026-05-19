from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
    build_context_persistence_profile_plan_history_snapshot_context_intake_payload,
    build_today_practice_guidance_persisted_context_recovery_e2e_payload,
    build_today_practice_guidance_persisted_context_recovery_e2e_summary,
    today_practice_guidance_persisted_context_recovery_e2e_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_persisted_001",
        "currentGoal": "提高 jazz comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 145]},
        "avoid": ["too_fast_tempo", "too_many_new_concepts_in_one_session"],
        "practiceModePreference": "follow_plan_with_flexible_adjustment",
    }


def _plan() -> dict:
    return {
        "planId": "plan_persisted_001",
        "title": "Persisted Medium Swing Comping Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_002", "title": "Blue Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "session_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True},
    ]


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
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
        "providerResult": _provider_result(),
    }


def test_persisted_context_recovery_contract_is_display_only() -> None:
    spec = today_practice_guidance_persisted_context_recovery_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION == "v2_8_17"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/persisted-context-recovery/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview"
    assert spec["terminal_command"] == "/today-practice-guidance-persisted-context-recovery"
    assert spec["execution_status"]["persisted_context_recovery_enabled"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_recovery_e2e_uses_snapshot_intake_then_profile_aware_guidance_without_execution() -> None:
    snapshot = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(_args(), trace_id="trace_persisted_recovery_snapshot").to_dict()
    payload_obj = build_today_practice_guidance_persisted_context_recovery_e2e_payload(
        {"snapshotContextIntakePayload": snapshot, "providerResult": _provider_result(), "availableMinutes": 25},
        trace_id="trace_persisted_recovery",
    )
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_persisted_context_recovery_e2e_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_17"
    assert payload["validation"]["profile_context_recovered"] is True
    assert payload["validation"]["active_plan_context_recovered"] is True
    assert payload["validation"]["routine_history_context_recovered"] is True
    assert payload["validation"]["guidance_action_card_is_valid"] is True
    assert payload["guidance_payload"]["action_card_payload"]["validation"]["is_valid"] is True
    assert payload["guidance_payload"]["action_card_payload"]["normalized_guidance_output"]["profile_considerations"]
    assert summary["profile_context_recovered"] is True
    assert summary["routine_candidate_count"] == 1
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["post_session_recommendation_card_created"] is False


def test_recovery_e2e_can_build_snapshot_context_from_arguments() -> None:
    payload = build_today_practice_guidance_persisted_context_recovery_e2e_payload(_args(), trace_id="trace_args_recovery").to_dict()
    assert payload["recovery_bridge"]["snapshot_source"] == "snapshot_context_intake_builder"
    assert payload["recovered_context_summary"]["preferred_styles"] == ["medium_swing", "bossa_nova"]
    assert payload["validation"]["persisted_context_recovered"] is True
    assert payload["guidance_summary"]["profile_context_available"] is True
    assert "SHOULD_NOT_LEAK" not in json.dumps(payload, ensure_ascii=False)


def test_context_and_runtime_manifests_advertise_recovery_e2e() -> None:
    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_persisted_context_recovery_e2e_spec_route"] == "GET /agent/context/today-practice-guidance/persisted-context-recovery/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_persisted_context_recovery_e2e_preview"] == "POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview"
    assert runtime["today_practice_guidance_persisted_context_recovery_e2e"]["version"] == "v2_8_17"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_persisted_context_recovery_e2e"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_persisted_context_recovery_e2e_version"] == "v2_8_17"


def test_api_persisted_context_recovery_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/persisted-context-recovery/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_17"

    response = client.post("/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview", json=_args()).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_persisted_context_recovery_e2e_version"] == "v2_8_17"
    assert response["today_practice_guidance_persisted_context_recovery_e2e_summary"]["profile_context_recovered"] is True
    assert response["today_practice_guidance_persisted_context_recovery_e2e_summary"]["routine_candidate_count"] == 1
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_persisted_context_recovery_command(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.today_practice_guidance_persisted_context_recovery(_args())
    assert response["ok"] is True
    assert response["today_practice_guidance_persisted_context_recovery_e2e_summary"]["profile_context_recovered"] is True
    assert response["routine_start_enabled"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/today-practice-guidance-persisted-context-recovery " + json.dumps(_args(), ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "TodayPracticeGuidancePersistedContextRecoveryE2E>" in out
    assert "profile_context_recovered: True" in out
    assert "routine_start_enabled: false" in out


def test_persisted_context_recovery_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_V2_8_17.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
