from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_engine.core.gestures.gesture import GestureRequest, gesture_request
from jammate_engine.core.harmony.harmonic_region import HarmonicRegion

from .beat1_movability import Beat1Movability
from .pattern_event import PatternEvent
from .pattern_plan import PatternPlan
from .tail_policy import TailPolicy


PATTERN_RUNTIME_CONTRACT_VERSION = "v2_0_42"

_FORBIDDEN_PATTERN_CONCRETE_KEYS = {
    "midi_note",
    "midi_notes",
    "note",
    "notes",
    "pitch",
    "pitches",
    "frequency",
    "frequencies",
    "velocity",
    "duration",
    "duration_beats",
    "pedal",
}


def _find_forbidden_pattern_keys(value: Any, path: str = "metadata") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_PATTERN_CONCRETE_KEYS:
                found.append(f"{path}.{key_text}")
            found.extend(_find_forbidden_pattern_keys(child, f"{path}.{key_text}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_pattern_keys(child, f"{path}[{index}]"))
    return tuple(found)


@dataclass(frozen=True)
class PatternEventSpec:
    """Local, pitchless event inside a PatternCandidate.

    `local_beat` is measured from the start of the HarmonicRegion. A value of
    2.5 means beat 3& in a 4/4 bar/region.

    `gesture` is optional but preferred for harmonic events. `gesture_type`
    remains as a compatibility shortcut and is normalized into a GestureRequest
    during instantiation.
    """

    track: str
    local_beat: float
    role: str
    gesture_type: str = "simultaneous_onset"
    gesture: GestureRequest | None = None
    expression_hint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        forbidden = _find_forbidden_pattern_keys(self.metadata)
        if forbidden:
            joined = ", ".join(forbidden)
            raise ValueError(f"PatternEventSpec must stay pitchless/expression-profile-only; forbidden concrete keys: {joined}")


@dataclass(frozen=True)
class PatternCandidate:
    """Style-owned pitchless pattern candidate.

    A candidate may describe rhythm, roles, gesture requests, tail availability,
    beat-1 movability, category, and weight. It must not contain concrete MIDI
    pitches or final performance values.
    """

    name: str
    weight: float
    category: str
    events: tuple[PatternEventSpec, ...]
    default_gesture_type: str = "simultaneous_onset"
    expression_profile_id: str | None = None
    binding_strength: str = "soft"
    tail_policy: TailPolicy | None = None
    beat1_movability: Beat1Movability = field(default_factory=Beat1Movability)
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def rhythm_beats(self) -> tuple[float, ...]:
        return tuple(spec.local_beat for spec in self.events)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "category": self.category,
            "rhythm_beats": list(self.rhythm_beats),
            "event_count": len(self.events),
            "default_gesture_type": self.default_gesture_type,
            "expression_profile_id": self.expression_profile_id,
            "binding_strength": self.binding_strength,
            "beat1_movability": {
                "movable": self.beat1_movability.movable,
                "requires_previous_tail_space": self.beat1_movability.requires_previous_tail_space,
                "target_offset_beats": self.beat1_movability.target_offset_beats,
                "suppress_original": self.beat1_movability.suppress_original,
                "tie_from_previous": self.beat1_movability.tie_from_previous,
                "reason": self.beat1_movability.reason,
            },
            "tail_policy": None
            if self.tail_policy is None
            else {
                "beat4_available": self.tail_policy.beat4_available,
                "beat4_and_available": self.tail_policy.beat4_and_available,
                "can_receive_next_chord_anticipation": self.tail_policy.can_receive_next_chord_anticipation,
                "occupied_local_beats": list(self.tail_policy.occupied_local_beats),
            },
            "events": [
                {
                    "track": spec.track,
                    "local_beat": spec.local_beat,
                    "role": spec.role,
                    "gesture_type": (spec.gesture.gesture_type if spec.gesture else spec.gesture_type),
                    "projection_refs": list(spec.gesture.projection_refs) if spec.gesture else [],
                    "expression_hint": spec.expression_hint,
                    "metadata": dict(spec.metadata),
                }
                for spec in self.events
            ],
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    def instantiate(self, region: HarmonicRegion) -> PatternPlan:
        instantiated: list[PatternEvent] = []
        for index, spec in enumerate(self.events):
            gesture = spec.gesture or gesture_request(spec.gesture_type or self.default_gesture_type)
            expression_hint = spec.expression_hint or self.expression_profile_id
            event_id = f"{region.region_id}_{self.name}_{index}"
            instantiated.append(
                PatternEvent(
                    event_id=event_id,
                    track=spec.track,
                    region_id=region.region_id,
                    chord_symbol=region.chord_symbol,
                    onset_beat=region.start_beat + float(spec.local_beat),
                    role=spec.role,
                    gesture_type=gesture.gesture_type,
                    gesture=gesture,
                    expression_hint=expression_hint,
                    pattern_id=self.name,
                    local_beat=float(spec.local_beat),
                    metadata={
                        "candidate": self.name,
                        "category": self.category,
                        "binding_strength": self.binding_strength,
                        "previous_chord_symbol": region.metadata.get("previous_chord_symbol"),
                        "next_chord_symbol": region.next_chord_symbol,
                        "home_key": region.metadata.get("home_key") or region.metadata.get("key"),
                        "region_duration_beats": region.duration_beats,
                        "region_section_id": region.section_id,
                        "region_section_label": region.section_label,
                        "region_phrase": region.phrase,
                        "region_section_role": region.section_role,
                        "region_chorus_index": region.chorus_index,
                        "region_total_choruses": region.total_choruses,
                        "region_bar_index": region.bar_index,
                        "region_source_bar_index": region.source_bar_index,
                        "region_written_bar_index": region.written_bar_index,
                        "region_performance_bar_index": region.performance_bar_index,
                        "region_form_index": region.form_index,
                        "region_is_first_bar_of_section": region.is_first_bar_of_section,
                        "region_is_last_bar_of_section": region.is_last_bar_of_section,
                        "region_is_first_bar_of_chorus": region.is_first_bar_of_chorus,
                        "region_is_last_bar_of_chorus": region.is_last_bar_of_chorus,
                        **dict(spec.metadata),
                    },
                )
            )
        tail_policy = self.tail_policy or TailPolicy.from_local_beats(self.rhythm_beats)
        return PatternPlan(
            events=instantiated,
            tail_policy=tail_policy,
            beat1_movability=self.beat1_movability,
            selected_candidate=self.name,
            metadata={"category": self.category, "tags": list(self.tags), **dict(self.metadata)},
        )


def event_spec(
    *,
    track: str,
    beat: float,
    role: str,
    gesture_type: str = "simultaneous_onset",
    gesture: GestureRequest | None = None,
    expression_hint: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PatternEventSpec:
    if gesture is not None:
        gesture_type = gesture.gesture_type
    return PatternEventSpec(
        track=track,
        local_beat=float(beat),
        role=role,
        gesture_type=gesture_type,
        gesture=gesture,
        expression_hint=expression_hint,
        metadata=dict(metadata or {}),
    )
