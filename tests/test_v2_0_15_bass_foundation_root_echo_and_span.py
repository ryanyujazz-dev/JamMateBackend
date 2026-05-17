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


def _timeline_from_chart(chart: dict):
    return expand_form_to_regions(normalize_leadsheet(parse_leadsheet(chart)), choruses=1)


def test_root_echo_is_post_walking_ornament_not_style_vocabulary() -> None:
    chart = {
        "title": "Root echo smoke",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fmaj7", "beats": 4}]},
        ],
    }
    raw_policy = get_bass_foundation_policy()
    raw_policy.update({"root_echo_probability": 1.0, "root_echo_max_per_region": 1})
    plan = BassFoundationGenerator().generate(
        regions=_timeline_from_chart(chart).regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(raw_policy),
        rng=random.Random(15),
    )
    ornaments = [event for event in plan.events if event.metadata.get("ornament_type") == "current_root_echo"]
    assert ornaments
    assert all(event.metadata.get("bass_foundation_ornament") is True for event in ornaments)
    assert all(event.pattern_id and "::root_echo" in event.pattern_id for event in ornaments)
    assert all(event.metadata["length_profile"] == "short_pickup" for event in ornaments)


def test_root_echo_never_uses_4_and_even_if_policy_mentions_it() -> None:
    chart = {
        "title": "No 4 and echo",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fmaj7", "beats": 4}]},
        ],
    }
    raw_policy = get_bass_foundation_policy()
    raw_policy.update(
        {
            "root_echo_probability": 1.0,
            "root_echo_allowed_upbeats": (0.5, 3.5),
            "root_echo_max_per_region": 2,
        }
    )
    plan = BassFoundationGenerator().generate(
        regions=_timeline_from_chart(chart).regions,
        pattern_source=get_pattern_candidates,
        policy=BassFoundationPolicy.from_dict(raw_policy),
        rng=random.Random(150),
    )
    root_echo_beats = [float(event.local_beat) for event in plan.events if event.metadata.get("ornament_type") == "current_root_echo"]
    assert root_echo_beats
    assert 3.5 not in root_echo_beats


def test_every_chord_region_bass_span_stays_within_one_octave() -> None:
    leadsheet = json.loads((ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json").read_text())
    raw_policy = get_bass_foundation_policy()
    raw_policy.update({"root_echo_probability": 1.0})
    policy = BassFoundationPolicy.from_dict(raw_policy)
    plan = BassFoundationGenerator().generate(
        regions=_timeline_from_chart(leadsheet).regions,
        pattern_source=get_pattern_candidates,
        policy=policy,
        rng=random.Random(1515),
    )
    notes_by_region: dict[str, list[int]] = defaultdict(list)
    for event in plan.events:
        notes_by_region[event.region_id].append(int(event.metadata["resolved_midi_note"]))
    assert notes_by_region
    assert all(max(notes) - min(notes) <= policy.max_region_span for notes in notes_by_region.values() if notes)
    assert all(segment.get("notes") for segment in plan.metadata["segments"])


def test_root_echo_uses_logical_swing_upbeat_and_exact_region_root_note() -> None:
    chart = {
        "title": "Swing root echo",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fmaj7", "beats": 4}]},
        ],
    }
    raw_policy = get_bass_foundation_policy()
    raw_policy.update({"root_echo_probability": 1.0, "root_echo_max_per_region": 2})
    policy = BassFoundationPolicy.from_dict(raw_policy)
    plan = BassFoundationGenerator().generate(
        regions=_timeline_from_chart(chart).regions,
        pattern_source=get_pattern_candidates,
        policy=policy,
        rng=random.Random(1717),
    )
    events_by_region: dict[str, list] = defaultdict(list)
    for event in plan.events:
        events_by_region[event.region_id].append(event)
    ornaments = [event for event in plan.events if event.metadata.get("ornament_type") == "current_root_echo"]
    assert ornaments
    for ornament in ornaments:
        local = float(ornament.local_beat)
        assert abs((local % 1.0) - 0.5) < 0.02
        assert local in {0.5, 2.5}
        root_event = min(events_by_region[ornament.region_id], key=lambda event: float(event.local_beat or 0.0))
        assert int(ornament.metadata["resolved_midi_note"]) == int(root_event.metadata["resolved_midi_note"])
        assert ornament.metadata["root_echo_same_as_region_root"] is True
        assert ornament.metadata["root_echo_swing_upbeat"] is True
        assert ornament.metadata["timing_intent"] == "swing_upbeat"
