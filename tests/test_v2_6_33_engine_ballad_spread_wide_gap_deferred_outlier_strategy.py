from __future__ import annotations

# harness token: test_v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_WIDE_GAP_DEFERRED_OUTLIER_STRATEGY_V2_6_33.md"
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
            "output_path": str(tmp_path / "misty_v2_6_33.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_33_doc_exists_and_states_deferred_voicing_only_strategy() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_33",
        "Wide Gap Deferred Outlier Strategy",
        "voicing-only",
        "2+3 Fm7",
        "same-recipe",
        "not a broad scorer",
        "runtime replacement remains disabled",
        "density lane unchanged",
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


def test_v2_6_33_policy_declares_deferred_wide_gap_strategy() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    strategy = dict(metadata.get("ballad_spread_wide_gap_deferred_outlier_strategy") or {})

    assert strategy["version"] == "v2_6_33"
    assert strategy["scope"] == "voicing_only_same_recipe_wide_gap_deferred_micro_bias"
    assert strategy["target"] == "remaining 2+3 Fm7 wide gap outliers from v2_6_32"
    assert strategy["same_recipe_only"] is True
    assert strategy["not_broad_scorer"] is True
    assert strategy["keeps_density_lane_unchanged"] is True
    assert strategy["keeps_1plus4_low_frequency"] is True
    assert strategy["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_wide_gap_deferred_outlier_strategy_enabled"] is True
    assert metadata["spread_wide_gap_deferred_outlier_strategy_version"] == "v2_6_33"
    assert float(metadata["spread_wide_gap_deferred_same_recipe_max_primary_cost_delta"]) == 4.8
    assert metadata["spread_gap_aware_candidate_scope_micro_calibration_version"] == "v2_6_33"


def test_v2_6_33_misty_preserves_density_lane_and_keeps_wide_gap_auditable(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["functional_groupings"]["1+4"] == 10

    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["low_note_min"] >= 40
    assert audit["lower_foundation_span_violation_events"] == 0

    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0
    assert audit["spread_wide_gap_deferred_outlier_strategy_events_by_grouping"] == {"2+3": 2}


def test_v2_6_33_audit_records_deferred_same_recipe_alternatives_without_runtime_replacement(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["spread_gap_aware_candidate_scope_micro_calibration_version"] == "v2_6_33"
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events"] == 3
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events_by_recipe"] == {"spread_2plus4_contract": 3}
    assert audit["spread_gap_aware_candidate_scope_micro_calibration_events_by_grouping"] == {"2+4": 3}
    assert audit["spread_gap_aware_original_gap_min"] == 1
    assert audit["spread_gap_aware_replacement_gap_max"] == 3

    assert audit["spread_wide_gap_deferred_outlier_strategy_version"] == "v2_6_33"
    assert audit["spread_wide_gap_deferred_outlier_strategy_events"] == 2
    assert audit["spread_wide_gap_deferred_outlier_strategy_deferred_events"] == 2
    assert audit["spread_wide_gap_deferred_outlier_strategy_events_by_recipe"] == {"spread_2plus3_contract": 2}
    assert audit["spread_wide_gap_deferred_outlier_strategy_events_by_grouping"] == {"2+3": 2}
    assert audit["spread_wide_gap_deferred_original_gap_min"] == 12
    assert audit["spread_wide_gap_deferred_original_gap_max"] == 12
    assert audit["spread_wide_gap_deferred_replacement_gap_min"] == 5
    assert audit["spread_wide_gap_deferred_replacement_gap_max"] == 5


def test_v2_6_33_event_rows_mark_wide_gap_as_deferred_not_replaced(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    deferred = [
        row
        for row in audit.event_rows
        if row.get("spread_wide_gap_deferred_outlier_strategy_deferred") is True
    ]

    assert len(deferred) == 2
    assert {row["chord_symbol"] for row in deferred} == {"Fm7"}
    assert {row["functional_grouping"] for row in deferred} == {"2+3"}
    assert {row["recipe_id"] for row in deferred} == {"spread_2plus3_contract"}
    assert {row["group_gap_semitones"] for row in deferred} == {7}
    assert {row["spread_wide_gap_deferred_original_gap"] for row in deferred} == {12.0}
    assert {row["spread_wide_gap_deferred_best_replacement_gap"] for row in deferred} == {5.0}
    assert {row["spread_wide_gap_deferred_top_stable_replacement_gap"] for row in deferred} == {7.0}
    assert {row["spread_wide_gap_deferred_candidate_count"] for row in deferred} == {13}
    assert {row["spread_wide_gap_deferred_runtime_replacement_enabled"] for row in deferred} == {False}
    assert {row["spread_wide_gap_deferred_same_recipe_only"] for row in deferred} == {True}
    assert {row["spread_wide_gap_deferred_density_lane_unchanged"] for row in deferred} == {True}
    assert {row["spread_wide_gap_deferred_not_broad_scorer"] for row in deferred} == {True}
    assert {row["spread_wide_gap_deferred_reason"] for row in deferred} == {
        "runtime_replacement_deferred_to_avoid_density_lane_cascade"
    }

    for row in deferred:
        assert row["spread_wide_gap_deferred_best_replacement_primary_cost"] <= (
            row["spread_wide_gap_deferred_original_primary_cost"]
            + row["spread_wide_gap_deferred_max_primary_cost_delta"]
        )
