from __future__ import annotations

from jammate_engine.styles.jazz_ballad import comping_patterns


def test_v2_5_9_two_chord_soft_marks_use_beat_1_and_1and_not_beat_2() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    candidate = next(c for c in candidates if c.name == "ballad_phrase_two_chord_soft_marks")

    assert comping_patterns.PATTERN_LIBRARY_VERSION == "v2_5_9"
    assert comping_patterns.PHRASE_INTENT_VERSION == "v2_5_9"
    assert candidate.rhythm_beats == (0.0, 0.5)
    assert candidate.events[1].local_beat == 0.5
    assert candidate.metadata["rhythmic_cell"] == "region_start_1and"
    assert candidate.events[1].metadata["phrase_slot"] == "soft_mark"
    assert candidate.events[1].metadata["timing_intent"] == "swing_upbeat"


def test_v2_5_9_two_beat_fallback_retouch_also_uses_1and() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    candidate = next(c for c in candidates if c.name == "ballad_piano_two_beat_light_retouch")

    assert candidate.rhythm_beats == (0.0, 0.5)
    assert candidate.events[1].local_beat == 0.5
    assert candidate.metadata["rhythmic_cell"] == "region_start_1and"
    assert candidate.events[1].metadata["timing_intent"] == "swing_upbeat"
