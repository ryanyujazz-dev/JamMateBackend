from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_LANE_WEIGHTS_BY_ZONE = {
    "very_low": {"upper": 100.0, "lower": 0.0, "mixed": 0.0},
    "low": {"upper": 82.0, "lower": 13.0, "mixed": 5.0},
    "middle": {"upper": 47.0, "lower": 47.0, "mixed": 6.0},
    "high": {"upper": 13.0, "lower": 82.0, "mixed": 5.0},
    "very_high": {"upper": 0.0, "lower": 100.0, "mixed": 0.0},
}

DEFAULT_DEGREE_LANE_MULTIPLIERS = {
    "Second": {"upper": 3.00, "lower": 0.20, "mixed": 0.35},
    "Third": {"upper": 3.00, "lower": 0.20, "mixed": 0.35},
    "Fourth": {"upper": 2.40, "lower": 0.30, "mixed": 0.40},
    "Fifth": {"upper": 1.00, "lower": 1.00, "mixed": 0.55},
    "Sixth": {"upper": 0.20, "lower": 3.00, "mixed": 0.35},
    "Seventh": {"upper": 0.15, "lower": 3.50, "mixed": 0.35},
}

DEFAULT_CONNECTOR_FAMILY_WEIGHTS = {
    "scale_near_nextR": 40.0,
    "approach_nextR": 40.0,
    "dominant_connection": 10.0,
}


@dataclass(frozen=True)
class BassFoundationPolicy:
    """Runtime policy for role-level BassFoundation generation.

    Style owns vocabulary and preference numbers. Core owns target-to-target
    planning, octave choice, register-zone lane selection, connector selection,
    guardrails, and debug trace emission.
    """

    enabled: bool = False
    register_low: int = 26
    register_high: int = 48
    register_center: int = 37
    max_body_span: int = 12
    max_region_span: int = 12
    max_segment_span: int = 16
    max_preferred_leap: int = 7
    same_note_penalty: float = 30.0
    repeated_root_fifth_penalty: float = 8.0
    direction_bias_weight: float = 2.0
    lane_weights_by_zone: dict[str, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_LANE_WEIGHTS_BY_ZONE))
    degree_lane_multipliers: dict[str, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_DEGREE_LANE_MULTIPLIERS))
    connector_family_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_CONNECTOR_FAMILY_WEIGHTS))
    same_beat3_beat4_weight_multiplier: float = 0.15
    # v2_0_22 preserves the previous project's lane-instance behavior: after
    # the zone/lane weighted choice, pick one eligible instance randomly from
    # that lane. This keeps the old Medium Swing three-beat pattern feel instead
    # of replacing it with a new smoothness scorer.
    lane_instance_selection: str = "legacy_random"
    target_continuity_enabled: bool = True
    root_echo_enabled: bool = False
    root_echo_probability: float = 0.0
    root_echo_compact_probability_multiplier: float = 0.5
    root_echo_rr_start_3and_probability: float = 0.0
    root_echo_allowed_upbeats: tuple[float, ...] = (0.5, 2.5)
    root_echo_max_per_region: int = 1
    classic_fill_enabled: bool = False
    classic_fill_two_bar_tonic_probability: float = 0.0
    classic_fill_max_start_note: int = 43
    classic_fill_min_gap_regions: int = 8
    debug_name: str = "default_bass_foundation"

    @classmethod
    def from_dict(cls, data: dict | None) -> "BassFoundationPolicy":
        data = dict(data or {})
        return cls(
            enabled=bool(data.get("enabled", False)),
            register_low=int(data.get("register_low", cls.register_low)),
            register_high=int(data.get("register_high", cls.register_high)),
            register_center=int(data.get("register_center", cls.register_center)),
            max_body_span=int(data.get("max_body_span", cls.max_body_span)),
            max_region_span=int(data.get("max_region_span", data.get("max_body_span", cls.max_region_span))),
            max_segment_span=int(data.get("max_segment_span", cls.max_segment_span)),
            max_preferred_leap=int(data.get("max_preferred_leap", cls.max_preferred_leap)),
            same_note_penalty=float(data.get("same_note_penalty", cls.same_note_penalty)),
            repeated_root_fifth_penalty=float(data.get("repeated_root_fifth_penalty", cls.repeated_root_fifth_penalty)),
            direction_bias_weight=float(data.get("direction_bias_weight", cls.direction_bias_weight)),
            lane_weights_by_zone=_nested_float_dict(data.get("lane_weights_by_zone"), DEFAULT_LANE_WEIGHTS_BY_ZONE),
            degree_lane_multipliers=_nested_float_dict(data.get("degree_lane_multipliers"), DEFAULT_DEGREE_LANE_MULTIPLIERS),
            connector_family_weights={**DEFAULT_CONNECTOR_FAMILY_WEIGHTS, **{k: float(v) for k, v in dict(data.get("connector_family_weights", {})).items()}},
            same_beat3_beat4_weight_multiplier=float(data.get("same_beat3_beat4_weight_multiplier", cls.same_beat3_beat4_weight_multiplier)),
            lane_instance_selection=str(data.get("lane_instance_selection", cls.lane_instance_selection)),
            target_continuity_enabled=bool(data.get("target_continuity_enabled", cls.target_continuity_enabled)),
            root_echo_enabled=bool(data.get("root_echo_enabled", cls.root_echo_enabled)),
            root_echo_probability=float(data.get("root_echo_probability", cls.root_echo_probability)),
            root_echo_compact_probability_multiplier=float(data.get("root_echo_compact_probability_multiplier", cls.root_echo_compact_probability_multiplier)),
            root_echo_rr_start_3and_probability=float(data.get("root_echo_rr_start_3and_probability", cls.root_echo_rr_start_3and_probability)),
            root_echo_allowed_upbeats=tuple(float(beat) for beat in data.get("root_echo_allowed_upbeats", cls.root_echo_allowed_upbeats)),
            root_echo_max_per_region=int(data.get("root_echo_max_per_region", cls.root_echo_max_per_region)),
            classic_fill_enabled=bool(data.get("classic_fill_enabled", cls.classic_fill_enabled)),
            classic_fill_two_bar_tonic_probability=float(data.get("classic_fill_two_bar_tonic_probability", cls.classic_fill_two_bar_tonic_probability)),
            classic_fill_max_start_note=int(data.get("classic_fill_max_start_note", cls.classic_fill_max_start_note)),
            classic_fill_min_gap_regions=int(data.get("classic_fill_min_gap_regions", cls.classic_fill_min_gap_regions)),
            debug_name=str(data.get("debug_name", cls.debug_name)),
        )

    def to_debug_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "register_low": self.register_low,
            "register_high": self.register_high,
            "register_center": self.register_center,
            "max_body_span": self.max_body_span,
            "max_region_span": self.max_region_span,
            "max_segment_span": self.max_segment_span,
            "max_preferred_leap": self.max_preferred_leap,
            "same_note_penalty": self.same_note_penalty,
            "repeated_root_fifth_penalty": self.repeated_root_fifth_penalty,
            "direction_bias_weight": self.direction_bias_weight,
            "lane_weights_by_zone": self.lane_weights_by_zone,
            "degree_lane_multipliers": self.degree_lane_multipliers,
            "connector_family_weights": self.connector_family_weights,
            "same_beat3_beat4_weight_multiplier": self.same_beat3_beat4_weight_multiplier,
            "lane_instance_selection": self.lane_instance_selection,
            "target_continuity_enabled": self.target_continuity_enabled,
            "root_echo_enabled": self.root_echo_enabled,
            "root_echo_probability": self.root_echo_probability,
            "root_echo_compact_probability_multiplier": self.root_echo_compact_probability_multiplier,
            "root_echo_rr_start_3and_probability": self.root_echo_rr_start_3and_probability,
            "root_echo_allowed_upbeats": list(self.root_echo_allowed_upbeats),
            "root_echo_max_per_region": self.root_echo_max_per_region,
            "classic_fill_enabled": self.classic_fill_enabled,
            "classic_fill_two_bar_tonic_probability": self.classic_fill_two_bar_tonic_probability,
            "classic_fill_max_start_note": self.classic_fill_max_start_note,
            "classic_fill_min_gap_regions": self.classic_fill_min_gap_regions,
            "debug_name": self.debug_name,
        }




def _nested_float_dict(raw, default: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    merged = {key: dict(value) for key, value in default.items()}
    for key, value in dict(raw or {}).items():
        merged[str(key)] = {k: float(v) for k, v in dict(value).items()}
    return merged
