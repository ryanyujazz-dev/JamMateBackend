from __future__ import annotations

# harness token: test_v2_2_40_basic_spread_projection

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    BASIC_SPREAD_PROJECTION_VERSION,
    LOWER_GROUP_INVENTORY_VERSION,
    SPREAD_RECIPE_CONTRACT_VERSION,
    UPPER_SOURCE_ADAPTER_VERSION,
    SpreadProjectionCandidate,
    SpreadProjectionRegisterPolicy,
    SpreadProjectionResult,
    basic_spread_projection_debug,
    project_basic_spread_candidates,
    project_basic_spread_contract,
    spread_recipe_contract_by_id,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_40_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RECIPE_CONTRACT_VERSION == "v2_2_40"
    assert BASIC_SPREAD_PROJECTION_VERSION == "v2_2_40"
    # Preserve sub-contract provenance instead of pretending they were rebuilt.
    assert LOWER_GROUP_INVENTORY_VERSION == "v2_2_38"
    assert UPPER_SOURCE_ADAPTER_VERSION == "v2_2_39"


def test_basic_projection_projects_all_contracts_without_runtime_enablement() -> None:
    results = project_basic_spread_candidates("Cmaj7")
    assert len(results) == 7
    assert all(isinstance(result, SpreadProjectionResult) for result in results)
    assert all(result.legal_candidate_count > 0 for result in results)
    assert all(result.runtime_enabled is False for result in results)

    debug = basic_spread_projection_debug("Cmaj7")
    assert debug["contract_version"] == "v2_2_40"
    assert debug["basic_spread_projection_version"] == "v2_2_40"
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert debug["final_placed_closed_open_result_reuse_allowed"] is False
    assert len(debug["results"]) == 7


def test_spread_1plus4_uses_lower_root_and_upper_drop_resource_without_reusing_final_open_result() -> None:
    result = project_basic_spread_contract("Cmaj7", "spread_1plus4_contract")
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    first = legal[0]
    assert isinstance(first, SpreadProjectionCandidate)
    assert first.recipe_contract.grouping.value == "1+4"
    assert first.lower.instance.recipe.recipe_id.value == "lower_1note_root"
    assert first.lower_notes == (36,)
    assert first.upper_projection_method in {"drop2", "drop3"}
    assert first.density == 5
    assert first.metadata["expected_density"] == 5
    assert first.metadata["upper_projection_metadata"]["spread_upper_projection_uses_drop_family_resource"] is True
    assert first.metadata["upper_projection_metadata"]["spread_upper_projection_resource_owner"] == "core.voicing.disposition.open"
    assert first.metadata["source_oriented_not_placed"] is False
    assert first.metadata["final_placed_closed_open_result_reuse_allowed"] is False
    assert first.metadata["runtime_enabled"] is False
    assert first.metadata["notes_only"] is True
    assert first.metadata["no_expression_or_pedal"] is True


def test_basic_projection_respects_group_gap_span_and_register_metadata() -> None:
    policy = SpreadProjectionRegisterPolicy(
        lower_low=36,
        lower_high=60,
        upper_low=55,
        upper_high=84,
        min_group_gap=5,
        max_group_gap=28,
        max_overall_span=48,
    )
    result = project_basic_spread_contract("Dm7", spread_recipe_contract_by_id("spread_2plus3_contract"), policy)
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    for candidate in legal:
        assert candidate.group_gap_semitones is not None
        assert 5 <= candidate.group_gap_semitones <= 28
        assert candidate.overall_span_semitones <= 48
        # v2_2_73: lower 2-note SPREAD foundations use a fixed E2-E3 band
        # with the upper lower-note at least E2, independent of generic lower_low/high.
        assert min(candidate.lower_notes) >= 40
        assert max(candidate.lower_notes) <= 52
        assert max(candidate.lower_notes) >= 40
        assert min(candidate.upper_notes) >= 55
        assert max(candidate.upper_notes) <= 84
        assert candidate.metadata["group_gap_guard"]["actual_group_gap"] == candidate.group_gap_semitones
        assert candidate.metadata["span_guard"]["actual_overall_span"] == candidate.overall_span_semitones


def test_basic_projection_keeps_chord_symbol_color_gate_for_upper_sources() -> None:
    plain = project_basic_spread_contract("Cmaj7", "spread_1plus4_contract")
    plain_upper_degree_sets = {candidate.upper_source.degree_names for candidate in plain.candidates if candidate.is_legal}
    assert plain_upper_degree_sets
    assert all("9" not in degrees for degrees in plain_upper_degree_sets)

    explicit = project_basic_spread_contract("Cmaj9", "spread_1plus4_contract")
    explicit_upper_degree_sets = {candidate.upper_source.degree_names for candidate in explicit.candidates if candidate.is_legal}
    assert any("9" in degrees for degrees in explicit_upper_degree_sets)


def test_basic_spread_projection_docs_are_synced() -> None:
    docs = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/VOICING_SYSTEM_V2_DESIGN.md",
            "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
            "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/DEVELOPMENT_HARNESS_V2.md",
            "docs/GENERATION_RULES_SUMMARY_V2.md",
        )
    )
    required = [
        "Basic SPREAD Projection",
        "BASIC_SPREAD_PROJECTION_VERSION",
        "SpreadProjectionRegisterPolicy",
        "SpreadProjectionCandidate",
        "SpreadProjectionResult",
        "project_basic_spread_contract",
        "project_basic_spread_candidates",
        "basic_spread_projection_debug",
        "group_gap_guard",
        "span_guard",
        "lower inventory + upper source adapter",
        "runtime_enabled=false",
        "notes-only",
    ]
    for token in required:
        assert token in docs
