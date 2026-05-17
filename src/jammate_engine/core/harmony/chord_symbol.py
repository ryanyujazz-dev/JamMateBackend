from __future__ import annotations

NOTE_TO_PC = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

PC_TO_NOTE = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def parse_root(symbol: str) -> tuple[str, int, str]:
    if not symbol:
        return "C", 0, ""
    if len(symbol) >= 2 and symbol[1] in {"#", "b"}:
        root = symbol[:2]
        rest = symbol[2:]
    else:
        root = symbol[:1]
        rest = symbol[1:]
    return root, NOTE_TO_PC.get(root, 0), rest
