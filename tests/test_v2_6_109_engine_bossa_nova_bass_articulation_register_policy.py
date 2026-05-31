from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.realization.bass_foundation_realizer import BassFoundationRealizer
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_109"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_bass_articulation_and_register_policy.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_bass_articulation_and_register_policy", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Bass Articulation Register Test",
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
                    {"chords": [{"symbol": "Dm7b5", "beat": 1}, {"symbol": "G7b9", "beat": 3}]},
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_109_policy_declares_in_place_bass_articulation_register_boundaries() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["bossa_nova_bass_articulation_and_register_policy_active"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_bass_articulation_and_register_policy_behavior_change"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_parallel_selector"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_new_bass_engine"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_bar_first_restore"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_walking_bass"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_piano_pattern_change"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_core_voicing_change"] is True
    assert policy["bossa_nova_bass_articulation_and_register_policy_no_api_agent_harmonyos_change"] is True


def test_v2_6_109_pattern_metadata_adds_semantic_roles_without_concrete_values() -> None:
    candidates = bass_foundation_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "chord_symbol": "Cm7",
            "next_chord_symbol": "F7",
            "bossa_nova_arrangement_arc_intent": {
                "phase": "loop_wave_gentle_lift",
                "runtime_intent": "gentle_transition_lift",
                "full_band_arc_band": "gentle_lift",
            },
        }
    )
    events = [event for candidate in candidates for event in candidate.events]
    policies = {event.metadata.get("bossa_bass_register_policy") for event in events}
    roles = {event.metadata.get("bossa_bass_articulation_role") for event in events}

    assert all(event.metadata.get("bossa_bass_articulation_and_register_policy_version") == MILESTONE_ID for event in events)
    assert "root_stable_floor" in policies
    assert "main_fifth_nearest_with_root_repeat_fallback" in policies
    assert "pickup_fifth_nearest_continuity" in policies
    assert "next_root_light_nearest_continuity" in policies
    assert "light_2and_pickup_short" in roles
    assert "light_4and_next_root_short" in roles
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in events for key in event.metadata)


def test_v2_6_109_realizer_calibrates_pickup_and_nextroot_durations_without_new_engine() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=3)
    style = get_style("bossa_nova")
    rng = random.Random(23110)
    history: dict[str, object] = {}
    bass_events = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}})
        bass_events.extend([event for event in plan.events if event.track == "bass"])

    bass_events = sorted(bass_events, key=lambda event: (event.onset_beat, event.event_id))
    notes = BassFoundationRealizer().realize(bass_events)
    paired = list(zip(bass_events, notes))
    pickups = [note for event, note in paired if event.metadata.get("bossa_bass_articulation_role") == "light_2and_pickup_short"]
    next_roots = [note for event, note in paired if event.metadata.get("bossa_bass_articulation_role") == "light_4and_next_root_short"]
    roots_with_pickup = [note for event, note in paired if event.metadata.get("length_profile") == "bossa_root_with_pickup"]
    fifths_before_next = [note for event, note in paired if event.metadata.get("length_profile") == "bossa_fifth_before_next_root"]

    assert pickups and max(note.duration_beats for note in pickups) <= 0.38
    assert next_roots and max(note.duration_beats for note in next_roots) <= 0.38
    assert roots_with_pickup and max(note.duration_beats for note in roots_with_pickup) <= 1.1
    assert fifths_before_next and min(note.duration_beats for note in fifths_before_next) >= 1.1
    assert all(event.metadata.get("bossa_bass_articulation_and_register_policy_version") == MILESTONE_ID for event in bass_events)


def test_v2_6_109_runtime_keeps_bossa_bass_non_walking_and_smooth() -> None:
    module = _load_script_module()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x_pytest_v2_6_109"})

    assert runtime["ok"] is True
    assert runtime["bass_articulation_version_coverage_ratio"] == 1.0
    assert runtime["pickup_2and_event_count"] > 0
    assert runtime["next_root_4and_event_count"] > 0
    assert runtime["split_short_non_root_events"] == 0
    assert runtime["terminal_next_root_events"] == 0
    assert runtime["walking_like_bass_events"] == 0
    assert runtime["kick_pickup_follow_events"] == 0
    assert runtime["max_consecutive_bass_leap"] <= 12


def test_v2_6_109_blue_bossa_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23110, "slug": "blue_bossa_3x_pytest_acceptance_v2_6_109"})
    acceptance = module._acceptance(static, [runtime])

    assert static["policy_version"] == MILESTONE_ID
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["passed"] is True
