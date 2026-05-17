from __future__ import annotations

from typing import Protocol, Sequence

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion

from .pattern_candidate import PatternCandidate
from .pattern_plan import PatternPlan


class PlannerProtocol(Protocol):
    """A style-owned planner that returns pitchless PatternPlans."""

    def plan_region(self, region: HarmonicRegion, context: dict) -> PatternPlan:
        ...


class PatternLibraryProtocol(Protocol):
    """A style-owned pattern library module/object."""

    def get_pattern_candidates(self, context: dict | None = None) -> Sequence[PatternCandidate]:
        ...


StylePatternPlanner = PlannerProtocol
