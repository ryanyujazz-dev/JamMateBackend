from __future__ import annotations

# harness token: test_v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration

import json
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.voicing import ContentFamily, RootSupportPolicy
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_SAFE_EXTENSION_FREQUENCY_CALIBRATION_V2_6_42.md"
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
            "output_path": str(tmp_path / "misty_v2_6_42.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_42_doc_exists_and_declares_safe_extension_frequency_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_42",
        "Safe Extension Frequency Calibration",
        "major-seventh default safe colors",
        "9 / 13",
        "unnotated major-seventh #11",
        "explicit chart #11",
        "harmonic-color intent",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text


def test_v2_6_42_policy_declares_warm_major_seventh_safe_extension_rule() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_safe_extension_frequency_calibration") or {})

    assert plan["version"] == "v2_6_42"
    assert plan["scope"] == "voicing_only_safe_extension_frequency_audit"
    assert plan["major_seventh_default_preferred_colors"] == ["9", "13"]
    assert plan["major_seventh_sharp11_default"] == "disabled_unless_explicit_symbol_or_harmonic_color_intent"
    assert plan["expected_misty_three_chorus_unnotated_sharp11_events"] == 0
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["ballad_spread_safe_extension_frequency_calibration_enabled"] is True
    assert metadata["ballad_spread_safe_extension_frequency_calibration_version"] == "v2_6_42"
    assert metadata["ballad_major_seventh_default_safe_extension_colors"] == ["9", "13"]
    assert metadata["ballad_major_seventh_sharp11_default_enabled"] is False
    assert metadata["ballad_major_seventh_sharp11_requires_explicit_symbol_or_harmonic_color_intent"] is True


def test_v2_6_42_default_content_pool_still_excludes_unnotated_maj7_sharp11() -> None:
    policy = get_voicing_policy()
    upper3_policy = replace(
        policy,
        allowed_content=(ContentFamily.SHELL_PLUS_COLOR,),
        preferred_content=None,
        root_support=RootSupportPolicy.ROOT_OPTIONAL,
        preferred_density=3,
        min_density=3,
        max_density=3,
    )

    recipes = plan_content_recipes("Ebmaj7", upper3_policy)
    degree_sets = {tuple(recipe.degree_names) for recipe in recipes}

    assert ("3", "7", "9") in degree_sets
    assert ("3", "7", "13") in degree_sets
    assert all("#11" not in degrees for degrees in degree_sets)


def test_v2_6_42_misty_guardrails_remain_behavior_preserving(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["post_continuity_checkpoint_passed"] is True
    assert audit["same_chord_reattack_continuity_checkpoint_passed"] is True
    assert audit["spread_phrase_state_boundary_review_warning_events"] == 0


def test_v2_6_42_misty_major_seventh_safe_extension_frequency(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug)
    summary = audit.summary

    assert summary["ballad_spread_safe_extension_frequency_calibration_version"] == "v2_6_42"
    assert summary["major_seventh_safe_extension_events"] == 60
    assert summary["major_seventh_safe_extension_color_events"] == 21
    assert summary["major_seventh_safe_extension_warm_color_events"] == 21
    assert summary["major_seventh_safe_extension_degree_counts"] == {"13": 7, "9": 14}
    assert summary["major_seventh_safe_extension_degree_counts_by_chord"] == {
        "Ebmaj7": {"13": 6, "9": 2},
        "Abmaj7": {"9": 12, "13": 1},
        "Bbmaj7": {},
    }
    assert summary["major_seventh_safe_extension_non_safe_color_events_by_chord"] == {}
    assert summary["major_seventh_unnotated_sharp11_events"] == 0
    assert summary["major_seventh_explicit_sharp11_events"] == 0
    assert summary["major_seventh_safe_extension_preferred_colors"] == ["9", "13"]
    assert summary["major_seventh_safe_extension_checkpoint_passed"] is True

    maj7_rows = [row for row in audit.event_rows if "maj7" in str(row.get("chord_symbol"))]
    assert len(maj7_rows) == 60
    for row in maj7_rows:
        assert "#11" not in row["degrees"]
