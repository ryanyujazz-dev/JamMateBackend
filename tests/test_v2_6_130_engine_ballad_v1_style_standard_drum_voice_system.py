from __future__ import annotations

# harness token: test_v2_6_130_engine_ballad_v1_style_standard_drum_voice_system

import json
from pathlib import Path

from jammate_engine.realization import percussion_realizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns

ROOT = Path(__file__).resolve().parents[1]
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"
CUSTOM_BRUSH_VOICES = {"brush_swirl", "brush_sweep", "brush_tap", "brush_release"}
STANDARD_DRUM_VOICES = {"snare", "hihat_pedal", "kick", "ride"}


def test_v2_6_130_deletes_custom_brush_voice_mapping_from_realizer() -> None:
    assert CUSTOM_BRUSH_VOICES.isdisjoint(percussion_realizer.DRUM_NOTES)
    assert not any(key.startswith("ballad_brush_") for key in percussion_realizer.DYNAMIC_VELOCITY)
    assert not any(key.startswith("brush_texture_") for key in percussion_realizer.STROKE_DURATION)
    assert {"pp", "p", "feather"}.issubset(percussion_realizer.DYNAMIC_VELOCITY)


def test_v2_6_130_arrangement_policy_declares_v1_style_standard_voice_boundary() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["jazz_ballad_complete_brush_drum_system_version"] == "v2_6_130"
    assert policy["jazz_ballad_custom_brush_voice_mapping_deleted"] is True
    assert policy["jazz_ballad_brush_timbre_delegated_to_sound_source"] is True
    assert policy["jazz_ballad_v1_drum_style_reference"] is True


def test_v2_6_130_full_region_uses_v1_style_snare_hat_kick_not_custom_brush() -> None:
    candidate = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 4,
            "region_chorus_index": 1,
            "region_total_choruses": 3,
            "jazz_ballad_complete_brush_drum_system_active": True,
        }
    )[0]
    drums = [event.metadata.get("drum") for event in candidate.events]
    assert set(drums).issubset(STANDARD_DRUM_VOICES)
    assert CUSTOM_BRUSH_VOICES.isdisjoint(drums)
    assert drums.count("snare") >= 7
    assert drums.count("hihat_pedal") >= 2
    assert drums.count("kick") == 2
    assert candidate.metadata["custom_brush_voice_names_deleted"] is True
    assert candidate.metadata["brush_timbre_delegated_to_sound_source"] is True
    assert candidate.metadata["v1_ballad_drum_style_reference"] is True
    debug_text = json.dumps(candidate.to_debug_dict(), ensure_ascii=False)
    assert "midi_note" not in debug_text
    assert "velocity" not in debug_text


def test_v2_6_130_phrase_tail_and_release_use_standard_source_voices() -> None:
    phrase_tail = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 7,
            "region_chorus_index": 0,
            "region_total_choruses": 3,
            "jazz_ballad_complete_brush_drum_system_active": True,
        }
    )[0]
    final_release = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 31,
            "region_chorus_index": 2,
            "region_total_choruses": 3,
            "region_is_last_bar_of_chorus": True,
            "jazz_ballad_complete_brush_drum_system_active": True,
        }
    )[0]
    assert {event.metadata.get("drum") for event in phrase_tail.events}.issubset(STANDARD_DRUM_VOICES)
    assert [event.metadata.get("drum") for event in final_release.events] == ["snare", "ride"]


def test_v2_6_130_misty_runtime_has_complete_v1_style_drum_layer(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 1300,
            "output_path": str(tmp_path / "misty_v2_6_130.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    assert note_counts.get("piano", 0) > 0
    assert note_counts.get("bass", 0) > 0
    assert 350 <= note_counts.get("drums", 0) <= 1000
    assert result.debug.get("performance_choruses") == 3
