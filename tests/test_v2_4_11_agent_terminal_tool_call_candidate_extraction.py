from __future__ import annotations

import ast
from io import StringIO
from pathlib import Path

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import extract_tool_call_candidates

ROOT = Path(__file__).resolve().parents[1]


class CandidateProvider:
    def __init__(self, content: str) -> None:
        self.content = content

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
        return LLMProviderResult(ok=True, content=self.content, provider_name="fake", model="fake-model")


def test_extract_tool_call_candidates_from_fenced_json() -> None:
    result = extract_tool_call_candidates(
        '可以。\n```json\n{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}\n```'
    )
    assert result.ok is True
    assert result.to_dict()["extraction_version"] == "v2_4_11"
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.tool_name == "agent_playback_prepare"
    assert candidate.arguments == {"durationMinutes": 20}
    assert candidate.to_dict()["would_execute"] is False


def test_extract_tool_call_candidates_supports_tool_calls_list_and_dedupes() -> None:
    result = extract_tool_call_candidates(
        '{"tool_calls":[{"name":"agent_playback_prepare","arguments":{"durationMinutes":20}},'
        '{"name":"agent_playback_prepare","arguments":{"durationMinutes":20}},'
        '{"toolName":"chart_resolve","args":{"tune":"Blue Bossa"}}]}'
    )
    names = [candidate.tool_name for candidate in result.candidates]
    assert names == ["agent_playback_prepare", "chart_resolve"]


def test_extract_tool_call_candidates_ignores_plain_language() -> None:
    result = extract_tool_call_candidates("你可以考虑先生成伴奏，但这里没有显式 JSON tool call。")
    assert result.ok is True
    assert result.candidates == []
    assert result.to_dict()["candidate_count"] == 0


def test_terminal_chat_previews_extracted_allowed_candidate_without_execution() -> None:
    provider = CandidateProvider(
        '我建议先准备播放。\n```json\n{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}\n```'
    )
    session = TerminalChatSession(task_type="immediate_practice_playback", provider=provider)
    response = session.respond("练 Blue Bossa 20分钟")
    assert response["ok"] is True
    assert response["terminal_chat_version"] == "v2_4_11"
    assert response["tool_execution_enabled"] is False
    extraction = response["tool_call_candidate_extraction"]
    assert extraction["candidate_count"] == 1
    previews = response["tool_call_candidate_previews"]
    assert len(previews) == 1
    preview = previews[0]["preview"]
    assert preview["preview_version"] == "v2_4_11"
    assert preview["tool_name"] == "agent_playback_prepare"
    assert preview["allowed_by_context"] is True
    assert preview["would_execute"] is False
    assert "preview_does_not_dispatch_deterministic_workflows" in preview["blocking_reasons"]
    assert len(session.history) == 2


def test_terminal_chat_rejects_extracted_candidate_not_allowed_for_current_profile() -> None:
    provider = CandidateProvider('```json\n{"tool_name":"session_review_recommendation","arguments":{}}\n```')
    session = TerminalChatSession(task_type="immediate_practice_playback", provider=provider)
    response = session.respond("帮我练习")
    preview = response["tool_call_candidate_previews"][0]["preview"]
    assert preview["known_tool"] is True
    assert preview["allowed_by_context"] is False
    assert preview["status"] == "rejected_not_allowed_for_context"
    assert "tool_not_allowed_by_context_packet" in preview["blocking_reasons"]


def test_cli_once_prints_candidate_preview_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "jammate_agent.cli.terminal_chat.build_llm_provider_from_env",
        lambda: CandidateProvider('```json\n{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}\n```'),
    )
    out = StringIO()
    code = run_interactive_chat(["--task-type", "immediate_practice_playback", "--once", "练 Blue Bossa"], stdout=out)
    text = out.getvalue()
    assert code == 0
    assert "ToolCandidateExtraction> 1 candidate(s); execution disabled" in text
    assert "agent_playback_prepare: preview_only_blocked_by_execution_guard" in text
    assert "would_execute=False" in text


def test_help_mentions_candidate_extraction(monkeypatch) -> None:
    monkeypatch.setattr(
        "jammate_agent.cli.terminal_chat.build_llm_provider_from_env",
        lambda: CandidateProvider("普通回答"),
    )
    out = StringIO()
    code = run_interactive_chat(["--once", "/help"], stdout=out)
    assert code == 0
    assert "explicit JSON tool-call candidates" in out.getvalue()


def test_candidate_extraction_stays_agent_only_and_no_provider_sdk_imports() -> None:
    for rel in [
        "src/jammate_agent/cli/terminal_chat.py",
        "src/jammate_agent/core/tool_invocation.py",
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
