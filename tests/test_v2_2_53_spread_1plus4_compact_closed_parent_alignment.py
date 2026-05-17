# harness token: test_v2_2_53_spread_1plus4_compact_closed_parent_alignment

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.disposition.closed import compact_closed_parent_candidates_for_projection
from jammate_engine.core.voicing.disposition.spread import (
    SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION,
    project_basic_spread_candidates,
)
from jammate_engine.core.voicing.policy import VoicingPolicy


def _one_plus_four_candidates(chord_symbol: str):
    result = project_basic_spread_candidates(
        chord_symbol,
        contract_ids=("spread_1plus4_contract",),
        max_upper_options=8,
    )[0]
    return result.candidates


def test_engine_version_bumped_for_v2_2_53() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION == "v2_2_53"


def test_closed_layer_supplies_compact_parent_candidates_for_extensions() -> None:
    policy = VoicingPolicy(
        register_low=55,
        register_high=84,
        comfort_register_low=55,
        comfort_register_high=84,
        top_voice_low=55,
        top_voice_high=84,
        max_voicing_span=24,
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
        },
    )
    parents = compact_closed_parent_candidates_for_projection(
        0,
        [("R", 0), ("3", 4), ("5", 7), ("9", 14)],
        policy,
    )
    assert parents
    assert all(len(parent) == 4 for parent in parents)
    assert all(max(note for _, note in parent) - min(note for _, note in parent) <= 12 for parent in parents)
    assert all({degree for degree, _ in parent} == {"R", "3", "5", "9"} for parent in parents)


def test_spread_1plus4_upper_drop_uses_compact_closed_parent_not_oriented_extension_stack() -> None:
    candidates = _one_plus_four_candidates("Cmaj9")
    explicit_nine = [candidate for candidate in candidates if "9" in candidate.upper_source.degree_names]
    assert explicit_nine
    for candidate in explicit_nine:
        metadata = candidate.upper_projection_metadata
        assert candidate.recipe_contract.recipe_id == "spread_1plus4_contract"
        assert candidate.upper_projection_method in {"drop2", "drop3"}
        assert metadata["spread_upper_projection_uses_drop_family_resource"] is True
        assert metadata["spread_upper_projection_resource_owner"] == "core.voicing.disposition.open"
        assert metadata["spread_upper_parent_construction_owner"] == "core.voicing.disposition.closed.compact_closed_parent_candidates_for_projection"
        assert metadata["spread_upper_uses_compact_closed_parent_candidates"] is True
        assert metadata["spread_upper_oriented_stack_parent_reuse_allowed"] is False
        assert metadata["open_named_projection_parent_closed_span"] <= 12
        assert metadata["spread_upper_compact_parent_max_span"] <= 12
        assert max(candidate.upper_notes) - min(candidate.upper_notes) <= 24


def test_spread_1plus4_altered_dominant_parent_stays_compact_before_drop() -> None:
    candidates = _one_plus_four_candidates("G7b9")
    assert candidates
    for candidate in candidates:
        metadata = candidate.upper_projection_metadata
        assert "b9" in candidate.upper_source.degree_names
        assert metadata["spread_upper_uses_compact_closed_parent_candidates"] is True
        assert metadata["open_named_projection_parent_closed_span"] <= 12
        assert metadata["spread_upper_compact_parent_max_span"] <= 12
        assert max(candidate.upper_notes) - min(candidate.upper_notes) <= 24
