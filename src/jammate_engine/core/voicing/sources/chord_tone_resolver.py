from __future__ import annotations

from jammate_engine.core.harmony.chord_parser import ParsedChord, parse_chord
from jammate_engine.core.harmony.scale_resolver import resolve_functional_degree_role
from jammate_engine.core.harmony.material import (
    STACK_DEGREE_TO_SEMITONE as DEGREE_TO_SEMITONE,
    basic_triad_degrees as harmony_basic_triad_degrees,
    chord_material,
    degree_to_semitone,
    fifth_degree_for_chord,
    seventh_degree_for_chord,
    third_degree_for_chord,
)

from ..policy import ContentFamily, RootSupportPolicy, VoicingPolicy, harmonic_expansion_allowed


def chord_degrees(symbol: str) -> list[tuple[str, int]]:
    """Compatibility helper returning a basic chord stack for a symbol."""

    chord = parse_chord(symbol)
    family = triad_family_for_chord(chord)
    degrees = content_degrees(symbol, family, RootSupportPolicy.ROOT_REQUIRED)
    if chord.has_seventh and family not in {ContentFamily.SUS2_TRIAD, ContentFamily.SUS4_TRIAD}:
        seventh = seventh_degree_for_chord(chord)
        if seventh and seventh not in [degree for degree, _ in degrees]:
            degrees.append(_degree_pair(seventh))
    return degrees


def triad_family_for_chord(chord: ParsedChord) -> ContentFamily:
    if chord.quality == "minor":
        return ContentFamily.MINOR_TRIAD
    if chord.quality in {"diminished", "half_diminished"}:
        return ContentFamily.DIMINISHED_TRIAD
    if chord.quality == "augmented":
        return ContentFamily.AUGMENTED_TRIAD
    if chord.quality == "sus2":
        return ContentFamily.SUS2_TRIAD
    if chord.quality == "sus4":
        return ContentFamily.SUS4_TRIAD
    return ContentFamily.MAJOR_TRIAD


def basic_triad_degrees(chord: ParsedChord) -> list[str]:
    return list(harmony_basic_triad_degrees(chord))


def content_degree_names(
    symbol: str,
    family: ContentFamily,
    root_support: RootSupportPolicy = RootSupportPolicy.ROOT_OPTIONAL,
    policy: VoicingPolicy | None = None,
) -> list[str]:
    """Resolve a content family into symbolic degree names.

    This is the voicing-facing content contract.  It consumes
    ``core.harmony.material`` for chord tones, sevenths, available tensions, and
    alterations, but it deliberately returns symbolic degrees rather than MIDI
    pitches.  Register/disposition/selection stay outside this resolver.
    """

    chord = parse_chord(symbol)
    material = chord_material(symbol)
    third = third_degree_for_chord(chord)
    fifth = fifth_degree_for_chord(chord)
    seventh = material.seventh_degree or ("6" if chord.has_sixth else "6")
    colors = _preferred_color_degrees(material.available_tensions)
    specified_colors = _specified_color_degrees(chord)

    if family in _TRIAD_FAMILIES:
        degree_names = list(material.triad_degrees)
    elif family == ContentFamily.POWER_CHORD_5TH:
        degree_names = ["R", "5"]
    elif chord.quality == "diminished" and material.seventh_degree and family == ContentFamily.ROOTLESS_A:
        degree_names = [third, fifth, seventh, _first_color(colors, "9")]
    elif chord.quality == "diminished" and material.seventh_degree and family == ContentFamily.ROOTLESS_B:
        degree_names = [seventh, third, fifth, _first_color(colors, "9")]
    elif chord.quality == "diminished" and material.seventh_degree and family == ContentFamily.ROOTED_COLOR:
        degree_names = ["R", third, fifth, seventh, _first_color(colors, "9")]
    elif _is_altered_dominant(chord) and family == ContentFamily.ROOTLESS_A:
        degree_names = [third, seventh, *_altered_color_block(colors, target=2)]
    elif _is_altered_dominant(chord) and family == ContentFamily.ROOTLESS_B:
        degree_names = [seventh, third, *_altered_color_block(colors, target=2)]
    elif _is_altered_dominant(chord) and family == ContentFamily.SEVENTH_BASIC:
        degree_names = ["R", third, seventh, _altered_color_block(colors, target=1)[0]]
    elif _is_altered_dominant(chord) and family == ContentFamily.ROOTED_COLOR:
        degree_names = ["R", third, seventh, *_altered_color_block(colors, target=2)]
    elif chord.is_half_diminished and family == ContentFamily.ROOTLESS_A:
        degree_names = _resolve_functional_roles(chord, ("third", "fifth", "seventh", "ninth"))
    elif chord.is_half_diminished and family == ContentFamily.ROOTLESS_B:
        degree_names = _resolve_functional_roles(chord, ("seventh", "ninth", "third", "fifth"))
    elif chord.is_half_diminished and family == ContentFamily.ROOTED_COLOR:
        degree_names = _resolve_functional_roles(chord, ("root", "third", "fifth", "seventh", "ninth"))
    elif family == ContentFamily.SEVENTH_BASIC:
        if material.seventh_degree:
            degree_names = list(material.chord_tone_degrees)
        elif chord.has_sixth:
            degree_names = ["R", third, fifth, "6"]
        else:
            degree_names = list(material.triad_degrees)
    elif family == ContentFamily.GUIDE_TONE:
        degree_names = [third, seventh] if (material.seventh_degree or chord.has_sixth) else [third, fifth]
    elif family == ContentFamily.SHELL:
        shell_core = [third, seventh] if (material.seventh_degree or chord.has_sixth) else [third, fifth]
        degree_names = ["R", *shell_core] if root_support in _ROOT_REQUIRED_POLICIES else shell_core
    elif family == ContentFamily.SHELL_PLUS_5:
        # Rootless three-note guide-tone shell plus the chord-quality-correct fifth.
        # This is not a triad: it deliberately keeps 3rd/7th as the identity
        # core, then adds 5/b5/#5 only as a stabilizing chord tone.
        shell_core = [third, seventh, fifth] if (material.seventh_degree or chord.has_sixth) else [third, fifth]
        degree_names = ["R", *shell_core] if root_support in _ROOT_REQUIRED_POLICIES else shell_core
    elif family == ContentFamily.SHELL_PLUS_COLOR:
        # Conservative 3-note rootless shell plus exactly one allowed color.
        # Default mode is chord_symbol_only: use only colors/tensions/alterations
        # explicitly present in the chord symbol.  If no explicit color exists,
        # fall back to chord-internal identity tones rather than inventing 9/13.
        shell_core = _shell_plus_specified_color_degrees(
            chord=chord,
            third=third,
            seventh=seventh,
            fifth=fifth,
            specified_colors=specified_colors,
            fallback_colors=colors,
            policy=policy,
        )
        degree_names = ["R", *shell_core] if root_support in _ROOT_REQUIRED_POLICIES else shell_core
    elif family == ContentFamily.ROOTLESS_A:
        degree_names = [third, seventh, *_color_block(colors, target=2)] if material.seventh_degree else [third, fifth, _first_color(colors, "9")]
    elif family == ContentFamily.ROOTLESS_B:
        degree_names = [seventh, third, fifth, _first_color(colors, "9")] if material.seventh_degree else [third, _first_color(colors, "9"), fifth]
    elif family == ContentFamily.ROOTED_COLOR:
        if material.seventh_degree:
            degree_names = ["R", third, seventh, *_color_block(colors, target=2)]
        elif chord.has_sixth:
            degree_names = ["R", third, "6", _first_color(colors, "9")]
        else:
            degree_names = ["R", third, fifth, _first_color(colors, "9")]
    else:
        degree_names = list(material.triad_degrees)

    degree_names = _apply_root_support(degree_names, root_support)
    return _dedupe([degree for degree in degree_names if degree])


def content_degrees(
    symbol: str,
    family: ContentFamily,
    root_support: RootSupportPolicy = RootSupportPolicy.ROOT_OPTIONAL,
    policy: VoicingPolicy | None = None,
) -> list[tuple[str, int]]:
    """Resolve abstract voicing content into relative degrees.

    The returned degrees are still relative chord-degree symbols. They are not
    MIDI notes and have not yet been arranged into a disposition/register.
    """

    return [_degree_pair(degree) for degree in content_degree_names(symbol, family, root_support, policy=policy)]


_TRIAD_FAMILIES = {
    ContentFamily.MAJOR_TRIAD,
    ContentFamily.MINOR_TRIAD,
    ContentFamily.DIMINISHED_TRIAD,
    ContentFamily.AUGMENTED_TRIAD,
    ContentFamily.SUS2_TRIAD,
    ContentFamily.SUS4_TRIAD,
}
_ROOT_REQUIRED_POLICIES = {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED, RootSupportPolicy.ROOT_PREFERRED}


def _resolve_functional_roles(chord: ParsedChord, roles: tuple[str, ...]) -> list[str]:
    """Resolve voicing source roles via core Harmony rather than local accidentals."""

    return [resolve_functional_degree_role(chord, role) for role in roles]


def _apply_root_support(degree_names: list[str], root_support: RootSupportPolicy) -> list[str]:
    if root_support in _ROOT_REQUIRED_POLICIES and "R" not in degree_names:
        return ["R", *degree_names]
    if root_support == RootSupportPolicy.ROOTLESS_PREFERRED:
        rootless = [degree for degree in degree_names if degree != "R"]
        return rootless or degree_names
    return degree_names


def _shell_plus_specified_color_degrees(
    *,
    chord: ParsedChord,
    third: str,
    seventh: str,
    fifth: str,
    specified_colors: list[str],
    fallback_colors: list[str],
    policy: VoicingPolicy | None,
) -> list[str]:
    """Return the V2.1.6 conservative shell+one-color degree set.

    This routine intentionally distinguishes *specified color* from *available
    theoretical tension*.  Ordinary G7 should not silently become G13; G13 may
    use 13 because the chart asked for it.  Richer unnotated color is only
    allowed when the request/style explicitly enables harmonic expansion.
    """

    # Half-diminished identity: b5 is not optional color; it is the chord's
    # defining internal tone.  Keep the three-note shape clear and stable.
    if chord.is_half_diminished:
        return [third, seventh, fifth]

    # Fully diminished seventh identity: bb7 is enharmonic 6.  In a 3-note
    # shell-like audit target, keep b3 + bb7/6 + b5; dim triads without a
    # seventh include root so their identity remains audible.
    if chord.quality == "diminished":
        if seventh:
            return [third, seventh, fifth]
        return ["R", third, fifth]

    # Chord-symbol colors have priority.  C9 chooses 9, C13 chooses 13, C7b9
    # chooses b9, Cmaj7#11 chooses #11, etc.  If a symbol contains several
    # explicit colors, choose a stable first color; future passes may add a
    # multi-candidate color selector for voice-leading between explicit colors.
    if specified_colors:
        return [third, seventh, specified_colors[0]] if seventh else [third, fifth, specified_colors[0]]

    if harmonic_expansion_allowed(policy, chord):
        color = _first_color(fallback_colors, "9")
        return [third, seventh, color] if seventh else [third, fifth, color]

    # Default: no unnotated extension.  Stay within the chord symbol's internal
    # tones, effectively matching shell+5 for ordinary seventh chords.
    return [third, seventh, fifth] if seventh else [third, fifth]



def _specified_color_degrees(chord: ParsedChord) -> list[str]:
    """Return color/tension/alteration degrees explicitly written in the symbol."""

    out: list[str] = []
    alterations = set(chord.alterations or ())

    # Alterations are more specific than natural extension digits.  For C7b9,
    # the parser may also surface extension "9"; do not let that override b9.
    for degree in ("b9", "#9", "#11", "b13", "#5", "b5"):
        if degree in alterations:
            out.append(degree)

    extensions = set(chord.extensions or ())
    if "b9" not in alterations and "#9" not in alterations and "9" in extensions:
        out.append("9")
    if "#11" not in alterations and "11" in extensions:
        out.append("11")
    if "b13" not in alterations and "13" in extensions:
        out.append("13")

    # Suspensions are literal chord-symbol material.  In shell+specified-color
    # they may function as the one non-guide upper note for sus contexts.
    for suspension in chord.suspensions or ():
        if suspension == "sus4" and "11" not in out:
            out.append("11")
        elif suspension == "sus2" and "9" not in out:
            out.append("9")
    return _dedupe(out)


def _preferred_color_degrees(tensions: tuple[str, ...] | list[str]) -> list[str]:
    """Return stable color tones from Harmony available tensions.

    Explicit alterations from the chord symbol are already ordered by Harmony.
    This helper only normalizes a safe fallback order for content families.
    Avoid degrees are intentionally not used here because Harmony's
    ``available_tensions`` has already excluded obvious avoid tones.
    """

    preferred_order = ("b9", "#9", "9", "#11", "11", "b13", "13")
    tension_set = set(tensions or ())
    ordered = [degree for degree in preferred_order if degree in tension_set]
    return ordered or ["9", "13"]



def _is_altered_dominant(chord: ParsedChord) -> bool:
    return chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in chord.alterations)


def _altered_color_block(colors: list[str], *, target: int) -> list[str]:
    preferred = [degree for degree in ("b9", "#9", "b13", "#11", "#5", "b5") if degree in colors]
    out = list(preferred[:target])
    for fallback in ("b9", "#9", "b13", "#11"):
        if len(out) >= target:
            break
        if fallback not in out:
            out.append(fallback)
    return out[:target]

def _color_block(colors: list[str], *, target: int) -> list[str]:
    out = list(colors[:target])
    for fallback in ("9", "13", "#11", "11"):
        if len(out) >= target:
            break
        if fallback not in out:
            out.append(fallback)
    return out[:target]


def _first_color(colors: list[str], fallback: str) -> str:
    return colors[0] if colors else fallback


def _degree_pair(degree: str) -> tuple[str, int]:
    # Voicing uses stacked intervals, not compact pitch-class offsets.  This
    # keeps literal voicing degree 4 / 11 separate from BassFoundation's legacy
    # ``4 = nextR`` token handled by ``resolve_degree_token()``.
    return (degree, DEGREE_TO_SEMITONE.get(degree, degree_to_semitone(degree, stacked=True)))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
