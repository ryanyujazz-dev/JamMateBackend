from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import LLMProviderConfig, build_request_envelope
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def test_llm_provider_spec_route_is_disabled_by_default_and_has_config_guard() -> None:
    client = TestClient(app)
    response = client.get("/agent/llm/provider/spec")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    spec = payload["spec"]
    assert spec["version"] == "v2_4_7"
    assert spec["boundary_version"] == "v2_4_7"
    assert spec["guards"]["api_runloop_llm_calls_enabled"] is False
    assert spec["guards"]["autonomous_tool_execution_enabled"] is False
    assert spec["status"]["provider_name"] == "none"
    assert spec["status"]["provider_configured"] is False
    assert spec["status"]["llm_calls_enabled"] is False
    assert spec["future_provider_contract"]["request_envelope"] == [
        "context_packet",
        "allowed_tools",
        "output_contract",
        "runtime_policy",
        "messages",
    ]


def test_llm_provider_config_requires_provider_api_key_and_network_gate() -> None:
    assert LLMProviderConfig.from_env({}).provider_configured is False
    missing_network = LLMProviderConfig.from_env(
        {
            "JAMMATE_LLM_PROVIDER": "local_stub",
            "JAMMATE_LLM_API_KEY": "secret",
        }
    )
    assert missing_network.provider_configured is False
    assert missing_network.guard_reason == "JAMMATE_LLM_ENABLE_NETWORK_CALLS is not enabled."

    configured = LLMProviderConfig.from_env(
        {
            "JAMMATE_LLM_PROVIDER": "local_stub",
            "JAMMATE_LLM_MODEL": "test-model",
            "JAMMATE_LLM_API_KEY": "secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
        }
    )
    assert configured.provider_configured is True
    assert configured.to_dict()["execution_mode"] == "provider_configured_but_unsupported_or_missing_model"


def test_context_packet_embeds_provider_status_but_keeps_preview_only_runtime() -> None:
    packet = ContextBuilder().build(
        "coach_qa",
        "解释一下 altered dominant 什么时候用",
        client_context={"current_screen": "practice_home"},
    )
    data = packet.to_dict()
    runtime_policy = data["runtime_policy"]
    assert runtime_policy["llm_required"] is True
    assert runtime_policy["llm_provider_boundary_version"] == "v2_4_7"
    assert runtime_policy["llm_provider_status"]["provider_configured"] is False
    assert runtime_policy["llm_call_mode"] == "provider_boundary_preview_only"
    assert runtime_policy["autonomous_tool_execution_enabled"] is False


def test_runloop_preview_exposes_provider_status_and_request_envelope_summary() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/context/runtime/preview",
        json={"userInput": "解释一下 altered dominant", "taskType": "coach_qa"},
    )
    assert response.status_code == 200
    payload = response.json()
    preview = payload["runloop_preview"]
    assert preview["runtime_mode"] == "preview_only"
    assert preview["tool_execution_enabled"] is False
    assert preview["next_action"] == "llm_required_but_provider_unavailable"
    assert preview["llm_provider_status"]["boundary_version"] == "v2_4_7"
    assert preview["request_envelope_summary"]["message_count"] == 3
    assert preview["request_envelope_summary"]["allowed_tools"] == ["agent_practice_plan", "agent_playback_prepare"]


def test_request_envelope_is_provider_neutral_and_uses_allowed_tools() -> None:
    packet = ContextBuilder().build("practice_plan_generation", "我今天练Misty", available_minutes=45)
    envelope = build_request_envelope(packet)
    data = envelope.to_dict()
    assert data["allowed_tools"] == ["agent_practice_plan"]
    assert data["output_contract"]["schema"] == "PracticePlan"
    assert data["messages"][0]["role"] == "system"
    assert "JamMate Agent" in data["messages"][0]["content"]


def test_capability_manifest_advertises_provider_boundary_tool() -> None:
    client = TestClient(app)
    manifest = client.get("/agent/capabilities").json()["manifest"]
    tools = {tool["name"]: tool for tool in manifest["available_tools"]}
    assert "agent_llm_provider_boundary_spec" in tools
    assert tools["agent_llm_provider_boundary_spec"]["input_contract"]["route"] == "GET /agent/llm/provider/spec"
    assert tools["agent_llm_provider_boundary_spec"]["output_contract"]["llm_calls_enabled"] is False


def test_provider_boundary_does_not_import_engine_or_provider_sdks() -> None:
    path = ROOT / "src" / "jammate_agent" / "core" / "llm_provider.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
