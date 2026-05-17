from __future__ import annotations

from collections.abc import Mapping

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from .expression_plan import EventExpression, ExpressionPlan
from .policy import ExpressionPolicyBundle


EXPRESSION_REGION_DURATION_CLAMP_VERSION = "v2_2_51"
EXPRESSION_ANTICIPATION_TIE_DURATION_VERSION = "v2_3_9"
EXPRESSION_NEXT_EVENT_CLAMP_VERSION = "v2_3_9"
EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION = "v2_3_9"


class ExpressionResolver:
    """Resolve pitchless events into final performance expression.

    Styles may name expression hints such as ``core_short`` or
    ``soft_sustain``, but only this core resolver turns those hints into final
    duration, velocity, articulation, touch, pedal and release values.
    """

    def resolve(
        self,
        events: list[PatternEvent],
        style_policy: ExpressionPolicyBundle | Mapping | None = None,
    ) -> ExpressionPlan:
        policy = self._coerce_policy(style_policy)
        resolved: dict[str, EventExpression] = {}
        active_events = [event for event in events if event.status == "active"]
        next_same_track_starts = self._next_same_track_starts(active_events)
        for event in events:
            if event.status != "active":
                continue
            profile = policy.profile_for(event.expression_hint, event.track)
            duration_beats, duration_metadata = self._resolve_duration(
                event,
                profile.duration_beats,
                next_same_track_start=next_same_track_starts.get(event.event_id),
                policy_metadata=policy.metadata,
                profile_name=profile.name,
            )
            pedal, release_beats, pedal_release_metadata = self._resolve_pedal_release(
                event,
                profile,
                duration_metadata,
                policy_metadata=policy.metadata,
            )
            resolved[event.event_id] = EventExpression(
                event_id=event.event_id,
                duration_beats=duration_beats,
                velocity=profile.velocity,
                articulation=profile.articulation.value,
                pedal=pedal,
                touch=profile.touch.value,
                release_beats=release_beats,
                accent=profile.accent,
                profile_name=profile.name,
                metadata={**dict(profile.metadata), **duration_metadata, **pedal_release_metadata},
            )
        return ExpressionPlan(events=resolved)

    def _resolve_duration(
        self,
        event: PatternEvent,
        requested_duration: float,
        *,
        next_same_track_start: float | None = None,
        policy_metadata: Mapping | None = None,
        profile_name: str | None = None,
    ) -> tuple[float, dict]:
        anticipation = dict((event.metadata or {}).get("anticipation") or {})
        if anticipation.get("kind") == "next_beat1_to_previous_tail" and bool(anticipation.get("tie_from_previous", False)):
            duration, metadata = self._duration_for_anticipated_tie(
                event,
                requested_duration,
                anticipation,
                policy_metadata=policy_metadata,
                profile_name=profile_name,
            )
        else:
            duration, metadata = self._duration_clamped_to_region(event, requested_duration)
        return self._duration_clamped_to_next_same_track_event(event, duration, metadata, next_same_track_start=next_same_track_start)

    def _duration_clamped_to_next_same_track_event(
        self,
        event: PatternEvent,
        duration: float,
        metadata: dict,
        *,
        next_same_track_start: float | None,
    ) -> tuple[float, dict]:
        """Avoid sustained harmony overlapping the next same-track onset.

        Region clamps protect dense harmonic rhythm, but anticipation inserts can
        create a closer next event inside the previous region tail.  Bossa is the
        clearest case: the 3& core-batida sustain is correct when the bar tail is
        empty, but it must release before a 4& next-chord anticipation.  This
        guard runs after region/anticipation-tie duration resolution and only
        trims an event when a later active event on the same track is close.
        """

        metadata = dict(metadata)
        metadata.update(
            {
                "duration_next_event_clamp_version": EXPRESSION_NEXT_EVENT_CLAMP_VERSION,
                "duration_next_event_clamp_applied": False,
                "duration_next_event_clamp_reason": "next_same_track_event_missing",
            }
        )
        if next_same_track_start is None:
            return duration, metadata

        gap = max(0.0, float(next_same_track_start) - float(event.onset_beat))
        metadata["duration_next_event_gap_beats"] = round(gap, 6)
        if gap <= 0.0:
            return duration, metadata
        if float(duration) <= gap + 1e-9:
            metadata["duration_next_event_clamp_reason"] = "within_next_same_track_gap"
            return duration, metadata

        # Keep the event audible and allow exact sustain-to-next-onset ties, but
        # do not let it ring past the next same-track harmonic attack.
        clamped = max(0.05, min(float(duration), gap))
        metadata.update(
            {
                "duration_next_event_clamp_applied": clamped < float(duration) - 1e-9,
                "duration_next_event_clamp_reason": "clamped_to_next_same_track_event",
                "duration_before_next_event_clamp_beats": round(float(duration), 6),
                "duration_clamped_beats": clamped,
            }
        )
        return clamped, metadata

    def _duration_for_anticipated_tie(
        self,
        event: PatternEvent,
        requested_duration: float,
        anticipation: dict,
        *,
        policy_metadata: Mapping | None = None,
        profile_name: str | None = None,
    ) -> tuple[float, dict]:
        """Let a next-chord anticipation ring across the barline.

        Ordinary events are clamped to their own chord region so long ballad
        profiles do not blur through dense harmonic changes. An anticipated
        event is different: it is the next region's beat-1 event intentionally
        moved to the previous 4& and tied from there. Therefore its realized
        duration must include the lead-in distance plus the duration that the
        original beat-1 event would have received inside the source region.
        """

        requested = max(0.05, float(requested_duration))
        logical_lead_in = _coerce_float(anticipation.get("logical_lead_in_beats"), None)
        if logical_lead_in is None:
            logical_lead_in = _coerce_float(anticipation.get("lead_in_beats"), None)
        lead_in = _coerce_float(anticipation.get("performed_lead_in_beats"), None)
        if lead_in is None:
            original_onset = _coerce_float(anticipation.get("original_onset_beat"), None)
            if original_onset is None:
                target_offset = _coerce_float(anticipation.get("target_offset_beats"), 0.0)
                lead_in = abs(float(target_offset or 0.0))
            else:
                lead_in = abs(float(original_onset) - float(event.onset_beat))
        lead_in = max(0.0, float(lead_in))
        if logical_lead_in is None:
            logical_lead_in = lead_in
        logical_lead_in = max(0.0, float(logical_lead_in))

        source_region_duration = _coerce_float(anticipation.get("source_region_duration_beats"), None)
        original_local = _coerce_float(anticipation.get("original_local_beat_in_source"), 0.0) or 0.0
        if source_region_duration is None:
            original_region_duration = event.metadata.get("region_duration_beats")
            source_region_duration = _coerce_float(original_region_duration, None)

        if source_region_duration is None:
            original_sustain = requested
            source_remaining = None
            original_clamp_applied = False
        else:
            source_remaining = max(0.0, float(source_region_duration) - float(original_local))
            original_sustain = max(0.05, min(requested, source_remaining)) if source_remaining > 0 else 0.05
            original_clamp_applied = original_sustain < requested - 1e-9

        duration = max(0.05, lead_in + original_sustain)
        duration, micro_duration_metadata = _micro_tuned_anticipated_duration(
            duration,
            lead_in=lead_in,
            original_sustain=original_sustain,
            style_id=str((policy_metadata or {}).get("style", "")),
            profile_name=profile_name or event.expression_hint or "",
        )
        return duration, {
            "duration_region_clamp_version": EXPRESSION_REGION_DURATION_CLAMP_VERSION,
            "duration_region_clamp_applied": False,
            "duration_region_clamp_reason": "anticipated_tie_crosses_region_boundary",
            "duration_requested_beats": requested,
            "duration_anticipation_tie_version": EXPRESSION_ANTICIPATION_TIE_DURATION_VERSION,
            "duration_anticipation_tie_applied": True,
            "duration_anticipation_lead_in_beats": round(lead_in, 6),
            "duration_anticipation_performed_lead_in_beats": round(lead_in, 6),
            "duration_anticipation_logical_lead_in_beats": round(logical_lead_in, 6),
            "duration_anticipation_timing_grid_contract_version": anticipation.get("timing_grid_contract_version"),
            "duration_anticipation_timing_grid": anticipation.get("timing_grid"),
            "duration_anticipation_target_timing_intent": anticipation.get("target_timing_intent"),
            "duration_anticipation_original_sustain_beats": round(original_sustain, 6),
            "duration_anticipation_source_region_remaining_beats": None if source_remaining is None else round(source_remaining, 6),
            "duration_anticipation_original_region_clamp_applied": original_clamp_applied,
            "duration_clamped_beats": duration,
            **micro_duration_metadata,
        }


    def _resolve_pedal_release(
        self,
        event: PatternEvent,
        profile,
        duration_metadata: dict,
        *,
        policy_metadata: Mapping | None = None,
    ) -> tuple[str, float, dict]:
        """Apply style-specific release/pedal semantics for anticipated chords.

        Anticipation timing and pitchless movement are owned by the
        AnticipationResolver. This expression-layer pass only refines how the
        already-moved event releases: Bossa anticipations stay dry and clean,
        Ballad anticipations use a lighter pedal than ordinary long anchors, and
        Medium Swing anticipations stay dry/short so the push does not smear.
        """

        pedal = profile.pedal.value
        release = float(profile.release_beats)
        metadata = {
            "anticipation_pedal_release_micro_tuning_version": EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION,
            "anticipation_pedal_release_micro_tuning_applied": False,
            "anticipation_pedal_release_micro_tuning_reason": "not_anticipated_tie",
            "anticipation_original_pedal": pedal,
            "anticipation_original_release_beats": release,
        }
        if not bool(duration_metadata.get("duration_anticipation_tie_applied", False)):
            return pedal, release, metadata

        style_id = str((policy_metadata or {}).get("style", "")).strip().lower()
        profile_name = str(profile.name or event.expression_hint or "").strip().lower()
        metadata["anticipation_pedal_release_micro_tuning_applied"] = True
        metadata["anticipation_pedal_release_style"] = style_id or "unknown"

        if style_id == "bossa_nova":
            # A Bossa 4& anticipation should connect into the next downbeat but
            # release cleanly; do not let the light pedal from the ordinary 3&
            # sustain profile blur the next chord.
            pedal = "none"
            release = 0.025 if profile_name == "core_short" else 0.04
            reason = "bossa_dry_clean_anticipation_release"
        elif style_id == "jazz_ballad":
            # Ballad anticipations should be connected, but a full sustain pedal
            # on the 4& push can blur the barline. Use light pedal metadata and
            # a slightly shorter release while keeping the tied duration.
            pedal = "light"
            release = min(release, 0.08) if release > 0 else 0.08
            reason = "ballad_light_pedal_connected_anticipation"
        elif style_id == "medium_swing":
            pedal = "none"
            release = min(release, 0.03) if release > 0 else 0.03
            reason = "swing_dry_short_push_release"
        else:
            reason = "generic_anticipated_tie_preserve_profile_pedal_release"

        metadata.update(
            {
                "anticipation_pedal_release_micro_tuning_reason": reason,
                "anticipation_resolved_pedal": pedal,
                "anticipation_resolved_release_beats": release,
            }
        )
        return pedal, release, metadata

    def _duration_clamped_to_region(self, event: PatternEvent, requested_duration: float) -> tuple[float, dict]:
        """Keep realized expression inside its own harmonic/chord region.

        Patterns remain pitchless and style expression profiles still express the
        desired sustain character.  This core guard only prevents a concrete
        duration from spilling over the current ``HarmonicRegion`` once region
        metadata is available.  It is especially important for Ballad SPREAD
        listening isolation, where long warm voicings can otherwise blur across
        dense two-chord bars.
        """

        requested = max(0.05, float(requested_duration))
        region_duration = event.metadata.get("region_duration_beats")
        if region_duration is None:
            return requested, {
                "duration_region_clamp_version": EXPRESSION_REGION_DURATION_CLAMP_VERSION,
                "duration_region_clamp_applied": False,
                "duration_region_clamp_reason": "region_duration_missing",
                "duration_requested_beats": requested,
            }

        local_beat = float(event.local_beat or 0.0)
        remaining = max(0.0, float(region_duration) - local_beat)
        if remaining <= 0.0:
            clamped = 0.05
        else:
            clamped = max(0.05, min(requested, remaining))
        applied = clamped < requested - 1e-9
        return clamped, {
            "duration_region_clamp_version": EXPRESSION_REGION_DURATION_CLAMP_VERSION,
            "duration_region_clamp_applied": applied,
            "duration_region_clamp_reason": "clamped_to_chord_region_end" if applied else "within_chord_region",
            "duration_requested_beats": requested,
            "duration_region_remaining_beats": remaining,
            "duration_clamped_beats": clamped,
        }

    def _next_same_track_starts(self, events: list[PatternEvent]) -> dict[str, float | None]:
        grouped: dict[str, list[PatternEvent]] = {}
        for event in events:
            grouped.setdefault(event.track, []).append(event)
        result: dict[str, float | None] = {}
        for track_events in grouped.values():
            ordered = sorted(track_events, key=lambda event: (event.onset_beat, event.region_id, event.event_id))
            for index, event in enumerate(ordered):
                next_start = None
                for later in ordered[index + 1 :]:
                    if later.onset_beat > event.onset_beat + 1e-6:
                        next_start = float(later.onset_beat)
                        break
                result[event.event_id] = next_start
        return result

    def _coerce_policy(self, style_policy: ExpressionPolicyBundle | Mapping | None) -> ExpressionPolicyBundle:
        if isinstance(style_policy, ExpressionPolicyBundle):
            return style_policy
        return ExpressionPolicyBundle.from_legacy_dict(style_policy)


def _micro_tuned_anticipated_duration(
    duration: float,
    *,
    lead_in: float,
    original_sustain: float,
    style_id: str,
    profile_name: str,
) -> tuple[float, dict]:
    style = str(style_id or "").strip().lower()
    profile = str(profile_name or "").strip().lower()
    cap: float | None = None
    reason = "no_style_specific_duration_micro_tuning"
    if style == "bossa_nova":
        # Keep the 4& anticipated chord connected through beat 1, but avoid a
        # long held Bossa stab after the downbeat.
        cap = 0.36 if profile == "core_short" else 1.05
        reason = "bossa_clean_post_downbeat_release_cap"
    elif style == "jazz_ballad":
        # Preserve the ballad tie but avoid letting every 4& anticipation ring
        # almost the whole next bar.  This is intentionally soft; next-event
        # clamp remains the hard overlap guard.
        cap = 2.85
        reason = "ballad_connected_but_not_full_bar_anticipation_cap"
    elif style == "medium_swing":
        # Swing pushes should not become long pad-like chords.
        cap = 0.72
        reason = "swing_short_push_post_downbeat_release_cap"

    if cap is None or original_sustain <= cap + 1e-9:
        return duration, {
            "duration_anticipation_micro_tuning_version": EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION,
            "duration_anticipation_micro_tuning_applied": False,
            "duration_anticipation_micro_tuning_reason": reason,
            "duration_anticipation_post_downbeat_sustain_cap": cap,
        }
    tuned = max(0.05, float(lead_in) + float(cap))
    return tuned, {
        "duration_anticipation_micro_tuning_version": EXPRESSION_ANTICIPATION_PEDAL_RELEASE_VERSION,
        "duration_anticipation_micro_tuning_applied": True,
        "duration_anticipation_micro_tuning_reason": reason,
        "duration_anticipation_post_downbeat_sustain_cap": cap,
        "duration_anticipation_pre_micro_tuning_beats": round(float(duration), 6),
        "duration_anticipation_post_micro_tuning_beats": round(float(tuned), 6),
    }


def _coerce_float(value, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
