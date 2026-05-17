from __future__ import annotations

# harness token: test_v2_2_73_ballad_spread_2plus4_pilot_dual_demo

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_2PLUS4_PILOT_VERSION,
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


def _two_plus_four_policy(*, expanded: bool = False) -> VoicingPolicy:
    metadata = {
        "style": "jazz_ballad",
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_runtime_pilot": {
            "version": "v2_2_73",
            "enabled": True,
            "scene": "warm_spread_phrase",
            "contract_ids": ["spread_2plus4_contract"],
            "preferred_contract_ids": ["spread_2plus4_contract"],
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
            "required_recipe_id": "spread_2plus4_contract",
            "fallback_only_when_missing": True,
        },
        "spread_lower_2note_foundation_mode": "rooted",
        "spread_lower_2note_rootless_is_separate_mode": True,
        "spread_lower_2note_foundation_lock_enabled": True,
        "spread_lower_2note_recipe_change_penalty": 6.0,
        "spread_lower_2note_rooted_equal_weight_cycle_enabled": False,
        "spread_lower_2note_rooted_recipe_weights": {
            "lower_2note_root_3": 1,
            "lower_2note_root_5": 1,
            "lower_2note_root_7": 1,
        },
        "spread_rooted_bass_anchor_enabled": True,
        "spread_root_bass_anchor_low": 40,
        "spread_root_bass_anchor_high": 52,
        "spread_root_bass_anchor_target": 47,
        "spread_root_bass_anchor_high_tail_semitones": 4,
        "spread_root_bass_anchor_high_tail_max_lower_span": 12,
        "spread_whole_register_low": 40,
        "spread_whole_register_high": 83,
        "spread_whole_register_target_span": 34,
        "spread_lower_2note_low": 40,
        "spread_lower_2note_high": 83,
        "spread_lower_2note_target_low": 40,
        "spread_lower_2note_min_top": 0,
        "spread_upper_low": 52,
        "spread_upper_target_low": 61,
        "spread_min_group_gap": 1,
        "spread_max_group_gap": 7,
        "spread_max_overall_span": 43,
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


def test_v2_2_73_version_and_2plus4_pilot_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_2PLUS4_PILOT_VERSION == "v2_2_73"


def test_spread_2plus4_reuses_2plus3_lower_and_1plus4_upper_without_drop2_and_4() -> None:
    policy = _two_plus_four_policy()
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_2plus4_contract",),
        max_upper_options=12,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.recipe_contract.recipe_id == "spread_2plus4_contract"
        assert candidate.density == 6
        assert candidate.metadata["ballad_spread_2plus4_pilot_version"] == "v2_2_73"
        assert candidate.metadata["rooted_bass_anchor_enabled"] is True
        assert candidate.metadata["rooted_bass_anchor_passed"] is True
        assert min(candidate.notes) == candidate.metadata["root_bass_anchor_note"]
        assert 40 <= candidate.metadata["root_bass_anchor_note"] <= 52
        assert all(40 <= note <= 83 for note in candidate.notes)
        assert candidate.metadata["lower_group_recipe_id"] in {
            "lower_2note_root_3",
            "lower_2note_root_5",
            "lower_2note_root_7",
        }
        assert candidate.metadata["lower_group_recipe_id"] != "lower_2note_3_7"
        assert candidate.upper_projection_method in {"drop2", "drop3"}
        assert candidate.upper_projection_method != "drop2_and_4"
        assert candidate.metadata["upper_projection_metadata"]["spread_upper_4note_drop2_and_4_allowed"] is False
        assert tuple(candidate.metadata["upper_projection_metadata"]["spread_upper_4note_allowed_projection_methods"]) == (
            "drop2",
            "drop3",
        )
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert source_preserves_seventh_chord_identity("Ebmaj7", candidate.degrees)


def test_event_scoped_upper_4note_expansion_ratio_forces_three_of_five_slots_only() -> None:
    policy = _two_plus_four_policy(expanded=True)
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
    assert selected_policy.metadata["spread_upper_4note_expanded_color_only"] is True
    assert selected_policy.metadata["spread_upper_4note_prefer_expanded_color"] is True
    assert unselected_policy.harmonic_expansion_enabled is False
    assert unselected_policy.color_policy_mode == ColorPolicyMode.CHORD_SYMBOL_ONLY
    assert unselected_policy.metadata["spread_upper_4note_expanded_color_only"] is False
    assert unselected_policy.metadata["spread_upper_4note_prefer_expanded_color"] is False


def test_true_isolation_generates_valid_2plus4_spread_candidate_for_groupwise_selector() -> None:
    candidates = generate_candidates("Bb7", _two_plus_four_policy())
    spread_candidates = [candidate for candidate in candidates if candidate.recipe_id == "spread_2plus4_contract"]
    assert len(spread_candidates) >= 1
    for candidate in spread_candidates:
        assert candidate.disposition == Disposition.SPREAD
        assert candidate.functional_grouping == "2+4"
        assert candidate.density == 6
        assert len(candidate.notes) == 6
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert candidate.metadata["lower_group_recipe_id"] in {
            "lower_2note_root_3",
            "lower_2note_root_5",
            "lower_2note_root_7",
        }
        assert candidate.metadata["rooted_bass_anchor_passed"] is True
        assert min(candidate.notes) == candidate.metadata["root_bass_anchor_note"]
        assert all(40 <= note <= 83 for note in candidate.notes)
        assert candidate.metadata["upper_projection_method"] in {"drop2", "drop3"}
        assert candidate.metadata["upper_projection_method"] != "drop2_and_4"


def test_upper_4note_expanded_color_only_keeps_seventh_identity() -> None:
    policy = _two_plus_four_policy(expanded=True)
    scoped = _policy_with_event_texture_scope(
        policy,
        PatternEvent(
            event_id="a",
            track="piano",
            region_id="c0_b0_ch0",
            chord_symbol="Ebmaj7",
            onset_beat=0.0,
            role="harmonic",
        ),
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=scoped,
        contract_ids=("spread_2plus4_contract",),
        max_upper_options=12,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    assert {candidate.metadata["upper_source_family"] for candidate in legal} <= {
        ContentFamily.ROOTED_COLOR.value,
        ContentFamily.ROOTLESS_A.value,
        ContentFamily.ROOTLESS_B.value,
    }
    assert all(candidate.metadata["source_preserves_seventh_chord_identity"] is True for candidate in legal)
    assert all(source_preserves_seventh_chord_identity("Ebmaj7", candidate.degrees) for candidate in legal)


def test_2plus4_dual_demo_script_requests_unexpanded_and_expanded_60pct_outputs() -> None:
    script = _read("examples/scripts/generate_ballad_spread_2plus4_dual_listening_demos.py")
    assert "v2_2_73_misty_jazz_ballad_spread_2plus4_root_anchor_e2_e3_gap_p5_unexpanded_demo.mid" in script
    assert "v2_2_73_misty_jazz_ballad_spread_2plus4_root_anchor_e2_e3_gap_p5_expanded_60pct_demo.mid" in script
    assert '"required_recipe_id": _CONTRACT_ID' in script
    assert '"spread_upper_4note_expanded_color_target_ratio": 0.60' in script
    assert '"spread_lower_2note_foundation_mode": "rooted"' in script
    assert '"spread_rooted_bass_anchor_enabled": True' in script
    assert '"spread_root_bass_anchor_low": 40' in script
    assert '"spread_root_bass_anchor_high": 52' in script
    assert '"spread_whole_register_low": 40' in script
    assert '"spread_whole_register_high": 83' in script
    assert '"spread_groupwise_voice_leading_runtime_enabled": True' in script
    assert '"projection_methods_allowed": ["drop2", "drop3"]' in script
    assert '"drop2_and_4_allowed": False' in script
