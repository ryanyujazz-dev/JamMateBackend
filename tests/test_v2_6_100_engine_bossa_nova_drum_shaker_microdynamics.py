from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.styles.bossa_nova import arrangement_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_100"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_drum_shaker_microdynamics_and_pulse_shape", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Shaker Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "Fm7", "beat": 1}, {"symbol": "Bb7", "beat": 3}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_100_policy_metadata_declares_shaker_microdynamic_boundaries() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_active"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_version"] == MILESTONE_ID
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_behavior_change"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_parallel_selector"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_bar_first_restore"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_piano_bass_voicing_change"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_drum_shaker_microdynamics_and_pulse_shape_tracks"] == ("drums",)


def test_v2_6_100_bossa_shaker_pattern_events_add_semantic_pulse_slots_without_velocity_values() -> None:
    candidate = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "bar_index": 0})[0]
    shaker_events = [event for event in candidate.events if event.metadata.get("drum") == "shaker"]
    slots = [event.metadata.get("shaker_pulse_slot") for event in shaker_events]

    assert candidate.category == "bossa_shaker_cross_stick_light_kick_identity"
    assert len(shaker_events) == 8
    assert slots == [
        "primary_clear",
        "offbeat_light",
        "secondary_mid",
        "offbeat_feather",
        "primary_clear",
        "offbeat_light",
        "secondary_mid",
        "offbeat_feather",
    ]
    assert all(event.metadata["bossa_drum_voice"] == "shaker_time" for event in shaker_events)
    assert all(event.metadata["bossa_drum_voice_family"] == "shaker_time" for event in shaker_events)
    assert all(event.metadata["shaker_microdynamic_profile"] == "bossa_shaker_straight_8th_pulse_shape" for event in shaker_events)
    assert all(event.metadata["bossa_drum_shaker_microdynamics_and_pulse_shape_version"] == MILESTONE_ID for event in shaker_events)
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in shaker_events for key in event.metadata)


def test_v2_6_100_percussion_realizer_applies_shaker_pulse_shape_after_pattern_selection() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=1)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23100)

    drum_events = []
    for region in timeline.regions[:1]:
        plan = style.plan_region(
            region,
            context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}},
        )
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    realized = PercussionRealizer().realize(drum_events)
    shaker_pairs = [(event, note) for event, note in zip(drum_events, realized) if event.metadata.get("drum") == "shaker"]
    velocities_by_slot: dict[str, list[int]] = {}
    for event, note in shaker_pairs:
        velocities_by_slot.setdefault(str(event.metadata.get("shaker_pulse_slot")), []).append(note.velocity)

    assert set(velocities_by_slot) == {"primary_clear", "secondary_mid", "offbeat_light", "offbeat_feather"}
    assert len({velocity for values in velocities_by_slot.values() for velocity in values}) >= 4
    assert min(velocities_by_slot["primary_clear"]) > max(velocities_by_slot["offbeat_feather"])
    assert all(event.metadata.get("shaker_microdynamic_timing_intent") == "straight_even_not_swing" for event, _ in shaker_pairs)


def test_v2_6_100_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_version"] == MILESTONE_ID
    assert static["full_shaker_event_count"] == 8
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["checks"]["runtime_blue_bossa_shaker_microdynamics_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_100_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23100, "slug": "blue_bossa_3x_pytest_v2_6_100"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["planned_shaker_microdynamic_coverage_ratio"] == 1.0
    assert runtime["realized_shaker_velocity_unique_count"] >= 4
    assert runtime["realized_shaker_slot_average_velocity"]["primary_clear"] > runtime["realized_shaker_slot_average_velocity"]["offbeat_feather"]
    assert runtime["drum_swing_or_rock_events"] == 0
    assert runtime["split_region_shaker_overflow_events"] == 0
    assert acceptance["passed"] is True
