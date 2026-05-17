from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..disposition.method_lock import VoicingMethodLockMode
from ..disposition.method_weights import disposition_method_weight_spec_from_metadata
from ..disposition.models import (
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    coerce_open_projection_method,
)
from ..policy import ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy


class VoicingDispositionFamily(str, Enum):
    """High-level disposition/texture family used before local placement.

    This legacy texture-plan enum remains as the V2.1 compact-source vocabulary.
    v2_2_21 adds the broader ``VoicingTextureIntent`` / ``VoicingTextureState``
    runtime-planning contract below; do not confuse this compact-source family
    with the low-level ``DispositionFamily`` enum used by disposition projection.
    """

    COMPACT_VERTICAL_SOURCE = "compact_vertical_source"
    COMPACT_ROOTLESS = "compact_rootless"
    OPEN_ROOTLESS = "open_rootless"
    FOUNDATION_PROJECTION = "foundation_projection"
    SPREAD_BALLAD = "spread_ballad"
    QUARTAL_COLOR = "quartal_color"


class VoicingTextureScopeType(str, Enum):
    """Scope where one voicing texture language should remain coherent."""

    PHRASE = "phrase"
    SECTION = "section"
    CHORUS = "chorus"
    ARRANGEMENT_SEGMENT = "arrangement_segment"


class VoicingTextureCharacter(str, Enum):
    """LLM / arrangement-facing texture character vocabulary.

    These are semantic labels. They are intentionally not direct projection
    methods, and they should be resolved through style policy before runtime
    candidate generation consumes any concrete family/method constraints.
    """

    COMPACT = "compact"
    COMPACT_OPEN = "compact_open"
    OPEN_SWING = "open_swing"
    LIGHT_BOSSA = "light_bossa"
    WIDE_WARM_BALLAD = "wide_warm_ballad"
    ROOTED_SPREAD = "rooted_spread"
    THICK_ENDING = "thick_ending"


class VoicingTextureContinuity(str, Enum):
    STABLE = "stable"
    GRADUAL = "gradual"
    CONTRAST = "contrast"


class VoicingTextureMethodUniformity(str, Enum):
    LOOSE = "loose"
    PROGRESSION_LOCKED = "progression_locked"
    PHRASE_LOCKED = "phrase_locked"


class VoicingTextureFamilySwitchPolicy(str, Enum):
    FORBIDDEN = "forbidden"
    BOUNDARY_ONLY = "boundary_only"
    FREE = "free"


class VoicingTextureStateSource(str, Enum):
    STYLE_DEFAULT = "style_default"
    ARRANGEMENT_PLAN = "arrangement_plan"
    LLM_INTENT = "llm_intent"
    EXPLICIT_USER_REQUEST = "explicit_user_request"
    POLICY_METADATA = "policy_metadata"


DEFAULT_TEXTURE_SWITCH_BOUNDARIES: tuple[str, ...] = (
    "phrase_boundary",
    "section_boundary",
    "chorus_boundary",
    "cadence_or_ending",
    "arrangement_energy_change",
    "density_arc_change",
    "explicit_fill_or_gesture",
    "ensemble_context_change",
    "register_guard_rescue",
)


@dataclass(frozen=True)
class VoicingTextureIntent:
    """Human/LLM-facing voicing texture request.

    This is deliberately a semantic intent object rather than a projection
    instruction.  An LLM may ask for ``open_swing`` or ``wide_warm_ballad`` at a
    phrase/section/chorus scope, but the engine still resolves that through
    style defaults, ensemble context, and progression context before candidates
    see concrete ``DispositionFamily`` or projection-method weights.
    """

    scope_id: str = ""
    scope_type: VoicingTextureScopeType = VoicingTextureScopeType.PHRASE
    character: VoicingTextureCharacter = VoicingTextureCharacter.COMPACT_OPEN
    energy: float = 0.5
    density: float = 0.5
    width: float = 0.5
    continuity: VoicingTextureContinuity = VoicingTextureContinuity.STABLE
    method_uniformity: VoicingTextureMethodUniformity = VoicingTextureMethodUniformity.PROGRESSION_LOCKED
    allow_family_switch: VoicingTextureFamilySwitchPolicy = VoicingTextureFamilySwitchPolicy.BOUNDARY_ONLY
    preferred_family: DispositionFamily | None = None
    preferred_methods: tuple[str, ...] = ()
    avoid_families: tuple[DispositionFamily, ...] = ()
    avoid_methods: tuple[str, ...] = ()
    source: VoicingTextureStateSource = VoicingTextureStateSource.STYLE_DEFAULT

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": "voicing_texture_intent_llm_arrangement_semantic_contract_v2_2_21",
            "scope_id": self.scope_id,
            "scope_type": self.scope_type.value,
            "character": self.character.value,
            "energy": float(self.energy),
            "density": float(self.density),
            "width": float(self.width),
            "continuity": self.continuity.value,
            "method_uniformity": self.method_uniformity.value,
            "allow_family_switch": self.allow_family_switch.value,
            "preferred_family": self.preferred_family.value if self.preferred_family else None,
            "preferred_methods": list(self.preferred_methods),
            "avoid_families": [family.value for family in self.avoid_families],
            "avoid_methods": list(self.avoid_methods),
            "source": self.source.value,
            "llm_boundary": "LLM expresses semantic texture intent; engine resolves concrete family/method state.",
        }


@dataclass(frozen=True)
class VoicingTextureState:
    """Engine-resolved phrase/section/chorus voicing texture contract.

    v2_2_38 keeps this as the runtime contract and debug surface for
    phrase/section/chorus texture language.  It can expose planned contrast
    dimensions such as width/energy/density without forcing a projection method
    or replacing method lock.
    """

    scope_id: str = ""
    scope_type: VoicingTextureScopeType = VoicingTextureScopeType.PHRASE
    primary_family: DispositionFamily = DispositionFamily.CLOSED
    allowed_families: tuple[DispositionFamily, ...] = (DispositionFamily.CLOSED,)
    energy: float = 0.5
    density: float = 0.5
    width: float = 0.5
    contrast_role: str = "baseline"
    family_weights: dict[str, float] = field(default_factory=dict)
    open_method_weights: dict[str, float] = field(default_factory=dict)
    spread_method_weights: dict[str, float] = field(default_factory=dict)
    family_stickiness: float = 0.85
    method_stickiness: float = 0.65
    switch_allowed_at: tuple[str, ...] = DEFAULT_TEXTURE_SWITCH_BOUNDARIES
    family_switch_policy: VoicingTextureFamilySwitchPolicy = VoicingTextureFamilySwitchPolicy.BOUNDARY_ONLY
    progression_method_lock_mode: VoicingMethodLockMode = VoicingMethodLockMode.STRICT
    rescue_policy: str = "same_family_safe_method_then_closed_compact_then_audited_unlock"
    source: VoicingTextureStateSource = VoicingTextureStateSource.STYLE_DEFAULT
    intent_character: VoicingTextureCharacter | None = None

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": "voicing_texture_state_engine_resolved_contract_v2_2_21",
            "extension_contract": "voicing_texture_state_contrast_dimensions_v2_2_38",
            "scope_id": self.scope_id,
            "scope_type": self.scope_type.value,
            "primary_family": self.primary_family.value,
            "allowed_families": [family.value for family in self.allowed_families],
            "energy": float(self.energy),
            "density": float(self.density),
            "width": float(self.width),
            "contrast_role": self.contrast_role,
            "family_weights": dict(self.family_weights),
            "open_method_weights": dict(self.open_method_weights),
            "spread_method_weights": dict(self.spread_method_weights),
            "family_stickiness": float(self.family_stickiness),
            "method_stickiness": float(self.method_stickiness),
            "switch_allowed_at": list(self.switch_allowed_at),
            "family_switch_policy": self.family_switch_policy.value,
            "progression_method_lock_mode": self.progression_method_lock_mode.value,
            "rescue_policy": self.rescue_policy,
            "source": self.source.value,
            "intent_character": self.intent_character.value if self.intent_character else None,
            "architecture_boundary": "VoicingTextureState controls family continuity; method lock controls progression method continuity; Disposition Projection generates notes.",
        }


@dataclass(frozen=True)
class VoicingTexturePlan:
    """Phrase/section-level voicing texture contract.

    V2.1.14 formalizes the larger voicing pipeline:

        VoicingTexturePlan
        -> Content Recipe
        -> Canonical closed-position source
        -> Disposition/Orientation candidates
        -> Voice-leading scorer

    The plan is deliberately lightweight now.  It gives every candidate a stable
    texture family and inertia contract, without enabling broad drop2/open/spread
    randomization before those families are tuned.
    """

    primary_disposition_family: VoicingDispositionFamily
    allowed_disposition_families: tuple[VoicingDispositionFamily, ...]
    density: int
    root_support: str
    canonical_source_required: bool = True
    disposition_inertia: float = 0.35
    variation_scope: str = "phrase_or_section"
    change_triggers: tuple[str, ...] = (
        "section_start",
        "phrase_boundary",
        "chorus_change",
        "energy_or_density_arc_change",
        "llm_texture_intent",
        "fill_turnaround_or_ending",
        "register_guard_rescue",
    )
    source: str = "policy_default"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "primary_disposition_family": self.primary_disposition_family.value,
            "allowed_disposition_families": [family.value for family in self.allowed_disposition_families],
            "density": int(self.density),
            "root_support": str(self.root_support),
            "canonical_source_required": bool(self.canonical_source_required),
            "disposition_inertia": float(self.disposition_inertia),
            "variation_scope": self.variation_scope,
            "change_triggers": list(self.change_triggers),
            "source": self.source,
            "architecture_contract": "VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> DispositionGenerator -> VoiceLeadingScorer",
        }


def derive_voicing_texture_intent(
    policy: VoicingPolicy,
    *,
    scope_id: str = "",
    scope_type: VoicingTextureScopeType | str | None = None,
) -> VoicingTextureIntent:
    """Resolve the semantic texture intent from metadata/style defaults.

    The parser accepts either ``metadata["voicing_texture_intent"]`` or flat
    metadata keys.  It is intentionally permissive so a later arrangement/LLM
    adapter can pass a compact JSON object without needing a new planner.
    """

    metadata = dict(policy.metadata or {})
    nested = metadata.get("voicing_texture_intent") or metadata.get("texture_intent") or {}
    if not isinstance(nested, dict):
        nested = {"character": nested}
    values = {**metadata, **nested}

    source = _coerce_enum(
        VoicingTextureStateSource,
        values.get("source") or values.get("texture_intent_source"),
        _default_intent_source(values),
    )
    character = _coerce_enum(
        VoicingTextureCharacter,
        values.get("character") or values.get("texture_character") or values.get("default_texture"),
        _default_character_for_style(policy),
    )
    return VoicingTextureIntent(
        scope_id=str(values.get("scope_id") or values.get("texture_scope_id") or scope_id or ""),
        scope_type=_coerce_enum(VoicingTextureScopeType, values.get("scope_type") or scope_type, VoicingTextureScopeType.PHRASE),
        character=character,
        energy=_safe_float(values.get("energy"), default=0.5),
        density=_safe_float(values.get("density"), default=float(policy.preferred_density) / 7.0),
        width=_safe_float(values.get("width"), default=_default_width_for_policy(policy)),
        continuity=_coerce_enum(VoicingTextureContinuity, values.get("continuity"), VoicingTextureContinuity.STABLE),
        method_uniformity=_coerce_enum(
            VoicingTextureMethodUniformity,
            values.get("method_uniformity"),
            VoicingTextureMethodUniformity.PROGRESSION_LOCKED,
        ),
        allow_family_switch=_coerce_enum(
            VoicingTextureFamilySwitchPolicy,
            values.get("allow_family_switch") or values.get("family_switch_policy"),
            VoicingTextureFamilySwitchPolicy.BOUNDARY_ONLY,
        ),
        preferred_family=_coerce_disposition_family(values.get("preferred_family") or values.get("primary_family")),
        preferred_methods=_coerce_string_tuple(values.get("preferred_methods") or values.get("preferred_projection_methods")),
        avoid_families=_coerce_disposition_family_tuple(values.get("avoid_families")),
        avoid_methods=_coerce_string_tuple(values.get("avoid_methods")),
        source=source,
    )


def derive_voicing_texture_state(
    policy: VoicingPolicy,
    *,
    intent: VoicingTextureIntent | None = None,
    scope_id: str = "",
    scope_type: VoicingTextureScopeType | str | None = None,
) -> VoicingTextureState:
    """Resolve the engine-side texture state without changing selection.

    This function reuses existing policy metadata and disposition method weights.
    It is the v2_2_21 contract bridge between LLM/arrangement intent and the
    lower disposition projection layer.  Callers may attach its debug dict to
    candidates before any future pass starts consuming it for filtering/scoring.
    """

    metadata = dict(policy.metadata or {})
    resolved_intent = intent or derive_voicing_texture_intent(policy, scope_id=scope_id, scope_type=scope_type)
    weight_spec = disposition_method_weight_spec_from_metadata(metadata)

    preferred_family = resolved_intent.preferred_family or _family_from_policy(policy)
    explicit_primary = _coerce_disposition_family(
        metadata.get("primary_texture_family")
        or metadata.get("voicing_texture_primary_family")
        or metadata.get("primary_family")
    )
    primary = explicit_primary or preferred_family

    allowed = _coerce_disposition_family_tuple(
        metadata.get("allowed_texture_families")
        or metadata.get("voicing_texture_allowed_families")
        or metadata.get("allowed_families")
    )
    if not allowed:
        allowed = _allowed_families_from_policy(policy, primary)
    allowed = _apply_avoid_families(allowed, resolved_intent.avoid_families) or (primary,)
    if primary not in allowed:
        allowed = (primary, *allowed)

    return VoicingTextureState(
        scope_id=resolved_intent.scope_id or scope_id,
        scope_type=resolved_intent.scope_type,
        primary_family=primary,
        allowed_families=allowed,
        energy=float(resolved_intent.energy),
        density=float(resolved_intent.density),
        width=float(resolved_intent.width),
        contrast_role=str(metadata.get("voicing_texture_contrast_role") or metadata.get("texture_contrast_role") or "baseline"),
        family_weights=dict(weight_spec.family_weights),
        open_method_weights=_filter_avoided_methods(weight_spec.open_method_weights, resolved_intent.avoid_methods),
        spread_method_weights=_filter_avoided_methods(weight_spec.spread_method_weights, resolved_intent.avoid_methods),
        family_stickiness=_safe_float(metadata.get("family_stickiness"), default=_default_family_stickiness(resolved_intent)),
        method_stickiness=_safe_float(metadata.get("method_stickiness"), default=_default_method_stickiness(resolved_intent)),
        switch_allowed_at=_coerce_string_tuple(metadata.get("switch_allowed_at") or metadata.get("texture_switch_allowed_at"))
        or DEFAULT_TEXTURE_SWITCH_BOUNDARIES,
        family_switch_policy=resolved_intent.allow_family_switch,
        progression_method_lock_mode=_coerce_enum(
            VoicingMethodLockMode,
            metadata.get("progression_method_lock_mode") or metadata.get("voicing_method_lock_mode"),
            _method_lock_mode_from_uniformity(resolved_intent.method_uniformity),
        ),
        source=_coerce_enum(
            VoicingTextureStateSource,
            metadata.get("voicing_texture_state_source") or metadata.get("texture_state_source"),
            resolved_intent.source,
        ),
        intent_character=resolved_intent.character,
    )


def derive_voicing_texture_plan(
    policy: VoicingPolicy,
    *,
    content_family: ContentFamily | None = None,
) -> VoicingTexturePlan:
    """Derive the current stable disposition family from policy/context.

    Metadata may explicitly provide ``primary_disposition_family`` when an
    arrangement/LLM layer wants a phrase-level texture.  Otherwise, V2.1.14 uses
    conservative defaults: rootless jazz voicings stay compact-rootless, spread
    requests stay spread-ballad, and root-required/rooted layouts become
    foundation-projection.  This prevents canonical-source derivation from
    becoming per-chord random disposition switching.
    """

    metadata = dict(policy.metadata or {})
    explicit = metadata.get("primary_disposition_family") or metadata.get("voicing_disposition_family")
    if explicit:
        try:
            primary = VoicingDispositionFamily(str(explicit))
        except ValueError:
            primary = _default_family(policy, content_family)
        source = "policy_metadata"
    else:
        primary = _default_family(policy, content_family)
        source = "policy_default"

    allowed = metadata.get("allowed_disposition_families")
    allowed_families: tuple[VoicingDispositionFamily, ...]
    if allowed:
        values = allowed if isinstance(allowed, (list, tuple)) else (allowed,)
        parsed: list[VoicingDispositionFamily] = []
        for value in values:
            try:
                parsed.append(VoicingDispositionFamily(str(value)))
            except ValueError:
                continue
        allowed_families = tuple(parsed) or (primary,)
    else:
        allowed_families = (primary,)

    return VoicingTexturePlan(
        primary_disposition_family=primary,
        allowed_disposition_families=allowed_families,
        density=int(policy.preferred_density),
        root_support=getattr(policy.root_support, "value", str(policy.root_support)),
        disposition_inertia=float(metadata.get("disposition_inertia", 0.35)),
        variation_scope=str(metadata.get("variation_scope", "phrase_or_section")),
        source=source,
    )


def _default_family(policy: VoicingPolicy, content_family: ContentFamily | None) -> VoicingDispositionFamily:
    if content_family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}:
        return VoicingDispositionFamily.COMPACT_ROOTLESS
    if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED, RootSupportPolicy.ROOT_PREFERRED}:
        return VoicingDispositionFamily.FOUNDATION_PROJECTION
    if policy.preferred_disposition in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD}:
        return VoicingDispositionFamily.SPREAD_BALLAD
    if policy.preferred_disposition == Disposition.LEFT_ROOT_RIGHT_ROOTLESS:
        return VoicingDispositionFamily.FOUNDATION_PROJECTION
    if policy.interval_structure.value == "quartal":
        return VoicingDispositionFamily.QUARTAL_COLOR
    return VoicingDispositionFamily.COMPACT_VERTICAL_SOURCE


def _default_intent_source(metadata: dict[str, Any]) -> VoicingTextureStateSource:
    source = str(metadata.get("source") or metadata.get("texture_intent_source") or "").strip().lower()
    if source:
        return _coerce_enum(VoicingTextureStateSource, source, VoicingTextureStateSource.POLICY_METADATA)
    if "voicing_texture_intent" in metadata or "texture_intent" in metadata:
        return VoicingTextureStateSource.POLICY_METADATA
    return VoicingTextureStateSource.STYLE_DEFAULT


def _default_character_for_style(policy: VoicingPolicy) -> VoicingTextureCharacter:
    style = str((policy.metadata or {}).get("style") or "").strip().lower()
    if style == "medium_swing":
        return VoicingTextureCharacter.OPEN_SWING
    if style == "bossa_nova":
        return VoicingTextureCharacter.LIGHT_BOSSA
    if style == "jazz_ballad":
        return VoicingTextureCharacter.WIDE_WARM_BALLAD
    if policy.preferred_disposition in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD}:
        return VoicingTextureCharacter.ROOTED_SPREAD
    if policy.preferred_disposition == Disposition.OPEN:
        return VoicingTextureCharacter.COMPACT_OPEN
    return VoicingTextureCharacter.COMPACT


def _default_width_for_policy(policy: VoicingPolicy) -> float:
    if policy.preferred_disposition in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD, Disposition.LEFT_ROOT_RIGHT_CHORD, Disposition.LEFT_ROOT_RIGHT_ROOTLESS}:
        return 0.8
    if policy.preferred_disposition == Disposition.OPEN:
        return 0.65
    return 0.35


def _family_from_policy(policy: VoicingPolicy) -> DispositionFamily:
    disposition = policy.preferred_disposition
    if disposition == Disposition.OPEN:
        return DispositionFamily.OPEN
    if disposition in {
        Disposition.SPREAD,
        Disposition.TWO_HAND_SPREAD,
        Disposition.LEFT_ROOT_RIGHT_CHORD,
        Disposition.LEFT_ROOT_RIGHT_ROOTLESS,
        Disposition.OPEN_ROOT_10TH,
    }:
        return DispositionFamily.SPREAD
    return DispositionFamily.CLOSED


def _allowed_families_from_policy(policy: VoicingPolicy, primary: DispositionFamily) -> tuple[DispositionFamily, ...]:
    values: list[DispositionFamily] = []
    for disposition in policy.effective_dispositions:
        if disposition == Disposition.OPEN:
            family = DispositionFamily.OPEN
        elif disposition in {
            Disposition.SPREAD,
            Disposition.TWO_HAND_SPREAD,
            Disposition.LEFT_ROOT_RIGHT_CHORD,
            Disposition.LEFT_ROOT_RIGHT_ROOTLESS,
            Disposition.OPEN_ROOT_10TH,
        }:
            family = DispositionFamily.SPREAD
        else:
            family = DispositionFamily.CLOSED
        if family not in values:
            values.append(family)
    if primary not in values:
        values.insert(0, primary)
    return tuple(values) or (primary,)


def _default_family_stickiness(intent: VoicingTextureIntent) -> float:
    if intent.allow_family_switch == VoicingTextureFamilySwitchPolicy.FORBIDDEN:
        return 0.97
    if intent.allow_family_switch == VoicingTextureFamilySwitchPolicy.FREE:
        return 0.45
    if intent.continuity == VoicingTextureContinuity.CONTRAST:
        return 0.70
    return 0.88


def _default_method_stickiness(intent: VoicingTextureIntent) -> float:
    if intent.method_uniformity == VoicingTextureMethodUniformity.PHRASE_LOCKED:
        return 0.92
    if intent.method_uniformity == VoicingTextureMethodUniformity.LOOSE:
        return 0.45
    return 0.68


def _method_lock_mode_from_uniformity(uniformity: VoicingTextureMethodUniformity) -> VoicingMethodLockMode:
    if uniformity == VoicingTextureMethodUniformity.LOOSE:
        return VoicingMethodLockMode.PREFER
    return VoicingMethodLockMode.STRICT


def _filter_avoided_methods(weights: dict[str, float], avoid_methods: tuple[str, ...]) -> dict[str, float]:
    if not avoid_methods:
        return dict(weights)
    avoided = {str(method).strip().lower().replace("-", "_") for method in avoid_methods}
    out = {}
    for method, weight in weights.items():
        if str(method).strip().lower().replace("-", "_") in avoided:
            continue
        out[method] = float(weight)
    return out


def _apply_avoid_families(
    allowed: tuple[DispositionFamily, ...],
    avoid_families: tuple[DispositionFamily, ...],
) -> tuple[DispositionFamily, ...]:
    if not avoid_families:
        return allowed
    return tuple(family for family in allowed if family not in avoid_families)


def _coerce_disposition_family(value: Any) -> DispositionFamily | None:
    if isinstance(value, DispositionFamily):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return None
    aliases = {
        "compact": DispositionFamily.CLOSED,
        "closed": DispositionFamily.CLOSED,
        "compact_open": DispositionFamily.OPEN,
        "open_swing": DispositionFamily.OPEN,
        "open": DispositionFamily.OPEN,
        "drop": DispositionFamily.OPEN,
        "wide": DispositionFamily.SPREAD,
        "wide_warm": DispositionFamily.SPREAD,
        "wide_warm_ballad": DispositionFamily.SPREAD,
        "rooted_spread": DispositionFamily.SPREAD,
        "spread": DispositionFamily.SPREAD,
        "foundation_projection": DispositionFamily.SPREAD,
    }
    if text in aliases:
        return aliases[text]
    try:
        return DispositionFamily(text)
    except ValueError:
        return None


def _coerce_disposition_family_tuple(value: Any) -> tuple[DispositionFamily, ...]:
    if value is None:
        return ()
    values: list[Any]
    if isinstance(value, str):
        values = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[DispositionFamily] = []
    for item in values:
        family = _coerce_disposition_family(item)
        if family is not None and family not in out:
            out.append(family)
    return tuple(out)


def _coerce_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.replace(";", ",").split(",") if part.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _coerce_enum(enum_type: type[Enum], value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return default
    aliases = {
        "false": "forbidden",
        "no": "forbidden",
        "none": "forbidden",
        "true": "boundary_only",
        "yes": "boundary_only",
        "boundary": "boundary_only",
        "phrase": "phrase",
        "section": "section",
        "chorus": "chorus",
        "llm": "llm_intent",
        "user": "explicit_user_request",
    }
    text = aliases.get(text, text)
    try:
        return enum_type(text)
    except ValueError:
        return default


def _safe_float(value: Any, *, default: float) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        out = default
    return min(1.0, max(0.0, out))


# Explicit references keep the imported method enums visible to static greps and
# future adapters without making v2_2_21 consume them for runtime behavior.
_OPEN_METHOD_ENUM_FOR_TEXTURE_STATE_CONTRACT = OpenProjectionMethod
_SPREAD_METHOD_ENUM_FOR_TEXTURE_STATE_CONTRACT = SpreadProjectionMethod
_COERCE_OPEN_METHOD_FOR_TEXTURE_STATE_CONTRACT = coerce_open_projection_method
