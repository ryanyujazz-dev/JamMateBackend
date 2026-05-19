from __future__ import annotations

# harness token: test_v2_6_34_engine_ballad_spread_2plus3_wide_gap_source_inventory_plan

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_2PLUS3_WIDE_GAP_SOURCE_INVENTORY_PLAN_V2_6_34.md"
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
            "output_path": str(tmp_path / "misty_v2_6_34.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_34_doc_exists_and_states_source_inventory_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_34",
        "2+3 Wide Gap Source Inventory Plan",
        "voicing-only",
        "source-inventory",
        "runtime replacement",
        "density-lane cascade",
        "5-note:183 / 6-note:13",
        "phrase-scope or source-inventory-level candidate availability",
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


def test_v2_6_34_policy_declares_source_inventory_plan_without_runtime_replacement() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    plan = dict(metadata.get("ballad_spread_2plus3_wide_gap_source_inventory_plan") or {})

    assert plan["version"] == "v2_6_34"
    assert plan["scope"] == "voicing_only_source_inventory_plan_and_audit"
    assert plan["target"] == "remaining 2+3 Fm7 wide gap outliers from v2_6_33"
    assert plan["same_recipe_only"] is True
    assert plan["not_broad_scorer"] is True
    assert plan["runtime_replacement_enabled"] is False
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_wide_gap_source_inventory_plan_enabled"] is True
    assert metadata["spread_wide_gap_source_inventory_plan_version"] == "v2_6_34"
    assert metadata["spread_wide_gap_source_inventory_runtime_replacement_enabled"] is False


def test_v2_6_34_misty_preserves_v2_6_33_runtime_guardrails(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["lower_foundation_span_violation_events"] == 0
    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0


def test_v2_6_34_audit_summarizes_source_inventory_plan(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["spread_wide_gap_source_inventory_plan_version"] == "v2_6_34"
    assert audit["spread_wide_gap_source_inventory_plan_events"] == 2
    assert audit["spread_wide_gap_source_inventory_plan_events_by_recipe"] == {"spread_2plus3_contract": 2}
    assert audit["spread_wide_gap_source_inventory_plan_events_by_grouping"] == {"2+3": 2}
    assert audit["spread_wide_gap_source_inventory_best_replacement_gap_min"] == 5
    assert audit["spread_wide_gap_source_inventory_best_replacement_gap_max"] == 5
    assert audit["spread_wide_gap_source_inventory_top_stable_replacement_gap_min"] == 7
    assert audit["spread_wide_gap_source_inventory_top_stable_replacement_gap_max"] == 7
    assert audit["spread_wide_gap_source_inventory_runtime_replacement_enabled_events"] == 0
    assert audit["spread_wide_gap_source_inventory_recommended_next_boundaries"] == {
        "phrase_scope_or_inventory_level_candidate_availability_not_runtime_replacement": 2
    }


def test_v2_6_34_event_rows_expose_inventory_alternatives_without_replacement(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    rows = [row for row in audit.event_rows if row.get("spread_wide_gap_source_inventory_plan_active")]

    assert len(rows) == 2
    assert {row["chord_symbol"] for row in rows} == {"Fm7"}
    assert {row["recipe_id"] for row in rows} == {"spread_2plus3_contract"}
    assert {row["functional_grouping"] for row in rows} == {"2+3"}
    assert {row["group_gap_semitones"] for row in rows} == {7}
    assert {row["spread_wide_gap_source_inventory_original_gap"] for row in rows} == {12.0}
    assert {row["spread_wide_gap_source_inventory_plan_version"] for row in rows} == {"v2_6_34"}
    assert {row["spread_wide_gap_source_inventory_candidate_count"] for row in rows} == {13}
    assert {row["spread_wide_gap_source_inventory_comfort_candidate_count"] for row in rows} == {13}
    assert {row["spread_wide_gap_source_inventory_best_replacement_gap"] for row in rows} == {5.0}
    assert {row["spread_wide_gap_source_inventory_top_stable_replacement_gap"] for row in rows} == {7.0}
    assert {tuple(row["spread_wide_gap_source_inventory_original_upper_source_degrees"]) for row in rows} == {("b3", "b7", "11")}
    assert {tuple(row["spread_wide_gap_source_inventory_best_replacement_upper_source_degrees"]) for row in rows} == {("b3", "b7", "9")}
    assert {tuple(row["spread_wide_gap_source_inventory_top_stable_upper_source_degrees"]) for row in rows} == {("b3", "b7", "11")}
    assert {row["spread_wide_gap_source_inventory_runtime_replacement_enabled"] for row in rows} == {False}
    assert {row["spread_wide_gap_source_inventory_density_lane_unchanged"] for row in rows} == {True}
    assert {row["spread_wide_gap_source_inventory_not_broad_scorer"] for row in rows} == {True}
    assert {row["spread_wide_gap_source_inventory_recommended_next_boundary"] for row in rows} == {
        "phrase_scope_or_inventory_level_candidate_availability_not_runtime_replacement"
    }
