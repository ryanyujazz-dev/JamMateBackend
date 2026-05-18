from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, TextIO

from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import LLMProvider, build_llm_provider_from_env, build_request_envelope
from jammate_agent.core.tool_invocation import ToolInvocationProposal, preview_tool_invocation
from jammate_agent.core.trace import AgentTrace, JsonTraceStore, TraceLogger

TERMINAL_CHAT_VERSION = "v2_4_7"


@dataclass
class TerminalChatSession:
    """Interactive terminal chat session for provider-boundary debugging.

    The session can call a configured LLM provider, but it does not execute Agent
    tools. Every turn rebuilds a task-scoped ContextPacket so the CLI exercises
    the same context/runtime boundary used by API previews.

    `/tool-preview` is an explicit terminal command that validates a proposed
    tool call against the same ContextPacket allow-list and preview contract.
    It never dispatches deterministic workflows or engine adapters.
    """

    task_type: str = "coach_qa"
    instrument: str = "piano"
    provider: LLMProvider = field(default_factory=build_llm_provider_from_env)
    context_builder: ContextBuilder = field(default_factory=ContextBuilder)
    history: list[dict[str, str]] = field(default_factory=list)
    trace_logger: TraceLogger | None = None
    last_trace_id: str | None = None
    last_trace_path: str | None = None

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
        if result.ok and result.content:
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": result.content})
        self._finish_trace(
            trace,
            "passed" if result.ok else "guarded",
            {"ok": result.ok, "task_type": packet.task_type, "terminal_chat_version": TERMINAL_CHAT_VERSION, "tool_execution_enabled": False},
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
            "context_packet_summary": packet.summary(),
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


def run_interactive_chat(argv: list[str] | None = None, stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    parser = argparse.ArgumentParser(description="JamMate Agent terminal LLM chat CLI")
    parser.add_argument("--task-type", default="coach_qa", help="Context profile task type. Default: coach_qa")
    parser.add_argument("--instrument", default="piano", help="Instrument hint for the context packet. Default: piano")
    parser.add_argument("--once", help="Send one message and exit; useful for smoke tests. Slash commands are supported.")
    parser.add_argument("--show-provider-status", action="store_true", help="Print provider status before chatting.")
    parser.add_argument("--trace-dir", help="Export terminal chat/tool-preview traces as JSON into this directory.")
    args = parser.parse_args(argv)

    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    trace_logger = TraceLogger(JsonTraceStore(args.trace_dir)) if args.trace_dir else None
    session = TerminalChatSession(task_type=args.task_type, instrument=args.instrument, provider=build_llm_provider_from_env(), trace_logger=trace_logger)
    status = session.provider_status()

    if args.show_provider_status or not status.get("terminal_chat_enabled"):
        _print_provider_status(status, output_stream)

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
    if user_input == "/trace":
        _print_trace_status(session, stdout)
        return True
    if user_input == "/traces":
        _print_recent_traces(session, stdout)
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
        return
    print(f"JamMate[guarded]> {response.get('error_code')}: {response.get('message')}", file=stdout)


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
    print("  /help", file=stdout)
    print("  /tools", file=stdout)
    print('  /tool-preview <tool_name> [json_object_arguments]', file=stdout)
    print("  /trace", file=stdout)
    print("  /traces", file=stdout)
    print("  /exit", file=stdout)
    print("Use --trace-dir <dir> to export terminal chat/tool-preview traces as JSON.", file=stdout)
    print("Tool preview validates only; it never executes tools or engine workflows.", file=stdout)


def main() -> int:
    return run_interactive_chat()


if __name__ == "__main__":
    raise SystemExit(main())
