from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    AGENT_HARMONYOS_TODAY_GUIDANCE_API_CONTRACT_ALIGNMENT_VERSION,
    agent_harmonyos_today_guidance_api_contract_alignment_contract,
    build_agent_harmonyos_today_guidance_api_contract_alignment_payload,
    build_agent_harmonyos_today_guidance_api_contract_alignment_summary,
    build_context_persistence_sqlite_backend_store_payload,
)
from jammate_api.app import app


def _profile() -> dict:
    return {
        "userId": "user_harmonyos_001",
        "currentGoal": "鸿蒙端今日练习建议联调",
        "preferredStyles": ["medium_swing", "bossa_nova"],
        "focusAreas": ["comping", "time feel"],
    }


def _plan() -> dict:
    return {
        "planId": "plan_harmonyos_001",
        "title": "HarmonyOS Agent Contract Plan",
        "status": "active",
        "planBlocks": [
            {"blockId": "block_swing", "title": "Medium Swing guide-tone comping", "style": "medium_swing", "tempo": 104, "durationMinutes": 15, "completed": False},
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "completed": False},
        ],
    }


def _completion_record() -> dict:
    return {
        "sessionId": "session_harmonyos_001",
        "title": "Medium Swing guide-tone comping",
        "style": "medium_swing",
        "tempo": 104,
        "actualSeconds": 900,
        "completed": True,
        "completedAtUtc": "2026-05-19T22:00:00+00:00",
        "practiceGoal": "完成 guide-tone 连接",
    }


def _guidance_output() -> dict:
    return {
        "guidance_mode": "adjust_based_on_history",
        "summary": "已读取鸿蒙端保存的练习记录，今天建议继续 Bossa comping review。",
        "recommended_focus": "Bossa comping review after Medium Swing completion",
        "recommended_blocks": [
            {"blockId": "block_bossa", "title": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "goal": "承接完成记录"},
        ],
        "routine_candidates": [
            {"candidateId": "routine_harmonyos_today", "routineName": "Bossa comping review", "style": "bossa_nova", "tempo": 118, "durationMinutes": 10, "practiceGoal": "根据完成历史继续推进"},
        ],
        "adjustment_reason": "recent routine history shows the swing block was completed",
        "profile_considerations": "保持 swing/bossa 练习路线。",
        "user_confirmation_required": True,
        "next_client_actions": ["show_guidance", "present_routine_candidate"],
    }


def _provider_result() -> dict:
    return {"ok": True, "provider_name": "fixture", "model": "fixture-model", "content": json.dumps(_guidance_output(), ensure_ascii=False)}


def _seed_profile_plan(db_path: Path) -> None:
    payload = build_context_persistence_sqlite_backend_store_payload(
        {
            "backendPersistenceEnabled": True,
            "executeBackendPersistence": True,
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "userDecision": "approved",
            "confirmationStatus": "user_approved_future_executor_required",
            "traceId": "trace_harmonyos_seed",
            "idempotencyKey": "idem_harmonyos_seed",
            "userId": "user_harmonyos_001",
            "candidateKind": "practice_plan_persistence_candidate",
            "candidateId": "candidate_harmonyos_seed",
            "confirmationId": "confirmation_harmonyos_seed",
            "entities": ["user_practice_profile", "active_practice_plan"],
            "userPracticeProfile": _profile(),
            "practicePlan": _plan(),
        }
    ).to_dict()
    assert payload["validation"]["status"] == "sqlite_backend_store_ready"
    assert payload["backend_database_written"] is True


def test_harmonyos_contract_alignment_packet_defines_product_wrapper_routes() -> None:
    spec = agent_harmonyos_today_guidance_api_contract_alignment_contract()
    payload_obj = build_agent_harmonyos_today_guidance_api_contract_alignment_payload({})
    payload = payload_obj.to_dict()
    summary = build_agent_harmonyos_today_guidance_api_contract_alignment_summary(payload=payload_obj)

    assert spec["version"] == AGENT_HARMONYOS_TODAY_GUIDANCE_API_CONTRACT_ALIGNMENT_VERSION == "v2_10_5"
    assert spec["today_guidance_preview_route"] == "POST /agent/harmonyos/today-practice-guidance/preview"
    assert spec["routine_completion_record_execute_route"] == "POST /agent/harmonyos/routine-completion-record/execute"
    assert spec["canonical_response_shape"]["top_level"] == ["ok", "code", "message", "data", "debug", "safety"]
    assert payload["validation"]["status"] == "harmonyos_today_guidance_api_contract_alignment_ready"
    assert payload["request_contracts"]["today_guidance_preview"]["camel_case_preferred"] is True
    assert payload["safety_contract"]["writes_harmonyos_local_state"] is False
    assert summary["product_facing_wrapper_routes_defined"] is True
    assert summary["backend_database_written"] is False


def test_harmonyos_contract_preview_route_is_preview_only() -> None:
    client = TestClient(app)
    spec = client.get("/agent/harmonyos/today-guidance-api-contract-alignment/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_10_5"

    response = client.post("/agent/harmonyos/today-guidance-api-contract-alignment/preview", json={}).json()
    assert response["ok"] is True
    assert response["agentHarmonyOSTodayGuidanceApiContractAlignmentVersion"] == "v2_10_5"
    assert response["routeCatalog"]["today_guidance_preview"] == "POST /agent/harmonyos/today-practice-guidance/preview"
    assert response["safety"]["writesHarmonyOSLocalState"] is False
    assert response["safety"]["callsEngineAdapter"] is False


def test_harmonyos_today_guidance_wrapper_reads_sqlite_and_returns_camel_case_response(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_guidance.sqlite"
    _seed_profile_plan(db_path)
    client = TestClient(app)

    response = client.post(
        "/agent/harmonyos/today-practice-guidance/preview",
        json={
            "userId": "user_harmonyos_001",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "userInput": "今天该练什么？",
            "providerResult": _provider_result(),
        },
    ).json()

    assert response["ok"] is True
    assert response["code"] == "today_guidance_ready"
    assert response["data"]["guidancePreviewReady"] is True
    assert response["data"]["contextSource"] == "sqlite_backend"
    assert response["data"]["routineCandidateCount"] == 1
    assert isinstance(response["data"]["actionCardPayload"], dict)
    assert response["debug"]["agentHarmonyOSTodayGuidanceApiContractAlignmentVersion"] == "v2_10_5"
    assert response["debug"]["underlyingVersion"] == "v2_10_2"
    assert response["debug"]["sqliteReadbackAttempted"] is True
    assert response["debug"]["backendDatabaseRead"] is True
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False


def test_harmonyos_today_guidance_wrapper_no_context_returns_actionable_state() -> None:
    client = TestClient(app)
    response = client.post("/agent/harmonyos/today-practice-guidance/preview", json={"userInput": "今天该练什么？"}).json()

    assert response["ok"] is True
    assert response["code"] == "today_guidance_needs_context_or_provider"
    assert response["data"]["guidancePreviewReady"] is False
    assert response["data"]["contextSource"] in {"none", "plain_fallback_after_sqlite_miss"}
    assert response["debug"]["backendDatabaseRead"] is False
    assert response["safety"]["backendSQLiteWriteMayOccur"] is False
    assert "练习上下文" in response["message"]


def test_harmonyos_completion_wrapper_writes_backend_context_and_not_local_state(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_completion.sqlite"
    client = TestClient(app)

    response = client.post(
        "/agent/harmonyos/routine-completion-record/execute",
        json={
            "userId": "user_harmonyos_001",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "clientConfirmedRecordWrite": True,
            "idempotencyKey": "idem_harmonyos_completion_001",
            "routineCompletionRecord": _completion_record(),
        },
    ).json()

    assert response["ok"] is True
    assert response["code"] == "routine_completion_record_persisted"
    assert response["data"]["completionRecordPersisted"] is True
    assert response["data"]["nextTodayGuidanceCanReadHistory"] is True
    assert response["debug"]["underlyingVersion"] == "v2_10_3"
    assert response["debug"]["backendDatabaseWritten"] is True
    assert response["debug"]["sqliteRowsWritten"] is True
    assert response["safety"]["backendSQLiteWriteMayOccur"] is True
    assert response["safety"]["writesHarmonyOSLocalState"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False


def test_harmonyos_completion_then_guidance_uses_persisted_history(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_completion_to_guidance.sqlite"
    _seed_profile_plan(db_path)
    client = TestClient(app)

    write_response = client.post(
        "/agent/harmonyos/routine-completion-record/execute",
        json={
            "userId": "user_harmonyos_001",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "clientConfirmedRecordWrite": True,
            "idempotencyKey": "idem_harmonyos_completion_to_guidance_001",
            "routineCompletionRecord": _completion_record(),
        },
    ).json()
    assert write_response["ok"] is True

    guidance_response = client.post(
        "/agent/harmonyos/today-practice-guidance/preview",
        json={
            "userId": "user_harmonyos_001",
            "sqliteDbPath": str(db_path),
            "environment": "test",
            "userInput": "今天该练什么？",
            "providerResult": _provider_result(),
        },
    ).json()

    assert guidance_response["ok"] is True
    assert guidance_response["code"] == "today_guidance_ready"
    assert guidance_response["debug"]["sqliteRowsRead"] >= 2
    assert guidance_response["data"]["routineCandidateCount"] == 1
    assert guidance_response["safety"]["startsPlayback"] is False


def test_terminal_command_exposes_harmonyos_contract_alignment() -> None:
    session = TerminalChatSession(provider=None)
    response = session.harmonyos_today_guidance_api_contract_alignment({})

    assert response["ok"] is True
    assert response["agent_harmonyos_today_guidance_api_contract_alignment_version"] == "v2_10_5"
    assert response["route_catalog"]["today_guidance_preview"] == "POST /agent/harmonyos/today-practice-guidance/preview"
    assert response["backend_database_written"] is False
    assert response["routine_start_enabled"] is False
    assert response["engine_adapter_called"] is False


def test_context_and_runtime_manifests_advertise_harmonyos_routes() -> None:
    manifest = context_profile_manifest()
    runtime = llm_context_runtime_contract()

    assert manifest["agent_harmonyos_today_guidance_api_contract_alignment_spec_route"] == "GET /agent/harmonyos/today-guidance-api-contract-alignment/spec"
    assert manifest["agent_harmonyos_today_practice_guidance_preview_route"] == "POST /agent/harmonyos/today-practice-guidance/preview"
    assert manifest["agent_harmonyos_routine_completion_record_execute_route"] == "POST /agent/harmonyos/routine-completion-record/execute"
    assert runtime["routes"]["agent_harmonyos_today_practice_guidance_preview"] == "POST /agent/harmonyos/today-practice-guidance/preview"
    assert runtime["agent_harmonyos_today_guidance_api_contract_alignment"]["version"] == "v2_10_5"
