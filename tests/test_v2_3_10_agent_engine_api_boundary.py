from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from jammate_agent.adapters.jammate_engine_accompaniment_adapter import JamMateEngineAccompanimentAdapter
from jammate_agent.capabilities.accompaniment.models import AccompanimentRequest
from jammate_agent.capabilities.charts.chart_resolver import ChartResolver
from jammate_agent.capabilities.charts.models import ChartResolveRequest, ChartStatus
from jammate_agent.capabilities.practice.models import AccompanimentPracticeConfig, PracticeMaterial
from jammate_agent.capabilities.practice.planner import PracticePlanner
from jammate_api.app import app


def test_agent_and_engine_are_sibling_packages_importable() -> None:
    import jammate_agent
    import jammate_engine
    import jammate_api

    assert jammate_agent is not None
    assert jammate_engine is not None
    assert jammate_api is not None


def test_practice_planner_generates_duration_consistent_plan() -> None:
    plan = PracticePlanner().build_plan("我今天有45分钟，想练Misty的ballad comping", available_minutes=45)
    assert plan.duration_minutes == 45
    assert sum(block.duration_minutes for block in plan.blocks) == 45
    assert plan.blocks


def test_chart_resolver_finds_existing_autumn_leaves_fixture() -> None:
    result = ChartResolver().resolve(ChartResolveRequest(tune="Autumn Leaves"))
    assert result.chart_status == ChartStatus.RESOLVED
    assert result.leadsheet is not None
    assert result.leadsheet["title"] == "Autumn Leaves"


def test_agent_playback_prepare_returns_real_midi_base64() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/playback/prepare",
        json={"user_input": "我想练 Autumn Leaves 30分钟，钢琴和声色彩丰富一点", "duration_minutes": 30},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["asset"]["format"] == "midi_base64"
    assert len(base64.b64decode(data["asset"]["midi_base64"])) > 8
    assert data["asset"]["midi_path"].endswith(".mid")


def test_direct_accompaniment_route_does_not_require_agent() -> None:
    client = TestClient(app)
    response = client.post(
        "/accompaniment/generate",
        json={"tune": "Blue Bossa", "style": "bossa_nova", "tempo": 120, "choruses": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["asset"]["debug_summary"]["path"] == "direct_accompaniment_api"
    assert data["debug_summary"]["path"] == "direct_accompaniment_api"
    assert len(base64.b64decode(data["asset"]["midi_base64"])) > 8


def test_jammate_engine_adapter_is_only_required_engine_bridge() -> None:
    chart = ChartResolver().resolve(ChartResolveRequest(tune="Blue Bossa"))
    provider = JamMateEngineAccompanimentAdapter()
    asset = provider.generate(
        AccompanimentRequest(
            material=PracticeMaterial(type="tune", tune="Blue Bossa"),
            leadsheet=chart.leadsheet,
            config=AccompanimentPracticeConfig(style="bossa_nova", tempo=120, loop_count=1),
        )
    )
    assert asset.midi_path and asset.midi_path.endswith(".mid")
    assert len(base64.b64decode(asset.midi_base64)) > 8
