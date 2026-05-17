from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenerationResult:
    ok: bool
    midi_path: str | None
    version: str
    style: str
    tempo: int
    debug: dict[str, Any] = field(default_factory=dict)
