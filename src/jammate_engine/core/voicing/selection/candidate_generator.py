from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

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
from ..disposition.closed import compact_closed_parent_candidates_for_projection
from ..disposition.models import (
    ClosedProjectionMethod,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    open_projection_method_pool_from_metadata,
    projection_spec_from_legacy_disposition,
)
from ..disposition.projection import project_source_to_disposition
from ..disposition.spread_projection_core import project_basic_spread_candidates
from ..disposition.spread_runtime_adapter import spread_projection_candidate_to_voicing_candidate_adapter
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
    candidates = _maybe_use_grouped_spread_runtime_candidates(symbol, policy, candidates)
    if _method_lock_rescue_runtime_enabled(policy.metadata):
        candidates = _execute_method_lock_rescue_if_needed(symbol, policy, candidates)
    candidates = _apply_medium_swing_four_note_rotation_alignment(candidates, policy)
    return _apply_medium_swing_deliberate_revoice_micro_motion_policy(candidates, policy)



def _apply_medium_swing_deliberate_revoice_micro_motion_policy(
    candidates: list[VoicingCandidate],
    policy: VoicingPolicy,
) -> list[VoicingCandidate]:
    """Constrain explicit same-region fresh revoicings to small local motion.

    v2_6_55 is deliberately narrow.  It does not create revoice gestures and it
    does not change default same-chord reuse.  It only filters the candidate pool
    when the realizer has already seen an explicit fresh-revoicing intent and
    supplied the cached region voicing as the previous-note anchor.
    """

    if not candidates:
        return candidates
    metadata = dict(policy.metadata or {})
    if not _deliberate_revoice_micro_motion_policy_requested(metadata):
        return candidates

    previous_notes = _coerce_int_sequence(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_previous_notes"))
    if not previous_notes:
        return [
            _annotate_deliberate_revoice_micro_motion_candidate(
                candidate,
                metadata,
                applied=False,
                reason="previous_notes_unavailable",
                matched=False,
                original_count=len(candidates),
                kept_count=len(candidates),
            )
            for candidate in candidates
        ]

    matching = [candidate for candidate in candidates if _candidate_matches_deliberate_revoice_micro_motion(candidate, metadata, previous_notes)]
    if not matching:
        return [
            _annotate_deliberate_revoice_micro_motion_candidate(
                candidate,
                metadata,
                applied=False,
                reason="no_safe_micro_motion_candidate_available",
                matched=False,
                original_count=len(candidates),
                kept_count=len(candidates),
            )
            for candidate in candidates
        ]

    return [
        _annotate_deliberate_revoice_micro_motion_candidate(
            candidate,
            metadata,
            applied=True,
            reason="filtered_to_safe_micro_motion_candidate",
            matched=True,
            original_count=len(candidates),
            kept_count=len(matching),
        )
        for candidate in matching
    ]


def _deliberate_revoice_micro_motion_policy_requested(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    return (
        _coerce_bool(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled"), default=False)
        and _coerce_bool(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_requested"), default=False)
    )


def _candidate_matches_deliberate_revoice_micro_motion(
    candidate: VoicingCandidate,
    metadata: dict,
    previous_notes: list[int],
) -> bool:
    previous_density = metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_previous_density")
    if previous_density is not None and int(candidate.density or 0) != _coerce_int(previous_density, default=int(candidate.density or 0)):
        return False
    previous_method = str(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_method") or "")
    if previous_method and str(dict(candidate.metadata or {}).get("disposition_projection_method") or "") != previous_method:
        return False
    stats = _deliberate_revoice_micro_motion_stats(previous_notes, candidate.notes)
    if not stats:
        return False
    require_foundation = _coerce_bool(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_require_foundation_stable"), default=True)
    max_low = _coerce_int(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_max_low_motion"), default=0)
    max_top = _coerce_int(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_max_top_motion"), default=2)
    max_avg = _coerce_float(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_max_avg_motion"), default=2.5)
    if require_foundation and not bool(stats.get("foundation_stable")):
        return False
    return (
        int(stats["low_motion_abs"]) <= max_low
        and int(stats["top_motion_abs"]) <= max_top
        and float(stats["avg_motion_abs"]) <= max_avg
    )


def _deliberate_revoice_micro_motion_stats(previous_notes: Iterable[int], current_notes: Iterable[int]) -> dict[str, Any]:
    previous = sorted(_coerce_int_sequence(previous_notes))
    current = sorted(_coerce_int_sequence(current_notes))
    if not previous or not current:
        return {}
    pair_count = min(len(previous), len(current))
    paired_motion = [abs(int(current[index]) - int(previous[index])) for index in range(pair_count)]
    return {
        "low_motion_abs": abs(int(current[0]) - int(previous[0])),
        "top_motion_abs": abs(int(current[-1]) - int(previous[-1])),
        "avg_motion_abs": sum(paired_motion) / float(pair_count),
        "foundation_stable": int(current[0]) == int(previous[0]),
    }


def _annotate_deliberate_revoice_micro_motion_candidate(
    candidate: VoicingCandidate,
    policy_metadata: dict,
    *,
    applied: bool,
    reason: str,
    matched: bool,
    original_count: int,
    kept_count: int,
) -> VoicingCandidate:
    stats = _deliberate_revoice_micro_motion_stats(
        _coerce_int_sequence(policy_metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_previous_notes")),
        candidate.notes,
    )
    metadata = {
        **dict(candidate.metadata or {}),
        **_medium_swing_deliberate_revoice_micro_motion_policy_metadata(policy_metadata),
        "medium_swing_deliberate_revoice_micro_motion_policy_filter_applied": bool(applied),
        "medium_swing_deliberate_revoice_micro_motion_policy_filter_reason": reason,
        "medium_swing_deliberate_revoice_micro_motion_policy_candidate_matches": bool(matched),
        "medium_swing_deliberate_revoice_micro_motion_policy_original_candidate_count": int(original_count),
        "medium_swing_deliberate_revoice_micro_motion_policy_kept_candidate_count": int(kept_count),
        "medium_swing_deliberate_revoice_micro_motion_policy_selected_notes": list(candidate.notes),
    }
    if stats:
        metadata.update(
            {
                "medium_swing_deliberate_revoice_micro_motion_policy_low_motion_abs": stats.get("low_motion_abs"),
                "medium_swing_deliberate_revoice_micro_motion_policy_top_motion_abs": stats.get("top_motion_abs"),
                "medium_swing_deliberate_revoice_micro_motion_policy_avg_motion_abs": stats.get("avg_motion_abs"),
                "medium_swing_deliberate_revoice_micro_motion_policy_foundation_stable": bool(stats.get("foundation_stable")),
            }
        )
    return replace(candidate, metadata=metadata)


def _medium_swing_deliberate_revoice_micro_motion_policy_metadata(policy_metadata: dict) -> dict:
    keys = (
        "medium_swing_deliberate_revoice_micro_motion_policy_version",
        "medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled",
        "medium_swing_deliberate_revoice_micro_motion_policy_requested",
        "medium_swing_deliberate_revoice_micro_motion_policy_motion_policy",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_notes",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_event_id",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_chord_symbol",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_density",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_content_family",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_family",
        "medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_method",
        "medium_swing_deliberate_revoice_micro_motion_policy_require_foundation_stable",
        "medium_swing_deliberate_revoice_micro_motion_policy_max_low_motion",
        "medium_swing_deliberate_revoice_micro_motion_policy_max_top_motion",
        "medium_swing_deliberate_revoice_micro_motion_policy_max_avg_motion",
        "medium_swing_deliberate_revoice_micro_motion_policy_scope",
    )
    return {key: policy_metadata.get(key) for key in keys if key in policy_metadata}


def _coerce_int(value: object, *, default: int) -> int:
    try:
        if value is None:
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _coerce_float(value: object, *, default: float) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _apply_medium_swing_four_note_rotation_alignment(
    candidates: list[VoicingCandidate],
    policy: VoicingPolicy,
) -> list[VoicingCandidate]:
    """Filter to the desired generic 4-note follow rotation when safely available.

    v2_6_51 generalizes the v2_6_50 rootless-only A/B follow hook.  It consumes
    policy metadata produced by the realizer's local method-lock scope and can
    align conservative rooted 4-note rotations, rooted-color 4-note rotations,
    and rootless A/B rotations under the same contract.  If no matching current
    candidate exists, the full pool is preserved and annotated for audit.
    """

    if not candidates:
        return candidates
    metadata = dict(policy.metadata or {})
    if not _four_note_rotation_alignment_policy_applied(metadata):
        return candidates

    target = _four_note_rotation_alignment_target_from_metadata(metadata)
    if not target.get("desired_ab_side"):
        return [
            _annotate_four_note_rotation_alignment_candidate(
                candidate,
                metadata,
                applied=False,
                reason="missing_desired_four_note_rotation_side",
                matched=False,
                original_count=len(candidates),
                kept_count=len(candidates),
            )
            for candidate in candidates
        ]

    matching = [candidate for candidate in candidates if _candidate_matches_four_note_rotation_alignment(candidate, target)]
    if not matching:
        return [
            _annotate_four_note_rotation_alignment_candidate(
                candidate,
                metadata,
                applied=False,
                reason="no_matching_four_note_rotation_candidate_available",
                matched=False,
                original_count=len(candidates),
                kept_count=len(candidates),
            )
            for candidate in candidates
        ]

    smoothness_guard = _four_note_rotation_alignment_smoothness_guard(matching, target)
    if not smoothness_guard.get("passed"):
        return [
            _annotate_four_note_rotation_alignment_candidate(
                candidate,
                metadata,
                applied=False,
                reason="matching_four_note_rotation_candidates_fail_smoothness_guard",
                matched=False,
                original_count=len(candidates),
                kept_count=len(candidates),
                smoothness_guard=smoothness_guard,
            )
            for candidate in candidates
        ]

    return [
        _annotate_four_note_rotation_alignment_candidate(
            candidate,
            metadata,
            applied=True,
            reason="filtered_to_matching_four_note_rotation",
            matched=True,
            original_count=len(candidates),
            kept_count=len(matching),
            smoothness_guard=smoothness_guard,
        )
        for candidate in matching
    ]


def _four_note_rotation_alignment_target_from_metadata(metadata: dict) -> dict[str, object]:
    """Normalize v2_6_51 generic fields plus v2_6_50 rootless aliases."""

    desired_ab_side = str(
        metadata.get("medium_swing_four_note_rotation_alignment_desired_ab_side")
        or metadata.get("medium_swing_rootless_ab_orientation_alignment_desired_orientation")
        or ""
    )
    desired_family = str(metadata.get("medium_swing_four_note_rotation_alignment_desired_family") or "")
    desired_content_type = str(
        metadata.get("medium_swing_four_note_rotation_alignment_desired_content_type")
        or metadata.get("medium_swing_rootless_ab_orientation_alignment_desired_content_type")
        or ""
    )
    desired_source_family = str(metadata.get("medium_swing_four_note_rotation_alignment_desired_source_family") or "")
    desired_pair_index = metadata.get("medium_swing_four_note_rotation_alignment_desired_ab_pair_index")
    desired_inversion = metadata.get("medium_swing_four_note_rotation_alignment_desired_inversion_index")
    if desired_inversion is None:
        desired_inversion = metadata.get("medium_swing_rootless_ab_orientation_alignment_desired_inversion_index")
    return {
        "desired_ab_side": desired_ab_side,
        "desired_family": desired_family,
        "desired_content_type": desired_content_type,
        "desired_source_family": desired_source_family,
        "desired_pair_index": desired_pair_index,
        "desired_inversion": desired_inversion,
        "previous_notes": tuple(_coerce_int_sequence(metadata.get("medium_swing_four_note_rotation_alignment_previous_notes"))),
    }


def _candidate_matches_four_note_rotation_alignment(candidate: VoicingCandidate, target: dict[str, object]) -> bool:
    metadata = dict(candidate.metadata or {})
    if not _coerce_bool(metadata.get("four_note_rotation_ab_eligible"), default=False):
        return False
    if str(metadata.get("four_note_rotation_ab_side") or "") != str(target.get("desired_ab_side") or ""):
        return False
    desired_family = str(target.get("desired_family") or "")
    if desired_family and str(metadata.get("four_note_rotation_family") or "") != desired_family:
        return False
    desired_content_type = str(target.get("desired_content_type") or "")
    if desired_content_type and str(metadata.get("four_note_rotation_content_type") or "") != desired_content_type:
        return False
    desired_source_family = str(target.get("desired_source_family") or "")
    if desired_source_family and str(metadata.get("four_note_rotation_source_family") or "") != desired_source_family:
        return False
    desired_pair_index = target.get("desired_pair_index")
    if desired_pair_index is not None and str(metadata.get("four_note_rotation_ab_pair_index")) != str(desired_pair_index):
        return False
    desired_inversion = target.get("desired_inversion")
    if desired_inversion is not None and str(metadata.get("four_note_rotation_inversion_index")) != str(desired_inversion):
        return False
    return True


def _four_note_rotation_alignment_smoothness_guard(
    matching_candidates: list[VoicingCandidate],
    target: dict[str, object],
) -> dict[str, Any]:
    """Return whether generic 4-note hard filtering is musically safe.

    Rootless A/B was already treated as a vocabulary-level orientation contract in
    v2_6_50.  For rooted/basic 4-note rotations, v2_6_51 must not force 1357→5713
    when every matching candidate would create a large register jump.  The guard
    therefore only blocks hard filtering when previous realized notes are available
    and all matching candidates exceed conservative OPEN/DROP motion thresholds.
    """

    previous_notes = _coerce_int_sequence(target.get("previous_notes"))
    if not previous_notes:
        return {"passed": True, "reason": "previous_notes_unavailable"}

    best: dict[str, Any] | None = None
    for candidate in matching_candidates:
        stats = _four_note_rotation_motion_stats(previous_notes, candidate.notes)
        if not stats:
            continue
        if best is None or float(stats["avg_motion_abs"]) < float(best["avg_motion_abs"]):
            best = stats
        if (
            int(stats["top_motion_abs"]) <= 7
            and int(stats["low_motion_abs"]) <= 8
            and float(stats["avg_motion_abs"]) <= 6.0
        ):
            return {
                "passed": True,
                "reason": "matching_candidate_within_motion_guard",
                **stats,
            }

    if best is None:
        return {"passed": True, "reason": "candidate_notes_unavailable"}
    return {
        "passed": False,
        "reason": "all_matching_candidates_exceed_motion_guard",
        **best,
    }


def _four_note_rotation_motion_stats(previous_notes: Iterable[int], current_notes: Iterable[int]) -> dict[str, Any]:
    previous = sorted(_coerce_int_sequence(previous_notes))
    current = sorted(_coerce_int_sequence(current_notes))
    if not previous or not current:
        return {}
    pair_count = min(len(previous), len(current))
    paired_motion = [abs(int(current[index]) - int(previous[index])) for index in range(pair_count)]
    return {
        "low_motion_abs": abs(int(current[0]) - int(previous[0])),
        "top_motion_abs": abs(int(current[-1]) - int(previous[-1])),
        "avg_motion_abs": sum(paired_motion) / float(pair_count),
    }


def _four_note_rotation_alignment_smoothness_guard_metadata(smoothness_guard: dict[str, Any] | None) -> dict[str, Any]:
    if not smoothness_guard:
        return {}
    metadata: dict[str, Any] = {
        "medium_swing_four_note_rotation_alignment_smoothness_guard_passed": bool(smoothness_guard.get("passed")),
        "medium_swing_four_note_rotation_alignment_smoothness_guard_reason": smoothness_guard.get("reason"),
    }
    for key in ("low_motion_abs", "top_motion_abs", "avg_motion_abs"):
        if key in smoothness_guard:
            metadata[f"medium_swing_four_note_rotation_alignment_smoothness_guard_{key}"] = smoothness_guard.get(key)
    return metadata


def _coerce_int_sequence(value: object) -> list[int]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return []
    try:
        return [int(item) for item in value]  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return []


def _annotate_four_note_rotation_alignment_candidate(
    candidate: VoicingCandidate,
    policy_metadata: dict,
    *,
    applied: bool,
    reason: str,
    matched: bool,
    original_count: int,
    kept_count: int,
    smoothness_guard: dict[str, Any] | None = None,
) -> VoicingCandidate:
    candidate_metadata = dict(candidate.metadata or {})
    metadata = {
        **candidate_metadata,
        **_medium_swing_four_note_rotation_alignment_policy_metadata(policy_metadata),
        "medium_swing_four_note_rotation_alignment_filter_applied": bool(applied),
        "medium_swing_four_note_rotation_alignment_filter_reason": reason,
        "medium_swing_four_note_rotation_alignment_candidate_matches": bool(matched),
        "medium_swing_four_note_rotation_alignment_original_candidate_count": int(original_count),
        "medium_swing_four_note_rotation_alignment_kept_candidate_count": int(kept_count),
        **_four_note_rotation_alignment_smoothness_guard_metadata(smoothness_guard),
        "medium_swing_four_note_rotation_alignment_selected_family": candidate_metadata.get("four_note_rotation_family"),
        "medium_swing_four_note_rotation_alignment_selected_ab_side": candidate_metadata.get("four_note_rotation_ab_side"),
        "medium_swing_four_note_rotation_alignment_selected_content_type": candidate_metadata.get("four_note_rotation_content_type"),
        "medium_swing_four_note_rotation_alignment_selected_source_family": candidate_metadata.get("four_note_rotation_source_family"),
        "medium_swing_four_note_rotation_alignment_selected_ab_pair_index": candidate_metadata.get("four_note_rotation_ab_pair_index"),
        "medium_swing_four_note_rotation_alignment_selected_inversion_index": candidate_metadata.get("four_note_rotation_inversion_index"),
        # v2_6_50 compatibility aliases.  These stay meaningful for rootless A/B
        # but are now populated from the generic selected fields only when the
        # selected candidate actually belongs to the rootless_ab family.
        **_rootless_ab_alignment_alias_candidate_metadata(candidate_metadata, policy_metadata, applied, reason, matched, original_count, kept_count),
    }
    return replace(candidate, metadata=metadata)


def _rootless_ab_alignment_alias_candidate_metadata(
    candidate_metadata: dict,
    policy_metadata: dict,
    applied: bool,
    reason: str,
    matched: bool,
    original_count: int,
    kept_count: int,
) -> dict:
    if "medium_swing_rootless_ab_orientation_alignment_runtime_enabled" not in policy_metadata:
        return {}
    alias_reason = reason.replace("four_note_rotation", "rootless_ab_orientation")
    selected_is_rootless = candidate_metadata.get("four_note_rotation_family") == "rootless_ab"
    return {
        **_medium_swing_rootless_ab_orientation_alignment_policy_metadata(policy_metadata),
        "medium_swing_rootless_ab_orientation_alignment_filter_applied": bool(applied and selected_is_rootless),
        "medium_swing_rootless_ab_orientation_alignment_filter_reason": alias_reason,
        "medium_swing_rootless_ab_orientation_alignment_candidate_matches": bool(matched and selected_is_rootless),
        "medium_swing_rootless_ab_orientation_alignment_original_candidate_count": int(original_count),
        "medium_swing_rootless_ab_orientation_alignment_kept_candidate_count": int(kept_count),
        "medium_swing_rootless_ab_orientation_alignment_selected_orientation": candidate_metadata.get("rootless_ab_orientation_family"),
        "medium_swing_rootless_ab_orientation_alignment_selected_content_type": candidate_metadata.get("rootless_ab_content_type"),
        "medium_swing_rootless_ab_orientation_alignment_selected_inversion_index": candidate_metadata.get("rootless_ab_inversion_index"),
    }


def _medium_swing_four_note_rotation_alignment_policy_metadata(policy_metadata: dict) -> dict:
    keys = (
        "medium_swing_four_note_rotation_alignment_version",
        "medium_swing_four_note_rotation_alignment_runtime_enabled",
        "medium_swing_four_note_rotation_alignment_policy_applied",
        "medium_swing_four_note_rotation_alignment_reason",
        "medium_swing_four_note_rotation_alignment_pair_type",
        "medium_swing_four_note_rotation_alignment_previous_region_id",
        "medium_swing_four_note_rotation_alignment_current_region_id",
        "medium_swing_four_note_rotation_alignment_previous_family",
        "medium_swing_four_note_rotation_alignment_desired_family",
        "medium_swing_four_note_rotation_alignment_previous_ab_side",
        "medium_swing_four_note_rotation_alignment_desired_ab_side",
        "medium_swing_four_note_rotation_alignment_previous_content_type",
        "medium_swing_four_note_rotation_alignment_desired_content_type",
        "medium_swing_four_note_rotation_alignment_previous_source_family",
        "medium_swing_four_note_rotation_alignment_desired_source_family",
        "medium_swing_four_note_rotation_alignment_previous_ab_pair_index",
        "medium_swing_four_note_rotation_alignment_desired_ab_pair_index",
        "medium_swing_four_note_rotation_alignment_previous_inversion_index",
        "medium_swing_four_note_rotation_alignment_desired_inversion_index",
        "medium_swing_four_note_rotation_alignment_previous_notes",
        "medium_swing_four_note_rotation_alignment_runtime_filtering_enabled",
        "medium_swing_four_note_rotation_alignment_mode",
        "medium_swing_four_note_rotation_alignment_scope",
    )
    return {key: policy_metadata.get(key) for key in keys if key in policy_metadata}


def _medium_swing_rootless_ab_orientation_alignment_policy_metadata(policy_metadata: dict) -> dict:
    keys = (
        "medium_swing_rootless_ab_orientation_alignment_version",
        "medium_swing_rootless_ab_orientation_alignment_runtime_enabled",
        "medium_swing_rootless_ab_orientation_alignment_policy_applied",
        "medium_swing_rootless_ab_orientation_alignment_reason",
        "medium_swing_rootless_ab_orientation_alignment_pair_type",
        "medium_swing_rootless_ab_orientation_alignment_previous_region_id",
        "medium_swing_rootless_ab_orientation_alignment_current_region_id",
        "medium_swing_rootless_ab_orientation_alignment_previous_orientation",
        "medium_swing_rootless_ab_orientation_alignment_desired_orientation",
        "medium_swing_rootless_ab_orientation_alignment_previous_content_type",
        "medium_swing_rootless_ab_orientation_alignment_desired_content_type",
        "medium_swing_rootless_ab_orientation_alignment_previous_inversion_index",
        "medium_swing_rootless_ab_orientation_alignment_desired_inversion_index",
        "medium_swing_rootless_ab_orientation_alignment_runtime_filtering_enabled",
        "medium_swing_rootless_ab_orientation_alignment_mode",
        "medium_swing_rootless_ab_orientation_alignment_scope",
    )
    return {key: policy_metadata.get(key) for key in keys if key in policy_metadata}


def _four_note_rotation_alignment_policy_applied(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    generic_enabled = _coerce_bool(metadata.get("medium_swing_four_note_rotation_alignment_runtime_enabled"), default=False) and _coerce_bool(
        metadata.get("medium_swing_four_note_rotation_alignment_policy_applied"),
        default=False,
    ) and _coerce_bool(metadata.get("medium_swing_four_note_rotation_alignment_runtime_filtering_enabled"), default=False)
    legacy_enabled = _rootless_ab_alignment_policy_applied(metadata)
    return bool(generic_enabled or legacy_enabled)


def _rootless_ab_alignment_policy_applied(metadata: dict | None) -> bool:
    metadata = dict(metadata or {})
    return _coerce_bool(metadata.get("medium_swing_rootless_ab_orientation_alignment_runtime_enabled"), default=False) and _coerce_bool(
        metadata.get("medium_swing_rootless_ab_orientation_alignment_policy_applied"),
        default=False,
    ) and _coerce_bool(metadata.get("medium_swing_rootless_ab_orientation_alignment_runtime_filtering_enabled"), default=False)


# Backward-compatible public-ish helper names retained for older focused tests.
def _apply_medium_swing_rootless_ab_orientation_alignment(
    candidates: list[VoicingCandidate],
    policy: VoicingPolicy,
) -> list[VoicingCandidate]:
    return _apply_medium_swing_four_note_rotation_alignment(candidates, policy)


def _candidate_matches_rootless_ab_alignment(
    candidate: VoicingCandidate,
    *,
    desired_orientation: str,
    desired_content_type: str,
    desired_inversion,
) -> bool:
    return _candidate_matches_four_note_rotation_alignment(
        candidate,
        {
            "desired_family": "rootless_ab",
            "desired_ab_side": desired_orientation,
            "desired_content_type": desired_content_type,
            "desired_inversion": desired_inversion,
        },
    )


def _maybe_use_grouped_spread_runtime_candidates(
    symbol: str,
    policy: VoicingPolicy,
    candidates: list[VoicingCandidate],
) -> list[VoicingCandidate]:
    """Use the current grouped-SPREAD runtime pool when the event policy asks for it.

    This replaces the retired Ballad SPREAD pilot/dry-run wiring.  It only
    adapts already-legal SPREAD projection candidates into runtime candidates;
    source choice, projection, register guards, expression, and MIDI remain
    owned by their dedicated layers.
    """

    metadata = dict(policy.metadata or {})
    spread_requested = _coerce_bool(metadata.get("spread_selector_enabled"), default=False) or _coerce_bool(
        metadata.get("spread_groupwise_voice_leading_runtime_enabled"),
        default=False,
    )
    if not spread_requested:
        return candidates
    if "spread" not in _metadata_family_values(metadata):
        return candidates

    contract_ids = _grouped_spread_runtime_contract_ids(metadata)
    if not contract_ids:
        return candidates

    try:
        max_upper_options = int(
            metadata.get("spread_runtime_adapter_max_upper_options", metadata.get("max_upper_options", 12)) or 12
        )
    except (TypeError, ValueError):
        max_upper_options = 12

    projected = project_basic_spread_candidates(
        symbol,
        policy,
        contract_ids=contract_ids,
        max_upper_options=max_upper_options,
    )
    spread_candidates: list[VoicingCandidate] = []
    for result in projected:
        for projection_candidate in result.candidates:
            if not bool(getattr(projection_candidate, "is_legal", False)):
                continue
            adapter_result = spread_projection_candidate_to_voicing_candidate_adapter(
                projection_candidate,
                policy,
                allow_conversion=True,
                selector_reason="grouped_spread_runtime_candidate_pool",
            )
            if not adapter_result.converted or adapter_result.adapted_candidate is None:
                continue
            spread_candidates.append(_annotate_grouped_spread_runtime_candidate(adapter_result.adapted_candidate, metadata))

    if not spread_candidates:
        return candidates

    pool_metadata = metadata.get("spread_grouping_mix_candidate_pool") or {}
    if not isinstance(pool_metadata, dict):
        pool_metadata = {}
    use_compatible_only = _coerce_bool(
        pool_metadata.get("use_compatible_contracts", metadata.get("spread_grouping_mix_candidate_pool_uses_compatible_contracts")),
        default=True,
    )
    if use_compatible_only:
        return list(spread_candidates)
    return [*spread_candidates, *candidates]


def _metadata_family_values(metadata: dict) -> set[str]:
    values: set[str] = set()
    for key in ("primary_family", "preferred_disposition", "preferred_family"):
        value = metadata.get(key)
        if value is not None:
            values.add(str(getattr(value, "value", value)).strip().lower())
    allowed = metadata.get("allowed_families") or metadata.get("effective_disposition_families") or ()
    if isinstance(allowed, str):
        allowed = [part.strip() for part in allowed.replace(";", ",").split(",") if part.strip()]
    if isinstance(allowed, Iterable):
        for item in allowed:
            values.add(str(getattr(item, "value", item)).strip().lower())
    return values


def _grouped_spread_runtime_contract_ids(metadata: dict) -> tuple[str, ...]:
    ids: list[str] = []

    pool_metadata = metadata.get("spread_grouping_mix_candidate_pool") or {}
    if not isinstance(pool_metadata, dict):
        pool_metadata = {}
    for source in (
        pool_metadata.get("selected_contract_id"),
        metadata.get("ballad_spread_grouping_mix_selected_contract_id"),
    ):
        if source:
            text = str(source).strip()
            if text and text not in ids:
                ids.append(text)

    pool_compatible_ids = _as_string_sequence(pool_metadata.get("compatible_contract_ids"))
    if pool_compatible_ids:
        for item in pool_compatible_ids:
            if item and item not in ids:
                ids.append(item)
        return tuple(ids)

    for source in (
        metadata.get("spread_grouping_mix_candidate_contract_ids"),
        metadata.get("spread_density_runtime_contract_ids"),
        metadata.get("compatible_contract_ids"),
    ):
        for item in _as_string_sequence(source):
            if item and item not in ids:
                ids.append(item)
    return tuple(ids)


def _as_string_sequence(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.replace(";", ",").split(",") if part.strip())
    if isinstance(value, Iterable):
        return tuple(str(getattr(item, "value", item)).strip() for item in value if str(getattr(item, "value", item)).strip())
    text = str(getattr(value, "value", value)).strip()
    return (text,) if text else ()


def _annotate_grouped_spread_runtime_candidate(candidate: VoicingCandidate, metadata: dict) -> VoicingCandidate:
    candidate_metadata = dict(candidate.metadata or {})
    selected_contract_id = metadata.get("ballad_spread_grouping_mix_selected_contract_id")
    try:
        six_note_bias = float(metadata.get("spread_grouping_mix_selected_6note_contract_bias", 0.0) or 0.0)
    except (TypeError, ValueError):
        six_note_bias = 0.0
    decision = dict(metadata.get("ballad_spread_grouping_mix_policy_decision") or {})
    if selected_contract_id:
        decision = {**decision, "selected_contract_id": selected_contract_id}
    candidate_metadata.update(
        {
            "spread_grouped_runtime_candidate_pool_version": "v2_6_22",
            "candidate_pool_source": "grouped_spread_runtime",
            "candidate_generator_wiring_allowed": True,
            "style_runtime_wiring_enabled": True,
            "runtime_enabled": True,
            "spread_groupwise_voice_leading_runtime_enabled": True,
            "ballad_spread_grouping_mix_policy_decision": decision,
            "ballad_spread_grouping_mix_selected_contract_id": selected_contract_id,
            "spread_grouping_mix_policy_decision": decision,
            "spread_grouping_mix_selected_contract_id": selected_contract_id,
            "no_expression_or_pedal": True,
            "no_pattern_anticipation_gesture_or_midi": True,
        }
    )
    selector_decision = dict(candidate.selector_decision or {})
    selector_decision.update(
        {
            "source": "grouped_spread_runtime_candidate_pool",
            "candidate_pool_source": "grouped_spread_runtime",
            "candidate_generator_wiring_allowed": True,
            "style_runtime_wiring_enabled": True,
            "runtime_enabled": True,
        }
    )
    score = float(candidate.score or 0.0)
    if six_note_bias > 0.0 and str(candidate.recipe_id) == "spread_2plus4_contract":
        score += six_note_bias * 0.4
    return replace(candidate, score=score, metadata=candidate_metadata, selector_decision=selector_decision)


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
                                "medium_swing_phrase_scope_method_lock_policy_version": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_version"),
                                "medium_swing_phrase_scope_method_lock_policy_runtime_enabled": bool(policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_runtime_enabled", False)),
                                "medium_swing_phrase_scope_method_lock_policy_applied": bool(policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_applied", False)),
                                "medium_swing_phrase_scope_method_lock_policy_reason": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_reason"),
                                "medium_swing_phrase_scope_method_lock_policy_pair_type": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_pair_type"),
                                "medium_swing_phrase_scope_method_lock_policy_previous_region_id": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_region_id"),
                                "medium_swing_phrase_scope_method_lock_policy_previous_chord_symbol": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_chord_symbol"),
                                "medium_swing_phrase_scope_method_lock_policy_previous_method": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_method"),
                                "medium_swing_phrase_scope_method_lock_policy_current_region_id": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_current_region_id"),
                                **_medium_swing_rootless_ab_orientation_alignment_policy_metadata(policy_metadata),
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
                    "medium_swing_phrase_scope_method_lock_policy_version": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_version"),
                    "medium_swing_phrase_scope_method_lock_policy_runtime_enabled": bool(policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_runtime_enabled", False)),
                    "medium_swing_phrase_scope_method_lock_policy_applied": bool(policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_applied", False)),
                    "medium_swing_phrase_scope_method_lock_policy_reason": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_reason"),
                    "medium_swing_phrase_scope_method_lock_policy_pair_type": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_pair_type"),
                    "medium_swing_phrase_scope_method_lock_policy_previous_region_id": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_region_id"),
                    "medium_swing_phrase_scope_method_lock_policy_previous_chord_symbol": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_chord_symbol"),
                    "medium_swing_phrase_scope_method_lock_policy_previous_method": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_previous_method"),
                    "medium_swing_phrase_scope_method_lock_policy_current_region_id": policy_metadata.get("medium_swing_phrase_scope_method_lock_policy_current_region_id"),
                    **_medium_swing_rootless_ab_orientation_alignment_policy_metadata(policy_metadata),
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
    """Return compact closed parent variants for project-then-filter DROP methods.

    DROP2, DROP3, and DROP2&4 are projections of compact CLOSED parents.  The
    previous wiring reused ordinary CLOSED runtime placement variants; when a
    style such as Bossa did not enable strict compact-closed metadata, those
    "parents" could already be open/spread shapes such as ``[53, 56, 67, 71]``.
    Dropping from those non-compact parents produced illegal-sounding shapes
    like ``[53, 55, 56, 71]`` while still being labelled DROP2.

    Use the existing closed-disposition compact parent helper directly here so
    named OPEN methods always project from true compact parents.  This is not a
    new voicing capability; it restores the intended drop-family boundary.
    """

    compact_candidates = compact_closed_parent_candidates_for_projection(chord.root_pc, degrees, policy)
    if compact_candidates:
        return compact_candidates

    # Conservative fallback for exotic sources that the compact pitch-class
    # helper cannot represent.  Keep the old path available, but ordinary 4-note
    # tertian/drop-family sources should never need it.
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
