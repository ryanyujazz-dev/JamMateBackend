from __future__ import annotations

from jammate_engine.core.expression import ExpressionResolver
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.medium_swing.expression_policy import get_expression_policy


ALLOWED_SEMANTIC_HINTS = {
    "soft_hold",
    "light_stab",
    "accent_stab",
    "accent_hold",
    "backbeat_hold",
    "final_hold",
}


def _event(event_id: str, onset: float, hint: str, semantic_hint: str) -> PatternEvent:
    return PatternEvent(
        event_id=event_id,
        track="piano",
        region_id="r1",
        chord_symbol="Cmaj7",
        onset_beat=onset,
        role="harmonic",
        expression_hint=hint,
        pattern_id="probe",
        local_beat=onset,
        metadata={
            "region_duration_beats": 4.0,
            "semantic_expression_hint": semantic_hint,
            "expression_hint_handoff_policy_version": "v2_6_63",
        },
    )


def test_v2_6_63_medium_swing_expression_policy_declares_accent_hold_and_next_touch_hold_semantics() -> None:
    policy = get_expression_policy()
    assert policy.metadata["piano_expression_hint_handoff_version"] == "v2_6_63"
    assert policy.metadata["hold_duration_semantics"] == "hold_until_next_touch"

    for profile_name in {"comp_medium", "comp_backbeat_hold", "comp_accent_hold", "comp_final_hold"}:
        profile = policy.profiles[profile_name]
        assert profile.metadata["duration_semantics"] == "hold_until_next_touch"
        assert profile.metadata["duration_semantics_version"] == "v2_6_63"

    assert comping_patterns.EXPRESSION_PROFILE_BY_SEMANTIC_HINT["accent_hold"] == "comp_accent_hold"
    assert comping_patterns.EXPRESSION_PROFILE_BY_SEMANTIC_HINT["backbeat_hold"] == "comp_backbeat_hold"
    assert comping_patterns.EXPRESSION_PROFILE_BY_SEMANTIC_HINT["final_hold"] == "comp_final_hold"


def test_v2_6_63_pattern_library_carries_semantic_hints_only_and_includes_accent_hold() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 4.0})
    semantic_hints = set()
    for candidate in candidates:
        assert candidate.metadata["expression_hint_handoff_policy_version"] == "v2_6_63"
        for spec in candidate.events:
            hint = spec.metadata.get("semantic_expression_hint")
            semantic_hints.add(hint)
            assert hint in ALLOWED_SEMANTIC_HINTS
            assert "velocity" not in spec.metadata
            assert "duration" not in spec.metadata
            assert "duration_beats" not in spec.metadata
            assert "pedal" not in spec.metadata

    assert "accent_hold" in semantic_hints


def test_v2_6_63_hold_expression_last_until_next_same_track_touch() -> None:
    resolver = ExpressionResolver()
    policy = get_expression_policy()
    events = [
        _event("a", 0.0, "comp_medium", "soft_hold"),
        _event("b", 2.0, "comp_short", "light_stab"),
    ]
    plan = resolver.resolve(events, policy, timing_policy={"feel": "straight"})
    held = plan.events["a"]
    short = plan.events["b"]

    assert held.duration_beats == 2.0
    assert held.metadata["duration_next_touch_hold_version"] in {"v2_6_63", "v2_6_66"}
    assert held.metadata["duration_next_touch_hold_applied"] is True
    assert held.metadata["duration_next_touch_hold_reason"] in {"held_until_next_same_track_touch", "held_until_next_same_track_touch_within_region"}
    assert short.duration_beats == policy.profiles["comp_short"].duration_beats


def test_v2_6_63_accent_hold_is_accented_but_not_a_short_stab() -> None:
    resolver = ExpressionResolver()
    events = [
        _event("a", 0.0, "comp_accent_hold", "accent_hold"),
        _event("b", 1.5, "comp_short", "light_stab"),
    ]
    plan = resolver.resolve(events, get_expression_policy(), timing_policy={"feel": "straight"})
    accent_hold = plan.events["a"]

    assert accent_hold.duration_beats == 1.5
    assert accent_hold.articulation == "accent"
    assert accent_hold.touch == "accented"
    assert accent_hold.accent > 0
    assert accent_hold.metadata["duration_next_touch_hold_profile_semantics"] == "hold_until_next_touch"
