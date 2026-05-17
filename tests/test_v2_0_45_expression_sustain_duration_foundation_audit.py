from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.expression import (
    EXPRESSION_AUDIT_CONTRACT_VERSION,
    ArticulationKind,
    ExpressionPolicyBundle,
    ExpressionProfile,
    ExpressionResolver,
    build_expression_foundation_audit,
    format_expression_foundation_audit_report,
)
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment


ROOT = Path(__file__).resolve().parents[1]


def _minimal_result(tmp_path):
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json").read_text(encoding="utf-8"))
    return generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "medium_swing",
            "tempo": 132,
            "choruses": 1,
            "seed": 45,
            "output_path": str(tmp_path / "v2_0_45_expression_audit.mid"),
            "ensemble": {"bass_present": True},
        }
    )


def test_expression_foundation_audit_is_attached_to_generation_debug(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    debug = result.debug

    assert debug["expression_foundation_audit"]["contract_version"] == EXPRESSION_AUDIT_CONTRACT_VERSION
    assert debug["expression_foundation_audit"]["events"] == len(debug["expression_foundation_audit_events"])
    assert debug["expression_foundation_audit"]["events"] > 0
    assert "expression_sustain_duration_foundation_audit" in debug["pipeline"]


def test_expression_audit_rows_expose_gap_region_duration_and_flags(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    row = result.debug["expression_foundation_audit_events"][0]

    assert row["event_id"]
    assert row["profile_name"]
    assert row["articulation"]
    assert row["duration_beats"] > 0
    assert row["region_remaining_beats"] is not None
    assert "gap_to_next_same_track" in row
    assert isinstance(row["flags"], list)


def test_piano_musical_audit_includes_expression_audit_summary(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    audit = build_piano_musical_audit(result.debug)

    assert audit.summary["expression_audit"]["contract_version"] == EXPRESSION_AUDIT_CONTRACT_VERSION
    assert "expression_flags" in audit.summary
    assert "expression_flags" in audit.event_rows[0]


def test_expression_audit_detects_short_overlap_with_next_event() -> None:
    events = [
        PatternEvent(
            event_id="e1",
            track="piano",
            region_id="r1",
            chord_symbol="Cmaj7",
            onset_beat=0.0,
            local_beat=0.0,
            role="harmonic",
            expression_hint="too_long_short",
            pattern_id="synthetic",
            metadata={"region_duration_beats": 1.0},
        ),
        PatternEvent(
            event_id="e2",
            track="piano",
            region_id="r2",
            chord_symbol="Dm7",
            onset_beat=0.5,
            local_beat=0.0,
            role="harmonic",
            expression_hint="too_long_short",
            pattern_id="synthetic",
            metadata={"region_duration_beats": 1.0},
        ),
    ]
    policy = ExpressionPolicyBundle(
        profiles={
            "too_long_short": ExpressionProfile(
                name="too_long_short",
                duration_beats=0.8,
                velocity=60,
                articulation=ArticulationKind.SHORT,
            )
        },
        default_profile="too_long_short",
    )
    plan = ExpressionResolver().resolve(events, policy)
    audit = build_expression_foundation_audit(events, plan, style_id="synthetic")

    first = audit.event_rows[0]
    assert "short_overlaps_next_event" in first["flags"]
    assert audit.summary["short_overlap_count"] == 1


def test_expression_foundation_audit_report_is_markdown(tmp_path) -> None:
    result = _minimal_result(tmp_path)
    audit = build_expression_foundation_audit([], ExpressionResolver().resolve([], None), style_id="empty")
    assert "Expression / Sustain / Duration Foundation Audit" in format_expression_foundation_audit_report(audit)

    payload = result.debug
    runtime_audit = build_expression_foundation_audit([], ExpressionResolver().resolve([], None), style_id="empty")
    runtime_audit = type(runtime_audit)(
        summary=payload["expression_foundation_audit"],
        event_rows=payload["expression_foundation_audit_events"],
        warnings=[],
    )
    report = format_expression_foundation_audit_report(runtime_audit, max_events=2)
    assert "## Event Trace" in report
    assert "observational" in report
