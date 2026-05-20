from __future__ import annotations

import random

from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.anticipation.tail_arbitration import is_tail_slot_available
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, event_spec
from jammate_engine.styles.registry import get_style


def _region(region_id: str, chord: str, start: float, duration: float, *, next_chord: str | None = None) -> HarmonicRegion:
    return HarmonicRegion(
        region_id=region_id,
        chord_symbol=chord,
        next_chord_symbol=next_chord,
        chorus_index=0,
        bar_index=0,
        chord_index=0,
        start_beat=start,
        duration_beats=duration,
    )


def _policy() -> AnticipationPolicy:
    return AnticipationPolicy(
        enabled=True,
        probability=1.0,
        target_offset_beats=-0.5,
        timing_grid="swing_triplet_upbeat",
        target_timing_intent="swing_upbeat",
        performed_lead_in_beats=1.0 / 3.0,
        expected_upbeat_fraction=2.0 / 3.0,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
        require_previous_last_beat_empty=True,
        require_previous_last_upbeat_empty=True,
        debug_name="test_region_first_medium_swing",
    )


def _plan(region: HarmonicRegion, *, name: str, beats: tuple[float, ...]) -> object:
    return PatternCandidate(
        name=name,
        weight=1.0,
        category="test_region_first_anticipation",
        events=tuple(event_spec(track="piano", beat=beat, role="harmonic") for beat in beats),
        beat1_movability=Beat1Movability(movable=(0.0 in beats)),
    ).instantiate(region)


def test_v2_6_61_medium_swing_policy_exposes_region_first_anticipation_checkpoint() -> None:
    style = get_style("medium_swing")
    arrangement = style.arrangement_policy
    assert arrangement["piano_region_first_anticipation_compatibility_checkpoint"] is True
    assert arrangement["piano_region_first_anticipation_compatibility_checkpoint_version"] == "v2_6_61"
    assert "2-beat regions use local 2&/1.5" in arrangement["piano_region_first_anticipation_compatibility_contract"]

    policy = style.anticipation_policy
    assert policy.metadata["region_first_anticipation_compatibility_checkpoint_version"] == "v2_6_61"
    assert policy.debug_name == "medium_swing_light_region_tail_push"
    assert policy.metadata["no_bar_first_4and_assumption"] is True


def test_v2_6_61_tail_slot_availability_uses_region_duration_not_bar_4and() -> None:
    # Four-beat region: target tail is local 3.5, equivalent to written 4&.
    four = _region("r4", "Dm7", 0.0, 4.0)
    available_four = is_tail_slot_available(
        previous_region=four,
        previous_events=[],
        target_abs_beat=3.5,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
    )
    assert available_four.can_place_anticipation is True
    assert available_four.target_local_beat == 3.5
    assert available_four.checked_local_beats == (3.0, 3.5)

    # Two-beat region: target tail is local 1.5, not bar-local 3.5.
    two = _region("r2", "Dm7", 8.0, 2.0)
    available_two = is_tail_slot_available(
        previous_region=two,
        previous_events=[],
        target_abs_beat=9.5,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
    )
    assert available_two.can_place_anticipation is True
    assert available_two.target_local_beat == 1.5
    assert available_two.checked_local_beats == (1.0, 1.5)

    wrong_bar_tail = is_tail_slot_available(
        previous_region=two,
        previous_events=[],
        target_abs_beat=11.5,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
    )
    assert wrong_bar_tail.can_place_anticipation is False
    assert wrong_bar_tail.reason == "target_is_not_inside_previous_region"


def test_v2_6_61_resolver_places_two_beat_region_anticipation_on_local_2and() -> None:
    previous_region = _region("r_prev_2", "Dm7", 0.0, 2.0, next_chord="G7")
    current_region = _region("r_next_2", "G7", 2.0, 2.0, next_chord="Cmaj7")
    previous_plan = _plan(previous_region, name="previous_two_beat_tail_free", beats=(0.0,))
    current_plan = _plan(current_region, name="next_two_beat_downbeat", beats=(0.0,))

    rewritten = AnticipationResolver().resolve(
        list(previous_plan.events) + list(current_plan.events),
        _policy(),
        random.Random(1),
        regions=(previous_region, current_region),
        region_plans={previous_region.region_id: previous_plan, current_region.region_id: current_plan},
    )
    anticipated = [event for event in rewritten if event.source_event_id == current_plan.events[0].event_id and event.status == "active"]
    suppressed = [event for event in rewritten if event.event_id == current_plan.events[0].event_id and event.status == "suppressed"]

    assert len(anticipated) == 1
    assert anticipated[0].onset_beat == 1.5
    assert anticipated[0].local_beat == 1.5
    metadata = anticipated[0].metadata["anticipation"]
    assert metadata["region_first_anticipation_compatibility_checkpoint_version"] == "v2_6_61"
    assert metadata["previous_region_duration_beats"] == 2.0
    assert metadata["previous_region_last_beat_local"] == 1.0
    assert metadata["previous_region_last_upbeat_local"] == 1.5
    assert metadata["target_local_beat_in_previous"] == 1.5
    assert metadata["tail_checked_local_beats"] == (1.0, 1.5)
    assert metadata["bar_first_4and_assumption"] is False
    assert len(suppressed) == 1


def test_v2_6_61_one_beat_region_anchor_blocks_previous_tail_anticipation() -> None:
    previous_region = _region("r_prev_1", "Dm7", 0.0, 1.0, next_chord="G7")
    current_region = _region("r_next_1", "G7", 1.0, 1.0, next_chord="Cmaj7")
    previous_plan = _plan(previous_region, name="previous_one_beat_anchor", beats=(0.0,))
    current_plan = _plan(current_region, name="next_one_beat_downbeat", beats=(0.0,))

    rewritten = AnticipationResolver().resolve(
        list(previous_plan.events) + list(current_plan.events),
        _policy(),
        random.Random(1),
        regions=(previous_region, current_region),
        region_plans={previous_region.region_id: previous_plan, current_region.region_id: current_plan},
    )

    assert not any(event.source_event_id == current_plan.events[0].event_id for event in rewritten)
    assert any(event.event_id == current_plan.events[0].event_id and event.status == "active" for event in rewritten)
