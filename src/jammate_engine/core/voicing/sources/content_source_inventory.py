from __future__ import annotations

from typing import Any

from jammate_engine.core.harmony.chord_parser import ParsedChord, parse_chord
from jammate_engine.core.harmony.material import (
    ChordMaterial,
    fifth_degree_for_chord,
    seventh_degree_for_chord,
    third_degree_for_chord,
)
from jammate_engine.core.harmony.scale_resolver import resolve_functional_degree_role

from .chord_tone_resolver import content_degrees
from .content_family_router import ROOTLESS_FAMILIES, TRIAD_FAMILIES
from .color_permission import (
    ColorPermissionContext,
    build_voicing_color_permission_context as _color_permission_context,
    expansion_color_candidates as _expansion_color_candidates,
    explicit_symbol_color_degrees as _explicit_symbol_color_degrees,
    four_note_color_permission_notes as _four_note_color_permission_notes,
    is_half_diminished_like as _is_half_diminished_like,
    ordered_explicit_colors as _ordered_explicit_colors,
    rootless_ab_explicit_color_degrees as _rootless_ab_explicit_color_degrees,
)
from .four_note_sources import (
    degree_order_token as _degree_order_token,
    degree_pair as _degree_pair,
    functional_source_rotation_options as _functional_source_rotation_options,
    role_order_token as _role_order_token,
    rotations as _rotations,
)
from ..policy import (
    ContentFamily,
    RootSupportPolicy,
    VoicingPolicy,
    altered_dominant_source_weight_bias,
    harmonic_expansion_allowed,
    resolve_altered_dominant_policy,
)

CONTENT_SOURCE_INVENTORY_VERSION = "v2_6_19"

def content_degree_options(
    symbol: str,
    chord: ParsedChord,
    material: ChordMaterial,
    family: ContentFamily,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return one or more degree recipes for a content family.

    Most content families have a single deterministic degree set.  The 3-note
    shell tuning families are intentionally variant-producing so the selector
    can make weighted choices between extension color and internal 1/5 support
    without pretending root+3/10 is a standalone 2-note voicing.

    v2_1_11 makes the color gate global: 3-note shell color, 4-note rootless A/B,
    and future 5/6/7+ color recipes must all use HarmonicExpansionPolicy /
    VoicingColorPolicy rather than local family-specific gates.  Rootless A/B is
    one consumer of that policy: ordinary Cmaj7 / Dm7 / G7 stay conservative,
    while explicit chart colors or expansion intent may allow color recipes.
    """

    if family == ContentFamily.SHELL_PLUS_5:
        return _shell_plus_1_or_5_options(chord, policy)
    if family == ContentFamily.SHELL_PLUS_COLOR:
        return _shell_plus_color_options(chord, material, policy)
    if family == ContentFamily.SEVENTH_BASIC:
        return _seventh_basic_1357_options(chord, policy)
    if family == ContentFamily.ROOTED_COLOR:
        return _rooted_color_4note_source_inventory_options(chord, material, policy)
    if family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}:
        return _rootless_ab_options(chord, material, family, policy)
    if family in TRIAD_FAMILIES:
        triad_4note_options = _four_note_triad_symbol_options(chord, policy)
        if triad_4note_options:
            return triad_4note_options
    return [(content_degrees(symbol, family, policy.root_support, policy=policy), ())]


def _resolve_source_roles(chord: ParsedChord, roles: tuple[str, ...]) -> tuple[str, ...]:
    """Resolve functional source roles into chord-quality-correct degree tokens."""

    return tuple(resolve_functional_degree_role(chord, role) for role in roles)


def _fifth_degree_for_voicing(chord: ParsedChord) -> str:
    return "b5" if _is_half_diminished_like(chord) else fifth_degree_for_chord(chord)


def _seventh_basic_1357_options(
    chord: ParsedChord,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return source-derived rotations for conservative 4-note chord material.

    V2.1.23 keeps the voicing source names at the functional-role layer.  The
    old ``1357`` label remains a compatibility alias, but the canonical source
    contract is now expressed as role order, for example
    ``root-third-fifth-seventh`` or ``root-fourth-fifth-seventh``.  Core Harmony
    resolves the concrete accidentals: diminished seventh resolves to ``bb7``,
    sus4 resolves the third slot as a fourth only when the source explicitly asks
    for ``fourth``, and sixth chords use ``sixth`` rather than pretending the
    role is a seventh.
    """

    source_roles, legacy_alias, content_note, extra_notes = _basic_4note_source_inventory_for_chord(chord)
    source = _resolve_source_roles(chord, source_roles)
    if not source[-1]:
        return [(content_degrees(chord.symbol, ContentFamily.SEVENTH_BASIC, policy.root_support, policy=policy), ())]

    return _functional_source_rotation_options(
        source=source,
        source_roles=source_roles,
        note_prefix="basic_4note",
        family_notes=(
            "basic_4note_functional_source_family",
            "basic_4note_1357_source_family",  # compatibility alias for existing tuning code/tests
            content_note,
            f"basic_4note_content_type_{legacy_alias}",
            f"basic_4note_functional_content_type_{_role_order_token(source_roles)}",
            *extra_notes,
            "basic_4note_conservative_chord_symbol_material",
            "voicing_source_roles_resolved_by_core_harmony",
        ),
    )


def _basic_4note_source_inventory_for_chord(chord: ParsedChord) -> tuple[tuple[str, ...], str, str, tuple[str, ...]]:
    """Return the conservative 4-note source family for this chord symbol."""

    if chord.quality == "diminished" and chord.has_seventh:
        return (
            ("root", "third", "fifth", "seventh"),
            "dim7",
            "basic_4note_functional_content_type_root_third_fifth_seventh",
            ("basic_4note_dim7_source_family", "basic_4note_dim7_resolved_by_harmony_as_root_third_fifth_diminished_seventh"),
        )
    if chord.is_suspended and chord.has_seventh:
        return (
            ("root", "fourth", "fifth", "seventh"),
            "145b7",
            "basic_4note_functional_content_type_root_fourth_fifth_seventh",
            ("basic_4note_sus_source_family", "basic_4note_sus_145b7_alias"),
        )
    if chord.has_sixth and not chord.has_seventh:
        return (
            ("root", "third", "fifth", "sixth"),
            "1356",
            "basic_4note_functional_content_type_root_third_fifth_sixth",
            ("basic_4note_sixth_source_family", "basic_4note_1356_alias"),
        )
    return (
        ("root", "third", "fifth", "seventh"),
        "1357",
        "basic_4note_functional_content_type_root_third_fifth_seventh",
        ("basic_4note_root_third_fifth_seventh_from_canonical_inversion_family",),
    )




def _four_note_triad_symbol_options(
    chord: ParsedChord,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return 4-note closed functional sources for no-seventh triad/add/sus symbols.

    Plain triads are complete three-note symbols, but a density-4 closed request
    should not fall back to a missing seventh or to jazz upper-extension logic.
    It should double the compact triad by rotation: root-third-fifth-root,
    third-fifth-root-third, fifth-root-third-fifth.  Sus symbols follow the same
    logic, e.g. sus2 -> root-second-fifth-root / second-fifth-root-second /
    fifth-root-second-fifth.  Explicit add9/sixth symbols remain functional
    four-note sources such as root-third-fifth-ninth or root-third-fifth-sixth.
    """

    min_density, preferred_density, max_density = policy.effective_density_range
    if preferred_density < 4 or max_density < 4:
        return []
    if chord.has_seventh:
        return []

    specified = _explicit_symbol_color_degrees(chord)
    expansion = harmonic_expansion_allowed(policy, chord)
    base_notes = (
        "triad_4note_functional_source_family",
        "four_note_triad_aware_source_pool",
        "four_note_no_seventh_chord_not_partial_fallback",
        "voicing_source_roles_resolved_by_core_harmony",
    )

    # Explicit add-tone / sixth symbols are chord-symbol material, not reharm.
    if chord.has_sixth and "9" in specified:
        return _triad_4note_single_source(
            chord,
            ("root", "third", "sixth", "ninth"),
            (*base_notes, "explicit_chord_symbol_sixth_used", "explicit_chord_symbol_color_used", "triad_4note_content_type_root_third_sixth_ninth", "triad_4note_1369_alias"),
        )
    if chord.has_sixth:
        return _triad_4note_single_source(
            chord,
            ("root", "third", "fifth", "sixth"),
            (*base_notes, "explicit_chord_symbol_sixth_used", "triad_4note_content_type_root_third_fifth_sixth", "triad_4note_1356_alias"),
        )
    if "9" in specified and not chord.is_suspended:
        return _triad_4note_single_source(
            chord,
            ("root", "third", "fifth", "ninth"),
            (*base_notes, "explicit_chord_symbol_color_used", "triad_4note_content_type_root_third_fifth_ninth", "triad_4note_1359_alias"),
        )

    if expansion and not chord.is_suspended and chord.quality not in {"diminished", "augmented"}:
        options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
        # Conservative triad expansion only: seventh / sixth / add9.  Do not
        # jump from a plain triad directly into 9/11/13 shell-color language.
        for roles, note in (
            (("root", "third", "fifth", "seventh"), "triad_harmonic_expansion_low_order_seventh"),
            (("root", "third", "fifth", "sixth"), "triad_harmonic_expansion_low_order_sixth"),
            (("root", "third", "fifth", "ninth"), "triad_harmonic_expansion_low_order_add9"),
        ):
            options.extend(_triad_4note_single_source(chord, roles, (*base_notes, note, f"triad_4note_content_type_{_role_order_token(roles)}")))
        # Keep the doubled triad available as the stable non-expanded fallback.
        options.extend(_triad_4note_doubled_rotation_sources(chord, _triad_base_roles_for_chord(chord), (*base_notes, "triad_harmonic_expansion_plain_doubled_triad_fallback")))
        return options

    return _triad_4note_doubled_rotation_sources(chord, _triad_base_roles_for_chord(chord), base_notes)


def _triad_base_roles_for_chord(chord: ParsedChord) -> tuple[str, str, str]:
    if chord.quality == "sus2":
        return ("root", "second", "fifth")
    if chord.quality == "sus4" or "sus4" in set(chord.suspensions or ()):
        return ("root", "fourth", "fifth")
    return ("root", "third", "fifth")


def _triad_4note_single_source(
    chord: ParsedChord,
    source_roles: tuple[str, ...],
    notes: tuple[str, ...],
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    source = _resolve_source_roles(chord, source_roles)
    return _functional_source_rotation_options(
        source=source,
        source_roles=source_roles,
        note_prefix="triad_4note",
        family_notes=(
            *notes,
            f"triad_4note_functional_content_type_{_role_order_token(source_roles)}",
        ),
    )


def _triad_4note_doubled_rotation_sources(
    chord: ParsedChord,
    base_roles: tuple[str, str, str],
    notes: tuple[str, ...],
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return 1351/3513/5135-style sources while preserving the doubled note."""

    out: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    for inversion_index in range(len(base_roles)):
        roles = tuple(base_roles[inversion_index:] + base_roles[:inversion_index] + (base_roles[inversion_index],))
        resolved = _resolve_source_roles(chord, roles)
        role_token = _role_order_token(roles)
        degree_token = _degree_order_token(resolved)
        variant_notes = (
            *notes,
            "triad_4note_doubled_closed_rotation_family",
            f"triad_4note_functional_content_type_{role_token}",
            f"triad_4note_content_type_{role_token}",
            f"triad_4note_inversion_index_{inversion_index}",
            f"triad_4note_source_role_order_{_role_order_token(base_roles)}",
            f"triad_4note_degree_role_order_{role_token}",
            f"triad_4note_source_order_{degree_token}",
            f"triad_4note_degree_order_{degree_token}",
            "triad_4note_from_doubled_triad_rotation_family",
        )
        # Do not dedupe: root-third-fifth-root must remain a 4-note source.
        out.append(([_degree_pair(degree) for degree in resolved], variant_notes))
    return out


def _three_note_color_role(color: str) -> str:
    if color in {"b9", "#9", "b13", "#5"}:
        return "altered_color"
    if color == "#11":
        return "eleventh"
    if color == "11":
        return "eleventh"
    if color == "13":
        return "thirteenth"
    return "ninth"


def _three_note_source_option(
    chord: ParsedChord,
    source_roles: tuple[str, ...],
    notes: tuple[str, ...] = (),
    *,
    explicit_degrees: tuple[str, ...] = (),
) -> tuple[list[tuple[str, int]], tuple[str, ...]]:
    resolved: list[str] = []
    explicit_iter = iter(explicit_degrees)
    for role in source_roles:
        if role == "altered_color":
            resolved.append(next(explicit_iter, "b9"))
        else:
            resolved.append(resolve_functional_degree_role(chord, role))
    role_token = _role_order_token(source_roles)
    degree_token = _degree_order_token(tuple(resolved))
    metadata = (
        "three_note_functional_source_family",
        f"three_note_functional_source_type_{role_token}",
        f"three_note_source_role_order_{role_token}",
        f"three_note_degree_order_{degree_token}",
        "voicing_source_roles_resolved_by_core_harmony",
        *notes,
    )
    return ([_degree_pair(degree) for degree in resolved], metadata)

def _shell_plus_1_or_5_options(chord: ParsedChord, policy: VoicingPolicy) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    seventh = seventh_degree_for_chord(chord)
    if _is_half_diminished_like(chord):
        return [_three_note_source_option(chord, ("third", "seventh", "fifth"), ("three_note_half_diminished_identity_source",))]
    if chord.quality == "diminished":
        if seventh:
            return [_three_note_source_option(chord, ("third", "seventh", "fifth"), ("three_note_diminished_identity_source",))]
        return [_three_note_source_option(chord, ("root", "third", "fifth"), ("three_note_diminished_triad_source",))]
    if not seventh:
        return _three_note_triad_symbol_options(chord, expansion=False, notes=("three_note_triad_aware_no_partial_fallback", "no_seventh_chord_uses_triad_source_pool"))

    return [
        _three_note_source_option(chord, ("third", "seventh", "fifth"), ("shell_plus_1or5_component_5_primary", "three_note_source_component_fifth_primary")),
        _three_note_source_option(chord, ("third", "seventh", "root"), ("shell_plus_1or5_component_root_low_weight", "three_note_source_component_root_low_weight")),
    ]


def _shell_plus_color_options(
    chord: ParsedChord,
    material: ChordMaterial,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    seventh = seventh_degree_for_chord(chord)
    specified = _explicit_symbol_color_degrees(chord)

    # m7b5 and m11b5-like symbols remain identity-first in color-tuning mode.
    if _is_half_diminished_like(chord):
        return [_three_note_source_option(chord, ("third", "seventh", "fifth"), ("half_diminished_uses_b3_b7_b5", "three_note_half_diminished_identity_source"))]
    if chord.quality == "diminished":
        if seventh:
            return [_three_note_source_option(chord, ("third", "seventh", "fifth"), ("diminished_internal_identity_tones", "three_note_diminished_identity_source"))]
        return [_three_note_source_option(chord, ("root", "third", "fifth"), ("diminished_triad_root_identity", "three_note_diminished_triad_source"))]

    if not seventh:
        return _three_note_triad_symbol_options(
            chord,
            expansion=harmonic_expansion_allowed(policy, chord),
            notes=("three_note_triad_aware_source_pool",),
        )

    if specified:
        color = _ordered_explicit_colors(chord)[0]
        role = _three_note_color_role(color)
        return [_three_note_source_option(chord, ("third", "seventh", role), ("explicit_chord_symbol_color_used", f"three_note_source_component_explicit_{_degree_order_token((color,))}"), explicit_degrees=(color,))]

    if not harmonic_expansion_allowed(policy, chord):
        return [_three_note_source_option(chord, ("third", "seventh", "fifth"), ("no_unspecified_color_added", "three_note_source_component_fifth_fallback"))]

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    for color in _expansion_color_candidates(chord, material, policy):
        role = _three_note_color_role(color)
        options.append(_three_note_source_option(chord, ("third", "seventh", role), ("harmonic_expansion_color_used", f"shell_expansion_component_{color}", f"three_note_source_component_expanded_{_degree_order_token((color,))}"), explicit_degrees=(color,)))

    # Even with expansion enabled, not every 3-note shell should be colored.
    # 5 remains the stable internal fallback; root/1 is a very low-weight
    # occasional cluster/tension accent, not a rooted-foundation default.
    options.append(_three_note_source_option(chord, ("third", "seventh", "fifth"), ("harmonic_expansion_internal_5_fallback", "shell_expansion_component_5", "three_note_source_component_fifth_fallback")))
    options.append(_three_note_source_option(chord, ("third", "seventh", "root"), ("harmonic_expansion_root_cluster_low_weight", "shell_expansion_component_root", "three_note_source_component_root_low_weight")))
    return options


def _three_note_triad_symbol_options(
    chord: ParsedChord,
    *,
    expansion: bool,
    notes: tuple[str, ...] = (),
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return 3-note functional sources for non-seventh triad/add/sus symbols.

    Plain triads are not partial shell fallbacks.  When a chart writes C/Cm/Csus
    and harmonic expansion is off, density-3 closed voicing should use a real
    three-note rooted source.  If expansion is on, keep triad expansion
    conservative: seventh/sixth/add9/sus-like sources only, not 9/11/13 shell
    colors.
    """

    base_notes = (
        *notes,
        "three_note_functional_triad_add_sus_source_pool",
        "three_note_no_seventh_chord_not_partial_fallback",
    )
    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []

    if chord.quality == "sus2":
        options.append(_three_note_source_option(chord, ("root", "second", "fifth"), (*base_notes, "three_note_source_component_sus2", "explicit_chord_symbol_suspension_used")))
        if expansion:
            options.append(_three_note_source_option(chord, ("root", "fifth", "ninth"), (*base_notes, "triad_harmonic_expansion_low_order_add9", "three_note_source_component_add9_like")))
        return options

    if chord.quality == "sus4":
        options.append(_three_note_source_option(chord, ("root", "fourth", "fifth"), (*base_notes, "three_note_source_component_sus4", "explicit_chord_symbol_suspension_used")))
        if expansion:
            options.append(_three_note_source_option(chord, ("root", "fifth", "ninth"), (*base_notes, "triad_harmonic_expansion_low_order_add9", "three_note_source_component_add9_like")))
        return options

    if chord.has_sixth:
        options.append(_three_note_source_option(chord, ("root", "third", "sixth"), (*base_notes, "explicit_chord_symbol_sixth_used", "three_note_source_component_explicit_6")))
        if "9" in _explicit_symbol_color_degrees(chord):
            options.append(_three_note_source_option(chord, ("root", "third", "ninth"), (*base_notes, "explicit_chord_symbol_color_used", "three_note_source_component_explicit_9")))
        return options

    if "9" in _explicit_symbol_color_degrees(chord):
        return [_three_note_source_option(chord, ("root", "third", "ninth"), (*base_notes, "explicit_chord_symbol_color_used", "three_note_source_component_explicit_9"))]

    options.append(_three_note_source_option(chord, ("root", "third", "fifth"), (*base_notes, "three_note_source_component_plain_triad")))

    if expansion and chord.quality not in {"diminished", "augmented"}:
        options.extend([
            _three_note_source_option(chord, ("root", "third", "sixth"), (*base_notes, "triad_harmonic_expansion_low_order_sixth", "three_note_source_component_expanded_6")),
            _three_note_source_option(chord, ("root", "third", "ninth"), (*base_notes, "triad_harmonic_expansion_low_order_add9", "three_note_source_component_expanded_9")),
            _three_note_source_option(chord, ("root", "third", "seventh"), (*base_notes, "triad_harmonic_expansion_low_order_seventh", "three_note_source_component_expanded_7")),
        ])
    return options



def _explicit_eleventh_requested(specified: set[str]) -> bool:
    return bool({"11", "#11"} & set(specified))


def _explicit_eleventh_context_notes(chord: ParsedChord, resolved_eleventh: str) -> tuple[str, ...]:
    notes = ["explicit_eleventh_source_family"]
    if resolved_eleventh == "#11":
        notes.append("explicit_sharp_eleventh_source_family")
    else:
        notes.append("explicit_natural_eleventh_source_family")
    return tuple(notes)


def _ninth_allowed_by_color_context(chord: ParsedChord, color_context: ColorPermissionContext) -> bool:
    ninth = resolve_functional_degree_role(chord, "ninth")
    return ninth in set(color_context.allowed)

def _rooted_color_4note_source_inventory_options(
    chord: ParsedChord,
    material: ChordMaterial,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return 4-note rooted color canonical sources without changing ratios.

    This is an inventory/formalization pass.  It exposes the remaining compact
    closed-position source families while preserving the global color gate:
    explicit chart colors are always faithful to the symbol, and unnotated color
    only appears when HarmonicExpansionPolicy allows it.
    """

    color_context = _color_permission_context(chord, material, policy)
    specified = set(color_context.explicit)
    expansion = color_context.expansion_enabled
    source_roles: tuple[str, ...] | None = None
    source: tuple[str, ...] | None = None
    legacy_alias = ""
    content_note = ""
    extra_notes: tuple[str, ...] = ()
    altered_decision = resolve_altered_dominant_policy(policy, chord)
    altered_rooted_options = _rooted_color_4note_altered_dominant_options(
        chord=chord,
        material=material,
        policy=policy,
        color_context=color_context,
        specified=specified,
        expansion=expansion,
        altered_decision=altered_decision,
    )
    if altered_decision.explicit_chord_symbol_altered and altered_rooted_options:
        return altered_rooted_options

    if _is_half_diminished_like(chord) or (chord.quality == "diminished" and chord.has_seventh):
        # Half-diminished and diminished-seventh quality depends on the 5th as
        # well as the guide tones.  The global seventh-source integrity gate
        # must therefore preserve 3/7 *and* the diminished fifth identity here
        # instead of replacing it with add9 color.
        source_roles = ("root", "third", "fifth", "seventh")
        source = _resolve_source_roles(chord, source_roles)
        legacy_alias = "1_3_b5_7" if _is_half_diminished_like(chord) else "1_b3_b5_bb7"
        content_note = "rooted_color_4note_functional_content_type_root_third_fifth_seventh"
        extra_notes = (
            "rooted_color_4note_diminished_identity_source_family",
            "global_seventh_chord_expansion_source_integrity_gate_applied",
            "seventh_chord_expansion_preserves_3_and_7",
            "seventh_chord_expansion_preserves_diminished_fifth_identity",
            "triad_add9_source_blocked_for_seventh_chord",
        )
    elif _explicit_eleventh_requested(specified) and (seventh_degree_for_chord(chord) or chord.has_seventh or chord.is_dominant):
        source_roles = ("root", "third", "seventh", "eleventh")
        source = _resolve_source_roles(chord, source_roles)
        resolved_eleventh = source[-1]
        legacy_alias = "1_3_7_sharp11" if resolved_eleventh == "#11" else "1_3_7_11"
        content_note = "rooted_color_4note_functional_content_type_root_third_seventh_eleventh"
        extra_notes = (
            "rooted_color_4note_explicit_eleventh_source_family",
            "rooted_color_4note_1_3_7_11_alias",
            *_explicit_eleventh_context_notes(chord, resolved_eleventh),
            f"rooted_color_4note_resolved_eleventh_{_degree_order_token((resolved_eleventh,))}",
        )
    elif chord.has_sixth and "9" in specified:
        source_roles = ("root", "third", "sixth", "ninth")
        source = _resolve_source_roles(chord, source_roles)
        legacy_alias = "1369"
        content_note = "rooted_color_4note_functional_content_type_root_third_sixth_ninth"
        extra_notes = ("rooted_color_4note_6_9_source_family", "rooted_color_4note_1369_alias")
    elif "13" in specified and (seventh_degree_for_chord(chord) or chord.has_seventh or chord.is_dominant):
        source_roles = ("root", "third", "seventh", "thirteenth")
        source = _resolve_source_roles(chord, source_roles)
        legacy_alias = "1_3_7_13"
        content_note = "rooted_color_4note_functional_content_type_root_third_seventh_thirteenth"
        extra_notes = ("rooted_color_4note_explicit_13_source_family", "rooted_color_4note_1_3_7_13_alias")
    elif "9" in specified:
        if _seventh_chord_source_integrity_required(chord):
            source_roles = ("root", "third", "seventh", "ninth")
            source = _resolve_source_roles(chord, source_roles)
            legacy_alias = "1_3_7_9"
            content_note = "rooted_color_4note_functional_content_type_root_third_seventh_ninth"
            extra_notes = (
                "rooted_color_4note_explicit_9_source_family",
                "rooted_color_4note_1_3_7_9_alias",
                "global_seventh_chord_expansion_source_integrity_gate_applied",
                "seventh_chord_expansion_preserves_3_and_7",
                "triad_add9_source_blocked_for_seventh_chord",
            )
        else:
            source_roles = ("root", "third", "fifth", "ninth")
            source = _resolve_source_roles(chord, source_roles)
            legacy_alias = "1359"
            content_note = "rooted_color_4note_functional_content_type_root_third_fifth_ninth"
            extra_notes = ("rooted_color_4note_add9_source_family", "rooted_color_4note_1359_alias")
    elif expansion:
        colors = _expansion_color_candidates(chord, material, policy)
        color_set = set(colors)
        if {"9", "b9", "#9"} & color_set:
            if _seventh_chord_source_integrity_required(chord):
                source_roles = ("root", "third", "seventh", "ninth")
                source = _resolve_source_roles(chord, source_roles)
                legacy_alias = "1_3_7_9"
                content_note = "rooted_color_4note_functional_content_type_root_third_seventh_ninth"
                extra_notes = (
                    "rooted_color_4note_harmonic_expansion_source_family",
                    "harmonic_expansion_color_used",
                    "rooted_color_4note_1_3_7_9_alias",
                    "global_seventh_chord_expansion_source_integrity_gate_applied",
                    "seventh_chord_expansion_preserves_3_and_7",
                    "triad_add9_source_blocked_for_seventh_chord",
                )
            else:
                source_roles = ("root", "third", "fifth", "ninth")
                source = _resolve_source_roles(chord, source_roles)
                legacy_alias = "1359"
                content_note = "rooted_color_4note_functional_content_type_root_third_fifth_ninth"
                extra_notes = ("rooted_color_4note_harmonic_expansion_source_family", "harmonic_expansion_color_used")
        elif {"13", "b13"} & color_set and _seventh_chord_source_integrity_required(chord):
            source_roles = ("root", "third", "seventh", "thirteenth")
            source = _resolve_source_roles(chord, source_roles)
            legacy_alias = "1_3_7_13"
            content_note = "rooted_color_4note_functional_content_type_root_third_seventh_thirteenth"
            extra_notes = (
                "rooted_color_4note_harmonic_expansion_source_family",
                "harmonic_expansion_color_used",
                "rooted_color_4note_1_3_7_13_alias",
                "global_seventh_chord_expansion_source_integrity_gate_applied",
                "seventh_chord_expansion_preserves_3_and_7",
            )

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    if source_roles and source:
        options.extend(_functional_source_rotation_options(
            source=source,
            source_roles=source_roles,
            note_prefix="rooted_color_4note",
            family_notes=(
                "rooted_color_4note_functional_source_family",
                *_four_note_color_permission_notes(chord, source, color_context),
                content_note,
                f"rooted_color_4note_content_type_{legacy_alias}",
                *extra_notes,
                "voicing_source_roles_resolved_by_core_harmony",
            ),
        ))
    if altered_rooted_options:
        options.extend(altered_rooted_options)
    return options


def _rooted_color_4note_altered_dominant_options(
    *,
    chord: ParsedChord,
    material: ChordMaterial,
    policy: VoicingPolicy,
    color_context: ColorPermissionContext,
    specified: set[str],
    expansion: bool,
    altered_decision: Any,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    if not altered_decision.authorized_for_chord:
        return []
    colors = _ordered_altered_dominant_colors(chord, material, specified=specified, expansion=expansion)
    if not colors:
        return []
    source_roles = ("root", "third", "seventh", "altered_color_a")
    source = _resolve_source_roles(chord, ("root", "third", "seventh")) + (colors[0],)
    return _functional_source_rotation_options(
        source=source,
        source_roles=source_roles,
        note_prefix="rooted_color_4note",
        family_notes=(
            "rooted_color_4note_functional_source_family",
            *_four_note_color_permission_notes(chord, source, color_context),
            "rooted_color_4note_functional_content_type_root_third_seventh_altered_color",
            "rooted_color_4note_content_type_1_3_b7_X",
            "rooted_color_4note_altered_dominant_rooted_source",
            "rooted_color_4note_altered_dominant_source_1_3_b7_X",
            "altered_dominant_natural_5_omitted",
            f"rooted_color_4note_altered_color_x_{_degree_order_token((colors[0],))}",
            f"altered_dominant_functional_scope_{altered_decision.functional_scope.value}",
            f"altered_dominant_inferred_functional_scope_{altered_decision.inferred_functional_scope.value}",
            f"altered_dominant_authorization_reason_{altered_decision.reason}",
            f"altered_dominant_intensity_{altered_decision.intensity.value}",
            f"altered_dominant_source_weight_bias_rooted_color_{altered_dominant_source_weight_bias(policy, chord, 'rooted_color'):+.3f}",
            "voicing_source_roles_resolved_by_core_harmony",
        ),
    )




def _seventh_chord_source_integrity_required(chord: ParsedChord) -> bool:
    """Return whether expanded/color sources must preserve seventh identity.

    v2_2_54 global rule: once the chart symbol is a seventh-chord family
    (maj7/m7/7/m7b5/dim7 and their explicit extensions), color expansion must
    retain the defining guide-tone shell.  Triad/add/sixth paths may still use
    add9/6-9 sources such as 1359/1369, but seventh chords cannot be rewritten
    into add-chord material by omitting the seventh.
    """

    return bool(chord.has_seventh or chord.is_dominant or _is_half_diminished_like(chord))


def source_preserves_seventh_chord_identity(chord: ParsedChord | str, degree_names: tuple[str, ...] | list[str]) -> bool:
    """Return whether a source retains the original seventh-chord identity.

    This is a source-gate helper, not a new selector.  It is density- and
    disposition-agnostic so CLOSED, OPEN, SPREAD and future grouped voicings can
    all audit the same rule: a seventh-chord source must contain the resolved
    third and seventh/guide tones.
    """

    parsed = parse_chord(chord) if isinstance(chord, str) else chord
    if not _seventh_chord_source_integrity_required(parsed):
        return True
    names = set(str(degree) for degree in degree_names)
    third = third_degree_for_chord(parsed)
    seventh = seventh_degree_for_chord(parsed)
    if parsed.is_suspended:
        third_ok = bool({"4", "11", third} & names)
    else:
        third_ok = third in names
    seventh_ok = bool(seventh and seventh in names)
    if _is_half_diminished_like(parsed) or parsed.quality == "diminished":
        return bool(third_ok and seventh_ok and fifth_degree_for_chord(parsed) in names)
    return bool(third_ok and seventh_ok)


def seventh_chord_source_integrity_notes(chord: ParsedChord | str, degree_names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Return audit notes for the global seventh-chord expansion source gate."""

    parsed = parse_chord(chord) if isinstance(chord, str) else chord
    if not _seventh_chord_source_integrity_required(parsed):
        return ("seventh_chord_source_integrity_not_required_for_triad_or_add_chord",)
    if source_preserves_seventh_chord_identity(parsed, degree_names):
        notes = [
            "global_seventh_chord_expansion_source_integrity_gate_applied",
            "seventh_chord_expansion_preserves_3_and_7",
        ]
        if _is_half_diminished_like(parsed) or parsed.quality == "diminished":
            notes.append("seventh_chord_expansion_preserves_diminished_fifth_identity")
        return tuple(notes)
    return (
        "global_seventh_chord_expansion_source_integrity_gate_applied",
        "seventh_chord_expansion_source_rejected_missing_3_or_7",
    )


def _is_altered_dominant_for_rooted_color(chord: ParsedChord) -> bool:
    alterations = set(chord.alterations or ())
    return bool(chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in alterations or alterations & {"b9", "#9", "#11", "b13", "#5", "b5"}))


def _altered_dominant_authorized_for_policy(chord: ParsedChord, policy: VoicingPolicy) -> bool:
    decision = resolve_altered_dominant_policy(policy, chord)
    return bool(decision.authorized_for_chord)

def _rootless_ab_options(
    chord: ParsedChord,
    material: ChordMaterial,
    family: ContentFamily,
    policy: VoicingPolicy,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return 4-note rootless A/B recipes under the global color policy.

    V2_1_12 separates two axes that are easy to mix up:

    * A/B orientation: whether the guide-tone shell is in the 3rd-oriented
      family (A) or the 7th-oriented family (B).
    * rootless content type: whether the same A/B family is the safer
      ``with_5`` shape (3-5-7-9 / 7-9-3-5) or the richer ``with_13`` shape
      (3-13-7-9 / 7-9-3-13).

    The content type should stay consistent across one ii-V or V-I root motion.
    Selection/scoring handles that continuity using the metadata emitted here.
    """

    color_context = _color_permission_context(chord, material, policy, rootless=True)
    specified = set(color_context.explicit)
    expansion = color_context.expansion_enabled
    if not color_context.allowed and not expansion:
        return []

    third = third_degree_for_chord(chord)
    fifth = _fifth_degree_for_voicing(chord)
    seventh = seventh_degree_for_chord(chord)
    if not seventh:
        return []

    # Diminished seventh is a complete symmetric chord, not a rootless A/B
    # target.  It should be handled by the complete diminished family instead.
    if chord.quality == "diminished":
        return []

    altered_decision = resolve_altered_dominant_policy(policy, chord)
    altered_options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    if altered_decision.authorized_for_chord:
        # Altered dominant is a source-candidate pool, not a post-voicing note
        # rewrite.  Explicit altered chart symbols such as G7alt/G7b9b13 remain
        # chart fidelity and should not fall back to natural-5 rootless material.
        # Plain dominants authorized by the altered policy, however, must keep
        # ordinary 9/13 rootless sources in the same candidate pool so style
        # weighting can make altered color occasional instead of absolute.
        altered_options = _altered_dominant_rootless_ab_options(
            chord=chord,
            material=material,
            family=family,
            third=third,
            seventh=seventh,
            specified=specified,
            expansion=expansion,
            color_context=color_context,
            policy=policy,
        )
        if altered_decision.explicit_chord_symbol_altered:
            return altered_options

    if _explicit_other_color_should_take_priority(chord, specified) and not expansion:
        return _rootless_ab_explicit_only_options(chord, family, third, fifth, seventh, specified, color_context=color_context)

    if specified and not expansion:
        return _rootless_ab_explicit_only_options(chord, family, third, fifth, seventh, specified, color_context=color_context)

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    if specified and expansion and _explicit_other_color_should_take_priority(chord, specified):
        # Explicit chart colors keep a visible candidate path even when expansion
        # also opens broader 9/13 sources.  The chart-fidelity scorer will favor
        # these when they contain the written color.
        options.extend(_rootless_ab_explicit_only_options(chord, family, third, fifth, seventh, specified, color_context=color_context))

    options.extend(_generic_scale_spelled_rootless_ab_options(
        chord=chord,
        family=family,
        policy=policy,
        third=third,
        fifth=fifth,
        seventh=seventh,
        specified=specified,
        color_context=color_context,
    ))
    if altered_options:
        options.extend(altered_options)
    return options


def _generic_scale_spelled_rootless_ab_options(
    *,
    chord: ParsedChord,
    family: ContentFamily,
    policy: VoicingPolicy,
    third: str,
    fifth: str,
    seventh: str,
    specified: set[str],
    color_context: ColorPermissionContext,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return generic 4-note rootless A/B sources with mode-correct spelling.

    The active source families stay abstract and universal:

    - ``with_5`` = third + fifth + seventh + scale-spelled ninth
    - ``with_13`` = third + scale-spelled thirteenth + seventh + scale-spelled ninth

    Half-diminished is not a separate rootless source family. It reaches
    ``b3-b5-b7-b9`` and ``b3-b13-b7-b9`` because the common Harmony/Scale layer
    spells the same generic slots under Locrian as ``5 -> b5``, ``9 -> b9``,
    and ``13 -> b13``.
    """

    with_5_roles = ("third", "fifth", "seventh", "ninth")
    with_5_b_roles = ("seventh", "ninth", "third", "fifth")
    with_13_roles = ("third", "thirteenth", "seventh", "ninth")
    with_13_b_roles = ("seventh", "ninth", "third", "thirteenth")
    with_5_source = _resolve_source_roles(chord, with_5_roles)
    with_5_b_source = _resolve_source_roles(chord, with_5_b_roles)
    with_13_source = _resolve_source_roles(chord, with_13_roles)
    with_13_b_source = _resolve_source_roles(chord, with_13_b_roles)
    ninth = with_5_source[-1]
    thirteenth = with_13_source[1]
    context_notes = _generic_rootless_context_notes(chord, ninth=ninth, thirteenth=thirteenth)

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    with_5_permission = _four_note_color_permission_notes(chord, with_5_source, color_context)
    if "four_note_color_permission_blocked_unallowed_color" not in with_5_permission:
        options.extend(
            _rootless_ab_orientations(
                family=family,
                low_first=with_5_source,
                high_first=with_5_b_source,
                low_roles=with_5_roles,
                high_roles=with_5_b_roles,
                notes=(*context_notes, *with_5_permission, "rootless_ab_content_type_with_5", "rootless_ab_functional_source_type_third_fifth_seventh_ninth"),
            )
        )
    if _minor_13_allowed_for_rootless_ab(chord, policy, specified):
        with_13_permission = _four_note_color_permission_notes(chord, with_13_source, color_context)
        if "four_note_color_permission_blocked_unallowed_color" not in with_13_permission:
            options.extend(
                _rootless_ab_orientations(
                    family=family,
                    low_first=with_13_source,
                    high_first=with_13_b_source,
                    low_roles=with_13_roles,
                    high_roles=with_13_b_roles,
                    notes=(*context_notes, *with_13_permission, "rootless_ab_content_type_with_13", "rootless_ab_functional_source_type_third_thirteenth_seventh_ninth", _minor_13_context_note(chord, policy, specified)),
                )
            )
    return options


def _generic_rootless_context_notes(chord: ParsedChord, *, ninth: str, thirteenth: str) -> tuple[str, ...]:
    if chord.quality == "minor":
        base = ["rootless_ab_expansion_minor_safe_color"]
    elif chord.has_major_seventh:
        base = ["rootless_ab_expansion_major_safe_color"]
    elif chord.is_dominant:
        base = ["rootless_ab_expansion_dominant_safe_color"]
    else:
        base = ["rootless_ab_expansion_safe_color"]
    base.extend([
        "rootless_ab_generic_functional_source",
        "rootless_ab_generic_scale_spelled_source",
        "voicing_source_roles_resolved_by_core_harmony",
        f"rootless_ab_resolved_ninth_{_degree_order_token((ninth,))}",
        f"rootless_ab_resolved_thirteenth_{_degree_order_token((thirteenth,))}",
        f"rootless_ab_scale_ninth_{_degree_order_token((ninth,))}",
        f"rootless_ab_scale_thirteenth_{_degree_order_token((thirteenth,))}",
    ])
    if _is_half_diminished_like(chord):
        base.append("half_diminished_uses_generic_rootless_sources_via_harmony_resolution")
    return tuple(base)


def _is_altered_dominant_for_rootless_ab(chord: ParsedChord) -> bool:
    alterations = set(chord.alterations or ())
    return bool(chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in alterations or alterations & {"b9", "#9", "#11", "b13", "#5", "b5"}))


def _altered_dominant_rootless_ab_options(
    *,
    chord: ParsedChord,
    material: ChordMaterial,
    family: ContentFamily,
    third: str,
    seventh: str,
    specified: set[str],
    expansion: bool,
    color_context: ColorPermissionContext,
    policy: VoicingPolicy | None = None,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return the no-root altered dominant source ``3-b7-X-Y``.

    This is distinct from rooted altered dominant ``1-3-b7-X`` and from the
    ordinary rootless ``with_5`` source.  It prevents symbols such as ``G7alt``
    and explicitly altered dominants with two altered colors from falling back
    to ``3-5-b7-9`` with a natural fifth.
    """

    colors = _ordered_altered_dominant_colors(chord, material, specified=specified, expansion=expansion)
    if len(colors) < 2:
        return []
    x, y = colors[:2]
    return _rootless_ab_orientations(
        family=family,
        low_first=(third, seventh, x, y),
        high_first=(seventh, x, third, y),
        low_roles=("third", "seventh", "altered_color_a", "altered_color_b"),
        high_roles=("seventh", "altered_color_a", "third", "altered_color_b"),
        notes=(
            *_four_note_color_permission_notes(chord, (third, seventh, x, y), color_context),
            f"altered_dominant_functional_scope_{resolve_altered_dominant_policy(policy, chord).functional_scope.value}",
            f"altered_dominant_inferred_functional_scope_{resolve_altered_dominant_policy(policy, chord).inferred_functional_scope.value}",
            f"altered_dominant_authorization_reason_{resolve_altered_dominant_policy(policy, chord).reason}",
            f"altered_dominant_intensity_{resolve_altered_dominant_policy(policy, chord).intensity.value}",
            f"altered_dominant_source_weight_bias_rootless_ab_{altered_dominant_source_weight_bias(policy, chord, 'rootless_ab'):+.3f}",
            "rootless_ab_altered_dominant_rootless_source",
            "rootless_ab_altered_dominant_source_3_b7_x_y",
            "rootless_ab_content_type_altered_dominant_rootless",
            "altered_dominant_natural_5_omitted",
            f"rootless_ab_altered_color_x_{_degree_order_token((x,))}",
            f"rootless_ab_altered_color_y_{_degree_order_token((y,))}",
        ),
    )


def _ordered_altered_dominant_colors(
    chord: ParsedChord,
    material: ChordMaterial,
    *,
    specified: set[str],
    expansion: bool,
) -> list[str]:
    explicit = _ordered_explicit_colors(chord, explicit=specified)
    explicit_altered = [degree for degree in explicit if degree in {"b9", "#9", "#11", "b13", "#5", "b5"}]
    if "alt" in set(chord.alterations or ()) or "alt" in chord.symbol.lower():
        # G7alt is itself an explicit altered-dominant color request. Use a
        # compact altered pair by default instead of adding a natural 5.
        return _dedupe([*explicit_altered, "b9", "#9", "b13", "#11"])
    if len(explicit_altered) >= 2:
        return explicit_altered
    if expansion:
        available_altered = [degree for degree in material.available_tensions if degree in {"b9", "#9", "#11", "b13", "#5", "b5"}]
        return _dedupe([*explicit_altered, *available_altered, "b9", "#9", "b13", "#11"])
    return explicit_altered


def _explicit_other_color_should_take_priority(chord: ParsedChord, specified: set[str]) -> bool:
    # Explicit non-9/non-13 chart colors such as m11b5 should not be ignored just
    # because a broader rootless tuning preset also enables expansion. This is a
    # generic chord-symbol priority rule, not a separate half-diminished source.
    return bool(specified and not ({"9", "b9", "13", "b13"} & specified))


def _minor_13_allowed_for_rootless_ab(chord: ParsedChord, policy: VoicingPolicy, specified: set[str]) -> bool:
    """Return whether an m7 rootless A/B may use the 13-shape.

    Minor 13 is a strong Dorian / modal-minor color.  It should not be the
    default outcome of merely enabling safe extensions.  Non-minor qualities may
    still use the with_13 rootless A/B family; minor chords need either explicit
    chart notation (Dm13 / Dm7(13)) or a policy/LLM modal-context marker.
    """

    if chord.quality != "minor":
        return True
    if "13" in specified:
        return True
    metadata = dict(getattr(policy, "metadata", {}) or {})
    explicit_flags = {
        "rootless_ab_minor_13_allowed",
        "allow_minor_13",
        "dorian_minor_13_allowed",
    }
    if any(bool(metadata.get(flag)) for flag in explicit_flags):
        return True

    textual_markers = {
        str(metadata.get("scale_mode", "")).lower(),
        str(metadata.get("minor_mode", "")).lower(),
        str(metadata.get("modal_context", "")).lower(),
        str(metadata.get("harmony_context", "")).lower(),
    }
    if textual_markers & {"dorian", "modal", "modal_minor", "modal-minor", "dorian_minor", "dorian-minor"}:
        return True

    # Rich reharm still does not automatically imply Dorian minor. The LLM or
    # arrangement layer should say so explicitly via metadata.
    return False


def _minor_13_context_note(chord: ParsedChord, policy: VoicingPolicy, specified: set[str]) -> str:
    if chord.quality != "minor":
        return "rootless_ab_with_13_non_minor"
    if "13" in specified:
        return "rootless_ab_minor_13_explicit_symbol"
    return "rootless_ab_minor_13_dorian_modal_context"



def _rootless_ab_explicit_eleventh_options(
    *,
    chord: ParsedChord,
    family: ContentFamily,
    third: str,
    fifth: str,
    seventh: str,
    color_context: ColorPermissionContext,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return explicit eleventh / sharp-eleventh rootless source options.

    Eleventh is a generic functional role.  Cmaj7#11 resolves the role to
    ``#11`` in Harmony, while Dm11 and Cm11 resolve to natural ``11``.  Ninth is
    only used in the rootless 3-7-9-11 source when the chart or expansion policy
    has actually allowed that ninth; otherwise the compact 3-5-7-11 source keeps
    the explicit 11 without sneaking in an unnotated 9.
    """

    resolved_eleventh = resolve_functional_degree_role(chord, "eleventh")
    resolved_ninth = resolve_functional_degree_role(chord, "ninth")
    if _is_half_diminished_like(chord):
        compact_source = (third, resolved_eleventh, fifth, seventh)
        compact_high = (seventh, third, resolved_eleventh, fifth)
        compact_low_roles = ("third", "eleventh", "fifth", "seventh")
        compact_high_roles = ("seventh", "third", "eleventh", "fifth")
        compact_functional_type = "rootless_ab_functional_source_type_third_eleventh_fifth_seventh"
        compact_extra_notes = ("rootless_ab_half_diminished_explicit_11_compact",)
    else:
        compact_source = (third, fifth, seventh, resolved_eleventh)
        compact_high = (seventh, resolved_eleventh, third, fifth)
        compact_low_roles = ("third", "fifth", "seventh", "eleventh")
        compact_high_roles = ("seventh", "eleventh", "third", "fifth")
        compact_functional_type = "rootless_ab_functional_source_type_third_fifth_seventh_eleventh"
        compact_extra_notes = ()

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    if _ninth_allowed_by_color_context(chord, color_context):
        source = (third, seventh, resolved_ninth, resolved_eleventh)
        notes = (
            *_four_note_color_permission_notes(chord, source, color_context),
            "rootless_ab_explicit_chord_symbol_color_used",
            "rootless_ab_explicit_eleventh_source_family",
            "rootless_ab_content_type_explicit_eleventh",
            "rootless_ab_functional_source_type_third_seventh_ninth_eleventh",
            *_explicit_eleventh_context_notes(chord, resolved_eleventh),
            f"rootless_ab_resolved_eleventh_{_degree_order_token((resolved_eleventh,))}",
            f"rootless_ab_resolved_ninth_{_degree_order_token((resolved_ninth,))}",
        )
        if "four_note_color_permission_blocked_unallowed_color" not in notes:
            options.extend(_rootless_ab_orientations(
                family=family,
                low_first=source,
                high_first=(seventh, resolved_ninth, third, resolved_eleventh),
                low_roles=("third", "seventh", "ninth", "eleventh"),
                high_roles=("seventh", "ninth", "third", "eleventh"),
                notes=notes,
            ))

    permission_notes = _four_note_color_permission_notes(chord, compact_source, color_context)
    base_notes = (
        "rootless_ab_explicit_chord_symbol_color_used",
        "rootless_ab_explicit_eleventh_source_family",
        "rootless_ab_content_type_explicit_eleventh",
        compact_functional_type,
        *compact_extra_notes,
        *_explicit_eleventh_context_notes(chord, resolved_eleventh),
        f"rootless_ab_resolved_eleventh_{_degree_order_token((resolved_eleventh,))}",
    )
    if "four_note_color_permission_blocked_unallowed_color" not in permission_notes:
        options.extend(_rootless_ab_orientations(
            family=family,
            low_first=compact_source,
            high_first=compact_high,
            low_roles=compact_low_roles,
            high_roles=compact_high_roles,
            notes=(*permission_notes, *base_notes),
        ))
    return options

def _rootless_ab_explicit_only_options(
    chord: ParsedChord,
    family: ContentFamily,
    third: str,
    fifth: str,
    seventh: str,
    specified: set[str],
    color_context: ColorPermissionContext,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return rootless A/B options when chart color, not expansion, opens the gate.

    In this mode the voicing may use colors that the chord symbol already wrote,
    but must not sneak in extra unnotated tensions.  Cmaj9 therefore allows the
    with_5 family because it contains 9; G13 allows the with_13 family but keeps
    the non-specified extra color conservative by using 5 when 9 is not explicit.
    """

    explicit_colors = _ordered_explicit_colors(chord, explicit=specified)
    if _explicit_eleventh_requested(specified):
        eleventh_options = _rootless_ab_explicit_eleventh_options(
            chord=chord,
            family=family,
            third=third,
            fifth=fifth,
            seventh=seventh,
            color_context=color_context,
        )
        if eleventh_options:
            return eleventh_options

    altered_colors = [degree for degree in explicit_colors if degree in {"b9", "#9", "#11", "b13", "#5", "b5"}]
    if chord.is_dominant and len(altered_colors) >= 2:
        color = altered_colors[0]
        second_color = altered_colors[1]
        return _rootless_ab_orientations(
            family=family,
            low_first=(third, seventh, color, second_color),
            high_first=(seventh, color, third, second_color),
            low_roles=("third", "seventh", "altered_color_a", "altered_color_b"),
            high_roles=("seventh", "altered_color_a", "third", "altered_color_b"),
            notes=(
                *_four_note_color_permission_notes(chord, (third, seventh, color, second_color), color_context),
                "rootless_ab_explicit_altered_dominant_colors_used",
                "rootless_ab_altered_dominant_rootless_source",
                "rootless_ab_content_type_altered_dominant_rootless",
                "rootless_ab_functional_source_type_third_seventh_altered_color_a_altered_color_b",
                "altered_dominant_natural_5_omitted",
            ),
        )

    options: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    if "9" in specified:
        options.extend(
            _rootless_ab_orientations(
                family=family,
                low_first=(third, fifth, seventh, "9"),
                high_first=(seventh, "9", third, fifth),
                low_roles=("third", "fifth", "seventh", "ninth"),
                high_roles=("seventh", "ninth", "third", "fifth"),
                notes=(
                    *_four_note_color_permission_notes(chord, (third, fifth, seventh, "9"), color_context),
                    "rootless_ab_explicit_chord_symbol_color_used",
                    "rootless_ab_content_type_with_5",
                    "rootless_ab_functional_source_type_third_fifth_seventh_ninth",
                ),
            )
        )
    if "13" in specified:
        # If 9 is also explicit, use the full with_13 shape requested in the
        # tuning rule.  If only 13 is explicit, keep 5 as the fourth tone so the
        # explicit-color gate does not add an unnotated 9.
        upper_color = "9" if "9" in specified else fifth
        upper_role = "ninth" if upper_color == "9" else "fifth"
        functional_type = "third_thirteenth_seventh_ninth" if upper_role == "ninth" else "third_thirteenth_seventh_fifth"
        options.extend(
            _rootless_ab_orientations(
                family=family,
                low_first=(third, "13", seventh, upper_color),
                high_first=(seventh, upper_color, third, "13"),
                low_roles=("third", "thirteenth", "seventh", upper_role),
                high_roles=("seventh", upper_role, "third", "thirteenth"),
                notes=(
                    *_four_note_color_permission_notes(chord, (third, "13", seventh, upper_color), color_context),
                    "rootless_ab_explicit_chord_symbol_color_used",
                    "rootless_ab_content_type_with_13",
                    f"rootless_ab_functional_source_type_{functional_type}",
                ),
            )
        )
    if options:
        return options

    color = explicit_colors[0] if explicit_colors else "9"
    return _rootless_ab_orientations(
        family=family,
        low_first=(third, fifth, seventh, color),
        high_first=(seventh, color, third, fifth),
        low_roles=("third", "fifth", "seventh", "explicit_color"),
        high_roles=("seventh", "explicit_color", "third", "fifth"),
        notes=(
            *_four_note_color_permission_notes(chord, (third, fifth, seventh, color), color_context),
            "rootless_ab_explicit_chord_symbol_color_used",
            "rootless_ab_content_type_explicit_other",
            "rootless_ab_functional_source_type_third_fifth_seventh_explicit_color",
        ),
    )


def _rootless_ab_orientations(
    *,
    family: ContentFamily,
    low_first: tuple[str, ...],
    high_first: tuple[str, ...],
    notes: tuple[str, ...],
    low_roles: tuple[str, ...] | None = None,
    high_roles: tuple[str, ...] | None = None,
) -> list[tuple[list[tuple[str, int]], tuple[str, ...]]]:
    """Return the requested A/B family as source-derived inversion candidates.

    V2_1_15 upgrades rootless A/B from one hand-written voicing per family to a
    canonical-source inversion family.  For with_5, A starts from ``3-5-7-9``
    and its rotations are ``5-7-9-3``, ``7-9-3-5``, ``9-3-5-7``.  B starts
    from the paired source ``7-9-3-5`` and its rotations are ``9-3-5-7``,
    ``3-5-7-9``, ``5-7-9-3``.  with_13 follows the same rule with
    ``3-13-7-9`` and ``7-9-3-13``.  The scorer then prefers AB/BAB movement
    by keeping the same inversion index while flipping A/B across ii-V or V-I.
    """

    source = low_first if family == ContentFamily.ROOTLESS_A else high_first
    source_roles = low_roles if family == ContentFamily.ROOTLESS_A else high_roles
    orientation = "rootless_ab_orientation_A" if family == ContentFamily.ROOTLESS_A else "rootless_ab_orientation_B"
    orientation_family = "A" if family == ContentFamily.ROOTLESS_A else "B"
    role_rotations = _rotations(source_roles) if source_roles else []
    out: list[tuple[list[tuple[str, int]], tuple[str, ...]]] = []
    for inversion_index, rotated in enumerate(_rotations(source)):
        rotated_roles = role_rotations[inversion_index] if role_rotations else ()
        role_notes = ()
        if source_roles:
            role_notes = (
                f"rootless_ab_source_role_order_{_role_order_token(source_roles)}",
                f"rootless_ab_degree_role_order_{_role_order_token(rotated_roles)}",
            )
        variant_notes = (
            *notes,
            *role_notes,
            orientation,
            f"rootless_ab_inversion_index_{inversion_index}",
            f"rootless_ab_source_order_{_degree_order_token(source)}",
            f"rootless_ab_degree_order_{_degree_order_token(rotated)}",
            "rootless_ab_orientation_from_canonical_inversion_family",
            f"rootless_ab_ab_pair_key_{orientation_family}{inversion_index}",
        )
        out.append(([_degree_pair(degree) for degree in _dedupe(list(rotated))], variant_notes))
    return out


def _first_color(colors: list[str], fallback: str) -> str:
    return colors[0] if colors else fallback


def trim_content_degrees(degrees: list[tuple[str, int]], policy: VoicingPolicy) -> list[tuple[str, int]]:
    """Apply the legacy density limit while preserving required root support."""

    if not degrees:
        return []
    min_density, preferred_density, max_density_limit = policy.effective_density_range
    max_density = max(min_density, min(preferred_density, max_density_limit, len(degrees)))
    trimmed = degrees[:max_density]
    if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED} and all(degree != "R" for degree, _ in trimmed):
        root = next((item for item in degrees if item[0] == "R"), ("R", 0))
        trimmed = [root, *trimmed]
    return trimmed[: policy.max_density]


def content_validity_notes(chord: ParsedChord, family: ContentFamily, degree_names: tuple[str, ...], policy: VoicingPolicy | None = None) -> tuple[str, ...]:
    notes: list[str] = []
    if family in TRIAD_FAMILIES:
        notes.append("chord_quality_matched_triad_family")
    if _is_half_diminished_like(chord) and "b5" in degree_names:
        notes.append("half_diminished_b5_retained")
    if family == ContentFamily.SHELL_PLUS_COLOR:
        notes.append("shell_plus_specified_color_policy")
        explicit = _explicit_symbol_color_degrees(chord)
        if _is_half_diminished_like(chord) and "b5" in degree_names:
            notes.append("half_diminished_uses_b3_b7_b5")
        elif chord.quality == "diminished" and {"b3", "b5"}.issubset(set(degree_names)):
            notes.append("diminished_internal_identity_tones")
        elif any(degree in explicit for degree in degree_names):
            notes.append("explicit_chord_symbol_color_used")
        elif not harmonic_expansion_allowed(policy, chord):
            notes.append("no_unspecified_color_added")
        else:
            notes.append("harmonic_expansion_color_used")
    if family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}:
        notes.append("global_harmonic_expansion_policy_applied")
        notes.append("rootless_ab_color_comping_policy")
        explicit = _rootless_ab_explicit_color_degrees(chord)
        if explicit and any(degree in explicit for degree in degree_names):
            notes.append("rootless_ab_explicit_chord_symbol_color_used")
        elif harmonic_expansion_allowed(policy, chord):
            notes.append("rootless_ab_harmonic_expansion_enabled")
        else:
            notes.append("rootless_ab_gate_closed")
    notes.extend(seventh_chord_source_integrity_notes(chord, degree_names))
    if chord.quality == "diminished" and "b5" in degree_names:
        notes.append("diminished_b5_retained")
    if chord.is_dominant and ("alt" in chord.symbol.lower() or "alt" in chord.alterations) and "5" not in degree_names:
        notes.append("altered_dominant_natural_5_omitted")
    if not (chord.has_seventh or chord.has_sixth) and family not in ROOTLESS_FAMILIES:
        notes.append("plain_triad_uses_rooted_or_triad_family")
    return tuple(_dedupe(notes))


def _dedupe(values: list[ContentFamily] | list[str]) -> list:
    seen: set = set()
    out: list = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out

# Backward-compatible internal aliases for legacy tests/imports.
_content_degree_options = content_degree_options
_content_validity_notes = content_validity_notes
