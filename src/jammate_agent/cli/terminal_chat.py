from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, TextIO

from jammate_agent.core.context import CONTEXT_PROFILES, ContextBuilder
from jammate_agent.core.llm_provider import (
    LLM_CONFIG_FILE_ENV_VAR,
    LLMProvider,
    LLMProviderConfig,
    build_llm_provider_from_env,
    build_request_envelope,
    default_user_llm_config_path,
    write_llm_config_file,
)
from jammate_agent.core.tool_invocation import (
    TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
    TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION,
    TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
    TOOL_EXECUTOR_BOUNDARY_VERSION,
    ToolExecutionConfirmationEnvelope,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_tool_call_preview_trace_summary,
    build_tool_execution_confirmation_summary,
    build_tool_executor_summary,
    confirm_tool_invocation,
    execute_tool_dry_run,
    extract_tool_call_candidates,
    preview_tool_invocation,
)
from jammate_agent.core.trace import AgentTrace, JsonTraceStore, TraceLogger

TERMINAL_CHAT_VERSION = "v2_4_13"


@dataclass
class TerminalChatSession:
    """Interactive terminal chat session for provider-boundary debugging.

    The session can call a configured LLM provider, but it does not execute Agent
    tools. Every turn rebuilds a task-scoped ContextPacket so the CLI exercises
    the same context/runtime boundary used by API previews.

    `/tool-preview` is an explicit terminal command that validates a proposed
    tool call against the same ContextPacket allow-list and preview contract.
    It never dispatches deterministic workflows or engine adapters.

    v2_4_10 adds explicit terminal context/session controls so developers can
    switch task profiles, inspect ContextPacket summaries, reset local chat
    history, and change instrument hints without restarting the CLI.

    v2_4_13 additionally scans successful assistant text for explicit JSON
    tool-call candidates and sends them through the preview contract. Extracted
    candidates never execute tools or engine workflows.

    v2_4_13 adds setup/doctor configuration helpers and local config-file
    loading for terminal LLM use. These helpers do not change tool execution
    policy and do not expose API keys in status, trace, or response payloads.

    v2_6_3 adds a dry-run/no-op ToolExecutor boundary after explicit user
    confirmation. The dry-run proves execution request/result shape only and
    still never dispatches workflows, routes, or engine adapters.
    """

    task_type: str = "coach_qa"
    instrument: str = "piano"
    provider: LLMProvider = field(default_factory=build_llm_provider_from_env)
    context_builder: ContextBuilder = field(default_factory=ContextBuilder)
    history: list[dict[str, str]] = field(default_factory=list)
    trace_logger: TraceLogger | None = None
    last_trace_id: str | None = None
    last_trace_path: str | None = None
    pending_confirmation: ToolExecutionConfirmationEnvelope | None = None

    def provider_status(self) -> dict:
        return self.provider.status()

    def respond(self, user_input: str) -> dict:
        trace = self._start_trace("terminal_chat", user_input)
        packet = self.context_builder.build(
            self.task_type,
            user_input,
            instrument=self.instrument,
            client_context={"entry_point": "terminal_chat_cli"},
        )
        self._add_trace_step(trace, "terminal_context_packet_built", packet.summary())
        envelope = build_request_envelope(packet, conversation_history=self.history)
        self._add_trace_step(
            trace,
            "terminal_request_envelope_built",
            {
                "message_count": len(envelope.messages),
                "allowed_tools": list(envelope.allowed_tools),
                "output_schema": envelope.output_contract.get("schema"),
                "tool_execution_enabled": False,
            },
        )
        result = self.provider.generate(envelope)
        response = result.to_dict()
        response["terminal_chat_version"] = TERMINAL_CHAT_VERSION
        response["task_type"] = packet.task_type
        response["tool_execution_enabled"] = False
        response["allowed_tools"] = list(packet.allowed_tools)
        response["context_runtime_version"] = packet.context_runtime_version
        self._add_trace_step(
            trace,
            "terminal_provider_response_received",
            {
                "ok": result.ok,
                "provider_name": result.provider_name,
                "model": result.model,
                "error_code": result.error_code,
                "content_chars": len(result.content or ""),
                "tool_execution_enabled": False,
            },
        )
        extraction_payload: dict[str, Any] = {
            "extraction_version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
            "ok": True,
            "candidate_count": 0,
            "candidates": [],
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }
        candidate_previews: list[dict[str, Any]] = []
        confirmation_envelopes: list[dict[str, Any]] = []
        extraction = extract_tool_call_candidates(None)
        if result.ok and result.content:
            extraction = extract_tool_call_candidates(result.content)
            extraction_payload = extraction.to_dict()
            self._add_trace_step(trace, "terminal_tool_call_candidates_extracted", extraction_payload)
            for candidate in extraction.candidates:
                proposal = candidate.to_proposal(
                    task_type=packet.task_type,
                    user_input=user_input,
                    client_context={
                        "entry_point": "terminal_chat_cli",
                        "source": "assistant_text_candidate_extraction",
                    },
                )
                preview = preview_tool_invocation(proposal, allowed_tools=packet.allowed_tools)
                preview_payload = preview.to_dict()
                confirmation_payload: dict[str, Any] | None = None
                if preview.ok:
                    confirmation = build_confirmation_envelope(preview)
                    self.pending_confirmation = confirmation
                    confirmation_payload = confirmation.to_dict()
                    confirmation_envelopes.append(confirmation_payload)
                    self._add_trace_step(trace, "terminal_tool_confirmation_envelope_created", confirmation_payload)
                candidate_previews.append({
                    "candidate": candidate.to_dict(),
                    "preview": preview_payload,
                    "confirmation": confirmation_payload,
                    "would_execute": False,
                })
            if candidate_previews:
                self._add_trace_step(
                    trace,
                    "terminal_tool_call_candidates_previewed",
                    {
                        "candidate_preview_count": len(candidate_previews),
                        "previews": candidate_previews,
                        "tool_execution_enabled": False,
                    },
                )
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": result.content})
        trace_summary = build_tool_call_preview_trace_summary(
            extraction=extraction,
            candidate_previews=candidate_previews,
            task_type=packet.task_type,
            source="terminal_chat_cli",
        )
        confirmation_summary = build_tool_execution_confirmation_summary(
            confirmation=self.pending_confirmation,
            source="terminal_chat_cli",
        )
        self._add_trace_step(trace, "terminal_tool_call_preview_trace_summary_recorded", trace_summary)
        if confirmation_envelopes:
            self._add_trace_step(
                trace,
                "terminal_tool_execution_confirmation_summary_recorded",
                confirmation_summary,
            )
        response["tool_call_candidate_extraction_version"] = TOOL_CALL_CANDIDATE_EXTRACTION_VERSION
        response["tool_call_preview_trace_contract_version"] = TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION
        response["tool_call_candidate_extraction"] = extraction_payload
        response["tool_call_candidate_previews"] = candidate_previews
        response["tool_call_candidate_preview_count"] = len(candidate_previews)
        response["tool_call_preview_trace_summary"] = trace_summary
        response["tool_execution_confirmation_contract_version"] = TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION
        response["tool_execution_confirmation_envelopes"] = confirmation_envelopes
        response["tool_execution_confirmation_summary"] = confirmation_summary
        self._finish_trace(
            trace,
            "passed" if result.ok else "guarded",
            {
                "ok": result.ok,
                "task_type": packet.task_type,
                "terminal_chat_version": TERMINAL_CHAT_VERSION,
                "tool_execution_enabled": False,
                "tool_call_preview_trace_contract_version": TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION,
                "tool_call_candidate_count": extraction_payload.get("candidate_count", 0),
                "tool_call_candidate_preview_count": len(candidate_previews),
                "tool_call_preview_trace_summary": trace_summary,
                "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
                "tool_execution_confirmation_summary": confirmation_summary,
            },
        )
        response["trace_id"] = self.last_trace_id
        response["trace_path"] = self.last_trace_path
        return response

    def preview_tool_call(self, tool_name: str, arguments: dict[str, Any] | None = None, user_input: str | None = None) -> dict:
        """Preview a proposed tool call from the terminal without executing it."""

        tool_arguments = arguments or {}
        prompt = user_input or f"Terminal tool preview: {tool_name}"
        trace = self._start_trace("terminal_tool_preview", prompt)
        packet = self.context_builder.build(
            self.task_type,
            prompt,
            instrument=self.instrument,
            client_context={"entry_point": "terminal_chat_cli", "terminal_command": "/tool-preview"},
        )
        self._add_trace_step(trace, "terminal_context_packet_built", packet.summary())
        proposal = ToolInvocationProposal(
            tool_name=tool_name,
            arguments=tool_arguments,
            task_type=packet.task_type,
            user_input=prompt,
            client_context={"entry_point": "terminal_chat_cli", "terminal_command": "/tool-preview"},
        )
        preview = preview_tool_invocation(proposal, allowed_tools=packet.allowed_tools)
        preview_payload = preview.to_dict()
        self._add_trace_step(trace, "terminal_tool_invocation_previewed", preview_payload)
        confirmation_payload: dict[str, Any] | None = None
        confirmation_summary = build_tool_execution_confirmation_summary(source="terminal_chat_cli")
        if preview.ok:
            confirmation = build_confirmation_envelope(preview)
            self.pending_confirmation = confirmation
            confirmation_payload = confirmation.to_dict()
            confirmation_summary = build_tool_execution_confirmation_summary(confirmation=confirmation, source="terminal_chat_cli")
            self._add_trace_step(trace, "terminal_tool_confirmation_envelope_created", confirmation_payload)
            self._add_trace_step(trace, "terminal_tool_execution_confirmation_summary_recorded", confirmation_summary)
        self._finish_trace(
            trace,
            "previewed" if preview.ok else "blocked",
            {"ok": preview.ok, "tool_name": tool_name, "status": preview.status, "would_execute": preview.would_execute},
        )
        return {
            "ok": preview.ok,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/tool-preview",
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "would_execute": False,
            "preview": preview_payload,
            "confirmation": confirmation_payload,
            "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
            "tool_execution_confirmation_summary": confirmation_summary,
            "context_packet_summary": packet.summary(),
            "session_summary": self.session_summary(),
            "trace_id": self.last_trace_id,
            "trace_path": self.last_trace_path,
        }

    def pending_confirmation_status(self) -> dict[str, Any]:
        summary = build_tool_execution_confirmation_summary(
            confirmation=self.pending_confirmation,
            source="terminal_chat_cli",
        )
        return {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/pending",
            "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
            "has_pending_confirmation": self.pending_confirmation is not None and self.pending_confirmation.confirmation_status == "pending",
            "confirmation": self.pending_confirmation.to_dict() if self.pending_confirmation else None,
            "tool_execution_confirmation_summary": summary,
            "tool_execution_enabled": False,
            "would_execute": False,
        }

    def confirm_pending_tool(self) -> dict[str, Any]:
        return self._decide_pending_confirmation(user_approved=True, command="/confirm")

    def reject_pending_tool(self) -> dict[str, Any]:
        return self._decide_pending_confirmation(user_approved=False, command="/reject")

    def _decide_pending_confirmation(self, *, user_approved: bool, command: str) -> dict[str, Any]:
        if self.pending_confirmation is None or self.pending_confirmation.confirmation_status != "pending":
            return {
                "ok": False,
                "terminal_chat_version": TERMINAL_CHAT_VERSION,
                "command": command,
                "error_code": "NO_PENDING_CONFIRMATION",
                "message": "No pending tool confirmation. Use /tool-preview or an LLM JSON tool-call candidate first.",
                "tool_execution_enabled": False,
                "would_execute": False,
            }
        trace = self._start_trace("terminal_tool_confirmation", command)
        result = confirm_tool_invocation(self.pending_confirmation, user_approved=user_approved)
        self.pending_confirmation = result.confirmation
        result_payload = result.to_dict()
        step_name = "terminal_tool_confirmation_user_approved" if user_approved else "terminal_tool_confirmation_user_rejected"
        self._add_trace_step(trace, step_name, result_payload)
        summary = build_tool_execution_confirmation_summary(result=result, source="terminal_chat_cli")
        self._add_trace_step(trace, "terminal_tool_execution_confirmation_summary_recorded", summary)
        self._finish_trace(
            trace,
            "confirmed" if user_approved else "rejected",
            {
                "ok": result.ok,
                "command": command,
                "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
                "tool_execution_confirmation_summary": summary,
                "would_execute": False,
                "execution_still_disabled": True,
            },
        )
        return {
            "ok": result.ok,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": command,
            "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
            "result": result_payload,
            "tool_execution_confirmation_summary": summary,
            "tool_execution_enabled": False,
            "would_execute": False,
            "execution_still_disabled": True,
            "trace_id": self.last_trace_id,
            "trace_path": self.last_trace_path,
        }

    def execute_confirmed_tool_dry_run(self) -> dict[str, Any]:
        if self.pending_confirmation is None:
            return {
                "ok": False,
                "terminal_chat_version": TERMINAL_CHAT_VERSION,
                "command": "/execute-dry-run",
                "error_code": "NO_CONFIRMATION_AVAILABLE",
                "message": "No confirmed tool is available. Use /tool-preview and /confirm first.",
                "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
                "real_tool_executed": False,
            }
        trace = self._start_trace("terminal_tool_executor_dry_run", "/execute-dry-run")
        self._add_trace_step(
            trace,
            "terminal_tool_executor_dry_run_requested",
            {
                "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
                "tool_name": self.pending_confirmation.tool_name,
                "proposal_id": self.pending_confirmation.proposal_id,
                "confirmation_status": self.pending_confirmation.confirmation_status,
                "user_approved": self.pending_confirmation.user_approved,
                "dry_run": True,
            },
        )
        result = execute_tool_dry_run(self.pending_confirmation)
        result_payload = result.to_dict()
        step_name = "terminal_tool_executor_dry_run_completed" if result.ok else "terminal_tool_executor_dry_run_blocked"
        self._add_trace_step(trace, step_name, result_payload)
        summary = build_tool_executor_summary(execution_result=result, source="terminal_chat_cli")
        self._add_trace_step(trace, "terminal_tool_executor_summary_recorded", summary)
        self._finish_trace(
            trace,
            "dry_run_completed" if result.ok else "dry_run_blocked",
            {
                "ok": result.ok,
                "command": "/execute-dry-run",
                "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
                "tool_executor_summary": summary,
                "real_tool_executed": False,
                "deterministic_workflow_dispatched": False,
                "engine_adapter_called": False,
            },
        )
        return {
            "ok": result.ok,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/execute-dry-run",
            "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
            "execution_result": result_payload,
            "tool_executor_summary": summary,
            "dry_run": True,
            "noop_only": True,
            "real_tool_executed": False,
            "deterministic_workflow_dispatched": False,
            "engine_adapter_called": False,
            "trace_id": self.last_trace_id,
            "trace_path": self.last_trace_path,
        }

    def allowed_tool_names(self) -> list[str]:
        packet = self.context_builder.build(
            self.task_type,
            "Terminal tool list preview",
            instrument=self.instrument,
            client_context={"entry_point": "terminal_chat_cli", "terminal_command": "/tools"},
        )
        return list(packet.allowed_tools)

    def context_packet_preview(self, *, full: bool = False, user_input: str = "Terminal context preview") -> dict[str, Any]:
        """Build the current task-scoped ContextPacket without calling the provider."""

        packet = self.context_builder.build(
            self.task_type,
            user_input,
            instrument=self.instrument,
            client_context={"entry_point": "terminal_chat_cli", "terminal_command": "/context"},
        )
        payload = {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/context",
            "task_type": packet.task_type,
            "instrument": self.instrument,
            "summary": packet.summary(),
            "tool_execution_enabled": False,
            "provider_call_enabled": False,
        }
        if full:
            payload["context_packet"] = packet.to_dict()
        return payload

    def profile_manifest(self) -> dict[str, Any]:
        return {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "current_task_type": self.task_type,
            "profiles": self.context_builder.profile_manifest(),
        }

    def current_profile(self) -> dict[str, Any]:
        profile = CONTEXT_PROFILES.get(self.task_type)
        return {
            "ok": profile is not None,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "task_type": self.task_type,
            "profile": profile.to_dict() if profile else None,
        }

    def switch_task_type(self, task_type: str) -> dict[str, Any]:
        normalized = task_type.strip()
        if normalized not in CONTEXT_PROFILES:
            return {
                "ok": False,
                "terminal_chat_version": TERMINAL_CHAT_VERSION,
                "error_code": "UNKNOWN_CONTEXT_PROFILE",
                "message": f"Unknown task_type: {normalized}",
                "available_task_types": sorted(CONTEXT_PROFILES.keys()),
                "task_type": self.task_type,
            }
        previous = self.task_type
        history_messages_before = len(self.history)
        self.task_type = normalized
        self.history.clear()
        return {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/task-type",
            "previous_task_type": previous,
            "task_type": self.task_type,
            "history_cleared": True,
            "history_messages_cleared": history_messages_before,
            "profile": CONTEXT_PROFILES[self.task_type].to_dict(),
        }

    def set_instrument(self, instrument: str) -> dict[str, Any]:
        normalized = instrument.strip()
        if not normalized:
            return {
                "ok": False,
                "terminal_chat_version": TERMINAL_CHAT_VERSION,
                "error_code": "INSTRUMENT_REQUIRED",
                "message": "Usage: /instrument <instrument>",
                "instrument": self.instrument,
            }
        previous = self.instrument
        self.instrument = normalized
        return {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/instrument",
            "previous_instrument": previous,
            "instrument": self.instrument,
        }

    def reset_session(self) -> dict[str, Any]:
        cleared = len(self.history)
        had_pending_confirmation = self.pending_confirmation is not None
        self.history.clear()
        self.pending_confirmation = None
        return {
            "ok": True,
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "command": "/reset",
            "history_messages_cleared": cleared,
            "task_type": self.task_type,
            "instrument": self.instrument,
            "pending_confirmation_cleared": had_pending_confirmation,
            "tool_execution_enabled": False,
        }

    def session_summary(self) -> dict[str, Any]:
        return {
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "task_type": self.task_type,
            "instrument": self.instrument,
            "history_message_count": len(self.history),
            "history_turn_count": len(self.history) // 2,
            "trace_export_enabled": self.trace_export_enabled(),
            "last_trace_id": self.last_trace_id,
            "last_trace_path": self.last_trace_path,
            "has_pending_confirmation": self.pending_confirmation is not None and self.pending_confirmation.confirmation_status == "pending",
            "pending_tool_name": self.pending_confirmation.tool_name if self.pending_confirmation else None,
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }

    def trace_export_enabled(self) -> bool:
        return self.trace_logger is not None

    def recent_traces(self, limit: int = 5) -> list[dict[str, Any]]:
        if not self.trace_logger:
            return []
        return self.trace_logger.list_recent(limit=limit)

    def _start_trace(self, task_type: str, user_input: str) -> AgentTrace | None:
        if not self.trace_logger:
            self.last_trace_id = None
            self.last_trace_path = None
            return None
        trace = self.trace_logger.start(task_type, user_input)
        trace.context_packet_summary = {
            "terminal_chat_version": TERMINAL_CHAT_VERSION,
            "cli_task_type": self.task_type,
            "instrument": self.instrument,
            "history_message_count": len(self.history),
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }
        self.trace_logger.add_step(trace, "terminal_trace_started", trace.context_packet_summary)
        return trace

    def _add_trace_step(self, trace: AgentTrace | None, name: str, payload: dict[str, Any]) -> None:
        if trace and self.trace_logger:
            self.trace_logger.add_step(trace, name, payload)

    def _finish_trace(self, trace: AgentTrace | None, validation_result: str, final_response_summary: dict[str, Any]) -> None:
        if not trace or not self.trace_logger:
            return
        self.trace_logger.finish(trace, validation_result, final_response_summary)
        self.last_trace_id = trace.trace_id
        self.last_trace_path = self._trace_path(trace.trace_id)

    def _trace_path(self, trace_id: str) -> str | None:
        if not self.trace_logger or not self.trace_logger.trace_store:
            return None
        return str(self.trace_logger.trace_store.trace_dir / f"{trace_id}.json")



def _build_provider_with_optional_config(config_file: str | None) -> LLMProvider:
    if not config_file:
        return build_llm_provider_from_env()
    env = dict(os.environ)
    env[LLM_CONFIG_FILE_ENV_VAR] = config_file
    return build_llm_provider_from_env(env)


def _run_setup_command(argv: list[str], stdin: TextIO, stdout: TextIO) -> int:
    parser = argparse.ArgumentParser(prog="jammate-agent-chat setup", description="Create a local JamMate Agent LLM config file")
    parser.add_argument("--config-file", default=str(default_user_llm_config_path()), help="Config file to write. Default: ~/.jammate/agent_config.env")
    parser.add_argument("--provider", default="openai_compatible", help="Provider name. Default: openai_compatible")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--api-key", help="API key. Stored only in the chosen local config file.")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="OpenAI-compatible base URL")
    parser.add_argument("--chat-completions-path", default="/chat/completions", help="Chat completions path")
    parser.add_argument("--enable-network-calls", default="true", choices=["true", "false", "yes", "no"], help="Whether terminal chat may call the provider. Default: true")
    parser.add_argument("--max-output-tokens", default="1200")
    parser.add_argument("--temperature", default="0.2")
    parser.add_argument("--request-timeout-seconds", default="30")
    parser.add_argument("--yes", action="store_true", help="Non-interactive mode; fail if required values are missing.")
    args = parser.parse_args(argv)

    model = args.model or _prompt(stdin, stdout, "Model", default="gpt-4o-mini" if not args.yes else None)
    api_key = args.api_key or _prompt_secret(stdin, stdout, "API key", required=not args.yes)
    if args.yes and (not model or not api_key):
        print("SetupError> --model and --api-key are required with --yes.", file=stdout)
        return 2
    if not model or not api_key:
        print("SetupError> model and API key are required.", file=stdout)
        return 2

    values = {
        "JAMMATE_LLM_PROVIDER": args.provider,
        "JAMMATE_LLM_MODEL": model,
        "JAMMATE_LLM_API_KEY_ENV_VAR": "JAMMATE_LLM_API_KEY",
        "JAMMATE_LLM_API_KEY": api_key,
        "JAMMATE_LLM_ENABLE_NETWORK_CALLS": "true" if args.enable_network_calls.lower() in {"true", "yes"} else "false",
        "JAMMATE_LLM_BASE_URL": args.base_url.rstrip("/"),
        "JAMMATE_LLM_CHAT_COMPLETIONS_PATH": args.chat_completions_path,
        "JAMMATE_LLM_MAX_OUTPUT_TOKENS": str(args.max_output_tokens),
        "JAMMATE_LLM_TEMPERATURE": str(args.temperature),
        "JAMMATE_LLM_REQUEST_TIMEOUT_SECONDS": str(args.request_timeout_seconds),
    }
    path = write_llm_config_file(args.config_file, values)
    status = LLMProviderConfig.from_env({LLM_CONFIG_FILE_ENV_VAR: str(path)}).to_dict()
    print("LLMConfigSetup> saved", file=stdout)
    print(f"  path: {path}", file=stdout)
    print(f"  provider_name: {status.get('provider_name')}", file=stdout)
    print(f"  model: {status.get('model')}", file=stdout)
    print(f"  api_key_configured: {status.get('api_key_configured')}", file=stdout)
    print(f"  network_calls_enabled: {status.get('network_calls_enabled')}", file=stdout)
    print("  secret_policy: API key is stored locally and never printed in status/trace output.", file=stdout)
    print("Next: jammate-agent-chat --config-file <path> or set JAMMATE_AGENT_LLM_CONFIG_FILE=<path>.", file=stdout)
    return 0


def _run_doctor_command(argv: list[str], stdout: TextIO) -> int:
    parser = argparse.ArgumentParser(prog="jammate-agent-chat doctor", description="Inspect terminal LLM provider configuration")
    parser.add_argument("--config-file", help="Config file to inspect")
    parser.add_argument("--json", action="store_true", help="Print machine-readable status")
    args = parser.parse_args(argv)
    env = dict(os.environ)
    if args.config_file:
        env[LLM_CONFIG_FILE_ENV_VAR] = args.config_file
    config = LLMProviderConfig.from_env(env)
    status = config.to_dict()
    status["ok"] = bool(config.terminal_chat_available)
    status["terminal_chat_setup_version"] = TERMINAL_CHAT_VERSION
    status["tool_execution_enabled"] = False
    status["autonomous_tool_execution_enabled"] = False
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2), file=stdout)
        return 0 if status["ok"] else 1
    _print_doctor_status(status, stdout)
    return 0 if status["ok"] else 1


def _run_config_path_command(argv: list[str], stdout: TextIO) -> int:
    parser = argparse.ArgumentParser(prog="jammate-agent-chat config-path", description="Print default local LLM config path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    path = default_user_llm_config_path()
    payload = {
        "ok": True,
        "terminal_chat_version": TERMINAL_CHAT_VERSION,
        "default_user_config_path": str(path),
        "env_override": LLM_CONFIG_FILE_ENV_VAR,
        "repo_local_filename": ".jammate_agent.env",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=stdout)
    else:
        print(f"Default user LLM config path: {path}", file=stdout)
        print(f"Override with {LLM_CONFIG_FILE_ENV_VAR}=<path> or --config-file <path>.", file=stdout)
    return 0


def _prompt(stdin: TextIO, stdout: TextIO, label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    print(f"{label}{suffix}: ", end="", file=stdout)
    stdout.flush()
    value = stdin.readline().strip()
    return value or (default or "")


def _prompt_secret(stdin: TextIO, stdout: TextIO, label: str, required: bool = True) -> str:
    # Use stdin/stdout instead of getpass so this remains testable and works in
    # non-tty IDE terminals. The value is never echoed back by JamMate output.
    value = _prompt(stdin, stdout, label)
    if required and not value:
        return ""
    return value

def run_interactive_chat(argv: list[str] | None = None, stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    argv_list = list(argv or [])
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    if argv_list and argv_list[0] in {"setup", "doctor", "config-path"}:
        command = argv_list[0]
        if command == "setup":
            return _run_setup_command(argv_list[1:], input_stream, output_stream)
        if command == "doctor":
            return _run_doctor_command(argv_list[1:], output_stream)
        return _run_config_path_command(argv_list[1:], output_stream)

    parser = argparse.ArgumentParser(description="JamMate Agent terminal LLM chat CLI")
    parser.add_argument("--task-type", default="coach_qa", help="Context profile task type. Default: coach_qa")
    parser.add_argument("--instrument", default="piano", help="Instrument hint for the context packet. Default: piano")
    parser.add_argument("--once", help="Send one message and exit; useful for smoke tests. Slash commands are supported.")
    parser.add_argument("--show-provider-status", action="store_true", help="Print provider status before chatting.")
    parser.add_argument("--trace-dir", help="Export terminal chat/tool-preview traces as JSON into this directory.")
    parser.add_argument("--config-file", help="Read LLM provider settings from this local .env-style config file.")
    args = parser.parse_args(argv_list)

    trace_logger = TraceLogger(JsonTraceStore(args.trace_dir)) if args.trace_dir else None
    provider = _build_provider_with_optional_config(args.config_file)
    session = TerminalChatSession(task_type=args.task_type, instrument=args.instrument, provider=provider, trace_logger=trace_logger)
    status = session.provider_status()

    if args.show_provider_status or not status.get("terminal_chat_enabled"):
        _print_provider_status(status, output_stream)
        if not status.get("terminal_chat_enabled"):
            _print_setup_hint(status, output_stream)

    if args.once:
        once_input = args.once.strip()
        if _handle_terminal_command(once_input, session, output_stream):
            _print_trace_export(session, output_stream)
            return 0
        _print_response(session.respond(once_input), output_stream)
        _print_trace_export(session, output_stream)
        return 0

    print("JamMate Agent terminal chat. Type /help for commands or /exit to quit.", file=output_stream)
    while True:
        print("You> ", end="", file=output_stream)
        output_stream.flush()
        line = input_stream.readline()
        if not line:
            break
        user_input = line.strip()
        if user_input in {"/exit", "/quit"}:
            break
        if not user_input:
            continue
        if _handle_terminal_command(user_input, session, output_stream):
            _print_trace_export(session, output_stream)
            continue
        _print_response(session.respond(user_input), output_stream)
        _print_trace_export(session, output_stream)
    return 0


def _handle_terminal_command(user_input: str, session: TerminalChatSession, stdout: TextIO) -> bool:
    if not user_input.startswith("/"):
        return False
    if user_input == "/help":
        _print_help(stdout)
        return True
    if user_input == "/tools":
        tools = session.allowed_tool_names()
        print("Allowed tools for this task:", file=stdout)
        for tool in tools:
            print(f"  - {tool}", file=stdout)
        print("Tool execution remains disabled; use /tool-preview to validate a proposed call.", file=stdout)
        return True
    if user_input == "/session":
        _print_session_summary(session.session_summary(), stdout)
        return True
    if user_input.startswith("/context"):
        full = user_input.strip() in {"/context full", "/context --full", "/context json", "/context --json"}
        _print_context_preview(session.context_packet_preview(full=full), stdout, full=full)
        return True
    if user_input == "/profiles":
        _print_profile_manifest(session.profile_manifest(), stdout)
        return True
    if user_input.startswith("/profile"):
        rest = user_input[len("/profile") :].strip()
        if not rest:
            _print_current_profile(session.current_profile(), stdout)
            return True
        _print_task_type_switch(session.switch_task_type(rest), stdout)
        return True
    if user_input.startswith("/task-type"):
        rest = user_input[len("/task-type") :].strip()
        if not rest:
            _print_current_profile(session.current_profile(), stdout)
            return True
        _print_task_type_switch(session.switch_task_type(rest), stdout)
        return True
    if user_input.startswith("/instrument"):
        rest = user_input[len("/instrument") :].strip()
        if not rest:
            print(f"Instrument> {session.instrument}", file=stdout)
            return True
        _print_instrument_update(session.set_instrument(rest), stdout)
        return True
    if user_input == "/reset":
        _print_reset_response(session.reset_session(), stdout)
        return True
    if user_input == "/trace":
        _print_trace_status(session, stdout)
        return True
    if user_input == "/traces":
        _print_recent_traces(session, stdout)
        return True
    if user_input == "/pending":
        _print_pending_confirmation(session.pending_confirmation_status(), stdout)
        return True
    if user_input == "/confirm":
        _print_confirmation_decision(session.confirm_pending_tool(), stdout)
        return True
    if user_input == "/reject":
        _print_confirmation_decision(session.reject_pending_tool(), stdout)
        return True
    if user_input == "/execute-dry-run":
        _print_execution_dry_run(session.execute_confirmed_tool_dry_run(), stdout)
        return True
    if user_input.startswith("/tool-preview"):
        result = _parse_tool_preview_command(user_input)
        if not result["ok"]:
            _print_command_error(result, stdout)
            return True
        response = session.preview_tool_call(result["tool_name"], result["arguments"])
        _print_tool_preview_response(response, stdout)
        return True
    print(f"Unknown command: {user_input}. Type /help for available commands.", file=stdout)
    return True


def _parse_tool_preview_command(command: str) -> dict[str, Any]:
    rest = command[len("/tool-preview") :].strip()
    if not rest:
        return {
            "ok": False,
            "error_code": "TOOL_PREVIEW_USAGE",
            "message": "Usage: /tool-preview <tool_name> [json_object_arguments]",
        }
    parts = rest.split(maxsplit=1)
    tool_name = parts[0].strip()
    raw_args = parts[1].strip() if len(parts) > 1 else "{}"
    if not raw_args:
        raw_args = "{}"
    try:
        parsed_args = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error_code": "TOOL_PREVIEW_INVALID_JSON",
            "message": f"Arguments must be a JSON object: {exc.msg}",
        }
    if not isinstance(parsed_args, dict):
        return {
            "ok": False,
            "error_code": "TOOL_PREVIEW_ARGUMENTS_NOT_OBJECT",
            "message": "Arguments must be a JSON object, for example: {\"durationMinutes\": 20}",
        }
    return {"ok": True, "tool_name": tool_name, "arguments": parsed_args}



def _print_setup_hint(status: dict, stdout: TextIO) -> None:
    print("LLM setup hint:", file=stdout)
    print("  Run `jammate-agent-chat setup` to create a local config file,", file=stdout)
    print("  or pass `--config-file <path>` / set JAMMATE_AGENT_LLM_CONFIG_FILE.", file=stdout)
    print("  Until configured, terminal chat stays in guarded preview mode.", file=stdout)


def _print_doctor_status(status: dict, stdout: TextIO) -> None:
    print("LLMConfigDoctor>", file=stdout)
    print(f"  status: {'ready' if status.get('ok') else 'guarded'}", file=stdout)
    print(f"  terminal_chat_setup_version: {status.get('terminal_chat_setup_version')}", file=stdout)
    print(f"  provider_name: {status.get('provider_name')}", file=stdout)
    print(f"  model: {status.get('model')}", file=stdout)
    print(f"  api_key_env_var: {status.get('api_key_env_var')}", file=stdout)
    print(f"  api_key_configured: {status.get('api_key_configured')}", file=stdout)
    print(f"  network_calls_enabled: {status.get('network_calls_enabled')}", file=stdout)
    print(f"  base_url: {status.get('base_url')}", file=stdout)
    print(f"  config_source: {status.get('config_source')}", file=stdout)
    print(f"  config_file_path: {status.get('config_file_path')}", file=stdout)
    print(f"  terminal_chat_available: {status.get('terminal_chat_available')}", file=stdout)
    print(f"  guard_reason: {status.get('guard_reason')}", file=stdout)
    print("  tool_execution_enabled: False", file=stdout)
    print("  secret_policy: API key values are not printed, traced, or packaged.", file=stdout)

def _print_provider_status(status: dict, stdout: TextIO) -> None:
    print("Provider status:", file=stdout)
    print(f"  provider_name: {status.get('provider_name')}", file=stdout)
    print(f"  model: {status.get('model')}", file=stdout)
    print(f"  terminal_chat_enabled: {status.get('terminal_chat_enabled')}", file=stdout)
    print(f"  llm_calls_enabled: {status.get('llm_calls_enabled')}", file=stdout)
    print(f"  tool_execution_enabled: {status.get('tool_execution_enabled', False)}", file=stdout)
    print(f"  guard_reason: {status.get('guard_reason')}", file=stdout)


def _print_response(response: dict, stdout: TextIO) -> None:
    if response.get("ok"):
        print(f"JamMate> {response.get('content', '')}", file=stdout)
        _print_candidate_preview_summary(response, stdout)
        return
    print(f"JamMate[guarded]> {response.get('error_code')}: {response.get('message')}", file=stdout)


def _print_candidate_preview_summary(response: dict, stdout: TextIO) -> None:
    previews = response.get("tool_call_candidate_previews") or []
    extraction = response.get("tool_call_candidate_extraction") or {}
    candidate_count = extraction.get("candidate_count", 0)
    if not candidate_count:
        return
    print(f"ToolCandidateExtraction> {candidate_count} candidate(s); execution disabled", file=stdout)
    for item in previews:
        candidate = item.get("candidate") or {}
        preview = item.get("preview") or {}
        confirmation = item.get("confirmation") or {}
        confirmation_status = confirmation.get("confirmation_status") or "none"
        print(f"  - {candidate.get('tool_name')}: {preview.get('status')} would_execute={preview.get('would_execute')} confirmation={confirmation_status}", file=stdout)
        if confirmation_status == "pending":
            print("    confirmation required: use /confirm to approve or /reject to reject", file=stdout)
        blocking = preview.get("blocking_reasons") or []
        if blocking:
            print(f"    blocking_reasons: {', '.join(str(value) for value in blocking)}", file=stdout)


def _print_tool_preview_response(response: dict, stdout: TextIO) -> None:
    preview = response.get("preview") or {}
    status = preview.get("status")
    tool_name = preview.get("tool_name")
    print(f"ToolPreview> {tool_name}: {status}", file=stdout)
    print(f"  ok: {preview.get('ok')}", file=stdout)
    print(f"  known_tool: {preview.get('known_tool')}", file=stdout)
    print(f"  allowed_by_context: {preview.get('allowed_by_context')}", file=stdout)
    print(f"  would_execute: {preview.get('would_execute')}", file=stdout)
    blocking = preview.get("blocking_reasons") or []
    if blocking:
        print(f"  blocking_reasons: {', '.join(str(item) for item in blocking)}", file=stdout)
    warnings = preview.get("warnings") or []
    if warnings:
        print(f"  warnings: {', '.join(str(item) for item in warnings)}", file=stdout)
    confirmation = response.get("confirmation") or {}
    if confirmation:
        print(f"  confirmation_status: {confirmation.get('confirmation_status')}", file=stdout)
        print(f"  risk_summary: {confirmation.get('risk_summary')}", file=stdout)
        print("  next: /confirm or /reject", file=stdout)


def _print_pending_confirmation(response: dict[str, Any], stdout: TextIO) -> None:
    confirmation = response.get("confirmation") or {}
    if not response.get("has_pending_confirmation"):
        print("PendingConfirmation> none", file=stdout)
        print("  tool_execution_enabled: False", file=stdout)
        return
    print(f"PendingConfirmation> {confirmation.get('tool_name')}: {confirmation.get('confirmation_status')}", file=stdout)
    print(f"  proposal_id: {confirmation.get('proposal_id')}", file=stdout)
    print(f"  side_effect_level: {confirmation.get('side_effect_level')}", file=stdout)
    print(f"  risk_summary: {confirmation.get('risk_summary')}", file=stdout)
    print("  would_execute_after_confirmation: False", file=stdout)
    print("  execution_still_disabled: True", file=stdout)


def _print_confirmation_decision(response: dict[str, Any], stdout: TextIO) -> None:
    if not response.get("ok") and response.get("error_code"):
        _print_command_error(response, stdout)
        return
    result = response.get("result") or {}
    confirmation = result.get("confirmation") or {}
    print(f"ToolConfirmation> {confirmation.get('tool_name')}: {result.get('status')}", file=stdout)
    print(f"  user_approved: {result.get('user_approved')}", file=stdout)
    print("  would_execute: False", file=stdout)
    print("  execution_still_disabled: True", file=stdout)
    print("  next_stage_required: ToolExecutorBoundary", file=stdout)


def _print_execution_dry_run(response: dict[str, Any], stdout: TextIO) -> None:
    if not response.get("ok") and response.get("error_code"):
        _print_command_error(response, stdout)
        return
    result = response.get("execution_result") or {}
    print(f"ToolExecutorDryRun> {result.get('tool_name')}: {result.get('status')}", file=stdout)
    print(f"  dry_run: {result.get('dry_run')}", file=stdout)
    print(f"  noop_only: {result.get('noop_only')}", file=stdout)
    print("  real_tool_executed: False", file=stdout)
    print("  deterministic_workflow_dispatched: False", file=stdout)
    print("  engine_adapter_called: False", file=stdout)
    print("  next_stage_required: DeterministicWorkflowDispatcher", file=stdout)


def _print_session_summary(summary: dict[str, Any], stdout: TextIO) -> None:
    print("Session>", file=stdout)
    print(f"  task_type: {summary.get('task_type')}", file=stdout)
    print(f"  instrument: {summary.get('instrument')}", file=stdout)
    print(f"  history_messages: {summary.get('history_message_count')}", file=stdout)
    print(f"  history_turns: {summary.get('history_turn_count')}", file=stdout)
    print(f"  trace_export_enabled: {summary.get('trace_export_enabled')}", file=stdout)
    print(f"  last_trace_id: {summary.get('last_trace_id')}", file=stdout)
    print("  tool_execution_enabled: False", file=stdout)


def _print_context_preview(payload: dict[str, Any], stdout: TextIO, *, full: bool = False) -> None:
    if full:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=stdout)
        return
    summary = payload.get("summary") or {}
    print("ContextPacket>", file=stdout)
    print(f"  task_type: {payload.get('task_type')}", file=stdout)
    print(f"  instrument: {payload.get('instrument')}", file=stdout)
    print(f"  context_runtime_version: {summary.get('context_runtime_version')}", file=stdout)
    print(f"  selected_layers: {', '.join(summary.get('selected_context_layers') or [])}", file=stdout)
    print(f"  allowed_tools: {', '.join(summary.get('allowed_tools') or [])}", file=stdout)
    print(f"  output_schema: {summary.get('output_schema')}", file=stdout)
    print("  provider_call_enabled: False", file=stdout)
    print("  tool_execution_enabled: False", file=stdout)


def _print_profile_manifest(payload: dict[str, Any], stdout: TextIO) -> None:
    print(f"ContextProfiles> current_task_type: {payload.get('current_task_type')}", file=stdout)
    profiles = payload.get("profiles") or {}
    for task_type in sorted(profiles):
        profile = profiles[task_type]
        tools = profile.get("allowed_tools") or []
        print(f"  - {task_type}: schema={profile.get('output_schema')} llm_required={profile.get('llm_required')} tools={','.join(tools)}", file=stdout)


def _print_current_profile(payload: dict[str, Any], stdout: TextIO) -> None:
    profile = payload.get("profile") or {}
    print(f"CurrentProfile> {payload.get('task_type')}", file=stdout)
    print(f"  output_schema: {profile.get('output_schema')}", file=stdout)
    print(f"  llm_required: {profile.get('llm_required')}", file=stdout)
    print(f"  deterministic_fallback: {profile.get('deterministic_fallback')}", file=stdout)
    print(f"  allowed_tools: {', '.join(profile.get('allowed_tools') or [])}", file=stdout)


def _print_task_type_switch(payload: dict[str, Any], stdout: TextIO) -> None:
    if not payload.get("ok"):
        _print_command_error(payload, stdout)
        available = payload.get("available_task_types") or []
        if available:
            print(f"  available_task_types: {', '.join(available)}", file=stdout)
        return
    print(f"TaskType> {payload.get('previous_task_type')} -> {payload.get('task_type')}", file=stdout)
    print(f"  history_cleared: {payload.get('history_cleared')}", file=stdout)
    print(f"  output_schema: {(payload.get('profile') or {}).get('output_schema')}", file=stdout)


def _print_instrument_update(payload: dict[str, Any], stdout: TextIO) -> None:
    if not payload.get("ok"):
        _print_command_error(payload, stdout)
        return
    print(f"Instrument> {payload.get('previous_instrument')} -> {payload.get('instrument')}", file=stdout)


def _print_reset_response(payload: dict[str, Any], stdout: TextIO) -> None:
    print("SessionReset>", file=stdout)
    print(f"  history_messages_cleared: {payload.get('history_messages_cleared')}", file=stdout)
    print(f"  task_type: {payload.get('task_type')}", file=stdout)
    print(f"  instrument: {payload.get('instrument')}", file=stdout)
    print("  tool_execution_enabled: False", file=stdout)


def _print_command_error(response: dict[str, Any], stdout: TextIO) -> None:
    print(f"JamMate[command-error]> {response.get('error_code')}: {response.get('message')}", file=stdout)


def _print_trace_export(session: TerminalChatSession, stdout: TextIO) -> None:
    if not session.trace_export_enabled() or not session.last_trace_id:
        return
    print(f"TraceExport> trace_id: {session.last_trace_id}", file=stdout)
    if session.last_trace_path:
        print(f"  path: {session.last_trace_path}", file=stdout)


def _print_trace_status(session: TerminalChatSession, stdout: TextIO) -> None:
    if not session.trace_export_enabled():
        print("Trace export is disabled. Start the CLI with --trace-dir <dir> to write JSON traces.", file=stdout)
        return
    if not session.last_trace_id:
        print("Trace export is enabled, but no terminal turn has been traced yet.", file=stdout)
        return
    print(f"Last trace: {session.last_trace_id}", file=stdout)
    if session.last_trace_path:
        print(f"  path: {session.last_trace_path}", file=stdout)


def _print_recent_traces(session: TerminalChatSession, stdout: TextIO) -> None:
    if not session.trace_export_enabled():
        print("Trace export is disabled. Start the CLI with --trace-dir <dir> to write JSON traces.", file=stdout)
        return
    traces = session.recent_traces(limit=5)
    if not traces:
        print("No exported terminal traces yet.", file=stdout)
        return
    print("Recent terminal traces:", file=stdout)
    for item in traces:
        print(f"  - {item.get('trace_id')} {item.get('task_type')} {item.get('validation_result')}", file=stdout)


def _print_help(stdout: TextIO) -> None:
    print("Commands:", file=stdout)
    print("  setup        # shell subcommand: create local LLM config", file=stdout)
    print("  doctor       # shell subcommand: inspect provider config", file=stdout)
    print("  config-path  # shell subcommand: print default config path", file=stdout)
    print("  /help", file=stdout)
    print("  /session", file=stdout)
    print("  /context [full|--full|json|--json]", file=stdout)
    print("  /profiles", file=stdout)
    print("  /profile [task_type]", file=stdout)
    print("  /task-type [task_type]", file=stdout)
    print("  /instrument [instrument]", file=stdout)
    print("  /reset", file=stdout)
    print("  /tools", file=stdout)
    print('  /tool-preview <tool_name> [json_object_arguments]', file=stdout)
    print("  /pending", file=stdout)
    print("  /confirm", file=stdout)
    print("  /reject", file=stdout)
    print("  /execute-dry-run", file=stdout)
    print("  /trace", file=stdout)
    print("  /traces", file=stdout)
    print("  /exit", file=stdout)
    print("Use `jammate-agent-chat setup` once to avoid repeated shell exports.", file=stdout)
    print("Use --config-file <path> to load a specific local LLM config.", file=stdout)
    print("Use --trace-dir <dir> to export terminal chat/tool-preview traces as JSON.", file=stdout)
    print("Use `python -m jammate_agent.cli.trace_viewer --trace-dir <dir> list|show` to inspect exported traces.", file=stdout)
    print("Context controls rebuild preview packets only; they never call the provider, execute tools, or call engine workflows.", file=stdout)
    print("Tool preview validates only; it never executes tools or engine workflows.", file=stdout)
    print("Tool confirmation records /confirm or /reject only; it still never executes tools.", file=stdout)
    print("Tool executor dry-run proves request/result shape only; it never dispatches workflows or engine adapters.", file=stdout)
    print("Successful LLM replies are scanned for explicit JSON tool-call candidates and previewed only.", file=stdout)


def main() -> int:
    return run_interactive_chat()


if __name__ == "__main__":
    raise SystemExit(main())
