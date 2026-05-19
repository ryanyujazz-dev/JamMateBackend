from __future__ import annotations

import json
from pathlib import Path

EXPECTED_VERSION = (Path(__file__).resolve().parents[1] / "VERSION").read_text(encoding="utf-8").strip()

from fastapi.testclient import TestClient

from jammate_agent.core.contract_codegen import harmonyos_api_smoke_pack, harmonyos_api_smoke_pack_files
from jammate_api.app import app


def test_smoke_pack_endpoint_exposes_minimum_harmonyos_sequence() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/smoke-pack")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == EXPECTED_VERSION
    steps = payload["minimum_smoke_sequence"]
    assert [step["path"] for step in steps] == ["/health", "/accompaniment/generate", "/agent/playback/prepare"]
    direct_request = payload["requests"]["directAccompanimentBlueBossa"]
    assert direct_request["leadsheet"]["schema_version"] == "jammate_leadsheet_v2"
    assert "sections" in direct_request["leadsheet"]
    assert "written_form" in direct_request["leadsheet"]
    assert direct_request["tune"] == "Blue Bossa"
    assert payload["playback_assertions"]["loop_rule"]


def test_smoke_pack_files_endpoint_exposes_copyable_json_and_curl_script() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/smoke-pack/files")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == EXPECTED_VERSION
    files = {item["relative_path"]: item for item in payload["files"]}
    assert "README.md" in files
    assert "curl_smoke.sh" in files
    assert "smoke_direct_accompaniment_blue_bossa.json" in files
    assert "smoke_agent_playback_blue_bossa.json" in files
    assert "POST /accompaniment/generate" in files["README.md"]["source"]
    assert "/agent/playback/prepare" in files["curl_smoke.sh"]["source"]


def test_smoke_pack_payloads_are_valid_json_and_match_endpoint_contracts() -> None:
    files = {item["relative_path"]: item for item in harmonyos_api_smoke_pack_files()["files"]}
    direct = json.loads(files["smoke_direct_accompaniment_blue_bossa.json"]["source"])
    agent = json.loads(files["smoke_agent_playback_blue_bossa.json"]["source"])
    plan = json.loads(files["smoke_agent_practice_plan_misty.json"]["source"])
    assert direct["leadsheet"]["schema_version"] == "jammate_leadsheet_v2"
    assert "sections" in direct["leadsheet"]
    assert "written_form" in direct["leadsheet"]
    assert direct["tune"] == "Blue Bossa"
    assert direct["outputFormat"] == "midi_base64"
    assert "voicingOverride" in direct
    assert agent["durationMinutes"] == 20
    assert plan["availableMinutes"] == 45


def test_repository_harmonyos_smoke_files_are_present() -> None:
    root = Path(__file__).resolve().parents[1]
    smoke_root = root / "frontend_fixtures" / "harmonyos" / "smoke"
    assert (smoke_root / "README.md").exists()
    assert (smoke_root / "curl_smoke.sh").exists()
    assert (smoke_root / "smoke_pack.json").exists()
    assert EXPECTED_VERSION in (smoke_root / "README.md").read_text(encoding="utf-8")
    assert "Blue Bossa" in (smoke_root / "smoke_direct_accompaniment_blue_bossa.json").read_text(encoding="utf-8")


def test_minimum_smoke_sequence_runs_through_test_client() -> None:
    client = TestClient(app)
    pack = harmonyos_api_smoke_pack()

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    direct_request = pack["requests"]["directAccompanimentBlueBossa"]
    direct = client.post("/accompaniment/generate", json=direct_request)
    assert direct.status_code == 200
    direct_payload = direct.json()
    assert direct_payload["ok"] is True
    assert direct_payload["asset"]["midi_base64"]
    assert direct_payload["asset"]["cache_key"].startswith("direct_accomp:")
    assert direct_payload["asset"]["debug_summary"]["chart_source"] == "request.leadsheet"
    assert direct_payload["asset"]["debug_summary"]["inline_leadsheet_schema_version"] == "jammate_leadsheet_v2"

    agent_request = pack["requests"]["agentPlaybackBlueBossa"]
    agent = client.post("/agent/playback/prepare", json=agent_request)
    assert agent.status_code == 200
    agent_payload = agent.json()
    assert agent_payload["ok"] is True
    assert agent_payload["asset"]["midi_base64"]
    assert agent_payload["playback_instruction"]["client_loop_until_target_duration"] is True
