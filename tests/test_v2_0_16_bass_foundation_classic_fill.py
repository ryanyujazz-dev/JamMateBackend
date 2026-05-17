from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.generation.bass_foundation import BassFoundationGenerator, BassFoundationPolicy
from jammate_engine.styles.medium_swing.bass_foundation_patterns import get_bass_foundation_policy, get_pattern_candidates

ROOT = Path(__file__).resolve().parents[1]


def _regions(chart: dict):
    return expand_form_to_regions(normalize_leadsheet(parse_leadsheet(chart)), choruses=1).regions


def test_classic_fill_candidates_are_scene_triggered_not_ordinary_walking() -> None:
    ordinary = get_pattern_candidates({"region_duration_beats": 4.0, "chord_symbol": "Cmaj7", "next_chord_symbol": "Cmaj7"})
    assert ordinary
    assert not any(candidate.metadata.get("bass_foundation_fill") for candidate in ordinary)

    scene = get_pattern_candidates(
        {
            "bass_foundation_fill_scene": "two_bar_tonic",
            "region_duration_beats": 8.0,
            "chord_symbol": "Cmaj7",
            "next_chord_symbol": "Fm7",
        }
    )
    assert any(candidate.metadata.get("fill_id") == "CF_TWO_BAR_TONIC_01" for candidate in scene)
    assert all("classic_fill" in candidate.category for candidate in scene)


def test_two_bar_tonic_fill_consumes_two_regions_and_preserves_one_octave_region_span() -> None:
    chart = {
        "title": "Classic fill smoke",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fm7", "beats": 4}]},
        ],
    }
    raw_policy = get_bass_foundation_policy()
    raw_policy.update(
        {
            "classic_fill_two_bar_tonic_probability": 1.0,
            "classic_fill_min_gap_regions": 0,
            "root_echo_probability": 0.0,
        }
    )
    policy = BassFoundationPolicy.from_dict(raw_policy)
    plan = BassFoundationGenerator().generate(
        regions=_regions(chart),
        pattern_source=get_pattern_candidates,
        policy=policy,
        rng=random.Random(16),
    )
    fill_segments = [segment for segment in plan.metadata["segments"] if segment.get("classic_fill_triggered")]
    assert len(fill_segments) == 1
    assert fill_segments[0]["consumed_region_ids"] == ["c0_b0_ch0", "c0_b1_ch0"]
    assert fill_segments[0]["target_region_id"] == "c0_b2_ch0"

    fill_events = [event for event in plan.events if event.metadata.get("bass_foundation_fill")]
    assert len(fill_events) == 9
    assert {event.region_id for event in fill_events} == {"c0_b0_ch0", "c0_b1_ch0"}
    assert any(event.metadata.get("degree") == "#4" for event in fill_events)
    assert any(event.metadata.get("degree") == "classic_connect_nextR" for event in fill_events)
    upbeat_events = [event for event in fill_events if abs((float(event.local_beat or 0.0) % 1.0) - 0.5) < 0.02]
    assert upbeat_events
    assert any(abs(float(event.local_beat or 0.0) - 0.5) < 0.02 for event in fill_events)
    assert any(abs(float(event.onset_beat) - 4.5) < 0.02 for event in fill_events)

    notes_by_region: dict[str, list[int]] = defaultdict(list)
    for event in fill_events:
        notes_by_region[event.region_id].append(int(event.metadata["resolved_midi_note"]))
    assert all(max(notes) - min(notes) <= policy.max_region_span for notes in notes_by_region.values())


def test_attya_seeded_demo_plan_contains_classic_fill_debug_trace() -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    raw_policy = get_bass_foundation_policy()
    raw_policy.update({"classic_fill_min_gap_regions": 0, "classic_fill_two_bar_tonic_probability": 1.0})
    plan = BassFoundationGenerator().generate(
        regions=_regions(leadsheet),
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(raw_policy),
        rng=random.Random(1),
    )
    triggered = [segment for segment in plan.metadata["segments"] if segment.get("classic_fill_triggered")]
    assert triggered
    assert all(segment["classic_fill_scene"] == "two_bar_tonic" for segment in triggered)
    assert all("classic_fill_region_spans" in segment for segment in triggered)
