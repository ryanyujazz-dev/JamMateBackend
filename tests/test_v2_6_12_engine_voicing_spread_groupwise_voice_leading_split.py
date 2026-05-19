from __future__ import annotations

# harness token: test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split

import ast
from pathlib import Path

from jammate_engine.core.voicing.disposition import (
    SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION,
)
from jammate_engine.core.voicing.disposition import spread as public_spread
from jammate_engine.core.voicing.disposition import spread_voice_leading
from jammate_engine.core.voicing.disposition.spread import project_basic_spread_contract

ROOT = Path(__file__).resolve().parents[1]
SPREAD = ROOT / "src/jammate_engine/core/voicing/disposition/spread.py"
SPREAD_VL = ROOT / "src/jammate_engine/core/voicing/disposition/spread_voice_leading.py"


def _defined_symbols(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in module.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}


def _first_legal_signature(symbol: str) -> tuple[object, ...]:
    result = project_basic_spread_contract(symbol, "spread_2plus3_contract")
    legal = [candidate for candidate in result.candidates if candidate.is_legal]
    assert legal
    first = legal[0]
    return (
        len(result.candidates),
        len(legal),
        first.notes,
        first.degrees,
        first.density,
        first.recipe_contract.grouping.value,
        first.upper_projection_method,
        first.lower.instance.recipe.recipe_id.value,
    )


def test_v2_6_12_groupwise_voice_leading_has_dedicated_owner() -> None:
    assert SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_VERSION == "v2_6_12"
    assert SPREAD_VL.exists()

    new_owner_symbols = _defined_symbols(SPREAD_VL)
    assert "SpreadGroupwiseVoiceLeadingWeights" in new_owner_symbols
    assert "SpreadGroupwiseVoiceLeadingScore" in new_owner_symbols
    assert "compute_groupwise_motion_score" in new_owner_symbols
    assert "rank_spread_candidates_by_group_motion" in new_owner_symbols
    assert "spread_voice_leading_debug" in new_owner_symbols

    spread_symbols = _defined_symbols(SPREAD)
    assert "SpreadGroupwiseVoiceLeadingWeights" not in spread_symbols
    assert "SpreadGroupwiseVoiceLeadingScore" not in spread_symbols
    assert "score_spread_groupwise_voice_leading" not in spread_symbols
    assert "rank_spread_candidates_by_groupwise_voice_leading" not in spread_symbols


def test_v2_6_12_public_compatibility_surface_reexports_new_owner() -> None:
    assert public_spread.SpreadGroupwiseVoiceLeadingWeights is spread_voice_leading.SpreadGroupwiseVoiceLeadingWeights
    assert public_spread.SpreadGroupwiseVoiceLeadingScore is spread_voice_leading.SpreadGroupwiseVoiceLeadingScore
    assert public_spread.score_spread_groupwise_voice_leading is spread_voice_leading.score_spread_groupwise_voice_leading
    assert (
        public_spread.rank_spread_candidates_by_groupwise_voice_leading
        is spread_voice_leading.rank_spread_candidates_by_groupwise_voice_leading
    )

    debug = public_spread.spread_groupwise_voice_leading_path_debug(("Dm7", "G7", "Cmaj7"))
    assert debug["implementation_owner"] == "core.voicing.disposition.spread_voice_leading"
    assert debug["spread_groupwise_voice_leading_split_version"] == "v2_6_12"
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True


def test_v2_6_12_spread_candidate_signatures_remain_stable_for_core_symbols() -> None:
    assert _first_legal_signature("Cmaj7") == (
        14,
        11,
        (47, 48, 55, 59, 64),
        ("7", "R", "5", "7", "3"),
        5,
        "2+3",
        "closed_upper_stack",
        "lower_2note_root_7",
    )
    assert _first_legal_signature("G7b9") == (
        28,
        24,
        (43, 47, 53, 56, 59),
        ("R", "3", "b7", "b9", "3"),
        5,
        "2+3",
        "closed_upper_stack",
        "lower_2note_root_3",
    )
    assert _first_legal_signature("Bm7b5") == (
        14,
        11,
        (45, 47, 53, 57, 62),
        ("b7", "R", "b5", "b7", "b3"),
        5,
        "2+3",
        "closed_upper_stack",
        "lower_2note_root_7",
    )


def test_v2_6_12_groupwise_scoring_stays_notes_only_and_componentized() -> None:
    previous = [candidate for candidate in project_basic_spread_contract("Dm7", "spread_2plus3_contract").candidates if candidate.is_legal][0]
    current = [candidate for candidate in project_basic_spread_contract("G7", "spread_2plus3_contract").candidates if candidate.is_legal][0]
    score = spread_voice_leading.compute_groupwise_motion_score(current, previous)
    debug = score.to_debug_dict()

    assert debug["implementation_owner"] == "core.voicing.disposition.spread_voice_leading"
    assert debug["lower_group_motion"] >= 0
    assert debug["upper_group_motion"] >= 0
    assert debug["top_voice_motion"] >= 0
    assert debug["group_gap_change"] >= 0
    assert debug["scored_groupwise_not_total_motion_only"] is True
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
