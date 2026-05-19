from __future__ import annotations

# harness token: test_v2_6_40_engine_ballad_spread_phrase_state_anchor_policy_boundary

import json
from pathlib import Path

from jammate_engine.core.voicing.runtime.state import (
    VOICING_STATE_ADVANCE_ANCHOR_POLICY_GATE_VERSION,
    VoicingStateAdvanceAnchor,
    state_advance_anchor_allowed_by_policy,
    state_advance_notes_and_degrees,
)
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_ANCHOR_POLICY_BOUNDARY_V2_6_40.md"
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
            "output_path": str(tmp_path / "misty_v2_6_40.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_40_doc_exists_and_declares_policy_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_40",
        "Phrase-State Anchor Policy Boundary",
        "policy boundary",
        "VoicingStateAdvanceAnchor",
        "realized_notes",
        "state_anchor_notes",
        "disabled without style policy gate",
        "ballad_spread_phrase_scope_wide_gap_candidate_availability",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI writer",
        "Agent / API / HarmonyOS",
    ):
        assert token in text


def test_v2_6_40_core_anchor_consumption_requires_policy_gate() -> None:
    anchor = VoicingStateAdvanceAnchor(
        notes=(41, 51, 63, 68, 70),
        degrees=("R", "b7", "b3", "5", "9"),
        reason="test_anchor",
        policy_gate_scope="ballad_spread_phrase_scope_wide_gap_candidate_availability",
    )
    metadata = anchor.to_metadata()

    assert metadata["voicing_state_advance_anchor_policy_gate_version"] == VOICING_STATE_ADVANCE_ANCHOR_POLICY_GATE_VERSION
    assert metadata["voicing_state_advance_anchor_policy_gate_required"] is True
    assert metadata["voicing_state_advance_anchor_policy_gate_scope"] == "ballad_spread_phrase_scope_wide_gap_candidate_availability"

    assert state_advance_anchor_allowed_by_policy(metadata=metadata, policy_metadata=None) is True
    assert state_advance_anchor_allowed_by_policy(
        metadata=metadata,
        policy_metadata={"voicing_state_advance_anchor_policy_gate_enabled": False},
    ) is False
    assert state_advance_anchor_allowed_by_policy(
        metadata=metadata,
        policy_metadata={
            "voicing_state_advance_anchor_policy_gate_enabled": True,
            "voicing_state_advance_anchor_allowed_scopes": ["some_other_scope"],
        },
    ) is False
    assert state_advance_anchor_allowed_by_policy(
        metadata=metadata,
        policy_metadata={
            "voicing_state_advance_anchor_policy_gate_enabled": True,
            "voicing_state_advance_anchor_allowed_scopes": ["ballad_spread_phrase_scope_wide_gap_candidate_availability"],
        },
    ) is True

    realized_notes = [41, 51, 58, 63, 68]
    realized_degrees = ["R", "b7", "9", "b3", "5"]
    notes, degrees, resolved = state_advance_notes_and_degrees(
        metadata=metadata,
        realized_notes=realized_notes,
        realized_degrees=realized_degrees,
        policy_metadata={"voicing_state_advance_anchor_policy_gate_enabled": False},
    )
    assert notes == tuple(realized_notes)
    assert degrees == tuple(realized_degrees)
    assert resolved is None

    notes, degrees, resolved = state_advance_notes_and_degrees(
        metadata=metadata,
        realized_notes=realized_notes,
        realized_degrees=realized_degrees,
        policy_metadata={
            "voicing_state_advance_anchor_policy_gate_enabled": True,
            "voicing_state_advance_anchor_allowed_scopes": ["ballad_spread_phrase_scope_wide_gap_candidate_availability"],
        },
    )
    assert notes == (41, 51, 63, 68, 70)
    assert degrees == ("R", "b7", "b3", "5", "9")
    assert resolved is not None


def test_v2_6_40_policy_declares_narrow_state_anchor_gate() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_phrase_state_anchor_policy_boundary") or {})

    assert plan["version"] == "v2_6_40"
    assert plan["scope"] == "policy_gated_core_voicing_state_anchor"
    assert plan["core_helper"] == "VoicingStateAdvanceAnchor"
    assert plan["default_global_behavior"] == "disabled_without_style_policy_gate"
    assert plan["enabled_for_scopes"] == ["ballad_spread_phrase_scope_wide_gap_candidate_availability"]
    assert plan["not_generalized_to_other_styles"] is True
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["voicing_state_advance_anchor_policy_gate_enabled"] is True
    assert metadata["voicing_state_advance_anchor_policy_gate_version"] == "v2_6_40"
    assert metadata["voicing_state_advance_anchor_allowed_scopes"] == ["ballad_spread_phrase_scope_wide_gap_candidate_availability"]
    assert metadata["spread_phrase_state_anchor_policy_boundary_enabled"] is True


def test_v2_6_40_misty_guardrails_remain_behavior_preserving(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["lower_foundation_span_violation_events"] == 0


def test_v2_6_40_audit_marks_policy_gated_anchor_scope(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug)
    summary = audit.summary

    assert summary["spread_phrase_state_anchor_policy_boundary_version"] == "v2_6_40"
    assert summary["spread_phrase_state_anchor_policy_boundary_events"] == 2
    assert summary["spread_phrase_state_anchor_policy_boundary_gate_required_events"] == 2
    assert summary["spread_phrase_state_anchor_policy_boundary_scopes"] == {
        "ballad_spread_phrase_scope_wide_gap_candidate_availability": 2
    }
    assert summary["spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events"] == 3

    assert summary["spread_phrase_scope_wide_gap_candidate_availability_events"] == 2
    assert summary["spread_phrase_scope_wide_gap_state_advance_protected_events"] == 2
    assert summary["spread_phrase_state_boundary_review_warning_events"] == 0
    assert summary["spread_phrase_state_boundary_review_state_anchor_matches_override_events"] == 2

    rows = [row for row in audit.event_rows if row.get("spread_phrase_state_anchor_policy_boundary_applied")]
    assert len(rows) == 2
    for row in rows:
        assert row["voicing_state_advance_anchor_policy_gate_version"] == "v2_6_40"
        assert row["voicing_state_advance_anchor_policy_gate_required"] is True
        assert row["voicing_state_advance_anchor_policy_gate_scope"] == "ballad_spread_phrase_scope_wide_gap_candidate_availability"
        assert row["spread_phrase_state_anchor_policy_boundary_contract"] == "core_helper_requires_explicit_policy_gate"
        assert row["spread_phrase_state_anchor_policy_boundary_scope"] == "ballad_spread_phrase_scope_wide_gap_candidate_availability"
