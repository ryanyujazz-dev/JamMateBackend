from __future__ import annotations

import random
from dataclasses import replace

from jammate_engine.core.anticipation import AnticipationResolver
from jammate_engine.core.expression import ArticulationKind, ExpressionPolicyBundle, ExpressionProfile, ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec
from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile


def _regions() -> tuple[HarmonicRegion, HarmonicRegion]:
    return (
        HarmonicRegion(
            region_id="r_prev_ballad",
            chord_symbol="Fm7",
            next_chord_symbol="Bb7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=0.0,
            duration_beats=4.0,
        ),
        HarmonicRegion(
            region_id="r_next_ballad",
            chord_symbol="Bb7",
            next_chord_symbol="Ebmaj7",
            chorus_index=0,
            bar_index=1,
            chord_index=0,
            start_beat=4.0,
            duration_beats=4.0,
        ),
    )


def _anticipated_with_ballad_policy():
    prev_region, next_region = _regions()
    previous = PatternCandidate(
        name="prev_tail_free_ballad",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
    ).instantiate(prev_region)
    next_plan = PatternCandidate(
        name="next_ballad_downbeat",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic", expression_hint="soft_sustain"),),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)
    style = JazzBalladProfile()
    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        replace(style.anticipation_policy, probability=1.0),
        random.Random(7),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )
    anticipated = next(event for event in rewritten if event.event_id.endswith("__anticipated_from_previous"))
    return anticipated, style


def test_v2_5_9_jazz_ballad_default_timing_feel_is_swing8() -> None:
    style = JazzBalladProfile()

    assert style.timing_policy["feel"] == "swing"
    assert style.timing_policy["version"] == "v2_0_43"
    assert style.timing_policy["metadata"]["stage"] == "v2_5_9_ballad_default_swing8_timing"
    assert performed_beat(3.5, "auto", style.timing_policy) == 3.0 + 2.0 / 3.0


def test_v2_5_9_ballad_anticipation_keeps_logical_4and_but_performs_swing_upbeat() -> None:
    anticipated, style = _anticipated_with_ballad_policy()
    anticipation = anticipated.metadata["anticipation"]

    assert anticipated.onset_beat == 3.5
    assert anticipated.local_beat == 3.5
    assert anticipated.metadata["timing_intent"] == "swing_upbeat"
    assert anticipation["timing_grid"] == "swing_triplet_upbeat"
    assert anticipation["logical_lead_in_beats"] == 0.5
    assert abs(anticipation["performed_lead_in_beats"] - (1.0 / 3.0)) < 1e-6
    assert abs(anticipation["expected_upbeat_fraction"] - (2.0 / 3.0)) < 1e-6

    performed = performed_beat(anticipated.onset_beat, anticipated.metadata["timing_intent"], style.timing_policy)
    assert abs(performed - (3.0 + 2.0 / 3.0)) < 1e-6
    assert abs(performed - anticipation["expected_performed_onset_beat"]) < 1e-6


def test_v2_5_9_ballad_anticipated_tie_duration_uses_swing8_lead_in() -> None:
    anticipated, style = _anticipated_with_ballad_policy()
    policy = ExpressionPolicyBundle(
        profiles={
            "soft_sustain": ExpressionProfile(
                name="soft_sustain",
                duration_beats=1.0,
                velocity=50,
                articulation=ArticulationKind.SUSTAIN,
            )
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain"},
        metadata={"style": "jazz_ballad"},
    )
    expr = ExpressionResolver().resolve([anticipated], policy, timing_policy=style.timing_policy).events[anticipated.event_id]

    assert abs(expr.metadata["duration_anticipation_logical_lead_in_beats"] - 0.5) < 1e-6
    assert abs(expr.metadata["duration_anticipation_performed_lead_in_beats"] - (1.0 / 3.0)) < 1e-6
    assert expr.metadata["duration_anticipation_timing_grid"] == "swing_triplet_upbeat"
    assert expr.metadata["duration_anticipation_target_timing_intent"] == "swing_upbeat"
