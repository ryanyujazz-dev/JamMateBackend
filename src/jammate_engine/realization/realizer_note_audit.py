from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.gestures.gesture import GestureKind
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import VoicingPlan
from jammate_engine.realization.note_event_builder import NoteEvent

REALIZER_NOTE_AUDIT_CLEANUP_VERSION = "v2_6_24"

REALIZER_NOTE_AUDIT_OWNED_RESPONSIBILITIES: tuple[str, ...] = (
    "piano_audit_event_debug_payload_construction",
    "final_note_event_audit_sync",
    "note_event_debug_projection_metadata_serialization",
    "partial_reattack_motion_voice_release_using_selected_voicing_metadata",
)

REALIZER_NOTE_AUDIT_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "does_not_construct_degree_sources",
    "does_not_route_content_families",
    "does_not_decide_color_permission",
    "does_not_project_closed_open_or_spread_voicings",
    "does_not_score_or_select_voicing_candidates",
    "does_not_build_voicing_requests",
    "does_not_apply_expression_or_write_midi",
)


@dataclass(frozen=True)
class RealizerNoteAuditCleanupProfile:
    version: str = REALIZER_NOTE_AUDIT_CLEANUP_VERSION
    implementation_owner: str = "jammate_engine.realization.realizer_note_audit"
    owned_responsibilities: tuple[str, ...] = REALIZER_NOTE_AUDIT_OWNED_RESPONSIBILITIES
    forbidden_responsibilities: tuple[str, ...] = REALIZER_NOTE_AUDIT_FORBIDDEN_RESPONSIBILITIES
    note_event_boundary_only: bool = True
    voicing_request_orchestration_owner: str = "jammate_engine.realization.realizer_voicing_request_orchestration"

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "realizer_note_audit_cleanup_version": self.version,
            "implementation_owner": self.implementation_owner,
            "owned_responsibilities": list(self.owned_responsibilities),
            "forbidden_responsibilities": list(self.forbidden_responsibilities),
            "note_event_boundary_only": self.note_event_boundary_only,
            "voicing_request_orchestration_owner": self.voicing_request_orchestration_owner,
        }


def realizer_note_audit_cleanup_profile() -> RealizerNoteAuditCleanupProfile:
    return RealizerNoteAuditCleanupProfile()


def event_is_partial_reattack(event: PatternEvent) -> bool:
    gesture = getattr(event, "gesture", None)
    gesture_kind = getattr(gesture, "kind", None)
    gesture_type = str(getattr(event, "gesture_type", "") or getattr(gesture, "gesture_type", "") or "").strip().lower()
    if gesture_kind == GestureKind.INNER_MOVEMENT or gesture_type == GestureKind.INNER_MOVEMENT.value:
        metadata = dict(getattr(gesture, "metadata", {}) or {})
        held_policy = str(metadata.get("held_voice_policy") or "").strip().lower()
        scope = str(metadata.get("rearticulation_scope") or "").strip().lower()
        return held_policy in {"hold_foundation_common_tones", "hold_common_tones", "tie_foundation"} or "inner" in scope or "color" in scope
    return False


def release_reattacked_motion_voices(
    *,
    existing_notes: list[NoteEvent],
    current_event: PatternEvent,
    current_notes: list[NoteEvent],
    event_by_id: dict[str, PatternEvent],
    timing_policy: Mapping[str, Any] | None = None,
) -> list[NoteEvent]:
    """Trim only voices reattacked by an INNER_MOVEMENT gesture.

    This realization-layer adjustment consumes already-selected voicing
    projection metadata and never chooses new pitch content, source family,
    color permission, projection method, expression, or MIDI behavior.
    """

    if not current_notes:
        return existing_notes
    current_start = min(_performed_start_for_partial_release(note, timing_policy) for note in current_notes)
    selected_keys = {_voice_identity_key(note) for note in current_notes}
    selected_pitches = {int(note.note) for note in current_notes}
    out: list[NoteEvent] = []
    for note in existing_notes:
        prior_event = event_by_id.get(str(note.expression_event_id or ""))
        if prior_event is None or prior_event.region_id != current_event.region_id or prior_event.track != current_event.track:
            out.append(note)
            continue
        if float(note.start_beat) >= current_start - 1e-9:
            out.append(note)
            continue
        prior_start = _performed_start_for_partial_release(note, timing_policy)
        note_end = prior_start + float(note.duration_beats)
        if note_end <= current_start + 1e-9:
            out.append(note)
            continue
        if _voice_identity_key(note) not in selected_keys and int(note.note) not in selected_pitches:
            out.append(note)
            continue
        new_duration = max(0.05, current_start - prior_start)
        if new_duration >= float(note.duration_beats) - 1e-9:
            out.append(note)
            continue
        pedal_debug = dict(note.pedal_debug or {})
        pedal_debug.update(
            {
                "partial_reattack_release_version": "v2_5_4",
                "partial_reattack_release_applied": True,
                "partial_reattack_release_reason": "inner_movement_restruck_motion_voice_foundation_held",
                "partial_reattack_source_event_id": current_event.event_id,
                "partial_reattack_original_duration_beats": round(float(note.duration_beats), 6),
                "partial_reattack_trimmed_duration_beats": round(float(new_duration), 6),
                "realizer_note_audit_cleanup_version": REALIZER_NOTE_AUDIT_CLEANUP_VERSION,
            }
        )
        out.append(replace(note, duration_beats=new_duration, pedal_debug=pedal_debug))
    return out


def _performed_start_for_partial_release(note: NoteEvent, timing_policy: Mapping[str, Any] | None = None) -> float:
    """Return the rendered timing-grid start used for partial reattack trims.

    This mirrors the expression-layer duration adjacency rule without importing
    the MIDI renderer.  The realized NoteEvent still carries logical grid
    timing; trimming against the performed swing upbeat avoids a small audible
    gap between a held Ballad foundation and a swung 1& upper re-touch.
    """

    intent = str(getattr(note, "timing_intent", "auto") or "auto")
    beat = float(getattr(note, "start_beat", 0.0) or 0.0)
    if intent in {"straight_even", "literal"}:
        return beat
    policy = dict(timing_policy or {})
    feel = str(policy.get("feel", "straight")).strip().lower()
    if intent == "swing_upbeat" or (intent == "auto" and feel == "swing"):
        half_grid = float(policy.get("half_beat_grid", 0.5) or 0.5)
        ratio = float(policy.get("swing_ratio", 2.0 / 3.0) or (2.0 / 3.0))
        whole = int(beat)
        frac = beat - whole
        if abs(frac - half_grid) < 1e-6:
            return whole + ratio
    return beat


def sync_piano_audit_realized_notes(audit_events: list[dict[str, Any]], final_notes: list[NoteEvent]) -> list[dict[str, Any]]:
    notes_by_expression_event: dict[str, list[NoteEvent]] = {}
    for note in final_notes:
        if note.expression_event_id:
            notes_by_expression_event.setdefault(str(note.expression_event_id), []).append(note)
    synced: list[dict[str, Any]] = []
    for row in audit_events:
        event_id = str(row.get("event_id") or "")
        if event_id in notes_by_expression_event:
            row = dict(row)
            row["realized_notes"] = [note_event_debug(note) for note in notes_by_expression_event[event_id]]
        synced.append(row)
    return synced


def piano_audit_event(
    event: PatternEvent,
    expression: EventExpression,
    voicing: VoicingPlan,
    realized_notes: list[NoteEvent],
) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "pattern_event": {
            "event_id": event.event_id,
            "track": event.track,
            "region_id": event.region_id,
            "chord_symbol": event.chord_symbol,
            "onset_beat": event.onset_beat,
            "local_beat": event.local_beat,
            "role": event.role,
            "gesture_type": event.gesture_type,
            "gesture": gesture_debug(event),
            "expression_hint": event.expression_hint,
            "pattern_id": event.pattern_id,
            "source_event_id": event.source_event_id,
            "status": event.status,
            "metadata": dict(event.metadata),
        },
        "expression": asdict(expression),
        "voicing": voicing.to_debug_dict(),
        "realized_notes": [note_event_debug(note) for note in realized_notes],
        "realizer_note_audit_cleanup_version": REALIZER_NOTE_AUDIT_CLEANUP_VERSION,
    }


def gesture_debug(event: PatternEvent) -> dict[str, Any]:
    gesture = event.gesture
    return {
        "gesture_type": gesture.gesture_type,
        "projection_refs": list(gesture.projection_refs),
        "onset_offsets_beats": list(gesture.onset_offsets_beats),
        "metadata": dict(gesture.metadata),
    }


def note_event_debug(note: NoteEvent) -> dict[str, Any]:
    return {
        "track": note.track,
        "channel": note.channel,
        "note": note.note,
        "velocity": note.velocity,
        "start_beat": note.start_beat,
        "duration_beats": note.duration_beats,
        "timing_intent": note.timing_intent,
        "voice_role": note.voice_role,
        "group_id": note.group_id,
        "projection_ref": note.projection_ref,
        "voicing_event_id": note.voicing_event_id,
        "expression_event_id": note.expression_event_id,
        "pedal": note.pedal,
        "release_beats": note.release_beats,
        "pedal_debug": dict(note.pedal_debug),
    }


def _voice_identity_key(note: NoteEvent) -> tuple[str | None, str | None, str | None]:
    return (note.voice_role, note.group_id, note.projection_ref)
