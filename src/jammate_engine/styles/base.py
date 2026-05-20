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
PIANO_COMPING_ACTIVE_FILL_BUSY_MULTI_REGION_HISTORY_SCORER_VERSION = "v2_6_67"
PIANO_COMPING_HARMONIC_FUNCTION_POLICY_VERSION = "v2_6_60"
PIANO_COMPING_PROGRESSION_SPECIFIC_SUBSET_POLICY_VERSION = "v2_6_65"
PIANO_COMPING_NO_4AND_DELAYED_TAIL_POLICY_VERSION = "v2_6_66"
PIANO_COMPING_ENDING_SPECIFIC_SUBSET_POLICY_VERSION = "v2_6_70"
PIANO_COMPING_OPTIONAL_FILL_VARIATION_VOCABULARY_POLICY_VERSION = "v2_6_71"
PIANO_COMPING_OPTIONAL_FILL_VARIATION_LISTENING_REFINEMENT_POLICY_VERSION = "v2_6_72"
PIANO_COMPING_PHRASE_END_FILL_CONTEXT_PRECISION_POLICY_VERSION = "v2_6_73"
PIANO_COMPING_STANDARD_TUNE_FILL_FREQUENCY_CHECKPOINT_VERSION = "v2_6_74"
PIANO_COMPING_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_76"
PIANO_COMPING_TWO_BEAT_REGION_DENSITY_RELIEF_POLICY_VERSION = "v2_6_80"
MEDIUM_SWING_ARRANGEMENT_ARC_RUNTIME_INTENT_USAGE_VERSION = "v2_6_85"
MEDIUM_SWING_ARRANGEMENT_ARC_RUNTIME_LISTENING_REFINEMENT_VERSION = "v2_6_86"
MEDIUM_SWING_FULL_BAND_ENDING_REALIZATION_CHECKPOINT_VERSION = "v2_6_87"
MEDIUM_SWING_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_88"
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




def _ending_subset_candidate_profile(candidate: PatternCandidate) -> dict[str, Any]:
    metadata = dict(candidate.metadata)
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "unknown")
    rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
    phrase_role = str(metadata.get("phrase_role") or "")
    tail_push_risk = str(metadata.get("tail_push_risk") or "none")
    event_roles = _candidate_event_roles(candidate)
    has_start = _candidate_has_region_start(candidate)
    has_tail_support = any(role in {"tail_support", "backbeat_support", "delayed_support", "support"} for role in event_roles) or any(
        token in rhythm_family or token in rhythmic_cell for token in ("tail", "backbeat", "delayed")
    )
    is_push = tail_push_risk == "high" or calibration_class == "tail_push" or "push" in rhythm_family or "4and" in rhythmic_cell
    is_active = calibration_class == "active" or str(metadata.get("density") or "") == "active" or "active" in phrase_role
    is_offbeat_without_start = (calibration_class == "offbeat" or "offbeat" in rhythm_family or "answer" in rhythm_family) and not has_start
    is_final_role = "final" in phrase_role or "final" in rhythm_family or "final" in rhythmic_cell
    is_settle_anchor = has_start and calibration_class == "stable"
    return {
        "has_start": bool(has_start),
        "has_tail_support": bool(has_tail_support),
        "is_push": bool(is_push),
        "is_active": bool(is_active),
        "is_offbeat_without_start": bool(is_offbeat_without_start),
        "is_final_role": bool(is_final_role),
        "is_settle_anchor": bool(is_settle_anchor),
        "calibration_class": calibration_class,
        "rhythm_family": rhythm_family,
        "rhythmic_cell": rhythmic_cell,
        "phrase_role": phrase_role,
    }


def _apply_piano_comping_ending_specific_subset_policy(
    candidates: Sequence[PatternCandidate],
    *,
    region: HarmonicRegion,
    context: dict[str, Any],
) -> tuple[PatternCandidate, ...]:
    """Reweight ending-region candidates inside the existing region pool.

    v2_6_70 handles final-bar Medium Swing piano comping as a ChordRegion-first
    preferred-subset policy.  It does not add an ending selector, does not add
    rhythm vocabulary, and does not choose voicings or final expression values.
    Ending regions prefer clear region-start settling support, allow modest
    tail/backbeat support, and strongly control active/4& push material.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    motion = _motion_from_region_context(region, context)
    label = _piano_harmonic_context_label(region, motion)
    subset_key = "ending_specific_region" if label == "ending" else "non_ending_context"
    if label != "ending":
        return tuple(
            replace(
                candidate,
                metadata={
                    **dict(candidate.metadata),
                    "ending_specific_subset_policy_version": PIANO_COMPING_ENDING_SPECIFIC_SUBSET_POLICY_VERSION,
                    "ending_specific_subset_policy_applied": False,
                    "ending_specific_context_label": label,
                    "ending_specific_subset_key": subset_key,
                    "ending_specific_subset_status": "non_ending_context_passthrough",
                    "ending_specific_subset_contract": "Ending-specific subset policy only reweights ChordRegion candidates when the current region is the final bar of a chorus; non-ending regions keep the existing pool unchanged.",
                },
            )
            for candidate in candidates
        )

    adjusted: list[PatternCandidate] = []
    preferred_count = 0
    profiles = [(candidate, _ending_subset_candidate_profile(candidate)) for candidate in candidates]
    for _, profile in profiles:
        if profile["is_final_role"] or profile["is_settle_anchor"] or (profile["has_tail_support"] and not profile["is_push"]):
            preferred_count += 1

    for candidate, profile in profiles:
        multiplier = 1.0
        reasons: list[str] = []
        status = "ending_neutral_candidate"
        if profile["is_final_role"]:
            multiplier *= 1.55
            status = "ending_final_role_preferred"
            reasons.append("ending_final_role_preferred")
        if profile["is_settle_anchor"]:
            multiplier *= 1.36
            status = "ending_settle_anchor_preferred"
            reasons.append("ending_stable_region_start_settle")
        if profile["has_tail_support"] and not profile["is_push"]:
            multiplier *= 1.12
            if status == "ending_neutral_candidate":
                status = "ending_tail_support_allowed"
            reasons.append("ending_tail_or_backbeat_support_allowed")
        if profile["is_active"]:
            multiplier *= 0.42
            status = "ending_active_downweighted"
            reasons.append("ending_active_control")
        if profile["is_offbeat_without_start"]:
            multiplier *= 0.48
            if status == "ending_neutral_candidate":
                status = "ending_offbeat_without_anchor_downweighted"
            reasons.append("ending_offbeat_without_region_start_control")
        if profile["is_push"]:
            multiplier *= 0.16
            status = "ending_tail_push_near_block"
            reasons.append("ending_4and_tail_push_near_block")
        if not reasons:
            multiplier *= 0.72
            status = "ending_generic_fallback_downweighted"
            reasons.append("ending_generic_nonpreferred_downweight")

        metadata = dict(candidate.metadata)
        metadata.update(
            {
                "ending_specific_subset_policy_version": PIANO_COMPING_ENDING_SPECIFIC_SUBSET_POLICY_VERSION,
                "ending_specific_subset_policy_applied": True,
                "ending_specific_context_label": label,
                "ending_specific_subset_key": subset_key,
                "ending_specific_subset_status": status,
                "ending_specific_subset_multiplier": round(multiplier, 4),
                "ending_specific_subset_reasons": tuple(reasons),
                "ending_specific_preferred_candidate_count": preferred_count,
                "ending_specific_total_candidate_count": len(profiles),
                "ending_specific_has_region_start": bool(profile["has_start"]),
                "ending_specific_has_tail_support": bool(profile["has_tail_support"]),
                "ending_specific_is_push": bool(profile["is_push"]),
                "ending_specific_is_active": bool(profile["is_active"]),
                "ending_specific_previous_to_current_type": motion.previous_to_current_type,
                "ending_specific_current_to_next_type": motion.current_to_next_type,
                "ending_specific_window_type": motion.window_type,
                "ending_specific_tags": tuple(motion.tags),
                "ending_specific_subset_contract": "Ending regions are reweighted inside the existing ChordRegion-length candidate pool toward stable region-start settling and away from active/4& push; no parallel ending selector, no new vocabulary, no voicing, and no final expression values are introduced.",
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
    # v2_6_67 upgrades the old four-entry guard into a multi-region memory
    # window.  Six regions is enough to catch short active/fill/busy clusters
    # without turning the scorer into a phrase-level selector.
    for item in recent[-6:]:
        if isinstance(item, dict):
            normalized.append(dict(item))
    return normalized


def _candidate_local_beats(candidate: PatternCandidate) -> tuple[float, ...]:
    return tuple(round(float(getattr(event, "local_beat", 0.0)), 6) for event in candidate.events)


def _apply_piano_comping_two_beat_region_density_relief_policy(
    candidates: Sequence[PatternCandidate],
    *,
    region: HarmonicRegion,
    context: dict[str, Any],
    history: dict,
    source_key: str,
) -> tuple[PatternCandidate, ...]:
    """Relax Medium Swing piano comping in dense 2-beat harmonic rhythm.

    v2_6_80 responds to standard tunes such as Autumn Leaves where long runs of
    2-beat ChordRegions can make the piano sound busy in a full band.  The
    policy stays in the existing style-owned candidate weighting path: it does
    not create a bar-first two-chord-bar selector, does not add rhythm
    vocabulary, and does not touch voicing/expression/API behavior.

    It also deliberately favors simple region-start anchors, which leave the
    previous region tail slot free for the already-generic AnticipationResolver
    to move a next-region beat-1 event to the prior local 2& when probability
    permits.
    """

    if len(candidates) <= 1 or _region_length_family_for_coverage(float(region.duration_beats)) != "two_beat_region":
        return tuple(candidates)

    recent = _history_recent_entries(history, source_key)
    previous = recent[-1] if recent else {}
    previous_two_beat = str(previous.get("region_length_family") or "") == "two_beat_region"
    previous_event_count = int(previous.get("event_count") or 0) if previous else 0
    previous_dense_short = previous_two_beat and previous_event_count > 1
    label = _piano_harmonic_context_label(region, _motion_from_region_context(region, context))
    is_first_half = bool(region.is_first_region_of_bar) and not bool(region.is_last_region_of_bar)
    is_second_half = bool(region.is_last_region_of_bar) and not bool(region.is_first_region_of_bar)

    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        metadata = dict(candidate.metadata)
        beats = _candidate_local_beats(candidate)
        has_start = 0.0 in beats
        event_count = len(beats)
        is_start_only = has_start and event_count == 1
        has_tail_upbeat = 1.5 in beats
        has_midbeat = 1.0 in beats
        has_early_upbeat = 0.5 in beats
        calibration_class = str(metadata.get("weight_calibration_class") or "stable")

        multiplier = 1.0
        reasons: list[str] = []
        relief_status = "neutral"

        if is_start_only:
            multiplier *= 4.00
            relief_status = "simple_anchor_preferred"
            reasons.append("two_beat_dense_harmony_simple_anchor_bonus")
            if is_second_half:
                multiplier *= 1.15
                reasons.append("second_half_region_prefers_light_anchor")
        elif event_count > 1:
            multiplier *= 0.14
            relief_status = "multi_touch_short_region_downweighted"
            reasons.append("two_beat_dense_harmony_multi_touch_downweight")
            if has_tail_upbeat:
                multiplier *= 0.55
                reasons.append("tail_slot_preserved_for_generic_anticipation")
            if has_early_upbeat:
                multiplier *= 0.55
                reasons.append("early_upbeat_in_short_region_extra_downweight")
            if is_second_half:
                multiplier *= 0.55
                reasons.append("avoid_both_halves_strong_comping")
        elif not has_start:
            multiplier *= 0.20
            relief_status = "delayed_only_short_region_downweighted"
            reasons.append("two_beat_dense_harmony_delayed_only_downweight")
            if has_midbeat or has_tail_upbeat or has_early_upbeat:
                reasons.append("offbeat_only_presence_kept_rare_in_full_band")

        if previous_dense_short and event_count > 1:
            multiplier *= 0.25
            reasons.append("previous_two_beat_multi_touch_history_relief")
        if previous_two_beat and not is_start_only and calibration_class == "offbeat":
            multiplier *= 0.35
            reasons.append("consecutive_two_beat_offbeat_relief")
        if label in {"section_end", "ending"} and is_start_only:
            multiplier *= 1.08
            reasons.append(f"{label}_short_region_settle_anchor_bonus")

        metadata.update(
            {
                "two_beat_region_density_relief_policy_version": PIANO_COMPING_TWO_BEAT_REGION_DENSITY_RELIEF_POLICY_VERSION,
                "two_beat_region_density_relief_policy_applied": True,
                "two_beat_region_density_relief_multiplier": round(multiplier, 4),
                "two_beat_region_density_relief_status": relief_status,
                "two_beat_region_density_relief_reasons": tuple(reasons),
                "two_beat_region_density_relief_event_count": event_count,
                "two_beat_region_density_relief_local_beats": beats,
                "two_beat_region_density_relief_has_start": bool(has_start),
                "two_beat_region_density_relief_has_tail_upbeat": bool(has_tail_upbeat),
                "two_beat_region_density_relief_is_first_half_of_bar": is_first_half,
                "two_beat_region_density_relief_is_second_half_of_bar": is_second_half,
                "two_beat_region_density_relief_previous_two_beat": previous_two_beat,
                "two_beat_region_density_relief_previous_dense_short": previous_dense_short,
                "two_beat_region_density_relief_context_label": label,
                "two_beat_region_density_relief_preserves_tail_space_for_generic_anticipation": bool(is_start_only),
                "two_beat_region_density_relief_contract": "Dense 2-beat ChordRegions are relaxed inside the existing ChordRegion-local candidate pool: simple anchors are favored, multi-touch/offbeat short-region cells are reduced, and tail space is preserved for the generic AnticipationResolver. No bar-first/two-chord-bar selector, new vocabulary, voicing, expression values, API, Agent, or HarmonyOS behavior is introduced.",
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


def _candidate_continuity_metadata(candidate: PatternCandidate) -> dict[str, Any]:
    metadata = dict(candidate.metadata)
    calibration_class = str(metadata.get("weight_calibration_class") or "stable")
    rhythm_family = str(metadata.get("rhythm_family") or candidate.category or "unknown")
    rhythmic_cell = str(metadata.get("rhythmic_cell") or "")
    pattern_function = str(metadata.get("pattern_function") or "")
    phrase_role = str(metadata.get("phrase_role") or "")
    region_family = str(metadata.get("region_length_family") or "")
    tail_push_risk = str(metadata.get("tail_push_risk") or "none")
    density = str(metadata.get("density") or "medium")
    event_roles = _candidate_event_roles(candidate)
    event_count = len(candidate.events)
    text_blob = " ".join(
        str(item).lower()
        for item in (
            candidate.name,
            candidate.category,
            calibration_class,
            rhythm_family,
            rhythmic_cell,
            pattern_function,
            phrase_role,
            density,
            " ".join(event_roles),
        )
    )
    is_tail_push = (
        tail_push_risk == "high"
        or calibration_class == "tail_push"
        or "tail_push" in text_blob
        or "4and" in rhythmic_cell.lower()
    )
    is_push = is_tail_push or "push" in text_blob
    is_busy = (
        calibration_class == "busy"
        or density == "busy"
        or "busy" in text_blob
        or event_count >= 4
    )
    is_fill = (
        "fill" in text_blob
        or "transition" in text_blob
        or phrase_role in {"phrase_fill", "section_fill", "turnaround_fill", "ending_fill"}
    )
    is_active = calibration_class == "active" or density == "active" or "active" in phrase_role or is_busy
    is_offbeat = calibration_class == "offbeat" or "offbeat" in rhythm_family or "answer" in rhythm_family
    is_no_4and_delayed_tail = bool(metadata.get("no_4and_delayed_tail_idiom", False))

    if is_tail_push:
        continuity_class = "tail_push"
    elif is_busy:
        continuity_class = "busy"
    elif is_fill:
        continuity_class = "fill"
    elif is_active:
        continuity_class = "active"
    elif is_offbeat:
        continuity_class = "offbeat"
    else:
        continuity_class = "stable"

    return {
        "name": candidate.name,
        "category": candidate.category,
        "rhythm_family": rhythm_family,
        "rhythmic_cell": rhythmic_cell,
        "pattern_function": pattern_function,
        "phrase_role": phrase_role,
        "weight_calibration_class": calibration_class,
        "continuity_class": continuity_class,
        "activity_class": continuity_class,
        "tail_push_risk": tail_push_risk,
        "density": density,
        "region_length_family": region_family,
        "event_count": event_count,
        "has_region_start": _candidate_has_region_start(candidate),
        "is_active": bool(is_active or continuity_class == "active"),
        "is_fill": bool(is_fill or continuity_class == "fill"),
        "is_busy": bool(is_busy or continuity_class == "busy"),
        "is_push": bool(is_push),
        "is_tail_push": bool(is_tail_push),
        "is_offbeat": bool(is_offbeat),
        "is_no_4and_delayed_tail": bool(is_no_4and_delayed_tail),
    }


def _recent_flag_count(recent: Sequence[dict[str, Any]], key: str) -> int:
    return sum(1 for item in recent if bool(item.get(key)))


def _is_fill_context(label: str) -> bool:
    return label in {"section_end", "ending", "turnaround_like", "dominant_resolution"}


def _is_busy_context(label: str, context: dict[str, Any] | None) -> bool:
    energy = str((context or {}).get("energy") or (context or {}).get("comping_energy") or "").lower()
    density = str((context or {}).get("piano_density") or "").lower()
    return label in {"section_end", "ending", "turnaround_like"} or energy in {"high", "active", "busy"} or density in {"high", "busy"}


def _as_policy_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "end", "ending", "phrase_end", "section_end"}


def _phrase_end_fill_precision_context(region: HarmonicRegion, label: str, context: dict[str, Any] | None) -> dict[str, Any]:
    """Return a ChordRegion-first phrase-end gate for optional transition fills.

    v2_6_73 intentionally stays inside the existing candidate weighting path.
    It treats explicit bar/section metadata as highest trust, then uses a small
    jazz-standard fallback: the last region of every 4-bar mini-phrase can act
    as a light phrase end.  This does not create a phrase engine or bar-first
    template; it only narrows where the existing optional transition-fill cell
    may receive a bonus.
    """

    metadata = {**dict(getattr(region, "metadata", {}) or {}), **dict(context or {})}
    explicit_keys = (
        "phrase_end",
        "is_phrase_end",
        "phrase_boundary",
        "section_end",
        "is_section_end",
        "turnaround",
        "is_turnaround",
    )
    explicit_phrase_end = any(_as_policy_bool(metadata.get(key)) for key in explicit_keys)
    phrase_position = str(metadata.get("phrase_position") or metadata.get("phrase_role") or "").strip().lower()
    if phrase_position in {"end", "ending", "last", "tail", "cadence", "phrase_end", "section_end"}:
        explicit_phrase_end = True

    last_region_of_bar = bool(getattr(region, "is_last_region_of_bar", False))
    # Older focused tests and a few synthetic probes may omit the bar-local
    # last-region flag even for a full-bar ChordRegion.  Treat only that
    # genuinely unknown/full-bar shape as a tail; an explicit bar-local end
    # with is_last_region_of_bar=False remains non-tail.
    if not last_region_of_bar and getattr(region, "bar_local_end_beat", None) is None and float(getattr(region, "duration_beats", 0.0) or 0.0) >= 3.75:
        last_region_of_bar = True
    last_bar_of_section = bool(getattr(region, "is_last_bar_of_section", False))
    last_bar_of_chorus = bool(getattr(region, "is_last_bar_of_chorus", False))
    source_bar_index = getattr(region, "source_bar_index", None)
    try:
        source_bar_mod4 = int(source_bar_index) % 4 if source_bar_index is not None else None
        source_bar_mod8 = int(source_bar_index) % 8 if source_bar_index is not None else None
    except (TypeError, ValueError):
        source_bar_mod4 = None
        source_bar_mod8 = None

    four_bar_phrase_tail = last_region_of_bar and source_bar_mod4 == 3
    eight_bar_phrase_tail = last_region_of_bar and source_bar_mod8 == 7
    section_tail = last_region_of_bar and last_bar_of_section
    chorus_tail = last_region_of_bar and last_bar_of_chorus
    harmonic_tail = label in {"section_end", "turnaround_like", "dominant_resolution"}
    ending_tail = label == "ending" or chorus_tail

    phrase_end_context = bool((explicit_phrase_end and last_region_of_bar) or section_tail or four_bar_phrase_tail or eight_bar_phrase_tail)
    precision_status = "non_phrase_end"
    if ending_tail:
        precision_status = "ending_controlled"
    elif section_tail:
        precision_status = "section_phrase_end"
    elif explicit_phrase_end and last_region_of_bar:
        precision_status = "explicit_phrase_end"
    elif eight_bar_phrase_tail:
        precision_status = "eight_bar_phrase_tail"
    elif four_bar_phrase_tail:
        precision_status = "four_bar_phrase_tail"
    elif harmonic_tail:
        precision_status = "harmonic_transition_without_phrase_tail"

    return {
        "phrase_end_context": phrase_end_context,
        "section_tail": section_tail,
        "chorus_tail": chorus_tail,
        "ending_tail": ending_tail,
        "harmonic_tail": harmonic_tail,
        "explicit_phrase_end": explicit_phrase_end,
        "four_bar_phrase_tail": four_bar_phrase_tail,
        "eight_bar_phrase_tail": eight_bar_phrase_tail,
        "last_region_of_bar": last_region_of_bar,
        "source_bar_mod4": source_bar_mod4,
        "source_bar_mod8": source_bar_mod8,
        "precision_status": precision_status,
    }


def _apply_piano_comping_optional_fill_variation_vocabulary_policy(
    candidates: Sequence[PatternCandidate],
    *,
    region: HarmonicRegion,
    context: dict[str, Any],
    history: dict | None = None,
    source_key: str | None = None,
) -> tuple[PatternCandidate, ...]:
    """Guard optional fill/variation candidates inside the existing region pool.

    v2_6_71 activates only a few low-weight optional Medium Swing piano fill
    and variation cells.  v2_6_72 refines the listening behavior after user
    review by splitting variation/fill/busy context weights more precisely while
    keeping the same vocabulary and the same normal ChordRegion-length path; it
    is not a fill selector, phrase engine, voicing chooser, or expression-value
    writer.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    motion = _motion_from_region_context(region, context)
    label = _piano_harmonic_context_label(region, motion)
    fill_context = _is_fill_context(label)
    busy_context = _is_busy_context(label, context)
    phrase_precision = _phrase_end_fill_precision_context(region, label, context)
    phrase_end_context = bool(phrase_precision.get("phrase_end_context"))
    harmonic_transition_context = label in {"section_end", "turnaround_like", "dominant_resolution"}
    transition_context = phrase_end_context or harmonic_transition_context
    precise_transition_fill_context = phrase_end_context and not bool(phrase_precision.get("ending_tail"))
    generic_light_context = label in {"generic", "tonic_prolongation", "section_start", "tonic_resolution"}
    recent = _history_recent_entries(history or {}, source_key or "") if history is not None and source_key else []
    previous = recent[-1] if recent else {}
    recent_active_count = _recent_flag_count(recent, "is_active")
    recent_fill_count = _recent_flag_count(recent, "is_fill")
    recent_busy_count = _recent_flag_count(recent, "is_busy")
    recent_push_count = _recent_flag_count(recent, "is_push")
    recent_tail_push_count = _recent_flag_count(recent, "is_tail_push")

    adjusted: list[PatternCandidate] = []
    optional_count = sum(1 for candidate in candidates if bool(candidate.metadata.get("optional_fill_variation_vocabulary_candidate")))
    for candidate in candidates:
        metadata = dict(candidate.metadata)
        is_optional = bool(metadata.get("optional_fill_variation_vocabulary_candidate"))
        role = str(metadata.get("optional_fill_variation_role") or "none")
        info = _candidate_continuity_metadata(candidate)
        multiplier = 1.0
        reasons: list[str] = []
        status = "non_optional_passthrough"

        if is_optional:
            status = "optional_low_weight_candidate"
            if transition_context:
                if role == "transition_fill":
                    multiplier *= 1.34
                    reasons.append(f"{label}_transition_fill_phrase_end_bonus_v2_6_72")
                    if precise_transition_fill_context:
                        multiplier *= 1.18
                        reasons.append(f"{phrase_precision['precision_status']}_transition_fill_precision_bonus_v2_6_73")
                        status = "optional_context_allowed" if phrase_precision.get("precision_status") == "section_phrase_end" else "optional_phrase_end_precise_context"
                    elif phrase_end_context:
                        multiplier *= 1.04
                        reasons.append("phrase_tail_transition_fill_precision_micro_bonus_v2_6_73")
                        status = "optional_phrase_end_precise_context"
                    else:
                        multiplier *= 0.72
                        reasons.append("harmonic_transition_without_phrase_tail_fill_precision_guard_v2_6_73")
                        status = "optional_transition_harmonic_only_guarded"
                elif role == "variation":
                    multiplier *= 1.06
                    reasons.append(f"{label}_light_variation_context_bonus_v2_6_72")
                    status = "optional_context_allowed"
                elif role == "busy_fill":
                    multiplier *= 0.82 if busy_context else 0.18
                    reasons.append(f"{label}_busy_fill_still_guarded_v2_6_72")
                    status = "optional_busy_context_guarded"
                else:
                    multiplier *= 1.0
                    reasons.append(f"{label}_optional_context_passthrough_v2_6_72")
                    status = "optional_context_allowed"
            elif label == "ending":
                multiplier *= 0.12 if info.get("is_push") or info.get("is_tail_push") else 0.32
                reasons.append("ending_optional_fill_variation_stricter_control_v2_6_72")
                status = "optional_ending_controlled"
            elif generic_light_context and role == "variation" and not info.get("is_push"):
                multiplier *= 0.52
                reasons.append("generic_light_variation_low_frequency_allowance_v2_6_72")
                status = "optional_generic_low_frequency"
            else:
                multiplier *= 0.34
                reasons.append("generic_context_optional_stronger_downweight_v2_6_72")
                status = "optional_generic_low_frequency"

            if info.get("is_fill") and not fill_context:
                multiplier *= 0.58
                reasons.append("optional_fill_outside_fill_context_downweight")
            if info.get("is_busy") and not busy_context:
                multiplier *= 0.08
                reasons.append("optional_busy_outside_busy_context_near_block")
            if info.get("is_push") and label not in {"section_end", "turnaround_like", "dominant_resolution"}:
                multiplier *= 0.30
                reasons.append("optional_push_outside_transition_context_strong_downweight")

            if previous.get("is_active") and info.get("is_active"):
                multiplier *= 0.35
                reasons.append("optional_active_after_active_history_guard")
            if previous.get("is_fill") and info.get("is_fill"):
                multiplier *= 0.25
                reasons.append("optional_fill_after_fill_history_guard")
            if previous.get("is_busy") and info.get("is_busy"):
                multiplier *= 0.02
                reasons.append("optional_busy_after_busy_near_block")
            if recent_active_count >= 1 and info.get("is_active"):
                multiplier *= 0.55
                reasons.append("optional_recent_active_memory_guard")
            if recent_fill_count >= 1 and info.get("is_fill"):
                multiplier *= 0.45
                reasons.append("optional_recent_fill_memory_guard")
            if recent_busy_count >= 1 and info.get("is_busy"):
                multiplier *= 0.04
                reasons.append("optional_recent_busy_memory_guard")
            if recent_push_count >= 1 and info.get("is_push"):
                multiplier *= 0.35
                reasons.append("optional_recent_push_memory_guard")
            if recent_tail_push_count >= 1 and info.get("is_tail_push"):
                multiplier *= 0.08
                reasons.append("optional_recent_tail_push_memory_guard")

            if role == "variation" and recent_fill_count == 0 and recent_busy_count == 0 and transition_context:
                multiplier *= 1.08
                reasons.append("variation_after_clear_recent_history_micro_bonus_v2_6_72")
            if role == "transition_fill" and phrase_end_context and recent_fill_count == 0 and recent_busy_count == 0:
                multiplier *= 1.06
                reasons.append("transition_fill_clear_phrase_end_history_micro_bonus_v2_6_73")
            if role == "transition_fill" and not transition_context:
                multiplier *= 0.60
                reasons.append("transition_fill_requires_transition_context_v2_6_72")
            if role == "transition_fill" and harmonic_transition_context and not phrase_end_context:
                multiplier *= 0.72
                reasons.append("transition_fill_harmonic_only_context_precision_downweight_v2_6_73")
            if role == "busy_fill" and recent_active_count >= 1:
                multiplier *= 0.42
                reasons.append("busy_fill_after_recent_activity_extra_guard_v2_6_72")

            if info.get("region_length_family") in {"one_beat_region", "two_beat_region"}:
                multiplier *= 0.20
                reasons.append("optional_short_region_safety_downweight")

        metadata.update(
            {
                "optional_fill_variation_policy_version": PIANO_COMPING_OPTIONAL_FILL_VARIATION_VOCABULARY_POLICY_VERSION,
                "optional_fill_variation_listening_refinement_policy_version": PIANO_COMPING_OPTIONAL_FILL_VARIATION_LISTENING_REFINEMENT_POLICY_VERSION,
                "optional_fill_variation_listening_refinement_policy_applied": True,
                "phrase_end_fill_context_precision_policy_version": PIANO_COMPING_PHRASE_END_FILL_CONTEXT_PRECISION_POLICY_VERSION,
                "phrase_end_fill_context_precision_policy_applied": True,
                "standard_tune_fill_frequency_checkpoint_version": PIANO_COMPING_STANDARD_TUNE_FILL_FREQUENCY_CHECKPOINT_VERSION,
                "standard_tune_fill_frequency_checkpoint_applied": True,
                "standard_tune_fill_frequency_checkpoint_scope": "audit_only_no_behavior_change",
                "medium_swing_piano_comping_phase_completion_checkpoint_version": PIANO_COMPING_PHASE_COMPLETION_CHECKPOINT_VERSION,
                "medium_swing_piano_comping_phase_completion_checkpoint_applied": True,
                "medium_swing_piano_comping_phase_completion_checkpoint_scope": "stage_summary_no_behavior_change",
                "optional_fill_variation_policy_applied": True,
                "optional_fill_variation_candidate": bool(is_optional),
                "optional_fill_variation_context_label": label,
                "optional_fill_variation_transition_context": transition_context,
                "optional_fill_variation_phrase_end_context": phrase_end_context,
                "optional_fill_variation_precise_transition_fill_context": precise_transition_fill_context,
                "optional_fill_variation_harmonic_transition_context": harmonic_transition_context,
                "optional_fill_variation_phrase_precision_status": phrase_precision.get("precision_status"),
                "optional_fill_variation_phrase_source_bar_mod4": phrase_precision.get("source_bar_mod4"),
                "optional_fill_variation_phrase_source_bar_mod8": phrase_precision.get("source_bar_mod8"),
                "optional_fill_variation_phrase_last_region_of_bar": phrase_precision.get("last_region_of_bar"),
                "optional_fill_variation_phrase_explicit_phrase_end": phrase_precision.get("explicit_phrase_end"),
                "optional_fill_variation_phrase_four_bar_tail": phrase_precision.get("four_bar_phrase_tail"),
                "optional_fill_variation_phrase_eight_bar_tail": phrase_precision.get("eight_bar_phrase_tail"),
                "optional_fill_variation_generic_light_context": generic_light_context,
                "optional_fill_variation_role_runtime": role,
                "optional_fill_variation_status": status,
                "optional_fill_variation_multiplier": round(multiplier, 4),
                "optional_fill_variation_reasons": tuple(reasons),
                "optional_fill_variation_total_optional_candidate_count": optional_count,
                "optional_fill_variation_recent_active_count": recent_active_count,
                "optional_fill_variation_recent_fill_count": recent_fill_count,
                "optional_fill_variation_recent_busy_count": recent_busy_count,
                "optional_fill_variation_recent_push_count": recent_push_count,
                "optional_fill_variation_recent_tail_push_count": recent_tail_push_count,
                "optional_fill_variation_contract": "Optional fill/variation candidates are reweighted inside the existing ChordRegion-length pool and remain protected by the v2_6_67 active/fill/busy history scorer; no parallel fill selector, bar-first phrase route, voicing logic, or final expression values are introduced.",
                "optional_fill_variation_listening_refinement_contract": "v2_6_72 keeps the v2_6_71 three-candidate vocabulary unchanged and only refines context/history multipliers so variation stays low-intrusion, transition fill prefers phrase/section/turnaround contexts, and busy remains heavily guarded.",
                "phrase_end_fill_context_precision_contract": "v2_6_73 narrows the existing optional transition-fill bonus toward explicit phrase ends, section tails, and 4/8-bar phrase tails while downweighting harmonic-transition-only regions; it does not add a phrase engine, fill selector, new vocabulary, voicing logic, or final expression values.",
                "standard_tune_fill_frequency_checkpoint_contract": "v2_6_74 is an audit/listening checkpoint that measures optional fill/variation frequency, phrase-tail targeting, and continuity safety on standard-tune demos; it does not change weights, add vocabulary, create a fill selector, or touch voicing/expression/API behavior.",
                "medium_swing_piano_comping_phase_completion_checkpoint_contract": "v2_6_76 is a stage-completion checkpoint for the v2_6_56 through v2_6_74 Medium Swing piano comping line. It summarizes vocabulary, history, expression handoff, ending, and optional-fill safety before returning to voicing or broader listening work; it does not change pattern weights, add vocabulary, or touch voicing/expression/API/Agent/HarmonyOS behavior.",
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


def _apply_piano_comping_history_continuity_scorer(
    candidates: Sequence[PatternCandidate],
    *,
    history: dict,
    source_key: str,
    region: HarmonicRegion | None = None,
    context: dict[str, Any] | None = None,
) -> tuple[PatternCandidate, ...]:
    """Apply Medium Swing piano comping history scoring in-place.

    v2_6_67 keeps the existing ChordRegion-length candidate pool and extends
    the old v2_6_59 continuity scorer with multi-region active/fill/busy/push
    memory.  It is still a weight rewriter before normal sampling, not a
    parallel pattern selector or a bar-first phrase engine.
    """

    if len(candidates) <= 1:
        return tuple(candidates)
    recent = _history_recent_entries(history, source_key)
    previous = recent[-1] if recent else {}
    recent_classes = [str(item.get("continuity_class") or "") for item in recent]
    recent_tail_push_count = _recent_flag_count(recent, "is_tail_push") or sum(1 for value in recent_classes if value == "tail_push")
    recent_push_count = _recent_flag_count(recent, "is_push") or recent_tail_push_count
    recent_active_count = _recent_flag_count(recent, "is_active") or sum(1 for value in recent_classes if value == "active")
    recent_fill_count = _recent_flag_count(recent, "is_fill") or sum(1 for value in recent_classes if value == "fill")
    recent_busy_count = _recent_flag_count(recent, "is_busy") or sum(1 for value in recent_classes if value == "busy")
    recent_offbeat_count = _recent_flag_count(recent, "is_offbeat") or sum(1 for value in recent_classes if value == "offbeat")
    motion = _motion_from_region_context(region, context or {}) if region is not None else None
    label = _piano_harmonic_context_label(region, motion) if region is not None and motion is not None else "unknown"
    fill_context = _is_fill_context(label)
    busy_context = _is_busy_context(label, context)

    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        info = _candidate_continuity_metadata(candidate)
        continuity_class = str(info["continuity_class"])
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

        if bool(info.get("is_active")) and previous.get("is_active"):
            multiplier *= 0.55
            reasons.append("active_after_active_medium_penalty")
        if recent_active_count >= 1 and continuity_class == "active":
            multiplier *= 0.18
            reasons.append("recent_active_penalty")
        if recent_active_count >= 2 and bool(info.get("is_active")):
            multiplier *= 0.45
            reasons.append("recent_active_multi_region_penalty")

        if bool(info.get("is_fill")):
            if previous.get("is_fill"):
                multiplier *= 0.38
                reasons.append("fill_after_fill_strong_penalty")
            if recent_fill_count >= 1:
                multiplier *= 0.62
                reasons.append("recent_fill_multi_region_penalty")
            if not fill_context:
                multiplier *= 0.58
                reasons.append("fill_outside_phrase_section_turnaround_context_downweight")

        if bool(info.get("is_busy")):
            if previous.get("is_busy"):
                multiplier *= 0.02
                reasons.append("busy_after_busy_near_block")
            if recent_busy_count >= 1:
                multiplier *= 0.06
                reasons.append("recent_busy_near_block")
            if previous.get("is_active") or previous.get("is_fill"):
                multiplier *= 0.25
                reasons.append("busy_after_active_or_fill_strong_penalty")
            if not busy_context:
                multiplier *= 0.05
                reasons.append("busy_outside_explicit_high_energy_or_phrase_end_near_block")

        if bool(info.get("is_push")) and previous.get("is_push"):
            multiplier *= 0.22
            reasons.append("push_after_push_strong_penalty")
        if recent_push_count >= 1 and bool(info.get("is_push")):
            multiplier *= 0.35
            reasons.append("recent_push_multi_region_penalty")
        if recent_tail_push_count >= 1 and bool(info.get("is_tail_push")):
            multiplier *= 0.05
            reasons.append("recent_tail_push_penalty")

        if previous.get("continuity_class") in {"active", "tail_push"} and continuity_class == "stable":
            multiplier *= 1.18
            reasons.append("stable_reset_after_active_bonus")
        if previous.get("continuity_class") == "fill" and continuity_class == "stable":
            multiplier *= 1.25
            reasons.append("stable_reset_after_fill_bonus")
        if previous.get("continuity_class") == "busy" and continuity_class == "stable":
            multiplier *= 1.35
            reasons.append("stable_reset_after_busy_bonus")
        if previous.get("continuity_class") == "offbeat" and continuity_class == "stable":
            multiplier *= 1.08
            reasons.append("stable_reset_after_offbeat_bonus")
        if previous.get("is_active") and continuity_class == "stable" and info.get("has_region_start") and info.get("region_length_family") in {"one_beat_region", "two_beat_region"}:
            multiplier *= 1.12
            reasons.append("anchor_led_short_region_after_active_bonus")
        if recent_push_count >= 1 and bool(info.get("is_no_4and_delayed_tail")):
            multiplier *= 1.15
            reasons.append("no_4and_delayed_tail_after_recent_push_bonus")

        metadata = {
            **dict(candidate.metadata),
            "history_continuity_scorer_version": PIANO_COMPING_HISTORY_CONTINUITY_SCORER_VERSION,
            "medium_swing_active_fill_busy_history_policy_version": PIANO_COMPING_ACTIVE_FILL_BUSY_MULTI_REGION_HISTORY_SCORER_VERSION,
            "active_fill_busy_multi_region_history_policy_version": PIANO_COMPING_ACTIVE_FILL_BUSY_MULTI_REGION_HISTORY_SCORER_VERSION,
            "history_continuity_scorer_applied": True,
            "history_continuity_multiplier": round(multiplier, 4),
            "history_continuity_reasons": tuple(reasons),
            "history_continuity_class": continuity_class,
            "history_activity_class": info.get("activity_class"),
            "history_continuity_previous_class": previous.get("continuity_class"),
            "history_continuity_previous_candidate": previous.get("name"),
            "history_continuity_recent_window_size": len(recent),
            "history_recent_active_count": recent_active_count,
            "history_recent_fill_count": recent_fill_count,
            "history_recent_busy_count": recent_busy_count,
            "history_recent_push_count": recent_push_count,
            "history_recent_tail_push_count": recent_tail_push_count,
            "history_recent_offbeat_count": recent_offbeat_count,
            "history_candidate_is_active": bool(info.get("is_active")),
            "history_candidate_is_fill": bool(info.get("is_fill")),
            "history_candidate_is_busy": bool(info.get("is_busy")),
            "history_candidate_is_push": bool(info.get("is_push")),
            "history_candidate_is_tail_push": bool(info.get("is_tail_push")),
            "history_candidate_is_no_4and_delayed_tail": bool(info.get("is_no_4and_delayed_tail")),
            "history_context_label": label,
            "history_fill_context": fill_context,
            "history_busy_context": busy_context,
            "history_continuity_contract": "Existing region-length candidate pool is reweighted by recent piano comping history; v2_6_67 adds multi-region active/fill/busy/push memory without creating a parallel selector or bar-first phrase route.",
        }
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


def _record_piano_comping_history(history: dict, source_key: str, candidate: PatternCandidate) -> None:
    info = _candidate_continuity_metadata(candidate)
    recent = _history_recent_entries(history, source_key)
    recent.append(info)
    history[f"{source_key}:recent_comping"] = recent[-6:]
    history[f"{source_key}:rhythm_family"] = info["rhythm_family"]
    history[f"{source_key}:weight_calibration_class"] = info["weight_calibration_class"]
    history[f"{source_key}:continuity_class"] = info["continuity_class"]
    history[f"{source_key}:activity_class"] = info["activity_class"]
    history[f"{source_key}:tail_push_risk"] = info["tail_push_risk"]
    history[f"{source_key}:recent_active_count"] = _recent_flag_count(recent, "is_active")
    history[f"{source_key}:recent_fill_count"] = _recent_flag_count(recent, "is_fill")
    history[f"{source_key}:recent_busy_count"] = _recent_flag_count(recent, "is_busy")
    history[f"{source_key}:recent_push_count"] = _recent_flag_count(recent, "is_push")
    history[f"{source_key}:recent_tail_push_count"] = _recent_flag_count(recent, "is_tail_push")


def _resolve_medium_swing_arrangement_arc_runtime_intent(region: HarmonicRegion) -> dict[str, Any]:
    try:
        from jammate_engine.styles.medium_swing.arrangement_policy import resolve_runtime_arrangement_arc_intent
    except Exception:
        return {}
    return dict(resolve_runtime_arrangement_arc_intent(region.chorus_index, region.total_choruses))


def _apply_medium_swing_arrangement_arc_runtime_intent_policy(
    candidates: Sequence[PatternCandidate],
    *,
    intent: dict[str, Any] | None,
    listening_refinement_enabled: bool = False,
    ending_realization_checkpoint_enabled: bool = False,
    style_baseline_phase_completion_enabled: bool = False,
) -> tuple[PatternCandidate, ...]:
    """Use repeat-count-aware arrangement arc as style intent, not as a new selector."""

    if len(candidates) <= 1 or not intent:
        return tuple(candidates)
    try:
        from jammate_engine.styles.medium_swing.arrangement_policy import arrangement_arc_runtime_candidate_multiplier
    except Exception:
        return tuple(candidates)

    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        multiplier, reasons, status = arrangement_arc_runtime_candidate_multiplier(dict(candidate.metadata), dict(intent))
        metadata = {
            **dict(candidate.metadata),
            "medium_swing_arrangement_arc_runtime_intent_usage_version": MEDIUM_SWING_ARRANGEMENT_ARC_RUNTIME_INTENT_USAGE_VERSION,
            "medium_swing_arrangement_arc_runtime_intent_usage_applied": True,
            "medium_swing_arrangement_arc_runtime_intent_phase": intent.get("phase"),
            "medium_swing_arrangement_arc_runtime_intent_energy_band": intent.get("energy_band"),
            "medium_swing_arrangement_arc_runtime_intent_density_bias": intent.get("density_bias"),
            "medium_swing_arrangement_arc_runtime_intent_piano_comping_bias": intent.get("piano_comping_bias"),
            "medium_swing_arrangement_arc_runtime_intent_piano_comping_runtime_intent": intent.get("piano_comping_runtime_intent"),
            "medium_swing_arrangement_arc_runtime_intent_fill_bias": intent.get("fill_bias"),
            "medium_swing_arrangement_arc_runtime_intent_thick_voicing_bias": intent.get("thick_voicing_bias"),
            "medium_swing_arrangement_arc_runtime_intent_chorus_index": intent.get("chorus_index"),
            "medium_swing_arrangement_arc_runtime_intent_total_choruses": intent.get("total_choruses"),
            "medium_swing_arrangement_arc_runtime_intent_normalized_position": intent.get("normalized_position"),
            "medium_swing_arrangement_arc_runtime_intent_loop_block_position": intent.get("loop_block_position"),
            "medium_swing_arrangement_arc_runtime_intent_multiplier": round(float(multiplier), 4),
            "medium_swing_arrangement_arc_runtime_intent_status": status,
            "medium_swing_arrangement_arc_runtime_intent_reasons": tuple(reasons),
            "medium_swing_arrangement_arc_runtime_intent_not_three_chorus_hardcoded": True,
            "medium_swing_arrangement_arc_runtime_intent_boundary": "style_intent_metadata_and_candidate_weighting_only",
            "medium_swing_arrangement_arc_runtime_intent_contract": "v2_6_85 connects the repeat-count-aware Medium Swing arc to runtime piano-comping candidate weighting and event metadata. It does not add vocabulary, create a selector, choose voicing sources, write expression values, or hard-code a 3-chorus arc.",
        }
        if listening_refinement_enabled:
            metadata.update({
                "medium_swing_arrangement_arc_runtime_listening_refinement": True,
                "medium_swing_arrangement_arc_runtime_listening_refinement_version": MEDIUM_SWING_ARRANGEMENT_ARC_RUNTIME_LISTENING_REFINEMENT_VERSION,
                "medium_swing_arrangement_arc_runtime_listening_refinement_scope": "post_user_approved_runtime_arc_checkpoint_metadata_only",
                "medium_swing_arrangement_arc_runtime_listening_refinement_behavior_change": False,
                "medium_swing_arrangement_arc_runtime_listening_refinement_contract": "v2_6_86 preserves the v2_6_85 repeat-count-aware arc weighting after user listening approval and stamps checkpoint metadata for 3x/5x full-band audit. It does not add patterns, alter multipliers, change core voicing, write expression numbers, or touch API/Agent/HarmonyOS.",
            })
        if ending_realization_checkpoint_enabled:
            metadata.update({
                "medium_swing_full_band_ending_realization_checkpoint": True,
                "medium_swing_full_band_ending_realization_checkpoint_version": MEDIUM_SWING_FULL_BAND_ENDING_REALIZATION_CHECKPOINT_VERSION,
                "medium_swing_full_band_ending_realization_checkpoint_scope": "full_band_ending_audit_metadata_only",
                "medium_swing_full_band_ending_realization_checkpoint_behavior_change": False,
                "medium_swing_full_band_ending_realization_checkpoint_contract": "v2_6_87 audits full-band Medium Swing ending realization after the user-approved repeat-count-aware arc. It stamps checkpoint metadata only and does not add ending patterns, alter multipliers, modify core voicing, write expression numbers, or touch API/Agent/HarmonyOS.",
            })
        if style_baseline_phase_completion_enabled:
            metadata.update({
                "medium_swing_style_baseline_phase_completion_checkpoint": True,
                "medium_swing_style_baseline_phase_completion_checkpoint_version": MEDIUM_SWING_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
                "medium_swing_style_baseline_phase_completion_checkpoint_scope": "full_band_baseline_summary_metadata_only",
                "medium_swing_style_baseline_phase_completion_checkpoint_behavior_change": False,
                "medium_swing_style_baseline_phase_completion_checkpoint_contract": "v2_6_88 summarizes the Medium Swing v2_6_56-v2_6_87 full-band baseline: ChordRegion-first piano comping, semantic expression hints, generic anticipation, 2-beat density relief, explicit low-intrusion 5/6-note voicing intent, bass/piano and drum/piano interaction, repeat-count-aware arc, and ending realization. It stamps phase-completion audit metadata only and does not change pattern weights, add vocabulary, modify core voicing, write expression numbers, or touch API/Agent/HarmonyOS.",
            })
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * float(multiplier)), metadata=metadata))
    return tuple(adjusted)


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
        piano_ending_subset_policy = bool(self.arrangement_policy.get("piano_comping_ending_specific_subset_policy", False))
        piano_optional_fill_variation_policy = bool(self.arrangement_policy.get("piano_comping_optional_fill_variation_vocabulary_policy", False))
        piano_two_beat_density_relief_policy = bool(self.arrangement_policy.get("piano_comping_two_beat_region_density_relief_policy", False))
        medium_swing_arrangement_arc_runtime_intent_usage = bool(self.arrangement_policy.get("medium_swing_arrangement_arc_runtime_intent_usage", False))
        medium_swing_arrangement_arc_runtime_listening_refinement = bool(self.arrangement_policy.get("medium_swing_arrangement_arc_runtime_listening_refinement", False))
        medium_swing_full_band_ending_realization_checkpoint = bool(self.arrangement_policy.get("medium_swing_full_band_ending_realization_checkpoint", False))
        medium_swing_style_baseline_phase_completion_checkpoint = bool(self.arrangement_policy.get("medium_swing_style_baseline_phase_completion_checkpoint", False))
        piano_region_first_coverage_guard = bool(self.arrangement_policy.get("piano_region_first_coverage_guard", False))

        arrangement_arc_intent: dict[str, Any] = {}
        if self.name == "medium_swing" and medium_swing_arrangement_arc_runtime_intent_usage:
            arrangement_arc_intent = _resolve_medium_swing_arrangement_arc_runtime_intent(region)
            region_context["medium_swing_arrangement_arc_intent"] = arrangement_arc_intent

        plans: list[PatternPlan] = []
        selected: list[str] = []
        for source_index, source in enumerate(self.pattern_sources):
            candidates = tuple(source(region_context))
            if not candidates:
                continue
            source_key = f"{self.name}:{source_index}:{getattr(source, '__module__', '')}.{getattr(source, '__name__', 'source')}"
            is_piano_comping_source = ".comping_patterns" in source_key
            two_beat_density_relief_repeat_exception = (
                is_piano_comping_source
                and piano_two_beat_density_relief_policy
                and _region_length_family_for_coverage(float(region.duration_beats)) == "two_beat_region"
            )
            choice_pool = candidates
            if avoid_repeat and not two_beat_density_relief_repeat_exception and len(choice_pool) > 1:
                previous_name = history.get(source_key)
                filtered = tuple(candidate for candidate in choice_pool if candidate.name != previous_name)
                if filtered:
                    choice_pool = filtered
            if avoid_category_repeat and not two_beat_density_relief_repeat_exception and len(choice_pool) > 1:
                previous_category = history.get(f"{source_key}:category")
                filtered = tuple(candidate for candidate in choice_pool if candidate.category != previous_category)
                if filtered:
                    choice_pool = filtered
            if piano_density_guard and is_piano_comping_source and len(choice_pool) > 1:
                previous_density = history.get(f"{source_key}:density")
                if previous_density == "dense":
                    filtered = tuple(candidate for candidate in choice_pool if candidate.metadata.get("density") != "dense")
                    if filtered:
                        choice_pool = filtered
            if piano_progression_subset_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_progression_specific_subset_policy(choice_pool, region=region, context=region_context)
            if piano_ending_subset_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_ending_specific_subset_policy(choice_pool, region=region, context=region_context)
            if piano_two_beat_density_relief_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_two_beat_region_density_relief_policy(choice_pool, region=region, context=region_context, history=history, source_key=source_key)
            if medium_swing_arrangement_arc_runtime_intent_usage and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_medium_swing_arrangement_arc_runtime_intent_policy(
                    choice_pool,
                    intent=arrangement_arc_intent,
                    listening_refinement_enabled=medium_swing_arrangement_arc_runtime_listening_refinement,
                    ending_realization_checkpoint_enabled=medium_swing_full_band_ending_realization_checkpoint,
                    style_baseline_phase_completion_enabled=medium_swing_style_baseline_phase_completion_checkpoint,
                )
            if piano_optional_fill_variation_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_optional_fill_variation_vocabulary_policy(choice_pool, region=region, context=region_context, history=history, source_key=source_key)
            if piano_no_4and_delayed_tail_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_no_4and_delayed_tail_policy(choice_pool)
            if piano_harmonic_function_policy and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_harmonic_function_policy(choice_pool, region=region, context=region_context)
            if piano_history_scorer and is_piano_comping_source and len(choice_pool) > 1:
                choice_pool = _apply_piano_comping_history_continuity_scorer(choice_pool, history=history, source_key=source_key, region=region, context=region_context)
            candidate = choose_weighted_candidate(choice_pool, rng)
            history[source_key] = candidate.name
            history[f"{source_key}:category"] = candidate.category
            if is_piano_comping_source:
                history[f"{source_key}:density"] = str(candidate.metadata.get("density", "medium"))
                if piano_history_scorer:
                    _record_piano_comping_history(history, source_key, candidate)
            selected.append(candidate.name)
            plan = candidate.instantiate(region)
            if is_piano_comping_source and (piano_history_scorer or piano_harmonic_function_policy or piano_progression_subset_policy or piano_ending_subset_policy or piano_optional_fill_variation_policy or piano_two_beat_density_relief_policy or medium_swing_arrangement_arc_runtime_intent_usage or piano_no_4and_delayed_tail_policy or piano_region_first_coverage_guard):
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
