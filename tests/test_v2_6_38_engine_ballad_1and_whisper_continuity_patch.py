from __future__ import annotations

# harness token: test_v2_6_38_engine_ballad_1and_whisper_continuity_patch

import json
from pathlib import Path

from jammate_engine.generation.piano_audit import build_piano_musical_audit
from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import comping_patterns

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_BALLAD_1AND_WHISPER_CONTINUITY_PATCH_V2_6_38.md"
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
            "output_path": str(tmp_path / "misty_v2_6_38.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    return result


def _event_end(note: dict, timing_policy: dict) -> float:
    return performed_beat(float(note["start_beat"]), str(note.get("timing_intent") or "auto"), timing_policy) + float(note["duration_beats"])


def _event_start(note: dict, timing_policy: dict) -> float:
    return performed_beat(float(note["start_beat"]), str(note.get("timing_intent") or "auto"), timing_policy)


def test_v2_6_38_doc_exists_and_declares_ballad_continuity_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "v2_6_38",
        "Ballad 1& Whisper Continuity Patch",
        "not a voicing selector change",
        "non-interrupting upper/projection-group re-touch",
        "Pattern",
        "Expression",
        "Realizer",
        "MIDI writer",
        "Agent",
        "HarmonyOS",
    ):
        assert token in text


def test_v2_6_38_near_downbeat_1and_patterns_request_partial_projection_group_reattack() -> None:
    names = {
        "ballad_piano_downbeat_1and_whisper",
        "ballad_phrase_two_chord_soft_marks",
        "ballad_piano_two_beat_light_retouch",
    }
    candidates = list(comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})) + list(
        comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    )
    found = {candidate.name: candidate for candidate in candidates if candidate.name in names}

    assert set(found) == names
    for candidate in found.values():
        second = candidate.events[1]
        assert second.local_beat == 0.5
        assert second.gesture_type == "inner_movement"
        assert tuple(second.gesture.projection_refs) == ("projection_group",)
        assert second.metadata["timing_intent"] == "swing_upbeat"
        assert second.metadata["gesture_intent"] == "inner_movement"


def test_v2_6_38_misty_guardrails_remain_unchanged_after_continuity_patch(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug).summary

    assert audit["densities"] == {"5": 124, "6": 72}
    assert audit["functional_groupings"] == {"2+3": 114, "2+4": 68, "1+4": 10, "3+3": 4}
    assert audit["densities"].get("4", 0) == 0
    assert audit["densities"].get("7", 0) == 0
    assert audit["top_note_max"] <= 74
    assert audit["top_note_ge_75_events"] == 0
    assert audit["lower_upper_group_gap_too_tight_events"] == 0
    assert audit["lower_upper_group_gap_too_wide_events"] == 0


def test_v2_6_38_problem_bars_keep_foundation_through_1and_projection_retouch(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)
    timing_policy = dict(result.debug.get("timing_policy") or {})

    retouch_rows = [
        row
        for row in audit.event_rows
        if row["pattern_id"] == "ballad_piano_downbeat_1and_whisper"
        and row["gesture_type"] == "inner_movement"
        and int(float(row["onset_beat"]) // 4) + 1 in {41, 63, 95}
    ]
    assert [int(float(row["onset_beat"]) // 4) + 1 for row in retouch_rows] == [41, 63, 95]

    rows_by_region = {row["region_id"]: [] for row in audit.event_rows}
    for row in audit.event_rows:
        rows_by_region.setdefault(row["region_id"], []).append(row)

    for retouch in retouch_rows:
        prior_candidates = [
            row
            for row in rows_by_region[retouch["region_id"]]
            if row["pattern_id"] == "ballad_piano_downbeat_1and_whisper"
            and row["gesture_type"] == "simultaneous_onset"
            and float(row["onset_beat"]) < float(retouch["onset_beat"])
        ]
        assert len(prior_candidates) == 1
        anchor = prior_candidates[0]

        retouch_start = min(_event_start(note, timing_policy) for note in retouch["realized_notes"])
        retouch_end = max(_event_end(note, timing_policy) for note in retouch["realized_notes"])
        anchor_notes = list(anchor["realized_notes"])
        anchor_ends = [_event_end(note, timing_policy) for note in anchor_notes]

        assert len(retouch["realized_notes"]) < len(anchor_notes)
        assert {note["projection_ref"] for note in retouch["realized_notes"]} == {"projection_group"}
        assert sum(1 for end in anchor_ends if end >= retouch_end - 1e-6) >= 2
        assert sum(1 for end in anchor_ends if abs(end - retouch_start) < 1e-6) >= 3


def test_v2_6_38_two_chord_soft_marks_are_no_longer_full_chord_retouches(tmp_path: Path) -> None:
    result = _generate_misty(tmp_path)
    audit = build_piano_musical_audit(result.debug)

    rows = [
        row
        for row in audit.event_rows
        if row["pattern_id"] == "ballad_phrase_two_chord_soft_marks" and row["local_beat"] == 0.5
    ]
    assert rows
    for row in rows:
        assert row["gesture_type"] == "inner_movement"
        assert {note["projection_ref"] for note in row["realized_notes"]} == {"projection_group"}
        assert row["realized_note_count"] < len(row["midi_notes"])
