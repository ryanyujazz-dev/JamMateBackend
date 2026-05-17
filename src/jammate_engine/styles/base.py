from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Sequence, Any

from jammate_engine.core.anticipation import AnticipationPolicy
from jammate_engine.core.expression import ExpressionPolicyBundle
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime.pattern_candidate import PatternCandidate
from jammate_engine.core.pattern_runtime.pattern_plan import PatternPlan
from jammate_engine.core.voicing import VoicingPolicy

PatternSource = Callable[[dict | None], Sequence[PatternCandidate]]


@dataclass(frozen=True)
class StylePolicyBundle:
    """Style-owned policy bundle consumed by core stages."""

    expression_policy: ExpressionPolicyBundle = field(default_factory=ExpressionPolicyBundle)
    anticipation_policy: AnticipationPolicy = field(default_factory=AnticipationPolicy)
    voicing_policy: VoicingPolicy = field(default_factory=VoicingPolicy)
    gesture_policy: dict = field(default_factory=dict)
    fill_policy: dict = field(default_factory=dict)
    arrangement_policy: dict = field(default_factory=dict)
    bass_foundation_policy: dict = field(default_factory=dict)
    timing_policy: dict = field(default_factory=dict)

    def merge(self, overrides: dict | None = None) -> "StylePolicyBundle":
        overrides = overrides or {}
        expression_override = overrides.get("expression_policy")
        anticipation_override = overrides.get("anticipation_policy")
        anticipation_policy = anticipation_override if isinstance(anticipation_override, AnticipationPolicy) else self.anticipation_policy
        return StylePolicyBundle(
            expression_policy=self.expression_policy.merge(expression_override) if expression_override else self.expression_policy,
            anticipation_policy=anticipation_policy,
            voicing_policy=self.voicing_policy.merge(overrides.get("voicing_policy")),
            gesture_policy={**self.gesture_policy, **dict(overrides.get("gesture_policy", {}))},
            fill_policy={**self.fill_policy, **dict(overrides.get("fill_policy", {}))},
            arrangement_policy={**self.arrangement_policy, **dict(overrides.get("arrangement_policy", {}))},
            bass_foundation_policy={**self.bass_foundation_policy, **dict(overrides.get("bass_foundation_policy", {}))},
            timing_policy={**self.timing_policy, **dict(overrides.get("timing_policy", {}))},
        )

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "expression_policy": self.expression_policy.to_legacy_dict(),
            "anticipation_policy": {
                "enabled": self.anticipation_policy.enabled,
                "probability": self.anticipation_policy.probability,
                "target_offset_beats": self.anticipation_policy.target_offset_beats,
                "eligible_tracks": list(self.anticipation_policy.eligible_tracks),
                "eligible_roles": list(self.anticipation_policy.eligible_roles),
                "debug_name": self.anticipation_policy.debug_name,
            },
            "voicing_policy": self.voicing_policy.to_debug_dict(),
            "gesture_policy": dict(self.gesture_policy),
            "fill_policy": dict(self.fill_policy),
            "arrangement_policy": dict(self.arrangement_policy),
            "bass_foundation_policy": dict(self.bass_foundation_policy),
            "timing_policy": dict(self.timing_policy),
        }


def choose_weighted_candidate(candidates: Sequence[PatternCandidate], rng: random.Random | None = None) -> PatternCandidate:
    if not candidates:
        raise ValueError("Pattern source returned no candidates")
    if rng is None:
        # Deterministic default for reproducibility and tests.
        return max(candidates, key=lambda c: c.weight)
    total = sum(max(0.0, c.weight) for c in candidates)
    if total <= 0:
        return candidates[0]
    needle = rng.random() * total
    acc = 0.0
    for candidate in candidates:
        acc += max(0.0, candidate.weight)
        if needle <= acc:
            return candidate
    return candidates[-1]


@dataclass(frozen=True)
class StyleProfile:
    name: str
    policies: StylePolicyBundle = field(default_factory=StylePolicyBundle)
    pattern_sources: tuple[PatternSource, ...] = field(default_factory=tuple)
    bass_foundation_source: PatternSource | None = None

    @property
    def expression_policy(self) -> ExpressionPolicyBundle:
        return self.policies.expression_policy

    @property
    def anticipation_policy(self) -> AnticipationPolicy:
        return self.policies.anticipation_policy

    @property
    def voicing_policy(self) -> VoicingPolicy:
        return self.policies.voicing_policy

    @property
    def gesture_policy(self) -> dict:
        return self.policies.gesture_policy

    @property
    def fill_policy(self) -> dict:
        return self.policies.fill_policy

    @property
    def arrangement_policy(self) -> dict:
        return self.policies.arrangement_policy

    @property
    def bass_foundation_policy(self) -> dict:
        return self.policies.bass_foundation_policy

    @property
    def timing_policy(self) -> dict:
        return self.policies.timing_policy

    def merge_policies(self, overrides: dict | None = None) -> StylePolicyBundle:
        return self.policies.merge(overrides)

    def plan_region(self, region: HarmonicRegion, context: dict) -> PatternPlan:
        """Default style planner: select one candidate from each style-owned source.

        v2_0_9 passes the current region into style-owned pattern libraries so
        candidates can respect two-chord bars without emitting events past the
        harmonic region. It also offers a lightweight history guard, controlled
        by arrangement policy, to avoid immediately repeating the same pattern.
        """

        rng = context.get("rng") if isinstance(context.get("rng"), random.Random) else None
        region_context = {
            **dict(context),
            "region": region,
            "region_duration_beats": region.duration_beats,
            "chord_symbol": region.chord_symbol,
            "next_chord_symbol": region.next_chord_symbol,
        }
        history = region_context.get("style_pattern_history")
        if not isinstance(history, dict):
            history = {}
        avoid_repeat = bool(self.arrangement_policy.get("avoid_immediate_pattern_repeat", False))
        avoid_category_repeat = bool(self.arrangement_policy.get("avoid_immediate_pattern_category_repeat", False))
        piano_density_guard = bool(self.arrangement_policy.get("piano_comping_density_guard", False))

        plans: list[PatternPlan] = []
        selected: list[str] = []
        for source_index, source in enumerate(self.pattern_sources):
            candidates = tuple(source(region_context))
            if not candidates:
                continue
            source_key = f"{self.name}:{source_index}:{getattr(source, '__module__', '')}.{getattr(source, '__name__', 'source')}"
            choice_pool = candidates
            if avoid_repeat and len(choice_pool) > 1:
                previous_name = history.get(source_key)
                filtered = tuple(candidate for candidate in choice_pool if candidate.name != previous_name)
                if filtered:
                    choice_pool = filtered
            if avoid_category_repeat and len(choice_pool) > 1:
                previous_category = history.get(f"{source_key}:category")
                filtered = tuple(candidate for candidate in choice_pool if candidate.category != previous_category)
                if filtered:
                    choice_pool = filtered
            if piano_density_guard and ".comping_patterns" in source_key and len(choice_pool) > 1:
                previous_density = history.get(f"{source_key}:density")
                if previous_density == "dense":
                    filtered = tuple(candidate for candidate in choice_pool if candidate.metadata.get("density") != "dense")
                    if filtered:
                        choice_pool = filtered
            candidate = choose_weighted_candidate(choice_pool, rng)
            history[source_key] = candidate.name
            history[f"{source_key}:category"] = candidate.category
            if ".comping_patterns" in source_key:
                history[f"{source_key}:density"] = str(candidate.metadata.get("density", "medium"))
            selected.append(candidate.name)
            plans.append(candidate.instantiate(region))
        return PatternPlan.combine(
            plans,
            selected_candidate=" + ".join(selected),
            metadata={"style": self.name, "selected_candidates": selected},
        )
