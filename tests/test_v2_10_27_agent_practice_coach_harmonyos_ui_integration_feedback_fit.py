from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION

PC_ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"
COMPLETION_ROUTE = "/agent/harmonyos/routine-completion-record/execute"
ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
SEQUENCE_PATH = SMOKE_DIR / "product_practice_coach_harmonyos_ui_integration_sequence.json"
SCRIPT_PATH = SMOKE_DIR / "curl_practice_coach_harmonyos_ui_integration_smoke.sh"
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
            "items": [
                {
                    "itemId": block.get("blockId"),
                    "title": block.get("title"),
                    "type": block.get("type") or "practice_block",
                    "durationSeconds": int(block.get("durationMinutes") or 0) * 60,
                    "status": "completed",
                }
                for block in card.get("blocks") or []
            ],
            "notes": "UI integration smoke completion record.",
        },
    }


def _assert_ui_action(body: dict, expected: dict) -> dict:
    ui_action = ((body.get("data") or {}).get("frontendUiAction") or (body.get("debug") or {}).get("frontendUiAction") or {})
    assert ui_action["version"] == PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION
    for key, value in expected.items():
        assert ui_action.get(key) == value, f"{key}: expected {value!r}, got {ui_action.get(key)!r} in {ui_action}"
    assert ui_action["safeToAutostartRoutine"] is False
    assert ui_action["backendStartsRoutine"] is False
    return ui_action


def _recent_memory_from_practice_coach_response(body: dict) -> dict:
    preview = (body.get("data") or {}).get("llmRequestPreview") or {}
    for block in preview.get("contextBlocks") or []:
        if block.get("name") == "recent_practice_memory_summary":
            payload = block.get("payload")
            return payload if isinstance(payload, dict) else {}
    return {}


def test_ui_integration_fixture_is_black_box_and_documents_expected_actions() -> None:
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    assert sequence["version"] == PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION
    assert sequence["practiceCoachEndpoint"] == PC_ROUTE
    assert sequence["completionEndpoint"] == COMPLETION_ROUTE
    assert _walk_forbidden(sequence) == []
    assert [step["name"] for step in sequence["steps"]] == [
        "create_initial_plan_card",
        "revise_plan_card_replace_current",
        "confirm_to_routine_card",
        "submit_completion_and_show_recorded_summary",
        "next_guidance_reads_history",
    ]


def test_practice_coach_response_includes_frontend_ui_action_for_cards_and_completion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_ui_integration.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    base = dict(sequence["baseRequest"])
    base["sessionId"] = "practice-coach-ui-integration-test"

    plan = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][0]["userMessage"]})
    assert plan["ok"] is True
    assert plan["data"]["responseType"] == "practice_plan_proposal"
    plan_ui = _assert_ui_action(plan, sequence["steps"][0]["expectedUiAction"])
    assert plan_ui["payloadRefs"]["planProposal"] == "data.planProposal"

    revision = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][1]["userMessage"]})
    assert revision["ok"] is True
    assert revision["data"]["responseType"] == "practice_plan_revision"
    revision_ui = _assert_ui_action(revision, sequence["steps"][1]["expectedUiAction"])
    assert revision_ui["shouldReplaceCurrentProposal"] is True
    assert revision["data"]["planProposal"]["totalDurationMinutes"] == 20

    card_response = _post(client, PC_ROUTE, {**base, "userMessage": sequence["steps"][2]["userMessage"]})
    assert card_response["ok"] is True
    assert card_response["data"]["responseType"] == "routine_card_ready"
    card_ui = _assert_ui_action(card_response, sequence["steps"][2]["expectedUiAction"])
    assert card_ui["payloadRefs"]["routineCardPayload"] == "data.routineCardPayload"
    assert card_response["safety"]["startsRoutine"] is False
    assert card_response["safety"]["callsEngineAdapter"] is False
    card = card_response["data"]["routineCardPayload"]

    completion = _post(client, COMPLETION_ROUTE, _completion_record_from_card(base=base, card=card))
    assert completion["ok"] is True
    assert completion["data"]["completionRecordPersisted"] is True
    completion_ui = _assert_ui_action(completion, sequence["steps"][3]["expectedUiAction"])
    assert completion_ui["shouldOpenPracticeCoach"] is False
    assert completion_ui["shouldShowPostSessionRecommendationCard"] is False
    assert completion["safety"]["createsPostSessionRecommendationCard"] is False

    next_response = _post(
        client,
        PC_ROUTE,
        {**base, "sessionId": base["sessionId"] + "-next", "userMessage": sequence["steps"][4]["userMessage"]},
    )
    assert next_response["ok"] is True
    recent = _recent_memory_from_practice_coach_response(next_response)
    assert recent["recent_sessions"]
    assert recent["recent_sessions"][0]["title"] == card["title"]


def test_practice_coach_types_and_mapper_reference_frontend_ui_action() -> None:
    types = (ROOT / "frontend_fixtures" / "harmonyos" / "types" / "PracticeCoachTypes.ets").read_text(encoding="utf-8")
    mapper = (ROOT / "frontend_fixtures" / "harmonyos" / "api" / "PracticeCoachStateMapper.ets").read_text(encoding="utf-8")
    assert "PracticeCoachFrontendUiAction" in types
    assert "frontendUiAction?: PracticeCoachFrontendUiAction" in types
    assert "shouldReplaceCurrentProposal" in mapper
    assert "shouldShowRecordedSummary" in mapper
    assert "safeToAutostartRoutine: false" in mapper


def test_ui_integration_smoke_pack_and_docs_reference_v2_10_27() -> None:
    doc = (ROOT / "docs" / "AGENT_PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_V2_10_27.md").read_text(encoding="utf-8")
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))
    readme = (SMOKE_DIR / "README.md").read_text(encoding="utf-8")
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "v2_10_27" in doc
    assert "frontendUiAction" in doc
    assert "replace_plan_proposal_card" in doc
    assert pack["practice_coach_harmonyos_ui_integration_feedback_fit"]["version"] == "v2_10_27"
    assert pack["practice_coach_harmonyos_ui_integration_feedback_fit"]["script"] == "curl_practice_coach_harmonyos_ui_integration_smoke.sh"
    assert "curl_practice_coach_harmonyos_ui_integration_smoke.sh" in readme
    assert "frontendUiAction" in script
