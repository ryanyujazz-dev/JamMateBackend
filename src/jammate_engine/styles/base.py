from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from typing import Callable, Sequence, Any

from jammate_engine.core.anticipation import AnticipationPolicy
from jammate_engine.core.expression import ExpressionPolicyBundle
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.harmony.harmonic_context import FunctionalMotion, classify_functional_motion
from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime.beat1_movability import Beat1Movability
from jammate_engine.core.pattern_runtime.pattern_candidate import PatternCandidate
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.pattern_runtime.pattern_plan import PatternPlan
from jammate_engine.core.pattern_runtime.tail_policy import TailPolicy
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


PIANO_COMPING_HISTORY_CONTINUITY_SCORER_VERSION = "v2_6_59"
PIANO_COMPING_HARMONIC_FUNCTION_POLICY_VERSION = "v2_6_60"
PIANO_COMPING_PROGRESSION_SPECIFIC_SUBSET_POLICY_VERSION = "v2_6_65"
PIANO_COMPING_NO_4AND_DELAYED_TAIL_POLICY_VERSION = "v2_6_66"
PIANO_COMPING_REGION_FIRST_COVERAGE_GUARD_VERSION = "v2_6_62"



def _region_length_family_for_coverage(duration_beats: float) -> str:
    rounded = round(float(duration_beats), 2)
    if rounded <= 1.25:
        return "one_beat_region"
    if rounded <= 2.25:
        return "two_beat_region"
    if rounded <= 3.25:
        return "three_beat_region"
    if rounded <= 4.25:
        return "four_beat_region"
    if rounded <= 5.25:
        return "five_beat_region"
    return "long_region"


def _coverage_guard_metadata(region: HarmonicRegion, *, outcome: str, inserted: bool = False) -> dict[str, Any]:
    return {
        "piano_region_first_coverage_guard_version": PIANO_COMPING_REGION_FIRST_COVERAGE_GUARD_VERSION,
        "piano_region_first_coverage_guard_checked": True,
        "piano_region_first_coverage_guard_outcome": outcome,
        "piano_region_first_coverage_guard_inserted": bool(inserted),
        "piano_region_first_coverage_guard_scope": "ChordRegion",
        "piano_region_first_coverage_guard_contract": "CoverageGuard is a fallback after region-length pattern policy; it only inserts a pitchless region-start anchor when a ChordRegion would otherwise have no piano harmonic presence, and never routes through bar-first/two-chord-bar logic.",
        "coverage_time_reference": "region_local_beats",
        "coverage_region_duration_beats": float(region.duration_beats),
        "coverage_region_length_family": _region_length_family_for_coverage(float(region.duration_beats)),
        "coverage_requires_region_start_anchor": float(region.duration_beats) <= 2.25,
        "coverage_guard_is_backup_only": True,
    }


def _apply_piano_region_first_coverage_guard(
    plan: PatternPlan,
    *,
    region: HarmonicRegion,
    style_name: str,
    enabled: bool,
) -> PatternPlan:
    """Ensure selected Medium Swing piano plans have region-first harmonic presence.

    The guard is intentionally downstream of the normal ChordRegion-length
    pattern policy and upstream of anticipation/expression/voicing.  It does not
    choose voicing, duration, velocity, pedal, or a new rhythm vocabulary.  In
    the common case it only stamps audit metadata onto already-selected piano
    events.  It inserts a single region-start fallback anchor only if the
    selected plan contains no piano harmonic event for the region.
    """

    if not enabled:
        return plan
    piano_events = [event for event in plan.events if event.track == "piano" and event.role == "harmonic"]
    if piano_events:
        metadata = _coverage_guard_metadata(region, outcome="covered_by_selected_region_length_pattern", inserted=False)
        annotated_events = [
            replace(event, metadata={**dict(event.metadata), **metadata}) if event.track == "piano" and event.role == "harmonic" else event
            for event in plan.events
        ]
        return replace(
            plan,
            events=annotated_events,
            metadata={
                **dict(plan.metadata),
                "piano_region_first_coverage_guard_version": PIANO_COMPING_REGION_FIRST_COVERAGE_GUARD_VERSION,
                "piano_region_first_coverage_guard_checked": True,
                "piano_region_first_coverage_guard_inserted": False,
                "piano_region_first_coverage_guard_outcome": "covered_by_selected_region_length_pattern",
            },
        )

    fallback_metadata = _coverage_guard_metadata(region, outcome="inserted_region_start_fallback_anchor", inserted=True)
    fallback = PatternEvent(
        event_id=f"{region.region_id}_piano_region_first_coverage_fallback_anchor_0",
        track="piano",
        region_id=region.region_id,
        chord_symbol=region.chord_symbol,
        onset_beat=region.start_beat,
        role="harmonic",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(metadata={"coverage_guard_fallback": True}),
        expression_hint="comp_short" if float(region.duration_beats) <= 2.25 else "comp_medium",
        pattern_id="piano_region_first_coverage_fallback_anchor",
        local_beat=0.0,
        metadata={
            "candidate": "piano_region_first_coverage_fallback_anchor",
            "category": "coverage_guard_region_start_anchor",
            "style_id": style_name,
            "event_role": "coverage_anchor",
            "semantic_expression_hint": "light_stab" if float(region.duration_beats) <= 2.25 else "soft_hold",
            "required": True,
            "can_anticipate": False,
            "region_duration_beats": float(region.duration_beats),
            "region_section_id": region.section_id,
            "region_section_label": region.section_label,
            "region_phrase": region.phrase,
            "region_chorus_index": region.chorus_index,
            "region_total_choruses": region.total_choruses,
            "region_bar_index": region.bar_index,
            "region_source_bar_index": region.source_bar_index,
            "region_written_bar_index": region.written_bar_index,
            "region_performance_bar_index": region.performance_bar_index,
            "time_reference": "region_local_beats",
            **fallback_metadata,
        },
    )
    occupied = tuple(dict.fromkeys(tuple(plan.tail_policy.occupied_local_beats) + (0.0,)))
    return replace(
        plan,
        events=[*plan.events, fallback],
        tail_policy=TailPolicy.from_local_beats(occupied),
        beat1_movability=Beat1Movability(movable=False, reason="coverage_guard_fallback_anchor_not_movable"),
        selected_candidate=f"{plan.selected_candidate or ''} + piano_region_first_coverage_fallback_anchor".strip(" +"),
        metadata={
            **dict(plan.metadata),
            "piano_region_first_coverage_guard_version": PIANO_COMPING_REGION_FIRST_COVERAGE_GUARD_VERSION,
            "piano_region_first_coverage_guard_checked": True,
            "piano_region_first_coverage_guard_inserted": True,
            "piano_region_first_coverage_guard_outcome": "inserted_region_start_fallback_anchor",
        },
    )

def _motion_from_region_context(region: HarmonicRegion, context: dict[str, Any]) -> FunctionalMotion:
    previous_symbol = context.get("previous_chord_symbol") or region.metadata.get("previous_chord_symbol")
    next_symbol = context.get("next_chord_symbol") or region.next_chord_symbol or region.metadata.get("next_chord_symbol")
    return classify_functional_motion(
        chord_symbol=region.chord_symbol,
        previous_chord_symbol=str(previous_symbol) if previous_symbol else None,
        next_chord_symbol=str(next_symbol) if next_symbol else None,
    )


def _piano_harmonic_context_label(region: HarmonicRegion, motion: FunctionalMotion) -> str:
    if region.is_last_bar_of_chorus:
        return "ending"
    if region.is_last_bar_of_section:
        return "section_end"
    if region.is_first_bar_of_section:
        return "section_start"
    if motion.is_ii_v_i or motion.current_to_next_type in {"v_i_major", "v_i_minor", "dominant_to_tonic"}:
        return "dominant_resolution"
    if motion.previous_to_current_type in {"v_i_major", "v_i_minor", "dominant_to_tonic"}:
        return "tonic_resolution"
    if motion.current_to_next_type in {"ii_v", "minor_ii_v"}:
        return "predominant_to_dominant"
    if motion.is_tonic_prolongation:
        return "tonic_prolongation"
    if motion.is_turnaround_like:
        return "turnaround_like"
    return "generic"

def _candidate_event_roles(candidate: PatternCandidate) -> tuple[str, ...]:
    return tuple(str(getattr(event, "metadata", {}).get("event_role") or "") for event in candidate.events)


def _candidate_has_region_start(candidate: PatternCandidate) -> bool:
    return any(abs(float(getattr(event, "local_beat", 999.0))) < 1e-6 for event in candidate.events)


def _progression_subset_key(label: str, motion: FunctionalMotion) -> str:
    if label == "predominant_to_dominant":
        return "minor_ii_setup_region" if motion.current_to_next_type == "minor_ii_v" else "ii_setup_region"
    if label == "dominant_resolution":
        if motion.window_type == "minor_ii_v_i" or motion.current_to_next_type == "v_i_minor":
            return "minor_251_dominant_region"
        if motion.window_type == "major_ii_v_i" or motion.current_to_next_type in {"v_i_major", "dominant_to_tonic"}:
            return "major_251_dominant_region"
        return "dominant_resolution_region"
    if label == "tonic_resolution":
        return "tonic_resolution_region"
    if label == "ending":
        return "ending_region"
    if label == "section_start":
        return "section_start_region"
    if label == "section_end":
        return "section_end_region"
    if label == "turnaround_like":
        return "turnaround_like_region"
    if label == "tonic_prolongation":
        return "tonic_prolongation_region"
    return "generic_region"


def _progression_subset_preference(candidate: PatternCandidate, *, label: str, motion: FunctionalMotion) -> tuple[bool, tuple[str, ...]]:
    metadata = dict(candidate.metadata)
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "unknown")
    rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
    phrase_role = str(metadata.get("phrase_role") or "")
    region_family = str(metadata.get("region_length_family") or "")
    tail_push_risk = str(metadata.get("tail_push_risk") or "none")
    event_roles = _candidate_event_roles(candidate)
    has_start = _candidate_has_region_start(candidate)
    has_answer = any("answer" in role for role in event_roles) or "answer" in rhythm_family or "charleston" in rhythm_family
    has_tail = any(role in {"tail_support", "backbeat_support", "delayed_support", "support"} for role in event_roles) or any(token in rhythm_family or token in rhythmic_cell for token in ("tail", "backbeat", "delayed"))
    is_push = tail_push_risk == "high" or calibration_class == "tail_push" or "push" in rhythm_family or "push" in rhythmic_cell
    is_short = region_family in {"one_beat_region", "two_beat_region"}
    is_stable = calibration_class == "stable"
    is_offbeat = calibration_class == "offbeat"
    reasons: list[str] = []

    if not candidate.events or calibration_class == "inactive":
        return False, ("inactive_or_rest_candidate_not_progression_subset",)

    if label == "predominant_to_dominant":
        # V1 ii_setup idioms state or lightly answer the predominant while avoiding a strong 4& shove.
        if is_push:
            return False, ("ii_setup_tail_push_not_preferred",)
        if is_short and has_start:
            return True, ("ii_setup_short_region_start_anchor",)
        if has_start and (is_stable or has_answer or has_tail):
            reasons.append("ii_setup_start_statement_or_answer")
        elif has_tail or "delayed" in rhythmic_cell:
            reasons.append("ii_setup_delayed_no_4and_support")
        return bool(reasons), tuple(reasons or ["ii_setup_generic_nonpreferred"])

    if label == "dominant_resolution":
        # V1 major/minor 251 V-region idioms usually give V a clear support/answer, with 4& only rare.
        if is_push:
            return False, ("dominant_resolution_tail_push_rare_not_subset_default",)
        if is_short and (has_start or has_tail):
            return True, ("dominant_resolution_short_region_support",)
        if has_start and (has_answer or has_tail):
            reasons.append("dominant_resolution_statement_answer_or_tail")
        elif has_tail or "delayed" in rhythmic_cell:
            reasons.append("dominant_resolution_delayed_tail_no_4and")
        elif has_start and is_stable:
            reasons.append("dominant_resolution_plain_anchor_fallback")
        return bool(reasons), tuple(reasons or ["dominant_resolution_generic_nonpreferred"])

    if label in {"tonic_resolution", "section_start", "ending"}:
        if is_push:
            return False, (f"{label}_push_not_preferred",)
        if has_start and is_stable:
            return True, (f"{label}_stable_region_start_settle",)
        if label == "ending" and ("final" in phrase_role or "final" in rhythmic_cell):
            return True, ("ending_final_role",)
        return False, (f"{label}_needs_region_start_stable_settle",)

    if label == "section_end":
        if is_push:
            return False, ("section_end_push_not_preferred",)
        if has_tail or (has_start and is_stable):
            return True, ("section_end_tail_or_stable_anchor",)
        return False, ("section_end_nonpreferred",)

    if label == "turnaround_like":
        if is_push:
            return False, ("turnaround_tail_push_control",)
        if has_start and (has_answer or has_tail or is_stable):
            return True, ("turnaround_statement_answer_or_anchor",)
        return False, ("turnaround_nonpreferred",)

    if label == "tonic_prolongation":
        if is_push:
            return False, ("tonic_prolongation_push_control",)
        if is_stable or is_offbeat:
            return True, ("tonic_prolongation_stable_or_light_conversation",)
        return False, ("tonic_prolongation_nonpreferred",)

    return False, ("generic_context_no_progression_subset",)


def _apply_piano_comping_progression_specific_subset_policy(
    candidates: Sequence[PatternCandidate],
    *,
    region: HarmonicRegion,
    context: dict[str, Any],
) -> tuple[PatternCandidate, ...]:
    """Prioritize V1-derived progression-specific idioms in V2's region-first pool.

    This is a preferred-subset reweight inside the existing ChordRegion-length
    candidate pool.  It translates V1 major_251/minor_251/two_five/ii_setup
    priority into V2 context labels without creating a bar-first template route,
    without selecting voicings, and without bypassing the normal harmonic
    multiplier, history scorer, or weighted sampler.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    motion = _motion_from_region_context(region, context)
    label = _piano_harmonic_context_label(region, motion)
    subset_key = _progression_subset_key(label, motion)
    if label == "generic":
        return tuple(
            replace(
                candidate,
                metadata={
                    **dict(candidate.metadata),
                    "progression_specific_subset_policy_version": PIANO_COMPING_PROGRESSION_SPECIFIC_SUBSET_POLICY_VERSION,
                    "progression_specific_subset_policy_applied": False,
                    "progression_specific_context_label": label,
                    "progression_specific_subset_key": subset_key,
                    "progression_specific_subset_status": "generic_context_no_subset",
                    "progression_specific_subset_contract": "Generic contexts keep the existing ChordRegion-length candidate pool; no bar-first/two-chord-bar route is introduced.",
                },
            )
            for candidate in candidates
        )

    preference_rows = [
        (candidate, *_progression_subset_preference(candidate, label=label, motion=motion))
        for candidate in candidates
    ]
    preferred_count = sum(1 for _, preferred, _ in preference_rows if preferred)
    if preferred_count == 0 or preferred_count == len(preference_rows):
        status = "no_distinct_preferred_subset_available" if preferred_count == 0 else "all_candidates_match_subset"
        return tuple(
            replace(
                candidate,
                metadata={
                    **dict(candidate.metadata),
                    "progression_specific_subset_policy_version": PIANO_COMPING_PROGRESSION_SPECIFIC_SUBSET_POLICY_VERSION,
                    "progression_specific_subset_policy_applied": False,
                    "progression_specific_context_label": label,
                    "progression_specific_subset_key": subset_key,
                    "progression_specific_subset_status": status,
                    "progression_specific_subset_preferred_candidate_count": preferred_count,
                    "progression_specific_subset_total_candidate_count": len(preference_rows),
                    "progression_specific_subset_reasons": tuple(reasons),
                    "progression_specific_subset_contract": "Progression-specific subset policy is backup-safe: when no distinct preferred subset exists, it leaves weights unchanged and only stamps audit metadata.",
                },
            )
            for candidate, _, reasons in preference_rows
        )

    adjusted: list[PatternCandidate] = []
    for candidate, preferred, reasons in preference_rows:
        metadata = dict(candidate.metadata)
        calibration_class = str(metadata.get("weight_calibration_class") or "stable")
        tail_push_risk = str(metadata.get("tail_push_risk") or "none")
        multiplier = 1.35 if preferred else 0.58
        status = "preferred_subset_candidate" if preferred else "fallback_candidate_downweighted"
        if preferred and metadata.get("region_length_family") in {"one_beat_region", "two_beat_region"}:
            multiplier = 1.20
            status = "preferred_short_region_subset_candidate"
        if not preferred and (tail_push_risk == "high" or calibration_class == "tail_push"):
            multiplier *= 0.55
        metadata.update(
            {
                "progression_specific_subset_policy_version": PIANO_COMPING_PROGRESSION_SPECIFIC_SUBSET_POLICY_VERSION,
                "progression_specific_subset_policy_applied": True,
                "progression_specific_context_label": label,
                "progression_specific_subset_key": subset_key,
                "progression_specific_subset_status": status,
                "progression_specific_subset_multiplier": round(multiplier, 4),
                "progression_specific_subset_reasons": tuple(reasons),
                "progression_specific_subset_preferred_candidate_count": preferred_count,
                "progression_specific_subset_total_candidate_count": len(preference_rows),
                "progression_specific_previous_to_current_type": motion.previous_to_current_type,
                "progression_specific_current_to_next_type": motion.current_to_next_type,
                "progression_specific_window_type": motion.window_type,
                "progression_specific_tags": tuple(motion.tags),
                "progression_specific_subset_contract": "V1 progression-specific vocabulary is translated as a preferred subset inside the existing ChordRegion-first region-length candidate pool; this is not a bar-first template path and does not choose voicing or final expression values.",
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)




def _candidate_is_no_4and_delayed_tail(candidate: PatternCandidate) -> bool:
    metadata = dict(candidate.metadata)
    tail_push_risk = str(metadata.get("tail_push_risk") or "none")
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "")
    rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
    if tail_push_risk == "high" or calibration_class == "tail_push" or "4and" in rhythmic_cell or "push" in rhythm_family:
        return False
    return any(token in rhythm_family or token in rhythmic_cell for token in ("delayed", "tail", "backbeat"))


def _apply_piano_comping_no_4and_delayed_tail_policy(
    candidates: Sequence[PatternCandidate],
) -> tuple[PatternCandidate, ...]:
    """Reinforce V1's no-4& / delayed-tail idiom inside V2's region-first pool.

    This policy is a lightweight reweight pass.  It does not add a bar-first
    template route and does not delete 4& material; it keeps native tail-push
    cells as rare lift while giving region-local delayed/tail/backbeat cells a
    small idiomatic preference.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        metadata = dict(candidate.metadata)
        calibration_class = str(metadata.get("weight_calibration_class") or "stable")
        tail_push_risk = str(metadata.get("tail_push_risk") or "none")
        region_family = str(metadata.get("region_length_family") or "")
        rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
        rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "")
        is_tail_push = tail_push_risk == "high" or calibration_class == "tail_push" or "4and" in rhythmic_cell or "push" in rhythm_family
        is_no_4and = _candidate_is_no_4and_delayed_tail(candidate)
        multiplier = 1.0
        reasons: list[str] = []
        status = "neutral"
        if is_no_4and:
            # V1 gently rewards delayed/tail shapes because they create motion
            # without overusing the 4& -> next downbeat pickup habit.  Keep the
            # boost modest, especially for short ChordRegions.
            multiplier *= 1.10
            status = "no_4and_delayed_tail_preferred"
            reasons.append("no_4and_delayed_tail_small_bonus")
            if region_family in {"one_beat_region", "two_beat_region"}:
                multiplier = min(multiplier, 1.05)
                reasons.append("short_region_no_4and_bonus_ceiling")
        if is_tail_push:
            multiplier *= 0.45
            status = "tail_push_rare_lift_downweighted"
            reasons.append("native_4and_tail_push_kept_rare")
        metadata.update(
            {
                "no_4and_delayed_tail_policy_version": PIANO_COMPING_NO_4AND_DELAYED_TAIL_POLICY_VERSION,
                "no_4and_delayed_tail_policy_applied": True,
                "no_4and_delayed_tail_idiom": bool(is_no_4and),
                "no_4and_tail_push_candidate": bool(is_tail_push),
                "no_4and_delayed_tail_multiplier": round(multiplier, 4),
                "no_4and_delayed_tail_status": status,
                "no_4and_delayed_tail_reasons": tuple(reasons),
                "no_4and_delayed_tail_contract": "V1 no-4& / delayed-tail idiom is translated as region-local candidate reweighting; 4& is retained as rare lift, not deleted, and routing remains ChordRegion-first.",
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


def _apply_piano_comping_harmonic_function_policy(
    candidates: Sequence[PatternCandidate],
    *,
    region: HarmonicRegion,
    context: dict[str, Any],
) -> tuple[PatternCandidate, ...]:
    """Reweight Medium Swing piano comping candidates by harmonic context.

    This policy is deliberately a multiplier on the existing ChordRegion-length
    candidate pool.  It does not introduce a bar-first pattern path, choose
    voicings, or bypass the normal history scorer / weighted sampler.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    motion = _motion_from_region_context(region, context)
    label = _piano_harmonic_context_label(region, motion)
    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        metadata = dict(candidate.metadata)
        calibration_class = str(metadata.get("weight_calibration_class") or "stable")
        rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "unknown")
        phrase_role = str(metadata.get("phrase_role") or "")
        event_roles = tuple(str(getattr(event, "metadata", {}).get("event_role") or "") for event in candidate.events)
        tail_push_risk = str(metadata.get("tail_push_risk") or "none")
        has_start = any(abs(float(getattr(event, "local_beat", 999.0))) < 1e-6 for event in candidate.events)
        has_tail_support = any(role in {"tail_support", "backbeat_support", "delayed_support"} for role in event_roles)
        has_answer = any("answer" in role for role in event_roles)
        has_push = tail_push_risk == "high" or calibration_class == "tail_push" or "push" in rhythm_family
        multiplier = 1.0
        reasons: list[str] = []

        if label in {"section_start", "tonic_resolution", "ending"}:
            if has_start and calibration_class == "stable":
                multiplier *= 1.18
                reasons.append(f"{label}_stable_anchor_bonus")
            if calibration_class in {"active", "tail_push"} or has_push:
                multiplier *= 0.55 if label != "ending" else 0.35
                reasons.append(f"{label}_active_push_control")
            if label == "ending" and "final" in phrase_role:
                multiplier *= 1.12
                reasons.append("ending_final_role_bonus")
        elif label == "dominant_resolution":
            if has_answer or has_tail_support:
                multiplier *= 1.12
                reasons.append("dominant_resolution_answer_tail_bonus")
            if has_start and calibration_class == "stable":
                multiplier *= 1.05
                reasons.append("dominant_resolution_anchor_support_bonus")
            if has_push:
                multiplier *= 0.72
                reasons.append("dominant_resolution_tail_push_control")
        elif label == "predominant_to_dominant":
            if has_start and calibration_class == "stable":
                multiplier *= 1.10
                reasons.append("predominant_to_dominant_stable_support_bonus")
            if calibration_class == "offbeat" and has_answer:
                multiplier *= 1.04
                reasons.append("predominant_to_dominant_light_answer_bonus")
            if has_push:
                multiplier *= 0.65
                reasons.append("predominant_to_dominant_push_control")
        elif label == "section_end":
            if has_tail_support or has_start:
                multiplier *= 1.10
                reasons.append("section_end_tail_or_anchor_bonus")
            if calibration_class == "active" or has_push:
                multiplier *= 0.60
                reasons.append("section_end_active_push_control")
        elif label == "tonic_prolongation":
            if calibration_class == "offbeat":
                multiplier *= 1.06
                reasons.append("tonic_prolongation_light_conversation_bonus")
            if calibration_class == "active" or has_push:
                multiplier *= 0.72
                reasons.append("tonic_prolongation_active_push_control")
        elif label == "turnaround_like":
            if has_start and has_answer:
                multiplier *= 1.08
                reasons.append("turnaround_statement_answer_bonus")
            if has_push:
                multiplier *= 0.70
                reasons.append("turnaround_push_control")

        # Short harmonic regions should remain anchor-led even when the local
        # harmonic label invites conversation.  Keep offbeat boosts modest.
        region_family = str(metadata.get("region_length_family") or "")
        if region_family in {"one_beat_region", "two_beat_region"} and calibration_class == "offbeat" and multiplier > 1.08:
            multiplier = 1.08
            reasons.append("short_region_offbeat_boost_ceiling")

        metadata.update(
            {
                "harmonic_function_comping_policy_version": PIANO_COMPING_HARMONIC_FUNCTION_POLICY_VERSION,
                "harmonic_function_comping_policy_applied": True,
                "harmonic_function_context_label": label,
                "harmonic_function_multiplier": round(multiplier, 4),
                "harmonic_function_reasons": tuple(reasons),
                "harmonic_function_previous_to_current_type": motion.previous_to_current_type,
                "harmonic_function_current_to_next_type": motion.current_to_next_type,
                "harmonic_function_window_type": motion.window_type,
                "harmonic_function_tags": tuple(motion.tags),
                "harmonic_function_comping_contract": "Existing ChordRegion-length candidate pool is reweighted by functional motion; no bar-first/two-chord-bar or parallel selector path is introduced.",
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)

def _history_recent_entries(history: dict, source_key: str) -> list[dict[str, Any]]:
    recent = history.get(f"{source_key}:recent_comping")
    if not isinstance(recent, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in recent[-4:]:
        if isinstance(item, dict):
            normalized.append(dict(item))
    return normalized


def _candidate_continuity_metadata(candidate: PatternCandidate) -> dict[str, str]:
    metadata = dict(candidate.metadata)
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "unknown")
    tail_push_risk = str(metadata.get("tail_push_risk") or "none")
    density = str(metadata.get("density") or "medium")
    if tail_push_risk == "high" or calibration_class == "tail_push" or "push" in rhythm_family:
        continuity_class = "tail_push"
    elif calibration_class == "active" or density == "active":
        continuity_class = "active"
    elif calibration_class == "offbeat" or "offbeat" in rhythm_family or "answer" in rhythm_family:
        continuity_class = "offbeat"
    else:
        continuity_class = "stable"
    return {
        "name": candidate.name,
        "category": candidate.category,
        "rhythm_family": rhythm_family,
        "weight_calibration_class": calibration_class,
        "continuity_class": continuity_class,
        "tail_push_risk": tail_push_risk,
        "density": density,
    }


def _apply_piano_comping_history_continuity_scorer(
    candidates: Sequence[PatternCandidate],
    *,
    history: dict,
    source_key: str,
) -> tuple[PatternCandidate, ...]:
    """Apply a lightweight Medium Swing comping history scorer.

    This is not a parallel pattern selector. It reuses the already routed
    ChordRegion-length candidate pool and only adjusts candidate weights before
    normal weighted sampling. Pattern files remain style-owned and pitchless.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    recent = _history_recent_entries(history, source_key)
    previous = recent[-1] if recent else {}
    recent_classes = [str(item.get("continuity_class") or "") for item in recent]
    recent_tail_push_count = sum(1 for value in recent_classes if value == "tail_push")
    recent_active_count = sum(1 for value in recent_classes if value == "active")
    recent_offbeat_count = sum(1 for value in recent_classes if value == "offbeat")
    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        info = _candidate_continuity_metadata(candidate)
        continuity_class = info["continuity_class"]
        multiplier = 1.0
        reasons: list[str] = []
        if previous.get("name") == candidate.name:
            multiplier *= 0.12
            reasons.append("exact_repeat_penalty")
        if previous.get("rhythm_family") == info["rhythm_family"]:
            if continuity_class == "stable":
                multiplier *= 0.72
                reasons.append("stable_family_repeat_soft_penalty")
            else:
                multiplier *= 0.42
                reasons.append("nonstable_family_repeat_penalty")
        if previous.get("continuity_class") == "offbeat" and continuity_class == "offbeat":
            multiplier *= 0.30
            reasons.append("consecutive_offbeat_penalty")
        if recent_offbeat_count >= 2 and continuity_class == "offbeat":
            multiplier *= 0.35
            reasons.append("recent_offbeat_cluster_penalty")
        if recent_active_count >= 1 and continuity_class == "active":
            multiplier *= 0.18
            reasons.append("recent_active_penalty")
        if recent_tail_push_count >= 1 and continuity_class == "tail_push":
            multiplier *= 0.05
            reasons.append("recent_tail_push_penalty")
        if previous.get("continuity_class") in {"active", "tail_push"} and continuity_class == "stable":
            multiplier *= 1.18
            reasons.append("stable_reset_after_active_bonus")
        if previous.get("continuity_class") == "offbeat" and continuity_class == "stable":
            multiplier *= 1.08
            reasons.append("stable_reset_after_offbeat_bonus")
        metadata = {
            **dict(candidate.metadata),
            "history_continuity_scorer_version": PIANO_COMPING_HISTORY_CONTINUITY_SCORER_VERSION,
            "history_continuity_scorer_applied": True,
            "history_continuity_multiplier": round(multiplier, 4),
            "history_continuity_reasons": tuple(reasons),
            "history_continuity_class": continuity_class,
            "history_continuity_previous_class": previous.get("continuity_class"),
            "history_continuity_previous_candidate": previous.get("name"),
            "history_continuity_recent_window_size": len(recent),
            "history_continuity_contract": "Existing region-length candidate pool is reweighted by recent piano comping history; no parallel pattern path is introduced.",
        }
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


def _record_piano_comping_history(history: dict, source_key: str, candidate: PatternCandidate) -> None:
    info = _candidate_continuity_metadata(candidate)
    recent = _history_recent_entries(history, source_key)
    recent.append(info)
    history[f"{source_key}:recent_comping"] = recent[-4:]
    history[f"{source_key}:rhythm_family"] = info["rhythm_family"]
    history[f"{source_key}:weight_calibration_class"] = info["weight_calibration_class"]
    history[f"{source_key}:continuity_class"] = info["continuity_class"]
    history[f"{source_key}:tail_push_risk"] = info["tail_push_risk"]


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

        v2_6_56 treats style-owned pattern libraries as ChordRegion-first:
        candidates are selected from region-local vocabulary keyed by harmonic
        region length, rather than bar-level/two-chord-bar assumptions.  The
        default planner still applies lightweight history guards controlled by
        arrangement policy to avoid immediately repeating the same pattern.
        """

        rng = context.get("rng") if isinstance(context.get("rng"), random.Random) else None
        region_context = {
            **dict(context),
            "region": region,
            "region_duration_beats": region.duration_beats,
            "chord_symbol": region.chord_symbol,
            "previous_chord_symbol": region.metadata.get("previous_chord_symbol"),
            "next_chord_symbol": region.next_chord_symbol,
        }
        history = region_context.get("style_pattern_history")
        if not isinstance(history, dict):
            history = {}
        avoid_repeat = bool(self.arrangement_policy.get("avoid_immediate_pattern_repeat", False))
        avoid_category_repeat = bool(self.arrangement_policy.get("avoid_immediate_pattern_category_repeat", False))
        piano_density_guard = bool(self.arrangement_policy.get("piano_comping_density_guard", False))
        piano_history_scorer = bool(self.arrangement_policy.get("piano_comping_history_continuity_scorer", False))
        piano_harmonic_function_policy = bool(self.arrangement_policy.get("piano_comping_harmonic_function_policy", False))
        piano_progression_subset_policy = bool(self.arrangement_policy.get("piano_comping_progression_specific_subset_policy", False))
        piano_no_4and_delayed_tail_policy = bool(self.arrangement_policy.get("piano_comping_no_4and_delayed_tail_idiom_policy", False))
        piano_region_first_coverage_guard = bool(self.arrangement_policy.get("piano_region_first_coverage_guard", False))

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
            is_piano_comping_source = ".comping_patterns" in source_key
            if piano_density_guard and is_piano_comping_source and len(choice_pool) > 1:
                previous_density = history.get(f"{source_key}:density")
                if previous_density == "dense":
                    filtered = tuple(candidate for candidate in choice_pool if candidate.metadata.get("density") != "dense")
                    if filtered:
                        choice_pool = filtered
            if piano_progression_subset_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_progression_specific_subset_policy(choice_pool, region=region, context=region_context)
            if piano_no_4and_delayed_tail_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_no_4and_delayed_tail_policy(choice_pool)
            if piano_harmonic_function_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_harmonic_function_policy(choice_pool, region=region, context=region_context)
            if piano_history_scorer and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_history_continuity_scorer(choice_pool, history=history, source_key=source_key)
            candidate = choose_weighted_candidate(choice_pool, rng)
            history[source_key] = candidate.name
            history[f"{source_key}:category"] = candidate.category
            if is_piano_comping_source:
                history[f"{source_key}:density"] = str(candidate.metadata.get("density", "medium"))
                if piano_history_scorer:
                    _record_piano_comping_history(history, source_key, candidate)
            selected.append(candidate.name)
            plan = candidate.instantiate(region)
            if is_piano_comping_source and (piano_history_scorer or piano_harmonic_function_policy or piano_progression_subset_policy or piano_no_4and_delayed_tail_policy or piano_region_first_coverage_guard):
                plan = replace(
                    plan,
                    events=[
                        replace(
                            event,
                            metadata={
                                **dict(candidate.metadata),
                                **dict(event.metadata),
                            },
                        )
                        for event in plan.events
                    ],
                    metadata={**dict(plan.metadata), **dict(candidate.metadata)},
                )
            plans.append(plan)
        combined_plan = PatternPlan.combine(
            plans,
            selected_candidate=" + ".join(selected),
            metadata={"style": self.name, "selected_candidates": selected},
        )
        return _apply_piano_region_first_coverage_guard(
            combined_plan,
            region=region,
            style_name=self.name,
            enabled=piano_region_first_coverage_guard,
        )
