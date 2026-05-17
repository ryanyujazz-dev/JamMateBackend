from __future__ import annotations

# harness token: test_v2_2_56_ballad_spread_1plus3_pilot

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    BALLAD_SPREAD_1PLUS3_PILOT_VERSION,
    ContentFamily,
    ColorPolicyMode,
    Disposition,
    VoicingPolicy,
    generate_candidates,
    guard_ballad_spread_pilot_runtime_enablement,
    source_preserves_seventh_chord_identity,
)
from jammate_engine.core.voicing.disposition import (
    BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION,
    ballad_spread_runtime_entry_contract,
    project_basic_spread_candidates,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _one_plus_three_policy() -> VoicingPolicy:
    return VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={
            "style": "jazz_ballad",
            "primary_family": "spread",
            "allowed_families": ["spread"],
            "spread_selector_enabled": True,
            "ballad_spread_runtime_pilot": {
                "version": "v2_2_56",
                "enabled": True,
                "scene": "warm_spread_phrase",
                "contract_ids": ["spread_1plus3_contract"],
                "preferred_contract_ids": ["spread_1plus3_contract"],
            },
            "ballad_spread_runtime_safe_dry_run": {
                "version": "v2_2_56",
                "dry_run_enabled": True,
                "candidate_conversion_allowed": True,
            },
            "spread_runtime_adapter_skeleton": {
                "version": "v2_2_56",
                "adapter_conversion_allowed": True,
            },
            "ballad_spread_runtime_candidate_pool": {
                "version": "v2_2_56",
                "candidate_pool_enabled": True,
                "adapter_conversion_allowed": True,
                "candidate_pool_merge_allowed": True,
                "candidate_generator_wiring_allowed": True,
                "fallback_to_existing_pool": True,
            },
            "ballad_spread_pilot_runtime_enablement_guard": {
                "version": "v2_2_56",
                "runtime_guard_enabled": True,
                "listening_isolation_enabled": True,
                "first_listening_isolation_only": True,
            },
            "spread_contract_true_isolation": {
                "version": "v2_2_56",
                "enabled": True,
                "required_recipe_id": "spread_1plus3_contract",
                "fallback_only_when_missing": True,
            },
        },
    )


def test_v2_2_56_version_and_1plus3_pilot_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert BALLAD_SPREAD_1PLUS3_PILOT_VERSION == "v2_2_56"
    assert BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION == "v2_2_43"


def test_ballad_entry_contract_deprecates_1plus3_from_active_spread_entry() -> None:
    contract = ballad_spread_runtime_entry_contract(
        _one_plus_three_policy(),
        contract_ids=("spread_1plus3_contract",),
    )
    assert "spread_1plus3_contract" not in contract.allowed_contract_ids
    assert "1+3" not in contract.allowed_groupings
    assert contract.density_range == (4, 6)


def test_spread_1plus3_candidates_preserve_seventh_identity_for_seventh_chords() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={"harmonic_expansion_target_families": [ContentFamily.ROOTED_COLOR.value]},
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_1plus3_contract",),
        max_upper_options=8,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.recipe_contract.recipe_id == "spread_1plus3_contract"
        assert candidate.density == 4
        assert candidate.metadata["ballad_spread_1plus3_pilot_version"] == "v2_2_56"
        assert candidate.metadata["source_preserves_seventh_chord_identity"] is True
        assert source_preserves_seventh_chord_identity("Ebmaj7", candidate.degrees)


def test_active_generator_no_longer_routes_to_1plus3_spread_candidate() -> None:
    candidates = generate_candidates("Ebmaj7", _one_plus_three_policy())
    assert candidates
    assert not any(candidate.recipe_id == "spread_1plus3_contract" for candidate in candidates)


def test_1plus3_guard_no_longer_activates_deprecated_grouping() -> None:
    base = tuple(
        generate_candidates(
            "Ebmaj7",
            VoicingPolicy(
                preferred_disposition=Disposition.OPEN,
                allowed_dispositions=(Disposition.OPEN,),
                metadata={"style": "jazz_ballad"},
            ),
        )
    )
    result = guard_ballad_spread_pilot_runtime_enablement(
        "Ebmaj7",
        _one_plus_three_policy(),
        base_candidates=base,
    )
    assert result.guarded_candidates
    assert not any(candidate.recipe_id == "spread_1plus3_contract" for candidate in result.guarded_candidates)


def test_demo_script_requests_1plus3_isolation() -> None:
    script = _read("examples/scripts/generate_ballad_spread_first_listening_isolation_demo.py")
    assert "v2_2_56_misty_jazz_ballad_spread_1plus3_pilot_demo.mid" in script
    assert "spread_contract_true_isolation" in script
    assert '"required_recipe_id": "spread_1plus3_contract"' in script


def test_1plus3_expanded_color_isolation_can_force_actual_color_tone() -> None:
    policy = VoicingPolicy(
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        metadata={
            "spread_upper_3note_prefer_expanded_color": True,
            "spread_upper_3note_expanded_color_only": True,
        },
    )
    result = project_basic_spread_candidates(
        "Ebmaj7",
        policy=policy,
        contract_ids=("spread_1plus3_contract",),
        max_upper_options=8,
    )[0]
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    assert all(candidate.upper_source.source_family == ContentFamily.SHELL_PLUS_COLOR.value for candidate in legal)
    assert any("9" in candidate.upper_source.degree_names for candidate in legal)
    assert not any("R" in candidate.upper_source.degree_names for candidate in legal)
    assert not any("5" in candidate.upper_source.degree_names for candidate in legal)


def test_expanded_color_demo_script_requests_harmonic_expansion_and_color_only_filter() -> None:
    script = _read("examples/scripts/generate_ballad_spread_1plus3_expanded_listening_demo.py")
    assert "v2_2_56_misty_jazz_ballad_spread_1plus3_expanded_color_demo.mid" in script
    assert '"harmonic_expansion_enabled": True' in script
    assert '"color_policy_mode": "style_safe_extensions"' in script
    assert '"spread_upper_3note_prefer_expanded_color": True' in script
    assert '"spread_upper_3note_expanded_color_only": True' in script
