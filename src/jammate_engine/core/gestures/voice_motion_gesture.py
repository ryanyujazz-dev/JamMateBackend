from __future__ import annotations

from dataclasses import dataclass

from .gesture import GestureKind, GestureRequest


@dataclass(frozen=True)
class VoiceMotionGesture:
    """Pitchless voice-motion request such as an inner answer or top response."""

    motion_shape: str
    target_voice_class: str = "inner"

    def as_request(self) -> GestureRequest:
        return GestureRequest(
            kind=GestureKind.INNER_MOVEMENT,
            voice_order=(self.target_voice_class,),
            metadata={"motion_shape": self.motion_shape},
        )
