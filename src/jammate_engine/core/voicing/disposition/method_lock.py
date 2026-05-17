from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from jammate_engine.core.harmony.harmonic_context import FunctionalMotion, HarmonicContext, classify_functional_motion

from .models import (
    ClosedProjectionMethod,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    coerce_open_projection_method,
)


class VoicingMethodLockScope(str, Enum):
    """Logical scope where one voicing projection method should stay stable.

    This is a planning contract, not a chord-region candidate generator.  The
    eventual progression/phrase planner should choose the scope and the first
    region's selected family/method, then pass the locked method to later regions.
    """

    CHORD_REGION = "chord_region"
    PROGRESSION = "progression"
    PHRASE = "phrase"
    SECTION = "section"
    ARRANGEMENT_SEGMENT = "arrangement_segment"


class VoicingMethodLockPattern(str, Enum):
    """Common idiomatic scopes that benefit from stable voicing method language."""

    II_V = "ii_v"
    V_I = "v_i"
    II_V_I = "ii_v_i"
    TURNAROUND = "turnaround"
    ARRANGED_PHRASE = "arranged_phrase"
    SECTION = "section"
    EXPLICIT_SCOPE = "explicit_scope"


class VoicingMethodLockMode(str, Enum):
    """How strongly a planner should preserve the locked method."""

    OFF = "off"
    PREFER = "prefer"
    STRICT = "strict"


class VoicingMethodLockRescueAction(str, Enum):
    """Planning-only rescue actions for a strict method lock with no candidates.

    These actions document the future fallback order.  v2_2_14 does not run
    automatic rescue or change default style output; it only exposes an audit
    contract so the eventual runtime can break a lock for explicit reasons.
    """

    NONE = "none"
    KEEP_LOCKED_CANDIDATE = "keep_locked_candidate"
    TRY_SAME_FAMILY_SAFE_METHOD = "try_same_family_safe_method"
    TRY_CLOSED_COMPACT = "try_closed_compact"
    UNLOCK_CURRENT_REGION_WITH_AUDIT = "unlock_current_region_with_audit"


DEFAULT_METHOD_LOCK_BREAK_TRIGGERS: tuple[str, ...] = (
    "phrase_ending",
    "section_boundary",
    "chorus_change",
    "arrangement_intent_change",
    "density_arc_change",
    "gesture_driven_revoice",
    "register_guard_rescue",
    "ensemble_context_change",
)




@dataclass(frozen=True)
class VoicingMethodLockScopePlan:
    """HarmonicContext-backed plan for a method-lock scope.

    This is an adapter contract, not a new progression recognizer.  It consumes
    the existing ``core/harmony/harmonic_context.py`` FunctionalMotion labels
    and converts them into a voicing-method lock scope that can later be seeded
    with the first region's selected DispositionFamily + ProjectionMethod.
    """

    enabled: bool = False
    scope: VoicingMethodLockScope = VoicingMethodLockScope.CHORD_REGION
    pattern: VoicingMethodLockPattern = VoicingMethodLockPattern.EXPLICIT_SCOPE
    mode: VoicingMethodLockMode = VoicingMethodLockMode.OFF
    scope_id: str = ""
    region_ids: tuple[str, ...] = ()
    seed_region_id: str = ""
    current_region_id: str = ""
    source: str = "none"
    target_family: DispositionFamily | None = None
    target_closed_method: ClosedProjectionMethod | None = None
    target_open_method: OpenProjectionMethod | None = None
    target_spread_method: SpreadProjectionMethod | None = None
    harmonic_window_type: str = "none"
    previous_to_current_type: str = "none"
    current_to_next_type: str = "none"
    functional_motion_tags: tuple[str, ...] = ()
    break_triggers: tuple[str, ...] = DEFAULT_METHOD_LOCK_BREAK_TRIGGERS

    @property
    def target_method_value(self) -> str:
        method = self.target_closed_method or self.target_open_method or self.target_spread_method
        return method.value if method is not None else "unresolved_seed_method"

    @property
    def needs_seed_method(self) -> bool:
        return self.enabled and self.target_family is None

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": "harmonic_context_backed_method_lock_scope_adapter_v2_2_14",
            "enabled": bool(self.enabled),
            "scope": self.scope.value,
            "pattern": self.pattern.value,
            "mode": self.mode.value,
            "scope_id": self.scope_id,
            "region_ids": list(self.region_ids),
            "seed_region_id": self.seed_region_id,
            "current_region_id": self.current_region_id,
            "source": self.source,
            "target_family": self.target_family.value if self.target_family else None,
            "target_method": self.target_method_value,
            "target_closed_method": self.target_closed_method.value if self.target_closed_method else None,
            "target_open_method": self.target_open_method.value if self.target_open_method else None,
            "target_spread_method": self.target_spread_method.value if self.target_spread_method else None,
            "needs_seed_method": self.needs_seed_method,
            "harmonic_window_type": self.harmonic_window_type,
            "previous_to_current_type": self.previous_to_current_type,
            "current_to_next_type": self.current_to_next_type,
            "functional_motion_tags": list(self.functional_motion_tags),
            "break_triggers": list(self.break_triggers),
        }


@dataclass(frozen=True)
class VoicingMethodLockSeedFollowPlan:
    """Runtime wiring plan for seed-then-follow method locking.

    This is not a progression recognizer. It consumes an existing
    ``VoicingMethodLockScopePlan`` plus the selected seed candidate metadata,
    then emits the strict follow-region metadata needed by the existing
    method-lock runtime filtering path.
    """

    enabled: bool = False
    scope: VoicingMethodLockScope = VoicingMethodLockScope.CHORD_REGION
    pattern: VoicingMethodLockPattern = VoicingMethodLockPattern.EXPLICIT_SCOPE
    mode: VoicingMethodLockMode = VoicingMethodLockMode.OFF
    scope_id: str = ""
    region_ids: tuple[str, ...] = ()
    seed_region_id: str = ""
    follow_region_ids: tuple[str, ...] = ()
    current_region_id: str = ""
    target_family: DispositionFamily | None = None
    target_closed_method: ClosedProjectionMethod | None = None
    target_open_method: OpenProjectionMethod | None = None
    target_spread_method: SpreadProjectionMethod | None = None
    locked_from_region_id: str = ""
    runtime_filtering_enabled: bool = False
    source: str = "none"
    reason: str = "disabled"

    @property
    def target_method_value(self) -> str:
        method = self.target_closed_method or self.target_open_method or self.target_spread_method
        return method.value if method is not None else "unresolved_seed_method"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": "method_lock_seed_then_follow_runtime_wiring_v2_2_14",
            "enabled": bool(self.enabled),
            "scope": self.scope.value,
            "pattern": self.pattern.value,
            "mode": self.mode.value,
            "scope_id": self.scope_id,
            "region_ids": list(self.region_ids),
            "seed_region_id": self.seed_region_id,
            "follow_region_ids": list(self.follow_region_ids),
            "current_region_id": self.current_region_id,
            "target_family": self.target_family.value if self.target_family else None,
            "target_method": self.target_method_value,
            "target_closed_method": self.target_closed_method.value if self.target_closed_method else None,
            "target_open_method": self.target_open_method.value if self.target_open_method else None,
            "target_spread_method": self.target_spread_method.value if self.target_spread_method else None,
            "locked_from_region_id": self.locked_from_region_id,
            "runtime_filtering_enabled": bool(self.runtime_filtering_enabled),
            "source": self.source,
            "reason": self.reason,
        }


def method_lock_scope_plan_from_harmonic_context(
    context: HarmonicContext,
    *,
    previous_region_id: str = "previous",
    current_region_id: str = "current",
    next_region_id: str = "next",
    scope_id: str = "",
    mode: VoicingMethodLockMode | str | None = None,
    source: str = "harmonic_context_adapter",
) -> VoicingMethodLockScopePlan:
    """Adapt existing HarmonicContext functional motion into a lock scope plan.

    The function deliberately reuses ``HarmonicContext.functional_motion``.  It
    must not duplicate ii-V / V-I / ii-V-I recognition rules in voicing.
    """

    return method_lock_scope_plan_from_functional_motion(
        context.functional_motion,
        previous_region_id=previous_region_id,
        current_region_id=current_region_id,
        next_region_id=next_region_id,
        scope_id=scope_id,
        mode=mode,
        source=source,
    )


def method_lock_scope_plan_from_symbols(
    *,
    chord_symbol: str,
    previous_chord_symbol: str | None = None,
    next_chord_symbol: str | None = None,
    previous_region_id: str = "previous",
    current_region_id: str = "current",
    next_region_id: str = "next",
    scope_id: str = "",
    mode: VoicingMethodLockMode | str | None = None,
    source: str = "harmonic_context_adapter",
) -> VoicingMethodLockScopePlan:
    """Convenience wrapper that uses the existing harmony classifier."""

    motion = classify_functional_motion(
        chord_symbol=chord_symbol,
        previous_chord_symbol=previous_chord_symbol,
        next_chord_symbol=next_chord_symbol,
    )
    return method_lock_scope_plan_from_functional_motion(
        motion,
        previous_region_id=previous_region_id,
        current_region_id=current_region_id,
        next_region_id=next_region_id,
        scope_id=scope_id,
        mode=mode,
        source=source,
    )


def method_lock_scope_plan_from_functional_motion(
    motion: FunctionalMotion,
    *,
    previous_region_id: str = "previous",
    current_region_id: str = "current",
    next_region_id: str = "next",
    scope_id: str = "",
    mode: VoicingMethodLockMode | str | None = None,
    source: str = "harmonic_context_adapter",
) -> VoicingMethodLockScopePlan:
    """Create a voicing-method lock scope from existing FunctionalMotion tags."""

    resolved_mode = _coerce_enum(VoicingMethodLockMode, mode, VoicingMethodLockMode.STRICT)
    pattern: VoicingMethodLockPattern | None = None
    region_ids: tuple[str, ...] = ()
    seed_region_id = ""

    # Specific three-chord windows win over pair-level interpretations.  This
    # avoids splitting Dm7-G7-Cmaj7 into ii-V and V-I scopes.
    if motion.is_ii_v_i:
        pattern = VoicingMethodLockPattern.II_V_I
        region_ids = tuple(item for item in (previous_region_id, current_region_id, next_region_id) if item)
        seed_region_id = previous_region_id or current_region_id
    elif motion.is_turnaround_like:
        pattern = VoicingMethodLockPattern.TURNAROUND
        region_ids = tuple(item for item in (previous_region_id, current_region_id, next_region_id) if item)
        seed_region_id = previous_region_id or current_region_id
    elif motion.is_current_next_ii_v:
        pattern = VoicingMethodLockPattern.II_V
        region_ids = tuple(item for item in (current_region_id, next_region_id) if item)
        seed_region_id = current_region_id
    elif motion.is_current_next_v_i:
        pattern = VoicingMethodLockPattern.V_I
        region_ids = tuple(item for item in (current_region_id, next_region_id) if item)
        seed_region_id = current_region_id

    if pattern is None or not region_ids:
        return VoicingMethodLockScopePlan(
            enabled=False,
            mode=VoicingMethodLockMode.OFF,
            current_region_id=current_region_id,
            source=source,
            harmonic_window_type=motion.window_type,
            previous_to_current_type=motion.previous_to_current_type,
            current_to_next_type=motion.current_to_next_type,
            functional_motion_tags=motion.tags,
        )

    resolved_scope_id = scope_id or _default_method_lock_scope_id(pattern, region_ids)
    return VoicingMethodLockScopePlan(
        enabled=True,
        scope=VoicingMethodLockScope.PROGRESSION,
        pattern=pattern,
        mode=resolved_mode,
        scope_id=resolved_scope_id,
        region_ids=region_ids,
        seed_region_id=seed_region_id,
        current_region_id=current_region_id,
        source=source,
        harmonic_window_type=motion.window_type,
        previous_to_current_type=motion.previous_to_current_type,
        current_to_next_type=motion.current_to_next_type,
        functional_motion_tags=motion.tags,
    )


def method_lock_spec_from_scope_plan(
    plan: VoicingMethodLockScopePlan,
    *,
    family: DispositionFamily | str | None = None,
    closed_method: ClosedProjectionMethod | str | None = None,
    open_method: OpenProjectionMethod | str | None = None,
    spread_method: SpreadProjectionMethod | str | None = None,
    locked_from_region_id: str | None = None,
    source: str = "scope_plan_seed",
) -> VoicingMethodLockSpec:
    """Seed a runtime lock spec from a scope plan after the seed region picks a method."""

    resolved_family = _coerce_family(family) or plan.target_family
    resolved_closed = _coerce_closed_method(closed_method) or plan.target_closed_method
    resolved_open = coerce_open_projection_method(open_method) or plan.target_open_method
    resolved_spread = _coerce_spread_method(spread_method) or plan.target_spread_method
    return VoicingMethodLockSpec(
        enabled=bool(plan.enabled and resolved_family is not None),
        scope=plan.scope,
        pattern=plan.pattern,
        mode=plan.mode if plan.enabled else VoicingMethodLockMode.OFF,
        scope_id=plan.scope_id,
        locked_from_region_id=locked_from_region_id or plan.seed_region_id,
        family=resolved_family,
        closed_method=resolved_closed,
        open_method=resolved_open,
        spread_method=resolved_spread,
        source=source,
        break_triggers=plan.break_triggers,
    )


def method_lock_seed_follow_plan_from_seed_candidate_metadata(
    plan: VoicingMethodLockScopePlan,
    seed_candidate_metadata: dict[str, Any] | None,
    *,
    current_region_id: str = "",
    runtime_filtering_enabled: bool = True,
    source: str = "scope_plan_seed_candidate",
) -> VoicingMethodLockSeedFollowPlan:
    """Create a follow-region runtime wiring plan from a selected seed candidate.

    The selected seed candidate is expected to expose the normalized projection
    metadata already produced by ``project_source_to_disposition``. This helper
    intentionally reuses that existing metadata rather than re-selecting or
    re-recognizing the progression.
    """

    metadata = dict(seed_candidate_metadata or {})
    if not plan.enabled:
        return VoicingMethodLockSeedFollowPlan(source=source, reason="scope_plan_disabled")

    family = _coerce_family(metadata.get("disposition_projection_family")) or plan.target_family
    method_value = metadata.get("disposition_projection_method")
    closed_method: ClosedProjectionMethod | None = None
    open_method: OpenProjectionMethod | None = None
    spread_method: SpreadProjectionMethod | None = None
    if family == DispositionFamily.CLOSED:
        closed_method = _coerce_closed_method(method_value) or plan.target_closed_method
    elif family == DispositionFamily.OPEN:
        open_method = coerce_open_projection_method(method_value) or plan.target_open_method
    elif family == DispositionFamily.SPREAD:
        spread_method = _coerce_spread_method(method_value) or plan.target_spread_method

    follow_region_ids = tuple(region_id for region_id in plan.region_ids if region_id and region_id != plan.seed_region_id)
    resolved_current_region_id = str(current_region_id or (follow_region_ids[0] if follow_region_ids else ""))
    enabled = bool(family is not None and (closed_method or open_method or spread_method) and follow_region_ids)
    reason = "seed_candidate_projection_resolved" if enabled else "seed_candidate_missing_projection_method"
    return VoicingMethodLockSeedFollowPlan(
        enabled=enabled,
        scope=plan.scope,
        pattern=plan.pattern,
        mode=plan.mode if enabled else VoicingMethodLockMode.OFF,
        scope_id=plan.scope_id,
        region_ids=plan.region_ids,
        seed_region_id=plan.seed_region_id,
        follow_region_ids=follow_region_ids,
        current_region_id=resolved_current_region_id,
        target_family=family,
        target_closed_method=closed_method,
        target_open_method=open_method,
        target_spread_method=spread_method,
        locked_from_region_id=plan.seed_region_id,
        runtime_filtering_enabled=bool(runtime_filtering_enabled and enabled and plan.mode == VoicingMethodLockMode.STRICT),
        source=source,
        reason=reason,
    )


def method_lock_spec_from_seed_follow_plan(plan: VoicingMethodLockSeedFollowPlan) -> VoicingMethodLockSpec:
    """Convert a seed-follow plan into the strict runtime lock spec used by candidates."""

    return VoicingMethodLockSpec(
        enabled=bool(plan.enabled and plan.target_family is not None),
        scope=plan.scope,
        pattern=plan.pattern,
        mode=plan.mode if plan.enabled else VoicingMethodLockMode.OFF,
        scope_id=plan.scope_id,
        locked_from_region_id=plan.locked_from_region_id,
        family=plan.target_family,
        closed_method=plan.target_closed_method,
        open_method=plan.target_open_method,
        spread_method=plan.target_spread_method,
        source="seed_follow_runtime_wiring" if plan.enabled else "none",
    )


def method_lock_follow_metadata_from_seed_candidate(
    plan: VoicingMethodLockScopePlan,
    seed_candidate_metadata: dict[str, Any] | None,
    *,
    current_region_id: str = "",
    runtime_filtering_enabled: bool = True,
) -> dict[str, Any]:
    """Return metadata for a follow region after the seed region selected a method.

    This is the v2_2_14 seed-then-follow wiring bridge. It does not run by
    default; callers/tests must explicitly create and attach the returned
    metadata to follow-region policies.
    """

    follow_plan = method_lock_seed_follow_plan_from_seed_candidate_metadata(
        plan,
        seed_candidate_metadata,
        current_region_id=current_region_id,
        runtime_filtering_enabled=runtime_filtering_enabled,
    )
    spec = method_lock_spec_from_seed_follow_plan(follow_plan)
    debug = follow_plan.to_debug_dict()
    metadata: dict[str, Any] = {
        "voicing_method_lock_scope_runtime_wiring": debug,
        "voicing_method_lock_scope_runtime_wiring_enabled": bool(follow_plan.enabled),
        "voicing_method_lock_scope_runtime_wiring_source": follow_plan.source,
        "voicing_method_lock_scope_runtime_wiring_reason": follow_plan.reason,
        "voicing_method_lock_scope_runtime_wiring_current_region_id": follow_plan.current_region_id,
        "voicing_method_lock_scope_runtime_wiring_seed_region_id": follow_plan.seed_region_id,
        "voicing_method_lock_scope_runtime_wiring_follow_region_ids": list(follow_plan.follow_region_ids),
        "voicing_method_lock": spec.to_debug_dict(),
    }
    if follow_plan.runtime_filtering_enabled:
        metadata["voicing_method_lock"]["runtime_filtering_enabled"] = True
        metadata["method_lock_runtime_filtering_enabled"] = True
    return metadata


def method_lock_scope_runtime_wiring_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Expose seed-then-follow wiring debug metadata on generated candidates."""

    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock_scope_runtime_wiring") or {}
    if not isinstance(nested, dict):
        nested = {}
    return {
        "contract": nested.get("contract") or "method_lock_seed_then_follow_runtime_wiring_v2_2_14",
        "enabled": bool(metadata.get("voicing_method_lock_scope_runtime_wiring_enabled") or nested.get("enabled") or False),
        "scope": nested.get("scope") or "chord_region",
        "pattern": nested.get("pattern") or "explicit_scope",
        "scope_id": nested.get("scope_id") or "",
        "seed_region_id": nested.get("seed_region_id") or metadata.get("voicing_method_lock_scope_runtime_wiring_seed_region_id") or "",
        "follow_region_ids": list(nested.get("follow_region_ids") or metadata.get("voicing_method_lock_scope_runtime_wiring_follow_region_ids") or []),
        "current_region_id": nested.get("current_region_id") or metadata.get("voicing_method_lock_scope_runtime_wiring_current_region_id") or "",
        "target_family": nested.get("target_family"),
        "target_method": nested.get("target_method"),
        "runtime_filtering_enabled": bool(nested.get("runtime_filtering_enabled") or metadata.get("method_lock_runtime_filtering_enabled") or False),
        "source": nested.get("source") or metadata.get("voicing_method_lock_scope_runtime_wiring_source") or "none",
        "reason": nested.get("reason") or metadata.get("voicing_method_lock_scope_runtime_wiring_reason") or "none",
    }


def method_lock_scope_plan_from_metadata(
    metadata: dict[str, Any] | None,
    *,
    current_symbol: str | None = None,
) -> VoicingMethodLockScopePlan:
    """Optional metadata bridge for future arrangement/LLM adapters.

    This does not affect candidate filtering by itself.  It only exposes the
    deterministic HarmonicContext-backed scope plan for audits and future
    progression-aware runtime wiring.
    """

    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock_scope") or metadata.get("progression_voicing_method_lock_scope") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}
    enabled = _coerce_bool(
        values.get("auto_method_lock_scope_enabled")
        or values.get("method_lock_scope_adapter_enabled")
        or values.get("harmonic_context_method_lock_scope_enabled"),
        default=False,
    )
    if not enabled:
        return VoicingMethodLockScopePlan()

    chord_symbol = str(values.get("chord_symbol") or current_symbol or "").strip()
    if not chord_symbol:
        return VoicingMethodLockScopePlan(source="metadata_missing_chord_symbol")

    return method_lock_scope_plan_from_symbols(
        chord_symbol=chord_symbol,
        previous_chord_symbol=values.get("previous_chord_symbol"),
        next_chord_symbol=values.get("next_chord_symbol"),
        previous_region_id=str(values.get("previous_region_id") or "previous"),
        current_region_id=str(values.get("current_region_id") or "current"),
        next_region_id=str(values.get("next_region_id") or "next"),
        scope_id=str(values.get("scope_id") or ""),
        mode=values.get("mode") or values.get("lock_mode"),
        source="metadata_harmonic_context_adapter",
    )


def _default_method_lock_scope_id(pattern: VoicingMethodLockPattern, region_ids: tuple[str, ...]) -> str:
    safe_regions = "_".join(str(region_id).replace(" ", "_") for region_id in region_ids if region_id)
    return f"{pattern.value}:{safe_regions}" if safe_regions else pattern.value


@dataclass(frozen=True)
class VoicingMethodLockSpec:
    """Phrase/progression-level disposition projection method lock contract.

    The lock records a chosen ``DispositionFamily + ProjectionMethod`` for a
    coherent idiomatic scope such as ii-V, V-I, ii-V-I, turnaround, or an
    arranged phrase/section.  v2_2_8 only exposes the contract and debug fields;
    it does not force candidate filtering yet, so default musical output remains
    unchanged.
    """

    enabled: bool = False
    scope: VoicingMethodLockScope = VoicingMethodLockScope.CHORD_REGION
    pattern: VoicingMethodLockPattern = VoicingMethodLockPattern.EXPLICIT_SCOPE
    mode: VoicingMethodLockMode = VoicingMethodLockMode.OFF
    scope_id: str = ""
    locked_from_region_id: str = ""
    family: DispositionFamily | None = None
    closed_method: ClosedProjectionMethod | None = None
    open_method: OpenProjectionMethod | None = None
    spread_method: SpreadProjectionMethod | None = None
    source: str = "none"
    break_triggers: tuple[str, ...] = DEFAULT_METHOD_LOCK_BREAK_TRIGGERS

    @property
    def method_value(self) -> str:
        method = self.closed_method or self.open_method or self.spread_method
        return method.value if method is not None else "unspecified"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "scope": self.scope.value,
            "pattern": self.pattern.value,
            "mode": self.mode.value,
            "scope_id": self.scope_id,
            "locked_from_region_id": self.locked_from_region_id,
            "family": self.family.value if self.family else None,
            "method": self.method_value,
            "closed_method": self.closed_method.value if self.closed_method else None,
            "open_method": self.open_method.value if self.open_method else None,
            "spread_method": self.spread_method.value if self.spread_method else None,
            "source": self.source,
            "break_triggers": list(self.break_triggers),
            "contract": "progression_phrase_voicing_method_lock_planning_only",
        }


@dataclass(frozen=True)
class VoicingMethodLockRescuePlan:
    """Planning-only rescue contract for strict method-lock failures.

    A real method lock is a hard binding.  Rescue is therefore not a soft
    weighting rule; it is an explicit, auditable exception path for cases where
    the locked family/method yields no legal candidates.  v2_2_14 only records
    the plan and recommended fallback order.  Automatic fallback remains a
    later implementation step.
    """

    enabled: bool = False
    rescue_needed: bool = False
    mode: VoicingMethodLockMode = VoicingMethodLockMode.OFF
    scope: VoicingMethodLockScope = VoicingMethodLockScope.CHORD_REGION
    pattern: VoicingMethodLockPattern = VoicingMethodLockPattern.EXPLICIT_SCOPE
    locked_family: str = ""
    locked_method: str = ""
    kept_candidate_count: int = 0
    filtered_candidate_count: int = 0
    runtime_filtering_enabled: bool = False
    fallback_returned: bool = False
    recommended_actions: tuple[VoicingMethodLockRescueAction, ...] = (VoicingMethodLockRescueAction.NONE,)
    same_family_safe_method: str = ""
    break_reason: str = ""
    reason: str = "disabled"
    contract: str = "method_lock_rescue_planning_v2_2_14"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "enabled": bool(self.enabled),
            "rescue_needed": bool(self.rescue_needed),
            "mode": self.mode.value,
            "scope": self.scope.value,
            "pattern": self.pattern.value,
            "locked_family": self.locked_family,
            "locked_method": self.locked_method,
            "kept_candidate_count": int(self.kept_candidate_count),
            "filtered_candidate_count": int(self.filtered_candidate_count),
            "runtime_filtering_enabled": bool(self.runtime_filtering_enabled),
            "fallback_returned": bool(self.fallback_returned),
            "recommended_actions": [action.value for action in self.recommended_actions],
            "same_family_safe_method": self.same_family_safe_method,
            "break_reason": self.break_reason,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class VoicingMethodLockRuntimePlan:
    """Runtime-planning view for one candidate against a method lock.

    v2_2_10 still does not filter candidates or change scores.  This object
    only records how a future selector should treat a candidate once
    progression/phrase-level method locking becomes active.
    """

    enabled: bool = False
    mode: VoicingMethodLockMode = VoicingMethodLockMode.OFF
    scope: VoicingMethodLockScope = VoicingMethodLockScope.CHORD_REGION
    pattern: VoicingMethodLockPattern = VoicingMethodLockPattern.EXPLICIT_SCOPE
    candidate_family: str = ""
    candidate_method: str = ""
    locked_family: str = ""
    locked_method: str = ""
    candidate_matches_lock: bool = False
    scoring_enabled: bool = False
    filtering_enabled: bool = False
    planned_action: str = "none"
    reason: str = "disabled"
    contract: str = "progression_phrase_method_lock_runtime_enforcement_pilot"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "enabled": bool(self.enabled),
            "mode": self.mode.value,
            "scope": self.scope.value,
            "pattern": self.pattern.value,
            "candidate_family": self.candidate_family,
            "candidate_method": self.candidate_method,
            "locked_family": self.locked_family,
            "locked_method": self.locked_method,
            "candidate_matches_lock": bool(self.candidate_matches_lock),
            "scoring_enabled": bool(self.scoring_enabled),
            "filtering_enabled": bool(self.filtering_enabled),
            "planned_action": self.planned_action,
            "reason": self.reason,
        }


def method_lock_rescue_plan_for_generation(
    spec: VoicingMethodLockSpec,
    *,
    kept_candidate_count: int = 0,
    filtered_candidate_count: int = 0,
    runtime_filtering_enabled: bool = False,
    fallback_returned: bool = False,
) -> VoicingMethodLockRescuePlan:
    """Return the v2_2_14 audit plan for strict method-lock rescue.

    This helper does not generate fallback voicings.  It documents what the
    future runtime should try if a STRICT lock filters away all candidates.
    The fallback order is intentionally conservative: preserve the locked
    family first when a safe method exists, then fall back to compact closed,
    and only unlock the current region with an explicit audit reason if needed.
    """

    locked_family = spec.family.value if spec.family else ""
    locked_method = spec.method_value if spec.family else ""
    kept = max(0, int(kept_candidate_count))
    filtered = max(0, int(filtered_candidate_count))

    if not spec.enabled or spec.mode == VoicingMethodLockMode.OFF:
        return VoicingMethodLockRescuePlan(
            enabled=False,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            locked_family=locked_family,
            locked_method=locked_method,
            kept_candidate_count=kept,
            filtered_candidate_count=filtered,
            runtime_filtering_enabled=bool(runtime_filtering_enabled),
            fallback_returned=bool(fallback_returned),
            reason="method_lock_disabled",
        )

    if spec.mode != VoicingMethodLockMode.STRICT or not runtime_filtering_enabled:
        return VoicingMethodLockRescuePlan(
            enabled=True,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            locked_family=locked_family,
            locked_method=locked_method,
            kept_candidate_count=kept,
            filtered_candidate_count=filtered,
            runtime_filtering_enabled=bool(runtime_filtering_enabled),
            fallback_returned=bool(fallback_returned),
            reason="rescue_not_runtime_active",
        )

    if kept > 0:
        return VoicingMethodLockRescuePlan(
            enabled=True,
            rescue_needed=False,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            locked_family=locked_family,
            locked_method=locked_method,
            kept_candidate_count=kept,
            filtered_candidate_count=filtered,
            runtime_filtering_enabled=True,
            fallback_returned=bool(fallback_returned),
            recommended_actions=(VoicingMethodLockRescueAction.KEEP_LOCKED_CANDIDATE,),
            reason="locked_candidate_available",
        )

    if filtered <= 0:
        return VoicingMethodLockRescuePlan(
            enabled=True,
            rescue_needed=True,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            locked_family=locked_family,
            locked_method=locked_method,
            kept_candidate_count=kept,
            filtered_candidate_count=filtered,
            runtime_filtering_enabled=True,
            fallback_returned=bool(fallback_returned),
            recommended_actions=(
                VoicingMethodLockRescueAction.TRY_CLOSED_COMPACT,
                VoicingMethodLockRescueAction.UNLOCK_CURRENT_REGION_WITH_AUDIT,
            ),
            break_reason="no_candidates_generated_before_lock",
            reason="strict_lock_has_no_candidate_pool",
        )

    safe_method = _safe_same_family_method_for_rescue(spec)
    actions: tuple[VoicingMethodLockRescueAction, ...]
    if safe_method:
        actions = (
            VoicingMethodLockRescueAction.TRY_SAME_FAMILY_SAFE_METHOD,
            VoicingMethodLockRescueAction.TRY_CLOSED_COMPACT,
            VoicingMethodLockRescueAction.UNLOCK_CURRENT_REGION_WITH_AUDIT,
        )
    else:
        actions = (
            VoicingMethodLockRescueAction.TRY_CLOSED_COMPACT,
            VoicingMethodLockRescueAction.UNLOCK_CURRENT_REGION_WITH_AUDIT,
        )
    return VoicingMethodLockRescuePlan(
        enabled=True,
        rescue_needed=True,
        mode=spec.mode,
        scope=spec.scope,
        pattern=spec.pattern,
        locked_family=locked_family,
        locked_method=locked_method,
        kept_candidate_count=kept,
        filtered_candidate_count=filtered,
        runtime_filtering_enabled=True,
        fallback_returned=bool(fallback_returned),
        recommended_actions=actions,
        same_family_safe_method=safe_method,
        break_reason="method_lock_filtered_all_candidates",
        reason="strict_lock_rescue_required",
    )


def _safe_same_family_method_for_rescue(spec: VoicingMethodLockSpec) -> str:
    if spec.family == DispositionFamily.OPEN:
        if spec.open_method != OpenProjectionMethod.GENERIC_OPEN:
            return OpenProjectionMethod.GENERIC_OPEN.value
        return ""
    if spec.family == DispositionFamily.SPREAD:
        if spec.spread_method != SpreadProjectionMethod.LOWER_UPPER_GROUPED:
            return SpreadProjectionMethod.LOWER_UPPER_GROUPED.value
        return ""
    return ""


def method_lock_runtime_plan_for_projection(
    spec: VoicingMethodLockSpec,
    projection_metadata: dict[str, Any] | None,
    *,
    filtering_enabled: bool | None = None,
    scoring_enabled: bool | None = None,
) -> VoicingMethodLockRuntimePlan:
    """Describe runtime method-lock treatment for one projected candidate.

    ``STRICT`` means hard method binding when explicit runtime filtering is
    enabled by metadata.  The default remains no selector effect so existing
    style output is unchanged unless a caller opts into this pilot.
    """

    metadata = dict(projection_metadata or {})
    candidate_family = str(metadata.get("disposition_projection_family") or "")
    candidate_method = str(metadata.get("disposition_projection_method") or "")
    locked_family = spec.family.value if spec.family else ""
    locked_method = spec.method_value if spec.family else ""

    if not spec.enabled or spec.mode == VoicingMethodLockMode.OFF:
        return VoicingMethodLockRuntimePlan(
            enabled=False,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            candidate_family=candidate_family,
            candidate_method=candidate_method,
            locked_family=locked_family,
            locked_method=locked_method,
            planned_action="none",
            reason="method_lock_disabled",
        )

    if not locked_family or not locked_method or locked_method == "unspecified":
        return VoicingMethodLockRuntimePlan(
            enabled=True,
            mode=spec.mode,
            scope=spec.scope,
            pattern=spec.pattern,
            candidate_family=candidate_family,
            candidate_method=candidate_method,
            locked_family=locked_family,
            locked_method=locked_method,
            candidate_matches_lock=False,
            planned_action="none",
            reason="lock_has_no_resolved_family_method",
        )

    matches = candidate_family == locked_family and candidate_method == locked_method
    runtime_filtering_enabled = bool(filtering_enabled) and spec.mode == VoicingMethodLockMode.STRICT
    runtime_scoring_enabled = bool(scoring_enabled) and spec.mode == VoicingMethodLockMode.PREFER

    if spec.mode == VoicingMethodLockMode.STRICT:
        if runtime_filtering_enabled:
            action = "keep_candidate" if matches else "filter_candidate"
            reason = "strict_runtime_filtering_enabled"
        else:
            action = "keep_candidate_future" if matches else "filter_candidate_future"
            reason = "strict_filtering_not_enabled"
    elif spec.mode == VoicingMethodLockMode.PREFER:
        if runtime_scoring_enabled:
            action = "prefer_candidate" if matches else "deprioritize_candidate"
            reason = "prefer_runtime_scoring_enabled"
        else:
            action = "prefer_candidate_future" if matches else "deprioritize_candidate_future"
            reason = "prefer_scoring_not_enabled"
    else:
        action = "none"
        reason = "method_lock_mode_off"

    return VoicingMethodLockRuntimePlan(
        enabled=True,
        mode=spec.mode,
        scope=spec.scope,
        pattern=spec.pattern,
        candidate_family=candidate_family,
        candidate_method=candidate_method,
        locked_family=locked_family,
        locked_method=locked_method,
        candidate_matches_lock=matches,
        scoring_enabled=runtime_scoring_enabled,
        filtering_enabled=runtime_filtering_enabled,
        planned_action=action,
        reason=reason,
    )


def method_lock_spec_from_metadata(metadata: dict[str, Any] | None) -> VoicingMethodLockSpec:
    """Build a method-lock planning spec from policy/arrangement metadata.

    Supported metadata shapes are intentionally permissive so future style or
    LLM planners can pass either a nested ``voicing_method_lock`` object or flat
    keys.  Missing metadata returns a disabled spec and never changes candidate
    generation behavior.
    """

    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock") or metadata.get("progression_voicing_method_lock") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}

    family = _coerce_family(
        values.get("family")
        or values.get("disposition_family")
        or values.get("locked_disposition_family")
        or values.get("voicing_method_lock_family")
    )
    closed_method = _coerce_closed_method(values.get("closed_method") or values.get("locked_closed_projection_method"))
    open_method = coerce_open_projection_method(
        values.get("open_method")
        or values.get("active_open_projection_method")
        or values.get("locked_open_projection_method")
        or values.get("open_projection_method")
    )
    spread_method = _coerce_spread_method(
        values.get("spread_method")
        or values.get("locked_spread_projection_method")
        or values.get("spread_projection_method")
    )

    method_value = values.get("method") or values.get("projection_method") or values.get("locked_projection_method")
    if method_value and family is not None:
        if family == DispositionFamily.CLOSED and closed_method is None:
            closed_method = _coerce_closed_method(method_value)
        elif family == DispositionFamily.OPEN and open_method is None:
            open_method = coerce_open_projection_method(method_value)
        elif family == DispositionFamily.SPREAD and spread_method is None:
            spread_method = _coerce_spread_method(method_value)

    enabled = _coerce_bool(values.get("enabled") or values.get("voicing_method_lock_enabled"), default=False)
    if not enabled:
        enabled = any(
            key in values
            for key in (
                "voicing_method_lock",
                "progression_voicing_method_lock",
                "voicing_method_lock_enabled",
                "locked_disposition_family",
                "locked_projection_method",
                "voicing_method_lock_family",
            )
        ) and family is not None

    scope = _coerce_enum(
        VoicingMethodLockScope,
        values.get("scope") or values.get("lock_scope") or values.get("voicing_method_lock_scope"),
        VoicingMethodLockScope.PROGRESSION if enabled else VoicingMethodLockScope.CHORD_REGION,
    )
    pattern = _coerce_enum(
        VoicingMethodLockPattern,
        values.get("pattern") or values.get("progression_pattern") or values.get("lock_pattern"),
        VoicingMethodLockPattern.EXPLICIT_SCOPE,
    )
    mode = _coerce_enum(
        VoicingMethodLockMode,
        values.get("mode") or values.get("lock_mode") or values.get("voicing_method_lock_mode"),
        VoicingMethodLockMode.STRICT if enabled else VoicingMethodLockMode.OFF,
    )
    break_triggers = _coerce_string_tuple(values.get("break_triggers") or values.get("allow_break_triggers"))

    return VoicingMethodLockSpec(
        enabled=bool(enabled),
        scope=scope,
        pattern=pattern,
        mode=mode,
        scope_id=str(values.get("scope_id") or values.get("voicing_method_lock_scope_id") or ""),
        locked_from_region_id=str(values.get("locked_from_region_id") or values.get("first_region_id") or ""),
        family=family,
        closed_method=closed_method,
        open_method=open_method,
        spread_method=spread_method,
        source=str(values.get("source") or ("metadata" if enabled else "none")),
        break_triggers=break_triggers or DEFAULT_METHOD_LOCK_BREAK_TRIGGERS,
    )


def _coerce_family(value: Any) -> DispositionFamily | None:
    if isinstance(value, DispositionFamily):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return None
    aliases = {
        "closed": DispositionFamily.CLOSED,
        "compact": DispositionFamily.CLOSED,
        "open": DispositionFamily.OPEN,
        "drop": DispositionFamily.OPEN,
        "spread": DispositionFamily.SPREAD,
        "foundation_projection": DispositionFamily.SPREAD,
        "root_anchored": DispositionFamily.SPREAD,
    }
    if text in aliases:
        return aliases[text]
    try:
        return DispositionFamily(text)
    except ValueError:
        return None


def _coerce_closed_method(value: Any) -> ClosedProjectionMethod | None:
    if isinstance(value, ClosedProjectionMethod):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return None
    aliases = {"closed": ClosedProjectionMethod.COMPACT, "compact_closed": ClosedProjectionMethod.COMPACT, "compact": ClosedProjectionMethod.COMPACT}
    if text in aliases:
        return aliases[text]
    try:
        return ClosedProjectionMethod(text)
    except ValueError:
        return None


def _coerce_spread_method(value: Any) -> SpreadProjectionMethod | None:
    if isinstance(value, SpreadProjectionMethod):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return None
    aliases = {
        "spread": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "two_hand_spread": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "lower_upper": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "lower_upper_grouped": SpreadProjectionMethod.LOWER_UPPER_GROUPED,
        "foundation": SpreadProjectionMethod.FOUNDATION_PROJECTION,
        "foundation_projection": SpreadProjectionMethod.FOUNDATION_PROJECTION,
        "root_anchored": SpreadProjectionMethod.ROOT_ANCHORED,
        "root_10th": SpreadProjectionMethod.ROOT_10TH_PROJECTION,
        "root_10th_projection": SpreadProjectionMethod.ROOT_10TH_PROJECTION,
    }
    if text in aliases:
        return aliases[text]
    try:
        return SpreadProjectionMethod(text)
    except ValueError:
        return None


def _coerce_enum(enum_type: type[Enum], value: Any, default: Any) -> Any:
    if isinstance(value, enum_type):
        return value
    text = str(value or "").strip().lower().replace("-", "_")
    if not text:
        return default
    try:
        return enum_type(text)
    except ValueError:
        return default


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _coerce_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return tuple(part for part in parts if part)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value),)
