from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.styles.bossa_nova import arrangement_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_107"
COMPLETED = ("v2_6_100", "v2_6_101", "v2_6_105", "v2_6_106")


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_drum_baseline_checkpoint.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_drum_baseline_checkpoint", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Drum Baseline Checkpoint Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "F7", "beat": 1}]},
                    {"chords": [{"symbol": "Bb7", "beat": 1}]},
                    {"chords": [{"symbol": "Ebmaj7", "beat": 1}]},
                    {"chords": [{"symbol": "Abmaj7", "beat": 1}]},
                    {"chords": [{"symbol": "Dm7b5", "beat": 1}]},
                    {"chords": [{"symbol": "G7b9", "beat": 1}]},
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_107_policy_metadata_declares_drum_checkpoint_boundaries() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["bossa_nova_drum_baseline_checkpoint_active"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_version"] == MILESTONE_ID
    assert policy["bossa_nova_drum_baseline_checkpoint_behavior_change"] is False
    assert policy["bossa_nova_drum_baseline_checkpoint_no_parallel_selector"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_no_bar_first_restore"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_no_new_drum_vocabulary"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_no_piano_bass_voicing_change"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_no_core_voicing_change"] is True
    assert policy["bossa_nova_drum_baseline_checkpoint_no_api_agent_harmonyos_change"] is True
    assert tuple(policy["bossa_nova_drum_baseline_checkpoint_completed_versions"]) == COMPLETED


def test_v2_6_107_percussion_candidate_stamps_checkpoint_without_new_behavior() -> None:
    candidate = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7})[0]
    drum_events = list(candidate.events)

    assert candidate.metadata["bossa_drum_baseline_checkpoint_active"] is True
    assert candidate.metadata["bossa_drum_baseline_checkpoint_version"] == MILESTONE_ID
    assert candidate.metadata["bossa_drum_baseline_checkpoint_behavior_change"] is False
    assert tuple(candidate.metadata["bossa_drum_baseline_checkpoint_completed_versions"]) == COMPLETED
    assert "drum_baseline_checkpoint" in candidate.tags
    assert drum_events
    assert all(event.metadata.get("bossa_drum_baseline_checkpoint_active") is True for event in drum_events)
    assert all(event.metadata.get("bossa_drum_baseline_checkpoint_version") == MILESTONE_ID for event in drum_events)
    assert all(event.metadata.get("bossa_drum_baseline_checkpoint_behavior_change") is False for event in drum_events)
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in drum_events for key in event.metadata)


def test_v2_6_107_runtime_blue_bossa_drum_layers_are_all_covered() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=3)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23107)
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}})
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    assert drum_events
    assert all(event.metadata.get("bossa_drum_baseline_checkpoint_version") == MILESTONE_ID for event in drum_events)
    assert sum(1 for event in drum_events if event.metadata.get("shaker_microdynamic_enabled")) > 0
    assert sum(1 for event in drum_events if event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_active")) > 0
    assert sum(1 for event in drum_events if event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_active")) > 0
    assert sum(1 for event in drum_events if event.metadata.get("bossa_light_marker_fill_policy_active")) > 0
    assert sum(1 for event in drum_events if event.metadata.get("swing_ride_pattern") is not False or event.metadata.get("rock_backbeat_pattern") is not False) == 0


def test_v2_6_107_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_version"] == MILESTONE_ID
    assert static["candidate_version"] == MILESTONE_ID
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["checks"]["runtime_blue_bossa_drum_checkpoint_pass"] is False
    assert acceptance["passed"] is False


def test_v2_6_107_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23107, "slug": "blue_bossa_3x_pytest_v2_6_107"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["checkpoint_coverage_ratio"] == 1.0
    assert runtime["shaker_microdynamic_event_count"] > 0
    assert runtime["cross_stick_contour_event_count"] > 0
    assert runtime["kick_bass_lock_event_count"] > 0
    assert runtime["light_marker_event_count"] > 0
    assert runtime["drum_swing_or_rock_events"] == 0
    assert runtime["tom_crash_roll_marker_events"] == 0
    assert acceptance["passed"] is True
