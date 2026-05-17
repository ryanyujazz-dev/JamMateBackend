from __future__ import annotations

Degree = tuple[str, int]
PlacedDegree = tuple[str, int]


def degree_to_note(root_pc: int, semitone: int, target_low: int, target_high: int) -> int:
    """Place one chord-degree pitch class inside a target register band."""

    pc = (int(root_pc) + int(semitone)) % 12
    note = 60 + pc
    while note < int(target_low):
        note += 12
    while note > int(target_high):
        note -= 12
    return int(note)


def dedupe_by_note(placed: list[PlacedDegree]) -> list[PlacedDegree]:
    """Keep the first degree assigned to each MIDI note."""

    seen: set[int] = set()
    out: list[PlacedDegree] = []
    for degree, note in placed:
        note = int(note)
        if note in seen:
            continue
        seen.add(note)
        out.append((str(degree), note))
    return out


def place_stack(
    root_pc: int,
    degrees: list[Degree],
    low: int,
    high: int,
    *,
    target_low: int,
    spread_upper_voices: bool = False,
) -> list[PlacedDegree]:
    """Place a source as a compact stack, with optional legacy upper widening.

    This helper is intentionally low-level.  Disposition meaning lives in
    closed/open/spread projection modules; this function only solves the common
    pitch-class-to-register mechanics that used to be private to
    ``disposition/facade.py``.
    """

    placed: list[PlacedDegree] = []
    for degree, semitone in degrees:
        note = degree_to_note(root_pc, semitone, target_low, high)
        if not (int(low) <= note <= int(high)):
            continue
        placed.append((str(degree), note))
    placed = sorted(dedupe_by_note(placed), key=lambda item: item[1])
    if spread_upper_voices and len(placed) >= 4:
        widened: list[PlacedDegree] = []
        for idx, (degree, note) in enumerate(placed):
            candidate = note + 12 if idx >= 2 and note + 12 <= int(high) else note
            widened.append((degree, candidate))
        placed = sorted(dedupe_by_note(widened), key=lambda item: item[1])
    return placed
