from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _post_message(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/message/execute", json=payload).json()


def test_unified_practice_coach_message_routes_clarify_to_proposal_to_routine_card(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_unified_flow.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)
    base = {"userId": "local-dev-user", "sessionId": "coach-unified-flow", "deviceId": "harmonyos-device-local"}

    first = _post_message(client, {**base, "userMessage": "今天该练什么？"})
    assert first["ok"] is True
    assert first["code"] == "practice_coach_message_ask_clarifying_question"
    assert first["debug"]["traceVersion"] == "v2_10_16"
    assert first["debug"]["llmCalled"] is False
    assert first["debug"]["networkCallExecuted"] is False
    assert first["safety"]["startsRoutine"] is False
    assert first["safety"]["callsEngineAdapter"] is False
    assert first["safety"]["createsMidiAsset"] is False
    assert first["safety"]["writesHarmonyOSLocalState"] is False
    assert first["data"]["selectedActionExecutor"] == "message_state"
    assert first["data"]["responseType"] == "ask_clarifying_question"
    assert set(first["data"]["agentActionPreview"]["missingFields"]) == {"available_minutes", "practice_focus"}

    second = _post_message(client, {**base, "userMessage": "20 分钟，想练 Bossa"})
    assert second["ok"] is True
    assert second["code"] == "practice_coach_message_plan_proposal_ready"
    assert second["data"]["selectedActionExecutor"] == "plan_proposal"
    assert second["data"]["responseType"] == "practice_plan_proposal"
    assert second["data"]["planProposalReady"] is True
    assert second["data"]["routineCardPayload"] is None
    proposal = second["data"]["planProposal"]
    assert proposal["practiceFocus"] == "bossa"
    assert proposal["totalDurationMinutes"] == 20
    assert second["data"]["stateAfter"]["awaiting_confirmation"] is True
    assert second["safety"]["startsRoutine"] is False

    third = _post_message(client, {**base, "userMessage": "确认这个安排"})
    assert third["ok"] is True
    assert third["code"] == "practice_coach_message_routine_card_ready"
    assert third["data"]["selectedActionExecutor"] == "routine_card"
    assert third["data"]["responseType"] == "routine_card_ready"
    assert third["data"]["routineCardReady"] is True
    card = third["data"]["routineCardPayload"]
    assert card["sourceProposalId"] == proposal["proposalId"]
    assert card["practiceFocus"] == "bossa"
    assert card["totalDurationMinutes"] == 20
    assert card["backendStartsRoutine"] is False
    assert card["requiresUserTapToStart"] is True
    assert third["data"]["routineStartEnabled"] is True
    assert third["safety"]["startsRoutine"] is False
    assert third["safety"]["callsEngineAdapter"] is False
    assert third["safety"]["createsMidiAsset"] is False


def test_unified_practice_coach_message_routes_profile_form_submission(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_unified_profile.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_message(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-unified-profile",
            "deviceId": "harmonyos-device-local",
            "userMessage": "提交基础信息",
            "profileFormResult": {
                "primaryInstrument": "piano",
                "skillLevel": "intermediate",
                "dailyAvailableMinutes": 30,
                "mainGoal": "提升伴奏稳定性",
                "preferredStyles": ["bossa", "swing"],
            },
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_message_recorded"
    assert response["data"]["selectedActionExecutor"] == "profile_sheet"
    assert response["data"]["responseType"] == "chat_message"
    assert response["data"]["profileSheetIntentReady"] is False
    state = response["data"]["stateAfter"]
    assert state["last_agent_action"] == "profile_sheet_result_recorded"
    assert state["collected_fields"]["practice_profile"]["primary_instrument"] == "piano"
    assert state["collected_fields"]["practice_profile"]["preferred_styles"] == ["bossa", "swing"]
    profile_block = next(block for block in response["data"]["llmRequestPreview"]["contextBlocks"] if block["name"] == "user_profile_summary")
    assert profile_block["payload"]["instrument"] == "piano"
    assert profile_block["payload"]["preferred_styles"] == ["bossa", "swing"]


def test_unified_practice_coach_message_can_explicitly_request_profile_sheet(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_unified_profile_request.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_message(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-unified-profile-request",
            "deviceId": "harmonyos-device-local",
            "userMessage": "帮我补充基础信息",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_message_profile_sheet_intent_ready"
    assert response["data"]["selectedActionExecutor"] == "profile_sheet"
    assert response["data"]["responseType"] == "request_profile_sheet"
    assert response["data"]["profileSheetIntentReady"] is True
    assert response["data"]["sheetIntent"]["sheetType"] == "practice_profile_setup"
    assert "open_profile_sheet" in response["data"]["nextClientActions"]
    assert response["safety"]["frontendMayOpenNativeSheet"] is True


def test_unified_practice_coach_message_preserves_cache_friendly_context_shape(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_unified_cache.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post_message(
        client,
        {"userId": "u-unified-cache", "sessionId": "s-unified-cache-1", "deviceId": "d-unified-cache", "userMessage": "今天该练什么？"},
    )["data"]["llmRequestPreview"]
    second = _post_message(
        client,
        {"userId": "u-unified-cache", "sessionId": "s-unified-cache-2", "deviceId": "d-unified-cache", "userMessage": "今天该练什么？"},
    )["data"]["llmRequestPreview"]

    assert first["debugMetadata"]["stable_prefix_digest"] == second["debugMetadata"]["stable_prefix_digest"]
    assert first["blockDigests"]["stable_product_contract"] == second["blockDigests"]["stable_product_contract"]
    assert first["blockDigests"]["stable_action_contract"] == second["blockDigests"]["stable_action_contract"]


def test_unified_practice_coach_message_docs_are_updated() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_UNIFIED_MESSAGE_ACTION_ROUTER_V2_10_16.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (api_doc, agent_plan, agent_changelog, dev_text):
        assert "v2_10_16" in text
        assert "Practice Coach Session" in text
        assert "practice-coach-session/message/execute" in text
    assert "unified message/action router" in dev_text
    assert "不调用大模型" in dev_text
    assert "不启动 Routine" in dev_text
