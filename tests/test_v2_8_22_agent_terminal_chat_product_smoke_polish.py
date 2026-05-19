from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.llm_provider import LLMProviderConfig, OpenAICompatibleChatProvider
from jammate_agent.core.tool_invocation import (
    TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION,
    build_today_practice_guidance_terminal_product_smoke_polish_payload,
    build_today_practice_guidance_terminal_product_smoke_polish_summary,
    today_practice_guidance_terminal_product_smoke_polish_contract,
)
from jammate_api.app import app


def _ready_provider_status() -> dict:
    return OpenAICompatibleChatProvider(
        LLMProviderConfig(
            provider_name="openai_compatible",
            model="test-model",
            api_key_configured=True,
            network_calls_enabled=True,
            api_key_value="test-secret-value",
        )
    ).status()


def test_terminal_product_smoke_contract_exposes_routes_command_and_guards() -> None:
    spec = today_practice_guidance_terminal_product_smoke_polish_contract()
    assert spec["version"] == TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION == "v2_8_22"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/terminal-product-smoke/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/terminal-product-smoke/preview"
    assert spec["terminal_command"] == "/terminal-product-smoke [json_payload]"
    assert spec["execution_status"]["terminal_product_smoke_preview_enabled"] is True
    assert spec["execution_status"]["calls_llm_provider"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_starts_routine"] is False


def test_terminal_product_smoke_payload_is_redacted_ready_and_side_effect_free() -> None:
    payload_obj = build_today_practice_guidance_terminal_product_smoke_polish_payload(
        {"sampleUserInput": "今天该练什么？"},
        provider_status=_ready_provider_status(),
    )
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_terminal_product_smoke_polish_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_22"
    assert payload["readiness"]["terminal_chat_provider_ready"] is True
    assert payload["readiness"]["readiness_status"] == "ready_for_manual_llm_smoke"
    assert "test-secret-value" not in str(payload)
    assert summary["terminal_chat_provider_ready"] is True
    assert summary["passed_check_count"] == summary["check_count"]
    assert summary["ordinary_chinese_guidance_route_available"] is True
    assert summary["persisted_context_memory_controls_available"] is True
    assert payload["llm_called"] is False
    assert payload["storage_written"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["routine_start_enabled"] is False


def test_terminal_product_smoke_payload_gives_guarded_setup_hint_when_provider_missing() -> None:
    payload_obj = build_today_practice_guidance_terminal_product_smoke_polish_payload({})
    payload = payload_obj.to_dict()
    summary = build_today_practice_guidance_terminal_product_smoke_polish_summary(payload=payload_obj)

    assert payload["readiness"]["terminal_chat_provider_ready"] is False
    assert payload["readiness"]["next_manual_step"] == "run setup then doctor before ordinary Chinese prompt"
    assert summary["readiness_status"] == "configuration_required_but_preview_commands_available"
    assert "provider_not_ready_manual_llm_smoke_requires_setup_or_env_config" in summary["warnings"]


def test_terminal_product_smoke_session_command_uses_provider_status_without_calling_llm() -> None:
    session = TerminalChatSession(provider=OpenAICompatibleChatProvider(LLMProviderConfig(provider_name="openai_compatible", model="test-model", api_key_configured=True, network_calls_enabled=True, api_key_value="secret")))
    response = session.terminal_product_smoke_polish({})
    assert response["ok"] is True
    summary = response["today_practice_guidance_terminal_product_smoke_polish_summary"]
    assert summary["terminal_chat_provider_ready"] is True
    assert response["llm_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_product_smoke_cli_command_is_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    exit_code = run_interactive_chat(["--once", "/terminal-product-smoke"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "TerminalProductSmokePolish>" in out
    assert "ordinary_chinese_guidance_route_available: True" in out
    assert "routine_start_enabled: false" in out
    assert "engine_adapter_called: false" in out


def test_terminal_product_smoke_preview_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/terminal-product-smoke/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_22"
    response = client.post("/agent/context/today-practice-guidance/terminal-product-smoke/preview", json={"sampleUserInput": "今天该练什么？"}).json()
    assert response["ok"] is True
    summary = response["today_practice_guidance_terminal_product_smoke_polish_summary"]
    assert summary["ordinary_chinese_guidance_route_available"] is True
    assert response["llm_called"] is False
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_product_smoke_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert manifest["today_practice_guidance_terminal_product_smoke_polish_spec_route"] == "GET /agent/context/today-practice-guidance/terminal-product-smoke/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["today_practice_guidance_terminal_product_smoke_polish"] == "POST /agent/context/today-practice-guidance/terminal-product-smoke/preview"
    assert runtime["today_practice_guidance_terminal_product_smoke_polish"]["version"] == "v2_8_22"
    assert CapabilityManifest().to_dict()["supports_today_practice_guidance_terminal_product_smoke_polish"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["today_practice_guidance_terminal_product_smoke_polish_version"] == "v2_8_22"


def test_terminal_product_smoke_does_not_import_engine_or_touch_frontend_fixture_files() -> None:
    root = Path(__file__).resolve().parents[1]
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_TERMINAL_CHAT_PRODUCT_SMOKE_POLISH_V2_8_22.md"
    assert "from jammate_engine" not in terminal_chat
    assert "from jammate_engine" not in tool_invocation
    assert doc_path.exists()
