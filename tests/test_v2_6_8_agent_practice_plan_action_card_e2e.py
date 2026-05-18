from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_harmonyos_agent_action_card,
    build_practice_plan_action_card_e2e_summary,
    build_routine_practice_plan_action_payload,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    execute_tool_dry_run,
    practice_plan_action_card_e2e_contract,
    preview_tool_invocation,
)
from jammate_agent.core.trace import trace_api_contract
from jammate_api.app import app


def _controlled_practice_plan_chain():
    proposal = ToolInvocationProposal(
        tool_name="agent_practice_plan",
        arguments={"userInput": "练 30 分钟 Blue Bossa comping", "availableMinutes": 30, "instrument": "piano"},
        task_type="practice_plan_generation",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["agent_practice_plan"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_v268")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)
    controlled = execute_controlled_workflow(
        dispatch,
        workflow_runner=lambda tool_name, args: {
            "ok": True,
            "intent_type": "practice_plan_generation",
            "plan": {
                "plan_id": "plan_v268",
                "title": "Blue Bossa Comping 30",
                "duration_minutes": 30,
                "main_focus": "Blue Bossa comping with controlled voicing and time feel",
                "estimated_difficulty": "medium",
                "source": "rule_based",
                "blocks": [
                    {
                        "block_id": "block_1",
                        "type": "voicing",
                        "title": "Blue Bossa voicing continuity",
                        "intent": "控制 lower foundation、voice-leading 与和声密度。",
                        "duration_minutes": 9,
                        "material": {"type": "tune", "tune": "Blue Bossa", "section": None, "key": None, "progression": None, "bars": None, "raw": {}},
                        "tempo": 110,
                        "style": "bossa_nova",
                        "accompaniment_config": None,
                        "status": "pending",
                    },
                    {
                        "block_id": "block_2",
                        "type": "comping",
                        "title": "Blue Bossa comping with rhythm section",
                        "intent": "关闭 piano 伴奏声部，跟 bass/drums 练 comping。",
                        "duration_minutes": 17,
                        "material": {"type": "tune", "tune": "Blue Bossa", "section": None, "key": None, "progression": None, "bars": None, "raw": {}},
                        "tempo": 110,
                        "style": "bossa_nova",
                        "accompaniment_config": {
                            "enabled": True,
                            "style": "bossa_nova",
                            "tempo": 110,
                            "loop_count": None,
                            "duration_minutes": None,
                            "section_loop": True,
                            "muted_roles": ["piano"],
                            "count_in": True,
                            "harmonic_expansion_enabled": False,
                            "density": "normal",
                            "practice_role": "piano_comping",
                            "output_format": "midi_base64",
                            "arrangement_intent": {},
                        },
                        "status": "pending",
                    },
                    {
                        "block_id": "block_3",
                        "type": "review",
                        "title": "Review",
                        "intent": "记录左手、密度、time feel 与卡点。",
                        "duration_minutes": 4,
                        "material": None,
                        "tempo": None,
                        "style": None,
                        "accompaniment_config": None,
                        "status": "pending",
                    },
                ],
            },
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        },
    )
    return preview, confirmation, approved, execution, dispatch, controlled


def test_practice_plan_action_card_e2e_contract_is_routine_payload_only() -> None:
    spec = practice_plan_action_card_e2e_contract()
    assert spec["version"] == PRACTICE_PLAN_ACTION_CARD_E2E_VERSION == "v2_6_8"
    assert spec["spec_route"] == "GET /agent/actions/practice-plan/spec"
    assert spec["execute_controlled_route"] == "POST /agent/actions/practice-plan/execute-controlled"
    assert spec["execution_status"]["routine_payload_enabled"] is True
    assert spec["execution_status"]["open_routine_setup_enabled"] is True
    assert spec["execution_status"]["playback_execution_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_calls_accompaniment_generate"] is False
    assert spec["guards"]["payload_creates_midi_asset"] is False


def test_core_action_card_contains_routine_practice_plan_payload() -> None:
    preview, confirmation, approved, execution, dispatch, controlled = _controlled_practice_plan_chain()
    card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=approved,
        execution_result=execution,
        workflow_dispatch_result=dispatch,
        controlled_result=controlled,
        trace_id="trace_v268",
    )
    payload = card.to_dict()["result_preview"]["routine_practice_plan_payload"]

    assert payload["payload_contract_version"] == "v2_6_8"
    assert payload["plan"]["title"] == "Blue Bossa Comping 30"
    assert payload["plan"]["duration_minutes"] == 30
    assert payload["plan"]["block_count"] == 3
    assert sum(block["duration_minutes"] for block in payload["routine_blocks"]) == 30
    assert payload["routine_config_candidate"]["routine_name"] == "Blue Bossa Comping 30"
    assert payload["routine_config_candidate"]["style"] == "bossa_nova"
    assert payload["routine_config_candidate"]["tune_title"] == "Blue Bossa"
    assert payload["routine_config_candidate"]["requires_user_start_confirmation"] is True
    assert payload["routine_config_candidate"]["accompaniment_generate_call_enabled"] is False
    assert payload["routine_config_candidate"]["playback_execution_enabled"] is False
    assert payload["client_button_semantics"]["primary"]["action"] == "open_routine_setup"
    assert payload["client_button_semantics"]["primary"]["does_start_playback"] is False
    assert "open_routine_setup" in payload["next_client_actions"]
    assert "open_routine_setup" in card.to_dict()["available_client_actions"]
    assert payload["routine_blocks"][1]["accompaniment_request_candidate"]["call_enabled_now"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False

    summary = build_practice_plan_action_card_e2e_summary(action_card=card, source="test")
    assert summary["practice_plan_action_card_e2e_version"] == "v2_6_8"
    assert summary["has_routine_practice_plan_payload"] is True
    assert summary["block_count"] == 3
    assert summary["playback_started"] is False
    assert summary["midi_asset_created"] is False


def test_payload_builder_handles_missing_plan_without_side_effects() -> None:
    _, _, _, _, _, controlled = _controlled_practice_plan_chain()
    payload = build_routine_practice_plan_action_payload(controlled, trace_id="trace_direct").to_dict()
    assert payload["trace_id"] == "trace_direct"
    assert payload["route_called"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["accompaniment_generate_call_enabled"] is False


def test_terminal_practice_plan_action_card_e2e_traces_payload(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="practice_plan_generation", trace_logger=None)
    # Re-create with trace store so the constructor path stays explicit for regression.
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(task_type="practice_plan_generation", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    session.preview_tool_call("agent_practice_plan", {"userInput": "练 30 分钟 Blue Bossa comping", "availableMinutes": 30})
    session.confirm_pending_tool()
    session.execute_confirmed_tool_dry_run()
    session.dispatch_confirmed_tool_workflow_dry_run()
    controlled = session.execute_controlled_workflow()
    assert controlled["ok"] is True

    response = session.practice_plan_action_card_e2e()
    assert response["ok"] is True
    payload = response["action_card"]["result_preview"]["routine_practice_plan_payload"]
    assert payload["payload_contract_version"] == "v2_6_8"
    assert payload["plan"]["duration_minutes"] == 30
    assert "open_routine_setup" in payload["next_client_actions"]
    assert response["midi_asset_created"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    matches = [item for item in traces if item["task_type"] == "terminal_practice_plan_action_card_e2e"]
    assert len(matches) == 1
    step_names = [step["name"] for step in matches[0]["steps"]]
    assert "terminal_practice_plan_action_card_payload_built" in step_names
    assert matches[0]["final_response_summary"]["practice_plan_action_card_e2e_summary"]["has_routine_practice_plan_payload"] is True


def test_practice_plan_action_card_api_route_returns_routine_payload() -> None:
    client = TestClient(app)
    spec = client.get("/agent/actions/practice-plan/spec").json()["spec"]
    assert spec["version"] == "v2_6_8"
    assert spec["execution_status"]["playback_execution_enabled"] is False

    response = client.post(
        "/agent/actions/practice-plan/execute-controlled",
        json={
            "taskType": "practice_plan_generation",
            "toolName": "agent_practice_plan",
            "arguments": {"userInput": "练 30 分钟 Blue Bossa comping", "availableMinutes": 30},
            "userApproved": True,
            "traceId": "trace_api_v268",
        },
    ).json()
    assert response["ok"] is True
    assert response["practice_plan_action_card_e2e_version"] == "v2_6_8"
    payload = response["action_card"]["result_preview"]["routine_practice_plan_payload"]
    assert payload["payload_contract_version"] == "v2_6_8"
    assert payload["plan"]["duration_minutes"] == 30
    assert payload["routine_config_candidate"]["requires_user_start_confirmation"] is True
    assert "open_routine_setup" in payload["next_client_actions"]
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False

    blocked = client.post(
        "/agent/actions/practice-plan/execute-controlled",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": True,
        },
    ).json()
    assert blocked["ok"] is False
    assert blocked["action_card"]["tool_name"] == "agent_playback_prepare"
    assert "routine_practice_plan_payload" not in blocked["action_card"].get("result_preview", {})
    assert blocked["midi_asset_created"] is False


def test_trace_contract_exposes_practice_plan_action_card_e2e() -> None:
    trace_spec = trace_api_contract()
    contract = trace_spec["practice_plan_action_card_e2e_trace_contract"]
    assert contract["version"] == "v2_6_8"
    assert contract["routine_payload_enabled"] is True
    assert contract["open_routine_setup_enabled"] is True
    assert contract["playback_execution_enabled"] is False
    assert contract["accompaniment_generate_call_enabled"] is False
    assert contract["engine_adapter_dispatch_enabled"] is False
    assert contract["midi_asset_creation_enabled"] is False
