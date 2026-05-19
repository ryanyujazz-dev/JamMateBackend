from __future__ import annotations

from jammate_engine.core.expression import ArticulationKind
from jammate_engine.core.expression.expression_resolver import ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.jazz_ballad import comping_patterns
from jammate_engine.styles.jazz_ballad.expression_policy import get_expression_policy
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile


def _region(duration: float = 4.0) -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r_v2_5_9_ballad_1and_continuity",
        chord_symbol="Cmaj9",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=duration,
        metadata={"home_key": "C"},
    )


def _candidate(name: str, *, duration: float = 4.0):
    return next(c for c in comping_patterns.get_pattern_candidates({"region_duration_beats": duration}) if c.name == name)


def test_v2_5_9_ballad_1and_anchor_duration_reaches_performed_swing_upbeat() -> None:
    candidate = _candidate("ballad_piano_downbeat_1and_whisper", duration=4.0)
    plan = candidate.instantiate(_region(4.0))

    expression = ExpressionResolver().resolve(
        list(plan.events),
        get_expression_policy(),
        timing_policy=JazzBalladProfile().timing_policy,
    )

    anchor = expression.events[plan.events[0].event_id]
    second = expression.events[plan.events[1].event_id]

    assert comping_patterns.PATTERN_LIBRARY_VERSION == "v2_5_9"
    assert plan.events[1].local_beat == 0.5
    assert plan.events[1].metadata["timing_intent"] == "swing_upbeat"
    # v2_6_38 supersedes the earlier full-chord clamp: the 1& whisper is now
    # a non-interrupting upper/projection-group re-touch, so the beat-1
    # foundation must keep its warm sustain instead of being shortened.
    assert round(anchor.duration_beats, 6) == 3.5
    assert anchor.metadata["duration_next_event_clamp_applied"] is False
    assert plan.events[1].gesture_type == "inner_movement"
    assert tuple(plan.events[1].gesture.projection_refs) == ("projection_group",)
    assert second.profile_name == "soft_whisper"


def test_v2_5_9_ballad_near_downbeat_whisper_is_sustained_not_short() -> None:
    policy = get_expression_policy()
    profile = policy.profiles["soft_whisper"]

    assert profile.articulation == ArticulationKind.SUSTAIN
    assert profile.duration_beats >= 1.0
    assert profile.metadata["role"] == "ballad_near_downbeat_sustained_whisper"
