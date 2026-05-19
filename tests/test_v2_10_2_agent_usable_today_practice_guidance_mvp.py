from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    AGENT_CONTEXT_DB_PATH_ENV_VAR,
    AGENT_USABLE_TODAY_PRACTICE_GUIDANCE_MVP_VERSION,
    build_agent_usable_today_practice_guidance_mvp_payload,
    build_agent_usable_today_practice_guidance_mvp_summary,
    build_context_persistence_sqlite_backend_store_payload,
    agent_usable_today_practice_guidance_mvp_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_usable_today_001",
        "currentGoal": "把 Medium Swing ii-V-I comping 练稳",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["ii-V-I", "comping", "time feel"],
        "comfortableTempoRanges": {"medium_swing": [92, 116]},
        "avoid": ["too_fast_tempo"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_usable_today_001",
        "title": "Usable Agent MVP Practice Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_swing_guide", "title": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_bossa_review", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _history() -> list[dict]:
    return [
        {"sessionId": "session_usable_today_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 780, "completed": True},
    ]


def _guidance_output() -> dict:
    return {
        "guidance_mode": "continue_original_plan",
        "summary": "今天继续 Medium Swing guide-tone comping，先做 15 分钟稳定练习。",
        "recommended_focus": "Medium Swing ii-V-I guide-tone voice leading",
        "recommended_blocks": [
            {"blockId": "block_swing_guide", "title": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "goal": "稳定 3/7 声部连接"},
        ],
        "routine_candidates": [
            {"candidateId": "routine_usable_today", "routineName": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "practiceGoal": "稳定 comping"},
        ],
        "profile_considerations": "使用已恢复 profile/plan/history，避免过快速度。",
        "user_confirmation_required": True,
        "next_client_actions": ["show_guidance", "present_routine_candidate"],
    }


def _provider_result() -> dict:
    return {"ok": True, "provider_name": "fixture", "model": "fixture-model", "content": json.dumps(_guidance_output(), ensure_ascii=False)}


class _FakeProvider:
    def status(self) -> dict:
        return {"provider_class": "FakeProvider", "terminal_chat_enabled": True, "api_key_value": "SECRET_SHOULD_NOT_LEAK"}

    def generate(self, envelope) -> LLMProviderResult:  # noqa: ANN001
        assert envelope.runtime_policy["tool_execution_enabled"] is False
        return LLMProviderResult(ok=True, content=json.dumps(_guidance_output(), ensure_ascii=False), provider_name="fake", model="fake-model")


def _approved_store_args(db_path: Path, *, idempotency_key: str = "idem_usable_today") -> dict:
    return {
        "backendPersistenceEnabled": True,
        "executeBackendPersistence": True,
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "traceId": "trace_usable_today_store",
        "idempotencyKey": idempotency_key,
        "userId": "dev_user",
        "candidateKind": "practice_plan_persistence_candidate",
        "candidateId": "candidate_usable_today_001",
        "confirmationId": "confirmation_usable_today_001",
        "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "routineHistoryRecords": _history(),
    }


def _write_store(db_path: Path, *, idempotency_key: str = "idem_usable_today") -> None:
    payload = build_context_persistence_sqlite_backend_store_payload(_approved_store_args(db_path, idempotency_key=idempotency_key)).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["backend_database_written"] is True


def test_usable_today_practice_guidance_mvp_contract_is_product_facing() -> None:
    spec = agent_usable_today_practice_guidance_mvp_contract()
    assert spec["version"] == AGENT_USABLE_TODAY_PRACTICE_GUIDANCE_MVP_VERSION == "v2_10_2"
    assert spec["spec_route"] == "GET /agent/context/usable-today-practice-guidance-mvp/spec"
    assert spec["preview_route"] == "POST /agent/context/usable-today-practice-guidance-mvp/preview"
    assert spec["context_db_path_env_var"] == AGENT_CONTEXT_DB_PATH_ENV_VAR
    assert spec["execution_status"]["ordinary_terminal_chat_entry_enabled"] is True
    assert spec["execution_status"]["sqlite_context_autoload_when_db_path_configured"] is True
    assert spec["execution_status"]["database_write_enabled"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False


def test_usable_today_practice_guidance_without_db_returns_clear_no_context_message(tmp_path: Path) -> None:
    payload_obj = build_agent_usable_today_practice_guidance_mvp_payload({"userInput": "今天该练什么？"})
    payload = payload_obj.to_dict()
    summary = build_agent_usable_today_practice_guidance_mvp_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_10_2"
    assert payload["context_source"] == "none"
    assert payload["sqlite_readback_attempted"] is False
    assert payload["validation"]["status"] == "usable_today_practice_guidance_needs_context_or_provider"
    assert payload["terminal_response"]["content"].startswith("现在还没有可恢复的练习上下文")
    assert summary["accepted"] is True
    assert summary["guidance_action_card_is_valid"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert not list(tmp_path.iterdir())


def test_usable_today_practice_guidance_reads_sqlite_and_builds_display_guidance(tmp_path: Path) -> None:
    db_path = tmp_path / "usable_today_agent_context.sqlite"
    _write_store(db_path)

    payload_obj = build_agent_usable_today_practice_guidance_mvp_payload(
        {
            "userInput": "今天该练什么？",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "providerResult": _provider_result(),
            "availableMinutes": 25,
        },
        trace_id="trace_usable_today_mvp",
    )
    payload = payload_obj.to_dict()
    summary = build_agent_usable_today_practice_guidance_mvp_summary(payload=payload_obj)

    assert payload["validation"]["status"] == "usable_today_practice_guidance_ready"
    assert payload["context_source"] == "sqlite_backend"
    assert payload["sqlite_readback_attempted"] is True
    assert payload["backend_database_read"] is True
    assert payload["sqlite_connection_created"] is True
    assert payload["sqlite_rows_read"] == 1
    assert payload["validation"]["guidance_action_card_is_valid"] is True
    assert payload["terminal_response"]["routine_candidate_count"] == 1
    assert summary["sqlite_context_recovered"] is True
    assert summary["routine_candidate_count"] == 1
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["sqlite_tables_created"] is False
    assert payload["sqlite_rows_written"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False


def test_terminal_ordinary_today_question_auto_uses_sqlite_context(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_usable_today.sqlite"
    _write_store(db_path)
    session = TerminalChatSession(provider=_FakeProvider(), context_db_path=str(db_path))

    response = session.respond("今天该练什么？")

    assert response["ok"] is True
    assert response["agent_usable_today_practice_guidance_mvp_version"] == "v2_10_2"
    assert response["payload_kind"] == "agent_usable_today_practice_guidance_mvp"
    assert response["context_source"] == "sqlite_backend"
    assert response["sqlite_readback_attempted"] is True
    assert response["backend_database_read"] is True
    assert response["guidance_preview_ready"] is True
    assert response["routine_candidate_count"] == 1
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False
    assert "SECRET_SHOULD_NOT_LEAK" not in json.dumps(response, ensure_ascii=False)


def test_api_usable_today_practice_guidance_mvp_preview_reads_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "api_usable_today.sqlite"
    _write_store(db_path)
    client = TestClient(app)

    spec = client.get("/agent/context/usable-today-practice-guidance-mvp/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_10_2"

    response = client.post(
        "/agent/context/usable-today-practice-guidance-mvp/preview",
        json={"userInput": "今天该练什么？", "sqliteDbPath": str(db_path), "environment": "test", "providerResult": _provider_result()},
    ).json()
    assert response["ok"] is True
    assert response["agent_usable_today_practice_guidance_mvp_version"] == "v2_10_2"
    assert response["context_source"] == "sqlite_backend"
    assert response["sqlite_readback_attempted"] is True
    assert response["guidance_preview_ready"] is True
    assert response["backend_database_read"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False


def test_context_and_runtime_manifests_advertise_usable_today_practice_guidance_mvp() -> None:
    manifest = context_profile_manifest()
    assert manifest["agent_usable_today_practice_guidance_mvp_spec_route"] == "GET /agent/context/usable-today-practice-guidance-mvp/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["agent_usable_today_practice_guidance_mvp"] == "POST /agent/context/usable-today-practice-guidance-mvp/preview"
    assert runtime["agent_usable_today_practice_guidance_mvp"]["version"] == "v2_10_2"
    assert runtime["agent_usable_today_practice_guidance_mvp"]["execution_status"]["ordinary_terminal_chat_entry_enabled"] is True
    assert CapabilityManifest().to_dict()["supports_agent_usable_today_practice_guidance_mvp"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["agent_usable_today_practice_guidance_mvp_version"] == "v2_10_2"


def test_run_interactive_once_with_context_db_path_prints_usable_mvp_summary(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    db_path = tmp_path / "once_usable_today.sqlite"
    _write_store(db_path)
    exit_code = run_interactive_chat(["--context-db-path", str(db_path), "--once", "今天该练什么？"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "UsableTodayPracticeGuidanceMVP>" in out
    assert "version: v2_10_2" in out
    assert "sqlite_readback_attempted: True" in out
    assert "routine_start_enabled: False" in out
    assert "accompaniment_generate_call_enabled: False" in out
