from __future__ import annotations

from jammate_engine.core.harmony import (
    HarmonicContext,
    chord_material,
    parse_chord,
    resolve_degree_token,
    resolve_scale_policy_detail,
)
from jammate_engine.core.voicing.sources.chord_tone_resolver import content_degrees
from jammate_engine.core.voicing.policy import ContentFamily, RootSupportPolicy
from jammate_engine.realization.bass_degree_resolver import resolve_bass_degree_token


def test_v2_0_25_chord_parser_contract_covers_common_jazz_qualities() -> None:
    major = parse_chord("Cmaj7")
    minor = parse_chord("Dm7")
    dominant = parse_chord("G7alt")
    half_dim = parse_chord("Bm7b5")
    diminished_triad = parse_chord("Cdim")

    assert major.quality == "major"
    assert major.has_major_seventh
    assert not major.is_dominant
    assert minor.quality == "minor"
    assert minor.has_minor_seventh
    assert dominant.is_dominant
    assert "alt" in dominant.alterations
    assert half_dim.quality == "half_diminished"
    assert half_dim.is_half_diminished
    assert diminished_triad.quality == "diminished"
    assert not diminished_triad.has_seventh


def test_v2_0_25_degree_resolution_lives_in_core_harmony() -> None:
    core = resolve_degree_token(chord_symbol="Dm7", token="4", next_chord_symbol="G7")
    compatibility = resolve_bass_degree_token(chord_symbol="Dm7", token="4", next_chord_symbol="G7")

    assert core.degree == "nextR"
    assert core.pitch_class == 7
    assert compatibility == core
    assert resolve_degree_token(chord_symbol="G7", token="Seventh").pitch_class == 5
    assert resolve_degree_token(chord_symbol="Cmaj7", token="Seventh").pitch_class == 11
    assert resolve_degree_token(chord_symbol="G7alt", token="b9").pitch_class == 8
    assert resolve_degree_token(chord_symbol="G7alt", token="b13").pitch_class == 3


def test_v2_0_25_chord_material_and_voicing_share_degree_contract() -> None:
    material = chord_material("Bm7b5")
    assert material.triad_degrees == ("R", "b3", "b5")
    assert material.seventh_degree == "b7"
    assert material.chord_tone_degrees == ("R", "b3", "b5", "b7")

    voicing_degrees = content_degrees("Bm7b5", ContentFamily.SEVENTH_BASIC, RootSupportPolicy.ROOT_REQUIRED)
    assert [degree for degree, _ in voicing_degrees] == ["R", "b3", "b5", "b7"]


def test_v2_0_25_scale_policy_and_context_contract() -> None:
    dominant = resolve_scale_policy_detail("G7alt")
    half_dim = resolve_scale_policy_detail("Bm7b5")
    context = HarmonicContext.from_symbols(previous_chord_symbol="Dm7", chord_symbol="G7", next_chord_symbol="Cmaj7")

    assert dominant.mode == "altered"
    assert "b9" in dominant.available_tensions
    assert half_dim.mode == "locrian"
    assert context.current_chord.is_dominant
    assert context.next_chord is not None and context.next_chord.has_major_seventh
    assert context.scale_policy == "mixolydian"
