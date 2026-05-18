from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jammate_agent.cli import terminal_chat
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import (
    LLMProviderConfig,
    OpenAICompatibleChatProvider,
    _normalize_messages_for_chat_completions,
    build_request_envelope,
)


def test_chat_completions_payload_downgrades_developer_role_for_compatible_providers() -> None:
    packet = ContextBuilder().build("coach_qa", "今天该练什么？", available_minutes=25)
    envelope = build_request_envelope(
        packet,
        conversation_history=[
            {"role": "user", "content": "昨天练了 Blue Bossa"},
            {"role": "assistant", "content": "今天可以复盘 comping"},
        ],
    )

    provider_messages = _normalize_messages_for_chat_completions(envelope.messages, max_chars=12000)
    roles = [message["role"] for message in provider_messages]

    assert "developer" not in roles
    assert "context" not in roles
    assert roles[0] == "system"
    assert set(roles).issubset({"system", "user", "assistant"})
    assert "System product context" in provider_messages[0]["content"]
    assert provider_messages[-1] == {"role": "user", "content": "今天该练什么？"}


def test_openai_compatible_provider_sends_normalized_roles(monkeypatch) -> None:
    packet = ContextBuilder().build("coach_qa", "今天该练什么？")
    envelope = build_request_envelope(packet)
    captured_payload: dict[str, Any] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "好的，今天建议练 comping。"}}]}).encode("utf-8")

    def fake_urlopen(request, timeout: int = 30):  # noqa: ANN001
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleChatProvider(
        LLMProviderConfig(
            provider_name="openai_compatible",
            model="compat-model",
            api_key_configured=True,
            network_calls_enabled=True,
            api_key_value="fake-secret",
        )
    )

    result = provider.generate(envelope)

    assert result.ok is True
    assert result.content == "好的，今天建议练 comping。"
    roles = [message["role"] for message in captured_payload["messages"]]
    assert "developer" not in roles
    assert set(roles).issubset({"system", "user", "assistant"})


def test_module_main_forwards_sys_argv_to_setup_doctor_commands(monkeypatch, tmp_path: Path, capsys) -> None:  # noqa: ANN001
    config_path = tmp_path / "agent.env"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "jammate-agent-chat",
            "setup",
            "--config-file",
            str(config_path),
            "--provider",
            "openai_compatible",
            "--model",
            "compat-model",
            "--api-key",
            "fake-secret",
            "--yes",
        ],
    )

    assert terminal_chat.main() == 0
    out = capsys.readouterr().out
    assert "LLMConfigSetup> saved" in out
    assert "compat-model" in out
    assert "fake-secret" not in out
    assert config_path.exists()
