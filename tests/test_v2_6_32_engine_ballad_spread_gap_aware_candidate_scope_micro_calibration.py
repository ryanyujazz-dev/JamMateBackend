from __future__ import annotations

# harness token: test_v2_6_32_engine_ballad_spread_gap_aware_candidate_scope_micro_calibration

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_GAP_AWARE_CANDIDATE_SCOPE_MICRO_CALIBRATION_V2_6_32.md"
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _generate_misty(tmp_path: Path):
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 26912,
            "output_path": str(tmp_path / "misty_v2_6_32.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_32_doc_exists_and_states_voicing_only_candidate_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_32",
        "Gap-Aware Candidate-Scope Micro Calibration",
        "voicing-only",
        "same-recipe",
        "2+4",
        "2+3",
        "density lane unchanged",
        "1+4",
        "top note stays <= 74",
        "Pattern",
        "Anticipation",
        "Expression",
        "Gesture",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ]
    for token in required:
        assert token in text


def test_v2_6_32_policy_declares_same_recipe_gap_micro_calibration() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    calibration = dict(metadata.get("ballad_spread_gap_aware_candidate_scope_micro_calibration") or {})

    assert calibration["version"] == "v2_6_33"
    assert calibration["scope"] == "voicing_only_same_recipe_candidate_micro_bias"
    assert calibration["runtime_scope"] == "Jazz Ballad SPREAD grouped voicing selection only"
    assert calibration["same_recipe_only"] is True
    assert calibration["keeps_density_lane_unchanged"] is True
    assert calibration["keeps_1plus4_low_frequency"] is True
    assert calibration["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_gap_aware_candidate_scope_micro_calibration_enabled"] is True
    assert metadata["spread_gap_aware_candidate_scope_micro_calibration_version"] == "v2_6_33"
    assert metadata["spread_gap_aware_comfort_min"] == 2
    assert metadata["spread_gap_aware_comfort_max"] == 7
    assert float(metadata["spread_gap_aware_same_recipe_max_primary_cost_delta"]) == 3.3
    assert int(metadata["spread_top_register_micro_soft_high"]) == 74


def test_v2_6_32_misty_fixes_tight_gap_outliers_without_reopening_retired_lanes(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["functional_groupings"]["1+4"] == 10

    five = audit["densities"]["5"]
    six = audit["densities"]["6"]
    assert 0.62 <= five / float(five + six) <= 0.64
    assert audit["functional_groupings"]["2+3"] + audit["functional_groupings"]["1+4"] == five
    assert audit["functional_groupings"]["2+4"] + audit["functional_groupings"]["3+3"] == six

    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["low_note_min"] >= 40
    assert audit["lower_foundation_span_violation_events"] == 0

    voicings = [event.get("voicing") or {} for event in result.debug.get("piano_musical_audit_events", [])]
    assert [
        voicing
        for voicing in voicings
        if "maj7" in str(voicing.get("chord_symbol"))
        and any(str(degree) == "#11" for degree in voicing.get("degrees", []))
    ] == []


def test_v2_6_32_gap_audit_records_tight_fix_and_deferred_wide_outliers(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["lower_upper_gap_audit_version"] == "v2_6_31"
    assert audit["lower_upper_gap_comfort_min"] == 2
    assert audit["lower_upper_gap_comfort_max"] == 7
    assert audit["lower_upper_group_gap_min"] == 2
    assert audit["lower_upper_group_gap_max"] == 7
    assert 5.09 <= audit["lower_upper_group_gap_average"] <= 5.11

    by_grouping = audit["lower_upper_group_gap_by_grouping"]
    assert by_grouping["2+3"] == {"count": 114, "min": 5, "max": 7, "average": 6.035}
    assert by_grouping["2+4"] == {"count": 68, "min": 2, "max": 7, "average": 3.706}
    assert by_grouping["1+4"] == {"count": 10, "min": 4, "max": 4, "average": 4}
    assert by_grouping["3+3"] == {"count": 4, "min": 5, "max": 5, "average": 5}

    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_tight_events_by_grouping"] == {}
    assert audit["lower_upper_group_gap_too_wide_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events_by_grouping"] == {}

    assert audit["spread_gap_aware_candidate_scope_micro_calibration_version"] == "v2_6_33"
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events"] == 3
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events_by_recipe"] == {"spread_2plus4_contract": 3}
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events_by_grouping"] == {"2+4": 3}
    assert audit["spread_gap_aware_original_gap_min"] == 1
    assert audit["spread_gap_aware_original_gap_max"] == 1
    assert audit["spread_gap_aware_replacement_gap_min"] == 3
    assert audit["spread_gap_aware_replacement_gap_max"] == 3


def test_v2_6_32_event_rows_mark_same_recipe_density_lane_micro_replacements(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    applied = [
        row
        for row in audit.event_rows
        if row.get("spread_gap_aware_candidate_scope_micro_calibration_applied") is True
    ]

    assert len(applied) == 3
    assert {row["functional_grouping"] for row in applied} == {"2+4"}
    assert {row["recipe_id"] for row in applied} == {"spread_2plus4_contract"}
    assert {row["spread_gap_aware_candidate_scope_micro_calibration_version"] for row in applied} == {"v2_6_33"}
    assert {row["spread_gap_aware_original_gap"] for row in applied} == {1.0}
    assert {row["spread_gap_aware_replacement_gap"] for row in applied} == {3.0}
    assert {row["spread_gap_aware_same_recipe_only"] for row in applied} == {True}
    assert {row["spread_gap_aware_density_lane_unchanged"] for row in applied} == {True}
    assert max(max(row["midi_notes"]) for row in applied) <= 74
    for row in applied:
        assert row["spread_gap_aware_replacement_primary_cost"] <= row["spread_gap_aware_original_primary_cost"] + 3.3
