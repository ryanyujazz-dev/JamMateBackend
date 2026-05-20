from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "frontend_fixtures" / "harmonyos"
SMOKE_ROOT = FIXTURE_ROOT / "smoke"


def _provider_result() -> dict:
    return {
        "ok": True,
        "provider_name": "fixture",
        "model": "fixture-model",
        "content": json.dumps(
            {
                "summary": "根据刚完成的练习记录，今天建议继续 Blue Bossa comping practice。",
                "routine_candidates": [
                    {
                        "candidateId": "routine_frontend_contract_001",
                        "routineName": "Blue Bossa comping practice",
                        "durationMinutes": 15,
                        "practiceGoal": "承接最近完成记录",
                    }
                ],
                "user_confirmation_required": True,
            },
            ensure_ascii=False,
        ),
    }


def _frontend_completion_payload() -> dict:
    return {
        "userId": "local-dev-user",
        "sessionId": "practice-session-1779200000000",
        "deviceId": "harmonyos-device-local",
        "routineCompletionRecord": {
            "routineId": "routine-xxx",
            "routineTitle": "今日基础练习",
            "completedAt": "2026-05-20T20:30:00-07:00",
            "durationSeconds": 1800,
            "status": "completed",
            "items": [
                {
                    "itemId": "item-1",
                    "title": "Blue Bossa comping practice",
                    "type": "tune_practice",
                    "durationSeconds": 900,
                    "status": "completed",
                }
            ],
            "notes": "optional user note",
        },
    }


def _frontend_guidance_payload() -> dict:
    return {
        "userId": "local-dev-user",
        "sessionId": "agent-session-1779200000000",
        "deviceId": "harmonyos-device-local",
        "userMessage": "今天该练什么？",
        "providerResult": _provider_result(),
    }


def test_harmonyos_product_completion_payload_without_db_path_or_gate_writes_backend_context(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "harmonyos_product_contract.sqlite"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    payload = _frontend_completion_payload()
    assert "dbPath" not in payload
    assert "sqliteDbPath" not in payload
    assert "clientConfirmedRecordWrite" not in payload

    response = TestClient(app).post("/agent/harmonyos/routine-completion-record/execute", json=payload).json()

    assert response["ok"] is True
    assert response["code"] == "routine_completion_record_persisted"
    assert response["data"]["completionRecordPersisted"] is True
    assert response["data"]["nextTodayGuidanceCanReadHistory"] is True
    assert response["data"]["routineCompletionRecord"]["title"] == "今日基础练习"
    assert response["data"]["routineCompletionRecord"]["routineId"] == "routine-xxx"
    assert response["debug"]["backendDatabaseWritten"] is True
    assert response["safety"]["writesHarmonyOSLocalState"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False


def test_harmonyos_product_today_guidance_payload_uses_user_message_and_backend_owned_db_path(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "harmonyos_product_guidance.sqlite"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    write_response = client.post("/agent/harmonyos/routine-completion-record/execute", json=_frontend_completion_payload()).json()
    assert write_response["ok"] is True

    guidance_payload = _frontend_guidance_payload()
    assert "dbPath" not in guidance_payload
    assert "sqliteDbPath" not in guidance_payload
    assert "userInput" not in guidance_payload

    response = client.post("/agent/harmonyos/today-practice-guidance/preview", json=guidance_payload).json()

    assert response["ok"] is True
    assert response["code"] == "today_guidance_ready"
    assert response["data"]["guidancePreviewReady"] is True
    assert response["data"]["contextSource"] == "sqlite_backend"
    assert "Blue Bossa" in response["data"]["content"]
    assert response["debug"]["sqliteReadbackAttempted"] is True
    assert response["debug"]["backendDatabaseRead"] is True
    assert response["safety"]["backendSQLiteWriteMayOccur"] is False
    assert response["safety"]["startsPlayback"] is False


def test_product_fixtures_match_frontend_report_payload_shape() -> None:
    completion = json.loads((SMOKE_ROOT / "smoke_agent_harmonyos_routine_completion_record_execute_product.json").read_text(encoding="utf-8"))
    guidance = json.loads((SMOKE_ROOT / "smoke_agent_harmonyos_today_practice_guidance_preview_product.json").read_text(encoding="utf-8"))
    smoke_pack = json.loads((SMOKE_ROOT / "smoke_pack.json").read_text(encoding="utf-8"))

    assert "sqliteDbPath" not in completion
    assert "dbPath" not in completion
    assert "clientConfirmedRecordWrite" not in completion
    assert completion["routineCompletionRecord"]["routineTitle"] == "今日基础练习"

    assert "sqliteDbPath" not in guidance
    assert "dbPath" not in guidance
    assert guidance["userMessage"] == "今天该练什么？"

    assert smoke_pack["v2_10_8_harmonyos_black_box_contract_fit"]["frontend_does_not_send_db_path"] is True
    assert smoke_pack["v2_10_8_harmonyos_black_box_contract_fit"]["frontend_does_not_send_internal_write_gate"] is True


def test_shared_contract_docs_mark_db_path_and_write_gate_as_backend_owned() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "INTEGRATION_HARMONYOS_AGENT_BLACK_BOX_CONTRACT_FIT_V2_10_8.md").read_text(encoding="utf-8")
    types = (FIXTURE_ROOT / "types" / "AgentTypes.ets").read_text(encoding="utf-8")

    assert "Do **not** send internal `sqliteDbPath`" in api_doc
    assert "Product clients do **not** send `sqliteDbPath` or `clientConfirmedRecordWrite`" in api_doc
    assert "v2_10_8 — HarmonyOS Agent Black-Box Contract Fit" in changelog
    assert "no `dbPath` / `sqliteDbPath`" in handoff
    assert "userMessage?: string" in types
    assert "clientConfirmedRecordWrite?: boolean" in types


def test_contract_fit_does_not_modify_engine_or_agent_core_boundaries() -> None:
    assert (ROOT / "src" / "jammate_engine").exists()
    assert (ROOT / "src" / "jammate_agent" / "core").exists()
    api_client = (FIXTURE_ROOT / "api" / "JamMateApiClient.ets").read_text(encoding="utf-8")
    assert "/agent/harmonyos/routine-completion-record/execute" in api_client
    assert "/agent/harmonyos/today-practice-guidance/preview" in api_client
