from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_api.app import app


def test_arkts_contract_files_endpoint_returns_split_copyable_files() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/arkts/files")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "v2_4_7"
    files = {item["filename"]: item for item in payload["files"]}
    assert {"AgentTypes.ets", "PracticeTypes.ets", "PlaybackTypes.ets", "JamMateApiClient.ets"}.issubset(files)
    assert "export interface AgentResponse" in files["AgentTypes.ets"]["source"]
    assert "export interface PracticePlan" in files["PracticeTypes.ets"]["source"]
    assert "export interface PlaybackInstruction" in files["PlaybackTypes.ets"]["source"]
    assert "generateDirectAccompaniment" in files["JamMateApiClient.ets"]["source"]


def test_frontend_fixture_pack_endpoint_contains_plan_playback_and_direct_fixtures() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/fixtures")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "v2_4_7"
    fixtures = payload["fixtures"]
    assert fixtures["agentPracticePlanResponse"]["plan"]["blocks"]
    assert fixtures["agentPlaybackPrepareResponse"]["playbackInstruction"]["clientLoopUntilTargetDuration"] is True
    assert fixtures["agentPlaybackPrepareResponse"]["asset"]["cacheKey"]
    assert fixtures["directAccompanimentGenerateResponse"]["asset"]["debugSummary"]["path"] == "direct_accompaniment_api"
    assert fixtures["sessionReviewRequest"]["difficulty"] == "good_challenge"


def test_frontend_pack_endpoint_returns_filesystem_style_pack() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/frontend-pack")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    rels = {item["relative_path"] for item in payload["files"]}
    assert "types/AgentTypes.ets" in rels
    assert "types/PracticeTypes.ets" in rels
    assert "types/PlaybackTypes.ets" in rels
    assert "api/CaseAdapter.ets" in rels
    assert "api/JamMateApiClient.ets" in rels
    assert "fixtures/PracticeFixtures.json" in rels
    assert "README.md" in rels


def test_repository_frontend_fixture_files_are_present_and_aligned() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_root = root / "frontend_fixtures" / "harmonyos"
    assert (fixture_root / "types" / "AgentTypes.ets").exists()
    assert (fixture_root / "types" / "PracticeTypes.ets").exists()
    assert (fixture_root / "types" / "PlaybackTypes.ets").exists()
    assert (fixture_root / "api" / "JamMateApiClient.ets").exists()
    assert (fixture_root / "fixtures" / "PracticeFixtures.json").exists()
    assert "v2_4_7" in (fixture_root / "README.md").read_text(encoding="utf-8")
