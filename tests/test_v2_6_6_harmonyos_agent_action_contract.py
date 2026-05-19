from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_harmonyos_agent_action_card,
    build_harmonyos_agent_action_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    execute_tool_dry_run,
    harmonyos_agent_action_contract,
    preview_tool_invocation,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _practice_plan_chain():
    proposal = ToolInvocationProposal(
        tool_name="agent_practice_plan",
        arguments={"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
        task_type="practice_plan_generation",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["agent_practice_plan"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_action_test")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)
    controlled = execute_controlled_workflow(
        dispatch,
        workflow_runner=lambda tool_name, args: {
            "ok": True,
            "intent_type": "practice_plan_generation",
            "plan": {"title": "Blue Bossa Practice", "duration_minutes": 30, "blocks": []},
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        },
    )
    return preview, confirmation, approved, execution, dispatch, controlled


def test_harmonyos_agent_action_contract_exposes_routine_action_card_schema() -> None:
    spec = harmonyos_agent_action_contract()
    assert spec["version"] == HARMONYOS_AGENT_ACTION_CONTRACT_VERSION == "v2_6_6"
    assert spec["spec_route"] == "GET /agent/actions/spec"
    assert spec["preview_route"] == "POST /agent/actions/preview"
    assert spec["controlled_execute_route"] == "POST /agent/actions/execute-controlled"
    assert spec["execution_status"]["action_card_enabled"] is True
    assert spec["execution_status"]["controlled_practice_plan_execution_enabled"] is True
    assert spec["execution_status"]["playback_execution_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["execution_status"]["midi_asset_creation_enabled"] is False
    assert spec["guards"]["action_card_calls_accompaniment_generate"] is False
    assert spec["guards"]["action_card_creates_midi_asset"] is False


def test_action_card_for_pending_preview_requires_user_confirmation() -> None:
    proposal = ToolInvocationProposal(
        tool_name="agent_practice_plan",
        arguments={"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
        task_type="practice_plan_generation",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["agent_practice_plan"])
    confirmation = build_confirmation_envelope(preview)

    card = build_harmonyos_agent_action_card(preview=preview, confirmation=confirmation, trace_id="trace_test").to_dict()
    assert card["action_contract_version"] == "v2_6_6"
    assert card["tool_name"] == "agent_practice_plan"
    assert card["title"] == "Agent Practice Plan"
    assert card["preview_status"] == "preview_only_blocked_by_execution_guard"
    assert card["confirmation_status"] == "pending"
    assert card["execution_status"] == "confirmation_required"
    assert card["requires_user_confirmation"] is True
    assert "confirm" in card["available_client_actions"]
    assert "reject" in card["available_client_actions"]
    assert card["trace_id"] == "trace_test"
    assert card["route_called"] is False
    assert card["engine_adapter_called"] is False
    assert card["midi_asset_created"] is False


def test_action_card_can_wrap_controlled_practice_plan_result_without_midi_asset() -> None:
    preview, confirmation, approved, execution, dispatch, controlled = _practice_plan_chain()
    card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=approved,
        execution_result=execution,
        workflow_dispatch_result=dispatch,
        controlled_result=controlled,
        trace_id="trace_controlled",
    ).to_dict()

    assert card["tool_name"] == "agent_practice_plan"
    assert card["confirmation_status"] == "approved"
    assert card["user_approved"] is True
    assert card["execution_status"] == "controlled_execution_succeeded"
    assert card["workflow_name"] == "PracticePlanner.build_plan"
    assert card["result_preview"]["plan"]["duration_minutes"] == 30
    assert card["result_preview"]["plan"]["block_count"] == 0
    assert card["route_called"] is False
    assert card["engine_adapter_called"] is False
    assert card["midi_asset_created"] is False

    summary = build_harmonyos_agent_action_summary(action_card=build_harmonyos_agent_action_card(controlled_result=controlled), source="test")
    assert summary["harmonyos_agent_action_contract_version"] == "v2_6_6"
    assert summary["source"] == "test"
    assert summary["has_action_card"] is True
    assert summary["route_called"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["midi_asset_created"] is False


def test_terminal_action_card_summarizes_latest_controlled_execution_and_traces_it(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="practice_plan_generation", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    session.preview_tool_call("agent_practice_plan", {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30})
    session.confirm_pending_tool()
    session.execute_confirmed_tool_dry_run()
    session.dispatch_confirmed_tool_workflow_dry_run()
    controlled = session.execute_controlled_workflow()
    assert controlled["ok"] is True

    action = session.harmonyos_agent_action_card()
    assert action["ok"] is True
    card = action["action_card"]
    assert card["tool_name"] == "agent_practice_plan"
    assert card["execution_status"] == "controlled_execution_succeeded"
    assert card["route_called"] is False
    assert card["engine_adapter_called"] is False
    assert card["midi_asset_created"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    action_traces = [payload for payload in traces if payload["task_type"] == "terminal_harmonyos_agent_action_card"]
    assert len(action_traces) == 1
    completed = action_traces[0]
    assert completed["validation_result"] == "action_card_built"
    step_names = [step["name"] for step in completed["steps"]]
    assert "terminal_harmonyos_agent_action_card_built" in step_names
    assert completed["final_response_summary"]["harmonyos_agent_action_summary"]["midi_asset_created"] is False


def test_harmonyos_agent_action_api_preview_and_controlled_execution_routes() -> None:
    client = TestClient(app)
    spec = client.get("/agent/actions/spec").json()["spec"]
    assert spec["version"] == "v2_6_6"
    assert spec["execution_status"]["playback_execution_enabled"] is False

    preview = client.post(
        "/agent/actions/preview",
        json={
            "taskType": "practice_plan_generation",
            "toolName": "agent_practice_plan",
            "arguments": {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
            "traceId": "trace_from_client",
        },
    ).json()
    assert preview["ok"] is True
    assert preview["harmonyos_agent_action_contract_version"] == "v2_6_6"
    assert preview["action_card"]["confirmation_status"] == "pending"
    assert preview["action_card"]["execution_status"] == "confirmation_required"
    assert preview["action_card"]["trace_id"] == "trace_from_client"

    controlled = client.post(
        "/agent/actions/execute-controlled",
        json={
            "taskType": "practice_plan_generation",
            "toolName": "agent_practice_plan",
            "arguments": {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
            "userApproved": True,
        },
    ).json()
    assert controlled["ok"] is True
    card = controlled["action_card"]
    assert card["execution_status"] == "controlled_execution_succeeded"
    assert card["result_preview"]["plan"]["duration_minutes"] == 30
    assert card["route_called"] is False
    assert card["engine_adapter_called"] is False
    assert card["midi_asset_created"] is False

    blocked_playback = client.post(
        "/agent/actions/execute-controlled",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": True,
        },
    ).json()
    assert blocked_playback["ok"] is False
    assert blocked_playback["action_card"]["tool_name"] == "agent_playback_prepare"
    assert blocked_playback["action_card"]["execution_status"] == "controlled_execution_blocked"
    assert blocked_playback["action_card"]["midi_asset_created"] is False


def test_runtime_and_trace_specs_expose_harmonyos_agent_action_boundary() -> None:
    trace_spec = trace_api_contract()
    action_trace = trace_spec["harmonyos_agent_action_trace_contract"]
    assert action_trace["version"] == "v2_6_6"
    assert action_trace["action_card_enabled"] is True
    assert action_trace["accompaniment_generate_call_enabled"] is False
    assert action_trace["engine_adapter_dispatch_enabled"] is False
    assert action_trace["midi_asset_creation_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["harmonyos_agent_action_boundary"]
    assert boundary["version"] == "v2_6_6"
    assert boundary["execution_status"]["midi_asset_creation_enabled"] is False


def test_action_contract_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
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
        assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
        assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)


def test_agent_track_docs_record_v2_6_6_without_shared_doc_dependency() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_HARMONYOS_AGENT_ACTION_CONTRACT_V2_6_6.md").read_text(encoding="utf-8")
    assert "v2_6_6_harmonyos_agent_action_contract" in plan
    assert "v2_6_6 — HarmonyOS Agent Action Contract" in changelog
    assert "Routine-facing AgentActionCard" in detail_doc
    assert "does not call /accompaniment/generate" in detail_doc
