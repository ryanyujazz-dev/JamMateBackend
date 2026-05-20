from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import (
    PRACTICE_COACH_PLAN_REVISION_INTENT_ROUTING_HOTFIX_VERSION,
    infer_practice_plan_revision_reason,
    is_practice_plan_revision_message,
)

ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"
ROOT = Path(__file__).resolve().parents[1]


def _post(client: TestClient, payload: dict) -> dict:
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    return response.json()


def _make_initial_draft(client: TestClient, base: dict) -> dict:
    first = _post(client, {**base, "userMessage": "今天该练什么？"})
    assert first["ok"] is True
    assert first["data"]["responseType"] == "ask_clarifying_question"

    second = _post(client, {**base, "userMessage": "中级，今天可以练30分钟，目标是提升伴奏稳定性，喜欢 bossa 和 swing。"})
    assert second["ok"] is True
    assert second["data"]["responseType"] == "practice_plan_proposal"
    assert second["data"]["stateAfter"]["awaiting_confirmation"] is True
    assert second["data"]["planProposal"]["totalDurationMinutes"] == 30
    return second


def test_revision_intent_adjust_duration_updates_existing_draft_without_routine_card(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_revision_duration.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    base = {"userId": "local-dev-user", "sessionId": "revision-duration", "deviceId": "harmonyos-device-local"}

    original = _make_initial_draft(client, base)
    original_proposal_id = original["data"]["planProposal"]["proposalId"]

    revised = _post(client, {**base, "userMessage": "我想调整为20分钟"})

    assert revised["ok"] is True
    assert revised["code"] == "practice_coach_message_plan_revision_ready"
    assert revised["data"]["selectedActionExecutor"] == "plan_proposal"
    assert revised["data"]["routerDecisionReason"] == "existing_draft_plan_revision_requested"
    assert revised["data"]["responseType"] == "practice_plan_revision"
    assert revised["data"]["planProposalReady"] is True
    assert revised["data"]["routineCardPayload"] is None
    assert revised["data"]["routineStartEnabled"] is False
    proposal = revised["data"]["planProposal"]
    assert proposal["totalDurationMinutes"] == 20
    assert proposal["revisionOfProposalId"] == original_proposal_id
    assert proposal["revisionReason"] == "adjust_duration"
    assert proposal["source"] == "deterministic_practice_coach_plan_revision_routing_hotfix_v2_10_23"
    assert revised["data"]["stateAfter"]["draft_plan"]["totalDurationMinutes"] == 20
    assert revised["data"]["stateAfter"]["awaiting_confirmation"] is True
    assert revised["debug"]["planRevisionIntentRoutingHotfixVersion"] == PRACTICE_COACH_PLAN_REVISION_INTENT_ROUTING_HOTFIX_VERSION
    assert revised["safety"]["startsRoutine"] is False
    assert revised["safety"]["callsEngineAdapter"] is False
    assert revised["safety"]["createsMidiAsset"] is False

    confirmed = _post(client, {**base, "userMessage": "确认这个安排"})
    assert confirmed["ok"] is True
    assert confirmed["data"]["responseType"] == "routine_card_ready"
    assert confirmed["data"]["routerDecisionReason"] == "existing_draft_plan_explicit_confirmation"
    assert confirmed["data"]["routineCardPayload"]["totalDurationMinutes"] == 20
    assert confirmed["data"]["routineCardPayload"]["sourceProposalId"] == proposal["proposalId"]


def test_revision_intent_adjust_focus_and_metronome_updates_existing_draft(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_revision_focus.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    base = {"userId": "local-dev-user", "sessionId": "revision-focus", "deviceId": "harmonyos-device-local"}
    _make_initial_draft(client, base)

    revised = _post(client, {**base, "userMessage": "我想多安排基本功和节拍器稳定性练习"})

    assert revised["ok"] is True
    assert revised["data"]["responseType"] == "practice_plan_revision"
    assert revised["data"]["routerDecisionReason"] == "existing_draft_plan_revision_requested"
    proposal = revised["data"]["planProposal"]
    assert proposal["practiceFocus"] == "fundamentals"
    assert proposal["practiceFocusLabel"] == "基本功"
    assert proposal["revisionReason"] == "adjust_focus"
    assert any("基本功" in block["title"] or "基础" in block["title"] for block in proposal["blocks"])
    assert revised["data"]["stateAfter"]["awaiting_confirmation"] is True


def test_revision_intent_change_tune_updates_existing_draft_to_tune_practice(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_revision_tune.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    base = {"userId": "local-dev-user", "sessionId": "revision-tune", "deviceId": "harmonyos-device-local"}
    _make_initial_draft(client, base)

    revised = _post(client, {**base, "userMessage": "我想换成曲目练习"})

    assert revised["ok"] is True
    assert revised["data"]["responseType"] == "practice_plan_revision"
    proposal = revised["data"]["planProposal"]
    assert proposal["practiceFocus"] == "tune_practice"
    assert proposal["practiceFocusLabel"] == "曲目"
    assert proposal["revisionReason"] == "change_tune"
    assert any(block["type"] == "tune_practice" for block in proposal["blocks"])


def test_revision_helpers_cover_frontend_report_phrases() -> None:
    phrases = [
        "我想调整为20分钟",
        "改成20分钟",
        "多安排基本功",
        "加强节拍器稳定性",
        "换成曲目练习",
        "换一首 standard",
    ]
    for phrase in phrases:
        assert is_practice_plan_revision_message(phrase), phrase
    assert infer_practice_plan_revision_reason("我想调整为20分钟") == "adjust_duration"
    assert infer_practice_plan_revision_reason("换一首 standard") == "change_tune"
    assert infer_practice_plan_revision_reason("多安排基本功") == "adjust_focus"


def test_plan_revision_hotfix_docs_are_updated() -> None:
    doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_PLAN_REVISION_INTENT_ROUTING_HOTFIX_V2_10_23.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "existing_draft_plan_revision_requested" in text
    assert "practice_plan_revision" in text
    assert "我想调整为20分钟" in text
    assert "Routine" in text

    api_text = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    assert "v2_10_23" in api_text
    assert "practice_plan_revision" in api_text
