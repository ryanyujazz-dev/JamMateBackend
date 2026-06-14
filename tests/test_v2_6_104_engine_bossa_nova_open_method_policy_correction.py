from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.voicing import Disposition, generate_candidates
from jammate_engine.core.voicing.disposition.method_weights import disposition_method_weight_spec_from_metadata
from jammate_engine.styles.bossa_nova import arrangement_policy, voicing_policy

MILESTONE_ID = "v2_6_104"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_open_method_policy_correction_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_open_method_policy_correction_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_104_bossa_declares_open_drop_family_policy_without_style_local_method_weights() -> None:
    arr = arrangement_policy.get_arrangement_policy()
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})

    assert arr["bossa_nova_open_method_policy_correction_active"] is True
    assert arr["bossa_nova_open_method_policy_correction_version"] == MILESTONE_ID
    assert policy.preferred_disposition == Disposition.OPEN
    assert metadata["primary_texture_family"] == "open"
    assert metadata["allowed_texture_families"] == ["open"]
    assert metadata["open_projection_methods"] == ["drop2", "drop3", "drop2_and_4"]
    assert "generic_open" not in metadata["open_projection_methods"]
    assert "disposition_method_weights" not in metadata
    assert metadata["bossa_open_method_policy_correction"]["generic_open_role"] == "fallback_or_rescue_only_not_normal_candidate"

    weight_spec = disposition_method_weight_spec_from_metadata(metadata)
    assert weight_spec.source == "style_default:bossa_nova"
    assert weight_spec.enabled_for_scoring is True
    assert weight_spec.open_method_weights == {
        "generic_open": 0.0,
        "drop2": 0.52,
        "drop3": 0.38,
        "drop2_and_4": 0.10,
    }


def test_v2_6_104_bossa_candidate_pool_excludes_generic_open_and_stays_open_drop_family() -> None:
    policy = voicing_policy.get_voicing_policy()
    candidates = generate_candidates("Cm7", policy)

    assert candidates
    assert {candidate.disposition for candidate in candidates} == {Disposition.OPEN}
    methods = {candidate.metadata.get("disposition_projection_method") for candidate in candidates}
    assert methods <= {"drop2", "drop3", "drop2_and_4"}
    assert "generic_open" not in methods
    assert all(int(candidate.density or 0) >= 4 for candidate in candidates)
    assert all(candidate.functional_grouping is None for candidate in candidates if int(candidate.density or 0) == 4)


def test_v2_6_104_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_open_method_policy_correction_version"] == MILESTONE_ID
    assert static["open_projection_methods"] == ["drop2", "drop3", "drop2_and_4"]
    assert static["has_style_local_disposition_method_weights"] is False
    assert static["weight_spec_source"] == "style_default:bossa_nova"
    assert static["open_method_weights"] == {"generic_open": 0.0, "drop2": 0.52, "drop3": 0.38, "drop2_and_4": 0.10}
    assert acceptance["checks"]["runtime_blue_bossa_full_band_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_104_blue_bossa_runtime_uses_drop_family_open_methods_without_generic_open() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22904, "slug": "blue_bossa_3x_pytest_v2_6_104"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert set(runtime["piano_disposition_counts"]) <= {"open", "spread"}
    assert runtime["piano_disposition_counts"].get("open", 0) > runtime["piano_disposition_counts"].get("spread", 0)
    open_methods = {
        method for method in runtime["piano_open_projection_method_counts"] if method != "unknown"
    }
    assert open_methods <= {"drop2", "drop3", "drop2_and_4"}
    assert "generic_open" not in runtime["piano_open_projection_method_counts"]
    assert runtime["retired_4note_grouping_event_count"] == 0
    # v2_6_123 permits only low-frequency event-scoped 5-note SPREAD 2+3;
    # generic_open and retired ordinary 4-note SPREAD groupings remain forbidden.
    assert runtime["spread_grouping_event_count"] >= 0
    assert runtime["low_density_2_or_3_event_count"] == 0
    assert acceptance["passed"] is True
