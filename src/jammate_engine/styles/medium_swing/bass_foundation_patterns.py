from __future__ import annotations

from dataclasses import dataclass

from jammate_engine.core.harmony.harmonic_context import classify_functional_motion
from jammate_engine.core.pattern_runtime import PatternCandidate, TailPolicy, event_spec


WALK_META = {"length_profile": "walking_quarter", "register_low": 26, "register_high": 48}
TWO_FEEL_META = {"length_profile": "two_feel_half", "register_low": 26, "register_high": 48}


@dataclass(frozen=True)
class WalkingSkeletonSpec:
    """Style-owned Medium Swing walking vocabulary item.

    The three weights are inherited from the previous project's v6.2.x
    ThreeBeatSkeleton table. They are style preference data, not core logic.
    Core BassFoundation generation reads this metadata and performs the runtime
    zone/lane/connector choice.
    """

    identifier: str
    group: str
    degrees: tuple[str, str, str]
    weight_low: float
    weight_mid: float
    weight_high: float
    allow_repetition: bool = False


# Complete previous-project ordinary walking skeleton table, kept as
# Medium Swing style vocabulary. Do not move this to vocabulary/: vocabulary/
# is reserved for melodic foreground / solo material in V2.
THREE_BEAT_SKELETONS: tuple[WalkingSkeletonSpec, ...] = (
    WalkingSkeletonSpec("C01_R_Third_Fifth", "chord", ("R", "Third", "Fifth"), 14.00, 12.00, 10.67),
    WalkingSkeletonSpec("C02_R_Fifth_Third", "chord", ("R", "Fifth", "Third"), 9.50, 9.00, 8.50),
    WalkingSkeletonSpec("C03_R_R_Fifth", "chord", ("R", "R", "Fifth"), 9.56, 9.00, 8.44, allow_repetition=True),
    WalkingSkeletonSpec("C04_R_Fifth_R", "chord", ("R", "Fifth", "R"), 4.00, 4.00, 3.60, allow_repetition=True),
    WalkingSkeletonSpec("C05_R_R_Third", "chord", ("R", "R", "Third"), 10.12, 9.00, 8.44, allow_repetition=True),
    WalkingSkeletonSpec("C06_R_Third_R", "chord", ("R", "Third", "R"), 3.00, 3.00, 2.70, allow_repetition=True),
    WalkingSkeletonSpec("C07_R_Fifth_Seventh", "chord", ("R", "Fifth", "Seventh"), 8.36, 9.00, 10.29),
    WalkingSkeletonSpec("C08_R_Seventh_Fifth", "chord", ("R", "Seventh", "Fifth"), 9.75, 12.00, 15.00),
    WalkingSkeletonSpec("C09_R_Third_Seventh", "chord", ("R", "Third", "Seventh"), 5.25, 6.00, 6.75),
    WalkingSkeletonSpec("C10_R_Seventh_Third", "chord", ("R", "Seventh", "Third"), 4.88, 6.00, 7.12),
    WalkingSkeletonSpec("C11_R_R_Seventh", "chord", ("R", "R", "Seventh"), 7.50, 9.00, 10.50, allow_repetition=True),
    WalkingSkeletonSpec("C12_R_Seventh_R", "chord", ("R", "Seventh", "R"), 2.70, 3.00, 3.00, allow_repetition=True),
    WalkingSkeletonSpec("S01_R_Second_Third", "scale", ("R", "Second", "Third"), 12.50, 10.00, 8.75),
    WalkingSkeletonSpec("S02_R_Third_Fourth", "scale", ("R", "Third", "Fourth"), 11.88, 10.00, 9.38),
    WalkingSkeletonSpec("S03_R_Fourth_Fifth", "scale", ("R", "Fourth", "Fifth"), 7.29, 6.00, 5.57),
    WalkingSkeletonSpec("S04_R_Fifth_Sixth", "scale", ("R", "Fifth", "Sixth"), 4.57, 4.00, 4.00),
    WalkingSkeletonSpec("S05_R_Sixth_Seventh", "scale", ("R", "Sixth", "Seventh"), 2.00, 2.00, 2.33),
    WalkingSkeletonSpec("S06_R_Third_Second", "scale", ("R", "Third", "Second"), 4.00, 4.00, 4.50),
    WalkingSkeletonSpec("S07_R_Fourth_Third", "scale", ("R", "Fourth", "Third"), 2.00, 2.00, 2.14),
    WalkingSkeletonSpec("S08_R_Fifth_Fourth", "scale", ("R", "Fifth", "Fourth"), 1.86, 2.00, 2.29),
    WalkingSkeletonSpec("S09_R_Sixth_Fifth", "scale", ("R", "Sixth", "Fifth"), 1.86, 2.00, 2.43),
    WalkingSkeletonSpec("S10_R_Seventh_Sixth", "scale", ("R", "Seventh", "Sixth"), 7.31, 9.00, 11.25),
)


def get_bass_foundation_policy() -> dict:
    """Medium swing BassFoundation policy.

    Style declares preference numbers. Core owns the target-to-target planning,
    octave/register choice, lane selection, and connector realization.
    """

    return {
        "enabled": True,
        "register_low": 26,
        "register_high": 48,
        "register_center": 37,
        "max_body_span": 12,
        "max_region_span": 12,
        "max_segment_span": 16,
        "max_preferred_leap": 7,
        "same_note_penalty": 30.0,
        "repeated_root_fifth_penalty": 8.0,
        "direction_bias_weight": 2.0,
        "lane_weights_by_zone": {
            "very_low": {"upper": 100.0, "lower": 0.0, "mixed": 0.0},
            "low": {"upper": 82.0, "lower": 13.0, "mixed": 5.0},
            "middle": {"upper": 47.0, "lower": 47.0, "mixed": 6.0},
            "high": {"upper": 13.0, "lower": 82.0, "mixed": 5.0},
            "very_high": {"upper": 0.0, "lower": 100.0, "mixed": 0.0},
        },
        "degree_lane_multipliers": {
            "Second": {"upper": 3.00, "lower": 0.20, "mixed": 0.35},
            "Third": {"upper": 3.00, "lower": 0.20, "mixed": 0.35},
            "Fourth": {"upper": 2.40, "lower": 0.30, "mixed": 0.40},
            "Fifth": {"upper": 1.00, "lower": 1.00, "mixed": 0.55},
            "Sixth": {"upper": 0.20, "lower": 3.00, "mixed": 0.35},
            "Seventh": {"upper": 0.15, "lower": 3.50, "mixed": 0.35},
        },
        # v2_0_22 preserves previous-project v6.2.x connector family
        # distribution for Medium Swing ordinary walking. Later musicality
        # passes may tune style policy, but this value is the reference
        # alignment point for the old engine's feel.
        "connector_family_weights": {
            "scale_near_nextR": 40.0,
            "approach_nextR": 40.0,
            "dominant_connection": 10.0,
        },
        "same_beat3_beat4_weight_multiplier": 0.15,
        "lane_instance_selection": "legacy_random",
        "target_continuity_enabled": True,
        "root_echo_enabled": True,
        "root_echo_probability": 0.14,
        "root_echo_compact_probability_multiplier": 0.22,
        "root_echo_rr_start_3and_probability": 0.32,
        "root_echo_allowed_upbeats": (0.5, 2.5),
        "root_echo_max_per_region": 1,
        "classic_fill_enabled": True,
        "classic_fill_two_bar_tonic_probability": 0.18,
        "classic_fill_max_start_note": 43,
        "classic_fill_min_gap_regions": 14,
        "debug_name": "medium_swing_bass_foundation_rule_organization_v2_0_24",
    }


def get_pattern_candidates(context: dict | None = None) -> tuple[PatternCandidate, ...]:
    """Medium swing BassFoundation walking vocabulary.

    All entries are style-owned pitchless degree/function patterns. Historical
    shorthand ``4`` is intentionally expressed as ``nextR`` or, for literal
    scale degree 4, ``Fourth``. This prevents ambiguity with V2's bass-library
    rule that ``4`` means next root.
    """

    context = context or {}
    if context.get("bass_foundation_fill_scene") == "two_bar_tonic" or context.get("bass_foundation_scene") == "two_bar_tonic":
        return _classic_fill_candidates()
    duration = float(context.get("region_duration_beats", 4.0))
    if duration <= 2.0:
        return _two_beat_region_candidates()
    # v2_0_22: full-bar ordinary walking should align with the previous
    # project's ThreeBeatSkeleton selection table. Contextual ii-V/V-I
    # vocabulary is intentionally not mixed into the ordinary three-beat
    # skeleton pool, because it changes the first-three-beat occurrence
    # distribution and makes audit comparisons with the old Medium Swing bass
    # harder. Scene-specific vocabulary can return through explicit scene
    # requests, not through the generic walking candidate pool.
    return tuple(_candidate_from_skeleton(spec) for spec in THREE_BEAT_SKELETONS)


def _candidate_from_skeleton(spec: WalkingSkeletonSpec) -> PatternCandidate:
    category = f"walking_{spec.group}_tone"
    return PatternCandidate(
        name=f"medium_swing_bass_{spec.identifier}",
        weight=spec.weight_mid,
        category=category,
        events=_events(spec.degrees + ("beat4_auto",)),
        tail_policy=TailPolicy.from_local_beats((0.0, 1.0, 2.0, 3.0)),
        tags=("swing", "bass_foundation", "walking", spec.group, "target_to_target"),
        metadata={
            "skeleton_id": spec.identifier,
            "skeleton_group": spec.group,
            "skeleton_degrees": spec.degrees,
            "zone_weights": {"low": spec.weight_low, "mid": spec.weight_mid, "high": spec.weight_high},
            "allow_repetition": spec.allow_repetition,
            "connector_policy": "weighted_family_auto",
        },
    )


def _contextual_vocabulary(context: dict) -> tuple[PatternCandidate, ...]:
    chord_symbol = str(context.get("chord_symbol", ""))
    next_symbol = str(context.get("next_chord_symbol", ""))
    candidates: list[PatternCandidate] = []
    if _looks_like_minor_ii_to_v(chord_symbol, next_symbol):
        candidates.extend(
            [
                _contextual_candidate("2to5_major_R_2_b3_3_nextR", ("R", "Second", "b3", "Third"), 3.4, "ii_v_vocabulary"),
                _contextual_candidate("2to5_major_R_b3_5_b5_nextR", ("R", "b3", "Fifth", "b5"), 2.6, "ii_v_vocabulary"),
                _contextual_candidate("2to5_major_R_b7_6_5_nextR", ("R", "Seventh", "Sixth", "Fifth"), 2.1, "ii_v_vocabulary"),
            ]
        )
    if _looks_like_dominant_to_major(chord_symbol, next_symbol):
        candidates.extend(
            [
                _contextual_candidate("5to1_major_R_b7_6_5_nextR", ("R", "Seventh", "Sixth", "Fifth"), 3.0, "v_i_vocabulary"),
                _contextual_candidate("5to1_major_R_b2_2_3_nextR", ("R", "b2", "Second", "Third"), 2.0, "v_i_vocabulary"),
            ]
        )
    return tuple(candidates)


def _contextual_candidate(name: str, degrees: tuple[str, str, str, str], weight: float, category: str) -> PatternCandidate:
    return PatternCandidate(
        name=f"medium_swing_bass_{name}",
        weight=weight,
        category=category,
        events=_events(degrees),
        tail_policy=TailPolicy.from_local_beats((0.0, 1.0, 2.0, 3.0)),
        tags=("swing", "bass_foundation", "vocabulary", category),
        metadata={
            "skeleton_id": name,
            "skeleton_group": "contextual",
            "skeleton_degrees": degrees[:3],
            "zone_weights": {"low": weight, "mid": weight, "high": weight},
            "allow_repetition": False,
            "connector_policy": "weighted_family_auto",
        },
    )


def _classic_fill_candidates() -> tuple[PatternCandidate, ...]:
    """High-level BassFoundation fill candidates.

    These are not ordinary walking vocabulary. They are returned only when core
    BassFoundation generation has detected a matching scene and explicitly asks
    for ``bass_foundation_fill_scene`` candidates.
    """

    return (
        PatternCandidate(
            name="medium_swing_bass_CF_TWO_BAR_TONIC_01",
            weight=1.0,
            category="classic_fill_two_bar_tonic",
            events=(
                event_spec(track="bass", beat=0.0, role="bass_note", metadata={"degree": "R", "length_profile": "classic_fill_quarter", "dynamic_profile": "downbeat", **WALK_META}),
                event_spec(track="bass", beat=0.5, role="bass_note", metadata={"degree": "classic_low3", "length_profile": "classic_fill_syncopated_sustain", "dynamic_profile": "classic_fill_accent", **WALK_META}),
                event_spec(track="bass", beat=2.0, role="bass_note", metadata={"degree": "degree4", "length_profile": "classic_fill_quarter", "dynamic_profile": "classic_fill", **WALK_META}),
                event_spec(track="bass", beat=3.0, role="bass_note", metadata={"degree": "#4", "length_profile": "classic_fill_quarter", "dynamic_profile": "classic_fill_chromatic", **WALK_META}),
                event_spec(track="bass", beat=4.0, role="bass_note", metadata={"degree": "Fifth", "length_profile": "classic_fill_quarter", "dynamic_profile": "downbeat", **WALK_META}),
                event_spec(track="bass", beat=4.5, role="bass_note", metadata={"degree": "Fifth", "length_profile": "classic_fill_upbeat", "dynamic_profile": "light", **WALK_META}),
                event_spec(track="bass", beat=5.0, role="bass_note", metadata={"degree": "degree4", "length_profile": "classic_fill_quarter", "dynamic_profile": "classic_fill", **WALK_META}),
                event_spec(track="bass", beat=6.0, role="bass_note", metadata={"degree": "Third", "length_profile": "classic_fill_quarter", "dynamic_profile": "classic_fill", **WALK_META}),
                event_spec(track="bass", beat=7.0, role="bass_note", metadata={"degree": "classic_connect_nextR", "length_profile": "classic_fill_connector", "dynamic_profile": "connector", **WALK_META}),
            ),
            tail_policy=TailPolicy.from_local_beats((0.0, 0.5, 2.0, 3.0, 4.0, 4.5, 5.0, 6.0, 7.0)),
            tags=("swing", "bass_foundation", "classic_fill", "two_bar_tonic", "scene_triggered"),
            metadata={
                "bass_foundation_fill": True,
                "fill_id": "CF_TWO_BAR_TONIC_01",
                "scene": "two_bar_tonic",
                "not_ordinary_walking": True,
                "max_region_span_required": 12,
            },
        ),
    )


def _two_beat_region_candidates() -> tuple[PatternCandidate, ...]:
    return (
        PatternCandidate(
            name="medium_swing_bass_compact_R_weighted_connector_nextR",
            weight=3.0,
            category="compact_two_chord_bar_walking",
            events=_events(("R", "beat4_auto"), beats=(0.0, 1.0)),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0)),
            tags=("swing", "bass_foundation", "two_chord_bar", "compact"),
            metadata={"connector_policy": "weighted_family_auto"},
        ),
        PatternCandidate(
            name="medium_swing_bass_compact_R_approach_below_nextR",
            weight=1.4,
            category="compact_two_chord_bar_walking",
            events=_events(("R", "approach_nextR_below"), beats=(0.0, 1.0)),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0)),
            tags=("swing", "bass_foundation", "two_chord_bar", "compact"),
        ),
        PatternCandidate(
            name="medium_swing_bass_compact_R_approach_above_nextR",
            weight=1.0,
            category="compact_two_chord_bar_walking",
            events=_events(("R", "approach_nextR_above"), beats=(0.0, 1.0)),
            tail_policy=TailPolicy.from_local_beats((0.0, 1.0)),
            tags=("swing", "bass_foundation", "two_chord_bar", "compact"),
        ),
    )


def _events(degrees: tuple[str, ...], beats: tuple[float, ...] | None = None):
    beats = beats or tuple(float(i) for i in range(len(degrees)))
    return tuple(
        event_spec(
            track="bass",
            beat=beat,
            role="bass_note",
            metadata={
                "degree": degree,
                "dynamic_profile": "downbeat" if beat == 0.0 else ("connector" if index == len(degrees) - 1 else "walk"),
                **WALK_META,
            },
        )
        for index, (beat, degree) in enumerate(zip(beats, degrees))
    )


def _looks_like_minor_ii_to_v(chord_symbol: str, next_symbol: str) -> bool:
    if not chord_symbol or not next_symbol:
        return False
    motion = classify_functional_motion(chord_symbol=chord_symbol, next_chord_symbol=next_symbol)
    return motion.current_to_next_type in {"ii_v", "minor_ii_v"}


def _looks_like_dominant_to_major(chord_symbol: str, next_symbol: str) -> bool:
    if not chord_symbol or not next_symbol:
        return False
    motion = classify_functional_motion(chord_symbol=chord_symbol, next_chord_symbol=next_symbol)
    return motion.current_to_next_type == "v_i_major"
