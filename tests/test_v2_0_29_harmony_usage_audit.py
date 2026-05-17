from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.harmony.material import resolve_degree_token
from jammate_engine.generation.bass_foundation.generator import BassFoundationGenerator
from jammate_engine.generation.bass_foundation.policy import BassFoundationPolicy
from jammate_engine.realization.bass_degree_resolver import resolve_bass_degree_token
from jammate_engine.styles.medium_swing.bass_foundation_patterns import (
    _looks_like_dominant_to_major,
    _looks_like_minor_ii_to_v,
)


def test_bass_degree_facade_delegates_pitch_class_semantics_to_core_harmony() -> None:
    for token in ("R", "Third", "Seventh", "nextR", "approach_nextR_below", "scale_near_nextR_above"):
        facade = resolve_bass_degree_token(chord_symbol="Dm7", token=token, next_chord_symbol="G7")
        core = resolve_degree_token(chord_symbol="Dm7", token=token, next_chord_symbol="G7")
        assert facade == core


def test_classic_fill_tokens_use_harmony_degree_resolution_for_pitch_class() -> None:
    generator = BassFoundationGenerator()
    policy = BassFoundationPolicy(enabled=True, register_low=26, register_high=48, register_center=37, max_region_span=12)
    end_region = HarmonicRegion(
        region_id="r_end",
        chord_symbol="Fmaj7",
        next_chord_symbol="G7",
        chorus_index=0,
        bar_index=2,
        chord_index=0,
        start_beat=8.0,
        duration_beats=4.0,
    )

    token_aliases = {
        "R": "R",
        "Third": "Third",
        "classic_low3": "classic_low3",
        "degree4": "degree4",
        "#4": "#4",
        "Fifth": "Fifth",
    }
    for token, harmony_token in token_aliases.items():
        note = generator._classic_fill_note_for_token(
            token=token,
            chord_symbol="Cmaj7",
            reference=36,
            existing_region_notes=[],
            policy=policy,
            end_region=end_region,
        )
        expected = resolve_degree_token(chord_symbol="Cmaj7", token=harmony_token, next_chord_symbol="Fmaj7").pitch_class
        assert note % 12 == expected


def test_medium_swing_contextual_motion_helpers_delegate_to_harmony_classifier() -> None:
    assert _looks_like_minor_ii_to_v("Dm7", "G7")
    assert _looks_like_minor_ii_to_v("Bm7b5", "E7")
    assert not _looks_like_minor_ii_to_v("Dm7", "Ab7")

    assert _looks_like_dominant_to_major("G7", "Cmaj7")
    assert not _looks_like_dominant_to_major("G7", "Dbmaj7")
