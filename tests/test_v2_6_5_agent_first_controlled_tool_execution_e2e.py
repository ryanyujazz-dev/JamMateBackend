from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    CONTROLLED_WORKFLOW_EXECUTION_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_controlled_workflow_execution_summary,
    confirm_tool_invocation,
    controlled_workflow_execution_contract,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    execute_tool_dry_run,
    preview_tool_invocation,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _practice_plan_dispatch_result(arguments: dict | None = None):
    proposal = ToolInvocationProposal(
        tool_name="agent_practice_plan",
        arguments=arguments or {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
        task_type="practice_plan_generation",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["agent_practice_plan"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_controlled_test")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    return dispatch_deterministic_workflow_dry_run(execution)


def test_controlled_workflow_execution_contract_limits_real_execution_to_practice_plan() -> None:
    spec = controlled_workflow_execution_contract()
    assert spec["version"] == CONTROLLED_WORKFLOW_EXECUTION_VERSION == "v2_6_5"
    assert spec["spec_route"] == "GET /agent/tools/workflows/controlled-execution/spec"
    assert spec["execute_route"] == "POST /agent/tools/workflows/execute-controlled"
    assert spec["execution_status"]["controlled_execution_enabled"] is True
    assert spec["execution_status"]["autonomous_execution_enabled"] is False
    assert spec["execution_status"]["allowed_tool_names"] == ["agent_practice_plan"]
    assert spec["execution_status"]["allowed_workflow_names"] == ["PracticePlanner.build_plan"]
    assert spec["execution_status"]["route_call_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["execution_status"]["midi_asset_creation_enabled"] is False
    assert spec["guards"]["controlled_execution_calls_route"] is False
    assert spec["guards"]["controlled_execution_creates_midi_asset"] is False


def test_controlled_workflow_executes_practice_plan_without_engine_or_route_calls() -> None:
    dispatch = _practice_plan_dispatch_result()

    def runner(tool_name: str, arguments: dict) -> dict:
        assert tool_name == "agent_practice_plan"
        assert arguments["availableMinutes"] == 30
        return {
            "ok": True,
            "intent_type": "practice_plan_generation",
            "plan": {"title": "Blue Bossa Practice 30", "duration_minutes": 30, "blocks": []},
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }

    result = execute_controlled_workflow(dispatch, workflow_runner=runner).to_dict()
    assert result["ok"] is True
    assert result["status"] == "controlled_workflow_completed"
    assert result["tool_name"] == "agent_practice_plan"
    assert result["workflow_name"] == "PracticePlanner.build_plan"
    assert result["workflow_invoked"] is True
    assert result["deterministic_workflow_dispatched"] is True
    assert result["route_called"] is False
    assert result["engine_adapter_called"] is False
    assert result["side_effects_created"] is False
    assert result["midi_asset_created"] is False
    assert result["workflow_output"]["plan"]["duration_minutes"] == 30


def test_controlled_workflow_blocks_side_effectful_playback_workflow() -> None:
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    confirmation = build_confirmation_envelope(preview)
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)

    result = execute_controlled_workflow(dispatch, workflow_runner=lambda _name, _args: {"ok": True}).to_dict()
    assert result["ok"] is False
    assert result["status"] == "blocked_by_controlled_execution_policy"
    assert "tool_not_enabled_for_first_controlled_execution" in result["blocking_reasons"]
    assert "workflow_not_enabled_for_first_controlled_execution" in result["blocking_reasons"]
    assert "side_effectful_workflow_not_allowed_in_v2_6_5" in result["blocking_reasons"]
    assert result["workflow_invoked"] is False
    assert result["engine_adapter_called"] is False
    assert result["midi_asset_created"] is False


def test_terminal_controlled_practice_plan_e2e_traces_output(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="practice_plan_generation", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))

    missing = session.execute_controlled_workflow()
    assert missing["ok"] is False
    assert missing["error_code"] == "NO_WORKFLOW_DISPATCH_DESCRIPTOR_AVAILABLE"

    preview = session.preview_tool_call("agent_practice_plan", {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30})
    assert preview["confirmation"]["confirmation_status"] == "pending"
    assert session.confirm_pending_tool()["result"]["confirmation_status"] == "approved"
    assert session.execute_confirmed_tool_dry_run()["ok"] is True
    assert session.dispatch_confirmed_tool_workflow_dry_run()["ok"] is True

    controlled = session.execute_controlled_workflow()
    assert controlled["ok"] is True
    result = controlled["controlled_workflow_execution_result"]
    assert result["status"] == "controlled_workflow_completed"
    assert result["workflow_invoked"] is True
    assert result["route_called"] is False
    assert result["engine_adapter_called"] is False
    assert result["midi_asset_created"] is False
    plan = result["workflow_output"]["plan"]
    assert plan["duration_minutes"] == 30
    assert sum(block["duration_minutes"] for block in plan["blocks"]) == 30

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    controlled_traces = [payload for payload in traces if payload["task_type"] == "terminal_controlled_workflow_execution"]
    assert len(controlled_traces) == 1
    completed = controlled_traces[0]
    assert completed["validation_result"] == "controlled_workflow_completed"
    step_names = [step["name"] for step in completed["steps"]]
    assert "terminal_controlled_workflow_execution_requested" in step_names
    assert "terminal_controlled_workflow_execution_completed" in step_names
    summary = completed["final_response_summary"]["controlled_workflow_execution_summary"]
    assert summary["workflow_invoked"] is True
    assert summary["route_called"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["midi_asset_created"] is False


def test_controlled_execution_api_spec_and_route_run_practice_plan_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/tools/workflows/controlled-execution/spec").json()["spec"]
    assert spec["version"] == "v2_6_5"
    assert spec["execution_status"]["allowed_tool_names"] == ["agent_practice_plan"]

    blocked = client.post(
        "/agent/tools/workflows/execute-controlled",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": True,
        },
    ).json()
    assert blocked["ok"] is False
    assert blocked["controlled_workflow_execution_result"]["workflow_invoked"] is False
    assert blocked["controlled_workflow_execution_result"]["engine_adapter_called"] is False

    approved = client.post(
        "/agent/tools/workflows/execute-controlled",
        json={
            "taskType": "practice_plan_generation",
            "toolName": "agent_practice_plan",
            "arguments": {"userInput": "练 30 分钟 Blue Bossa", "availableMinutes": 30},
            "userApproved": True,
        },
    ).json()
    assert approved["ok"] is True
    assert approved["controlled_workflow_execution_version"] == "v2_6_5"
    result = approved["controlled_workflow_execution_result"]
    assert result["status"] == "controlled_workflow_completed"
    assert result["workflow_output"]["plan"]["duration_minutes"] == 30
    assert result["route_called"] is False
    assert result["engine_adapter_called"] is False
    assert result["midi_asset_created"] is False


def test_runtime_and_trace_specs_expose_controlled_workflow_execution_boundary() -> None:
    trace_spec = trace_api_contract()
    controlled_trace = trace_spec["controlled_workflow_execution_trace_contract"]
    assert controlled_trace["version"] == "v2_6_5"
    assert controlled_trace["controlled_execution_enabled"] is True
    assert controlled_trace["allowed_tool_names"] == ["agent_practice_plan"]
    assert controlled_trace["route_call_enabled"] is False
    assert controlled_trace["engine_adapter_dispatch_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["controlled_workflow_execution_boundary"]
    assert boundary["version"] == "v2_6_5"
    assert boundary["execution_status"]["midi_asset_creation_enabled"] is False


def test_controlled_execution_summary_shape_is_stable() -> None:
    result = execute_controlled_workflow(
        _practice_plan_dispatch_result(),
        workflow_runner=lambda _name, _args: {"ok": True, "plan": {"duration_minutes": 30}},
    )
    summary = build_controlled_workflow_execution_summary(execution_result=result, source="test")
    assert summary["controlled_workflow_execution_version"] == "v2_6_5"
    assert summary["source"] == "test"
    assert summary["has_controlled_execution_result"] is True
    assert summary["execution_status"] == "controlled_workflow_completed"
    assert summary["tool_name"] == "agent_practice_plan"
    assert summary["workflow_name"] == "PracticePlanner.build_plan"
    assert summary["workflow_invoked"] is True
    assert summary["route_called"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["midi_asset_created"] is False


def test_controlled_execution_does_not_import_engine_or_network_clients_in_boundary_files() -> None:
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


def test_agent_track_docs_record_v2_6_5_without_shared_doc_dependency() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_FIRST_CONTROLLED_TOOL_EXECUTION_E2E_V2_6_5.md").read_text(encoding="utf-8")
    assert "v2_6_5_agent_first_controlled_tool_execution_e2e" in plan
    assert "v2_6_5 — Agent First Controlled Tool Execution E2E" in changelog
    assert "agent_practice_plan" in detail_doc
    assert "PracticePlanner.build_plan" in detail_doc
    assert "MIDI" in detail_doc
