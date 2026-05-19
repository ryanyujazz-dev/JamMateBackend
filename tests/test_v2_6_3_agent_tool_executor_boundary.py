from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    TOOL_EXECUTOR_BOUNDARY_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_tool_executor_summary,
    confirm_tool_invocation,
    execute_tool_dry_run,
    preview_tool_invocation,
    tool_executor_boundary_contract,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _approved_confirmation():
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_executor_test")
    return confirm_tool_invocation(confirmation, user_approved=True)


def test_tool_executor_contract_is_dry_run_noop_only() -> None:
    spec = tool_executor_boundary_contract()
    assert spec["version"] == TOOL_EXECUTOR_BOUNDARY_VERSION == "v2_6_3"
    assert spec["execution_status"]["dry_run_enabled"] is True
    assert spec["execution_status"]["noop_execution_enabled"] is True
    assert spec["execution_status"]["real_tool_execution_enabled"] is False
    assert spec["execution_status"]["deterministic_workflow_dispatch_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["guards"]["executor_executes_real_tool"] is False
    assert spec["guards"]["executor_creates_midi_asset"] is False


def test_unapproved_confirmation_is_blocked_by_executor_boundary() -> None:
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    pending = build_confirmation_envelope(preview)

    result = execute_tool_dry_run(pending).to_dict()
    assert result["ok"] is False
    assert result["status"] == "blocked_requires_approved_confirmation"
    assert "approved_confirmation_required_before_executor_boundary" in result["blocking_reasons"]
    assert result["real_tool_executed"] is False
    assert result["deterministic_workflow_dispatched"] is False
    assert result["engine_adapter_called"] is False


def test_approved_confirmation_dry_run_returns_noop_result_without_dispatch() -> None:
    approved = _approved_confirmation()
    result = execute_tool_dry_run(approved).to_dict()

    assert result["ok"] is True
    assert result["status"] == "dry_run_noop_completed"
    assert result["tool_executor_boundary_version"] == "v2_6_3"
    assert result["tool_name"] == "agent_playback_prepare"
    assert result["user_approved"] is True
    assert result["confirmation_status"] == "approved"
    assert result["dry_run"] is True
    assert result["noop_only"] is True
    assert result["real_tool_executed"] is False
    assert result["deterministic_workflow_dispatched"] is False
    assert result["engine_adapter_called"] is False
    assert result["route_called"] is False
    assert result["side_effects_created"] is False
    assert result["next_stage_required"] == "DeterministicWorkflowDispatcher"
    assert result["result_preview"]["would_dispatch_workflow"] is False
    assert result["result_preview"]["would_call_engine_adapter"] is False


def test_executor_summary_shape_is_stable() -> None:
    execution = execute_tool_dry_run(_approved_confirmation())
    summary = build_tool_executor_summary(execution_result=execution, source="test")
    assert summary["tool_executor_boundary_version"] == "v2_6_3"
    assert summary["source"] == "test"
    assert summary["has_execution_result"] is True
    assert summary["execution_status"] == "dry_run_noop_completed"
    assert summary["dry_run"] is True
    assert summary["real_tool_execution_enabled"] is False
    assert summary["deterministic_workflow_dispatched"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["requires_workflow_dispatcher"] is True


def test_terminal_execute_dry_run_requires_confirm_then_traces_result(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))

    preview_response = session.preview_tool_call("agent_playback_prepare", {"durationMinutes": 20})
    assert preview_response["confirmation"]["confirmation_status"] == "pending"

    blocked = session.execute_confirmed_tool_dry_run()
    assert blocked["ok"] is False
    assert blocked["execution_result"]["status"] == "blocked_requires_approved_confirmation"
    assert blocked["execution_result"]["real_tool_executed"] is False

    confirmed = session.confirm_pending_tool()
    assert confirmed["result"]["confirmation_status"] == "approved"

    executed = session.execute_confirmed_tool_dry_run()
    assert executed["ok"] is True
    assert executed["execution_result"]["status"] == "dry_run_noop_completed"
    assert executed["execution_result"]["deterministic_workflow_dispatched"] is False
    assert executed["execution_result"]["engine_adapter_called"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    dry_run_traces = [payload for payload in traces if payload["task_type"] == "terminal_tool_executor_dry_run"]
    assert len(dry_run_traces) == 2
    completed = next(payload for payload in dry_run_traces if payload["validation_result"] == "dry_run_completed")
    step_names = [step["name"] for step in completed["steps"]]
    assert "terminal_tool_executor_dry_run_requested" in step_names
    assert "terminal_tool_executor_dry_run_completed" in step_names
    assert completed["final_response_summary"]["tool_executor_summary"]["real_tool_executed"] is False


def test_executor_api_spec_and_dry_run_route_are_noop_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/tools/executor/spec").json()["spec"]
    assert spec["spec_route"] == "GET /agent/tools/executor/spec"
    assert spec["dry_run_route"] == "POST /agent/tools/executor/dry-run"
    assert spec["execution_status"]["real_tool_execution_enabled"] is False

    blocked = client.post(
        "/agent/tools/executor/dry-run",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": False,
        },
    ).json()
    assert blocked["ok"] is False
    assert blocked["execution_result"]["status"] == "blocked_requires_approved_confirmation"
    assert blocked["execution_result"]["real_tool_executed"] is False

    approved = client.post(
        "/agent/tools/executor/dry-run",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
            "userApproved": True,
        },
    ).json()
    assert approved["ok"] is True
    assert approved["tool_executor_boundary_version"] == "v2_6_3"
    assert approved["execution_result"]["status"] == "dry_run_noop_completed"
    assert approved["execution_result"]["deterministic_workflow_dispatched"] is False
    assert approved["execution_result"]["engine_adapter_called"] is False


def test_runtime_and_trace_specs_expose_executor_boundary() -> None:
    trace_spec = trace_api_contract()
    executor_trace = trace_spec["tool_executor_trace_contract"]
    assert executor_trace["version"] == "v2_6_3"
    assert executor_trace["dry_run_enabled"] is True
    assert executor_trace["real_execution_enabled"] is False
    assert executor_trace["dispatch_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["tool_executor_boundary"]
    assert boundary["version"] == "v2_6_3"
    assert boundary["execution_status"]["engine_adapter_dispatch_enabled"] is False


def test_executor_boundary_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
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


def test_agent_track_docs_record_v2_6_3_without_shared_doc_dependency() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_TOOL_EXECUTOR_BOUNDARY_V2_6_3.md").read_text(encoding="utf-8")
    assert "v2_6_3_agent_tool_executor_boundary" in plan
    assert "v2_6_3 — Agent Tool Executor Boundary" in changelog
    assert "dry-run / no-op only" in detail_doc
    assert "不" not in detail_doc or "does not" in detail_doc
