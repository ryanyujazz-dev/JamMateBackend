from __future__ import annotations

# harness token: test_v2_2_40_spread_upper_source_adapter

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    SPREAD_RECIPE_CONTRACT_VERSION,
    UPPER_SOURCE_ADAPTER_VERSION,
    SpreadUpperSourceKind,
    adapt_spread_upper_source,
    spread_upper_source_adapter_debug,
    spread_upper_source_refs,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v2_2_40_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert SPREAD_RECIPE_CONTRACT_VERSION == "v2_2_40"
    assert UPPER_SOURCE_ADAPTER_VERSION == "v2_2_39"


def test_upper_source_refs_are_contract_derived_and_not_final_results() -> None:
    refs = {ref.ref_id: ref for ref in spread_upper_source_refs()}
    assert set(refs) == {
        "upper_2note_existing_guide_shell_source_ref",
        "upper_3note_existing_content_source_ref",
        "upper_4note_drop2_drop3_derived_source_ref",
    }
    assert refs["upper_4note_drop2_drop3_derived_source_ref"].kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK
    assert refs["upper_4note_drop2_drop3_derived_source_ref"].projection_methods == ("DROP2", "DROP3")
    for ref in refs.values():
        assert ref.adapter_required is True
        assert ref.final_placed_result_reuse_allowed is False


def test_upper_3note_adapter_reuses_existing_source_and_color_policy() -> None:
    result = adapt_spread_upper_source("G7b9", "upper_3note_existing_content_source_ref")
    assert result.option_count >= 3
    options = result.options
    degree_sets = {option.degree_names for option in options}
    assert ("3", "b7", "5") in degree_sets
    assert ("3", "b7", "b9") in degree_sets

    color_option = next(option for option in options if option.degree_names == ("3", "b7", "b9"))
    assert color_option.functional_source_type == "third_seventh_altered_color"
    assert "explicit_chord_symbol_color_used" in color_option.source_metadata
    assert color_option.final_placed_result_reuse_allowed is False
    assert color_option.notes_only is True
    assert color_option.runtime_enabled is False


def test_upper_4note_adapter_reuses_canonical_orientation_and_drop_resource_refs() -> None:
    result = adapt_spread_upper_source("Cmaj7", "upper_4note_drop2_drop3_derived_source_ref")
    assert result.upper_source_ref.kind == SpreadUpperSourceKind.DROP_FAMILY_DERIVED_PROJECTION_BLOCK
    assert result.option_count >= 4
    assert result.policy_metadata["reuses_core_content_planner"] is True
    assert result.policy_metadata["reuses_core_color_permission"] is True
    assert result.policy_metadata["reuses_drop_family_projection_resource"] is True
    assert result.policy_metadata["final_placed_result_reuse_allowed"] is False

    first = result.options[0]
    assert first.degree_names == ("R", "3", "5", "7")
    assert first.projection_methods == ("drop2", "drop3")
    assert any("basic_4note_functional_source_family" == token for token in first.source_metadata)
    assert first.orientation_token != "source_order_as_emitted_by_content_planner"
    assert first.to_debug_dict()["source_oriented_not_placed"] is True


def test_upper_4note_adapter_respects_chord_symbol_only_color_gate() -> None:
    plain = adapt_spread_upper_source("Cmaj7", "upper_4note_drop2_drop3_derived_source_ref")
    plain_degree_sets = {option.degree_names for option in plain.options}
    assert all("9" not in degrees for degrees in plain_degree_sets)

    explicit = adapt_spread_upper_source("Cmaj9", "upper_4note_drop2_drop3_derived_source_ref")
    explicit_degree_sets = {option.degree_names for option in explicit.options}
    assert any("9" in degrees for degrees in explicit_degree_sets)
    assert any(
        ("rootless_ab_explicit_chord_symbol_color_used" in option.source_metadata)
        or ("four_note_explicit_chart_color_set_9" in option.source_metadata)
        for option in explicit.options
        if "9" in option.degree_names
    )


def test_upper_source_adapter_debug_and_docs_are_synced() -> None:
    debug = spread_upper_source_adapter_debug("Dm7")
    assert debug["contract_version"] == "v2_2_40"
    assert debug["upper_source_adapter_version"] == "v2_2_39"
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert debug["source_oriented_not_placed"] is True
    assert debug["final_placed_result_reuse_allowed"] is False
    assert len(debug["results"]) == 3

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
        "Upper Source Adapter",
        "UPPER_SOURCE_ADAPTER_VERSION",
        "SpreadUpperSourceOption",
        "SpreadUpperSourceAdapterResult",
        "adapt_spread_upper_source",
        "spread_upper_source_adapter_debug",
        "source_oriented_not_placed",
        "final placed closed/open",
        "content_planner",
        "DROP2/DROP3",
        "notes-only",
    ]
    for token in required:
        assert token in docs
