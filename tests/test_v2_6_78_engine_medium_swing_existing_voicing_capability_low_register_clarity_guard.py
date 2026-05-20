from __future__ import annotations

from dataclasses import replace

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import Disposition
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy


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
    nested["activation"] = "explicit_low_register_clarity_test_intent"
    return replace(
        base,
        metadata={
            **dict(base.metadata),
            "medium_swing_existing_voicing_capability_usage_policy": nested,
        },
    )


def test_v2_6_78_low_register_clarity_guard_is_declared_without_changing_core_voicing_boundary() -> None:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]

    assert arrangement["medium_swing_existing_voicing_capability_usage_policy_version"] == "v2_6_77"
    assert arrangement["medium_swing_existing_voicing_capability_low_register_clarity_guard_version"] == "v2_6_78"
    assert arrangement["medium_swing_existing_voicing_capability_low_register_clarity_guard"] is True
    assert nested["low_register_clarity_guard_version"] == "v2_6_78"
    assert nested["low_register_clarity_guard_enabled"] is True
    assert nested["low_register_clarity_threshold"] == 48
    assert nested["low_register_clarity_max_notes_below"] == 1
    assert nested["no_core_voicing_change"] is True


def test_v2_6_78_section_tail_uses_existing_spread_low_register_density_guard() -> None:
    scoped = policy_with_event_voicing_context(_enabled_policy(), _event())

    assert scoped.preferred_disposition == Disposition.SPREAD
    assert scoped.preferred_density == 5
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is True
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_scene"] == "final_chorus_section_tail_support"
    assert scoped.metadata["medium_swing_existing_voicing_capability_low_register_clarity_guard_version"] == "v2_6_78"
    assert scoped.metadata["spread_low_register_density_guard_enabled"] is True
    assert scoped.metadata["spread_low_register_density_threshold"] == 48
    assert scoped.metadata["spread_low_register_density_max_notes_below"] == 1

    candidates = generate_candidates("Gmaj7", scoped)
    assert candidates
    assert {candidate.recipe_id for candidate in candidates} == {"spread_2plus3_contract"}
    assert {candidate.density for candidate in candidates} == {5}
    assert all(sum(1 for note in candidate.notes if int(note) < 48) <= 1 for candidate in candidates)
    assert all([43, 47, 54, 59, 64] != list(candidate.notes) for candidate in candidates)


def test_v2_6_78_ordinary_body_remains_open_drop_four_note_even_when_capability_is_enabled() -> None:
    scoped = policy_with_event_voicing_context(_enabled_policy(), _event(chorus=1, total=3, last_section=False, last_chorus=False))

    assert scoped.preferred_disposition == Disposition.OPEN
    assert scoped.preferred_density == 4
    assert scoped.max_density == 5
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_version"] == "v2_6_77"
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is False
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_scene"] == "ordinary_open_drop"
