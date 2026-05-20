from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _post_state(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/message-state/execute", json=payload).json()


def _post_proposal(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/plan-proposal/execute", json=payload).json()


def _block(preview: dict, name: str) -> dict:
    for block in preview["contextBlocks"]:
        if block["name"] == name:
            return block
    raise AssertionError(f"missing context block: {name}")


def test_practice_coach_plan_proposal_contract_builds_structured_proposal_after_missing_fields_are_collected(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_plan_proposal.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    assert _post_state(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-plan-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )["ok"] is True
    assert _post_state(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-plan-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "20 分钟，想练 Bossa",
        },
    )["ok"] is True

    response = _post_proposal(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-plan-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "生成练习计划草案",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_plan_proposal_ready"
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False
    assert response["data"]["routineCardPayload"] is None
    assert response["data"]["routineStartEnabled"] is False
    assert response["data"]["requiresUserConfirmationBeforeRoutineCard"] is True

    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "practice_plan_proposal"
    assert action["requiresUserConfirmation"] is True
    assert "show_practice_plan_proposal" in action["nextClientActions"]

    proposal = response["data"]["planProposal"]
    assert proposal["practiceFocus"] == "bossa"
    assert proposal["totalDurationMinutes"] == 20
    assert proposal["requiresUserConfirmation"] is True
    assert proposal["routineCardCreated"] is False
    assert proposal["routineStartEnabled"] is False
    assert proposal["confirmationStatus"] == "awaiting_user_confirmation"
    assert len(proposal["blocks"]) == 3
    assert sum(block["durationMinutes"] for block in proposal["blocks"]) == 20
    assert proposal["blocks"][0]["title"] == "Bossa 核心节奏热身"

    state_after = response["data"]["stateAfter"]
    assert state_after["awaiting_confirmation"] is True
    assert state_after["draft_plan"]["proposalId"] == proposal["proposalId"]
    assert state_after["pending_missing_fields"] == []
    assert state_after["last_agent_action"] == "practice_plan_proposal"

    preview = response["data"]["llmRequestPreview"]
    session_block = _block(preview, "practice_coach_session_state")
    assert session_block["payload"]["awaiting_confirmation"] is True
    assert session_block["payload"]["draft_plan"]["proposalId"] == proposal["proposalId"]


def test_practice_coach_plan_proposal_contract_asks_for_missing_info_when_context_is_incomplete(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_plan_missing.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_proposal(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-plan-missing",
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_plan_proposal_needs_more_context"
    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "ask_clarifying_question"
    assert set(action["missingFields"]) == {"available_minutes", "practice_focus"}
    assert response["data"]["planProposal"] is None
    assert response["data"]["stateAfter"]["awaiting_confirmation"] is False
    assert response["data"]["stateAfter"]["draft_plan"] is None
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["createsMidiAsset"] is False


def test_practice_coach_plan_proposal_contract_preserves_stable_prompt_prefix(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_plan_cache.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    first = _post_proposal(
        client,
        {
            "userId": "u-cache-plan",
            "sessionId": "s-cache-plan",
            "deviceId": "d-cache-plan",
            "userMessage": "30分钟，练swing",
        },
    )["data"]["llmRequestPreview"]
    second = _post_proposal(
        client,
        {
            "userId": "u-cache-plan",
            "sessionId": "s-cache-plan-2",
            "deviceId": "d-cache-plan",
            "userMessage": "20分钟，练bossa",
        },
    )["data"]["llmRequestPreview"]

    assert first["debugMetadata"]["stable_prefix_digest"] == second["debugMetadata"]["stable_prefix_digest"]
    assert first["blockDigests"]["stable_product_contract"] == second["blockDigests"]["stable_product_contract"]
    assert first["blockDigests"]["stable_action_contract"] == second["blockDigests"]["stable_action_contract"]
    assert first["blockDigests"]["current_user_turn"] != second["blockDigests"]["current_user_turn"]
    assert first["blockDigests"]["practice_coach_session_state"] != second["blockDigests"]["practice_coach_session_state"]
    all_messages = json.dumps(second["messages"], ensure_ascii=False)
    assert "s-cache-plan-2" not in all_messages
    assert "d-cache-plan" not in all_messages


def test_practice_coach_plan_proposal_contract_docs_are_updated() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_PLAN_PROPOSAL_CONTRACT_V2_10_13.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (api_doc, agent_plan, agent_changelog, dev_text):
        assert "v2_10_13" in text
        assert "Practice Coach Session" in text
        assert "plan-proposal/execute" in text
    assert "practice_plan_proposal" in dev_text
    assert "不启动 Routine" in dev_text
    assert "不会调用大模型" in dev_text
