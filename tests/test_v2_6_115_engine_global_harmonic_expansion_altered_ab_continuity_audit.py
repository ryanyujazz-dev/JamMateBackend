from __future__ import annotations

import importlib.util
from pathlib import Path

MILESTONE_ID = "v2_6_115"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_global_harmonic_expansion_altered_ab_continuity_audit.py"
    spec = importlib.util.spec_from_file_location("generate_engine_global_harmonic_expansion_altered_ab_continuity_audit", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_115_global_audit_runs_all_three_styles_with_expansion_and_altered() -> None:
    module = _load_script_module()
    audits = [module.generate_style_audit(style, spec) for style, spec in module.SPEC_BY_STYLE.items()]
    findings = module.build_global_findings(audits)

    assert {audit["style"] for audit in audits} == {"bossa_nova", "medium_swing", "jazz_ballad"}
    assert all(audit["ok"] for audit in audits)
    assert all(audit["harmonic_expansion_enabled"] for audit in audits)
    assert all(audit["color_policy_mode"] == "altered_dominant" for audit in audits)
    assert findings["all_runtime_ok"] is True


def test_v2_6_115_audit_is_superseded_by_v2_6_116_style_neutral_method_lock_wiring() -> None:
    module = _load_script_module()
    bossa = module.generate_style_audit("bossa_nova", module.SPEC_BY_STYLE["bossa_nova"])
    swing = module.generate_style_audit("medium_swing", module.SPEC_BY_STYLE["medium_swing"])
    ballad = module.generate_style_audit("jazz_ballad", module.SPEC_BY_STYLE["jazz_ballad"])
    findings = module.build_global_findings([bossa, swing, ballad])

    assert "medium_swing" in findings["styles_with_method_lock_wiring_pairs"]
    assert "bossa_nova" in findings["styles_with_method_lock_wiring_pairs"]
    assert bossa["progression_audit"]["local_functional_pair_count"] > 0
    assert bossa["progression_audit"]["method_lock_runtime_wiring_enabled_pair_count"] == bossa["progression_audit"]["local_functional_pair_count"]
    # Ballad currently remains SPREAD-dominant in this audit, so the style-neutral
    # policy is enabled but no open drop-family method-lock scope is forced.
    assert "jazz_ballad" in findings["styles_missing_method_lock_wiring_pairs"]


def test_v2_6_115_audit_detects_ab_metadata_and_allows_later_orientation_wiring_supersession() -> None:
    module = _load_script_module()
    bossa = module.generate_style_audit("bossa_nova", module.SPEC_BY_STYLE["bossa_nova"])
    swing = module.generate_style_audit("medium_swing", module.SPEC_BY_STYLE["medium_swing"])
    findings = module.build_global_findings([bossa, swing])

    assert bossa["ab_eligible_event_count"] > 0
    assert bossa["altered_source_event_count"] > 0
    assert bossa["altered_source_without_ab_metadata_count"] == 0
    assert isinstance(findings["styles_missing_ab_rotation_filter_pairs"], list)
    assert set(findings["styles_with_ab_rotation_filter_pairs"]).issubset({"bossa_nova", "medium_swing"})


def test_v2_6_115_acceptance_passes_for_global_audit() -> None:
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
