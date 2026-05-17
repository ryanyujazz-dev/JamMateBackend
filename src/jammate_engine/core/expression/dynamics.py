from __future__ import annotations


def clamp_velocity(value: int) -> int:
    return max(1, min(127, int(value)))
