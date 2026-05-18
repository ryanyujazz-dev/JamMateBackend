from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_tool_execution_confirmation_summary,
    confirm_tool_invocation,
    tool_execution_confirmation_contract,
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
            "guard_reason": "fake provider for confirmation tests",
        }

    def generate(self, envelope):
        return LLMProviderResult(ok=True, content=self.content, provider_name="fake", model="fake-model")


def _preview(tool_name: str = "agent_playback_prepare", arguments: dict | None = None, allowed_tools: list[str] | None = None):
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments or {"durationMinutes": 20},
        task_type="immediate_practice_playback",
    )
    return preview_tool_invocation(proposal, allowed_tools=allowed_tools or ["chart_resolve", "agent_playback_prepare"])


def test_confirmation_envelope_from_preview_is_pending_but_execution_disabled() -> None:
    preview = _preview()
    envelope = build_confirmation_envelope(preview, proposal_id="proposal_test")
    payload = envelope.to_dict()

    assert payload["confirmation_contract_version"] == TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION
    assert payload["proposal_id"] == "proposal_test"
    assert payload["tool_name"] == "agent_playback_prepare"
    assert payload["confirmation_status"] == "pending"
    assert payload["requires_user_confirmation"] is True
    assert payload["user_approved"] is False
    assert payload["would_execute_after_confirmation"] is False
    assert payload["execution_still_disabled"] is True
    assert "MIDI asset" in payload["risk_summary"]


def test_confirm_and_reject_record_decision_without_execution() -> None:
    envelope = build_confirmation_envelope(_preview())

    approved = confirm_tool_invocation(envelope, user_approved=True).to_dict()
    assert approved["ok"] is True
    assert approved["status"] == "approved_execution_still_disabled"
    assert approved["user_approved"] is True
    assert approved["would_execute"] is False
    assert approved["execution_still_disabled"] is True
    assert approved["next_stage_required"] == "ToolExecutorBoundary"

    rejected = confirm_tool_invocation(envelope, user_approved=False).to_dict()
    assert rejected["ok"] is True
    assert rejected["status"] == "rejected_by_user"
    assert rejected["user_approved"] is False
    assert rejected["would_execute"] is False


def test_unknown_or_not_allowed_tool_cannot_enter_confirmable_state() -> None:
    unknown = build_confirmation_envelope(_preview(tool_name="unknown_tool"))
    assert unknown.confirmable is False
    assert unknown.confirmation_status == "not_confirmable"
    assert unknown.requires_user_confirmation is False
    assert confirm_tool_invocation(unknown, user_approved=True).status == "blocked_not_confirmable"

    not_allowed = build_confirmation_envelope(_preview(allowed_tools=["chart_resolve"]))
    assert not_allowed.confirmable is False
    assert not_allowed.confirmation_status == "not_confirmable"
    assert "tool_not_allowed_by_context_packet" in not_allowed.blocking_reasons


def test_confirmation_redacts_sensitive_argument_keys() -> None:
    preview = _preview(arguments={"durationMinutes": 20, "apiKey": "sk-secret", "nested": {"access_token": "tok-value"}})
    envelope = build_confirmation_envelope(preview)
    args = envelope.to_dict()["arguments_preview"]
    assert args["apiKey"] == "[REDACTED]"
    assert args["nested"]["access_token"] == "[REDACTED]"
    assert "sk-secret" not in json.dumps(envelope.to_dict())
    assert "tok-value" not in json.dumps(envelope.to_dict())


def test_terminal_preview_pending_confirm_and_reject_commands_trace_results(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))

    preview_response = session.preview_tool_call("agent_playback_prepare", {"durationMinutes": 20})
    assert preview_response["confirmation"]["confirmation_status"] == "pending"
    assert session.pending_confirmation_status()["has_pending_confirmation"] is True

    confirm_response = session.confirm_pending_tool()
    assert confirm_response["result"]["status"] == "approved_execution_still_disabled"
    assert confirm_response["result"]["would_execute"] is False
    assert session.pending_confirmation_status()["has_pending_confirmation"] is False

    no_pending = session.reject_pending_tool()
    assert no_pending["error_code"] == "NO_PENDING_CONFIRMATION"

    traces = sorted(tmp_path.glob("trace_*.json"))
    assert len(traces) == 2
    trace_payloads = [json.loads(path.read_text(encoding="utf-8")) for path in traces]
    confirm_trace = next(
        payload for payload in trace_payloads
        if "terminal_tool_confirmation_user_approved" in [step["name"] for step in payload["steps"]]
    )
    step_names = [step["name"] for step in confirm_trace["steps"]]
    assert "terminal_tool_confirmation_user_approved" in step_names
    final = confirm_trace["final_response_summary"]
    assert final["tool_execution_confirmation_summary"]["user_approved"] is True
    assert final["tool_execution_confirmation_summary"]["execution_still_disabled"] is True


def test_terminal_llm_candidate_creates_pending_confirmation_and_trace(tmp_path: Path) -> None:
    provider = CandidateProvider('```json\n{"tool_name":"agent_playback_prepare","arguments":{"durationMinutes":20}}\n```')
    session = TerminalChatSession(
        task_type="immediate_practice_playback",
        provider=provider,
        trace_logger=TraceLogger(JsonTraceStore(tmp_path)),
    )
    response = session.respond("练 Blue Bossa 20 分钟")

    assert response["tool_execution_confirmation_contract_version"] == "v2_6_2"
    assert response["tool_execution_confirmation_summary"]["has_pending_confirmation"] is True
    assert response["tool_execution_confirmation_envelopes"][0]["confirmation_status"] == "pending"
    assert response["tool_execution_confirmation_envelopes"][0]["would_execute_after_confirmation"] is False

    trace = json.loads(next(tmp_path.glob("trace_*.json")).read_text(encoding="utf-8"))
    step_names = [step["name"] for step in trace["steps"]]
    assert "terminal_tool_confirmation_envelope_created" in step_names
    assert "terminal_tool_execution_confirmation_summary_recorded" in step_names
    assert trace["final_response_summary"]["tool_execution_confirmation_summary"]["requires_executor_boundary"] is True


def test_confirmation_contract_and_api_routes_are_preview_only() -> None:
    spec = tool_execution_confirmation_contract()
    assert spec["version"] == "v2_6_2"
    assert spec["execution_status"]["tool_execution_enabled"] is False
    assert spec["execution_status"]["execution_still_disabled"] is True
    assert spec["guards"]["confirmation_calls_engine_adapter"] is False

    client = TestClient(app)
    route_spec = client.get("/agent/tools/confirmation/spec").json()["spec"]
    assert route_spec["spec_route"] == "GET /agent/tools/confirmation/spec"

    response = client.post(
        "/agent/tools/confirmation/preview",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"durationMinutes": 20},
        },
    ).json()
    assert response["ok"] is True
    assert response["confirmation"]["confirmation_status"] == "pending"
    assert response["confirmation"]["execution_still_disabled"] is True


def test_trace_and_runtime_specs_expose_confirmation_boundary() -> None:
    trace_spec = trace_api_contract()
    assert trace_spec["tool_execution_confirmation_trace_contract"]["version"] == "v2_6_2"
    assert trace_spec["tool_execution_confirmation_trace_contract"]["execution_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["tool_execution_confirmation_boundary"]
    assert boundary["version"] == "v2_6_2"
    assert boundary["execution_status"]["deterministic_workflow_dispatch_enabled"] is False


def test_confirmation_summary_none_and_pending_shapes() -> None:
    none_summary = build_tool_execution_confirmation_summary()
    assert none_summary["confirmation_status"] == "none"
    assert none_summary["has_pending_confirmation"] is False
    assert none_summary["execution_still_disabled"] is True

    envelope = build_confirmation_envelope(_preview())
    pending_summary = build_tool_execution_confirmation_summary(confirmation=envelope)
    assert pending_summary["confirmation_status"] == "pending"
    assert pending_summary["has_pending_confirmation"] is True
    assert pending_summary["confirmed_tool_name"] == "agent_playback_prepare"


def test_confirmation_gate_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
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


def test_agent_track_docs_record_v2_6_2_without_shared_doc_dependency() -> None:
    plan = (ROOT / "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs/CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    detail_doc = (ROOT / "docs/AGENT_TOOL_EXECUTION_CONFIRMATION_GATE_V2_6_2.md").read_text(encoding="utf-8")
    assert "v2_6_2_agent_tool_execution_confirmation_gate" in plan
    assert "v2_6_2 — Agent Tool Execution Confirmation Gate" in changelog
    assert "不执行工具" in detail_doc
