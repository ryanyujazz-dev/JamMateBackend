from __future__ import annotations

from dataclasses import dataclass, field

from .policy import ArticulationKind, PedalMode, TouchKind


@dataclass(frozen=True)
class EventExpression:
    event_id: str
    duration_beats: float
    velocity: int
    articulation: str = ArticulationKind.SUSTAIN.value
    pedal: str = PedalMode.NONE.value
    touch: str = TouchKind.NEUTRAL.value
    release_beats: float = 0.0
    accent: float = 0.0
    profile_name: str = "default"
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExpressionPlan:
    events: dict[str, EventExpression]
