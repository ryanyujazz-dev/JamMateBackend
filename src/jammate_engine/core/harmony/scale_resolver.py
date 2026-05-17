from __future__ import annotations

from dataclasses import dataclass

from .chord_parser import ParsedChord, parse_chord
from .material import (
    available_tension_policy,
    chord_tone_degrees,
    degree_to_semitone,
    fifth_degree_for_chord,
    seventh_degree_for_chord,
    third_degree_for_chord,
)


@dataclass(frozen=True)
class ResolvedScalePolicy:
    mode: str
    pitch_classes: frozenset[int]
    available_tensions: tuple[str, ...]
    avoid_degrees: tuple[str, ...]
    source: str = "core_harmony_default"
    scale_degrees: tuple[str, ...] = ()
    chord_tone_degrees: tuple[str, ...] = ()
    explicit_alterations: tuple[str, ...] = ()
    color_tensions: tuple[str, ...] = ()


def resolve_scale_policy(chord_symbol: str) -> str:
    """Compatibility helper returning only the default mode name."""

    return resolve_scale_policy_detail(chord_symbol).mode


def resolve_scale_policy_detail(chord_symbol: str) -> ResolvedScalePolicy:
    """Resolve default mode, scale pitch classes, and tension policy.

    Core Harmony owns the neutral material contract: mode family, pitch-class
    set, available tensions, avoid degrees, explicit alterations, and chord
    tones.  Style layers may later decide how strongly to use this material;
    this resolver does not choose voicings, register, density, or taste.
    """

    chord = parse_chord(chord_symbol)
    mode = _select_default_mode(chord)
    scale_degrees = _scale_degrees_for_mode(mode, chord)
    tensions, avoids = available_tension_policy(chord_symbol)
    return ResolvedScalePolicy(
        mode=mode,
        pitch_classes=frozenset(_pitch_classes_from_degrees(chord.root_pc, scale_degrees)),
        available_tensions=tensions,
        avoid_degrees=avoids,
        scale_degrees=scale_degrees,
        chord_tone_degrees=chord_tone_degrees(chord),
        explicit_alterations=chord.alterations,
        color_tensions=tuple(degree for degree in tensions if degree not in chord_tone_degrees(chord)),
    )






FUNCTIONAL_DEGREE_ROLE_ALIASES: dict[str, str] = {
    "r": "root",
    "1": "root",
    "root": "root",
    "third": "third",
    "3rd": "third",
    "second": "second",
    "2nd": "second",
    "2": "second",
    "fifth": "fifth",
    "5th": "fifth",
    "seventh": "seventh",
    "7th": "seventh",
    "sixth": "sixth",
    "6th": "sixth",
    "fourth": "fourth",
    "4th": "fourth",
    "ninth": "ninth",
    "9th": "ninth",
    "eleventh": "eleventh",
    "11th": "eleventh",
    "sharp_eleventh": "eleventh",
    "#11": "eleventh",
    "sharp11": "eleventh",
    "thirteenth": "thirteenth",
    "13th": "thirteenth",
}


def resolve_functional_degree_role(chord_symbol: str | ParsedChord, role: str) -> str:
    """Resolve a voicing functional-degree role through core Harmony.

    Voicing canonical sources should name *roles* such as ``third``, ``fifth``,
    ``seventh`` and ``ninth``.  Harmony then spells those roles for the actual
    chord quality, extensions, alterations and default scale policy.  For
    example, the same source role order ``third-fifth-seventh-ninth`` becomes
    ``3-5-7-9`` on Cmaj9, ``b3-5-b7-9`` on Cm9, and ``b3-b5-b7-b9`` on a plain
    half-diminished chord under the default Locrian policy.
    """

    chord = chord_symbol if isinstance(chord_symbol, ParsedChord) else parse_chord(str(chord_symbol))
    key = str(role).strip().lower().replace("-", "_").replace(" ", "_")
    key = FUNCTIONAL_DEGREE_ROLE_ALIASES.get(key, key)

    if key == "root":
        return "R"
    if key == "third":
        return third_degree_for_chord(chord)
    if key == "fifth":
        return fifth_degree_for_chord(chord)
    if key == "seventh":
        explicit_seventh = seventh_degree_for_chord(chord)
        if explicit_seventh:
            return explicit_seventh
        if chord.has_sixth:
            return "6"
        # For triad-aware 3-note expansion, an unqualified major triad should
        # not be forced into a dominant seventh.  Without harmonic-function
        # context, keep major triads major-seventh colored, minor/sus/augmented
        # triads minor-seventh colored only when an expansion policy explicitly
        # chooses root-third-seventh.
        return "7" if chord.quality == "major" else "b7"
    if key == "second":
        return "2"
    if key == "sixth":
        return "6"
    if key == "fourth":
        return "4"
    if key == "ninth":
        return scale_spelling_for_extension(chord, "9")
    if key == "eleventh":
        return scale_spelling_for_extension(chord, "11")
    if key == "thirteenth":
        return scale_spelling_for_extension(chord, "13")
    return str(role)


def scale_spelling_for_extension(chord_symbol: str | ParsedChord, extension: str) -> str:
    """Return the mode-correct spelling for a generic extension slot.

    Voicing content types such as rootless A/B use abstract slots like
    ``with_5`` = third/fifth/seventh/ninth and ``with_13`` =
    third/thirteenth/seventh/ninth.  The spelling of the ninth or thirteenth
    must come from core Harmony/scale policy, not from a local voicing shortcut.
    For example, ordinary half-diminished chords default to Locrian, so their
    generic 9 and 13 slots resolve to ``b9`` and ``b13``.  If a chart explicitly
    writes ``m9b5``, the resolver may return natural ``9`` through the
    locrian-natural-2 policy because the chord symbol asked for it.
    """

    symbol = chord_symbol.symbol if isinstance(chord_symbol, ParsedChord) else str(chord_symbol)
    detail = resolve_scale_policy_detail(symbol)
    slot = str(extension).strip()
    candidates_by_slot = {
        "9": ("9", "b9", "#9"),
        "13": ("13", "b13"),
        "11": ("11", "#11"),
    }
    for candidate in candidates_by_slot.get(slot, (slot,)):
        if candidate in detail.scale_degrees:
            return candidate
    return slot

def _select_default_mode(chord: ParsedChord) -> str:
    lower = chord.normalized_suffix
    alterations = set(chord.alterations)

    if chord.is_half_diminished:
        return "locrian_natural_2" if "9" in chord.extensions else "locrian"

    if chord.quality == "diminished":
        return "whole_half_diminished" if chord.has_seventh else "locrian"

    if chord.is_dominant:
        if "alt" in alterations or "alt" in lower:
            return "altered"
        if "#5" in alterations or "b13" in alterations:
            return "whole_tone" if not ({"b9", "#9", "#11"} & alterations) else "altered_dominant"
        if "#11" in alterations:
            return "lydian_dominant"
        if chord.is_suspended:
            return "mixolydian_sus"
        # Keep the v2_0_26 compatibility contract: explicit b9 dominants remain
        # in the mixolydian family rather than forcing a style/color choice.
        return "mixolydian"

    if chord.quality == "augmented":
        return "whole_tone"

    if chord.quality == "minor":
        if chord.has_major_seventh or chord.has_sixth:
            return "melodic_minor"
        return "dorian"

    if chord.quality == "sus2":
        return "major_pentatonic_sus2"
    if chord.quality == "sus4":
        return "mixolydian_sus" if chord.has_minor_seventh else "sus4_major"

    if chord.has_major_seventh:
        return "lydian"
    if chord.has_sixth:
        return "ionian"
    return "major"


def _scale_degrees_for_mode(mode: str, chord: ParsedChord) -> tuple[str, ...]:
    base: tuple[str, ...]
    if mode == "lydian":
        base = ("R", "9", "3", "#11", "5", "13", "7")
    elif mode == "major":
        # Compatibility with the pre-v2_0_27 neutral major pitch-class set.
        base = ("R", "9", "3", "#11", "5", "13", "7")
    elif mode == "ionian":
        base = ("R", "9", "3", "11", "5", "13", "7")
    elif mode == "dorian":
        base = ("R", "9", "b3", "11", "5", "13", "b7")
    elif mode == "melodic_minor":
        base = ("R", "9", "b3", "11", "5", "13", "7")
    elif mode == "mixolydian":
        base = ("R", "9", "3", "11", "5", "13", "b7")
    elif mode == "mixolydian_sus":
        base = ("R", "9", "4", "5", "13", "b7")
    elif mode == "lydian_dominant":
        base = ("R", "9", "3", "#11", "5", "13", "b7")
    elif mode == "altered":
        base = ("R", "b9", "#9", "3", "#11", "b13", "b7")
    elif mode == "altered_dominant":
        base = ("R", "b9", "#9", "3", "#11", "b13", "b7")
    elif mode == "whole_tone":
        base = ("R", "9", "3", "#11", "#5", "b7") if chord.is_dominant else ("R", "9", "3", "#11", "#5", "7")
    elif mode == "locrian_natural_2":
        base = ("R", "9", "b3", "11", "b5", "b13", "b7")
    elif mode == "locrian":
        base = ("R", "b9", "b3", "11", "b5", "b13", "b7")
    elif mode == "whole_half_diminished":
        base = ("R", "9", "b3", "11", "b5", "b13", "bb7", "7")
    elif mode == "major_pentatonic_sus2":
        base = ("R", "9", "3", "5", "13")
    elif mode == "sus4_major":
        base = ("R", "9", "4", "5", "13", "7")
    else:
        base = ("R", "9", "3", "#11", "5", "13", "7")

    return _apply_explicit_alterations(base, chord.alterations)


def _apply_explicit_alterations(degrees: tuple[str, ...], alterations: tuple[str, ...]) -> tuple[str, ...]:
    result = list(degrees)
    replacements = {
        "b9": "9",
        "#9": "9",
        "#11": "11",
        "b5": "5",
        "#5": "5",
        "b13": "13",
    }
    for alteration in alterations:
        if alteration == "alt":
            continue
        natural = replacements.get(alteration)
        if natural and natural in result:
            result[result.index(natural)] = alteration
        elif alteration not in result:
            result.append(alteration)
    return tuple(_dedupe(result))


def _pitch_classes_from_degrees(root_pc: int, degrees: tuple[str, ...]) -> set[int]:
    return {(root_pc + degree_to_semitone(degree, stacked=False)) % 12 for degree in degrees}


def _dedupe(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
