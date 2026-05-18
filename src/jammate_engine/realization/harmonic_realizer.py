from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.expression.expression_plan import ExpressionPlan
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.realization.gesture_realizer import GestureRealizer
from jammate_engine.realization.note_event_builder import NoteEvent
from jammate_engine.realization.realizer_note_audit import (
    event_is_partial_reattack,
    piano_audit_event,
    release_reattacked_motion_voices,
    sync_piano_audit_realized_notes,
)
from jammate_engine.realization.realizer_voicing_request_orchestration import (
    RealizerVoicingRequestOrchestrator,
    base_voicing_policy_from_style_input,
)


HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION = "v2_6_26"

HARMONIC_REALIZER_SURFACE_OWNED_RESPONSIBILITIES: tuple[str, ...] = (
    "active_piano_pattern_event_iteration",
    "realization_pass_cache_reset",
    "voicing_plan_request_delegation",
    "gesture_realizer_invocation",
    "note_event_list_ownership",
    "piano_audit_surface_version_attachment",
)

HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "does_not_construct_degree_sources",
    "does_not_route_content_families",
    "does_not_decide_color_permission",
    "does_not_project_closed_open_or_spread_voicings",
    "does_not_score_or_select_voicing_candidates_directly",
    "does_not_build_voicing_requests_directly",
    "does_not_own_region_cache_logic",
    "does_not_build_note_audit_payloads_directly",
    "does_not_write_midi_or_apply_expression",
)


@dataclass(frozen=True)
class HarmonicRealizerSurfaceFinalCleanupProfile:
    version: str = HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION
    implementation_owner: str = "jammate_engine.realization.harmonic_realizer"
    request_orchestration_owner: str = "jammate_engine.realization.realizer_voicing_request_orchestration"
    note_audit_owner: str = "jammate_engine.realization.realizer_note_audit"
    gesture_realizer_owner: str = "jammate_engine.realization.gesture_realizer"
    output_boundary: str = "list[NoteEvent] plus last_piano_audit_events"
    owned_responsibilities: tuple[str, ...] = HARMONIC_REALIZER_SURFACE_OWNED_RESPONSIBILITIES
    forbidden_responsibilities: tuple[str, ...] = HARMONIC_REALIZER_SURFACE_FORBIDDEN_RESPONSIBILITIES

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "harmonic_realizer_surface_final_cleanup_version": self.version,
            "implementation_owner": self.implementation_owner,
            "request_orchestration_owner": self.request_orchestration_owner,
            "note_audit_owner": self.note_audit_owner,
            "gesture_realizer_owner": self.gesture_realizer_owner,
            "output_boundary": self.output_boundary,
            "owned_responsibilities": list(self.owned_responsibilities),
            "forbidden_responsibilities": list(self.forbidden_responsibilities),
            "realization_surface_only": True,
            "delegates_request_cache_and_audit": True,
            "no_source_color_projection_or_selector_ownership": True,
        }


def harmonic_realizer_surface_final_cleanup_profile() -> HarmonicRealizerSurfaceFinalCleanupProfile:
    return HarmonicRealizerSurfaceFinalCleanupProfile()


class HarmonicRealizer:
    def __init__(self, rng=None) -> None:
        self.voicing_orchestrator = RealizerVoicingRequestOrchestrator(rng=rng)
        self.gesture_realizer = GestureRealizer()
        self.last_piano_audit_events: list[dict[str, Any]] = []

    def realize(
        self,
        events: list[PatternEvent],
        expression: ExpressionPlan,
        style_voicing_policy,
        ensemble: EnsembleContext | dict,
    ) -> list[NoteEvent]:
        self.last_piano_audit_events = []
        policy = base_voicing_policy_from_style_input(style_voicing_policy)
        self.voicing_orchestrator.begin_realization_pass()
        out: list[NoteEvent] = []
        event_by_id = {event.event_id: event for event in events}
        piano_events = sorted(
            (event for event in events if event.status == "active" and event.track == "piano"),
            key=lambda event: (event.onset_beat, event.region_id, event.event_id),
        )
        for event in piano_events:
            expr = expression.events.get(event.event_id)
            if expr is None:
                continue
            voicing = self.voicing_orchestrator.resolve_event_voicing(
                event=event,
                expression=expr,
                base_policy=policy,
                ensemble=ensemble,
            )
            realized = self.gesture_realizer.realize_harmonic_event(event, voicing, expr)
            if event_is_partial_reattack(event):
                out = release_reattacked_motion_voices(
                    existing_notes=out,
                    current_event=event,
                    current_notes=realized,
                    event_by_id=event_by_id,
                )
            out.extend(realized)
            audit_row = piano_audit_event(event, expr, voicing, realized)
            audit_row["harmonic_realizer_surface_final_cleanup_version"] = HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION
            self.last_piano_audit_events.append(audit_row)
        self.last_piano_audit_events = sync_piano_audit_realized_notes(self.last_piano_audit_events, out)
        return out
