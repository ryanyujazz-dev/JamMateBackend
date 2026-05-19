from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    AGENT_ROUTINE_COMPLETION_RECORD_TO_BACKEND_CONTEXT_WRITE_MVP_VERSION,
    build_agent_routine_completion_record_to_backend_context_write_mvp_payload,
    build_agent_routine_completion_record_to_backend_context_write_mvp_summary,
    build_agent_usable_today_practice_guidance_mvp_payload,
    build_context_persistence_sqlite_backend_store_payload,
    agent_routine_completion_record_to_backend_context_write_mvp_contract,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_completion_001",
        "currentGoal": "稳定 Medium Swing comping 与 Bossa groove",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["comping", "time feel"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_completion_001",
        "title": "Completion MVP Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_swing", "title": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _completion_record() -> dict:
    return {
        "sessionId": "session_completion_001",
        "title": "Medium Swing guide-tone comping",
        "style": "medium_swing",
        "tempo": 104,
        "actualSeconds": 900,
        "completed": True,
        "completedAtUtc": "2026-05-19T20:00:00+00:00",
        "practiceGoal": "稳定 3/7 声部连接",
    }


def _guidance_output() -> dict:
    return {
        "guidance_mode": "adjust_based_on_history",
        "summary": "已参考刚完成的 Medium Swing 练习，今天下一步转到 Bossa comping review。",
        "recommended_focus": "Bossa comping review after completed swing block",
        "recommended_blocks": [
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "goal": "巩固 bossa piano rhythm"},
        ],
        "routine_candidates": [
            {"candidateId": "routine_after_completion", "routineName": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "practiceGoal": "承接已完成记录"},
        ],
        "adjustment_reason": "recent routine history shows the swing block was completed",
        "profile_considerations": "保持用户偏好的 swing/bossa 方向。",
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


def _seed_profile_plan(db_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_store_payload(
        {
            "backendPersistenceEnabled": True,
            "executeBackendPersistence": True,
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "userDecision": "approved",
            "confirmationStatus": "user_approved_future_executor_required",
            "traceId": "trace_seed_profile_plan",
            "idempotencyKey": "idem_seed_profile_plan",
            "userId": "user_completion_001",
            "candidateKind": "practice_plan_persistence_candidate",
            "candidateId": "candidate_seed_plan",
            "confirmationId": "confirmation_seed_plan",
            "entities": ["user_practice_profile", "active_practice_plan"],
            "userPracticeProfile": _profile(),
            "practicePlan": _plan(),
        }
    ).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["backend_database_written"] is True


def _write_args(db_path: Path, *, confirmed: bool = True, idem: str = "idem_completion_001") -> dict:
    return {
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "userId": "user_completion_001",
        "clientConfirmedRecordWrite": confirmed,
        "traceId": "trace_completion_write",
        "idempotencyKey": idem,
        "routineCompletionRecord": _completion_record(),
    }


def test_routine_completion_record_write_mvp_contract_is_product_facing() -> None:
    spec = agent_routine_completion_record_to_backend_context_write_mvp_contract()

    assert spec["version"] == AGENT_ROUTINE_COMPLETION_RECORD_TO_BACKEND_CONTEXT_WRITE_MVP_VERSION == "v2_10_3"
    assert spec["spec_route"] == "GET /agent/context/routine-completion-record-to-backend-context-write-mvp/spec"
    assert spec["execute_route"] == "POST /agent/context/routine-completion-record-to-backend-context-write-mvp/execute"
    assert spec["execution_status"]["database_write_enabled_after_explicit_client_confirmation"] is True
    assert spec["execution_status"]["writes_routine_history_records"] is True
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_writes_harmonyos_local_state"] is False


def test_completion_write_without_confirmation_is_blocked_and_does_not_create_db(tmp_path: Path) -> None:
    db_path = tmp_path / "blocked_completion.sqlite"

    payload_obj = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(_write_args(db_path, confirmed=False))
    payload = payload_obj.to_dict()
    summary = build_agent_routine_completion_record_to_backend_context_write_mvp_summary(payload=payload_obj)

    assert payload["validation"]["status"] == "routine_completion_record_backend_context_write_blocked"
    assert "backend_persistence_enabled_must_be_true" in payload["validation"]["blocked_reasons"]
    assert summary["completion_record_persisted"] is False
    assert payload["backend_database_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert not db_path.exists()


def test_completion_write_persists_routine_history_and_verifies_readback(tmp_path: Path) -> None:
    db_path = tmp_path / "completion_write.sqlite"

    payload_obj = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(_write_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_agent_routine_completion_record_to_backend_context_write_mvp_summary(payload=payload_obj)

    assert payload["validation"]["status"] == "routine_completion_record_backend_context_write_ready"
    assert payload["routine_completion_record"]["sessionId"] == "session_completion_001"
    assert payload["context_store_summary"]["candidate_kind"] == "routine_history_persistence_candidate"
    assert payload["context_store_payload"]["requested_entities"] == ["routine_history_records"]
    assert summary["completion_record_persisted"] is True
    assert summary["backend_database_written"] is True
    assert summary["backend_database_read"] is True
    assert summary["sqlite_rows_written"] is True
    assert summary["sqlite_rows_read"] == 1
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False


def test_completion_write_is_idempotent_for_same_completion_record(tmp_path: Path) -> None:
    db_path = tmp_path / "completion_idempotent.sqlite"

    first = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(_write_args(db_path)).to_dict()
    second = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(_write_args(db_path)).to_dict()

    assert first["validation"]["status"] == "routine_completion_record_backend_context_write_ready"
    assert second["validation"]["status"] == "routine_completion_record_backend_context_write_idempotent_replay"
    assert second["idempotent_replay"] is True
    assert second["backend_database_written"] is False
    assert second["validation"]["completion_record_persisted"] is True


def test_completion_write_then_ordinary_today_guidance_reads_real_history(tmp_path: Path) -> None:
    db_path = tmp_path / "completion_to_guidance.sqlite"
    _seed_profile_plan(db_path)

    write_payload = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(_write_args(db_path)).to_dict()
    assert write_payload["validation"]["completion_record_persisted"] is True

    guidance_obj = build_agent_usable_today_practice_guidance_mvp_payload(
        {
            "userInput": "今天该练什么？",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "providerResult": _provider_result(),
        },
        trace_id="trace_guidance_after_completion",
    )
    guidance = guidance_obj.to_dict()

    assert guidance["validation"]["status"] == "usable_today_practice_guidance_ready"
    assert guidance["context_source"] == "sqlite_backend"
    assert guidance["sqlite_rows_read"] == 2
    assert guidance["validation"]["guidance_action_card_is_valid"] is True
    assert guidance["terminal_response"]["routine_candidate_count"] == 1
    assert guidance["backend_database_written"] is False
    assert guidance["routine_start_enabled"] is False


def test_terminal_command_writes_completion_record_with_context_db_path(tmp_path: Path) -> None:
    db_path = tmp_path / "terminal_completion.sqlite"
    session = TerminalChatSession(provider=_FakeProvider(), context_db_path=str(db_path))

    response = session.routine_completion_record_to_backend_context_write_mvp(
        {
            "environment": "test",
            "userId": "user_completion_001",
            "clientConfirmedRecordWrite": True,
            "routineCompletionRecord": _completion_record(),
        }
    )

    assert response["ok"] is True
    assert response["agent_routine_completion_record_to_backend_context_write_mvp_version"] == "v2_10_3"
    assert response["completion_record_persisted"] is True
    assert response["backend_database_written"] is True
    assert response["routine_start_enabled"] is False
    assert "SECRET_SHOULD_NOT_LEAK" not in json.dumps(response, ensure_ascii=False)


def test_api_completion_record_write_execute_route(tmp_path: Path) -> None:
    db_path = tmp_path / "api_completion.sqlite"
    client = TestClient(app)

    spec = client.get("/agent/context/routine-completion-record-to-backend-context-write-mvp/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_10_3"

    response = client.post(
        "/agent/context/routine-completion-record-to-backend-context-write-mvp/execute",
        json=_write_args(db_path),
    ).json()

    assert response["ok"] is True
    assert response["agent_routine_completion_record_to_backend_context_write_mvp_version"] == "v2_10_3"
    assert response["completion_record_persisted"] is True
    assert response["backend_database_written"] is True
    assert response["sqlite_rows_written"] is True
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False


def test_context_and_runtime_manifests_advertise_completion_write_mvp() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()

    assert manifest["agent_routine_completion_record_to_backend_context_write_mvp_spec_route"] == "GET /agent/context/routine-completion-record-to-backend-context-write-mvp/spec"
    assert runtime["routes"]["agent_routine_completion_record_to_backend_context_write_mvp"] == "POST /agent/context/routine-completion-record-to-backend-context-write-mvp/execute"
    assert runtime["agent_routine_completion_record_to_backend_context_write_mvp"]["version"] == "v2_10_3"
    assert CapabilityManifest().to_dict()["supports_agent_routine_completion_record_to_backend_context_write_mvp"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["agent_routine_completion_record_to_backend_context_write_mvp_version"] == "v2_10_3"
