from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .beat1_movability import Beat1Movability
from .pattern_event import PatternEvent
from .tail_policy import TailPolicy


@dataclass(frozen=True)
class PatternPlan:
    """Pitchless plan returned by a style planner for one harmonic region."""

    events: list[PatternEvent]
    tail_policy: TailPolicy = field(default_factory=TailPolicy)
    beat1_movability: Beat1Movability = field(default_factory=Beat1Movability)
    selected_candidate: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def combine(plans: list["PatternPlan"], *, selected_candidate: str | None = None, metadata: dict[str, Any] | None = None) -> "PatternPlan":
        events: list[PatternEvent] = []
        occupied: list[float] = []
        for plan in plans:
            events.extend(plan.events)
            occupied.extend(plan.tail_policy.occupied_local_beats)
        tail_policy = TailPolicy.from_local_beats(tuple(occupied))
        return PatternPlan(
            events=events,
            tail_policy=tail_policy,
            beat1_movability=plans[0].beat1_movability if plans else Beat1Movability(),
            selected_candidate=selected_candidate,
            metadata=dict(metadata or {}),
        )
