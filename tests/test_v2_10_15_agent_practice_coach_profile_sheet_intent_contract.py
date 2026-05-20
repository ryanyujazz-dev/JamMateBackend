from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _post_profile_sheet(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/profile-sheet/execute", json=payload).json()


def _block(preview: dict, name: str) -> dict:
    for block in preview["contextBlocks"]:
        if block["name"] == name:
            return block
    raise AssertionError(f"missing context block: {name}")


def test_practice_coach_profile_sheet_intent_requests_native_sheet_when_profile_is_missing(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_profile_sheet.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_profile_sheet(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-profile-sheet-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_profile_sheet_intent_ready"
    assert response["debug"]["traceVersion"] == "v2_10_15"
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False
    assert response["safety"]["writesHarmonyOSLocalState"] is False
    assert response["safety"]["frontendMayOpenNativeSheet"] is True
    assert response["safety"]["frontendOwnsNativeSheetRendering"] is True

    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "request_profile_sheet"
    assert "open_profile_sheet" in action["nextClientActions"]
    assert "submit_profile_form_result" in action["nextClientActions"]
    assert response["data"]["profileSheetIntentReady"] is True
    assert response["data"]["profileFormResultRecorded"] is False
    assert response["data"]["routineCardPayload"] is None
    assert response["data"]["routineStartEnabled"] is False

    sheet = response["data"]["sheetIntent"]
    assert sheet["sheetType"] == "practice_profile_setup"
    assert sheet["presentation"] == "harmonyos_bind_sheet"
    assert sheet["submitAction"]["endpoint"] == "/agent/harmonyos/practice-coach-session/profile-sheet/execute"
    assert sheet["submitAction"]["payloadField"] == "profileFormResult"
    assert sheet["clientRenderingPolicy"]["llmDoesNotRenderUi"] is True
    assert sheet["clientRenderingPolicy"]["frontendOwnsNativeSheet"] is True
    required_keys = {field["fieldKey"] for field in sheet["requiredFields"]}
    assert required_keys == {"primary_instrument", "skill_level", "daily_available_minutes", "main_goal", "preferred_styles"}

    state = response["data"]["stateAfter"]
    assert state["last_agent_action"] == "request_profile_sheet"
    assert set(state["pending_missing_fields"]) == {
        "practice_profile.primary_instrument",
        "practice_profile.skill_level",
        "practice_profile.daily_available_minutes",
        "practice_profile.main_goal",
        "practice_profile.preferred_styles",
    }


def test_practice_coach_profile_sheet_records_submitted_profile_and_projects_it_into_context(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_profile_sheet_submit.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post_profile_sheet(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-profile-sheet-submit",
            "deviceId": "harmonyos-device-local",
            "userMessage": "先补充基础信息",
        },
    )
    assert first["ok"] is True

    response = _post_profile_sheet(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-profile-sheet-submit",
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
    assert response["code"] == "practice_coach_profile_sheet_result_recorded"
    assert response["data"]["profileSheetIntentReady"] is False
    assert response["data"]["profileFormResultRecorded"] is True
    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "chat_message"
    assert action["sheetIntent"] is None
    assert "continue_practice_coach_conversation" in action["nextClientActions"]

    state = response["data"]["stateAfter"]
    assert state["last_agent_action"] == "profile_sheet_result_recorded"
    assert state["pending_missing_fields"] == []
    assert state["collected_fields"]["practice_profile"] == {
        "primary_instrument": "piano",
        "skill_level": "intermediate",
        "daily_available_minutes": 30,
        "main_goal": "提升伴奏稳定性",
        "preferred_styles": ["bossa", "swing"],
    }

    profile_block = _block(response["data"]["llmRequestPreview"], "user_profile_summary")
    assert profile_block["payload"]["instrument"] == "piano"
    assert profile_block["payload"]["level"] == "intermediate"
    assert profile_block["payload"]["default_available_minutes"] == 30
    assert profile_block["payload"]["main_goals"] == ["提升伴奏稳定性"]
    assert profile_block["payload"]["preferred_styles"] == ["bossa", "swing"]


def test_practice_coach_profile_sheet_partial_submission_keeps_missing_fields_and_current_values(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_profile_sheet_partial.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_profile_sheet(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-profile-sheet-partial",
            "deviceId": "harmonyos-device-local",
            "userMessage": "我是中级钢琴，平时30分钟",
            "profileFormResult": {
                "primaryInstrument": "piano",
                "skillLevel": "intermediate",
                "dailyAvailableMinutes": 30,
            },
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_profile_sheet_intent_ready"
    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "request_profile_sheet"
    assert set(action["missingFields"]) == {"practice_profile.main_goal", "practice_profile.preferred_styles"}
    sheet = response["data"]["sheetIntent"]
    field_by_key = {field["fieldKey"]: field for field in sheet["requiredFields"]}
    assert field_by_key["primary_instrument"]["currentValue"] == "piano"
    assert field_by_key["skill_level"]["currentValue"] == "intermediate"
    assert field_by_key["daily_available_minutes"]["currentValue"] == 30
    assert field_by_key["main_goal"]["currentValue"] is None
    assert field_by_key["preferred_styles"]["currentValue"] == []


def test_practice_coach_profile_sheet_preserves_stable_prompt_prefix(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_profile_sheet_cache.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post_profile_sheet(
        client,
        {"userId": "u-profile-cache", "sessionId": "s-profile-cache-1", "deviceId": "d-profile-cache", "userMessage": "需要补充资料"},
    )["data"]["llmRequestPreview"]
    second = _post_profile_sheet(
        client,
        {"userId": "u-profile-cache", "sessionId": "s-profile-cache-2", "deviceId": "d-profile-cache", "userMessage": "我是中级钢琴，平时30分钟"},
    )["data"]["llmRequestPreview"]

    assert first["debugMetadata"]["stable_prefix_digest"] == second["debugMetadata"]["stable_prefix_digest"]
    assert first["blockDigests"]["stable_product_contract"] == second["blockDigests"]["stable_product_contract"]
    assert first["blockDigests"]["stable_action_contract"] == second["blockDigests"]["stable_action_contract"]
    assert first["blockDigests"]["current_user_turn"] != second["blockDigests"]["current_user_turn"]
    all_messages = json.dumps(second["messages"], ensure_ascii=False)
    assert "s-profile-cache-2" not in all_messages
    assert "d-profile-cache" not in all_messages


def test_practice_coach_profile_sheet_docs_are_updated() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_PROFILE_SHEET_INTENT_CONTRACT_V2_10_15.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (api_doc, agent_plan, agent_changelog, dev_text):
        assert "v2_10_15" in text
        assert "Practice Coach Session" in text
        assert "profile-sheet/execute" in text
    assert "request_profile_sheet" in dev_text
    assert "sheetIntent" in dev_text
    assert "不调用大模型" in dev_text
    assert "不启动 Routine" in dev_text
