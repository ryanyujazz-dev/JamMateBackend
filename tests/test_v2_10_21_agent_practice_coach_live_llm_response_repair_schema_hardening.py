from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app
from jammate_agent.core.practice_coach_session import (
    PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_VERSION,
    parse_practice_coach_llm_action_content_detailed,
)

ROUTE = "/agent/harmonyos/practice-coach-session/message/execute"


def _base_payload(tmp_path: Path, *, session_id: str, message: str = "今天20分钟想练Bossa") -> dict:
    return {
        "userId": "local-dev-user",
        "sessionId": session_id,
        "deviceId": "harmonyos-device-local",
        "userMessage": message,
        "sqliteDbPath": str(tmp_path / "practice_coach_response_repair.sqlite3"),
    }


def test_parser_repairs_markdown_preface_and_nested_action_json() -> None:
    raw = """
当然可以。下面是结构化 action：

```json
{
  "action": {
    "type": "profile_sheet",
    "content": "为了给你安排更准确的练习，我需要先了解你的基础信息。",
    "missing_fields": ["practice_profile.primary_instrument"]
  }
}
```
"""
    action, error, repair_report = parse_practice_coach_llm_action_content_detailed(raw)

    assert error is None
    assert action is not None
    assert action["type"] == "profile_sheet"
    assert action["content"].startswith("为了给你安排")
    assert repair_report["repairVersion"] == PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_VERSION
    assert repair_report["markdownFenceStripped"] is True
    assert repair_report["nestedActionUnwrapped"] is True
    assert repair_report["parseRepairApplied"] is True


def test_unified_message_repairs_llm_markdown_alias_plan_proposal_without_fallback(tmp_path: Path) -> None:
    client = TestClient(app)
    payload = _base_payload(tmp_path, session_id="v2-10-21-repair-plan")
    payload["llmActionDecisionResult"] = """
这里是建议：

```json
{
  "type": "plan_proposal",
  "content": "我建议今天先按 20 分钟 Bossa 稳定性练习。",
  "title": "今日 Bossa 稳定性练习",
  "durationMinutes": 20,
  "focus": "bossa",
  "blocks": [
    {"name": "Bossa 核心节奏热身", "minutes": 5, "description": "稳定 1、2、3& 的核心 batida。"},
    {"name": "Bossa 曲式循环练习", "minutes": 11, "description": "在曲式里保持 comping 稳定。"},
    {"name": "回听与记录", "minutes": 4, "description": "记录最不稳定的换和弦点。"}
  ],
  "actions": ["show_practice_plan_proposal", "ask_user_to_confirm_or_adjust"]
}
```
"""

    response = client.post(ROUTE, json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["responseType"] == "practice_plan_proposal"
    assert body["data"]["planProposalReady"] is True
    assert body["data"]["planProposal"]["title"] == "今日 Bossa 稳定性练习"
    assert body["data"]["planProposal"]["totalDurationMinutes"] == 20
    assert body["data"]["planProposal"]["blocks"][0]["durationMinutes"] == 5
    assert body["debug"]["deterministicFallbackUsed"] is False
    assert body["debug"]["llmActionDecisionValidation"]["ok"] is True
    repair = body["debug"]["llmActionDecisionRepairReport"]
    assert repair["parseRepairApplied"] is True
    assert repair["schemaRepairApplied"] is True
    assert "response_type_alias_repaired" in repair["schemaWarnings"]
    assert "message_alias_repaired" in repair["schemaWarnings"]
    assert "plan_proposal_repaired_from_top_level_fields" in repair["schemaWarnings"]
    assert body["safety"]["startsRoutine"] is False
    assert body["safety"]["callsEngineAdapter"] is False
    assert body["safety"]["createsMidiAsset"] is False


def test_unified_message_repairs_profile_sheet_alias_and_defaults_backend_sheet_intent(tmp_path: Path) -> None:
    client = TestClient(app)
    payload = _base_payload(tmp_path, session_id="v2-10-21-repair-sheet", message="帮我先补充基础信息")
    payload["llmActionDecisionResult"] = {
        "response_type": "bindSheet",
        "text": "我需要先了解你的基础练习信息。",
        "missing": ["practice_profile.primary_instrument", "practice_profile.skill_level"],
    }

    response = client.post(ROUTE, json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["responseType"] == "request_profile_sheet"
    assert body["data"]["profileSheetIntentReady"] is True
    assert body["data"]["sheetIntent"]["sheetType"] == "practice_profile_setup"
    assert body["data"]["sheetIntent"]["clientRenderingPolicy"]["frontendOwnsNativeSheet"] is True
    repair = body["debug"]["llmActionDecisionRepairReport"]
    assert repair["schemaRepairApplied"] is True
    assert "response_type_alias_repaired" in repair["schemaWarnings"]
    assert "sheet_intent_defaulted_by_backend" in repair["schemaWarnings"]
    assert body["safety"]["frontendMayOpenNativeSheet"] is True
    assert body["safety"]["startsRoutine"] is False


def test_forbidden_llm_payload_is_rejected_and_deterministic_fallback_is_used(tmp_path: Path) -> None:
    client = TestClient(app)
    payload = _base_payload(tmp_path, session_id="v2-10-21-forbidden")
    payload["llmActionDecisionResult"] = {
        "responseType": "routine_card_ready",
        "message": "我已经直接开始生成播放资产。",
        "midiBase64": "forbidden",
    }

    response = client.post(ROUTE, json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["debug"]["deterministicFallbackUsed"] is True
    assert body["debug"]["llmActionDecisionValidation"]["ok"] is False
    assert body["debug"]["llmActionDecisionValidation"]["reason"] == "forbidden_action_payload_key"
    assert body["data"]["responseType"] != "routine_card_ready"
    assert body["safety"]["startsRoutine"] is False
    assert body["safety"]["callsEngineAdapter"] is False
    assert body["safety"]["createsMidiAsset"] is False


def test_v2_10_21_docs_record_repair_and_schema_hardening() -> None:
    root = Path(__file__).resolve().parents[1]
    dev_doc = root / "docs" / "AGENT_PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_V2_10_21.md"
    api_doc = root / "docs" / "API_CONTRACT_V2.md"
    changelog = root / "docs" / "CHANGELOG_AGENT.md"

    for path in (dev_doc, api_doc, changelog):
        text = path.read_text(encoding="utf-8")
        assert "v2_10_21" in text
        assert "response repair" in text or "Response Repair" in text or "响应修复" in text
        assert "schema" in text.lower() or "契约" in text
        assert "deterministic fallback" in text or "deterministic fallback" in text.lower() or "兜底" in text
        assert "不启动 Routine" in text or "startsRoutine=false" in text or "startsRoutine = false" in text
