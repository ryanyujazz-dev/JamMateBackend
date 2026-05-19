from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION,
    build_context_and_guidance_skeleton_cleanup_payload,
    build_context_and_guidance_skeleton_cleanup_summary,
    context_and_guidance_skeleton_cleanup_contract,
)
from jammate_api.app import app


def test_context_guidance_cleanup_contract_registers_ordered_v2_7_chain() -> None:
    contract = context_and_guidance_skeleton_cleanup_contract()
    assert contract["version"] == CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION == "v2_8_0"
    assert contract["route"] == "GET /agent/context/guidance-skeleton-cleanup"
    assert contract["terminal_command"] == "/context-guidance-skeleton"
    stage_ids = [stage["stage_id"] for stage in contract["stage_registry"]]
    assert stage_ids == [
        "context_engineering_skeleton",
        "today_practice_guidance_prompt_contract",
        "user_capability_map_and_intent_taxonomy",
        "today_practice_guidance_output_validation",
        "today_practice_guidance_provider_boundary_e2e",
        "today_practice_guidance_action_card",
        "today_practice_guidance_terminal_chat_e2e",
    ]
    assert all(stage["side_effects_created"] is False for stage in contract["stage_registry"])
    assert "No Routine end recommendation card" in contract["non_goals"]
    assert contract["summary"]["routine_start_enabled"] is False
    assert contract["summary"]["accompaniment_generate_call_enabled"] is False


def test_context_guidance_cleanup_payload_and_summary_are_side_effect_free() -> None:
    payload_obj = build_context_and_guidance_skeleton_cleanup_payload(
        {"focus": "today_practice_guidance_chain"},
        trace_id="trace_cleanup",
    )
    payload = payload_obj.to_dict()
    assert payload["cleanup_version"] == "v2_8_0"
    assert payload["frontend_flow_assumption"] is False
    assert payload["client_decides_presentation"] is True
    assert payload["routine_end_recommendation_card_created"] is False
    assert payload["normalized_guard_flags"]["post_session_recommendation_card_created"] is False
    assert payload["normalized_guard_flags"]["routine_start_enabled"] is False
    assert payload["canonical_routes"]["today_practice_guidance_action_card"].endswith("/action-card/preview")
    assert "/today-practice-guidance-chat-e2e" in payload["terminal_commands"]

    summary = build_context_and_guidance_skeleton_cleanup_summary(payload=payload_obj)
    assert summary["stage_count"] == 7
    assert summary["all_stages_side_effect_free"] is True
    assert summary["client_decides_presentation"] is True
    assert summary["midi_asset_created"] is False
    assert summary["playback_started"] is False


def test_context_guidance_cleanup_is_exposed_in_runtime_manifests() -> None:
    context_manifest = context_profile_manifest()
    assert context_manifest["context_and_guidance_skeleton_cleanup_spec_route"] == "GET /agent/context/guidance-skeleton-cleanup"

    runtime_contract = llm_context_runtime_contract()
    assert runtime_contract["routes"]["context_and_guidance_skeleton_cleanup"] == "GET /agent/context/guidance-skeleton-cleanup"
    assert runtime_contract["context_and_guidance_skeleton_cleanup_boundary"]["version"] == "v2_8_0"
    assert any("v2_8_0" in item for item in runtime_contract["non_goals"])


def test_api_context_guidance_cleanup_route_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/agent/context/guidance-skeleton-cleanup").json()
    assert response["ok"] is True
    assert response["context_and_guidance_skeleton_cleanup_version"] == "v2_8_0"
    assert response["context_and_guidance_skeleton_cleanup_summary"]["stage_count"] == 7
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_context_guidance_cleanup_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_guidance_skeleton_cleanup()
    assert response["ok"] is True
    assert response["context_and_guidance_skeleton_cleanup_version"] == "v2_8_0"
    assert response["context_and_guidance_skeleton_cleanup_summary"]["all_stages_side_effect_free"] is True
    assert response["routine_start_enabled"] is False

    exit_code = run_interactive_chat(["--once", "/context-guidance-skeleton"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextGuidanceSkeletonCleanup>" in out
    assert "all_stages_side_effect_free: True" in out
    assert "routine_start_enabled: False" in out


def test_context_guidance_cleanup_does_not_import_engine_or_use_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_V2_8_0.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert docs_path.exists()
