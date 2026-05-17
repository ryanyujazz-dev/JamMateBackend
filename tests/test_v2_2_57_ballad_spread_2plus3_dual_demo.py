from __future__ import annotations

# harness token: test_v2_2_73_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_foundation_lock

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_2PLUS3_PILOT_VERSION,
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    VoicingPolicy,
    generate_candidates,
    source_preserves_seventh_chord_identity,
)
from jammate_engine.core.voicing.disposition import project_basic_spread_candidates
from jammate_engine.realization.harmonic_realizer import _policy_with_event_texture_scope

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _two_plus_three_policy(*, expanded: bool = False) -> VoicingPolicy:
    metadata = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_runtime_pilot": {
            "version": "v2_2_73",
            "enabled": True,
            "scene": "warm_spread_phrase",
            "contract_ids": ["spread_2plus3_contract"],
            "preferred_contract_ids": ["spread_2plus3_contract"],
        },
        "ballad_spread_runtime_safe_dry_run": {
            "version": "v2_2_73",
            "dry_run_enabled": True,
            "candidate_conversion_allowed": True,
        },
        "spread_runtime_adapter_skeleton": {
            "version": "v2_2_73",
            "adapter_conversion_allowed": True,
        },
        "ballad_spread_runtime_candidate_pool": {
            "version": "v2_2_73",
            "candidate_pool_enabled": True,
            "adapter_conversion_allowed": True,
            "candidate_pool_merge_allowed": True,
            "candidate_generator_wiring_allowed": True,
            "fallback_to_existing_pool": True,
        },
        "ballad_spread_pilot_selection_weight_fallback_audit": {
            "version": "v2_2_73",
            "audit_enabled": True,
            "fallback_required": True,
            "max_spread_candidate_share": 1.0,
            "max_spread_score_margin": 0.15,
            "candidate_order_is_selection_priority": False,
        },
        "ballad_spread_pilot_runtime_enablement_guard": {
            "version": "v2_2_73",
            "runtime_guard_enabled": True,
            "listening_isolation_enabled": True,
            "first_listening_isolation_only": True,
        },
        "spread_contract_true_isolation": {
            "version": "v2_2_73",
            "enabled": True,
            "required_recipe_id": "spread_2plus3_contract",
            "fallback_only_when_missing": True,
        },
        "spread_lower_2note_foundation_mode": "rooted",
        "spread_lower_2note_rootless_is_separate_mode": True,
        "spread_lower_2note_foundation_lock_enabled": True,
        "spread_lower_2note_recipe_change_penalty": 6.0,
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": 40,
        "spread_root_bass_anchor_high": 52,
        "spread_root_bass_anchor_target": 47,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
        "spread_whole_register_low": 40,
        "spread_whole_register_high": 73,
        "spread_lower_2note_low": 40,
        "spread_lower_2note_high": 68,
        "spread_lower_2note_target_low": 40,
        "spread_lower_2note_min_top": 0,
        "spread_upper_low": 52,
        "spread_upper_target_low": 61,
        "spread_upper_3note_min_note_floor": 52,
        "spread_upper_3note_shell_plus_1_allowed": False,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 7,
        "spread_max_overall_span": 33,
        "spread_runtime_adapter_emit_all_candidates": True,
        "spread_emit_all_candidates_for_groupwise_selection": True,
        "spread_groupwise_voice_leading_runtime_enabled": True,
        "spread_lower_2note_rooted_equal_weight_cycle_enabled": False,
        "spread_lower_2note_rooted_recipe_weights": {
            "lower_2note_root_3": 1,
            "lower_2note_root_5": 1,
            "lower_2note_root_7": 1,
        },
    }
    if expanded:
        metadata.update(
            {
                "spread_upper_3note_expanded_color_target_ratio": 0.60,
                "spread_upper_3note_expanded_color_ratio_cycle": 5,
            }
        )
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        harmonic_expansion_enabled=expanded,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expanded else ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata=metadata,
    )


def test_v2_2_73_version_and_2plus3_pilot_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_2PLUS3_PILOT_VERSION == "v2_2_73"


def test_spread_2plus3_candidates_preserve_seventh_identity_for_seventh_chords() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={
            "harmonic_expansion_target_families": [ContentFamily.ROOTED_COLOR.value],
            "spread_upper_3note_expanded_color_only": True,
        },
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_2plus3_contract",),
        max_upper_options=8,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.recipe_contract.recipe_id == "spread_2plus3_contract"
        assert candidate.density == 5
        assert candidate.metadata["ballad_spread_2plus3_pilot_version"] == "v2_2_73"
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert source_preserves_seventh_chord_identity("Ebmaj7", candidate.degrees)


def test_true_isolation_generates_multiple_2plus3_spread_candidates_for_groupwise_selector() -> None:
    candidates = generate_candidates("Ebmaj7", _two_plus_three_policy())
    spread_candidates = [candidate for candidate in candidates if candidate.recipe_id == "spread_2plus3_contract"]
    assert len(spread_candidates) >= 1
    for candidate in spread_candidates:
        assert candidate.disposition == Disposition.SPREAD
        assert candidate.functional_grouping == "2+3"
        assert candidate.density == 5
        assert len(candidate.notes) == 5
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert candidate.metadata["lower_group_recipe_id"] in {
            "lower_2note_root_3",
            "lower_2note_root_5",
            "lower_2note_root_7",
        }
        assert candidate.metadata["lower_group_recipe_id"] != "lower_2note_3_7"
        lower_notes = candidate.metadata["lower_group_notes"]
        assert candidate.metadata["rooted_bass_anchor_enabled"] is True
        assert candidate.metadata["rooted_bass_anchor_passed"] is True
        assert min(candidate.notes) == candidate.metadata["root_bass_anchor_note"]
        assert 40 <= candidate.metadata["root_bass_anchor_note"] <= 52
        assert all(40 <= note <= 73 for note in candidate.notes)
        upper_notes = candidate.metadata["upper_group_notes"]
        assert min(upper_notes) >= 48
        assert candidate.metadata["upper_projection_method"] == "closed_upper_stack"
        assert max(upper_notes) - min(upper_notes) <= 12
        assert "R" not in candidate.metadata["upper_source_degrees"]


def test_event_scoped_expanded_ratio_forces_three_of_five_slots_only() -> None:
    policy = _two_plus_three_policy(expanded=True)
    selected_event = PatternEvent(
        event_id="a",
        track="piano",
        region_id="c0_b0_ch0",
        chord_symbol="Ebmaj7",
        onset_beat=0.0,
        role="harmonic",
    )
    unselected_event = PatternEvent(
        event_id="b",
        track="piano",
        region_id="c0_b1_ch1",
        chord_symbol="Ebmaj7",
        onset_beat=8.0,
        role="harmonic",
    )
    selected_policy = _policy_with_event_texture_scope(policy, selected_event)
    unselected_policy = _policy_with_event_texture_scope(policy, unselected_event)
    assert selected_policy.harmonic_expansion_enabled is True
    assert selected_policy.color_policy_mode == ColorPolicyMode.STYLE_SAFE_EXTENSIONS
    assert selected_policy.metadata["spread_upper_3note_expanded_color_only"] is True
    assert unselected_policy.harmonic_expansion_enabled is False
    assert unselected_policy.color_policy_mode == ColorPolicyMode.CHORD_SYMBOL_ONLY
    assert unselected_policy.metadata["spread_upper_3note_expanded_color_only"] is False


def test_lower_2note_rooted_family_is_equal_weight_not_event_forced_cycle() -> None:
    policy = _two_plus_three_policy(expanded=False)
    event = PatternEvent(
        event_id="e0",
        track="piano",
        region_id="c0_b0_ch0",
        chord_symbol="Ebmaj7",
        onset_beat=0.0,
        role="harmonic",
    )
    scoped = _policy_with_event_texture_scope(policy, event)
    assert scoped.metadata["spread_lower_2note_foundation_mode"] == "rooted"
    assert scoped.metadata["spread_lower_2note_rooted_equal_weight_cycle_enabled"] is False
    assert scoped.metadata["spread_lower_2note_foundation_lock_enabled"] is True
    assert scoped.metadata["spread_rooted_bass_anchor_enabled"] is True
    assert "spread_lower_2note_preferred_recipe_id" not in scoped.metadata
    assert scoped.metadata["spread_lower_2note_rooted_recipe_weights"] == {
        "lower_2note_root_3": 1,
        "lower_2note_root_5": 1,
        "lower_2note_root_7": 1,
    }


def test_projected_2plus3_excludes_rootless_lower_and_upper_shell_plus_one_by_default() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata={
            "spread_lower_2note_foundation_mode": "rooted",
            "spread_rooted_bass_anchor_enabled": True,
            "spread_root_bass_anchor_low": 40,
            "spread_root_bass_anchor_high": 52,
            "spread_root_bass_anchor_target": 47,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
            "spread_whole_register_low": 40,
            "spread_whole_register_high": 73,
            "spread_lower_2note_low": 40,
            "spread_lower_2note_high": 68,
            "spread_upper_low": 52,
            "spread_upper_target_low": 61,
            "spread_upper_3note_shell_plus_1_allowed": False,
        },
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_2plus3_contract",),
        max_upper_options=8,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    assert {candidate.metadata["lower_group_recipe_id"] for candidate in legal} <= {
        "lower_2note_root_3",
        "lower_2note_root_5",
        "lower_2note_root_7",
    }
    assert all(candidate.metadata["lower_group_recipe_id"] != "lower_2note_3_7" for candidate in legal)
    assert all(candidate.metadata["rooted_bass_anchor_enabled"] is True for candidate in legal)
    assert all(candidate.metadata["rooted_bass_anchor_passed"] is True for candidate in legal)
    assert all(min(candidate.notes) == candidate.metadata["root_bass_anchor_note"] for candidate in legal)
    assert all(40 <= candidate.metadata["root_bass_anchor_note"] <= 52 for candidate in legal)
    assert all(all(40 <= note <= 73 for note in candidate.notes) for candidate in legal)
    assert all(min(candidate.upper_notes) >= 48 for candidate in legal)
    assert all(max(candidate.upper_notes) - min(candidate.upper_notes) <= 12 for candidate in legal)
    assert {candidate.upper_projection_method for candidate in legal} == {"closed_upper_stack"}
    assert all("R" not in candidate.metadata["upper_source_degrees"] for candidate in legal if candidate.metadata["upper_source_family"] in {"shell_plus_5", "shell_plus_color"})


def test_2plus3_dual_demo_script_requests_unexpanded_and_expanded_60pct_outputs() -> None:
    script = _read("examples/scripts/generate_ballad_spread_2plus3_dual_listening_demos.py")
    assert "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_unexpanded_demo.mid" in script
    assert "v2_2_73_misty_jazz_ballad_spread_2plus3_root_anchor_e2_e3_gap_p5_expanded_60pct_demo.mid" in script
    assert '"required_recipe_id": _CONTRACT_ID' in script
    assert '"spread_upper_3note_expanded_color_target_ratio": 0.60' in script
    assert "actual_expanded_ratio" in script
    assert '"spread_lower_2note_foundation_mode": "rooted"' in script
    assert '"spread_upper_3note_shell_plus_1_allowed": False' in script
    assert '"spread_rooted_bass_anchor_enabled": True' in script
    assert '"spread_root_bass_anchor_low": 40' in script
    assert '"spread_whole_register_low": 40' in script
    assert '"spread_groupwise_voice_leading_runtime_enabled": True' in script


def test_spread_selector_collapses_multiple_2plus3_candidates_by_groupwise_vl() -> None:
    from jammate_engine.core.voicing import VoicingState, select_candidate

    policy = _two_plus_three_policy(expanded=False)
    candidates = generate_candidates("Bb7", policy)
    spread_candidates = [candidate for candidate in candidates if candidate.recipe_id == "spread_2plus3_contract"]
    assert len(spread_candidates) >= 1
    previous_state = VoicingState.empty().advance(
        event_id="prev",
        chord_symbol="Fm7",
        notes=[41, 48, 53, 56, 60],
        degrees=["R", "b7", "b3", "5", "b7"],
        metadata={
            "lower_group_notes": [41, 48],
            "upper_group_notes": [53, 56, 60],
            "group_gap_semitones": 5,
        },
    )
    selected = select_candidate(candidates, policy=policy, state=previous_state)
    assert selected.recipe_id == "spread_2plus3_contract"
    assert selected.metadata["spread_groupwise_voice_leading_runtime_applied"] is True
    assert selected.metadata["spread_groupwise_voice_leading_candidate_count"] == len(spread_candidates)
    assert selected.metadata["rooted_bass_anchor_passed"] is True
    assert min(selected.notes) == selected.metadata["root_bass_anchor_note"]
    assert min(selected.metadata["upper_group_notes"]) >= 48
    assert max(selected.metadata["upper_group_notes"]) - min(selected.metadata["upper_group_notes"]) <= 12
