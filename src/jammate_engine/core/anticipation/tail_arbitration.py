from __future__ import annotations

from dataclasses import dataclass

from jammate_engine.core.harmony.harmonic_region import HarmonicRegion
from jammate_engine.core.pattern_runtime.pattern_event import PatternEvent


@dataclass(frozen=True)
class TailAvailability:
    can_place_anticipation: bool
    reason: str = ""
    target_local_beat: float | None = None
    checked_local_beats: tuple[float, ...] = ()


def is_tail_slot_available(
    *,
    previous_region: HarmonicRegion,
    previous_events: list[PatternEvent],
    target_abs_beat: float,
    eligible_tracks: tuple[str, ...],
    eligible_roles: tuple[str, ...],
    require_last_beat_empty: bool = True,
    require_last_upbeat_empty: bool = True,
    epsilon: float = 1e-6,
) -> TailAvailability:
    """Check whether a previous region can receive a next-chord anticipation.

    This is intentionally pitchless and track-aware. A drum ride on beat 4 should
    not automatically block a piano chord anticipation; only eligible pitchless
    harmonic events on the same policy-controlled track/role family are treated
    as occupying the harmonic tail slot.
    """

    region_start = float(previous_region.start_beat)
    region_end = region_start + float(previous_region.duration_beats)
    if target_abs_beat < region_start - epsilon or target_abs_beat >= region_end - epsilon:
        return TailAvailability(False, "target_is_not_inside_previous_region")

    target_local = round(float(target_abs_beat) - region_start, 6)
    last_beat_local = round(max(0.0, float(previous_region.duration_beats) - 1.0), 6)
    last_upbeat_local = round(max(0.0, float(previous_region.duration_beats) - 0.5), 6)
    checked: list[float] = []
    if require_last_beat_empty:
        checked.append(last_beat_local)
    if require_last_upbeat_empty:
        checked.append(last_upbeat_local)

    occupied: set[float] = set()
    for event in previous_events:
        if event.status != "active":
            continue
        if event.track not in eligible_tracks or event.role not in eligible_roles:
            continue
        if event.local_beat is not None:
            occupied.add(round(float(event.local_beat), 6))
        else:
            occupied.add(round(float(event.onset_beat) - region_start, 6))

    for local_beat in checked:
        if any(abs(local_beat - occupied_beat) <= epsilon for occupied_beat in occupied):
            return TailAvailability(
                False,
                f"eligible_tail_slot_occupied_at_{local_beat}",
                target_local_beat=target_local,
                checked_local_beats=tuple(checked),
            )

    return TailAvailability(True, "tail_space_available", target_local_beat=target_local, checked_local_beats=tuple(checked))
