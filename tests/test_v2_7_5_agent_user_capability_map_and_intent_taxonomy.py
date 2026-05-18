from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
    build_user_capability_map_and_intent_taxonomy_payload,
    build_user_capability_map_and_intent_taxonomy_summary,
    context_engineering_skeleton_contract,
    user_capability_map_and_intent_taxonomy_contract,
)
from jammate_api.app import app


def test_user_capability_map_contract_defines_llm_user_scope_without_execution() -> None:
    spec = user_capability_map_and_intent_taxonomy_contract()
    assert spec["version"] == USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION == "v2_7_5"
    assert spec["spec_route"] == "GET /agent/capabilities/user-intents/spec"
    assert spec["preview_route"] == "POST /agent/capabilities/user-intents/preview"
    assert spec["execution_status"]["capability_map_enabled"] is True
    assert spec["execution_status"]["intent_taxonomy_enabled"] is True
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["tool_execution_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_calls_llm"] is False
    assert spec["guards"]["payload_executes_tool"] is False
    assert spec["current_capability_summary"]["call_accompaniment_generate"] == "disabled_for_agent"


def test_user_capability_map_payload_contains_layers_intents_and_boundaries() -> None:
    payload_obj = build_user_capability_map_and_intent_taxonomy_payload(
        {"userInput": "今天该练什么？", "midiBase64": "SHOULD_NOT_LEAK", "localMidiPath": "/tmp/secret.mid"},
        trace_id="trace_capability",
    )
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_5"
    assert payload["validation"]["status"] == "capability_map_ready"
    assert payload["validation"]["has_today_practice_guidance_intent"] is True
    assert payload["validation"]["has_routine_config_prepare_intent"] is True
    assert payload["routine_agent_boundaries"]["routine_end_page_agent_recommendation_card_enabled"] is False
    assert payload["routine_agent_boundaries"]["client_decides_presentation"] is True
    assert payload["side_effect_policy"]["autonomous_execution_enabled"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False

    intent_types = {item["intent_type"] for item in payload["intent_taxonomy"]}
    assert "today_practice_guidance" in intent_types
    assert "practice_plan_generation" in intent_types
    assert "routine_config_prepare" in intent_types
    assert "playback_prepare_guarded" in intent_types

    forbidden_layer = next(item for item in payload["capability_layers"] if item["layer_id"] == "forbidden_direct_actions")
    assert forbidden_layer["current_status"] == "forbidden_for_llm_autonomy"
    assert "直接调用 /accompaniment/generate" in forbidden_layer["examples"]

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/secret.mid" not in serialized

    summary = build_user_capability_map_and_intent_taxonomy_summary(payload=payload_obj)
    assert summary["capability_layer_count"] >= 4
    assert summary["intent_type_count"] >= 6
    assert summary["has_today_practice_guidance_intent"] is True
    assert summary["llm_called"] is False
    assert summary["tool_executed"] is False


def test_api_user_capability_map_routes_are_contract_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/capabilities/user-intents/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_5"

    response = client.post("/agent/capabilities/user-intents/preview", json={"userInput": "今天该练什么？"}).json()
    assert response["ok"] is True
    assert response["user_capability_map_and_intent_taxonomy_version"] == "v2_7_5"
    assert response["user_capability_map_summary"]["has_today_practice_guidance_intent"] is True
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_terminal_user_capability_map_command_traces_payload(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.user_capability_map({"userInput": "帮我准备一个 20 分钟伴奏"})
    assert response["ok"] is True
    assert response["user_capability_map_summary"]["has_routine_config_prepare_intent"] is True
    assert response["llm_called"] is False
    assert response["tool_executed"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_user_capability_map" for item in traces)


def test_context_engineering_skeleton_includes_capability_map_without_engine_dependency() -> None:
    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["user_capability_map_and_intent_taxonomy"]["version"] == "v2_7_5"
    assert skeleton["guards"]["llm_called"] is False
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_V2_7_5.md"
    assert "from jammate_engine" not in tool_invocation
    assert docs_path.exists()
