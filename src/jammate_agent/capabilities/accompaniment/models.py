from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_agent.capabilities.practice.models import AccompanimentPracticeConfig, PracticeMaterial, new_id


@dataclass
class AccompanimentRequest:
    config: AccompanimentPracticeConfig
    material: PracticeMaterial | None = None
    leadsheet: dict[str, Any] | None = None
    block_id: str | None = None
    output_dir: str = "demos"


@dataclass
class AccompanimentAsset:
    midi_base64: str
    asset_id: str = field(default_factory=lambda: new_id("asset"))
    format: str = "midi_base64"
    midi_path: str | None = None
    duration_seconds: int | None = None
    cache_key: str | None = None
    debug_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "format": self.format,
            "midi_base64": self.midi_base64,
            "midi_path": self.midi_path,
            "duration_seconds": self.duration_seconds,
            "cache_key": self.cache_key,
            "debug_summary": self.debug_summary,
        }
