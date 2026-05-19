from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    TOOL_WORKFLOW_DISPATCHER_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_tool_workflow_dispatcher_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_tool_dry_run,
    preview_tool_invocation,
    tool_workflow_dispatcher_contract,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _successful_executor_result():
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_dispatch_test")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    return execute_tool_dry_run(approved)


def test_workflow_dispatcher_contract_is_descriptor_only() -> None:
    spec = tool_workflow_dispatcher_contract()
    assert spec["version"] == TOOL_WORKFLOW_DISPATCHER_VERSION == "v2_6_4"
    assert spec["spec_route"] == "GET /agent/tools/workflows/spec"
    assert spec["dispatch_dry_run_route"] == "POST /agent/tools/workflows/dispatch-dry-run"
    assert spec["execution_status"]["workflow_descriptor_resolution_enabled"] is True
    assert spec["execution_status"]["real_workflow_dispatch_enabled"] is False
    assert spec["execution_status"]["route_call_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["guards"]["dispatcher_invokes_workflow"] is False
    assert spec["guards"]["dispatcher_creates_midi_asset"] is False


def test_dispatcher_blocks_before_successful_executor_dry_run() -> None:
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    pending = build_confirmation_envelope(preview)
    blocked_executor = execute_tool_dry_run(pending)

    dispatch = dispatch_deterministic_workflow_dry_run(blocked_executor).to_dict()
    assert dispatch["ok"] is False
    assert dispatch["status"] == "blocked_requires_successful_executor_dry_run"
    assert "successful_tool_executor_dry_run_required_before_workflow_descriptor_resolution" in dispatch["blocking_reasons"]
    assert dispatch["workflow_descriptor_resolved"] is False
    assert dispatch["deterministic_workflow_dispatched"] is False
    assert dispatch["engine_adapter_called"] is False


def test_dispatcher_resolves_workflow_descriptor_without_invoking_it() -> None:
    execution = _successful_executor_result()
    dispatch = dispatch_deterministic_workflow_dry_run(execution).to_dict()

    assert dispatch["ok"] is True
    assert dispatch["status"] == "workflow_descriptor_resolved"
    assert dispatch["tool_workflow_dispatcher_version"] == "v2_6_4"
    assert dispatch["workflow_descriptor_resolved"] is True
    assert dispatch["deterministic_workflow_dispatched"] is False
    assert dispatch["workflow_invoked"] is False
    assert dispatch["route_called"] is False
    assert dispatch["engine_adapter_called"] is False
    assert dispatch["side_effects_created"] is False

    descriptor = dispatch["workflow_descriptor"]
    assert descriptor["tool_name"] == "agent_playback_prepare"
    assert descriptor["workflow_name"] == "ImmediatePlaybackWorkflow.prepare"
    assert descriptor["route"] == "POST /agent/playback/prepare"
    assert descriptor["adapter_boundary"] == "jammate_agent.adapters.JamMateEngineAccompanimentAdapter"
    assert descriptor["workflow_descriptor_resolved"] is True
    assert descriptor["deterministic_workflow_dispatched"] is False
    assert descriptor["next_stage_required"] == "ControlledWorkflowExecution"


def test_dispatcher_summary_shape_is_stable() -> None:
    result = dispatch_deterministic_workflow_dry_run(_successful_executor_result())
    summary = build_tool_workflow_dispatcher_summary(dispatch_result=result, source="test")
    assert summary["tool_workflow_dispatcher_version"] == "v2_6_4"
    assert summary["source"] == "test"
    assert summary["has_dispatch_result"] is True
    assert summary["dispatch_status"] == "workflow_descriptor_resolved"
    assert summary["workflow_name"] == "ImmediatePlaybackWorkflow.prepare"
    assert summary["workflow_descriptor_resolved"] is True
    assert summary["deterministic_workflow_dispatched"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["requires_controlled_workflow_execution"] is True


def test_terminal_dispatch_dry_run_requires_executor_then_traces_descriptor(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))

    no_executor = session.dispatch_confirmed_tool_workflow_dry_run()
    assert no_executor["ok"] is False
    assert no_executor["error_code"] == "NO_EXECUTOR_DRY_RUN_AVAILABLE"

    preview = session.preview_tool_call("agent_playback_prepare", {"durationMinutes": 20})
    assert preview["confirmation"]["confirmation_status"] == "pending"
    confirmed = session.confirm_pending_tool()
    assert confirmed["result"]["confirmation_status"] == "approved"
    executed = session.execute_confirmed_tool_dry_run()
    assert executed["ok"] is True

    dispatch = session.dispatch_confirmed_tool_workflow_dry_run()
    assert dispatch["ok"] is True
    assert dispatch["workflow_dispatch_result"]["status"] == "workflow_descriptor_resolved"
    assert dispatch["workflow_dispatch_result"]["workflow_descriptor"]["workflow_name"] == "ImmediatePlaybackWorkflow.prepare"
    assert dispatch["workflow_dispatch_result"]["deterministic_workflow_dispatched"] is False
    assert dispatch["workflow_dispatch_result"]["engine_adapter_called"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    dispatch_traces = [payload for payload in traces if payload["task_type"] == "terminal_tool_workflow_dispatch_dry_run"]
    assert len(dispatch_traces) == 1
    completed = dispatch_traces[0]
    assert completed["validation_result"] == "workflow_descriptor_resolved"
    step_names = [step["name"] for step in completed["steps"]]
    assert "terminal_tool_workflow_dispatch_dry_run_requested" in step_names
    assert "terminal_tool_workflow_descriptor_resolved" in step_names
    assert completed["final_response_summary"]["tool_workflow_dispatcher_summary"]["deterministic_workflow_dispatched"] is False


def test_workflow_dispatcher_api_spec_and_dry_run_route_are_descriptor_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/tools/workflows/spec").json()["spec"]
    assert spec["version"] == "v2_6_4"
    assert spec["execution_status"]["workflow_descriptor_resolution_enabled"] is True
    assert spec["execution_status"]["real_workflow_dispatch_enabled"] is False

    blocked = client.post(
        "/agent/tools/workflows/dispatch-dry-run",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": False,
        },
    ).json()
    assert blocked["ok"] is False
    assert blocked["workflow_dispatch_result"]["status"] == "blocked_requires_successful_executor_dry_run"

    approved = client.post(
        "/agent/tools/workflows/dispatch-dry-run",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": True,
        },
    ).json()
    assert approved["ok"] is True
    assert approved["tool_workflow_dispatcher_version"] == "v2_6_4"
    assert approved["workflow_dispatch_result"]["status"] == "workflow_descriptor_resolved"
    assert approved["workflow_dispatch_result"]["deterministic_workflow_dispatched"] is False
    assert approved["workflow_dispatch_result"]["route_called"] is False
    assert approved["workflow_dispatch_result"]["engine_adapter_called"] is False


def test_runtime_and_trace_specs_expose_workflow_dispatcher_boundary() -> None:
    trace_spec = trace_api_contract()
    workflow_trace = trace_spec["tool_workflow_dispatcher_trace_contract"]
    assert workflow_trace["version"] == "v2_6_4"
    assert workflow_trace["workflow_descriptor_resolution_enabled"] is True
    assert workflow_trace["real_workflow_dispatch_enabled"] is False
    assert workflow_trace["route_call_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["tool_workflow_dispatcher_boundary"]
    assert boundary["version"] == "v2_6_4"
    assert boundary["execution_status"]["engine_adapter_dispatch_enabled"] is False


def test_workflow_dispatcher_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
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


def test_agent_track_docs_record_v2_6_4_without_shared_doc_dependency() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_DETERMINISTIC_WORKFLOW_DISPATCHER_V2_6_4.md").read_text(encoding="utf-8")
    assert "v2_6_4_agent_deterministic_workflow_dispatcher" in plan
    assert "v2_6_4 — Agent Deterministic Workflow Dispatcher" in changelog
    assert "descriptor resolution only" in detail_doc
    assert "does not invoke workflows" in detail_doc
