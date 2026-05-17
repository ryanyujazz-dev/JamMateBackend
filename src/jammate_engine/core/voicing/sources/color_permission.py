from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from jammate_engine.core.harmony.chord_parser import ParsedChord


@dataclass(frozen=True)
class ColorPermissionContext:
    """Unified 4-note color permission contract.

    Explicit chart colors and optional harmonic-expansion colors are additive:
    chart colors should be represented faithfully, while expansion may add
    style/function-safe colors for ordinary basic symbols or for already colored
    symbols when the style/LLM permits it. Voicing sources stay functional-role
    contracts; this context only decides whether the concrete resolved colors
    used by a candidate are allowed.
    """

    explicit: frozenset[str]
    expansion: frozenset[str]
    allowed: frozenset[str]
    expansion_enabled: bool


COLOR_DEGREES = {"9", "b9", "#9", "11", "#11", "13", "b13", "b5", "#5"}
ALTERED_DOMINANT_PALETTE = {"b9", "#9", "#11", "b13", "#5", "b5"}


def is_half_diminished_like(chord: ParsedChord) -> bool:
    """Treat minor-b5 seventh-family spelling as half-diminished-like.

    This helper sits in the color-permission boundary because both color gating
    and source planning need the same answer: b5 is an identity tone for m7b5,
    not an optional chart color.
    """

    return bool(chord.is_half_diminished or (chord.quality == "minor" and "b5" in set(chord.alterations or ())))


def build_color_permission_context(
    *,
    explicit: Iterable[str],
    expansion: Iterable[str],
    expansion_enabled: bool,
) -> ColorPermissionContext:
    """Build the additive explicit-chart + expansion color contract."""

    explicit_set = set(explicit)
    expansion_set = set(expansion) if expansion_enabled else set()
    return ColorPermissionContext(
        explicit=frozenset(explicit_set),
        expansion=frozenset(expansion_set),
        allowed=frozenset(explicit_set | expansion_set),
        expansion_enabled=bool(expansion_enabled),
    )


def four_note_color_permission_notes(
    chord: ParsedChord,
    source_degrees: tuple[str, ...] | list[str],
    context: ColorPermissionContext,
) -> tuple[str, ...]:
    """Return gate/fidelity metadata for a concrete 4-note color source.

    This is the central audit surface for color-bearing 4-note voicings. Gate
    notes remain backward compatible while chart-fidelity notes show whether the
    chosen source represents or omits explicitly written chart color.
    """

    source_colors = source_color_degrees(chord, source_degrees)
    explicit = set(context.explicit)
    expansion = set(context.expansion)
    allowed = set(context.allowed)
    unauthorized = source_colors - allowed
    explicit_hit = source_colors & explicit
    explicit_omitted = explicit - source_colors
    if alt_symbol_uses_palette_fidelity(chord):
        # ``alt`` means the chart has requested the altered-dominant palette,
        # not that a 4-note voicing must contain every altered color at once.
        altered_hit = source_colors & ALTERED_DOMINANT_PALETTE
        if altered_hit:
            explicit_hit = altered_hit
            explicit_omitted = set()

    notes: list[str] = ["four_note_allowed_color_set_contract_v2_1_27"]
    if explicit and expansion:
        notes.append("four_note_color_gate_open_explicit_chart_color_plus_harmonic_expansion")
        # Keep both historical gate markers visible for existing audit tooling.
        notes.append("four_note_color_gate_open_explicit_chord_symbol_color")
        notes.append("four_note_color_gate_open_harmonic_expansion")
    elif explicit:
        notes.append("four_note_color_gate_open_explicit_chord_symbol_color")
    elif expansion:
        notes.append("four_note_color_gate_open_harmonic_expansion")
    else:
        notes.append("four_note_color_gate_closed")

    if source_colors:
        notes.append(f"four_note_source_color_set_{_degree_order_token(tuple(sorted(source_colors)))}")
    if explicit:
        notes.append(f"four_note_explicit_chart_color_set_{_degree_order_token(tuple(sorted(explicit)))}")
    if expansion:
        notes.append(f"four_note_expansion_color_set_{_degree_order_token(tuple(sorted(expansion)))}")
    if allowed:
        notes.append(f"four_note_allowed_color_set_{_degree_order_token(tuple(sorted(allowed)))}")

    if unauthorized:
        notes.append("four_note_color_permission_blocked_unallowed_color")
        notes.append(f"four_note_unallowed_color_set_{_degree_order_token(tuple(sorted(unauthorized)))}")
    if explicit_hit:
        notes.append("chart_color_fidelity_contains_explicit_color")
        notes.append(f"chart_color_fidelity_explicit_hit_{_degree_order_token(tuple(sorted(explicit_hit)))}")
    if explicit_omitted:
        notes.append("chart_color_fidelity_omits_explicit_color")
        notes.append(f"chart_color_fidelity_explicit_omitted_{_degree_order_token(tuple(sorted(explicit_omitted)))}")
    return tuple(_dedupe(notes))


def alt_symbol_uses_palette_fidelity(chord: ParsedChord) -> bool:
    """Return whether ``alt`` should be treated as a palette request."""

    return bool(chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in set(chord.alterations or ())))


def source_color_degrees(chord: ParsedChord, degrees: tuple[str, ...] | list[str]) -> set[str]:
    """Return color/tension degrees used by a resolved source.

    Chord-defining altered chord tones such as the b5 of m7b5/dim are not
    treated as optional color. Dominant altered b5/#5 remain color material.
    """

    colors = {str(degree) for degree in degrees if str(degree) in COLOR_DEGREES}
    if is_half_diminished_like(chord) or chord.quality == "diminished":
        colors.discard("b5")
    if chord.quality == "augmented" and not chord.is_dominant:
        colors.discard("#5")
    return colors


def _degree_order_token(source: tuple[str, ...]) -> str:
    return "_".join(str(degree).replace("#", "sharp").replace("b", "flat") for degree in source)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
