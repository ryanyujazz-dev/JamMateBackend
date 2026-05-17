from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import derive_voicing_texture_state
from jammate_engine.realization.harmonic_realizer import _policy_with_event_texture_scope
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy


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
        },
    )


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_bridge_open_method_retune_prefers_drop3_without_family_switch() -> None:
    base = get_voicing_policy()
    bridge_policy = _policy_with_event_texture_scope(base, _event("B", role="bridge", phrase="B"))
    state = derive_voicing_texture_state(bridge_policy)

    assert state.primary_family.value == "open"
    assert tuple(state.allowed_families) == (state.primary_family,)
    assert state.contrast_role == "bridge_open_contrast"
    assert state.open_method_weights == {
        "generic_open": 0.0,
        "drop2": 0.35,
        "drop3": 0.53,
        "drop2_and_4": 0.12,
    }
    assert state.open_method_weights["drop3"] > state.open_method_weights["drop2"]


def test_final_chorus_open_lift_retune_raises_drop3_and_keeps_drop24_controlled() -> None:
    base = get_voicing_policy()
    mid_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=1, total=3))
    final_policy = _policy_with_event_texture_scope(base, _event("A1", chorus_index=2, total=3))

    mid_state = derive_voicing_texture_state(mid_policy)
    final_state = derive_voicing_texture_state(final_policy)

    assert mid_state.contrast_role == "baseline_open_swing"
    assert final_state.contrast_role == "final_chorus_open_lift"
    assert final_state.primary_family.value == "open"
    assert final_state.open_method_weights == {
        "generic_open": 0.0,
        "drop2": 0.43,
        "drop3": 0.48,
        "drop2_and_4": 0.09,
    }
    assert final_state.open_method_weights["drop3"] > mid_state.open_method_weights["drop3"]
    assert final_state.open_method_weights["drop2_and_4"] < mid_state.open_method_weights["drop2_and_4"]
    assert mid_state.open_method_weights["generic_open"] == 0.0
