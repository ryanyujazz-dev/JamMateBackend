from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from jammate_engine.core.harmony.chord_parser import ParsedChord, parse_chord

from .candidate import VoicingCandidate
from .constraints import evaluate_register_guard
from ..sources.canonical_source import canonical_closed_source_from_degrees
from ..sources.content_planner import plan_content_recipes
from ..disposition.method_lock import (
    method_lock_rescue_plan_for_generation,
    method_lock_runtime_plan_for_projection,
    method_lock_scope_plan_from_metadata,
    method_lock_scope_runtime_wiring_from_metadata,
    method_lock_spec_from_metadata,
)
from ..disposition.method_weights import disposition_method_weight_spec_from_metadata
from ..disposition.models import (
    ClosedProjectionMethod,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    open_projection_method_pool_from_metadata,
    projection_spec_from_legacy_disposition,
)
from ..disposition.projection import project_source_to_disposition
from ..disposition.spread import guard_ballad_spread_pilot_runtime_enablement
from ..policy import ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy, harmonic_expansion_allowed
from ..density_policy import density_disposition_decision
from ..runtime.texture_plan import derive_voicing_texture_plan, derive_voicing_texture_state
from .content_placement import place_content_recipe_for_projection
from .register_variants import (
    closed_voicing_compactness_metadata,
    policy_for_disposition_guard,
    register_variants,
)
from .source_rotation_metadata import source_rotation_metadata


def generate_candidates(symbol: str, policy: VoicingPolicy) -> list[VoicingCandidate]:
    """Generate voicing candidates, with explicit method-lock rescue when requested.

    Normal style output is unchanged: rescue execution is opt-in via metadata.
    Without that explicit flag this function returns the planning/audit behavior
    that existed before v2_2_15.
    """

    candidates = _generate_candidates_without_runtime_rescue(symbol, policy)
    candidates = _maybe_merge_ballad_spread_runtime_pilot_candidates(symbol, policy, candidates)
    if not _method_lock_rescue_runtime_enabled(policy.metadata):
        return candidates
    return _execute_method_lock_rescue_if_needed(symbol, policy, candidates)


def _maybe_merge_ballad_spread_runtime_pilot_candidates(
    symbol: str,
    policy: VoicingPolicy,
    candidates: list[VoicingCandidate],
) -> list[VoicingCandidate]:
    """Optionally add explicit Ballad SPREAD pilot candidates to the pool.

    The default path returns the original list unchanged.  The SPREAD pilot path
    requires dedicated policy metadata gates and always keeps the existing pool
    as fallback.
    """

    result = guard_ballad_spread_pilot_runtime_enablement(
        symbol,
        policy,
        base_candidates=tuple(candidates),
    )
    if not result.enabled_for_listening_isolation:
        return candidates
    return list(result.guarded_candidates)


def _generate_candidates_without_runtime_rescue(symbol: str, policy: VoicingPolicy) -> list[VoicingCandidate]:
    chord = parse_chord(symbol)
    candidates: list[VoicingCandidate] = []
    root_support_decision = dict((policy.metadata or {}).get("root_support_decision", {}))
    policy_metadata = dict(policy.metadata or {})
    voicing_method_lock_spec = method_lock_spec_from_metadata(policy_metadata)
    voicing_method_lock_debug = voicing_method_lock_spec.to_debug_dict()
    voicing_method_lock_scope_plan = method_lock_scope_plan_from_metadata(policy_metadata, current_symbol=symbol)
    voicing_method_lock_scope_debug = voicing_method_lock_scope_plan.to_debug_dict()
    voicing_method_lock_scope_runtime_wiring_debug = method_lock_scope_runtime_wiring_from_metadata(policy_metadata)
    method_lock_runtime_filtering_enabled = _method_lock_runtime_filtering_enabled(policy_metadata)
    method_lock_runtime_scoring_enabled = _method_lock_runtime_scoring_enabled(policy_metadata)
    method_lock_filtered_candidate_count = 0
    disposition_method_weight_spec = disposition_method_weight_spec_from_metadata(policy_metadata)
    disposition_method_weight_debug = disposition_method_weight_spec.to_debug_dict()
    texture_state = derive_voicing_texture_state(policy)
    texture_state_debug = texture_state.to_debug_dict()
    texture_state_runtime_debug = _texture_state_runtime_filter_debug(
        policy_metadata,
        dispositions=list(policy.effective_dispositions),
        texture_state=texture_state,
    )
    dispositions = list(texture_state_runtime_debug.pop("_effective_dispositions"))
    if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED}:
        if Disposition.LEFT_ROOT_RIGHT_CHORD not in dispositions:
            dispositions.insert(0, Disposition.LEFT_ROOT_RIGHT_CHORD)

    for content_recipe in plan_content_recipes(symbol, policy):
        family = content_recipe.family
        degrees = list(content_recipe.degrees)
        recipe = content_recipe.density_recipe
        recipe_debug = content_recipe.to_debug_dict()
        canonical_source = canonical_closed_source_from_degrees(content_recipe.degrees)
        texture_plan = derive_voicing_texture_plan(policy, content_family=family)
        texture_debug = texture_plan.to_debug_dict()
        canonical_debug = canonical_source.to_debug_dict()
        for disposition in dispositions:
            density_disposition = density_disposition_decision(
                disposition=disposition,
                density=recipe.density,
                functional_grouping=recipe.functional_grouping,
                policy=policy,
            )
            if not density_disposition.allowed:
                continue
            open_method_pool = _open_projection_methods_for_disposition(disposition, policy)
            for open_method_index, open_method in enumerate(open_method_pool):
                projection_policy = _policy_with_active_open_projection_method(policy, disposition, open_method, open_method_pool)
                projection = project_source_to_disposition(
                    disposition=disposition,
                    policy=projection_policy,
                    root_pc=chord.root_pc,
                    degrees=degrees,
                    legacy_placement_callback=lambda disposition=disposition, projection_policy=projection_policy: place_content_recipe_for_projection(
                        chord, degrees, family, disposition, projection_policy, content_recipe.validity_notes
                    ),
                    closed_parent_placement_callback=lambda projection_policy=projection_policy: _project_closed_parent_for_named_open_projection(
                        chord, degrees, family, projection_policy, content_recipe.validity_notes
                    ),
                    closed_parent_placement_candidates_callback=lambda projection_policy=projection_policy: _project_closed_parent_candidates_for_named_open_projection(
                        chord, degrees, family, projection_policy, content_recipe.validity_notes
                    ),
                )
                placed = projection.placed_list
                if not placed:
                    continue
                disposition_guard = projection.disposition_guard
                method_lock_runtime_plan = method_lock_runtime_plan_for_projection(
                    voicing_method_lock_spec,
                    projection.metadata,
                    filtering_enabled=method_lock_runtime_filtering_enabled,
                    scoring_enabled=method_lock_runtime_scoring_enabled,
                )
                if _should_filter_candidate_for_method_lock(method_lock_runtime_plan):
                    method_lock_filtered_candidate_count += 1
                    continue
                method_lock_runtime_debug = method_lock_runtime_plan.to_debug_dict()
                disposition_method_weight_value = disposition_method_weight_spec.method_weight(
                    family=projection.spec.family,
                    closed_method=projection.spec.closed_method,
                    open_method=projection.spec.open_method,
                    spread_method=projection.spec.spread_method,
                )
                if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED} and "R" not in [degree for degree, _ in placed]:
                    continue
                source_rotation_debug = source_rotation_metadata(family, content_recipe.validity_notes)
                for variant_index, variant_placed in enumerate(register_variants(placed, projection_policy, disposition)):
                    placed_degrees = [degree for degree, _ in variant_placed]
                    variant_notes = [note for _, note in variant_placed]
                    register_guard = evaluate_register_guard(variant_notes, policy_for_disposition_guard(projection_policy, disposition)).to_debug_dict()
                    if _runtime_filter_failed_register_guard_candidates(projection_policy.metadata) and not bool(register_guard.get("passed", False)):
                        continue
                    candidates.append(
                        VoicingCandidate(
                            notes=variant_notes,
                            degrees=placed_degrees,
                            score=_score_candidate(variant_notes, placed_degrees, family, disposition, projection_policy, chord),
                            content_family=family,
                            root_support=projection_policy.root_support,
                            bass_relation=projection_policy.bass_relation,
                            disposition=disposition,
                            interval_structure=projection_policy.interval_structure,
                            functional_grouping=recipe.functional_grouping,
                            recipe_id=recipe.recipe_id,
                            group_roles=recipe.group_roles,
                            root_support_decision=root_support_decision,
                            disposition_guard=disposition_guard,
                            register_guard=register_guard,
                            metadata={
                                "symbol": symbol,
                                "content_family": family.value,
                                "disposition": disposition.value,
                                "root_support": projection_policy.root_support.value,
                                "root_support_decision": root_support_decision,
                                "voicing_method_lock_plan": voicing_method_lock_debug,
                                "voicing_method_lock_scope_adapter_plan": voicing_method_lock_scope_debug,
                                "voicing_method_lock_scope_adapter_enabled": voicing_method_lock_scope_debug["enabled"],
                                "voicing_method_lock_scope_adapter_pattern": voicing_method_lock_scope_debug["pattern"],
                                "voicing_method_lock_scope_adapter_source": voicing_method_lock_scope_debug["source"],
                                "voicing_method_lock_scope_adapter_needs_seed_method": voicing_method_lock_scope_debug["needs_seed_method"],
                                "voicing_method_lock_scope_runtime_wiring": voicing_method_lock_scope_runtime_wiring_debug,
                                "voicing_method_lock_scope_runtime_wiring_enabled": voicing_method_lock_scope_runtime_wiring_debug["enabled"],
                                "voicing_method_lock_scope_runtime_wiring_current_region_id": voicing_method_lock_scope_runtime_wiring_debug["current_region_id"],
                                "voicing_method_lock_scope_runtime_wiring_seed_region_id": voicing_method_lock_scope_runtime_wiring_debug["seed_region_id"],
                                "voicing_method_lock_enabled": voicing_method_lock_debug["enabled"],
                                "voicing_method_lock_scope": voicing_method_lock_debug["scope"],
                                "voicing_method_lock_pattern": voicing_method_lock_debug["pattern"],
                                "voicing_method_lock_runtime_plan": method_lock_runtime_debug,
                                "voicing_method_lock_candidate_matches": method_lock_runtime_debug["candidate_matches_lock"],
                                "voicing_method_lock_runtime_action": method_lock_runtime_debug["planned_action"],
                                "voicing_method_lock_runtime_scoring_enabled": method_lock_runtime_debug["scoring_enabled"],
                                "voicing_method_lock_runtime_filtering_enabled": method_lock_runtime_debug["filtering_enabled"],
                                "disposition_method_weight_plan": disposition_method_weight_debug,
                                "disposition_method_weight": disposition_method_weight_value,
                                "disposition_method_weight_scoring_enabled": disposition_method_weight_debug["enabled_for_scoring"],
                                "voicing_texture_method_weight_shaping": policy_metadata.get("voicing_texture_method_weight_shaping"),
                                "voicing_texture_method_weight_shaping_enabled": bool(policy_metadata.get("voicing_texture_method_weight_shaping_enabled", False)),
                                "voicing_texture_method_weight_shaping_contract": policy_metadata.get("voicing_texture_method_weight_shaping_contract"),
                                "disposition_guard": disposition_guard,
                                "register_guard": register_guard,
                                # projection.metadata supplies disposition_projection_family,
                                # disposition_projection_method, and
                                # legacy_projection_callback_used for v2_2_1 migration audits.
                                **projection.metadata,
                                "open_projection_method_pool": [method.value for method in open_method_pool if method is not None],
                                "open_projection_method_pool_enabled": disposition == Disposition.OPEN and len([method for method in open_method_pool if method is not None]) > 1,
                                "open_projection_method_pool_size": len([method for method in open_method_pool if method is not None]),
                                "open_projection_method_pool_index": open_method_index if open_method is not None else None,
                                "active_open_projection_method": open_method.value if open_method is not None else None,
                                "interval_structure": projection_policy.interval_structure.value,
                                "register_variant": variant_index,
                                **closed_voicing_compactness_metadata(variant_notes, projection_policy, disposition),
                                "content_recipe": recipe_debug,
                                "density_recipe": recipe.to_debug_dict(),
                                "density_disposition_decision": density_disposition.to_debug_dict(),
                                "voicing_density_disposition_policy_version": density_disposition.version,
                                "canonical_closed_source": canonical_debug,
                                "voicing_texture_plan": texture_debug,
                                "voicing_texture_family": texture_debug["primary_disposition_family"],
                                "disposition_inertia": texture_debug["disposition_inertia"],
                                "voicing_texture_state": texture_state_debug,
                                "voicing_texture_state_primary_family": texture_state_debug["primary_family"],
                                "voicing_texture_state_allowed_families": texture_state_debug["allowed_families"],
                                "voicing_texture_state_source": texture_state_debug["source"],
                                "voicing_texture_state_family_stickiness": texture_state_debug["family_stickiness"],
                                "voicing_texture_state_runtime_filter": texture_state_runtime_debug,
                                "voicing_texture_state_runtime_filtering_enabled": texture_state_runtime_debug["enabled"],
                                **source_rotation_debug,
                            },
                        )
                    )
    if not candidates:
        fallback_register_guard = evaluate_register_guard([60], policy).to_debug_dict()
        method_lock_rescue_plan = method_lock_rescue_plan_for_generation(
            voicing_method_lock_spec,
            kept_candidate_count=0,
            filtered_candidate_count=method_lock_filtered_candidate_count,
            runtime_filtering_enabled=method_lock_runtime_filtering_enabled,
            fallback_returned=True,
        )
        method_lock_rescue_debug = method_lock_rescue_plan.to_debug_dict()
        return [
            VoicingCandidate(
                notes=[60],
                degrees=["R"],
                score=0.0,
                content_family=None,
                root_support=policy.root_support,
                disposition=policy.preferred_disposition,
                recipe_id="d1__ungrouped__fallback",
                root_support_decision=root_support_decision,
                register_guard=fallback_register_guard,
                metadata={
                    "fallback": True,
                    "symbol": symbol,
                    "root_support_decision": root_support_decision,
                    "voicing_method_lock_plan": voicing_method_lock_debug,
                    "voicing_method_lock_scope_adapter_plan": voicing_method_lock_scope_debug,
                    "voicing_method_lock_scope_adapter_enabled": voicing_method_lock_scope_debug["enabled"],
                    "voicing_method_lock_scope_runtime_wiring": voicing_method_lock_scope_runtime_wiring_debug,
                    "voicing_method_lock_scope_runtime_wiring_enabled": voicing_method_lock_scope_runtime_wiring_debug["enabled"],
                    "voicing_method_lock_enabled": voicing_method_lock_debug["enabled"],
                    "voicing_method_lock_rescue_plan": method_lock_rescue_debug,
                    "voicing_method_lock_rescue_needed": method_lock_rescue_debug["rescue_needed"],
                    "voicing_method_lock_rescue_reason": method_lock_rescue_debug["reason"],
                    "voicing_method_lock_rescue_break_reason": method_lock_rescue_debug["break_reason"],
                    "voicing_method_lock_filtered_candidate_count": method_lock_filtered_candidate_count,
                    "disposition_method_weight_plan": disposition_method_weight_debug,
                    "disposition_method_weight_scoring_enabled": disposition_method_weight_debug["enabled_for_scoring"],
                    "voicing_texture_state": texture_state_debug,
                    "voicing_texture_state_runtime_filter": texture_state_runtime_debug,
                    "voicing_texture_state_runtime_filtering_enabled": texture_state_runtime_debug["enabled"],
                    "register_guard": fallback_register_guard,
                },
            )
        ]
    return candidates



def _texture_state_runtime_filter_debug(
    metadata: dict | None,
    *,
    dispositions: list[Disposition],
    texture_state,
) -> dict:
    """Return effective disposition list after optional texture-state filtering.

    This is the first runtime consumer of ``VoicingTextureState``.  It is still
    intentionally small: when a style opts in, family-level texture continuity
    filters the legacy disposition list before low-level projection starts.  It
    does not choose pitches, methods, voicings, or phrase plans; it only prevents
    OPEN/CLOSED/SPREAD from being a per-chord random selector when the style has
    declared a phrase/section texture language.
    """

    original = list(dispositions)
    enabled = _voicing_texture_state_runtime_filtering_enabled(metadata)
    if not enabled:
        return {
            "contract": "voicing_texture_state_runtime_filter_contract_v2_2_28",
            "enabled": False,
            "source": "disabled",
            "reason": "policy_metadata_did_not_enable_runtime_filtering",
            "primary_family": texture_state.primary_family.value,
            "allowed_families": [family.value for family in texture_state.allowed_families],
            "original_dispositions": [disposition.value for disposition in original],
            "_effective_dispositions": original,
            "effective_dispositions": [disposition.value for disposition in original],
            "effective_disposition_values": [disposition.value for disposition in original],
            "fallback_to_original": False,
        }

    allowed_families = set(texture_state.allowed_families or (texture_state.primary_family,))
    filtered = [
        disposition
        for disposition in original
        if projection_spec_from_legacy_disposition(disposition).family in allowed_families
    ]
    fallback_to_original = False
    reason = "filtered_to_voicing_texture_state_allowed_families"
    if not filtered:
        filtered = original
        fallback_to_original = True
        reason = "no_disposition_survived_texture_state_filter"

    return {
        "contract": "voicing_texture_state_runtime_filter_contract_v2_2_28",
        "enabled": True,
        "source": "policy_metadata",
        "reason": reason,
        "primary_family": texture_state.primary_family.value,
        "allowed_families": [family.value for family in texture_state.allowed_families],
        "original_dispositions": [disposition.value for disposition in original],
        "_effective_dispositions": filtered,
        "effective_dispositions": [disposition.value for disposition in filtered],
        "effective_disposition_values": [disposition.value for disposition in filtered],
        "fallback_to_original": fallback_to_original,
    }


def _voicing_texture_state_runtime_filtering_enabled(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    nested = metadata.get("voicing_texture_state") or metadata.get("voicing_texture_runtime") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}
    return _coerce_bool(
        values.get("runtime_filtering_enabled")
        or values.get("voicing_texture_state_runtime_filtering_enabled")
        or values.get("texture_state_runtime_filtering_enabled")
        or values.get("family_runtime_filtering_enabled"),
        default=False,
    )


def _method_lock_rescue_runtime_enabled(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock") or metadata.get("progression_voicing_method_lock") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}
    return _coerce_bool(
        values.get("method_lock_rescue_runtime_enabled")
        or values.get("voicing_method_lock_rescue_runtime_enabled")
        or values.get("runtime_rescue_enabled")
        or values.get("rescue_runtime_enabled"),
        default=False,
    )


def _execute_method_lock_rescue_if_needed(
    symbol: str,
    policy: VoicingPolicy,
    candidates: list[VoicingCandidate],
) -> list[VoicingCandidate]:
    if not _candidates_need_method_lock_rescue(candidates):
        return candidates

    metadata = dict(policy.metadata or {})
    spec = method_lock_spec_from_metadata(metadata)
    rescue_plan_debug = dict(candidates[0].metadata.get("voicing_method_lock_rescue_plan") or {})
    filtered_count = int(candidates[0].metadata.get("voicing_method_lock_filtered_candidate_count") or 0)
    attempts = _method_lock_rescue_attempts(policy, spec)

    for action, attempt_policy in attempts:
        rescued = _generate_candidates_without_runtime_rescue(symbol, attempt_policy)
        real_candidates = [candidate for candidate in rescued if not candidate.metadata.get("fallback")]
        if real_candidates:
            return _annotate_method_lock_rescue_candidates(
                real_candidates,
                action=action,
                original_spec=spec,
                rescue_plan_debug=rescue_plan_debug,
                filtered_count=filtered_count,
                succeeded=True,
            )

    unlock_policy = _policy_for_method_lock_unlock_rescue(policy)
    unlocked = _generate_candidates_without_runtime_rescue(symbol, unlock_policy)
    if unlocked:
        return _annotate_method_lock_rescue_candidates(
            unlocked,
            action="unlock_current_region_with_audit",
            original_spec=spec,
            rescue_plan_debug=rescue_plan_debug,
            filtered_count=filtered_count,
            succeeded=not all(candidate.metadata.get("fallback") for candidate in unlocked),
        )

    return _annotate_method_lock_rescue_candidates(
        candidates,
        action="rescue_failed_return_original_fallback",
        original_spec=spec,
        rescue_plan_debug=rescue_plan_debug,
        filtered_count=filtered_count,
        succeeded=False,
    )


def _candidates_need_method_lock_rescue(candidates: list[VoicingCandidate]) -> bool:
    if not candidates:
        return False
    if len(candidates) != 1:
        return False
    metadata = dict(candidates[0].metadata or {})
    return bool(metadata.get("fallback")) and bool(metadata.get("voicing_method_lock_rescue_needed"))


def _method_lock_rescue_attempts(
    policy: VoicingPolicy,
    spec,
) -> list[tuple[str, VoicingPolicy]]:
    attempts: list[tuple[str, VoicingPolicy]] = []
    if spec.family == DispositionFamily.OPEN and spec.open_method != OpenProjectionMethod.GENERIC_OPEN:
        attempts.append((
            "try_same_family_safe_method",
            _policy_for_locked_method(
                policy,
                disposition=Disposition.OPEN,
                family=DispositionFamily.OPEN,
                method=OpenProjectionMethod.GENERIC_OPEN.value,
            ),
        ))
    elif spec.family == DispositionFamily.SPREAD and spec.spread_method != SpreadProjectionMethod.LOWER_UPPER_GROUPED:
        attempts.append((
            "try_same_family_safe_method",
            _policy_for_locked_method(
                policy,
                disposition=Disposition.SPREAD,
                family=DispositionFamily.SPREAD,
                method=SpreadProjectionMethod.LOWER_UPPER_GROUPED.value,
            ),
        ))

    attempts.append((
        "try_closed_compact",
        _policy_for_locked_method(
            policy,
            disposition=Disposition.CLOSED,
            family=DispositionFamily.CLOSED,
            method=ClosedProjectionMethod.COMPACT.value,
        ),
    ))
    return attempts


def _policy_for_locked_method(
    policy: VoicingPolicy,
    *,
    disposition: Disposition,
    family: DispositionFamily,
    method: str,
) -> VoicingPolicy:
    metadata = dict(policy.metadata or {})
    metadata["voicing_method_lock"] = {
        "enabled": True,
        "mode": "strict",
        "scope": metadata.get("voicing_method_lock_scope") or "progression",
        "pattern": metadata.get("voicing_method_lock_pattern") or "explicit_scope",
        "family": family.value,
        "method": method,
        "runtime_filtering_enabled": True,
        "method_lock_rescue_runtime_enabled": False,
        "source": "method_lock_rescue_runtime",
    }
    metadata["method_lock_rescue_runtime_attempt"] = True
    metadata["method_lock_rescue_runtime_attempt_family"] = family.value
    metadata["method_lock_rescue_runtime_attempt_method"] = method
    metadata["method_lock_rescue_runtime_enabled"] = False
    if disposition == Disposition.OPEN:
        metadata["active_open_projection_method"] = method
        metadata["open_projection_method"] = method
        metadata["allowed_open_projection_methods"] = [method]
    return replace(
        policy,
        preferred_disposition=disposition,
        allowed_dispositions=(disposition,),
        metadata=metadata,
    )


def _policy_for_method_lock_unlock_rescue(policy: VoicingPolicy) -> VoicingPolicy:
    metadata = dict(policy.metadata or {})
    metadata.pop("voicing_method_lock", None)
    metadata.pop("progression_voicing_method_lock", None)
    metadata["voicing_method_lock_enabled"] = False
    metadata["method_lock_rescue_runtime_enabled"] = False
    metadata["method_lock_rescue_runtime_unlock_attempt"] = True
    metadata["method_lock_rescue_runtime_unlock_reason"] = "explicit_unlock_current_region_with_audit"
    return replace(policy, metadata=metadata)


def _annotate_method_lock_rescue_candidates(
    candidates: list[VoicingCandidate],
    *,
    action: str,
    original_spec,
    rescue_plan_debug: dict,
    filtered_count: int,
    succeeded: bool,
) -> list[VoicingCandidate]:
    annotated: list[VoicingCandidate] = []
    for candidate in candidates:
        metadata = dict(candidate.metadata or {})
        metadata.update({
            "voicing_method_lock_rescue_runtime_executed": True,
            "voicing_method_lock_rescue_runtime_action": action,
            "voicing_method_lock_rescue_runtime_succeeded": bool(succeeded),
            "voicing_method_lock_rescue_original_plan": rescue_plan_debug,
            "voicing_method_lock_rescue_original_family": original_spec.family.value if original_spec.family else "",
            "voicing_method_lock_rescue_original_method": original_spec.method_value if original_spec.family else "",
            "voicing_method_lock_rescue_original_filtered_candidate_count": int(filtered_count),
        })
        annotated.append(replace(candidate, metadata=metadata))
    return annotated


def _open_projection_methods_for_disposition(
    disposition: Disposition,
    policy: VoicingPolicy,
) -> tuple[OpenProjectionMethod | None, ...]:
    if disposition != Disposition.OPEN:
        return (None,)
    metadata = dict(policy.metadata or {})
    lock_spec = method_lock_spec_from_metadata(metadata)
    if (
        _method_lock_runtime_filtering_enabled(metadata)
        and lock_spec.enabled
        and lock_spec.mode.value == "strict"
        and lock_spec.family is not None
        and lock_spec.family.value == "open"
        and lock_spec.open_method is not None
    ):
        return (lock_spec.open_method,)
    return open_projection_method_pool_from_metadata(metadata)


def _method_lock_runtime_filtering_enabled(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock") or metadata.get("progression_voicing_method_lock") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}
    return _coerce_bool(
        values.get("runtime_filtering_enabled")
        or values.get("filtering_enabled")
        or values.get("voicing_method_lock_runtime_filtering_enabled")
        or values.get("method_lock_runtime_filtering_enabled"),
        default=False,
    )


def _method_lock_runtime_scoring_enabled(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    nested = metadata.get("voicing_method_lock") or metadata.get("progression_voicing_method_lock") or {}
    if not isinstance(nested, dict):
        nested = {}
    values = {**metadata, **nested}
    return _coerce_bool(
        values.get("runtime_scoring_enabled")
        or values.get("scoring_enabled")
        or values.get("voicing_method_lock_runtime_scoring_enabled")
        or values.get("method_lock_runtime_scoring_enabled"),
        default=False,
    )


def _should_filter_candidate_for_method_lock(runtime_plan) -> bool:
    return (
        bool(runtime_plan.filtering_enabled)
        and runtime_plan.mode.value == "strict"
        and not bool(runtime_plan.candidate_matches_lock)
    )


def _runtime_filter_failed_register_guard_candidates(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    return _coerce_bool(
        metadata.get("runtime_filter_failed_register_guard_candidates")
        or metadata.get("voicing_runtime_filter_failed_register_guard_candidates"),
        default=False,
    )


def _coerce_bool(value, *, default: bool) -> bool:
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


def _policy_with_active_open_projection_method(
    policy: VoicingPolicy,
    disposition: Disposition,
    open_method: OpenProjectionMethod | None,
    open_method_pool: Iterable[OpenProjectionMethod | None],
) -> VoicingPolicy:
    if disposition != Disposition.OPEN or open_method is None:
        return policy
    pool_values = [method.value for method in open_method_pool if method is not None]
    metadata = dict(policy.metadata or {})
    metadata["active_open_projection_method"] = open_method.value
    metadata["open_projection_method_pool_resolved"] = pool_values
    metadata["open_projection_method_pool_enabled"] = len(pool_values) > 1
    metadata["open_projection_method_pool_size"] = len(pool_values)
    return replace(policy, metadata=metadata)


def _project_closed_parent_for_named_open_projection(
    chord: ParsedChord,
    degrees: list[tuple[str, int]],
    family,
    policy: VoicingPolicy,
    validity_notes: tuple[str, ...] = (),
) -> list[tuple[str, int]]:
    """Return the same closed parent path that named OPEN methods derive from.

    DROP2, DROP3, and DROP2_AND_4 are open-family projections of an existing
    4-note closed voicing, not direct source-order stackers.  This helper routes
    the parent through the normalized closed projection entry first, then falls
    back to the legacy closed content placement only through that closed entry's
    callback.
    """

    parent = project_source_to_disposition(
        disposition=Disposition.CLOSED,
        policy=policy,
        root_pc=chord.root_pc,
        degrees=degrees,
        legacy_placement_callback=lambda: place_content_recipe_for_projection(
            chord, degrees, family, Disposition.CLOSED, policy, validity_notes
        ),
    )
    return parent.placed_list


def _project_closed_parent_for_drop2(
    chord: ParsedChord,
    degrees: list[tuple[str, int]],
    family,
    policy: VoicingPolicy,
    validity_notes: tuple[str, ...] = (),
) -> list[tuple[str, int]]:
    """Compatibility alias for the v2_2_5 DROP2 parent helper name."""

    return _project_closed_parent_for_named_open_projection(chord, degrees, family, policy, validity_notes)


def _project_closed_parent_candidates_for_named_open_projection(
    chord: ParsedChord,
    degrees: list[tuple[str, int]],
    family,
    policy: VoicingPolicy,
    validity_notes: tuple[str, ...] = (),
) -> list[list[tuple[str, int]]]:
    """Return closed parent variants for project-then-filter DROP methods.

    DROP2, DROP3, and DROP2&4 should not inherit a single pre-selected closed
    parent.  They need all source/orientation-aware closed register variants so
    the dropped projections can be filtered by their own raised drop-register
    guard and then selected.
    """

    seed = _project_closed_parent_for_named_open_projection(chord, degrees, family, policy, validity_notes)
    variants = register_variants(seed, policy, Disposition.CLOSED) if seed else []
    if not variants:
        return [seed] if seed else []
    out: list[list[tuple[str, int]]] = []
    seen: set[tuple[tuple[str, int], ...]] = set()
    for variant in variants:
        key = tuple((str(degree), int(note)) for degree, note in sorted(variant, key=lambda item: item[1]))
        if key in seen:
            continue
        seen.add(key)
        out.append(list(key))
    return out




def _score_candidate(
    notes: list[int],
    degrees: list[str],
    family,
    disposition: Disposition,
    policy: VoicingPolicy,
    chord: ParsedChord | None = None,
) -> float:
    score = 1.0
    if family == policy.preferred_content:
        score += 0.5
    family_weights = dict(policy.content_family_weights or {})
    if family is not None:
        score += float(family_weights.get(family.value, family_weights.get(str(family), 0.0)))
    if disposition == policy.preferred_disposition:
        score += 0.5
    if policy.root_support == RootSupportPolicy.ROOTLESS_PREFERRED and "R" not in degrees:
        score += 0.4
    if policy.root_support in {RootSupportPolicy.ROOT_REQUIRED, RootSupportPolicy.BASS_ROOT_REQUIRED} and "R" in degrees:
        score += 0.8
    score += _low_priority_degree_adjustment(degrees, policy, chord)
    score += _shell_component_score_adjustment(degrees, family, policy, chord)
    density_distance = abs(len(notes) - policy.preferred_density)
    score -= density_distance * 0.05
    span = max(notes) - min(notes) if len(notes) > 1 else 0
    if policy.preferred_disposition in {Disposition.SPREAD, Disposition.TWO_HAND_SPREAD, Disposition.LEFT_ROOT_RIGHT_CHORD}:
        score += min(span / 24, 1.0) * 0.2
    return score




def _shell_component_score_adjustment(degrees: list[str], family, policy: VoicingPolicy, chord: ParsedChord | None) -> float:
    """Bias 3-note shell variants without hard-forcing a single answer.

    v2_1_9 treats shell+5 as shell+1or5 and treats expanded shell+color as a
    weighted candidate pool: color is primary, 5 is a reduced stable internal
    fallback, and root/1 is an even rarer cluster accent.  These are score
    biases only; the selector may still choose alternatives when voice-leading
    or stochastic sampling makes them useful.
    """

    family_value = getattr(family, "value", str(family))
    degree_set = set(degrees)
    if family_value == "shell_plus_5":
        if "R" in degree_set:
            return -0.78
        return 0.22 if {"5", "b5", "#5"}.intersection(degree_set) else 0.0
    if family_value != "shell_plus_color":
        return 0.0

    if chord is not None and (chord.is_half_diminished or chord.quality == "diminished"):
        return 0.25
    explicit = _explicit_symbol_degrees(chord)
    if any(degree in explicit for degree in degrees):
        return 0.55
    expansion = harmonic_expansion_allowed(policy, chord)
    if not expansion:
        return 0.0
    color_degrees = {"9", "11", "13", "b9", "#9", "#11", "b13"}
    if any(degree in color_degrees for degree in degrees):
        # Expansion means color is allowed, not forced.  v2_1_39 removes the
        # directed-m2 spacing preference, so keep source balance explicit: the
        # stable internal fifth remains the most common 3-note fallback, while
        # color sources stay audible but not constant.
        return -0.03
    if {"5", "b5", "#5"}.intersection(degree_set):
        return 0.42
    if "R" in degree_set:
        # Root/1 is intentionally retained as a rare cluster/bite option.
        # It is now even lower probability, and spacing rules must not erase
        # the bite when it appears.
        return -1.08
    return 0.0



def _low_priority_degree_adjustment(degrees: list[str], policy: VoicingPolicy, chord: ParsedChord | None) -> float:
    """Apply style-policy color caution without changing Harmony material.

    Harmony says which tensions are available.  A style may still mark some
    colors as low-priority for ordinary comping.  Explicit chord-symbol colors
    such as G7#11 or Cmaj9#11 are protected from this penalty.
    """

    low_priority = {str(degree) for degree in policy.low_priority_degrees}
    penalty = float(policy.low_priority_degree_penalty or 0.0)
    if not low_priority or penalty <= 0:
        return 0.0
    explicit = _explicit_symbol_degrees(chord)
    count = sum(1 for degree in degrees if degree in low_priority and degree not in explicit)
    return -penalty * count


def _explicit_symbol_degrees(chord: ParsedChord | None) -> set[str]:
    if chord is None:
        return set()
    explicit = set(chord.alterations) | set(chord.extensions) | set(chord.suspensions)
    if "alt" in explicit:
        explicit.update({"b9", "#9", "#11", "b13", "#5", "b5"})
    if "sus4" in explicit:
        explicit.add("11")
    if "sus2" in explicit:
        explicit.add("9")
    return explicit
