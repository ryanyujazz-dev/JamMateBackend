from __future__ import annotations

# harness token: test_v2_6_22_engine_voicing_cleanup_retired_spread_pilot_logic

from dataclasses import replace
from pathlib import Path

from jammate_engine.core.voicing import generate_candidates
from jammate_engine.core.voicing.disposition import spread as public_spread
from jammate_engine.core.voicing.disposition import spread_runtime_adapter
from jammate_engine.styles.jazz_ballad.profile import JazzBalladProfile

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_6_22_retired_spread_pilot_symbols_are_removed_from_public_spread_surface() -> None:
    retired_symbols = [
        "BalladSpreadRuntimeEntryContract",
        "ballad_spread_runtime_entry_contract",
        "run_ballad_spread_runtime_safe_dry_run",
        "spread_runtime_conversion_boundary_audit",
        "run_ballad_spread_runtime_adapter_skeleton",
        "build_ballad_spread_runtime_pilot_candidate_pool",
        "guard_ballad_spread_pilot_runtime_enablement",
        "audit_ballad_spread_pilot_selection_weight_and_fallback",
    ]
    for name in retired_symbols:
        assert not hasattr(public_spread, name), name


def test_v2_6_22_spread_runtime_adapter_owns_projection_candidate_conversion() -> None:
    assert hasattr(spread_runtime_adapter, "spread_projection_candidate_to_voicing_candidate_adapter")
    assert public_spread.spread_projection_candidate_to_voicing_candidate_adapter is spread_runtime_adapter.spread_projection_candidate_to_voicing_candidate_adapter
    debug = spread_runtime_adapter.spread_runtime_adapter_owner_debug({"spread_runtime_adapter": {"adapter_conversion_allowed": True}})
    assert debug["implementation_owner"] == "core.voicing.disposition.spread_runtime_adapter"


def test_v2_6_22_candidate_generator_uses_grouped_spread_runtime_not_pilot_guard() -> None:
    text = _read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    assert "guard_ballad_spread_pilot_runtime_enablement" not in text
    assert "_maybe_merge_ballad_spread_runtime_pilot_candidates" not in text
    assert "_maybe_use_grouped_spread_runtime_candidates" in text
    assert "project_basic_spread_candidates" in text
    assert "spread_projection_candidate_to_voicing_candidate_adapter" in text


def test_v2_6_22_ballad_policy_no_longer_exposes_disabled_pilot_metadata_keys() -> None:
    metadata = JazzBalladProfile().voicing_policy.metadata
    retired_top_level_keys = {
        "ballad_spread_runtime_pilot",
        "ballad_spread_runtime_safe_dry_run",
        "ballad_spread_runtime_candidate_pool",
        "ballad_spread_pilot_runtime_enablement_guard",
        "ballad_spread_1plus3_pilot",
        "ballad_spread_1plus4_true_isolation",
    }
    assert retired_top_level_keys.isdisjoint(metadata.keys())
    assert metadata["retired_spread_pilot_logic_cleanup"]["version"] == "v2_6_22"


def test_v2_6_22_grouped_spread_runtime_candidate_pool_still_generates_selected_contract() -> None:
    policy = JazzBalladProfile().voicing_policy
    selected = "spread_2plus4_contract"
    metadata = {
        **dict(policy.metadata or {}),
        "primary_family": "spread",
        "allowed_families": ["spread"],
        "spread_selector_enabled": True,
        "ballad_spread_grouping_mix_selected_contract_id": selected,
        "ballad_spread_grouping_mix_policy_decision": {"selected_contract_id": selected},
        "spread_grouping_mix_candidate_pool": {
            "version": "v2_6_22",
            "use_compatible_contracts": True,
            "compatible_contract_ids": [selected],
            "selected_contract_id": selected,
        },
        "spread_runtime_adapter": {"adapter_conversion_allowed": True},
        "spread_groupwise_voice_leading_runtime_enabled": True,
    }
    candidates = generate_candidates("Cmaj7", replace(policy, metadata=metadata))
    assert candidates
    assert {candidate.recipe_id for candidate in candidates} == {selected}
    assert all(len(candidate.notes) == 6 for candidate in candidates)
    assert all(candidate.metadata.get("candidate_pool_source") == "grouped_spread_runtime" for candidate in candidates)
    assert all(candidate.metadata.get("spread_grouped_runtime_candidate_pool_version") == "v2_6_22" for candidate in candidates)
    assert all(candidate.metadata.get("no_expression_or_pedal") is True for candidate in candidates)
