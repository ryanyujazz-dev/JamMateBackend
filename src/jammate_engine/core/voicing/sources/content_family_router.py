from __future__ import annotations

from jammate_engine.core.harmony.chord_parser import ParsedChord, parse_chord

from .chord_tone_resolver import triad_family_for_chord
from .color_permission import (
    explicit_symbol_color_degrees as _explicit_symbol_color_degrees,
    is_half_diminished_like as _is_half_diminished_like,
    rootless_ab_explicit_color_degrees as _rootless_ab_explicit_color_degrees,
)
from ..policy import (
    ContentFamily,
    RootSupportPolicy,
    VoicingPolicy,
    color_is_chord_symbol_specified,
    harmonic_expansion_allowed,
)

ROOTLESS_FAMILIES = {
    ContentFamily.ROOTLESS_A,
    ContentFamily.ROOTLESS_B,
    ContentFamily.GUIDE_TONE,
    ContentFamily.SHELL,
    ContentFamily.SHELL_PLUS_5,
    ContentFamily.SHELL_PLUS_COLOR,
}
ROOTED_FAMILIES = {ContentFamily.SEVENTH_BASIC, ContentFamily.ROOTED_COLOR}
TRIAD_FAMILIES = {
    ContentFamily.MAJOR_TRIAD,
    ContentFamily.MINOR_TRIAD,
    ContentFamily.DIMINISHED_TRIAD,
    ContentFamily.AUGMENTED_TRIAD,
    ContentFamily.SUS2_TRIAD,
    ContentFamily.SUS4_TRIAD,
    ContentFamily.POWER_CHORD_5TH,
}


CONTENT_FAMILY_ROUTER_VERSION = "v2_6_19"


def choose_content_families(symbol: str, policy: VoicingPolicy) -> list[ContentFamily]:
    """Return chord-quality-valid content families allowed by a style policy.

    This module owns content-family routing and chord-quality normalization.
    Source-degree inventory remains in ``content_planner.py`` until the later
    content-source-inventory split.  The behavior is intentionally preserved
    from the v2_6_16 planner implementation.
    """

    chord = parse_chord(symbol)
    if policy.allowed_content:
        families = list(policy.allowed_content)
    elif policy.preferred_content:
        families = [policy.preferred_content]
    else:
        triad = triad_family_for_chord(chord)
        if policy.root_support == RootSupportPolicy.ROOTLESS_PREFERRED and chord.has_seventh:
            families = [ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.GUIDE_TONE]
        elif policy.root_support == RootSupportPolicy.ROOTLESS_ALLOWED and chord.has_seventh:
            families = [ContentFamily.ROOTLESS_A, ContentFamily.SEVENTH_BASIC, triad]
        elif chord.has_seventh:
            families = [ContentFamily.SEVENTH_BASIC, ContentFamily.ROOTED_COLOR, triad]
        else:
            families = [triad]

    if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED}:
        rooted = [family for family in families if family not in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.GUIDE_TONE}]
        if rooted:
            families = rooted
        elif ContentFamily.SEVENTH_BASIC not in families:
            families = [ContentFamily.SEVENTH_BASIC, *families]

    return normalize_content_families_for_chord(chord, _dedupe(families), policy)


def normalize_content_families_for_chord(
    chord: ParsedChord,
    families: list[ContentFamily],
    policy: VoicingPolicy | None = None,
) -> list[ContentFamily]:
    """Normalize broad style content preferences against actual chord quality."""

    actual_triad = triad_family_for_chord(chord)
    supports_rootless = chord.has_seventh or chord.has_sixth or chord.is_dominant or _is_half_diminished_like(chord)
    normalized: list[ContentFamily] = []
    saw_triad_family = False

    altered_dominant = _is_altered_dominant_for_rooted_color(chord)
    for family in families:
        if family in TRIAD_FAMILIES:
            saw_triad_family = True
            if altered_dominant:
                continue
            if family == ContentFamily.POWER_CHORD_5TH:
                normalized.append(family)
            elif family == actual_triad:
                normalized.append(family)
            continue
        if family in ROOTLESS_FAMILIES and not supports_rootless:
            if is_three_note_closed_request(families, policy) and family in {ContentFamily.SHELL_PLUS_5, ContentFamily.SHELL_PLUS_COLOR}:
                # v2_1_39: a density-3 closed audit preset may intentionally ask
                # the shell-tuning family to inspect plain triads/add9/sus symbols.
                normalized.append(family)
                continue
            continue
        if family == ContentFamily.SEVENTH_BASIC:
            if altered_dominant:
                # Altered dominant material lives in color families so
                # SEVENTH_BASIC can remain literal chord-symbol material.
                continue
            if not (chord.has_seventh or chord.has_sixth):
                continue
        if family == ContentFamily.ROOTED_COLOR and chord.is_suspended and not chord.has_seventh:
            # No-seventh sus symbols are triad-family material at density 4.
            continue
        if (
            family == ContentFamily.ROOTED_COLOR
            and not (chord.has_seventh or chord.has_sixth)
            and not _explicit_symbol_color_degrees(chord)
            and harmonic_expansion_allowed(policy, chord)
        ):
            # Plain-triad expansion is handled by the triad family.
            continue
        if family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B, ContentFamily.ROOTED_COLOR}:
            if not four_note_color_gate_open(chord, family, policy):
                continue
        normalized.append(family)

    if saw_triad_family and actual_triad not in normalized and not altered_dominant:
        normalized.append(actual_triad)
    if altered_dominant and ContentFamily.ROOTED_COLOR not in normalized and not is_three_note_closed_request(families, policy):
        # Migration fallback for legacy callers that requested only SEVENTH_BASIC
        # on altered dominants without leaking altered material into SEVENTH_BASIC.
        normalized.append(ContentFamily.ROOTED_COLOR)
    if not normalized:
        if chord.has_seventh or chord.has_sixth or _is_half_diminished_like(chord):
            normalized.append(ContentFamily.SEVENTH_BASIC)
        else:
            normalized.append(actual_triad)
    return _dedupe(normalized)


def is_three_note_closed_request(families: list[ContentFamily], policy: VoicingPolicy | None) -> bool:
    if policy is None:
        return False
    if int(getattr(policy, "max_density", 99) or 99) > 3:
        return False
    metadata = dict(getattr(policy, "metadata", {}) or {})
    if metadata.get("closed_3note_per_source_minimum_motion"):
        return True
    three_note_families = {ContentFamily.SHELL_PLUS_COLOR, ContentFamily.SHELL_PLUS_5, ContentFamily.SHELL, ContentFamily.GUIDE_TONE}
    return bool(set(families).intersection(three_note_families)) and not {ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}.intersection(families)


def four_note_color_gate_open(chord: ParsedChord, family: ContentFamily, policy: VoicingPolicy | None) -> bool:
    """Return whether a color-bearing 4-note family may enter the candidate pool."""

    if family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}:
        explicit = _rootless_ab_explicit_color_degrees(chord)
    elif family == ContentFamily.ROOTED_COLOR:
        explicit = _explicit_symbol_color_degrees(chord)
    else:
        return True
    if color_is_chord_symbol_specified(explicit):
        return True
    return bool(harmonic_expansion_allowed(policy, chord) and family_expansion_target_allowed(family, policy))


def family_expansion_target_allowed(family: ContentFamily, policy: VoicingPolicy | None) -> bool:
    """Return whether style-level expansion is allowed to open this family."""

    metadata = dict(getattr(policy, "metadata", {}) or {}) if policy is not None else {}
    raw = metadata.get("harmonic_expansion_target_families", metadata.get("color_expansion_target_families"))
    if not raw:
        return True
    if isinstance(raw, str):
        targets = {raw}
    else:
        targets = {str(item) for item in raw}
    return family.value in targets or family.name in targets


def _is_altered_dominant_for_rooted_color(chord: ParsedChord) -> bool:
    alterations = set(chord.alterations or ())
    return bool(chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in alterations or alterations & {"b9", "#9", "#11", "b13", "#5", "b5"}))


def _dedupe(values: list[ContentFamily] | list[str]) -> list:
    seen: set = set()
    out: list = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
