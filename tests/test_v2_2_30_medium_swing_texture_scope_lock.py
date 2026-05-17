from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import derive_voicing_texture_intent, derive_voicing_texture_state, generate_candidates
from jammate_engine.realization.harmonic_realizer import _policy_with_event_texture_scope
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy


def _event(section_id: str, chorus_index: int = 0) -> PatternEvent:
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
            "region_phrase": "A" if section_id.startswith("A") else "B",
            "region_section_role": "bridge" if section_id == "B" else "normal",
            "region_chorus_index": chorus_index,
            "region_total_choruses": 3,
            "region_performance_bar_index": 8,
            "region_is_first_bar_of_section": True,
            "region_is_last_bar_of_section": False,
        },
    )


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_medium_swing_policy_declares_section_scoped_texture_runtime() -> None:
    policy = get_medium_swing_voicing_policy()
    assert policy.metadata["voicing_texture_state_runtime_filtering_enabled"] is True
    assert policy.metadata["voicing_texture_scope_runtime_enabled"] is True
    assert policy.metadata["voicing_texture_runtime_scope_type"] == "section"
    assert "v2_2_38" in policy.metadata["texture_scope_runtime_contract"]


def test_event_scoped_policy_derives_section_voicing_texture_state() -> None:
    policy = get_medium_swing_voicing_policy()
    scoped = _policy_with_event_texture_scope(policy, _event("A1", chorus_index=1))
    intent = derive_voicing_texture_intent(scoped)
    state = derive_voicing_texture_state(scoped, intent=intent)

    assert state.scope_type.value == "section"
    assert state.scope_id == "chorus:1|section:A1"
    assert state.primary_family.value == "open"
    assert state.allowed_families[0].value == "open"
    assert scoped.metadata["voicing_texture_scope_runtime_contract"].startswith("v2_2_38")
    assert scoped.metadata["voicing_texture_scope_region_context"]["section_id"] == "A1"


def test_different_sections_get_different_texture_state_scope_ids_without_changing_family() -> None:
    policy = get_medium_swing_voicing_policy()
    a_state = derive_voicing_texture_state(_policy_with_event_texture_scope(policy, _event("A1", chorus_index=0)))
    b_state = derive_voicing_texture_state(_policy_with_event_texture_scope(policy, _event("B", chorus_index=0)))

    assert a_state.scope_id == "chorus:0|section:A1"
    assert b_state.scope_id == "chorus:0|section:B"
    assert a_state.allowed_families == b_state.allowed_families


def test_section_scoped_policy_still_filters_candidates_to_open_family() -> None:
    policy = get_medium_swing_voicing_policy()
    scoped = _policy_with_event_texture_scope(policy, _event("A1"))
    candidates = generate_candidates("G7", scoped)

    assert candidates
    first = candidates[0]
    texture_state = first.metadata["voicing_texture_state"]
    runtime_filter = first.metadata["voicing_texture_state_runtime_filter"]
    assert texture_state["scope_type"] == "section"
    assert texture_state["scope_id"] == "chorus:0|section:A1"
    assert runtime_filter["effective_dispositions"] == ["open"]
    assert {candidate.metadata.get("disposition_projection_family") for candidate in candidates} == {"open"}
