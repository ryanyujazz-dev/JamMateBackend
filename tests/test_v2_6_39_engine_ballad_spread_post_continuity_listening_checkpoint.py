from __future__ import annotations

# harness token: test_v2_6_39_engine_ballad_spread_post_continuity_listening_checkpoint

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_POST_CONTINUITY_LISTENING_CHECKPOINT_V2_6_39.md"
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
            "output_path": str(tmp_path / "misty_v2_6_39.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_39_doc_exists_and_declares_checkpoint_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_39",
        "Post-Continuity Listening Checkpoint",
        "observational only",
        "density lane stays stable",
        "Misty bars 41, 63, and 95",
        "Voicing selector: no candidate/source/density changes",
        "Pattern",
        "Anticipation",
        "Expression",
        "Realizer",
        "MIDI writer",
        "Agent / API / HarmonyOS",
    ):
        assert token in text


def test_v2_6_39_policy_declares_observational_checkpoint() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_post_continuity_listening_checkpoint") or {})

    assert plan["version"] == "v2_6_39"
    assert plan["scope"] == "voicing_checkpoint_after_ballad_continuity_bugfix"
    assert plan["observational_only"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["confirms_v2_6_38_problem_bars"] == [41, 63, 95]
    assert plan["confirms_state_anchor_boundary"] is True
    assert plan["keeps_density_lane_unchanged"] is True
    assert plan["keeps_1plus4_low_frequency"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["ballad_spread_post_continuity_listening_checkpoint_enabled"] is True
    assert metadata["ballad_spread_post_continuity_listening_checkpoint_version"] == "v2_6_39"
    assert metadata["ballad_spread_post_continuity_listening_checkpoint_observational_only"] is True


def test_v2_6_39_misty_voicing_guardrails_remain_after_continuity_patch(tmp_path: Path) -> None:
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


def test_v2_6_39_post_continuity_checkpoint_marks_problem_bars(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug)
    summary = audit.summary

    assert summary["ballad_spread_post_continuity_listening_checkpoint_version"] == "v2_6_39"
    assert summary["post_continuity_problem_bars_checked"] == [41, 63, 95]
    assert summary["post_continuity_problem_bars_found"] == [41, 63, 95]
    assert summary["post_continuity_problem_bar_retouch_events"] == 3
    assert summary["post_continuity_foundation_sustain_events"] == 3
    assert summary["post_continuity_projection_only_retouch_events"] == 3
    assert summary["post_continuity_anchor_projection_trim_events"] == 3
    assert summary["post_continuity_warning_events"] == 0
    assert summary["post_continuity_checkpoint_passed"] is True

    rows = [row for row in audit.event_rows if row.get("post_continuity_listening_checkpoint_applied")]
    assert [row["post_continuity_problem_bar"] for row in rows] == [41, 63, 95]
    for row in rows:
        assert row["post_continuity_retouch_projection_only"] is True
        assert row["post_continuity_foundation_notes_sustaining_through_retouch"] >= 2
        assert row["post_continuity_projection_notes_trimmed_to_retouch_start"] >= 3
        assert row["post_continuity_warning"] is False
        assert row["post_continuity_no_voicing_selector_change"] is True


def test_v2_6_39_state_anchor_boundary_still_passes_after_continuity_patch(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug).summary

    assert audit["spread_phrase_scope_wide_gap_candidate_availability_events"] == 2
    assert audit["spread_phrase_scope_wide_gap_state_advance_protected_events"] == 2
    assert audit["spread_phrase_scope_wide_gap_runtime_realization_enabled_events"] == 2
    assert audit["spread_phrase_state_boundary_helper_cleanup_events"] == 2
    assert audit["spread_phrase_state_boundary_helper_state_anchor_events"] == 2
    assert audit["spread_phrase_state_boundary_review_events"] == 2
    assert audit["spread_phrase_state_boundary_review_next_events_found"] == 2
    assert audit["spread_phrase_state_boundary_review_state_anchor_matches_override_events"] == 2
    assert audit["spread_phrase_state_boundary_review_realized_notes_not_used_as_state_events"] == 2
    assert audit["spread_phrase_state_boundary_review_voice_leading_previous_matches_override_events"] == 2
    assert audit["spread_phrase_state_boundary_review_warning_events"] == 0
