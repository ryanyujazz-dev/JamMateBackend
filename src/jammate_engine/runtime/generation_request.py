from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenerationRequest:
    """Top-level generation request for V2 runtime."""

    leadsheet: dict[str, Any]
    style: str = "medium_swing"
    tempo: int = 120
    choruses: int = 3
    seed: int = 42
    output_path: str | None = None
    ensemble: dict[str, Any] = field(default_factory=dict)
    voicing_override: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "GenerationRequest":
        return GenerationRequest(
            leadsheet=data.get("leadsheet", {}),
            style=data.get("style", "medium_swing"),
            tempo=int(data.get("tempo", 120)),
            choruses=int(data.get("choruses", 3)),
            seed=int(data.get("seed", 42)),
            output_path=data.get("output_path"),
            ensemble=dict(data.get("ensemble", {})),
            voicing_override=dict(data.get("voicing_override", data.get("voicing_tuning", {})) or {}),
        )
