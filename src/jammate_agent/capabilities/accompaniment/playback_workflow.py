from __future__ import annotations

import re
from dataclasses import dataclass

from jammate_agent.capabilities.charts.chart_resolver import ChartResolver
from jammate_agent.capabilities.charts.models import ChartResolveRequest, ChartStatus
from jammate_agent.capabilities.practice.models import AccompanimentPracticeConfig, PracticeMaterial

from .models import AccompanimentRequest
from .provider import AccompanimentProvider


@dataclass
class PlaybackPrepareResult:
    ok: bool
    intent_type: str
    practice_session: dict | None = None
    asset: dict | None = None
    playback_instruction: dict | None = None
    explanation: str | None = None
    error_code: str | None = None
    message: str | None = None
    options: list[dict] | None = None


class ImmediatePlaybackWorkflow:
    def __init__(self, chart_resolver: ChartResolver, accompaniment_provider: AccompanimentProvider) -> None:
        self.chart_resolver = chart_resolver
        self.accompaniment_provider = accompaniment_provider

    def prepare(self, user_input: str, duration_minutes: int = 30) -> PlaybackPrepareResult:
        tune = self._extract_tune(user_input)
        style = self._infer_style(user_input)
        tempo = self._infer_tempo(user_input, style)
        richer = self._wants_richer_harmony(user_input)
        chart = self.chart_resolver.resolve(ChartResolveRequest(tune=tune))
        if chart.chart_status != ChartStatus.RESOLVED:
            return PlaybackPrepareResult(
                ok=False,
                intent_type="immediate_practice_playback",
                error_code="CHART_NOT_FOUND",
                message=chart.message,
                options=chart.options,
            )

        config = AccompanimentPracticeConfig(
            style=style,
            tempo=tempo,
            duration_minutes=duration_minutes,
            loop_count=self._asset_loop_count(chart.leadsheet or {}, tempo, duration_minutes),
            muted_roles=[],
            harmonic_expansion_enabled=richer,
            density="medium_rich" if richer else "normal",
            practice_role="general_practice",
            arrangement_intent=self._arrangement_intent(richer),
        )
        material = PracticeMaterial(type="tune", tune=tune, key=(chart.leadsheet or {}).get("key"))
        asset = self.accompaniment_provider.generate(AccompanimentRequest(config=config, material=material, leadsheet=chart.leadsheet))
        return PlaybackPrepareResult(
            ok=True,
            intent_type="immediate_practice_playback",
            practice_session={
                "status": "active",
                "total_planned_minutes": duration_minutes,
                "material": material.to_dict(),
                "accompaniment_config": config.to_dict(),
            },
            asset=asset.to_dict(),
            playback_instruction={
                "auto_start": True,
                "target_duration_minutes": duration_minutes,
                "client_loop_until_target_duration": True,
                "asset_loop_mode": "loop_until_target_duration",
                "stop_condition": "practice_timer_reaches_target_duration_or_user_stops",
                "requires_local_timer": True,
                "cache_policy": {
                    "cache_key": asset.to_dict().get("cache_key"),
                    "scope": "recent_practice_asset",
                    "reuse_when_request_signature_matches": True,
                },
            },
            explanation=f"已准备 {tune or '所选材料'} 的 {style} 练习伴奏。",
        )

    def _extract_tune(self, text: str) -> str | None:
        known = ["All The Things You Are", "Autumn Leaves", "Blue Bossa", "Misty", "Minimal Ii V I"]
        lower = text.lower()
        for tune in known:
            if tune.lower() in lower:
                return tune
        match = re.search(r"练\s*([A-Za-z][A-Za-z\s]+?)(?:\d+|，|,|。|$)", text)
        return match.group(1).strip() if match else None

    def _infer_style(self, text: str) -> str:
        lower = text.lower()
        if "bossa" in lower or "波萨" in text:
            return "bossa_nova"
        if "ballad" in lower or "misty" in lower or "抒情" in text:
            return "jazz_ballad"
        return "medium_swing"

    def _infer_tempo(self, text: str, style: str) -> int:
        match = re.search(r"(?:bpm|tempo|速度)\s*[:=]?\s*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        if style == "jazz_ballad":
            return 76
        if style == "bossa_nova":
            return 120
        return 132

    def _wants_richer_harmony(self, text: str) -> bool:
        return any(k in text for k in ["色彩丰富", "和声色彩", "丰富一点", "richer", "altered", "张力"])

    def _arrangement_intent(self, richer: bool) -> dict:
        if not richer:
            return {}
        return {
            "harmonic_color": "richer_jazz_color",
            "voicing_density": "medium_rich",
            "altered_dominants_enabled": "moderate",
            "source": "jammate_agent_p0_keyword_inference",
        }

    def _asset_loop_count(self, leadsheet: dict, tempo: int, duration_minutes: int) -> int:
        """Return a bounded MIDI asset loop count.

        Practice duration is a playback/session target, not a requirement to
        render a single huge MIDI file. HarmonyOS should loop the returned asset
        until `target_duration_minutes` is reached. This keeps API latency low.
        """
        bars = self._count_bars(leadsheet) or 8
        one_chorus_seconds = bars * 4 * 60 / max(tempo, 1)
        requested_choruses = max(1, round((duration_minutes * 60) / one_chorus_seconds))
        return min(requested_choruses, 3)

    def _count_bars(self, leadsheet: dict) -> int:
        sections = leadsheet.get("sections", {})
        if isinstance(sections, dict):
            return sum(len(section.get("bars", [])) for section in sections.values() if isinstance(section, dict))
        if isinstance(sections, list):
            return sum(len(section.get("bars", [])) for section in sections if isinstance(section, dict))
        return 0
