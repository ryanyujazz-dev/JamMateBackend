from __future__ import annotations

from jammate_engine.core.harmony import HarmonicContext, classify_functional_motion


def test_v2_0_28_major_ii_v_i_window_detection() -> None:
    context = HarmonicContext.from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
    )
    motion = context.functional_motion

    assert motion.previous_to_current_type == "ii_v"
    assert motion.current_to_next_type == "v_i_major"
    assert motion.window_type == "major_ii_v_i"
    assert motion.is_ii_v_i
    assert motion.is_dominant_resolution
    assert motion.root_interval_from_previous == 5
    assert motion.root_interval_to_next == 5
    assert motion.has_tag("cycle_of_fourths")


def test_v2_0_28_current_next_ii_v_and_v_i_pair_detection() -> None:
    ii_v = classify_functional_motion(chord_symbol="Dm7", next_chord_symbol="G13")
    v_i = classify_functional_motion(chord_symbol="G7b9", next_chord_symbol="C6/9")

    assert ii_v.current_to_next_type == "ii_v"
    assert ii_v.is_current_next_ii_v
    assert ii_v.current_function == "predominant_minor_or_minor_tonic"
    assert ii_v.next_function == "dominant"

    assert v_i.current_to_next_type == "v_i_major"
    assert v_i.is_current_next_v_i
    assert v_i.is_dominant_resolution
    assert v_i.next_function == "tonic_major_candidate"


def test_v2_0_28_minor_two_five_one_window_detection() -> None:
    context = HarmonicContext.from_symbols(
        previous_chord_symbol="Bm7b5",
        chord_symbol="E7b9",
        next_chord_symbol="Am6",
    )
    motion = context.functional_motion

    assert motion.previous_to_current_type == "minor_ii_v"
    assert motion.current_to_next_type == "v_i_minor"
    assert motion.window_type == "minor_ii_v_i"
    assert motion.is_minor_ii_v
    assert motion.is_minor_ii_v_i
    assert motion.is_dominant_resolution


def test_v2_0_28_tonic_prolongation_and_turnaround_like_metadata() -> None:
    prolongation = classify_functional_motion(chord_symbol="Cmaj7", next_chord_symbol="C6/9")
    turnaround_opening = classify_functional_motion(
        previous_chord_symbol="Cmaj7",
        chord_symbol="A7",
        next_chord_symbol="Dm7",
    )
    turnaround_middle = classify_functional_motion(
        previous_chord_symbol="A7",
        chord_symbol="Dm7",
        next_chord_symbol="G7",
    )

    assert prolongation.current_to_next_type == "tonic_prolongation"
    assert prolongation.is_tonic_prolongation

    assert turnaround_opening.current_to_next_type == "v_i_minor"
    assert turnaround_opening.window_type == "turnaround_like"
    assert turnaround_opening.is_turnaround_like
    assert turnaround_opening.root_interval_from_previous == 9

    assert turnaround_middle.current_to_next_type == "ii_v"
    assert turnaround_middle.window_type == "turnaround_like"
    assert turnaround_middle.is_turnaround_like


def test_v2_0_28_non_functional_adjacent_change_stays_neutral() -> None:
    motion = classify_functional_motion(chord_symbol="Cmaj7", next_chord_symbol="F#m7")

    assert motion.current_to_next_type == "non_functional"
    assert motion.is_non_functional
    assert not motion.is_current_next_ii_v
    assert not motion.is_current_next_v_i
    assert motion.window_type == "none"
    assert motion.tags == ()
