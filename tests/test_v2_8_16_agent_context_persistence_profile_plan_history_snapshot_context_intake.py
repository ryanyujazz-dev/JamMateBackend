from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
    build_context_persistence_dev_sqlite_fixture_store_payload,
    build_context_persistence_profile_plan_history_snapshot_context_intake_payload,
    build_context_persistence_profile_plan_history_snapshot_context_intake_summary,
    context_persistence_profile_plan_history_snapshot_context_intake_contract,
)
from jammate_api.app import app


def _write_dev_fixture(path: Path, *, trace_id: str = "trace_snapshot_intake") -> None:
    payload = build_context_persistence_dev_sqlite_fixture_store_payload(
        {
            "fixtureStoreWriteEnabled": True,
            "executeFixtureStore": True,
            "fixtureStorePath": str(path),
            "environment": "test",
            "userDecision": "approved",
            "confirmationStatus": "user_approved_future_executor_required",
            "candidateKind": "practice_plan_persistence_candidate",
            "candidateId": "candidate_snapshot_001",
            "confirmationId": "confirmation_snapshot_001",
            "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
        },
        trace_id=trace_id,
    ).to_dict()
    assert payload["fixture_store_result"]["fixture_store_write_executed"] is True


def test_snapshot_context_intake_contract_is_context_only() -> None:
    spec = context_persistence_profile_plan_history_snapshot_context_intake_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION == "v2_8_16"
    assert spec["spec_route"] == "GET /agent/context/persistence-snapshot-context-intake/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-snapshot-context-intake/preview"
    assert spec["terminal_command"] == "/context-persistence-snapshot-context-intake"
    assert spec["execution_status"]["snapshot_context_intake_defined"] is True
    assert spec["execution_status"]["context_packet_injection_previewed"] is True
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["payload_calls_llm"] is False
    assert spec["guards"]["payload_calls_engine_adapter"] is False
    assert spec["guards"]["payload_creates_midi_asset"] is False


def test_snapshot_context_intake_builds_context_sections_from_explicit_payloads() -> None:
    payload_obj = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        {
            "userPracticeProfile": {
                "currentGoal": "提高 jazz comping 稳定性",
                "preferredStyles": ["medium_swing"],
                "comfortableTempoRanges": {"medium_swing": [130, 90]},
            },
            "practicePlan": {
                "title": "Medium Swing Comping Plan",
                "planBlocks": [{"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 100, "durationMinutes": 12}],
            },
            "routineHistoryRecords": [
                {"sessionId": "session_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": True}
            ],
        },
        trace_id="trace_explicit_snapshot_intake",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_profile_plan_history_snapshot_context_intake_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_16"
    assert payload["validation"]["status"] == "snapshot_context_intake_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["context_builder_injection_preview"]["context_builder_can_accept_section"] is True
    assert "user_practice_profile_context" in payload["normalized_context_sections"]
    assert "active_practice_plan_context" in payload["normalized_context_sections"]
    assert "routine_history_context" in payload["normalized_context_sections"]
    assert payload["normalized_context_sections"]["user_practice_profile_context"]["profile"]["comfortable_tempo_ranges"]["medium_swing"]["min"] == 90
    assert summary["profile_context_present"] is True
    assert summary["active_plan_context_present"] is True
    assert summary["routine_history_context_present"] is True
    assert summary["storage_written"] is False
    assert summary["engine_adapter_called"] is False


def test_snapshot_context_intake_reads_dev_fixture_and_context_builder_injects_sections(tmp_path: Path) -> None:
    fixture_path = tmp_path / "snapshot_fixture_store.jsonl"
    _write_dev_fixture(fixture_path, trace_id="trace_fixture_snapshot_intake")
    payload_obj = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        {
            "fixtureStorePath": str(fixture_path),
            "environment": "test",
            "filterTraceId": "trace_fixture_snapshot_intake",
            "userId": "dev_user",
        },
        trace_id="trace_fixture_snapshot_intake",
    )
    payload = payload_obj.to_dict()
    section = payload["context_packet_section"]

    assert payload["snapshot_source"] == "dev_fixture_readback_bridge"
    assert payload["validation"]["accepted"] is True
    assert payload["readback_summary"]["matched_record_count"] == 1
    assert payload["normalized_context_sections"]["user_practice_profile_context"]["profile_status"] == "restored_snapshot_preview_metadata_only"
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["sqlite_connection_created"] is False
    assert payload["engine_adapter_called"] is False

    packet = ContextBuilder().build(
        "today_practice_guidance",
        "今天该练什么？",
        context_persistence_snapshot_context_intake=section,
    )
    assert packet.learner_context["user_practice_profile_context"]["profile_status"] == "restored_snapshot_preview_metadata_only"
    assert packet.learner_context["active_practice_plan_context"]["active_plan"]["plan_status"] == "restored_snapshot_preview_metadata_only"
    assert packet.learner_context["routine_history_context"]["section_name"] == "practice_history_context"
    assert packet.learner_context["context_persistence_snapshot_context_intake"]
    assert "context_persistence_snapshot_context_intake" in packet.selected_context_layers
    assert packet.routing_hints["context_persistence_profile_plan_history_snapshot_context_intake_version"] == "v2_8_16"
    assert packet.routing_hints["context_persistence_snapshot_context_intake_present"] is True


def test_snapshot_context_intake_blocks_sensitive_payload() -> None:
    payload = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        {"apiKey": "SHOULD_NOT_LEAK", "midiBase64": "SHOULD_NOT_LEAK"},
        trace_id="trace_sensitive_snapshot_intake",
    ).to_dict()
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "snapshot_context_intake_blocked"
    assert "forbidden_context_fields_present" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["engine_adapter_called"] is False


def test_context_and_runtime_manifests_advertise_snapshot_context_intake() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_profile_plan_history_snapshot_context_intake_spec_route"] == "GET /agent/context/persistence-snapshot-context-intake/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_profile_plan_history_snapshot_context_intake"] == "POST /agent/context/persistence-snapshot-context-intake/preview"
    assert runtime["context_persistence_profile_plan_history_snapshot_context_intake"]["version"] == "v2_8_16"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_profile_plan_history_snapshot_context_intake"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_profile_plan_history_snapshot_context_intake_version"] == "v2_8_16"


def test_api_snapshot_context_intake_preview(tmp_path: Path) -> None:
    fixture_path = tmp_path / "api_snapshot_fixture_store.jsonl"
    _write_dev_fixture(fixture_path, trace_id="trace_api_snapshot_intake")
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-snapshot-context-intake/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_16"

    response = client.post(
        "/agent/context/persistence-snapshot-context-intake/preview",
        json={"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_api_snapshot_intake"},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_profile_plan_history_snapshot_context_intake_version"] == "v2_8_16"
    assert response["context_persistence_profile_plan_history_snapshot_context_intake_summary"]["validation_status"] == "snapshot_context_intake_ready"
    assert response["context_persistence_profile_plan_history_snapshot_context_intake_summary"]["context_builder_can_accept_section"] is True
    assert response["storage_written"] is False
    assert response["backend_database_written"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False


def test_terminal_snapshot_context_intake_command(tmp_path: Path, capsys) -> None:  # noqa: ANN001 - pytest fixture.
    fixture_path = tmp_path / "terminal_snapshot_fixture_store.jsonl"
    _write_dev_fixture(fixture_path, trace_id="trace_terminal_snapshot_intake")
    session = TerminalChatSession()
    response = session.context_persistence_profile_plan_history_snapshot_context_intake(
        {"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_terminal_snapshot_intake"}
    )
    assert response["ok"] is True
    assert response["context_persistence_profile_plan_history_snapshot_context_intake_summary"]["validation_status"] == "snapshot_context_intake_ready"

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-snapshot-context-intake " + json.dumps(
            {"fixtureStorePath": str(fixture_path), "environment": "test", "filterTraceId": "trace_terminal_snapshot_intake"},
            ensure_ascii=False,
        ),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceProfilePlanHistorySnapshotContextIntake>" in out
    assert "version: v2_8_16" in out
    assert "context_builder_can_accept_section: True" in out
    assert "sqlite_connection_created: false" in out
    assert "backend_database_written: false" in out


def test_snapshot_context_intake_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_SNAPSHOT_CONTEXT_INTAKE_V2_8_16.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
