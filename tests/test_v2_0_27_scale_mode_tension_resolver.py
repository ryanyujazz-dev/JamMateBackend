from __future__ import annotations

from jammate_engine.core.harmony import resolve_scale_policy, resolve_scale_policy_detail
from jammate_engine.core.harmony.material import scale_pitch_classes


def test_v2_0_27_major_minor_and_sixth_mode_policy() -> None:
    major_seventh = resolve_scale_policy_detail("Cmaj7")
    major_six = resolve_scale_policy_detail("C6/9")
    minor_seventh = resolve_scale_policy_detail("Cm9")
    minor_six = resolve_scale_policy_detail("Cm6")
    minor_major = resolve_scale_policy_detail("CmMaj7")

    assert resolve_scale_policy("Cmaj7") == "lydian"
    assert major_seventh.scale_degrees == ("R", "9", "3", "#11", "5", "13", "7")
    assert "#11" in major_seventh.available_tensions
    assert "11" in major_seventh.avoid_degrees

    assert major_six.mode == "ionian"
    assert "11" in major_six.scale_degrees
    assert major_six.available_tensions == ("9",)

    assert minor_seventh.mode == "dorian"
    assert minor_seventh.chord_tone_degrees == ("R", "b3", "5", "b7")
    assert {"9", "11", "13"}.issubset(set(minor_seventh.available_tensions))

    assert minor_six.mode == "melodic_minor"
    assert minor_major.mode == "melodic_minor"
    assert "7" in minor_major.scale_degrees


def test_v2_0_27_dominant_alteration_and_sus_policy() -> None:
    dominant = resolve_scale_policy_detail("G13")
    sharp_eleven = resolve_scale_policy_detail("G7#11")
    flat_nine = resolve_scale_policy_detail("G7b9")
    altered = resolve_scale_policy_detail("G7alt")
    augmented = resolve_scale_policy_detail("G7#5")
    sus = resolve_scale_policy_detail("G7sus")

    assert dominant.mode == "mixolydian"
    assert dominant.available_tensions == ("9", "13")
    assert dominant.avoid_degrees == ("11",)

    assert sharp_eleven.mode == "lydian_dominant"
    assert sharp_eleven.explicit_alterations == ("#11",)
    assert "#11" in sharp_eleven.available_tensions
    assert "11" not in sharp_eleven.avoid_degrees

    # Compatibility: explicit b9 dominants remain mixolydian-family in v2_0_27,
    # but the explicit alteration replaces natural 9 in the detailed pitch set.
    assert flat_nine.mode == "mixolydian"
    assert "b9" in flat_nine.available_tensions
    assert "9" not in flat_nine.available_tensions
    assert (7 + 1) % 12 in flat_nine.pitch_classes

    assert altered.mode == "altered"
    assert altered.scale_degrees == ("R", "b9", "#9", "3", "#11", "b13", "b7")
    assert altered.avoid_degrees == ()

    assert augmented.mode == "whole_tone"
    assert "#5" in augmented.explicit_alterations
    assert "#5" in augmented.scale_degrees

    assert sus.mode == "mixolydian_sus"
    assert "3" in sus.avoid_degrees
    assert "4" in sus.chord_tone_degrees


def test_v2_0_27_half_diminished_and_diminished_policy() -> None:
    half_dim = resolve_scale_policy_detail("Bm7b5")
    half_dim_natural_two = resolve_scale_policy_detail("Bm9b5")
    dim_triad = resolve_scale_policy_detail("Cdim")
    dim_seventh = resolve_scale_policy_detail("Co7")

    assert half_dim.mode == "locrian"
    assert "b9" in half_dim.scale_degrees
    assert half_dim.available_tensions == ("b9", "11", "b13")
    assert half_dim.avoid_degrees == ()

    assert half_dim_natural_two.mode == "locrian_natural_2"
    assert "9" in half_dim_natural_two.scale_degrees
    assert "b9" not in half_dim_natural_two.avoid_degrees

    assert dim_triad.mode == "locrian"
    assert dim_triad.chord_tone_degrees == ("R", "b3", "b5")

    assert dim_seventh.mode == "whole_half_diminished"
    assert dim_seventh.chord_tone_degrees == ("R", "b3", "b5", "bb7")
    assert "7" in dim_seventh.available_tensions


def test_v2_0_27_compatibility_scale_pitch_classes_remain_stable_for_bassfoundation() -> None:
    # BassFoundation still consumes the legacy compatibility helper through
    # generation/bass_foundation/rules.py, so this output stays stable in this
    # pass while the detailed resolver carries richer mode metadata.
    assert scale_pitch_classes("Cmaj7") == {0, 2, 4, 6, 7, 9, 11}
    assert scale_pitch_classes("G7") == {7, 9, 11, 0, 2, 4, 5}
