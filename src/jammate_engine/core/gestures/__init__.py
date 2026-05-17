from __future__ import annotations

from .fill_gesture import FillGesture
from .gesture import (
    Gesture,
    GestureKind,
    GestureRequest,
    OnsetMode,
    ProjectionRefPrefix,
    arpeggiated_onset,
    gesture_request,
    rolled_onset,
    simultaneous_onset,
)
from .gesture_timeline import GestureTimeline
from .voice_motion_gesture import VoiceMotionGesture

GESTURE_PROJECTION_CONTRACT_VERSION = "v2_0_40"
GESTURE_PROJECTION_KEYS = (
    "all_voices",
    "lowest",
    "inner",
    "inner_*",
    "top",
    "support_group",
    "foundation_group",
    "projection_group",
    "color_group",
    "motion_group",
    "anchor_group",
    "extension_group",
)

__all__ = [
    "FillGesture",
    "Gesture",
    "GESTURE_PROJECTION_CONTRACT_VERSION",
    "GESTURE_PROJECTION_KEYS",
    "GestureKind",
    "GestureRequest",
    "GestureTimeline",
    "OnsetMode",
    "ProjectionRefPrefix",
    "VoiceMotionGesture",
    "arpeggiated_onset",
    "gesture_request",
    "rolled_onset",
    "simultaneous_onset",
]
