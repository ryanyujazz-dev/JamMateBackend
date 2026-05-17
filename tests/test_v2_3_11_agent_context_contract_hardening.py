from __future__ import annotations

from fastapi.testclient import TestClient

from jammate_api.app import app


def test_agent_capability_manifest_exposes_direct_and_agent_paths() -> None:
    client = TestClient(app)
    response = client.get("/agent/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    manifest = data["manifest"]
    tool_names = {tool["name"] for tool in manifest["available_tools"]}
    assert "direct_accompaniment_generate" in tool_names
    assert "agent_playback_prepare" in tool_names
    assert manifest["dependency_boundary"]["jammate_engine_imports_jammate_agent"] is False


def test_context_profile_manifest_documents_playback_and_plan_profiles() -> None:
    client = TestClient(app)
    response = client.get("/agent/context/profiles")
    assert response.status_code == 200
    profiles = response.json()["manifest"]["profiles"]
    profile_types = {profile["task_type"] for profile in profiles}
    assert "practice_plan_generation" in profile_types
    assert "immediate_practice_playback" in profile_types


def test_arkts_contract_sketch_is_available_for_harmonyos() -> None:
    client = TestClient(app)
    response = client.get("/agent/contracts/arkts")
    assert response.status_code == 200
    interfaces = response.json()["contract"]["interfaces"]
    assert "AgentResponse" in interfaces
    assert "PracticePlan" in interfaces
    assert "AccompanimentAsset" in interfaces


def test_agent_trace_is_persisted_and_queryable() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/practice/plan",
        json={"userInput": "我今天有45分钟，想练Misty的ballad comping", "availableMinutes": 45},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    trace_id = payload["trace_id"]
    trace_response = client.get(f"/agent/traces/{trace_id}")
    assert trace_response.status_code == 200
    trace_payload = trace_response.json()
    assert trace_payload["ok"] is True
    assert trace_payload["trace"]["trace_id"] == trace_id
    assert trace_payload["trace"]["steps"]


def test_api_accepts_camel_case_harmonyos_payloads_for_playback() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/playback/prepare",
        json={"userInput": "我想练 Blue Bossa 20分钟", "durationMinutes": 20},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["playback_instruction"]["client_loop_until_target_duration"] is True


def test_agent_engine_dependency_boundary_is_still_adapter_only() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    agent_files = sorted((root / "src" / "jammate_agent").rglob("*.py"))
    offenders = []
    for path in agent_files:
        rel = path.relative_to(root).as_posix()
        if "/adapters/" in rel:
            continue
        text = path.read_text(encoding="utf-8")
        import_lines = [line.strip() for line in text.splitlines() if line.strip().startswith(("import ", "from "))]
        if any("jammate_engine" in line for line in import_lines):
            offenders.append(rel)
    assert offenders == []

    engine_files = sorted((root / "src" / "jammate_engine").rglob("*.py"))
    engine_offenders = []
    for path in engine_files:
        text = path.read_text(encoding="utf-8")
        import_lines = [line.strip() for line in text.splitlines() if line.strip().startswith(("import ", "from "))]
        if any("jammate_agent" in line for line in import_lines):
            engine_offenders.append(path.relative_to(root).as_posix())
    assert engine_offenders == []
