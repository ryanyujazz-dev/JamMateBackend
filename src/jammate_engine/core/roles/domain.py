from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GenerationDomain(str, Enum):
    """Music-function domain, independent of a concrete instrument."""

    COMPING = "comping"
    BASS_FOUNDATION = "bass_foundation"
    PERCUSSION = "percussion"
    MELODIC_FOREGROUND = "melodic_foreground"
    FILL = "fill"


class MusicalRole(str, Enum):
    """Runtime role assigned to one instrument or instrument sub-role."""

    HARMONIC_COMPING = "harmonic_comping"
    PIANO_RH_HARMONIC_COMPING = "piano_rh_harmonic_comping"
    BASS_FOUNDATION = "bass_foundation"
    PIANO_LH_BASS_FOUNDATION = "piano_lh_bass_foundation"
    PERCUSSION_GROOVE = "percussion_groove"
    MELODIC_FOREGROUND = "melodic_foreground"


@dataclass(frozen=True)
class TrackRolePlan:
    """Small active contract for mapping tracks to generation domains.

    It is intentionally kept in one file for now. If role assignment becomes
    complex, it may split into role_assignment.py / track_plan.py later.
    """

    track: str
    instrument: str
    domain: GenerationDomain
    role: MusicalRole
    channel: int
