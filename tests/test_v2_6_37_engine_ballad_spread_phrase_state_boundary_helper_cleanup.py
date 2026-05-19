from __future__ import annotations

# harness token: test_v2_6_37_engine_ballad_spread_phrase_state_boundary_helper_cleanup

from pathlib import Path
import json

from jammate_engine.core.voicing.runtime.state import (
    VOICING_STATE_ADVANCE_ANCHOR_HELPER_VERSION,
    VoicingStateAdvanceAnchor,
    state_advance_notes_and_degrees,
)
from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_BOUNDARY_HELPER_CLEANUP_V2_6_37.md"
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
            "output_path": str(tmp_path / "misty_v2_6_37.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_37_doc_exists_and_declares_helper_cleanup_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_37",
        "Phrase-State Boundary Helper Cleanup",
        "voicing-only helper cleanup",
        "VoicingStateAdvanceAnchor",
        "realized_notes",
        "state_anchor_notes",
        "legacy aliases",
        "Pattern",
        "Anticipation",
        "Expression",
        "Gesture",
        "MIDI writer",
        "Agent",
        "HarmonyOS",
    ]
    for token in required:
        assert token in text


def test_v2_6_37_anchor_helper_preserves_legacy_aliases_and_runtime_payload() -> None:
    anchor = VoicingStateAdvanceAnchor(
        notes=(41, 51, 63, 68, 70),
        degrees=("R", "b7", "b3", "5", "9"),
        lower_group_notes=(41, 51),
        upper_group_notes=(63, 68, 70),
        upper_group_degrees=("b3", "5", "9"),
        lower_group_placed_degrees=("R", "b7"),
        group_gap_semitones=12,
        reason="test_anchor",
    )
    metadata = anchor.to_metadata()

    assert metadata["voicing_state_advance_anchor_helper_version"] == VOICING_STATE_ADVANCE_ANCHOR_HELPER_VERSION
    assert metadata["voicing_state_advance_anchor_notes"] == [41, 51, 63, 68, 70]
    assert metadata["voicing_state_advance_override_notes"] == [41, 51, 63, 68, 70]
    assert metadata["voicing_state_advance_anchor_group_gap_semitones"] == 12
    assert metadata["voicing_state_advance_override_group_gap_semitones"] == 12

    notes, degrees, resolved = state_advance_notes_and_degrees(
        metadata=metadata,
        realized_notes=[41, 51, 58, 63, 68],
        realized_degrees=["R", "b7", "9", "b3", "5"],
    )
    assert notes == (41, 51, 63, 68, 70)
    assert degrees == ("R", "b7", "b3", "5", "9")
    assert resolved is not None
    assert resolved.to_state_metadata({})["state_advance_anchor_enabled"] is True


def test_v2_6_37_policy_declares_behavior_preserving_helper_cleanup() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    plan = dict(metadata.get("ballad_spread_phrase_state_boundary_helper_cleanup") or {})

    assert plan["version"] == "v2_6_37"
    assert plan["scope"] == "voicing_only_runtime_state_anchor_helper_cleanup"
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["helper_owner"] == "VoicingStateAdvanceAnchor"
    assert plan["selector_declares_anchor"] is True
    assert plan["resolver_consumes_anchor"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_phrase_state_boundary_helper_cleanup_enabled"] is True
    assert metadata["spread_phrase_state_boundary_helper_cleanup_version"] == "v2_6_37"
    assert metadata["spread_phrase_state_boundary_helper_cleanup_behavior_preserving"] is True


def test_v2_6_37_misty_guardrails_remain_behavior_preserving(tmp_path: Path) -> None:
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


def test_v2_6_37_event_rows_use_helper_fields_while_preserving_v2_6_36_boundary(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    summary = audit.summary

    assert summary["spread_phrase_state_boundary_helper_cleanup_version"] == "v2_6_37"
    assert summary["spread_phrase_state_boundary_helper_cleanup_events"] == 2
    assert summary["spread_phrase_state_boundary_helper_state_anchor_events"] == 2
    assert summary["spread_phrase_state_boundary_helper_legacy_alias_match_events"] == 2
    assert summary["spread_phrase_state_boundary_helper_previous_state_anchor_events"] == 3

    rows = [row for row in audit.event_rows if row.get("spread_phrase_state_boundary_helper_cleanup_applied")]
    assert len(rows) == 2
    for row in rows:
        assert row["spread_phrase_state_boundary_helper_cleanup_contract"] == "realized_notes_separate_from_state_anchor"
        assert row["spread_phrase_state_boundary_helper_cleanup_state_anchor_owner"] == "VoicingStateAdvanceAnchor"
        assert row["spread_phrase_state_boundary_helper_cleanup_resolver_consumes_anchor"] is True
        assert row["voicing_state_advance_anchor_helper_version"] == "v2_6_37"
        assert row["voicing_state_advance_anchor_enabled"] is True
        assert tuple(row["voicing_state_advance_anchor_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["spread_phrase_scope_wide_gap_state_advance_override_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["midi_notes"]) == (41, 51, 58, 63, 68)

    after_rows = [row for row in audit.event_rows if row.get("spread_phrase_state_boundary_review_after_protected_event")]
    assert len(after_rows) == 2
    for row in after_rows:
        assert row["previous_voicing_state_state_advance_anchor_enabled"] is True
        assert tuple(row["previous_voicing_state_state_advance_anchor_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["previous_voicing_state_previous_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["voice_leading_previous_notes"]) == (41, 51, 63, 68, 70)
        assert row["spread_phrase_state_boundary_review_state_anchor_matches_override"] is True
