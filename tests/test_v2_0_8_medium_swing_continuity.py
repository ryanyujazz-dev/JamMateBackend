from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.core.leadsheet.models import Leadsheet
from jammate_engine.midi.midi_writer import write_midi
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.styles.medium_swing import bass_foundation_patterns, percussion_patterns, comping_patterns


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_v2_leadsheet_expands_attya_written_form_shape() -> None:
    score = json.loads((PROJECT_ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    leadsheet = Leadsheet.from_dict(score)

    assert leadsheet.title == "All the Things You Are"
    # V2 score stores the written form only; performance repetitions live in GenerationRequest.choruses.
    assert len(leadsheet.bars) == 36
    assert leadsheet.bars[5].section_id == "A1"
    assert leadsheet.bars[5].chords[0].symbol == "Dm7"
    assert leadsheet.bars[5].chords[0].beats == 2.0
    assert leadsheet.bars[5].chords[1].symbol == "G7"
    assert leadsheet.bars[5].chords[1].beat == 3.0
    assert leadsheet.bars[5].chords[1].beats == 2.0


def test_medium_swing_two_beat_region_patterns_do_not_spill_past_region() -> None:
    context = {"region_duration_beats": 2.0}
    for source in (comping_patterns.get_pattern_candidates, bass_foundation_patterns.get_pattern_candidates, percussion_patterns.get_pattern_candidates):
        for candidate in source(context):
            assert candidate.events
            assert all(event.local_beat < 2.0 for event in candidate.events)


def test_bass_program_change_lives_on_bass_track(tmp_path: Path) -> None:
    midi_path = tmp_path / "bass_program.mid"
    write_midi(
        [NoteEvent(track="bass", channel=1, note=40, velocity=72, start_beat=0.0, duration_beats=1.0)],
        midi_path,
        tempo_bpm=132,
    )
    data = midi_path.read_bytes()
    # Raw MIDI program change for channel 2 / zero-based channel 1 using GM
    # Acoustic Bass: status 0xC1, program 32 (0x20).
    assert b"\xC1\x20" in data
