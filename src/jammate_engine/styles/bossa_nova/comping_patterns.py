from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

STYLE_ID = "bossa_nova"
PATTERN_LIBRARY_ID = "bossa_nova.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_6_92"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOSSA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION = "v2_6_91"
BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION = "v2_6_92"
BOSSA_ANTICIPATION_TAIL_POLICY_VERSION = "v2_6_93"
BOSSA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION = "v2_6_103"
BOSSA_TWO_BEAT_PHRASE_PAIR_VOCABULARY_VERSION = "v2_6_120"
BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION = "v2_6_99"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "single_core_batida_identity_anchor",
    "class_A_class_B_rhythm_cells_active",
    "context_archetype_policy_active",
    "history_scorer_refined",
    "anticipation_tail_policy_native_4and_audit_active",
    "harmonic_rhythm_region_clarity_voicing_intent_audit_active",
    "two_beat_phrase_pair_vocabulary_v2_6_120",
    "chord_region_first",
    "no_voicing_logic",
    "no_final_expression_values",
)


def _comping_metadata(
    *,
    density: str,
    cell: str,
    function: str,
    region_shape: str = "four_beat_region",
    rhythm_class: str = "core",
    native_4and: bool = False,
    hit_count: int = 1,
    ordinary_body_candidate: bool = False,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "density": density,
        "style_id": STYLE_ID,
        "pattern_domain": PATTERN_DOMAIN,
        "pattern_library_id": PATTERN_LIBRARY_ID,
        "pattern_library_version": PATTERN_LIBRARY_VERSION,
        "track_role": TRACK_ROLE,
        "region_shape": region_shape,
        "rhythmic_cell": cell,
        "rhythm_class": rhythm_class,
        "pattern_function": function,
        "hit_count": int(hit_count),
        "native_4and": bool(native_4and),
        "ordinary_body_candidate": bool(ordinary_body_candidate),
        "onset_mode": DEFAULT_ONSET_MODE,
        "voicing_boundary": "pattern_is_pitchless",
        "expression_boundary": "pattern_uses_semantic_profile_ids_only",
        "bossa_non_core_rhythm_cell_vocabulary_version": BOSSA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION,
        "bossa_non_core_rhythm_cell_vocabulary_active": True,
        "bossa_non_core_rhythm_cell_vocabulary_contract": (
            "Bossa piano non-core vocabulary is implemented inside the existing style-owned ChordRegion-first pattern library. "
            "It adds pitchless Class A/Class B rhythm cells while keeping core_batida as the sole identity anchor; "
            "it does not choose voicing, MIDI velocity, final duration, pedal, or a parallel selector."
        ),
        "bossa_context_archetype_policy_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_context_archetype_policy_active": True,
        "bossa_anticipation_tail_policy_version": BOSSA_ANTICIPATION_TAIL_POLICY_VERSION,
        "bossa_anticipation_tail_policy_native_4and_audit_active": True,
        "bossa_harmonic_rhythm_region_clarity_and_voicing_intent_version": BOSSA_HARMONIC_RHYTHM_REGION_CLARITY_AND_VOICING_INTENT_VERSION,
        "bossa_harmonic_rhythm_region_clarity_and_voicing_intent_candidate_metadata_active": True,
        "bossa_style_baseline_phase_completion_checkpoint": True,
        "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_style_baseline_phase_completion_checkpoint_boundary": "piano_pattern_metadata_only_no_vocabulary_or_weight_change",
    }
    if extra_metadata:
        metadata.update(dict(extra_metadata))
    return metadata


def _two_beat_phrase_pair_metadata(*, role: str, family: str = "beat1_beat2_to_1and_hold") -> dict[str, Any]:
    metadata = {
        "two_beat_phrase_pair_candidate": True,
        "two_beat_phrase_pair_vocabulary_version": BOSSA_TWO_BEAT_PHRASE_PAIR_VOCABULARY_VERSION,
        "two_beat_phrase_pair_family": family,
        "two_beat_phrase_pair_role": role,
        "two_beat_phrase_pair_contract": (
            "Bossa models the common two-2-beat-ChordRegion phrase as region-local pitchless vocabulary plus shared history-aware weighting: "
            "the first 2-beat region may play local beat 1+2, and the following 2-beat region may answer on local 1& with a hold, "
            "corresponding to full-bar beat 3&. No bar-first selector, concrete voicing, velocity, duration, pedal, or MIDI pitch is embedded in the pattern."
        ),
    }
    if role == "call":
        metadata["two_beat_phrase_pair_triggers_response_cells"] = ("bossa_half_region_1and_hold",)
    return metadata


def _event_metadata(
    *,
    cell: str,
    rhythm_class: str,
    event_role: str,
    semantic_hint: str,
    native_4and: bool = False,
    event_index: int = 0,
) -> dict[str, Any]:
    return {
        "rhythmic_cell": cell,
        "rhythm_class": rhythm_class,
        "bossa_event_role": event_role,
        "semantic_expression_hint": semantic_hint,
        "native_4and": bool(native_4and),
        "event_index_in_cell": int(event_index),
        "timing_intent": "straight_even",
        "bossa_non_core_rhythm_cell_vocabulary_version": BOSSA_NON_CORE_RHYTHM_CELL_VOCABULARY_VERSION,
        "bossa_anticipation_tail_policy_version": BOSSA_ANTICIPATION_TAIL_POLICY_VERSION,
        "native_4and_is_current_chord_event_not_anticipation": bool(native_4and),
        "expression_boundary": "semantic_hint_only",
        "voicing_boundary": "pitchless_event_only",
        "bossa_style_baseline_phase_completion_checkpoint": True,
        "bossa_style_baseline_phase_completion_checkpoint_version": BOSSA_STYLE_BASELINE_PHASE_COMPLETION_CHECKPOINT_VERSION,
        "bossa_style_baseline_phase_completion_checkpoint_behavior_change": False,
        "bossa_style_baseline_phase_completion_checkpoint_boundary": "piano_event_metadata_only_no_expression_or_voicing_change",
    }


def _event(beat: float, *, cell: str, rhythm_class: str, role: str, hint: str, native_4and: bool = False, index: int = 0):
    semantic_hint = "close_gap_mostly_short" if hint == "cell_close_gap_short" else "soft_hold"
    if hint == "core_short":
        semantic_hint = "core_short"
    elif hint == "core_sustain":
        semantic_hint = "core_sustain"
    return event_spec(
        track="piano",
        beat=beat,
        role="harmonic",
        gesture=simultaneous_onset(),
        expression_hint=hint,
        metadata=_event_metadata(
            cell=cell,
            rhythm_class=rhythm_class,
            event_role=role,
            semantic_hint=semantic_hint,
            native_4and=native_4and,
            event_index=index,
        ),
    )


def _candidate(
    *,
    name: str,
    weight: float,
    category: str,
    cell: str,
    rhythm_class: str,
    beats: tuple[tuple[float, str, str], ...],
    density: str,
    function: str,
    tags: tuple[str, ...],
    region_shape: str = "four_beat_region",
    native_4and: bool = False,
    ordinary_body_candidate: bool = False,
    extra_metadata: dict[str, Any] | None = None,
    extra_tags: tuple[str, ...] = (),
) -> PatternCandidate:
    local_beats = tuple(float(beat) for beat, _role, _hint in beats)
    beat1_present = any(abs(beat) < 1e-6 for beat in local_beats)
    return PatternCandidate(
        name=name,
        weight=float(weight),
        category=category,
        events=tuple(
            _event(
                beat,
                cell=cell,
                rhythm_class=rhythm_class,
                role=role,
                hint=hint,
                native_4and=native_4and and abs(float(beat) - 3.5) < 1e-6,
                index=index,
            )
            for index, (beat, role, hint) in enumerate(beats)
        ),
        tail_policy=TailPolicy.from_local_beats(local_beats),
        beat1_movability=Beat1Movability(
            movable=beat1_present,
            reason=(
                f"{cell}_beat1_can_move_to_previous_4and_when_tail_free"
                if beat1_present
                else f"{cell}_has_no_region_start_event_for_previous_tail_anticipation"
            ),
        ),
        metadata=_comping_metadata(
            density=density,
            cell=cell,
            function=function,
            region_shape=region_shape,
            rhythm_class=rhythm_class,
            native_4and=native_4and,
            hit_count=len(beats),
            ordinary_body_candidate=ordinary_body_candidate,
            extra_metadata=extra_metadata,
        ),
        tags=tags + extra_tags,
    )


def _core_candidate() -> PatternCandidate:
    return _candidate(
        name="bossa_piano_core_batida_1_2_3and",
        weight=220.0,
        category="core_batida_identity_anchor",
        cell="1_2_3and",
        rhythm_class="core_batida",
        beats=((0.0, "core_anchor_short", "core_short"), (1.0, "core_pulse_short", "core_short"), (2.5, "core_sync_sustain", "core_sustain")),
        density="identity",
        function="core_batida_identity_anchor",
        tags=("bossa", "piano", "core_batida", "identity_anchor", "chord_region_first", "comping"),
    )


def _half_region_candidate() -> PatternCandidate:
    return _candidate(
        name="bossa_piano_half_region_1_2",
        weight=1.0,
        category="core_batida_half_region_adaptation",
        cell="half_region_1_2",
        rhythm_class="half_region_adaptation",
        beats=((0.0, "short_region_anchor", "core_short"), (1.0, "short_region_hold", "core_sustain")),
        density="identity",
        function="dense_harmonic_rhythm_normal_voicing_adaptation",
        region_shape="two_beat_region",
        extra_metadata=_two_beat_phrase_pair_metadata(role="call"),
        extra_tags=("two_beat_phrase_pair", "phrase_call"),
        tags=("bossa", "piano", "core_batida", "two_beat_region", "dense_harmonic_region", "chord_region_first", "comping"),
    )


def _half_region_1and_hold_candidate() -> PatternCandidate:
    return _candidate(
        name="bossa_piano_half_region_1and_hold",
        weight=0.45,
        category="bossa_two_beat_phrase_response_hold",
        cell="bossa_half_region_1and_hold",
        rhythm_class="half_region_phrase_response",
        beats=((0.5, "phrase_response_hold", "cell_soft_hold"),),
        density="low_mid",
        function="two_beat_phrase_response_local_1and_hold",
        region_shape="two_beat_region",
        extra_metadata={
            **_two_beat_phrase_pair_metadata(role="response"),
            "two_beat_phrase_pair_responds_to_cell": "half_region_1_2",
            "two_beat_phrase_pair_responds_to_cells": ("half_region_1_2",),
            "two_beat_phrase_pair_local_beat_semantics": "second 2-beat Bossa region local 1& equals full-bar beat 3&",
        },
        extra_tags=("two_beat_phrase_pair", "phrase_response", "hold"),
        tags=("bossa", "piano", "bossa_cell", "two_beat_region", "phrase_response", "chord_region_first", "comping"),
    )


def _half_region_phrase_pair_candidates() -> tuple[PatternCandidate, ...]:
    return (_half_region_candidate(), _half_region_1and_hold_candidate())


def _class_a_candidates() -> tuple[PatternCandidate, ...]:
    base_tags = ("bossa", "piano", "bossa_cell", "class_A", "chord_region_first", "comping")
    return (
        _candidate(
            name="bossa_piano_cell_A_1",
            weight=162.0,
            category="bossa_cell_A",
            cell="A_1",
            rhythm_class="class_A",
            beats=((0.0, "single_hold", "cell_soft_hold"),),
            density="low_mid",
            function="ordinary_single_chord_region_cell",
            tags=base_tags + ("one_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_A_1_2and",
            weight=180.0,
            category="bossa_cell_A",
            cell="A_1_2and",
            rhythm_class="class_A",
            beats=((0.0, "cell_event_1", "cell_soft_hold"), (1.5, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="ordinary_single_chord_region_cell",
            tags=base_tags + ("two_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_A_1_3and",
            weight=252.0,
            category="bossa_cell_A",
            cell="A_1_3and",
            rhythm_class="class_A",
            beats=((0.0, "cell_event_1", "cell_soft_hold"), (2.5, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="ordinary_single_chord_region_cell",
            tags=base_tags + ("two_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_A_1_4and",
            weight=27.0,
            category="bossa_cell_A_rare_4and",
            cell="A_1_4and",
            rhythm_class="class_A",
            beats=((0.0, "cell_event_1", "cell_soft_hold"), (3.5, "native_4and_color", "cell_soft_hold")),
            density="low_mid",
            function="rare_native_current_chord_4and_color",
            tags=base_tags + ("native_4and", "rare"),
            native_4and=True,
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_A_1_3",
            weight=72.0,
            category="bossa_cell_A_low",
            cell="A_1_3",
            rhythm_class="class_A",
            beats=((0.0, "cell_event_1", "cell_soft_hold"), (2.0, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="stable_square_lower_weight_cell",
            tags=base_tags + ("two_hit", "stable_low_weight"),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_A_1_2_3and",
            weight=207.0,
            category="bossa_cell_A",
            cell="A_1_2_3and",
            rhythm_class="class_A",
            beats=((0.0, "cell_event_1", "cell_close_gap_short"), (1.0, "cell_event_2", "cell_soft_hold"), (2.5, "cell_event_3", "cell_soft_hold")),
            density="medium",
            function="ordinary_three_hit_cell_not_identity_core",
            tags=base_tags + ("three_hit",),
            ordinary_body_candidate=True,
        ),
    )


def _class_b_candidates() -> tuple[PatternCandidate, ...]:
    base_tags = ("bossa", "piano", "bossa_cell", "class_B", "one_and_start", "chord_region_first", "comping")
    return (
        _candidate(
            name="bossa_piano_cell_B_1and",
            weight=22.0,
            category="bossa_cell_B",
            cell="B_1and",
            rhythm_class="class_B",
            beats=((0.5, "single_hold", "cell_soft_hold"),),
            density="low_mid",
            function="ordinary_single_chord_region_cell_color",
            tags=base_tags + ("one_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_B_1and_3",
            weight=38.0,
            category="bossa_cell_B",
            cell="B_1and_3",
            rhythm_class="class_B",
            beats=((0.5, "cell_event_1", "cell_soft_hold"), (2.0, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="strongest_one_and_start_color",
            tags=base_tags + ("two_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_B_1and_3and",
            weight=17.0,
            category="bossa_cell_B",
            cell="B_1and_3and",
            rhythm_class="class_B",
            beats=((0.5, "cell_event_1", "cell_soft_hold"), (2.5, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="airy_one_and_start_color",
            tags=base_tags + ("two_hit",),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_B_1and_4",
            weight=8.0,
            category="bossa_cell_B_rare",
            cell="B_1and_4",
            rhythm_class="class_B",
            beats=((0.5, "cell_event_1", "cell_soft_hold"), (3.0, "cell_event_2", "cell_soft_hold")),
            density="low_mid",
            function="rare_delayed_landing_color",
            tags=base_tags + ("two_hit", "rare"),
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_B_1and_4and",
            weight=7.0,
            category="bossa_cell_B_rare_4and",
            cell="B_1and_4and",
            rhythm_class="class_B",
            beats=((0.5, "cell_event_1", "cell_soft_hold"), (3.5, "native_4and_color", "cell_soft_hold")),
            density="low_mid",
            function="very_rare_native_current_chord_4and_color",
            tags=base_tags + ("native_4and", "rare"),
            native_4and=True,
            ordinary_body_candidate=True,
        ),
        _candidate(
            name="bossa_piano_cell_B_1and_3_4and",
            weight=8.0,
            category="bossa_cell_B_rare_4and",
            cell="B_1and_3_4and",
            rhythm_class="class_B",
            beats=((0.5, "cell_event_1", "cell_soft_hold"), (2.0, "cell_event_2", "cell_soft_hold"), (3.5, "native_4and_color", "cell_soft_hold")),
            density="medium",
            function="very_rare_light_forward_native_4and_color",
            tags=base_tags + ("native_4and", "three_hit", "rare"),
            native_4and=True,
            ordinary_body_candidate=True,
        ),
    )


def _ordinary_cell_pool() -> tuple[PatternCandidate, ...]:
    return (*_class_a_candidates(), *_class_b_candidates())


def describe_pattern_library(context: dict | None = None) -> dict[str, Any]:
    candidates = tuple(get_pattern_candidates(context, apply_context_policy=False))
    return {
        "style_id": STYLE_ID,
        "library_id": PATTERN_LIBRARY_ID,
        "version": PATTERN_LIBRARY_VERSION,
        "domain": PATTERN_DOMAIN,
        "track_role": TRACK_ROLE,
        "default_onset_mode": DEFAULT_ONSET_MODE,
        "boundary_notes": list(BOUNDARY_NOTES),
        "candidate_count": len(candidates),
        "class_A_candidate_count": sum(1 for candidate in candidates if candidate.metadata.get("rhythm_class") == "class_A"),
        "class_B_candidate_count": sum(1 for candidate in candidates if candidate.metadata.get("rhythm_class") == "class_B"),
        "core_candidate_count": sum(1 for candidate in candidates if candidate.metadata.get("rhythm_class") == "core_batida"),
        "candidates": [candidate.to_debug_dict() for candidate in candidates],
    }


def get_pattern_candidates(context: dict | None = None, *, apply_context_policy: bool = True) -> tuple[PatternCandidate, ...]:
    """Bossa Nova piano pattern candidates.

    v2_6_92 keeps the v2_6_91 Class A/Class B vocabulary and directly
    overwrites the former simple weighting with a V2-native context archetype
    policy.  The policy changes candidate weights and metadata in place; it is
    not a selector, phrase engine, voicing policy, expression numeric layer, or
    bar-first restoration.
    """

    context = dict(context or {})
    duration = float(context.get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return tuple(
            _annotate_archetype(candidate, context, multiplier=1.0, status="dense_harmonic_short_region")
            for candidate in _half_region_phrase_pair_candidates()
        )

    candidates: tuple[PatternCandidate, ...] = (_core_candidate(), *_ordinary_cell_pool())
    if not apply_context_policy:
        return candidates

    archetype = _resolve_bossa_groove_archetype(context)
    if _is_opening_core_anchor_context(context):
        return (_annotate_policy(_core_candidate(), context, multiplier=64.0, status="opening_first_two_bars_core_only"),)

    include_core = _should_include_core_reset(context) or archetype["name"] == "core_batida_anchor"
    ordinary = _ordinary_cell_pool()
    if include_core:
        candidates = (_core_candidate(), *ordinary)
    else:
        candidates = ordinary
    return _apply_bossa_context_weighting(candidates, context, archetype=archetype)


def _is_opening_core_anchor_context(context: dict[str, Any]) -> bool:
    region = context.get("region")
    if region is None:
        return False
    try:
        chorus_index = int(getattr(region, "chorus_index", 0) or 0)
        perf_bar = int(getattr(region, "performance_bar_index", 999999) or 0)
        duration = float(getattr(region, "duration_beats", context.get("region_duration_beats", 4.0)) or 4.0)
    except Exception:
        return False
    if duration <= 2.0:
        return False
    return chorus_index == 0 and perf_bar in {0, 1}


def _should_include_core_reset(context: dict[str, Any]) -> bool:
    region = context.get("region")
    if region is None:
        return False
    try:
        if bool(getattr(region, "is_first_bar_of_section", False)) or bool(getattr(region, "is_first_bar_of_chorus", False)):
            return True
        perf_bar = getattr(region, "performance_bar_index", None)
        if perf_bar is not None and int(perf_bar) % 8 == 0:
            return True
    except Exception:
        return False
    return False


def _apply_bossa_context_weighting(
    candidates: Iterable[PatternCandidate],
    context: dict[str, Any],
    *,
    archetype: dict[str, Any] | None = None,
) -> tuple[PatternCandidate, ...]:
    archetype = dict(archetype or _resolve_bossa_groove_archetype(context))
    previous_category, previous_name = _previous_bossa_category_and_name(context)
    recent_entries = _recent_bossa_history_entries(context)
    recent_categories = tuple(str(item.get("category") or "") for item in recent_entries)[-4:] or _recent_bossa_categories(context)
    recent_class_b_count = sum(1 for item in recent_entries[-4:] if item.get("rhythm_class") == "class_B")
    recent_native_4and_count = sum(1 for item in recent_entries[-4:] if bool(item.get("native_4and")))
    recent_three_hit_count = sum(1 for item in recent_entries[-4:] if int(item.get("hit_count") or 0) >= 3)
    recent_one_hit_count = sum(1 for item in recent_entries[-4:] if int(item.get("hit_count") or 0) == 1)
    adjusted: list[PatternCandidate] = []
    for candidate in candidates:
        metadata = dict(candidate.metadata)
        rhythm_class = str(metadata.get("rhythm_class") or "")
        cell = str(metadata.get("rhythmic_cell") or candidate.name)
        hit_count = int(metadata.get("hit_count") or 0)
        multiplier = 1.0
        reasons: list[str] = []
        status = "ordinary_weight"

        class_multiplier = _archetype_class_multiplier(archetype, rhythm_class)
        if abs(class_multiplier - 1.0) > 1e-6:
            multiplier *= class_multiplier
            reasons.append(f"archetype_{archetype['name']}_{rhythm_class}_multiplier")
            status = f"{archetype['name']}_weighted"

        if candidate.name == previous_name:
            multiplier *= 0.20
            reasons.append("avoid_immediate_same_bossa_cell_repeat")
            status = "exact_repeat_guard"
        if rhythm_class == "core_batida" and archetype["name"] != "core_batida_anchor":
            multiplier *= 0.22
            status = "core_available_only_for_reset"
            reasons.append("core_batida_not_looped_mechanically_after_opening")
        if rhythm_class == "class_A":
            if previous_category and "bossa_cell_B" in previous_category:
                multiplier *= 1.35
                reasons.append("class_A_restable_after_class_B")
        if rhythm_class == "class_B":
            if previous_category and "bossa_cell_B" in previous_category:
                multiplier *= 0.08
                status = "class_B_history_guard_strong_downweight"
                reasons.append("avoid_consecutive_class_B")
            elif recent_class_b_count >= 1 or any("bossa_cell_B" in category for category in recent_categories[-2:]):
                multiplier *= 0.22
                status = "class_B_recent_history_guard_downweight"
                reasons.append("keep_class_B_as_occasional_color")
            if recent_class_b_count >= 2:
                multiplier *= 0.12
                status = "class_B_cluster_near_block"
                reasons.append("recent_class_B_cluster_near_block")
        if bool(metadata.get("native_4and")):
            native_multiplier = float(archetype.get("native_4and_multiplier", 0.40))
            multiplier *= native_multiplier
            reasons.append("native_4and_is_current_chord_color_not_anticipation_slot")
            if recent_native_4and_count >= 1 or _recent_native_4and(context):
                multiplier *= 0.18
                status = "native_4and_recent_history_guard_downweight"
                reasons.append("avoid_repeated_native_4and_color")
        if hit_count >= 3:
            three_hit_multiplier = float(archetype.get("three_hit_multiplier", 1.0))
            multiplier *= three_hit_multiplier
            if abs(three_hit_multiplier - 1.0) > 1e-6:
                reasons.append("archetype_three_hit_density_shape")
            if recent_three_hit_count >= 1 or _recent_three_hit(context):
                multiplier *= 0.32
                reasons.append("avoid_consecutive_three_hit_density")
        if hit_count == 1:
            one_hit_multiplier = float(archetype.get("one_hit_multiplier", 1.0))
            multiplier *= one_hit_multiplier
            if abs(one_hit_multiplier - 1.0) > 1e-6:
                reasons.append("archetype_one_hit_breath_shape")
            if recent_one_hit_count >= 2 or _recent_one_hit(context):
                multiplier *= 0.58
                reasons.append("avoid_too_many_one_hit_breath_cells")

        metadata.update(
            {
                "bossa_context_weighting_applied": True,
                "bossa_context_weighting_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
                "bossa_context_weighting_multiplier": round(multiplier, 4),
                "bossa_context_weighting_status": status,
                "bossa_context_weighting_reasons": tuple(reasons),
                "bossa_context_weighting_previous_category": previous_category,
                "bossa_context_weighting_previous_name": previous_name,
                "bossa_context_archetype_policy_active": True,
                "bossa_context_archetype_policy_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
                "bossa_context_archetype": archetype["name"],
                "bossa_context_archetype_reason": archetype.get("reason"),
                "bossa_context_archetype_anticipation_intent": archetype.get("anticipation_intent"),
                "bossa_context_archetype_class_multiplier": round(class_multiplier, 4),
                "bossa_context_history_recent_count": len(recent_entries),
                "bossa_context_history_recent_class_B_count": recent_class_b_count,
                "bossa_context_history_recent_native_4and_count": recent_native_4and_count,
                "bossa_context_history_recent_three_hit_count": recent_three_hit_count,
                "bossa_context_history_recent_one_hit_count": recent_one_hit_count,
                "bossa_context_weighting_contract": (
                    "Bossa Class A/Class B balance is handled by weighting existing style candidates in place. "
                    "The v2_6_92 archetype policy shapes the same candidate pool for core_batida_anchor, steady_batida_flow, breath_space, response_comping, transition_lift, release, and dense_harmonic_marks; "
                    "it does not create a parallel selector, write expression numbers, choose voicing, or restore bar-first phrase templates."
                ),
            }
        )
        adjusted.append(replace(candidate, weight=max(0.0, float(candidate.weight) * multiplier), metadata=metadata))
    return tuple(adjusted)


BOSSA_GROOVE_ARCHETYPES: dict[str, dict[str, Any]] = {
    "core_batida_anchor": {
        "core_multiplier": 7.0,
        "class_A_multiplier": 1.10,
        "class_B_multiplier": 0.20,
        "native_4and_multiplier": 0.28,
        "three_hit_multiplier": 0.92,
        "one_hit_multiplier": 1.00,
        "anticipation_intent": "none",
    },
    "steady_batida_flow": {
        "core_multiplier": 1.00,
        "class_A_multiplier": 1.12,
        "class_B_multiplier": 0.42,
        "native_4and_multiplier": 0.34,
        "three_hit_multiplier": 0.95,
        "one_hit_multiplier": 1.00,
        "anticipation_intent": "internal_phrase_connect",
    },
    "breath_space": {
        "core_multiplier": 1.00,
        "class_A_multiplier": 0.92,
        "class_B_multiplier": 1.35,
        "native_4and_multiplier": 0.22,
        "three_hit_multiplier": 0.34,
        "one_hit_multiplier": 1.55,
        "anticipation_intent": "none",
    },
    "response_comping": {
        "core_multiplier": 1.00,
        "class_A_multiplier": 1.02,
        "class_B_multiplier": 0.95,
        "native_4and_multiplier": 0.38,
        "three_hit_multiplier": 1.02,
        "one_hit_multiplier": 1.00,
        "anticipation_intent": "response_push",
    },
    "transition_lift": {
        "core_multiplier": 1.00,
        "class_A_multiplier": 1.15,
        "class_B_multiplier": 0.45,
        "native_4and_multiplier": 0.42,
        "three_hit_multiplier": 1.26,
        "one_hit_multiplier": 1.00,
        "anticipation_intent": "transition_lift",
    },
    "release": {
        "core_multiplier": 1.00,
        "class_A_multiplier": 0.95,
        "class_B_multiplier": 0.24,
        "native_4and_multiplier": 0.10,
        "three_hit_multiplier": 0.28,
        "one_hit_multiplier": 1.80,
        "anticipation_intent": "none",
    },
    "dense_harmonic_marks": {
        "core_multiplier": 0.25,
        "class_A_multiplier": 0.80,
        "class_B_multiplier": 0.18,
        "native_4and_multiplier": 0.05,
        "three_hit_multiplier": 0.30,
        "one_hit_multiplier": 1.30,
        "anticipation_intent": "none",
    },
}


def _archetype_payload(name: str, *, reason: str) -> dict[str, Any]:
    base = dict(BOSSA_GROOVE_ARCHETYPES.get(name) or BOSSA_GROOVE_ARCHETYPES["steady_batida_flow"])
    base.update({"name": name, "reason": reason, "version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION})
    return base


def _resolve_bossa_groove_archetype(context: dict[str, Any]) -> dict[str, Any]:
    region = context.get("region")
    duration = float(context.get("region_duration_beats", 4.0) or 4.0)
    if duration <= 2.0:
        return _archetype_payload("dense_harmonic_marks", reason="short_chord_region_requires_clarity")
    if _is_opening_core_anchor_context(context):
        return _archetype_payload("core_batida_anchor", reason="opening_first_two_full_bars")
    if region is None:
        return _archetype_payload("steady_batida_flow", reason="no_region_context_default")

    try:
        chorus_index = int(getattr(region, "chorus_index", 0) or 0)
        total_choruses = int(getattr(region, "total_choruses", 1) or 1)
        perf_bar = int(getattr(region, "performance_bar_index", getattr(region, "bar_index", 0)) or 0)
        source_bar = int(getattr(region, "source_bar_index", getattr(region, "bar_index", 0)) or 0)
        section_role = str(getattr(region, "section_role", "") or "").lower()
        phrase = str(getattr(region, "phrase", "") or "").lower()
        is_first_bar_of_section = bool(getattr(region, "is_first_bar_of_section", False))
        is_first_bar_of_chorus = bool(getattr(region, "is_first_bar_of_chorus", False))
        is_last_bar_of_section = bool(getattr(region, "is_last_bar_of_section", False))
        is_last_bar_of_chorus = bool(getattr(region, "is_last_bar_of_chorus", False))
    except Exception:
        return _archetype_payload("steady_batida_flow", reason="region_context_parse_fallback")

    if is_last_bar_of_chorus and chorus_index >= total_choruses - 1:
        return _archetype_payload("release", reason="final_chorus_last_bar_release")
    if is_first_bar_of_chorus or is_first_bar_of_section or perf_bar % 8 == 0:
        return _archetype_payload("core_batida_anchor", reason="section_or_phrase_reset")
    if _recent_context_is_too_dense(context):
        return _archetype_payload("breath_space", reason="recent_cells_need_breath")
    if is_last_bar_of_section or source_bar % 8 in {5, 6, 7}:
        return _archetype_payload("transition_lift", reason="phrase_end_or_cadence_lift")
    if section_role == "bridge" or phrase == "b" or source_bar % 8 in {2, 3}:
        return _archetype_payload("breath_space", reason="bridge_or_mid_phrase_breath")
    if source_bar % 4 in {1, 2}:
        return _archetype_payload("response_comping", reason="light_answer_position")
    return _archetype_payload("steady_batida_flow", reason="ordinary_body_default")


def _archetype_class_multiplier(archetype: dict[str, Any], rhythm_class: str) -> float:
    if rhythm_class == "core_batida":
        return float(archetype.get("core_multiplier", 1.0))
    if rhythm_class == "class_A":
        return float(archetype.get("class_A_multiplier", 1.0))
    if rhythm_class == "class_B":
        return float(archetype.get("class_B_multiplier", 1.0))
    return 1.0


def _annotate_archetype(candidate: PatternCandidate, context: dict[str, Any], *, multiplier: float, status: str) -> PatternCandidate:
    archetype = _resolve_bossa_groove_archetype(context)
    metadata = {
        **dict(candidate.metadata),
        "bossa_context_weighting_applied": True,
        "bossa_context_weighting_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_context_weighting_multiplier": round(float(multiplier), 4),
        "bossa_context_weighting_status": status,
        "bossa_context_weighting_reasons": (archetype.get("reason"),),
        "bossa_context_archetype_policy_active": True,
        "bossa_context_archetype_policy_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_context_archetype": archetype["name"],
        "bossa_context_archetype_reason": archetype.get("reason"),
        "bossa_context_archetype_anticipation_intent": archetype.get("anticipation_intent"),
        "bossa_context_weighting_contract": "v2_6_92 annotates the existing Bossa candidate with context-archetype metadata in place; no parallel selector or bar-first path is introduced.",
    }
    return replace(candidate, weight=float(candidate.weight) * float(multiplier), metadata=metadata)


def _recent_context_is_too_dense(context: dict[str, Any]) -> bool:
    entries = _recent_bossa_history_entries(context)
    if len(entries) < 2:
        return False
    recent = entries[-3:]
    class_b = sum(1 for item in recent if item.get("rhythm_class") == "class_B")
    three_hit = sum(1 for item in recent if int(item.get("hit_count") or 0) >= 3)
    native = sum(1 for item in recent if bool(item.get("native_4and")))
    return class_b >= 2 or three_hit >= 2 or native >= 2


def _history_values(context: dict[str, Any]) -> dict[str, Any]:
    history = context.get("style_pattern_history")
    return history if isinstance(history, dict) else {}


def _recent_bossa_history_entries(context: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    history = _history_values(context)
    entries: list[dict[str, Any]] = []
    for key, value in history.items():
        key_text = str(key)
        if "bossa_nova" not in key_text or "comping_patterns" not in key_text or not key_text.endswith(":recent_bossa_comping"):
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, dict):
                    entries.append(dict(item))
    return tuple(entries[-6:])


def _previous_bossa_category_and_name(context: dict[str, Any]) -> tuple[str | None, str | None]:
    history = _history_values(context)
    category = None
    name = None
    for key, value in history.items():
        key_text = str(key)
        if "bossa_nova" not in key_text or "comping_patterns" not in key_text:
            continue
        if key_text.endswith(":category"):
            category = str(value)
        elif ":" not in key_text.rsplit("comping_patterns", 1)[-1]:
            name = str(value)
    return category, name


def _recent_bossa_categories(context: dict[str, Any]) -> tuple[str, ...]:
    history = _history_values(context)
    categories = [str(value) for key, value in history.items() if "bossa_nova" in str(key) and "comping_patterns" in str(key) and str(key).endswith(":category")]
    return tuple(categories[-4:])


def _recent_native_4and(context: dict[str, Any]) -> bool:
    previous_category, previous_name = _previous_bossa_category_and_name(context)
    text = f"{previous_category or ''} {previous_name or ''}"
    return "4and" in text or "4_and" in text


def _recent_three_hit(context: dict[str, Any]) -> bool:
    _previous_category, previous_name = _previous_bossa_category_and_name(context)
    return bool(previous_name and ("1_2_3and" in previous_name or "1and_3_4and" in previous_name))


def _recent_one_hit(context: dict[str, Any]) -> bool:
    _previous_category, previous_name = _previous_bossa_category_and_name(context)
    return bool(previous_name and (previous_name.endswith("_A_1") or previous_name.endswith("_B_1and")))


def _annotate_policy(candidate: PatternCandidate, context: dict[str, Any], *, multiplier: float, status: str) -> PatternCandidate:
    archetype = _resolve_bossa_groove_archetype(context)
    metadata = {
        **dict(candidate.metadata),
        "bossa_context_weighting_applied": True,
        "bossa_context_weighting_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_context_weighting_multiplier": round(float(multiplier), 4),
        "bossa_context_weighting_status": status,
        "bossa_context_weighting_reasons": ("opening_first_two_bars_force_core_identity",),
        "bossa_context_archetype_policy_active": True,
        "bossa_context_archetype_policy_version": BOSSA_CONTEXT_ARCHETYPE_POLICY_VERSION,
        "bossa_context_archetype": archetype["name"],
        "bossa_context_archetype_reason": archetype.get("reason"),
        "bossa_context_archetype_anticipation_intent": archetype.get("anticipation_intent"),
        "bossa_context_weighting_contract": "Opening first two Bossa bars expose only the sole core_batida identity anchor when the ChordRegion is a full four-beat region.",
    }
    return replace(candidate, weight=float(candidate.weight) * float(multiplier), metadata=metadata)
