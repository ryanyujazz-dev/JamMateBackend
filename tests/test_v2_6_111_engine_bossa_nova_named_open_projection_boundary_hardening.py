from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.voicing import Disposition, generate_candidates
from jammate_engine.styles.bossa_nova import voicing_policy

MILESTONE_ID = "v2_6_111"
EXPECTED_PARENT_SOURCE = "compact_closed_parent_candidates_for_projection"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_named_open_projection_boundary_hardening_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_named_open_projection_boundary_hardening_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_111_named_open_candidates_do_not_use_silent_noncompact_parent_fallback() -> None:
    policy = voicing_policy.get_voicing_policy()
    for symbol in ("G7b9", "Fm7", "Dm7b5", "Cm7"):
        candidates = [candidate for candidate in generate_candidates(symbol, policy) if candidate.disposition == Disposition.OPEN]
        assert candidates
        for candidate in candidates:
            metadata = dict(candidate.metadata or {})
            method = metadata.get("disposition_projection_method")
            assert method in {"drop2", "drop3", "drop2_and_4"}
            assert metadata.get("open_named_projection_parent_source") == EXPECTED_PARENT_SOURCE
            assert metadata.get("open_named_projection_noncompact_parent_fallback_used") is False
            assert metadata.get("open_named_projection_legacy_parent_fallback_used") is False
            assert metadata.get("open_named_projection_silent_fallback_allowed") is False
            assert int(metadata.get("open_named_projection_parent_closed_span") or 0) <= 12


def test_v2_6_111_static_audit_has_no_fallback_parent_candidates() -> None:
    module = _load_script_module()
    static = module.build_static_audit()

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["fallback_parent_count"] == 0
    assert static["wrong_parent_source_count"] == 0
    assert static["silent_fallback_allowed_count"] == 0
    assert static["bad_parent_span_count"] == 0
    assert static["bad_low_cluster_candidate_count"] == 0
    assert static["no_new_voicing_ability"] is True


def test_v2_6_111_runtime_audit_has_no_fallback_parent_events() -> None:
    module = _load_script_module()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23111, "slug": "blue_bossa_3x_pytest_v2_6_111"})

    assert runtime["ok"] is True
    assert runtime["generic_open_event_count"] == 0
    assert runtime["fallback_parent_event_count"] == 0
    assert runtime["wrong_parent_source_event_count"] == 0
    assert runtime["silent_fallback_allowed_event_count"] == 0
    assert runtime["low_cluster_top_gap_event_count"] == 0
    assert runtime["parent_closed_span_over_12_count"] == 0


def test_v2_6_111_acceptance_passes_for_blue_bossa_runtime() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23111, "slug": "blue_bossa_3x_pytest_acceptance_v2_6_111"})
    acceptance = module._acceptance(static, [runtime])

    assert acceptance["passed"] is True
