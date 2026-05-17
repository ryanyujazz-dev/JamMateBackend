from __future__ import annotations

import base64

from jammate_agent.capabilities.accompaniment.models import AccompanimentAsset, AccompanimentRequest


class PlaceholderAccompanimentAdapter:
    """Fallback adapter for client/API integration before real engine wiring."""

    def generate(self, request: AccompanimentRequest) -> AccompanimentAsset:
        payload = {
            "placeholder": True,
            "style": request.config.style,
            "tempo": request.config.tempo,
            "loop_count": request.config.loop_count,
            "muted_roles": request.config.muted_roles,
            "leadsheet_title": (request.leadsheet or {}).get("title"),
        }
        midi_base64 = base64.b64encode(str(payload).encode("utf-8")).decode("ascii")
        return AccompanimentAsset(midi_base64=midi_base64, duration_seconds=0, debug_summary=payload)
