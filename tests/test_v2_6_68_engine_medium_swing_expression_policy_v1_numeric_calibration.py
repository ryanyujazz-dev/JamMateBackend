from __future__ import annotations

from jammate_engine.core.expression import ExpressionResolver
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.styles.medium_swing import comping_patterns
from jammate_engine.styles.medium_swing.arrangement_policy import get_arrangement_policy
from jammate_engine.styles.medium_swing.expression_policy import get_expression_policy

MILESTONE = "v2_6_68"
FORBIDDEN_PATTERN_EXPRESSION_KEYS = {"velocity", "duration", "duration_beats", "pedal", "release_beats", "accent"}


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


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return float(bounds[0]) - 1e-9 <= float(value) <= float(bounds[1]) + 1e-9


def test_v2_6_68_arrangement_and_expression_policy_declare_v1_numeric_calibration_contract() -> None:
    arrangement = get_arrangement_policy()
    expression = get_expression_policy()

    assert arrangement["piano_expression_policy_v1_numeric_calibration"] is True
    assert arrangement["piano_expression_policy_v1_numeric_calibration_version"] == MILESTONE
    assert "pattern files remain semantic-only" in arrangement["piano_expression_policy_v1_numeric_calibration_contract"]

    assert expression.metadata["medium_swing_expression_policy_v1_numeric_calibration"] is True
    assert expression.metadata["medium_swing_expression_policy_v1_numeric_calibration_version"] == MILESTONE
    assert expression.metadata["medium_swing_expression_policy_v1_reference_ticks_per_beat"] == 120
    assert "patterns keep semantic_expression_hint" in expression.metadata["medium_swing_expression_policy_v1_numeric_calibration_contract"]


def test_v2_6_68_comping_profiles_are_inside_v1_reference_velocity_and_duration_ranges() -> None:
    policy = get_expression_policy()
    expected = {
        "comp_medium": "soft_hold",
        "comp_short": "light_stab",
        "comp_accent": "accent_stab",
        "comp_backbeat_hold": "backbeat_hold",
        "comp_final_hold": "final_hold",
    }
    for profile_name, semantic_hint in expected.items():
        profile = policy.profiles[profile_name]
        metadata = profile.metadata
        assert metadata["medium_swing_expression_policy_v1_numeric_calibration_version"] == MILESTONE
        assert metadata["v1_reference_semantic_hint"] == semantic_hint
        assert _in_range(profile.velocity, metadata["v1_reference_velocity_range"])
        assert _in_range(profile.duration_beats, metadata["v1_reference_duration_beats_range"])
        assert "velocity" not in metadata.get("calibration_contract", "") or "pattern" in metadata.get("calibration_contract", "")

    accent_hold = policy.profiles["comp_accent_hold"]
    assert accent_hold.metadata["v1_reference_semantic_hint"] == "accent_hold_from_accent_stab_plus_hold_semantics"
    assert _in_range(accent_hold.velocity, accent_hold.metadata["v1_reference_velocity_range"])
    assert _in_range(accent_hold.duration_beats, accent_hold.metadata["v1_reference_duration_beats_range"])
    assert accent_hold.articulation.value == "accent"
    assert accent_hold.accent > 0


def test_v2_6_68_patterns_still_carry_semantic_hints_only_not_v1_numeric_values() -> None:
    candidates = []
    for duration in (1.0, 2.0, 4.0):
        candidates.extend(comping_patterns.get_pattern_candidates({"region_duration_beats": duration}))
    assert candidates
    for candidate in candidates:
        assert candidate.metadata["expression_boundary"] == "pattern_carries_semantic_hint_not_final_values"
        for spec in candidate.events:
            metadata = dict(spec.metadata)
            assert metadata.get("semantic_expression_hint") in comping_patterns.EXPRESSION_PROFILE_BY_SEMANTIC_HINT
            assert not (FORBIDDEN_PATTERN_EXPRESSION_KEYS & set(metadata))


def test_v2_6_68_expression_resolver_keeps_hold_boundary_guard_after_numeric_calibration() -> None:
    resolver = ExpressionResolver()
    events = [
        _event("a", 0.0, "r1", 0.0, "comp_medium", "soft_hold", duration=4.0),
        _event("b", 6.0, "r2", 2.0, "comp_short", "light_stab", duration=4.0),
    ]
    plan = resolver.resolve(events, get_expression_policy(), timing_policy={"feel": "straight"})
    held = plan.events["a"]
    short = plan.events["b"]

    # The profile fallback is V1-calibrated, but hold semantics still obey the
    # v2_6_66 ChordRegion boundary guard and do not ring into the later G7.
    assert held.profile_name == "comp_medium"
    assert held.velocity == 54
    assert held.duration_beats == 4.0
    assert held.metadata["duration_next_touch_hold_version"] == "v2_6_66"
    assert held.metadata["duration_next_touch_hold_reason"] == "next_same_track_touch_beyond_region_clamped_to_region_end"
    assert held.metadata["medium_swing_expression_policy_v1_numeric_calibration_version"] == MILESTONE

    assert short.profile_name == "comp_short"
    assert short.velocity == 56
    assert short.duration_beats == get_expression_policy().profiles["comp_short"].duration_beats
    assert short.metadata["v1_reference_semantic_hint"] == "light_stab"
