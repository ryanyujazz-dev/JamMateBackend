from __future__ import annotations

from jammate_engine.core.voicing.disposition import (
    BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION,
    BalladSpreadGroupingMixScene,
    project_basic_spread_contract,
    resolve_ballad_spread_grouping_mix_policy,
)
from jammate_engine.core.voicing.policy import VoicingPolicy
from jammate_engine.core.voicing.selection.voice_leading import set_based_voice_leading_distance


def test_v2_2_82_grouping_mix_uses_texture_state_not_free_event_random() -> None:
    decision = resolve_ballad_spread_grouping_mix_policy(
        {"metadata": {"ballad_spread_grouping_mix_policy": {"enabled": True, "weight_cycle": 100}}},
        event_context={"region_id": "c0_b11_ch0", "region_chorus_index": 0, "region_total_choruses": 3, "region_bar_index": 11},
    )
    assert BALLAD_SPREAD_GROUPING_MIX_POLICY_VERSION == "v2_2_84"
    assert decision.enabled is True
    assert decision.texture_state_enabled is True
    assert decision.texture_state_id
    assert decision.compatible_contract_ids
    assert "spread_1plus3_contract" not in decision.compatible_contract_ids
    assert decision.selected_contract_id in decision.compatible_contract_ids
    assert decision.reason == "selected_existing_spread_contract_from_texture_state_mix"


def test_v2_2_82_ending_texture_state_allows_3plus4_without_normalizing_it() -> None:
    ending = resolve_ballad_spread_grouping_mix_policy(
        {"metadata": {"ballad_spread_grouping_mix_policy": {"enabled": True, "weight_cycle": 100}}},
        event_context={"region_id": "c2_b30_ch0", "region_chorus_index": 2, "region_total_choruses": 3, "region_bar_index": 30},
    )
    assert ending.scene == BalladSpreadGroupingMixScene.ENDING_CLIMAX
    assert "spread_3plus4_contract" in ending.compatible_contract_ids
    assert ending.weights["spread_3plus4_contract"] > 0
    assert ending.weights["spread_1plus4_contract"] == 0


def test_v2_2_82_set_based_voice_leading_treats_extra_color_as_inserted_voice() -> None:
    profile = set_based_voice_leading_distance((64, 67, 71), (62, 64, 67, 71), birth_death_penalty=3.0)
    assert profile.common_tones == 3
    assert profile.inserted_notes == (62,)
    assert profile.released_notes == ()
    assert profile.distance == 3.0
    debug = profile.to_debug_dict()
    assert debug["handles_unequal_note_counts"] is True
    assert debug["does_not_zip_by_index"] is True


def test_v2_2_82_1plus4_closes_gap_by_upper_candidates_not_lower_root_lift() -> None:
    policy = VoicingPolicy(
        metadata={
            "spread_upper_4note_emit_all_parent_projections": True,
            "spread_upper_4note_allow_octave_shift_candidates": True,
            "spread_upper_low": 45,
            "spread_upper_target_low": 50,
            "spread_min_group_gap": 1,
            "spread_max_group_gap": 28,
        }
    )
    result = project_basic_spread_contract("Ebmaj7", "spread_1plus4_contract", policy, max_upper_options=20)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    assert min(candidate.group_gap_semitones or 999 for candidate in legal) <= 12
    assert all(candidate.lower_notes == (39,) for candidate in legal)
    assert any(min(candidate.upper_notes) <= 51 for candidate in legal)


def test_v2_2_82_spread_top_voice_continuity_prefers_closer_soprano_line() -> None:
    from jammate_engine.core.voicing.disposition import Disposition
    from jammate_engine.core.voicing.selection.candidate import VoicingCandidate
    from jammate_engine.core.voicing.selection.selector import select_candidate
    from jammate_engine.core.voicing.runtime.state import VoicingState

    state = VoicingState(
        previous_notes=(40, 52, 56, 60, 64),
        previous_top_note=64,
        metadata={"lower_group_notes": [40], "upper_group_notes": [52, 56, 60, 64], "group_gap_semitones": 12},
    )
    policy = VoicingPolicy(
        selector_temperature=0.0,
        metadata={
            "spread_groupwise_voice_leading_runtime_enabled": True,
            "spread_top_voice_continuity_weight": 2.0,
            "spread_target_group_gap": 7,
            "spread_comfort_group_gap_max": 12,
        },
    )
    jumpy = VoicingCandidate(
        notes=[40, 52, 56, 60, 76],
        degrees=["R", "3", "5", "7", "9"],
        disposition=Disposition.SPREAD,
        metadata={"lower_group_notes": [40], "upper_group_notes": [52, 56, 60, 76], "group_gap_semitones": 12},
    )
    close = VoicingCandidate(
        notes=[40, 52, 56, 60, 65],
        degrees=["R", "3", "5", "7", "9"],
        disposition=Disposition.SPREAD,
        metadata={"lower_group_notes": [40], "upper_group_notes": [52, 56, 60, 65], "group_gap_semitones": 12},
    )
    selected = select_candidate([jumpy, close], policy=policy, state=state)
    profile = selected.metadata["spread_top_voice_continuity_profile"]
    assert max(selected.notes) == 65
    assert selected.metadata["spread_top_voice_continuity_runtime_applied"] is True
    assert profile["version"] == "v2_2_84"
    assert profile["top_voice_abs_motion"] == 1
    assert profile["label"] == "close"
