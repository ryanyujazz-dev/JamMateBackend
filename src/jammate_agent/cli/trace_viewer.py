from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from jammate_agent.core.trace import JsonTraceStore, TRACE_API_CONTRACT_VERSION, TRACE_NOT_FOUND_ERROR_CODE

TRACE_VIEWER_CLI_VERSION = "v2_4_13"
DEFAULT_TRACE_DIR = "demos/agent_traces"


def run_trace_viewer(argv: list[str] | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    """Read-only terminal viewer for AgentTrace JSON files.

    This CLI intentionally uses JsonTraceStore only. It never executes tools,
    calls an LLM provider, dispatches deterministic workflows, or imports the
    accompaniment engine.
    """

    parser = argparse.ArgumentParser(description="JamMate Agent trace viewer CLI")
    parser.add_argument("--trace-dir", default=DEFAULT_TRACE_DIR, help=f"Trace directory. Default: {DEFAULT_TRACE_DIR}")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List recent traces")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum trace summaries to display. Default: 20")
    list_parser.add_argument("--json", action="store_true", help="Print the list response as JSON")

    show_parser = subparsers.add_parser("show", help="Show one trace by trace_id")
    show_parser.add_argument("trace_id", help="Trace id, for example trace_xxx")
    show_parser.add_argument("--json", action="store_true", help="Print the detail response as JSON")

    spec_parser = subparsers.add_parser("spec", help="Show trace viewer CLI contract")
    spec_parser.add_argument("--json", action="store_true", help="Print the spec as JSON")

    args = parser.parse_args(argv)
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    command = args.command or "list"

    if command == "spec":
        payload = trace_viewer_contract(args.trace_dir)
        if args.json:
            _print_json(payload, output)
        else:
            _print_spec(payload, output)
        return 0

    store = JsonTraceStore(args.trace_dir)
    if command == "list":
        payload = list_trace_summaries(store, limit=max(0, args.limit))
        if args.json:
            _print_json(payload, output)
        else:
            _print_trace_list(payload, output)
        return 0

    if command == "show":
        payload = load_trace_detail(store, args.trace_id)
        if args.json:
            _print_json(payload, output)
        elif payload["ok"]:
            _print_trace_detail(payload, output)
        else:
            print(f"{payload['error_code']}: {payload['message']}", file=error_output)
        return 0 if payload["ok"] else 1

    parser.print_help(output)
    return 0


def trace_viewer_contract(trace_dir: str | Path = DEFAULT_TRACE_DIR) -> dict[str, Any]:
    return {
        "ok": True,
        "trace_viewer_cli_version": TRACE_VIEWER_CLI_VERSION,
        "trace_contract_version": TRACE_API_CONTRACT_VERSION,
        "entrypoints": {
            "module": "python -m jammate_agent.cli.trace_viewer",
            "console_script": "jammate-agent-traces",
        },
        "commands": {
            "list": "list [--limit N] [--json]",
            "show": "show <trace_id> [--json]",
            "spec": "spec [--json]",
        },
        "trace_dir": str(trace_dir),
        "guards": {
            "read_only": True,
            "executes_tools": False,
            "calls_llm_provider": False,
            "dispatches_workflows": False,
            "calls_engine_adapter": False,
        },
    }


def list_trace_summaries(store: JsonTraceStore, limit: int = 20) -> dict[str, Any]:
    return {
        "ok": True,
        "trace_viewer_cli_version": TRACE_VIEWER_CLI_VERSION,
        "trace_contract_version": TRACE_API_CONTRACT_VERSION,
        "trace_dir": str(store.trace_dir),
        "traces": store.list_recent(limit=limit),
    }


def load_trace_detail(store: JsonTraceStore, trace_id: str) -> dict[str, Any]:
    trace = store.load(trace_id)
    if not trace:
        return {
            "ok": False,
            "trace_viewer_cli_version": TRACE_VIEWER_CLI_VERSION,
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "error_code": TRACE_NOT_FOUND_ERROR_CODE,
            "message": f"Trace not found: {trace_id}",
            "trace": None,
        }
    return {
        "ok": True,
        "trace_viewer_cli_version": TRACE_VIEWER_CLI_VERSION,
        "trace_contract_version": TRACE_API_CONTRACT_VERSION,
        "trace_dir": str(store.trace_dir),
        "trace": trace.to_detail_dict(),
    }


def _print_json(payload: dict[str, Any], stdout: TextIO) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=stdout)


def _print_spec(payload: dict[str, Any], stdout: TextIO) -> None:
    print(f"JamMate Agent Trace Viewer CLI {payload['trace_viewer_cli_version']}", file=stdout)
    print(f"Trace contract: {payload['trace_contract_version']}", file=stdout)
    print(f"Trace dir: {payload['trace_dir']}", file=stdout)
    print("Commands:", file=stdout)
    for name, usage in payload["commands"].items():
        print(f"  {name}: {usage}", file=stdout)
    print("Guards: read-only; no tools, no LLM provider, no workflows, no engine adapter.", file=stdout)


def _print_trace_list(payload: dict[str, Any], stdout: TextIO) -> None:
    traces = payload.get("traces") or []
    print(f"JamMate Agent traces ({len(traces)})", file=stdout)
    print(f"Trace dir: {payload.get('trace_dir')}", file=stdout)
    if not traces:
        print("No traces found.", file=stdout)
        return
    for item in traces:
        print(
            f"- {item.get('trace_id')} | {item.get('task_type')} | {item.get('validation_result')} | steps={item.get('step_count')} | {item.get('user_input_preview')}",
            file=stdout,
        )


def _print_trace_detail(payload: dict[str, Any], stdout: TextIO) -> None:
    trace = payload.get("trace") or {}
    print(f"Trace {trace.get('trace_id')}", file=stdout)
    print(f"  task_type: {trace.get('task_type')}", file=stdout)
    print(f"  request_id: {trace.get('request_id')}", file=stdout)
    print(f"  validation_result: {trace.get('validation_result')}", file=stdout)
    print(f"  created_at: {trace.get('created_at')}", file=stdout)
    print(f"  updated_at: {trace.get('updated_at')}", file=stdout)
    print(f"  user_input: {trace.get('user_input')}", file=stdout)
    print("  steps:", file=stdout)
    for index, step in enumerate(trace.get("steps") or [], start=1):
        print(f"    {index}. {step.get('name')} @ {step.get('at')}", file=stdout)
    final_summary = trace.get("final_response_summary") or {}
    if final_summary:
        print("  final_response_summary:", file=stdout)
        for key, value in final_summary.items():
            print(f"    {key}: {value}", file=stdout)


def main() -> int:
    return run_trace_viewer()


if __name__ == "__main__":
    raise SystemExit(main())
