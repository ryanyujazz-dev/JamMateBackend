from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GestureKind(str, Enum):
    """Core gesture families.

    Gesture names are intentionally musical/projection contracts, not final
    MIDI rendering instructions. Do not use the traditional block-chord term here; the safe
    neutral name for all voices sounding together is "simultaneous_onset".
    """

    SIMULTANEOUS_ONSET = "simultaneous_onset"
    ROLLED_ONSET = "rolled_onset"
    ARPEGGIATED_ONSET = "arpeggiated_onset"
    BROKEN_CHORD = "broken_chord"
    INNER_MOVEMENT = "inner_movement"
    FILL = "fill"


class ProjectionRefPrefix(str, Enum):
    """Optional explicit prefixes for projection-map references."""

    VOICE = "voice_ref"
    GROUP = "group_ref"


class OnsetMode(str, Enum):
    """Onset projection mode used by realization.

    These names describe how voicing voices are projected over time. They are
    separate from traditional jazz "block chord" terminology.
    """

    SIMULTANEOUS_ONSET = GestureKind.SIMULTANEOUS_ONSET.value
    ROLLED_ONSET = GestureKind.ROLLED_ONSET.value
    ARPEGGIATED_ONSET = GestureKind.ARPEGGIATED_ONSET.value
    BROKEN_CHORD = GestureKind.BROKEN_CHORD.value


_FORBIDDEN_CONCRETE_KEYS = {
    "midi_note",
    "midi_notes",
    "pitch",
    "pitches",
    "frequency",
    "frequencies",
    "velocity",
    "duration",
    "duration_beats",
    "pedal",
}


def _find_forbidden_keys(value: Any, path: str = "metadata") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_CONCRETE_KEYS:
                found.append(f"{path}.{key_text}")
            found.extend(_find_forbidden_keys(child, f"{path}.{key_text}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_keys(child, f"{path}[{index}]"))
    return tuple(found)


def normalize_gesture_kind(value: GestureKind | str) -> GestureKind:
    if isinstance(value, GestureKind):
        return value
    text = str(value)
    for kind in GestureKind:
        if text == kind.value or text == kind.name:
            return kind
    raise ValueError(f"Unknown gesture kind: {value!r}")


@dataclass(frozen=True)
class GestureRequest:
    """Pitchless request for projecting an event into voiced material.

    A style may request a gesture family and abstract voice-order preferences,
    but it must not provide concrete MIDI pitches, final durations, velocities,
    or pedal decisions here.
    """

    kind: GestureKind | str = GestureKind.SIMULTANEOUS_ONSET
    voice_order: tuple[str, ...] = field(default_factory=tuple)
    onset_offsets_beats: tuple[float, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = normalize_gesture_kind(self.kind)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "voice_order", tuple(self.voice_order))
        object.__setattr__(self, "onset_offsets_beats", tuple(float(x) for x in self.onset_offsets_beats))

        forbidden = _find_forbidden_keys(self.metadata)
        if forbidden:
            joined = ", ".join(forbidden)
            raise ValueError(f"GestureRequest must stay pitchless/expressionless; forbidden concrete keys: {joined}")

    @property
    def gesture_type(self) -> str:
        return self.kind.value

    @property
    def projection_refs(self) -> tuple[str, ...]:
        """Ordered abstract voice/group references requested by this gesture.

        ``voice_order`` is retained as the stable constructor field for backward
        compatibility.  Semantically, its values are projection refs such as
        ``lowest``, ``top``, ``inner_1``, ``support_group`` or
        ``group_ref:projection_group``.  Realization resolves them against the
        already-selected ``VoicingPlan.projection_map``; it must not reselect
        pitch content.
        """

        return self.voice_order


Gesture = GestureRequest


def gesture_request(
    kind: GestureKind | str = GestureKind.SIMULTANEOUS_ONSET,
    *,
    voice_order: tuple[str, ...] = (),
    onset_offsets_beats: tuple[float, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> GestureRequest:
    return GestureRequest(
        kind=kind,
        voice_order=voice_order,
        onset_offsets_beats=onset_offsets_beats,
        metadata=dict(metadata or {}),
    )


def simultaneous_onset(*, metadata: dict[str, Any] | None = None) -> GestureRequest:
    return gesture_request(GestureKind.SIMULTANEOUS_ONSET, metadata=metadata)


def rolled_onset(
    *,
    voice_order: tuple[str, ...] = ("lowest", "inner", "top"),
    onset_offsets_beats: tuple[float, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> GestureRequest:
    return gesture_request(
        GestureKind.ROLLED_ONSET,
        voice_order=voice_order,
        onset_offsets_beats=onset_offsets_beats,
        metadata=metadata,
    )


def arpeggiated_onset(
    *,
    voice_order: tuple[str, ...] = ("lowest", "inner", "top"),
    onset_offsets_beats: tuple[float, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> GestureRequest:
    return gesture_request(
        GestureKind.ARPEGGIATED_ONSET,
        voice_order=voice_order,
        onset_offsets_beats=onset_offsets_beats,
        metadata=metadata,
    )
