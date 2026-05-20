from __future__ import annotations

from pathlib import Path

from jammate_agent.core.practice_coach_session import (
    PRACTICE_COACH_LLM_ACTION_DECISION_CONTRACT_VERSION,
    build_practice_coach_unified_message_action_router_execute,
)


def _db(tmp_path: Path) -> str:
    return str(tmp_path / "practice_coach_llm_action_decision.sqlite")


def test_injected_llm_can_request_profile_sheet_and_backend_persists_state(tmp_path: Path) -> None:
    result = build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-sheet",
            "sessionId": "s-sheet",
            "sqliteDbPath": _db(tmp_path),
            "userMessage": "今天该练什么？",
            "llmActionDecisionResult": {
                "responseType": "request_profile_sheet",
                "message": "为了更准确安排练习，我需要先了解你的基础信息。",
                "missingFields": ["practice_profile.primary_instrument", "practice_profile.skill_level"],
                "nextClientActions": ["open_profile_sheet", "submit_profile_form_result"],
            },
        }
    )

    assert result["practiceCoachLlmActionDecisionContractVersion"] == PRACTICE_COACH_LLM_ACTION_DECISION_CONTRACT_VERSION
    assert result["decisionMode"] == "llm_action_decision"
    assert result["responseType"] == "request_profile_sheet"
    assert result["selectedActionExecutor"] == "llm_action_decision"
    assert result["deterministicFallbackUsed"] is False
    assert result["statePersisted"] is True
    assert result["sheetIntent"]["sheetType"] == "practice_profile_setup"
    assert result["safety"]["frontendMayOpenNativeSheet"] is True
    assert result["safety"]["llmControlsUiDirectly"] is False
    assert result["safety"]["backendValidatesLlmActionContract"] is True


def test_injected_llm_plan_proposal_becomes_persisted_draft_plan(tmp_path: Path) -> None:
    result = build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-plan",
            "sessionId": "s-plan",
            "sqliteDbPath": _db(tmp_path),
            "userMessage": "今天20分钟，想练Bossa",
            "llmActionDecisionResult": {
                "responseType": "practice_plan_proposal",
                "message": "我建议今天安排 20 分钟 Bossa 稳定性练习。",
                "planProposal": {
                    "title": "今日 Bossa 稳定性练习",
                    "practiceFocus": "bossa",
                    "totalDurationMinutes": 20,
                    "blocks": [
                        {"title": "核心节奏热身", "durationMinutes": 5},
                        {"title": "Blue Bossa 循环", "durationMinutes": 15},
                    ],
                },
                "requiresUserConfirmation": True,
                "nextClientActions": ["show_practice_plan_proposal", "ask_user_to_confirm_or_adjust"],
            },
        }
    )

    assert result["decisionMode"] == "llm_action_decision"
    assert result["responseType"] == "practice_plan_proposal"
    assert result["planProposal"]["confirmationStatus"] == "awaiting_user_confirmation"
    assert result["stateAfter"]["awaiting_confirmation"] is True
    assert result["stateAfter"]["draft_plan"]["title"] == "今日 Bossa 稳定性练习"
    assert result["stateAfter"]["collected_fields"]["available_minutes"] == 20
    assert result["stateAfter"]["collected_fields"]["practice_focus"] == "bossa"
    assert result["safety"]["routineCardCreated"] is False


def test_llm_routine_card_ready_is_rebuilt_from_backend_draft_plan(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-card",
            "sessionId": "s-card",
            "sqliteDbPath": db_path,
            "userMessage": "今天20分钟，想练Bossa",
            "llmActionDecisionResult": {
                "responseType": "practice_plan_proposal",
                "message": "先给你一个草案。",
                "planProposal": {
                    "title": "可信的 Bossa 练习草案",
                    "practiceFocus": "bossa",
                    "totalDurationMinutes": 20,
                    "blocks": [{"title": "Bossa comping", "durationMinutes": 20}],
                },
                "nextClientActions": ["show_practice_plan_proposal"],
            },
        }
    )

    result = build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-card",
            "sessionId": "s-card",
            "sqliteDbPath": db_path,
            "userMessage": "确认这个安排",
            "llmActionDecisionResult": {
                "responseType": "routine_card_ready",
                "message": "好的，生成练习卡片。",
                "routineCard": {"title": "LLM 不能直接决定的卡片标题", "routineStartEnabled": True},
                "nextClientActions": ["show_routine_card", "wait_for_user_start_routine"],
            },
        }
    )

    assert result["responseType"] == "routine_card_ready"
    assert result["routineCardPayload"]["title"] == "可信的 Bossa 练习草案"
    assert result["routineCardPayload"]["startEnabled"] is True
    assert result["safety"]["routineCardCreated"] is True
    assert result["safety"]["clientMustStartRoutineExplicitly"] is True
    assert "routine_card_payload_rebuilt_from_backend_draft_plan" in result["safety"]["safetyNotes"]


def test_invalid_or_forbidden_llm_action_falls_back_to_deterministic_router(tmp_path: Path) -> None:
    result = build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-fallback",
            "sessionId": "s-fallback",
            "sqliteDbPath": _db(tmp_path),
            "userMessage": "今天该练什么？",
            "llmActionDecisionResult": {
                "responseType": "request_profile_sheet",
                "message": "bad",
                "midiBase64": "not_allowed",
                "nextClientActions": ["open_profile_sheet"],
            },
        }
    )

    assert result["decisionMode"] == "deterministic_fallback"
    assert result["deterministicFallbackUsed"] is True
    assert result["llmActionDecisionValidation"]["ok"] is False
    assert result["llmActionDecisionValidation"]["reason"] == "forbidden_action_payload_key"
    assert result["safety"]["llmActionDecisionValidated"] is False
    assert result["responseType"] == "ask_clarifying_question"


def test_llm_action_request_preview_exposes_messages_and_output_contract(tmp_path: Path) -> None:
    result = build_practice_coach_unified_message_action_router_execute(
        {
            "userId": "u-preview",
            "sessionId": "s-preview",
            "sqliteDbPath": _db(tmp_path),
            "userMessage": "今天该练什么？",
            "llmActionDecisionResult": {
                "responseType": "ask_clarifying_question",
                "message": "你今天有多少时间？想练什么方向？",
                "missingFields": ["available_minutes", "practice_focus"],
                "nextClientActions": ["show_chat_message", "show_suggested_replies"],
            },
        }
    )

    preview = result["llmActionRequestPreview"]
    assert preview["contractVersion"] == PRACTICE_COACH_LLM_ACTION_DECISION_CONTRACT_VERSION
    assert preview["outputContract"]["strictJsonOnly"] is True
    assert "request_profile_sheet" in preview["outputContract"]["allowedResponseTypes"]
    assert "practice_plan_proposal" in preview["outputContract"]["allowedResponseTypes"]
    assert "midiBase64" in preview["outputContract"]["forbiddenFields"]
    assert [message["role"] for message in preview["messages"]] == ["system", "system", "user", "user"]
    joined_messages = "\n".join(message["content"] for message in preview["messages"])
    assert "s-preview" not in joined_messages
