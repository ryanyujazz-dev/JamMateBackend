from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
    build_context_persistence_confirmation_boundary_payload,
    build_context_persistence_confirmation_boundary_summary,
    context_persistence_confirmation_boundary_contract,
)
from jammate_api.app import app


def _plan() -> dict:
    return {
        "planId": "plan_001",
        "title": "Medium Swing Comping Plan",
        "mainFocus": "ii-V-I comping 稳定性",
        "planBlocks": [
            {"title": "Guide-tone warmup", "style": "medium_swing", "tempo": 96, "durationMinutes": 10},
            {"title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 120, "durationMinutes": 20},
        ],
        "apiKey": "SHOULD_NOT_LEAK",
        "midiBase64": "SHOULD_NOT_LEAK",
        "localMidiPath": "/tmp/nope.mid",
    }


def _history_records() -> list[dict]:
    return [
        {
            "sessionId": "session_001",
            "title": "Blue Bossa comping",
            "tuneTitle": "Blue Bossa",
            "style": "bossa_nova",
            "tempo": 118,
            "actualSeconds": 1260,
            "completed": True,
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/nope.mid",
        }
    ]


def test_context_persistence_confirmation_contract_is_record_only() -> None:
    spec = context_persistence_confirmation_boundary_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION == "v2_8_8"
    assert spec["spec_route"] == "GET /agent/context/persistence-confirmation/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-confirmation/preview"
    assert spec["terminal_command"] == "/context-persistence-confirmation"
    assert spec["execution_status"]["confirmation_record_enabled"] is True
    assert spec["execution_status"]["future_persistence_executor_implemented"] is False
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["midi_base64_allowed_in_context_confirmation"] is False


def test_practice_plan_candidate_can_be_confirmed_without_writing_storage() -> None:
    payload_obj = build_context_persistence_confirmation_boundary_payload(
        {"candidateKind": "practice_plan", "practicePlan": _plan(), "userDecision": "approved"},
        trace_id="trace_confirm_plan",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_confirmation_boundary_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_8"
    assert payload["candidate_kind"] == "practice_plan_persistence_candidate"
    assert payload["user_decision"] == "approved"
    assert payload["confirmation_status"] == "user_approved_future_executor_required"
    assert payload["confirmation_envelope"]["would_write_if_future_executor_confirmed"] is True
    assert payload["future_executor_boundary"]["implemented_now"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert summary["candidate_kind"] == "practice_plan_persistence_candidate"
    assert summary["future_executor_required"] is True
    assert summary["future_executor_implemented"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized


def test_routine_history_candidate_confirmation_keeps_post_session_card_disabled() -> None:
    payload = build_context_persistence_confirmation_boundary_payload(
        {"candidateKind": "routine_history", "routineHistoryRecords": _history_records(), "decision": "confirm"}
    ).to_dict()
    assert payload["candidate_kind"] == "routine_history_persistence_candidate"
    assert payload["confirmation_status"] == "user_approved_future_executor_required"
    assert payload["validation"]["accepted"] is True
    assert payload["post_session_recommendation_card_created"] is False
    assert payload["guard_summary"]["post_session_recommendation_card_created"] is False
    assert payload["storage_written"] is False
    assert payload["future_executor_boundary"]["implemented_now"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized


def test_unknown_confirmation_candidate_is_blocked_without_side_effects() -> None:
    payload = build_context_persistence_confirmation_boundary_payload({"candidateKind": "unknown", "userDecision": "approved"}).to_dict()
    assert payload["candidate_kind"] == "unknown"
    assert payload["confirmation_status"] == "not_confirmable"
    assert payload["validation"]["accepted"] is False
    assert "unsupported_or_missing_persistence_candidate_kind" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["tool_executed"] is False


def test_context_and_runtime_manifests_advertise_confirmation_boundary() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_confirmation_boundary_spec_route"] == "GET /agent/context/persistence-confirmation/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_confirmation_boundary_preview"] == "POST /agent/context/persistence-confirmation/preview"
    assert runtime["context_persistence_confirmation_boundary"]["version"] == "v2_8_8"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_confirmation_boundary"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_confirmation_boundary_version"] == "v2_8_8"


def test_api_context_persistence_confirmation_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-confirmation/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_8"

    response = client.post(
        "/agent/context/persistence-confirmation/preview",
        json={"candidateKind": "practice_plan", "practicePlan": _plan(), "userDecision": "approved"},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_confirmation_boundary_version"] == "v2_8_8"
    assert response["context_persistence_confirmation_boundary_summary"]["confirmation_status"] == "user_approved_future_executor_required"
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


def test_terminal_context_persistence_confirmation_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_confirmation_boundary({"candidateKind": "practice_plan", "practicePlan": _plan()})
    assert response["ok"] is True
    assert response["context_persistence_confirmation_boundary_summary"]["validation_status"] in {"confirmation_ready", "confirmation_ready_with_warnings"}
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-confirmation " + json.dumps({"candidateKind": "practice_plan", "practicePlan": _plan()}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceConfirmationBoundary>" in out
    assert "version: v2_8_8" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "future_executor_implemented: false" in out


def test_confirmation_boundary_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_V2_8_8.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
