from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.arrangement_policy import get_arrangement_policy

from examples.scripts.generate_medium_swing_piano_standard_tune_listening_checkpoint import (
    MILESTONE_ID,
    build_static_audit,
    _acceptance,
    _expression_rows,
    _expression_summary,
    _pattern_summary,
    _piano_pattern_rows,
    _selected_region_rows,
    _history_summary,
)



def test_v2_6_69_arrangement_policy_declares_behavior_preserving_standard_tune_checkpoint() -> None:
    arrangement = get_arrangement_policy()

    assert arrangement["piano_standard_tune_listening_checkpoint"] is True
    assert arrangement["piano_standard_tune_listening_checkpoint_version"] == MILESTONE_ID
    assert "behavior-preserving" in arrangement["piano_standard_tune_listening_checkpoint_contract"]
    assert "audit/demo coverage only" in arrangement["piano_standard_tune_listening_checkpoint_contract"]
    assert arrangement["milestone"] == "v2_6_69_medium_swing_piano_standard_tune_listening_checkpoint"

    # v2_6_69 must be a checkpoint on top of the prior Medium Swing piano work,
    # not a reset/restart of the pattern, expression, or voicing line.
    assert arrangement["piano_comping_active_fill_busy_multi_region_history_scorer_version"] == "v2_6_67"
    assert arrangement["piano_expression_policy_v1_numeric_calibration_version"] == "v2_6_68"
    assert arrangement["piano_comping_no_4and_delayed_tail_idiom_policy_version"] == "v2_6_66"


def test_v2_6_69_static_audit_keeps_pattern_expression_voicing_boundaries_clean() -> None:
    static_audit = build_static_audit()

    assert static_audit["arrangement_checkpoint_enabled"] is True
    assert static_audit["arrangement_checkpoint_version"] == MILESTONE_ID
    assert static_audit["missing_or_mismatched_prior_policy_versions"] == {}
    assert static_audit["expression_policy_version"] == "v2_6_68"
    assert static_audit["pattern_candidate_count"] > 0
    assert static_audit["pattern_forbidden_expression_candidates"] == []
    assert static_audit["pattern_forbidden_voicing_candidates"] == []
    assert static_audit["bar_first_two_chord_bar_candidates"] == []


def test_v2_6_69_standard_tune_runtime_checkpoint_keeps_history_expression_and_voicing_guards() -> None:
    score = json.loads((PROJECT_ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": 3690,
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    debug = dict(result.debug)
    piano_audit = build_piano_musical_audit(debug)
    pattern_rows = _piano_pattern_rows(debug)
    selected_rows = _selected_region_rows(pattern_rows)
    expression_rows = _expression_rows(debug)
    pattern_summary = _pattern_summary(pattern_rows)
    history_summary = _history_summary(selected_rows)
    expression_summary = _expression_summary(expression_rows, debug)

    assert debug["performance_choruses"] == 3
    assert len(pattern_rows) >= 100
    assert pattern_summary["history_metadata_events"] == len(pattern_rows)
    assert pattern_summary["forbidden_expression_key_events"] == 0
    assert pattern_summary["forbidden_voicing_key_events"] == 0
    assert pattern_summary["bar_first_two_chord_bar_events"] == 0

    assert expression_summary["calibrated_expression_events"] == expression_summary["piano_expression_events"]
    assert expression_summary["hold_boundary_guard_events"] > 0
    assert expression_summary["cross_region_count"] == 0

    consecutive = history_summary["consecutive_flag_counts"]
    assert int(consecutive.get("busy") or 0) == 0
    assert int(consecutive.get("tail_push") or 0) == 0

    assert piano_audit.summary["medium_swing_open_drop_top_note_ge_75_events"] == 0
    assert piano_audit.summary["medium_swing_open_drop_voice_leading_warning_events"] == 0


def test_v2_6_69_acceptance_contract_accepts_realistic_summarized_checkpoint_rows() -> None:
    static_audit = build_static_audit()
    output = {
        "ok": True,
        "slug": "fixture",
        "performance_choruses": 3,
        "piano_pattern_events": 144,
        "pattern_summary": {
            "history_metadata_events": 144,
            "forbidden_expression_key_events": 0,
            "forbidden_voicing_key_events": 0,
            "bar_first_two_chord_bar_events": 0,
        },
        "history_summary": {"consecutive_flag_counts": {"busy": 0, "tail_push": 0}},
        "expression_summary": {
            "piano_expression_events": 144,
            "calibrated_expression_events": 144,
            "hold_boundary_guard_events": 88,
            "cross_region_count": 0,
        },
        "voicing_summary": {"top_note_ge_75_events": 0, "voice_leading_warning_events": 0},
    }

    acceptance = _acceptance(static_audit, [output])
    assert acceptance["passed"] is True
    assert all(check["passed"] for check in acceptance["checks"])
