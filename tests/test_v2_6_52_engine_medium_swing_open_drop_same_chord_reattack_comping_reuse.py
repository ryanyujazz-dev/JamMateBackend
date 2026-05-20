from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
LEADSHEETS = ROOT / "examples" / "leadsheets"
DOC = ROOT / "docs" / "ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_SAME_CHORD_REATTACK_COMPING_REUSE_V2_6_52.md"


def _generate(slug: str, *, tmp_path: Path, seed: int):
    score = json.loads((LEADSHEETS / f"{slug}.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": seed,
            "output_path": str(tmp_path / f"{slug}_v2_6_52.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return build_piano_musical_audit(result.debug)


def test_v2_6_52_policy_declares_same_chord_reattack_comping_reuse_contract() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    target = dict(metadata.get("medium_swing_same_chord_reattack_comping_reuse_target") or {})

    assert metadata["medium_swing_same_chord_reattack_comping_reuse_version"] == "v2_6_52"
    assert metadata["medium_swing_same_chord_reattack_comping_reuse_enabled"] is True
    assert target["scope"] == "same_chord_region"
    assert target["cache_contract"] == "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices"
    assert target["fresh_revoicing_escape_hatches"] == ["force_fresh_voicing", "revoice_within_region"]
    assert target["default_same_region_behavior"] == "reuse_cached_voicing_exactly"
    assert target["does_not_change_pattern_expression_anticipation_or_midi"] is True


def test_v2_6_52_all_the_things_you_are_same_chord_reattacks_reuse_cached_voicing(tmp_path: Path) -> None:
    audit = _generate("all_the_things_you_are", tmp_path=tmp_path, seed=3300)
    summary = audit.summary

    assert summary["medium_swing_same_chord_reattack_comping_reuse_version"] == "v2_6_52"
    reuse_events = summary["medium_swing_same_chord_reattack_comping_reuse_events"]
    assert reuse_events >= 54
    assert summary["medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_exact_voicing_reuse_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_foundation_stable_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_fresh_revoicing_events"] == 0
    assert summary["medium_swing_same_chord_reattack_comping_reuse_warning_events"] == 0
    assert summary["medium_swing_same_chord_reattack_comping_reuse_checkpoint_passed"] is True

    rows = [row for row in audit.event_rows if row.get("same_chord_reattack_continuity_applied")]
    assert len(rows) == reuse_events
    assert all(row["same_chord_reattack_region_voicing_reused"] is True for row in rows)
    assert all(row["same_chord_reattack_exact_voicing_reuse"] is True for row in rows)
    assert all(row["same_chord_reattack_foundation_stable"] is True for row in rows)
    assert all(row["same_chord_reattack_warning"] is False for row in rows)
    assert all(row["disposition_projection_family"] == "open" for row in rows)


def test_v2_6_52_autumn_leaves_same_chord_reattacks_reuse_cached_voicing(tmp_path: Path) -> None:
    audit = _generate("autumn_leaves", tmp_path=tmp_path, seed=3301)
    summary = audit.summary

    assert summary["medium_swing_same_chord_reattack_comping_reuse_version"] == "v2_6_52"
    reuse_events = summary["medium_swing_same_chord_reattack_comping_reuse_events"]
    assert reuse_events >= 60
    assert summary["medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_exact_voicing_reuse_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_foundation_stable_events"] == reuse_events
    assert summary["medium_swing_same_chord_reattack_comping_reuse_fresh_revoicing_events"] == 0
    assert summary["medium_swing_same_chord_reattack_comping_reuse_warning_events"] == 0
    assert summary["medium_swing_same_chord_reattack_comping_reuse_checkpoint_passed"] is True

    rows = [row for row in audit.event_rows if row.get("same_chord_reattack_continuity_applied")]
    assert len(rows) == reuse_events
    assert all(row["same_chord_reattack_region_voicing_reused"] is True for row in rows)
    assert all(row["same_chord_reattack_exact_voicing_reuse"] is True for row in rows)
    assert all(row["same_chord_reattack_foundation_stable"] is True for row in rows)
    assert all(row["same_chord_reattack_warning"] is False for row in rows)
    assert all(row["disposition_projection_family"] == "open" for row in rows)


def test_v2_6_52_doc_records_medium_swing_same_chord_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_52",
        "Same-Chord Reattack / Comping Reuse",
        "one-default-voicing-per-chord-region",
        "reuse cached region voicing",
        "force_fresh_voicing",
        "revoice_within_region",
        "All The Things You Are",
        "Autumn Leaves",
        "Pattern",
        "Anticipation",
        "Expression",
        "MIDI",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text
