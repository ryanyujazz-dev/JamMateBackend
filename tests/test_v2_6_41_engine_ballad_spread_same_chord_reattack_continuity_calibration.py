from __future__ import annotations

# harness token: test_v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_BALLAD_SPREAD_SAME_CHORD_REATTACK_CONTINUITY_CALIBRATION_V2_6_41.md"
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
            "output_path": str(tmp_path / "misty_v2_6_41.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def test_v2_6_41_doc_exists_and_declares_same_chord_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_41",
        "Same-Chord Reattack Continuity Calibration",
        "one default voicing selection per chord region",
        "reuse cached voicing",
        "fresh revoicing only",
        "lower/foundation group should remain stable",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text


def test_v2_6_41_policy_declares_behavior_preserving_same_chord_plan() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    plan = dict(metadata.get("ballad_spread_same_chord_reattack_continuity_calibration") or {})

    assert plan["version"] == "v2_6_41"
    assert plan["scope"] == "voicing_only_same_chord_region_reattack_audit"
    assert plan["uses_existing_region_voicing_cache"] is True
    assert plan["one_default_voicing_per_chord_region"] is True
    assert plan["fresh_revoicing_only_with_explicit_escape_hatch"] is True
    assert plan["foundation_should_remain_stable"] is True
    assert plan["behavior_preserving"] is True
    assert plan["no_runtime_candidate_change"] is True
    assert plan["does_not_change_pattern_anticipation_expression_or_midi"] is True

    assert metadata["ballad_spread_same_chord_reattack_continuity_enabled"] is True
    assert metadata["ballad_spread_same_chord_reattack_continuity_version"] == "v2_6_41"


def test_v2_6_41_misty_guardrails_remain_unchanged(tmp_path: Path) -> None:
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
    assert audit["spread_phrase_state_boundary_review_warning_events"] == 0


def test_v2_6_41_same_chord_reattacks_reuse_cached_voicing(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug)
    summary = audit.summary

    assert summary["ballad_spread_same_chord_reattack_continuity_version"] == "v2_6_41"
    assert summary["same_chord_reattack_regions_reviewed"] == 46
    assert summary["same_chord_reattack_events"] == 46
    assert summary["same_chord_reattack_region_voicing_reused_events"] == 46
    assert summary["same_chord_reattack_exact_voicing_reuse_events"] == 46
    assert summary["same_chord_reattack_foundation_stable_events"] == 46
    assert summary["same_chord_reattack_projection_or_retouch_events"] == 46
    assert summary["same_chord_reattack_fresh_revoicing_events"] == 0
    assert summary["same_chord_reattack_changed_voicing_warning_events"] == 0
    assert summary["same_chord_reattack_continuity_warning_events"] == 0
    assert summary["same_chord_reattack_continuity_checkpoint_passed"] is True

    rows = [row for row in audit.event_rows if row.get("same_chord_reattack_continuity_applied")]
    assert len(rows) == 46
    for row in rows:
        assert row["same_chord_reattack_region_voicing_reused"] is True
        assert row["same_chord_reattack_exact_voicing_reuse"] is True
        assert row["same_chord_reattack_foundation_stable"] is True
        assert row["same_chord_reattack_warning"] is False
        assert row["same_chord_reattack_no_density_lane_change"] is True
        assert row["region_voicing_reused"] is True
        assert row["same_chord_reattack_continuity_metadata_version"] == "v2_6_41"
        assert row["same_chord_reattack_continuity_region_cache_reuse"] is True


def test_v2_6_41_projection_retouch_rows_keep_same_voicing_while_expression_handles_partial_retouch(tmp_path: Path) -> None:
    audit = build_piano_musical_audit(_generate_misty(tmp_path).debug)
    retouch_rows = [
        row
        for row in audit.event_rows
        if row.get("same_chord_reattack_continuity_applied")
        and row.get("gesture_type") == "inner_movement"
    ]
    assert len(retouch_rows) >= 30
    for row in retouch_rows:
        assert row["same_chord_reattack_exact_voicing_reuse"] is True
        assert row["same_chord_reattack_foundation_stable"] is True
        assert row["region_voicing_reused"] is True
