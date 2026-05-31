from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.voicing import Disposition, generate_candidates
from jammate_engine.styles.bossa_nova import voicing_policy

MILESTONE_ID = "v2_6_112"
EXPECTED_PARENT_SOURCE = "compact_closed_parent_candidates_for_projection"
ALLOWED_METHODS = {"drop2", "drop3", "drop2_and_4"}


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_voicing_listening_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_voicing_listening_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_112_policy_declares_bossa_voicing_checkpoint_without_behavior_change() -> None:
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})
    checkpoint = dict(metadata.get("bossa_voicing_listening_checkpoint") or {})

    assert checkpoint["version"] == MILESTONE_ID
    assert checkpoint["enabled"] is True
    assert checkpoint["behavior_change"] is False
    assert checkpoint["preferred_disposition"] == "open"
    assert tuple(checkpoint["normal_open_projection_methods"]) == ("drop2", "drop3", "drop2_and_4")
    assert checkpoint["generic_open_role"] == "fallback_or_rescue_only_not_ordinary_runtime"
    assert tuple(checkpoint["ordinary_density_range"]) == (4, 5)
    assert checkpoint["forced_2_or_3_note_voicing"] is False
    assert checkpoint["spread_grouped_voicing"] is False
    assert checkpoint["ordinary_4note_grouping_metadata_retired"] is True
    assert checkpoint["named_open_parent_boundary"] == EXPECTED_PARENT_SOURCE + "_only"
    assert checkpoint["noncompact_parent_silent_fallback_allowed"] is False
    assert checkpoint["no_new_voicing_ability"] is True
    assert checkpoint["no_parallel_selector"] is True


def test_v2_6_112_bossa_candidates_remain_open_drop_family_without_retired_grouping() -> None:
    policy = voicing_policy.get_voicing_policy()
    for symbol in ("Cm7", "Fm7", "Dm7b5", "G7b9", "Ab7", "Dbmaj7"):
        candidates = [candidate for candidate in generate_candidates(symbol, policy) if candidate.disposition == Disposition.OPEN]
        assert candidates
        for candidate in candidates:
            metadata = dict(candidate.metadata or {})
            density_recipe = dict(metadata.get("density_recipe") or {})
            method = metadata.get("active_open_projection_method") or metadata.get("disposition_projection_method")
            assert candidate.density in {4, 5}
            assert method in ALLOWED_METHODS
            assert metadata.get("open_named_projection_parent_source") == EXPECTED_PARENT_SOURCE
            assert metadata.get("open_named_projection_noncompact_parent_fallback_used") is False
            assert metadata.get("open_named_projection_legacy_parent_fallback_used") is False
            assert metadata.get("open_named_projection_silent_fallback_allowed") is False
            assert int(metadata.get("open_named_projection_parent_closed_span") or 0) <= 12
            assert candidate.functional_grouping is None
            assert density_recipe.get("functional_grouping") is None
            assert "1plus3" not in str(candidate.recipe_id)
            assert "2plus2" not in str(candidate.recipe_id)


def test_v2_6_112_static_audit_passes_checkpoint_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["generic_open_candidate_count"] == 0
    assert static["low_density_candidate_count"] == 0
    assert static["fallback_parent_candidate_count"] == 0
    assert static["wrong_parent_source_candidate_count"] == 0
    assert static["silent_fallback_allowed_candidate_count"] == 0
    assert static["parent_closed_span_over_12_candidate_count"] == 0
    assert static["low_cluster_top_gap_candidate_count"] == 0
    assert static["retired_4note_grouping_candidate_count"] == 0


def test_v2_6_112_runtime_blue_bossa_voicing_checkpoint_acceptance() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23112, "slug": "blue_bossa_3x_pytest_v2_6_112"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["non_open_event_count"] == 0
    assert runtime["generic_open_event_count"] == 0
    assert runtime["low_density_event_count"] == 0
    assert runtime["retired_4note_grouping_event_count"] == 0
    assert runtime["fallback_parent_event_count"] == 0
    assert runtime["wrong_parent_source_event_count"] == 0
    assert runtime["parent_closed_span_over_12_count"] == 0
    assert runtime["low_cluster_top_gap_event_count"] == 0
    assert runtime["inspected_bar_bad_event_count"] == 0
    assert acceptance["passed"] is True
