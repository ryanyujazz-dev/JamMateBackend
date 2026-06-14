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

MILESTONE_ID = "v2_6_101"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_cross_stick_phrase_local_contour_refinement.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_cross_stick_phrase_local_contour_refinement", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Cross Stick Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "F7", "beat": 1}]},
                    {"chords": [{"symbol": "Fm7", "beat": 1}, {"symbol": "Bb7", "beat": 3}]},
                    {"chords": [{"symbol": "Ebmaj7", "beat": 1}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_101_policy_metadata_declares_cross_stick_boundaries() -> None:
    style = get_style("bossa_nova")
    policy = arrangement_policy.get_arrangement_policy()

    assert style.arrangement_policy == policy
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_active"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_version"] == MILESTONE_ID
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_behavior_change"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_no_parallel_selector"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_no_bar_first_restore"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_no_new_pattern_vocabulary"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_no_piano_bass_voicing_change"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_drum_cross_stick_phrase_local_contour_tracks"] == ("drums",)


def test_v2_6_101_cross_stick_events_use_phrase_local_slots_without_velocity_values() -> None:
    candidate_a = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    candidate_b = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 1})[0]
    cross_a = [event for event in candidate_a.events if event.metadata.get("drum") == "cross_stick"]
    cross_b = [event for event in candidate_b.events if event.metadata.get("drum") == "cross_stick"]

    assert [event.local_beat for event in cross_a] == [0.0, 1.5, 3.0]
    assert [event.metadata.get("cross_stick_phrase_slot") for event in cross_a] == [
        "A_beat1_phrase_anchor",
        "A_2and_syncopated_answer",
        "A_beat4_phrase_tail",
    ]
    assert [event.local_beat for event in cross_b] == [1.0, 2.5]
    assert [event.metadata.get("cross_stick_phrase_slot") for event in cross_b] == [
        "B_beat2_response_anchor",
        "B_3and_light_answer",
    ]
    assert all(event.metadata["bossa_drum_cross_stick_phrase_local_contour_version"] == MILESTONE_ID for event in [*cross_a, *cross_b])
    assert all(event.metadata["cross_stick_contour_timing_intent"] == "straight_even_not_swing" for event in [*cross_a, *cross_b])
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in [*cross_a, *cross_b] for key in event.metadata)


def test_v2_6_101_arc_aware_light_subtraction_removes_forward_tail_in_breath_and_release() -> None:
    breath_a = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 2,
            "bossa_nova_arrangement_arc_intent": {"phase": "loop_wave_breath_space", "piano_comping_runtime_intent": "breath_space"},
        }
    )[0]
    release_a = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 0,
            "bossa_nova_arrangement_arc_intent": {"phase": "final_soft_release", "piano_comping_runtime_intent": "settled_release"},
        }
    )[0]
    release_b = percussion_patterns.get_pattern_candidates(
        {
            "region_duration_beats": 4.0,
            "region_source_bar_index": 1,
            "bossa_nova_arrangement_arc_intent": {"phase": "final_soft_release", "piano_comping_runtime_intent": "settled_release"},
        }
    )[0]

    breath_slots = [event.metadata.get("cross_stick_phrase_slot") for event in breath_a.events if event.metadata.get("drum") == "cross_stick"]
    release_a_slots = [event.metadata.get("cross_stick_phrase_slot") for event in release_a.events if event.metadata.get("drum") == "cross_stick"]
    release_b_slots = [event.metadata.get("cross_stick_phrase_slot") for event in release_b.events if event.metadata.get("drum") == "cross_stick"]

    assert "A_beat4_phrase_tail" not in breath_slots
    assert "A_beat4_phrase_tail" not in release_a_slots
    assert "B_3and_light_answer" not in release_b_slots
    assert release_a_slots == ["A_beat1_phrase_anchor", "A_2and_syncopated_answer"]
    assert release_b_slots == ["B_beat2_response_anchor"]


def test_v2_6_101_percussion_realizer_applies_cross_stick_contour_after_selection() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=1)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23101)

    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}},
        )
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    realized = PercussionRealizer().realize(drum_events)
    cross_pairs = [(event, note) for event, note in zip(drum_events, realized) if event.metadata.get("drum") == "cross_stick"]
    velocities_by_slot: dict[str, list[int]] = {}
    for event, note in cross_pairs:
        velocities_by_slot.setdefault(str(event.metadata.get("cross_stick_phrase_slot")), []).append(note.velocity)

    assert {event.metadata.get("cross_stick_phrase_pattern") for event, _ in cross_pairs} >= {"A", "B"}
    assert "A_beat1_phrase_anchor" in velocities_by_slot
    assert "A_2and_syncopated_answer" in velocities_by_slot
    assert min(velocities_by_slot["A_beat1_phrase_anchor"]) > max(velocities_by_slot["A_2and_syncopated_answer"])
    assert all(event.metadata.get("cross_stick_contour_timing_intent") == "straight_even_not_swing" for event, _ in cross_pairs)


def test_v2_6_101_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_version"] == MILESTONE_ID
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["checks"]["runtime_blue_bossa_cross_stick_contour_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_101_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23101, "slug": "blue_bossa_3x_pytest_v2_6_101"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["planned_cross_stick_contour_coverage_ratio"] == 1.0
    assert runtime["cross_stick_phrase_patterns_present"] == ["A", "B", "split"]
    assert runtime["breath_A_tail_push_events"] == 0
    assert runtime["release_tail_push_events"] == 0
    assert runtime["drum_swing_or_rock_events"] == 0
    assert acceptance["passed"] is True
