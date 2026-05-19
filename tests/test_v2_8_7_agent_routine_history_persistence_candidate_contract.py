from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
    build_routine_history_persistence_candidate_payload,
    build_routine_history_persistence_candidate_summary,
    routine_history_persistence_candidate_contract,
)
from jammate_api.app import app


def _history_records() -> list[dict]:
    return [
        {
            "sessionId": "session_001",
            "routineId": "routine_blue_bossa",
            "title": "Blue Bossa comping",
            "tuneTitle": "Blue Bossa",
            "style": "bossa_nova",
            "tempo": 118,
            "plannedDurationMinutes": 20,
            "actualSeconds": 1260,
            "completed": True,
            "practiceGoal": "bossa comping 稳定性",
            "planId": "plan_001",
            "planBlockId": "block_bossa",
            "finishedAt": "2026-05-18T16:00:00Z",
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/should_not_leak.mid",
            "currentPositionMs": 12345,
            "asset": {"midi_base64": "SHOULD_NOT_LEAK"},
        },
        {
            "sessionId": "session_002",
            "routineId": "routine_swing",
            "title": "Medium Swing ii-V-I",
            "tuneTitle": "All The Things You Are",
            "style": "medium_swing",
            "tempo": 104,
            "durationMinutes": 10,
            "completed": False,
            "practiceGoal": "ii-V-I comping",
            "finishedAt": "2026-05-18T17:00:00Z",
        },
    ]


def test_routine_history_persistence_candidate_contract_is_preview_only() -> None:
    spec = routine_history_persistence_candidate_contract()
    assert spec["version"] == ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION == "v2_8_7"
    assert spec["spec_route"] == "GET /agent/routine-history/persistence-candidate/spec"
    assert spec["preview_route"] == "POST /agent/routine-history/persistence-candidate/preview"
    assert spec["terminal_command"] == "/routine-history-persistence-candidate"
    assert spec["execution_status"]["candidate_payload_enabled"] is True
    assert spec["execution_status"]["confirmation_required"] is True
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["post_session_recommendation_card_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["midi_base64_allowed_in_history_candidate"] is False
    assert spec["guards"]["local_midi_path_allowed_in_history_candidate"] is False


def test_routine_history_persistence_candidate_payload_normalizes_and_discards_client_only_fields() -> None:
    payload_obj = build_routine_history_persistence_candidate_payload({"routineHistoryRecords": _history_records()}, trace_id="trace_history")
    payload = payload_obj.to_dict()
    summary = build_routine_history_persistence_candidate_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_7"
    assert payload["operation"] == "append_new_records"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["normalized_record_count"] == 2
    assert payload["validation"]["context_item_count"] == 2
    assert payload["candidate_action"]["requires_user_confirmation"] is True
    assert payload["candidate_action"]["writes_now"] is False
    assert payload["candidate_action"]["creates_post_session_recommendation_card"] is False
    assert payload["confirmation_policy"]["autonomous_write_allowed"] is False
    assert payload["storage_boundary"]["object_type"] == "RoutineHistorySummary"
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert payload["post_session_recommendation_card_created"] is False
    assert summary["record_count"] == 2
    assert summary["context_item_count"] == 2
    assert summary["total_practice_minutes"] >= 31
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/should_not_leak.mid" not in serialized
    assert "12345" not in serialized


def test_upsert_candidate_accepts_context_payload_without_writing() -> None:
    context_payload = {"routine_history_records": _history_records()}
    payload = build_routine_history_persistence_candidate_payload(
        {"operation": "upsert", "historyScopeId": "user_001", "routineHistoryContextPayload": context_payload}
    ).to_dict()
    assert payload["operation"] == "upsert_summary_batch"
    assert payload["target_history_ref"]["history_scope_id"] == "user_001"
    assert payload["aggregate_summary"]["completed_count"] == 1
    assert payload["validation"]["storage_written"] is False
    assert payload["guard_summary"]["preview_confirmation_noop_boundary"] is True
    assert payload["guard_summary"]["post_session_recommendation_card_created"] is False


def test_context_and_runtime_manifests_advertise_routine_history_persistence_candidate() -> None:
    manifest = context_profile_manifest()
    assert manifest["routine_history_persistence_candidate_spec_route"] == "GET /agent/routine-history/persistence-candidate/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["routine_history_persistence_candidate_preview"] == "POST /agent/routine-history/persistence-candidate/preview"
    assert runtime["routine_history_persistence_candidate_boundary"]["version"] == "v2_8_7"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_routine_history_persistence_candidate_contract"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["routine_history_persistence_candidate_contract_version"] == "v2_8_7"


def test_api_routine_history_persistence_candidate_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/routine-history/persistence-candidate/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_7"

    response = client.post(
        "/agent/routine-history/persistence-candidate/preview",
        json={"operation": "upsert", "routineHistoryRecords": _history_records()},
    ).json()
    assert response["ok"] is True
    assert response["routine_history_persistence_candidate_contract_version"] == "v2_8_7"
    assert response["routine_history_persistence_candidate_summary"]["operation"] == "upsert_summary_batch"
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


def test_terminal_routine_history_persistence_candidate_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.routine_history_persistence_candidate({"routineHistoryRecords": _history_records()})
    assert response["ok"] is True
    assert response["routine_history_persistence_candidate_summary"]["validation_status"] in {"candidate_ready", "candidate_ready_with_warnings"}
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/routine-history-persistence-candidate " + json.dumps({"routineHistoryRecords": _history_records()}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "RoutineHistoryPersistenceCandidate>" in out
    assert "version: v2_8_7" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out
    assert "post_session_recommendation_card_created: false" in out


def test_routine_history_persistence_candidate_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_V2_8_7.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
