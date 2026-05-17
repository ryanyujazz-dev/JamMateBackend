from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.contracts import agent_capability_manifest
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def test_context_runtime_spec_declares_preview_only_bounded_runloop() -> None:
    client = TestClient(app)
    response = client.get("/agent/context/runtime/spec")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    spec = payload["spec"]
    assert spec["version"] == "v2_4_1"
    assert spec["routes"]["preview"] == "POST /agent/context/runtime/preview"
    assert spec["runloop"]["execution_status"]["llm_calls_enabled"] is False
    assert spec["runloop"]["execution_status"]["autonomous_tool_execution_enabled"] is False
    assert "No real LLM network call in v2_4_1." in spec["non_goals"]


def test_context_runtime_preview_builds_traceable_task_scoped_packet() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/context/runtime/preview",
        json={
            "requestId": "ctx_preview_test_001",
            "userInput": "我想练 Blue Bossa 20分钟，帮我安排一下",
            "taskType": "immediate_practice_playback",
            "durationMinutes": 20,
            "instrument": "piano",
            "clientContext": {
                "currentScreen": "practice_home",
                "availableMinutes": 20,
                "timezone": "America/Los_Angeles",
                "locale": "zh-CN",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["task_type"] == "immediate_practice_playback"

    context = payload["context_packet"]
    assert context["context_runtime_version"] == "v2_4_1"
    assert context["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]
    assert context["output_contract"]["schema"] == "PlaybackPrepareResult"
    assert context["constraints"]["harmonyos_local_timer_owns_practice_duration"] is True
    assert context["routing_hints"]["engine_boundary"] == "Agent may use engine only through jammate_agent.adapters."

    preview = payload["runloop_preview"]
    assert preview["runtime_mode"] == "preview_only"
    assert preview["tool_execution_enabled"] is False
    assert preview["allowed_tools"] == ["chart_resolve", "agent_playback_prepare"]
    assert preview["next_action"] == "deterministic_workflow_fallback"

    trace_id = payload["trace_id"]
    trace_response = client.get(f"/agent/traces/{trace_id}")
    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]
    assert trace["request_id"] == "ctx_preview_test_001"
    assert trace["task_type"] == "llm_context_runtime_preview"
    assert {step["name"] for step in trace["steps"]} >= {
        "context_runtime_packet_built",
        "bounded_runloop_previewed",
    }


def test_coach_qa_profile_reports_llm_required_but_does_not_execute_tools() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/context/runtime/preview",
        json={"userInput": "解释一下 altered dominant 什么时候用", "taskType": "coach_qa"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "coach_qa"
    assert payload["context_packet"]["runtime_policy"]["llm_required"] is True
    assert payload["runloop_preview"]["next_action"] == "llm_required_but_unavailable"
    assert payload["runloop_preview"]["tool_execution_enabled"] is False


def test_context_builder_runtime_packet_stays_agent_side_and_task_scoped() -> None:
    packet = ContextBuilder().build(
        "practice_plan_generation",
        "我今天有45分钟练Misty",
        request_id="ctx_builder_unit",
        available_minutes=45,
        instrument="piano",
        client_context={"current_screen": "practice_home", "available_minutes": 45},
    )
    data = packet.to_dict()
    assert data["context_runtime_version"] == "v2_4_1"
    assert data["allowed_tools"] == ["agent_practice_plan"]
    assert data["runtime_policy"]["tool_loop_mode"] == "bounded_preview"
    assert data["constraints"]["must_preserve_engine_independence"] is True
    assert "jammate_engine" not in ContextBuilder.__module__


def test_capability_manifest_includes_context_runtime_preview_tool() -> None:
    manifest = agent_capability_manifest()
    tool_names = {tool["name"] for tool in manifest["available_tools"]}
    assert "agent_llm_context_runtime_preview" in tool_names
    preview_tool = next(tool for tool in manifest["available_tools"] if tool["name"] == "agent_llm_context_runtime_preview")
    assert preview_tool["input_contract"]["route"] == "POST /agent/context/runtime/preview"
    assert preview_tool["output_contract"]["runtime_mode"] == "preview_only"


def test_agent_engine_dependency_boundary_remains_adapter_only_for_context_runtime() -> None:
    offenders: list[str] = []
    for path in sorted((ROOT / "src" / "jammate_agent").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/adapters/" in rel:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = [node.module]
            else:
                imported = []
            for module in imported:
                if module == "jammate_engine" or module.startswith("jammate_engine."):
                    offenders.append(rel)
    assert offenders == []
