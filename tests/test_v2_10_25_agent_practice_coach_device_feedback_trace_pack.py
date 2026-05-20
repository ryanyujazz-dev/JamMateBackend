from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION

ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend_fixtures" / "harmonyos"
SMOKE_DIR = FRONTEND / "smoke"
FIXTURE_PATH = SMOKE_DIR / "product_practice_coach_device_feedback_trace_request.json"
SCRIPT_PATH = SMOKE_DIR / "curl_practice_coach_device_feedback_trace_smoke.sh"


def _post(client: TestClient, payload: dict) -> dict:
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    return response.json()


def test_device_feedback_trace_pack_is_returned_for_unified_practice_coach_message(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_device_feedback.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)

    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    body = _post(client, payload)

    assert body["ok"] is True
    assert body["debug"]["deviceFeedbackTracePackVersion"] == PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION
    pack = body["debug"]["deviceFeedbackTracePack"]
    assert pack == body["data"]["deviceFeedbackTracePack"]
    assert pack["tracePackVersion"] == PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION
    assert pack["copyThisForBackendIssue"] is True
    assert pack["endpoint"] == f"POST {ROUTE}"
    assert pack["requestSummary"]["userId"] == payload["userId"]
    assert pack["requestSummary"]["sessionId"] == payload["sessionId"]
    assert pack["requestSummary"]["deviceId"] == payload["deviceId"]
    assert pack["requestSummary"]["userMessageDigest"]
    assert pack["requestSummary"]["userMessagePreview"]
    assert pack["responseSummary"]["responseType"] == body["data"]["responseType"]
    assert pack["responseSummary"]["conversationStatePersisted"] is True
    assert pack["decisionTrace"]["deterministicFallbackUsed"] is True
    assert pack["decisionTrace"]["networkCallExecuted"] is False
    assert pack["stateTrace"]["stateDigestAfter"] == body["data"]["stateDigestAfter"]
    assert pack["stateTrace"]["turnCountAfter"] == 1
    assert pack["ioTrace"]["sqliteRowsWritten"] is True
    assert pack["ioTrace"]["transactionCommitted"] is True
    assert pack["safetyTrace"]["startsRoutine"] is False
    assert pack["safetyTrace"]["callsEngineAdapter"] is False
    assert pack["safetyTrace"]["writesHarmonyOSLocalState"] is False
    assert "deviceFeedbackTracePack object" in pack["frontendFeedbackChecklist"]


def test_device_feedback_trace_pack_updates_across_plan_revision_sequence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_device_feedback_sequence.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    base = {
        "userId": "local-dev-user",
        "sessionId": "practice-coach-device-feedback-sequence",
        "deviceId": "harmonyos-device-local",
        "clientLocalDate": "2026-05-20",
        "clientTimezone": "Asia/Shanghai",
        "locale": "zh-CN",
    }

    proposal = _post(client, {**base, "userMessage": "中级，今天可以练30分钟，目标是提升伴奏稳定性，喜欢 bossa 和 swing。"})
    revision = _post(client, {**base, "userMessage": "我想调整为20分钟"})

    proposal_pack = proposal["debug"]["deviceFeedbackTracePack"]
    revision_pack = revision["debug"]["deviceFeedbackTracePack"]
    assert proposal_pack["responseSummary"]["responseType"] == "practice_plan_proposal"
    assert proposal_pack["artifactTrace"]["planProposalTotalDurationMinutes"] == 30
    assert revision_pack["responseSummary"]["responseType"] == "practice_plan_revision"
    assert revision_pack["artifactTrace"]["planProposalTotalDurationMinutes"] == 20
    assert revision_pack["decisionTrace"]["routerDecisionReason"] == "existing_draft_plan_revision_requested"
    assert revision_pack["stateTrace"]["awaitingConfirmationBefore"] is True
    assert revision_pack["stateTrace"]["awaitingConfirmationAfter"] is True
    assert revision_pack["stateTrace"]["draftPlanDigestBefore"] != revision_pack["stateTrace"]["draftPlanDigestAfter"]


def test_frontend_contract_types_and_smoke_pack_document_device_feedback_trace_pack() -> None:
    types_text = (FRONTEND / "types" / "PracticeCoachTypes.ets").read_text(encoding="utf-8")
    mapper_text = (FRONTEND / "api" / "PracticeCoachStateMapper.ets").read_text(encoding="utf-8")
    doc_text = (ROOT / "docs" / "AGENT_PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_V2_10_25.md").read_text(encoding="utf-8")
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))

    assert "PracticeCoachDeviceFeedbackTracePack" in types_text
    assert "deviceFeedbackTracePack" in types_text
    assert "deviceFeedbackTracePack" in mapper_text
    assert "v2_10_25" in doc_text
    assert "deviceFeedbackTracePack" in doc_text
    assert pack["practice_coach_device_feedback_trace_pack"]["script"] == "curl_practice_coach_device_feedback_trace_smoke.sh"
    assert pack["practice_coach_device_feedback_trace_pack"]["fixture"] == "product_practice_coach_device_feedback_trace_request.json"


def test_device_feedback_trace_smoke_script_keeps_product_request_black_box() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "llmActionDecisionResult" not in json.dumps(payload)
    assert "providerResult" not in json.dumps(payload)
    assert "sqliteDbPath" not in json.dumps(payload)
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "deviceFeedbackTracePack" in script_text
    assert "copyThisForBackendIssue" in script_text
    assert "startsRoutine" in script_text
