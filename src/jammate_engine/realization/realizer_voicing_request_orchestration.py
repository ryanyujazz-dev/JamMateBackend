from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.harmony.harmonic_context import classify_functional_motion
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import VoicingPlan, VoicingPolicy, VoicingRequest, VoicingResolver
from jammate_engine.core.voicing.disposition.method_lock import (
    VoicingMethodLockMode,
    VoicingMethodLockPattern,
    VoicingMethodLockScope,
    VoicingMethodLockScopePlan,
    method_lock_follow_metadata_from_seed_candidate,
    method_lock_scope_plan_from_functional_motion,
)
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context

REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION = "v2_6_25"
REALIZER_SAME_CHORD_REATTACK_CONTINUITY_VERSION = "v2_6_41"
MEDIUM_SWING_PHRASE_SCOPE_METHOD_LOCK_POLICY_VERSION = "v2_6_49"
MEDIUM_SWING_ROOTLESS_AB_ORIENTATION_ALIGNMENT_VERSION = "v2_6_50"
MEDIUM_SWING_FOUR_NOTE_ROTATION_ALIGNMENT_VERSION = "v2_6_51"
MEDIUM_SWING_DELIBERATE_REVOICE_GESTURE_BOUNDARY_VERSION = "v2_6_54"
MEDIUM_SWING_DELIBERATE_REVOICE_MICRO_MOTION_POLICY_VERSION = "v2_6_55"
STYLE_NEUTRAL_PROGRESSION_METHOD_LOCK_WIRING_VERSION = "v2_6_116"
STYLE_NEUTRAL_FOUR_NOTE_ORIENTATION_ALIGNMENT_WIRING_VERSION = "v2_6_117"

REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES: tuple[str, ...] = (
    "style_voicing_policy_input_coercion",
    "event_scoped_voicing_request_construction",
    "one_default_voicing_selection_per_chord_region_cache",
    "explicit_fresh_revoicing_escape_hatch",
    "region_voicing_reuse_metadata_attachment",
    "style_neutral_progression_method_lock_runtime_wiring",
    "style_neutral_four_note_orientation_alignment_runtime_wiring",
    "medium_swing_phrase_scope_method_lock_policy_runtime_wiring_compatibility_alias",
    "medium_swing_rootless_ab_orientation_alignment_runtime_wiring_compatibility_alias",
    "medium_swing_four_note_rotation_alignment_runtime_wiring_compatibility_alias",
    "medium_swing_deliberate_revoice_gesture_boundary_runtime_wiring",
    "medium_swing_deliberate_revoice_micro_motion_policy_runtime_wiring",
)

REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "does_not_construct_degree_sources",
    "does_not_route_content_families",
    "does_not_decide_color_permission",
    "does_not_project_closed_open_or_spread_voicings",
    "does_not_score_or_select_voicing_candidates_directly",
    "does_not_build_piano_audit_payloads",
    "does_not_apply_expression_or_write_midi",
    "does_not_classify_progressions_independently_of_core_harmony",
)

RegionVoicingCacheKey = tuple[str, str, str]
RegionVoicingCache = dict[RegionVoicingCacheKey, VoicingPlan]


@dataclass(frozen=True)
class RealizerVoicingRequestOrchestrationProfile:
    version: str = REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION
    implementation_owner: str = "jammate_engine.realization.realizer_voicing_request_orchestration"
    consumed_by: str = "jammate_engine.realization.harmonic_realizer"
    output_boundary: str = "VoicingPlan resolved for one PatternEvent"
    cache_contract: str = "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices"
    owned_responsibilities: tuple[str, ...] = REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES
    forbidden_responsibilities: tuple[str, ...] = REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "realizer_voicing_request_orchestration_version": self.version,
            "implementation_owner": self.implementation_owner,
            "consumed_by": self.consumed_by,
            "output_boundary": self.output_boundary,
            "cache_contract": self.cache_contract,
            "owned_responsibilities": list(self.owned_responsibilities),
            "forbidden_responsibilities": list(self.forbidden_responsibilities),
            "request_orchestration_only": True,
            "no_source_construction_or_projection": True,
            "no_audit_or_note_realization": True,
        }


def realizer_voicing_request_orchestration_profile() -> RealizerVoicingRequestOrchestrationProfile:
    return RealizerVoicingRequestOrchestrationProfile()


def base_voicing_policy_from_style_input(style_voicing_policy: VoicingPolicy | dict | None) -> VoicingPolicy:
    """Coerce API/style inputs into a core VoicingPolicy without interpreting music.

    This is a realization-boundary adapter helper. It does not route content
    families, decide color permission, construct sources, project voicings,
    score candidates, or write MIDI.
    """

    if isinstance(style_voicing_policy, VoicingPolicy):
        return style_voicing_policy
    return VoicingPolicy.from_legacy_dict(style_voicing_policy or {})


class RealizerVoicingRequestOrchestrator:
    """Owns request construction and per-realization region voicing reuse.

    Harmonic realization should ask this object for a VoicingPlan and then hand
    that plan to the gesture realizer. The object deliberately delegates all
    musical source/projection/selection decisions to the core VoicingResolver.
    """

    def __init__(self, rng=None) -> None:
        self.voicing_resolver = VoicingResolver(rng=rng)
        self.region_voicing_cache: RegionVoicingCache = {}
        self.progression_method_lock_seed: dict[str, Any] | None = None

    def begin_realization_pass(self) -> None:
        self.region_voicing_cache = {}
        self.progression_method_lock_seed = None

    def resolve_event_voicing(
        self,
        *,
        event: PatternEvent,
        expression: EventExpression,
        base_policy: VoicingPolicy,
        ensemble: Any,
    ) -> VoicingPlan:
        cache_key = region_voicing_cache_key(event)
        cached = self.region_voicing_cache.get(cache_key)
        fresh_request = deliberate_revoice_request_from_event(event)
        if cached is None or fresh_request["requested"]:
            event_policy = policy_with_event_voicing_context(base_policy, event)
            event_policy = self._policy_with_style_neutral_progression_method_lock(event_policy, event)
            if cached is not None and fresh_request["requested"]:
                event_policy = policy_with_deliberate_revoice_micro_motion_context(
                    event_policy,
                    previous_voicing=cached,
                    request=fresh_request,
                )
            request_chord_symbol = voicing_request_chord_symbol(event, event_policy)
            req = VoicingRequest(
                event_id=event.event_id,
                chord_symbol=request_chord_symbol,
                track=event.track,
                gesture_type=event.gesture_type,
                gesture=event.gesture,
                expression_articulation=expression.articulation,
                ensemble_context=ensemble,
                policy=event_policy,
                onset_beat=event.onset_beat,
            )
            voicing = self.voicing_resolver.resolve(req)
            if request_chord_symbol != event.chord_symbol:
                voicing = replace(
                    voicing,
                    metadata={
                        **dict(getattr(voicing, "metadata", {}) or {}),
                        "voicing_request_chord_symbol_override_applied": True,
                        "voicing_request_original_chord_symbol": event.chord_symbol,
                        "voicing_request_effective_chord_symbol": request_chord_symbol,
                        "voicing_request_chord_symbol_override_source": dict(event_policy.metadata or {}).get("voicing_request_chord_symbol_override_source"),
                        "bossa_high_color_harmonic_expansion_policy_version": dict(event_policy.metadata or {}).get("bossa_high_color_harmonic_expansion_policy_version"),
                        "bossa_high_color_harmonic_expansion_applied": dict(event_policy.metadata or {}).get("bossa_high_color_harmonic_expansion_applied"),
                        "bossa_high_color_harmonic_expansion_color_family": dict(event_policy.metadata or {}).get("bossa_high_color_harmonic_expansion_color_family"),
                        "bossa_high_color_harmonic_expansion_no_voicing_module_change": dict(event_policy.metadata or {}).get("bossa_high_color_harmonic_expansion_no_voicing_module_change"),
                    },
                )
            if cached is not None and fresh_request["requested"]:
                voicing = annotate_deliberate_revoice_gesture_boundary(
                    voicing,
                    event=event,
                    previous_voicing=cached,
                    request=fresh_request,
                )
            self.region_voicing_cache[cache_key] = voicing
            self._record_style_neutral_progression_method_lock_seed(event_policy, event, voicing)
            return voicing
        return reuse_region_voicing(cached, event.event_id)

    def _policy_with_style_neutral_progression_method_lock(
        self,
        policy: VoicingPolicy,
        event: PatternEvent,
    ) -> VoicingPolicy:
        """Apply style-neutral local progression method lock metadata.

        This is orchestration-only wiring. It reuses the existing core harmony
        functional-motion classifier and the existing method-lock candidate
        filtering path; it does not choose notes, build sources, project DROP
        voicings, score candidates, or write MIDI.
        """

        metadata = dict(policy.metadata or {})
        if not _progression_method_lock_enabled(metadata):
            return policy

        seed = self.progression_method_lock_seed
        current_region_id = str(getattr(event, "region_id", "") or "")
        if not seed or str(seed.get("region_id") or "") == current_region_id:
            return _policy_with_progression_method_lock_debug(
                policy,
                applied=False,
                reason="no_previous_distinct_seed_region",
            )

        current_scope_id = str(metadata.get("voicing_texture_runtime_scope_id") or metadata.get("texture_scope_id") or "")
        if current_scope_id and str(seed.get("texture_scope_id") or "") != current_scope_id:
            return _policy_with_progression_method_lock_debug(
                policy,
                applied=False,
                reason="texture_scope_boundary",
                previous_region_id=str(seed.get("region_id") or ""),
                previous_method=str(seed.get("method") or ""),
            )

        previous_method = str(seed.get("method") or "")
        if previous_method not in _PROGRESSION_METHOD_LOCK_SEED_METHODS:
            return _policy_with_progression_method_lock_debug(
                policy,
                applied=False,
                reason="previous_method_not_propagated",
                previous_region_id=str(seed.get("region_id") or ""),
                previous_method=previous_method,
            )

        previous_chord_symbol = str(seed.get("chord_symbol") or "")
        motion = classify_functional_motion(
            previous_chord_symbol=previous_chord_symbol or None,
            chord_symbol=event.chord_symbol,
            next_chord_symbol=metadata.get("next_chord_symbol"),
        )
        pair_type = str(motion.previous_to_current_type or "")
        if pair_type not in _PROGRESSION_METHOD_LOCK_PAIR_TYPES:
            return _policy_with_progression_method_lock_debug(
                policy,
                applied=False,
                reason="not_local_functional_progression",
                pair_type=pair_type,
                previous_region_id=str(seed.get("region_id") or ""),
                previous_method=previous_method,
            )

        next_region_id = "next" if metadata.get("next_chord_symbol") else ""
        scope_id = _progression_method_lock_scope_id(metadata, seed, current_region_id, current_scope_id, pair_type)
        previous_region_id = str(seed.get("region_id") or "previous")
        scope_plan = method_lock_scope_plan_from_functional_motion(
            motion,
            previous_region_id=previous_region_id,
            current_region_id=current_region_id or "current",
            next_region_id=next_region_id,
            scope_id=scope_id,
            mode="strict",
            source="style_neutral_progression_method_lock_policy",
        )
        if not scope_plan.enabled:
            scope_plan = _progression_pair_method_lock_scope_plan(
                motion=motion,
                previous_region_id=previous_region_id,
                current_region_id=current_region_id or "current",
                scope_id=scope_id,
                pair_type=pair_type,
            )

        follow_metadata = method_lock_follow_metadata_from_seed_candidate(
            scope_plan,
            dict(seed.get("voicing_metadata") or {}),
            current_region_id=current_region_id or "current",
            runtime_filtering_enabled=True,
        )
        if not follow_metadata.get("voicing_method_lock_scope_runtime_wiring_enabled"):
            return _policy_with_progression_method_lock_debug(
                policy,
                applied=False,
                reason="follow_metadata_not_enabled",
                pair_type=pair_type,
                previous_region_id=str(seed.get("region_id") or ""),
                previous_method=previous_method,
            )

        locked = {**metadata, **follow_metadata}
        locked.update(
            _progression_method_lock_metadata(
                metadata,
                applied=True,
                reason="local_progression_follow_region_locked_to_previous_method",
                pair_type=pair_type,
                previous_region_id=str(seed.get("region_id") or ""),
                previous_chord_symbol=previous_chord_symbol,
                previous_method=previous_method,
                current_region_id=current_region_id,
            )
        )
        locked = _metadata_with_style_neutral_four_note_orientation_alignment(
            locked,
            seed=seed,
            current_region_id=current_region_id,
            pair_type=pair_type,
        )
        return replace(policy, metadata=locked)

    def _record_style_neutral_progression_method_lock_seed(
        self,
        policy: VoicingPolicy,
        event: PatternEvent,
        voicing: VoicingPlan,
    ) -> None:
        metadata = dict(policy.metadata or {})
        if not _progression_method_lock_enabled(metadata):
            return

        voicing_metadata = dict(voicing.metadata or {})
        family = str(voicing_metadata.get("disposition_projection_family") or "")
        method = str(voicing_metadata.get("disposition_projection_method") or "")
        if family != "open" or method not in _PROGRESSION_METHOD_LOCK_RECORDED_METHODS:
            return

        region_id = str(getattr(event, "region_id", "") or "")
        if self.progression_method_lock_seed and str(self.progression_method_lock_seed.get("region_id") or "") == region_id:
            return

        self.progression_method_lock_seed = {
            "region_id": region_id,
            "event_id": str(getattr(event, "event_id", "") or ""),
            "chord_symbol": str(getattr(event, "chord_symbol", "") or ""),
            "method": method,
            "texture_scope_id": str(metadata.get("voicing_texture_runtime_scope_id") or metadata.get("texture_scope_id") or ""),
            "voicing_metadata": voicing_metadata,
            "voicing_notes": [int(note.midi_note) for note in getattr(voicing, "notes", [])],
        }


def _metadata_with_style_neutral_four_note_orientation_alignment(
    metadata: dict[str, Any],
    *,
    seed: dict[str, Any],
    current_region_id: str,
    pair_type: str,
) -> dict[str, Any]:
    """Attach style-neutral progression four-note orientation continuity intent.

    This is the v2_6_117 first-principles contract: source/color has already
    been decided before this point, method lock has already established the
    local progression scope, and this helper only carries the selected seed's
    generic four-note A/B orientation metadata forward.  Candidate generation
    may then filter to a matching follow orientation when a safe candidate is
    available.  No voicing source, DROP projection, selector scoring, or MIDI
    realization is changed here.
    """

    if not _progression_four_note_orientation_alignment_enabled(metadata):
        return metadata

    seed_metadata = dict(seed.get("voicing_metadata") or {})
    seed_rotation = _four_note_rotation_seed_from_metadata(seed_metadata)
    previous_family = str(seed_rotation.get("family") or "")
    previous_ab_side = str(seed_rotation.get("ab_side") or "")
    if not previous_family or previous_ab_side not in {"A", "B"} or not _coerce_bool(seed_rotation.get("ab_eligible"), default=False):
        out = {
            **metadata,
            **_metadata_with_medium_swing_rootless_ab_skip_alias(metadata, reason="previous_seed_not_rootless_ab"),
            **_progression_four_note_orientation_alignment_metadata(
                metadata,
                applied=False,
                reason="previous_seed_not_generic_four_note_orientation",
                pair_type=pair_type,
                previous_region_id=str(seed.get("region_id") or ""),
                current_region_id=current_region_id,
            ),
        }
        if _medium_swing_four_note_rotation_alignment_enabled(metadata):
            out.update(
                _medium_swing_four_note_rotation_alignment_compat_metadata(
                    out,
                    applied=False,
                    reason="previous_seed_not_generic_four_note_rotation",
                    pair_type=pair_type,
                    seed=seed,
                    current_region_id=current_region_id,
                )
            )
        return out

    previous_content_type = str(seed_rotation.get("content_type") or "")
    previous_source_family = str(seed_rotation.get("source_family") or "")
    previous_notes = [int(note) for note in (seed.get("voicing_notes") or [])]
    previous_pair_index = seed_rotation.get("ab_pair_index")
    previous_inversion_index = seed_rotation.get("inversion_index")
    desired_side = "B" if previous_ab_side == "A" else "A"
    desired_inversion_index = seed_rotation.get("follow_inversion_index")
    if desired_inversion_index is None:
        try:
            desired_inversion_index = (int(previous_inversion_index) + 2) % 4
        except (TypeError, ValueError):
            desired_inversion_index = previous_inversion_index

    out = {
        **metadata,
        **_progression_four_note_orientation_alignment_metadata(
            metadata,
            applied=True,
            reason="method_locked_local_progression_follow_region_requests_four_note_orientation_flip",
            pair_type=pair_type,
            previous_region_id=str(seed.get("region_id") or ""),
            current_region_id=current_region_id,
            previous_family=previous_family,
            desired_family=previous_family,
            previous_ab_side=previous_ab_side,
            desired_ab_side=desired_side,
            previous_content_type=previous_content_type,
            desired_content_type=previous_content_type,
            previous_source_family=previous_source_family,
            desired_source_family=previous_source_family,
            previous_ab_pair_index=previous_pair_index,
            desired_ab_pair_index=previous_pair_index,
            previous_inversion_index=previous_inversion_index,
            desired_inversion_index=desired_inversion_index,
            previous_notes=previous_notes,
        ),
    }
    if _medium_swing_four_note_rotation_alignment_enabled(metadata):
        out.update(
            _medium_swing_four_note_rotation_alignment_compat_metadata(
                out,
                applied=True,
                reason="method_locked_local_progression_follow_region_requests_generic_four_note_rotation_flip",
                pair_type=pair_type,
                seed=seed,
                current_region_id=current_region_id,
                previous_family=previous_family,
                desired_family=previous_family,
                previous_ab_side=previous_ab_side,
                desired_ab_side=desired_side,
                previous_content_type=previous_content_type,
                desired_content_type=previous_content_type,
                previous_source_family=previous_source_family,
                desired_source_family=previous_source_family,
                previous_ab_pair_index=previous_pair_index,
                desired_ab_pair_index=previous_pair_index,
                previous_inversion_index=previous_inversion_index,
                desired_inversion_index=desired_inversion_index,
                previous_notes=previous_notes,
            )
        )
    if previous_family == "rootless_ab" and _medium_swing_rootless_ab_orientation_alignment_enabled(out):
        out.update(
            _metadata_with_medium_swing_rootless_ab_orientation_alignment_alias(
                out,
                seed=seed,
                current_region_id=current_region_id,
                pair_type=pair_type,
                previous_ab_side=previous_ab_side,
                desired_side=desired_side,
                previous_content_type=previous_content_type,
                previous_inversion_index=previous_inversion_index,
            )
        )
    elif _medium_swing_rootless_ab_orientation_alignment_enabled(out):
        out.update(_metadata_with_medium_swing_rootless_ab_skip_alias(out, reason="previous_seed_not_rootless_ab"))
    return out


def _progression_four_note_orientation_alignment_metadata(
    metadata: dict[str, Any],
    *,
    applied: bool,
    reason: str,
    pair_type: str,
    previous_region_id: str,
    current_region_id: str,
    previous_family: str = "",
    desired_family: str = "",
    previous_ab_side: str = "",
    desired_ab_side: str = "",
    previous_content_type: str = "",
    desired_content_type: str = "",
    previous_source_family: str = "",
    desired_source_family: str = "",
    previous_ab_pair_index: Any = None,
    desired_ab_pair_index: Any = None,
    previous_inversion_index: Any = None,
    desired_inversion_index: Any = None,
    previous_notes: list[int] | None = None,
) -> dict[str, Any]:
    style = str(metadata.get("style") or "").strip().lower()
    return {
        "progression_four_note_orientation_alignment_policy_version": STYLE_NEUTRAL_FOUR_NOTE_ORIENTATION_ALIGNMENT_WIRING_VERSION,
        "progression_four_note_orientation_alignment_policy_runtime_enabled": True,
        "progression_four_note_orientation_alignment_policy_applied": bool(applied),
        "progression_four_note_orientation_alignment_policy_reason": reason,
        "progression_four_note_orientation_alignment_policy_pair_type": pair_type,
        "progression_four_note_orientation_alignment_policy_previous_region_id": previous_region_id,
        "progression_four_note_orientation_alignment_policy_current_region_id": current_region_id,
        "progression_four_note_orientation_alignment_policy_previous_family": previous_family,
        "progression_four_note_orientation_alignment_policy_desired_family": desired_family,
        "progression_four_note_orientation_alignment_policy_previous_ab_side": previous_ab_side,
        "progression_four_note_orientation_alignment_policy_desired_ab_side": desired_ab_side,
        "progression_four_note_orientation_alignment_policy_previous_content_type": previous_content_type,
        "progression_four_note_orientation_alignment_policy_desired_content_type": desired_content_type,
        "progression_four_note_orientation_alignment_policy_previous_source_family": previous_source_family,
        "progression_four_note_orientation_alignment_policy_desired_source_family": desired_source_family,
        "progression_four_note_orientation_alignment_policy_previous_ab_pair_index": previous_ab_pair_index,
        "progression_four_note_orientation_alignment_policy_desired_ab_pair_index": desired_ab_pair_index,
        "progression_four_note_orientation_alignment_policy_previous_inversion_index": previous_inversion_index,
        "progression_four_note_orientation_alignment_policy_desired_inversion_index": desired_inversion_index,
        "progression_four_note_orientation_alignment_policy_previous_notes": list(previous_notes or []),
        "progression_four_note_orientation_alignment_policy_runtime_filtering_enabled": True,
        "progression_four_note_orientation_alignment_policy_mode": "strict_when_matching_candidate_available",
        "progression_four_note_orientation_alignment_policy_scope": "same_texture_scope_local_functional_pair",
        "progression_four_note_orientation_alignment_policy_style": style,
        "style_neutral_four_note_orientation_alignment_no_voicing_projection_change": True,
        "style_neutral_four_note_orientation_alignment_no_source_inventory_change": True,
        "style_neutral_four_note_orientation_alignment_no_selector_change": True,
    }


def _medium_swing_four_note_rotation_alignment_compat_metadata(
    metadata: dict[str, Any],
    *,
    applied: bool,
    reason: str,
    pair_type: str,
    seed: dict[str, Any],
    current_region_id: str,
    previous_family: str = "",
    desired_family: str = "",
    previous_ab_side: str = "",
    desired_ab_side: str = "",
    previous_content_type: str = "",
    desired_content_type: str = "",
    previous_source_family: str = "",
    desired_source_family: str = "",
    previous_ab_pair_index: Any = None,
    desired_ab_pair_index: Any = None,
    previous_inversion_index: Any = None,
    desired_inversion_index: Any = None,
    previous_notes: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "medium_swing_four_note_rotation_alignment_version": MEDIUM_SWING_FOUR_NOTE_ROTATION_ALIGNMENT_VERSION,
        "medium_swing_four_note_rotation_alignment_runtime_enabled": True,
        "medium_swing_four_note_rotation_alignment_policy_applied": bool(applied),
        "medium_swing_four_note_rotation_alignment_reason": reason,
        "medium_swing_four_note_rotation_alignment_pair_type": pair_type,
        "medium_swing_four_note_rotation_alignment_previous_region_id": str(seed.get("region_id") or ""),
        "medium_swing_four_note_rotation_alignment_current_region_id": current_region_id,
        "medium_swing_four_note_rotation_alignment_previous_family": previous_family,
        "medium_swing_four_note_rotation_alignment_desired_family": desired_family,
        "medium_swing_four_note_rotation_alignment_previous_ab_side": previous_ab_side,
        "medium_swing_four_note_rotation_alignment_desired_ab_side": desired_ab_side,
        "medium_swing_four_note_rotation_alignment_previous_content_type": previous_content_type,
        "medium_swing_four_note_rotation_alignment_desired_content_type": desired_content_type,
        "medium_swing_four_note_rotation_alignment_previous_source_family": previous_source_family,
        "medium_swing_four_note_rotation_alignment_desired_source_family": desired_source_family,
        "medium_swing_four_note_rotation_alignment_previous_ab_pair_index": previous_ab_pair_index,
        "medium_swing_four_note_rotation_alignment_desired_ab_pair_index": desired_ab_pair_index,
        "medium_swing_four_note_rotation_alignment_previous_inversion_index": previous_inversion_index,
        "medium_swing_four_note_rotation_alignment_desired_inversion_index": desired_inversion_index,
        "medium_swing_four_note_rotation_alignment_previous_notes": list(previous_notes or []),
        "medium_swing_four_note_rotation_alignment_runtime_filtering_enabled": True,
        "medium_swing_four_note_rotation_alignment_mode": "strict_when_matching_candidate_available",
        "medium_swing_four_note_rotation_alignment_scope": "same_texture_scope_local_functional_pair",
    }


# v2_6_51 compatibility name retained for direct focused imports/tests.
def _metadata_with_medium_swing_four_note_rotation_alignment(
    metadata: dict[str, Any],
    *,
    seed: dict[str, Any],
    current_region_id: str,
    pair_type: str,
) -> dict[str, Any]:
    return _metadata_with_style_neutral_four_note_orientation_alignment(
        metadata,
        seed=seed,
        current_region_id=current_region_id,
        pair_type=pair_type,
    )

def _metadata_with_medium_swing_rootless_ab_orientation_alignment_alias(
    metadata: dict[str, Any],
    *,
    seed: dict[str, Any],
    current_region_id: str,
    pair_type: str,
    previous_ab_side: str,
    desired_side: str,
    previous_content_type: str,
    previous_inversion_index: Any,
) -> dict[str, Any]:
    """Keep v2_6_50 rootless audit fields as compatibility aliases."""

    return {
        "medium_swing_rootless_ab_orientation_alignment_version": MEDIUM_SWING_ROOTLESS_AB_ORIENTATION_ALIGNMENT_VERSION,
        "medium_swing_rootless_ab_orientation_alignment_runtime_enabled": True,
        "medium_swing_rootless_ab_orientation_alignment_policy_applied": True,
        "medium_swing_rootless_ab_orientation_alignment_reason": "method_locked_local_progression_follow_region_requests_ab_flip",
        "medium_swing_rootless_ab_orientation_alignment_pair_type": pair_type,
        "medium_swing_rootless_ab_orientation_alignment_previous_region_id": str(seed.get("region_id") or ""),
        "medium_swing_rootless_ab_orientation_alignment_current_region_id": current_region_id,
        "medium_swing_rootless_ab_orientation_alignment_previous_orientation": previous_ab_side,
        "medium_swing_rootless_ab_orientation_alignment_desired_orientation": desired_side,
        "medium_swing_rootless_ab_orientation_alignment_previous_content_type": previous_content_type,
        "medium_swing_rootless_ab_orientation_alignment_desired_content_type": previous_content_type,
        "medium_swing_rootless_ab_orientation_alignment_previous_inversion_index": previous_inversion_index,
        "medium_swing_rootless_ab_orientation_alignment_desired_inversion_index": previous_inversion_index,
        "medium_swing_rootless_ab_orientation_alignment_runtime_filtering_enabled": True,
        "medium_swing_rootless_ab_orientation_alignment_mode": "strict_when_matching_candidate_available",
        "medium_swing_rootless_ab_orientation_alignment_scope": "same_texture_scope_local_functional_pair",
    }


def _metadata_with_medium_swing_rootless_ab_skip_alias(metadata: dict[str, Any], *, reason: str) -> dict[str, Any]:
    if not _medium_swing_rootless_ab_orientation_alignment_enabled(metadata):
        return {}
    return {
        "medium_swing_rootless_ab_orientation_alignment_version": MEDIUM_SWING_ROOTLESS_AB_ORIENTATION_ALIGNMENT_VERSION,
        "medium_swing_rootless_ab_orientation_alignment_runtime_enabled": True,
        "medium_swing_rootless_ab_orientation_alignment_policy_applied": False,
        "medium_swing_rootless_ab_orientation_alignment_reason": reason,
    }


# v2_6_50 compatibility name retained for direct focused imports/tests.
def _metadata_with_medium_swing_rootless_ab_orientation_alignment(
    metadata: dict[str, Any],
    *,
    seed: dict[str, Any],
    current_region_id: str,
    pair_type: str,
) -> dict[str, Any]:
    return _metadata_with_medium_swing_four_note_rotation_alignment(
        metadata,
        seed=seed,
        current_region_id=current_region_id,
        pair_type=pair_type,
    )


def _four_note_rotation_seed_from_metadata(seed_metadata: dict[str, Any]) -> dict[str, Any]:
    """Normalize selected-plan metadata into the generic v2_6_51 rotation seed.

    Older v2_6_50 tests and external debug probes may provide only rootless_ab_*
    fields, so rootless A/B remains a first-class compatibility source.
    """

    if seed_metadata.get("four_note_rotation_family"):
        return {
            "family": seed_metadata.get("four_note_rotation_family"),
            "content_type": seed_metadata.get("four_note_rotation_content_type"),
            "source_family": seed_metadata.get("four_note_rotation_source_family"),
            "ab_side": seed_metadata.get("four_note_rotation_ab_side"),
            "ab_pair_index": seed_metadata.get("four_note_rotation_ab_pair_index"),
            "inversion_index": seed_metadata.get("four_note_rotation_inversion_index"),
            "follow_inversion_index": seed_metadata.get("four_note_rotation_follow_inversion_index"),
            "ab_eligible": seed_metadata.get("four_note_rotation_ab_eligible", True),
        }
    if seed_metadata.get("rootless_ab_orientation_family") in {"A", "B"}:
        inversion = seed_metadata.get("rootless_ab_inversion_index")
        return {
            "family": "rootless_ab",
            "content_type": seed_metadata.get("rootless_ab_content_type"),
            "source_family": seed_metadata.get("rootless_ab_functional_source_type") or seed_metadata.get("rootless_ab_content_type"),
            "ab_side": seed_metadata.get("rootless_ab_orientation_family"),
            "ab_pair_index": inversion,
            "inversion_index": inversion,
            "follow_inversion_index": inversion,
            "ab_eligible": True,
        }
    if seed_metadata.get("basic_4note_inversion_index") is not None:
        inversion = seed_metadata.get("basic_4note_inversion_index")
        try:
            inv = int(inversion)
        except (TypeError, ValueError):
            inv = 0
        source_family = seed_metadata.get("basic_4note_source_family") or seed_metadata.get("basic_4note_source_role_order")
        return {
            "family": "basic_4note",
            "content_type": seed_metadata.get("basic_4note_functional_content_type") or seed_metadata.get("basic_4note_content_type"),
            "source_family": source_family,
            "ab_side": "A" if inv in {0, 1} else "B",
            "ab_pair_index": inv % 2,
            "inversion_index": inv,
            "follow_inversion_index": (inv + 2) % 4,
            "ab_eligible": True,
        }
    return {"ab_eligible": False}



def policy_with_deliberate_revoice_micro_motion_context(
    policy: VoicingPolicy,
    *,
    previous_voicing: VoicingPlan,
    request: dict[str, Any],
) -> VoicingPolicy:
    """Attach v2_6_55 same-chord deliberate-revoice micro-motion constraints.

    This remains an orchestration helper: it does not pick notes or project a
    voicing.  It only tells candidate generation that this explicit fresh
    same-region voicing should stay close to the cached region voicing.
    """

    metadata = dict(policy.metadata or {})
    if not _medium_swing_deliberate_revoice_micro_motion_enabled(metadata):
        return policy
    motion_policy = str(request.get("motion_policy") or "micro_motion")
    if motion_policy not in _MEDIUM_SWING_DELIBERATE_REVOICE_MICRO_MOTION_POLICIES:
        return policy
    previous_notes = [int(note.midi_note) for note in getattr(previous_voicing, "notes", [])]
    if not previous_notes:
        return policy
    max_low = _coerce_int(request.get("max_low_motion"), default=int(metadata.get("medium_swing_deliberate_revoice_micro_motion_max_low_motion", 0) or 0))
    max_top = _coerce_int(request.get("max_top_motion"), default=int(metadata.get("medium_swing_deliberate_revoice_micro_motion_max_top_motion", 2) or 2))
    max_avg = _coerce_float(request.get("max_avg_motion"), default=float(metadata.get("medium_swing_deliberate_revoice_micro_motion_max_avg_motion", 2.5) or 2.5))
    require_foundation = _coerce_bool(
        request.get("require_foundation_stable"),
        default=_coerce_bool(metadata.get("medium_swing_deliberate_revoice_micro_motion_require_foundation_stable"), default=True),
    )
    metadata.update(
        {
            "medium_swing_deliberate_revoice_micro_motion_policy_version": MEDIUM_SWING_DELIBERATE_REVOICE_MICRO_MOTION_POLICY_VERSION,
            "medium_swing_deliberate_revoice_micro_motion_policy_runtime_enabled": True,
            "medium_swing_deliberate_revoice_micro_motion_policy_requested": True,
            "medium_swing_deliberate_revoice_micro_motion_policy_motion_policy": motion_policy,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_notes": previous_notes,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_event_id": previous_voicing.event_id,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_chord_symbol": previous_voicing.chord_symbol,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_density": previous_voicing.density,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_content_family": previous_voicing.content_family,
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_family": dict(previous_voicing.metadata or {}).get("disposition_projection_family"),
            "medium_swing_deliberate_revoice_micro_motion_policy_previous_projection_method": dict(previous_voicing.metadata or {}).get("disposition_projection_method"),
            "medium_swing_deliberate_revoice_micro_motion_policy_require_foundation_stable": require_foundation,
            "medium_swing_deliberate_revoice_micro_motion_policy_max_low_motion": max_low,
            "medium_swing_deliberate_revoice_micro_motion_policy_max_top_motion": max_top,
            "medium_swing_deliberate_revoice_micro_motion_policy_max_avg_motion": max_avg,
            "medium_swing_deliberate_revoice_micro_motion_policy_scope": "same_chord_region_explicit_revoice_micro_motion",
        }
    )
    return replace(policy, metadata=metadata)



def voicing_request_chord_symbol(event: PatternEvent, policy: VoicingPolicy) -> str:
    """Return the chord symbol used for one voicing request.

    This is a harmonic-request boundary, not a voicing source/projection hook.
    Styles may attach an explicit, event-scoped harmonic-expansion symbol in
    policy metadata; the core voicing resolver still owns all source admission,
    drop-family projection, scoring, and selection.
    """

    metadata = dict(getattr(policy, "metadata", {}) or {})
    if not _coerce_bool(metadata.get("voicing_request_chord_symbol_override_enabled"), default=False):
        return event.chord_symbol
    override = str(metadata.get("voicing_request_chord_symbol_override") or "").strip()
    if not override:
        return event.chord_symbol
    return override


def region_voicing_cache_key(event: PatternEvent) -> RegionVoicingCacheKey:
    return (event.region_id, event.chord_symbol, event.track)


def deliberate_revoice_request_from_event(event: PatternEvent) -> dict[str, Any]:
    """Return the explicit same-region fresh-voicing request, if present.

    This is a boundary helper, not a voicing selector.  It only recognizes
    pitchless event/gesture intent flags that allow the cache to be bypassed.
    The actual note choice remains owned by ``VoicingResolver``.
    """

    event_metadata = dict(getattr(event, "metadata", {}) or {})
    gesture_metadata = dict(getattr(getattr(event, "gesture", None), "metadata", {}) or {})
    escape_hatches = ("force_fresh_voicing", "revoice_within_region")
    for source, metadata in (("event_metadata", event_metadata), ("gesture_metadata", gesture_metadata)):
        for key in escape_hatches:
            if _coerce_bool(metadata.get(key), default=False):
                return {
                    "requested": True,
                    "source": source,
                    "escape_hatch": key,
                    "reason": str(metadata.get("revoice_reason") or metadata.get("gesture_reason") or key),
                    "gesture_type": str(getattr(event, "gesture_type", "") or ""),
                    "motion_policy": str(
                        metadata.get("revoice_motion_policy")
                        or metadata.get("revoice_policy")
                        or metadata.get("revoice_gesture")
                        or "micro_motion"
                    ),
                    "max_low_motion": metadata.get("revoice_max_low_motion", metadata.get("micro_motion_max_low_motion")),
                    "max_top_motion": metadata.get("revoice_max_top_motion", metadata.get("micro_motion_max_top_motion")),
                    "max_avg_motion": metadata.get("revoice_max_avg_motion", metadata.get("micro_motion_max_avg_motion")),
                    "require_foundation_stable": metadata.get("revoice_require_foundation_stable", metadata.get("micro_motion_require_foundation_stable")),
                }
    return {
        "requested": False,
        "source": "",
        "escape_hatch": "",
        "reason": "no_explicit_revoice_intent",
        "gesture_type": str(getattr(event, "gesture_type", "") or ""),
    }


def event_requests_fresh_voicing(event: PatternEvent) -> bool:
    """Backward-compatible bool wrapper for the explicit revoicing escape hatch."""

    return bool(deliberate_revoice_request_from_event(event).get("requested", False))


def annotate_deliberate_revoice_gesture_boundary(
    voicing: VoicingPlan,
    *,
    event: PatternEvent,
    previous_voicing: VoicingPlan,
    request: dict[str, Any],
) -> VoicingPlan:
    """Mark an intentionally fresh same-region voicing selected via explicit intent."""

    previous_notes = [int(note.midi_note) for note in getattr(previous_voicing, "notes", [])]
    selected_notes = [int(note.midi_note) for note in getattr(voicing, "notes", [])]
    metadata = dict(voicing.metadata or {})
    metadata.update(
        {
            "medium_swing_deliberate_revoice_gesture_boundary_version": MEDIUM_SWING_DELIBERATE_REVOICE_GESTURE_BOUNDARY_VERSION,
            "medium_swing_deliberate_revoice_gesture_boundary_applied": True,
            "medium_swing_deliberate_revoice_gesture_boundary_scope": "same_chord_region_explicit_gesture_intent",
            "medium_swing_deliberate_revoice_gesture_boundary_reason": request.get("reason") or "explicit_revoice_intent",
            "medium_swing_deliberate_revoice_gesture_boundary_escape_hatch": request.get("escape_hatch") or "",
            "medium_swing_deliberate_revoice_gesture_boundary_source": request.get("source") or "",
            "medium_swing_deliberate_revoice_gesture_boundary_previous_event_id": previous_voicing.event_id,
            "medium_swing_deliberate_revoice_gesture_boundary_current_event_id": event.event_id,
            "medium_swing_deliberate_revoice_gesture_boundary_region_id": event.region_id,
            "medium_swing_deliberate_revoice_gesture_boundary_previous_notes": previous_notes,
            "medium_swing_deliberate_revoice_gesture_boundary_selected_notes": selected_notes,
            "medium_swing_deliberate_revoice_gesture_boundary_changed_notes": previous_notes != selected_notes,
            "medium_swing_deliberate_revoice_gesture_boundary_cache_bypass": True,
            "medium_swing_deliberate_revoice_micro_motion_policy_version": voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_version"),
            "medium_swing_deliberate_revoice_micro_motion_policy_applied": bool(voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_filter_applied", False)),
            "medium_swing_deliberate_revoice_micro_motion_policy_filter_reason": voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_filter_reason"),
            "medium_swing_deliberate_revoice_micro_motion_policy_candidate_matches": bool(voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_candidate_matches", False)),
            "medium_swing_deliberate_revoice_micro_motion_policy_low_motion_abs": voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_low_motion_abs"),
            "medium_swing_deliberate_revoice_micro_motion_policy_top_motion_abs": voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_top_motion_abs"),
            "medium_swing_deliberate_revoice_micro_motion_policy_avg_motion_abs": voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_avg_motion_abs"),
            "medium_swing_deliberate_revoice_micro_motion_policy_foundation_stable": bool(voicing.metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_foundation_stable", False)),
            "medium_swing_deliberate_revoice_gesture_boundary_cache_bypass": True,
            "medium_swing_deliberate_revoice_gesture_boundary_no_pattern_change": True,
            "medium_swing_deliberate_revoice_gesture_boundary_no_expression_change": True,
            "medium_swing_deliberate_revoice_gesture_boundary_no_midi_writer_change": True,
            "same_chord_reattack_continuity_version": REALIZER_SAME_CHORD_REATTACK_CONTINUITY_VERSION,
            "same_chord_reattack_continuity_contract": "reuse_cached_region_voicing_until_explicit_fresh_revoicing",
            "same_chord_reattack_continuity_region_cache_reuse": False,
            "same_chord_reattack_explicit_fresh_revoicing": True,
        }
    )
    return replace(voicing, event_id=event.event_id, metadata=metadata)


def reuse_region_voicing(voicing: VoicingPlan, event_id: str) -> VoicingPlan:
    metadata = dict(voicing.metadata or {})
    metadata.update(
        {
            "region_voicing_reused": True,
            "region_voicing_source_event_id": voicing.event_id,
            "region_voicing_contract": "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices",
            "realizer_voicing_request_orchestration_version": REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION,
            "same_chord_reattack_continuity_version": REALIZER_SAME_CHORD_REATTACK_CONTINUITY_VERSION,
            "same_chord_reattack_continuity_contract": "reuse_cached_region_voicing_until_explicit_fresh_revoicing",
            "same_chord_reattack_continuity_region_cache_reuse": True,
        }
    )
    return replace(voicing, event_id=event_id, metadata=metadata)



_MEDIUM_SWING_DELIBERATE_REVOICE_MICRO_MOTION_POLICIES: set[str] = {
    "micro_motion",
    "inner_motion",
    "top_voice_answer",
}


def _medium_swing_deliberate_revoice_micro_motion_enabled(metadata: dict[str, Any]) -> bool:
    return (
        str(metadata.get("style") or "").strip().lower() == "medium_swing"
        and _coerce_bool(metadata.get("medium_swing_deliberate_revoice_micro_motion_policy_enabled"), default=False)
    )


def _coerce_int(value: Any, *, default: int) -> int:
    try:
        if value is None:
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _coerce_float(value: Any, *, default: float) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)

_PROGRESSION_METHOD_LOCK_PAIR_TYPES: set[str] = {
    "ii_v",
    "minor_ii_v",
    "v_i_major",
    "v_i_minor",
    "dominant_to_tonic",
}

_PROGRESSION_METHOD_LOCK_RECORDED_METHODS: set[str] = {"drop2", "drop3", "drop2_and_4"}
_PROGRESSION_METHOD_LOCK_SEED_METHODS: set[str] = {"drop2", "drop3"}


def _progression_pair_method_lock_scope_plan(
    *,
    motion: Any,
    previous_region_id: str,
    current_region_id: str,
    scope_id: str,
    pair_type: str,
) -> VoicingMethodLockScopePlan:
    """Build a strict previous-current pair scope from core FunctionalMotion labels.

    ``method_lock_scope_plan_from_functional_motion`` naturally seeds current-next
    pairs.  The v2_6_49 realizer policy is invoked on the follow region after a
    seed has already been selected, so a previous-current V-I or ii-V pair needs
    this small adapter.  It still consumes the core harmony classifier output and
    does not duplicate progression recognition rules.
    """

    if pair_type in {"ii_v", "minor_ii_v"}:
        pattern = VoicingMethodLockPattern.II_V
    elif pair_type in {"v_i_major", "v_i_minor", "dominant_to_tonic"}:
        pattern = VoicingMethodLockPattern.V_I
    else:
        return VoicingMethodLockScopePlan(
            enabled=False,
            mode=VoicingMethodLockMode.OFF,
            current_region_id=current_region_id,
            source="style_neutral_progression_method_lock_policy_previous_pair_disabled",
            harmonic_window_type=str(getattr(motion, "window_type", "none") or "none"),
            previous_to_current_type=str(getattr(motion, "previous_to_current_type", "none") or "none"),
            current_to_next_type=str(getattr(motion, "current_to_next_type", "none") or "none"),
            functional_motion_tags=tuple(getattr(motion, "tags", ()) or ()),
        )

    region_ids = tuple(item for item in (previous_region_id, current_region_id) if item)
    return VoicingMethodLockScopePlan(
        enabled=bool(region_ids),
        scope=VoicingMethodLockScope.PROGRESSION,
        pattern=pattern,
        mode=VoicingMethodLockMode.STRICT,
        scope_id=scope_id,
        region_ids=region_ids,
        seed_region_id=previous_region_id,
        current_region_id=current_region_id,
        source="style_neutral_progression_method_lock_policy_previous_pair",
        harmonic_window_type=str(getattr(motion, "window_type", "none") or "none"),
        previous_to_current_type=str(getattr(motion, "previous_to_current_type", "none") or "none"),
        current_to_next_type=str(getattr(motion, "current_to_next_type", "none") or "none"),
        functional_motion_tags=tuple(getattr(motion, "tags", ()) or ()),
    )


def _progression_method_lock_enabled(metadata: dict[str, Any]) -> bool:
    nested = metadata.get("progression_voicing_method_lock_policy") or metadata.get("progression_method_lock_policy") or {}
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    return _coerce_bool(
        nested.get("enabled")
        or metadata.get("progression_voicing_method_lock_policy_enabled")
        or metadata.get("style_neutral_progression_method_lock_policy_enabled")
        or metadata.get("medium_swing_phrase_scope_method_lock_policy_enabled"),
        default=False,
    )


def _progression_four_note_orientation_alignment_enabled(metadata: dict[str, Any]) -> bool:
    nested = (
        metadata.get("progression_four_note_orientation_alignment_policy")
        or metadata.get("progression_orientation_continuity_policy")
        or {}
    )
    if not isinstance(nested, dict):
        nested = {"enabled": nested}
    return _coerce_bool(
        nested.get("enabled")
        or metadata.get("progression_four_note_orientation_alignment_policy_enabled")
        or metadata.get("style_neutral_four_note_orientation_alignment_policy_enabled")
        or metadata.get("medium_swing_four_note_rotation_alignment_enabled")
        or metadata.get("medium_swing_rootless_ab_orientation_alignment_enabled"),
        default=False,
    )


def _medium_swing_four_note_rotation_alignment_enabled(metadata: dict[str, Any]) -> bool:
    return (
        str(metadata.get("style") or "").strip().lower() == "medium_swing"
        and _coerce_bool(
            metadata.get("medium_swing_four_note_rotation_alignment_enabled")
            or metadata.get("medium_swing_rootless_ab_orientation_alignment_enabled"),
            default=False,
        )
    )


def _medium_swing_rootless_ab_orientation_alignment_enabled(metadata: dict[str, Any]) -> bool:
    return (
        str(metadata.get("style") or "").strip().lower() == "medium_swing"
        and _coerce_bool(metadata.get("medium_swing_rootless_ab_orientation_alignment_enabled"), default=False)
    )


def _policy_with_progression_method_lock_debug(
    policy: VoicingPolicy,
    *,
    applied: bool,
    reason: str,
    pair_type: str = "",
    previous_region_id: str = "",
    previous_method: str = "",
) -> VoicingPolicy:
    metadata = dict(policy.metadata or {})
    metadata.update(
        _progression_method_lock_metadata(
            metadata,
            applied=applied,
            reason=reason,
            pair_type=pair_type,
            previous_region_id=previous_region_id,
            previous_chord_symbol="",
            previous_method=previous_method,
            current_region_id="",
        )
    )
    return replace(policy, metadata=metadata)


def _progression_method_lock_metadata(
    metadata: dict[str, Any],
    *,
    applied: bool,
    reason: str,
    pair_type: str = "",
    previous_region_id: str = "",
    previous_chord_symbol: str = "",
    previous_method: str = "",
    current_region_id: str = "",
) -> dict[str, Any]:
    style = str(metadata.get("style") or "").strip().lower()
    out: dict[str, Any] = {
        "style_neutral_progression_method_lock_policy_version": STYLE_NEUTRAL_PROGRESSION_METHOD_LOCK_WIRING_VERSION,
        "progression_voicing_method_lock_policy_runtime_enabled": True,
        "progression_voicing_method_lock_policy_applied": bool(applied),
        "progression_voicing_method_lock_policy_reason": reason,
        "progression_voicing_method_lock_policy_pair_type": pair_type,
        "progression_voicing_method_lock_policy_previous_region_id": previous_region_id,
        "progression_voicing_method_lock_policy_previous_chord_symbol": previous_chord_symbol,
        "progression_voicing_method_lock_policy_previous_method": previous_method,
        "progression_voicing_method_lock_policy_current_region_id": current_region_id,
        "progression_voicing_method_lock_policy_style": style,
        "method_lock_rescue_runtime_enabled": True,
        "style_neutral_progression_method_lock_no_voicing_projection_change": True,
        "style_neutral_progression_method_lock_no_source_inventory_change": True,
    }
    if style == "medium_swing" or _coerce_bool(metadata.get("medium_swing_phrase_scope_method_lock_policy_enabled"), default=False):
        out.update(
            {
                "medium_swing_phrase_scope_method_lock_policy_version": MEDIUM_SWING_PHRASE_SCOPE_METHOD_LOCK_POLICY_VERSION,
                "medium_swing_phrase_scope_method_lock_policy_runtime_enabled": True,
                "medium_swing_phrase_scope_method_lock_policy_applied": bool(applied),
                "medium_swing_phrase_scope_method_lock_policy_reason": reason,
                "medium_swing_phrase_scope_method_lock_policy_pair_type": pair_type,
                "medium_swing_phrase_scope_method_lock_policy_previous_region_id": previous_region_id,
                "medium_swing_phrase_scope_method_lock_policy_previous_chord_symbol": previous_chord_symbol,
                "medium_swing_phrase_scope_method_lock_policy_previous_method": previous_method,
                "medium_swing_phrase_scope_method_lock_policy_current_region_id": current_region_id,
            }
        )
    return out


def _progression_method_lock_scope_id(
    metadata: dict[str, Any],
    seed: dict[str, Any],
    current_region_id: str,
    texture_scope_id: str,
    pair_type: str,
) -> str:
    previous_region_id = str(seed.get("region_id") or "previous")
    scope = texture_scope_id or "section:unknown"
    style = str(metadata.get("style") or "style").strip().lower() or "style"
    return f"{style}:{scope}:{pair_type}:{previous_region_id}->{current_region_id or 'current'}"


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return default
