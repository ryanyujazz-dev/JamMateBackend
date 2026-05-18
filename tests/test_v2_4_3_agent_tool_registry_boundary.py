from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, tool_registry_manifest, validate_allowed_tools
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def test_tool_registry_route_is_descriptor_only_and_contains_task_allow_lists() -> None:
    client = TestClient(app)
    response = client.get("/agent/tools/registry")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    registry = payload["registry"]
    assert registry["version"] == "v2_4_7"
    assert registry["execution_status"]["tool_execution_enabled"] is False
    assert registry["execution_status"]["autonomous_tool_execution_enabled"] is False
    assert "agent_tool_registry_spec" in registry["tool_names"]
    assert registry["task_allow_lists"]["immediate_practice_playback"] == ["direct_accompaniment_generate", "chart_resolve", "agent_playback_prepare"]


def test_context_packet_embeds_tool_descriptors_without_enabling_execution() -> None:
    packet = ContextBuilder().build("immediate_practice_playback", "帮我准备 Blue Bossa 20分钟", duration_minutes=20)
    data = packet.to_dict()
    assert data["context_runtime_version"] == "v2_4_7"
    assert data["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]
    descriptors = {descriptor["name"]: descriptor for descriptor in data["tool_descriptors"]}
    assert set(descriptors) == {"chart_resolve", "agent_playback_prepare"}
    assert descriptors["agent_playback_prepare"]["autonomous_execution_enabled"] is False
    assert data["runtime_policy"]["tool_registry_boundary_version"] == TOOL_REGISTRY_VERSION
    assert data["runtime_policy"]["tool_execution_enabled"] is False
    assert data["runtime_policy"]["allowed_tool_validation"]["all_known"] is True


def test_runloop_preview_reports_tool_registry_summary_but_does_not_execute_tools() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/context/runtime/preview",
        json={"userInput": "我今天练Misty", "taskType": "practice_plan_generation"},
    )
    assert response.status_code == 200
    payload = response.json()
    preview = payload["runloop_preview"]
    assert preview["runtime_mode"] == "preview_only"
    assert preview["tool_execution_enabled"] is False
    assert preview["tool_registry_summary"]["registry_version"] == "v2_4_7"
    assert preview["tool_registry_summary"]["all_known"] is True
    assert preview["request_envelope_summary"]["tool_registry_version"] == "v2_4_7"
    assert preview["request_envelope_summary"]["tool_descriptor_count"] == 1


def test_capability_manifest_reuses_registry_descriptors() -> None:
    client = TestClient(app)
    manifest = client.get("/agent/capabilities").json()["manifest"]
    registry = tool_registry_manifest()
    manifest_names = [tool["name"] for tool in manifest["available_tools"]]
    assert manifest["version"] == "v2_4_7"
    assert manifest["tool_registry"]["route"] == "GET /agent/tools/registry"
    assert manifest_names == registry["tool_names"]
    tools = {tool["name"]: tool for tool in manifest["available_tools"]}
    assert tools["agent_tool_registry_spec"]["route"] == "GET /agent/tools/registry"
    assert tools["direct_accompaniment_generate"]["input_contract"]["preferred_chart_input"] == "inline jammate_leadsheet_v2"


def test_tool_registry_validation_flags_unknown_allowed_tools() -> None:
    result = validate_allowed_tools(["agent_practice_plan", "unknown_tool"])
    assert result["all_known"] is False
    assert result["unknown_tools"] == ["unknown_tool"]
    assert result["tool_execution_enabled"] is False
    assert result["autonomous_execution_enabled"] is False


def test_context_runtime_spec_exposes_tool_registry_route_and_boundary() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/runtime/spec").json()["spec"]
    assert spec["version"] == "v2_4_7"
    assert spec["routes"]["tool_registry"] == "GET /agent/tools/registry"
    assert spec["tool_registry_boundary"]["execution_status"]["autonomous_tool_execution_enabled"] is False
    assert "No runloop-driven tool execution in v2_4_7; tools are descriptor-only." in spec["non_goals"]


def test_tool_registry_does_not_import_engine_or_provider_sdks() -> None:
    path = ROOT / "src" / "jammate_agent" / "core" / "tool_registry.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} for module in imported)
