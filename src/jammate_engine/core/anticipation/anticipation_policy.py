from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AnticipationPolicy:
    """Style-configurable policy for pitchless anticipation rewrites.

    The resolver owns the actual timeline mutation. Styles may only tune whether
    anticipation is enabled, how often it may happen, and which pitchless event
    categories are eligible. Concrete pitches, durations, velocities and voiced
    notes are intentionally outside this contract.
    """

    enabled: bool = False
    probability: float = 0.0
    # Logical musical target offset.  -0.5 means “move beat 1 to the previous
    # written upbeat” on the pitchless timeline.  Style timing policy later
    # performs that written upbeat as straight 1/2 or swing 2/3.
    target_offset_beats: float = -0.5
    # Timing-grid contract for realized anticipation.  Straight/Bossa keeps
    # the written upbeat at .5; Swing keeps the logical .5 grid but must render
    # it through timing_intent=swing_upbeat so it performs at 2/3.
    timing_grid: str = "straight_upbeat"
    target_timing_intent: str = "auto"
    performed_lead_in_beats: float | None = None
    expected_upbeat_fraction: float | None = None
    eligible_tracks: tuple[str, ...] = ("piano",)
    eligible_roles: tuple[str, ...] = ("harmonic",)
    require_previous_tail_space: bool = True
    require_previous_last_beat_empty: bool = True
    require_previous_last_upbeat_empty: bool = True
    min_previous_region_duration_beats: float | None = None
    suppress_original: bool = True
    tie_from_previous: bool = True
    debug_name: str = "default_anticipation_policy"
    metadata: dict = field(default_factory=dict)

    def normalized_probability(self) -> float:
        return min(1.0, max(0.0, float(self.probability)))
