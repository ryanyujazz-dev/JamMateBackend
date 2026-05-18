from __future__ import annotations

import ast
from io import StringIO
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.llm_provider import LLMProviderResult

ROOT = Path(__file__).resolve().parents[1]


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
        return LLMProviderResult(ok=True, content="context-controlled chat", provider_name="fake", model="fake-model")


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

    def generate(self, envelope):  # pragma: no cover - context controls must never call provider.
        raise AssertionError("context/profile/session controls must not call provider")


def test_session_context_preview_and_profile_manifest_do_not_call_provider() -> None:
    session = TerminalChatSession(task_type="coach_qa", instrument="piano", provider=FailingProvider())
    context = session.context_packet_preview()
    assert context["ok"] is True
    assert context["terminal_chat_version"] == "v2_4_13"
    assert context["task_type"] == "coach_qa"
    assert context["instrument"] == "piano"
    assert context["provider_call_enabled"] is False
    assert context["tool_execution_enabled"] is False
    assert context["summary"]["allowed_tools"] == ["agent_practice_plan", "agent_playback_prepare"]

    manifest = session.profile_manifest()
    assert manifest["terminal_chat_version"] == "v2_4_13"
    assert manifest["current_task_type"] == "coach_qa"
    assert "immediate_practice_playback" in manifest["profiles"]
    assert manifest["profiles"]["coach_qa"]["llm_required"] is True


def test_switch_task_type_clears_local_history_and_changes_allowed_tools() -> None:
    session = TerminalChatSession(task_type="coach_qa", provider=EchoProvider())
    response = session.respond("hello")
    assert response["ok"] is True
    assert len(session.history) == 2

    switched = session.switch_task_type("immediate_practice_playback")
    assert switched["ok"] is True
    assert switched["previous_task_type"] == "coach_qa"
    assert switched["task_type"] == "immediate_practice_playback"
    assert switched["history_cleared"] is True
    assert switched["history_messages_cleared"] == 2
    assert session.history == []

    context = session.context_packet_preview()
    assert context["summary"]["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]


def test_unknown_task_type_is_rejected_with_available_profiles() -> None:
    session = TerminalChatSession(task_type="coach_qa", provider=FailingProvider())
    result = session.switch_task_type("unknown_task")
    assert result["ok"] is False
    assert result["error_code"] == "UNKNOWN_CONTEXT_PROFILE"
    assert result["task_type"] == "coach_qa"
    assert "coach_qa" in result["available_task_types"]


def test_instrument_and_reset_controls_are_session_only() -> None:
    session = TerminalChatSession(task_type="coach_qa", provider=EchoProvider())
    session.respond("hello")
    instrument = session.set_instrument("guitar")
    assert instrument == {
        "ok": True,
        "terminal_chat_version": "v2_4_13",
        "command": "/instrument",
        "previous_instrument": "piano",
        "instrument": "guitar",
    }
    summary = session.session_summary()
    assert summary["instrument"] == "guitar"
    assert summary["history_message_count"] == 2
    assert summary["tool_execution_enabled"] is False

    reset = session.reset_session()
    assert reset["ok"] is True
    assert reset["history_messages_cleared"] == 2
    assert session.history == []


def test_cli_context_control_commands_are_printed_and_do_not_call_provider(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: FailingProvider())
    stdin = StringIO("/session\n/context\n/profiles\n/profile immediate_practice_playback\n/tools\n/instrument bass\n/reset\n/exit\n")
    out = StringIO()
    code = run_interactive_chat(["--task-type", "coach_qa"], stdin=stdin, stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "Session>" in text
    assert "ContextPacket>" in text
    assert "ContextProfiles> current_task_type: coach_qa" in text
    assert "TaskType> coach_qa -> immediate_practice_playback" in text
    assert "Allowed tools for this task:" in text
    assert "chart_resolve" in text
    assert "Instrument> piano -> bass" in text
    assert "SessionReset>" in text
    assert "provider_call_enabled: False" in text
    assert "tool_execution_enabled: False" in text


def test_cli_context_full_outputs_json(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: FailingProvider())
    out = StringIO()
    code = run_interactive_chat(["--once", "/context full"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert '"terminal_chat_version": "v2_4_13"' in text
    assert '"context_packet"' in text
    assert '"provider_call_enabled": false' in text


def test_cli_help_mentions_context_controls(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: FailingProvider())
    out = StringIO()
    code = run_interactive_chat(["--once", "/help"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "/session" in text
    assert "/context [full|--full|json|--json]" in text
    assert "/profiles" in text
    assert "/profile [task_type]" in text
    assert "/task-type [task_type]" in text
    assert "/instrument [instrument]" in text
    assert "/reset" in text
    assert "Context controls rebuild preview packets only" in text


def test_terminal_context_controls_stay_agent_only_and_no_provider_sdk_imports() -> None:
    path = ROOT / "src" / "jammate_agent" / "cli" / "terminal_chat.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert "jammate_agent.core.context" in imported
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
