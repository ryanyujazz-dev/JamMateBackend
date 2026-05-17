from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.expression import (
    EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION,
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    ExpressionResolver,
    PedalMode,
    build_expression_foundation_audit,
)
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from tools.demo_audit_pipeline import run_job, standard_jobs, validate_job_audit


def _anticipated_event(*, hint: str = "soft_sustain", performed_lead_in: float = 0.5) -> PatternEvent:
    return PatternEvent(
        event_id="anticipated",
        track="piano",
        region_id="r_next",
        chord_symbol="G7",
        onset_beat=3.5,
        local_beat=3.5,
        role="harmonic",
        expression_hint=hint,
        metadata={
            "region_duration_beats": 4.0,
            "anticipation": {
                "kind": "next_beat1_to_previous_tail",
                "tie_from_previous": True,
                "original_onset_beat": 4.0,
                "original_local_beat_in_source": 0.0,
                "source_region_duration_beats": 4.0,
                "logical_lead_in_beats": 0.5,
                "performed_lead_in_beats": performed_lead_in,
                "timing_grid": "straight_even_upbeat",
            },
        },
    )


def _policy(style: str) -> ExpressionPolicyBundle:
    return ExpressionPolicyBundle(
        profiles={
            "soft_sustain": ExpressionProfile(
                name="soft_sustain",
                duration_beats=3.5,
                velocity=48,
                articulation=ArticulationKind.SUSTAIN,
                pedal=PedalMode.SUSTAIN,
                release_beats=0.12,
            ),
            "core_short": ExpressionProfile(
                name="core_short",
                duration_beats=0.45,
                velocity=56,
                articulation=ArticulationKind.SHORT,
                pedal=PedalMode.NONE,
                release_beats=0.03,
            ),
            "comp_medium": ExpressionProfile(
                name="comp_medium",
                duration_beats=0.85,
                velocity=61,
                articulation=ArticulationKind.SHORT,
                pedal=PedalMode.NONE,
                release_beats=0.04,
            ),
        },
        default_profile="soft_sustain",
        track_default_profiles={"piano": "soft_sustain"},
        metadata={"style": style},
    )


def test_ballad_anticipated_chord_uses_light_pedal_and_shorter_connected_release() -> None:
    event = _anticipated_event(hint="soft_sustain")
    expr = ExpressionResolver().resolve([event], _policy("jazz_ballad")).events[event.event_id]

    assert expr.metadata["anticipation_pedal_release_micro_tuning_version"] == EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION
    assert expr.metadata["anticipation_pedal_release_micro_tuning_applied"] is True
    assert expr.metadata["duration_anticipation_micro_tuning_applied"] is True
    assert expr.pedal == "light"
    assert expr.release_beats == 0.08
    assert expr.duration_beats == 3.35


def test_bossa_anticipated_short_is_dry_and_releases_cleanly_after_downbeat() -> None:
    event = _anticipated_event(hint="core_short")
    expr = ExpressionResolver().resolve([event], _policy("bossa_nova")).events[event.event_id]

    assert expr.pedal == "none"
    assert expr.release_beats == 0.025
    assert expr.duration_beats == 0.86
    assert expr.metadata["duration_anticipation_micro_tuning_reason"] == "bossa_clean_post_downbeat_release_cap"


def test_swing_anticipated_push_uses_performed_lead_in_and_stays_dry() -> None:
    event = _anticipated_event(hint="comp_medium", performed_lead_in=1.0 / 3.0)
    expr = ExpressionResolver().resolve([event], _policy("medium_swing")).events[event.event_id]

    assert expr.pedal == "none"
    assert expr.release_beats == 0.03
    assert abs(expr.duration_beats - (1.0 / 3.0 + 0.72)) < 1e-6
    assert expr.metadata["duration_anticipation_performed_lead_in_beats"] == round(1.0 / 3.0, 6)


def test_expression_audit_summarizes_anticipation_release_micro_tuning() -> None:
    event = _anticipated_event(hint="soft_sustain")
    plan = ExpressionResolver().resolve([event], _policy("jazz_ballad"))
    audit = build_expression_foundation_audit([event], plan, style_id="jazz_ballad")

    assert audit.summary["anticipation_tie_event_count"] == 1
    assert audit.summary["anticipation_pedal_release_micro_tuned_count"] == 1
    assert audit.summary["anticipation_duration_micro_tuned_count"] == 1
    assert audit.summary["anticipation_pedal_modes"] == {"light": 1}
    assert audit.summary["anticipation_avg_release_beats"] == 0.08


def test_demo_matrix_validates_anticipation_release_micro_tuning(tmp_path: Path) -> None:
    paths = run_job(standard_jobs()["blue_bossa_minor_altered"], output_dir=tmp_path)
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    result = validate_job_audit("blue_bossa_minor_altered", audit)
    actual = result["actual"]

    assert result["status"] == "passed"
    assert actual["anticipation_pedal_release_micro_tuned_events"] >= 8
    assert actual["anticipation_sustain_pedal_events"] == 0
    assert actual["anticipation_avg_release_beats"] <= 0.045
