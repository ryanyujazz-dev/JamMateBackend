from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_108"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_bass_pickup_next_root_anticipation.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_bass_pickup_next_root_anticipation", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Bass Pickup Test",
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


def test_v2_6_108_policy_declares_bass_pickup_boundaries() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_active"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_version"] == MILESTONE_ID
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_behavior_change"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_parallel_selector"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_bar_first_restore"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_walking_bass"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_piano_pattern_change"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_core_voicing_change"] is True
    assert policy["bossa_nova_bass_pickup_and_next_root_anticipation_no_api_agent_harmonyos_change"] is True


def test_v2_6_108_full_region_candidate_pool_adds_pickups_without_concrete_values() -> None:
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
    names = {candidate.name for candidate in candidates}
    events = [event for candidate in candidates for event in candidate.events]

    assert "bossa_bass_root_fifth_2bar_A" in names
    assert "bossa_bass_root_2and_fifth_pickup_3_fifth" in names
    assert "bossa_bass_root_fifth_4and_next_root" in names
    assert any(event.local_beat == 1.5 and event.metadata.get("degree") == "fifth" for event in events)
    assert any(event.local_beat == 3.5 and event.metadata.get("degree") == "next_root" for event in events)
    assert all(event.metadata.get("walking_bass") is False for event in events)
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in events for key in event.metadata)


def test_v2_6_108_split_and_short_regions_remain_root_only() -> None:
    split = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "chord_symbol": "Dm7b5", "next_chord_symbol": "G7b9"})[0]
    short = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "chord_symbol": "G7b9", "next_chord_symbol": "Cm7"})[0]

    assert tuple(event.metadata.get("degree") for event in split.events) == ("root",)
    assert tuple(event.metadata.get("degree") for event in short.events) == ("root",)
    assert split.metadata["bossa_bass_pickup_and_next_root_anticipation_no_walking_bass"] is True
    assert short.metadata["bossa_bass_pickup_and_next_root_anticipation_no_walking_bass"] is True


def test_v2_6_108_runtime_tiny_chart_has_pickups_no_walking_and_no_terminal_nextroot() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=3)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23108)
    bass_events = []
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(region, context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}})
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    assert bass_events
    assert all(event.metadata.get("bossa_bass_pickup_and_next_root_anticipation_version") == MILESTONE_ID for event in bass_events)
    assert sum(1 for event in bass_events if event.local_beat == 1.5 and event.metadata.get("degree") == "fifth") > 0
    assert sum(1 for event in bass_events if event.metadata.get("walking_bass") is not False) == 0
    assert sum(1 for event in bass_events if float(event.metadata.get("region_duration_beats", 4.0)) <= 2.25 and event.metadata.get("degree") != "root") == 0
    assert sum(
        1
        for event in bass_events
        if event.metadata.get("degree") == "next_root"
        and event.metadata.get("region_is_last_bar_of_chorus")
        and int(event.metadata.get("region_chorus_index") or 0) >= int(event.metadata.get("region_total_choruses") or 1) - 1
    ) == 0
    assert sum(1 for event in drum_events if event.metadata.get("drum") == "kick" and event.local_beat in {1.5, 3.5}) == 0


def test_v2_6_108_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23108, "slug": "blue_bossa_3x_pytest_v2_6_108"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["pickup_2and_event_count"] > 0
    assert runtime["next_root_4and_event_count"] > 0
    assert runtime["split_short_non_root_events"] == 0
    assert runtime["terminal_next_root_events"] == 0
    assert runtime["kick_pickup_follow_events"] == 0
    assert runtime["walking_like_bass_events"] == 0
    assert acceptance["passed"] is True
