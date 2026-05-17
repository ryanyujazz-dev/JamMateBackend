from __future__ import annotations

import itertools
import random
from typing import Callable, Sequence

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.material import resolve_degree_token
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, PatternEvent

from .models import BassFoundationPlan, BassTarget, Beat4Choice
from .policy import BassFoundationPolicy
from .rules import (
    _candidate_allowed_for_chord,
    _choose_region_start_note,
    _classic_connector_to_nextR,
    _event_at_or_before,
    _is_connector_degree,
    _is_natural_fourth,
    _is_swing_upbeat,
    _nearest_note_for_pc,
    _nearest_note_for_pc_within_span,
    _normalize_degree_for_lane,
    _note_for_pc_within_span_near,
    _weighted_instance_choice,
    is_major_quality,
    is_six_quality,
    _next_root_pc,
    _nextR_octave_candidates,
    _notes_for_pitch_class,
    _resolve_pc,
    _root_anchor_event,
    _same_swing_upbeat_slot,
    _scale_pcs_for_chord,
    _skeleton_starts_with_repeated_root,
    _span_ok,
    _two_bar_tonic_scene_allowed,
    _weighted_choice,
    effective_lane_weights_for_candidate,
    lane_bias_label_for_candidate,
    lane_bias_specs_for_candidate,
    lane_of_instance,
    root_zone,
)

PatternSource = Callable[[dict | None], Sequence[PatternCandidate]]


class BassFoundationGenerator:
    """Generate a target-to-target BassFoundation walking timeline."""

    def generate(
        self,
        *,
        regions: Sequence[HarmonicRegion],
        pattern_source: PatternSource,
        policy: BassFoundationPolicy,
        rng: random.Random,
        context: dict | None = None,
    ) -> BassFoundationPlan:
        if not policy.enabled:
            return BassFoundationPlan(events=[], metadata={"enabled": False})

        events: list[PatternEvent] = []
        selected: list[str] = []
        debug_segments: list[dict] = []
        previous_note: int | None = None
        inherited_target_note: int | None = None
        pattern_history: dict[str, str] = {}
        targets = [BassTarget.from_region(region) for region in regions]

        index = 0
        last_classic_fill_index = -999999
        while index < len(regions):
            region = regions[index]
            target = targets[index]
            region_context = {
                **dict(context or {}),
                "region": region,
                "region_duration_beats": region.duration_beats,
                "chord_symbol": region.chord_symbol,
                "next_chord_symbol": region.next_chord_symbol,
                "style_pattern_history": pattern_history,
            }
            candidates = tuple(pattern_source(region_context))
            bass_candidates = tuple(c for c in candidates if any(e.track == "bass" for e in c.events))
            if not bass_candidates:
                index += 1
                continue

            start_note, start_note_source, continuity_match = _choose_region_start_note(
                region.chord_symbol,
                policy,
                previous_note,
                inherited_target_note,
                rng,
            )
            zone = root_zone(start_note)

            fill_events, fill_debug, consumed = self._try_generate_classic_fill(
                regions=regions,
                start_index=index,
                pattern_source=pattern_source,
                policy=policy,
                rng=rng,
                context=context or {},
                previous_note=previous_note,
                start_note=start_note,
                zone=zone,
                last_classic_fill_index=last_classic_fill_index,
            )
            if fill_events:
                fill_debug.update({
                    "start_note": start_note,
                    "start_note_source": start_note_source,
                    "previous_target_nextR_note": inherited_target_note,
                    "target_continuity_match": continuity_match,
                })
                events.extend(fill_events)
                debug_segments.append(fill_debug)
                selected.append(str(fill_debug.get("candidate", "classic_fill")))
                pattern_history["last_candidate"] = str(fill_debug.get("candidate", "classic_fill"))
                pattern_history["last_category"] = str(fill_debug.get("category", "classic_fill"))
                carried_note = fill_debug.get("target_nextR_note")
                previous_note = int(carried_note) if carried_note is not None else int(fill_events[-1].metadata["resolved_midi_note"])
                inherited_target_note = int(carried_note) if carried_note is not None else None
                last_classic_fill_index = index
                index += max(1, consumed)
                continue

            candidate = self._choose_candidate(
                candidates=bass_candidates,
                rng=rng,
                history=pattern_history,
                duration_beats=region.duration_beats,
                zone=zone,
                chord_symbol=region.chord_symbol,
                region=region,
                policy=policy,
                start_note=start_note,
            )
            selected.append(candidate.name)
            pattern_history["last_candidate"] = candidate.name
            pattern_history["last_category"] = candidate.category

            if region.duration_beats <= 2.0:
                segment_events, segment_debug = self._generate_compact_segment(
                    region=region,
                    candidate=candidate,
                    policy=policy,
                    rng=rng,
                    start_note=start_note,
                    zone=zone,
                )
            else:
                segment_events, segment_debug = self._generate_walking_segment(
                    region=region,
                    candidate=candidate,
                    policy=policy,
                    rng=rng,
                    start_note=start_note,
                    zone=zone,
                )

            ornament_events, ornament_debug = self._apply_root_echo_ornaments(
                region=region,
                segment_events=segment_events,
                candidate=candidate,
                policy=policy,
                rng=rng,
                zone=zone,
            )
            if ornament_events:
                segment_events = sorted(segment_events + ornament_events, key=lambda event: (float(event.local_beat or 0.0), event.event_id))
                segment_debug["root_echo_ornaments"] = ornament_debug
            else:
                segment_debug["root_echo_ornaments"] = []

            segment_debug.update({
                "start_note": start_note,
                "start_note_source": start_note_source,
                "previous_target_nextR_note": inherited_target_note,
                "target_continuity_match": continuity_match,
            })
            events.extend(segment_events)
            debug_segments.append(segment_debug)
            carried_note = segment_debug.get("target_nextR_note")
            if carried_note is not None:
                previous_note = int(carried_note)
                inherited_target_note = int(carried_note)
            elif segment_events:
                previous_note = int(segment_events[-1].metadata["resolved_midi_note"])
                inherited_target_note = None
            index += 1

        return BassFoundationPlan(
            events=events,
            selected_candidates=selected,
            metadata={
                "enabled": True,
                "policy": policy.to_debug_dict(),
                "selected_candidates": selected,
                "targets": len(targets),
                "segments": debug_segments,
            },
        )

    def _choose_candidate(
        self,
        *,
        candidates: Sequence[PatternCandidate],
        rng: random.Random,
        history: dict[str, str],
        duration_beats: float,
        zone: str,
        chord_symbol: str,
        region: HarmonicRegion,
        policy: BassFoundationPolicy,
        start_note: int,
    ) -> PatternCandidate:
        # Previous-engine alignment: do NOT remove the immediately previous
        # skeleton before the weighted draw.  The old Medium Swing bass selected
        # from the full legal ThreeBeatSkeleton pool every segment; history
        # guards here would distort low/mid/high weight distributions.
        pool = tuple(candidates)
        if duration_beats <= 2.0:
            compact = tuple(c for c in pool if "two_chord_bar" in c.category or "compact" in c.category)
            pool = compact or pool
        else:
            walking = tuple(c for c in pool if "walking" in c.category or "vocabulary" in c.category)
            pool = walking or pool
            legal: list[PatternCandidate] = []
            for candidate in pool:
                if not _candidate_allowed_for_chord(candidate, chord_symbol):
                    continue
                specs = [spec for spec in candidate.events if spec.track == "bass" and spec.local_beat < region.duration_beats]
                if len(specs) < 3:
                    continue
                instances = self._instantiate_body(
                    region,
                    specs[:3],
                    policy,
                    start_note,
                    bool(candidate.metadata.get("allow_repetition", False)),
                )
                if not instances:
                    continue
                if not self._has_eligible_lane(instances, start_note, zone, candidate, policy):
                    continue
                legal.append(candidate)
            pool = tuple(legal) or tuple(pool)
        weights = [self._candidate_weight_for_zone(candidate, zone) for candidate in pool]
        return _weighted_choice(list(pool), weights, rng)

    def _candidate_weight_for_zone(self, candidate: PatternCandidate, zone: str) -> float:
        zone_weights = dict(candidate.metadata.get("zone_weights", {}))
        if zone in {"very_low", "low"}:
            return float(zone_weights.get("low", candidate.weight))
        if zone in {"high", "very_high"}:
            return float(zone_weights.get("high", candidate.weight))
        return float(zone_weights.get("mid", candidate.weight))

    def _generate_walking_segment(
        self,
        *,
        region: HarmonicRegion,
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
        rng: random.Random,
        start_note: int,
        zone: str,
    ) -> tuple[list[PatternEvent], dict]:
        specs = [spec for spec in candidate.events if spec.track == "bass" and spec.local_beat < region.duration_beats]
        if len(specs) < 3:
            return self._generate_compact_segment(region=region, candidate=candidate, policy=policy, rng=rng, start_note=start_note, zone=zone)
        body_specs = specs[:3]
        instances = self._instantiate_body(region, body_specs, policy, start_note, bool(candidate.metadata.get("allow_repetition", False)))
        if not instances:
            fallback_notes = [start_note]
            for spec in body_specs[1:]:
                pc = _resolve_pc(region, str(spec.metadata.get("degree", "R")))
                fallback_notes.append(_nearest_note_for_pc(pc, start_note, policy))
            instances = [tuple(fallback_notes[:3])]

        notes123, selected_lane, lane_bias_label, lane_weights = self._choose_instance_by_lane(instances, start_note, zone, candidate, policy, rng)
        repeated_root_start = _skeleton_starts_with_repeated_root(candidate)
        nextR_note, beat4 = self._choose_nextR_and_beat4(region, notes123[2], policy, rng, repeated_root_start, current_region_notes=notes123)

        full_notes = list(notes123) + [beat4.note, nextR_note]
        if max(full_notes) - min(full_notes) > policy.max_segment_span:
            for nextR_alt in _nextR_octave_candidates(_next_root_pc(region), notes123[2], policy, rng):
                b4s = self._generate_beat4_candidates(region, notes123[2], nextR_alt, policy, repeated_root_start)
                b4s = [choice for choice in b4s if _span_ok(list(notes123) + [choice.note], policy.max_region_span)]
                if not b4s:
                    continue
                b4_alt = _weighted_choice(b4s, [c.weight for c in b4s], rng)
                candidate_notes = list(notes123) + [b4_alt.note, nextR_alt]
                if max(candidate_notes) - min(candidate_notes) <= policy.max_segment_span:
                    beat4 = b4_alt
                    nextR_note = nextR_alt
                    break

        notes = [notes123[0], notes123[1], notes123[2], beat4.note]
        return self._events_from_notes(
            region=region,
            candidate=candidate,
            specs=specs[:4],
            notes=notes,
            policy=policy,
            extra_metadata={
                "zone": zone,
                "selected_lane": selected_lane,
                "lane_bias": lane_bias_label,
                "lane_weights": lane_weights,
                "pattern_zone_weight": self._candidate_weight_for_zone(candidate, zone),
                "candidate_preflight": "old_engine_legal_skeleton_pool",
                "legal_skeleton_pool_size": 1,
                "beat4_connector_kind": beat4.kind,
                "beat4_connector_weight": beat4.weight,
                "beat4_connector_description": beat4.description,
                "repeated_root_start": repeated_root_start,
                "repeated_root_exact": (notes123[0] == notes123[1]) if repeated_root_start else True,
                "repeated_root_notes": (notes123[0], notes123[1]) if repeated_root_start else (),
                "target_nextR_note": nextR_note,
                "skeleton_id": candidate.metadata.get("skeleton_id", candidate.name),
                "skeleton_degrees": tuple(candidate.metadata.get("skeleton_degrees", ())),
            },
        )

    def _generate_compact_segment(
        self,
        *,
        region: HarmonicRegion,
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
        rng: random.Random,
        start_note: int,
        zone: str,
    ) -> tuple[list[PatternEvent], dict]:
        specs = [spec for spec in candidate.events if spec.track == "bass" and spec.local_beat < region.duration_beats]
        if not specs:
            return [], {"region_id": region.region_id, "reason": "no_compact_specs"}
        first_spec = specs[0]
        connector_spec = specs[1] if len(specs) > 1 else specs[0]
        token = str(connector_spec.metadata.get("degree", "beat4_auto"))
        target_nextR_note = _nearest_note_for_pc(_next_root_pc(region), start_note, policy)
        if token == "beat4_auto":
            nextR_note = target_nextR_note
            choices = self._generate_beat4_candidates(region, start_note, nextR_note, policy, disallow_current_root_pc=False)
            beat4 = _weighted_choice(choices, [c.weight for c in choices], rng) if choices else Beat4Choice(nextR_note - 1, "compact_approach", 1.0, "fallback compact approach")
            connector_note = beat4.note
            connector_kind = beat4.kind
            connector_weight = beat4.weight
        else:
            connector_note = _nearest_note_for_pc(_resolve_pc(region, token), start_note, policy)
            connector_kind = token
            connector_weight = 1.0
        if token != "beat4_auto":
            target_nextR_note = _nearest_note_for_pc(_next_root_pc(region), connector_note, policy)
        if not _span_ok([start_note, connector_note], policy.max_region_span):
            connector_note = _nearest_note_for_pc_within_span(_resolve_pc(region, token if token != "beat4_auto" else "approach_nextR_below"), start_note, policy, [start_note])
            target_nextR_note = _nearest_note_for_pc(_next_root_pc(region), connector_note, policy)
            connector_kind = f"{connector_kind}_span_guarded"

        specs_out = [first_spec]
        notes = [start_note]
        if region.duration_beats > 1.0 and connector_spec.local_beat < region.duration_beats:
            specs_out.append(connector_spec)
            notes.append(connector_note)
        return self._events_from_notes(
            region=region,
            candidate=candidate,
            specs=specs_out,
            notes=notes,
            policy=policy,
            extra_metadata={
                "zone": zone,
                "selected_lane": "compact",
                "lane_bias": "compact",
                "lane_weights": policy.lane_weights_by_zone.get(zone, {}),
                "pattern_zone_weight": self._candidate_weight_for_zone(candidate, zone),
                "beat4_connector_kind": connector_kind,
                "beat4_connector_weight": connector_weight,
                "beat4_connector_description": "compact two-beat connector",
                "target_nextR_note": target_nextR_note,
                "repeated_root_start": False,
                "skeleton_id": candidate.metadata.get("skeleton_id", candidate.name),
                "skeleton_degrees": tuple(candidate.metadata.get("skeleton_degrees", ())),
            },
        )

    def _try_generate_classic_fill(
        self,
        *,
        regions: Sequence[HarmonicRegion],
        start_index: int,
        pattern_source: PatternSource,
        policy: BassFoundationPolicy,
        rng: random.Random,
        context: dict,
        previous_note: int | None,
        start_note: int,
        zone: str,
        last_classic_fill_index: int,
    ) -> tuple[list[PatternEvent], dict, int]:
        if not policy.classic_fill_enabled or policy.classic_fill_two_bar_tonic_probability <= 0:
            return [], {}, 0
        if start_index + 2 >= len(regions):
            return [], {}, 0
        if start_index - last_classic_fill_index < policy.classic_fill_min_gap_regions:
            return [], {}, 0
        if start_note > policy.classic_fill_max_start_note:
            return [], {}, 0

        start_region = regions[start_index]
        mid_region = regions[start_index + 1]
        end_region = regions[start_index + 2]
        allowed, reason = _two_bar_tonic_scene_allowed(start_region, mid_region, end_region)
        if not allowed:
            return [], {}, 0
        if rng.random() > policy.classic_fill_two_bar_tonic_probability:
            return [], {"region_id": start_region.region_id, "classic_fill_scene": "two_bar_tonic", "classic_fill_rejected": "probability"}, 0

        scene_context = {
            **dict(context),
            "region": start_region,
            "region_duration_beats": start_region.duration_beats + mid_region.duration_beats,
            "chord_symbol": start_region.chord_symbol,
            "next_chord_symbol": end_region.chord_symbol,
            "bass_foundation_scene": "two_bar_tonic",
            "bass_foundation_fill_scene": "two_bar_tonic",
        }
        fill_candidates = tuple(
            c for c in pattern_source(scene_context)
            if "classic_fill" in c.category or "classic_fill" in c.tags or c.metadata.get("bass_foundation_fill")
        )
        if not fill_candidates:
            return [], {}, 0
        candidate = _weighted_choice(list(fill_candidates), [c.weight for c in fill_candidates], rng)
        events, debug = self._generate_two_bar_tonic_fill_events(
            start_region=start_region,
            mid_region=mid_region,
            end_region=end_region,
            candidate=candidate,
            policy=policy,
            start_note=start_note,
            previous_note=previous_note,
            zone=zone,
        )
        if not events:
            return [], debug, 0
        target_nextR_note = _nearest_note_for_pc(parse_chord(end_region.chord_symbol).root_pc, int(events[-1].metadata["resolved_midi_note"]), policy)
        debug.update({
            "target_nextR_note": target_nextR_note,
            "zone": zone,
            "selected_lane": "classic_fill",
            "lane_weights": policy.lane_weights_by_zone.get(zone, {}),
            "pattern_zone_weight": candidate.weight,
            "beat4_connector_kind": "classic_fill_connector",
            "classic_fill_triggered": True,
            "classic_fill_scene": "two_bar_tonic",
            "classic_fill_reason": reason,
            "consumed_region_ids": [start_region.region_id, mid_region.region_id],
            "target_region_id": end_region.region_id,
            "classic_fill_probability": policy.classic_fill_two_bar_tonic_probability,
        })
        return events, debug, 2

    def _generate_two_bar_tonic_fill_events(
        self,
        *,
        start_region: HarmonicRegion,
        mid_region: HarmonicRegion,
        end_region: HarmonicRegion,
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
        start_note: int,
        previous_note: int | None,
        zone: str,
    ) -> tuple[list[PatternEvent], dict]:
        split_beat = float(start_region.duration_beats)
        region_notes: dict[str, list[int]] = {start_region.region_id: [], mid_region.region_id: []}
        events: list[PatternEvent] = []
        debug_notes: list[dict] = []
        previous_fill_note = previous_note if previous_note is not None else start_note

        for index, spec in enumerate(sorted(candidate.events, key=lambda item: item.local_beat)):
            offset = float(spec.local_beat)
            if offset >= split_beat + mid_region.duration_beats:
                continue
            active_region = start_region if offset < split_beat else mid_region
            active_local_beat = offset if active_region is start_region else offset - split_beat
            token = str(spec.metadata.get("degree", "R"))
            existing = region_notes[active_region.region_id]
            if index == 0 and token == "R":
                note = start_note
            else:
                note = self._classic_fill_note_for_token(
                    token=token,
                    chord_symbol=start_region.chord_symbol,
                    reference=previous_fill_note,
                    existing_region_notes=existing,
                    policy=policy,
                    end_region=end_region,
                )
            if not _span_ok(existing + [note], policy.max_region_span):
                return [], {
                    "region_id": start_region.region_id,
                    "candidate": candidate.name,
                    "classic_fill_rejected": "max_region_span",
                    "failed_token": token,
                    "failed_note": note,
                    "existing_region_notes": existing,
                    "max_region_span": policy.max_region_span,
                }
            region_notes[active_region.region_id].append(note)
            previous_fill_note = note
            event = PatternEvent(
                event_id=f"{active_region.region_id}_bass_foundation_{candidate.name}_{index}",
                track="bass",
                region_id=active_region.region_id,
                chord_symbol=active_region.chord_symbol,
                onset_beat=start_region.start_beat + offset,
                role="bass_note",
                expression_hint=spec.expression_hint,
                pattern_id=candidate.name,
                local_beat=active_local_beat,
                metadata={
                    "candidate": candidate.name,
                    "category": candidate.category,
                    "generation_domain": "bass_foundation",
                    "bass_foundation_generated": True,
                    "bass_foundation_fill": True,
                    "classic_fill_scene": "two_bar_tonic",
                    "fill_id": candidate.metadata.get("fill_id", candidate.name),
                    "degree": token,
                    "resolved_midi_note": note,
                    "next_chord_symbol": end_region.chord_symbol,
                    "region_duration_beats": active_region.duration_beats,
                    "length_profile": spec.metadata.get("length_profile", "classic_fill_quarter"),
                    "dynamic_profile": spec.metadata.get("dynamic_profile", "classic_fill"),
                    "register_low": policy.register_low,
                    "register_high": policy.register_high,
                    "zone": zone,
                    "selected_lane": "classic_fill",
                    "max_region_span": policy.max_region_span,
                    "source_fill_offset_beats": offset,
                    "target_region_id": end_region.region_id,
                    **{k: v for k, v in spec.metadata.items() if k not in {"degree", "length_profile", "dynamic_profile", "register_low", "register_high"}},
                },
            )
            events.append(event)
            debug_notes.append({
                "region_id": active_region.region_id,
                "local_beat": active_local_beat,
                "source_offset": offset,
                "degree": token,
                "note": note,
            })

        for region_id, notes in region_notes.items():
            if not _span_ok(notes, policy.max_region_span):
                return [], {"region_id": region_id, "classic_fill_rejected": "post_span_guard", "notes": notes}
        return events, {
            "region_id": start_region.region_id,
            "candidate": candidate.name,
            "category": candidate.category,
            "notes": [item["note"] for item in debug_notes],
            "classic_fill_notes": debug_notes,
            "classic_fill_region_spans": {region_id: (max(notes) - min(notes) if notes else 0) for region_id, notes in region_notes.items()},
            "max_region_span": policy.max_region_span,
        }

    def _classic_fill_note_for_token(
        self,
        *,
        token: str,
        chord_symbol: str,
        reference: int,
        existing_region_notes: Sequence[int],
        policy: BassFoundationPolicy,
        end_region: HarmonicRegion,
    ) -> int:
        normalized = token.strip()
        if normalized in {"classic_connect_nextR", "connect_to_nextR", "approach_nextR"}:
            return _classic_connector_to_nextR(end_region, reference, policy, existing_region_notes)

        # Harmony owns symbolic degree pitch-class meaning.  Classic-fill keeps
        # only fill-local aliases / target-direction preferences here; it no
        # longer maintains a local degree-to-pitch-class table.
        pc = resolve_degree_token(
            chord_symbol=chord_symbol,
            token=normalized,
            next_chord_symbol=end_region.chord_symbol,
        ).pitch_class
        target = reference
        if normalized in {"Third", "classic_low3"}:
            target = reference + 4
        elif normalized in {"degree4", "scale4", "Fourth"}:
            target = reference + 1
        elif normalized in {"#4", "sharp4", "b5"}:
            target = reference + 1
        elif normalized == "Fifth":
            target = reference + 1
        return _note_for_pc_within_span_near(pc, target, policy, existing_region_notes)

    def _apply_root_echo_ornaments(
        self,
        *,
        region: HarmonicRegion,
        segment_events: list[PatternEvent],
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
        rng: random.Random,
        zone: str,
    ) -> tuple[list[PatternEvent], list[dict]]:
        if not policy.root_echo_enabled or policy.root_echo_probability <= 0 or not segment_events:
            return [], []
        occupied = {round(float(event.local_beat or 0.0), 3) for event in segment_events}
        segment_notes = [int(event.metadata["resolved_midi_note"]) for event in segment_events]
        root_pc = parse_chord(region.chord_symbol).root_pc
        repeated_root_start = _skeleton_starts_with_repeated_root(candidate)
        ornaments: list[PatternEvent] = []
        debug: list[dict] = []
        for local_beat in policy.root_echo_allowed_upbeats:
            if len(ornaments) >= policy.root_echo_max_per_region:
                break
            local_beat = float(local_beat)
            if local_beat >= region.duration_beats or round(local_beat, 3) in occupied:
                continue
            if abs(local_beat - 3.5) < 0.001:
                # Historical v6.2.7+ rule: no 4& root echo. Beat 4 is reserved for connector logic.
                continue
            anchor_beat = float(int(local_beat))
            anchor = _event_at_or_before(segment_events, anchor_beat)
            root_anchor = _root_anchor_event(segment_events)
            if anchor is None or root_anchor is None:
                continue
            probability = policy.root_echo_probability
            if region.duration_beats <= 2.0:
                probability *= policy.root_echo_compact_probability_multiplier
            if repeated_root_start and _same_swing_upbeat_slot(local_beat, 2.5):
                probability = max(probability, policy.root_echo_rr_start_3and_probability)
            if rng.random() >= probability:
                continue
            anchor_note = int(anchor.metadata["resolved_midi_note"])
            root_anchor_note = int(root_anchor.metadata["resolved_midi_note"])
            # DI/root echo must be the exact current-root note that started the
            # chord region.  Do not re-octavize it around the preceding anchor
            # note; that made some echoes sound like a different bass tone even
            # when the pitch class was technically the root.
            echo_note = root_anchor_note
            if echo_note % 12 != root_pc or not _span_ok(segment_notes + [echo_note], policy.max_region_span):
                continue
            event = PatternEvent(
                event_id=f"{region.region_id}_bass_foundation_root_echo_{len(ornaments)}_{int(local_beat * 100)}",
                track="bass",
                region_id=region.region_id,
                chord_symbol=region.chord_symbol,
                onset_beat=region.start_beat + local_beat,
                role="bass_note",
                expression_hint="bass_foundation_root_echo",
                pattern_id=f"{candidate.name}::root_echo",
                local_beat=local_beat,
                metadata={
                    "candidate": candidate.name,
                    "category": candidate.category,
                    "generation_domain": "bass_foundation",
                    "bass_foundation_generated": True,
                    "bass_foundation_ornament": True,
                    "ornament_type": "current_root_echo",
                    "degree": "R",
                    "resolved_midi_note": echo_note,
                    "next_chord_symbol": region.next_chord_symbol,
                    "region_duration_beats": region.duration_beats,
                    "length_profile": "short_pickup",
                    "dynamic_profile": "light",
                    "register_low": policy.register_low,
                    "register_high": policy.register_high,
                    "zone": zone,
                    "selected_lane": "root_echo",
                    "root_echo_probability": probability,
                    "root_echo_anchor_beat": anchor.local_beat,
                    "root_echo_anchor_note": anchor_note,
                    "root_echo_region_root_note": root_anchor_note,
                    "root_echo_same_as_region_root": echo_note == root_anchor_note,
                    "root_echo_swing_upbeat": _is_swing_upbeat(local_beat),
                    "timing_intent": "swing_upbeat",
                    "max_region_span": policy.max_region_span,
                },
            )
            ornaments.append(event)
            occupied.add(round(local_beat, 3))
            segment_notes.append(echo_note)
            debug.append({
                "local_beat": local_beat,
                "note": echo_note,
                "probability": probability,
                "anchor_beat": anchor.local_beat,
                "anchor_note": anchor_note,
                "region_root_note": root_anchor_note,
                "same_as_region_root": echo_note == root_anchor_note,
                "swing_upbeat": _is_swing_upbeat(local_beat),
            })
        return ornaments, debug

    def _events_from_notes(
        self,
        *,
        region: HarmonicRegion,
        candidate: PatternCandidate,
        specs,
        notes: list[int],
        policy: BassFoundationPolicy,
        extra_metadata: dict,
    ) -> tuple[list[PatternEvent], dict]:
        events: list[PatternEvent] = []
        for index, (spec, note) in enumerate(zip(specs, notes)):
            degree = str(spec.metadata.get("degree", "R"))
            dynamic_profile = str(spec.metadata.get("dynamic_profile", "downbeat" if spec.local_beat == 0.0 else "walk"))
            if _is_connector_degree(degree) or index == len(notes) - 1:
                dynamic_profile = str(spec.metadata.get("dynamic_profile", "connector"))
            events.append(
                PatternEvent(
                    event_id=f"{region.region_id}_bass_foundation_{candidate.name}_{index}",
                    track="bass",
                    region_id=region.region_id,
                    chord_symbol=region.chord_symbol,
                    onset_beat=region.start_beat + float(spec.local_beat),
                    role="bass_note",
                    expression_hint=spec.expression_hint,
                    pattern_id=candidate.name,
                    local_beat=float(spec.local_beat),
                    metadata={
                        "candidate": candidate.name,
                        "category": candidate.category,
                        "generation_domain": "bass_foundation",
                        "bass_foundation_generated": True,
                        "degree": degree,
                        "resolved_midi_note": note,
                        "next_chord_symbol": region.next_chord_symbol,
                        "region_duration_beats": region.duration_beats,
                        "length_profile": spec.metadata.get("length_profile", "walking_quarter"),
                        "dynamic_profile": dynamic_profile,
                        "register_low": policy.register_low,
                        "register_high": policy.register_high,
                        **extra_metadata,
                        **{k: v for k, v in spec.metadata.items() if k not in {"degree", "length_profile", "dynamic_profile", "register_low", "register_high"}},
                    },
                )
            )
        segment_debug = {
            "region_id": region.region_id,
            "chord_symbol": region.chord_symbol,
            "candidate": candidate.name,
            "notes": notes,
            **extra_metadata,
        }
        return events, segment_debug

    def _instantiate_body(
        self,
        region: HarmonicRegion,
        specs,
        policy: BassFoundationPolicy,
        start_note: int,
        allow_repetition: bool,
    ) -> list[tuple[int, int, int]]:
        pcs = [_resolve_pc(region, str(spec.metadata.get("degree", "R"))) for spec in specs]
        pools: list[list[int]] = [[start_note]]
        for spec, pc in zip(specs[1:], pcs[1:]):
            degree = str(spec.metadata.get("degree", "R"))
            if _normalize_degree_for_lane(degree) == "R":
                options = [start_note]
            else:
                options = _notes_for_pitch_class(pc, policy.register_low, policy.register_high)
            pools.append(options)
        instances: list[tuple[int, int, int]] = []
        for combo in itertools.product(*pools):
            notes = tuple(int(n) for n in combo)
            if max(notes) - min(notes) > policy.max_body_span:
                continue
            if not allow_repetition and (notes[0] == notes[1] or notes[1] == notes[2]):
                continue
            instances.append(notes)
        return sorted(set(instances))

    def _choose_instance_by_lane(
        self,
        instances: list[tuple[int, int, int]],
        start_note: int,
        zone: str,
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
        rng: random.Random,
    ) -> tuple[tuple[int, int, int], str, str, dict[str, float]]:
        buckets = {"upper": [], "lower": [], "mixed": []}
        for inst in instances:
            buckets[lane_of_instance(inst, start_note)].append(inst)
        lane_weights = effective_lane_weights_for_candidate(zone, candidate, policy)
        lanes = ["upper", "lower", "mixed"]
        weights = [lane_weights[lane] if buckets[lane] else 0.0 for lane in lanes]
        if sum(weights) <= 0:
            choice = rng.choice(instances)
            return choice, lane_of_instance(choice, start_note), lane_bias_label_for_candidate(candidate), lane_weights
        lane = _weighted_choice(lanes, weights, rng)
        if policy.lane_instance_selection == "legacy_random":
            choice = rng.choice(buckets[lane])
        else:
            choice = _weighted_instance_choice(buckets[lane], policy, rng)
        return choice, lane, lane_bias_label_for_candidate(candidate), lane_weights

    def _has_eligible_lane(
        self,
        instances: list[tuple[int, int, int]],
        start_note: int,
        zone: str,
        candidate: PatternCandidate,
        policy: BassFoundationPolicy,
    ) -> bool:
        buckets = {"upper": [], "lower": [], "mixed": []}
        for inst in instances:
            buckets[lane_of_instance(inst, start_note)].append(inst)
        lane_weights = effective_lane_weights_for_candidate(zone, candidate, policy)
        return any(lane_weights[lane] > 0 and buckets[lane] for lane in ("upper", "lower", "mixed"))

    def _choose_nextR_and_beat4(
        self,
        region: HarmonicRegion,
        beat3_note: int,
        policy: BassFoundationPolicy,
        rng: random.Random,
        disallow_current_root_pc: bool,
        current_region_notes: Sequence[int] = (),
    ) -> tuple[int, Beat4Choice]:
        region_anchor = list(current_region_notes) or [beat3_note]
        for nextR_note in _nextR_octave_candidates(_next_root_pc(region), beat3_note, policy, rng):
            candidates = self._generate_beat4_candidates(region, beat3_note, nextR_note, policy, disallow_current_root_pc)
            span_safe = [choice for choice in candidates if _span_ok(region_anchor + [choice.note], policy.max_region_span)]
            if span_safe:
                return nextR_note, _weighted_choice(span_safe, [c.weight for c in span_safe], rng)
        nextR_note = _nearest_note_for_pc(_next_root_pc(region), beat3_note, policy)
        fallback = beat3_note
        return nextR_note, Beat4Choice(fallback, "span_safe_repeat_fallback", 0.1, "fallback preserving one-octave region span")

    def _generate_beat4_candidates(
        self,
        region: HarmonicRegion,
        beat3_note: int,
        nextR_note: int,
        policy: BassFoundationPolicy,
        disallow_current_root_pc: bool,
    ) -> list[Beat4Choice]:
        chord = parse_chord(region.chord_symbol)
        candidates: list[Beat4Choice] = []

        def add(note: int, kind: str, weight: float, description: str, max_leap: int) -> None:
            if not (policy.register_low <= note <= policy.register_high):
                return
            if is_major_quality(region.chord_symbol) and _is_natural_fourth(region.chord_symbol, note):
                return
            if disallow_current_root_pc and note % 12 == chord.root_pc % 12:
                return
            if abs(note - beat3_note) > max_leap:
                return
            adjusted = weight * (policy.same_beat3_beat4_weight_multiplier if note == beat3_note else 1.0)
            if adjusted > 0:
                candidates.append(Beat4Choice(note=note, kind=kind, weight=adjusted, description=description))

        scale_notes: list[tuple[int, str]] = []
        for interval in (-2, -1, 1, 2):
            note = nextR_note + interval
            if policy.register_low <= note <= policy.register_high and note % 12 in _scale_pcs_for_chord(region.chord_symbol) and abs(note - beat3_note) <= 6:
                scale_notes.append((note, f"scaleNearNextR nextR{interval:+}"))
        deduped_scale = []
        seen = set()
        for note, label in scale_notes:
            if note not in seen:
                seen.add(note)
                deduped_scale.append((note, label))
        if deduped_scale:
            per = policy.connector_family_weights.get("scale_near_nextR", 40.0) / len(deduped_scale)
            for note, label in deduped_scale:
                add(note, "scale_near_nextR", per, label, max_leap=6)

        approach_weight = policy.connector_family_weights.get("approach_nextR", 40.0) / 2.0
        add(nextR_note - 1, "approach", approach_weight, "chromaticBelowNextR", max_leap=6)
        add(nextR_note + 1, "approach", approach_weight, "chromaticAboveNextR", max_leap=6)

        dom_notes = [(nextR_note - 5, "dominantConnection nextR-5"), (nextR_note + 7, "dominantConnection nextR+7")]
        legal_dom = [(note, label) for note, label in dom_notes if policy.register_low <= note <= policy.register_high and abs(note - beat3_note) <= 7]
        if legal_dom:
            per = policy.connector_family_weights.get("dominant_connection", 10.0) / len(legal_dom)
            for note, label in legal_dom:
                add(note, "dominant_connection", per, label, max_leap=7)

        merged: dict[tuple[int, str], Beat4Choice] = {}
        for candidate in candidates:
            key = (candidate.note, candidate.kind)
            old = merged.get(key)
            if old is None:
                merged[key] = candidate
            else:
                merged[key] = Beat4Choice(candidate.note, candidate.kind, old.weight + candidate.weight, old.description + "+" + candidate.description)
        return [candidate for candidate in merged.values() if candidate.weight > 0]


