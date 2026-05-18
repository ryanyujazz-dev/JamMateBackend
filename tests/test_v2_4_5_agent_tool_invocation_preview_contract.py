from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_invocation import (
    TOOL_INVOCATION_PREVIEW_VERSION,
    ToolInvocationProposal,
    preview_tool_invocation,
    tool_invocation_preview_contract,
)
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def test_tool_invocation_preview_contract_spec_route_is_validation_only() -> None:
    client = TestClient(app)
    payload = client.get("/agent/tools/invocation/spec").json()
    assert payload["ok"] is True
    spec = payload["spec"]
    assert spec["version"] == "v2_4_12"
    assert spec["route"] == "POST /agent/tools/invocation/preview"
    assert spec["execution_status"]["tool_execution_enabled"] is False
    assert spec["execution_status"]["deterministic_workflow_dispatch_enabled"] is False
    assert "tool_must_be_allowed_by_context_packet" in spec["policy"]["required_guards"]


def test_allowed_tool_call_is_previewed_but_never_executed() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/tools/invocation/preview",
        json={
            "userInput": "我想练 Blue Bossa 20分钟",
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"userInput": "练 Blue Bossa 20分钟", "durationMinutes": 20},
            "clientContext": {"currentScreen": "practice_home", "availableMinutes": 20},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    preview = payload["preview"]
    assert preview["preview_version"] == "v2_4_12"
    assert preview["status"] == "preview_only_blocked_by_execution_guard"
    assert preview["known_tool"] is True
    assert preview["allowed_by_context"] is True
    assert preview["would_execute"] is False
    assert preview["execution_enabled"] is False
    assert preview["descriptor"]["name"] == "agent_playback_prepare"
    assert preview["validation"]["schema_name"] == "AgentPlaybackPrepareRequest"
    assert "preview_does_not_dispatch_deterministic_workflows" in preview["blocking_reasons"]


def test_not_allowed_tool_is_rejected_against_context_packet_allow_list() -> None:
    client = TestClient(app)
    payload = client.post(
        "/agent/tools/invocation/preview",
        json={"taskType": "immediate_practice_playback", "toolName": "agent_practice_plan", "arguments": {}},
    ).json()
    assert payload["ok"] is False
    preview = payload["preview"]
    assert preview["status"] == "rejected_not_allowed_for_context"
    assert preview["known_tool"] is True
    assert preview["allowed_by_context"] is False
    assert "tool_not_allowed_by_context_packet" in preview["blocking_reasons"]
    assert payload["context_packet_summary"]["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]


def test_unknown_tool_is_rejected_without_execution() -> None:
    packet = ContextBuilder().build("coach_qa", "帮我分析练习", instrument="piano")
    preview = preview_tool_invocation(
        ToolInvocationProposal(tool_name="unknown_tool", task_type=packet.task_type, arguments={"x": 1}),
        allowed_tools=packet.allowed_tools,
    ).to_dict()
    assert preview["ok"] is False
    assert preview["status"] == "rejected_unknown_tool"
    assert preview["would_execute"] is False
    assert preview["known_tool"] is False


def test_context_and_runloop_surface_tool_invocation_preview_policy() -> None:
    client = TestClient(app)
    payload = client.post(
        "/agent/context/runtime/preview",
        json={"userInput": "解释一下 comping", "taskType": "coach_qa"},
    ).json()
    runtime_policy = payload["context_packet"]["runtime_policy"]
    assert runtime_policy["tool_invocation_preview_version"] == TOOL_INVOCATION_PREVIEW_VERSION
    assert runtime_policy["tool_invocation_preview_policy"]["execution_enabled"] is False
    summary = payload["runloop_preview"]["request_envelope_summary"]
    assert summary["tool_invocation_preview_version"] == "v2_4_12"
    assert summary["tool_invocation_preview_enabled"] is True


def test_capability_and_runtime_specs_include_invocation_preview_boundary() -> None:
    client = TestClient(app)
    capability = client.get("/agent/capabilities").json()["manifest"]
    assert "agent_tool_invocation_preview" in [tool["name"] for tool in capability["available_tools"]]
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    assert runtime_spec["tool_invocation_preview_boundary"]["version"] == "v2_4_12"
    assert runtime_spec["routes"]["tool_invocation_preview"] == "POST /agent/tools/invocation/preview"
    assert "No runloop-driven tool execution in v2_4_12; tools are descriptor-only and invocation preview is validation-only." in runtime_spec["non_goals"]


def test_contract_codegen_and_harmonyos_smoke_include_tool_invocation_preview() -> None:
    agent_types = (ROOT / "frontend_fixtures/harmonyos/types/AgentTypes.ets").read_text(encoding="utf-8")
    client_source = (ROOT / "frontend_fixtures/harmonyos/api/JamMateApiClient.ets").read_text(encoding="utf-8")
    smoke = (ROOT / "frontend_fixtures/harmonyos/smoke/smoke_pack.json").read_text(encoding="utf-8")
    assert "AgentToolInvocationPreviewRequest" in agent_types
    assert "previewAgentToolInvocation" in client_source
    assert "/agent/tools/invocation/preview" in smoke
    assert (ROOT / "frontend_fixtures/harmonyos/smoke/smoke_agent_tool_invocation_preview.json").exists()


def test_tool_invocation_preview_module_does_not_import_engine_or_provider_sdks() -> None:
    path = ROOT / "src" / "jammate_agent" / "core" / "tool_invocation.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} for module in imported)


def test_direct_contract_function_remains_pure_spec() -> None:
    spec = tool_invocation_preview_contract()
    assert spec["version"] == "v2_4_12"
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
