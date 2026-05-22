from __future__ import annotations

import random

from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.expression import ArticulationKind, ExpressionPolicyBundle, ExpressionProfile, ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec

MILESTONE_ID = "v2_6_113"


def _region(region_id: str, chord: str, start: float, duration: float) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=None,
        chorus_index=0,
        total_choruses=1,
        bar_index=int(start // 4),
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
        source_bar_index=int(start // 4),
        performance_bar_index=int(start // 4),
    )


def _expression_policy() -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "soft_hold": ExpressionProfile(
                name="soft_hold",
                duration_beats=0.8,
                velocity=50,
                articulation=ArticulationKind.SUSTAIN,
                metadata={"duration_semantics": "hold_until_next_touch"},
            ),
            "short": ExpressionProfile(
                name="short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
            ),
        },
        default_profile="soft_hold",
        track_default_profiles={"piano": "soft_hold"},
    )


def _rewrite_with_source_pattern(*, first_hint: str = "soft_hold"):
    prev_region = _region("prev", "Dm7", 0.0, 4.0)
    next_region = _region("next", "G7", 4.0, 4.0)
    previous = PatternCandidate(
        name="prev_tail_free",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
    ).instantiate(prev_region)
    source = PatternCandidate(
        name="source_beat1_to_3and",
        weight=1.0,
        category="test",
        events=(
            event_spec(track="piano", beat=0.0, role="harmonic", expression_hint=first_hint),
            event_spec(track="piano", beat=3.5, role="harmonic", expression_hint="short"),
        ),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)
    rewritten = AnticipationResolver().resolve(
        list(previous.events) + list(source.events),
        AnticipationPolicy(enabled=True, probability=1.0, debug_name="test_source_continuation"),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: source},
    )
    anticipated = next(event for event in rewritten if event.event_id.endswith("__anticipated_from_previous"))
    return rewritten, anticipated


def test_v2_6_113_anticipated_hold_preserves_source_pattern_next_touch_target() -> None:
    rewritten, anticipated = _rewrite_with_source_pattern(first_hint="soft_hold")
    anticipation = anticipated.metadata["anticipation"]

    assert anticipation["source_continuation_contract_version"] == MILESTONE_ID
    assert anticipation["source_continuation_target_kind"] == "next_same_track_touch"
    assert anticipation["source_next_same_track_gap_beats"] == 3.5
    assert anticipation["source_next_same_track_local_beat"] == 3.5

    plan = ExpressionResolver().resolve(rewritten, _expression_policy())
    expr = plan.events[anticipated.event_id]

    # The original beat-1 hold would have lasted to source-region 3& (3.5 beats).
    # After moving it to previous 4&, duration must include the 0.5-beat lead-in:
    # previous 4& -> source-region 3& = 4.0 beats.
    assert expr.duration_beats == 4.0
    assert expr.metadata["duration_anticipation_source_continuation_version"] == MILESTONE_ID
    assert expr.metadata["duration_anticipation_source_continuation_applied"] is True
    assert expr.metadata["duration_anticipation_source_continuation_reason"] == "hold_until_source_next_same_track_touch"
    assert expr.metadata["duration_anticipation_original_sustain_beats"] == 3.5


def test_v2_6_113_fixed_short_anticipation_does_not_inherit_long_source_target() -> None:
    rewritten, anticipated = _rewrite_with_source_pattern(first_hint="short")
    expr = ExpressionResolver().resolve(rewritten, _expression_policy()).events[anticipated.event_id]

    assert anticipated.metadata["anticipation"]["source_next_same_track_gap_beats"] == 3.5
    assert expr.duration_beats == 0.95
    assert expr.metadata["duration_anticipation_source_continuation_applied"] is False
    assert expr.metadata["duration_anticipation_original_sustain_beats"] == 0.45
