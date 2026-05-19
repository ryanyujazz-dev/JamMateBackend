from __future__ import annotations

# harness token: test_v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_review

from pathlib import Path
import json

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_BOUNDARY_REGRESSION_REVIEW_V2_6_36.md"
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
            "output_path": str(tmp_path / "misty_v2_6_36.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_36_doc_exists_and_declares_observational_boundary_review() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "v2_6_36",
        "Phrase-State Boundary Regression Review",
        "voicing-only audit / regression pass",
        "does not generalize",
        "protected phrase anchor",
        "observational audit fields",
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


def test_v2_6_36_policy_declares_boundary_review_without_runtime_change() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})
    plan = dict(metadata.get("ballad_spread_phrase_state_boundary_regression_review") or {})

    assert plan["version"] == "v2_6_36"
    assert plan["scope"] == "voicing_only_phrase_state_boundary_audit"
    assert plan["target"] == "state-protected events introduced by v2_6_35"
    assert plan["observational_only"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["checks_next_event_uses_state_anchor"] is True
    assert plan["checks_realized_notes_not_used_as_state"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["spread_phrase_state_boundary_regression_review_enabled"] is True
    assert metadata["spread_phrase_state_boundary_regression_review_version"] == "v2_6_36"
    assert metadata["spread_phrase_state_boundary_regression_review_observational_only"] is True


def test_v2_6_36_misty_guardrails_remain_unchanged(tmp_path: Path) -> None:
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


def test_v2_6_36_summary_reviews_next_event_state_boundary(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["spread_phrase_state_boundary_review_version"] == "v2_6_36"
    assert audit["spread_phrase_state_boundary_review_events"] == 2
    assert audit["spread_phrase_state_boundary_review_next_events_found"] == 2
    assert audit["spread_phrase_state_boundary_review_state_anchor_matches_override_events"] == 2
    assert audit["spread_phrase_state_boundary_review_realized_notes_not_used_as_state_events"] == 2
    assert audit["spread_phrase_state_boundary_review_voice_leading_previous_matches_override_events"] == 2
    assert audit["spread_phrase_state_boundary_review_warning_events"] == 0
    assert audit["spread_phrase_state_boundary_review_next_event_top_motion_max"] == 0.0
    assert audit["spread_phrase_state_boundary_review_next_event_voice_leading_distance_max"] == 5.333
    assert audit["spread_phrase_state_boundary_review_next_event_smoothness_labels"] == {"moderate": 2}


def test_v2_6_36_event_rows_show_next_state_uses_anchor_not_realized_substitute(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    rows = [row for row in audit.event_rows if row.get("spread_phrase_state_boundary_review_applied")]

    assert len(rows) == 2
    for row in rows:
        assert row["spread_phrase_state_boundary_review_state_anchor_matches_override"] is True
        assert row["spread_phrase_state_boundary_review_voice_leading_previous_matches_override"] is True
        assert row["spread_phrase_state_boundary_review_realized_notes_not_used_as_state"] is True
        assert row["spread_phrase_state_boundary_review_warning"] is False
        assert row["spread_phrase_state_boundary_review_no_runtime_change"] is True
        assert tuple(row["spread_phrase_scope_wide_gap_realized_notes"]) == (41, 51, 58, 63, 68)
        assert tuple(row["spread_phrase_scope_wide_gap_state_advance_override_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["spread_phrase_state_boundary_review_next_midi_notes"]) == (46, 50, 53, 62, 68, 70)
        assert row["spread_phrase_state_boundary_review_next_top_motion"] == 0.0
        assert row["spread_phrase_state_boundary_review_next_voice_leading_distance"] == 5.333
        assert row["spread_phrase_state_boundary_review_next_smoothness_label"] == "moderate"

    after_rows = [row for row in audit.event_rows if row.get("spread_phrase_state_boundary_review_after_protected_event")]
    assert len(after_rows) == 2
    for row in after_rows:
        assert tuple(row["previous_voicing_state_previous_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["voice_leading_previous_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["spread_phrase_state_boundary_review_previous_override_notes"]) == (41, 51, 63, 68, 70)
        assert tuple(row["spread_phrase_state_boundary_review_previous_realized_notes"]) == (41, 51, 58, 63, 68)
        assert row["spread_phrase_state_boundary_review_state_anchor_matches_override"] is True
