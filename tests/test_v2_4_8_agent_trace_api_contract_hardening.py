from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.trace import TRACE_API_CONTRACT_VERSION, AgentTrace, JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app
from jammate_api.routes import agent_routes

ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "demos" / "agent_traces"


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
        return LLMProviderResult(ok=True, content="trace contract chat", provider_name="fake", model="fake-model")


def _reset_api_agent_trace_store() -> None:
    agent_routes._AGENT = None
    if TRACE_DIR.exists():
        shutil.rmtree(TRACE_DIR)


def test_trace_api_spec_route_exposes_stable_contract_and_guards() -> None:
    client = TestClient(app)
    payload = client.get("/agent/traces/spec").json()
    assert payload["ok"] is True
    spec = payload["spec"]
    assert spec["version"] == "v2_4_13"
    assert spec["trace_contract_version"] == "v2_4_13"
    assert spec["routes"]["list"] == "GET /agent/traces?limit=20"
    assert spec["routes"]["detail"] == "GET /agent/traces/{trace_id}"
    assert "trace_id" in spec["summary_fields"]
    assert "final_response_summary" in spec["detail_fields"]
    assert spec["guards"]["trace_api_executes_tools"] is False
    assert spec["guards"]["trace_api_calls_llm_provider"] is False
    assert spec["guards"]["trace_api_calls_engine_adapter"] is False


def test_trace_list_and_detail_use_versioned_summary_and_detail_contracts() -> None:
    _reset_api_agent_trace_store()
    client = TestClient(app)
    preview = client.post(
        "/agent/context/runtime/preview",
        json={"requestId": "trace_contract_001", "userInput": "解释一下 guide tones", "taskType": "coach_qa"},
    ).json()
    trace_id = preview["trace_id"]

    list_payload = client.get("/agent/traces?limit=5").json()
    assert list_payload["ok"] is True
    assert list_payload["trace_contract_version"] == "v2_4_13"
    summary = next(item for item in list_payload["traces"] if item["trace_id"] == trace_id)
    assert summary["trace_schema_version"] == "agent_trace_summary_v1"
    assert summary["request_id"] == "trace_contract_001"
    assert summary["user_input_preview"] == "解释一下 guide tones"
    assert summary["step_count"] >= 2
    assert summary["steps"] == summary["step_count"]
    assert summary["has_context_packet_summary"] is True
    assert summary["has_final_response_summary"] is True

    detail_payload = client.get(f"/agent/traces/{trace_id}").json()
    assert detail_payload["ok"] is True
    assert detail_payload["trace_contract_version"] == "v2_4_13"
    detail = detail_payload["trace"]
    assert detail["trace_schema_version"] == "agent_trace_detail_v1"
    assert detail["trace_id"] == trace_id
    assert detail["request_id"] == "trace_contract_001"
    assert detail["user_input"] == "解释一下 guide tones"
    assert detail["context_packet_summary"]["task_type"] == "coach_qa"
    assert [step["name"] for step in detail["steps"]] == ["context_runtime_packet_built", "bounded_runloop_previewed"]
    assert detail["final_response_summary"]["next_action"] in {"deterministic_workflow_fallback", "llm_required_but_provider_unavailable"}


def test_trace_not_found_response_keeps_contract_shape() -> None:
    client = TestClient(app)
    payload = client.get("/agent/traces/trace_missing_for_contract").json()
    assert payload == {
        "ok": False,
        "trace_contract_version": "v2_4_13",
        "error_code": "TRACE_NOT_FOUND",
        "message": "Trace not found: trace_missing_for_contract",
        "trace": None,
    }


def test_json_trace_store_summaries_are_generated_from_agent_trace_objects(tmp_path: Path) -> None:
    store = JsonTraceStore(tmp_path)
    logger = TraceLogger(store)
    trace = logger.start("terminal_chat", "a" * 150, request_id="req_001")
    logger.add_step(trace, "context", {"ok": True})
    logger.finish(trace, "passed", {"ok": True})

    summary = store.list_recent(limit=1)[0]
    assert summary["trace_contract_version"] == TRACE_API_CONTRACT_VERSION
    assert summary["trace_schema_version"] == "agent_trace_summary_v1"
    assert summary["user_input_preview"].endswith("…")
    assert summary["step_count"] == 1

    loaded = store.load(trace.trace_id)
    assert isinstance(loaded, AgentTrace)
    detail = loaded.to_detail_dict()
    assert detail["trace_schema_version"] == "agent_trace_detail_v1"
    assert detail["final_response_summary"] == {"ok": True}


def test_terminal_trace_export_files_can_be_read_by_hardened_trace_store(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="coach_qa", provider=EchoProvider(), trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.respond("hello trace")
    assert response["trace_id"].startswith("trace_")

    store = JsonTraceStore(tmp_path)
    summary = store.list_recent(limit=1)[0]
    detail = store.load(response["trace_id"]).to_detail_dict()
    assert summary["task_type"] == "terminal_chat"
    assert summary["trace_contract_version"] == "v2_4_13"
    assert detail["trace_contract_version"] == "v2_4_13"
    assert detail["final_response_summary"]["terminal_chat_version"] == "v2_4_13"


def test_runtime_spec_and_context_profile_manifest_include_trace_api_boundary() -> None:
    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    assert runtime_spec["trace_api_boundary"]["version"] == "v2_4_13"
    assert runtime_spec["routes"]["trace_spec"] == "GET /agent/traces/spec"
    assert "Trace API and terminal trace viewer only shape/read trace list/detail/spec responses" in runtime_spec["non_goals"][-1]

    profiles = client.get("/agent/context/profiles").json()["manifest"]
    assert profiles["trace_api_spec_route"] == "GET /agent/traces/spec"
    assert profiles["trace_detail_route"] == "GET /agent/traces/{trace_id}"


def test_harmonyos_codegen_and_smoke_pack_include_trace_contract() -> None:
    agent_types = (ROOT / "frontend_fixtures/harmonyos/types/AgentTypes.ets").read_text(encoding="utf-8")
    client_source = (ROOT / "frontend_fixtures/harmonyos/api/JamMateApiClient.ets").read_text(encoding="utf-8")
    smoke = json.loads((ROOT / "frontend_fixtures/harmonyos/smoke/smoke_pack.json").read_text(encoding="utf-8"))
    assert "AgentTraceListResponse" in agent_types
    assert "AgentTraceDetailResponse" in agent_types
    assert "AgentTraceApiSpecResponse" in agent_types
    assert "getAgentTraceSpec" in client_source
    assert "listAgentTraces" in client_source
    assert "getAgentTrace" in client_source
    optional_paths = [item["path"] for item in smoke["optional_smoke_sequence"]]
    assert "/agent/traces/spec" in optional_paths
    assert "/agent/traces" in optional_paths


def test_trace_contract_module_does_not_import_engine_or_provider_sdks() -> None:
    path = ROOT / "src" / "jammate_agent" / "core" / "trace.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
    assert not any(module in {"openai", "anthropic", "requests", "httpx"} for module in imported)


def test_direct_trace_api_contract_function_is_pure_spec() -> None:
    spec = trace_api_contract()
    assert spec["version"] == "v2_4_13"
    assert spec["guards"]["trace_api_executes_tools"] is False
    assert spec["guards"]["trace_api_calls_engine_adapter"] is False
