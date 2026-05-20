from __future__ import annotations

from typing import Any, Iterable

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

STYLE_ID = "medium_swing"
PATTERN_LIBRARY_ID = "medium_swing.piano_comping"
PATTERN_LIBRARY_VERSION = "v2_6_56"
CANDIDATE_LOOKUP_POLICY_VERSION = "v2_6_57"
WEIGHT_CALIBRATION_POLICY_VERSION = "v2_6_58"
EXPRESSION_HINT_HANDOFF_POLICY_VERSION = "v2_6_63"
NO_4AND_DELAYED_TAIL_POLICY_VERSION = "v2_6_66"
OPTIONAL_FILL_VARIATION_VOCABULARY_VERSION = "v2_6_71"
PATTERN_DOMAIN = "comping"
TRACK_ROLE = "piano_harmonic_comping"
DEFAULT_ONSET_MODE = "simultaneous_onset"
BOUNDARY_NOTES = (
    "pitchless",
    "style_owned",
    "region_length_aware",
    "region_local_beats",
    "no_bar_first_two_chord_bar_logic",
    "no_voicing_logic",
    "no_final_expression_values",
    "semantic_expression_hint_handoff_v2_6_63",
    "hold_hints_resolved_by_expression_as_hold_until_next_touch",
    "optional_fill_variation_vocabulary_guarded_by_history_scorer_v2_6_71",
)

EXPRESSION_PROFILE_BY_SEMANTIC_HINT = {
    "soft_hold": "comp_medium",
    "light_stab": "comp_short",
    "accent_stab": "comp_accent",
    "accent_hold": "comp_accent_hold",
    "backbeat_hold": "comp_backbeat_hold",
    "final_hold": "comp_final_hold",
}


def _region_length_family(duration_beats: float) -> str:
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


def _comping_metadata(
    *,
    density: str,
    cell: str,
    function: str,
    region_length_beats: float,
    rhythm_family: str,
    phrase_role: str,
    tail_push_risk: str = "none",
    requires_region_start_anchor: bool = False,
    context_gate: str = "generic",
    activation: str = "active_runtime",
    weight_calibration_class: str = "stable",
) -> dict[str, Any]:
    region_length = float(region_length_beats)
    family = _region_length_family(region_length)
    return {
        "density": density,
        "density_class": density,
        "style_id": STYLE_ID,
        "pattern_domain": PATTERN_DOMAIN,
        "pattern_library_id": PATTERN_LIBRARY_ID,
        "pattern_library_version": PATTERN_LIBRARY_VERSION,
        "track_role": TRACK_ROLE,
        "region_length_beats": region_length,
        "region_length_family": family,
        # Compatibility key: now means ChordRegion length family, not bar-level shape.
        "region_shape": family,
        "rhythmic_cell": cell,
        "pattern_function": function,
        "rhythm_family": rhythm_family,
        "phrase_role": phrase_role,
        "tail_push_risk": tail_push_risk,
        "requires_region_start_anchor": bool(requires_region_start_anchor),
        "context_gate": context_gate,
        "activation": activation,
        "candidate_lookup_policy_version": CANDIDATE_LOOKUP_POLICY_VERSION,
        "candidate_lookup_policy": "region_length_aware",
        "candidate_lookup_key": family,
        "weight_calibration_policy_version": WEIGHT_CALIBRATION_POLICY_VERSION,
        "weight_calibration_policy": "stable_primary_offbeat_secondary_active_and_tail_push_controlled",
        "weight_calibration_class": weight_calibration_class,
        "candidate_lookup_contract": "ChordRegion duration selects region-local pattern family before weighted sampling; no bar-first/two-chord-bar routing.",
        "onset_mode": DEFAULT_ONSET_MODE,
        "voicing_boundary": "pattern_is_pitchless",
        "expression_boundary": "pattern_carries_semantic_hint_not_final_values",
        "expression_hint_handoff_policy_version": EXPRESSION_HINT_HANDOFF_POLICY_VERSION,
        "expression_hint_contract": "Pattern carries semantic hints only; ExpressionResolver maps hold hints to hold-until-next-touch durations, clamped to the current ChordRegion.",
        "region_first_short_region_route": True,
        "no_4and_delayed_tail_static_policy_version": NO_4AND_DELAYED_TAIL_POLICY_VERSION,
        "no_4and_delayed_tail_idiom": bool(tail_push_risk != "high" and any(token in rhythm_family or token in cell for token in ("delayed", "tail", "backbeat"))),
        "time_reference": "region_local_beats",
    }


def _optional_fill_variation_metadata(*, role: str, activation_context: str) -> dict[str, Any]:
    return {
        "optional_fill_variation_vocabulary_candidate": True,
        "optional_fill_variation_vocabulary_version": OPTIONAL_FILL_VARIATION_VOCABULARY_VERSION,
        "optional_fill_variation_role": role,
        "optional_fill_variation_activation": "guarded_low_frequency_v2_6_71",
        "optional_fill_variation_activation_context": activation_context,
        "optional_fill_variation_contract": (
            "Optional fill/variation cells are pitchless ChordRegion-local candidates with very low base weight; "
            "StyleProfile reweights them by region context and the v2_6_67 history scorer still prevents consecutive active/fill/busy/push behavior."
        ),
    }


def _event(
    beat: float,
    *,
    event_role: str,
    semantic_expression_hint: str,
    can_anticipate: bool = False,
    required: bool = False,
):
    return event_spec(
        track="piano",
        beat=beat,
        role="harmonic",
        gesture=simultaneous_onset(),
        expression_hint=EXPRESSION_PROFILE_BY_SEMANTIC_HINT[semantic_expression_hint],
        metadata={
            "event_role": event_role,
            "semantic_expression_hint": semantic_expression_hint,
            "can_anticipate": bool(can_anticipate),
            "required": bool(required),
            "time_reference": "region_local_beats",
            "expression_hint_handoff_policy_version": EXPRESSION_HINT_HANDOFF_POLICY_VERSION,
        },
    )


def _tail(beats: Iterable[float]) -> TailPolicy:
    return TailPolicy.from_local_beats(tuple(float(beat) for beat in beats))


def _movable(reason: str) -> Beat1Movability:
    return Beat1Movability(movable=True, reason=reason)


def _not_movable(reason: str) -> Beat1Movability:
    return Beat1Movability(movable=False, reason=reason)


def describe_pattern_library(context: dict | None = None) -> dict[str, Any]:
    candidates = tuple(get_pattern_candidates(context))
    return {
        "style_id": STYLE_ID,
        "library_id": PATTERN_LIBRARY_ID,
        "version": PATTERN_LIBRARY_VERSION,
        "domain": PATTERN_DOMAIN,
        "track_role": TRACK_ROLE,
        "default_onset_mode": DEFAULT_ONSET_MODE,
        "boundary_notes": list(BOUNDARY_NOTES),
        "candidate_count": len(candidates),
        "candidates": [candidate.to_debug_dict() for candidate in candidates],
    }


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Medium swing piano comping candidates.

    v2_6_58 keeps the v2_6_56 vocabulary baseline and v2_6_57
    ChordRegion-length-aware lookup policy, then calibrates stable/offbeat/active weights in the existing style-owned
    pattern source.  Candidate routing is region-first: 1/2/4-beat regions
    select their own region-local cells before weighted sampling; this does
    not introduce a parallel bar-first/two-chord-bar path.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    family = _region_length_family(duration)
    if family == "one_beat_region":
        return _one_beat_region_candidates(duration)
    if family == "two_beat_region":
        return _two_beat_region_candidates(duration)
    if family == "three_beat_region":
        return _three_beat_region_candidates(duration)
    if family == "five_beat_region":
        return _five_beat_region_candidates(duration)
    if family == "long_region":
        return _long_region_candidates(duration)
    return _four_beat_region_candidates(duration)


def _four_beat_region_candidates(duration: float = 4.0) -> tuple[PatternCandidate, ...]:
    active = (
        PatternCandidate(
            name="medium_swing_piano_anchor_1",
            weight=1.1,
            category="stable_comping_anchor",
            events=(_event(0.0, event_role="anchor", semantic_expression_hint="soft_hold", can_anticipate=True, required=True),),
            tail_policy=_tail((0.0,)),
            beat1_movability=_movable("region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="1", function="anchor", region_length_beats=duration, rhythm_family="stable", phrase_role="statement", requires_region_start_anchor=True, weight_calibration_class="stable"),
            tags=("swing", "piano", "stable", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_charleston_1_2and",
            weight=1.0,
            category="swing_comping_charleston",
            events=(
                _event(0.0, event_role="anchor", semantic_expression_hint="accent_hold", can_anticipate=True, required=True),
                _event(1.5, event_role="answer", semantic_expression_hint="light_stab"),
            ),
            tail_policy=_tail((0.0, 1.5)),
            beat1_movability=_movable("charleston_region_start_can_be_anticipated_later"),
            metadata=_comping_metadata(density="medium", cell="1_2and", function="charleston_answer", region_length_beats=duration, rhythm_family="charleston", phrase_role="statement_answer", requires_region_start_anchor=True, weight_calibration_class="stable"),
            tags=("swing", "piano", "charleston", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_1_3and_answer",
            weight=0.8,
            category="swing_comping_answer",
            events=(
                _event(0.0, event_role="anchor", semantic_expression_hint="soft_hold", can_anticipate=True, required=True),
                _event(2.5, event_role="answer", semantic_expression_hint="light_stab"),
            ),
            tail_policy=_tail((0.0, 2.5)),
            beat1_movability=_movable("region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="medium", cell="1_3and", function="answer", region_length_beats=duration, rhythm_family="stable_answer", phrase_role="statement_answer", requires_region_start_anchor=True, weight_calibration_class="stable"),
            tags=("swing", "piano", "answer", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_backbeat_2_4",
            weight=0.5,
            category="swing_comping_backbeat",
            events=(
                _event(1.0, event_role="backbeat_support", semantic_expression_hint="backbeat_hold"),
                _event(3.0, event_role="tail_support", semantic_expression_hint="backbeat_hold"),
            ),
            tail_policy=_tail((1.0, 3.0)),
            beat1_movability=_not_movable("no_region_start_harmonic_event_in_this_cell"),
            metadata=_comping_metadata(density="medium", cell="2_4", function="backbeat_answer", region_length_beats=duration, rhythm_family="backbeat", phrase_role="answer_tail", weight_calibration_class="stable"),
            tags=("swing", "piano", "backbeat", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_light_2and_only",
            weight=0.35,
            category="sparse_offbeat_answer",
            events=(_event(1.5, event_role="answer", semantic_expression_hint="light_stab"),),
            tail_policy=_tail((1.5,)),
            beat1_movability=_not_movable("no_region_start_harmonic_event_in_this_cell"),
            metadata=_comping_metadata(density="sparse", cell="2and", function="light_offbeat_answer", region_length_beats=duration, rhythm_family="offbeat_conversation", phrase_role="answer", weight_calibration_class="offbeat"),
            tags=("swing", "piano", "sparse", "audible_v208", "comping"),
        ),
    )
    region_lookup_expansion = (
        _four_beat_region_lookup_candidate("medium_swing_piano_anchor_3", 0.20, "3", "delayed_anchor", ((2.0, "delayed_anchor", "soft_hold"),), "stable", "delayed_statement", density="sparse"),
        _four_beat_region_lookup_candidate("medium_swing_piano_anchor_1_3", 0.90, "1_3", "stable_two_hit", ((0.0, "anchor", "soft_hold"), (2.0, "support", "backbeat_hold")), "stable", "statement", density="medium", requires_anchor=True),
        _four_beat_region_lookup_candidate("medium_swing_piano_1_4_tail", 0.25, "1_4", "tail_support", ((0.0, "anchor", "soft_hold"), (3.0, "tail_support", "backbeat_hold")), "stable_tail", "statement_tail", density="medium", requires_anchor=True),
        _four_beat_region_lookup_candidate("medium_swing_piano_1_2and_4", 0.22, "1_2and_4", "charleston_tail_no_4and", ((0.0, "anchor", "accent_hold"), (1.5, "answer", "light_stab"), (3.0, "tail_support", "backbeat_hold")), "charleston_tail", "active_statement", density="active", requires_anchor=True),
        _four_beat_region_lookup_candidate("medium_swing_piano_reverse_charleston_1and_3", 0.38, "1and_3", "reverse_charleston_answer", ((0.5, "pickup_answer", "light_stab"), (2.0, "support", "soft_hold")), "offbeat_conversation", "answer", density="medium"),
        _four_beat_region_lookup_candidate("medium_swing_piano_2and_4_answer", 0.45, "2and_4", "offbeat_tail_answer_no_4and", ((1.5, "answer", "light_stab"), (3.0, "tail_support", "backbeat_hold")), "offbeat_tail", "answer_tail", density="medium"),
        _four_beat_region_lookup_candidate("medium_swing_piano_2_3and_answer", 0.28, "2_3and", "delayed_answer", ((1.0, "delayed_support", "backbeat_hold"), (2.5, "answer", "light_stab")), "delayed_answer", "answer", density="medium"),
        _four_beat_region_lookup_candidate("medium_swing_piano_1_4and_rare_push", 0.015, "1_4and", "rare_tail_push", ((0.0, "anchor", "soft_hold"), (3.5, "tail_push", "accent_stab")), "tail_push", "rare_push", density="rare_push", tail_push_risk="high", requires_anchor=True),
        _four_beat_region_lookup_candidate("medium_swing_piano_1_2and_4and_rare_push", 0.006, "1_2and_4and", "rare_charleston_tail_push", ((0.0, "anchor", "accent_hold"), (1.5, "answer", "light_stab"), (3.5, "tail_push", "accent_stab")), "tail_push", "rare_push", density="rare_push", tail_push_risk="high", requires_anchor=True),
    )
    optional_fill_variation = (
        PatternCandidate(
            name="medium_swing_piano_optional_variation_1_2and_3and",
            weight=0.075,
            category="optional_active_variation",
            events=(
                _event(0.0, event_role="anchor", semantic_expression_hint="accent_hold", can_anticipate=True, required=True),
                _event(1.5, event_role="answer", semantic_expression_hint="light_stab"),
                _event(2.5, event_role="answer", semantic_expression_hint="light_stab"),
            ),
            tail_policy=_tail((0.0, 1.5, 2.5)),
            beat1_movability=_movable("optional_variation_region_start_can_be_anticipated_later"),
            metadata={
                **_comping_metadata(
                    density="active",
                    cell="1_2and_3and",
                    function="optional_active_variation_no_4and",
                    region_length_beats=duration,
                    rhythm_family="optional_variation_no_4and",
                    phrase_role="variation",
                    requires_region_start_anchor=True,
                    activation="optional_fill_variation_vocabulary_v2_6_71",
                    weight_calibration_class="active",
                ),
                **_optional_fill_variation_metadata(role="variation", activation_context="generic_light_conversation_or_phrase_motion"),
            },
            tags=("swing", "piano", "optional_fill_variation", "variation", "no_4and", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_optional_fill_2and_4_4and",
            weight=0.018,
            category="optional_transition_fill_tail_push",
            events=(
                _event(1.5, event_role="answer", semantic_expression_hint="light_stab"),
                _event(3.0, event_role="tail_support", semantic_expression_hint="backbeat_hold"),
                _event(3.5, event_role="tail_push", semantic_expression_hint="accent_stab"),
            ),
            tail_policy=_tail((1.5, 3.0, 3.5)),
            beat1_movability=_not_movable("optional_fill_has_no_region_start_anchor"),
            metadata={
                **_comping_metadata(
                    density="active",
                    cell="2and_4_4and",
                    function="optional_transition_fill_tail_push",
                    region_length_beats=duration,
                    rhythm_family="optional_fill_tail_push",
                    phrase_role="turnaround_fill",
                    tail_push_risk="high",
                    activation="optional_fill_variation_vocabulary_v2_6_71",
                    weight_calibration_class="tail_push",
                ),
                **_optional_fill_variation_metadata(role="transition_fill", activation_context="section_end_turnaround_or_dominant_resolution_only"),
            },
            tags=("swing", "piano", "optional_fill_variation", "fill", "tail_push", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_optional_busy_1and_2and_3and_4",
            weight=0.004,
            category="optional_busy_fill_no_4and",
            events=(
                _event(0.5, event_role="pickup_answer", semantic_expression_hint="light_stab"),
                _event(1.5, event_role="answer", semantic_expression_hint="light_stab"),
                _event(2.5, event_role="answer", semantic_expression_hint="light_stab"),
                _event(3.0, event_role="tail_support", semantic_expression_hint="backbeat_hold"),
            ),
            tail_policy=_tail((0.5, 1.5, 2.5, 3.0)),
            beat1_movability=_not_movable("optional_busy_fill_has_no_region_start_anchor"),
            metadata={
                **_comping_metadata(
                    density="busy",
                    cell="1and_2and_3and_4",
                    function="optional_busy_fill_no_4and",
                    region_length_beats=duration,
                    rhythm_family="optional_busy_fill_no_4and",
                    phrase_role="section_fill",
                    activation="optional_fill_variation_vocabulary_v2_6_71",
                    weight_calibration_class="busy",
                ),
                **_optional_fill_variation_metadata(role="busy_fill", activation_context="explicit_high_energy_or_phrase_end_only"),
            },
            tags=("swing", "piano", "optional_fill_variation", "busy", "no_4and", "comping"),
        ),
    )
    return active + region_lookup_expansion + optional_fill_variation


def _infer_weight_calibration_class(density: str, rhythm_family: str, tail_push_risk: str = "none") -> str:
    if tail_push_risk == "high" or "push" in rhythm_family:
        return "tail_push"
    if density == "busy" or "busy" in rhythm_family:
        return "busy"
    if density == "active":
        return "active"
    if rhythm_family in {"offbeat_conversation", "offbeat_tail", "delayed_answer"}:
        return "offbeat"
    if rhythm_family in {"short_region_answer", "short_region_offbeat"}:
        return "offbeat"
    return "stable"


def _four_beat_region_lookup_candidate(
    name: str,
    weight: float,
    cell: str,
    function: str,
    specs: tuple[tuple[float, str, str], ...],
    rhythm_family: str,
    phrase_role: str,
    *,
    density: str,
    tail_push_risk: str = "none",
    requires_anchor: bool = False,
    weight_calibration_class: str | None = None,
) -> PatternCandidate:
    beats = tuple(item[0] for item in specs)
    return PatternCandidate(
        name=name,
        weight=float(weight),
        category=f"region_lookup_{rhythm_family}",
        events=tuple(
            _event(beat, event_role=role, semantic_expression_hint=hint, can_anticipate=(beat == 0.0), required=(beat == 0.0 and requires_anchor))
            for beat, role, hint in specs
        ),
        tail_policy=_tail(beats),
        beat1_movability=_movable("region_lookup_start_anchor_can_be_anticipated_later") if 0.0 in beats else _not_movable("no_region_start_harmonic_event_in_this_cell"),
        metadata=_comping_metadata(
            density=density,
            cell=cell,
            function=function,
            region_length_beats=4.0,
            rhythm_family=rhythm_family,
            phrase_role=phrase_role,
            tail_push_risk=tail_push_risk,
            requires_region_start_anchor=requires_anchor,
            activation="active_region_length_lookup_v2_6_57" if weight > 0.0 else "inactive_vocabulary_baseline",
            weight_calibration_class=weight_calibration_class or _infer_weight_calibration_class(density, rhythm_family, tail_push_risk),
        ),
        tags=("swing", "piano", "region_length_lookup", "region_length_aware", "comping"),
    )


def _two_beat_region_candidates(duration: float = 2.0) -> tuple[PatternCandidate, ...]:
    active = (
        PatternCandidate(
            name="medium_swing_piano_two_beat_region_start_anchor",
            weight=2.4,
            category="short_region_anchor",
            events=(_event(0.0, event_role="anchor", semantic_expression_hint="soft_hold", can_anticipate=True, required=True),),
            tail_policy=_tail((0.0,)),
            beat1_movability=_movable("short_region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="start", function="short_region_anchor", region_length_beats=duration, rhythm_family="short_region_anchor", phrase_role="short_region_support", requires_region_start_anchor=True, weight_calibration_class="stable"),
            tags=("swing", "piano", "two_beat_region", "region_start", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_two_beat_region_start_local2and",
            weight=0.35,
            category="short_region_answer",
            events=(
                _event(0.0, event_role="anchor", semantic_expression_hint="light_stab", can_anticipate=True, required=True),
                _event(1.5, event_role="answer", semantic_expression_hint="light_stab"),
            ),
            tail_policy=_tail((0.0, 1.5)),
            beat1_movability=_movable("short_region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="medium", cell="start_local2and", function="short_region_offbeat_answer", region_length_beats=duration, rhythm_family="short_region_answer", phrase_role="short_region_answer", requires_region_start_anchor=True, weight_calibration_class="offbeat"),
            tags=("swing", "piano", "two_beat_region", "offbeat", "audible_v208", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_two_beat_region_local2_only",
            weight=0.55,
            category="short_region_light_push",
            events=(_event(1.0, event_role="delayed_support", semantic_expression_hint="light_stab"),),
            tail_policy=_tail((1.0,)),
            beat1_movability=_not_movable("no_short_region_start_harmonic_event"),
            metadata=_comping_metadata(density="sparse", cell="local2", function="short_region_light_push", region_length_beats=duration, rhythm_family="short_region_delayed", phrase_role="short_region_answer", weight_calibration_class="stable"),
            tags=("swing", "piano", "two_beat_region", "light", "audible_v208", "comping"),
        ),
    )
    region_lookup_expansion = (
        _short_region_lookup_candidate("medium_swing_piano_two_beat_region_start_local2", 0.35, 2.0, "start_local2", ((0.0, "anchor", "soft_hold"), (1.0, "support", "backbeat_hold")), "short_region_stable", density="medium"),
        _short_region_lookup_candidate("medium_swing_piano_two_beat_region_start_local1and", 0.08, 2.0, "start_local1and", ((0.0, "anchor", "soft_hold"), (0.5, "answer", "light_stab")), "short_region_answer", density="medium"),
        _short_region_lookup_candidate("medium_swing_piano_two_beat_region_local1and_only", 0.03, 2.0, "local1and", ((0.5, "answer", "light_stab"),), "short_region_offbeat", density="sparse"),
    )
    return active + region_lookup_expansion


def _short_region_lookup_candidate(name: str, weight: float, duration: float, cell: str, specs: tuple[tuple[float, str, str], ...], rhythm_family: str, *, density: str) -> PatternCandidate:
    beats = tuple(item[0] for item in specs)
    return PatternCandidate(
        name=name,
        weight=float(weight),
        category=f"region_lookup_{rhythm_family}",
        events=tuple(_event(beat, event_role=role, semantic_expression_hint=hint, can_anticipate=(beat == 0.0), required=(beat == 0.0)) for beat, role, hint in specs),
        tail_policy=_tail(beats),
        beat1_movability=_movable("region_lookup_short_region_start_anchor_can_be_anticipated_later") if 0.0 in beats else _not_movable("no_short_region_start_harmonic_event"),
        metadata=_comping_metadata(density=density, cell=cell, function=f"{cell}_region_lookup", region_length_beats=duration, rhythm_family=rhythm_family, phrase_role="short_region_vocabulary", activation="active_region_length_lookup_v2_6_57", weight_calibration_class=_infer_weight_calibration_class(density, rhythm_family)),
        tags=("swing", "piano", "region_length_lookup", _region_length_family(duration), "comping"),
    )


def _one_beat_region_candidates(duration: float = 1.0) -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_piano_one_beat_region_start_anchor",
            weight=2.0,
            category="very_short_region_anchor",
            events=(_event(0.0, event_role="anchor", semantic_expression_hint="light_stab", can_anticipate=True, required=True),),
            tail_policy=_tail((0.0,)),
            beat1_movability=_movable("one_beat_region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="start", function="one_beat_region_anchor", region_length_beats=duration, rhythm_family="one_beat_anchor", phrase_role="very_short_region_support", requires_region_start_anchor=True, weight_calibration_class="stable"),
            tags=("swing", "piano", "one_beat_region", "region_start", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_one_beat_region_local_and",
            weight=0.02,
            category="region_lookup_one_beat_offbeat",
            events=(_event(0.5, event_role="answer", semantic_expression_hint="light_stab"),),
            tail_policy=_tail((0.5,)),
            beat1_movability=_not_movable("no_one_beat_region_start_harmonic_event"),
            metadata=_comping_metadata(density="sparse", cell="local_and", function="one_beat_region_light_offbeat", region_length_beats=duration, rhythm_family="one_beat_offbeat", phrase_role="very_short_region_answer", activation="active_region_length_lookup_v2_6_57", weight_calibration_class="offbeat"),
            tags=("swing", "piano", "one_beat_region", "region_length_lookup", "comping"),
        ),
        PatternCandidate(
            name="medium_swing_piano_one_beat_region_rest_if_covered",
            weight=0.0,
            category="inactive_one_beat_rest_if_covered",
            events=(),
            tail_policy=_tail(()),
            beat1_movability=_not_movable("no_harmonic_event_in_rest_if_covered_cell"),
            metadata=_comping_metadata(density="inactive", cell="rest_if_covered", function="one_beat_region_rest_if_covered", region_length_beats=duration, rhythm_family="one_beat_rest_if_covered", phrase_role="space", context_gate="covered_by_neighboring_regions_only", activation="inactive_vocabulary_baseline", weight_calibration_class="inactive"),
            tags=("swing", "piano", "one_beat_region", "rest_if_covered", "inactive_vocabulary", "comping"),
        ),
    )


def _three_beat_region_candidates(duration: float = 3.0) -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_piano_three_beat_region_start_anchor",
            weight=1.0,
            category="future_meter_region_anchor",
            events=(_event(0.0, event_role="anchor", semantic_expression_hint="soft_hold", can_anticipate=True, required=True),),
            tail_policy=_tail((0.0,)),
            beat1_movability=_movable("three_beat_region_start_anchor_can_be_anticipated_later"),
            metadata=_comping_metadata(density="sparse", cell="start", function="three_beat_region_anchor_placeholder", region_length_beats=duration, rhythm_family="future_meter_anchor", phrase_role="support", requires_region_start_anchor=True),
            tags=("swing", "piano", "three_beat_region", "future_meter_safe", "comping"),
        ),
    )


def _five_beat_region_candidates(duration: float = 5.0) -> tuple[PatternCandidate, ...]:
    return _four_beat_region_candidates(4.0) + (
        PatternCandidate(
            name="medium_swing_piano_five_beat_region_tail_support",
            weight=0.0,
            category="inactive_future_meter_region_tail",
            events=(_event(4.0, event_role="tail_support", semantic_expression_hint="backbeat_hold"),),
            tail_policy=_tail((4.0,)),
            beat1_movability=_not_movable("no_region_start_harmonic_event_in_tail_support_cell"),
            metadata=_comping_metadata(density="inactive", cell="local5_tail_support", function="five_beat_region_tail_support_placeholder", region_length_beats=duration, rhythm_family="future_meter_tail", phrase_role="tail", activation="inactive_vocabulary_baseline"),
            tags=("swing", "piano", "five_beat_region", "future_meter_safe", "inactive_vocabulary", "comping"),
        ),
    )


def _long_region_candidates(duration: float) -> tuple[PatternCandidate, ...]:
    return _four_beat_region_candidates(min(duration, 4.0))


def get_voicing_tuning_anchor_only_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Temporary voicing-isolation piano pattern source.

    This source intentionally emits exactly one piano harmonic event at the
    start of every harmonic region. It is used by the ``medium_swing_voicing_tuning``
    profile so voicing choices can be audited and listened to without rhythmic
    comping variation. It must not replace the normal Medium Swing comping
    vocabulary.
    """

    duration = float((context or {}).get("region_duration_beats", 4.0))
    return (
        PatternCandidate(
            name="medium_swing_voicing_tuning_region_start_anchor",
            weight=1.0,
            category="voicing_tuning_anchor_only",
            events=(
                event_spec(
                    track="piano",
                    beat=0.0,
                    role="harmonic",
                    gesture=simultaneous_onset(metadata={"tuning_mode": "voicing_isolation"}),
                    expression_hint="comp_final_hold",
                    metadata={"event_role": "anchor", "semantic_expression_hint": "final_hold", "required": True, "time_reference": "region_local_beats", "expression_hint_handoff_policy_version": EXPRESSION_HINT_HANDOFF_POLICY_VERSION},
                ),
            ),
            tail_policy=_tail((0.0,)),
            beat1_movability=_not_movable("voicing_tuning_keeps_all_events_on_region_start"),
            metadata={
                **_comping_metadata(density="voicing_isolation", cell="region_start_only", function="voicing_tuning_anchor", region_length_beats=duration, rhythm_family="voicing_tuning_anchor", phrase_role="voicing_tuning", requires_region_start_anchor=True),
                "tuning_mode": "voicing_isolation",
                "normal_style_default": False,
                "purpose": "freeze_pattern_choice_to_region_start_for_voicing_audit",
            },
            tags=("swing", "piano", "voicing_tuning", "region_start", "comping"),
        ),
    )
