from __future__ import annotations

# harness token: test_v2_2_55_spread_upper_4note_drop2_drop3_only

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition import (
    SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION,
    project_basic_spread_candidates,
    spread_recipe_contract_skeleton,
)
from jammate_engine.core.voicing.disposition import spread as spread_module


def test_v2_2_55_version_and_spread_upper_constant_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    assert SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION == "v2_2_55"


def test_spread_upper_four_note_contract_excludes_drop2_and_4() -> None:
    upper_4_contracts = [
        contract for contract in spread_recipe_contract_skeleton() if contract.upper_source.note_count == 4
    ]
    assert upper_4_contracts
    for contract in upper_4_contracts:
        normalized = tuple(method.lower().replace("_", "") for method in contract.upper_source.projection_methods)
        assert normalized == ("drop2", "drop3")
        assert "drop2_and_4" not in contract.upper_source.projection_methods
        assert "DROP2_AND_4" not in contract.upper_source.projection_methods


def test_spread_upper_four_note_projection_filter_rejects_rogue_drop2_and_4() -> None:
    assert spread_module._spread_allowed_upper_4note_projection_methods(("DROP2", "DROP2&4", "DROP3")) == (
        "drop2",
        "drop3",
    )
    assert spread_module._spread_allowed_upper_4note_projection_methods(("DROP2_AND_4",)) == (
        "drop2",
        "drop3",
    )


def test_spread_1plus4_real_candidates_only_report_drop2_or_drop3() -> None:
    result = project_basic_spread_candidates(
        "Cmaj9",
        contract_ids=("spread_1plus4_contract",),
        max_upper_options=8,
    )[0]
    assert result.candidates
    for candidate in result.candidates:
        assert candidate.recipe_contract.recipe_id == "spread_1plus4_contract"
        assert candidate.upper_projection_method in {"drop2", "drop3"}
        assert candidate.upper_projection_method != "drop2_and_4"
        metadata = candidate.upper_projection_metadata
        assert metadata["spread_upper_4note_drop2_drop3_only_version"] == "v2_2_55"
        assert metadata["spread_upper_4note_allowed_projection_methods"] == ["drop2", "drop3"]
        assert metadata["spread_upper_4note_drop2_and_4_allowed"] is False
        assert "open_drop2_and_4_projection" not in metadata
