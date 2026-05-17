from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Any

from ..runtime.state import VoicingState


def sorted_notes(notes: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(int(note) for note in notes))


def top_note(notes: list[int] | tuple[int, ...]) -> int | None:
    ordered = sorted_notes(notes)
    return ordered[-1] if ordered else None


def average_pitch(notes: list[int] | tuple[int, ...]) -> float:
    ordered = sorted_notes(notes)
    if not ordered:
        return 0.0
    return sum(ordered) / len(ordered)


@dataclass(frozen=True)
class SetBasedVoiceLeadingDistance:
    """Birth/death-aware set distance for unequal-size voicing groups.

    Upper SPREAD groups may move between 3-note and 4-note projections.  Treating
    them as index-aligned lists makes the extra color note look like every voice
    moved.  This profile keeps common/nearest tones matched and prices inserted
    or released color voices separately.
    """

    distance: float
    matched_pairs: tuple[tuple[int, int], ...]
    inserted_notes: tuple[int, ...]
    released_notes: tuple[int, ...]
    common_tones: int
    previous_count: int
    current_count: int
    birth_death_penalty: float

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "version": "v2_2_81",
            "algorithm": "set_based_partial_assignment_birth_death_aware",
            "distance": round(float(self.distance), 3),
            "matched_pairs": [[int(left), int(right)] for left, right in self.matched_pairs],
            "inserted_notes": list(self.inserted_notes),
            "released_notes": list(self.released_notes),
            "common_tones": int(self.common_tones),
            "previous_count": int(self.previous_count),
            "current_count": int(self.current_count),
            "birth_death_penalty": float(self.birth_death_penalty),
            "handles_unequal_note_counts": True,
            "does_not_zip_by_index": True,
        }


def set_based_voice_leading_distance(
    previous_notes: list[int] | tuple[int, ...],
    current_notes: list[int] | tuple[int, ...],
    *,
    birth_death_penalty: float = 3.0,
) -> SetBasedVoiceLeadingDistance:
    """Return a partial-assignment distance for note sets of any size.

    The dynamic program has three actions: match one previous note to one
    current note, release one previous note, or insert one current note.  Exact
    common tones naturally cost zero; extra color tones cost a small birth/death
    penalty rather than forcing unrelated voices to move by index.
    """

    previous = tuple(sorted(int(note) for note in previous_notes))
    current = tuple(sorted(int(note) for note in current_notes))
    if not previous and not current:
        return SetBasedVoiceLeadingDistance(0.0, (), (), (), 0, 0, 0, float(birth_death_penalty))
    if not previous:
        inserted = tuple(current)
        return SetBasedVoiceLeadingDistance(
            float(len(inserted)) * float(birth_death_penalty),
            (),
            inserted,
            (),
            0,
            0,
            len(current),
            float(birth_death_penalty),
        )
    if not current:
        released = tuple(previous)
        return SetBasedVoiceLeadingDistance(
            float(len(released)) * float(birth_death_penalty),
            (),
            (),
            released,
            0,
            len(previous),
            0,
            float(birth_death_penalty),
        )

    # Dynamic programming over sorted pitches.  Sorted matching preserves voice
    # order on a 1D pitch axis while still allowing insert/release operations.
    m, n = len(previous), len(current)
    dp: list[list[tuple[float, tuple[str, int | None, int | None] | None]]] = [
        [(0.0, None) for _ in range(n + 1)] for _ in range(m + 1)
    ]
    for i in range(1, m + 1):
        dp[i][0] = (dp[i - 1][0][0] + float(birth_death_penalty), ("release", previous[i - 1], None))
    for j in range(1, n + 1):
        dp[0][j] = (dp[0][j - 1][0] + float(birth_death_penalty), ("insert", None, current[j - 1]))
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match_cost = dp[i - 1][j - 1][0] + abs(previous[i - 1] - current[j - 1])
            release_cost = dp[i - 1][j][0] + float(birth_death_penalty)
            insert_cost = dp[i][j - 1][0] + float(birth_death_penalty)
            choices = (
                (match_cost, ("match", previous[i - 1], current[j - 1])),
                (release_cost, ("release", previous[i - 1], None)),
                (insert_cost, ("insert", None, current[j - 1])),
            )
            # Prefer true matches on ties so common tones are visible in audit.
            dp[i][j] = min(choices, key=lambda item: (item[0], 0 if item[1][0] == "match" else 1))

    matched: list[tuple[int, int]] = []
    inserted: list[int] = []
    released: list[int] = []
    i, j = m, n
    while i > 0 or j > 0:
        _, action = dp[i][j]
        if action is None:
            break
        kind, left, right = action
        if kind == "match":
            matched.append((int(left), int(right)))
            i -= 1
            j -= 1
        elif kind == "release":
            released.append(int(left))
            i -= 1
        else:
            inserted.append(int(right))
            j -= 1
    matched.reverse()
    inserted.reverse()
    released.reverse()
    common = sum(1 for left, right in matched if int(left) == int(right))
    return SetBasedVoiceLeadingDistance(
        float(dp[m][n][0]),
        tuple(matched),
        tuple(inserted),
        tuple(released),
        int(common),
        len(previous),
        len(current),
        float(birth_death_penalty),
    )


def voice_leading_distance(previous: tuple[int, ...], current: tuple[int, ...]) -> float:
    """Return a lightweight voice-leading distance in semitones.

    This intentionally avoids becoming a full voice-leading engine. It gives the
    weighted selector enough information to prefer nearby shapes over repeated
    octave jumps while still allowing style policies to choose content families.
    """

    if not previous or not current:
        return 0.0
    previous_sorted = sorted_notes(previous)
    current_sorted = sorted_notes(current)
    total = 0.0
    pairs = 0
    for left, right in zip_longest(previous_sorted, current_sorted):
        if left is None or right is None:
            total += 8.0
        else:
            total += abs(left - right)
        pairs += 1
    return total / max(1, pairs)


def common_tone_count(previous: tuple[int, ...], current: tuple[int, ...]) -> int:
    """Return exact pitch common-tone count for the current register realization."""

    return len(set(sorted_notes(previous)).intersection(sorted_notes(current)))


def top_voice_motion(state: VoicingState, current_notes: list[int] | tuple[int, ...]) -> int | None:
    current_top = top_note(current_notes)
    if state.previous_top_note is None or current_top is None:
        return None
    return current_top - state.previous_top_note


def repeated_top_voice_count(state: VoicingState, current_top: int | None, *, lookback: int = 3) -> int:
    if current_top is None or not state.recent_top_notes:
        return 0
    recent = state.recent_top_notes[-max(1, int(lookback)) :]
    return sum(1 for note in recent if note == current_top)


def repeated_top_voice_penalty(state: VoicingState, current_top: int | None) -> float:
    return float(repeated_top_voice_count(state, current_top)) * 0.35


@dataclass(frozen=True)
class VoiceLeadingProfile:
    """Inspectable voice-leading state for one candidate.

    This is a diagnostic contract, not a full voice-leading engine. It gives the
    selector, tests, audit scripts, and future LLM tooling a stable summary of
    why a candidate is considered smooth, jumpy, repeated, or top-line-safe.
    """

    has_previous: bool
    previous_notes: tuple[int, ...]
    current_notes: tuple[int, ...]
    previous_top_note: int | None
    current_top_note: int | None
    previous_low_note: int | None
    current_low_note: int | None
    voice_leading_distance: float | None
    common_tones: int
    top_voice_motion: int | None
    top_voice_abs_motion: int | None
    top_voice_direction: str | None
    top_voice_repeated_recent_count: int
    top_voice_leap_exceeds_max: bool
    smoothness_label: str

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "has_previous": self.has_previous,
            "previous_notes": list(self.previous_notes),
            "current_notes": list(self.current_notes),
            "previous_top_note": self.previous_top_note,
            "current_top_note": self.current_top_note,
            "previous_low_note": self.previous_low_note,
            "current_low_note": self.current_low_note,
            "voice_leading_distance": round(self.voice_leading_distance, 3) if self.voice_leading_distance is not None else None,
            "common_tones": self.common_tones,
            "top_voice_motion": self.top_voice_motion,
            "top_voice_abs_motion": self.top_voice_abs_motion,
            "top_voice_direction": self.top_voice_direction,
            "top_voice_repeated_recent_count": self.top_voice_repeated_recent_count,
            "top_voice_leap_exceeds_max": self.top_voice_leap_exceeds_max,
            "smoothness_label": self.smoothness_label,
        }


def analyze_voice_leading(
    current_notes: list[int] | tuple[int, ...],
    state: VoicingState | None = None,
    *,
    max_top_voice_leap: int | None = None,
) -> VoiceLeadingProfile:
    """Return an inspectable profile for previous-state continuity scoring."""

    state = state or VoicingState.empty()
    current = sorted_notes(current_notes)
    current_top = top_note(current)
    current_low = current[0] if current else None
    motion = top_voice_motion(state, current)
    abs_motion = abs(motion) if motion is not None else None
    direction = None
    if motion is not None:
        if motion > 0:
            direction = "up"
        elif motion < 0:
            direction = "down"
        else:
            direction = "repeat"

    distance = voice_leading_distance(state.previous_notes, current) if state.has_previous else None
    if distance is None:
        label = "no_previous_state"
    elif distance <= 3.0:
        label = "smooth"
    elif distance <= 6.0:
        label = "moderate"
    else:
        label = "jumpy"

    return VoiceLeadingProfile(
        has_previous=state.has_previous,
        previous_notes=tuple(state.previous_notes),
        current_notes=current,
        previous_top_note=state.previous_top_note,
        current_top_note=current_top,
        previous_low_note=state.previous_low_note,
        current_low_note=current_low,
        voice_leading_distance=distance,
        common_tones=common_tone_count(state.previous_notes, current) if state.has_previous else 0,
        top_voice_motion=motion,
        top_voice_abs_motion=abs_motion,
        top_voice_direction=direction,
        top_voice_repeated_recent_count=repeated_top_voice_count(state, current_top),
        top_voice_leap_exceeds_max=bool(abs_motion is not None and max_top_voice_leap is not None and abs_motion > max_top_voice_leap),
        smoothness_label=label,
    )
