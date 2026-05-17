from __future__ import annotations

from jammate_engine.core.expression import (
    EXPRESSION_REGION_DURATION_CLAMP_VERSION,
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    ExpressionResolver,
    build_expression_foundation_audit,
)
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent


def _event(*, region_duration: float | None = 2.0, local_beat: float = 0.0) -> PatternEvent:
    metadata = {} if region_duration is None else {"region_duration_beats": region_duration}
    return PatternEvent(
        event_id="evt_region_clamp",
        track="piano",
        region_id="r1",
        chord_symbol="Cmaj7",
        onset_beat=local_beat,
        local_beat=local_beat,
        role="harmonic",
        expression_hint="soft_sustain",
        pattern_id="synthetic_region_clamp",
        metadata=metadata,
    )


def _policy() -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "soft_sustain": ExpressionProfile(
                name="soft_sustain",
                duration_beats=3.5,
                velocity=48,
                articulation=ArticulationKind.SUSTAIN,
            )
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain"},
    )


def test_expression_duration_is_clamped_to_chord_region_end() -> None:
    event = _event(region_duration=2.0, local_beat=0.0)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 2.0
    assert expr.metadata["duration_region_clamp_version"] == EXPRESSION_REGION_DURATION_CLAMP_VERSION
    assert expr.metadata["duration_region_clamp_applied"] is True
    assert expr.metadata["duration_region_clamp_reason"] == "clamped_to_chord_region_end"
    assert expr.metadata["duration_requested_beats"] == 3.5
    assert expr.metadata["duration_region_remaining_beats"] == 2.0


def test_expression_duration_respects_local_beat_inside_region() -> None:
    event = _event(region_duration=2.0, local_beat=1.5)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 0.5
    assert expr.metadata["duration_region_clamp_applied"] is True
    assert expr.metadata["duration_region_remaining_beats"] == 0.5


def test_expression_duration_without_region_metadata_stays_profile_owned() -> None:
    event = _event(region_duration=None, local_beat=0.0)
    expr = ExpressionResolver().resolve([event], _policy()).events[event.event_id]

    assert expr.duration_beats == 3.5
    assert expr.metadata["duration_region_clamp_applied"] is False
    assert expr.metadata["duration_region_clamp_reason"] == "region_duration_missing"


def test_expression_audit_treats_region_clamped_ballad_sustain_as_intentional() -> None:
    event = _event(region_duration=2.0, local_beat=0.0)
    plan = ExpressionResolver().resolve([event], _policy())
    audit = build_expression_foundation_audit([event], plan, style_id="jazz_ballad")
    row = audit.event_rows[0]

    assert row["duration_beats"] == 2.0
    assert row["crosses_region_end"] is False
    assert "ballad_soft_sustain_too_short" not in row["flags"]
    assert row["metadata"]["duration_region_clamp_applied"] is True
