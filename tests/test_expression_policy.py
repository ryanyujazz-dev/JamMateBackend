from __future__ import annotations

from jammate_engine.core.expression import ExpressionPolicyBundle, ExpressionResolver, ExpressionProfile
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, event_spec
from jammate_engine.styles.bossa_nova import expression_policy as bossa_expression_policy
from jammate_engine.styles.jazz_ballad import expression_policy as ballad_expression_policy
from jammate_engine.styles.registry import get_style


def _region() -> HarmonicRegion:
    return HarmonicRegion(
        region_id="r_expr",
        chord_symbol="Cmaj7",
        next_chord_symbol="Fmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=0.0,
        duration_beats=4.0,
    )


def test_style_profiles_use_expression_policy_bundle_not_inline_dict() -> None:
    style = get_style("bossa_nova")
    assert isinstance(style.expression_policy, ExpressionPolicyBundle)
    assert "core_short" in style.expression_policy.profiles
    assert "core_sustain" in style.expression_policy.profiles


def test_bossa_short_short_sustain_is_resolved_by_core_expression() -> None:
    style = get_style("bossa_nova")
    plan = style.plan_region(_region(), context={})
    piano_events = [event for event in plan.events if event.track == "piano"]
    expr = ExpressionResolver().resolve(piano_events, style.expression_policy)
    values = [expr.events[event.event_id] for event in piano_events]

    assert [value.profile_name for value in values] == ["core_short", "core_short", "core_sustain"]
    assert [value.duration_beats for value in values] == [0.45, 0.45, 1.3]
    assert [value.articulation for value in values] == ["short", "short", "sustain"]
    assert values[-1].touch == "light"


def test_ballad_soft_sustain_policy_is_style_owned_and_core_resolved() -> None:
    policy = ballad_expression_policy.get_expression_policy()
    candidate = PatternCandidate(
        name="ballad_expr_demo",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic", expression_hint="soft_sustain"),),
    )
    event = candidate.instantiate(_region()).events[0]
    expr = ExpressionResolver().resolve([event], policy).events[event.event_id]
    assert expr.duration_beats == 3.5
    assert expr.velocity == 48
    assert expr.pedal == "sustain"
    assert expr.touch == "warm"


def test_expression_policy_bundle_accepts_legacy_dict_for_runtime_compatibility() -> None:
    event = PatternCandidate(
        name="legacy_expr_demo",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic", expression_hint="legacy_short"),),
    ).instantiate(_region()).events[0]
    expr = ExpressionResolver().resolve(
        [event],
        {"profiles": {"legacy_short": {"duration_beats": 0.5, "velocity": 63, "articulation": "short"}}},
    ).events[event.event_id]
    assert expr.duration_beats == 0.5
    assert expr.velocity == 63
    assert expr.articulation == "short"


def test_expression_profile_rejects_non_expression_data() -> None:
    # The expression policy module should expose profiles only, not patterns or concrete notes.
    policy = bossa_expression_policy.get_expression_policy()
    for profile in policy.profiles.values():
        assert isinstance(profile, ExpressionProfile)
        assert "midi_note" not in profile.metadata
        assert "chord_tones" not in profile.metadata
