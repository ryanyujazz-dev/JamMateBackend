from __future__ import annotations

# harness token: test_v2_6_35_engine_ballad_spread_phrase_scope_wide_gap_candidate_availability

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_PHRASE_SCOPE_WIDE_GAP_CANDIDATE_AVAILABILITY_V2_6_35.md"
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
            "output_path": str(tmp_path / "misty_v2_6_35.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_35_doc_exists_and_states_phrase_scope_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_35",
        "Phrase-Scope Wide Gap Candidate Availability",
        "voicing-only",
        "state advancement",
        "state-advance override",
        "5-note:183 / 6-note:13",
        "not_broad_scorer",
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


def test_v2_6_35_policy_declares_phrase_scope_candidate_availability() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    plan = dict(metadata.get("ballad_spread_phrase_scope_wide_gap_candidate_availability") or {})

    assert plan["version"] == "v2_6_35"
    assert plan["scope"] == "voicing_only_phrase_scope_candidate_availability"
    assert plan["target"] == "remaining 2+3 Fm7 wide gap outliers from v2_6_34"
    assert plan["same_recipe_only"] is True
    assert plan["not_broad_scorer"] is True
    assert plan["uses_top_stable_candidate"] is True
    assert plan["state_advance_protected"] is True
    assert plan["runtime_realization_enabled"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_phrase_scope_wide_gap_candidate_availability_enabled"] is True
    assert metadata["spread_phrase_scope_wide_gap_candidate_availability_version"] == "v2_6_35"
    assert metadata["spread_phrase_scope_wide_gap_state_advance_protection_enabled"] is True


def test_v2_6_35_misty_fixes_wide_gap_without_density_cascade(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0

    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["lower_foundation_span_violation_events"] == 0


def test_v2_6_35_audit_summarizes_phrase_scope_fix(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["spread_phrase_scope_wide_gap_candidate_availability_version"] == "v2_6_35"
    assert audit["spread_phrase_scope_wide_gap_candidate_availability_events"] == 2
    assert audit["spread_phrase_scope_wide_gap_candidate_availability_events_by_recipe"] == {"spread_2plus3_contract": 2}
    assert audit["spread_phrase_scope_wide_gap_candidate_availability_events_by_grouping"] == {"2+3": 2}
    assert audit["spread_phrase_scope_wide_gap_original_gap_min"] == 12
    assert audit["spread_phrase_scope_wide_gap_original_gap_max"] == 12
    assert audit["spread_phrase_scope_wide_gap_realized_gap_min"] == 7
    assert audit["spread_phrase_scope_wide_gap_realized_gap_max"] == 7
    assert audit["spread_phrase_scope_wide_gap_state_advance_protected_events"] == 2
    assert audit["spread_phrase_scope_wide_gap_runtime_realization_enabled_events"] == 2


def test_v2_6_35_event_rows_realize_top_stable_candidate_but_preserve_state_anchor(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    rows = [row for row in audit.event_rows if row.get("spread_phrase_scope_wide_gap_candidate_availability_applied")]

    assert len(rows) == 2
    assert {row["chord_symbol"] for row in rows} == {"Fm7"}
    assert {row["recipe_id"] for row in rows} == {"spread_2plus3_contract"}
    assert {row["functional_grouping"] for row in rows} == {"2+3"}
    assert {row["group_gap_semitones"] for row in rows} == {7}
    assert {tuple(row["midi_notes"]) for row in rows} == {(41, 51, 58, 63, 68)}
    assert {tuple(row["spread_phrase_scope_wide_gap_original_notes"]) for row in rows} == {(41, 51, 63, 68, 70)}
    assert {tuple(row["spread_phrase_scope_wide_gap_realized_notes"]) for row in rows} == {(41, 51, 58, 63, 68)}
    assert {tuple(row["spread_phrase_scope_wide_gap_state_advance_override_notes"]) for row in rows} == {(41, 51, 63, 68, 70)}
    assert {row["spread_phrase_scope_wide_gap_original_gap"] for row in rows} == {12.0}
    assert {row["spread_phrase_scope_wide_gap_realized_gap"] for row in rows} == {7.0}
    assert {row["spread_phrase_scope_wide_gap_state_advance_protected"] for row in rows} == {True}
    assert {row["spread_phrase_scope_wide_gap_state_advance_override_enabled"] for row in rows} == {True}
    assert {row["spread_phrase_scope_wide_gap_not_broad_scorer"] for row in rows} == {True}
    assert {row["spread_phrase_scope_wide_gap_same_recipe_only"] for row in rows} == {True}
    assert {row["spread_phrase_scope_wide_gap_density_lane_guarded"] for row in rows} == {True}
    assert {row["spread_phrase_scope_wide_gap_runtime_realization_enabled"] for row in rows} == {True}
