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

ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = ROOT / "frontend_fixtures" / "harmonyos" / "smoke"
SCRIPT = SMOKE_ROOT / "curl_agent_today_guidance_runtime_smoke.sh"


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


def test_strict_harmonyos_agent_runtime_smoke_script_is_agent_only_and_assertive() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    readme = (SMOKE_ROOT / "README.md").read_text(encoding="utf-8")
    smoke_pack = json.loads((SMOKE_ROOT / "smoke_pack.json").read_text(encoding="utf-8"))

    assert "POST /agent/harmonyos/routine-completion-record/execute" in script
    assert "POST /agent/harmonyos/today-practice-guidance/preview" in script
    assert "assert_json_path" in script
    assert "data.nextTodayGuidanceCanReadHistory" in script
    assert "debug.backendDatabaseWritten" in script
    assert "debug.backendDatabaseRead" in script
    assert "safety.startsPlayback" in script
    assert "/accompaniment/generate" not in script
    assert "/agent/playback/prepare" not in script

    assert "curl_agent_today_guidance_runtime_smoke.sh" in readme
    runtime_smoke = smoke_pack["agent_today_guidance_runtime_smoke"]
    assert runtime_smoke["version"] == "v2_10_7"
    assert runtime_smoke["script"] == "curl_agent_today_guidance_runtime_smoke.sh"
    assert "/accompaniment/generate" in runtime_smoke["excluded_routes"]
    assert "/agent/playback/prepare" in runtime_smoke["excluded_routes"]
    assert runtime_smoke["side_effects"]["harmonyos_local_state_write"] is False
    assert runtime_smoke["side_effects"]["engine_adapter_call"] is False


def test_strict_harmonyos_agent_runtime_smoke_runs_against_live_fastapi(tmp_path: Path) -> None:
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    db_path = tmp_path / "harmonyos_agent_today_guidance_runtime_smoke.sqlite"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["JAMMATE_AGENT_RUNTIME_SMOKE_RUN_ID"] = "pytest-v2-10-7"

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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_health(base_url)
        completed = subprocess.run(
            ["bash", str(SCRIPT), base_url, str(db_path)],
            cwd=SMOKE_ROOT,
            env=env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "PASS: HarmonyOS Agent today-guidance runtime smoke completed." in completed.stdout
        assert db_path.exists()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover - cleanup fallback
            server.kill()
            server.wait(timeout=5)
        stdout = server.stdout.read() if server.stdout is not None else ""
        stderr = server.stderr.read() if server.stderr is not None else ""
        if server.returncode not in (0, -15, None):
            raise AssertionError(f"uvicorn exited unexpectedly: stdout={stdout}\nstderr={stderr}")


def test_runtime_smoke_contract_docs_are_present() -> None:
    api_doc = (ROOT / "docs" / "API_CONTRACT_V2.md").read_text(encoding="utf-8")
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    task_plan = (ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md").read_text(encoding="utf-8")
    runtime_doc = ROOT / "docs" / "INTEGRATION_HARMONYOS_AGENT_TODAY_GUIDANCE_RUNTIME_SMOKE_V2_10_7.md"

    assert runtime_doc.exists()
    runtime_text = runtime_doc.read_text(encoding="utf-8")
    assert "curl_agent_today_guidance_runtime_smoke.sh" in api_doc
    assert "v2_10_7 — HarmonyOS Agent Today Guidance Runtime Smoke" in changelog
    assert "v2_10_7 Integration HarmonyOS Agent Today Guidance Runtime Smoke" in task_plan
    assert "debug.sqliteRowsRead>=1" in runtime_text
    assert "/accompaniment/generate" in runtime_text
    assert "/agent/playback/prepare" in runtime_text
