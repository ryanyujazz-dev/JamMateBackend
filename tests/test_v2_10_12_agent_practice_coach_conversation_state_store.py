from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _post(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/message-state/execute", json=payload).json()


def _block(preview: dict, name: str) -> dict:
    for block in preview["contextBlocks"]:
        if block["name"] == name:
            return block
    raise AssertionError(f"missing context block: {name}")


def test_practice_coach_session_state_store_persists_first_missing_info_turn(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_session_state.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_session_state_persisted"
    assert response["data"]["conversationStatePersisted"] is True
    assert response["data"]["stateFoundBeforeTurn"] is False
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["safety"]["backendSQLiteWriteMayOccur"] is True
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False

    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "ask_clarifying_question"
    assert set(action["missingFields"]) == {"available_minutes", "practice_focus"}
    assert "多少时间" in action["message"]
    assert response["data"]["stateAfter"]["turn_count"] == 1
    assert set(response["data"]["stateAfter"]["pending_missing_fields"]) == {"available_minutes", "practice_focus"}

    preview = response["data"]["llmRequestPreview"]
    session_block = _block(preview, "practice_coach_session_state")
    assert session_block["payload"]["turn_count"] == 1
    assert set(session_block["payload"]["pending_missing_fields"]) == {"available_minutes", "practice_focus"}


def test_practice_coach_session_state_store_restores_pending_question_and_collects_next_turn(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_session_followup.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-session-followup",
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )
    second = _post(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-session-followup",
            "deviceId": "harmonyos-device-local",
            "userMessage": "20 分钟，想练 Bossa",
        },
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["data"]["stateFoundBeforeTurn"] is True
    assert set(second["data"]["stateBefore"]["pending_missing_fields"]) == {"available_minutes", "practice_focus"}
    assert second["data"]["extractedFieldsFromCurrentTurn"] == {"available_minutes": 20, "practice_focus": "bossa"}
    assert second["data"]["stateAfter"]["turn_count"] == 2
    assert second["data"]["stateAfter"]["pending_missing_fields"] == []
    assert second["data"]["stateAfter"]["collected_fields"] == {"available_minutes": 20, "practice_focus": "bossa"}

    action = second["data"]["agentActionPreview"]
    assert action["responseType"] == "chat_message"
    assert "练习计划草案" in action["message"]
    assert "build_practice_plan_proposal_next" in action["nextClientActions"]

    preview = second["data"]["llmRequestPreview"]
    session_block = _block(preview, "practice_coach_session_state")
    assert session_block["payload"]["collected_fields"] == {"available_minutes": 20, "practice_focus": "bossa"}
    assert session_block["payload"]["pending_missing_fields"] == []


def test_practice_coach_session_state_store_preserves_stable_prefix_across_followup_turns(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_session_cache.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post(
        client,
        {"userId": "u-cache", "sessionId": "s-cache", "deviceId": "d-cache", "userMessage": "今天该练什么？"},
    )["data"]["llmRequestPreview"]
    second = _post(
        client,
        {"userId": "u-cache", "sessionId": "s-cache", "deviceId": "d-cache", "userMessage": "30分钟，练swing"},
    )["data"]["llmRequestPreview"]

    assert first["debugMetadata"]["stable_prefix_digest"] == second["debugMetadata"]["stable_prefix_digest"]
    assert first["blockDigests"]["stable_product_contract"] == second["blockDigests"]["stable_product_contract"]
    assert first["blockDigests"]["stable_action_contract"] == second["blockDigests"]["stable_action_contract"]
    assert first["blockDigests"]["current_user_turn"] != second["blockDigests"]["current_user_turn"]
    assert first["blockDigests"]["practice_coach_session_state"] != second["blockDigests"]["practice_coach_session_state"]
    all_messages = json.dumps(second["messages"], ensure_ascii=False)
    assert "s-cache" not in all_messages
    assert "d-cache" not in all_messages


def test_practice_coach_session_state_store_docs_describe_boundary() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_CONVERSATION_STATE_STORE_V2_10_12.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (api_doc, agent_plan, agent_changelog, dev_text):
        assert "v2_10_12" in text
        assert "Practice Coach Session" in text
        assert "message-state/execute" in text
    assert "不会调用大模型" in dev_text
    assert "不启动 Routine" in dev_text
