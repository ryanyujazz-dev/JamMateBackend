from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
    build_practice_context_storage_boundary_payload,
    build_practice_context_storage_boundary_summary,
    practice_context_storage_boundary_contract,
)
from jammate_api.app import app


def _storage_boundary_input() -> dict:
    return {
        "userPracticeProfile": {"currentGoal": "提高 comping 稳定性", "preferredStyles": ["medium_swing"]},
        "activePracticePlan": {"planId": "plan_001", "title": "Comping Plan"},
        "routineHistoryRecords": [{"sessionId": "s1", "style": "medium_swing", "actualSeconds": 600}],
        "currentRoutineSession": {"sessionId": "live_1", "timerState": "running", "playbackPosition": 128},
        "playbackState": {"localMidiPath": "/tmp/jammate.mid", "midiBase64": "SHOULD_NOT_LEAK"},
        "availableMinutes": 20,
        "userInput": "今天该练什么？",
        "traceId": "trace_001",
        "apiKey": "SHOULD_NOT_LEAK",
        "hiddenChainOfThought": "SHOULD_NOT_LEAK",
    }


def test_storage_boundary_contract_is_preview_only() -> None:
    spec = practice_context_storage_boundary_contract()
    assert spec["version"] == PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION == "v2_8_2"
    assert spec["spec_route"] == "GET /agent/context/storage-boundary/spec"
    assert spec["preview_route"] == "POST /agent/context/storage-boundary/preview"
    assert spec["terminal_command"] == "/practice-context-storage-boundary"
    assert spec["execution_status"]["storage_boundary_payload_enabled"] is True
    assert spec["execution_status"]["database_persistence_implemented"] is False
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert "harmonyos_local_only" in spec["ownership_categories"]
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["midi_base64_allowed_in_agent_context"] is False


def test_storage_boundary_payload_classifies_context_without_echoing_sensitive_values() -> None:
    payload_obj = build_practice_context_storage_boundary_payload(_storage_boundary_input(), trace_id="trace_test")
    payload = payload_obj.to_dict()
    assert payload["payload_contract_version"] == "v2_8_2"
    assert payload["validation"]["status"] == "boundary_ready_with_warnings"
    assert payload["validation"]["contains_midi_base64_input"] is True
    assert payload["validation"]["contains_local_midi_path_input"] is True
    assert payload["validation"]["contains_api_key_input"] is True
    assert payload["validation"]["contains_hidden_chain_of_thought_input"] is True
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/jammate.mid" not in serialized
    assert "active_practice_plan" in payload["field_classification"]["detected_context_signals"]
    assert payload["field_classification"]["ownership_by_signal"]["current_routine_session"] == "harmonyos_local_only"
    assert payload["field_classification"]["ownership_by_signal"]["user_practice_profile"] == "backend_long_term_context"
    assert any(row["context_object"] == "RoutineSessionLiveState" and row["may_enter_context_packet"] is False for row in payload["ownership_matrix"])
    assert "midi_base64 asset payload" in payload["context_packet_boundary"]["must_not_enter_context_packet"]


def test_storage_boundary_summary_and_manifests_are_exposed() -> None:
    payload_obj = build_practice_context_storage_boundary_payload(_storage_boundary_input())
    summary = build_practice_context_storage_boundary_summary(payload=payload_obj)
    assert summary["practice_context_storage_boundary_version"] == "v2_8_2"
    assert summary["ownership_category_count"] >= 5
    assert summary["storage_contract_only"] is True
    assert summary["backend_write_enabled"] is False
    assert summary["midi_asset_created"] is False

    manifest = context_profile_manifest()
    assert manifest["practice_context_storage_boundary_spec_route"] == "GET /agent/context/storage-boundary/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["practice_context_storage_boundary_preview"] == "POST /agent/context/storage-boundary/preview"
    assert runtime["practice_context_storage_boundary"]["version"] == "v2_8_2"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_practice_context_storage_boundary_contract"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["practice_context_storage_boundary_version"] == "v2_8_2"


def test_api_storage_boundary_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/storage-boundary/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_2"

    response = client.post("/agent/context/storage-boundary/preview", json=_storage_boundary_input()).json()
    assert response["ok"] is True
    assert response["practice_context_storage_boundary_version"] == "v2_8_2"
    assert response["practice_context_storage_boundary_payload"]["validation"]["storage_contract_only"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["local_device_written"] is False
    assert response["llm_called"] is False
    assert response["tool_executed"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False
    assert response["accompaniment_generate_call_enabled"] is False
    assert response["routine_start_enabled"] is False


def test_terminal_storage_boundary_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.practice_context_storage_boundary(_storage_boundary_input())
    assert response["ok"] is True
    assert response["practice_context_storage_boundary_summary"]["validation_status"] == "boundary_ready_with_warnings"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        '/practice-context-storage-boundary {"availableMinutes":20,"userPracticeProfile":{"currentGoal":"comping"},"playbackState":{"localMidiPath":"/tmp/nope.mid"}}',
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PracticeContextStorageBoundary>" in out
    assert "version: v2_8_2" in out
    assert "storage_written: false" in out
    assert "backend_write_enabled: false" in out


def test_storage_boundary_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_PRACTICE_CONTEXT_STORAGE_BOUNDARY_V2_8_2.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
