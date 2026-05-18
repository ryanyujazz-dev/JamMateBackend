from __future__ import annotations

from dataclasses import dataclass

from jammate_engine.core.expression.expression_plan import EventExpression
from jammate_engine.core.gestures.gesture import GestureKind, GestureRequest, gesture_request
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from jammate_engine.core.voicing import VoicedNote, VoicingPlan

from .note_event_builder import NoteEvent


CHANNELS = {"piano": 0, "bass": 1, "drums": 9}


@dataclass(frozen=True)
class ProjectedVoice:
    """A realized reference to an already-selected voicing voice.

    This diagnostic wrapper is intentionally not a new musical decision layer.
    It records which ``GestureRequest`` projection ref selected a given
    ``VoicedNote`` so downstream tests/audits can prove realization consumed the
    provided ``VoicingPlan`` rather than reselecting pitch content.
    """

    note: VoicedNote
    projection_ref: str


class GestureRealizer:
    """Project a pitchless gesture request onto an already-resolved voicing.

    This class is deliberately small in the V2 foundation. It establishes the boundary:
    style asks for a gesture, core voicing supplies vertical notes, and core
    realization maps abstract voice/group references onto NoteEvents.
    """

    def realize_harmonic_event(
        self,
        event: PatternEvent,
        voicing: VoicingPlan,
        expression: EventExpression,
    ) -> list[NoteEvent]:
        request = self._gesture_for(event)
        projected = self._projected_voices(request, voicing)
        offsets = self._offsets_for(request, len(projected))

        out: list[NoteEvent] = []
        for projected_voice, offset in zip(projected, offsets):
            note = projected_voice.note
            start = event.onset_beat + offset
            duration = max(0.05, expression.duration_beats - offset)
            out.append(
                NoteEvent(
                    track=event.track,
                    channel=CHANNELS.get(event.track, 0),
                    note=note.midi_note,
                    velocity=expression.velocity,
                    start_beat=start,
                    duration_beats=duration,
                    timing_intent=str(event.metadata.get("timing_intent", "auto")),
                    voice_role=note.voice_role,
                    group_id=note.group_id,
                    projection_ref=projected_voice.projection_ref,
                    voicing_event_id=voicing.event_id,
                    expression_event_id=event.event_id,
                    pedal=str(expression.pedal or "none"),
                    release_beats=float(expression.release_beats or 0.0),
                    pedal_debug={
                        "pedal_source": "event_expression",
                        "expression_profile": expression.profile_name,
                        "articulation": expression.articulation,
                        "touch": expression.touch,
                    },
                )
            )
        return out

    def _gesture_for(self, event: PatternEvent) -> GestureRequest:
        if event.gesture is not None:
            return event.gesture
        return gesture_request(event.gesture_type)

    def _offsets_for(self, request: GestureRequest, count: int) -> tuple[float, ...]:
        if count <= 0:
            return ()
        if request.kind == GestureKind.SIMULTANEOUS_ONSET:
            return tuple(0.0 for _ in range(count))

        if request.onset_offsets_beats:
            offsets = list(request.onset_offsets_beats)
            while len(offsets) < count:
                offsets.append(offsets[-1])
            return tuple(offsets[:count])

        if request.kind == GestureKind.ROLLED_ONSET:
            return tuple(index * 0.04 for index in range(count))

        if request.kind in {GestureKind.ARPEGGIATED_ONSET, GestureKind.BROKEN_CHORD}:
            return tuple(index * 0.25 for index in range(count))

        # Inner movement is a partial reattack gesture in v2_5_4.  Timing is
        # simultaneous by default; the important distinction is voice selection,
        # handled by _projected_voices without appending unselected foundation
        # voices.
        return tuple(0.0 for _ in range(count))

    def _projected_voices(self, request: GestureRequest, voicing: VoicingPlan) -> list[ProjectedVoice]:
        notes = list(voicing.notes)
        if not request.projection_refs:
            if request.kind == GestureKind.INNER_MOVEMENT:
                return self._default_inner_movement_voices(notes)
            return [ProjectedVoice(note=note, projection_ref="all_voices") for note in notes]

        selected: list[ProjectedVoice] = []
        used: set[int] = set()
        for raw_ref in request.projection_refs:
            ref = self._normalize_projection_ref(raw_ref)
            matched = False

            if ref in voicing.projection_map:
                for idx in voicing.projection_map.get(ref, []):
                    if 0 <= idx < len(notes) and idx not in used:
                        selected.append(ProjectedVoice(note=notes[idx], projection_ref=ref))
                        used.add(idx)
                        matched = True
                continue

            for idx, note in enumerate(notes):
                if idx in used:
                    continue
                if self._matches_ref(note, ref):
                    selected.append(ProjectedVoice(note=note, projection_ref=ref))
                    used.add(idx)
                    matched = True

            # Unknown projection refs are intentionally ignored.  For chordal
            # gestures, the append-unselected fallback below preserves legacy
            # all-voices behavior.  For INNER_MOVEMENT, v2_5_4 must not append
            # foundation/common-tone voices, because that would turn a partial
            # reattack back into a low-level full-chord hit.
            _ = matched

        if request.kind == GestureKind.INNER_MOVEMENT:
            return selected or self._default_inner_movement_voices(notes)

        for idx, note in enumerate(notes):
            if idx not in used:
                selected.append(ProjectedVoice(note=note, projection_ref="all_voices"))
        return selected

    def _default_inner_movement_voices(self, notes: list[VoicedNote]) -> list[ProjectedVoice]:
        if not notes:
            return []
        inner = [
            ProjectedVoice(note=note, projection_ref="inner_default")
            for note in notes
            if note.voice_role.lower().startswith("inner")
        ]
        if inner:
            return inner[:2]
        if len(notes) >= 2:
            return [ProjectedVoice(note=notes[-1], projection_ref="top_default")]
        return [ProjectedVoice(note=notes[0], projection_ref="all_voices_default")]

    def _ordered_notes(self, request: GestureRequest, notes: list[VoicedNote]) -> list[VoicedNote]:
        """Backward-compatible helper retained for older tests/callers.

        New realization should use ``_projected_voices`` with a full
        ``VoicingPlan`` so abstract group refs can be resolved through
        ``projection_map``.
        """

        voicing = VoicingPlan(event_id="compat", chord_symbol="", notes=list(notes))
        return [projected.note for projected in self._projected_voices(request, voicing)]

    def _matches_ref(self, note: VoicedNote, ref: str) -> bool:
        ref = ref.lower()
        role = note.voice_role.lower()
        group_id = (note.group_id or "").lower()
        if ref == role:
            return True
        if ref == group_id:
            return True
        if ref == "inner" and role.startswith("inner"):
            return True
        if ref == "lowest" and role == "lowest":
            return True
        if ref == "top" and role == "top":
            return True
        return False

    def _normalize_projection_ref(self, value: str) -> str:
        text = str(value).strip().lower()
        for separator in (":", "."):
            if separator in text:
                prefix, payload = text.split(separator, 1)
                if prefix in {"voice_ref", "voice", "group_ref", "group"}:
                    return payload.strip()
        return text
