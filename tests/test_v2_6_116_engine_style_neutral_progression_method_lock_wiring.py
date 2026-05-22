from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_swing_voicing_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as get_ballad_voicing_policy

MILESTONE_ID = "v2_6_116"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_style_neutral_progression_method_lock_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_style_neutral_progression_method_lock_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_116_style_policies_opt_into_style_neutral_method_lock_without_voicing_projection_change() -> None:
    for style, policy in {
        "bossa_nova": get_bossa_voicing_policy(),
        "medium_swing": get_swing_voicing_policy(),
        "jazz_ballad": get_ballad_voicing_policy(),
    }.items():
        metadata = dict(policy.metadata or {})
        assert metadata["progression_voicing_method_lock_policy_version"] == MILESTONE_ID
        assert metadata["progression_voicing_method_lock_policy_enabled"] is True
        assert metadata["progression_voicing_method_lock_policy_target"]["propagated_seed_methods"] == ["drop2", "drop3"]
        assert metadata["progression_voicing_method_lock_policy_target"]["non_propagated_color_methods"] == ["drop2_and_4", "generic_open"]
        assert "projection" not in metadata["progression_voicing_method_lock_policy_contract"].lower() or "without changing voicing projection" in metadata["progression_voicing_method_lock_policy_contract"]


def test_v2_6_116_audit_enables_bossa_and_preserves_medium_swing_method_lock_runtime_wiring() -> None:
    module = _load_script_module()
    bossa = module.generate_style_audit("bossa_nova", module.SPEC_BY_STYLE["bossa_nova"])
    swing = module.generate_style_audit("medium_swing", module.SPEC_BY_STYLE["medium_swing"])

    assert bossa["progression_audit"]["local_functional_pair_count"] > 0
    assert bossa["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] == bossa["progression_audit"]["local_functional_pair_count"]
    assert bossa["progression_audit"]["method_continuity_ratio"] == 1.0
    assert bossa["generic_open_event_count"] == 0

    assert swing["progression_audit"]["local_functional_pair_count"] > 0
    assert swing["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] == swing["progression_audit"]["local_functional_pair_count"]
    assert swing["progression_audit"]["method_continuity_ratio"] == 1.0
    assert swing["generic_open_event_count"] == 0


def test_v2_6_116_ballad_opt_in_does_not_force_open_drop_family_when_ballad_runtime_is_spread() -> None:
    module = _load_script_module()
    ballad = module.generate_style_audit("jazz_ballad", module.SPEC_BY_STYLE["jazz_ballad"])

    assert ballad["ok"] is True
    assert ballad["progression_audit"]["local_functional_pair_count"] > 0
    assert ballad["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] == 0
    assert set(ballad["method_counts"].keys()).isdisjoint(module.DROP_FAMILY_METHODS)


def test_v2_6_116_acceptance_passes_for_style_neutral_method_lock_audit() -> None:
    module = _load_script_module()
    audits = [module.generate_style_audit(style, spec) for style, spec in module.SPEC_BY_STYLE.items()]
    summary = {
        "checkpoint_version": MILESTONE_ID,
        "engine_version_tag": "test",
        "styles": audits,
    }
    summary["global_findings"] = module.build_global_findings(audits)
    acceptance = module.acceptance(summary)

    assert acceptance["passed"] is True
