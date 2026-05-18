from __future__ import annotations

from dataclasses import replace
from typing import Any

from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.expression.expression_plan import ExpressionPlan
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.core.voicing import VoicingPolicy, VoicingRequest, VoicingResolver, VoicingPlan
from jammate_engine.realization.voicing_policy_context_adapter import policy_with_event_voicing_context
from jammate_engine.realization.realizer_note_audit import (
    event_is_partial_reattack,
    piano_audit_event,
    release_reattacked_motion_voices,
    sync_piano_audit_realized_notes,
)


class HarmonicRealizer:
    def __init__(self, rng=None) -> None:
        self.voicing_resolver = VoicingResolver(rng=rng)
        self.gesture_realizer = GestureRealizer()
        self.last_piano_audit_events: list[dict[str, Any]] = []

    def realize(
        self,
        events: list[PatternEvent],
        expression: ExpressionPlan,
        style_voicing_policy: VoicingPolicy | dict | None,
        ensemble: EnsembleContext | dict,
    ) -> list[NoteEvent]:
        self.last_piano_audit_events = []
        if isinstance(style_voicing_policy, VoicingPolicy):
            policy = style_voicing_policy
        else:
            policy = VoicingPolicy.from_legacy_dict(style_voicing_policy or {})
        out: list[NoteEvent] = []
        event_by_id = {event.event_id: event for event in events}
        # Default harmonic-comping contract: one vertical voicing decision per
        # chord region. Multiple piano hits inside the same region should reuse
        # that selected source/order/register unless a future explicit gesture
        # asks for re-voicing or voice motion. This keeps source-weight listening
        # stable and prevents repeated rhythm hits from randomly changing
        # inversion within one unchanged harmony.
        region_voicing_cache: dict[tuple[str, str, str], VoicingPlan] = {}
        piano_events = sorted(
            (event for event in events if event.status == "active" and event.track == "piano"),
            key=lambda event: (event.onset_beat, event.region_id, event.event_id),
        )
        for event in piano_events:
            expr = expression.events.get(event.event_id)
            if expr is None:
                continue
            cache_key = (event.region_id, event.chord_symbol, event.track)
            cached = region_voicing_cache.get(cache_key)
            if cached is None or _event_requests_fresh_voicing(event):
                event_policy = policy_with_event_voicing_context(policy, event)
                req = VoicingRequest(
                    event_id=event.event_id,
                    chord_symbol=event.chord_symbol,
                    track=event.track,
                    gesture_type=event.gesture_type,
                    gesture=event.gesture,
                    expression_articulation=expr.articulation,
                    ensemble_context=ensemble,
                    policy=event_policy,
                    onset_beat=event.onset_beat,
                )
                voicing = self.voicing_resolver.resolve(req)
                region_voicing_cache[cache_key] = voicing
            else:
                voicing = _reuse_region_voicing(cached, event.event_id)
            realized = self.gesture_realizer.realize_harmonic_event(event, voicing, expr)
            if event_is_partial_reattack(event):
                out = release_reattacked_motion_voices(
                    existing_notes=out,
                    current_event=event,
                    current_notes=realized,
                    event_by_id=event_by_id,
                )
            out.extend(realized)
            self.last_piano_audit_events.append(piano_audit_event(event, expr, voicing, realized))
        self.last_piano_audit_events = sync_piano_audit_realized_notes(self.last_piano_audit_events, out)
        return out


def _event_requests_fresh_voicing(event: PatternEvent) -> bool:
    """Future gesture escape hatch for deliberate re-voicing inside a region."""

    metadata = dict(getattr(event, "metadata", {}) or {})
    gesture_metadata = dict(getattr(getattr(event, "gesture", None), "metadata", {}) or {})
    return bool(
        metadata.get("force_fresh_voicing")
        or metadata.get("revoice_within_region")
        or gesture_metadata.get("force_fresh_voicing")
        or gesture_metadata.get("revoice_within_region")
    )


def _reuse_region_voicing(voicing: VoicingPlan, event_id: str) -> VoicingPlan:
    metadata = dict(voicing.metadata or {})
    metadata.update(
        {
            "region_voicing_reused": True,
            "region_voicing_source_event_id": voicing.event_id,
            "region_voicing_contract": "one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices",
        }
    )
    return replace(voicing, event_id=event_id, metadata=metadata)
