from __future__ import annotations

import importlib.util
import random
from collections import Counter
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.styles.bossa_nova import arrangement_policy
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_98"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_full_band_arrangement_arc_listening_refinement.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_full_band_arrangement_arc_listening_refinement", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Full-Band Arc Test",
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


def test_v2_6_98_policy_metadata_declares_full_band_refinement_boundaries() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_active"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_version"] == MILESTONE_ID
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_behavior_change"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_no_parallel_selector"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_no_bar_first_restore"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_no_core_voicing_change"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_full_band_arrangement_arc_listening_refinement_tracks"] == ("piano", "bass", "drums")


def test_v2_6_98_arc_refinement_maps_breath_lift_release_to_semantic_dynamics() -> None:
    breath = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 5)
    lift = arrangement_policy.resolve_runtime_arrangement_arc_intent(3, 5)
    release = arrangement_policy.resolve_runtime_arrangement_arc_intent(4, 5)

    breath_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(breath)
    lift_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(lift)
    release_ref = arrangement_policy.resolve_full_band_arrangement_arc_listening_refinement(release)

    assert breath_ref["version"] == MILESTONE_ID
    assert breath_ref["full_band_arc_band"] == "breath_space"
    assert breath_ref["bass_root_dynamic_profile"] == "bossa_root_soft"
    assert breath_ref["drum_shaker_dynamic_profile"] == "shaker_breath"

    assert lift_ref["full_band_arc_band"] == "gentle_lift"
    assert lift_ref["bass_root_dynamic_profile"] == "bossa_root_lift"
    assert lift_ref["drum_cross_main_dynamic_profile"] == "bossa_cross_lift"

    assert release_ref["full_band_arc_band"] == "soft_release"
    assert release_ref["bass_root_dynamic_profile"] == "bossa_root_release"
    assert release_ref["drum_shaker_dynamic_profile"] == "shaker_release"
    assert release_ref["no_parallel_selector"] is True


def test_v2_6_98_runtime_stamps_piano_bass_and_drums_with_full_band_arc_metadata() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=5)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(2298)

    track_events: dict[str, list] = {"piano": [], "bass": [], "drums": []}
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}},
        )
        for event in plan.events:
            if event.track in track_events:
                track_events[event.track].append(event)

    for track, events in track_events.items():
        assert events, track
        assert all(event.metadata.get("bossa_full_band_arrangement_arc_listening_refinement_version") == MILESTONE_ID for event in events), track
        assert all(event.metadata.get("bossa_full_band_arrangement_arc_listening_refinement_active") is True for event in events), track

    bass_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in track_events["bass"])
    drum_profiles = Counter(str(event.metadata.get("dynamic_profile")) for event in track_events["drums"])
    bass_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in track_events["bass"])
    drum_bands = Counter(str(event.metadata.get("bossa_full_band_arrangement_arc_band")) for event in track_events["drums"])

    assert bass_bands["breath_space"] > 0
    assert bass_bands["gentle_lift"] > 0
    assert bass_bands["soft_release"] > 0
    assert drum_bands["breath_space"] > 0
    assert drum_bands["gentle_lift"] > 0
    assert drum_bands["soft_release"] > 0

    assert bass_profiles["bossa_root_soft"] > 0
    assert bass_profiles["bossa_root_lift"] > 0
    assert bass_profiles["bossa_root_release"] > 0
    assert drum_profiles["shaker_breath"] > 0
    assert drum_profiles["bossa_cross_lift"] > 0
    assert drum_profiles["shaker_release"] > 0

    assert all(event.metadata.get("walking_bass") is False for event in track_events["bass"])
    assert all(event.metadata.get("drum_identity") == "shaker_cross_stick_light_kick" for event in track_events["drums"])
    assert all(event.metadata.get("swing_ride_pattern") is False for event in track_events["drums"])
    assert all(event.metadata.get("rock_backbeat_pattern") is False for event in track_events["drums"])


def test_v2_6_98_static_audit_and_mock_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["full_band_refinement_policy_version"] == MILESTONE_ID
    assert static["breath_refinement"]["full_band_arc_band"] == "breath_space"
    assert static["lift_refinement"]["full_band_arc_band"] == "gentle_lift"
    assert static["release_refinement"]["full_band_arc_band"] == "soft_release"
    assert acceptance["checks"]["runtime_blue_bossa_full_band_arc_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_98_blue_bossa_runtime_covers_full_band_arc_metadata() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 5, "seed": 22985, "slug": "blue_bossa_5x_pytest_v2_6_98"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["piano_full_band_arc_coverage_ratio"] == 1.0
    assert runtime["bass_full_band_arc_coverage_ratio"] == 1.0
    assert runtime["drums_full_band_arc_coverage_ratio"] == 1.0
    assert runtime["bass_walking_like_events"] == 0
    assert runtime["drum_swing_or_rock_events"] == 0
    assert runtime["bass_dynamic_profile_counts"].get("bossa_root_soft", 0) > 0
    assert runtime["bass_dynamic_profile_counts"].get("bossa_root_lift", 0) > 0
    assert runtime["bass_dynamic_profile_counts"].get("bossa_root_release", 0) > 0
    assert runtime["drum_dynamic_profile_counts"].get("shaker_breath", 0) > 0
    assert runtime["drum_dynamic_profile_counts"].get("bossa_cross_lift", 0) > 0
    assert runtime["drum_dynamic_profile_counts"].get("shaker_release", 0) > 0
    assert acceptance["passed"] is True
