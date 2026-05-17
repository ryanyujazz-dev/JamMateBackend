from __future__ import annotations

from jammate_engine.core.harmony import (
    chord_material,
    degree_to_semitone,
    parse_chord,
    resolve_degree_token,
    resolve_scale_policy_detail,
)


def test_v2_0_26_major_symbol_aliases_and_extensions() -> None:
    for symbol in ("CM7", "Cmaj7", "Cmaj9", "CΔ", "C^", "C^7"):
        chord = parse_chord(symbol)
        material = chord_material(symbol)
        assert chord.quality == "major"
        assert chord.has_major_seventh
        assert not chord.has_minor_seventh
        assert not chord.is_dominant
        assert material.seventh_degree == "7"
        assert material.chord_tone_degrees == ("R", "3", "5", "7")

    assert parse_chord("Cmaj9").extensions == ("9",)


def test_v2_0_26_minor_and_minor_major_symbol_aliases() -> None:
    minor = parse_chord("C-9")
    minor_major = parse_chord("CmMaj7")

    assert minor.quality == "minor"
    assert minor.has_minor_seventh
    assert minor.extensions == ("9",)
    assert chord_material("C-9").chord_tone_degrees == ("R", "b3", "5", "b7")

    assert minor_major.quality == "minor"
    assert minor_major.has_major_seventh
    assert not minor_major.has_minor_seventh
    assert chord_material("CmMaj7").seventh_degree == "7"


def test_v2_0_26_plain_9_11_13_symbols_imply_dominant_seventh() -> None:
    for symbol in ("G9", "G11", "G13", "G7b9", "G7#11", "G13b9"):
        chord = parse_chord(symbol)
        material = chord_material(symbol)
        assert chord.is_dominant
        assert chord.has_minor_seventh
        assert material.seventh_degree == "b7"

    altered = parse_chord("G7b9#11")
    assert altered.alterations == ("b9", "#11")
    assert resolve_scale_policy_detail("G7b9").mode == "mixolydian"
    assert "b9" in resolve_scale_policy_detail("G7b9").available_tensions


def test_v2_0_26_suspended_sixth_halfdim_dim_and_slash_metadata() -> None:
    sus = parse_chord("G7sus")
    six_nine = parse_chord("C6/9")
    slash = parse_chord("Cmaj7/E")
    half_dim = parse_chord("Bø7")
    full_dim = parse_chord("Co7")

    assert sus.quality == "sus4"
    assert sus.is_suspended
    assert sus.is_dominant
    assert chord_material("G7sus").chord_tone_degrees == ("R", "4", "5", "b7")

    assert six_nine.quality == "major"
    assert six_nine.has_sixth
    assert not six_nine.has_seventh
    assert not six_nine.is_dominant

    assert slash.root_name == "C"
    assert slash.root_pc == 0
    assert slash.has_slash_bass
    assert slash.bass_name == "E"
    assert slash.bass_pc == 4
    assert chord_material("Cmaj7/E").root_pc == 0

    assert half_dim.quality == "half_diminished"
    assert chord_material("Bø7").chord_tone_degrees == ("R", "b3", "b5", "b7")

    assert full_dim.quality == "diminished"
    assert full_dim.has_seventh
    assert chord_material("Co7").seventh_degree == "bb7"
    assert resolve_degree_token(chord_symbol="Co7", token="Seventh").pitch_class == 9


def test_v2_0_26_degree_aliases_and_literal_fourth_policy() -> None:
    assert resolve_degree_token(chord_symbol="C", token="4", next_chord_symbol="F").degree == "nextR"
    assert resolve_degree_token(chord_symbol="C", token="4", next_chord_symbol="F").pitch_class == 5
    assert resolve_degree_token(chord_symbol="C", token="literal4", next_chord_symbol="G").degree == "degree4"
    assert resolve_degree_token(chord_symbol="C", token="literal4", next_chord_symbol="G").pitch_class == 5
    assert resolve_degree_token(chord_symbol="C", token="minor_third").pitch_class == 3
    assert resolve_degree_token(chord_symbol="C", token="major_seventh").pitch_class == 11
    assert resolve_degree_token(chord_symbol="G7", token="flat_ninth").pitch_class == 8
    assert resolve_degree_token(chord_symbol="G7", token="sharp_eleventh").pitch_class == 1
    assert resolve_degree_token(chord_symbol="G7", token="flat_thirteenth").pitch_class == 3
    assert resolve_degree_token(chord_symbol="Dm7", token="scale_below_next_root", next_chord_symbol="G7").pitch_class == 5
    assert resolve_degree_token(chord_symbol="Dm7", token="dominant_next_root", next_chord_symbol="G7").pitch_class == 2

    assert degree_to_semitone("b9", stacked=True) == 13
    assert degree_to_semitone("#9", stacked=True) == 15
    assert degree_to_semitone("b13", stacked=True) == 20
