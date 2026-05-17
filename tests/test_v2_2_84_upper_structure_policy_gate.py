from __future__ import annotations

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.voicing.policy import (
    ColorPolicyMode,
    VoicingPolicy,
    resolve_altered_dominant_policy,
)
from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources


def _policy(*, expansion: bool, altered: bool = False) -> VoicingPolicy:
    return VoicingPolicy(
        harmonic_expansion_enabled=expansion,
        color_policy_mode=ColorPolicyMode.ALTERED_DOMINANT if altered else (
            ColorPolicyMode.STYLE_SAFE_EXTENSIONS if expansion else ColorPolicyMode.CHORD_SYMBOL_ONLY
        ),
        metadata={
            "spread_upper_structure_enabled": True,
            "harmonic_expansion_enabled": expansion,
            "color_policy_mode": "altered_dominant" if altered else ("style_safe_extensions" if expansion else "chord_symbol_only"),
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "altered_dominant_policy": {
                "enabled": altered,
                "intensity": "high" if altered else "off",
                "scope": "functional_dominants",
            },
        },
    )


def test_upper_structure_does_not_bypass_harmonic_expansion() -> None:
    sources = plan_upper_structure_sources("G7", density=3, policy=_policy(expansion=False, altered=False))
    assert sources == ()


def test_expansion_only_dominant_uses_safe_upper_structure_sources() -> None:
    sources = plan_upper_structure_sources("G7", density=3, policy=_policy(expansion=True, altered=False))
    assert sources
    assert {source.chord_quality_gate for source in sources} == {"dominant_safe"}
    assert all("upper_structure_profile_kind_safe" in source.source_notes for source in sources)
    assert all("upper_structure_profile_kind_altered" not in source.source_notes for source in sources)


def test_expansion_plus_altered_dominant_authorizes_altered_sources() -> None:
    sources = plan_upper_structure_sources("G7", density=4, policy=_policy(expansion=True, altered=True))
    assert sources
    assert any("upper_structure_profile_kind_altered" in source.source_notes for source in sources)
    assert any("upper_structure_altered_dominant_authorized_true" in source.source_notes for source in sources)


def test_altered_enabled_without_expansion_does_not_alter_plain_dominant() -> None:
    policy = _policy(expansion=False, altered=True)
    # Make the semantic conflict explicit: altered is requested, but expansion
    # is off, so a plain G7 cannot receive unnotated Upper Structure color.
    policy = VoicingPolicy(
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata={
            "spread_upper_structure_enabled": True,
            "harmonic_expansion_enabled": False,
            "color_policy_mode": "chord_symbol_only",
            "altered_dominant_policy": {"enabled": True, "intensity": "high"},
        },
    )
    decision = resolve_altered_dominant_policy(policy, parse_chord("G7"))
    assert decision.enabled is True
    assert decision.authorized_for_chord is False
    assert plan_upper_structure_sources("G7", density=3, policy=policy) == ()


def test_explicit_altered_symbol_is_honored_even_without_global_expansion() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        metadata={
            "spread_upper_structure_enabled": True,
            "harmonic_expansion_enabled": False,
            "color_policy_mode": "chord_symbol_only",
            "altered_dominant_policy": {"enabled": False, "intensity": "off"},
        },
    )
    decision = resolve_altered_dominant_policy(policy, parse_chord("G7alt"))
    sources = plan_upper_structure_sources("G7alt", density=3, policy=policy)
    assert decision.authorized_for_chord is True
    assert sources
    assert all("upper_structure_altered_dominant_authorized_true" in source.source_notes for source in sources)
