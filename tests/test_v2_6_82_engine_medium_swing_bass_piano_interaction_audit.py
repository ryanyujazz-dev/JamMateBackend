from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import Disposition
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_medium_swing_bass_piano_interaction_audit.py"
    spec = importlib.util.spec_from_file_location("generate_medium_swing_bass_piano_interaction_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _event(*, chorus: int = 2, total: int = 3, last_section: bool = True, last_chorus: bool = False) -> PatternEvent:
    return PatternEvent(
        event_id="e_c2_section_tail",
        track="piano",
        region_id="c2_b15_ch0",
        chord_symbol="Gmaj7",
        onset_beat=0.0,
        role="harmonic",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_hint="comp_medium",
        pattern_id="test_pattern",
        local_beat=0.0,
        metadata={
            "region_chorus_index": chorus,
            "region_total_choruses": total,
            "region_is_last_bar_of_section": last_section,
            "region_is_last_bar_of_chorus": last_chorus,
            "region_section_label": "A",
            "region_phrase": "A",
            "region_performance_bar_index": 87,
        },
    )


def _enabled_policy():
    base = voicing_policy.get_voicing_policy()
    nested = dict(base.metadata["medium_swing_existing_voicing_capability_usage_policy"])
    nested["enabled"] = True
    nested["activation"] = "explicit_bass_piano_interaction_guard_test_intent"
    return replace(
        base,
        metadata={
            **dict(base.metadata),
            "medium_swing_existing_voicing_capability_usage_policy": nested,
        },
    )


def test_v2_6_82_declares_bass_piano_interaction_audit_without_reopening_core_voicing() -> None:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]

    assert arrangement["medium_swing_full_band_post_density_relief_checkpoint_version"] == "v2_6_81"
    assert arrangement["medium_swing_bass_piano_interaction_audit"] is True
    assert arrangement["medium_swing_bass_piano_interaction_audit_version"] == "v2_6_82"
    assert "piano/bass low-register overlap" in arrangement["medium_swing_bass_piano_interaction_audit_contract"]
    assert "does not modify core voicing internals" in arrangement["medium_swing_bass_piano_interaction_audit_contract"]
    assert arrangement["medium_swing_bass_piano_interaction_audit_milestone"] == "v2_6_82_medium_swing_bass_piano_interaction_audit"

    assert nested["bass_piano_interaction_guard_version"] == "v2_6_82"
    assert nested["bass_piano_interaction_guard_enabled"] is True
    assert nested["bass_piano_interaction_register_floor"] == 48
    assert nested["bass_piano_interaction_spread_root_bass_anchor_low"] == 48
    assert nested["bass_piano_interaction_spread_root_bass_anchor_target"] == 54
    assert nested["no_core_voicing_change"] is True
    assert policy.preferred_density == 4
    assert policy.preferred_disposition.value == "open"


def test_v2_6_82_event_scoped_guard_requests_existing_spread_candidates_above_c3() -> None:
    scoped = policy_with_event_voicing_context(_enabled_policy(), _event())

    assert scoped.preferred_disposition == Disposition.SPREAD
    assert scoped.preferred_density == 5
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is True
    assert scoped.metadata["medium_swing_bass_piano_interaction_guard_version"] == "v2_6_82"
    assert scoped.metadata["medium_swing_bass_piano_interaction_guard_enabled"] is True
    assert scoped.metadata["spread_root_bass_anchor_low"] == 48
    assert scoped.metadata["spread_root_bass_anchor_high"] == 60
    assert scoped.metadata["spread_root_bass_anchor_target"] == 54
    assert scoped.metadata["spread_whole_register_low"] == 48
    assert scoped.metadata["spread_lower_2note_low"] == 48
    assert scoped.metadata["spread_lower_2note_target_low"] == 48
    assert scoped.metadata["medium_swing_existing_voicing_capability_no_core_voicing_change"] is True

    candidates = generate_candidates("Gmaj7", scoped)
    assert candidates
    assert {candidate.recipe_id for candidate in candidates} == {"spread_2plus3_contract"}
    assert {candidate.density for candidate in candidates} == {5}
    assert all(min(candidate.notes) >= 48 for candidate in candidates)
    assert all(43 not in tuple(candidate.notes) for candidate in candidates)


def test_v2_6_82_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == "v2_6_82"
    assert static["bass_piano_interaction_audit_enabled"] is True
    assert static["bass_piano_interaction_audit_version"] == "v2_6_82"
    assert static["previous_full_band_checkpoint_version"] == "v2_6_81"
    assert static["two_beat_density_relief_policy_version"] == "v2_6_80"
    assert static["existing_voicing_capability_policy_version"] == "v2_6_77"
    assert static["low_register_clarity_guard_version"] == "v2_6_78"
    assert static["bass_piano_interaction_guard_version"] == "v2_6_82"
    assert static["bass_piano_interaction_guard_enabled"] is True
    assert static["existing_voicing_capability_default_enabled"] is False
    assert static["existing_voicing_capability_ordinary_runtime_default"] is False
    assert static["base_preferred_density"] == 4
    assert static["base_preferred_disposition"] == "open"

    outputs = [
        {
            "slug": "all_the_things_you_are",
            "track_presence_ok": True,
            "piano_active_pattern_events": 192,
            "piano_two_beat_active_events": 24,
            "two_beat_start_anchor_events": 21,
            "two_beat_multi_touch_events": 0,
            "two_beat_anchor_ratio": 0.875,
            "active_anticipation_count": 5,
            "two_beat_previous_tail_anticipation_count": 1,
            "piano_voicing_events": 192,
            "grouped_spread_events": 5,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "five_six_low_below_c3_events": 0,
            "five_six_low_below_c3_interaction_events": 0,
            "five_six_exact_low_unison_events": 0,
            "bass_piano_joined_events": 192,
            "bass_piano_exact_low_unison_events": 1,
            "bass_piano_close_low_spacing_events": 3,
            "bass_piano_foundation_gap_too_tight_events": 4,
            "bar_88_bass_piano_exact_low_unison_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "max_top_note": 73,
            "min_piano_low_note": 48,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "bass_root_echo_bad_same": 0,
            "bass_root_echo_bad_timing": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
        },
        {
            "slug": "autumn_leaves",
            "track_presence_ok": True,
            "piano_active_pattern_events": 190,
            "piano_two_beat_active_events": 134,
            "two_beat_start_anchor_events": 121,
            "two_beat_multi_touch_events": 4,
            "two_beat_anchor_ratio": 0.903,
            "active_anticipation_count": 14,
            "two_beat_previous_tail_anticipation_count": 13,
            "piano_voicing_events": 190,
            "grouped_spread_events": 5,
            "five_note_events": 5,
            "six_note_events": 0,
            "ordinary_body_5_6_events": 0,
            "five_six_low_below_c3_events": 0,
            "five_six_low_below_c3_interaction_events": 0,
            "five_six_exact_low_unison_events": 0,
            "bass_piano_joined_events": 190,
            "bass_piano_exact_low_unison_events": 0,
            "bass_piano_close_low_spacing_events": 0,
            "bass_piano_foundation_gap_too_tight_events": 3,
            "bar_88_bass_piano_exact_low_unison_events": 0,
            "low_register_dense_events": 0,
            "voice_leading_warning_events": 0,
            "max_top_note": 73,
            "min_piano_low_note": 48,
            "bass_span_violations": 0,
            "bass_target_continuity_mismatches": 0,
            "bass_repeated_root_violations": 0,
            "bass_root_echo_bad_same": 0,
            "bass_root_echo_bad_timing": 0,
            "pedal_cc64_event_count": 0,
            "pedal_warning_count": 0,
        },
    ]
    aggregate = module._aggregate(outputs)
    acceptance = module._acceptance(static, outputs, aggregate)

    assert aggregate["five_six_low_below_c3_events"] == 0
    assert aggregate["five_six_exact_low_unison_events"] == 0
    assert aggregate["bar_88_bass_piano_exact_low_unison_events"] == 0
    assert acceptance["passed"] is True
