from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jammate_engine.core.harmony.chord_parser import ParsedChord, parse_chord
from jammate_engine.core.harmony.material import degree_to_semitone
from jammate_engine.core.voicing.policy import (
    ALTERED_DOMINANT_POLICY_VERSION,
    AlteredDominantIntensity,
    ColorPolicyMode,
    altered_dominant_source_weight_bias,
    resolve_altered_dominant_policy,
)


UPPER_STRUCTURE_SOURCE_VERSION = "v2_2_88"
UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION = "v2_6_21"

UPPER_STRUCTURE_OWNED_RESPONSIBILITIES: tuple[str, ...] = (
    "source_level_upper_structure_degree_recipes",
    "upper_structure_density_gate_3_or_4",
    "upper_structure_policy_entry_gate",
    "dominant_safe_and_altered_source_recipe_catalog",
    "maj7_minor7_safe_source_recipe_catalog",
    "source_metadata_for_downstream_projection_reuse",
)

UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "does_not_project_closed_or_open_or_spread_voicings",
    "does_not_choose_register_or_octave_placement",
    "does_not_score_or_select_candidates",
    "does_not_rank_voice_leading",
    "does_not_adapt_runtime_spread_candidates",
    "does_not_write_midi_or_touch_expression",
)

_ALTERED_DEGREES = {"b9", "#9", "#11", "b13", "#5", "b5"}


@dataclass(frozen=True)
class UpperStructureBoundaryProfile:
    """Auditable boundary metadata for Upper Structure source planning.

    The profile is intentionally descriptive only. It must not contain concrete
    MIDI notes, projection decisions, register placement, or selector scores.
    """

    version: str
    owned_responsibilities: tuple[str, ...]
    forbidden_responsibilities: tuple[str, ...]
    source_only: bool = True
    reuses_existing_projection_layers: bool = True
    allowed_densities: tuple[int, ...] = (3, 4)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "upper_structure_boundary_audit_version": self.version,
            "owned_responsibilities": list(self.owned_responsibilities),
            "forbidden_responsibilities": list(self.forbidden_responsibilities),
            "source_only": bool(self.source_only),
            "reuses_existing_projection_layers": bool(self.reuses_existing_projection_layers),
            "allowed_densities": list(self.allowed_densities),
        }


def upper_structure_boundary_profile() -> UpperStructureBoundaryProfile:
    """Return the static v2_6_21 Upper Structure responsibility profile."""

    return UpperStructureBoundaryProfile(
        version=UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION,
        owned_responsibilities=UPPER_STRUCTURE_OWNED_RESPONSIBILITIES,
        forbidden_responsibilities=UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES,
    )


@dataclass(frozen=True)
class UpperStructureSource:
    """A source-level upper-structure recipe before disposition/projection.

    This object deliberately owns only pitch content. It does not decide closed
    inversions, DROP projection, register, or voice-leading; those are reused
    from core voicing disposition/selection layers.
    """

    symbol: str
    source_id: str
    density: int
    degrees: tuple[tuple[str, int], ...]
    chord_quality_gate: str
    structure_kind: str
    tension_profile: str
    source_notes: tuple[str, ...]

    @property
    def degree_names(self) -> tuple[str, ...]:
        return tuple(degree for degree, _ in self.degrees)

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "upper_structure_source_version": UPPER_STRUCTURE_SOURCE_VERSION,
            "altered_dominant_policy_version": ALTERED_DOMINANT_POLICY_VERSION,
            "symbol": self.symbol,
            "source_id": self.source_id,
            "density": int(self.density),
            "degree_names": list(self.degree_names),
            "degrees": [[degree, int(semitone)] for degree, semitone in self.degrees],
            "chord_quality_gate": self.chord_quality_gate,
            "structure_kind": self.structure_kind,
            "tension_profile": self.tension_profile,
            "source_notes": list(self.source_notes),
            "upper_structure_boundary_audit_version": UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION,
            "source_only_no_projection": True,
            "reuse_existing_closed_inversion_drop_projection": True,
            "forbidden_responsibilities": list(UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES),
        }


def plan_upper_structure_sources(
    symbol: str,
    *,
    density: int,
    policy: Any | None = None,
) -> tuple[UpperStructureSource, ...]:
    """Return policy-gated upper-structure sources for a chord.

    Upper Structure is a voicing source family, not a projection system. It may
    only add unnotated color when harmonic expansion is enabled. Altered
    dominant sources are a second gate: they require either an explicitly
    altered dominant chord symbol or an enabled AlteredDominantPolicy together
    with harmonic expansion. 3-note sources reuse existing closed/inversion
    placement; 4-note sources reuse existing closed/inversion/DROP2/DROP3.
    """

    if int(density) not in {3, 4}:
        return ()
    if not _upper_structure_entry_enabled(policy):
        return ()

    chord = parse_chord(symbol)
    if _is_halfdim_or_dim(chord):
        return ()

    expansion_enabled = _policy_harmonic_expansion_enabled(policy, _policy_metadata(policy))
    explicit_altered = _dominant_has_explicit_altered_color(chord)
    explicit_color = _chord_symbol_has_color(chord)
    altered_decision = resolve_altered_dominant_policy(policy, chord)
    altered_enabled = bool(altered_decision.enabled)
    altered_authorized = bool(altered_decision.authorized_for_chord)
    altered_intensity_bias = altered_dominant_source_weight_bias(policy, chord, "upper_structure")

    # In chord-symbol-only mode, Upper Structure must not introduce new color.
    # Explicitly written color may be honored, but only if it actually matches
    # the requested US pool. Plain G7 / Cmaj7 do not get US without expansion.
    if not expansion_enabled and not explicit_color:
        return ()

    if chord.is_dominant:
        specs = _dominant_specs(
            int(density),
            altered_authorized=altered_authorized,
            explicit_altered=explicit_altered,
            intensity=altered_decision.intensity,
        )
        gate = "dominant_altered" if altered_authorized else "dominant_safe"
    elif chord.has_seventh and chord.quality in {"major", "minor"}:
        if chord.quality == "major":
            specs = _maj7_specs(int(density), policy)
            gate = "maj7_safe"
        else:
            if not bool(_policy_metadata(policy).get("spread_upper_structure_allow_minor7", False)):
                return ()
            specs = _minor7_specs(int(density))
            gate = "minor7_safe"
    else:
        return ()

    out: list[UpperStructureSource] = []
    for source_id, degrees, profile in specs:
        degree_pairs = tuple((degree, degree_to_semitone(degree)) for degree in degrees)
        profile_kind = "altered" if "altered" in profile else "safe"
        out.append(
            UpperStructureSource(
                symbol=chord.symbol,
                source_id=source_id,
                density=int(density),
                degrees=degree_pairs,
                chord_quality_gate=gate,
                structure_kind="upper_structure_triad" if int(density) == 3 else "upper_structure_4note",
                tension_profile=profile,
                source_notes=(
                    "upper_structure_source_family",
                    "upper_structure_policy_gate_v2_2_84",
                    f"upper_structure_boundary_audit_version_{UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION}",
                    f"upper_structure_density_{int(density)}",
                    f"upper_structure_quality_gate_{gate}",
                    f"upper_structure_source_id_{source_id}",
                    f"upper_structure_tension_profile_{profile}",
                    f"upper_structure_profile_kind_{profile_kind}",
                    f"upper_structure_harmonic_expansion_enabled_{str(expansion_enabled).lower()}",
                    f"upper_structure_altered_dominant_enabled_{str(altered_enabled).lower()}",
                    f"upper_structure_altered_dominant_authorized_{str(altered_authorized).lower()}",
                    f"altered_dominant_intensity_{altered_decision.intensity.value}",
                    f"altered_dominant_functional_scope_{altered_decision.functional_scope.value}",
                    f"altered_dominant_inferred_functional_scope_{altered_decision.inferred_functional_scope.value}",
                    f"altered_dominant_authorization_reason_{altered_decision.reason}",
                    f"upper_structure_altered_dominant_intensity_bias_{altered_intensity_bias:+.3f}",
                    "source_only_reuses_existing_projection",
                    "three_note_reuses_closed_inversion" if int(density) == 3 else "four_note_reuses_closed_inversion_drop2_drop3",
                ),
            )
        )
    return tuple(out)


def _upper_structure_entry_enabled(policy: Any | None) -> bool:
    metadata = _policy_metadata(policy)
    if metadata.get("spread_upper_structure_force_enabled") is True:
        return True
    if metadata.get("spread_upper_structure_enabled") is False:
        return False
    if metadata.get("spread_upper_structure_enabled") is True:
        return True
    nested = metadata.get("upper_structure")
    return bool(isinstance(nested, dict) and nested.get("enabled") is True)


def _policy_harmonic_expansion_enabled(policy: Any | None, metadata: dict[str, object]) -> bool:
    if bool(metadata.get("harmonic_expansion_enabled", False)):
        return True
    if bool(getattr(policy, "harmonic_expansion_enabled", False)):
        return True
    mode = metadata.get("color_policy_mode") or getattr(getattr(policy, "color_policy_mode", None), "value", None)
    if mode is None:
        return False
    try:
        return ColorPolicyMode(str(mode)) in {
            ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
            ColorPolicyMode.ALTERED_DOMINANT,
            ColorPolicyMode.RICH_REHARM_COLOR,
        }
    except ValueError:
        return str(mode) not in {"", "chord_symbol_only", "None"}


def _altered_dominant_enabled(policy: Any | None) -> bool:
    metadata = _policy_metadata(policy)
    nested = metadata.get("altered_dominant_policy") or metadata.get("altered_dominant") or {}
    if isinstance(nested, dict):
        if nested.get("enabled") is not None:
            return bool(nested.get("enabled"))
        if str(nested.get("intensity") or "off") not in {"", "off", "false", "none"}:
            return True
    if metadata.get("altered_dominant_enabled") is not None:
        return bool(metadata.get("altered_dominant_enabled"))
    mode = metadata.get("color_policy_mode") or getattr(getattr(policy, "color_policy_mode", None), "value", None)
    return str(mode) == ColorPolicyMode.ALTERED_DOMINANT.value


def _policy_metadata(policy: Any | None) -> dict[str, object]:
    try:
        return dict(getattr(policy, "metadata", None) or {})
    except Exception:
        return dict(policy or {}) if isinstance(policy, dict) else {}


def _is_halfdim_or_dim(chord: ParsedChord) -> bool:
    return bool(chord.is_half_diminished or chord.is_fully_diminished or chord.quality == "diminished")


def _chord_symbol_has_color(chord: ParsedChord) -> bool:
    return bool(chord.extensions or chord.alterations or "alt" in chord.symbol.lower())


def _dominant_has_explicit_altered_color(chord: ParsedChord) -> bool:
    if not chord.is_dominant:
        return False
    lower = chord.symbol.lower()
    alterations = set(chord.alterations or ())
    return bool("alt" in lower or "alt" in alterations or alterations & _ALTERED_DEGREES)


def _degrees_are_altered(degrees: tuple[str, ...]) -> bool:
    return bool(set(degrees) & _ALTERED_DEGREES)


def _dominant_specs(
    density: int,
    *,
    altered_authorized: bool,
    explicit_altered: bool,
    intensity: AlteredDominantIntensity,
) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    safe3 = (
        ("dom_US_II_major", ("9", "#11", "13"), "lydian_dominant_safe"),
    )
    safe4 = (
        ("dom_US_II6", ("3", "9", "#11", "13"), "lydian_dominant_safe_4note"),
    )
    altered3 = (
        ("dom_US_bII_major", ("b9", "#11", "b13"), "altered_tense"),
        ("dom_US_VI_major", ("13", "b9", "3"), "altered_color_with_guide"),
        ("dom_US_bVI_major", ("b13", "R", "#9"), "altered_color_with_root_color"),
    )
    altered4 = (
        ("dom_US_alt_shell_color", ("3", "b7", "b9", "b13"), "altered_shell_color_4note"),
        ("dom_US_alt_3_b7_sharp9_b13", ("3", "b7", "#9", "b13"), "altered_shell_color_4note"),
    )
    safe = safe3 if density == 3 else safe4
    altered = altered3 if density == 3 else altered4
    if not altered_authorized:
        return safe
    if explicit_altered or intensity == AlteredDominantIntensity.FULL:
        return altered
    if intensity == AlteredDominantIntensity.LIGHT:
        # Keep US altered as an available low-priority source, not a total switch.
        return (*safe, altered[0])
    if intensity == AlteredDominantIntensity.MEDIUM:
        return (*safe, *altered[:2])
    if intensity == AlteredDominantIntensity.HIGH:
        return (*altered, *safe)
    return safe


def _maj7_specs(density: int, policy: Any | None) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    metadata = _policy_metadata(policy)
    allow_lydian = bool(metadata.get("spread_upper_structure_allow_maj7_lydian", True))
    if density == 3:
        specs: list[tuple[str, tuple[str, ...], str]] = [
            ("maj7_US_V_major", ("5", "7", "9"), "stable_major_color"),
        ]
        if allow_lydian:
            specs.append(("maj7_US_II_major", ("9", "#11", "13"), "lydian_major_color"))
        return tuple(specs)
    specs4: list[tuple[str, tuple[str, ...], str]] = [
        ("maj7_US_V_add6", ("5", "7", "9", "13"), "stable_major_color_4note"),
    ]
    if allow_lydian:
        specs4.append(("maj7_US_II6", ("7", "9", "#11", "13"), "lydian_major_color_4note"))
    return tuple(specs4)


def _minor7_specs(density: int) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    # Keep minor upper structures conservative.
    if density == 3:
        return (
            ("min7_US_V_minor", ("5", "b7", "9"), "stable_minor_color"),
            ("min7_US_IV_major", ("11", "13", "R"), "minor_sus_color"),
        )
    return (
        ("min7_US_Vm_add11", ("5", "b7", "9", "11"), "stable_minor_color_4note"),
    )
