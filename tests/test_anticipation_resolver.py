from __future__ import annotations

import random

from jammate_engine.core.anticipation import AnticipationPolicy, AnticipationResolver
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import Beat1Movability, PatternCandidate, TailPolicy, event_spec
from jammate_engine.styles.registry import get_style


def _regions() -> tuple[HarmonicRegion, HarmonicRegion]:
    return (
        HarmonicRegion(
            region_id="r_prev",
            chord_symbol="Dm7",
            next_chord_symbol="G7",
            chorus_index=0,
            bar_index=0,
            chord_index=0,
            start_beat=0.0,
            duration_beats=4.0,
        ),
        HarmonicRegion(
            region_id="r_next",
            chord_symbol="G7",
            next_chord_symbol="Cmaj7",
            chorus_index=0,
            bar_index=1,
            chord_index=0,
            start_beat=4.0,
            duration_beats=4.0,
        ),
    )


def _policy(probability: float = 1.0) -> AnticipationPolicy:
    return AnticipationPolicy(
        enabled=True,
        probability=probability,
        eligible_tracks=("piano",),
        eligible_roles=("harmonic",),
        require_previous_last_beat_empty=True,
        require_previous_last_upbeat_empty=True,
        debug_name="test_policy",
    )


def test_anticipation_moves_next_region_beat1_to_previous_4and_and_suppresses_original() -> None:
    prev_region, next_region = _regions()
    previous = PatternCandidate(
        name="prev_tail_free",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        tail_policy=TailPolicy.from_local_beats((0.0,)),
    ).instantiate(prev_region)
    next_plan = PatternCandidate(
        name="next_downbeat",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)

    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        _policy(),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )

    anticipated = [event for event in rewritten if event.source_event_id == next_plan.events[0].event_id and event.status == "active"]
    suppressed = [event for event in rewritten if event.event_id == next_plan.events[0].event_id and event.status == "suppressed"]

    assert len(anticipated) == 1
    assert anticipated[0].onset_beat == 3.5
    assert anticipated[0].chord_symbol == "G7"
    assert anticipated[0].metadata["anticipation"]["placed_in_region_id"] == "r_prev"
    assert len(suppressed) == 1
    assert suppressed[0].source_event_id == anticipated[0].event_id


def test_anticipation_is_blocked_when_previous_harmonic_tail_is_occupied() -> None:
    prev_region, next_region = _regions()
    previous = PatternCandidate(
        name="prev_tail_occupied",
        weight=1.0,
        category="test",
        events=(
            event_spec(track="piano", beat=0.0, role="harmonic"),
            event_spec(track="piano", beat=3.5, role="harmonic"),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0, 3.5)),
    ).instantiate(prev_region)
    next_plan = PatternCandidate(
        name="next_downbeat",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)

    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        _policy(),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )

    assert all(event.status == "active" for event in rewritten)
    assert not any(event.source_event_id == next_plan.events[0].event_id for event in rewritten)


def test_drum_or_bass_tail_events_do_not_block_piano_harmonic_anticipation() -> None:
    prev_region, next_region = _regions()
    previous = PatternCandidate(
        name="prev_only_drums_on_4and",
        weight=1.0,
        category="test",
        events=(
            event_spec(track="piano", beat=0.0, role="harmonic"),
            event_spec(track="drums", beat=3.5, role="drum"),
            event_spec(track="bass", beat=3.5, role="bass_note"),
        ),
        tail_policy=TailPolicy.from_local_beats((0.0, 3.5)),
    ).instantiate(prev_region)
    next_plan = PatternCandidate(
        name="next_downbeat",
        weight=1.0,
        category="test",
        events=(event_spec(track="piano", beat=0.0, role="harmonic"),),
        beat1_movability=Beat1Movability(movable=True),
    ).instantiate(next_region)

    rewritten = AnticipationResolver().resolve(
        previous.events + next_plan.events,
        _policy(),
        random.Random(1),
        regions=(prev_region, next_region),
        region_plans={prev_region.region_id: previous, next_region.region_id: next_plan},
    )

    assert any(event.status == "suppressed" and event.event_id == next_plan.events[0].event_id for event in rewritten)
    assert any(event.source_event_id == next_plan.events[0].event_id and event.onset_beat == 3.5 for event in rewritten)


def test_style_profiles_expose_typed_anticipation_policy() -> None:
    style = get_style("bossa_nova")
    assert isinstance(style.anticipation_policy, AnticipationPolicy)
    assert style.anticipation_policy.enabled is True
    assert style.anticipation_policy.eligible_tracks == ("piano",)
