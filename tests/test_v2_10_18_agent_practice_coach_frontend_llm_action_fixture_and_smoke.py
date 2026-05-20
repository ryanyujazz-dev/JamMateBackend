from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"

PRODUCT_FIXTURES = [
    "product_practice_coach_message_today_request.json",
    "product_practice_coach_profile_form_submit_request.json",
]
SMOKE_LLM_ACTION_FIXTURES = [
    "smoke_llm_action_ask_clarifying_request.json",
    "smoke_llm_action_request_profile_sheet_request.json",
    "smoke_llm_action_plan_proposal_request.json",
    "smoke_llm_action_routine_card_ready_request.json",
]


def _load(name: str) -> dict:
    return json.loads((SMOKE_DIR / name).read_text(encoding="utf-8"))


def _assert_no_key_recursive(value, forbidden: set[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert key not in forbidden, f"forbidden field {path}.{key} found"
            _assert_no_key_recursive(nested, forbidden, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_key_recursive(item, forbidden, f"{path}[{index}]")


def test_product_practice_coach_fixtures_do_not_leak_backend_or_llm_injection_fields() -> None:
    forbidden = {
        "dbPath",
        "sqliteDbPath",
        "sqlite_db_path",
        "clientConfirmedRecordWrite",
        "client_confirmed_record_write",
        "llmActionDecisionResult",
        "providerResult",
    }
    for fixture_name in PRODUCT_FIXTURES:
        payload = _load(fixture_name)
        _assert_no_key_recursive(payload, forbidden)
        assert payload["userId"]
        assert payload["sessionId"]
        assert payload["deviceId"]
        assert payload["userMessage"]


def test_smoke_llm_action_fixtures_are_marked_as_provider_boundary_injection_only() -> None:
    forbidden_backend = {"dbPath", "sqliteDbPath", "sqlite_db_path", "clientConfirmedRecordWrite", "client_confirmed_record_write"}
    expected_types = {
        "smoke_llm_action_ask_clarifying_request.json": "ask_clarifying_question",
        "smoke_llm_action_request_profile_sheet_request.json": "request_profile_sheet",
        "smoke_llm_action_plan_proposal_request.json": "practice_plan_proposal",
        "smoke_llm_action_routine_card_ready_request.json": "routine_card_ready",
    }
    for fixture_name, response_type in expected_types.items():
        payload = _load(fixture_name)
        _assert_no_key_recursive(payload, forbidden_backend)
        assert payload["llmActionDecisionResult"]["responseType"] == response_type
        assert payload["llmActionDecisionResult"]["message"]


def test_unified_message_execute_accepts_llm_action_smoke_sequence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(tmp_path / "practice_coach_llm_action_fixture.sqlite3"))
    client = TestClient(app)

    ask = _load("smoke_llm_action_ask_clarifying_request.json")
    ask["sessionId"] = "v2-10-18-ask"
    ask_response = client.post(ROUTE, json=ask).json()
    assert ask_response["ok"] is True
    assert ask_response["debug"]["decisionMode"] == "llm_action_decision"
    assert ask_response["debug"]["llmActionDecisionSource"] == "injected_provider_result"
    assert ask_response["debug"]["deterministicFallbackUsed"] is False
    assert ask_response["data"]["responseType"] == "ask_clarifying_question"
    assert ask_response["data"]["conversationStatePersisted"] is True
    assert ask_response["safety"]["startsRoutine"] is False
    assert ask_response["safety"]["createsMidiAsset"] is False

    sheet = _load("smoke_llm_action_request_profile_sheet_request.json")
    sheet["sessionId"] = "v2-10-18-sheet"
    sheet_response = client.post(ROUTE, json=sheet).json()
    assert sheet_response["ok"] is True
    assert sheet_response["data"]["responseType"] == "request_profile_sheet"
    assert sheet_response["data"]["profileSheetIntentReady"] is True
    assert sheet_response["data"]["sheetIntent"]["sheetType"] == "practice_profile_setup"
    assert sheet_response["safety"]["frontendMayOpenNativeSheet"] is True
    assert sheet_response["safety"]["frontendOwnsNativeSheetRendering"] is True

    product_profile = _load("product_practice_coach_profile_form_submit_request.json")
    product_profile["sessionId"] = "v2-10-18-product-profile"
    profile_response = client.post(ROUTE, json=product_profile).json()
    assert profile_response["ok"] is True
    assert profile_response["data"]["responseType"] == "chat_message"
    assert profile_response["data"]["stateAfter"]["collected_fields"]["practice_profile"]["primary_instrument"] == "piano"
    assert profile_response["safety"]["writesHarmonyOSLocalState"] is False

    plan = _load("smoke_llm_action_plan_proposal_request.json")
    card = _load("smoke_llm_action_routine_card_ready_request.json")
    plan["sessionId"] = card["sessionId"] = "v2-10-18-plan-card"
    plan_response = client.post(ROUTE, json=plan).json()
    assert plan_response["ok"] is True
    assert plan_response["data"]["responseType"] == "practice_plan_proposal"
    assert plan_response["data"]["planProposalReady"] is True
    assert plan_response["data"]["planProposal"]["confirmationStatus"] == "awaiting_user_confirmation"
    assert plan_response["data"]["routineCardPayload"] is None
    assert plan_response["data"]["routineStartEnabled"] is False

    card_response = client.post(ROUTE, json=card).json()
    assert card_response["ok"] is True
    assert card_response["data"]["responseType"] == "routine_card_ready"
    assert card_response["data"]["routineCardReady"] is True
    assert card_response["data"]["routineCardPayload"]["title"] == "今日 Bossa Comping 稳定性练习"
    assert card_response["data"]["routineCardPayload"]["backendStartsRoutine"] is False
    assert card_response["data"]["routineCardPayload"]["requiresUserTapToStart"] is True
    assert card_response["safety"]["startsRoutine"] is False
    assert card_response["safety"]["callsEngineAdapter"] is False
    assert card_response["safety"]["createsMidiAsset"] is False
    assert card_response["safety"]["startsPlayback"] is False
    assert card_response["safety"]["writesHarmonyOSLocalState"] is False


def test_curl_smoke_and_docs_reference_fixture_boundary() -> None:
    script = SMOKE_DIR / "curl_practice_coach_llm_action_smoke.sh"
    readme = SMOKE_DIR / "README.md"
    dev_doc = ROOT / "docs" / "AGENT_PRACTICE_COACH_FRONTEND_LLM_ACTION_FIXTURE_SMOKE_V2_10_18.md"
    api_doc = ROOT / "docs" / "API_CONTRACT_V2.md"

    assert script.exists()
    script_text = script.read_text(encoding="utf-8")
    assert "llmActionDecisionResult" in script_text
    assert "Product fixtures omit LLM injection" in script_text
    assert "request_profile_sheet" in script_text
    assert "practice_plan_proposal" in script_text
    assert "routine_card_ready" in script_text
    assert "startsRoutine=false" in script_text
    assert "callsEngineAdapter=false" in script_text

    for path in (readme, dev_doc, api_doc):
        text = path.read_text(encoding="utf-8")
        assert "v2_10_18" in text
        assert "practice-coach-session/message/execute" in text
        assert "llmActionDecisionResult" in text
    assert "Do not copy that field into HarmonyOS product code" in readme.read_text(encoding="utf-8")
    assert "not a HarmonyOS product field" in dev_doc.read_text(encoding="utf-8")


def test_smoke_pack_lists_v2_10_18_unified_practice_coach_fixture_pack() -> None:
    pack = json.loads((SMOKE_DIR / "smoke_pack.json").read_text(encoding="utf-8"))
    assert pack["version"] in {"v2_10_18", "v2_10_19", "v2_10_20"}
    section = pack["practice_coach_unified_llm_action_smoke"]
    assert section["endpoint"] == "POST /agent/harmonyos/practice-coach-session/message/execute"
    assert section["script"] == "curl_practice_coach_llm_action_smoke.sh"
    assert "product_practice_coach_message_today_request.json" in section["product_fixtures"]
    assert "smoke_llm_action_request_profile_sheet_request.json" in section["smoke_only_llm_action_fixtures"]
    assert section["safety_expectations"]["startsRoutine"] is False
