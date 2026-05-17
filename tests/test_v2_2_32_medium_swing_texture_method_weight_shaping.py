from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import derive_voicing_texture_state, generate_candidates
from jammate_engine.realization.harmonic_realizer import _policy_with_event_texture_scope
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy


def _event(section_id: str, *, role: str = "normal", phrase: str | None = None, chorus_index: int = 0, total: int = 3) -> PatternEvent:
    return PatternEvent(
        event_id=f"c{chorus_index}_{section_id}_event",
        track="piano",
        region_id=f"c{chorus_index}_{section_id}_r0",
        chord_symbol="G7",
        onset_beat=0.0,
        role="comp",
        local_beat=0.0,
        metadata={
            "region_section_id": section_id,
            "region_section_label": section_id,
            "region_phrase": phrase or ("B" if section_id == "B" else "A"),
            "region_section_role": role,
            "region_chorus_index": chorus_index,
            "region_total_choruses": total,
            "region_performance_bar_index": 8,
            "region_is_first_bar_of_section": True,
            "region_is_last_bar_of_section": False,
        },
    )


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_medium_swing_declares_bridge_chorus_texture_contrast_contract() -> None:
    policy = get_medium_swing_voicing_policy()
    assert policy.metadata["voicing_texture_contrast_planning_enabled"] is True
    assert "v2_2_38" in policy.metadata["voicing_texture_contrast_planning_contract"]
    assert policy.metadata["allowed_texture_families"] == ["open"]


def test_bridge_section_exposes_wider_open_texture_intent_with_small_method_weight_shaping() -> None:
    base = get_medium_swing_voicing_policy()
    a_policy = _policy_with_event_texture_scope(base, _event("A1", role="normal", chorus_index=0))
    bridge_policy = _policy_with_event_texture_scope(base, _event("B", role="bridge", phrase="B", chorus_index=0))

    a_state = derive_voicing_texture_state(a_policy)
    bridge_state = derive_voicing_texture_state(bridge_policy)

    assert a_state.contrast_role == "baseline_open_swing"
    assert bridge_state.contrast_role == "bridge_open_contrast"
    assert bridge_state.width > a_state.width
    assert bridge_state.primary_family.value == "open"
    assert bridge_state.allowed_families == a_state.allowed_families
    assert bridge_policy.metadata["voicing_texture_contrast_plan"]["behavior_scope"] == "runtime_open_method_weight_shaping_without_family_switch"
    assert bridge_policy.metadata["disposition_method_weights"]["open"]["drop3"] > a_policy.metadata["disposition_method_weights"]["open"]["drop3"]
    assert bridge_state.open_method_weights["drop3"] > a_state.open_method_weights["drop3"]


def test_final_chorus_exposes_open_lift_texture_intent_with_small_method_weight_shaping() -> None:
    base = get_medium_swing_voicing_policy()
    mid_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=1, total=3))
    final_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=2, total=3))

    mid_state = derive_voicing_texture_state(mid_policy)
    final_state = derive_voicing_texture_state(final_policy)

    assert mid_state.contrast_role == "baseline_open_swing"
    assert final_state.contrast_role == "final_chorus_open_lift"
    assert final_state.energy > mid_state.energy
    assert final_state.density > mid_state.density
    assert final_state.primary_family.value == "open"
    assert final_state.open_method_weights != mid_state.open_method_weights
    assert final_state.open_method_weights["drop3"] > mid_state.open_method_weights["drop3"]
    assert (final_state.open_method_weights["drop2"] + final_state.open_method_weights["drop3"]) > (mid_state.open_method_weights["drop2"] + mid_state.open_method_weights["drop3"])
    assert final_policy.metadata["voicing_texture_method_weight_shaping"]["contract"] == "v2_2_38_medium_swing_generic_open_fallback_only"


def test_bridge_texture_contrast_still_filters_runtime_candidates_to_open_family() -> None:
    base = get_medium_swing_voicing_policy()
    bridge_policy = _policy_with_event_texture_scope(base, _event("B", role="bridge", phrase="B"))
    candidates = generate_candidates("G7", bridge_policy)

    assert candidates
    first = candidates[0]
    texture_state = first.metadata["voicing_texture_state"]
    runtime_filter = first.metadata["voicing_texture_state_runtime_filter"]
    assert texture_state["contrast_role"] == "bridge_open_contrast"
    assert texture_state["width"] == 0.72
    assert runtime_filter["effective_dispositions"] == ["open"]
    assert first.metadata["voicing_texture_method_weight_shaping_enabled"] is True
    assert first.metadata["voicing_texture_method_weight_shaping"]["open_method_weights"]["drop3"] == 0.53
    assert first.metadata["voicing_texture_state"]["open_method_weights"]["drop3"] == 0.53
    assert {candidate.metadata.get("disposition_projection_family") for candidate in candidates} == {"open"}
