from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "frontend_fixtures" / "harmonyos"
SMOKE_ROOT = FIXTURE_ROOT / "smoke"


def _load_fixture(name: str) -> dict:
    return json.loads((SMOKE_ROOT / name).read_text(encoding="utf-8"))


def test_harmonyos_agent_today_guidance_client_types_and_methods_are_exposed() -> None:
    agent_types = (FIXTURE_ROOT / "types" / "AgentTypes.ets").read_text(encoding="utf-8")
    api_client = (FIXTURE_ROOT / "api" / "JamMateApiClient.ets").read_text(encoding="utf-8")

    assert "AgentHarmonyOSTodayPracticeGuidanceRequest" in agent_types
    assert "AgentHarmonyOSRoutineCompletionRecordRequest" in agent_types
    assert "AgentHarmonyOSTodayPracticeGuidanceResponse" in agent_types
    assert "AgentHarmonyOSRoutineCompletionRecordResponse" in agent_types
    assert "backendSQLiteWriteMayOccur" in agent_types
    assert "requiresUserConfirmationBeforeRoutineStart" in agent_types

    assert "previewHarmonyOSTodayPracticeGuidance" in api_client
    assert "recordHarmonyOSRoutineCompletion" in api_client
    assert "getHarmonyOSTodayGuidanceContractSpec" in api_client
    assert "/agent/harmonyos/today-practice-guidance/preview" in api_client
    assert "/agent/harmonyos/routine-completion-record/execute" in api_client


def test_harmonyos_agent_today_guidance_smoke_files_are_copyable() -> None:
    completion = _load_fixture("smoke_agent_harmonyos_routine_completion_record_execute.json")
    guidance = _load_fixture("smoke_agent_harmonyos_today_practice_guidance_preview.json")
    smoke_pack = _load_fixture("smoke_pack.json")
    curl = (SMOKE_ROOT / "curl_smoke.sh").read_text(encoding="utf-8")
    readme = (SMOKE_ROOT / "README.md").read_text(encoding="utf-8")

    assert completion["clientConfirmedRecordWrite"] is True
    assert completion["routineCompletionRecord"]["completed"] is True
    assert completion["sqliteDbPath"].endswith(".sqlite")
    assert "userPracticeProfile" in completion
    assert "practicePlan" in completion

    assert guidance["userInput"] == "今天该练什么？"
    assert guidance["providerResult"]["ok"] is True
    assert guidance["providerResult"]["content"]

    sequence = smoke_pack["agent_today_guidance_product_smoke_sequence"]
    assert [step["path"] for step in sequence] == [
        "/agent/harmonyos/routine-completion-record/execute",
        "/agent/harmonyos/today-practice-guidance/preview",
    ]
    assert "smoke_agent_harmonyos_routine_completion_record_execute.json" in curl
    assert "smoke_agent_harmonyos_today_practice_guidance_preview.json" in curl
    assert "HarmonyOS Agent today guidance integration smoke" in readme


def test_harmonyos_agent_today_guidance_fixtures_run_through_test_client(tmp_path: Path) -> None:
    db_path = tmp_path / "harmonyos_agent_today_guidance_integration.sqlite"
    completion = _load_fixture("smoke_agent_harmonyos_routine_completion_record_execute.json")
    guidance = _load_fixture("smoke_agent_harmonyos_today_practice_guidance_preview.json")
    completion["sqliteDbPath"] = str(db_path)
    guidance["sqliteDbPath"] = str(db_path)

    client = TestClient(app)
    completion_response = client.post("/agent/harmonyos/routine-completion-record/execute", json=completion)
    assert completion_response.status_code == 200
    completion_payload = completion_response.json()
    assert completion_payload["ok"] is True
    assert completion_payload["code"] == "routine_completion_record_persisted"
    assert completion_payload["data"]["completionRecordPersisted"] is True
    assert completion_payload["data"]["nextTodayGuidanceCanReadHistory"] is True
    assert completion_payload["safety"]["backendSQLiteWriteMayOccur"] is True
    assert completion_payload["safety"]["writesHarmonyOSLocalState"] is False
    assert completion_payload["safety"]["startsRoutine"] is False
    assert completion_payload["safety"]["callsEngineAdapter"] is False

    guidance_response = client.post("/agent/harmonyos/today-practice-guidance/preview", json=guidance)
    assert guidance_response.status_code == 200
    guidance_payload = guidance_response.json()
    assert guidance_payload["ok"] is True
    assert guidance_payload["code"] == "today_guidance_ready"
    assert guidance_payload["data"]["guidancePreviewReady"] is True
    assert guidance_payload["data"]["contextSource"] == "sqlite_backend"
    assert guidance_payload["data"]["requiresUserConfirmationBeforeRoutineStart"] is True
    assert guidance_payload["debug"]["sqliteReadbackAttempted"] is True
    assert guidance_payload["debug"]["backendDatabaseRead"] is True
    assert guidance_payload["safety"]["backendSQLiteWriteMayOccur"] is False
    assert guidance_payload["safety"]["startsPlayback"] is False
    assert guidance_payload["safety"]["createsMidiAsset"] is False


def test_shared_api_contract_documents_harmonyos_agent_product_routes() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff_doc = ROOT / "docs" / "INTEGRATION_HARMONYOS_AGENT_TODAY_GUIDANCE_HANDOFF_V2_10_6.md"

    assert "POST /agent/harmonyos/today-practice-guidance/preview" in api_doc
    assert "POST /agent/harmonyos/routine-completion-record/execute" in api_doc
    assert "requiresUserConfirmationBeforeRoutineStart" in api_doc
    assert "v2_10_6 — HarmonyOS Agent Today Guidance Integration Handoff" in changelog
    assert handoff_doc.exists()
    assert "clientConfirmedRecordWrite=true" in handoff_doc.read_text(encoding="utf-8")


def test_integration_handoff_does_not_modify_engine_generation_contract() -> None:
    # This integration handoff only wires Agent/HarmonyOS contract fixtures.
    assert (ROOT / "src" / "jammate_engine").exists()
    api_client = (FIXTURE_ROOT / "api" / "JamMateApiClient.ets").read_text(encoding="utf-8")
    assert "generateDirectAccompaniment" in api_client
    assert "/accompaniment/generate" in api_client
