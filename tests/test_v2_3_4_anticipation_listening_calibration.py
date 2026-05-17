from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.expression import (
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    ExpressionResolver,
    build_expression_foundation_audit,
)
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.bossa_nova.comping_patterns import get_pattern_candidates
from tools.demo_audit_pipeline import run_job, standard_jobs, validate_job_audit


def _policy() -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "core_sustain": ExpressionProfile(
                name="core_sustain",
                duration_beats=1.3,
                velocity=52,
                articulation=ArticulationKind.SUSTAIN,
            ),
            "core_short": ExpressionProfile(
                name="core_short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
            ),
        },
        default_profile="core_short",
        track_default_profiles={"piano": "core_short"},
    )


def _event(event_id: str, onset: float, hint: str, *, region_duration: float = 4.0, local: float | None = None) -> PatternEvent:
    return PatternEvent(
        event_id=event_id,
        track="piano",
        region_id="r1",
        chord_symbol="Cm7",
        onset_beat=onset,
        local_beat=onset if local is None else local,
        role="harmonic",
        expression_hint=hint,
        metadata={"region_duration_beats": region_duration},
    )


def test_next_event_clamp_prevents_bossa_sustain_overlap_before_anticipation() -> None:
    sustain = _event("prev_3and", 2.5, "core_sustain")
    anticipation = _event("next_4and", 3.5, "core_short")
    plan = ExpressionResolver().resolve([sustain, anticipation], _policy())
    expr = plan.events[sustain.event_id]

    assert expr.duration_beats == 1.0
    assert expr.metadata["duration_next_event_clamp_version"] == "v2_3_9"
    assert expr.metadata["duration_next_event_clamp_applied"] is True
    assert expr.metadata["duration_next_event_clamp_reason"] == "clamped_to_next_same_track_event"

    audit = build_expression_foundation_audit([sustain, anticipation], plan, style_id="bossa_nova")
    row = next(item for item in audit.event_rows if item["event_id"] == sustain.event_id)
    assert row["crosses_next_same_track_event"] is False
    assert "crosses_next_same_track_event" not in row["flags"]


def test_bossa_two_beat_regions_use_half_region_pattern_without_out_of_region_3and() -> None:
    region = HarmonicRegion(
        region_id="r_half",
        chord_symbol="G7",
        next_chord_symbol="Cm7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=2.0,
    )
    candidate = get_pattern_candidates({"region_duration_beats": 2.0})[0]
    plan = candidate.instantiate(region)

    assert candidate.name == "bossa_piano_half_region_1_2"
    assert [event.local_beat for event in plan.events] == [0.0, 1.0]
    assert all(float(event.local_beat or 0.0) < region.duration_beats for event in plan.events)


def test_v2_3_9_blue_bossa_anticipation_listening_thresholds_pass(tmp_path: Path) -> None:
    paths = run_job(standard_jobs()["blue_bossa_minor_altered"], output_dir=tmp_path)
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    result = validate_job_audit("blue_bossa_minor_altered", audit)
    actual = result["actual"]

    assert result["status"] == "passed"
    assert 8 <= actual["anticipation_events"] <= 20
    assert actual["anticipation_events"] == actual["anticipation_tie_expression_events"]
    assert actual["cross_next_event_count"] == 0
    assert actual["expression_warning_count"] == 0
    assert audit["piano_musical_audit"]["top_patterns"][0][0] == "bossa_piano_core_batida_1_2_3and"
    assert "bossa_piano_half_region_1_2" in dict(audit["piano_musical_audit"]["top_patterns"])
