from __future__ import annotations

import ast
import json
from io import StringIO
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.trace import JsonTraceStore, TraceLogger

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
        return LLMProviderResult(ok=True, content="traced chat", provider_name="fake", model="fake-model")


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

    def generate(self, envelope):  # pragma: no cover - /tool-preview must never call provider.
        raise AssertionError("tool preview trace export must not call provider")


def _read_single_trace(trace_dir: Path) -> dict:
    traces = sorted(trace_dir.glob("trace_*.json"))
    assert len(traces) == 1
    return json.loads(traces[0].read_text(encoding="utf-8"))


def test_terminal_chat_trace_export_records_context_envelope_and_provider_response(tmp_path: Path) -> None:
    trace_logger = TraceLogger(JsonTraceStore(tmp_path))
    session = TerminalChatSession(task_type="coach_qa", provider=EchoProvider(), trace_logger=trace_logger)
    response = session.respond("解释一下 guide tones")

    assert response["ok"] is True
    assert response["terminal_chat_version"] == "v2_4_12"
    assert response["trace_id"].startswith("trace_")
    assert Path(response["trace_path"]).exists()

    trace = _read_single_trace(tmp_path)
    assert trace["task_type"] == "terminal_chat"
    assert trace["validation_result"] == "passed"
    assert trace["context_packet_summary"]["terminal_chat_version"] == "v2_4_12"
    step_names = [step["name"] for step in trace["steps"]]
    assert "terminal_context_packet_built" in step_names
    assert "terminal_request_envelope_built" in step_names
    assert "terminal_provider_response_received" in step_names
    assert trace["final_response_summary"]["tool_execution_enabled"] is False


def test_terminal_tool_preview_trace_export_is_validation_only(tmp_path: Path) -> None:
    trace_logger = TraceLogger(JsonTraceStore(tmp_path))
    session = TerminalChatSession(task_type="immediate_practice_playback", provider=FailingProvider(), trace_logger=trace_logger)
    response = session.preview_tool_call("agent_playback_prepare", {"durationMinutes": 20})

    assert response["terminal_chat_version"] == "v2_4_12"
    assert response["would_execute"] is False
    assert response["trace_id"].startswith("trace_")
    preview = response["preview"]
    assert preview["would_execute"] is False
    assert "preview_does_not_dispatch_deterministic_workflows" in preview["blocking_reasons"]

    trace = _read_single_trace(tmp_path)
    assert trace["task_type"] == "terminal_tool_preview"
    assert trace["validation_result"] == "previewed"
    step_names = [step["name"] for step in trace["steps"]]
    assert "terminal_tool_invocation_previewed" in step_names
    assert trace["final_response_summary"] == {
        "ok": True,
        "tool_name": "agent_playback_prepare",
        "status": "preview_only_blocked_by_execution_guard",
        "would_execute": False,
    }


def test_cli_once_trace_dir_prints_trace_export_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: EchoProvider())
    out = StringIO()
    code = run_interactive_chat(["--trace-dir", str(tmp_path), "--once", "hello"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "JamMate> traced chat" in text
    assert "TraceExport> trace_id: trace_" in text
    assert "path:" in text
    assert len(list(tmp_path.glob("trace_*.json"))) == 1


def test_cli_trace_commands_report_disabled_and_recent_traces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: EchoProvider())
    disabled_out = StringIO()
    disabled_code = run_interactive_chat(["--once", "/trace"], stdout=disabled_out)
    assert disabled_code == 0
    assert "Trace export is disabled" in disabled_out.getvalue()

    stdin = StringIO("hello\n/trace\n/traces\n/exit\n")
    out = StringIO()
    code = run_interactive_chat(["--trace-dir", str(tmp_path)], stdin=stdin, stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "Last trace: trace_" in text
    assert "Recent terminal traces:" in text


def test_terminal_help_mentions_trace_export(monkeypatch) -> None:
    monkeypatch.setattr("jammate_agent.cli.terminal_chat.build_llm_provider_from_env", lambda: EchoProvider())
    out = StringIO()
    code = run_interactive_chat(["--once", "/help"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "--trace-dir <dir>" in text
    assert "/trace" in text
    assert "/traces" in text


def test_terminal_trace_export_stays_agent_only_and_no_engine_imports() -> None:
    path = ROOT / "src" / "jammate_agent" / "cli" / "terminal_chat.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert "jammate_agent.core.trace" in imported
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
