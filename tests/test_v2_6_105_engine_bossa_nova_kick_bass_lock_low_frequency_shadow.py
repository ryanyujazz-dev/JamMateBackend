from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.realization.bass_foundation_realizer import BassFoundationRealizer
from jammate_engine.realization.percussion_realizer import PercussionRealizer
from jammate_engine.styles.bossa_nova import arrangement_policy, bass_foundation_patterns, percussion_patterns
from jammate_engine.styles.registry import get_style

MILESTONE_ID = "v2_6_105"


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "examples" / "scripts" / "generate_engine_bossa_nova_kick_bass_lock_low_frequency_shadow_refinement.py"
    spec = importlib.util.spec_from_file_location("generate_engine_bossa_nova_kick_bass_lock_low_frequency_shadow_refinement", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_bossa_leadsheet() -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": "Tiny Bossa Kick Bass Lock Test",
        "tempo": 140,
        "sections": [
            {
                "id": "A",
                "label": "A",
                "bars": [
                    {"chords": [{"symbol": "Cm7", "beat": 1}]},
                    {"chords": [{"symbol": "F7", "beat": 1}, {"symbol": "Fm7", "beat": 3}]},
                    {"chords": [{"symbol": "Bb7", "beat": 1}]},
                    {"chords": [{"symbol": "Ebmaj7", "beat": 1}]},
                ],
            }
        ],
        "written_form": [{"section": "A"}],
    }


def test_v2_6_105_policy_metadata_declares_kick_bass_lock_boundaries() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_active"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_version"] == MILESTONE_ID
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_behavior_change"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_parallel_selector"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_bar_first_restore"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_new_drum_vocabulary"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_piano_voicing_change"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_core_voicing_change"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_no_api_agent_harmonyos_change"] is True
    assert policy["bossa_nova_kick_bass_lock_and_low_frequency_shadow_tracks"] == ("bass", "drums")


def test_v2_6_105_kick_events_lock_to_bass_root_fifth_without_new_pattern_vocabulary() -> None:
    full = percussion_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    split = percussion_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 0})[0]
    short = percussion_patterns.get_pattern_candidates({"region_duration_beats": 1.0, "region_source_bar_index": 0})[0]

    full_kicks = [event for event in full.events if event.metadata.get("drum") == "kick"]
    split_kicks = [event for event in split.events if event.metadata.get("drum") == "kick"]
    short_kicks = [event for event in short.events if event.metadata.get("drum") == "kick"]

    assert [event.local_beat for event in full_kicks] == [0.0, 2.0]
    assert [event.metadata.get("kick_bass_lock_slot") for event in full_kicks] == ["root_on_1_locked_shadow", "fifth_on_3_locked_shadow"]
    assert [event.metadata.get("kick_locked_to_bass_degree") for event in full_kicks] == ["root", "fifth"]
    assert [event.local_beat for event in split_kicks] == [0.0]
    assert [event.local_beat for event in short_kicks] == [0.0]
    assert all(event.metadata["kick_low_frequency_role"] == "shadow_not_driver" for event in [*full_kicks, *split_kicks, *short_kicks])
    assert all(event.metadata["kick_four_on_floor_driver"] is False for event in [*full_kicks, *split_kicks, *short_kicks])
    assert all(event.metadata["kick_rock_backbeat_driver"] is False for event in [*full_kicks, *split_kicks, *short_kicks])
    assert all(event.metadata["bossa_kick_bass_lock_and_low_frequency_shadow_version"] == MILESTONE_ID for event in [*full_kicks, *split_kicks, *short_kicks])
    forbidden = {"velocity", "duration", "duration_beats", "pedal", "midi_note", "note"}
    assert not any(key in forbidden for event in [*full_kicks, *split_kicks, *short_kicks] for key in event.metadata)


def test_v2_6_105_bass_events_declare_kick_counterpart_without_walking() -> None:
    full = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 4.0, "region_source_bar_index": 0})[0]
    split = bass_foundation_patterns.get_pattern_candidates({"region_duration_beats": 2.0, "region_source_bar_index": 0})[0]

    full_degrees = [event.metadata.get("degree") for event in full.events]
    split_degrees = [event.metadata.get("degree") for event in split.events]
    assert full_degrees == ["root", "fifth"]
    assert split_degrees == ["root"]
    assert [event.metadata.get("bass_kick_lock_expected_kick_slot") for event in full.events] == ["root_on_1_locked_shadow", "fifth_on_3_locked_shadow"]
    assert split.events[0].metadata.get("bass_kick_lock_expected_kick_slot") == "root_on_1_locked_shadow"
    assert all(event.metadata.get("walking_bass") is False for event in [*full.events, *split.events])
    assert all(event.metadata.get("bass_low_frequency_role") == "foundation_that_kick_shadows" for event in [*full.events, *split.events])


def test_v2_6_105_percussion_realizer_keeps_kick_below_bass_shadow_strength() -> None:
    leadsheet = normalize_leadsheet(parse_leadsheet(_tiny_bossa_leadsheet()))
    timeline = expand_form_to_regions(leadsheet, choruses=1)
    style = get_style("bossa_nova")
    history: dict[str, object] = {}
    rng = random.Random(23105)
    bass_events = []
    drum_events = []
    for region in timeline.regions:
        plan = style.plan_region(
            region,
            context={"style_pattern_history": history, "tempo": 140, "rng": rng, "ensemble": {"bass_present": True}},
        )
        bass_events.extend([event for event in plan.events if event.track == "bass"])
        drum_events.extend([event for event in plan.events if event.track == "drums"])

    bass_notes = BassFoundationRealizer().realize(bass_events)
    drum_notes = PercussionRealizer().realize(drum_events)
    kick_pairs = [(event, note) for event, note in zip(drum_events, drum_notes) if event.metadata.get("drum") == "kick"]
    root_kicks = [note.velocity for event, note in kick_pairs if event.metadata.get("kick_locked_to_bass_degree") == "root"]
    fifth_kicks = [note.velocity for event, note in kick_pairs if event.metadata.get("kick_locked_to_bass_degree") == "fifth"]

    assert root_kicks
    assert fifth_kicks
    assert max(root_kicks) < min(note.velocity for note in bass_notes)
    assert max(fifth_kicks) < min(root_kicks)
    assert all(event.metadata.get("kick_bass_lock_timing_intent") == "straight_even_not_swing" for event, _ in kick_pairs)


def test_v2_6_105_static_audit_acceptance_requires_runtime_for_full_pass() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    acceptance = module._acceptance(static, [])

    assert static["checkpoint_version"] == MILESTONE_ID
    assert static["policy_version"] == MILESTONE_ID
    assert static["full_kick_lock_slots"] == ["root_on_1_locked_shadow", "fifth_on_3_locked_shadow"]
    assert static["split_kick_lock_slots"] == ["root_on_1_locked_shadow"]
    assert static["forbidden_pattern_numeric_keys"] == []
    assert acceptance["checks"]["runtime_blue_bossa_kick_bass_lock_passes"] is False
    assert acceptance["passed"] is False


def test_v2_6_105_blue_bossa_runtime_acceptance_contract() -> None:
    module = _load_script_module()
    static = module.build_static_audit()
    runtime = module._generate_runtime_audit({"choruses": 3, "seed": 23105, "slug": "blue_bossa_3x_pytest_v2_6_105"})
    acceptance = module._acceptance(static, [runtime])

    assert runtime["ok"] is True
    assert runtime["kick_lock_coverage_ratio"] == 1.0
    assert runtime["kick_root_events"] > 0
    assert runtime["kick_fifth_events"] > 0
    assert runtime["split_or_short_fifth_kick_events"] == 0
    assert runtime["four_on_floor_driver_events"] == 0
    assert runtime["kick_max_velocity"] < runtime["bass_min_velocity"]
    assert runtime["bass_walking_like_events"] == 0
    assert acceptance["passed"] is True
