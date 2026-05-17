from __future__ import annotations

from pathlib import Path

from jammate_agent.capabilities.charts.chart_resolver import ChartResolver


def build_default_chart_resolver() -> ChartResolver:
    project_root = Path(__file__).resolve().parents[3]
    return ChartResolver(leadsheet_dirs=[project_root / "examples" / "leadsheets"])
