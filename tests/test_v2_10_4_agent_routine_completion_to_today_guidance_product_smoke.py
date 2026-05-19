from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.llm_provider import LLMProviderResult
from jammate_agent.core.tool_invocation import (
    AGENT_ROUTINE_COMPLETION_TO_TODAY_GUIDANCE_PRODUCT_SMOKE_VERSION,
    build_agent_routine_completion_to_today_guidance_product_smoke_payload,
    build_agent_routine_completion_to_today_guidance_product_smoke_summary,
    agent_routine_completion_to_today_guidance_product_smoke_contract,
)
from jammate_api.app import app


def _db_path(tmp_path: Path, name: str) -> Path:
    path = Path("/mnt/data") / f"jammate_v2_10_4_{tmp_path.name}_{name}"
    if path.exists():
        path.unlink()
    return path


def _profile() -> dict:
    return {
        "userId": "user_product_smoke_001",
        "currentGoal": "完成记录驱动今日练习建议",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["time feel", "comping"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_product_smoke_001",
        "title": "Product Smoke Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_swing", "title": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _completion_record() -> dict:
    return {
        "sessionId": "session_product_smoke_001",
        "title": "Medium Swing guide-tone comping",
        "style": "medium_swing",
        "tempo": 104,
        "actualSeconds": 900,
        "completed": True,
        "completedAtUtc": "2026-05-19T21:00:00+00:00",
        "practiceGoal": "完成 swing guide-tone 连接",
    }


def _guidance_output() -> dict:
    return {
        "guidance_mode": "adjust_based_on_history",
        "summary": "已记录刚完成的 Medium Swing 练习，今天下一步建议转到 Bossa comping review。",
        "recommended_focus": "Bossa comping review after completed swing block",
        "recommended_blocks": [
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "goal": "承接已完成记录"},
        ],
        "routine_candidates": [
            {"candidateId": "routine_after_completion", "routineName": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "practiceGoal": "基于刚完成的 swing 记录调整"},
        ],
        "adjustment_reason": "recent routine history shows the swing block was completed",
        "profile_considerations": "继续保持用户偏好的 swing/bossa 方向。",
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


def _smoke_args(db_path: Path, *, confirmed: bool = True, seed_confirmed: bool = True, idem: str = "idem_product_smoke_completion_001") -> dict:
    return {
        "sqliteDbPath": str(db_path),
        "environment": "test",
        "userId": "user_product_smoke_001",
        "seedInitialContext": True,
        "clientConfirmedInitialContextSeed": seed_confirmed,
        "initialContextIdempotencyKey": "idem_product_smoke_seed_001",
        "userPracticeProfile": _profile(),
        "practicePlan": _plan(),
        "clientConfirmedRecordWrite": confirmed,
        "idempotencyKey": idem,
        "routineCompletionRecord": _completion_record(),
        "userInput": "今天该练什么？",
        "providerResult": _provider_result(),
    }


def test_product_smoke_contract_is_product_facing() -> None:
    spec = agent_routine_completion_to_today_guidance_product_smoke_contract()

    assert spec["version"] == AGENT_ROUTINE_COMPLETION_TO_TODAY_GUIDANCE_PRODUCT_SMOKE_VERSION == "v2_10_4"
    assert spec["spec_route"] == "GET /agent/context/routine-completion-to-today-guidance-product-smoke/spec"
    assert spec["execute_route"] == "POST /agent/context/routine-completion-to-today-guidance-product-smoke/execute"
    assert spec["execution_status"]["completion_record_write_enabled_after_explicit_client_confirmation"] is True
    assert spec["execution_status"]["ordinary_today_guidance_readback_enabled"] is True
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_starts_routine"] is False


def test_product_smoke_seeds_context_writes_completion_and_guidance_reads_history(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path, "product_smoke.sqlite")

    payload_obj = build_agent_routine_completion_to_today_guidance_product_smoke_payload(_smoke_args(db_path))
    payload = payload_obj.to_dict()
    summary = build_agent_routine_completion_to_today_guidance_product_smoke_summary(payload=payload_obj)

    assert payload["validation"]["status"] == "routine_completion_to_today_guidance_product_smoke_ready"
    assert summary["accepted"] is True
    assert summary["initial_context_seed_requested"] is True
    assert summary["initial_context_seed_written"] is True
    assert summary["completion_record_persisted"] is True
    assert summary["guidance_preview_ready"] is True
    assert summary["guidance_context_source"] == "sqlite_backend"
    assert summary["recent_completion_history_read_by_guidance"] is True
    assert summary["routine_candidate_count"] == 1
    assert summary["backend_database_written"] is True
    assert summary["backend_database_read"] is True
    assert summary["sqlite_rows_written"] is True
    assert summary["sqlite_rows_read"] >= 1
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False


def test_product_smoke_blocks_without_completion_write_confirmation(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path, "blocked_product_smoke.sqlite")

    payload_obj = build_agent_routine_completion_to_today_guidance_product_smoke_payload(_smoke_args(db_path, confirmed=False))
    payload = payload_obj.to_dict()
    summary = build_agent_routine_completion_to_today_guidance_product_smoke_summary(payload=payload_obj)

    assert summary["accepted"] is False
    assert "routine_completion_record_not_persisted" in summary["blocked_reasons"]
    assert summary["completion_record_persisted"] is False
    assert summary["guidance_preview_built"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["engine_adapter_called"] is False


def test_product_smoke_completion_write_is_idempotent_but_guidance_still_runs(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path, "product_smoke_idempotent.sqlite")

    first = build_agent_routine_completion_to_today_guidance_product_smoke_payload(_smoke_args(db_path)).to_dict()
    second_obj = build_agent_routine_completion_to_today_guidance_product_smoke_payload(_smoke_args(db_path))
    second = second_obj.to_dict()
    second_summary = build_agent_routine_completion_to_today_guidance_product_smoke_summary(payload=second_obj)

    assert first["validation"]["accepted"] is True
    assert second["validation"]["accepted"] is True
    assert second_summary["idempotent_replay"] is True
    assert second_summary["completion_record_persisted"] is True
    assert second_summary["guidance_preview_ready"] is True
    assert second_summary["recent_completion_history_read_by_guidance"] is True


def test_terminal_product_smoke_command_uses_session_context_db_path(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path, "terminal_product_smoke.sqlite")
    session = TerminalChatSession(provider=_FakeProvider(), context_db_path=str(db_path))

    response = session.routine_completion_to_today_guidance_product_smoke(
        {k: v for k, v in _smoke_args(db_path).items() if k != "sqliteDbPath" and k != "providerResult"}
    )

    assert response["ok"] is True
    assert response["agent_routine_completion_to_today_guidance_product_smoke_version"] == "v2_10_4"
    assert response["completion_record_persisted"] is True
    assert response["guidance_preview_ready"] is True
    assert response["recent_completion_history_read_by_guidance"] is True
    assert response["routine_start_enabled"] is False
    assert "SECRET_SHOULD_NOT_LEAK" not in json.dumps(response, ensure_ascii=False)


def test_api_product_smoke_execute_route(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path, "api_product_smoke.sqlite")
    client = TestClient(app)

    spec = client.get("/agent/context/routine-completion-to-today-guidance-product-smoke/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_10_4"

    response = client.post(
        "/agent/context/routine-completion-to-today-guidance-product-smoke/execute",
        json=_smoke_args(db_path),
    ).json()

    assert response["ok"] is True
    assert response["agent_routine_completion_to_today_guidance_product_smoke_version"] == "v2_10_4"
    assert response["completion_record_persisted"] is True
    assert response["guidance_preview_ready"] is True
    assert response["recent_completion_history_read_by_guidance"] is True
    assert response["backend_database_written"] is True
    assert response["backend_database_read"] is True
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_context_and_runtime_manifests_advertise_product_smoke() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()

    assert manifest["agent_routine_completion_to_today_guidance_product_smoke_spec_route"] == "GET /agent/context/routine-completion-to-today-guidance-product-smoke/spec"
    assert runtime["routes"]["agent_routine_completion_to_today_guidance_product_smoke"] == "POST /agent/context/routine-completion-to-today-guidance-product-smoke/execute"
    assert runtime["agent_routine_completion_to_today_guidance_product_smoke"]["version"] == "v2_10_4"
    assert CapabilityManifest().to_dict()["supports_agent_routine_completion_to_today_guidance_product_smoke"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["agent_routine_completion_to_today_guidance_product_smoke_version"] == "v2_10_4"
