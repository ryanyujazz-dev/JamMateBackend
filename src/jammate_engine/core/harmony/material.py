from __future__ import annotations

from dataclasses import dataclass

from .chord_parser import ParsedChord, parse_chord

# Harmony owns symbolic degree semantics.  Realizers may still choose octave,
# register, and instrument-specific projection, but they should not re-parse
# chord symbols or redefine degree pitch-class meaning locally.
COMPACT_DEGREE_TO_SEMITONE: dict[str, int] = {
    "R": 0,
    "root": 0,
    "1": 0,
    "unison": 0,
    "b2": 1,
    "flat2": 1,
    "b9": 1,
    "flat9": 1,
    "2": 2,
    "Second": 2,
    "9": 2,
    "add9": 2,
    "#2": 3,
    "#9": 3,
    "sharp9": 3,
    "b3": 3,
    "minor3": 3,
    "m3": 3,
    "3": 4,
    "major3": 4,
    "M3": 4,
    "degree4": 5,
    "scale4": 5,
    "Fourth": 5,
    "4": 5,
    "11": 5,
    "#4": 6,
    "sharp4": 6,
    "tritone": 6,
    "b5": 6,
    "flat5": 6,
    "#11": 6,
    "sharp11": 6,
    "5": 7,
    "Fifth": 7,
    "perfect5": 7,
    "#5": 8,
    "sharp5": 8,
    "b6": 8,
    "flat6": 8,
    "b13": 8,
    "flat13": 8,
    "6": 9,
    "Sixth": 9,
    "13": 9,
    "bb7": 9,
    "dim7": 9,
    "b7": 10,
    "minor7": 10,
    "dominant7": 10,
    "7": 11,
    "major7": 11,
    "maj7": 11,
    "M7": 11,
}

# Voicing often needs stacked intervals rather than pitch-class offsets.  Keep
# the extended spelling here so voicing can consume harmony without duplicating
# a separate degree table.
STACK_DEGREE_TO_SEMITONE: dict[str, int] = {
    **COMPACT_DEGREE_TO_SEMITONE,
    "b9": 13,
    "flat9": 13,
    "9": 14,
    "add9": 14,
    "#9": 15,
    "sharp9": 15,
    "11": 17,
    "#11": 18,
    "sharp11": 18,
    "b13": 20,
    "flat13": 20,
    "13": 21,
}

DEGREE_ALIAS_MAP: dict[str, str] = {
    "r": "R",
    "root": "R",
    "1": "R",
    "third": "Third",
    "auto_third": "3_auto",
    "chord_third": "3_auto",
    "minor_third": "b3",
    "flat_third": "b3",
    "major_third": "3",
    "classic_low3": "3",
    "fifth": "Fifth",
    "auto_fifth": "5_auto",
    "chord_fifth": "5_auto",
    "flat_fifth": "b5",
    "diminished_fifth": "b5",
    "sharp_fifth": "#5",
    "augmented_fifth": "#5",
    "second": "Second",
    "ninth": "9",
    "flat_ninth": "b9",
    "sharp_ninth": "#9",
    "fourth": "Fourth",
    "literal4": "degree4",
    "literal_4": "degree4",
    "scale_4": "degree4",
    "eleventh": "11",
    "sharp_eleventh": "#11",
    "sixth": "Sixth",
    "thirteenth": "13",
    "flat_thirteenth": "b13",
    "seventh": "Seventh",
    "minor_seventh": "b7",
    "dominant_seventh": "b7",
    "major_seventh": "7",
    "diminished_seventh": "bb7",
    "nextr": "nextR",
    "next_root": "nextR",
    "next_root_exact": "nextR",
    "chromatic_below_next_root": "approach_nextR_below",
    "chromatic_above_next_root": "approach_nextR_above",
    "approach_below_next_root": "approach_nextR_below",
    "approach_above_next_root": "approach_nextR_above",
    "scale_below_next_root": "scale_near_nextR_below",
    "scale_above_next_root": "scale_near_nextR_above",
    "dominant_next_root": "dominant_to_nextR",
    "sharp_4": "#4",
    "sharp_fourth": "#4",
    "augmented_fourth": "#4",
}

LANE_DEGREE_ALIASES: dict[str, str] = {
    "root": "R",
    "r": "R",
    "1": "R",
    "2": "Second",
    "9": "Second",
    "b3": "Third",
    "3": "Third",
    "third": "Third",
    "degree4": "Fourth",
    "scale4": "Fourth",
    "fourth": "Fourth",
    "4": "Fourth",
    "b5": "Fifth",
    "5": "Fifth",
    "fifth": "Fifth",
    "6": "Sixth",
    "b6": "Sixth",
    "bb7": "Seventh",
    "b7": "Seventh",
    "7": "Seventh",
    "seventh": "Seventh",
    "minor7": "Seventh",
    "major7": "Seventh",
}


@dataclass(frozen=True)
class DegreeResolution:
    degree: str
    pitch_class: int
    source: str


@dataclass(frozen=True)
class ChordMaterial:
    symbol: str
    root_pc: int
    quality: str
    triad_degrees: tuple[str, ...]
    seventh_degree: str | None
    chord_tone_degrees: tuple[str, ...]
    available_tensions: tuple[str, ...] = ()
    avoid_degrees: tuple[str, ...] = ()


def normalize_degree_token(token: str | None) -> str:
    value = str(token or "R").strip()
    return DEGREE_ALIAS_MAP.get(value, DEGREE_ALIAS_MAP.get(value.lower(), value))


def normalize_degree_for_lane(degree: str) -> str:
    value = str(degree or "R").strip()
    return LANE_DEGREE_ALIASES.get(value, LANE_DEGREE_ALIASES.get(value.lower(), value))


def degree_to_semitone(degree: str, *, stacked: bool = False) -> int:
    table = STACK_DEGREE_TO_SEMITONE if stacked else COMPACT_DEGREE_TO_SEMITONE
    normalized = normalize_degree_token(degree)
    return table.get(normalized, table.get(degree, 0))


def third_degree_for_chord(chord: ParsedChord) -> str:
    if chord.quality in {"minor", "diminished", "half_diminished"}:
        return "b3"
    if chord.quality == "sus2":
        return "2"
    if chord.quality == "sus4":
        return "4"
    return "3"


def fifth_degree_for_chord(chord: ParsedChord) -> str:
    if chord.quality in {"diminished", "half_diminished"}:
        return "b5"
    if chord.quality == "augmented":
        return "#5"
    return "5"


def seventh_degree_for_chord(chord: ParsedChord | str) -> str | None:
    parsed = parse_chord(chord) if isinstance(chord, str) else chord
    lower = parsed.symbol.lower()
    if not parsed.has_seventh and not parsed.is_dominant and not parsed.is_half_diminished:
        return None
    if (parsed.is_fully_diminished and parsed.has_seventh) or ("dim7" in lower) or ("o7" in lower) or ("°7" in parsed.symbol):
        return "bb7"  # diminished seventh / bb7, enharmonic to 6
    if parsed.has_major_seventh:
        return "7"
    return "b7"


def basic_triad_degrees(chord: ParsedChord | str) -> tuple[str, ...]:
    parsed = parse_chord(chord) if isinstance(chord, str) else chord
    if parsed.quality == "minor":
        return ("R", "b3", "5")
    if parsed.quality in {"diminished", "half_diminished"}:
        return ("R", "b3", "b5")
    if parsed.quality == "augmented":
        return ("R", "3", "#5")
    if parsed.quality == "sus2":
        return ("R", "2", "5")
    if parsed.quality == "sus4":
        return ("R", "4", "5")
    return ("R", "3", "5")


def chord_tone_degrees(chord: ParsedChord | str, *, include_seventh: bool = True) -> tuple[str, ...]:
    parsed = parse_chord(chord) if isinstance(chord, str) else chord
    degrees = list(basic_triad_degrees(parsed))
    if include_seventh:
        seventh = seventh_degree_for_chord(parsed)
        if seventh and seventh not in degrees:
            degrees.append(seventh)
    return tuple(_dedupe(degrees))


def chord_material(chord_symbol: str) -> ChordMaterial:
    parsed = parse_chord(chord_symbol)
    triad = basic_triad_degrees(parsed)
    seventh = seventh_degree_for_chord(parsed)
    tones = chord_tone_degrees(parsed)
    tensions, avoids = available_tension_policy(chord_symbol)
    return ChordMaterial(
        symbol=parsed.symbol,
        root_pc=parsed.root_pc,
        quality=parsed.quality,
        triad_degrees=triad,
        seventh_degree=seventh,
        chord_tone_degrees=tones,
        available_tensions=tensions,
        avoid_degrees=avoids,
    )


def available_tension_policy(chord_symbol: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the neutral core available-tension / avoid-degree policy.

    Harmony identifies generally usable color material and obvious avoid notes.
    It deliberately does not decide how often a style should use those colors.
    Explicit alterations in the chord symbol are surfaced as available material
    while conservative natural defaults are preserved for compatibility.
    """

    chord = parse_chord(chord_symbol)
    lower = chord_symbol.lower()
    alterations = set(chord.alterations)

    if chord.is_half_diminished:
        # Half-diminished defaults to Locrian in the common harmony layer.
        # Therefore the generic 9/13 extension slots are spelled b9/b13 unless
        # the chart explicitly asks for natural 9 via m9b5 / m7b5(9).
        ninth = "9" if "9" in chord.extensions else "b9"
        tensions = [ninth, "11", "b13"]
        return tuple(_dedupe(tensions)), ()

    if chord.quality == "diminished":
        if chord.is_fully_diminished or chord.has_seventh:
            return ("9", "11", "b13", "7"), ()
        return ("9", "11"), ()

    if chord.is_dominant:
        if "alt" in lower or "alt" in alterations:
            return ("b9", "#9", "#11", "b13"), ()

        explicit_altered = [degree for degree in ("b9", "#9", "#11", "b13", "#5", "b5") if degree in alterations]
        natural_defaults = []
        if "b9" not in alterations and "#9" not in alterations:
            natural_defaults.append("9")
        if "b13" not in alterations and "#5" not in alterations:
            natural_defaults.append("13")
        if "#11" in alterations or "b5" in alterations:
            avoids: list[str] = []
        elif chord.is_suspended:
            avoids = ["3"]
        else:
            avoids = ["11"]
        return tuple(_dedupe([*explicit_altered, *natural_defaults])), tuple(_dedupe(avoids))

    if chord.quality == "augmented":
        return ("9", "#11"), ()

    if chord.quality == "minor":
        if chord.has_major_seventh or chord.has_sixth:
            return ("9", "11", "13"), ()
        return ("9", "11", "13"), ()

    if chord.quality in {"sus2", "sus4"}:
        return ("9", "13"), ("3",)

    if chord.has_sixth and not chord.has_major_seventh:
        return ("9",), ("11",)

    if chord.has_major_seventh or chord.quality == "major":
        return ("9", "#11", "13"), ("11",)

    return (), ()


def resolve_degree_token(
    *,
    chord_symbol: str,
    token: str | None,
    next_chord_symbol: str | None = None,
) -> DegreeResolution:
    """Resolve a symbolic degree token to pitch class.

    This function is the core Harmony contract for pitch-class meaning.  It
    deliberately does not choose octave/register and does not create notes.
    Bass vocabulary legacy shorthand ``4`` is interpreted as ``nextR`` for this
    resolver; literal fourth should be written as ``Fourth`` / ``degree4`` /
    ``scale4`` by style vocabulary.
    """

    chord = parse_chord(chord_symbol)
    normalized = normalize_degree_token(token)

    if normalized in {"3_auto", "third", "Third"}:
        normalized = third_degree_for_chord(chord)
    elif normalized in {"5_auto", "fifth", "Fifth"}:
        normalized = fifth_degree_for_chord(chord)
    elif normalized == "Sixth":
        normalized = "b6" if chord.quality in {"diminished", "half_diminished"} else "6"
    elif normalized == "Seventh":
        normalized = seventh_degree_for_chord(chord) or "b7"
    elif normalized in {"4", "nextR", "next_root", "next_root_exact"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="nextR", pitch_class=target.root_pc, source="next_chord_root")
    elif normalized in {"beat4_auto", "connector_auto"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="beat4_auto", pitch_class=(target.root_pc - 1) % 12, source="auto_connector_placeholder")
    elif normalized in {"approach_nextR_below", "approach_next_root_below"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="approach_nextR_below", pitch_class=(target.root_pc - 1) % 12, source="chromatic_below_next_root")
    elif normalized in {"approach_nextR_above", "approach_next_root_above"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="approach_nextR_above", pitch_class=(target.root_pc + 1) % 12, source="chromatic_above_next_root")
    elif normalized in {"scale_near_nextR", "scale_near_nextR_below"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="scale_near_nextR_below", pitch_class=(target.root_pc - 2) % 12, source="scale_near_next_root")
    elif normalized in {"scale_near_nextR_above"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="scale_near_nextR_above", pitch_class=(target.root_pc + 2) % 12, source="scale_near_next_root")
    elif normalized in {"dominant_to_nextR", "dominant_connection_nextR"}:
        target = parse_chord(next_chord_symbol or chord_symbol)
        return DegreeResolution(degree="dominant_to_nextR", pitch_class=(target.root_pc - 5) % 12, source="dominant_connection_next_root")

    semitone = degree_to_semitone(normalized, stacked=False)
    return DegreeResolution(degree=normalized, pitch_class=(chord.root_pc + semitone) % 12, source="current_chord_degree")


def is_major_quality(chord_symbol: str) -> bool:
    chord = parse_chord(chord_symbol)
    return chord.quality == "major" and not chord.is_dominant and not chord.has_minor_seventh


def is_six_quality(chord_symbol: str) -> bool:
    return parse_chord(chord_symbol).has_sixth


def is_tonic_major_like(chord_symbol: str) -> bool:
    chord = parse_chord(chord_symbol)
    return chord.quality == "major" and not chord.is_dominant and not chord.is_suspended


def scale_pitch_classes(chord_symbol: str) -> set[int]:
    chord = parse_chord(chord_symbol)
    if chord.quality == "minor":
        offsets = {0, 2, 3, 5, 7, 9, 10}
    elif chord.quality in {"diminished", "half_diminished"}:
        offsets = {0, 1, 3, 5, 6, 8, 10}
    elif chord.is_dominant:
        offsets = {0, 2, 4, 5, 7, 9, 10}
    else:
        offsets = {0, 2, 4, 6, 7, 9, 11}
    return {(chord.root_pc + offset) % 12 for offset in offsets}


def _dedupe(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
