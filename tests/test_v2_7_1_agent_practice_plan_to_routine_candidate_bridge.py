from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_harmonyos_agent_action_card,
    build_practice_plan_to_routine_candidate_bridge_payload,
    build_practice_plan_to_routine_candidate_bridge_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    execute_tool_dry_run,
    practice_plan_to_routine_candidate_bridge_contract,
    preview_tool_invocation,
)
from jammate_agent.core.trace import trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _plan_payload() -> dict:
    return {
        "payload_contract_version": "v2_6_8",
        "plan": {
            "plan_id": "plan_v271",
            "title": "Flexible Blue Bossa Routine",
            "duration_minutes": 30,
            "main_focus": "Bossa comping and time feel",
            "block_count": 3,
        },
        "routine_blocks": [
            {"block_index": 0, "block_id": "warmup", "title": "Warmup", "duration_minutes": 5, "intent": "light voicings", "requires_accompaniment_asset": False},
            {
                "block_index": 1,
                "block_id": "comping_block",
                "title": "Blue Bossa comping",
                "duration_minutes": 20,
                "intent": "comp with bass and drums",
                "material": {"type": "tune", "tune": "Blue Bossa"},
                "style": "bossa_nova",
                "tempo": 118,
                "requires_accompaniment_asset": True,
                "accompaniment_request_candidate": {
                    "style": "bossa_nova",
                    "tempo": 118,
                    "muted_roles": ["piano"],
                    "output_format": "midi_base64",
                    "call_enabled_now": False,
                },
            },
            {"block_index": 2, "block_id": "review", "title": "Review", "duration_minutes": 5, "requires_accompaniment_asset": False},
        ],
    }


def _controlled_practice_plan_card():
    proposal = ToolInvocationProposal(
        tool_name="agent_practice_plan",
        arguments={"userInput": "练 30 分钟 Blue Bossa comping", "availableMinutes": 30},
        task_type="practice_plan_generation",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["agent_practice_plan"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_v271")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)
    controlled = execute_controlled_workflow(
        dispatch,
        workflow_runner=lambda tool_name, args: {
            "ok": True,
            "plan": {
                "plan_id": "plan_v271",
                "title": "Flexible Blue Bossa Routine",
                "duration_minutes": 30,
                "main_focus": "Bossa comping and time feel",
                "blocks": [
                    {"block_id": "warmup", "title": "Warmup", "duration_minutes": 5, "intent": "light voicings"},
                    {
                        "block_id": "comping_block",
                        "title": "Blue Bossa comping",
                        "duration_minutes": 20,
                        "intent": "comp with bass and drums",
                        "material": {"type": "tune", "tune": "Blue Bossa"},
                        "style": "bossa_nova",
                        "tempo": 118,
                        "accompaniment_config": {
                            "enabled": True,
                            "style": "bossa_nova",
                            "tempo": 118,
                            "muted_roles": ["piano"],
                            "count_in": True,
                            "section_loop": True,
                            "output_format": "midi_base64",
                        },
                    },
                    {"block_id": "review", "title": "Review", "duration_minutes": 5},
                ],
            },
        },
    )
    card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=approved,
        execution_result=execution,
        workflow_dispatch_result=dispatch,
        controlled_result=controlled,
        trace_id="trace_v271",
    )
    return card


def test_bridge_contract_is_ui_flow_agnostic_and_no_side_effects() -> None:
    spec = practice_plan_to_routine_candidate_bridge_contract()
    assert spec["version"] == PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION == "v2_7_1"
    assert spec["spec_route"] == "GET /agent/actions/practice-plan/routine-candidate/spec"
    assert spec["prepare_route"] == "POST /agent/actions/practice-plan/routine-candidate/prepare"
    assert spec["execution_status"]["frontend_flow_assumption"] is False
    assert spec["execution_status"]["client_decides_presentation"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["frontend_flow_hardcoded"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_payload_selects_practice_plan_block_but_does_not_require_setup_page() -> None:
    payload = build_practice_plan_to_routine_candidate_bridge_payload(
        {"routinePracticePlanPayload": _plan_payload(), "blockId": "comping_block"},
        trace_id="trace_direct_v271",
    ).to_dict()
    candidate = payload["routine_candidate"]
    flow = payload["frontend_flow_contract"]

    assert payload["payload_contract_version"] == "v2_7_1"
    assert payload["candidate_scope"] == "practice_plan_block"
    assert payload["selected_block"]["block_id"] == "comping_block"
    assert candidate["candidate_source"] == "practice_plan_block"
    assert candidate["source_block_id"] == "comping_block"
    assert candidate["style"] == "bossa_nova"
    assert candidate["tempo"] == 118
    assert candidate["duration_minutes"] == 20
    assert candidate["tune_title"] == "Blue Bossa"
    assert candidate["frontend_flow_assumption"] is False
    assert candidate["client_decides_presentation"] is True
    assert flow["backend_does_not_require_open_routine_setup"] is True
    assert flow["client_decides_presentation"] is True
    assert "present_routine_candidate" in payload["available_client_actions"]
    assert "apply_to_current_routine" in payload["available_client_actions"]
    assert "show_confirmation_sheet" in payload["available_client_actions"]
    assert "open_routine_setup" not in payload["available_client_actions"]
    assert payload["accompaniment_generate_call_enabled"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False


def test_bridge_can_read_practice_plan_action_card_result_preview() -> None:
    card = _controlled_practice_plan_card()
    payload = build_practice_plan_to_routine_candidate_bridge_payload(action_card=card, trace_id="trace_card_v271").to_dict()
    assert payload["routine_candidate"]["source_block_id"] == "comping_block"
    assert payload["routine_candidate"]["style"] == "bossa_nova"
    assert payload["frontend_flow_contract"]["frontend_flow_assumption"] is False
    assert payload["client_action_semantics"]["primary"]["action"] == "present_routine_candidate"

    summary = build_practice_plan_to_routine_candidate_bridge_summary(payload=build_practice_plan_to_routine_candidate_bridge_payload(action_card=card), source="test")
    assert summary["practice_plan_to_routine_candidate_bridge_version"] == "v2_7_1"
    assert summary["client_decides_presentation"] is True
    assert summary["routine_start_enabled"] is False


def test_terminal_practice_plan_routine_candidate_bridge_traces_payload(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(task_type="practice_plan_generation", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    session.preview_tool_call("agent_practice_plan", {"userInput": "练 30 分钟 Blue Bossa comping", "availableMinutes": 30})
    session.confirm_pending_tool()
    session.execute_confirmed_tool_dry_run()
    session.dispatch_confirmed_tool_workflow_dry_run()
    session.execute_controlled_workflow()
    session.practice_plan_action_card_e2e()
    response = session.practice_plan_routine_candidate_bridge(block_id="block_2")

    assert response["ok"] is True
    payload = response["routine_candidate_bridge_payload"]
    assert payload["payload_contract_version"] == "v2_7_1"
    assert payload["frontend_flow_contract"]["client_decides_presentation"] is True
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    matches = [item for item in traces if item["task_type"] == "terminal_practice_plan_routine_candidate_bridge"]
    assert len(matches) == 1
    step_names = [step["name"] for step in matches[0]["steps"]]
    assert "terminal_practice_plan_routine_candidate_payload_built" in step_names
    assert matches[0]["final_response_summary"]["practice_plan_to_routine_candidate_bridge_summary"]["client_decides_presentation"] is True


def test_api_practice_plan_to_routine_candidate_bridge_route_returns_candidate_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/actions/practice-plan/routine-candidate/spec").json()["spec"]
    assert spec["version"] == "v2_7_1"
    assert spec["execution_status"]["client_decides_presentation"] is True

    response = client.post(
        "/agent/actions/practice-plan/routine-candidate/prepare",
        json={
            "payload": {"routinePracticePlanPayload": _plan_payload(), "blockId": "comping_block"},
            "traceId": "trace_api_v271",
        },
    ).json()
    assert response["ok"] is True
    payload = response["routine_candidate_bridge_payload"]
    assert response["practice_plan_to_routine_candidate_bridge_version"] == "v2_7_1"
    assert payload["routine_candidate"]["source_block_id"] == "comping_block"
    assert payload["frontend_flow_contract"]["client_decides_presentation"] is True
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["routine_start_enabled"] is False


def test_trace_and_runtime_specs_expose_bridge_boundary() -> None:
    trace_spec = trace_api_contract()
    contract = trace_spec["practice_plan_to_routine_candidate_bridge_trace_contract"]
    assert contract["version"] == "v2_7_1"
    assert contract["client_decides_presentation"] is True
    assert contract["frontend_flow_assumption"] is False
    assert contract["accompaniment_generate_call_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["practice_plan_to_routine_candidate_bridge_boundary"]
    assert boundary["version"] == "v2_7_1"
    assert boundary["execution_status"]["client_decides_presentation"] is True
    assert boundary["guards"]["frontend_flow_hardcoded"] is False


def test_bridge_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
    for rel in [
        "src/jammate_agent/core/tool_invocation.py",
        "src/jammate_agent/cli/terminal_chat.py",
        "src/jammate_agent/core/trace.py",
    ]:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert "jammate_engine" not in imported
        assert "requests" not in imported
        assert "httpx" not in imported
