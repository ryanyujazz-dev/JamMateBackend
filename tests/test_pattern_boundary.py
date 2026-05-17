from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.registry import get_style


def test_style_profile_uses_style_owned_pattern_sources() -> None:
    style = get_style("bossa_nova")
    assert style.pattern_sources
    assert all(callable(source) for source in style.pattern_sources)


def test_pattern_plan_is_pitchless() -> None:
    style = get_style("bossa_nova")
    region = HarmonicRegion(
        region_id="test_region",
        chord_symbol="Dm7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )
    plan = style.plan_region(region, context={})
    assert plan.events
    for event in plan.events:
        assert not hasattr(event, "note")
        assert not hasattr(event, "midi_note")
        assert not hasattr(event, "velocity")
        assert not hasattr(event, "duration_beats")


def test_bossa_core_batida_events_are_in_pattern_file() -> None:
    from jammate_engine.styles.bossa_nova.comping_patterns import get_pattern_candidates

    candidates = get_pattern_candidates({})
    assert candidates[0].name == "bossa_piano_core_batida_1_2_3and"
    assert candidates[0].rhythm_beats == (0.0, 1.0, 2.5)
