from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Sequence

from jammate_engine.core.harmony.chord_parser import parse_chord
from jammate_engine.core.harmony.material import (
    is_major_quality as harmony_is_major_quality,
    is_six_quality as harmony_is_six_quality,
    is_tonic_major_like as harmony_is_tonic_major_like,
    normalize_degree_for_lane as harmony_normalize_degree_for_lane,
    resolve_degree_token,
    scale_pitch_classes,
)
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime import PatternCandidate, PatternEvent

from .policy import DEFAULT_LANE_WEIGHTS_BY_ZONE

def root_zone(note: int) -> str:
    if note <= 30:
        return "very_low"
    if note <= 35:
        return "low"
    if note <= 40:
        return "middle"
    if note <= 44:
        return "high"
    return "very_high"


def lane_of_instance(notes: tuple[int, int, int], root_note: int) -> str:
    signs = []
    for note in notes[1:]:
        if note > root_note:
            signs.append(1)
        elif note < root_note:
            signs.append(-1)
    if not signs:
        return "mixed"
    if all(sign > 0 for sign in signs):
        return "upper"
    if all(sign < 0 for sign in signs):
        return "lower"
    return "mixed"


def effective_lane_weights_for_candidate(zone: str, candidate: PatternCandidate, policy: BassFoundationPolicy) -> dict[str, float]:
    weights = dict(policy.lane_weights_by_zone.get(zone, DEFAULT_LANE_WEIGHTS_BY_ZONE.get(zone, DEFAULT_LANE_WEIGHTS_BY_ZONE["middle"])))
    for degree, strength in lane_bias_specs_for_candidate(candidate):
        multipliers = policy.degree_lane_multipliers.get(degree, {"upper": 1.0, "lower": 1.0, "mixed": 1.0})
        for lane in ("upper", "lower", "mixed"):
            weights[lane] = float(weights.get(lane, 0.0)) * (float(multipliers.get(lane, 1.0)) ** strength)
    # Previous-engine alignment: effective lane weights are exactly the
    # five-zone table multiplied by degree-specific lane multipliers.  Do not
    # apply additional V2 register-gravity caps here; they change the skeleton
    # occurrence distribution and were not part of the old Medium Swing bass.
    return {lane: max(0.0, float(weights.get(lane, 0.0))) for lane in ("upper", "lower", "mixed")}


def _weighted_instance_choice(instances: Sequence[tuple[int, int, int]], policy: BassFoundationPolicy, rng: random.Random) -> tuple[int, int, int]:
    if not instances:
        raise ValueError("instance choice received no candidates")
    weights: list[float] = []
    for notes in instances:
        total_motion = abs(notes[1] - notes[0]) + abs(notes[2] - notes[1])
        span = max(notes) - min(notes)
        center_penalty = abs(notes[2] - policy.register_center) * 0.18
        extreme_penalty = sum(1.5 for note in notes if note <= policy.register_low + 1 or note >= policy.register_high - 1)
        repeat_penalty = 2.5 if notes[0] == notes[1] or notes[1] == notes[2] else 0.0
        cost = total_motion + center_penalty + span * 0.35 + extreme_penalty + repeat_penalty
        weights.append(1.0 / max(0.1, cost))
    return _weighted_choice(list(instances), weights, rng)


def lane_bias_specs_for_candidate(candidate: PatternCandidate) -> list[tuple[str, float]]:
    degrees = tuple(candidate.metadata.get("skeleton_degrees", ()))
    if len(degrees) < 3:
        degrees = tuple(str(spec.metadata.get("degree", "R")) for spec in candidate.events[:3])
    if len(degrees) < 3:
        return []
    beat2 = _normalize_degree_for_lane(str(degrees[1]))
    beat3 = _normalize_degree_for_lane(str(degrees[2]))
    specs: list[tuple[str, float]] = []
    if beat2 != "R":
        specs.append((beat2, 1.0))
        if beat3 != "R":
            specs.append((beat3, 0.85))
    elif beat3 != "R":
        specs.append((beat3, 1.0))
    return specs


def lane_bias_label_for_candidate(candidate: PatternCandidate) -> str:
    specs = lane_bias_specs_for_candidate(candidate)
    return "none" if not specs else "+".join(f"{degree}@{strength:.2f}" for degree, strength in specs)


def _candidate_allowed_for_chord(candidate: PatternCandidate, chord_symbol: str) -> bool:
    degrees = tuple(candidate.metadata.get("skeleton_degrees", ()))
    if is_major_quality(chord_symbol) and "Fourth" in degrees[1:]:
        return False
    if is_six_quality(chord_symbol) and "Seventh" in degrees[1:]:
        return False
    resolved: dict[str, int] = {}
    fake_region = _FakeRegion(chord_symbol=chord_symbol, next_chord_symbol=chord_symbol)
    for degree in degrees[1:]:
        normalized = _normalize_degree_for_lane(str(degree))
        if normalized == "R":
            continue
        pc = _resolve_pc(fake_region, str(degree)) % 12
        old = resolved.get(normalized)
        if old is not None and old != pc:
            return False
        if pc in resolved.values() and normalized not in resolved:
            return False
        resolved[normalized] = pc
    return True


@dataclass(frozen=True)
class _FakeRegion:
    chord_symbol: str
    next_chord_symbol: str | None


def _skeleton_starts_with_repeated_root(candidate: PatternCandidate) -> bool:
    degrees = tuple(candidate.metadata.get("skeleton_degrees", ()))
    if len(degrees) >= 2:
        return degrees[0] == "R" and degrees[1] == "R"
    return len(candidate.events) >= 2 and str(candidate.events[0].metadata.get("degree")) == "R" and str(candidate.events[1].metadata.get("degree")) == "R"


def _choose_region_start_note(
    chord_symbol: str,
    policy: BassFoundationPolicy,
    previous_note: int | None,
    inherited_target_note: int | None,
    rng: random.Random,
) -> tuple[int, str, bool]:
    pc = parse_chord(chord_symbol).root_pc
    if (
        policy.target_continuity_enabled
        and inherited_target_note is not None
        and int(inherited_target_note) % 12 == pc % 12
        and policy.register_low <= int(inherited_target_note) <= policy.register_high
    ):
        return int(inherited_target_note), "inherited_previous_target_nextR_note", True
    note = _choose_start_root_note(chord_symbol, policy, previous_note, rng)
    source = "nearest_previous_note" if previous_note is not None else "initial_center_root"
    return note, source, inherited_target_note is None


def _choose_start_root_note(chord_symbol: str, policy: BassFoundationPolicy, previous_note: int | None, rng: random.Random) -> int:
    pc = parse_chord(chord_symbol).root_pc
    candidates = _notes_for_pitch_class(pc, policy.register_low, policy.register_high)
    if previous_note is not None:
        return min(candidates, key=lambda note: (abs(note - previous_note) * 0.82 + abs(note - policy.register_center) * 0.18, note))
    by_center = sorted(candidates, key=lambda note: (abs(note - policy.register_center), note))
    return by_center[0] if by_center else policy.register_center


def _next_root_pc(region) -> int:
    return parse_chord(region.next_chord_symbol or region.chord_symbol).root_pc


def _resolve_pc(region, token: str) -> int:
    return resolve_degree_token(chord_symbol=region.chord_symbol, token=token, next_chord_symbol=region.next_chord_symbol).pitch_class


def _notes_for_pitch_class(pitch_class: int, low: int, high: int) -> list[int]:
    notes = [note for note in range(low, high + 1) if note % 12 == pitch_class]
    if notes:
        return notes
    note = low + ((pitch_class - low) % 12)
    return [max(low, min(high, note))]


def _nearest_note_for_pc(pitch_class: int, reference: int, policy: BassFoundationPolicy) -> int:
    candidates = _notes_for_pitch_class(pitch_class, policy.register_low, policy.register_high)
    return min(candidates, key=lambda note: (abs(note - reference), abs(note - policy.register_center), note))


def _nextR_octave_candidates(target_pc: int, reference: int, policy: BassFoundationPolicy, rng: random.Random | None = None) -> list[int]:
    candidates = _notes_for_pitch_class(target_pc, policy.register_low, policy.register_high)
    by_distance: dict[int, list[int]] = {}
    for note in candidates:
        by_distance.setdefault(abs(note - reference), []).append(note)
    ordered: list[int] = []
    for distance in sorted(by_distance):
        group = by_distance[distance]
        if rng is not None:
            rng.shuffle(group)
        else:
            group = sorted(group)
        ordered.extend(group)
    return ordered



def _two_bar_tonic_scene_allowed(start_region: HarmonicRegion, mid_region: HarmonicRegion, end_region: HarmonicRegion) -> tuple[bool, str]:
    start_chord = parse_chord(start_region.chord_symbol)
    mid_chord = parse_chord(mid_region.chord_symbol)
    if start_chord.root_pc != mid_chord.root_pc:
        return False, "roots differ"
    if not _is_tonic_major_like(start_region.chord_symbol) or not _is_tonic_major_like(mid_region.chord_symbol):
        return False, "not two tonic-like major regions"
    if not (3.5 <= float(start_region.duration_beats) <= 4.5 and 3.5 <= float(mid_region.duration_beats) <= 4.5):
        return False, "not two full-bar regions"
    if end_region.start_beat <= mid_region.start_beat:
        return False, "missing forward target"
    return True, "two consecutive tonic-like major full-bar regions"


def _is_tonic_major_like(chord_symbol: str) -> bool:
    return harmony_is_tonic_major_like(chord_symbol)


def _note_for_pc_within_span_near(pitch_class: int, target: int, policy: BassFoundationPolicy, existing_notes: Sequence[int]) -> int:
    candidates = _notes_for_pitch_class(pitch_class, policy.register_low, policy.register_high)
    safe = [note for note in candidates if _span_ok(list(existing_notes) + [note], policy.max_region_span)]
    pool = safe or candidates
    return min(pool, key=lambda note: (abs(note - target), abs(note - policy.register_center), note))


def _classic_connector_to_nextR(end_region: HarmonicRegion, reference: int, policy: BassFoundationPolicy, existing_notes: Sequence[int]) -> int:
    next_pc = parse_chord(end_region.chord_symbol).root_pc
    candidate_pcs = ((next_pc - 1) % 12, (next_pc + 1) % 12, (next_pc - 2) % 12)
    candidates: list[int] = []
    for pc in candidate_pcs:
        candidates.extend(_notes_for_pitch_class(pc, policy.register_low, policy.register_high))
    safe = [note for note in candidates if _span_ok(list(existing_notes) + [note], policy.max_region_span)]
    pool = safe or candidates or _notes_for_pitch_class((next_pc - 1) % 12, policy.register_low, policy.register_high)
    return min(pool, key=lambda note: (abs(note - reference) * 0.45 + abs(note - policy.register_center) * 0.15, note))

def _span_ok(notes: Sequence[int], max_span: int) -> bool:
    if not notes:
        return True
    return max(notes) - min(notes) <= max_span



def _root_anchor_event(events: Sequence[PatternEvent]) -> PatternEvent | None:
    for event in sorted(events, key=lambda item: float(item.local_beat or 0.0)):
        if event.local_beat is not None and abs(float(event.local_beat)) < 0.001:
            return event
    return None


def _same_swing_upbeat_slot(value: float, expected: float) -> bool:
    return abs(float(value) - expected) < 0.02


def _is_swing_upbeat(value: float) -> bool:
    fractional = float(value) % 1.0
    return abs(fractional - 0.5) < 0.02

def _event_at_or_before(events: Sequence[PatternEvent], local_beat: float) -> PatternEvent | None:
    legal = [event for event in events if event.local_beat is not None and float(event.local_beat) <= local_beat]
    if not legal:
        return None
    return max(legal, key=lambda event: float(event.local_beat or 0.0))


def _nearest_note_for_pc_within_span(pitch_class: int, reference: int, policy: BassFoundationPolicy, existing_notes: Sequence[int]) -> int:
    candidates = _notes_for_pitch_class(pitch_class, policy.register_low, policy.register_high)
    safe = [note for note in candidates if _span_ok(list(existing_notes) + [note], policy.max_region_span)]
    pool = safe or candidates
    return min(pool, key=lambda note: (abs(note - reference), abs(note - policy.register_center), note))


def _weighted_choice(items, weights: Sequence[float], rng: random.Random):
    if not items:
        raise ValueError("weighted choice received no items")
    total = sum(max(0.0, float(weight)) for weight in weights)
    if total <= 0:
        return items[0]
    needle = rng.uniform(0, total)
    acc = 0.0
    for item, weight in zip(items, weights):
        acc += max(0.0, float(weight))
        if acc >= needle:
            return item
    return items[-1]


def _nested_float_dict(raw, default: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    result = {key: dict(value) for key, value in default.items()}
    for key, value in dict(raw or {}).items():
        result[str(key)] = {inner_key: float(inner_value) for inner_key, inner_value in dict(value).items()}
    return result


def _normalize_degree_for_lane(degree: str) -> str:
    return harmony_normalize_degree_for_lane(degree)


def _is_connector_degree(degree: str) -> bool:
    normalized = degree.lower()
    return "nextr" in normalized or "next_root" in normalized or "approach" in normalized or "dominant" in normalized or "scale_near" in normalized or "beat4" in normalized


def is_major_quality(chord_symbol: str) -> bool:
    return harmony_is_major_quality(chord_symbol)


def is_six_quality(chord_symbol: str) -> bool:
    return harmony_is_six_quality(chord_symbol)


def _is_natural_fourth(chord_symbol: str, note: int) -> bool:
    return note % 12 == (parse_chord(chord_symbol).root_pc + 5) % 12


def _scale_pcs_for_chord(chord_symbol: str) -> set[int]:
    return scale_pitch_classes(chord_symbol)
