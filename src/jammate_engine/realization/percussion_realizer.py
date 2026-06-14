from __future__ import annotations

from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent
from .note_event_builder import NoteEvent

DRUM_NOTES = {
    "ride": 51,
    "ride_bell": 53,
    "hihat": 42,
    "hihat_pedal": 44,
    "kick": 36,
    "snare": 38,
    "cross_stick": 37,
    "low_tom": 45,
    "mid_tom": 47,
    "high_tom": 50,
    "shaker": 42,
}

DYNAMIC_VELOCITY = {
    "medium": 58,
    "soft": 54,
    "ghost": 45,
    "pp": 28,
    "p": 34,
    "feather": 24,
    "hat": 50,
    "accent": 70,
    "shaker_light": 34,
    "bossa_cross_main": 44,
    "bossa_cross_light": 39,
    "bossa_kick_root": 35,
    "bossa_kick_fifth": 31,
    "shaker_breath": 29,
    "bossa_cross_breath": 36,
    "bossa_cross_breath_light": 32,
    "bossa_kick_root_breath": 29,
    "bossa_kick_fifth_breath": 25,
    "shaker_release": 27,
    "bossa_cross_release": 34,
    "bossa_cross_release_light": 30,
    "bossa_kick_root_release": 27,
    "bossa_kick_fifth_release": 24,
    "shaker_lift": 37,
    "bossa_cross_lift": 48,
    "bossa_cross_lift_light": 42,
    "bossa_kick_root_lift": 38,
    "bossa_kick_fifth_lift": 34,
    "bossa_marker_micro": 35,
    "bossa_marker_turnaround_light": 39,
    "bossa_marker_ending_soft": 36,
    "brush_motion_pp": 23,
    "brush_skip_pp": 20,
    "brush_breath_pp": 19,
    "brush_hat_p": 30,
    "brush_hat_pp": 24,
    "brush_feather": 18,
    "brush_cymbal_pp": 22,
    "brush_hint_pp": 24,
    "brush_hint_p": 29,
    "brush_fill_pickup_p": 36,
    "brush_fill_drag_mp": 42,
    "brush_fill_release_mp": 46,
    "brush_fill_release_mf": 52,
    "brush_fill_cymbal_p": 38,
}

STROKE_DURATION = {
    "swing_time": 0.08,
    "short": 0.08,
    "choked": 0.05,
    "brush_sweep": 0.28,
    "brush_swish": 0.18,
    "brush_foot": 0.06,
    "brush_cymbal": 0.32,
    "brush_hint_tap": 0.08,
    "brush_hint_swish": 0.14,
    "brush_hint_release": 0.18,
    "brush_fill_tap": 0.11,
    "brush_fill_swish": 0.20,
    "brush_fill_drag": 0.30,
    "brush_fill_release": 0.34,
    "feather": 0.05,
}

BOSSA_SHAKER_PULSE_SLOT_OFFSET = {
    "primary_clear": 4,
    "secondary_mid": 1,
    "offbeat_light": -2,
    "offbeat_feather": -4,
}

BOSSA_SHAKER_ARC_BOUNDS = {
    "shaker_light": (28, 41),
    "shaker_breath": (23, 35),
    "shaker_release": (21, 33),
    "shaker_lift": (31, 45),
}

BOSSA_CROSS_STICK_PHRASE_SLOT_OFFSET = {
    "A_beat1_phrase_anchor": 1,
    "A_2and_syncopated_answer": -2,
    "A_beat4_phrase_tail": 0,
    "B_beat2_response_anchor": 0,
    "B_3and_light_answer": -3,
    "split_region_light_mark": -3,
}

BOSSA_CROSS_STICK_CONTOUR_OFFSET = {
    "identity_clear": 0,
    "warm_flow_full": 0,
    "breath_space_reduced": -2,
    "settled_release_sparse": -4,
    "gentle_lift_clear": 2,
    "split_region_single_mark": -2,
}

BOSSA_CROSS_STICK_ARC_BOUNDS = {
    "bossa_cross_main": (38, 48),
    "bossa_cross_light": (33, 42),
    "bossa_cross_breath": (29, 39),
    "bossa_cross_breath_light": (26, 36),
    "bossa_cross_release": (26, 36),
    "bossa_cross_release_light": (24, 34),
    "bossa_cross_lift": (42, 52),
    "bossa_cross_lift_light": (36, 46),
}

BOSSA_KICK_LOCK_SLOT_OFFSET = {
    "root_on_1_locked_shadow": 0,
    "fifth_on_3_locked_shadow": -3,
}

BOSSA_KICK_SHADOW_ARC_BOUNDS = {
    "bossa_kick_root": (30, 38),
    "bossa_kick_fifth": (25, 33),
    "bossa_kick_root_breath": (24, 32),
    "bossa_kick_fifth_breath": (20, 28),
    "bossa_kick_root_release": (22, 30),
    "bossa_kick_fifth_release": (19, 26),
    "bossa_kick_root_lift": (33, 41),
    "bossa_kick_fifth_lift": (28, 36),
}

BOSSA_LIGHT_MARKER_SLOT_OFFSET = {
    "micro_4and": -2,
    "turnaround_3and": -1,
    "turnaround_4and": 1,
    "ending_3and": -2,
    "ending_4": 0,
    "ending_4and": 1,
    "ending_short_region_4": -1,
    "ending_short_region_4and": 1,
}

BOSSA_LIGHT_MARKER_BOUNDS = {
    "bossa_marker_micro": (29, 38),
    "bossa_marker_turnaround_light": (33, 44),
    "bossa_marker_ending_soft": (29, 40),
}


def _stable_tiny_shaker_variation(event: PatternEvent) -> int:
    token = f"{event.region_id}:{event.local_beat}:{event.pattern_id}"
    value = sum(ord(ch) for ch in token) % 3
    return value - 1


def _stable_tiny_cross_stick_variation(event: PatternEvent) -> int:
    token = f"cross:{event.region_id}:{event.local_beat}:{event.pattern_id}"
    value = sum(ord(ch) for ch in token) % 3
    return value - 1


def _stable_tiny_kick_shadow_variation(event: PatternEvent) -> int:
    token = f"kick:{event.region_id}:{event.local_beat}:{event.pattern_id}"
    value = sum(ord(ch) for ch in token) % 3
    return value - 1


def _stable_tiny_light_marker_variation(event: PatternEvent) -> int:
    token = f"marker:{event.region_id}:{event.local_beat}:{event.pattern_id}"
    value = sum(ord(ch) for ch in token) % 3
    return value - 1



def _resolve_velocity(event: PatternEvent, dynamic_profile: str) -> int:
    base = int(DYNAMIC_VELOCITY.get(dynamic_profile, 55))
    if event.metadata.get("shaker_microdynamic_enabled") is True and event.metadata.get("drum") == "shaker":
        slot = str(event.metadata.get("shaker_pulse_slot") or "")
        base += int(BOSSA_SHAKER_PULSE_SLOT_OFFSET.get(slot, 0))
        base += _stable_tiny_shaker_variation(event)
        lo, hi = BOSSA_SHAKER_ARC_BOUNDS.get(dynamic_profile, (20, 50))
        return max(int(lo), min(int(hi), base))
    if event.metadata.get("bossa_light_marker_fill_policy_active") is True and event.metadata.get("drum") == "cross_stick":
        slot = str(event.metadata.get("bossa_light_marker_fill_policy_slot") or "")
        base += int(BOSSA_LIGHT_MARKER_SLOT_OFFSET.get(slot, 0))
        base += _stable_tiny_light_marker_variation(event)
        lo, hi = BOSSA_LIGHT_MARKER_BOUNDS.get(dynamic_profile, (26, 44))
        return max(int(lo), min(int(hi), base))
    if event.metadata.get("bossa_drum_cross_stick_phrase_local_contour_active") is True and event.metadata.get("drum") == "cross_stick":
        slot = str(event.metadata.get("cross_stick_phrase_slot") or "")
        contour = str(event.metadata.get("cross_stick_contour_density") or "")
        base += int(BOSSA_CROSS_STICK_PHRASE_SLOT_OFFSET.get(slot, 0))
        base += int(BOSSA_CROSS_STICK_CONTOUR_OFFSET.get(contour, 0))
        base += _stable_tiny_cross_stick_variation(event)
        lo, hi = BOSSA_CROSS_STICK_ARC_BOUNDS.get(dynamic_profile, (24, 52))
        return max(int(lo), min(int(hi), base))
    if event.metadata.get("bossa_kick_bass_lock_and_low_frequency_shadow_active") is True and event.metadata.get("drum") == "kick":
        slot = str(event.metadata.get("kick_bass_lock_slot") or "")
        base += int(BOSSA_KICK_LOCK_SLOT_OFFSET.get(slot, 0))
        base += _stable_tiny_kick_shadow_variation(event)
        lo, hi = BOSSA_KICK_SHADOW_ARC_BOUNDS.get(dynamic_profile, (18, 42))
        return max(int(lo), min(int(hi), base))
    return base


class PercussionRealizer:
    def realize(self, events: list[PatternEvent]) -> list[NoteEvent]:
        out: list[NoteEvent] = []
        for event in events:
            if event.status != "active" or event.track != "drums":
                continue
            drum = event.metadata.get("drum", "ride")
            dynamic_profile = str(event.metadata.get("dynamic_profile", "medium"))
            stroke_profile = str(event.metadata.get("stroke_profile", "short"))
            out.append(
                NoteEvent(
                    track="drums",
                    channel=9,
                    note=DRUM_NOTES.get(drum, 51),
                    velocity=_resolve_velocity(event, dynamic_profile),
                    start_beat=event.onset_beat,
                    duration_beats=STROKE_DURATION.get(stroke_profile, 0.1),
                    timing_intent=str(event.metadata.get("timing_intent", "auto")),
                )
            )
        return out
