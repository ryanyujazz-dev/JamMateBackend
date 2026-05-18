from __future__ import annotations

import ast
from io import StringIO
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, _parse_tool_preview_command, run_interactive_chat
from jammate_agent.core.llm_provider import LLMProviderResult

ROOT = Path(__file__).resolve().parents[1]


class FailingProvider:
    def status(self) -> dict:
        return {
            "provider_name": "fake",
            "model": "fake-model",
            "terminal_chat_enabled": True,
            "llm_calls_enabled": True,
            "tool_execution_enabled": False,
            "guard_reason": "fake provider for tests",
        }

    def generate(self, envelope):  # pragma: no cover - this must not be called by /tool-preview.
        raise AssertionError("/tool-preview must not call the LLM provider")


class EchoProvider:
    def status(self) -> dict:
        return {
            "provider_name": "fake",
            "model": "fake-model",
            "terminal_chat_enabled": True,
            "llm_calls_enabled": True,
            "tool_execution_enabled": False,
            "guard_reason": "fake provider for tests",
        }

    def generate(self, envelope):
        return LLMProviderResult(ok=True, content="normal chat", provider_name="fake", model="fake-model")


def test_terminal_session_tool_preview_reuses_context_allow_list_without_execution() -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", provider=FailingProvider())
    response = session.preview_tool_call(
        "agent_playback_prepare",
        {"userInput": "练 Blue Bossa 20分钟", "durationMinutes": 20},
    )
    assert response["terminal_chat_version"] == "v2_4_11"
    assert response["command"] == "/tool-preview"
    assert response["tool_execution_enabled"] is False
    assert response["would_execute"] is False
    preview = response["preview"]
    assert preview["preview_version"] == "v2_4_11"
    assert preview["tool_name"] == "agent_playback_prepare"
    assert preview["known_tool"] is True
    assert preview["allowed_by_context"] is True
    assert preview["would_execute"] is False
    assert "preview_does_not_dispatch_deterministic_workflows" in preview["blocking_reasons"]
    assert response["context_packet_summary"]["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]


def test_terminal_tool_preview_rejects_tool_not_in_current_task_allow_list() -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", provider=FailingProvider())
    response = session.preview_tool_call("agent_practice_plan", {})
    preview = response["preview"]
    assert response["ok"] is False
    assert preview["status"] == "rejected_not_allowed_for_context"
    assert preview["known_tool"] is True
    assert preview["allowed_by_context"] is False
    assert "tool_not_allowed_by_context_packet" in preview["blocking_reasons"]


def test_tool_preview_command_parser_accepts_json_object_arguments() -> None:
    parsed = _parse_tool_preview_command('/tool-preview agent_playback_prepare {"durationMinutes": 20}')
    assert parsed == {"ok": True, "tool_name": "agent_playback_prepare", "arguments": {"durationMinutes": 20}}


def test_tool_preview_command_parser_rejects_missing_or_invalid_arguments() -> None:
    missing = _parse_tool_preview_command("/tool-preview")
    assert missing["ok"] is False
    assert missing["error_code"] == "TOOL_PREVIEW_USAGE"
    invalid_json = _parse_tool_preview_command("/tool-preview agent_playback_prepare not-json")
    assert invalid_json["ok"] is False
    assert invalid_json["error_code"] == "TOOL_PREVIEW_INVALID_JSON"
    not_object = _parse_tool_preview_command("/tool-preview agent_playback_prepare [1, 2]")
    assert not_object["ok"] is False
    assert not_object["error_code"] == "TOOL_PREVIEW_ARGUMENTS_NOT_OBJECT"


def test_cli_once_tool_preview_prints_result_without_provider_call(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: FailingProvider())
    out = StringIO()
    code = run_interactive_chat(
        ["--task-type", "immediate_practice_playback", "--once", '/tool-preview agent_playback_prepare {"durationMinutes": 20}'],
        stdout=out,
    )
    text = out.getvalue()
    assert code == 0
    assert "ToolPreview> agent_playback_prepare: preview_only_blocked_by_execution_guard" in text
    assert "would_execute: False" in text
    assert "preview_does_not_dispatch_deterministic_workflows" in text


def test_interactive_tools_and_help_commands_are_preview_only(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: FailingProvider())
    stdin = StringIO("/help\n/tools\n/exit\n")
    out = StringIO()
    code = run_interactive_chat(["--task-type", "coach_qa"], stdin=stdin, stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "/tool-preview <tool_name>" in text
    assert "Allowed tools for this task:" in text
    assert "agent_practice_plan" in text
    assert "agent_playback_prepare" in text
    assert "Tool execution remains disabled" in text


def test_normal_once_chat_still_uses_provider_and_history() -> None:
    session = TerminalChatSession(task_type="coach_qa", provider=EchoProvider())
    response = session.respond("解释一下 guide tones")
    assert response["ok"] is True
    assert response["terminal_chat_version"] == "v2_4_11"
    assert response["content"] == "normal chat"
    assert len(session.history) == 2


def test_terminal_chat_cli_stays_agent_only_and_no_provider_sdk_imports() -> None:
    path = ROOT / "src" / "jammate_agent" / "cli" / "terminal_chat.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
