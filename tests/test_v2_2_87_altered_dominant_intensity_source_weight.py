from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.voicing import (
    ALTERED_DOMINANT_POLICY_VERSION,
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    VoicingPolicy,
    resolve_altered_dominant_policy,
)
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.core.voicing.sources.source_balance import (
    ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION,
    altered_dominant_source_kind,
)
from jammate_engine.core.voicing.sources.upper_structure import plan_upper_structure_sources
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy

ROOT = Path(__file__).resolve().parents[1]


def _policy(intensity: str, *, allowed_content: tuple[ContentFamily, ...] | None = None) -> VoicingPolicy:
    allowed = allowed_content or (ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.ROOTED_COLOR)
    return VoicingPolicy(
        allowed_content=allowed,
        preferred_content=allowed[0],
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata={
            "harmonic_expansion_enabled": True,
            "color_policy_mode": "style_safe_extensions",
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "home_key": "C",
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": intensity,
                "scopes": "resolving_v7",
            },
            "strict_closed_compact_pitch_class_layout": True,
        },
    )


def test_altered_dominant_policy_exports_v2_2_88_source_weight_biases() -> None:
    decision = resolve_altered_dominant_policy(_policy("high"), parse_chord("G7"))
    assert ALTERED_DOMINANT_POLICY_VERSION == "v2_2_88"
    assert ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION == "v2_2_88"
    assert decision.to_debug_dict()["altered_dominant_policy_version"] == "v2_2_88"
    assert decision.to_debug_dict()["source_weight_biases"] == {
        "rooted_color": 0.16,
        "rootless_ab": 0.1,
        "upper_structure": 0.08,
    }


def test_intensity_biases_are_monotonic_and_source_specific() -> None:
    decisions = {
        intensity: resolve_altered_dominant_policy(_policy(intensity), parse_chord("G7"))
        for intensity in ("light", "medium", "high", "full")
    }
    rooted = [decisions[key].source_weight_bias("rooted_color") for key in decisions]
    rootless = [decisions[key].source_weight_bias("rootless_ab") for key in decisions]
    upper = [decisions[key].source_weight_bias("upper_structure") for key in decisions]
    assert rooted == sorted(rooted)
    assert rootless == sorted(rootless)
    assert upper == sorted(upper)
    assert decisions["light"].source_weight_bias("rootless_ab") < 0.0
    assert decisions["full"].source_weight_bias("upper_structure") > decisions["medium"].source_weight_bias("upper_structure")


def test_selector_details_include_altered_intensity_source_score() -> None:
    scores: dict[str, float] = {}
    for intensity in ("light", "medium", "high", "full"):
        policy = _policy(intensity)
        candidate = next(c for c in generate_candidates("G7", policy) if altered_dominant_source_kind(c) == "rootless_ab")
        breakdown = score_candidate(candidate, policy)
        scores[intensity] = breakdown.details["altered_dominant_intensity_score"]
        assert breakdown.details["altered_dominant_source_kind"] == "rootless_ab"
        assert breakdown.details["source_balance_score"] == breakdown.details["altered_dominant_intensity_score"]
    assert scores["light"] < scores["medium"] < scores["high"] < scores["full"]


def test_upper_structure_intensity_changes_safe_vs_altered_source_mix() -> None:
    def sources(intensity: str):
        policy = replace(
            _policy(intensity),
            metadata={**(_policy(intensity).metadata or {}), "spread_upper_structure_enabled": True},
        )
        return plan_upper_structure_sources("G7", density=3, policy=policy)

    light = sources("light")
    high = sources("high")
    full = sources("full")
    assert ["upper_structure_profile_kind_altered" in source.source_notes for source in light] == [False, True]
    assert "upper_structure_profile_kind_altered" in high[0].source_notes
    assert all("upper_structure_profile_kind_altered" in source.source_notes for source in full)
    assert any("altered_dominant_intensity_light" in source.source_notes for source in light)
    assert any("upper_structure_altered_dominant_intensity_bias_+0.180" in source.source_notes for source in full)


def test_explicit_altered_symbols_receive_at_least_medium_bias_even_when_light() -> None:
    decision = resolve_altered_dominant_policy(_policy("light"), parse_chord("G7alt"))
    assert decision.authorized_for_chord is True
    assert decision.explicit_chord_symbol_altered is True
    assert decision.source_weight_bias("rooted_color") >= 0.10
    assert decision.source_weight_bias("rootless_ab") >= 0.02
    assert decision.source_weight_bias("upper_structure") >= 0.0


def test_style_profiles_supply_different_default_bias_tables() -> None:
    def activated(policy: VoicingPolicy, intensity: str = "high") -> VoicingPolicy:
        return replace(
            policy,
            metadata={
                **(policy.metadata or {}),
                "harmonic_expansion_enabled": True,
                "color_policy_mode": "style_safe_extensions",
                "previous_chord_symbol": "Dm7",
                "next_chord_symbol": "Cmaj7",
                "home_key": "C",
                "altered_dominant_policy": {"enabled": True, "intensity": intensity, "scopes": "resolving_v7"},
            },
        )

    swing = resolve_altered_dominant_policy(activated(swing_policy()), parse_chord("G7"))
    ballad = resolve_altered_dominant_policy(activated(ballad_policy()), parse_chord("G7"))
    bossa = resolve_altered_dominant_policy(activated(bossa_policy()), parse_chord("G7"))
    assert swing.source_weight_bias("rootless_ab") > bossa.source_weight_bias("rootless_ab")
    assert ballad.source_weight_bias("upper_structure") > bossa.source_weight_bias("upper_structure")
    assert bossa_policy().metadata["altered_dominant_source_weight_calibration"]["default_intensity"] == "light"


def test_v2_2_88_contract_and_docs_are_updated() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
        ROOT / "docs" / "ALTERED_DOMINANT_INTENSITY_SOURCE_WEIGHT_CALIBRATION_V2_2_87.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_2_88" in text, path
        assert "Altered Dominant Intensity / Source Weight Calibration" in text, path
        assert "rooted_color" in text and "rootless_ab" in text and "upper_structure" in text, path
