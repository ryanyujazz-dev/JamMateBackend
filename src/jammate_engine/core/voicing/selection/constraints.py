from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from ..policy import VoicingPolicy


LOW_REGISTER_MUD_THRESHOLD = 52
MIN_LOW_INTERVAL_SEMITONES = 5
LOW_REGISTER_SINGLE_NOTE_THRESHOLD = 40
MAX_NOTES_BELOW_LOW_REGISTER_SINGLE_NOTE_THRESHOLD = 1
LOW_REGISTER_SINGLE_NOTE_GUARD_VERSION = "v2_2_89"


def is_in_range(note: int, low: int, high: int) -> bool:
    return low <= note <= high


@dataclass(frozen=True)
class RegisterGuardResult:
    """Diagnostic register / span / muddy-low-interval guard result.

    This is a V2 contract object.  It makes register safety inspectable without
    changing style vocabulary or re-deciding voicing content.  Candidate
    generation may attach this object to metadata; scoring can read the same
    fields later without inventing a second register model.
    """

    notes: tuple[int, ...]
    register_low: int
    register_high: int
    comfort_register_low: int
    comfort_register_high: int
    top_voice_low: int
    top_voice_high: int
    max_voicing_span: int
    low_register_mud_threshold: int = LOW_REGISTER_MUD_THRESHOLD
    min_low_interval_semitones: int = MIN_LOW_INTERVAL_SEMITONES
    low_register_single_note_threshold: int = LOW_REGISTER_SINGLE_NOTE_THRESHOLD
    max_notes_below_low_register_single_note_threshold: int = MAX_NOTES_BELOW_LOW_REGISTER_SINGLE_NOTE_THRESHOLD
    in_register: bool = True
    out_of_range_notes: tuple[int, ...] = ()
    span: int = 0
    span_ok: bool = True
    lowest_interval: int | None = None
    muddy_low_interval_ok: bool = True
    low_register_single_note_count: int = 0
    low_register_single_note_ok: bool = True
    top_note: int | None = None
    top_voice_in_range: bool = True
    average_pitch: float | None = None
    average_in_comfort_register: bool = True
    passed: bool = True
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "notes": list(self.notes),
            "register_low": self.register_low,
            "register_high": self.register_high,
            "comfort_register_low": self.comfort_register_low,
            "comfort_register_high": self.comfort_register_high,
            "top_voice_low": self.top_voice_low,
            "top_voice_high": self.top_voice_high,
            "max_voicing_span": self.max_voicing_span,
            "low_register_mud_threshold": self.low_register_mud_threshold,
            "min_low_interval_semitones": self.min_low_interval_semitones,
            "low_register_single_note_guard_version": LOW_REGISTER_SINGLE_NOTE_GUARD_VERSION,
            "low_register_single_note_threshold": self.low_register_single_note_threshold,
            "max_notes_below_low_register_single_note_threshold": self.max_notes_below_low_register_single_note_threshold,
            "in_register": self.in_register,
            "out_of_range_notes": list(self.out_of_range_notes),
            "span": self.span,
            "span_ok": self.span_ok,
            "lowest_interval": self.lowest_interval,
            "muddy_low_interval_ok": self.muddy_low_interval_ok,
            "low_register_single_note_count": self.low_register_single_note_count,
            "low_register_single_note_ok": self.low_register_single_note_ok,
            "top_note": self.top_note,
            "top_voice_in_range": self.top_voice_in_range,
            "average_pitch": round(self.average_pitch, 3) if self.average_pitch is not None else None,
            "average_in_comfort_register": self.average_in_comfort_register,
            "passed": self.passed,
            "reasons": list(self.reasons),
        }


def evaluate_register_guard(
    notes: Iterable[int],
    policy: VoicingPolicy,
    *,
    low_register_mud_threshold: int = LOW_REGISTER_MUD_THRESHOLD,
    min_low_interval_semitones: int = MIN_LOW_INTERVAL_SEMITONES,
    low_register_single_note_threshold: int | None = None,
    max_notes_below_low_register_single_note_threshold: int | None = None,
) -> RegisterGuardResult:
    """Evaluate absolute register, voicing span, top voice, and mud risk.

    The low-register mud guard is intentionally conservative: if the lowest
    note is in the low/mid-low piano range and the next voice sits too close to
    it, the result is marked as a mud risk.  v2_2_89 adds a generic single-low-note
    guard: below the policy threshold, only one foundation note may appear. This
    expresses the project-level rule that low-register density must thin out
    before upper-color/upper-structure material is stacked above it. The function
    only reports the condition; caller code decides whether it is a hard filter
    or a soft score.
    """

    metadata = dict(getattr(policy, "metadata", None) or {})
    if low_register_single_note_threshold is None:
        low_register_single_note_threshold = int(
            metadata.get(
                "low_register_single_note_threshold",
                metadata.get("spread_low_register_density_threshold", LOW_REGISTER_SINGLE_NOTE_THRESHOLD),
            )
        )
    if max_notes_below_low_register_single_note_threshold is None:
        max_notes_below_low_register_single_note_threshold = int(
            metadata.get(
                "max_notes_below_low_register_single_note_threshold",
                metadata.get(
                    "spread_low_register_density_max_notes_below",
                    MAX_NOTES_BELOW_LOW_REGISTER_SINGLE_NOTE_THRESHOLD,
                ),
            )
        )

    sorted_notes = tuple(sorted(int(note) for note in notes))
    if not sorted_notes:
        return RegisterGuardResult(
            notes=(),
            register_low=policy.register_low,
            register_high=policy.register_high,
            comfort_register_low=policy.comfort_register_low,
            comfort_register_high=policy.comfort_register_high,
            top_voice_low=policy.top_voice_low,
            top_voice_high=policy.top_voice_high,
            max_voicing_span=policy.max_voicing_span,
            low_register_mud_threshold=low_register_mud_threshold,
            min_low_interval_semitones=min_low_interval_semitones,
            low_register_single_note_threshold=int(low_register_single_note_threshold),
            max_notes_below_low_register_single_note_threshold=int(max_notes_below_low_register_single_note_threshold),
            in_register=False,
            span_ok=False,
            top_voice_in_range=False,
            average_in_comfort_register=False,
            passed=False,
            reasons=("empty_voicing",),
        )

    out_of_range = tuple(note for note in sorted_notes if not is_in_range(note, policy.register_low, policy.register_high))
    in_register = not out_of_range
    span = sorted_notes[-1] - sorted_notes[0]
    span_ok = span <= policy.max_voicing_span
    top = sorted_notes[-1]
    top_voice_in_range = policy.top_voice_low <= top <= policy.top_voice_high
    average = sum(sorted_notes) / len(sorted_notes)
    average_in_comfort = policy.comfort_register_low <= average <= policy.comfort_register_high

    lowest_interval: int | None = None
    muddy_low_interval_ok = True
    if len(sorted_notes) >= 2:
        lowest_interval = sorted_notes[1] - sorted_notes[0]
        if sorted_notes[0] < low_register_mud_threshold and lowest_interval < min_low_interval_semitones:
            muddy_low_interval_ok = False

    low_register_single_note_count = sum(1 for note in sorted_notes if note < int(low_register_single_note_threshold))
    low_register_single_note_ok = low_register_single_note_count <= int(max_notes_below_low_register_single_note_threshold)

    reasons: list[str] = []
    if not in_register:
        reasons.append("outside_absolute_register")
    if not span_ok:
        reasons.append("span_exceeds_max_voicing_span")
    if not muddy_low_interval_ok:
        reasons.append("muddy_low_interval")
    if not top_voice_in_range:
        reasons.append("top_voice_outside_target")
    if not low_register_single_note_ok:
        reasons.append("low_register_single_note_guard")
    if not average_in_comfort:
        reasons.append("average_outside_comfort_register")

    passed = in_register and span_ok and muddy_low_interval_ok and low_register_single_note_ok
    if passed and not reasons:
        reasons.append("ok")

    return RegisterGuardResult(
        notes=sorted_notes,
        register_low=policy.register_low,
        register_high=policy.register_high,
        comfort_register_low=policy.comfort_register_low,
        comfort_register_high=policy.comfort_register_high,
        top_voice_low=policy.top_voice_low,
        top_voice_high=policy.top_voice_high,
        max_voicing_span=policy.max_voicing_span,
        low_register_mud_threshold=low_register_mud_threshold,
        min_low_interval_semitones=min_low_interval_semitones,
        low_register_single_note_threshold=int(low_register_single_note_threshold),
        max_notes_below_low_register_single_note_threshold=int(max_notes_below_low_register_single_note_threshold),
        in_register=in_register,
        out_of_range_notes=out_of_range,
        span=span,
        span_ok=span_ok,
        lowest_interval=lowest_interval,
        muddy_low_interval_ok=muddy_low_interval_ok,
        low_register_single_note_count=low_register_single_note_count,
        low_register_single_note_ok=low_register_single_note_ok,
        top_note=top,
        top_voice_in_range=top_voice_in_range,
        average_pitch=average,
        average_in_comfort_register=average_in_comfort,
        passed=passed,
        reasons=tuple(reasons),
    )
