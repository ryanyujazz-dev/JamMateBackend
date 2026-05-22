from __future__ import annotations

import importlib.util
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.styles.bossa_nova import arrangement_policy
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_97"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_repeat_count_arrangement_arc_policy.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_repeat_count_arrangement_arc_policy", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Arc Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "Fm7", "beat": 1}, {"symbol": "Bb7", "beat": 3}]},
                    {"chords": [{"symbol": "Ebmaj7", "beat": 1}]},
                    {"chords": [{"symbol": "Dø7", "beat": 1}, {"symbol": "G7", "beat": 3}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_97_policy_metadata_declares_bossa_arc_boundaries() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_active"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_behavior_change"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_parallel_selector"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_bar_first_restore"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_expression_numeric_change"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_core_voicing_change"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_not_medium_swing_clone"] is True
    assert policy["bossa_nova_repeat_count_arrangement_arc_policy_repeat_counts_audited"] == (1, 2, 3, 5, 10, 50)


def test_v2_6_97_resolves_repeat_count_arcs_without_three_chorus_hardcoding() -> None:
    one = arrangement_policy.simulate_repeat_count_arrangement_arc(1)
    two = arrangement_policy.simulate_repeat_count_arrangement_arc(2)
    three = arrangement_policy.simulate_repeat_count_arrangement_arc(3)
    five = arrangement_policy.simulate_repeat_count_arrangement_arc(5)
    fifty = arrangement_policy.simulate_repeat_count_arrangement_arc(50)

    assert [item["phase"] for item in one] == ["single_pass_clear_light"]
    assert [item["phase"] for item in two] == ["head_in_core_identity", "final_soft_release"]
    assert [item["phase"] for item in three] == ["head_in_core_identity", "gentle_lift", "final_soft_release"]
    assert [item["phase"] for item in five][:4] == ["head_in_core_identity", "loop_wave_warm_flow", "loop_wave_breath_space", "loop_wave_gentle_lift"]
    assert five[-1]["phase"] == "final_soft_release"
    assert any(item["phase"] == "loop_wave_reset" for item in fifty)
    assert any(item["phase"] == "loop_wave_breath_space" for item in fifty)
    assert fifty[-1]["phase"] == "final_soft_release"
    assert all(item["monotonic_ramp_allowed"] is False for item in fifty)
    assert all(item["not_medium_swing_clone"] is True for item in fifty)
    assert [item["phase"] for item in three] != [item["phase"] for item in five[:3]]


def test_v2_6_97_candidate_multiplier_is_bossa_specific_and_semantic_only() -> None:
    core = {"rhythm_class": "core_batida", "hit_count": 3, "category": "core_batida_identity_anchor"}
    class_b = {"rhythm_class": "class_B", "hit_count": 2, "native_4and": False}
    breath_one_hit = {"rhythm_class": "class_A", "hit_count": 1, "native_4and": False}
    release_busy = {"rhythm_class": "class_A", "hit_count": 3, "native_4and": True}

    reset = arrangement_policy.resolve_runtime_arrangement_arc_intent(0, 8)
    breath = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 8)
    release = arrangement_policy.resolve_runtime_arrangement_arc_intent(7, 8)

    core_mult, core_reasons, core_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(core, reset)
    class_b_mult, class_b_reasons, class_b_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(class_b, reset)
    breath_mult, breath_reasons, breath_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(breath_one_hit, breath)
    release_mult, release_reasons, release_status = arrangement_policy.arrangement_arc_runtime_candidate_multiplier(release_busy, release)

    assert core_mult > 1.0
    assert "core" in " ".join(core_reasons)
    assert core_status == "bossa_arc_core_identity_bonus"
    assert 0.0 < class_b_mult < 0.6
    assert "Class_B" in " ".join(class_b_reasons) or "class_B" in " ".join(class_b_reasons)
    assert "guard" in class_b_status
    assert breath_mult > 1.0
    assert "breath" in " ".join(breath_reasons)
    assert breath_status == "bossa_arc_breath_space"
    assert 0.0 < release_mult < 0.5
    assert "release" in " ".join(release_reasons)
    assert "guard" in release_status


def test_v2_6_97_runtime_stamps_bossa_arc_metadata_on_piano_events() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=5)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}

    phases_seen: set[str] = set()
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 140, "ensemble": {"bass_present": True}})
        for event in plan.events:
            if event.track != "piano":
                continue
            metadata = dict(event.metadata)
            assert metadata["bossa_nova_repeat_count_arrangement_arc_policy_version"] == MILESTONE_ID
            assert metadata["bossa_nova_repeat_count_arrangement_arc_policy_applied"] is True
            assert metadata["bossa_nova_repeat_count_arrangement_arc_not_three_chorus_hardcoded"] is True
            assert metadata["bossa_nova_repeat_count_arrangement_arc_not_medium_swing_clone"] is True
            assert metadata["bossa_nova_repeat_count_arrangement_arc_boundary"] == "style_intent_metadata_and_candidate_weighting_only"
            assert isinstance(metadata["bossa_nova_repeat_count_arrangement_arc_multiplier"], float)
            phases_seen.add(str(metadata["bossa_nova_repeat_count_arrangement_arc_phase"]))

    assert "head_in_core_identity" in phases_seen
    assert "loop_wave_breath_space" in phases_seen
    assert "final_soft_release" in phases_seen


def test_v2_6_97_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["arrangement_policy_version"] == MILESTONE_ID
    assert static["long_loop_50x_has_wave_reset"] is True
    assert static["long_loop_50x_has_breath_space"] is True
    assert static["long_loop_50x_final_phase"] == "final_soft_release"
    assert static["long_loop_50x_monotonic_ramp_allowed"] is False
    assert static["three_chorus_not_hardcoded"] is True
    assert acceptance["checks"]["runtime_blue_bossa_arc_metadata_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_97_blue_bossa_runtime_covers_repeat_arc_metadata() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 22807, "slug": "blue_bossa_3x_pytest_v2_6_97"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["piano_arc_event_count"] > 0
    assert runtime["piano_arc_coverage_ratio"] == 1.0
    assert runtime["piano_arc_phase_counts"]["head_in_core_identity"] > 0
    assert runtime["piano_arc_phase_counts"]["final_soft_release"] > 0
    assert runtime["piano_arc_not_medium_swing_clone_event_count"] == runtime["piano_arc_event_count"]
    assert runtime["piano_arc_not_three_chorus_hardcoded_event_count"] == runtime["piano_arc_event_count"]
    assert acceptance["passed"] is True
