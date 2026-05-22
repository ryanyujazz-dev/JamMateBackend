from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.styles.bossa_nova import voicing_policy

MILESTONE_ID = "v2_6_114"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_high_color_harmonic_expansion_policy.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_high_color_harmonic_expansion_policy", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_6_114_bossa_policy_declares_high_color_expansion_without_voicing_change() -> None:
    policy = voicing_policy.get_voicing_policy()
    metadata = dict(policy.metadata or {})
    high = dict(metadata.get("bossa_high_color_harmonic_expansion_policy") or {})

    assert high["version"] == MILESTONE_ID
    assert high["enabled_when_harmonic_expansion_enabled"] is True
    assert high["no_core_voicing_change"] is True
    assert high["no_projection_or_selector_change"] is True
    assert high["expanded_color_target_ratio"] == 0.80
    assert set(metadata["open_projection_methods"]) == {"drop2", "drop3", "drop2_and_4"}
    assert policy.min_density == 4
    assert policy.max_density == 5
    assert "b13" not in tuple(policy.low_priority_degrees or ())


def test_v2_6_114_static_audit_has_bossa_high_color_source_weights() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    weights = static["source_weights_harmonic_expansion"]

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_has_high_color_metadata"] is True
    assert weights["third_fifth_seventh_ninth"] >= 0.40
    assert weights["third_thirteenth_seventh_ninth"] >= 0.35
    assert weights["third_seventh_altered_color_a_altered_color_b"] >= 0.30
    assert "b13" not in static["low_priority_degrees"]


def test_v2_6_114_runtime_expanded_blue_bossa_uses_high_color_without_voicing_regression() -> None:
    module = _load_script_module()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23114, "slug": "blue_bossa_3x_pytest_v2_6_114"})

    assert runtime["ok"] is True
    assert runtime["harmonic_expansion_enabled"] is True
    assert runtime["color_policy_mode"] == "style_safe_extensions"
    assert runtime["high_color_ratio"] >= 0.75
    assert runtime["minor_cadence_dominant_flat13_ratio"] >= 0.80
    assert runtime["source_containing_ninth_count"] > 0
    assert runtime["source_containing_flat13_count"] > 0
    assert runtime["generic_open_event_count"] == 0
    assert runtime["low_density_event_count"] == 0
    assert runtime["non_drop_family_event_count"] == 0


def test_v2_6_114_acceptance_passes_for_generated_expanded_demo() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23114, "slug": "blue_bossa_3x_pytest_acceptance_v2_6_114"})
    acceptance = module._acceptance(static, [runtime])

    assert acceptance["passed"] is True
