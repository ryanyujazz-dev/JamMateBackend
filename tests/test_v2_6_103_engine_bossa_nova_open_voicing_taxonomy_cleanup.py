from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.voicing import ContentFamily, Disposition, RootSupportPolicy, describe_density_recipe, generate_candidates
from jammate_engine.core.voicing.disposition.method_weights import disposition_method_weight_spec_from_metadata
from jammate_engine.styles.bossa_nova import arrangement_policy, voicing_policy
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_103"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_open_voicing_taxonomy_cleanup_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_open_voicing_taxonomy_cleanup_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_103_bossa_policy_declares_open_main_without_low_density_or_spread_grouping() -> None:
    style = get_style("bossa_nova")
    arr = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})

    assert style.arrangement_policy == arr
    assert arr["bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_version"] == MILESTONE_ID
    assert arr["bossa_nova_open_voicing_main_policy_active"] is True
    assert arr["bossa_nova_retired_ordinary_4note_grouping_metadata"] is True
    assert policy.preferred_disposition == Disposition.OPEN
    assert policy.allowed_dispositions == (Disposition.OPEN, Disposition.CLOSED)
    assert policy.preferred_density == 4
    assert policy.min_density == 4
    assert policy.max_density == 5
    assert metadata["voicing_texture_state_runtime_filtering_enabled"] is True
    assert metadata["primary_texture_family"] == "open"
    assert metadata["allowed_texture_families"] == ["open"]
    assert metadata["bossa_open_voicing_main_policy"]["no_spread_grouping"] is True
    assert metadata["bossa_open_method_policy_correction"]["version"] == "v2_6_104"
    assert metadata["open_projection_methods"] == ["drop2", "drop3", "drop2_and_4"]
    assert "generic_open" not in metadata["open_projection_methods"]
    assert "disposition_method_weights" not in metadata
    weight_spec = disposition_method_weight_spec_from_metadata(metadata)
    assert weight_spec.source == "style_default:bossa_nova"
    assert weight_spec.open_method_weights == {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10}


def test_v2_6_103_ordinary_four_note_density_recipe_no_longer_emits_1plus3_or_2plus2_grouping() -> None:
    rooted = describe_density_recipe(
        ("R", "3", "5", "b7"),
        content_family=ContentFamily.SEVENTH_BASIC,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
    )
    rootless = describe_density_recipe(
        ("3", "5", "b7", "9"),
        content_family=ContentFamily.ROOTLESS_A,
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
    )

    assert rooted.density == 4
    assert rooted.functional_grouping is None
    assert rooted.group_roles == ()
    assert rooted.recipe_id == "d4__unGrouped__seventh_chord_basic__rootless_allowed"
    assert rootless.density == 4
    assert rootless.functional_grouping is None
    assert rootless.group_roles == ()
    assert rootless.recipe_id == "d4__unGrouped__rootless_A__rootless_allowed"


def test_v2_6_103_bossa_candidate_pool_filters_to_open_and_has_no_ordinary_4note_grouping_metadata() -> None:
    policy = voicing_policy.get_voicing_policy()
    candidates = generate_candidates("Cm7", policy)

    assert candidates
    assert {candidate.disposition for candidate in candidates} == {Disposition.OPEN}
    methods = {candidate.metadata.get("disposition_projection_method") for candidate in candidates}
    assert methods <= {"drop2", "drop3", "drop2_and_4"}
    assert "generic_open" not in methods
    assert all(int(candidate.density or 0) >= 4 for candidate in candidates)
    assert all(candidate.functional_grouping is None for candidate in candidates if int(candidate.density or 0) == 4)
    assert all(candidate.recipe_id and "1plus3" not in candidate.recipe_id and "2plus2" not in candidate.recipe_id for candidate in candidates)
    assert {candidate.metadata.get("voicing_texture_state_runtime_filter", {}).get("effective_dispositions", [None])[0] for candidate in candidates} == {"open"}


def test_v2_6_103_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["preferred_disposition"] == "open"
    assert static["primary_texture_family"] == "open"
    assert static["four_note_functional_grouping"] is None
    assert static["rootless_four_note_functional_grouping"] is None
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_103_blue_bossa_runtime_uses_open_and_no_retired_4note_grouping_metadata() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22803, "slug": "blue_bossa_3x_pytest_v2_6_103"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["note_events_by_track"]["piano"] > 0
    assert runtime["note_events_by_track"]["bass"] > 0
    assert runtime["note_events_by_track"]["drums"] > 0
    assert set(runtime["piano_disposition_counts"]) == {"open"}
    assert set(runtime["piano_open_projection_method_counts"]) <= {"drop2", "drop3", "drop2_and_4"}
    assert "generic_open" not in runtime["piano_open_projection_method_counts"]
    assert runtime["retired_4note_grouping_event_count"] == 0
    assert runtime["spread_grouping_event_count"] == 0
    assert runtime["low_density_2_or_3_event_count"] == 0
    assert "1+3" not in runtime["piano_functional_grouping_counts"]
    assert "2+2" not in runtime["piano_functional_grouping_counts"]
    assert acceptance["passed"] is True
