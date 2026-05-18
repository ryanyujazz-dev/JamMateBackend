from __future__ import annotations

from jammate_engine.midi.render_pipeline import performed_beat
from jammate_engine.styles.jazz_ballad import comping_patterns
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile


def _candidate(name: str):
    return next(c for c in comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0}) if c.name == name)


def test_v2_5_9_ballad_1and_remains_logical_half_and_swing8_performs_by_default() -> None:
    candidate = _candidate("ballad_phrase_two_chord_soft_marks")
    second = candidate.events[1]

    assert comping_patterns.PATTERN_LIBRARY_VERSION == "v2_5_9"
    assert second.local_beat == 0.5
    assert second.metadata["timing_intent"] == "swing_upbeat"

    # As of v2_5_9 Jazz Ballad defaults to swing-8 feel. The event-level
    # intent remains explicit so this musical 1& stays swung even if a future
    # isolation profile overrides the global timing feel.
    policy = JazzBalladProfile().timing_policy
    assert policy["feel"] == "swing"
    assert performed_beat(second.local_beat, "auto", policy) == 2.0 / 3.0
    assert performed_beat(second.local_beat, second.metadata["timing_intent"], policy) == 2.0 / 3.0


def test_v2_5_9_all_current_ballad_1and_second_touches_keep_explicit_swing_upbeat_intent() -> None:
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
        assert candidate.rhythm_beats[:2] == (0.0, 0.5)
        assert candidate.events[1].metadata["timing_intent"] == "swing_upbeat"
        assert "timing_boundary" in candidate.events[1].metadata
