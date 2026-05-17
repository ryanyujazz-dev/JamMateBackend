from __future__ import annotations

import random

from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.expression import (
    EXPRESSION_ANTICIPATION_TIE_DURATION_VERSION,
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    ExpressionResolver,
    build_expression_foundation_audit,
)
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent


def _policy(profile_duration: float = 3.5) -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "soft_sustain": ExpressionProfile(
                name="soft_sustain",
                duration_beats=profile_duration,
                velocity=48,
                articulation=ArticulationKind.SUSTAIN,
            ),
            "core_short": ExpressionProfile(
                name="core_short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
            ),
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain"},
    )


def _anticipated_event(*, expression_hint: str = "soft_sustain", source_region_duration: float = 4.0) -> PatternEvent:
    return PatternEvent(
        event_id="evt_next_beat1__anticipated_from_previous",
        track="piano",
        region_id="r_next",
        chord_symbol="G7",
        onset_beat=3.5,
        local_beat=3.5,
        role="harmonic",
        expression_hint=expression_hint,
        metadata={
            "region_duration_beats": source_region_duration,
            "anticipation": {
                "kind": "next_beat1_to_previous_tail",
                "tie_from_previous": True,
                "original_onset_beat": 4.0,
                "original_local_beat_in_source": 0.0,
                "source_region_duration_beats": source_region_duration,
                "lead_in_beats": 0.5,
            },
        },
    )


def test_anticipated_ballad_sustain_includes_lead_in_and_original_duration() -> None:
    event = _anticipated_event(expression_hint="soft_sustain", source_region_duration=4.0)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 4.0
    assert expr.metadata["duration_anticipation_tie_version"] == EXPRESSION_ANTICIPATION_TIE_DURATION_VERSION
    assert expr.metadata["duration_anticipation_tie_applied"] is True
    assert expr.metadata["duration_anticipation_lead_in_beats"] == 0.5
    assert expr.metadata["duration_anticipation_original_sustain_beats"] == 3.5
    assert expr.metadata["duration_region_clamp_reason"] == "anticipated_tie_crosses_region_boundary"


def test_anticipated_tie_respects_source_region_remaining_for_dense_harmony() -> None:
    event = _anticipated_event(expression_hint="soft_sustain", source_region_duration=2.0)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 2.5
    assert expr.metadata["duration_anticipation_original_region_clamp_applied"] is True
    assert expr.metadata["duration_anticipation_source_region_remaining_beats"] == 2.0


def test_anticipated_bossa_short_still_rings_across_original_beat1() -> None:
    event = _anticipated_event(expression_hint="core_short", source_region_duration=4.0)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 0.95
    assert expr.duration_beats > 0.5
    assert expr.metadata["duration_anticipation_tie_applied"] is True


def test_expression_audit_treats_anticipated_cross_region_sustain_as_intentional() -> None:
    event = _anticipated_event(expression_hint="soft_sustain", source_region_duration=4.0)
    plan = ExpressionResolver().resolve([event], _policy())
    audit = build_expression_foundation_audit([event], plan, style_id="jazz_ballad")
    row = audit.event_rows[0]

    assert row["duration_beats"] == 4.0
    assert row["metadata"]["duration_anticipation_tie_applied"] is True
    assert row["crosses_region_end"] is False
    assert "crosses_region_end" not in row["flags"]


def test_resolver_metadata_preserves_original_beat1_for_expression_tie() -> None:
    prev_region = HarmonicRegion(
        region_id="r_prev",
        chord_symbol="Dm7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    next_region = HarmonicRegion(
        region_id="r_next",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=1,
        chord_index=0,
        start_beat=4.0,
        duration_beats=4.0,
    )
    previous = PatternCandidate(
        name="prev_tail_free",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
    ).instantiate(prev_region)
    next_plan = PatternCandidate(
        name="next_downbeat",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic", expression_hint="soft_sustain"),),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)
    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        AnticipationPolicy(enabled=True, probability=1.0, debug_name="test"),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )
    anticipated = next(event for event in rewritten if event.event_id.endswith("__anticipated_from_previous"))

    assert anticipated.metadata["anticipation"]["original_onset_beat"] == 4.0
    assert anticipated.metadata["anticipation"]["lead_in_beats"] == 0.5
    expr = ExpressionResolver().resolve([anticipated], _policy()).events[anticipated.event_id]
    assert expr.duration_beats == 4.0
