from __future__ import annotations

from dataclasses import replace

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import Disposition
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.styles.medium_swing import arrangement_policy, voicing_policy


def _event(*, chorus: int = 2, total: int = 3, last_section: bool = False, last_chorus: bool = False) -> PatternEvent:
    return PatternEvent(
        event_id=f"e_c{chorus}_{'last' if last_chorus else 'section' if last_section else 'body'}",
        track="piano",
        region_id=f"c{chorus}_b7_ch0",
        chord_symbol="Cmaj7",
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
            "region_performance_bar_index": 79,
        },
    )


def _enabled_policy():
    base = voicing_policy.get_voicing_policy()
    nested = dict(base.metadata["medium_swing_existing_voicing_capability_usage_policy"])
    nested["enabled"] = True
    nested["activation"] = "explicit_test_intent"
    return replace(
        base,
        metadata={
            **dict(base.metadata),
            "medium_swing_existing_voicing_capability_usage_policy": nested,
        },
    )


def test_v2_6_77_policy_declares_existing_voicing_capability_usage_boundary() -> None:
    arrangement = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    nested = policy.metadata["medium_swing_existing_voicing_capability_usage_policy"]

    assert arrangement["medium_swing_existing_voicing_capability_usage_policy"] is True
    assert arrangement["medium_swing_existing_voicing_capability_usage_policy_version"] == "v2_6_77"
    assert "does not modify core voicing internals" in arrangement["medium_swing_existing_voicing_capability_usage_policy_contract"]
    assert nested["version"] == "v2_6_77"
    assert nested["available"] is True
    assert nested["enabled"] is False
    assert nested["activation"] == "explicit_intent_or_voicing_override_only"
    assert nested["ordinary_runtime_default"] is False
    assert nested["ordinary_body"] == "keep_open_drop_4note"
    assert nested["no_core_voicing_change"] is True
    assert "spread_2plus3_contract" in nested["requested_existing_contracts"]
    assert "spread_3plus3_contract" in nested["requested_existing_contracts"]


def test_v2_6_77_ordinary_body_keeps_open_drop_density_4_policy_by_default() -> None:
    base = voicing_policy.get_voicing_policy()
    scoped = policy_with_event_voicing_context(base, _event(chorus=1, total=3, last_section=False, last_chorus=False))

    assert scoped.preferred_disposition == Disposition.OPEN
    assert scoped.preferred_density == 4
    assert scoped.max_density == 5
    assert "medium_swing_existing_voicing_capability_usage_policy_applied" not in scoped.metadata


def test_v2_6_77_explicit_policy_keeps_ordinary_body_open_drop_density_4() -> None:
    base = _enabled_policy()
    scoped = policy_with_event_voicing_context(base, _event(chorus=1, total=3, last_section=False, last_chorus=False))

    assert scoped.preferred_disposition == Disposition.OPEN
    assert scoped.preferred_density == 4
    assert scoped.max_density == 5
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_version"] == "v2_6_77"
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is False
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_scene"] == "ordinary_open_drop"
    assert scoped.metadata["medium_swing_existing_voicing_capability_no_core_voicing_change"] is True


def test_v2_6_77_final_chorus_section_tail_requests_existing_5note_spread_contract_when_explicitly_enabled() -> None:
    base = _enabled_policy()
    scoped = policy_with_event_voicing_context(base, _event(chorus=2, total=3, last_section=True, last_chorus=False))

    assert scoped.preferred_disposition == Disposition.SPREAD
    assert scoped.preferred_density == 5
    assert scoped.max_density >= 6
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is True
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_scene"] == "final_chorus_section_tail_support"
    assert scoped.metadata["medium_swing_existing_voicing_capability_selected_contract_id"] == "spread_2plus3_contract"
    assert scoped.metadata["spread_grouping_mix_candidate_pool"]["compatible_contract_ids"] == ["spread_2plus3_contract"]

    candidates = generate_candidates("Cmaj7", scoped)
    assert candidates
    assert {candidate.recipe_id for candidate in candidates} == {"spread_2plus3_contract"}
    assert {candidate.density for candidate in candidates} == {5}


def test_v2_6_77_final_ending_requests_existing_6note_spread_contracts_when_explicitly_enabled() -> None:
    base = _enabled_policy()
    scoped = policy_with_event_voicing_context(base, _event(chorus=2, total=3, last_section=True, last_chorus=True))

    assert scoped.preferred_disposition == Disposition.SPREAD
    assert scoped.preferred_density == 6
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_policy_applied"] is True
    assert scoped.metadata["medium_swing_existing_voicing_capability_usage_scene"] == "final_ending_climax"
    assert scoped.metadata["medium_swing_existing_voicing_capability_selected_contract_id"] == "spread_3plus3_contract"
    assert scoped.metadata["spread_grouping_mix_candidate_pool"]["compatible_contract_ids"] == ["spread_2plus4_contract", "spread_3plus3_contract"]

    candidates = generate_candidates("Cmaj7", scoped)
    assert candidates
    assert {candidate.recipe_id for candidate in candidates} <= {"spread_2plus4_contract", "spread_3plus3_contract"}
    assert max(candidate.density for candidate in candidates) == 6
