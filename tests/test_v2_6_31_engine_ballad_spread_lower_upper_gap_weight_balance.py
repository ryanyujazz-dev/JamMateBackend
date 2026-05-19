from __future__ import annotations

# harness token: test_v2_6_31_engine_ballad_spread_lower_upper_gap_weight_balance

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_LOWER_UPPER_GAP_WEIGHT_BALANCE_V2_6_31.md"
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
            "output_path": str(tmp_path / "misty_v2_6_31.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_31_doc_exists_and_states_voicing_only_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_31",
        "lower/upper gap",
        "weight balance",
        "voicing-only",
        "audit",
        "5-note",
        "6-note",
        "6:4",
        "1+4",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
    ]
    for token in required:
        assert token in text


def test_v2_6_31_policy_declares_gap_balance_audit_without_density_lane_change() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    calibration = dict(metadata.get("ballad_spread_lower_upper_gap_weight_balance") or {})

    assert calibration["version"] == "v2_6_31"
    assert calibration["scope"] == "voicing_only_audit_and_guardrail"
    assert calibration["keeps_density_lane_unchanged"] is True
    assert calibration["keeps_1plus4_low_frequency"] is True
    assert calibration["tracks_lower_upper_gap_by_grouping_density_and_recipe"] is True
    assert calibration["gap_comfort_band_semitones"] == [2, 7]
    assert calibration["does_not_change_pattern_anticipation_expression_or_midi"] is True

    # v2_6_31 must not silently retune the v2_6_30 density/1+4 weights.
    weights_by_scene = metadata["ballad_spread_grouping_mix_policy"]["weights_by_scene"]
    assert int(weights_by_scene["normal_comping"]["spread_1plus4_contract"]) == 4
    assert int(weights_by_scene["chorus_lift"]["spread_1plus4_contract"]) == 3
    assert int(weights_by_scene["ending_climax"]["spread_1plus4_contract"]) == 0
    assert float(metadata["spread_grouping_mix_selected_6note_contract_bias"]) == 3.0


def test_v2_6_31_misty_gap_audit_preserves_v2_6_30_density_and_register_guardrails(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert 4 <= audit["functional_groupings"]["1+4"] <= 10
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["low_note_min"] >= 40
    assert audit["lower_foundation_span_violation_events"] == 0


def test_v2_6_31_lower_upper_gap_audit_exposes_gap_outliers_by_grouping_density_and_recipe(tmp_path: Path) -> None:
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

    by_density = audit["lower_upper_group_gap_by_density"]
    by_recipe = audit["lower_upper_group_gap_by_recipe"]
    assert by_density["5"]["count"] == 124
    assert by_density["6"]["count"] == 72
    assert by_recipe["spread_2plus3_contract"]["max"] == 7
    assert by_recipe["spread_2plus4_contract"]["min"] == 2
