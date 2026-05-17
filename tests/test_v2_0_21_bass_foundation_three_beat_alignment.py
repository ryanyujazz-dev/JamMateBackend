from __future__ import annotations

import random

from jammate_engine.core.form.form_expander import expand_form_to_regions
from jammate_engine.core.leadsheet.normalization import normalize_leadsheet
from jammate_engine.core.leadsheet.parser import parse_leadsheet
from jammate_engine.generation.bass_foundation import BassFoundationGenerator, BassFoundationPolicy
from jammate_engine.styles.medium_swing.bass_foundation_patterns import get_bass_foundation_policy, get_pattern_candidates


def test_full_bar_candidate_pool_uses_old_three_beat_skeletons_only() -> None:
    candidates = get_pattern_candidates({
        "region_duration_beats": 4.0,
        "chord_symbol": "Dm7",
        "next_chord_symbol": "G7",
    })
    skeleton_ids = [candidate.metadata.get("skeleton_id", "") for candidate in candidates]

    assert len(candidates) == 22
    assert all(str(skeleton_id).startswith(("C", "S")) for skeleton_id in skeleton_ids)
    assert not any("2to5" in str(skeleton_id) or "5to1" in str(skeleton_id) for skeleton_id in skeleton_ids)


def test_medium_swing_policy_restores_old_connector_and_lane_instance_rules() -> None:
    policy = get_bass_foundation_policy()

    assert policy["connector_family_weights"] == {
        "scale_near_nextR": 40.0,
        "approach_nextR": 40.0,
        "dominant_connection": 10.0,
    }
    assert policy["lane_instance_selection"] == "legacy_random"


def test_repeated_root_start_keeps_exact_same_root_note() -> None:
    chart = {
        "title": "Repeated root exactness",
        "key": "C",
        "bars": [
            {"chords": [{"symbol": "Cmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Fmaj7", "beats": 4}]},
            {"chords": [{"symbol": "Bbmaj7", "beats": 4}]},
        ],
    }
    timeline = expand_form_to_regions(normalize_leadsheet(parse_leadsheet(chart)), choruses=1)
    policy = BassFoundationPolicy.from_dict(get_bass_foundation_policy())

    # Search a range of deterministic seeds and assert every selected repeated-root
    # skeleton uses the exact same MIDI note on beats 1 and 2. This guards the
    # old-engine rule: R-R-starting patterns are same-note repeats, not octave jumps.
    seen_repeated_root = False
    for seed in range(80):
        plan = BassFoundationGenerator().generate(
            regions=timeline.regions,
            pattern_source=get_pattern_candidates,
            policy=policy,
            rng=random.Random(seed),
        )
        for segment in plan.metadata["segments"]:
            if segment.get("repeated_root_start"):
                seen_repeated_root = True
                assert segment.get("repeated_root_exact") is True
                notes = tuple(segment.get("repeated_root_notes") or ())
                assert len(notes) == 2
                assert notes[0] == notes[1]

    assert seen_repeated_root
