from __future__ import annotations

from jammate_engine.core.voicing.disposition import project_basic_spread_contract
from jammate_engine.core.voicing.policy import VoicingPolicy


def _policy() -> VoicingPolicy:
    return VoicingPolicy(
        metadata={
            "spread_upper_4note_emit_all_parent_projections": True,
            "spread_upper_4note_allow_octave_shift_candidates": True,
            "spread_upper_low": 45,
            "spread_upper_target_low": 50,
            "spread_min_group_gap": 1,
            "spread_max_group_gap": 28,
            "spread_target_group_gap": 7,
            "spread_comfort_group_gap_max": 12,
            "spread_large_group_gap_penalty": 6.0,
            "spread_group_gap_target_penalty": 0.08,
        }
    )


def test_spread_1plus4_upper_candidates_can_close_gap_without_lifting_lower_root() -> None:
    result = project_basic_spread_contract("Ebmaj7", "spread_1plus4_contract", _policy(), max_upper_options=20)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    assert min(candidate.group_gap_semitones or 999 for candidate in legal) <= 12
    assert all(candidate.lower_notes == (39,) for candidate in legal)


def test_spread_1plus4_upper_candidate_register_covers_common_ballad_roots() -> None:
    for chord_symbol in ("Abmaj7", "Ebmaj7", "Bb7"):
        result = project_basic_spread_contract(chord_symbol, "spread_1plus4_contract", _policy(), max_upper_options=20)
        legal = [candidate for candidate in result.candidates if candidate.is_legal]
        assert legal
        assert min(candidate.group_gap_semitones or 999 for candidate in legal) <= 12
