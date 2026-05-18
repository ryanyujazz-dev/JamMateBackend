from __future__ import annotations

from jammate_engine.core.expression import ExpressionResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.jazz_ballad import comping_patterns, expression_policy
from jammate_engine.styles.registry import get_style


def _region(duration_beats: float = 4.0) -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r_ballad_v250",
        chord_symbol="Cmaj7",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=duration_beats,
    )


def test_v2_5_0_ballad_comping_library_adds_light_motion_without_full_silence() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    names = {candidate.name for candidate in candidates}

    assert comping_patterns.PATTERN_LIBRARY_VERSION in {"v2_5_0", "v2_5_4", "v2_5_5", "v2_5_7", "v2_5_9", "v2_5_9"}
    assert "ballad_piano_soft_downbeat_sustain" in names
    assert "ballad_piano_downbeat_midbar_retouch" in names
    assert "ballad_piano_downbeat_3and_answer" in names
    assert "ballad_piano_downbeat_1and_whisper" in names
    assert all(candidate.rhythm_beats[0] == 0.0 for candidate in candidates)
    assert all(candidate.metadata["voicing_boundary"] == "pattern_is_pitchless" for candidate in candidates)
    assert max(candidate.weight for candidate in candidates) == next(
        candidate.weight for candidate in candidates if candidate.name == "ballad_piano_soft_downbeat_sustain"
    )


def test_v2_5_0_ballad_two_beat_regions_use_local_light_retouch_only() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    assert {candidate.metadata["region_shape"] for candidate in candidates} == {"two_beat_region"}
    assert all(max(candidate.rhythm_beats) < 2.0 for candidate in candidates)
    assert all(candidate.rhythm_beats[0] == 0.0 for candidate in candidates)


def test_v2_5_0_ballad_expression_profiles_stay_soft_and_core_resolved() -> None:
    policy = expression_policy.get_expression_policy()
    assert {"soft_retouch", "soft_answer", "soft_whisper"}.issubset(policy.profiles)
    assert policy.profiles["soft_retouch"].velocity < policy.profiles["soft_sustain"].velocity
    assert policy.profiles["soft_answer"].pedal.value == "light"
    assert policy.profiles["soft_whisper"].articulation.value == "sustain"

    candidate = next(c for c in comping_patterns.get_pattern_candidates({}) if c.name == "ballad_piano_downbeat_midbar_retouch")
    events = candidate.instantiate(_region()).events
    plan = ExpressionResolver().resolve(events, policy)
    assert [plan.events[event.event_id].profile_name for event in events] == ["soft_sustain", "soft_retouch"]
    assert plan.events[events[0].event_id].duration_beats == 2.0
    assert plan.events[events[0].event_id].metadata["duration_next_event_clamp_applied"] is True


def test_v2_5_0_default_ballad_style_still_selects_anchor_without_rng() -> None:
    style = get_style("jazz_ballad")
    plan = style.plan_region(_region(), context={})
    assert plan.selected_candidate == "ballad_piano_soft_downbeat_sustain + ballad_bass_root_anchor"
