from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import replace
from typing import Mapping, Sequence

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.pattern_runtime.pattern_plan import PatternPlan
from .anticipation_policy import AnticipationPolicy
from .tail_arbitration import TailAvailability, is_tail_slot_available


class AnticipationResolver:
    """Rewrite a pitchless event timeline before Expression and Voicing.

    Runtime order:
      1. Style patterns create ordinary pitchless events for each region.
      2. This resolver checks the previous region's eligible harmonic tail slots.
      3. If allowed by style probability, the next region's beat-1 event is moved
         to the previous region's last upbeat, and the original beat-1 event is
         suppressed/tied.
      4. Expression, voicing and MIDI realization happen later.
    """

    def resolve(
        self,
        events: list[PatternEvent],
        policy: AnticipationPolicy,
        rng: random.Random,
        *,
        regions: Sequence[HarmonicRegion] | None = None,
        region_plans: Mapping[str, PatternPlan] | None = None,
    ) -> list[PatternEvent]:
        if not policy.enabled or policy.normalized_probability() <= 0:
            return events

        ordered_regions = list(regions or self._derive_regions_from_events(events))
        if len(ordered_regions) < 2:
            return events

        plans_by_region = dict(region_plans or {})
        events_by_region: dict[str, list[PatternEvent]] = defaultdict(list)
        for event in events:
            events_by_region[event.region_id].append(event)

        replacements: dict[str, PatternEvent] = {}
        additions: list[PatternEvent] = []

        for index in range(1, len(ordered_regions)):
            previous_region = ordered_regions[index - 1]
            current_region = ordered_regions[index]
            current_plan = plans_by_region.get(current_region.region_id)
            candidate = self._find_movable_beat1_event(events_by_region.get(current_region.region_id, []), policy)
            if candidate is None:
                continue
            if self._is_terminal_ending_candidate(candidate):
                continue

            movability = current_plan.beat1_movability if current_plan is not None else None
            if movability is not None and not movability.movable:
                continue

            target_offset = movability.target_offset_beats if movability is not None else policy.target_offset_beats
            target_abs_beat = float(candidate.onset_beat) + float(target_offset)
            if not self._previous_region_duration_is_allowed(previous_region, policy):
                continue
            tail = self._check_tail(
                previous_region=previous_region,
                previous_events=events_by_region.get(previous_region.region_id, []),
                target_abs_beat=target_abs_beat,
                policy=policy,
                movability_requires_tail=movability.requires_previous_tail_space if movability is not None else True,
            )
            if not tail.can_place_anticipation:
                continue

            if rng.random() > policy.normalized_probability():
                continue

            anticipated = self._make_anticipated_event(
                candidate=candidate,
                previous_region=previous_region,
                current_region=current_region,
                source_region_events=events_by_region.get(current_region.region_id, []),
                target_abs_beat=target_abs_beat,
                target_local_beat=tail.target_local_beat,
                target_offset_beats=target_offset,
                policy=policy,
                tail_checked_local_beats=tail.checked_local_beats,
                tail_availability_reason=tail.reason,
            )
            suppressed = self._make_suppressed_original(candidate, anticipated, previous_region, policy)
            replacements[candidate.event_id] = suppressed
            additions.append(anticipated)

            # Make subsequent tail checks aware of the newly inserted harmonic event.
            events_by_region[previous_region.region_id].append(anticipated)

        rewritten = [replacements.get(event.event_id, event) for event in events]
        rewritten.extend(additions)
        return sorted(rewritten, key=self._sort_key)

    def _is_terminal_ending_candidate(self, event: PatternEvent) -> bool:
        metadata = dict(event.metadata or {})
        try:
            chorus_index = int(metadata.get("region_chorus_index"))
            total_choruses = int(metadata.get("region_total_choruses"))
        except (TypeError, ValueError):
            return False
        return (
            bool(metadata.get("region_is_last_bar_of_chorus"))
            and chorus_index == total_choruses - 1
            and bool(metadata.get("region_is_last_bar_of_section", True))
        )

    def _find_movable_beat1_event(self, events: list[PatternEvent], policy: AnticipationPolicy) -> PatternEvent | None:
        eligible = [
            event
            for event in events
            if event.status == "active"
            and event.track in policy.eligible_tracks
            and event.role in policy.eligible_roles
            and event.local_beat is not None
            and abs(float(event.local_beat) - 0.0) <= 1e-6
        ]
        if not eligible:
            return None
        return sorted(eligible, key=lambda event: (event.onset_beat, event.track, event.event_id))[0]

    def _previous_region_duration_is_allowed(self, previous_region: HarmonicRegion, policy: AnticipationPolicy) -> bool:
        minimum = policy.min_previous_region_duration_beats
        if minimum is None:
            return True
        return float(previous_region.duration_beats) + 1e-6 >= float(minimum)

    def _check_tail(
        self,
        *,
        previous_region: HarmonicRegion,
        previous_events: list[PatternEvent],
        target_abs_beat: float,
        policy: AnticipationPolicy,
        movability_requires_tail: bool,
    ) -> TailAvailability:
        if not policy.require_previous_tail_space or not movability_requires_tail:
            return TailAvailability(True, "tail_check_skipped", target_local_beat=round(target_abs_beat - previous_region.start_beat, 6))
        return is_tail_slot_available(
            previous_region=previous_region,
            previous_events=previous_events,
            target_abs_beat=target_abs_beat,
            eligible_tracks=policy.eligible_tracks,
            eligible_roles=policy.eligible_roles,
            require_last_beat_empty=policy.require_previous_last_beat_empty,
            require_last_upbeat_empty=policy.require_previous_last_upbeat_empty,
        )

    def _make_anticipated_event(
        self,
        *,
        candidate: PatternEvent,
        previous_region: HarmonicRegion,
        current_region: HarmonicRegion,
        source_region_events: list[PatternEvent],
        target_abs_beat: float,
        target_local_beat: float | None,
        target_offset_beats: float,
        policy: AnticipationPolicy,
        tail_checked_local_beats: tuple[float, ...] = (),
        tail_availability_reason: str = "",
    ) -> PatternEvent:
        anticipated_id = f"{candidate.event_id}__anticipated_from_previous"
        logical_lead_in = abs(float(target_abs_beat) - float(candidate.onset_beat))
        performed_lead_in = (
            float(policy.performed_lead_in_beats)
            if policy.performed_lead_in_beats is not None
            else logical_lead_in
        )
        target_timing_intent = str(policy.target_timing_intent or "auto")
        previous_duration = float(previous_region.duration_beats)
        current_duration = float(current_region.duration_beats)
        source_continuation = self._source_continuation_target(candidate, current_region, source_region_events, policy)
        previous_last_beat_local = round(max(0.0, previous_duration - 1.0), 6)
        previous_last_upbeat_local = round(max(0.0, previous_duration - 0.5), 6)
        metadata = {
            **dict(candidate.metadata),
            # The realized note builder consumes this.  For medium swing,
            # logical .5 must render as the triplet upbeat (2/3), not as a
            # literal straight eighth.
            "timing_intent": target_timing_intent,
            "anticipation": {
                "kind": "next_beat1_to_previous_tail",
                "policy": policy.debug_name,
                "original_event_id": candidate.event_id,
                "source_region_id": current_region.region_id,
                "placed_in_region_id": previous_region.region_id,
                "original_onset_beat": candidate.onset_beat,
                "original_local_beat_in_source": candidate.local_beat,
                "source_region_duration_beats": candidate.metadata.get("region_duration_beats"),
                "source_continuation_contract_version": "v2_6_113",
                "source_continuation_contract": "Anticipated event keeps the suppressed beat-1 event's source-pattern duration target; expression adds the lead-in to the original source continuation, rather than shortening the anticipation to the next downbeat.",
                "source_continuation_target_kind": source_continuation["target_kind"],
                "source_continuation_target_event_id": source_continuation.get("target_event_id"),
                "source_continuation_target_onset_beat": source_continuation.get("target_onset_beat"),
                "source_continuation_target_local_beat": source_continuation.get("target_local_beat"),
                "source_continuation_gap_beats": source_continuation["gap_beats"],
                "source_next_same_track_event_id": source_continuation.get("target_event_id") if source_continuation["target_kind"] == "next_same_track_touch" else None,
                "source_next_same_track_onset_beat": source_continuation.get("target_onset_beat") if source_continuation["target_kind"] == "next_same_track_touch" else None,
                "source_next_same_track_local_beat": source_continuation.get("target_local_beat") if source_continuation["target_kind"] == "next_same_track_touch" else None,
                "source_next_same_track_gap_beats": source_continuation["gap_beats"] if source_continuation["target_kind"] == "next_same_track_touch" else None,
                "target_offset_beats": target_offset_beats,
                "lead_in_beats": round(logical_lead_in, 6),
                "logical_lead_in_beats": round(logical_lead_in, 6),
                "performed_lead_in_beats": round(performed_lead_in, 6),
                "expected_performed_onset_beat": round(float(candidate.onset_beat) - performed_lead_in, 6),
                "timing_grid_contract_version": "v2_3_9",
                "timing_grid": policy.timing_grid,
                "target_timing_intent": target_timing_intent,
                "expected_upbeat_fraction": policy.expected_upbeat_fraction,
                "target_local_beat_in_previous": target_local_beat,
                "previous_region_duration_beats": round(previous_duration, 6),
                "current_region_duration_beats": round(current_duration, 6),
                "previous_region_last_beat_local": previous_last_beat_local,
                "previous_region_last_upbeat_local": previous_last_upbeat_local,
                "min_previous_region_duration_beats": policy.min_previous_region_duration_beats,
                "tail_checked_local_beats": tuple(tail_checked_local_beats),
                "tail_availability_reason": tail_availability_reason,
                "style_anticipation_policy_metadata": dict(policy.metadata),
                "region_first_anticipation_compatibility_checkpoint_version": "v2_6_61",
                "region_first_anticipation_contract": "target tail slot is previous_region.duration_beats - 0.5; 4-beat regions use local 3.5, 2-beat regions use local 1.5, and 1-beat regions use local 0.5 rather than a hard-coded bar 4&.",
                "bar_first_4and_assumption": False,
                "suppressed_original": policy.suppress_original,
                "tie_from_previous": policy.tie_from_previous,
            },
        }
        return replace(
            candidate,
            event_id=anticipated_id,
            onset_beat=round(float(target_abs_beat), 6),
            local_beat=target_local_beat,
            source_event_id=candidate.event_id,
            status="active",
            metadata=metadata,
        )

    def _source_continuation_target(
        self,
        candidate: PatternEvent,
        current_region: HarmonicRegion,
        source_region_events: list[PatternEvent],
        policy: AnticipationPolicy,
    ) -> dict:
        """Return the source-pattern duration target for a moved beat-1 event.

        First-principles contract: an anticipated event is the same logical
        source-region beat-1 event performed earlier.  Its duration endpoint
        should therefore be derived from the source timeline (usually the next
        active same-track harmonic touch, otherwise the source ChordRegion end),
        not from the new previous-tail onset.
        """

        later_events = [
            event
            for event in source_region_events
            if event.event_id != candidate.event_id
            and event.status == "active"
            and event.track == candidate.track
            and event.role in policy.eligible_roles
            and float(event.onset_beat) > float(candidate.onset_beat) + 1e-6
        ]
        if later_events:
            target = sorted(later_events, key=lambda event: (event.onset_beat, event.event_id))[0]
            gap = max(0.0, float(target.onset_beat) - float(candidate.onset_beat))
            return {
                "target_kind": "next_same_track_touch",
                "target_event_id": target.event_id,
                "target_onset_beat": round(float(target.onset_beat), 6),
                "target_local_beat": None if target.local_beat is None else round(float(target.local_beat), 6),
                "gap_beats": round(gap, 6),
            }

        region_end = float(current_region.start_beat) + float(current_region.duration_beats)
        gap = max(0.0, region_end - float(candidate.onset_beat))
        return {
            "target_kind": "source_region_end",
            "target_event_id": None,
            "target_onset_beat": round(region_end, 6),
            "target_local_beat": round(float(current_region.duration_beats), 6),
            "gap_beats": round(gap, 6),
        }


    def _make_suppressed_original(
        self,
        candidate: PatternEvent,
        anticipated: PatternEvent,
        previous_region: HarmonicRegion,
        policy: AnticipationPolicy,
        tail_checked_local_beats: tuple[float, ...] = (),
        tail_availability_reason: str = "",
    ) -> PatternEvent:
        if not policy.suppress_original:
            return candidate
        metadata = {
            **dict(candidate.metadata),
            "anticipation": {
                "kind": "suppressed_original_beat1",
                "policy": policy.debug_name,
                "anticipated_event_id": anticipated.event_id,
                "placed_in_region_id": previous_region.region_id,
                "tie_from_previous": policy.tie_from_previous,
            },
        }
        return replace(candidate, status="suppressed", source_event_id=anticipated.event_id, metadata=metadata)

    def _derive_regions_from_events(self, events: list[PatternEvent]) -> list[HarmonicRegion]:
        """Best-effort compatibility path for direct resolver tests.

        The engine passes real HarmonicRegion objects. This fallback exists so
        callers that only have events still get deterministic ordering, although
        duration-sensitive tail checks are most accurate with real regions.
        """

        by_region: dict[str, list[PatternEvent]] = defaultdict(list)
        for event in events:
            by_region[event.region_id].append(event)
        regions: list[HarmonicRegion] = []
        for idx, (region_id, region_events) in enumerate(by_region.items()):
            start = min(event.onset_beat - (event.local_beat or 0.0) for event in region_events)
            regions.append(
                HarmonicRegion(
                    region_id=region_id,
                    chord_symbol=region_events[0].chord_symbol,
                    next_chord_symbol=None,
                    chorus_index=0,
                    bar_index=idx,
                    chord_index=0,
                    start_beat=start,
                    duration_beats=4.0,
                )
            )
        return sorted(regions, key=lambda region: region.start_beat)

    def _sort_key(self, event: PatternEvent) -> tuple[float, int, str, str]:
        track_order = {"drums": 0, "bass": 1, "piano": 2}
        return (event.onset_beat, track_order.get(event.track, 99), event.status, event.event_id)
