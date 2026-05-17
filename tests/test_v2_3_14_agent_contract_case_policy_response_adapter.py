from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.core.contract_codegen import frontend_fixture_pack
from jammate_api.app import app


def test_case_policy_endpoint_declares_snake_backend_and_camel_client_domain() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/case-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    policy = payload["policy"]
    assert policy["version"] == "v2_3_17"
    assert policy["canonical_backend_response_case"] == "snake_case"
    assert policy["harmonyos_client_domain_case"] == "camelCase"
    assert "CaseAdapter.ets" == policy["adapter_file"]
    assert policy["examples"]["backend_raw"]["trace_id"] == "trace_001"
    assert policy["examples"]["harmonyos_domain"]["traceId"] == "trace_001"


def test_backend_response_remains_snake_case_for_canonical_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/playback/prepare",
        json={"userInput": "我想练 Blue Bossa 20分钟", "durationMinutes": 20},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "trace_id" in payload
    assert "traceId" not in payload
    assert "playback_instruction" in payload
    assert "playbackInstruction" not in payload
    assert payload["playback_instruction"]["client_loop_until_target_duration"] is True


def test_arkts_contract_files_include_case_adapter_and_camel_domain_types() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/arkts/files")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "v2_3_17"
    assert payload["response_case"] == "snake_case"
    assert payload["client_domain_case"] == "camelCase"
    files = {item["filename"]: item for item in payload["files"]}
    assert "CaseAdapter.ets" in files
    assert "deepSnakeToCamel" in files["CaseAdapter.ets"]["source"]
    assert "mapAgentResponse" in files["CaseAdapter.ets"]["source"]
    assert "intentType" in files["AgentTypes.ets"]["source"]
    assert "playbackInstruction" in files["AgentTypes.ets"]["source"]
    assert "midiBase64" in files["PlaybackTypes.ets"]["source"]
    assert "midi_base64:" not in files["PlaybackTypes.ets"]["source"]
    assert "mapDirectAccompanimentResponse" in files["JamMateApiClient.ets"]["source"]


def test_frontend_fixture_pack_carries_raw_and_camel_mapped_payloads() -> None:
    fixtures = frontend_fixture_pack()["fixtures"]
    assert fixtures["rawBackendAgentPlaybackPrepareResponse"]["playback_instruction"]["client_loop_until_target_duration"] is True
    assert fixtures["agentPlaybackPrepareResponse"]["playbackInstruction"]["clientLoopUntilTargetDuration"] is True
    assert fixtures["rawBackendAgentPlaybackPrepareResponse"]["asset"]["midi_base64"]
    assert fixtures["agentPlaybackPrepareResponse"]["asset"]["midiBase64"]
    assert fixtures["directAccompanimentGenerateResponse"]["asset"]["cacheKey"].startswith("direct_accomp:")


def test_repository_frontend_fixture_pack_writes_case_adapter_file() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_root = root / "frontend_fixtures" / "harmonyos"
    assert (fixture_root / "api" / "CaseAdapter.ets").exists()
    assert "deepSnakeToCamel" in (fixture_root / "api" / "CaseAdapter.ets").read_text(encoding="utf-8")
    assert "mapAgentResponse" in (fixture_root / "api" / "JamMateApiClient.ets").read_text(encoding="utf-8")
    assert "v2_3_17" in (fixture_root / "README.md").read_text(encoding="utf-8")
