from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from jammate_agent.capabilities.accompaniment.models import AccompanimentAsset, AccompanimentRequest
from jammate_engine.runtime.generate import generate_accompaniment


class JamMateEngineAccompanimentAdapter:
    """Adapter from JamMate Agent accompaniment requests to JamMate Engine runtime.

    This is the only layer in the agent package that imports `jammate_engine`.
    Agent/practice capabilities depend on the AccompanimentProvider contract, not
    on engine internals.
    """

    def __init__(self, output_dir: str | Path = "demos") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, request: AccompanimentRequest) -> AccompanimentAsset:
        if not request.leadsheet:
            raise ValueError("JamMateEngineAccompanimentAdapter requires a resolved leadsheet.")
        output_path = self.output_dir / self._build_output_filename(request)
        generation_request = self._to_generation_request(request, output_path)
        result = generate_accompaniment(generation_request)
        if not result.ok or not result.midi_path:
            raise RuntimeError(f"JamMateEngine generation failed: {result}")
        midi_path = Path(result.midi_path)
        midi_base64 = base64.b64encode(midi_path.read_bytes()).decode("ascii")
        return AccompanimentAsset(
            midi_base64=midi_base64,
            midi_path=str(midi_path),
            duration_seconds=self._estimate_duration_seconds(request),
            cache_key=self._cache_key(request),
            debug_summary={
                "provider": "jammate_engine",
                "version": result.version,
                "style": result.style,
                "tempo": result.tempo,
                "choruses": generation_request["choruses"],
                "engine_debug": result.debug,
            },
        )

    def _to_generation_request(self, request: AccompanimentRequest, output_path: Path) -> dict[str, Any]:
        config = request.config
        return {
            "leadsheet": request.leadsheet,
            "style": config.style,
            "tempo": int(config.tempo),
            "choruses": int(config.loop_count or 3),
            "seed": 42,
            "output_path": str(output_path),
            "ensemble": self._ensemble_from_muted_roles(config.muted_roles),
            "voicing_override": self._voicing_override(config),
        }

    def _ensemble_from_muted_roles(self, muted_roles: list[str]) -> dict[str, Any]:
        if not muted_roles:
            return {}
        return {
            "muted_roles": list(muted_roles),
            "piano_enabled": "piano" not in muted_roles,
            "bass_enabled": "bass" not in muted_roles,
            "drums_enabled": "drums" not in muted_roles,
            "melody_enabled": "melody" not in muted_roles,
        }

    def _voicing_override(self, config) -> dict[str, Any]:
        if not config.harmonic_expansion_enabled and not config.arrangement_intent:
            return {}
        color_mode = "style_safe_extensions"
        if config.arrangement_intent.get("altered_dominants_enabled") in {"high", "full"}:
            color_mode = "altered_dominant"
        return {
            "enabled": True,
            "harmonic_expansion_enabled": bool(config.harmonic_expansion_enabled),
            "color_policy_mode": color_mode,
            "metadata": {
                "practice_arrangement_intent": dict(config.arrangement_intent),
                "density": config.density,
                "practice_role": config.practice_role,
            },
        }

    def _build_output_filename(self, request: AccompanimentRequest) -> str:
        title = (request.leadsheet or {}).get("title", "practice_playback")
        safe_title = "".join(c.lower() if c.isalnum() else "_" for c in title).strip("_") or "practice_playback"
        return f"v2_3_15_agent_{safe_title}_{request.config.style}_{request.config.tempo}.mid"

    def _cache_key(self, request: AccompanimentRequest) -> str:
        title = (request.leadsheet or {}).get("title", "practice_playback")
        safe_title = "".join(c.lower() if c.isalnum() else "_" for c in title).strip("_") or "practice_playback"
        harmonic = "rich" if request.config.harmonic_expansion_enabled else "plain"
        muted = "+".join(sorted(request.config.muted_roles)) or "none"
        loop_count = request.config.loop_count or 3
        return f"accomp:{safe_title}:{request.config.style}:{request.config.tempo}:loops{loop_count}:{harmonic}:muted_{muted}"

    def _estimate_duration_seconds(self, request: AccompanimentRequest) -> int:
        bars = self._count_bars(request.leadsheet or {}) or 8
        beats = bars * 4 * int(request.config.loop_count or 1)
        return round(beats * 60 / max(int(request.config.tempo), 1))

    def _count_bars(self, leadsheet: dict) -> int:
        sections = leadsheet.get("sections", {})
        if isinstance(sections, dict):
            return sum(len(section.get("bars", [])) for section in sections.values() if isinstance(section, dict))
        if isinstance(sections, list):
            return sum(len(section.get("bars", [])) for section in sections if isinstance(section, dict))
        return 0
