from __future__ import annotations

import importlib.util
import random
from pathlib import Path
from types import SimpleNamespace

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.styles.bossa_nova import arrangement_policy, fill_policy, percussion_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_106"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_light_marker_fill_policy.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_light_marker_fill_policy", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Light Marker Test",
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


def _marker_events(candidate):
    return [event for event in candidate.events if event.metadata.get("bossa_light_marker_fill_policy_active")]


def test_v2_6_106_policy_metadata_declares_light_marker_boundaries() -> None:
    policy = arrangement_policy.get_arrangement_policy()
    marker_policy = fill_policy.get_light_marker_fill_policy()

    assert policy["bossa_nova_light_marker_fill_policy_active"] is True
    assert policy["bossa_nova_light_marker_fill_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_light_marker_fill_policy_no_parallel_selector"] is True
    assert policy["bossa_nova_light_marker_fill_policy_no_bar_first_restore"] is True
    assert policy["bossa_nova_light_marker_fill_policy_no_tom_crash_roll_fill"] is True
    assert policy["bossa_nova_light_marker_fill_policy_no_swing_or_rock_fill"] is True
    assert policy["bossa_nova_light_marker_fill_policy_no_piano_bass_voicing_change"] is True
    assert policy["bossa_nova_light_marker_fill_policy_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_light_marker_fill_policy_tracks"] == ("drums",)
    assert marker_policy["version"] == MILESTONE_ID
    assert marker_policy["pattern_layer_numeric_values"] is False


def test_v2_6_106_light_markers_are_sparse_cross_stick_semantics_not_numeric_pattern_values() -> None:
    phrase = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7})[0]
    lift_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(1, 3)
    lift = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 7, "bossa_nova_arrangement_arc_intent": lift_intent})[0]
    release_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 3)
    release_region = SimpleNamespace(is_last_bar_of_chorus=True, is_last_bar_of_section=True, source_bar_index=7, chorus_index=2, total_choruses=3)
    release = percussion_patterns.get_pattern_candidates({"region": release_region, "region_duration_beats": 2.0, "region_source_bar_index": 7, "bossa_nova_arrangement_arc_intent": release_intent})[0]

    phrase_markers = _marker_events(phrase)
    lift_markers = _marker_events(lift)
    release_markers = _marker_events(release)
    all_markers = phrase_markers + lift_markers + release_markers

    assert [event.metadata.get("bossa_light_marker_fill_policy_kind") for event in phrase_markers] == ["phrase_end_micro"]
    assert {event.metadata.get("bossa_light_marker_fill_policy_kind") for event in lift_markers} == {"turnaround_light"}
    assert {event.metadata.get("bossa_light_marker_fill_policy_kind") for event in release_markers} == {"ending_soft"}
    assert all(event.metadata.get("drum") == "cross_stick" for event in all_markers)
    assert all(event.metadata.get("tom_fill_pattern") is False for event in all_markers)
    assert all(event.metadata.get("crash_fill_pattern") is False for event in all_markers)
    assert all(event.metadata.get("snare_roll_fill_pattern") is False for event in all_markers)
    assert all(event.metadata.get("swing_ride_pattern") is False for event in all_markers)
    assert all(event.metadata.get("rock_backbeat_pattern") is False for event in all_markers)
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in all_markers for key in event.metadata)


def test_v2_6_106_split_regions_suppress_non_terminal_markers_but_allow_terminal_soft_marker() -> None:
    split = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 7})[0]
    release_intent = arrangement_policy.resolve_runtime_arrangement_arc_intent(2, 3)
    release_region = SimpleNamespace(is_last_bar_of_chorus=True, is_last_bar_of_section=True, source_bar_index=7, chorus_index=2, total_choruses=3)
    terminal_split = percussion_patterns.get_pattern_candidates({"region": release_region, "region_duration_beats": 2.0, "region_source_bar_index": 7, "bossa_nova_arrangement_arc_intent": release_intent})[0]

    assert _marker_events(split) == []
    assert [event.metadata.get("bossa_light_marker_fill_policy_slot") for event in _marker_events(terminal_split)] == ["ending_short_region_4and"]


def test_v2_6_106_percussion_realizer_keeps_markers_light() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=3)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23106)
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}})
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    drum_notes = PercussionRealizer().realize(drum_events)
    marker_pairs = [(event, note) for event, note in zip(drum_events, drum_notes) if event.metadata.get("bossa_light_marker_fill_policy_active")]
    assert marker_pairs
    assert max(note.velocity for _, note in marker_pairs) <= 45
    assert min(note.velocity for _, note in marker_pairs) >= 28
    assert all(event.metadata.get("bossa_light_marker_fill_policy_version") == MILESTONE_ID for event, _ in marker_pairs)


def test_v2_6_106_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_version"] == MILESTONE_ID
    assert static["fill_policy_version"] == MILESTONE_ID
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["checks"]["runtime_blue_bossa_light_markers_pass"] is False
    assert acceptance["passed"] is False


def test_v2_6_106_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23106, "slug": "blue_bossa_3x_pytest_v2_6_106"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["marker_event_count"] > 0
    assert runtime["marker_coverage_ratio"] == 1.0
    assert runtime["tom_crash_roll_marker_events"] == 0
    assert runtime["swing_or_rock_marker_events"] == 0
    assert runtime["drum_swing_or_rock_events"] == 0
    assert runtime["marker_max_velocity"] <= 45
    assert acceptance["passed"] is True
