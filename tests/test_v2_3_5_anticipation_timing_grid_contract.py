from __future__ import annotations

import json
import random
from dataclasses import replace

from jammate_engine.core.anticipation import AnticipationResolver
from jammate_engine.core.expression import ArticulationKind, ExpressionPolicyBundle, ExpressionProfile, ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec
from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.styles.medium_swing.profile import MediumSwingProfile
from tools.demo_audit_pipeline import run_job, standard_jobs, validate_job_audit


def _regions() -> tuple[HarmonicRegion, HarmonicRegion]:
    return (
        HarmonicRegion(
            region_id="r_prev",
            chord_symbol="Dm7",
            next_chord_symbol="G7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=0.0,
            duration_beats=4.0,
        ),
        HarmonicRegion(
            region_id="r_next",
            chord_symbol="G7",
            next_chord_symbol="Cmaj7",
            chorus_index=0,
            bar_index=1,
            chord_index=0,
            start_beat=4.0,
            duration_beats=4.0,
        ),
    )


def _anticipated_with_medium_swing_policy():
    prev_region, next_region = _regions()
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
    style = MediumSwingProfile()
    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        replace(style.anticipation_policy, probability=1.0),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )
    anticipated = next(event for event in rewritten if event.event_id.endswith("__anticipated_from_previous"))
    return anticipated, style


def test_medium_swing_anticipation_keeps_logical_4and_but_performs_at_triplet_upbeat() -> None:
    anticipated, style = _anticipated_with_medium_swing_policy()
    anticipation = anticipated.metadata["anticipation"]

    # Pitchless timeline still uses written 4& as the musical grid location.
    assert anticipated.onset_beat == 3.5
    assert anticipated.local_beat == 3.5

    # Rendering contract makes that written upbeat swing to beat 4 + 2/3.
    assert anticipated.metadata["timing_intent"] == "swing_upbeat"
    assert anticipation["timing_grid"] == "swing_triplet_upbeat"
    assert anticipation["logical_lead_in_beats"] == 0.5
    assert abs(anticipation["performed_lead_in_beats"] - (1.0 / 3.0)) < 1e-6
    performed = performed_beat(anticipated.onset_beat, anticipated.metadata["timing_intent"], style.timing_policy)
    assert abs(performed - (3.0 + 2.0 / 3.0)) < 1e-6
    assert abs(performed - anticipation["expected_performed_onset_beat"]) < 1e-6


def test_medium_swing_anticipation_tie_duration_uses_performed_lead_in_not_logical_half_beat() -> None:
    anticipated, _style = _anticipated_with_medium_swing_policy()
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
    )
    expr = ExpressionResolver().resolve([anticipated], policy).events[anticipated.event_id]

    assert abs(expr.duration_beats - (1.0 + 1.0 / 3.0)) < 1e-6
    assert expr.metadata["duration_anticipation_logical_lead_in_beats"] == 0.5
    assert abs(expr.metadata["duration_anticipation_performed_lead_in_beats"] - (1.0 / 3.0)) < 1e-6
    assert expr.metadata["duration_anticipation_timing_grid"] == "swing_triplet_upbeat"


def test_demo_matrix_audits_anticipation_timing_grid_for_medium_swing(tmp_path) -> None:
    paths = run_job(standard_jobs()["minimal_swing"], output_dir=tmp_path)
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    result = validate_job_audit("minimal_swing", audit)
    actual = result["actual"]
    piano = audit["piano_event_summary"]

    assert result["status"] == "passed"
    assert actual["anticipation_timing_grid_failures"] == 0
    assert actual["anticipation_timing_grid_error_max"] <= 1e-6
    samples = piano["anticipation_timing_grid_samples"]
    assert samples
    swing_samples = [row for row in samples if row["timing_grid"] == "swing_triplet_upbeat"]
    assert swing_samples
    assert any(abs(row["performed_lead_in_beats"] - (1.0 / 3.0)) < 1e-6 for row in swing_samples)
