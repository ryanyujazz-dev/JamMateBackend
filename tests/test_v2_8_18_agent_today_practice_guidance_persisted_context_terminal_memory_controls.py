from __future__ import annotations

import json
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
    today_practice_guidance_persisted_context_terminal_memory_controls_contract,
)


def _profile() -> dict:
    return {
        "userId": "user_memory_001",
        "currentGoal": "提高 jazz comping 稳定性",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping"],
        "comfortableTempoRanges": {"medium_swing": [90, 120], "bossa_nova": [100, 145]},
        "avoid": ["too_fast_tempo", "too_many_new_concepts_in_one_session"],
        "practiceModePreference": "follow_plan_with_flexible_adjustment",
    }


def _plan() -> dict:
    return {
        "planId": "plan_memory_001",
        "title": "Persisted Medium Swing Comping Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
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
            "summary": "根据已加载的终端临时上下文，今天继续练 Medium Swing ii-V-I comping。",
            "recommended_focus": "ii-V-I comping 稳定性",
            "recommended_blocks": [
                {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 guide-tone voice leading"},
            ],
            "routine_candidates": [
                {"routineName": "Memory context comping routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"},
            ],
            "profile_considerations": "匹配已加载 profile 的 medium_swing 偏好、ii-V-I focus 与 90-120 bpm 舒适速度。",
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }


def _args() -> dict:
    return {
        "availableMinutes": 25,
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
        "providerResult": _provider_result(),
    }


def test_terminal_memory_controls_contract_is_terminal_only_and_side_effect_free() -> None:
    spec = today_practice_guidance_persisted_context_terminal_memory_controls_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION == "v2_8_18"
    assert spec["terminal_commands"]["load"] == "/persisted-context-load [json_payload]"
    assert spec["execution_status"]["terminal_memory_controls_enabled"] is True
    assert spec["execution_status"]["session_memory_only"] is True
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["payload_calls_llm"] is False


def test_terminal_memory_load_show_clear_cycle() -> None:
    session = TerminalChatSession()
    assert session.persisted_context_show()["memory_loaded"] is False

    loaded = session.persisted_context_load(_args())
    assert loaded["ok"] is True
    assert loaded["memory_loaded"] is True
    assert loaded["summary"]["profile_context_present"] is True
    assert loaded["summary"]["active_plan_context_present"] is True
    assert loaded["summary"]["routine_history_context_present"] is True
    assert loaded["storage_written"] is False
    assert loaded["llm_called"] is False

    shown = session.persisted_context_show()
    assert shown["memory_loaded"] is True
    assert shown["will_inject_into_next_today_practice_guidance_turn"] is True

    cleared = session.persisted_context_clear()
    assert cleared["memory_was_loaded"] is True
    assert cleared["memory_loaded"] is False
    assert session.persisted_context_show()["memory_loaded"] is False


def test_loaded_terminal_memory_feeds_ordinary_today_guidance_turn_without_execution() -> None:
    session = TerminalChatSession()
    session.persisted_context_load(_args())
    response = session.respond("今天该练什么")
    assert response["ok"] is True
    assert response["persisted_context_terminal_memory_used"] is True
    assert response["payload_kind"] == "persisted_context_recovery_e2e"
    payload = response["today_practice_guidance_persisted_context_recovery_e2e_payload"]
    assert payload["validation"]["profile_context_recovered"] is True
    assert payload["validation"]["active_plan_context_recovered"] is True
    assert payload["validation"]["routine_history_context_recovered"] is True
    assert response["today_practice_guidance_action_card_summary"]["routine_candidate_count"] == 1
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_explicit_today_guidance_arguments_do_not_get_overridden_by_memory() -> None:
    session = TerminalChatSession()
    session.persisted_context_load(_args())
    response = session.respond_today_practice_guidance(
        "今天该练什么",
        {"userPracticeProfile": {"currentGoal": "explicit context should win"}, "providerResult": _provider_result()},
    )
    assert response["persisted_context_terminal_memory_used"] is False
    assert response["payload_kind"] == "terminal_chat_e2e"


def test_memory_controls_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert "/persisted-context-load" in manifest["today_practice_guidance_persisted_context_terminal_memory_controls_terminal_commands"]
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_persisted_context_terminal_memory_controls"] == "terminal-only: /persisted-context-load | /persisted-context-show | /persisted-context-clear"
    assert runtime["today_practice_guidance_persisted_context_terminal_memory_controls"]["version"] == "v2_8_18"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_persisted_context_terminal_memory_controls"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_persisted_context_terminal_memory_controls_version"] == "v2_8_18"


def test_terminal_memory_commands_are_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    args = json.dumps(_args(), ensure_ascii=False)
    exit_code = run_interactive_chat(["--once", "/persisted-context-load " + args])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PersistedContextTerminalMemory>" in out
    assert "memory_loaded: true" in out
    assert "routine_start_enabled: false" in out


def test_terminal_memory_controls_do_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_V2_8_18.md"
    assert "from jammate_engine" not in terminal_chat
    assert "from jammate_engine" not in tool_invocation
    assert doc_path.exists()
