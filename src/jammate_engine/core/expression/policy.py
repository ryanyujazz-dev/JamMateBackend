from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping, Any

from .dynamics import clamp_velocity


class ArticulationKind(str, Enum):
    SHORT = "short"
    SUSTAIN = "sustain"
    LEGATO = "legato"
    STACCATO = "staccato"
    ACCENT = "accent"


class PedalMode(str, Enum):
    NONE = "none"
    SUSTAIN = "sustain"
    LIGHT = "light"


class TouchKind(str, Enum):
    NEUTRAL = "neutral"
    LIGHT = "light"
    CLEAR = "clear"
    WARM = "warm"
    ACCENTED = "accented"


@dataclass(frozen=True)
class ExpressionProfile:
    """Reusable style-owned expression preset resolved by core.

    A profile is not a pattern. It contains performance behavior only:
    duration, velocity, articulation, touch, pedal, and release semantics.
    It must not contain chord tones, MIDI pitches, voicing notes, onsets, or
    rhythm pattern selection logic.
    """

    name: str
    duration_beats: float
    velocity: int
    articulation: ArticulationKind | str = ArticulationKind.SUSTAIN
    touch: TouchKind | str = TouchKind.NEUTRAL
    pedal: PedalMode | str = PedalMode.NONE
    release_beats: float = 0.0
    accent: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration_beats <= 0:
            raise ValueError("ExpressionProfile.duration_beats must be positive")
        object.__setattr__(self, "velocity", clamp_velocity(self.velocity))
        object.__setattr__(self, "articulation", self.articulation if isinstance(self.articulation, ArticulationKind) else ArticulationKind(str(self.articulation)))
        object.__setattr__(self, "touch", self.touch if isinstance(self.touch, TouchKind) else TouchKind(str(self.touch)))
        object.__setattr__(self, "pedal", self.pedal if isinstance(self.pedal, PedalMode) else PedalMode(str(self.pedal)))
        object.__setattr__(self, "release_beats", max(0.0, float(self.release_beats)))

    @classmethod
    def from_mapping(cls, name: str, data: Mapping[str, Any]) -> "ExpressionProfile":
        return cls(
            name=name,
            duration_beats=float(data.get("duration_beats", 1.0)),
            velocity=int(data.get("velocity", 60)),
            articulation=data.get("articulation", ArticulationKind.SUSTAIN.value),
            touch=data.get("touch", TouchKind.NEUTRAL.value),
            pedal=data.get("pedal", PedalMode.NONE.value),
            release_beats=float(data.get("release_beats", 0.0)),
            accent=float(data.get("accent", 0.0)),
            metadata=dict(data.get("metadata", {})),
        )

    def with_adjustments(self, *, velocity_delta: int = 0, duration_scale: float = 1.0) -> "ExpressionProfile":
        return replace(
            self,
            velocity=clamp_velocity(self.velocity + velocity_delta),
            duration_beats=max(0.05, self.duration_beats * duration_scale),
        )

    def to_legacy_dict(self) -> dict[str, Any]:
        """Temporary adapter for docs/debug compatibility."""
        return {
            "duration_beats": self.duration_beats,
            "velocity": self.velocity,
            "articulation": self.articulation.value,
            "touch": self.touch.value,
            "pedal": self.pedal.value,
            "release_beats": self.release_beats,
            "accent": self.accent,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ExpressionPolicyBundle:
    """Style-owned expression policy consumed by core ExpressionResolver."""

    profiles: dict[str, ExpressionProfile] = field(default_factory=dict)
    default_profile: str = "default"
    track_default_profiles: dict[str, str] = field(default_factory=dict)
    velocity_delta: int = 0
    duration_scale: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration_scale <= 0:
            raise ValueError("ExpressionPolicyBundle.duration_scale must be positive")
        profiles = dict(self.profiles)
        if "default" not in profiles:
            profiles["default"] = ExpressionProfile(
                name="default",
                duration_beats=0.75,
                velocity=60,
                articulation=ArticulationKind.SHORT,
                touch=TouchKind.NEUTRAL,
                pedal=PedalMode.NONE,
            )
        object.__setattr__(self, "profiles", profiles)

    @classmethod
    def from_legacy_dict(cls, data: Mapping[str, Any] | None) -> "ExpressionPolicyBundle":
        data = data or {}
        raw_profiles = data.get("profiles", {})
        profiles = {
            str(name): profile if isinstance(profile, ExpressionProfile) else ExpressionProfile.from_mapping(str(name), profile)
            for name, profile in dict(raw_profiles).items()
        }
        return cls(
            profiles=profiles,
            default_profile=str(data.get("default_profile", "default")),
            track_default_profiles=dict(data.get("track_default_profiles", {})),
            velocity_delta=int(data.get("velocity_delta", 0)),
            duration_scale=float(data.get("duration_scale", 1.0)),
            metadata=dict(data.get("metadata", {})),
        )

    def profile_for(self, hint: str | None, track: str | None = None) -> ExpressionProfile:
        preferred = hint or (self.track_default_profiles.get(track or "") if track else None) or self.default_profile
        profile = self.profiles.get(preferred) or self.profiles.get(self.default_profile) or self.profiles["default"]
        return profile.with_adjustments(velocity_delta=self.velocity_delta, duration_scale=self.duration_scale)

    def merge(self, overrides: Mapping[str, Any] | None = None) -> "ExpressionPolicyBundle":
        overrides = overrides or {}
        if isinstance(overrides, ExpressionPolicyBundle):
            return overrides
        profiles = dict(self.profiles)
        for name, raw in dict(overrides.get("profiles", {})).items():
            profiles[str(name)] = raw if isinstance(raw, ExpressionProfile) else ExpressionProfile.from_mapping(str(name), raw)
        return ExpressionPolicyBundle(
            profiles=profiles,
            default_profile=str(overrides.get("default_profile", self.default_profile)),
            track_default_profiles={**self.track_default_profiles, **dict(overrides.get("track_default_profiles", {}))},
            velocity_delta=int(overrides.get("velocity_delta", self.velocity_delta)),
            duration_scale=float(overrides.get("duration_scale", self.duration_scale)),
            metadata={**self.metadata, **dict(overrides.get("metadata", {}))},
        )

    def to_legacy_dict(self) -> dict[str, Any]:
        return {
            "profiles": {name: profile.to_legacy_dict() for name, profile in self.profiles.items()},
            "default_profile": self.default_profile,
            "track_default_profiles": dict(self.track_default_profiles),
            "velocity_delta": self.velocity_delta,
            "duration_scale": self.duration_scale,
            "metadata": dict(self.metadata),
        }
