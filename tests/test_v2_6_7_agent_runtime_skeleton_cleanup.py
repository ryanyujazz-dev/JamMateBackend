from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.contracts import llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    AGENT_RUNTIME_SKELETON_CLEANUP_VERSION,
    agent_runtime_no_side_effect_flags,
    agent_runtime_skeleton_contract,
    build_agent_runtime_skeleton_snapshot,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_skeleton_contract_consolidates_agent_lifecycle_without_side_effects() -> None:
    spec = agent_runtime_skeleton_contract()
    assert spec["version"] == AGENT_RUNTIME_SKELETON_CLEANUP_VERSION == "v2_6_7"
    assert spec["spec_route"] == "GET /agent/runtime/skeleton"
    assert spec["status"] == "skeleton_ready_for_specific_agent_features"
    assert spec["stage_count"] == 9
    assert [stage["stage"] for stage in spec["stages"]] == [
        "context_packet",
        "llm_provider_boundary",
        "tool_registry",
        "tool_invocation_preview",
        "tool_execution_confirmation",
        "tool_executor_boundary",
        "deterministic_workflow_dispatcher",
        "controlled_workflow_execution",
        "harmonyos_agent_action_card",
    ]
    assert spec["controlled_execution_allowed_tools"] == ["agent_practice_plan"]
    assert spec["contract_does_not_execute_tools"] is True
    assert spec["contract_does_not_dispatch_workflows"] is True
    assert spec["contract_does_not_call_engine_adapter"] is True
    assert spec["contract_does_not_create_midi_asset"] is True
    guards = spec["no_side_effect_guards"]
    assert guards == agent_runtime_no_side_effect_flags()
    assert guards["accompaniment_generate_call_enabled"] is False
    assert guards["engine_adapter_dispatch_enabled"] is False
    assert guards["midi_asset_creation_enabled"] is False


def test_runtime_skeleton_snapshot_is_read_only_and_stable() -> None:
    snapshot = build_agent_runtime_skeleton_snapshot().to_dict()
    assert snapshot["agent_runtime_skeleton_cleanup_version"] == "v2_6_7"
    assert "/runtime-skeleton" in snapshot["terminal_commands"]
    assert "GET /agent/runtime/skeleton" in snapshot["api_routes"]
    assert snapshot["cleanup_assertions"]["single_core_owner_for_agent_tool_lifecycle"] == "src/jammate_agent/core/tool_invocation.py"
    assert snapshot["cleanup_assertions"]["shared_docs_modified_by_agent_branch"] is False
    assert "agent_playback_prepare_real_execution" in snapshot["forbidden_until_future_milestone"]


def test_terminal_runtime_skeleton_command_records_read_only_trace(tmp_path: Path) -> None:
    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    result = session.agent_runtime_skeleton_status()
    assert result["ok"] is True
    assert result["agent_runtime_skeleton_cleanup_version"] == "v2_6_7"
    assert result["runtime_skeleton"]["stage_count"] == 9
    assert result["agent_runtime_skeleton_summary"]["midi_asset_creation_enabled"] is False

    traces = list(tmp_path.glob("trace_*.json"))
    assert len(traces) == 1
    payload = traces[0].read_text(encoding="utf-8")
    assert "terminal_agent_runtime_skeleton_snapshot_built" in payload
    assert "runtime_skeleton_status_built" in payload


def test_api_and_runtime_specs_expose_runtime_skeleton_cleanup_boundary() -> None:
    client = TestClient(app)
    response = client.get("/agent/runtime/skeleton").json()
    assert response["ok"] is True
    assert response["agent_runtime_skeleton_cleanup_version"] == "v2_6_7"
    assert response["runtime_skeleton"]["no_side_effect_guards"]["playback_execution_enabled"] is False
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False

    runtime_spec = llm_context_runtime_contract()
    assert runtime_spec["routes"]["agent_runtime_skeleton"] == "GET /agent/runtime/skeleton"
    assert runtime_spec["agent_runtime_skeleton_cleanup_boundary"]["version"] == "v2_6_7"

    trace_spec = trace_api_contract()
    trace_boundary = trace_spec["agent_runtime_skeleton_cleanup_trace_contract"]
    assert trace_boundary["version"] == "v2_6_7"
    assert trace_boundary["read_only_status_enabled"] is True
    assert trace_boundary["accompaniment_generate_call_enabled"] is False


def test_runtime_skeleton_cleanup_stays_agent_only_and_has_no_network_imports() -> None:
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


def test_agent_docs_record_v2_6_7_without_generic_continuation_names() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_RUNTIME_SKELETON_CLEANUP_V2_6_7.md").read_text(encoding="utf-8")
    assert "v2_6_7_agent_runtime_skeleton_cleanup" in plan
    assert "v2_6_7 — Agent Runtime Skeleton Cleanup" in changelog
    assert "read-only runtime skeleton status" in detail_doc
    assert "does not call /accompaniment/generate" in detail_doc

    forbidden_doc_names = {"CONTINUATION.md", "NEXT_STEPS.md", "TASK_PLAN.md"}
    assert not any(path.name in forbidden_doc_names for path in (ROOT / "docs").glob("*.md"))
