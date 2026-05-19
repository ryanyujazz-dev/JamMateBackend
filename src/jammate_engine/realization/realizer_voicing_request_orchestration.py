from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import VoicingPlan, VoicingPolicy, VoicingRequest, VoicingResolver
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context

REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION = "v2_6_25"
REALIZER_SAME_CHORD_REATTACK_CONTINUITY_VERSION = "v2_6_41"

REALIZER_VOICING_REQUEST_ORCHESTRATION_OWNED_RESPONSIBILITIES: tuple[str, ...] = (
    "style_voicing_policy_input_coercion",
    "event_scoped_voicing_request_construction",
    "one_default_voicing_selection_per_chord_region_cache",
    "explicit_fresh_revoicing_escape_hatch",
    "region_voicing_reuse_metadata_attachment",
)

REALIZER_VOICING_REQUEST_ORCHESTRATION_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "does_not_construct_degree_sources",
    "does_not_route_content_families",
    "does_not_decide_color_permission",
    "does_not_project_closed_open_or_spread_voicings",
    "does_not_score_or_select_voicing_candidates_directly",
    "does_not_build_piano_audit_payloads",
    "does_not_apply_expression_or_write_midi",
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

    def begin_realization_pass(self) -> None:
        self.region_voicing_cache = {}

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
        if cached is None or event_requests_fresh_voicing(event):
            event_policy = policy_with_event_voicing_context(base_policy, event)
            req = VoicingRequest(
                event_id=event.event_id,
                chord_symbol=event.chord_symbol,
                track=event.track,
                gesture_type=event.gesture_type,
                gesture=event.gesture,
                expression_articulation=expression.articulation,
                ensemble_context=ensemble,
                policy=event_policy,
                onset_beat=event.onset_beat,
            )
            voicing = self.voicing_resolver.resolve(req)
            self.region_voicing_cache[cache_key] = voicing
            return voicing
        return reuse_region_voicing(cached, event.event_id)


def region_voicing_cache_key(event: PatternEvent) -> RegionVoicingCacheKey:
    return (event.region_id, event.chord_symbol, event.track)


def event_requests_fresh_voicing(event: PatternEvent) -> bool:
    """Explicit gesture escape hatch for deliberate re-voicing inside a region."""

    metadata = dict(getattr(event, "metadata", {}) or {})
    gesture_metadata = dict(getattr(getattr(event, "gesture", None), "metadata", {}) or {})
    return bool(
        metadata.get("force_fresh_voicing")
        or metadata.get("revoice_within_region")
        or gesture_metadata.get("force_fresh_voicing")
        or gesture_metadata.get("revoice_within_region")
    )


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
