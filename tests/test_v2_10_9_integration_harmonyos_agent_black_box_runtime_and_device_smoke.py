from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
SCRIPT = SMOKE_ROOT / "curl_agent_black_box_product_contract_smoke.sh"
COMPLETION_FIXTURE = SMOKE_ROOT / "product_contract_routine_completion_request.json"
GUIDANCE_FIXTURE = SMOKE_ROOT / "product_contract_today_guidance_request.json"
FORBIDDEN_PRODUCT_FIELDS = {
    "dbPath",
    "sqliteDbPath",
    "sqlite_db_path",
    "clientConfirmedRecordWrite",
    "client_confirmed_record_write",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, timeout_seconds: float = 15.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=1.0) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:  # pragma: no cover - diagnostic retained on timeout
            last_error = exc
        time.sleep(0.2)
    raise AssertionError(f"FastAPI service did not become healthy at {base_url}: {last_error}")


def test_product_contract_fixtures_match_frontend_black_box_payloads() -> None:
    completion = _load(COMPLETION_FIXTURE)
    guidance = _load(GUIDANCE_FIXTURE)

    assert FORBIDDEN_PRODUCT_FIELDS.isdisjoint(_walk_keys(completion))
    assert FORBIDDEN_PRODUCT_FIELDS.isdisjoint(_walk_keys(guidance))

    assert completion == {
        "userId": "local-dev-user",
        "sessionId": "practice-session-1779200000000",
        "deviceId": "harmonyos-device-local",
        "routineCompletionRecord": {
            "routineId": "routine-xxx",
            "routineTitle": "今日基础练习",
            "completedAt": "2026-05-20T20:30:00-07:00",
            "durationSeconds": 1800,
            "status": "completed",
            "items": [
                {
                    "itemId": "item-1",
                    "title": "Blue Bossa comping practice",
                    "type": "tune_practice",
                    "durationSeconds": 900,
                    "status": "completed",
                }
            ],
            "notes": "optional user note",
        },
    }
    assert guidance == {
        "userId": "local-dev-user",
        "sessionId": "agent-session-1779200000000",
        "deviceId": "harmonyos-device-local",
        "userMessage": "今天该练什么？",
    }
    assert "providerResult" not in guidance
    assert "userInput" not in guidance


def test_black_box_product_payloads_run_through_backend_without_internal_fields(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "harmonyos_black_box_product_contract.sqlite3"
    monkeypatch.setenv("JAMMATE_AGENT_CONTEXT_DB_PATH", str(db_path))
    client = TestClient(app)

    completion_payload = _load(COMPLETION_FIXTURE)
    guidance_payload = _load(GUIDANCE_FIXTURE)

    completion_response = client.post("/agent/harmonyos/routine-completion-record/execute", json=completion_payload).json()
    assert completion_response["ok"] is True
    assert completion_response["code"] == "routine_completion_record_persisted"
    assert completion_response["data"]["completionRecordPersisted"] is True
    assert completion_response["data"]["nextTodayGuidanceCanReadHistory"] is True
    assert completion_response["debug"]["backendDatabaseWritten"] is True
    assert completion_response["debug"]["sqliteRowCountWritten"] >= 1
    assert completion_response["safety"]["writesHarmonyOSLocalState"] is False
    assert completion_response["safety"]["startsRoutine"] is False
    assert completion_response["safety"]["callsEngineAdapter"] is False
    assert completion_response["safety"]["createsMidiAsset"] is False
    assert completion_response["safety"]["startsPlayback"] is False
    assert completion_response["safety"]["createsPostSessionRecommendationCard"] is False

    guidance_response = client.post("/agent/harmonyos/today-practice-guidance/preview", json=guidance_payload).json()
    assert guidance_response["ok"] is True
    assert guidance_response["code"] in {"today_guidance_ready", "today_guidance_needs_context_or_provider"}
    assert guidance_response["data"]["content"].strip()
    assert guidance_response["data"]["contextSource"] == "sqlite_backend"
    assert guidance_response["data"]["requiresUserConfirmationBeforeRoutineStart"] is True
    assert guidance_response["debug"]["sqliteReadbackAttempted"] is True
    assert guidance_response["debug"]["backendDatabaseRead"] is True
    assert guidance_response["debug"]["sqliteRowsRead"] >= 1
    assert guidance_response["safety"]["backendSQLiteWriteMayOccur"] is False
    assert guidance_response["safety"]["writesHarmonyOSLocalState"] is False
    assert guidance_response["safety"]["startsRoutine"] is False
    assert guidance_response["safety"]["callsEngineAdapter"] is False
    assert guidance_response["safety"]["createsMidiAsset"] is False
    assert guidance_response["safety"]["startsPlayback"] is False
    assert guidance_response["safety"]["createsPostSessionRecommendationCard"] is False


def test_product_contract_smoke_script_calls_real_routes_without_payload_internals() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    smoke_pack = _load(SMOKE_ROOT / "smoke_pack.json")

    assert "GET /health" in script
    assert "POST /agent/harmonyos/routine-completion-record/execute" in script
    assert "POST /agent/harmonyos/today-practice-guidance/preview" in script
    assert "product_contract_routine_completion_request.json" in script
    assert "product_contract_today_guidance_request.json" in script
    assert "assert_product_payload_has_no_internal_fields" in script
    assert "JAMMATE_AGENT_CONTEXT_DB_PATH" in script
    assert "completion[\"sqliteDbPath\"]" not in script
    assert "guidance[\"sqliteDbPath\"]" not in script
    assert "clientConfirmedRecordWrite=true" not in script
    assert "/accompaniment/generate" not in script
    assert "/agent/playback/prepare" not in script

    product_smoke = smoke_pack["black_box_product_contract_runtime_device_smoke"]
    assert product_smoke["version"] == "v2_10_9"
    assert product_smoke["script"] == "curl_agent_black_box_product_contract_smoke.sh"
    assert product_smoke["product_fixtures"]["routine_completion"] == "product_contract_routine_completion_request.json"
    assert product_smoke["product_fixtures"]["today_guidance"] == "product_contract_today_guidance_request.json"
    assert "dbPath" in product_smoke["frontend_must_not_send"]
    assert "sqliteDbPath" in product_smoke["frontend_must_not_send"]
    assert "clientConfirmedRecordWrite" in product_smoke["frontend_must_not_send"]
    assert product_smoke["side_effects"]["harmonyos_local_state_write"] is False
    assert product_smoke["side_effects"]["engine_adapter_call"] is False


def test_product_contract_smoke_docs_include_lan_device_instructions_and_frontend_boundary() -> None:
    readme = (SMOKE_ROOT / "README.md").read_text(encoding="utf-8")
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    task_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    integration_doc = ROOT / "docs" / "INTEGRATION_HARMONYOS_AGENT_BLACK_BOX_RUNTIME_AND_DEVICE_SMOKE_V2_10_9.md"

    assert integration_doc.exists()
    integration_text = integration_doc.read_text(encoding="utf-8")
    for text in (readme, api_doc, integration_text):
        assert "--host 0.0.0.0 --port 8000" in text
        assert "http://<MAC_LAN_IP>:8000" in text
        assert "127.0.0.1" in text
        assert "/health" in text
        assert "dbPath" in text
        assert "sqliteDbPath" in text
        assert "clientConfirmedRecordWrite" in text
        assert "userMessage" in text
    assert "curl_agent_black_box_product_contract_smoke.sh" in api_doc
    assert "v2_10_9 Integration HarmonyOS Agent Black-Box Runtime and Device Smoke" in task_plan
    assert "v2_10_9 — HarmonyOS Agent Black-Box Runtime and Device Smoke" in changelog


def test_live_black_box_product_contract_smoke_runs_against_fastapi(tmp_path: Path) -> None:
    if os.environ.get("JAMMATE_ENABLE_LIVE_FASTAPI_SMOKE") != "1":
        pytest.skip("live FastAPI runtime smoke is opt-in; run with JAMMATE_ENABLE_LIVE_FASTAPI_SMOKE=1")
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    db_path = tmp_path / "harmonyos_black_box_product_contract_live.sqlite3"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["JAMMATE_AGENT_PRODUCT_CONTRACT_SMOKE_RUN_ID"] = "pytest-v2-10-9"
    env["JAMMATE_AGENT_CONTEXT_DB_PATH"] = str(db_path)

    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "jammate_api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        _wait_for_health(base_url)
        completed = subprocess.run(
            ["bash", str(SCRIPT), base_url],
            cwd=SMOKE_ROOT,
            env=env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "PASS: HarmonyOS Agent black-box product-contract smoke completed." in completed.stdout
        assert db_path.exists()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover - cleanup fallback
            server.kill()
            server.wait(timeout=5)
