from __future__ import annotations

# harness token: test_v2_6_43_engine_ballad_spread_lower_foundation_weight_register_final_pass

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_LOWER_FOUNDATION_WEIGHT_REGISTER_FINAL_PASS_V2_6_43.md"
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
            "output_path": str(tmp_path / "misty_v2_6_43.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_43_doc_exists_and_declares_lower_foundation_final_pass() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_43",
        "Lower Foundation Weight / Register Final Pass",
        "2+3  should not become thin",
        "2+4  may be heavier",
        "1+4  should remain a low-frequency color lane",
        "3+3  should remain very low frequency",
        "behavior-preserving",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text


def test_v2_6_43_policy_declares_lower_foundation_final_pass_boundary() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_lower_foundation_weight_register_final_pass") or {})

    assert plan["version"] == "v2_6_43"
    assert plan["scope"] == "voicing_only_lower_foundation_weight_register_checkpoint"
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["keeps_1plus4_low_frequency"] is True
    assert plan["lower_group_span_limit_semitones"] == 12
    assert plan["low_register_threshold"] == 43
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["ballad_spread_lower_foundation_weight_register_final_pass_enabled"] is True
    assert metadata["ballad_spread_lower_foundation_weight_register_final_pass_version"] == "v2_6_43"
    assert metadata["ballad_spread_lower_foundation_weight_register_final_pass_behavior_preserving"] is True


def test_v2_6_43_misty_guardrails_remain_behavior_preserving(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert summary["densities"] == {"5": 124, "6": 72}
    assert summary["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert summary["densities"].get("4", 0) == 0
    assert summary["densities"].get("7", 0) == 0
    assert summary["lower_upper_group_gap_too_tight_events"] == 0
    assert summary["lower_upper_group_gap_too_wide_events"] == 0
    assert summary["top_note_max"] <= 74
    assert summary["top_note_ge_75_events"] == 0
    assert summary["post_continuity_checkpoint_passed"] is True
    assert summary["same_chord_reattack_continuity_checkpoint_passed"] is True
    assert summary["major_seventh_unnotated_sharp11_events"] == 0


def test_v2_6_43_lower_foundation_final_profile(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert summary["ballad_spread_lower_foundation_weight_register_final_pass_version"] == "v2_6_43"
    assert summary["lower_foundation_weight_register_final_pass_behavior_preserving"] is True
    assert summary["lower_foundation_weight_register_final_pass_density_lane_unchanged"] is True
    assert summary["lower_foundation_weight_register_final_pass_grouping_mix_unchanged"] is True
    assert summary["lower_foundation_weight_register_final_pass_low_register_threshold"] == 43
    assert summary["lower_foundation_weight_register_final_pass_checkpoint_passed"] is True

    assert summary["lower_foundation_note_min"] == 41
    assert summary["lower_foundation_note_max"] == 58
    assert summary["lower_foundation_note_average"] == 49.93
    assert summary["lower_foundation_span_max"] == 11
    assert summary["lower_foundation_span_average"] == 6.138
    assert summary["lower_foundation_span_violation_events"] == 0
    assert summary["lower_foundation_low_register_events"] == 28
    assert summary["lower_foundation_low_register_events_by_grouping"] == {"2+4": 26, "2+3": 2}
    assert summary["lower_foundation_recipe_counts"] == {
        "lower_2note_root_3": 109,
        "lower_2note_root_7": 73,
        "lower_1note_root": 10,
        "lower_3note_root_3_7": 4,
    }


def test_v2_6_43_lower_foundation_grouping_roles_are_accepted(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary
    profile = summary["lower_foundation_weight_register_final_pass_profile_by_grouping"]

    assert summary["lower_foundation_weight_register_final_pass_2plus3_not_too_thin"] is True
    assert summary["lower_foundation_weight_register_final_pass_2plus4_pressure_accepted"] is True
    assert summary["lower_foundation_weight_register_final_pass_3plus3_no_low_mud"] is True
    assert summary["lower_foundation_weight_register_final_pass_1plus4_low_frequency_role_preserved"] is True

    assert profile["2+3"]["event_count"] == 114
    assert profile["2+3"]["note_average"] == 51.855
    assert profile["2+3"]["low_register_events"] == 2
    assert profile["2+3"]["gap_min"] == 5
    assert profile["2+3"]["gap_max"] == 7

    assert profile["2+4"]["event_count"] == 68
    assert profile["2+4"]["note_average"] == 46.603
    assert profile["2+4"]["low_register_events"] == 26
    assert profile["2+4"]["gap_min"] == 2
    assert profile["2+4"]["gap_max"] == 7

    assert profile["1+4"]["event_count"] == 10
    assert profile["1+4"]["note_average"] == 48.4
    assert profile["1+4"]["low_register_events"] == 0
    assert profile["1+4"]["gap_average"] == 4

    assert profile["3+3"]["event_count"] == 4
    assert profile["3+3"]["note_average"] == 52.333
    assert profile["3+3"]["span_max"] == 10
    assert profile["3+3"]["low_register_events"] == 0
