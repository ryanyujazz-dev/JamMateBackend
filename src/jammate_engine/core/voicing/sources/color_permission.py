from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from jammate_engine.core.harmony.chord_parser import ParsedChord
from jammate_engine.core.harmony.material import ChordMaterial
from ..policy import (
    VoicingPolicy,
    harmonic_expansion_allowed,
    resolve_altered_dominant_policy,
)


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
COLOR_PERMISSION_ADAPTER_VERSION = "v2_6_19"


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

# ---------------------------------------------------------------------------
# Adapter helpers
# ---------------------------------------------------------------------------
# These helpers own color-admission inputs and permission-context construction.
# They deliberately do *not* construct voicing sources. Inventory modules still
# decide which functional degree sources to emit after this module says which
# chart-explicit and style-expansion colors are admissible.


def explicit_symbol_color_degrees(chord: ParsedChord) -> set[str]:
    """Return concrete color/tension degrees explicitly requested by a chart.

    The result is a color-permission input, not a voicing source. Chord-quality
    identity tones such as the b5 of m7b5/dim are removed so they do not open a
    color gate by themselves.
    """

    out: set[str] = set(chord.alterations or ())
    if "alt" in out:
        out.discard("alt")
        out.update({"b9", "#9", "#11", "b13"})
    out.update(chord.extensions or ())
    if "sus4" in chord.suspensions:
        out.add("11")
    if "sus2" in chord.suspensions:
        out.add("9")
    # Prefer altered spelling over generic extension spelling when both appear.
    if "b9" in out or "#9" in out:
        out.discard("9")
    if "#11" in out:
        out.discard("11")
    if "b13" in out:
        out.discard("13")
    if is_half_diminished_like(chord) or chord.quality == "diminished":
        # b5 / bb7 are chord-quality identity tones here, not optional chart color.
        out.discard("b5")
        out.discard("bb7")
    return out


def rootless_ab_explicit_color_degrees(chord: ParsedChord) -> set[str]:
    """Return explicit colors that may open the 4-note rootless A/B gate."""

    # Preserve the historical rootless A/B routing behavior: rootless color
    # families only treat extension/alteration/sus material as explicit color.
    explicit = set(explicit_symbol_color_degrees(chord))
    if is_half_diminished_like(chord) or chord.quality == "diminished":
        explicit.discard("b5")
        explicit.discard("bb7")
    return explicit


def ordered_explicit_colors(chord: ParsedChord, explicit: set[str] | None = None) -> list[str]:
    """Return explicit chart colors in stable altered-before-diatonic order."""

    explicit = explicit_symbol_color_degrees(chord) if explicit is None else set(explicit)
    ordered: list[str] = []
    for degree in ("b9", "#9", "#11", "b13", "#5", "b5", "9", "11", "13"):
        if degree in explicit:
            ordered.append(degree)
    return ordered or list(explicit)


def expansion_color_candidates(chord: ParsedChord, material: ChordMaterial, policy: VoicingPolicy) -> list[str]:
    """Return style/policy-authorized unnotated color candidates.

    This is an admission helper. Source inventory may choose how to realize one
    of these colors, but should not duplicate this policy-gate ordering.
    """

    mode = getattr(policy.color_policy_mode, "value", str(policy.color_policy_mode))
    available = list(material.available_tensions)
    altered_decision = resolve_altered_dominant_policy(policy, chord)
    if altered_decision.authorized_for_chord and chord.is_dominant:
        preferred = ["b9", "#9", "b13", "#11", "#5", "b5", "13", "9"]
    elif mode == "altered_dominant" and chord.is_dominant:
        preferred = ["b9", "#9", "b13", "#11", "13", "9"]
    elif mode == "rich_reharm_color":
        preferred = ["9", "13", "#11", "11", "b9", "#9", "b13"]
    elif chord.is_dominant:
        preferred = ["13", "9", "b9", "#9", "b13", "#11"]
    elif is_half_diminished_like(chord):
        preferred = ["b9", "11", "b13"]
    elif chord.quality == "minor":
        preferred = ["9", "11", "13"]
    elif chord.has_major_seventh:
        preferred = major_seventh_safe_extension_preference(chord, policy)
    else:
        preferred = ["9", "13", "11", "#11"]
    colors = [degree for degree in preferred if degree in available]
    # Keep the candidate pool small so low-weight 1/5 alternatives can still be
    # sampled occasionally rather than buried behind too many equivalent colors.
    return _dedupe_str(colors)[:3] or ([available[0]] if available else ["9"])


def major_seventh_safe_extension_preference(chord: ParsedChord, policy: VoicingPolicy) -> list[str]:
    """Return style-safe color order for ordinary major-seventh expansion."""

    mode = getattr(policy.color_policy_mode, "value", str(policy.color_policy_mode))
    if mode == "rich_reharm_color":
        return ["9", "13", "#11"]
    if major_seventh_sharp11_harmonic_color_intent_enabled(policy):
        return ["9", "13", "#11"]
    return ["9", "13"]


def major_seventh_sharp11_harmonic_color_intent_enabled(policy: VoicingPolicy | None) -> bool:
    """Return whether unnotated maj7#11 has explicit harmonic-color intent."""

    metadata = dict(getattr(policy, "metadata", {}) or {}) if policy is not None else {}
    truthy_flags = (
        "allow_unnotated_major_seventh_sharp11",
        "allow_unnotated_maj7_sharp11",
        "major_seventh_sharp11_enabled",
        "maj7_sharp11_enabled",
        "lydian_major_color_enabled",
        "bright_major_color_enabled",
    )
    if any(bool(metadata.get(flag)) for flag in truthy_flags):
        return True

    nested = metadata.get("safe_extension_color_gate") or metadata.get("major_seventh_color_gate") or {}
    if isinstance(nested, dict):
        if any(bool(nested.get(flag)) for flag in truthy_flags):
            return True
        policy_value = str(
            nested.get("maj7_sharp11")
            or nested.get("major_seventh_sharp11")
            or nested.get("unnotated_maj7_sharp11")
            or ""
        ).strip().lower()
        if policy_value in {"allow", "enabled", "on", "intent", "lydian", "bright", "low_frequency", "occasional"}:
            return True

    textual_values = {
        str(metadata.get("harmonic_color_intent", "")).strip().lower(),
        str(metadata.get("major_color_intent", "")).strip().lower(),
        str(metadata.get("scale_mode", "")).strip().lower(),
        str(metadata.get("modal_context", "")).strip().lower(),
        str(metadata.get("harmony_context", "")).strip().lower(),
    }
    intent_tokens = {
        "lydian",
        "lydian_major",
        "lydian-major",
        "maj7#11",
        "major#11",
        "sharp11",
        "sharp_11",
        "#11",
        "bright",
        "brighter",
        "modern",
        "modern_bright",
    }
    return bool(textual_values & intent_tokens)


def build_voicing_color_permission_context(
    chord: ParsedChord,
    material: ChordMaterial,
    policy: VoicingPolicy,
    *,
    rootless: bool = False,
) -> ColorPermissionContext:
    """Return explicit + expansion color permission for one voicing family."""

    explicit = rootless_ab_explicit_color_degrees(chord) if rootless else explicit_symbol_color_degrees(chord)
    expansion_enabled = harmonic_expansion_allowed(policy, chord)
    expansion = expansion_color_candidates(chord, material, policy) if expansion_enabled else ()
    altered_decision = resolve_altered_dominant_policy(policy, chord)
    if expansion_enabled and altered_decision.authorized_for_chord and not altered_decision.explicit_chord_symbol_altered:
        expansion = _dedupe_str([*list(expansion), *list(ALTERED_DOMINANT_PALETTE)])
    return build_color_permission_context(
        explicit=explicit,
        expansion=expansion,
        expansion_enabled=bool(expansion_enabled),
    )


def _dedupe_str(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out

