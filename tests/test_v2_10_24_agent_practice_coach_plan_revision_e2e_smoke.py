from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"
ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
SEQUENCE_PATH = SMOKE_DIR / "product_practice_coach_plan_revision_e2e_sequence.json"
SCRIPT_PATH = SMOKE_DIR / "curl_practice_coach_plan_revision_e2e_smoke.sh"

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


def _post(client: TestClient, payload: dict) -> dict:
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    return response.json()


def test_product_plan_revision_sequence_fixture_is_black_box_and_complete() -> None:
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    assert sequence["version"] == "v2_10_24"
    assert sequence["endpoint"] == ROUTE
    assert _walk_forbidden(sequence) == []
    messages = [step["userMessage"] for step in sequence["steps"]]
    assert messages == [
        "今天该练什么？",
        "中级，今天可以练30分钟，目标是提升伴奏稳定性，喜欢 bossa 和 swing。",
        "我想调整为20分钟",
        "我想多安排基本功和节拍器稳定性练习",
        "我想换成曲目练习",
        "确认这个安排",
    ]


def test_practice_coach_plan_revision_e2e_sequence_matches_frontend_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_plan_revision_e2e.sqlite3"))
    monkeypatch.setenv("JAMMATE_LLM_ENABLE_NETWORK_CALLS", "false")
    client = TestClient(app)
    sequence = json.loads(SEQUENCE_PATH.read_text(encoding="utf-8"))
    base = dict(sequence["baseRequest"])
    base["sessionId"] = "practice-coach-plan-revision-e2e-test"

    responses = []
    for step in sequence["steps"]:
        body = _post(client, {**base, "userMessage": step["userMessage"]})
        assert body["ok"] is True, step["name"]
        assert body["data"]["responseType"] == step["expect"]["responseType"]
        assert body["safety"]["startsRoutine"] is False
        assert body["safety"]["callsEngineAdapter"] is False
        assert body["safety"]["createsMidiAsset"] is False
        assert body["safety"]["startsPlayback"] is False
        assert body["safety"]["writesHarmonyOSLocalState"] is False
        responses.append(body)

    initial = responses[1]["data"]["planProposal"]
    assert initial["totalDurationMinutes"] == 30
    assert initial["practiceFocus"] == "bossa"
    assert responses[1]["data"]["stateAfter"]["awaiting_confirmation"] is True

    duration_revision = responses[2]["data"]["planProposal"]
    assert responses[2]["data"]["routerDecisionReason"] == "existing_draft_plan_revision_requested"
    assert duration_revision["totalDurationMinutes"] == 20
    assert duration_revision["practiceFocus"] == "bossa"
    assert duration_revision["revisionReason"] == "adjust_duration"
    assert responses[2]["data"]["routineCardPayload"] is None
    assert responses[2]["data"]["routineStartEnabled"] is False

    fundamentals_revision = responses[3]["data"]["planProposal"]
    assert fundamentals_revision["totalDurationMinutes"] == 20
    assert fundamentals_revision["practiceFocus"] == "fundamentals"
    assert fundamentals_revision["revisionReason"] == "adjust_focus"
    assert any("节拍器" in block["goal"] or "技术" in block["title"] or "基本功" in block["title"] for block in fundamentals_revision["blocks"])

    tune_revision = responses[4]["data"]["planProposal"]
    assert tune_revision["totalDurationMinutes"] == 20
    assert tune_revision["practiceFocus"] == "tune_practice"
    assert tune_revision["revisionReason"] == "change_tune"
    assert responses[4]["data"]["stateAfter"]["awaiting_confirmation"] is True

    card = responses[5]["data"]["routineCardPayload"]
    assert responses[5]["data"]["responseType"] == "routine_card_ready"
    assert responses[5]["data"]["routerDecisionReason"] == "existing_draft_plan_explicit_confirmation"
    assert card["totalDurationMinutes"] == 20
    assert card["practiceFocus"] == "tune_practice"
    assert card["backendStartsRoutine"] is False
    assert card["requiresUserTapToStart"] is True
    assert responses[5]["data"]["stateAfter"]["awaiting_confirmation"] is False


def test_plan_revision_curl_smoke_documents_same_sequence_and_no_internal_fields() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "product_practice_coach_plan_revision_e2e_sequence.json" in text
    assert "llmActionDecisionResult" in text
    assert "forbidden field" in text
    assert "我想调整为20分钟" in text or "revise_duration_to_20" in text
    assert "routine_card_ready" in text
    assert "startsRoutine" in text
    assert "writesHarmonyOSLocalState" in text


def test_plan_revision_docs_and_smoke_pack_reference_v2_10_24() -> None:
    doc = (ROOT / "docs" / "AGENT_PRACTICE_COACH_PLAN_REVISION_E2E_SMOKE_V2_10_24.md").read_text(encoding="utf-8")
    assert "v2_10_24" in doc
    assert "curl_practice_coach_plan_revision_e2e_smoke.sh" in doc
    assert "existing_draft_plan_waiting_for_confirmation" in doc
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))
    # Keep the legacy smoke_pack version stable for older frontend smoke tests; v2_10_24 adds an explicit entry.
    assert pack["practice_coach_plan_revision_e2e"]["script"] == "curl_practice_coach_plan_revision_e2e_smoke.sh"
