from __future__ import annotations

import json
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


def _block(preview: dict[str, Any], name: str) -> dict[str, Any]:
    for block in preview["contextBlocks"]:
        if block["name"] == name:
            return block
    raise AssertionError(f"missing context block: {name}")


def test_practice_coach_context_builder_preview_uses_cache_friendly_block_order_without_llm_call(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_context_builder.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    completion_response = client.post("/agent/harmonyos/routine-completion-record/execute", json=_load(COMPLETION_FIXTURE)).json()
    assert completion_response["ok"] is True

    response = client.post("/agent/harmonyos/practice-coach-session/context-builder-preview", json=_load(GUIDANCE_FIXTURE)).json()
    assert response["ok"] is True
    assert response["code"] == "practice_coach_context_builder_preview_ready"
    assert response["debug"]["llmCalled"] is False
    assert response["debug"]["networkCallExecuted"] is False
    assert response["safety"]["startsRoutine"] is False
    assert response["safety"]["callsEngineAdapter"] is False
    assert response["safety"]["createsMidiAsset"] is False

    preview = response["data"]["llmRequestPreview"]
    assert preview["contextBuilderVersion"] == "v2_10_11"
    assert [block["name"] for block in preview["contextBlocks"]] == [
        "stable_product_contract",
        "stable_action_contract",
        "user_profile_summary",
        "active_practice_plan_summary",
        "recent_practice_memory_summary",
        "practice_coach_session_state",
        "current_user_turn",
    ]
    assert [block["volatility"] for block in preview["contextBlocks"]] == [
        "static",
        "static",
        "user_profile",
        "plan",
        "memory",
        "session",
        "turn",
    ]
    assert [message["role"] for message in preview["messages"]] == ["system", "system", "user", "user"]
    assert preview["messages"] == preview["chatCompletionsMessagesIfCalled"]
    assert preview["cacheDesign"]["sessionIdTraceIdDeviceIdExcludedFromPrompt"] is True

    message_text = json.dumps(preview["messages"], ensure_ascii=False)
    assert "agent-session-1779200000000" not in message_text
    assert "harmonyos-device-local" not in message_text
    assert "今天该练什么？" in message_text


def test_practice_coach_context_builder_cache_digests_keep_stable_prefix_when_only_turn_changes() -> None:
    client = TestClient(app)
    base = {
        "userId": "local-dev-user",
        "sessionId": "agent-session-stability",
        "deviceId": "harmonyos-device-local",
        "userPracticeProfile": {
            "instrument": "piano",
            "level": "intermediate",
            "preferredStyles": ["bossa", "swing"],
            "mainGoals": ["comping stability"],
            "dailyAvailableMinutes": 30,
        },
        "activePracticePlan": {
            "planId": "plan-1",
            "title": "Bossa comping month",
            "status": "active",
            "currentPhase": "week_1",
            "nextCandidateBlocks": [{"blockId": "b1", "title": "core batida"}],
        },
        "practiceCoachSessionState": {
            "pendingMissingFields": ["available_minutes"],
            "pendingQuestion": "你今天有多少时间？",
            "awaitingConfirmation": False,
        },
        "userMessage": "今天该练什么？",
    }
    first = client.post("/agent/harmonyos/practice-coach-session/context-builder-preview", json=base).json()["data"]["llmRequestPreview"]
    changed = dict(base)
    changed["userMessage"] = "我今天只有20分钟"
    second = client.post("/agent/harmonyos/practice-coach-session/context-builder-preview", json=changed).json()["data"]["llmRequestPreview"]

    assert first["debugMetadata"]["stable_prefix_digest"] == second["debugMetadata"]["stable_prefix_digest"]
    assert first["blockDigests"]["stable_product_contract"] == second["blockDigests"]["stable_product_contract"]
    assert first["blockDigests"]["stable_action_contract"] == second["blockDigests"]["stable_action_contract"]
    assert first["blockDigests"]["user_profile_summary"] == second["blockDigests"]["user_profile_summary"]
    assert first["blockDigests"]["active_practice_plan_summary"] == second["blockDigests"]["active_practice_plan_summary"]
    assert first["blockDigests"]["practice_coach_session_state"] == second["blockDigests"]["practice_coach_session_state"]
    assert first["blockDigests"]["current_user_turn"] != second["blockDigests"]["current_user_turn"]


def test_practice_coach_context_builder_projects_routine_items_and_notes_into_compact_history(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "practice_coach_history_items_notes.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)
    assert client.post("/agent/harmonyos/routine-completion-record/execute", json=_load(COMPLETION_FIXTURE)).json()["ok"] is True

    response = client.post("/agent/harmonyos/practice-coach-session/context-builder-preview", json=_load(GUIDANCE_FIXTURE)).json()
    preview = response["data"]["llmRequestPreview"]
    memory_block = _block(preview, "recent_practice_memory_summary")
    sessions = memory_block["payload"]["recent_sessions"]
    assert sessions
    assert sessions[0]["title"] == "今日基础练习"
    assert sessions[0]["duration_minutes"] == 30.0
    assert sessions[0]["item_summaries"] == [
        {
            "duration_minutes": 15.0,
            "status": "completed",
            "title": "Blue Bossa comping practice",
            "type": "tune_practice",
        }
    ]
    assert sessions[0]["user_note_summary"] == "optional user note"
    assert "notes" not in sessions[0]
    assert "items" not in sessions[0]
    assert response["debug"]["sqliteRowsRead"] >= 1


def test_practice_coach_context_builder_docs_are_agent_track_and_describe_cache_boundary() -> None:
    agent_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_AGENT_V2.md").read_text(encoding="utf-8")
    agent_changelog = (ROOT / "docs" / "CHANGELOG_AGENT.md").read_text(encoding="utf-8")
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_CONTEXT_BUILDER_V2_10_11.md"
    assert dev_doc.exists()
    dev_text = dev_doc.read_text(encoding="utf-8")
    for text in (agent_plan, agent_changelog, api_doc, dev_text):
        assert "v2_10_11" in text
        assert "Practice Coach Session" in text
    for text in (api_doc, dev_text):
        assert "POST /agent/harmonyos/practice-coach-session/context-builder-preview" in text
        assert "stable_product_contract" in text
        assert "recent_practice_memory_summary" in text
        assert "current_user_turn" in text
        assert "不会调用大模型" in text or "does not call an LLM" in text
