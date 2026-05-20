from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
COMPLETION_FIXTURE = SMOKE_ROOT / "product_contract_routine_completion_request.json"
GUIDANCE_FIXTURE = SMOKE_ROOT / "product_contract_today_guidance_request.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def test_today_guidance_llm_payload_trace_uses_black_box_product_request_without_provider_call(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "today_guidance_llm_payload_trace.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    completion_response = client.post(
        "/agent/harmonyos/routine-completion-record/execute",
        json=_load(COMPLETION_FIXTURE),
    ).json()
    assert completion_response["ok"] is True
    assert completion_response["data"]["completionRecordPersisted"] is True

    response = client.post(
        "/agent/harmonyos/today-practice-guidance/llm-payload-trace",
        json=_load(GUIDANCE_FIXTURE),
    ).json()
    assert response["ok"] is True
    assert response["code"] == "today_guidance_llm_payload_trace_ready"
    assert response["data"]["llmPayloadTraceReady"] is True
    assert response["data"]["userMessage"] == "今天该练什么？"
    assert response["data"]["contextSource"] == "sqlite_backend"
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["debug"]["backendDatabaseRead"] is True
    assert response["debug"]["sqliteRowsRead"] >= 1

    trace = response["data"]["llmRequestPreview"]
    assert trace["traceVersion"] == "v2_10_10"
    assert trace["routePurpose"] == "debug_preview_only_no_llm_call"
    assert trace["promptSource"] == "sqlite_backend"
    assert trace["userMessage"] == "今天该练什么？"
    assert trace["safety"]["llmCalledByThisTraceRoute"] is False
    assert trace["safety"]["networkCallExecuted"] is False
    assert trace["safety"]["rawApiKeyIncluded"] is False

    internal_roles = [message["role"] for message in trace["internalPromptMessages"]]
    assert internal_roles == ["system", "developer", "user", "context"]
    network_roles = [message["role"] for message in trace["chatCompletionsMessagesIfCalled"]]
    assert set(network_roles).issubset({"system", "user", "assistant"})
    assert network_roles == ["system", "user"]
    assert trace["roleNormalization"]["developerAndContextMergedIntoSystem"] is True

    request_body = trace["chatCompletionsRequestBodyPreview"]
    assert request_body["messages"] == trace["chatCompletionsMessagesIfCalled"]
    assert "Authorization" not in request_body
    assert "api_key" not in json.dumps(request_body, ensure_ascii=False).lower()

    assembled_context = trace["assembledPracticeContext"]
    history = assembled_context["practice_history_context"]["recent_practice_history"]
    assert history
    assert history[0]["title"] == "今日基础练习"
    assert history[0]["duration_minutes"] == 30.0
    assert "notes" not in history[0]
    assert "items" not in history[0]


def test_today_guidance_llm_payload_trace_fresh_install_still_shows_model_payload_shape(monkeypatch) -> None:
    monkeypatch.delenv("JAMMATE_AGENT_CONTEXT_DB_PATH", raising=False)
    client = TestClient(app)
    response = client.post(
        "/agent/harmonyos/today-practice-guidance/llm-payload-trace",
        json={"userId": "local-dev-user", "sessionId": "agent-session", "deviceId": "harmonyos-device", "userMessage": "今天该练什么？"},
    ).json()

    assert response["ok"] is True
    trace = response["data"]["llmRequestPreview"]
    assert response["data"]["contextSource"] == "plain_fallback_after_sqlite_miss"
    assert trace["promptSource"] == "plain_fallback"
    assert trace["providerStatus"]["llm_calls_enabled"] is False
    assert trace["providerStatus"]["provider_class"] in {"DisabledLLMProvider", "OpenAICompatibleChatProvider"}
    assert trace["chatCompletionsRequestBodyPreview"]["messages"]
    assert trace["outputSchema"]["schema_name"] == "TodayPracticeGuidanceOutput"
    assert "midi_base64" in trace["outputSchema"]["forbidden_fields"]
    assert trace["promptPolicy"]["routine_start_requires_user_confirmation"] is True


def test_today_guidance_llm_payload_trace_docs_and_contract_mentions() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    task_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    integration_doc = ROOT / "docs" / "INTEGRATION_HARMONYOS_AGENT_TODAY_GUIDANCE_LLM_PAYLOAD_TRACE_V2_10_10.md"
    assert integration_doc.exists()
    integration_text = integration_doc.read_text(encoding="utf-8")

    for text in (api_doc, task_plan, changelog, integration_text):
        assert "v2_10_10" in text
    for text in (api_doc, integration_text):
        assert "POST /agent/harmonyos/today-practice-guidance/llm-payload-trace" in text
        assert "llmRequestPreview" in text
        assert "chatCompletionsMessagesIfCalled" in text
        assert "internalPromptMessages" in text
        assert "不会调用大模型" in text or "no LLM call" in text


def test_today_guidance_llm_payload_trace_response_does_not_expose_frontend_forbidden_internals() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/harmonyos/today-practice-guidance/llm-payload-trace",
        json=_load(GUIDANCE_FIXTURE),
    ).json()
    trace_keys = _walk_keys(response)
    assert "clientConfirmedRecordWrite" not in trace_keys
    assert "executeBackendPersistence" not in trace_keys
    assert "backendPersistenceEnabled" not in trace_keys
    assert response["safety"]["backendSQLiteWriteMayOccur"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsAccompanimentGenerate"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False
    assert response["safety"]["startsPlayback"] is False
