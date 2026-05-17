from __future__ import annotations

# harness token: test_v2_2_41_spread_groupwise_voice_leading_scorer

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.spread import (
    BASIC_SPREAD_PROJECTION_VERSION,
    GROUPWISE_SPREAD_VOICE_LEADING_VERSION,
    LOWER_GROUP_INVENTORY_VERSION,
    SPREAD_RECIPE_CONTRACT_VERSION,
    UPPER_SOURCE_ADAPTER_VERSION,
    SpreadGroupwiseVoiceLeadingScore,
    SpreadGroupwiseVoiceLeadingWeights,
    project_basic_spread_contract,
    rank_spread_candidates_by_groupwise_voice_leading,
    score_spread_groupwise_voice_leading,
    select_spread_candidate_by_groupwise_voice_leading,
    spread_groupwise_voice_leading_path_debug,
)

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _legal(symbol: str, contract_id: str = "spread_2plus3_contract"):
    return [candidate for candidate in project_basic_spread_contract(symbol, contract_id).candidates if candidate.is_legal]


def test_v2_2_41_version_is_current_while_preserving_subcontract_versions() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert _read("VERSION").strip() == "v2_3_9"
    assert GROUPWISE_SPREAD_VOICE_LEADING_VERSION == "v2_2_41"
    # v2_2_41 adds a scorer; it does not rewrite the existing recipe/projection contracts.
    assert SPREAD_RECIPE_CONTRACT_VERSION == "v2_2_40"
    assert BASIC_SPREAD_PROJECTION_VERSION == "v2_2_40"
    assert LOWER_GROUP_INVENTORY_VERSION == "v2_2_38"
    assert UPPER_SOURCE_ADAPTER_VERSION == "v2_2_39"


def test_groupwise_scorer_exposes_separate_lower_upper_top_gap_span_components() -> None:
    previous = _legal("Dm7")[0]
    current = _legal("G7")[0]
    score = score_spread_groupwise_voice_leading(current, previous)
    assert isinstance(score, SpreadGroupwiseVoiceLeadingScore)
    debug = score.to_debug_dict()
    required = [
        "lower_group_motion",
        "upper_group_motion",
        "top_voice_motion",
        "group_gap_change",
        "span_penalty",
        "register_penalty",
        "weighted_penalty",
        "continuity_score",
        "scored_groupwise_not_total_motion_only",
    ]
    for token in required:
        assert token in debug
    assert debug["scored_groupwise_not_total_motion_only"] is True
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert score.total_motion == score.lower_group_motion + score.upper_group_motion


def test_groupwise_ranking_prefers_lower_group_continuity_when_weighted() -> None:
    previous = _legal("Dm7")[0]
    candidates = _legal("G7")
    weights = SpreadGroupwiseVoiceLeadingWeights(
        lower_group_motion=10.0,
        upper_group_motion=0.0,
        top_voice_motion=0.0,
        group_gap_stability=0.0,
        span_penalty=0.0,
        register_penalty=0.0,
    )
    ranked = rank_spread_candidates_by_groupwise_voice_leading(candidates, previous, weights)
    assert ranked
    min_lower_motion = min(
        score_spread_groupwise_voice_leading(candidate, previous, weights).lower_group_motion
        for candidate in candidates
    )
    assert ranked[0].lower_group_motion == min_lower_motion
    assert ranked[0].weights.lower_group_motion == 10.0


def test_groupwise_selector_and_path_debug_remain_notes_only_runtime_disabled() -> None:
    previous = _legal("Dm7")[0]
    selected = select_spread_candidate_by_groupwise_voice_leading(_legal("G7"), previous)
    assert selected is not None
    assert selected.runtime_enabled is False

    debug = spread_groupwise_voice_leading_path_debug(("Dm7", "G7", "Cmaj7"), contract_id="spread_2plus3_contract")
    assert debug["groupwise_spread_voice_leading_version"] == "v2_2_41"
    assert debug["selected_candidate_count"] == 3
    assert len(debug["selected_lower_group_path"]) == 3
    assert len(debug["selected_upper_group_path"]) == 3
    assert debug["scored_groupwise_not_total_motion_only"] is True
    assert debug["runtime_enabled"] is False
    assert debug["notes_only"] is True
    assert debug["no_expression_or_pedal"] is True
    assert all(score["weighted_penalty"] >= 0 for score in debug["scores"])


def test_groupwise_voice_leading_docs_are_synced() -> None:
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
        "Group-wise Voice-Leading Scorer",
        "GROUPWISE_SPREAD_VOICE_LEADING_VERSION",
        "SpreadGroupwiseVoiceLeadingWeights",
        "SpreadGroupwiseVoiceLeadingScore",
        "score_spread_groupwise_voice_leading",
        "rank_spread_candidates_by_groupwise_voice_leading",
        "select_spread_candidate_by_groupwise_voice_leading",
        "spread_groupwise_voice_leading_path_debug",
        "lower_group_motion",
        "upper_group_motion",
        "top_voice_motion",
        "group_gap_change",
        "runtime_enabled=false",
        "notes-only",
    ]
    for token in required:
        assert token in docs
