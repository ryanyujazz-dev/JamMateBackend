from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path

from jammate_engine.core.voicing import ColorPolicyMode, ContentFamily, VoicingPolicy
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_voicing_policy

MILESTONE_ID = "v2_6_118"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_additive_unnotated_altered_dominant_source_pool_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_additive_unnotated_altered_dominant_source_pool_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _authorized_plain_dominant_policy(base: VoicingPolicy | None = None) -> VoicingPolicy:
    policy = base or get_swing_voicing_policy()
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "harmonic_expansion_enabled": True,
            "color_policy_mode": ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "home_key": "C",
            "key": "C",
            "altered_dominant_policy": {
                "enabled": True,
                "intensity": "light",
                "scopes": ["resolving_v7"],
            },
        }
    )
    return replace(
        policy,
        allowed_content=(ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        min_density=4,
        preferred_density=4,
        max_density=4,
        metadata=metadata,
    )


def _rootless_recipes(symbol: str, policy: VoicingPolicy):
    return [recipe for recipe in plan_content_recipes(symbol, policy) if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]


def test_v2_6_118_style_policies_expose_additive_altered_source_pool_contract() -> None:
    for policy in (get_bossa_voicing_policy(), get_swing_voicing_policy(), get_ballad_voicing_policy()):
        metadata = dict(policy.metadata or {})
        assert metadata["dominant_altered_source_pool_policy_version"] == MILESTONE_ID
        assert metadata["dominant_altered_source_pool_policy_enabled"] is True
        assert metadata["dominant_altered_source_pool_policy_target"]["plain_authorized_dominants"] == "ordinary_9_13_plus_altered_pool"
        assert metadata["dominant_altered_source_pool_policy_target"]["explicit_altered_chart_symbols"] == "altered_only_chart_fidelity"
        assert metadata["dominant_altered_source_pool_policy_target"]["does_not_apply_post_voicing_note_alteration"] is True
        assert metadata["dominant_altered_source_pool_policy_target"]["does_not_change_projection"] is True


def test_v2_6_118_plain_authorized_dominant_adds_altered_rootless_without_replacing_safe_9_13_sources() -> None:
    recipes = _rootless_recipes("G7", _authorized_plain_dominant_policy())
    validity_sets = [set(recipe.validity_notes) for recipe in recipes]

    assert any("rootless_ab_content_type_with_5" in notes for notes in validity_sets)
    assert any("rootless_ab_content_type_with_13" in notes for notes in validity_sets)
    assert any("rootless_ab_content_type_altered_dominant_rootless" in notes for notes in validity_sets)
    assert any("altered_dominant_authorization_reason_harmonic_expansion_plus_altered_dominant_resolving_v7" in notes for notes in validity_sets)


def test_v2_6_118_explicit_altered_chart_symbol_stays_altered_only_for_rootless_chart_fidelity() -> None:
    recipes = _rootless_recipes("G7b9b13", _authorized_plain_dominant_policy())
    assert recipes
    assert all("rootless_ab_content_type_altered_dominant_rootless" in recipe.validity_notes for recipe in recipes)
    assert all("5" not in recipe.degree_names for recipe in recipes)
    assert any("altered_dominant_authorization_reason_explicit_chord_symbol_altered" in recipe.validity_notes for recipe in recipes)


def test_v2_6_118_neutral_ab_filter_can_keep_safe_and_altered_candidates_for_plain_dominant() -> None:
    policy = _authorized_plain_dominant_policy(get_bossa_voicing_policy())
    metadata = dict(policy.metadata or {})
    metadata.update(
        {
            "progression_four_note_orientation_alignment_policy_runtime_enabled": True,
            "progression_four_note_orientation_alignment_policy_applied": True,
            "progression_four_note_orientation_alignment_policy_runtime_filtering_enabled": True,
            "progression_four_note_orientation_alignment_policy_desired_family": "rootless_ab",
            "progression_four_note_orientation_alignment_policy_desired_ab_side": "B",
            "progression_four_note_orientation_alignment_policy_desired_content_type": "with_5",
            "progression_four_note_orientation_alignment_policy_desired_source_family": "third_fifth_seventh_ninth",
            "progression_four_note_orientation_alignment_policy_desired_ab_pair_index": 0,
            "progression_four_note_orientation_alignment_policy_desired_inversion_index": 0,
        }
    )
    candidates = generate_candidates("G7", replace(policy, metadata=metadata))
    rootless = [candidate for candidate in candidates if candidate.metadata.get("four_note_rotation_family") == "rootless_ab"]

    assert rootless
    assert {candidate.metadata.get("four_note_rotation_ab_side") for candidate in rootless} == {"B"}
    source_families = {candidate.metadata.get("four_note_rotation_source_family") for candidate in rootless}
    assert "third_fifth_seventh_ninth" in source_families
    assert "third_thirteenth_seventh_ninth" in source_families
    assert "altered_dominant_rootless" in source_families
    assert all(candidate.metadata.get("progression_four_note_orientation_alignment_policy_filter_applied") is True for candidate in rootless)


def test_v2_6_118_acceptance_passes_for_additive_altered_source_pool_audit() -> None:
    module = _load_script_module()
    audits = [module.generate_style_audit(style, spec) for style, spec in module.SPEC_BY_STYLE.items()]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": "test",
        "styles": audits,
    }
    summary["global_findings"] = module.build_global_findings(audits)
    acceptance = module.acceptance(summary)

    assert acceptance["passed"] is True
