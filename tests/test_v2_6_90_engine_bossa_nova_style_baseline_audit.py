from __future__ import annotations

from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style


BASELINE_MILESTONE_ID = "v2_6_90"
CURRENT_BOSSA_PATTERN_VERSION = "v2_6_92"


def test_v2_6_90_baseline_metadata_remains_registered_and_superseded_by_v2_6_91() -> None:
    style = get_style("bossa_nova")
    policy = style.arrangement_policy

    assert policy == arrangement_policy.get_arrangement_policy()
    assert policy["bossa_nova_style_baseline_audit"] is True
    assert policy["bossa_nova_style_baseline_audit_version"] == BASELINE_MILESTONE_ID
    assert policy["bossa_nova_style_baseline_audit_superseded_by"] == CURRENT_BOSSA_PATTERN_VERSION
    assert policy["bossa_nova_non_core_rhythm_cell_vocabulary_active"] is True
    assert policy["bossa_nova_context_archetype_policy_version"] == CURRENT_BOSSA_PATTERN_VERSION


def test_v2_6_90_core_batida_identity_survives_after_non_core_vocabulary_activation() -> None:
    full = comping_patterns.describe_pattern_library({"region_duration_beats": 4.0})
    half = comping_patterns.describe_pattern_library({"region_duration_beats": 2.0})
    full_candidates = list(full["candidates"])
    half_candidates = list(half["candidates"])
    core = [candidate for candidate in full_candidates if candidate["name"] == "bossa_piano_core_batida_1_2_3and"]
    half_region = [candidate for candidate in half_candidates if candidate["name"] == "bossa_piano_half_region_1_2"]
    all_tags = {tag for candidate in [*full_candidates, *half_candidates] for tag in candidate["tags"]}

    assert full["version"] == CURRENT_BOSSA_PATTERN_VERSION
    assert len(core) == 1
    assert core[0]["rhythm_beats"] == [0.0, 1.0, 2.5]
    assert [event["expression_hint"] for event in core[0]["events"]] == ["core_short", "core_short", "core_sustain"]
    assert len(half_region) == 1
    assert half_region[0]["rhythm_beats"] == [0.0, 1.0]
    assert "two_beat_region" in all_tags
    assert "chord_region_first" in all_tags
    assert "two_chord_bar" not in all_tags
    assert "bar_first" not in all_tags
    assert "split_bar" not in all_tags
