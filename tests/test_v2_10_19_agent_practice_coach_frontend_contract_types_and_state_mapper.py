from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend_fixtures" / "harmonyos"
TYPES = FRONTEND / "types" / "PracticeCoachTypes.ets"
MAPPER = FRONTEND / "api" / "PracticeCoachStateMapper.ets"
CLIENT = FRONTEND / "api" / "JamMateApiClient.ets"
SMOKE_PACK = FRONTEND / "smoke" / "smoke_pack.json"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_practice_coach_types_define_production_unified_endpoint_contract_without_llm_injection_field() -> None:
    text = _text(TYPES)
    assert "PracticeCoachMessageExecuteRequest" in text
    assert "PracticeCoachMessageExecuteResponse" in text
    assert "PracticeCoachResponseType" in text
    assert "profileFormResult" in text
    assert "request_profile_sheet" in text
    assert "practice_plan_proposal" in text
    assert "routine_card_ready" in text
    assert "PracticeCoachRoutineCardPayload" in text
    assert "backendStartsRoutine: false" in text
    assert "requiresUserTapToStart: true" in text
    assert not re.search(r"llmActionDecisionResult\s*[?:]", text), "production request interface must not expose llmActionDecisionResult"
    assert not re.search(r"providerResult\s*[?:]", text), "production request interface must not expose providerResult"
    assert not re.search(r"sqliteDbPath\s*[?:]", text), "production request interface must not expose sqliteDbPath"


def test_practice_coach_state_mapper_covers_response_types_and_never_autostarts_routine() -> None:
    text = _text(MAPPER)
    for response_type in [
        "ask_clarifying_question",
        "request_profile_sheet",
        "practice_plan_proposal",
        "practice_plan_revision",
        "routine_card_ready",
        "chat_message",
        "cannot_proceed",
    ]:
        assert response_type in text
    for ui_state in ["clarifying", "profile_sheet", "plan_proposal", "routine_card", "backend_error", "network_error"]:
        assert ui_state in text
    assert "safeToAutostartRoutine: false" in text
    assert "canStartRoutine" in text
    assert "requiresUserTapToStart" in text


def test_api_client_exposes_unified_execute_practice_coach_message_method() -> None:
    text = _text(CLIENT)
    assert "PracticeCoachMessageExecuteRequest" in text
    assert "PracticeCoachMessageExecuteResponse" in text
    assert "executePracticeCoachMessage" in text
    assert "/agent/harmonyos/practice-coach-session/message/execute" in text


def test_docs_and_frontend_readmes_describe_response_type_mapping_and_smoke_only_injection_boundary() -> None:
    paths = [
        ROOT / "docs" / "AGENT_PRACTICE_COACH_FRONTEND_CONTRACT_TYPES_STATE_MAPPER_V2_10_19.md",
        ROOT / "docs" / "API_CONTRACT_V2.md",
        FRONTEND / "README.md",
        FRONTEND / "smoke" / "README.md",
    ]
    for path in paths:
        text = _text(path)
        assert "v2_10_19" in text
        assert "practice-coach-session/message/execute" in text
        assert "PracticeCoachTypes.ets" in text
        assert "PracticeCoachStateMapper.ets" in text
        assert "llmActionDecisionResult" in text
        assert "smoke-only" in text or "smoke only" in text or "smoke-only".replace("-", " ") in text
        assert "routine_card_ready" in text


def test_smoke_pack_lists_v2_10_19_frontend_contract_types_and_state_mapper() -> None:
    pack = json.loads(SMOKE_PACK.read_text(encoding="utf-8"))
    assert pack["version"] in {"v2_10_19", "v2_10_20"}
    section = pack["practice_coach_frontend_contract_types_state_mapper"]
    assert section["endpoint"] == "POST /agent/harmonyos/practice-coach-session/message/execute"
    assert section["type_file"] == "../types/PracticeCoachTypes.ets"
    assert section["state_mapper"] == "../api/PracticeCoachStateMapper.ets"
    assert section["api_client_method"] == "executePracticeCoachMessage"
    assert "llmActionDecisionResult" in section["production_request_forbidden_fields"]
    assert section["response_type_to_ui_state"]["request_profile_sheet"] == "profile_sheet"
    assert section["response_type_to_ui_state"]["routine_card_ready"] == "routine_card"
    assert section["autostart_routine"] is False
