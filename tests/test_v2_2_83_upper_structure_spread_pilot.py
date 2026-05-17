from __future__ import annotations

from jammate_engine.core.voicing.policy import ColorPolicyMode, VoicingPolicy
from jammate_engine.core.voicing.disposition.spread import (
    LowerGroupRecipeId,
    project_basic_spread_contract,
)
from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources


def _policy() -> VoicingPolicy:
    return VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={
            "spread_upper_structure_enabled": True,
            "spread_upper_structure_only": True,
            "spread_upper_structure_lower_gate_enabled": True,
            "spread_low_register_density_guard_enabled": True,
            "spread_low_register_density_threshold": 40,
            "spread_low_register_density_max_notes_below": 1,
            "spread_rooted_bass_anchor_enabled": True,
            "spread_root_bass_anchor_low": 33,
            "spread_root_bass_anchor_high": 48,
            "spread_root_bass_anchor_target": 39,
            "spread_upper_4note_emit_all_parent_projections": True,
            "spread_upper_4note_allow_octave_shift_candidates": True,
        },
    )


def test_upper_structure_sources_are_source_only_and_density_specific() -> None:
    triads = plan_upper_structure_sources("G7", density=3, policy=_policy())
    four_note = plan_upper_structure_sources("G7", density=4, policy=_policy())

    assert triads
    assert four_note
    assert all(source.density == 3 for source in triads)
    assert all("source_only_reuses_existing_projection" in source.source_notes for source in triads)
    assert all("three_note_reuses_closed_inversion" in source.source_notes for source in triads)
    assert all("four_note_reuses_closed_inversion_drop2_drop3" in source.source_notes for source in four_note)


def test_upper_structure_spread_2plus3_uses_shell_lower_and_existing_closed_stack() -> None:
    result = project_basic_spread_contract("G7", "spread_2plus3_contract", _policy(), max_upper_options=36)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]

    assert legal
    assert {candidate.lower.instance.recipe.recipe_id for candidate in legal} == {LowerGroupRecipeId.THIRD_SEVENTH}
    assert all(candidate.metadata["upper_structure_source_enabled"] is True for candidate in legal)
    assert all(candidate.metadata["upper_structure_lower_mode"] == "shell" for candidate in legal)
    assert all(candidate.upper_projection_method == "closed_upper_stack" for candidate in legal)


def test_upper_structure_spread_3plus3_uses_root_shell_lower_and_low_register_guard() -> None:
    result = project_basic_spread_contract("G7", "spread_3plus3_contract", _policy(), max_upper_options=36)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]

    assert legal
    assert {candidate.metadata["upper_structure_lower_mode"] for candidate in legal} <= {"root_plus_shell"}
    assert all(candidate.metadata["low_register_density_guard"]["enabled"] is True for candidate in legal)
    assert all(candidate.metadata["low_register_density_guard"]["actual_notes_below"] <= 1 for candidate in legal)
    assert all(candidate.metadata["upper_structure_source_enabled"] is True for candidate in legal)


def test_upper_structure_spread_2plus4_reuses_drop2_drop3_only() -> None:
    result = project_basic_spread_contract("G7", "spread_2plus4_contract", _policy(), max_upper_options=36)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]

    assert legal
    assert all(candidate.metadata["upper_structure_source_enabled"] is True for candidate in legal)
    assert {candidate.upper_projection_method for candidate in legal} <= {"drop2", "drop3"}
    assert "drop2_and_4" not in {candidate.upper_projection_method for candidate in legal}
