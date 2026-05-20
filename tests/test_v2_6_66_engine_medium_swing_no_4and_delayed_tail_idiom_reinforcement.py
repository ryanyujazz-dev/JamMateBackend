
from __future__ import annotations

from jammate_engine.core.expression import ExpressionResolver
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.medium_swing.arrangement_policy import get_arrangement_policy
from jammate_engine.styles.medium_swing.expression_policy import get_expression_policy


def _event(event_id: str, onset: float, region_id: str, local_beat: float, hint: str, semantic_hint: str, duration: float = 4.0) -> PatternEvent:
    return PatternEvent(
        event_id=event_id,
        track="piano",
        region_id=region_id,
        chord_symbol="Cmaj7" if region_id == "r1" else "G7",
        onset_beat=onset,
        role="harmonic",
        expression_hint=hint,
        pattern_id="probe",
        local_beat=local_beat,
        metadata={
            "region_duration_beats": duration,
            "semantic_expression_hint": semantic_hint,
            "expression_hint_handoff_policy_version": "v2_6_63",
        },
    )


def test_v2_6_66_hold_until_next_touch_is_clamped_to_current_chord_region_when_next_touch_is_later_region() -> None:
    resolver = ExpressionResolver()
    events = [
        _event("a", 0.0, "r1", 0.0, "comp_medium", "soft_hold", duration=4.0),
        # No piano touch at the next ChordRegion boundary.  The next touch is
        # inside the later G7 region, so Cmaj7 must release at r1 end instead
        # of ringing through the harmony change.
        _event("b", 6.0, "r2", 2.0, "comp_short", "light_stab", duration=4.0),
    ]
    plan = resolver.resolve(events, get_expression_policy(), timing_policy={"feel": "straight"})
    held = plan.events["a"]
    assert held.duration_beats == 4.0
    assert held.metadata["duration_next_touch_hold_version"] == "v2_6_66"
    assert held.metadata["duration_next_touch_hold_reason"] == "next_same_track_touch_beyond_region_clamped_to_region_end"
    assert held.metadata["duration_region_remaining_beats"] == 4.0


def test_v2_6_66_hold_until_next_touch_still_releases_at_next_touch_inside_same_region() -> None:
    resolver = ExpressionResolver()
    events = [
        _event("a", 0.0, "r1", 0.0, "comp_medium", "soft_hold", duration=4.0),
        _event("b", 2.0, "r1", 2.0, "comp_short", "light_stab", duration=4.0),
    ]
    plan = resolver.resolve(events, get_expression_policy(), timing_policy={"feel": "straight"})
    held = plan.events["a"]
    assert held.duration_beats == 2.0
    assert held.metadata["duration_next_touch_hold_version"] == "v2_6_66"
    assert held.metadata["duration_next_touch_hold_reason"] == "held_until_next_same_track_touch_within_region"


def test_v2_6_66_no_4and_delayed_tail_policy_is_declared_without_bar_first_routing() -> None:
    policy = get_arrangement_policy()
    assert policy["piano_comping_no_4and_delayed_tail_idiom_policy"] is True
    assert policy["piano_comping_no_4and_delayed_tail_idiom_policy_version"] == "v2_6_66"
    assert "ChordRegion-first" in policy["piano_comping_no_4and_delayed_tail_idiom_contract"]


def test_v2_6_66_region_library_contains_no_4and_delayed_tail_metadata_and_keeps_tail_push_rare() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    no_4and_candidates = [
        c for c in candidates
        if c.metadata.get("no_4and_delayed_tail_idiom") is True
    ]
    tail_push_candidates = [
        c for c in candidates
        if c.metadata.get("tail_push_risk") == "high"
    ]
    assert no_4and_candidates
    assert tail_push_candidates
    assert sum(float(c.weight) for c in no_4and_candidates) > sum(float(c.weight) for c in tail_push_candidates) * 20
    for candidate in candidates:
        assert candidate.metadata["time_reference"] == "region_local_beats"
        assert candidate.metadata.get("region_first_short_region_route", True) is True
