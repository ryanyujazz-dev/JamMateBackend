from __future__ import annotations

# harness token: test_v2_6_129_engine_ballad_complete_brush_drum_system

import json
from pathlib import Path

from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns

ROOT = Path(__file__).resolve().parents[1]
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _active_context(**kwargs):
    return {**kwargs, "jazz_ballad_brush_sound_source_time_feel_active": True}


def test_v2_6_129_arrangement_policy_enables_current_complete_brush_sound_source() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["default_feel"] == "jazz_ballad"
    assert policy["jazz_ballad_brush_sound_source_time_feel_active"] is True
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert policy["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert policy["jazz_ballad_drum_planning_scope"] == "bar_level_brush_time_feel_with_region_projection"
    assert policy["jazz_ballad_drum_not_chord_region_loop"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_swing_ride"] is True
    assert policy["jazz_ballad_brush_semantic_policy_no_rock_backbeat"] is True


def test_v2_6_129_full_region_has_sweep_anchor_and_feather_kick() -> None:
    candidates = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=4,
            region_chorus_index=1,
            region_total_choruses=3,
        )
    )
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.category == "jazz_ballad_bar_level_brush_sound_source_time_feel"
    assert candidate.metadata["pattern_library_version"] == "v2_6_137"
    assert candidate.metadata["brush_feel_cell"] == "brush_two_feel"
    assert candidate.metadata["brush_time_anchor_intent"] == "hat_2_4_soft"
    assert candidate.metadata["brush_kick_policy_intent"] == "one_three_feather"
    drums = [event.metadata["drum"] for event in candidate.events]
    beats = [event.local_beat for event in candidate.events]
    assert drums.count("snare") >= 5
    assert drums.count("hihat_pedal") >= 2
    assert drums.count("kick") == 2
    assert "low_tom" in drums
    assert 1.0 in beats and 3.0 in beats
    debug_text = json.dumps(candidate.to_debug_dict(), ensure_ascii=False)
    assert "midi_note" not in debug_text
    assert "velocity" not in debug_text


def test_v2_6_129_two_beat_regions_project_one_bar_plan() -> None:
    first_half = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=2.0,
            region_source_bar_index=2,
            region_chorus_index=0,
            region_total_choruses=3,
            region_is_first_region_of_bar=True,
            region_is_last_region_of_bar=False,
        )
    )[0]
    second_half = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=2.0,
            region_source_bar_index=2,
            region_chorus_index=0,
            region_total_choruses=3,
            region_is_first_region_of_bar=False,
            region_is_last_region_of_bar=True,
        )
    )[0]
    assert first_half.metadata["bar_region_projection"]["region_role"] == "first_half"
    assert second_half.metadata["bar_region_projection"]["region_role"] == "second_half"
    assert any(event.metadata.get("drum") == "snare" for event in first_half.events)
    assert any(event.metadata.get("drum") == "hihat_pedal" for event in second_half.events)
    assert any(event.metadata.get("timing_intent") == "swing_upbeat" for event in second_half.events)


def test_v2_6_129_phrase_tail_and_final_release_are_contextual() -> None:
    phrase_tail = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=7,
            region_chorus_index=0,
            region_total_choruses=3,
        )
    )[0]
    final_release = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=31,
            region_chorus_index=2,
            region_total_choruses=3,
            region_is_last_bar_of_chorus=True,
        )
    )[0]
    assert phrase_tail.metadata["brush_feel_cell"] == "phrase_breath_release"
    assert phrase_tail.metadata["brush_classic_fill_cell"] == "v1_soft_swish_4and_hint"
    assert any(event.role == "ballad_section_transition_hint" for event in phrase_tail.events)
    assert final_release.metadata["brush_feel_cell"] == "final_release"
    assert [event.metadata.get("drum") for event in final_release.events] == ["snare", "ride"]
    assert all(event.metadata.get("brush_fill_foreground_lane") is True for event in final_release.events)


def test_v2_6_129_misty_runtime_has_complete_but_light_brush_drums(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 1290,
            "output_path": str(tmp_path / "misty_v2_6_129.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    assert note_counts.get("piano", 0) > 0
    assert note_counts.get("bass", 0) > 0
    assert 250 <= note_counts.get("drums", 0) <= 900
    assert result.debug.get("performance_choruses") == 3
