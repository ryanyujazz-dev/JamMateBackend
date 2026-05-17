from __future__ import annotations

from pathlib import Path

from jammate_engine.core.engine import JamMateEngine
from jammate_engine.realization.bass_degree_resolver import resolve_bass_degree_token
from jammate_engine.runtime.generation_request import GenerationRequest
from jammate_engine.styles.medium_swing import bass_foundation_patterns, percussion_patterns, comping_patterns


MINIMAL_LEADSHEET = {
    "title": "Medium Swing First Audible Test",
    "key": "C",
    "bars": [
        {"chords": [{"symbol": "Dm7", "beats": 4}]},
        {"chords": [{"symbol": "G7", "beats": 4}]},
        {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
        {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
    ],
}


def test_medium_swing_piano_has_multiple_pitchless_comping_candidates() -> None:
    candidates = comping_patterns.get_pattern_candidates({})
    assert len(candidates) >= 4
    assert any(candidate.name == "medium_swing_piano_charleston_1_2and" for candidate in candidates)
    for candidate in candidates:
        for spec in candidate.events:
            assert spec.track == "piano"
            assert "midi_note" not in spec.metadata
            assert "duration_beats" not in spec.metadata


def test_medium_swing_bass_library_contains_walking_next_root_tokens_only() -> None:
    candidates = bass_foundation_patterns.get_pattern_candidates({})
    walking = [candidate for candidate in candidates if "walking" in candidate.tags]
    assert walking
    assert any(
        any(spec.metadata.get("degree") in {"beat4_auto", "approach_nextR_below"} for spec in candidate.events)
        for candidate in walking
    )
    for candidate in candidates:
        for spec in candidate.events:
            assert spec.track == "bass"
            assert "midi_note" not in spec.metadata
            assert "duration_beats" not in spec.metadata
            assert "velocity" not in spec.metadata


def test_bass_degree_resolver_can_target_next_root_chromatically() -> None:
    resolved = resolve_bass_degree_token(chord_symbol="Dm7", token="approach_nextR_below", next_chord_symbol="G7")
    assert resolved.degree == "approach_nextR_below"
    assert resolved.source == "chromatic_below_next_root"
    assert resolved.pitch_class == 6  # F# approaches G from below.


def test_medium_swing_drums_use_spang_a_lang_not_flat_quarter_placeholder() -> None:
    candidate = percussion_patterns.get_pattern_candidates({})[0]
    beats = candidate.rhythm_beats
    assert 1.6667 in beats
    assert 3.6667 in beats
    assert any(spec.metadata.get("drum") == "hihat_pedal" for spec in candidate.events)
    for spec in candidate.events:
        assert "midi_note" not in spec.metadata
        assert "duration_beats" not in spec.metadata
        assert "velocity" not in spec.metadata


def test_engine_generates_first_audible_medium_swing_tracks(tmp_path: Path) -> None:
    path, debug = JamMateEngine().generate(
        GenerationRequest(
            leadsheet=MINIMAL_LEADSHEET,
            style="medium_swing",
            tempo=132,
            choruses=3,
            seed=207,
            ensemble={"bass_present": True},
        ),
        tmp_path / "medium_swing_first_audible.mid",
    )
    assert path.exists()
    assert debug["note_events_by_track"].get("piano", 0) > 0
    assert debug["note_events_by_track"].get("bass", 0) >= 24
    assert debug["note_events_by_track"].get("drums", 0) >= 80
