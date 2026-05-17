from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from jammate_engine.core.roles import EnsembleContext
from jammate_engine.core.gestures.gesture import GestureRequest

from ..policy import VoicingPolicy


@dataclass(frozen=True)
class VoicingRequest:
    """Public request boundary for core/voicing.

    The request may carry expression articulation and a pitchless gesture so
    voicing can understand context, but it must not contain final durations,
    velocities, pedal decisions, or already-realized MIDI note choices.
    """

    event_id: str
    chord_symbol: str
    track: str
    gesture_type: str
    gesture: GestureRequest
    expression_articulation: str
    ensemble_context: EnsembleContext | dict
    policy: VoicingPolicy
    onset_beat: float | None = None
    rng: random.Random | None = None

    def to_debug_dict(self) -> dict[str, Any]:
        ensemble = EnsembleContext.from_dict(self.ensemble_context)
        return {
            "event_id": self.event_id,
            "chord_symbol": self.chord_symbol,
            "track": self.track,
            "gesture_type": self.gesture_type,
            "gesture": {
                "kind": self.gesture.kind.value,
                "voice_order": list(self.gesture.voice_order),
                "onset_offsets_beats": list(self.gesture.onset_offsets_beats),
                "metadata": dict(self.gesture.metadata),
            },
            "expression_articulation": self.expression_articulation,
            "ensemble_context": ensemble.to_dict(),
            "policy": self.policy.to_debug_dict(),
            "onset_beat": self.onset_beat,
            "has_rng": self.rng is not None,
        }
