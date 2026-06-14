from __future__ import annotations

# harness token: test_v2_6_128_engine_ballad_first_audible_sparse_brush_foundation

import json
from pathlib import Path

from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_engine.styles.jazz_ballad import arrangement_policy, percussion_patterns

ROOT = Path(__file__).resolve().parents[1]
MISTY = ROOT / "examples" / "leadsheets" / "misty.json"


def _active_context(**kwargs):
    return {**kwargs, "jazz_ballad_brush_sound_source_time_feel_active": True}


def test_v2_6_128_arrangement_policy_tracks_current_sound_source_foundation() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    assert policy["default_feel"] == "jazz_ballad"
    assert policy["jazz_ballad_brush_semantic_policy_active"] is True
    assert policy["jazz_ballad_brush_semantic_policy_version"] == "v2_6_127"
    assert policy["jazz_ballad_brush_sound_source_time_feel_active"] is True
    assert policy["jazz_ballad_brush_sound_source_time_feel_version"] == "v2_6_137"
    assert policy["jazz_ballad_brush_sound_source_assumed"] is True
    assert policy["jazz_ballad_drum_not_chord_region_loop"] is True
    assert policy["jazz_ballad_no_custom_internal_brush_voices"] is True
    assert policy["jazz_ballad_brush_timbre_delegated_to_sound_source"] is True


def test_v2_6_128_current_brush_candidate_consumes_semantic_policy_without_midi_values() -> None:
    candidates = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=4,
            region_chorus_index=0,
            region_total_choruses=3,
        )
    )
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.category == "jazz_ballad_bar_level_brush_sound_source_time_feel"
    assert candidate.metadata["pattern_library_version"] == "v2_6_137"
    assert candidate.metadata["brush_feel_cell"] == "basic_brush_time"
    assert candidate.metadata["brush_runtime_audible"] is True
    assert candidate.metadata["jazz_ballad_drum_not_chord_region_loop"] is True
    assert candidate.metadata["brush_no_swing_ride"] is True
    assert candidate.metadata["brush_no_rock_backbeat"] is True
    assert candidate.metadata["jazz_ballad_no_custom_internal_brush_voices"] is True
    assert [event.local_beat for event in candidate.events] == [0.0, 0.0, 1.0, 1.0, 2.0, 3.0, 3.0]
    assert all(event.track == "drums" for event in candidate.events)

    debug_text = json.dumps(candidate.to_debug_dict(), ensure_ascii=False)
    assert "midi_note" not in debug_text
    assert "velocity" not in debug_text


def test_v2_6_128_short_regions_now_project_bar_level_brush_plan_and_phrase_tail_breathes() -> None:
    assert percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 1}) == ()

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
    assert first_half.metadata["bar_region_projection"]["region_role"] == "first_half"
    assert any(event.metadata.get("drum") == "snare" for event in first_half.events)

    phrase_tail = percussion_patterns.get_pattern_candidates(
        _active_context(
            region_duration_beats=4.0,
            region_source_bar_index=7,
            region_chorus_index=0,
            region_total_choruses=3,
        )
    )[0]
    assert phrase_tail.metadata["brush_feel_cell"] == "phrase_breath_release"
    assert phrase_tail.metadata["brush_classic_fill_cell"] == "v1_soft_swish_4and_hint"
    assert [event.metadata.get("brush_event_slot") for event in phrase_tail.events if event.role == "ballad_section_transition_hint"] == ["4&"]


def test_v2_6_128_percussion_realizer_maps_current_ballad_brush_semantics() -> None:
    candidate = percussion_patterns.get_pattern_candidates(
        _active_context(region_duration_beats=4.0, region_source_bar_index=4, region_chorus_index=0, region_total_choruses=3)
    )[0]

    from jammate_engine.core.harmony.harmonic_region import HarmonicRegion

    region = HarmonicRegion(region_id="r0", chord_symbol="Cm7", next_chord_symbol=None, chorus_index=0, bar_index=0, chord_index=0, start_beat=0.0, duration_beats=4.0)
    pattern_events = candidate.instantiate(region).events
    notes = PercussionRealizer().realize(pattern_events)
    assert len(notes) == len(candidate.events)
    assert all(note.track == "drums" for note in notes)
    assert all(18 <= note.velocity <= 36 for note in notes)
    assert {note.note for note in notes}.issubset({36, 38, 44, 45, 47, 51})


def test_v2_6_128_misty_runtime_has_current_light_brush_source_layer(tmp_path: Path) -> None:
    leadsheet = json.loads(MISTY.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "jazz_ballad",
            "tempo": 72,
            "choruses": 3,
            "seed": 1260,
            "output_path": str(tmp_path / "misty_v2_6_128.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    assert result.ok is True
    note_counts = dict(result.debug.get("note_events_by_track") or {})
    assert note_counts.get("piano", 0) > 0
    assert note_counts.get("bass", 0) > 0
    assert 150 <= note_counts.get("drums", 0) <= 900
    assert result.debug.get("performance_choruses") == 3
