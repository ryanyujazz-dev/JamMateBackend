from __future__ import annotations

import json

from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    build_today_practice_guidance_provider_boundary_e2e_payload,
    build_today_practice_guidance_prompt_contract_payload,
    build_today_practice_guidance_terminal_chat_e2e_payload,
)


class _PlainTextProvider:
    def status(self) -> dict:
        return {"provider_class": "PlainTextProvider", "terminal_chat_enabled": True}

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001
        assert envelope.runtime_policy["tool_execution_enabled"] is False
        return LLMProviderResult(
            ok=True,
            content="今天建议先练 20 分钟 Medium Swing ii-V-I，再做 5 分钟复盘。",
            provider_name="fake",
            model="plain-text-model",
        )


class _PartialJsonProvider:
    def status(self) -> dict:
        return {"provider_class": "PartialJsonProvider", "terminal_chat_enabled": True}

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001
        return LLMProviderResult(
            ok=True,
            content=json.dumps({"summary": "今天建议继续原计划，控制速度，不要引入太多新概念。"}, ensure_ascii=False),
            provider_name="fake",
            model="partial-json-model",
        )


def test_prompt_contract_demands_json_only_and_includes_required_shape() -> None:
    payload = build_today_practice_guidance_prompt_contract_payload({"userInput": "今天该练什么"})
    data = payload.to_dict()
    messages = data["prompt_messages"]
    system_content = messages[0]["content"]
    assert "Return JSON only" in system_content
    assert "Minimal valid shape" in system_content
    assert "user_confirmation_required" in system_content
    assert "next_client_actions" in system_content
    assert data["validation"]["prompt_message_count"] == 4


def test_provider_boundary_coerces_plain_text_provider_output_to_display_only_guidance() -> None:
    payload = build_today_practice_guidance_provider_boundary_e2e_payload(
        {"userInput": "今天该练什么", "callProvider": True},
        provider=_PlainTextProvider(),
    ).to_dict()
    assert payload["validation"]["output_validation_is_valid"] is True
    assert payload["validation"]["provider_content_parsed"] is True
    assert "provider_returned_plain_text_coerced_to_display_only_guidance" in payload["validation"]["provider_output_coercion_warnings"]
    normalized = payload["e2e_summary"]["normalized_guidance_output"]
    assert normalized["guidance_mode"] == "fallback_without_plan"
    assert normalized["summary"].startswith("今天建议先练")
    assert normalized["routine_candidates"] == []
    assert normalized["user_confirmation_required"] is True
    assert normalized["next_client_actions"] == ["show_guidance"]
    assert payload["routine_start_enabled"] is False
    assert payload["accompaniment_generate_call_enabled"] is False


def test_terminal_today_practice_turn_no_longer_blocks_when_provider_returns_plain_text() -> None:
    payload = build_today_practice_guidance_terminal_chat_e2e_payload(
        {"userInput": "今天该练什么", "callProvider": True},
        provider=_PlainTextProvider(),
    ).to_dict()
    assert payload["action_card_summary"]["is_valid"] is True
    assert payload["terminal_response"]["action_card_available"] is True
    assert "Guidance output was blocked" not in payload["terminal_response"]["content"]
    assert "今天建议先练" in payload["terminal_response"]["content"]
    assert payload["tool_executed"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False


def test_partial_json_provider_output_gets_required_safe_defaults() -> None:
    payload = build_today_practice_guidance_provider_boundary_e2e_payload(
        {"userInput": "今天该练什么", "callProvider": True},
        provider=_PartialJsonProvider(),
    ).to_dict()
    assert payload["validation"]["output_validation_is_valid"] is True
    warnings = payload["validation"]["provider_output_coercion_warnings"]
    assert "guidance_mode_filled_from_provider_output" in warnings
    assert "recommended_focus_filled_from_provider_output" in warnings
    normalized = payload["e2e_summary"]["normalized_guidance_output"]
    assert normalized["guidance_mode"] == "fallback_without_plan"
    assert normalized["recommended_focus"] == "今日练习安排"
    assert normalized["user_confirmation_required"] is True
