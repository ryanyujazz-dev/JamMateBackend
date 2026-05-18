from __future__ import annotations

import ast
import json
from io import StringIO
from pathlib import Path

from jammate_agent.cli.trace_viewer import (
    TRACE_VIEWER_CLI_VERSION,
    list_trace_summaries,
    load_trace_detail,
    run_trace_viewer,
    trace_viewer_contract,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger

ROOT = Path(__file__).resolve().parents[1]


def _make_trace(trace_dir: Path) -> str:
    logger = TraceLogger(JsonTraceStore(trace_dir))
    trace = logger.start("terminal_chat", "trace viewer hello", request_id="viewer_req_001")
    logger.add_step(trace, "terminal_context_packet_built", {"ok": True})
    logger.finish(trace, "passed", {"ok": True, "tool_execution_enabled": False})
    return trace.trace_id


def test_trace_viewer_contract_is_read_only() -> None:
    contract = trace_viewer_contract("tmp/traces")
    assert contract["ok"] is True
    assert contract["trace_viewer_cli_version"] == "v2_4_13"
    assert contract["trace_contract_version"] == "v2_4_13"
    assert contract["entrypoints"]["module"] == "python -m jammate_agent.cli.trace_viewer"
    assert contract["entrypoints"]["console_script"] == "jammate-agent-traces"
    assert contract["commands"]["list"] == "list [--limit N] [--json]"
    assert contract["guards"] == {
        "read_only": True,
        "executes_tools": False,
        "calls_llm_provider": False,
        "dispatches_workflows": False,
        "calls_engine_adapter": False,
    }


def test_trace_viewer_list_and_show_reuse_trace_store_contract(tmp_path: Path) -> None:
    trace_id = _make_trace(tmp_path)
    store = JsonTraceStore(tmp_path)

    list_payload = list_trace_summaries(store, limit=5)
    assert list_payload["ok"] is True
    assert list_payload["trace_viewer_cli_version"] == TRACE_VIEWER_CLI_VERSION
    assert list_payload["trace_contract_version"] == "v2_4_13"
    assert list_payload["traces"][0]["trace_id"] == trace_id
    assert list_payload["traces"][0]["trace_schema_version"] == "agent_trace_summary_v1"

    detail_payload = load_trace_detail(store, trace_id)
    assert detail_payload["ok"] is True
    assert detail_payload["trace_viewer_cli_version"] == "v2_4_13"
    detail = detail_payload["trace"]
    assert detail["trace_contract_version"] == "v2_4_13"
    assert detail["trace_schema_version"] == "agent_trace_detail_v1"
    assert detail["request_id"] == "viewer_req_001"
    assert detail["final_response_summary"]["tool_execution_enabled"] is False


def test_trace_viewer_missing_trace_returns_stable_not_found_shape(tmp_path: Path) -> None:
    payload = load_trace_detail(JsonTraceStore(tmp_path), "trace_missing")
    assert payload == {
        "ok": False,
        "trace_viewer_cli_version": "v2_4_13",
        "trace_contract_version": "v2_4_13",
        "error_code": "TRACE_NOT_FOUND",
        "message": "Trace not found: trace_missing",
        "trace": None,
    }


def test_cli_list_show_spec_and_json_output(tmp_path: Path) -> None:
    trace_id = _make_trace(tmp_path)

    out = StringIO()
    assert run_trace_viewer(["--trace-dir", str(tmp_path), "list", "--limit", "2"], stdout=out) == 0
    text = out.getvalue()
    assert "JamMate Agent traces (1)" in text
    assert trace_id in text
    assert "terminal_chat" in text

    out = StringIO()
    assert run_trace_viewer(["--trace-dir", str(tmp_path), "show", trace_id], stdout=out) == 0
    text = out.getvalue()
    assert f"Trace {trace_id}" in text
    assert "terminal_context_packet_built" in text

    out = StringIO()
    assert run_trace_viewer(["--trace-dir", str(tmp_path), "list", "--json"], stdout=out) == 0
    payload = json.loads(out.getvalue())
    assert payload["traces"][0]["trace_id"] == trace_id

    out = StringIO()
    assert run_trace_viewer(["spec"], stdout=out) == 0
    assert "JamMate Agent Trace Viewer CLI v2_4_13" in out.getvalue()


def test_cli_show_missing_trace_exits_nonzero(tmp_path: Path) -> None:
    out = StringIO()
    err = StringIO()
    code = run_trace_viewer(["--trace-dir", str(tmp_path), "show", "trace_missing"], stdout=out, stderr=err)
    assert code == 1
    assert "TRACE_NOT_FOUND: Trace not found: trace_missing" in err.getvalue()


def test_pyproject_exposes_trace_viewer_console_script() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'jammate-agent-traces = "jammate_agent.cli.trace_viewer:main"' in pyproject


def test_trace_viewer_cli_stays_agent_only_and_read_only() -> None:
    path = ROOT / "src" / "jammate_agent" / "cli" / "trace_viewer.py"
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


def test_docs_and_harness_record_trace_viewer_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agent = (ROOT / "agent.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    harness = (ROOT / "docs" / "DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "python -m jammate_agent.cli.trace_viewer" in readme
    assert "v2_4_13_agent_tool_call_preview_trace_contract" in agent
    assert "### Agent Trace Viewer CLI" in architecture
    assert "Agent Trace API / Viewer Rule" in harness
    assert "## v2_4_13 — Agent Tool Call Preview Trace Contract" in changelog
    assert "## v2_4_9 — Agent Trace Viewer CLI" in changelog
