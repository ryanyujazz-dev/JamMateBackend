from __future__ import annotations

import re
from dataclasses import dataclass

from .chord_symbol import NOTE_TO_PC, parse_root


@dataclass(frozen=True)
class ParsedChord:
    symbol: str
    root_name: str
    root_pc: int
    quality: str
    has_seventh: bool
    suffix: str = ""
    normalized_suffix: str = ""
    has_major_seventh: bool = False
    has_minor_seventh: bool = False
    has_sixth: bool = False
    is_dominant: bool = False
    is_half_diminished: bool = False
    is_fully_diminished: bool = False
    is_suspended: bool = False
    extensions: tuple[str, ...] = ()
    alterations: tuple[str, ...] = ()
    suspensions: tuple[str, ...] = ()
    bass_name: str | None = None
    bass_pc: int | None = None
    has_slash_bass: bool = False


def parse_chord(symbol: str) -> ParsedChord:
    """Parse a compact jazz chord symbol into the core Harmony contract.

    The parser is intentionally pragmatic rather than notation-complete.  It
    normalizes the common jazz symbols that generation, voicing, realization,
    and future melodic systems rely on: major/minor/dominant, sixth chords,
    diminished and half-diminished, suspended dominants, altered extensions,
    and slash-bass metadata.  Slash bass is parsed only as metadata here; it
    does not change the harmonic root used by current BassFoundation behavior.
    """

    raw_symbol = str(symbol or "C").strip() or "C"
    root_name, root_pc, rest = parse_root(raw_symbol)
    suffix, bass_name, bass_pc = _split_suffix_and_slash_bass(rest)
    normalized = _normalize_suffix(suffix)
    compact = _compact_suffix(normalized)
    lower = compact.lower()

    is_half_dim = _is_half_diminished(lower, normalized)
    is_full_dim = _is_fully_diminished(lower, normalized, is_half_dim)
    is_sus2 = "sus2" in lower
    is_sus4 = ("sus" in lower or "sus4" in lower) and not is_sus2
    is_aug = _is_augmented(lower)
    has_major_seventh = _has_major_seventh(compact, lower, normalized)
    is_minor = _looks_minor(compact, lower) and not is_half_dim

    if is_half_dim:
        quality = "half_diminished"
    elif is_full_dim:
        quality = "diminished"
    elif is_aug:
        quality = "augmented"
    elif is_sus2:
        quality = "sus2"
    elif is_sus4:
        quality = "sus4"
    elif is_minor:
        quality = "minor"
    else:
        quality = "major"

    extensions = _find_extensions(lower)
    alterations = _find_alterations(lower)
    has_sixth = _has_explicit_sixth(lower)
    has_dim_seventh = is_full_dim and _has_diminished_seventh(lower, normalized)
    has_plain_seventh = _has_plain_seventh(lower, extensions, quality=quality, has_major_seventh=has_major_seventh)
    has_minor_seventh = has_plain_seventh and not has_major_seventh and not has_dim_seventh
    is_dominant = quality in {"major", "sus2", "sus4", "augmented"} and has_minor_seventh
    has_seventh = has_major_seventh or has_minor_seventh or has_dim_seventh
    suspensions = tuple(value for value in ("sus2" if is_sus2 else "", "sus4" if is_sus4 else "") if value)

    return ParsedChord(
        symbol=raw_symbol,
        root_name=root_name,
        root_pc=root_pc,
        quality=quality,
        has_seventh=has_seventh,
        suffix=suffix,
        normalized_suffix=lower,
        has_major_seventh=has_major_seventh,
        has_minor_seventh=has_minor_seventh,
        has_sixth=has_sixth,
        is_dominant=is_dominant,
        is_half_diminished=is_half_dim,
        is_fully_diminished=is_full_dim,
        is_suspended=is_sus2 or is_sus4,
        extensions=extensions,
        alterations=alterations,
        suspensions=suspensions,
        bass_name=bass_name,
        bass_pc=bass_pc,
        has_slash_bass=bass_pc is not None,
    )


def _split_suffix_and_slash_bass(rest: str) -> tuple[str, str | None, int | None]:
    if "/" not in rest:
        return rest, None, None
    suffix, slash = rest.split("/", 1)
    slash = slash.strip()
    if not slash:
        return suffix, None, None
    # Avoid treating C6/9 as a slash-bass chord.  The parser keeps 6/9 as a
    # suffix spelling and only parses slash bass when a real pitch name follows.
    if slash[0].upper() not in {"A", "B", "C", "D", "E", "F", "G"}:
        return rest, None, None
    candidate = slash[0].upper() + slash[1:]
    if len(candidate) >= 2 and candidate[1] in {"#", "b"}:
        bass_name = candidate[:2]
    else:
        bass_name = candidate[:1]
    if bass_name not in NOTE_TO_PC:
        return rest, None, None
    return suffix, bass_name, NOTE_TO_PC[bass_name]


def _normalize_suffix(suffix: str) -> str:
    return (
        str(suffix or "")
        .strip()
        .replace("−", "-")
        .replace("–", "-")
        .replace("△", "Δ")
        .replace("♭", "b")
        .replace("♯", "#")
        .replace("º", "°")
    )


def _compact_suffix(suffix: str) -> str:
    return re.sub(r"[\s()\[\]]+", "", suffix)


def _looks_minor(compact_suffix: str, lower_suffix: str) -> bool:
    if not compact_suffix:
        return False
    # Do not mistake minor add chords such as ``madd9`` for the ``ma`` major
    # shorthand.  Treat ``ma`` as major only when it actually prefixes a major
    # seventh/extension spelling such as ma7 or ma9.
    if lower_suffix.startswith("maj") or re.match(r"^ma(?:7|9|11|13)", lower_suffix) or compact_suffix.startswith(("M", "Δ", "^")):
        return False
    return lower_suffix.startswith(("min", "mi")) or compact_suffix.startswith("-") or compact_suffix.startswith("m")


def _is_half_diminished(lower_suffix: str, normalized_suffix: str) -> bool:
    """Return whether a suffix names a half-diminished/minor-b5 seventh family.

    Keep this in the parser rather than in voicing: symbols such as ``m11b5``
    and ``m13b5`` must resolve to the half-diminished/Locrian harmony contract
    before any style or voicing layer chooses notes.
    """

    if "ø" in normalized_suffix:
        return True
    return bool(re.search(r"^(?:m|min|mi|-)(?:7|9|11|13)b5", lower_suffix))


def _is_fully_diminished(lower_suffix: str, normalized_suffix: str, is_half_dim: bool) -> bool:
    if is_half_dim:
        return False
    return lower_suffix.startswith("dim") or lower_suffix.startswith("o") or normalized_suffix.startswith("°")


def _is_augmented(lower_suffix: str) -> bool:
    return lower_suffix.startswith("aug") or lower_suffix.startswith("+") or "#5" in lower_suffix or "+5" in lower_suffix


def _has_major_seventh(compact_suffix: str, lower_suffix: str, normalized_suffix: str) -> bool:
    if "Δ" in normalized_suffix or "^" in compact_suffix:
        return True
    if re.search(r"maj(?:7|9|11|13)", lower_suffix):
        return True
    if re.search(r"ma(?:7|9|11|13)", lower_suffix):
        return True
    if re.search(r"(?:^|m)M(?:7|9|11|13)", compact_suffix):
        return True
    return False


def _has_explicit_sixth(lower_suffix: str) -> bool:
    return bool(re.search(r"(^|[^0-9])6($|[^0-9])", lower_suffix)) or lower_suffix.endswith("6") or "6/9" in lower_suffix


def _has_diminished_seventh(lower_suffix: str, normalized_suffix: str) -> bool:
    return "7" in lower_suffix or "°7" in normalized_suffix or "o7" in lower_suffix or "dim7" in lower_suffix


def _has_plain_seventh(
    lower_suffix: str,
    extensions: tuple[str, ...],
    *,
    quality: str,
    has_major_seventh: bool,
) -> bool:
    if quality == "half_diminished":
        return True
    if has_major_seventh:
        return False
    if "7" in lower_suffix:
        return True
    if "6/9" in lower_suffix or lower_suffix.startswith("add") or "add9" in lower_suffix:
        return False
    # In jazz shorthand, plain 9/11/13 dominants and minor 9/11/13 chords imply
    # the seventh unless the symbol explicitly says major seventh.
    return bool(extensions and quality in {"major", "minor", "sus2", "sus4", "augmented"})


def _find_extensions(lower_suffix: str) -> tuple[str, ...]:
    found: list[str] = []
    for token in ("9", "11", "13"):
        if re.search(rf"(?<!\d){token}(?!\d)", lower_suffix) or token in lower_suffix:
            found.append(token)
    return tuple(_dedupe(found))


def _find_alterations(lower_suffix: str) -> tuple[str, ...]:
    found: list[str] = []
    for token in ("bb7", "b9", "#9", "b5", "#5", "+5", "#11", "b13"):
        if token in lower_suffix:
            found.append("#5" if token == "+5" else token)
    if "alt" in lower_suffix:
        found.append("alt")
    return tuple(_dedupe(found))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
