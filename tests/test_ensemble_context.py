from __future__ import annotations

from pathlib import Path

from jammate_engine.core.engine import JamMateEngine
from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.pattern_runtime import PatternEvent
from jammate_engine.realization.piano_lh_bass_foundation_realizer import PianoLHBassFoundationRealizer
from jammate_engine.runtime.generation_request import GenerationRequest


MINIMAL_LEADSHEET = {
    "title": "Minimal ii V I",
    "key": "C",
    "time_signature": "4/4",
    "bars": [
        {"chords": [{"symbol": "Dm7", "beat": 1.0}]},
        {"chords": [{"symbol": "G7", "beat": 1.0}]},
        {"chords": [{"symbol": "Cmaj7", "beat": 1.0}]},
    ],
}


def test_ensemble_context_defaults_to_split_piano_when_bass_absent() -> None:
    context = EnsembleContext.from_dict({"bass_present": False})
    assert context.needs_piano_lh_bass_foundation is True
    assert context.should_force_root_in_harmonic_voicing is False
    assert context.harmonic_comping_role == "piano_rh_harmonic_comping"


def test_piano_lh_bass_foundation_realizes_bass_events_on_piano_channel() -> None:
    event = PatternEvent(
        event_id="bass_1",
        track="bass",
        region_id="r1",
        chord_symbol="Dm7",
        onset_beat=0.0,
        role="bass_note",
        metadata={"degree": "root"},
    )
    notes = PianoLHBassFoundationRealizer().realize([event], {"bass_present": False})
    assert len(notes) == 1
    assert notes[0].track == "piano_lh_bass_foundation"
    assert notes[0].channel == 0
    assert 36 <= notes[0].note <= 54


def test_engine_no_bass_routes_bass_pattern_to_piano_lh(tmp_path: Path) -> None:
    result_path, debug = JamMateEngine().generate(
        GenerationRequest(
            leadsheet=MINIMAL_LEADSHEET,
            style="medium_swing",
            tempo=120,
            choruses=1,
            seed=7,
            ensemble={"bass_present": False},
        ),
        tmp_path / "no_bass.mid",
    )
    assert result_path.exists()
    assert debug["ensemble_context"]["needs_piano_lh_bass_foundation"] is True
    assert debug["note_events_by_track"].get("bass", 0) == 0
    assert debug["note_events_by_track"].get("piano_lh_bass_foundation", 0) > 0
    assert debug["note_events_by_track"].get("piano", 0) > 0


def test_piano_lh_bass_foundation_resolves_R_as_root_not_fifth() -> None:
    event = PatternEvent(
        event_id="bass_R_token",
        track="bass",
        region_id="r1",
        chord_symbol="Cmaj7",
        onset_beat=0.0,
        role="bass_note",
        metadata={"degree": "R"},
    )
    notes = PianoLHBassFoundationRealizer().realize([event], {"bass_present": False})
    assert len(notes) == 1
    assert notes[0].note % 12 == 0
