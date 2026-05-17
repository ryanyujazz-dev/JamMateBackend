from __future__ import annotations

from jammate_engine.core.harmony.material import (
    COMPACT_DEGREE_TO_SEMITONE as DEGREE_TO_SEMITONE,
    DegreeResolution as BassDegreeResolution,
    resolve_degree_token,
)

# Compatibility facade kept in realization for existing callers.  The symbolic
# degree / pitch-class contract now lives in core.harmony.material.  Realization
# still owns register projection helpers because octave choice is not harmony.


def resolve_bass_degree_token(
    *,
    chord_symbol: str,
    token: str | None,
    next_chord_symbol: str | None = None,
) -> BassDegreeResolution:
    return resolve_degree_token(chord_symbol=chord_symbol, token=token, next_chord_symbol=next_chord_symbol)


def pitch_class_to_register_note(
    pitch_class: int,
    *,
    low: int = 26,
    high: int = 48,
    previous_note: int | None = None,
    prefer_downbeat_floor: int | None = None,
) -> int:
    candidates = [note for note in range(low, high + 1) if note % 12 == pitch_class]
    if not candidates:
        note = low + ((pitch_class - low) % 12)
        while note < low:
            note += 12
        while note > high:
            note -= 12
        candidates = [max(low, min(high, note))]

    if previous_note is not None:
        return min(candidates, key=lambda note: (abs(note - previous_note), note))

    if prefer_downbeat_floor is not None:
        above_floor = [note for note in candidates if note >= prefer_downbeat_floor]
        if above_floor:
            return above_floor[0]
    return candidates[0]
