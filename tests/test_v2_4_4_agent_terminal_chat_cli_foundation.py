from __future__ import annotations

import ast
import io
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import LLMProviderConfig, LLMProviderResult, build_llm_provider_from_env, build_request_envelope
from jammate_api.app import app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


class FakeProvider:
    def status(self) -> dict:
        return {
            "provider_name": "fake",
            "model": "fake-model",
            "provider_configured": True,
            "terminal_chat_enabled": True,
            "llm_calls_enabled": True,
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "guard_reason": "fake provider for tests",
        }

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001 - protocol-shaped test fake
        messages = envelope.to_dict()["messages"]
        assert messages[-1]["role"] == "user"
        assert envelope.to_dict()["allowed_tools"] == ["agent_practice_plan", "agent_playback_prepare"]
        return LLMProviderResult(ok=True, content=f"回答：{messages[-1]['content']}", provider_name="fake", model="fake-model")


def test_terminal_chat_cli_default_is_guarded_and_does_not_execute_tools() -> None:
    stdout = io.StringIO()
    code = run_interactive_chat(["--once", "解释一下 altered dominant"], stdout=stdout)
    output = stdout.getvalue()
    assert code == 0
    assert "Provider status:" in output
    assert "terminal_chat_enabled: False" in output
    assert "tool_execution_enabled: False" in output
    assert "JamMate[guarded]> LLM_PROVIDER_DISABLED" in output


def test_terminal_chat_session_reuses_context_packet_and_keeps_history() -> None:
    session = TerminalChatSession(provider=FakeProvider())
    response = session.respond("解释一下 altered dominant")
    assert response["ok"] is True
    assert response["terminal_chat_version"] == "v2_4_12"
    assert response["task_type"] == "coach_qa"
    assert response["tool_execution_enabled"] is False
    assert response["allowed_tools"] == ["agent_practice_plan", "agent_playback_prepare"]
    assert response["context_runtime_version"] == "v2_4_12"
    assert len(session.history) == 2


def test_provider_config_supports_openai_compatible_terminal_chat_gate() -> None:
    config = LLMProviderConfig.from_env(
        {
            "JAMMATE_LLM_PROVIDER": "openai_compatible",
            "JAMMATE_LLM_MODEL": "test-model",
            "JAMMATE_LLM_API_KEY": "secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
            "JAMMATE_LLM_BASE_URL": "https://example.test/v1",
        }
    )
    assert config.provider_configured is True
    assert config.supported_provider is True
    assert config.terminal_chat_available is True
    provider = build_llm_provider_from_env(
        {
            "JAMMATE_LLM_PROVIDER": "openai_compatible",
            "JAMMATE_LLM_MODEL": "test-model",
            "JAMMATE_LLM_API_KEY": "secret",
            "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true",
        }
    )
    status = provider.status()
    assert status["terminal_chat_enabled"] is True
    assert status["llm_calls_enabled"] is True
    assert status["autonomous_tool_execution_enabled"] is False


def test_request_envelope_can_include_conversation_history_without_tool_execution() -> None:
    packet = ContextBuilder().build("coach_qa", "继续解释", instrument="piano")
    envelope = build_request_envelope(packet, conversation_history=[{"role": "user", "content": "前一个问题"}, {"role": "assistant", "content": "前一个回答"}])
    data = envelope.to_dict()
    roles = [message["role"] for message in data["messages"]]
    assert roles[-3:] == ["user", "assistant", "user"]
    assert data["runtime_policy"]["tool_execution_enabled"] is False
    assert data["runtime_policy"]["autonomous_tool_execution_enabled"] is False


def test_provider_spec_documents_terminal_chat_but_api_runloop_remains_preview_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/llm/provider/spec").json()["spec"]
    assert spec["version"] == "v2_4_12"
    assert spec["terminal_chat"]["entrypoint"] == "python -m jammate_agent.cli.terminal_chat"
    assert spec["terminal_chat"]["tool_execution_enabled"] is False
    assert spec["guards"]["api_runloop_llm_calls_enabled"] is False
    assert spec["guards"]["terminal_chat_llm_calls_enabled_when_configured"] is True
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    assert "No real LLM network call from the API runloop preview in v2_4_12." in runtime_spec["non_goals"]


def test_terminal_chat_cli_has_console_script_and_no_engine_or_provider_sdk_imports() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'jammate-agent-chat = "jammate_agent.cli.terminal_chat:main"' in pyproject
    for rel in ["src/jammate_agent/cli/terminal_chat.py", "src/jammate_agent/core/llm_provider.py"]:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
        assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
