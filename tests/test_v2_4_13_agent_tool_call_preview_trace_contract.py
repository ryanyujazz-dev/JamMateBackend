from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION,
    build_tool_call_preview_trace_summary,
    extract_tool_call_candidates,
    preview_tool_invocation,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

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


def _single_trace(trace_dir: Path) -> dict:
    files = sorted(trace_dir.glob("trace_*.json"))
    assert len(files) == 1
    return json.loads(files[0].read_text(encoding="utf-8"))


def test_tool_call_preview_trace_summary_has_stable_guarded_contract() -> None:
    extraction = extract_tool_call_candidates('{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}')
    proposal = extraction.candidates[0].to_proposal(task_type="immediate_practice_playback")
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    summary = build_tool_call_preview_trace_summary(
        extraction=extraction,
        candidate_previews=[{"candidate": extraction.candidates[0].to_dict(), "preview": preview.to_dict(), "would_execute": False}],
        task_type="immediate_practice_playback",
    )

    assert summary["tool_call_preview_trace_contract_version"] == "v2_4_13"
    assert summary["candidate_count"] == 1
    assert summary["preview_count"] == 1
    assert summary["previewed_tool_names"] == ["agent_playback_prepare"]
    assert summary["preview_statuses"] == ["preview_only_blocked_by_execution_guard"]
    assert summary["all_previews_execution_blocked"] is True
    assert summary["execution_enabled"] is False
    assert summary["dispatch_enabled"] is False
    assert summary["engine_adapter_dispatch_enabled"] is False
    assert summary["preview_summaries"][0]["argument_keys"] == ["durationMinutes"]


def test_terminal_candidate_preview_trace_exports_contract_step_and_final_summary(tmp_path: Path) -> None:
    provider = CandidateProvider('```json\n{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}\n```')
    session = TerminalChatSession(
        task_type="immediate_practice_playback",
        provider=provider,
        trace_logger=TraceLogger(JsonTraceStore(tmp_path)),
    )
    response = session.respond("练 Blue Bossa 20分钟")

    assert response["tool_call_preview_trace_contract_version"] == TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION
    assert response["tool_call_preview_trace_summary"]["preview_count"] == 1
    assert response["tool_call_preview_trace_summary"]["all_previews_execution_blocked"] is True

    trace = _single_trace(tmp_path)
    assert trace["validation_result"] == "passed"
    step_names = [step["name"] for step in trace["steps"]]
    assert "terminal_tool_call_candidates_extracted" in step_names
    assert "terminal_tool_call_candidates_previewed" in step_names
    assert "terminal_tool_call_preview_trace_summary_recorded" in step_names
    final = trace["final_response_summary"]
    assert final["tool_call_preview_trace_contract_version"] == "v2_4_13"
    assert final["tool_call_preview_trace_summary"]["candidate_count"] == 1
    assert final["tool_call_preview_trace_summary"]["preview_summaries"][0]["would_execute"] is False


def test_terminal_no_candidate_trace_still_records_zero_count_contract(tmp_path: Path) -> None:
    session = TerminalChatSession(
        task_type="coach_qa",
        provider=CandidateProvider("普通回答，没有 JSON tool call。"),
        trace_logger=TraceLogger(JsonTraceStore(tmp_path)),
    )
    response = session.respond("解释一下 walking bass")
    summary = response["tool_call_preview_trace_summary"]
    assert summary["tool_call_preview_trace_contract_version"] == "v2_4_13"
    assert summary["candidate_count"] == 0
    assert summary["preview_count"] == 0
    assert summary["all_previews_execution_blocked"] is True

    trace = _single_trace(tmp_path)
    step_names = [step["name"] for step in trace["steps"]]
    assert "terminal_tool_call_preview_trace_summary_recorded" in step_names
    assert trace["final_response_summary"]["tool_call_candidate_preview_count"] == 0


def test_trace_api_and_runtime_spec_expose_tool_call_preview_trace_boundary() -> None:
    contract = trace_api_contract()
    assert contract["tool_call_preview_trace_contract"]["version"] == "v2_4_13"
    assert contract["tool_call_preview_trace_contract"]["execution_enabled"] is False

    client = TestClient(app)
    trace_spec = client.get("/agent/traces/spec").json()["spec"]
    assert trace_spec["tool_call_preview_trace_contract"]["summary_field"] == "final_response_summary.tool_call_preview_trace_summary"

    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["tool_call_preview_trace_boundary"]
    assert boundary["version"] == "v2_4_13"
    assert boundary["guards"]["trace_contract_dispatches_workflows"] is False
    assert boundary["summary_field"] == "tool_call_preview_trace_summary"


def test_docs_and_harness_mention_v2_4_13_trace_contract() -> None:
    assert "v2_4_13_agent_tool_call_preview_trace_contract" in (ROOT / "docs/DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
    assert "AGENT_TOOL_CALL_PREVIEW_TRACE_CONTRACT_V2_4_13" in (ROOT / "docs/CHANGELOG.md").read_text(encoding="utf-8")
    assert "tool-call preview trace contract" in (ROOT / "agent.md").read_text(encoding="utf-8")


def test_tool_call_preview_trace_contract_stays_agent_only() -> None:
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
