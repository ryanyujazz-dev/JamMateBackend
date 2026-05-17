from __future__ import annotations

from dataclasses import dataclass

from .gesture import GestureKind, GestureRequest


@dataclass(frozen=True)
class FillGesture:
    """High-level fill/ornament request.

    This is still pitchless. Concrete target notes must be resolved later by
    harmony, voicing, and realization.
    """

    fill_type: str
    density: str = "light"

    def as_request(self) -> GestureRequest:
        return GestureRequest(
            kind=GestureKind.FILL,
            metadata={"fill_type": self.fill_type, "density": self.density},
        )
