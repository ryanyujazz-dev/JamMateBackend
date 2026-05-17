from __future__ import annotations

import json
import re
from pathlib import Path

from .models import ChartResolveRequest, ChartResolveResult, ChartStatus


class ChartResolver:
    """Chart capability for JamMate Agent.

    P0 searches the repository's examples/leadsheets first. It does not fetch
    copyrighted charts from the web. Future providers can add user libraries,
    uploaded charts, authorized sources, and practice progression generation.
    """

    def __init__(self, leadsheet_dirs: list[Path] | None = None) -> None:
        project_root = Path(__file__).resolve().parents[4]
        self.leadsheet_dirs = leadsheet_dirs or [project_root / "examples" / "leadsheets"]

    def resolve(self, request: ChartResolveRequest) -> ChartResolveResult:
        if request.user_provided_progression:
            return ChartResolveResult(
                chart_status=ChartStatus.RESOLVED,
                source="user_provided_progression",
                leadsheet=self._progression_to_leadsheet(request.user_provided_progression, request.key or "C"),
                confidence="medium",
                requires_user_confirmation=True,
            )

        tune = (request.tune or "").strip()
        if tune:
            found = self._find_local_leadsheet(tune)
            if found:
                return ChartResolveResult(
                    chart_status=ChartStatus.RESOLVED,
                    source=str(found),
                    leadsheet=json.loads(found.read_text(encoding="utf-8")),
                    confidence="high",
                    requires_user_confirmation=False,
                )

        return ChartResolveResult(
            chart_status=ChartStatus.NOT_FOUND,
            message=f"没有找到 {tune or '该曲目'} 的本地曲谱。",
            options=[
                {"type": "upload_chart", "label": "上传曲谱"},
                {"type": "type_chord_progression", "label": "手动输入和弦"},
                {"type": "generate_related_practice_progression", "label": "生成相关练习 progression"},
            ],
        )

    def _find_local_leadsheet(self, tune: str) -> Path | None:
        target = self._normalize(tune)
        for folder in self.leadsheet_dirs:
            if not folder.exists():
                continue
            for path in sorted(folder.glob("*.json")):
                if self._normalize(path.stem) == target:
                    return path
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if self._normalize(str(data.get("title", ""))) == target:
                    return path
        return None

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.strip().lower())

    def _progression_to_leadsheet(self, progression: str, key: str) -> dict:
        chords = [c.strip() for c in progression.replace("|", " ").split() if c.strip()]
        return {
            "schema_version": "jammate_leadsheet_v2",
            "title": f"Custom Progression in {key}",
            "key": key,
            "default_time_signature": {"numerator": 4, "denominator": 4},
            "metadata": {"source": "user_provided_progression", "melody_not_included": True},
            "sections": {
                "A": {
                    "label": "A",
                    "phrase": "A",
                    "role": "normal",
                    "bars": [{"chords": [{"beat": 1.0, "symbol": chord}]} for chord in chords],
                }
            },
            "written_form": ["A"],
        }
