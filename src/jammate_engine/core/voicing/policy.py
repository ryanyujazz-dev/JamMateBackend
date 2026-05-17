from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from jammate_engine.core.roles import EnsembleContext

from .disposition import Disposition


class ContentFamily(str, Enum):
    """Vertical pitch-content family.

    This is one axis of the V2 voicing system. It says which chord tones or
    color tones are eligible before any register/disposition decision is made.
    It deliberately includes basic triads because V2 must support pop/folk/rock
    harmony, not only jazz rootless voicings.
    """

    MAJOR_TRIAD = "major_triad"
    MINOR_TRIAD = "minor_triad"
    DIMINISHED_TRIAD = "diminished_triad"
    AUGMENTED_TRIAD = "augmented_triad"
    SUS2_TRIAD = "sus2_triad"
    SUS4_TRIAD = "sus4_triad"
    POWER_CHORD_5TH = "power_chord_5th"
    SEVENTH_BASIC = "seventh_chord_basic"
    GUIDE_TONE = "guide_tone"
    SHELL = "shell"
    SHELL_PLUS_5 = "shell_plus_5"
    SHELL_PLUS_COLOR = "shell_plus_color"
    ROOTLESS_A = "rootless_A"
    ROOTLESS_B = "rootless_B"
    ROOTED_COLOR = "rooted_color"


class ColorPolicyMode(str, Enum):
    """How much unnotated color the voicing system may add.

    Default V2 tuning behavior is conservative: use only chord-symbol material.
    Richer color requires explicit user/LLM intent.
    """

    CHORD_SYMBOL_ONLY = "chord_symbol_only"
    STYLE_SAFE_EXTENSIONS = "style_safe_extensions"
    ALTERED_DOMINANT = "altered_dominant"
    RICH_REHARM_COLOR = "rich_reharm_color"


class AlteredDominantIntensity(str, Enum):
    OFF = "off"
    LIGHT = "light"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class AlteredDominantScope(str, Enum):
    FUNCTIONAL_DOMINANTS = "functional_dominants"
    RESOLVING_V7 = "resolving_v7"
    SECONDARY_DOMINANTS = "secondary_dominants"
    STATIC_BLUES_DOMINANTS = "static_blues_dominants"
    BACKDOOR_DOMINANTS = "backdoor_dominants"
    ALL_DOMINANTS = "all_dominants"
    LLM_SELECTED = "llm_selected"


class AlteredDominantFunctionalScope(str, Enum):
    NONE = "none"
    RESOLVING_V7 = "resolving_v7"
    SECONDARY_DOMINANT = "secondary_dominant"
    STATIC_BLUES_DOMINANT = "static_blues_dominant"
    BACKDOOR_DOMINANT = "backdoor_dominant"
    NONFUNCTIONAL_DOMINANT = "nonfunctional_dominant"
    LLM_SELECTED = "llm_selected"
    EXPLICIT_CHORD_SYMBOL_ALTERED = "explicit_chord_symbol_altered"


ALTERED_DOMINANT_POLICY_VERSION = "v2_2_88"

ALTERED_DOMINANT_SOURCE_KINDS = (
    "rooted_color",
    "rootless_ab",
    "upper_structure",
)

_DEFAULT_ALTERED_DOMINANT_INTENSITY_BIASES: dict[AlteredDominantIntensity, dict[str, float]] = {
    AlteredDominantIntensity.OFF: {
        "rooted_color": 0.0,
        "rootless_ab": 0.0,
        "upper_structure": 0.0,
    },
    # LIGHT opens the door but keeps altered material clearly secondary.
    AlteredDominantIntensity.LIGHT: {
        "rooted_color": 0.04,
        "rootless_ab": -0.08,
        "upper_structure": -0.12,
    },
    # MEDIUM makes rooted altered color audible and keeps rootless/US occasional.
    AlteredDominantIntensity.MEDIUM: {
        "rooted_color": 0.10,
        "rootless_ab": 0.02,
        "upper_structure": 0.00,
    },
    # HIGH is the normal jazz altered-dominant color setting.
    AlteredDominantIntensity.HIGH: {
        "rooted_color": 0.16,
        "rootless_ab": 0.10,
        "upper_structure": 0.08,
    },
    # FULL strongly favors altered pools when the functional gate authorizes them.
    AlteredDominantIntensity.FULL: {
        "rooted_color": 0.24,
        "rootless_ab": 0.20,
        "upper_structure": 0.18,
    },
}


@dataclass(frozen=True)
class AlteredDominantPolicyDecision:
    """Resolved policy gate for dominant altered color.

    This is intentionally separate from HarmonicExpansionPolicy: harmonic
    expansion answers whether unnotated color may be added; altered-dominant
    policy answers whether dominant color should come from an altered pool.
    LLM/user metadata may set ``altered_dominant_enabled`` or the nested
    ``altered_dominant_policy`` mapping.
    """

    enabled: bool = False
    intensity: AlteredDominantIntensity = AlteredDominantIntensity.OFF
    scope: AlteredDominantScope = AlteredDominantScope.FUNCTIONAL_DOMINANTS
    scopes: tuple[AlteredDominantScope, ...] = (AlteredDominantScope.FUNCTIONAL_DOMINANTS,)
    functional_scope: AlteredDominantFunctionalScope = AlteredDominantFunctionalScope.NONE
    inferred_functional_scope: AlteredDominantFunctionalScope = AlteredDominantFunctionalScope.NONE
    authorized_for_chord: bool = False
    explicit_chord_symbol_altered: bool = False
    requires_harmonic_expansion: bool = True
    reason: str = "disabled"
    source_weight_biases: tuple[tuple[str, float], ...] = ()

    def source_weight_bias(self, source_kind: str) -> float:
        weights = dict(self.source_weight_biases)
        return float(weights.get(str(source_kind), 0.0))

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "altered_dominant_policy_version": ALTERED_DOMINANT_POLICY_VERSION,
            "enabled": bool(self.enabled),
            "intensity": self.intensity.value,
            "scope": self.scope.value,
            "scopes": [scope.value for scope in self.scopes],
            "functional_scope": self.functional_scope.value,
            "inferred_functional_scope": self.inferred_functional_scope.value,
            "authorized_for_chord": bool(self.authorized_for_chord),
            "explicit_chord_symbol_altered": bool(self.explicit_chord_symbol_altered),
            "requires_harmonic_expansion": bool(self.requires_harmonic_expansion),
            "reason": self.reason,
            "source_weight_biases": {key: round(float(value), 4) for key, value in self.source_weight_biases},
        }


def resolve_altered_dominant_policy(policy: Any | None, chord: Any | None = None) -> AlteredDominantPolicyDecision:
    """Resolve the separate altered-dominant switch from policy metadata.

    v2_2_85 changes the authorization boundary from ``dominant quality`` to
    ``dominant function``.  A plain dominant may receive unnotated altered color
    only when harmonic expansion is open *and* the resolved functional scope is
    included by the policy. Explicit chart alterations such as G7b9/G7alt remain
    faithful chart material regardless of the unnotated altered switch.
    """

    try:
        metadata = dict(getattr(policy, "metadata", None) or {})
    except Exception:
        metadata = dict(policy or {}) if isinstance(policy, dict) else {}
    nested = metadata.get("altered_dominant_policy") or metadata.get("altered_dominant") or {}
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    raw_intensity = str(nested.get("intensity") or metadata.get("altered_dominant_intensity") or "off")
    intensity = _coerce_enum(AlteredDominantIntensity, raw_intensity, AlteredDominantIntensity.OFF)
    scopes = _resolve_altered_dominant_scopes(nested, metadata)
    scope = scopes[0] if scopes else AlteredDominantScope.FUNCTIONAL_DOMINANTS
    enabled = bool(nested.get("enabled", metadata.get("altered_dominant_enabled", False))) or intensity != AlteredDominantIntensity.OFF
    mode = metadata.get("color_policy_mode") or getattr(getattr(policy, "color_policy_mode", None), "value", None)
    if str(mode) == ColorPolicyMode.ALTERED_DOMINANT.value:
        enabled = True
        if intensity == AlteredDominantIntensity.OFF:
            intensity = AlteredDominantIntensity.HIGH
    harmonic_expansion = bool(metadata.get("harmonic_expansion_enabled", getattr(policy, "harmonic_expansion_enabled", False))) or str(mode) in {
        ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
        ColorPolicyMode.ALTERED_DOMINANT.value,
        ColorPolicyMode.RICH_REHARM_COLOR.value,
    }
    chord_is_dominant = bool(getattr(chord, "is_dominant", False))
    alterations = set(getattr(chord, "alterations", ()) or ())
    symbol = str(getattr(chord, "symbol", "")).lower()
    explicit_altered = bool(chord_is_dominant and ("alt" in symbol or "alt" in alterations or alterations & {"b9", "#9", "#11", "b13", "#5", "b5"}))
    functional_scope = _infer_altered_dominant_functional_scope(chord, metadata)
    inferred_functional_scope = functional_scope
    llm_selected = _altered_dominant_llm_selection_matches(metadata, nested)
    if llm_selected:
        functional_scope = AlteredDominantFunctionalScope.LLM_SELECTED

    if not chord_is_dominant:
        authorized = False
        reason = "not_dominant"
    elif explicit_altered:
        authorized = True
        functional_scope = AlteredDominantFunctionalScope.EXPLICIT_CHORD_SYMBOL_ALTERED
        reason = "explicit_chord_symbol_altered"
    elif enabled and not harmonic_expansion:
        authorized = False
        reason = "altered_requested_but_harmonic_expansion_off"
    elif enabled and _altered_dominant_scope_authorizes(functional_scope, scopes, llm_selected=llm_selected):
        authorized = True
        reason = f"harmonic_expansion_plus_altered_dominant_{functional_scope.value}"
    elif enabled:
        authorized = False
        reason = f"altered_scope_not_authorized_for_{functional_scope.value}"
    else:
        authorized = False
        reason = "altered_dominant_policy_disabled"
    decision = AlteredDominantPolicyDecision(
        enabled=bool(enabled),
        intensity=intensity,
        scope=scope,
        scopes=tuple(scopes),
        functional_scope=functional_scope,
        inferred_functional_scope=inferred_functional_scope,
        authorized_for_chord=bool(authorized),
        explicit_chord_symbol_altered=bool(explicit_altered),
        reason=reason,
        source_weight_biases=tuple(
            sorted(
                _altered_dominant_source_weight_biases(
                    nested=nested,
                    metadata=metadata,
                    intensity=intensity,
                    functional_scope=functional_scope,
                    authorized=bool(authorized),
                    explicit_altered=bool(explicit_altered),
                ).items()
            )
        ),
    )
    return decision


def altered_dominant_source_weight_bias(
    policy: Any | None,
    chord: Any | None,
    source_kind: str,
) -> float:
    """Return the v2_2_88 score bias for one altered-dominant source family.

    This is a selector bias, not an authorization gate. Authorization remains
    owned by :func:`resolve_altered_dominant_policy`; this helper only converts
    ``light / medium / high / full`` into how strongly a legal altered source
    should compete against safe/rooted/rootless alternatives.
    """

    decision = resolve_altered_dominant_policy(policy, chord)
    return decision.source_weight_bias(str(source_kind))


def _altered_dominant_source_weight_biases(
    *,
    nested: dict[str, Any],
    metadata: dict[str, Any],
    intensity: AlteredDominantIntensity,
    functional_scope: AlteredDominantFunctionalScope,
    authorized: bool,
    explicit_altered: bool,
) -> dict[str, float]:
    if not authorized:
        return {kind: 0.0 for kind in ALTERED_DOMINANT_SOURCE_KINDS}

    biases = dict(_DEFAULT_ALTERED_DOMINANT_INTENSITY_BIASES.get(intensity, {}))

    # Explicit chart alterations are fidelity, not optional expansion. Keep them
    # at least medium-strength even if the global intensity is light/off.
    if explicit_altered:
        medium = _DEFAULT_ALTERED_DOMINANT_INTENSITY_BIASES[AlteredDominantIntensity.MEDIUM]
        biases = {kind: max(float(biases.get(kind, 0.0)), float(medium[kind])) for kind in ALTERED_DOMINANT_SOURCE_KINDS}

    # LLM-selected regions should be audibly selected. Static/blues and backdoor
    # altered color should remain more conservative unless explicitly pushed.
    if functional_scope == AlteredDominantFunctionalScope.LLM_SELECTED:
        biases = {kind: float(value) + 0.06 for kind, value in biases.items()}
    elif functional_scope in {
        AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT,
        AlteredDominantFunctionalScope.BACKDOOR_DOMINANT,
    } and not explicit_altered:
        biases = {kind: float(value) - 0.04 for kind, value in biases.items()}

    override = (
        nested.get("source_weight_biases")
        or nested.get("source_weights")
        or metadata.get("altered_dominant_source_weight_biases")
        or metadata.get("altered_dominant_source_weights")
        or {}
    )
    if isinstance(override, dict):
        for key, value in override.items():
            normalized = _normalize_altered_source_kind(str(key))
            if normalized in ALTERED_DOMINANT_SOURCE_KINDS:
                try:
                    biases[normalized] = float(value)
                except (TypeError, ValueError):
                    pass

    by_intensity = nested.get("source_weight_biases_by_intensity") or metadata.get("altered_dominant_source_weight_biases_by_intensity") or {}
    if isinstance(by_intensity, dict):
        intensity_values = by_intensity.get(intensity.value) or by_intensity.get(str(intensity.value).lower()) or {}
        if isinstance(intensity_values, dict):
            for key, value in intensity_values.items():
                normalized = _normalize_altered_source_kind(str(key))
                if normalized in ALTERED_DOMINANT_SOURCE_KINDS:
                    try:
                        biases[normalized] = float(value)
                    except (TypeError, ValueError):
                        pass

    return {kind: float(biases.get(kind, 0.0)) for kind in ALTERED_DOMINANT_SOURCE_KINDS}


def _normalize_altered_source_kind(value: str) -> str:
    token = value.strip().lower().replace("-", "_")
    aliases = {
        "rooted": "rooted_color",
        "rooted_color": "rooted_color",
        "rooted_colour": "rooted_color",
        "rooted_altered": "rooted_color",
        "rootless": "rootless_ab",
        "rootless_ab": "rootless_ab",
        "rootless_a_b": "rootless_ab",
        "rootless_altered": "rootless_ab",
        "upper": "upper_structure",
        "upper_structure": "upper_structure",
        "us": "upper_structure",
        "upper_structure_altered": "upper_structure",
    }
    return aliases.get(token, token)


def _resolve_altered_dominant_scopes(nested: dict[str, Any], metadata: dict[str, Any]) -> tuple[AlteredDominantScope, ...]:
    raw = nested.get("scopes", nested.get("scope", metadata.get("altered_dominant_scopes", metadata.get("altered_dominant_scope"))))
    if raw is None:
        raw = AlteredDominantScope.FUNCTIONAL_DOMINANTS.value
    if isinstance(raw, str) and "," in raw:
        raw_values = [part.strip() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, (str, AlteredDominantScope)):
        raw_values = [raw]
    else:
        raw_values = list(raw or [])
    aliases = {
        "functional": AlteredDominantScope.FUNCTIONAL_DOMINANTS.value,
        "functional_dominant": AlteredDominantScope.FUNCTIONAL_DOMINANTS.value,
        "functional_dominants": AlteredDominantScope.FUNCTIONAL_DOMINANTS.value,
        "resolving": AlteredDominantScope.RESOLVING_V7.value,
        "resolving_v": AlteredDominantScope.RESOLVING_V7.value,
        "resolving_v7": AlteredDominantScope.RESOLVING_V7.value,
        "v7_to_i": AlteredDominantScope.RESOLVING_V7.value,
        "secondary": AlteredDominantScope.SECONDARY_DOMINANTS.value,
        "secondary_dominant": AlteredDominantScope.SECONDARY_DOMINANTS.value,
        "secondary_dominants": AlteredDominantScope.SECONDARY_DOMINANTS.value,
        "static": AlteredDominantScope.STATIC_BLUES_DOMINANTS.value,
        "blues": AlteredDominantScope.STATIC_BLUES_DOMINANTS.value,
        "static_blues": AlteredDominantScope.STATIC_BLUES_DOMINANTS.value,
        "static_blues_dominant": AlteredDominantScope.STATIC_BLUES_DOMINANTS.value,
        "static_blues_dominants": AlteredDominantScope.STATIC_BLUES_DOMINANTS.value,
        "backdoor": AlteredDominantScope.BACKDOOR_DOMINANTS.value,
        "backdoor_dominant": AlteredDominantScope.BACKDOOR_DOMINANTS.value,
        "backdoor_dominants": AlteredDominantScope.BACKDOOR_DOMINANTS.value,
        "all": AlteredDominantScope.ALL_DOMINANTS.value,
        "all_dominants": AlteredDominantScope.ALL_DOMINANTS.value,
        "llm": AlteredDominantScope.LLM_SELECTED.value,
        "llm_selected": AlteredDominantScope.LLM_SELECTED.value,
        "llm_selected_regions": AlteredDominantScope.LLM_SELECTED.value,
    }
    scopes: list[AlteredDominantScope] = []
    for value in raw_values:
        token = str(getattr(value, "value", value)).strip().lower().replace("-", "_")
        token = aliases.get(token, token)
        scopes.append(_coerce_enum(AlteredDominantScope, token, AlteredDominantScope.FUNCTIONAL_DOMINANTS))
    return tuple(dict.fromkeys(scopes)) or (AlteredDominantScope.FUNCTIONAL_DOMINANTS,)


def _infer_altered_dominant_functional_scope(chord: Any | None, metadata: dict[str, Any]) -> AlteredDominantFunctionalScope:
    if not bool(getattr(chord, "is_dominant", False)):
        return AlteredDominantFunctionalScope.NONE

    semantic = _metadata_text(metadata, "dominant_function", "dominant_context", "altered_dominant_function", "harmonic_function")
    if semantic in {"resolving", "resolving_v", "resolving_v7", "v7_to_i", "dominant_to_tonic"}:
        return AlteredDominantFunctionalScope.RESOLVING_V7
    if semantic in {"secondary", "secondary_dominant", "applied_dominant"}:
        return AlteredDominantFunctionalScope.SECONDARY_DOMINANT
    if semantic in {"static", "blues", "static_blues", "static_dominant", "blues_dominant"}:
        return AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT
    if semantic in {"backdoor", "backdoor_dominant", "backdoor_resolution"}:
        return AlteredDominantFunctionalScope.BACKDOOR_DOMINANT

    previous_symbol = _metadata_string(metadata, "previous_chord_symbol", "prev_chord_symbol") or None
    next_symbol = _metadata_string(metadata, "next_chord_symbol") or None
    home_key = _metadata_string(metadata, "home_key", "key", "tonic") or None
    if not next_symbol:
        return AlteredDominantFunctionalScope.NONFUNCTIONAL_DOMINANT

    try:
        from jammate_engine.core.harmony.harmonic_context import classify_functional_motion

        motion = classify_functional_motion(
            previous_chord_symbol=previous_symbol,
            chord_symbol=str(getattr(chord, "symbol", "")),
            next_chord_symbol=next_symbol,
        )
    except Exception:
        motion = None

    if motion is not None:
        if motion.current_to_next_type == "backdoor_dominant" or motion.has_tag("backdoor_dominant"):
            return (
                AlteredDominantFunctionalScope.BACKDOOR_DOMINANT
                if _next_symbol_is_home_tonic(next_symbol, home_key)
                else AlteredDominantFunctionalScope.SECONDARY_DOMINANT
            )
        if motion.current_to_next_type == "static_blues_dominant" or motion.has_tag("static_blues_dominant"):
            return AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT
        if motion.current_to_next_type == "secondary_dominant_motion" or motion.has_tag("secondary_dominant_motion"):
            return AlteredDominantFunctionalScope.SECONDARY_DOMINANT
        if motion.is_turnaround_like and motion.root_interval_to_next == 5:
            return AlteredDominantFunctionalScope.SECONDARY_DOMINANT
        if motion.current_to_next_type in {"v_i_major", "v_i_minor", "dominant_to_tonic"} or motion.has_tag("dominant_to_tonic"):
            if _next_symbol_is_home_tonic(next_symbol, home_key):
                return AlteredDominantFunctionalScope.RESOLVING_V7
            return AlteredDominantFunctionalScope.SECONDARY_DOMINANT

    return AlteredDominantFunctionalScope.NONFUNCTIONAL_DOMINANT


def _next_symbol_is_home_tonic(next_symbol: str | None, home_key: str | None) -> bool:
    if not next_symbol or not home_key:
        return True
    try:
        from jammate_engine.core.harmony.chord_parser import parse_chord

        next_chord = parse_chord(next_symbol)
        key_chord = parse_chord(home_key)
    except Exception:
        return True
    return bool(next_chord.root_pc == key_chord.root_pc)


def _altered_dominant_scope_authorizes(
    functional_scope: AlteredDominantFunctionalScope,
    scopes: tuple[AlteredDominantScope, ...],
    *,
    llm_selected: bool,
) -> bool:
    if AlteredDominantScope.ALL_DOMINANTS in scopes:
        return functional_scope != AlteredDominantFunctionalScope.NONE
    if AlteredDominantScope.LLM_SELECTED in scopes and llm_selected:
        return True
    if AlteredDominantScope.FUNCTIONAL_DOMINANTS in scopes and functional_scope in {
        AlteredDominantFunctionalScope.RESOLVING_V7,
        AlteredDominantFunctionalScope.SECONDARY_DOMINANT,
    }:
        return True
    scope_map = {
        AlteredDominantScope.RESOLVING_V7: AlteredDominantFunctionalScope.RESOLVING_V7,
        AlteredDominantScope.SECONDARY_DOMINANTS: AlteredDominantFunctionalScope.SECONDARY_DOMINANT,
        AlteredDominantScope.STATIC_BLUES_DOMINANTS: AlteredDominantFunctionalScope.STATIC_BLUES_DOMINANT,
        AlteredDominantScope.BACKDOOR_DOMINANTS: AlteredDominantFunctionalScope.BACKDOOR_DOMINANT,
    }
    return any(scope_map.get(scope) == functional_scope for scope in scopes)


def _altered_dominant_llm_selection_matches(metadata: dict[str, Any], nested: dict[str, Any]) -> bool:
    if bool(nested.get("force_current_chord") or nested.get("force_for_current_chord") or metadata.get("altered_dominant_force_current_chord")):
        return True
    selectors = nested.get("llm_selected") or nested.get("selected") or metadata.get("altered_dominant_selected") or {}
    if isinstance(selectors, bool):
        return selectors
    if not isinstance(selectors, dict):
        selectors = {}
    selector_pairs = (
        (("region_ids", "selected_region_ids"), ("region_id",)),
        (("section_ids", "selected_section_ids", "sections"), ("section_id", "section_label")),
        (("phrases", "phrase_ids", "selected_phrases"), ("phrase",)),
        (("chord_symbols", "symbols"), ("chord_symbol",)),
        (("chorus_indices",), ("chorus_index",)),
        (("bar_indices", "performance_bar_indices"), ("performance_bar_index", "bar_index")),
        (("written_bar_indices",), ("written_bar_index",)),
        (("source_bar_indices",), ("source_bar_index",)),
    )
    for selector_keys, metadata_keys in selector_pairs:
        raw_values = _first_existing(selectors, selector_keys)
        if raw_values is None:
            raw_values = _first_existing(nested, selector_keys)
        if raw_values is None:
            continue
        allowed = {str(item) for item in _as_list(raw_values)}
        for key in metadata_keys:
            value = metadata.get(key)
            if value is not None and str(value) in allowed:
                return True
    return False


def _metadata_text(metadata: dict[str, Any], *keys: str) -> str:
    value = _metadata_string(metadata, *keys)
    return value.lower()


def _metadata_string(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _first_existing(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, int, float)):
        return [value]
    return list(value) if isinstance(value, (list, tuple, set, frozenset)) else [value]



class RootSupportPolicy(str, Enum):
    ROOTLESS_PREFERRED = "rootless_preferred"
    ROOTLESS_ALLOWED = "rootless_allowed"
    ROOT_OPTIONAL = "root_optional"
    ROOT_PREFERRED = "root_preferred"
    ROOT_REQUIRED = "root_required"
    BASS_ROOT_REQUIRED = "bass_root_required"


class BassRelation(str, Enum):
    ROOT_POSITION = "root_position"
    FIRST_INVERSION = "first_inversion"
    SECOND_INVERSION = "second_inversion"
    THIRD_INVERSION = "third_inversion"
    ROOTLESS_LOWEST_3RD = "rootless_lowest_3rd"
    ROOTLESS_LOWEST_7TH = "rootless_lowest_7th"
    BASS_OMITTED = "bass_omitted"


class IntervalStructure(str, Enum):
    TERTIAN = "tertian"
    QUARTAL = "quartal"
    SECUNDAL_CLUSTER = "secundal_cluster"
    MIXED = "mixed"




class FunctionalGrouping(str, Enum):
    """Abstract density grouping axis for V2 voicing recipes.

    These names are intentionally not LH/RH. Instrument-specific realization may
    project them into hands, manuals, strings, registers, or sections later.
    """

    TWO = "2"
    THREE = "3"
    ONE_PLUS_THREE = "1+3"
    TWO_PLUS_TWO = "2+2"
    ONE_PLUS_FOUR = "1+4"
    TWO_PLUS_THREE = "2+3"
    TWO_PLUS_FOUR = "2+4"
    THREE_PLUS_THREE = "3+3"
    THREE_PLUS_FOUR = "3+4"


class VoicingGroupRole(str, Enum):
    """Functional group labels used by core/voicing metadata.

    They are abstract roles, not physical hands.
    """

    ANCHOR = "anchor"
    FOUNDATION = "foundation"
    SUPPORT = "support"
    PROJECTION = "projection"
    COLOR = "color"
    MOTION = "motion"
    EXTENSION = "extension"


class EnsembleRole(str, Enum):
    HARMONIC_COMPING = "harmonic_comping"
    PIANO_LH_BASS_FOUNDATION = "piano_lh_bass_foundation"
    PIANO_RH_HARMONIC_COMPING = "piano_rh_harmonic_comping"


@dataclass(frozen=True)
class RootSupportDecision:
    """Resolved root-support responsibility for one voicing request.

    This is a diagnostic/planning contract, not a new selector.  It makes the
    ensemble-level root foundation decision explicit before candidate
    generation, so downstream debugging can explain why a voicing was allowed
    to be rootless or required to include the root.
    """

    requested_policy: RootSupportPolicy
    effective_policy: RootSupportPolicy
    bass_present: bool
    bass_foundation_provider: str
    harmonic_comping_role: str
    piano_split_role_enabled: bool
    allow_rootless_without_bass: bool
    root_required: bool
    root_preferred: bool
    bass_root_required: bool
    rootless_allowed: bool
    rootless_preferred: bool
    reason: str

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "requested_policy": self.requested_policy.value,
            "effective_policy": self.effective_policy.value,
            "bass_present": self.bass_present,
            "bass_foundation_provider": self.bass_foundation_provider,
            "harmonic_comping_role": self.harmonic_comping_role,
            "piano_split_role_enabled": self.piano_split_role_enabled,
            "allow_rootless_without_bass": self.allow_rootless_without_bass,
            "root_required": self.root_required,
            "root_preferred": self.root_preferred,
            "bass_root_required": self.bass_root_required,
            "rootless_allowed": self.rootless_allowed,
            "rootless_preferred": self.rootless_preferred,
            "reason": self.reason,
        }


def resolve_root_support_decision(
    requested_policy: RootSupportPolicy | str | None,
    ensemble: EnsembleContext | dict | None,
) -> RootSupportDecision:
    """Resolve the effective root-support policy from ensemble context.

    Rules intentionally match the V2 voicing design document:
    - with bass: harmonic comping may follow the style policy, including
      rootless/guide-tone/color voicings.
    - no bass + split role: PianoLH_BassFoundation supplies foundation, so the
      harmonic comping side should not be forced to stuff root into every chord.
    - no bass + split disabled: harmonic voicing must include root support.
    - explicit allow_rootless_without_bass: keep intentional floating/rootless
      texture unless the policy itself requested roots.
    """

    context = EnsembleContext.from_dict(ensemble)
    requested = _coerce_enum(RootSupportPolicy, requested_policy, RootSupportPolicy.ROOT_OPTIONAL)
    effective = requested
    reason = "bass_present_use_style_policy" if context.bass_present else "use_style_policy"

    if context.needs_piano_lh_bass_foundation:
        reason = "no_bass_split_role_lh_foundation"
        if requested == RootSupportPolicy.ROOTLESS_PREFERRED:
            # The RH comping side may stay light/rootless, but the global
            # arrangement already has explicit LH bass support. Downgrading from
            # preferred to allowed avoids over-biasing RH rootless candidates.
            effective = RootSupportPolicy.ROOTLESS_ALLOWED
        elif requested in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED}:
            reason = "explicit_root_policy_with_split_role"
    elif context.should_force_root_in_harmonic_voicing:
        reason = "no_bass_no_split_role_requires_harmonic_root"
        effective = RootSupportPolicy.ROOT_REQUIRED
    elif not context.bass_present and context.allow_rootless_without_bass:
        reason = "no_bass_user_allowed_rootless_without_foundation"

    return RootSupportDecision(
        requested_policy=requested,
        effective_policy=effective,
        bass_present=context.bass_present,
        bass_foundation_provider=context.bass_foundation_provider,
        harmonic_comping_role=context.harmonic_comping_role,
        piano_split_role_enabled=context.piano_split_role_enabled,
        allow_rootless_without_bass=context.allow_rootless_without_bass,
        root_required=effective in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED},
        root_preferred=effective == RootSupportPolicy.ROOT_PREFERRED,
        bass_root_required=effective == RootSupportPolicy.BASS_ROOT_REQUIRED,
        rootless_allowed=effective in {
            RootSupportPolicy.ROOTLESS_PREFERRED,
            RootSupportPolicy.ROOTLESS_ALLOWED,
            RootSupportPolicy.ROOT_OPTIONAL,
        },
        rootless_preferred=effective == RootSupportPolicy.ROOTLESS_PREFERRED,
        reason=reason,
    )


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _coerce_enum(enum_type: type[Enum], value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_type):
        return value
    if value is None:
        return default
    try:
        return enum_type(value)
    except ValueError:
        return default


def _coerce_tuple(enum_type: type[Enum], values: Any) -> tuple[Enum, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, Enum)):
        values = (values,)
    out: list[Enum] = []
    for value in values:
        if isinstance(value, enum_type):
            out.append(value)
            continue
        try:
            out.append(enum_type(value))
        except ValueError:
            continue
    return tuple(out)


def _coerce_nested_float_map(value: Any) -> dict[str, dict[str, float]]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, dict[str, float]] = {}
    for gate, weights in value.items():
        if not isinstance(weights, dict):
            continue
        parsed = {str(k): float(v) for k, v in weights.items()}
        if parsed:
            out[str(gate)] = parsed
    return out


@dataclass(frozen=True)
class VoicingPolicy:
    """Typed, multi-axis voicing policy consumed by core/voicing.

    The important design choice is that this is not a single `voicing_type`.
    V2 separates at least these axes:
      - content family: triad, seventh, guide tone, shell, rootless, color
      - root support: rootless allowed/preferred vs root required
      - bass relation: root position, inversion, omitted/rootless lowest tone
      - disposition: legacy input preference normalized by core.voicing.disposition
      - interval structure: tertian/quartal/secundal/mixed
      - density and register constraints
    """

    root_support: RootSupportPolicy = RootSupportPolicy.ROOT_OPTIONAL
    preferred_content: ContentFamily | None = None
    allowed_content: tuple[ContentFamily, ...] = ()
    preferred_disposition: Disposition = Disposition.OPEN
    allowed_dispositions: tuple[Disposition, ...] = ()
    bass_relation: BassRelation = BassRelation.ROOT_POSITION
    interval_structure: IntervalStructure = IntervalStructure.TERTIAN
    content_family_weights: dict[str, float] | None = None
    source_family_weights: dict[str, float] | None = None
    source_family_weights_by_gate: dict[str, dict[str, float]] | None = None
    harmonic_expansion_enabled: bool = False
    color_policy_mode: ColorPolicyMode = ColorPolicyMode.CHORD_SYMBOL_ONLY
    low_priority_degrees: tuple[str, ...] = ()
    low_priority_degree_penalty: float = 0.0
    preferred_density: int = 4
    min_density: int = 2
    max_density: int = 6
    register_low: int = 48
    register_high: int = 72
    left_hand_low: int = 36
    left_hand_high: int = 60
    right_hand_low: int = 55
    right_hand_high: int = 79
    top_voice_low: int = 60
    top_voice_high: int = 76
    comfort_register_low: int = 56
    comfort_register_high: int = 70
    max_voicing_span: int = 24
    max_top_voice_leap: int = 7
    voice_leading_weight: float = 1.0
    top_voice_weight: float = 1.0
    register_guard_weight: float = 1.0
    selector_temperature: float = 0.18
    selection_pool_size: int = 3
    ensemble_role: EnsembleRole = EnsembleRole.HARMONIC_COMPING
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_legacy_dict(cls, value: dict | None) -> "VoicingPolicy":
        value = value or {}
        return cls(
            root_support=_coerce_enum(RootSupportPolicy, value.get("root_support"), cls.root_support),
            preferred_content=_coerce_enum(ContentFamily, value.get("preferred_content"), None) if value.get("preferred_content") else None,
            allowed_content=_coerce_tuple(ContentFamily, value.get("allowed_content")),
            preferred_disposition=_coerce_enum(Disposition, value.get("preferred_disposition"), cls.preferred_disposition),
            allowed_dispositions=_coerce_tuple(Disposition, value.get("allowed_dispositions")),
            bass_relation=_coerce_enum(BassRelation, value.get("bass_relation"), cls.bass_relation),
            interval_structure=_coerce_enum(IntervalStructure, value.get("interval_structure"), cls.interval_structure),
            content_family_weights={str(k): float(v) for k, v in dict(value.get("content_family_weights", {}) or {}).items()} or None,
            source_family_weights={str(k): float(v) for k, v in dict(value.get("source_family_weights", {}) or {}).items()} or None,
            source_family_weights_by_gate=_coerce_nested_float_map(value.get("source_family_weights_by_gate")) or None,
            harmonic_expansion_enabled=bool(value.get("harmonic_expansion_enabled", cls.harmonic_expansion_enabled)),
            color_policy_mode=_coerce_enum(ColorPolicyMode, value.get("color_policy_mode"), cls.color_policy_mode),
            low_priority_degrees=tuple(str(item) for item in value.get("low_priority_degrees", ()) or ()),
            low_priority_degree_penalty=float(value.get("low_priority_degree_penalty", cls.low_priority_degree_penalty)),
            preferred_density=int(value.get("preferred_density", cls.preferred_density)),
            min_density=int(value.get("min_density", cls.min_density)),
            max_density=int(value.get("max_density", cls.max_density)),
            register_low=int(value.get("register_low", cls.register_low)),
            register_high=int(value.get("register_high", cls.register_high)),
            left_hand_low=int(value.get("left_hand_low", cls.left_hand_low)),
            left_hand_high=int(value.get("left_hand_high", cls.left_hand_high)),
            right_hand_low=int(value.get("right_hand_low", cls.right_hand_low)),
            right_hand_high=int(value.get("right_hand_high", cls.right_hand_high)),
            top_voice_low=int(value.get("top_voice_low", cls.top_voice_low)),
            top_voice_high=int(value.get("top_voice_high", cls.top_voice_high)),
            comfort_register_low=int(value.get("comfort_register_low", cls.comfort_register_low)),
            comfort_register_high=int(value.get("comfort_register_high", cls.comfort_register_high)),
            max_voicing_span=int(value.get("max_voicing_span", cls.max_voicing_span)),
            max_top_voice_leap=int(value.get("max_top_voice_leap", cls.max_top_voice_leap)),
            voice_leading_weight=float(value.get("voice_leading_weight", cls.voice_leading_weight)),
            top_voice_weight=float(value.get("top_voice_weight", cls.top_voice_weight)),
            register_guard_weight=float(value.get("register_guard_weight", cls.register_guard_weight)),
            selector_temperature=float(value.get("selector_temperature", cls.selector_temperature)),
            selection_pool_size=int(value.get("selection_pool_size", cls.selection_pool_size)),
            ensemble_role=_coerce_enum(EnsembleRole, value.get("ensemble_role"), cls.ensemble_role),
            metadata=dict(value.get("metadata", {})),
        )

    def merge(self, overrides: "VoicingPolicy | dict | None") -> "VoicingPolicy":
        if overrides is None:
            return self
        if isinstance(overrides, VoicingPolicy):
            return overrides
        if not isinstance(overrides, dict):
            return self
        data = self.to_debug_dict()
        data.update(overrides)
        return VoicingPolicy.from_legacy_dict(data)

    @property
    def effective_density_range(self) -> tuple[int, int, int]:
        """Return normalized min / preferred / max density without mutation."""

        low = max(1, int(self.min_density))
        high = max(low, int(self.max_density))
        preferred = min(max(int(self.preferred_density), low), high)
        return low, preferred, high

    @property
    def effective_dispositions(self) -> tuple[Disposition, ...]:
        return self.allowed_dispositions or (self.preferred_disposition,)

    @property
    def is_root_required(self) -> bool:
        return self.root_support in {
            RootSupportPolicy.ROOT_REQUIRED,
            RootSupportPolicy.BASS_ROOT_REQUIRED,
            RootSupportPolicy.ROOT_PREFERRED,
        }

    def with_ensemble_context(self, ensemble: EnsembleContext | dict | None) -> "VoicingPolicy":
        context = EnsembleContext.from_dict(ensemble)
        decision = resolve_root_support_decision(self.root_support, context)
        root_support_metadata = {
            **dict(self.metadata or {}),
            "root_support_decision": decision.to_debug_dict(),
        }

        if context.needs_piano_lh_bass_foundation:
            # Preferred no-bass behavior: split the piano into two roles.
            # Bass-pattern events become PianoLH_BassFoundation elsewhere, while
            # harmonic piano events remain right-hand comping. Do not force a
            # root into every RH chord unless the user explicitly asks for it.
            return replace(
                self,
                root_support=decision.effective_policy,
                preferred_disposition=Disposition.OPEN
                if self.preferred_disposition in {Disposition.LEFT_ROOT_RIGHT_CHORD, Disposition.LEFT_ROOT_RIGHT_ROOTLESS, Disposition.OPEN_ROOT_10TH}
                else self.preferred_disposition,
                register_low=max(self.register_low, context.piano_rh_low),
                register_high=min(self.register_high, context.piano_rh_high),
                left_hand_low=context.piano_lh_low,
                left_hand_high=context.piano_lh_high,
                right_hand_low=context.piano_rh_low,
                right_hand_high=context.piano_rh_high,
                top_voice_low=max(self.top_voice_low, context.piano_rh_low + 5),
                top_voice_high=min(self.top_voice_high, context.piano_rh_high),
                comfort_register_low=max(self.comfort_register_low, context.piano_rh_low),
                comfort_register_high=min(self.comfort_register_high, context.piano_rh_high),
                ensemble_role=EnsembleRole.PIANO_RH_HARMONIC_COMPING,
                metadata=root_support_metadata,
            )
        if context.should_force_root_in_harmonic_voicing:
            # Fallback for users who disable split role while also removing bass.
            return replace(
                self,
                root_support=decision.effective_policy,
                preferred_disposition=Disposition.LEFT_ROOT_RIGHT_CHORD,
                ensemble_role=EnsembleRole.PIANO_LH_BASS_FOUNDATION,
                metadata=root_support_metadata,
            )
        return replace(self, root_support=decision.effective_policy, metadata=root_support_metadata)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "root_support": self.root_support.value,
            "preferred_content": self.preferred_content.value if self.preferred_content else None,
            "allowed_content": [_enum_value(value) for value in self.allowed_content],
            "preferred_disposition": self.preferred_disposition.value,
            "allowed_dispositions": [_enum_value(value) for value in self.allowed_dispositions],
            "bass_relation": self.bass_relation.value,
            "interval_structure": self.interval_structure.value,
            "content_family_weights": dict(self.content_family_weights or {}),
            "source_family_weights": dict(self.source_family_weights or {}),
            "source_family_weights_by_gate": {str(k): dict(v) for k, v in dict(self.source_family_weights_by_gate or {}).items()},
            "harmonic_expansion_enabled": bool(self.harmonic_expansion_enabled),
            "color_policy_mode": self.color_policy_mode.value,
            "low_priority_degrees": list(self.low_priority_degrees),
            "low_priority_degree_penalty": self.low_priority_degree_penalty,
            "preferred_density": self.preferred_density,
            "min_density": self.min_density,
            "max_density": self.max_density,
            "register_low": self.register_low,
            "register_high": self.register_high,
            "left_hand_low": self.left_hand_low,
            "left_hand_high": self.left_hand_high,
            "right_hand_low": self.right_hand_low,
            "right_hand_high": self.right_hand_high,
            "top_voice_low": self.top_voice_low,
            "top_voice_high": self.top_voice_high,
            "comfort_register_low": self.comfort_register_low,
            "comfort_register_high": self.comfort_register_high,
            "max_voicing_span": self.max_voicing_span,
            "max_top_voice_leap": self.max_top_voice_leap,
            "voice_leading_weight": self.voice_leading_weight,
            "top_voice_weight": self.top_voice_weight,
            "register_guard_weight": self.register_guard_weight,
            "selector_temperature": self.selector_temperature,
            "selection_pool_size": self.selection_pool_size,
            "ensemble_role": self.ensemble_role.value,
            "metadata": dict(self.metadata or {}),
        }



def color_policy_mode_value(policy: "VoicingPolicy | None") -> str:
    """Return the normalized global VoicingColorPolicy mode string.

    This helper is intentionally density-agnostic.  3-note shell color,
    4-note rootless A/B, and future 5/6/7+ color recipes must all read the
    same global policy rather than implementing local gates.
    """

    if policy is None:
        return ColorPolicyMode.CHORD_SYMBOL_ONLY.value
    mode = getattr(policy, "color_policy_mode", ColorPolicyMode.CHORD_SYMBOL_ONLY)
    return getattr(mode, "value", str(mode))


def harmonic_expansion_allowed(policy: "VoicingPolicy | None", chord: Any | None = None) -> bool:
    """Return whether unnotated color may be added by style/LLM policy.

    This does *not* mean that chord-symbol-specified color is forbidden when
    false.  It only answers whether the engine may actively add color/tension
    that the chart did not write.  Use this common helper across all density
    families so the expansion gate remains global.
    """

    if policy is None:
        return False
    if bool(getattr(policy, "harmonic_expansion_enabled", False)):
        return True
    mode_value = color_policy_mode_value(policy)
    if mode_value == ColorPolicyMode.ALTERED_DOMINANT.value:
        return bool(getattr(chord, "is_dominant", False))
    return mode_value in {
        ColorPolicyMode.STYLE_SAFE_EXTENSIONS.value,
        ColorPolicyMode.RICH_REHARM_COLOR.value,
    }


def color_is_chord_symbol_specified(explicit_degrees: set[str] | tuple[str, ...] | list[str]) -> bool:
    """Return whether the chart itself supplied color material.

    This helper is small but named deliberately: explicit chart color is not
    harmonic expansion.  It is allowed in chord_symbol_only mode, but only for
    the degrees the chord symbol actually specified.
    """

    return bool(explicit_degrees)
