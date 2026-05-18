from __future__ import annotations

from fastapi.testclient import TestClient

from jammate_api.app import app


def test_arkts_source_contract_endpoint_exposes_copyable_interfaces() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/arkts/source")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    contract = payload["contract"]
    assert contract["version"] == "v2_4_11"
    assert contract["filename_suggestion"] == "AgentTypes.ets"
    assert "export interface AgentResponse" in contract["source"]
    assert "export interface PlaybackInstruction" in contract["source"]
    assert "cache_key" in contract["source"]


def test_playback_spec_documents_client_loop_and_cache_policy() -> None:
    client = TestClient(app)
    response = client.get("/agent/playback/spec")
    assert response.status_code == 200
    spec = response.json()["spec"]
    assert spec["version"] == "v2_4_11"
    assert spec["playback_instruction_contract"]["client_loop_until_target_duration"]
    assert spec["playback_instruction_contract"]["requires_local_timer"] is True
    assert spec["asset_cache_policy"]["canonical_field"] == "asset.cache_key"
    assert "POST /accompaniment/generate for explicit manual accompaniment settings" in spec["non_llm_paths"]


def test_usage_examples_include_direct_and_agent_paths() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/examples")
    assert response.status_code == 200
    examples = response.json()["examples"]["examples"]
    assert examples["direct_accompaniment_no_llm"]["path"] == "/accompaniment/generate"
    assert examples["agent_immediate_playback"]["path"] == "/agent/playback/prepare"
    assert "asset.cache_key" in examples["agent_immediate_playback"]["response_focus"]


def test_agent_playback_response_carries_cache_key_and_detailed_loop_instruction() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/playback/prepare",
        json={"userInput": "我想练 Blue Bossa 20分钟", "durationMinutes": 20},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["asset"]["cache_key"]
    instruction = payload["playback_instruction"]
    assert instruction["client_loop_until_target_duration"] is True
    assert instruction["asset_loop_mode"] == "loop_until_target_duration"
    assert instruction["requires_local_timer"] is True
    assert instruction["cache_policy"]["cache_key"] == payload["asset"]["cache_key"]


def test_direct_accompaniment_response_carries_cache_key_without_agent() -> None:
    client = TestClient(app)
    response = client.post(
        "/accompaniment/generate",
        json={"tune": "Blue Bossa", "style": "bossa_nova", "tempo": 120, "choruses": 1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["asset"]["cache_key"].startswith("direct_accomp:")
    assert payload["asset"]["debug_summary"]["path"] == "direct_accompaniment_api"
