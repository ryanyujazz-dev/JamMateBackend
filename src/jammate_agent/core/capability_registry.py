from __future__ import annotations

from dataclasses import dataclass

from jammate_agent.capabilities.accompaniment.provider import AccompanimentProvider
from jammate_agent.capabilities.charts.chart_resolver import ChartResolver
from jammate_agent.capabilities.practice.planner import PracticePlanner
from jammate_agent.capabilities.practice.review_engine import ReviewEngine


@dataclass
class CapabilityRegistry:
    practice_planner: PracticePlanner
    chart_resolver: ChartResolver
    accompaniment_provider: AccompanimentProvider
    review_engine: ReviewEngine
