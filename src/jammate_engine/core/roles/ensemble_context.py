from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EnsembleContext:
    """Runtime ensemble role context.

    This object is the formal V2 boundary for questions such as:
    - Is there a real bass player / bass track?
    - Should piano supply a left-hand bass foundation?
    - May piano remain rootless even when no bass is present?

    It deliberately does not contain style patterns, concrete voicings, or MIDI
    notes. It only tells core stages which ensemble roles are active.
    """

    bass_present: bool = True
    piano_present: bool = True
    drums_present: bool = True
    piano_split_role_enabled: bool = True
    allow_rootless_without_bass: bool = False
    piano_lh_bass_foundation_enabled: bool = True
    piano_channel: int = 0
    bass_channel: int = 1
    drum_channel: int = 9
    piano_lh_low: int = 36
    piano_lh_high: int = 54
    piano_rh_low: int = 55
    piano_rh_high: int = 79
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, value: "EnsembleContext | dict[str, Any] | None") -> "EnsembleContext":
        if isinstance(value, EnsembleContext):
            return value
        value = dict(value or {})
        return cls(
            bass_present=bool(value.get("bass_present", True)),
            piano_present=bool(value.get("piano_present", True)),
            drums_present=bool(value.get("drums_present", True)),
            piano_split_role_enabled=bool(value.get("piano_split_role_enabled", True)),
            allow_rootless_without_bass=bool(value.get("allow_rootless_without_bass", False)),
            piano_lh_bass_foundation_enabled=bool(value.get("piano_lh_bass_foundation_enabled", True)),
            piano_channel=int(value.get("piano_channel", 0)),
            bass_channel=int(value.get("bass_channel", 1)),
            drum_channel=int(value.get("drum_channel", 9)),
            piano_lh_low=int(value.get("piano_lh_low", 36)),
            piano_lh_high=int(value.get("piano_lh_high", 54)),
            piano_rh_low=int(value.get("piano_rh_low", 55)),
            piano_rh_high=int(value.get("piano_rh_high", 79)),
            metadata=dict(value.get("metadata", {})),
        )

    @property
    def needs_piano_lh_bass_foundation(self) -> bool:
        return (
            self.piano_present
            and not self.bass_present
            and self.piano_split_role_enabled
            and self.piano_lh_bass_foundation_enabled
        )

    @property
    def should_force_root_in_harmonic_voicing(self) -> bool:
        """Fallback only; split-role is preferred over root-stuffing chords."""

        return (
            self.piano_present
            and not self.bass_present
            and not self.allow_rootless_without_bass
            and not self.needs_piano_lh_bass_foundation
        )

    @property
    def harmonic_comping_role(self) -> str:
        if self.needs_piano_lh_bass_foundation:
            return "piano_rh_harmonic_comping"
        return "harmonic_comping"

    @property
    def bass_foundation_provider(self) -> str:
        """Return the ensemble role currently responsible for root foundation."""

        if self.bass_present:
            return "bass_track"
        if self.needs_piano_lh_bass_foundation:
            return "piano_lh_bass_foundation"
        if self.should_force_root_in_harmonic_voicing:
            return "harmonic_voicing"
        if self.allow_rootless_without_bass:
            return "intentional_rootless_texture"
        return "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "bass_present": self.bass_present,
            "piano_present": self.piano_present,
            "drums_present": self.drums_present,
            "piano_split_role_enabled": self.piano_split_role_enabled,
            "allow_rootless_without_bass": self.allow_rootless_without_bass,
            "piano_lh_bass_foundation_enabled": self.piano_lh_bass_foundation_enabled,
            "piano_channel": self.piano_channel,
            "bass_channel": self.bass_channel,
            "drum_channel": self.drum_channel,
            "piano_lh_low": self.piano_lh_low,
            "piano_lh_high": self.piano_lh_high,
            "piano_rh_low": self.piano_rh_low,
            "piano_rh_high": self.piano_rh_high,
            "needs_piano_lh_bass_foundation": self.needs_piano_lh_bass_foundation,
            "should_force_root_in_harmonic_voicing": self.should_force_root_in_harmonic_voicing,
            "harmonic_comping_role": self.harmonic_comping_role,
            "bass_foundation_provider": self.bass_foundation_provider,
            "metadata": dict(self.metadata or {}),
        }
