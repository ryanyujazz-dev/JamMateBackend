from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _post_state(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/message-state/execute", json=payload).json()


def _post_proposal(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/plan-proposal/execute", json=payload).json()


def _post_routine_card(client: TestClient, payload: dict) -> dict:
    return client.post("/agent/harmonyos/practice-coach-session/routine-card/execute", json=payload).json()


def _seed_bossa_proposal(client: TestClient, *, session_id: str) -> dict:
    assert _post_state(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": session_id,
            "deviceId": "harmonyos-device-local",
            "userMessage": "今天该练什么？",
        },
    )["ok"] is True
    assert _post_state(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": session_id,
            "deviceId": "harmonyos-device-local",
            "userMessage": "20 分钟，想练 Bossa",
        },
    )["ok"] is True
    proposal_response = _post_proposal(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": session_id,
            "deviceId": "harmonyos-device-local",
            "userMessage": "生成练习计划草案",
        },
    )
    assert proposal_response["ok"] is True
    assert proposal_response["code"] == "practice_coach_plan_proposal_ready"
    return proposal_response


def test_practice_coach_routine_card_ready_after_explicit_confirmation(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_routine_card.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)
    proposal_response = _seed_bossa_proposal(client, session_id="coach-routine-card-session-1")
    proposal = proposal_response["data"]["planProposal"]

    response = _post_routine_card(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-routine-card-session-1",
            "deviceId": "harmonyos-device-local",
            "userMessage": "确认这个安排",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_routine_card_ready"
    assert response["debug"]["traceVersion"] == "v2_10_14"
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False
    assert response["safety"]["writesHarmonyOSLocalState"] is False

    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "routine_card_ready"
    assert "show_routine_card" in action["nextClientActions"]
    assert "wait_for_user_start_routine" in action["nextClientActions"]

    card = response["data"]["routineCardPayload"]
    assert card["sourceProposalId"] == proposal["proposalId"]
    assert card["title"] == proposal["title"]
    assert card["practiceFocus"] == "bossa"
    assert card["totalDurationMinutes"] == 20
    assert card["presentationType"] == "practice_routine_card"
    assert card["confirmationStatus"] == "confirmed"
    assert card["startEnabled"] is True
    assert card["routineStartEnabled"] is True
    assert card["requiresUserTapToStart"] is True
    assert card["backendStartsRoutine"] is False
    assert card["backendCallsEngine"] is False
    assert card["backendCreatesMidi"] is False
    assert len(card["blocks"]) == 3
    assert sum(block["durationMinutes"] for block in card["blocks"]) == 20

    assert response["data"]["routineStartEnabled"] is True
    assert response["data"]["requiresUserTapToStart"] is True
    assert response["data"]["backendStartsRoutine"] is False
    assert response["data"]["stateAfter"]["awaiting_confirmation"] is False
    assert response["data"]["stateAfter"]["last_agent_action"] == "routine_card_ready"
    assert response["data"]["stateAfter"]["draft_plan"]["confirmationStatus"] == "confirmed"
    assert response["data"]["stateAfter"]["draft_plan"]["routineCardCreated"] is True


def test_practice_coach_routine_card_requires_existing_draft_plan(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_routine_card_missing_plan.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    response = _post_routine_card(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-routine-card-missing-plan",
            "deviceId": "harmonyos-device-local",
            "userMessage": "确认这个安排",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_routine_card_needs_confirmation_or_plan"
    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "ask_clarifying_question"
    assert response["data"]["routineCardPayload"] is None
    assert response["data"]["routineStartEnabled"] is False
    assert "build_practice_plan_proposal_next" in action["nextClientActions"]
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["createsMidiAsset"] is False


def test_practice_coach_routine_card_does_not_convert_without_confirmation(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_routine_card_needs_confirm.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)
    _seed_bossa_proposal(client, session_id="coach-routine-card-needs-confirm")

    response = _post_routine_card(
        client,
        {
            "userId": "local-dev-user",
            "sessionId": "coach-routine-card-needs-confirm",
            "deviceId": "harmonyos-device-local",
            "userMessage": "我想再调整一下",
        },
    )

    assert response["ok"] is True
    assert response["code"] == "practice_coach_routine_card_needs_confirmation_or_plan"
    action = response["data"]["agentActionPreview"]
    assert action["responseType"] == "practice_plan_proposal"
    assert action["requiresUserConfirmation"] is True
    assert response["data"]["routineCardPayload"] is None
    assert response["data"]["stateAfter"]["awaiting_confirmation"] is True
    assert response["data"]["stateAfter"]["last_agent_action"] == "practice_plan_proposal"
    assert response["safety"]["startsRoutine"] is False


def test_practice_coach_routine_card_docs_are_updated() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_PLAN_CONFIRMATION_TO_ROUTINE_CARD_CONTRACT_V2_10_14.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (api_doc, agent_plan, agent_changelog, dev_text):
        assert "v2_10_14" in text
        assert "Practice Coach Session" in text
        assert "routine-card/execute" in text
    assert "routine_card_ready" in dev_text
    assert "不启动 Routine" in dev_text
    assert "不调用 Engine" in dev_text
