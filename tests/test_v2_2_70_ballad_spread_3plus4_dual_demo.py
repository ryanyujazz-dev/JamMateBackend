from __future__ import annotations

# harness token: test_v2_2_76_ballad_spread_3plus4_color_upper_a1_g5_register_dual_demo

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_3PLUS4_PILOT_VERSION,
    ColorPolicyMode,
    Disposition,
    VoicingPolicy,
    source_preserves_seventh_chord_identity,
)
from jammate_engine.core.voicing.disposition import project_basic_spread_candidates


def _three_plus_four_policy(*, expanded: bool = False) -> VoicingPolicy:
    metadata = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_runtime_pilot": {
            "version": "v2_2_76",
            "enabled": True,
            "scene": "warm_spread_phrase",
            "contract_ids": ["spread_3plus4_contract"],
            "preferred_contract_ids": ["spread_3plus4_contract"],
        },
        "spread_contract_true_isolation": {
            "version": "v2_2_76",
            "enabled": True,
            "required_recipe_id": "spread_3plus4_contract",
            "fallback_only_when_missing": True,
        },
        "spread_lower_3note_foundation_mode": "rooted",
        "spread_lower_3note_rootless_is_separate_mode": True,
        "spread_lower_3note_foundation_lock_enabled": True,
        "spread_lower_foundation_quality_gate_enabled": True,
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": 33,
        "spread_root_bass_anchor_high": 48,
        "spread_root_bass_anchor_target": 39,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
        "spread_whole_register_low": 33,
        "spread_whole_register_high": 79,
        "spread_upper_low": 52,
        "spread_upper_high": 79,
        "spread_upper_target_low": 61,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 7,
        "spread_max_overall_span": 43,
        "spread_upper_4note_emit_all_parent_projections": True,
        "spread_upper_4note_allow_octave_shift_candidates": True,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
    }
    if expanded:
        metadata.update(
            {
                "spread_upper_4note_expanded_color_target_ratio": 0.60,
                "spread_upper_4note_expanded_color_ratio_cycle": 5,
            }
        )
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        harmonic_expansion_enabled=expanded,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expanded else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata=metadata,
    )


def test_v2_2_76_version_and_3plus4_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert BALLAD_SPREAD_3PLUS4_PILOT_VERSION == "v2_2_76"


def test_spread_3plus4_reuses_3plus3_lower_and_2plus4_upper_without_drop2_and_4() -> None:
    policy = _three_plus_four_policy(expanded=True)
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_3plus4_contract",),
        max_upper_options=24,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.recipe_contract.recipe_id == "spread_3plus4_contract"
        assert candidate.density == 7
        assert candidate.metadata["ballad_spread_3plus4_pilot_version"] == "v2_2_76"
        assert candidate.metadata["rooted_bass_anchor_enabled"] is True
        assert candidate.metadata["rooted_bass_anchor_passed"] is True
        assert candidate.metadata["root_bass_anchor_low"] == 33
        assert candidate.metadata["root_bass_anchor_high"] == 48
        assert candidate.metadata["root_bass_anchor_target"] == 39
        assert min(candidate.notes) == candidate.metadata["root_bass_anchor_note"]
        assert 33 <= candidate.metadata["root_bass_anchor_note"] <= 48
        # v2_2_76: 3+4 uses an A1-C3 whole-register-aware root window with
        # an Eb2 target so the thick lower group stays below the color upper block.
        assert candidate.metadata["lower_group_max_note"] <= 62
        assert all(33 <= note <= 79 for note in candidate.notes)
        assert candidate.metadata["whole_register_high"] == 79
        assert candidate.metadata["register_policy"]["upper_high"] == 79
        assert candidate.metadata["lower_group_recipe_id"] == "lower_3note_root_7_upper3"
        assert candidate.metadata["root_bass_anchor_high_tail_span_guard_enabled"] is False
        assert candidate.metadata["lower_group_anchor_tail_span_guard_passed"] is None
        assert candidate.lower.span_semitones > 12
        assert candidate.upper_projection_method in {"drop2", "drop3"}
        assert candidate.upper_projection_method != "drop2_and_4"
        assert candidate.metadata["upper_projection_metadata"]["spread_upper_4note_drop2_and_4_allowed"] is False
        assert candidate.metadata["upper_projection_metadata"]["spread_upper_4note_emit_all_parent_projections"] is True
        assert candidate.metadata["spread_3plus4_upper_4note_color_only_enabled"] is True
        assert candidate.metadata["spread_3plus4_upper_4note_color_only_version"] == "v2_2_76"
        assert candidate.metadata["spread_3plus4_upper_source_color_passed"] is True
        assert candidate.metadata["spread_3plus4_musical_closure_version"] == "v2_2_76"
        assert candidate.metadata["spread_3plus4_upper_rootless_color_preferred"] is True
        assert candidate.metadata["spread_3plus4_upper_rootless_color_passed"] is True
        assert candidate.metadata["upper_source_contains_root_degree"] is False
        assert candidate.metadata["upper_source_family"] in {"rootless_A", "rootless_B"}
        assert any(degree in {"9", "b9", "#9", "11", "#11", "13", "b13"} for degree in candidate.metadata["upper_source_degrees"])
        assert candidate.metadata["group_gap_semitones"] <= 7
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert source_preserves_seventh_chord_identity("Ebmaj7", candidate.degrees)



def test_spread_3plus4_high_root_ab_uses_register_compression_under_g5() -> None:
    policy = _three_plus_four_policy(expanded=True)
    result = project_basic_spread_candidates(
        "Abmaj7",
        policy=policy,
        contract_ids=("spread_3plus4_contract",),
        max_upper_options=30,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.metadata["lower_group_recipe_id"] == "lower_3note_root_7_upper3"
        assert candidate.metadata["spread_3plus4_lower_upper3_compressed_within_root_octave"] is True
        assert min(candidate.notes) >= 33
        assert max(candidate.notes) <= 79
        assert candidate.metadata["group_gap_semitones"] <= 7
        assert candidate.metadata["spread_3plus4_upper_source_color_passed"] is True
        assert candidate.metadata["spread_3plus4_upper_rootless_color_passed"] is True
        assert candidate.metadata["upper_source_contains_root_degree"] is False
        assert candidate.metadata["rooted_bass_anchor_passed"] is True

def test_spread_3plus4_uses_root5upper3_for_triad_family_chords() -> None:
    policy = _three_plus_four_policy(expanded=True)
    result = project_basic_spread_candidates(
        "C",
        policy=policy,
        contract_ids=("spread_3plus4_contract",),
        max_upper_options=24,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.metadata["lower_group_recipe_id"] == "lower_3note_root_5_upper3"
        assert candidate.metadata["root_bass_anchor_high_tail_span_guard_enabled"] is False
        assert candidate.upper_projection_method in {"drop2", "drop3"}
        assert candidate.upper_projection_method != "drop2_and_4"
        assert candidate.metadata["spread_3plus4_upper_4note_color_only_enabled"] is True
        assert candidate.metadata["spread_3plus4_upper_source_color_passed"] is True
        # Plain triad-family 3+4 has no rootless A/B upper source, so it may fall
        # back to triad/add/6 color material while seventh-family chords prefer rootless upper.
        assert candidate.metadata["spread_3plus4_upper_rootless_color_passed"] is False
        assert candidate.metadata["register_policy"]["upper_high"] == 79
        assert all(33 <= note <= 79 for note in candidate.notes)
        assert candidate.metadata["group_gap_semitones"] <= 7
