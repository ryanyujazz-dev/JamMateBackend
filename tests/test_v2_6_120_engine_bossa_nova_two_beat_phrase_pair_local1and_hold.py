from __future__ import annotations

import random

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.bossa_nova import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style

PIANO_SOURCE_KEY = "bossa_nova:0:jammate_engine.styles.bossa_nova.comping_patterns.get_pattern_candidates"
MILESTONE_ID = "v2_6_120"


def _previous_bossa_half_region_1_2_history() -> dict:
    return {
        f"{PIANO_SOURCE_KEY}:recent_comping": [
            {
                "name": "bossa_piano_half_region_1_2",
                "category": "core_batida_half_region_adaptation",
                "rhythm_family": "core_batida_half_region_adaptation",
                "rhythmic_cell": "half_region_1_2",
                "pattern_function": "dense_harmonic_rhythm_normal_voicing_adaptation",
                "phrase_role": "",
                "weight_calibration_class": "stable",
                "continuity_class": "stable",
                "activity_class": "stable",
                "tail_push_risk": "none",
                "density": "identity",
                "region_length_family": "",
                "two_beat_phrase_pair_candidate": True,
                "two_beat_phrase_pair_family": "beat1_beat2_to_1and_hold",
                "two_beat_phrase_pair_role": "call",
                "two_beat_phrase_pair_triggers_response_cells": ("bossa_half_region_1and_hold",),
                "event_count": 2,
                "has_region_start": True,
                "is_active": False,
                "is_fill": False,
                "is_busy": False,
                "is_push": False,
                "is_tail_push": False,
                "is_offbeat": False,
            }
        ]
    }


def test_v2_6_120_adds_bossa_pitchless_local_1and_hold_two_beat_candidate() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    by_name = {candidate.name: candidate for candidate in candidates}

    assert "bossa_piano_half_region_1_2" in by_name
    assert "bossa_piano_half_region_1and_hold" in by_name

    call = by_name["bossa_piano_half_region_1_2"]
    response = by_name["bossa_piano_half_region_1and_hold"]

    assert call.rhythm_beats == (0.0, 1.0)
    assert call.metadata["two_beat_phrase_pair_role"] == "call"
    assert call.metadata["two_beat_phrase_pair_vocabulary_version"] == MILESTONE_ID

    assert response.rhythm_beats == (0.5,)
    assert response.metadata["rhythmic_cell"] == "bossa_half_region_1and_hold"
    assert response.metadata["two_beat_phrase_pair_role"] == "response"
    assert response.metadata["two_beat_phrase_pair_responds_to_cell"] == "half_region_1_2"
    assert response.events[0].expression_hint == "cell_soft_hold"
    assert response.events[0].metadata["semantic_expression_hint"] == "soft_hold"

    text = " ".join([response.name, response.category, str(response.metadata), " ".join(response.tags)])
    assert "two_chord_bar" not in text
    assert "bar_first" not in text
    assert response.metadata["voicing_boundary"] == "pattern_is_pitchless"
    assert "velocity" not in response.metadata
    assert "duration" not in response.metadata
    assert "pedal" not in response.metadata


def test_v2_6_120_bossa_phrase_pair_policy_declared_as_region_local_history_weighting() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_two_beat_phrase_pair_policy"] is True
    assert policy["piano_comping_two_beat_phrase_pair_policy_version"] == MILESTONE_ID
    assert policy["bossa_nova_two_beat_phrase_pair_policy_active"] is True
    contract = policy["piano_comping_two_beat_phrase_pair_policy_contract"]
    assert "local 1+2" in contract
    assert "local 1& with a hold" in contract
    assert "bar-first" in contract
    assert "voicing/expression" in contract


def test_v2_6_120_previous_bossa_local_1_plus_2_selects_following_local_1and_hold_response() -> None:
    style = get_style("bossa_nova")
    history = _previous_bossa_half_region_1_2_history()
    region = HarmonicRegion(
        region_id="bar0_second_half",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        chorus_index=0,
        bar_index=0,
        chord_index=1,
        start_beat=2.0,
        duration_beats=2.0,
        is_first_region_of_bar=False,
        is_last_region_of_bar=True,
    )

    plan = style.plan_region(region, {"style_pattern_history": history, "rng": random.Random(120)})
    piano_events = [event for event in plan.events if event.track == "piano"]

    assert len(piano_events) == 1
    event = piano_events[0]
    assert event.pattern_id == "bossa_piano_half_region_1and_hold"
    assert event.local_beat == 0.5
    assert event.expression_hint == "cell_soft_hold"
    assert event.metadata["two_beat_phrase_pair_policy_status"] == "phrase_response_preferred_after_call"
    assert event.metadata["two_beat_phrase_pair_policy_previous_cell"] == "half_region_1_2"
    assert event.metadata["two_beat_phrase_pair_policy_response_matched_previous"] is True
