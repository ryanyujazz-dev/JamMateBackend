from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
    build_context_persistence_confirmation_boundary_payload,
    build_context_persistence_executor_noop_payload,
    build_context_persistence_executor_noop_summary,
    context_persistence_executor_noop_contract,
)
from jammate_api.app import app


def _plan() -> dict:
    return {
        "planId": "plan_001",
        "title": "Medium Swing Comping Plan",
        "mainFocus": "ii-V-I comping 稳定性",
        "planBlocks": [
            {"title": "Guide-tone warmup", "style": "medium_swing", "tempo": 96, "durationMinutes": 10},
        ],
        "apiKey": "SHOULD_NOT_LEAK",
        "midiBase64": "SHOULD_NOT_LEAK",
        "localMidiPath": "/tmp/nope.mid",
    }


def _approved_confirmation() -> dict:
    return build_context_persistence_confirmation_boundary_payload(
        {"candidateKind": "practice_plan", "practicePlan": _plan(), "userDecision": "approved"},
        trace_id="trace_executor_noop",
    ).to_dict()


def test_context_persistence_executor_noop_contract_is_no_write() -> None:
    spec = context_persistence_executor_noop_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION == "v2_8_9"
    assert spec["spec_route"] == "GET /agent/context/persistence-executor-noop/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-executor-noop/preview"
    assert spec["terminal_command"] == "/context-persistence-executor-noop"
    assert spec["execution_status"]["noop_executor_enabled"] is True
    assert spec["execution_status"]["real_persistence_executor_implemented"] is False
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["midi_base64_allowed_in_executor_payload"] is False


def test_approved_confirmation_becomes_noop_executor_ready_without_storage_write() -> None:
    payload_obj = build_context_persistence_executor_noop_payload(
        {"contextPersistenceConfirmationBoundaryPayload": _approved_confirmation()},
        trace_id="trace_executor_noop",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_executor_noop_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_9"
    assert payload["candidate_kind"] == "practice_plan_persistence_candidate"
    assert payload["validation"]["status"] == "noop_executor_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["noop_execution_result"]["would_write_if_real_executor_existed"] is True
    assert payload["noop_execution_result"]["write_attempted"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert summary["validation_status"] == "noop_executor_ready"
    assert summary["future_real_executor_implemented"] is False
    assert summary["write_attempted"] is False
    assert summary["storage_written"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized


def test_pending_confirmation_blocks_executor_without_side_effects() -> None:
    payload = build_context_persistence_executor_noop_payload(
        {"candidateKind": "practice_plan", "practicePlan": _plan(), "userDecision": "pending"}
    ).to_dict()
    assert payload["validation"]["status"] == "noop_executor_blocked"
    assert payload["validation"]["accepted"] is False
    assert "user_confirmation_not_approved" in payload["validation"]["blocked_reasons"]
    assert payload["noop_execution_result"]["would_write_if_real_executor_existed"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["tool_executed"] is False


def test_idempotency_key_is_stable_for_same_confirmation() -> None:
    confirmation = _approved_confirmation()
    first = build_context_persistence_executor_noop_payload({"confirmationPayload": confirmation}).to_dict()
    second = build_context_persistence_executor_noop_payload({"confirmationPayload": confirmation}).to_dict()
    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["idempotency_key"].startswith("ctx_persist_noop_")


def test_context_and_runtime_manifests_advertise_noop_executor() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_executor_noop_spec_route"] == "GET /agent/context/persistence-executor-noop/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_executor_noop_preview"] == "POST /agent/context/persistence-executor-noop/preview"
    assert runtime["context_persistence_executor_noop"]["version"] == "v2_8_9"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_executor_noop"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_executor_noop_version"] == "v2_8_9"


def test_api_context_persistence_executor_noop_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-executor-noop/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_9"

    response = client.post(
        "/agent/context/persistence-executor-noop/preview",
        json={"contextPersistenceConfirmationBoundaryPayload": _approved_confirmation()},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_executor_noop_version"] == "v2_8_9"
    assert response["context_persistence_executor_noop_summary"]["validation_status"] == "noop_executor_ready"
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["post_session_recommendation_card_created"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_context_persistence_executor_noop_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_executor_noop({"contextPersistenceConfirmationBoundaryPayload": _approved_confirmation()})
    assert response["ok"] is True
    assert response["context_persistence_executor_noop_summary"]["validation_status"] == "noop_executor_ready"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-executor-noop " + json.dumps({"contextPersistenceConfirmationBoundaryPayload": _approved_confirmation()}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceExecutorNoop>" in out
    assert "version: v2_8_9" in out
    assert "noop_only: true" in out
    assert "write_attempted: false" in out
    assert "storage_written: false" in out


def test_noop_executor_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_EXECUTOR_NOOP_SKELETON_V2_8_9.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
