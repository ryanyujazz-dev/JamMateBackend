from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION,
    agent_v2_8_phase_cleanup_regression_handoff_contract,
    build_agent_v2_8_phase_cleanup_regression_handoff_payload,
    build_agent_v2_8_phase_cleanup_regression_handoff_summary,
)
from jammate_api.app import app


def test_agent_v2_8_phase_handoff_contract_exposes_routes_command_and_guards() -> None:
    spec = agent_v2_8_phase_cleanup_regression_handoff_contract()
    assert spec["version"] == AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION == "v2_8_23"
    assert spec["spec_route"] == "GET /agent/context/today-practice-guidance/v2-8-phase-handoff/spec"
    assert spec["preview_route"] == "POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview"
    assert spec["terminal_command"] == "/v2-8-phase-handoff [json_payload]"
    assert spec["execution_status"]["phase_handoff_preview_enabled"] is True
    assert spec["execution_status"]["calls_llm_provider"] is False
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_starts_routine"] is False


def test_agent_v2_8_phase_handoff_payload_summarizes_phase_and_preserves_boundaries() -> None:
    payload_obj = build_agent_v2_8_phase_cleanup_regression_handoff_payload(
        {"regressionResults": {"v2_8_regression_count": 157, "agent_targeted_regression_count": 396}}
    )
    payload = payload_obj.to_dict()
    summary = build_agent_v2_8_phase_cleanup_regression_handoff_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_23"
    assert payload["phase_status"] == "phase_handoff_ready"
    assert payload["validation"]["milestone_count"] == 22
    assert [item["version"] for item in payload["completed_milestones"]][:3] == ["v2_8_1", "v2_8_2", "v2_8_3"]
    assert payload["completed_milestones"][-1]["version"] == "v2_8_22"
    assert payload["terminal_smoke_handoff"]["smoke_command"] == "/terminal-product-smoke"
    assert payload["harmonyos_handoff_pack"]["frontend_fixture_files_modified_in_agent_line"] is False
    assert payload["persistence_handoff_pack"]["recommended_next_phase"] == "v2_9_x_agent_persistence_implementation"
    assert summary["milestone_count"] == 22
    assert summary["storage_written"] is False
    assert summary["backend_database_written"] is False
    assert summary["local_device_written"] is False
    assert summary["llm_called"] is False
    assert summary["engine_adapter_called"] is False
    assert summary["routine_start_enabled"] is False


def test_agent_v2_8_phase_handoff_session_and_cli_command_are_available(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.agent_v2_8_phase_cleanup_regression_handoff({})
    assert response["ok"] is True
    assert response["agent_v2_8_phase_cleanup_regression_handoff_summary"]["phase_status"] == "phase_handoff_ready"
    assert response["engine_adapter_called"] is False

    exit_code = run_interactive_chat(["--once", "/v2-8-phase-handoff"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "AgentV28PhaseHandoff>" in out
    assert "milestone_count: 22" in out
    assert "routine_start_enabled: false" in out
    assert "engine_adapter_called: false" in out


def test_agent_v2_8_phase_handoff_preview_route_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/today-practice-guidance/v2-8-phase-handoff/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_23"

    response = client.post("/agent/context/today-practice-guidance/v2-8-phase-handoff/preview", json={}).json()
    assert response["ok"] is True
    summary = response["agent_v2_8_phase_cleanup_regression_handoff_summary"]
    assert summary["phase_status"] == "phase_handoff_ready"
    assert response["llm_called"] is False
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["routine_start_enabled"] is False


def test_agent_v2_8_phase_handoff_advertised_in_context_manifests() -> None:
    manifest = context_profile_manifest()
    assert manifest["agent_v2_8_phase_cleanup_regression_handoff_spec_route"] == "GET /agent/context/today-practice-guidance/v2-8-phase-handoff/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["agent_v2_8_phase_cleanup_regression_handoff"] == "POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview"
    assert runtime["agent_v2_8_phase_cleanup_regression_handoff"]["version"] == "v2_8_23"
    assert CapabilityManifest().to_dict()["supports_agent_v2_8_phase_cleanup_regression_handoff"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["agent_v2_8_phase_cleanup_regression_handoff_version"] == "v2_8_23"


def test_agent_v2_8_phase_handoff_does_not_import_engine_or_touch_frontend_fixture_files() -> None:
    root = Path(__file__).resolve().parents[1]
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_V2_8_23.md"
    frontend_fixture_dir = root / "frontend_fixtures" / "harmonyos"
    assert "from jammate_engine" not in terminal_chat
    assert "from jammate_engine" not in tool_invocation
    assert doc_path.exists()
    assert not any(path.name.endswith("V2_8_23") for path in frontend_fixture_dir.glob("**/*")) if frontend_fixture_dir.exists() else True
