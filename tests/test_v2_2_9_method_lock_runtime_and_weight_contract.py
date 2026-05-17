from __future__ import annotations

from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing.disposition import (
    DispositionFamily,
    OpenProjectionMethod,
    VoicingMethodLockMode,
    VoicingMethodLockPattern,
    VoicingMethodLockScope,
    method_lock_runtime_plan_for_projection,
    method_lock_spec_from_metadata,
)
from jammate_engine.core.voicing.disposition.method_weights import (
    disposition_method_weight_spec_from_metadata,
)
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as medium_swing_policy
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy


def test_method_lock_runtime_plan_is_planning_only_for_strict_drop2() -> None:
    spec = method_lock_spec_from_metadata(
        {
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "pattern": "ii_v_i",
                "mode": "strict",
                "family": "open",
                "method": "drop2",
            }
        }
    )
    matched = method_lock_runtime_plan_for_projection(
        spec,
        {"disposition_projection_family": "open", "disposition_projection_method": "drop2"},
    ).to_debug_dict()
    mismatched = method_lock_runtime_plan_for_projection(
        spec,
        {"disposition_projection_family": "open", "disposition_projection_method": "drop3"},
    ).to_debug_dict()

    assert matched["candidate_matches_lock"] is True
    assert matched["planned_action"] == "keep_candidate_future"
    assert matched["scoring_enabled"] is False
    assert matched["filtering_enabled"] is False
    assert mismatched["candidate_matches_lock"] is False
    assert mismatched["planned_action"] == "filter_candidate_future"
    assert mismatched["filtering_enabled"] is False


def test_disposition_method_weight_contract_parses_style_defaults_and_metadata() -> None:
    medium = disposition_method_weight_spec_from_metadata({"style": "medium_swing"})
    assert medium.family_weights["open"] == 0.70
    assert medium.open_method_weights["drop2"] == 0.50
    assert medium.enabled_for_scoring is False

    custom = disposition_method_weight_spec_from_metadata(
        {
            "disposition_method_weights": {
                "family": {"open": 0.7, "closed": 0.3},
                "open": {"drop2": 0.6, "drop3": 0.4},
                "spread": {"foundation": 0.8},
            },
            "disposition_method_weights_enabled_for_scoring": True,
        }
    )
    assert custom.family_weights == {"open": 0.7, "closed": 0.3}
    assert custom.open_method_weights == {"drop2": 0.6, "drop3": 0.4}
    assert custom.spread_method_weights == {"foundation_projection": 0.8}
    assert custom.enabled_for_scoring is True


def test_candidates_expose_runtime_lock_and_weight_contract_without_scoring_effect() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=46,
        register_high=84,
        max_voicing_span=28,
        metadata={
            "style": "medium_swing",
            "open_projection_method_pool": "all",
            "voicing_method_lock": {
                "enabled": True,
                "scope": "progression",
                "pattern": "ii_v_i",
                "mode": "prefer",
                "family": "open",
                "method": "drop2",
            },
        },
    )
    candidates = generate_candidates("Dm7", policy)
    assert candidates
    methods = {candidate.metadata["disposition_projection_method"] for candidate in candidates}
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.issubset(methods)
    assert all(candidate.metadata["voicing_method_lock_runtime_scoring_enabled"] is False for candidate in candidates)
    assert all(candidate.metadata["voicing_method_lock_runtime_filtering_enabled"] is False for candidate in candidates)
    assert any(candidate.metadata["voicing_method_lock_candidate_matches"] is True for candidate in candidates)
    assert any(candidate.metadata["voicing_method_lock_candidate_matches"] is False for candidate in candidates)
    assert all(candidate.metadata["disposition_method_weight_scoring_enabled"] is False for candidate in candidates)
    drop2_candidates = [candidate for candidate in candidates if candidate.metadata["disposition_projection_method"] == "drop2"]
    assert drop2_candidates
    assert drop2_candidates[0].metadata["disposition_method_weight"] == 0.70 * 0.50


def test_style_policies_carry_disposition_method_weights_with_style_specific_runtime_flags() -> None:
    medium = medium_swing_policy()
    medium_metadata = dict(medium.metadata or {})
    assert medium_metadata["disposition_method_weight_contract"].startswith("runtime_pilot_v2_2_20")
    medium_spec = disposition_method_weight_spec_from_metadata(medium_metadata)
    assert medium_spec.family_weights
    assert medium_spec.open_method_weights
    assert medium_spec.spread_method_weights
    assert medium_spec.enabled_for_scoring is True

    for policy in [bossa_policy(), ballad_policy()]:
        metadata = dict(policy.metadata or {})
        assert metadata["disposition_method_weight_contract"].startswith("planning_only_v2_2_10")
        spec = disposition_method_weight_spec_from_metadata(metadata)
        assert spec.family_weights
        assert spec.open_method_weights
        assert spec.spread_method_weights
        assert spec.enabled_for_scoring is False


def test_method_lock_enums_remain_public_contract() -> None:
    assert VoicingMethodLockScope.PROGRESSION.value == "progression"
    assert VoicingMethodLockPattern.II_V_I.value == "ii_v_i"
    assert VoicingMethodLockMode.PREFER.value == "prefer"
    assert DispositionFamily.OPEN.value == "open"
    assert OpenProjectionMethod.DROP2_AND_4.value == "drop2_and_4"
