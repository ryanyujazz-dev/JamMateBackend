from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import PRACTICE_COACH_ROUTINE_CARD_COMPLETION_LOOP_SMOKE_VERSION

PC_ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"
COMPLETION_ROUTE = "/agent/harmonyos/routine-completion-record/execute"
ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
SEQUENCE_PATH = SMOKE_DIR / "product_practice_coach_routine_card_completion_loop_sequence.json"
SCRIPT_PATH = SMOKE_DIR / "curl_practice_coach_routine_card_completion_loop_smoke.sh"
FORBIDDEN_PRODUCT_KEYS = {
    "dbPath",
    "sqliteDbPath",
    "sqlite_db_path",
    "clientConfirmedRecordWrite",
    "client_confirmed_record_write",
    "providerResult",
    "llmActionDecisionResult",
    "apiKey",
}


def _walk_forbidden(value, *, path: str = "$", found: list[str] | None = None) -> list[str]:
    found = found if found is not None else []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PRODUCT_KEYS:
                found.append(f"{path}.{key}")
            _walk_forbidden(nested, path=f"{path}.{key}", found=found)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_forbidden(item, path=f"{path}[{index}]", found=found)
    return found


def _post(client: TestClient, route: str, payload: dict) -> dict:
    response = client.post(route, json=payload)
    assert response.status_code == 200
    return response.json()


def _completion_record_from_card(*, base: dict, card: dict) -> dict:
    items = []
    for block in card.get("blocks") or []:
        items.append(
            {
                "itemId": block.get("blockId"),
                "title": block.get("title"),
                "type": block.get("type") or "practice_block",
                "durationSeconds": int(block.get("durationMinutes") or 0) * 60,
                "status": "completed",
            }
        )
    return {
        "userId": base["userId"],
        "sessionId": f"practice-session-{base['sessionId']}",
        "deviceId": base["deviceId"],
        "routineCompletionRecord": {
            "routineId": card.get("routineId"),
            "routineTitle": card.get("title"),
            "completedAt": "2026-05-20T20:30:00+08:00",
            "durationSeconds": int(card.get("totalDurationMinutes") or 0) * 60,
            "status": "completed",
            "items": items,
            "notes": "今天节拍器稳定性比上次好，Bossa 切换仍需继续。",
        },
    }


def _recent_memory_from_practice_coach_response(body: dict) -> dict:
    preview = (body.get("data") or {}).get("llmRequestPreview") or {}
    for block in preview.get("contextBlocks") or []:
        if block.get("name") == "recent_practice_memory_summary":
            payload = block.get("payload")
            return payload if isinstance(payload, dict) else {}
    return {}


def test_product_routine_card_completion_loop_fixture_is_black_box_and_complete() -> None:
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    assert sequence["version"] == PRACTICE_COACH_ROUTINE_CARD_COMPLETION_LOOP_SMOKE_VERSION
    assert sequence["practiceCoachEndpoint"] == PC_ROUTE
    assert sequence["completionEndpoint"] == COMPLETION_ROUTE
    assert _walk_forbidden(sequence) == []
    assert [step["name"] for step in sequence["steps"]] == [
        "create_initial_bossa_plan",
        "revise_duration_to_20",
        "confirm_revised_plan_to_routine_card",
        "submit_routine_completion_record",
        "next_practice_coach_reads_completion_history",
    ]


def test_practice_coach_routine_card_completion_to_next_guidance_loop_reads_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_completion_loop.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    base = dict(sequence["baseRequest"])
    base["sessionId"] = "practice-coach-routine-card-completion-loop-test"

    plan = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][0]["userMessage"]})
    assert plan["ok"] is True
    assert plan["data"]["responseType"] == "practice_plan_proposal"
    assert plan["data"]["planProposal"]["totalDurationMinutes"] == 30
    assert plan["data"]["planProposal"]["practiceFocus"] == "bossa"

    revision = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][1]["userMessage"]})
    assert revision["ok"] is True
    assert revision["data"]["responseType"] == "practice_plan_revision"
    assert revision["data"]["planProposal"]["totalDurationMinutes"] == 20
    assert revision["data"]["stateAfter"]["awaiting_confirmation"] is True
    assert revision["data"]["routineCardPayload"] is None
    assert revision["data"]["routineStartEnabled"] is False

    card_response = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][2]["userMessage"]})
    assert card_response["ok"] is True
    assert card_response["data"]["responseType"] == "routine_card_ready"
    assert card_response["data"]["routineCardReady"] is True
    card = card_response["data"]["routineCardPayload"]
    assert card["totalDurationMinutes"] == 20
    assert card["backendStartsRoutine"] is False
    assert card["requiresUserTapToStart"] is True
    assert card_response["safety"]["startsRoutine"] is False
    assert card_response["safety"]["callsEngineAdapter"] is False
    assert card_response["safety"]["createsMidiAsset"] is False
    assert card_response["safety"]["startsPlayback"] is False

    completion_payload = _completion_record_from_card(base=base, card=card)
    completion = _post(client, COMPLETION_ROUTE, completion_payload)
    assert completion["ok"] is True
    assert completion["code"] == "routine_completion_record_persisted"
    assert completion["data"]["completionRecordPersisted"] is True
    assert completion["data"]["nextTodayGuidanceCanReadHistory"] is True
    assert completion["debug"]["backendDatabaseWritten"] is True
    assert completion["debug"]["sqliteRowsWritten"] is True
    assert completion["safety"]["writesHarmonyOSLocalState"] is False
    assert completion["safety"]["startsRoutine"] is False

    next_request = {
        **base,
        "sessionId": base["sessionId"] + "-next",
        "userMessage": sequence["steps"][4]["userMessage"],
    }
    next_response = _post(client, PC_ROUTE, next_request)
    assert next_response["ok"] is True
    source_projection = next_response["data"]["llmRequestPreview"]["sourceProjection"]
    assert source_projection["sqliteDbPathPresent"] is True
    assert source_projection["sqliteFileExists"] is True
    assert source_projection["sqliteReadOnlyConnectionCreated"] is True
    assert source_projection["sqliteRowsRead"] >= 1
    assert source_projection["recordsProjected"] >= 1
    recent = _recent_memory_from_practice_coach_response(next_response)
    assert recent["aggregate_summary"]["completed_count"] >= 1
    assert recent["aggregate_summary"]["total_recent_minutes"] >= 20
    first_session = recent["recent_sessions"][0]
    assert first_session["title"] == card["title"]
    assert first_session["routine_id"] == card["routineId"]
    assert first_session["completed"] is True
    assert first_session["duration_minutes"] == 20.0
    assert first_session["item_summaries"]
    assert first_session["item_summaries"][0]["title"] == card["blocks"][0]["title"]
    assert first_session["user_note_summary"] == "今天节拍器稳定性比上次好，Bossa 切换仍需继续。"
    assert next_response["debug"]["deviceFeedbackTracePack"]["ioTrace"]["sqliteRowsWritten"] is True
    assert next_response["safety"]["startsRoutine"] is False
    assert next_response["safety"]["writesHarmonyOSLocalState"] is False


def test_routine_card_completion_loop_curl_smoke_documents_same_product_path() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "product_practice_coach_routine_card_completion_loop_sequence.json" in text
    assert PC_ROUTE in text
    assert COMPLETION_ROUTE in text
    assert "completionRecordPersisted" in text
    assert "recent_practice_memory_summary" in text
    assert "llmActionDecisionResult" in text
    assert "forbidden field" in text
    assert "startsRoutine" in text
    assert "writesHarmonyOSLocalState" in text


def test_docs_and_smoke_pack_reference_routine_card_completion_loop_v2_10_26() -> None:
    doc = (ROOT / "docs" / "AGENT_PRACTICE_COACH_ROUTINE_CARD_COMPLETION_LOOP_SMOKE_V2_10_26.md").read_text(encoding="utf-8")
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))
    readme = (SMOKE_DIR / "README.md").read_text(encoding="utf-8")
    assert "v2_10_26" in doc
    assert "routine_card_ready" in doc
    assert "routine-completion-record/execute" in doc
    assert "recent_practice_memory_summary" in doc
    assert pack["practice_coach_routine_card_completion_loop"]["version"] == "v2_10_26"
    assert pack["practice_coach_routine_card_completion_loop"]["script"] == "curl_practice_coach_routine_card_completion_loop_smoke.sh"
    assert "curl_practice_coach_routine_card_completion_loop_smoke.sh" in readme
