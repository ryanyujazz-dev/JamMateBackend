from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
    build_today_practice_guidance_terminal_chat_e2e_payload,
    build_today_practice_guidance_terminal_chat_e2e_summary,
    context_engineering_skeleton_contract,
    detect_today_practice_guidance_intent,
    today_practice_guidance_terminal_chat_e2e_contract,
)
from jammate_api.app import app


def _safe_guidance_output() -> dict:
    return {
        "guidance_mode": "continue_original_plan",
        "summary": "今天建议继续原计划里的 Medium Swing ii-V-I，练 15 分钟 guide-tone voice leading。",
        "recommended_focus": "Medium Swing guide-tone voice leading",
        "recommended_blocks": [
            {
                "blockId": "day2_swing",
                "title": "ii-V-I Medium Swing",
                "goal": "Guide-tone voice leading",
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
            }
        ],
        "routine_candidates": [
            {
                "candidateId": "routine_day2_swing",
                "routineName": "ii-V-I Medium Swing",
                "durationMinutes": 15,
                "style": "medium_swing",
                "tempo": 104,
                "loopEnabled": True,
            }
        ],
        "user_confirmation_required": True,
        "next_client_actions": ["show_guidance", "present_routine_candidate"],
    }


def _provider_result() -> dict:
    return {"ok": True, "provider_name": "fixture", "model": "fixture-model", "content": json.dumps(_safe_guidance_output(), ensure_ascii=False)}


class _FakeProvider:
    def status(self) -> dict:
        return {"provider_class": "FakeProvider", "terminal_chat_enabled": True, "api_key_value": "SECRET_SHOULD_NOT_LEAK"}

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001 - protocol-style fake for tests.
        assert envelope.runtime_policy["tool_execution_enabled"] is False
        assert (envelope.context_packet.get("task_type") or "") == "today_practice_guidance"
        return LLMProviderResult(ok=True, content=_provider_result()["content"], provider_name="fake", model="fake-model")


def test_today_practice_guidance_terminal_chat_e2e_contract_routes_ordinary_turns() -> None:
    spec = today_practice_guidance_terminal_chat_e2e_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION == "v2_7_9"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/terminal-chat/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview"
    assert spec["execution_status"]["ordinary_chat_intent_detection_enabled"] is True
    assert spec["execution_status"]["provider_boundary_enabled"] is True
    assert spec["execution_status"]["output_validation_required"] is True
    assert spec["execution_status"]["card_display_only"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["calls_accompaniment_generate"] is False
    assert spec["uses_contracts"]["today_practice_guidance_action_card"] == "v2_7_8"


def test_today_practice_intent_detector_is_narrow() -> None:
    zh = detect_today_practice_guidance_intent("今天该练什么？")
    assert zh["is_today_practice_guidance_intent"] is True
    assert zh["intent_type"] == "today_practice_guidance"
    assert zh["routine_start_enabled"] is False

    en = detect_today_practice_guidance_intent("What should I practice today?")
    assert en["is_today_practice_guidance_intent"] is True

    other = detect_today_practice_guidance_intent("解释一下 ii-V-I 为什么重要")
    assert other["is_today_practice_guidance_intent"] is False


def test_payload_builds_display_only_action_card_from_ordinary_terminal_turn() -> None:
    payload_obj = build_today_practice_guidance_terminal_chat_e2e_payload(
        {"userInput": "今天该练什么？", "providerResult": _provider_result()},
        trace_id="trace_terminal_today",
    )
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_7_9"
    assert payload["detected_intent"]["is_today_practice_guidance_intent"] is True
    assert payload["action_card_summary"]["is_valid"] is True
    assert payload["action_card_summary"]["routine_candidate_count"] == 1
    assert payload["terminal_response"]["action_card_available"] is True
    assert payload["terminal_response"]["requires_separate_user_confirmation_before_routine_start"] is True
    assert payload["tool_executed"] is False
    assert payload["route_called"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["accompaniment_generate_call_enabled"] is False
    assert payload["routine_start_enabled"] is False

    summary = build_today_practice_guidance_terminal_chat_e2e_summary(payload=payload_obj)
    assert summary["detected_today_practice_guidance_intent"] is True
    assert summary["action_card_is_valid"] is True
    assert summary["card_display_only"] is True


def test_terminal_ordinary_chat_today_question_routes_to_guidance_action_card(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(provider=_FakeProvider(), trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    response = session.respond("今天该练什么？")
    assert response["ok"] is True
    assert response["task_type"] == "today_practice_guidance"
    assert response["ordinary_terminal_chat_guidance_e2e"] is True
    assert response["today_practice_guidance_terminal_chat_e2e_summary"]["action_card_is_valid"] is True
    assert response["today_practice_guidance_action_card_summary"]["routine_candidate_count"] == 1
    assert response["llm_called"] is True
    assert response["tool_executed"] is False
    assert response["routine_start_enabled"] is False
    serialized = json.dumps(response, ensure_ascii=False)
    assert "SECRET_SHOULD_NOT_LEAK" not in serialized

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    assert any(item["task_type"] == "terminal_today_practice_guidance_chat_e2e" for item in traces)


def test_api_terminal_chat_e2e_routes_are_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/terminal-chat/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_7_9"

    response = client.post(
        "/agent/context/today-practice-guidance/terminal-chat/e2e-preview",
        json={"userInput": "今天该练什么？", "providerResult": _provider_result(), "traceId": "api_trace_terminal_today"},
    ).json()
    assert response["ok"] is True
    assert response["today_practice_guidance_terminal_chat_e2e_version"] == "v2_7_9"
    assert response["today_practice_guidance_terminal_chat_e2e_summary"]["action_card_is_valid"] is True
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["routine_start_enabled"] is False


def test_run_interactive_once_prints_terminal_guidance_summary(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    # This smoke uses the disabled provider path. It still routes the ordinary
    # terminal user turn into the guarded today-practice chain and prints the
    # side-effect-free summary instead of generic chat candidate extraction.
    exit_code = run_interactive_chat(["--once", "今天该练什么？"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "TodayPracticeGuidanceChatE2E>" in captured
    assert "routine_start_enabled: False" in captured
    assert "accompaniment_generate_call_enabled: False" in captured


def test_context_builder_and_skeleton_reference_terminal_chat_e2e_without_engine_dependency() -> None:
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    data = packet.to_dict()
    assert data["capabilities"]["supports_today_practice_guidance_terminal_chat_e2e"] is True
    assert data["routing_hints"]["today_practice_guidance_terminal_chat_e2e_version"] == "v2_7_9"

    skeleton = context_engineering_skeleton_contract()
    assert skeleton["included_boundaries"]["today_practice_guidance_terminal_chat_e2e"]["version"] == "v2_7_9"
    assert skeleton["guards"]["midi_asset_created"] is False

    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    docs_path = root / "docs" / "AGENT_TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_V2_7_9.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert docs_path.exists()
