from __future__ import annotations

# harness token: test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_PHASE_SUMMARY_AND_HANDOFF_V2_6_44.md"
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
            "output_path": str(tmp_path / "misty_v2_6_44.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_44_doc_exists_and_declares_phase_handoff_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_44",
        "Ballad SPREAD Voicing Phase Summary and Handoff",
        "behavior-preserving",
        "Accepted guardrails",
        "2+3  main stable 5-note body",
        "1+4  low-frequency 5-note color lane",
        "State-anchor rule remains",
        "Medium Swing open/drop method-lock calibration",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text


def test_v2_6_44_policy_declares_phase_summary_handoff() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_voicing_phase_summary_and_handoff") or {})

    assert plan["version"] == "v2_6_44"
    assert plan["scope"] == "voicing_only_phase_summary_and_handoff"
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["freezes_current_density_lane"] is True
    assert plan["freezes_current_gap_guardrails"] is True
    assert plan["freezes_current_safe_extension_policy"] is True
    assert plan["handoff_ready"] is True
    assert plan["accepted_reference"] == "Misty / Jazz Ballad / 3 choruses / seed 26912"
    assert plan["accepted_guardrails"]["densities"] == {"5": 124, "6": 72}
    assert plan["accepted_guardrails"]["groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["ballad_spread_voicing_phase_summary_and_handoff_enabled"] is True
    assert metadata["ballad_spread_voicing_phase_summary_and_handoff_version"] == "v2_6_44"
    assert metadata["ballad_spread_voicing_phase_summary_and_handoff_behavior_preserving"] is True


def test_v2_6_44_misty_guardrails_are_frozen(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert summary["densities"] == {"5": 124, "6": 72}
    assert summary["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert summary["densities"].get("4", 0) == 0
    assert summary["densities"].get("7", 0) == 0
    assert summary["lower_upper_group_gap_too_tight_events"] == 0
    assert summary["lower_upper_group_gap_too_wide_events"] == 0
    assert summary["top_note_max"] <= 74
    assert summary["top_note_ge_75_events"] == 0
    assert summary["major_seventh_unnotated_sharp11_events"] == 0
    assert summary["lower_foundation_span_violation_events"] == 0
    assert summary["post_continuity_checkpoint_passed"] is True
    assert summary["same_chord_reattack_continuity_checkpoint_passed"] is True
    assert summary["spread_phrase_state_boundary_review_warning_events"] == 0


def test_v2_6_44_phase_summary_audit_reports_handoff_ready(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert summary["ballad_spread_voicing_phase_summary_version"] == "v2_6_44"
    assert summary["ballad_spread_voicing_phase_summary_behavior_preserving"] is True
    assert summary["ballad_spread_voicing_phase_summary_handoff_ready"] is True

    guardrails = summary["ballad_spread_voicing_phase_summary_frozen_guardrails"]
    assert guardrails["density_counts"] == {"5": 124, "6": 72}
    assert guardrails["grouping_counts"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert guardrails["disabled_default_densities"] == {"4": 0, "7": 0}
    assert guardrails["lower_upper_too_tight_events"] == 0
    assert guardrails["lower_upper_too_wide_events"] == 0
    assert guardrails["top_note_max_allowed"] == 74
    assert guardrails["unnotated_major_seventh_sharp11_events"] == 0
    assert guardrails["phrase_state_boundary_warning_events"] == 0


def test_v2_6_44_phase_milestones_and_next_areas_are_explicit(tmp_path: Path) -> None:
    summary = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    milestones = summary["ballad_spread_voicing_phase_summary_completed_milestones"]
    assert milestones[0] == "v2_6_30_1plus4_lower_foundation_calibration"
    assert "v2_6_40_state_anchor_policy_boundary" in milestones
    assert "v2_6_43_lower_foundation_weight_register_final_pass" in milestones

    next_areas = summary["ballad_spread_voicing_phase_summary_next_candidate_areas"]
    assert next_areas == [
        "medium_swing_open_drop_method_lock_calibration",
        "bossa_voicing_policy_boundary_and_default_texture",
        "upper_structure_policy_gated_runtime_expansion",
        "minor_dominant_altered_light_gate_plan",
    ]
