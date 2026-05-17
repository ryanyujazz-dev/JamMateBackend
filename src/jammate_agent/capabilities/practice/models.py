from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class ExerciseBlockType(str, Enum):
    TECHNIQUE = "technique"
    TIME_FEEL = "time_feel"
    EAR_TRAINING = "ear_training"
    GUIDE_TONE = "guide_tone"
    VOICING = "voicing"
    COMPING = "comping"
    IMPROVISATION = "improvisation"
    TRANSCRIPTION = "transcription"
    REPERTOIRE = "repertoire"
    REVIEW = "review"
    CUSTOM = "custom"


class ExerciseBlockStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PracticeSessionStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SyncStatus(str, Enum):
    LOCAL_ONLY = "local_only"
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


@dataclass
class PracticeMaterial:
    type: str
    tune: str | None = None
    section: str | None = None
    key: str | None = None
    progression: str | None = None
    bars: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "tune": self.tune,
            "section": self.section,
            "key": self.key,
            "progression": self.progression,
            "bars": self.bars,
            "raw": self.raw,
        }


@dataclass
class AccompanimentPracticeConfig:
    enabled: bool = True
    style: str = "medium_swing"
    tempo: int = 120
    loop_count: int | None = None
    duration_minutes: int | None = None
    section_loop: bool = True
    muted_roles: list[Literal["piano", "bass", "drums", "melody"]] = field(default_factory=list)
    count_in: bool = True
    harmonic_expansion_enabled: bool = False
    density: str = "normal"
    practice_role: str = "general_practice"
    output_format: Literal["midi_base64", "asset_id"] = "midi_base64"
    arrangement_intent: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "style": self.style,
            "tempo": self.tempo,
            "loop_count": self.loop_count,
            "duration_minutes": self.duration_minutes,
            "section_loop": self.section_loop,
            "muted_roles": list(self.muted_roles),
            "count_in": self.count_in,
            "harmonic_expansion_enabled": self.harmonic_expansion_enabled,
            "density": self.density,
            "practice_role": self.practice_role,
            "output_format": self.output_format,
            "arrangement_intent": dict(self.arrangement_intent),
        }


@dataclass
class ExerciseBlock:
    type: ExerciseBlockType
    title: str
    intent: str
    duration_minutes: int
    block_id: str = field(default_factory=lambda: new_id("block"))
    material: PracticeMaterial | None = None
    tempo: int | None = None
    style: str | None = None
    accompaniment_config: AccompanimentPracticeConfig | None = None
    success_criteria: list[str] = field(default_factory=list)
    review_prompt: str | None = None
    status: ExerciseBlockStatus = ExerciseBlockStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "type": self.type.value,
            "title": self.title,
            "intent": self.intent,
            "duration_minutes": self.duration_minutes,
            "material": self.material.to_dict() if self.material else None,
            "tempo": self.tempo,
            "style": self.style,
            "accompaniment_config": self.accompaniment_config.to_dict() if self.accompaniment_config else None,
            "success_criteria": list(self.success_criteria),
            "review_prompt": self.review_prompt,
            "status": self.status.value,
        }


@dataclass
class PracticePlan:
    title: str
    duration_minutes: int
    main_focus: str
    blocks: list[ExerciseBlock]
    plan_id: str = field(default_factory=lambda: new_id("plan"))
    estimated_difficulty: str = "medium"
    explanation: str | None = None
    source: Literal["rule_based", "llm", "template", "hybrid"] = "rule_based"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "main_focus": self.main_focus,
            "blocks": [b.to_dict() for b in self.blocks],
            "estimated_difficulty": self.estimated_difficulty,
            "explanation": self.explanation,
            "source": self.source,
        }


@dataclass
class PracticeSession:
    session_id: str = field(default_factory=lambda: new_id("session"))
    plan_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: PracticeSessionStatus = PracticeSessionStatus.PLANNED
    total_planned_minutes: int | None = None
    total_actual_minutes: int = 0
    current_block_id: str | None = None
    blocks: list[ExerciseBlock] = field(default_factory=list)
    sync_status: SyncStatus = SyncStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "plan_id": self.plan_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status.value,
            "total_planned_minutes": self.total_planned_minutes,
            "total_actual_minutes": self.total_actual_minutes,
            "current_block_id": self.current_block_id,
            "blocks": [b.to_dict() for b in self.blocks],
            "sync_status": self.sync_status.value,
        }


@dataclass
class SessionReview:
    session_id: str
    completed: bool = True
    difficulty: str = "good_challenge"
    focus_score: int | None = None
    time_feel: str | None = None
    tempo_result: dict[str, Any] | None = None
    stuck_points: list[dict[str, Any]] = field(default_factory=list)
    notes: str | None = None
    next_action_preference: str | None = None


@dataclass
class NextStepRecommendation:
    summary: str
    source: Literal["rule_based", "llm", "hybrid"] = "rule_based"
    recommendation_id: str = field(default_factory=lambda: new_id("rec"))
    actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "source": self.source,
            "summary": self.summary,
            "actions": list(self.actions),
        }
