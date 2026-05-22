from __future__ import annotations

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.styles.medium_swing import arrangement_policy, comping_patterns
from jammate_engine.styles.registry import get_style


PIANO_SOURCE_KEY = "medium_swing:0:jammate_engine.styles.medium_swing.comping_patterns.get_pattern_candidates"


def _previous_local_1_plus_2_history() -> dict:
    return {
        f"{PIANO_SOURCE_KEY}:recent_comping": [
            {
                "name": "medium_swing_piano_two_beat_region_start_local2",
                "category": "region_lookup_short_region_stable",
                "rhythm_family": "short_region_stable",
                "rhythmic_cell": "start_local2",
                "pattern_function": "start_local2_region_lookup",
                "phrase_role": "short_region_vocabulary",
                "weight_calibration_class": "stable",
                "continuity_class": "stable",
                "activity_class": "stable",
                "tail_push_risk": "none",
                "density": "medium",
                "region_length_family": "two_beat_region",
                "two_beat_phrase_pair_candidate": True,
                "two_beat_phrase_pair_family": "beat1_beat2_to_1and_hold",
                "two_beat_phrase_pair_role": "call",
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


def test_v2_6_119_adds_pitchless_local_1and_hold_two_beat_candidate() -> None:
    candidates = comping_patterns.get_pattern_candidates({"region_duration_beats": 2.0})
    by_name = {candidate.name: candidate for candidate in candidates}

    assert len(candidates) >= 7
    candidate = by_name["medium_swing_piano_two_beat_region_local1and_hold"]
    assert candidate.rhythm_beats == (0.5,)
    assert candidate.metadata["rhythmic_cell"] == "local1and_hold"
    assert candidate.metadata["two_beat_phrase_pair_role"] == "response"
    assert candidate.metadata["two_beat_phrase_pair_responds_to_cell"] == "start_local2"
    assert candidate.events[0].expression_hint == "comp_medium"
    assert candidate.events[0].metadata["semantic_expression_hint"] == "soft_hold"

    text = " ".join([candidate.name, candidate.category, str(candidate.metadata), " ".join(candidate.tags)])
    assert "two_chord_bar" not in text
    assert candidate.metadata["voicing_boundary"] == "pattern_is_pitchless"
    assert "velocity" not in candidate.metadata
    assert "duration" not in candidate.metadata
    assert "pedal" not in candidate.metadata


def test_v2_6_119_phrase_pair_policy_declared_as_region_local_history_weighting() -> None:
    policy = arrangement_policy.get_arrangement_policy()

    assert policy["piano_comping_two_beat_phrase_pair_policy"] is True
    assert policy["piano_comping_two_beat_phrase_pair_policy_version"] == "v2_6_119"
    contract = policy["piano_comping_two_beat_phrase_pair_policy_contract"]
    assert "local 1+2" in contract
    assert "local 1& with a hold" in contract
    assert "bar-first" in contract
    assert "voicing/expression" in contract


def test_v2_6_119_previous_local_1_plus_2_selects_following_local_1and_hold_response() -> None:
    style = get_style("medium_swing")
    history = _previous_local_1_plus_2_history()
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

    plan = style.plan_region(region, {"style_pattern_history": history})
    piano_events = [event for event in plan.events if event.track == "piano"]

    assert len(piano_events) == 1
    event = piano_events[0]
    assert event.pattern_id == "medium_swing_piano_two_beat_region_local1and_hold"
    assert event.local_beat == 0.5
    assert event.expression_hint == "comp_medium"
    assert event.metadata["two_beat_phrase_pair_policy_status"] == "phrase_response_preferred_after_call"
    assert event.metadata["two_beat_phrase_pair_policy_previous_cell"] == "start_local2"
