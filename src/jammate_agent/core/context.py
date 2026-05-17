from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityManifest:
    available_styles: list[str] = field(default_factory=lambda: ["medium_swing", "bossa_nova", "jazz_ballad"])
    available_practice_modes: list[str] = field(default_factory=lambda: ["general_practice", "piano_comping", "solo_improvisation", "time_feel", "repertoire"])
    can_mute_roles: list[str] = field(default_factory=lambda: ["piano", "bass", "drums", "melody"])
    supports_loop_count: bool = True
    supports_harmonic_expansion: bool = True


@dataclass
class ContextPacket:
    task_type: str
    user_request: dict[str, Any]
    user_profile: dict[str, Any] = field(default_factory=dict)
    learner_context: dict[str, Any] = field(default_factory=dict)
    active_context: dict[str, Any] = field(default_factory=dict)
    material_context: dict[str, Any] = field(default_factory=dict)
    capabilities: CapabilityManifest = field(default_factory=CapabilityManifest)
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "user_request": self.user_request,
            "user_profile": self.user_profile,
            "learner_context": self.learner_context,
            "active_context": self.active_context,
            "material_context": self.material_context,
            "capabilities": self.capabilities.__dict__,
            "constraints": self.constraints,
        }


class ContextBuilder:
    def build(self, task_type: str, user_input: str, **kwargs: Any) -> ContextPacket:
        return ContextPacket(
            task_type=task_type,
            user_request={"text": user_input, **kwargs},
            user_profile={"instrument": kwargs.get("instrument", "piano"), "level": "unknown"},
            learner_context={"recent_focus": [], "recent_weak_points": [], "note": "P0 placeholder; replace with LearnerModel summary."},
            constraints={"available_minutes": kwargs.get("available_minutes") or kwargs.get("duration_minutes")},
        )
