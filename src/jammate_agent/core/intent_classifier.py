from __future__ import annotations

from enum import Enum


class AgentIntentType(str, Enum):
    PRACTICE_PLAN_GENERATION = "practice_plan_generation"
    IMMEDIATE_PRACTICE_PLAYBACK = "immediate_practice_playback"
    SESSION_REVIEW = "session_review"
    COACH_QA = "coach_qa"
    UNKNOWN = "unknown"


class IntentClassifier:
    def classify(self, user_input: str) -> AgentIntentType:
        lower = user_input.lower()
        if any(token in lower for token in ["生成伴奏", "播放伴奏", "backing", "play along", "陪练"]):
            return AgentIntentType.IMMEDIATE_PRACTICE_PLAYBACK
        if any(token in lower for token in ["安排", "计划", "routine", "练习计划"]):
            return AgentIntentType.PRACTICE_PLAN_GENERATION
        if any(token in lower for token in ["复盘", "总结", "review"]):
            return AgentIntentType.SESSION_REVIEW
        return AgentIntentType.PRACTICE_PLAN_GENERATION
