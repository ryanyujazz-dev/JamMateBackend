from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
LEADSHEETS = ROOT / "examples" / "leadsheets"
DOC = ROOT / "docs" / "ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_SAFE_EXTENSION_TOP_REGISTER_CHECKPOINT_V2_6_53.md"


def _generate(slug: str, *, tmp_path: Path, seed: int):
    score = json.loads((LEADSHEETS / f"{slug}.json").read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": seed,
            "output_path": str(tmp_path / f"{slug}_v2_6_53.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return build_piano_musical_audit(result.debug)


def test_v2_6_53_policy_declares_safe_extension_top_register_checkpoint() -> None:
    metadata = dict(get_voicing_policy().metadata or {})
    target = dict(metadata.get("medium_swing_open_drop_safe_extension_top_register_checkpoint_target") or {})

    assert metadata["medium_swing_open_drop_safe_extension_top_register_checkpoint_version"] == "v2_6_53"
    assert metadata["medium_swing_open_drop_safe_extension_top_register_checkpoint_enabled"] is True
    assert target["scope"] == "medium_swing_open_drop_actual_runtime"
    assert target["projection_family"] == "open"
    assert target["top_note_max_allowed"] == 72
    assert target["top_note_ge_75_events"] == 0
    assert target["major_seventh_default_preferred_colors"] == ["9", "13"]
    assert target["major_seventh_sharp11_default"] == "disabled_unless_explicit_symbol_or_harmonic_color_intent"
    assert target["register_guard_failed_events"] == 0
    assert target["voice_leading_warning_events"] == 0
    assert target["behavior_preserving"] is True
    assert target["no_runtime_candidate_change"] is True
    assert target["does_not_change_pattern_anticipation_expression_or_midi"] is True


def test_v2_6_53_all_the_things_you_are_top_register_and_safe_extensions_are_calm(tmp_path: Path) -> None:
    audit = _generate("all_the_things_you_are", tmp_path=tmp_path, seed=3300)
    summary = audit.summary

    assert summary["medium_swing_open_drop_safe_extension_top_register_checkpoint_version"] == "v2_6_53"
    assert summary["medium_swing_open_drop_safe_extension_top_register_behavior_preserving"] is True
    assert summary["medium_swing_open_drop_top_note_max"] == 72
    assert summary["medium_swing_open_drop_top_note_ge_75_events"] == 0
    assert summary["medium_swing_open_drop_low_note_min"] == 48
    assert summary["medium_swing_open_drop_register_guard_failed_events"] == 0
    assert summary["medium_swing_open_drop_missing_note_events"] == 0
    assert summary["medium_swing_open_drop_voice_leading_warning_events"] == 0
    assert summary["medium_swing_open_drop_major_seventh_events"] >= 71
    assert summary["medium_swing_open_drop_major_seventh_color_events"] == 0
    assert summary["medium_swing_open_drop_major_seventh_degree_counts"] == {}
    assert summary["medium_swing_open_drop_major_seventh_non_safe_color_events_by_chord"] == {}
    assert summary["medium_swing_open_drop_major_seventh_unnotated_sharp11_events"] == 0
    assert summary["medium_swing_open_drop_safe_extension_top_register_checkpoint_passed"] is True

    assert all(max(row["midi_notes"]) <= 72 for row in audit.event_rows if row.get("midi_notes"))
    assert all("#11" not in row["degrees"] for row in audit.event_rows if "maj7" in str(row.get("chord_symbol", "")).lower())


def test_v2_6_53_autumn_leaves_top_register_and_safe_extensions_are_calm(tmp_path: Path) -> None:
    audit = _generate("autumn_leaves", tmp_path=tmp_path, seed=3301)
    summary = audit.summary

    assert summary["medium_swing_open_drop_safe_extension_top_register_checkpoint_version"] == "v2_6_53"
    assert summary["medium_swing_open_drop_top_note_max"] == 72
    assert summary["medium_swing_open_drop_top_note_ge_75_events"] == 0
    assert summary["medium_swing_open_drop_low_note_min"] == 48
    assert summary["medium_swing_open_drop_register_guard_failed_events"] == 0
    assert summary["medium_swing_open_drop_missing_note_events"] == 0
    assert summary["medium_swing_open_drop_voice_leading_warning_events"] == 0
    assert summary["medium_swing_open_drop_major_seventh_events"] >= 56
    assert summary["medium_swing_open_drop_major_seventh_color_events"] == 0
    assert summary["medium_swing_open_drop_major_seventh_degree_counts"] == {}
    assert summary["medium_swing_open_drop_major_seventh_non_safe_color_events_by_chord"] == {}
    assert summary["medium_swing_open_drop_major_seventh_unnotated_sharp11_events"] == 0
    assert summary["medium_swing_open_drop_safe_extension_top_register_checkpoint_passed"] is True

    assert all(max(row["midi_notes"]) <= 72 for row in audit.event_rows if row.get("midi_notes"))
    assert all("#11" not in row["degrees"] for row in audit.event_rows if "maj7" in str(row.get("chord_symbol", "")).lower())


def test_v2_6_53_doc_records_behavior_preserving_medium_swing_guardrails() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_53",
        "Safe Extension + Top Register Checkpoint",
        "behavior-preserving",
        "top_note_max_allowed: 72",
        "top_note_ge_75_events: 0",
        "unnotated major-seventh #11 events: 0",
        "9 / 13",
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
