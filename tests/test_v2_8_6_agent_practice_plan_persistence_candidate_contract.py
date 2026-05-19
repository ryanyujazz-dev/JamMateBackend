from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
    build_practice_plan_persistence_candidate_payload,
    build_practice_plan_persistence_candidate_summary,
    practice_plan_persistence_candidate_contract,
)
from jammate_api.app import app


def _plan() -> dict:
    return {
        "planId": "plan_001",
        "title": "Medium Swing Comping Plan",
        "status": "active",
        "mainFocus": "ii-V-I comping 稳定性",
        "durationMinutes": 30,
        "planBlocks": [
            {"blockId": "b1", "title": "Guide-tone warmup", "style": "medium_swing", "tempo": 96, "durationMinutes": 10},
            {"blockId": "b2", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 120, "durationMinutes": 20},
        ],
        "apiKey": "SHOULD_NOT_LEAK",
        "midiBase64": "SHOULD_NOT_LEAK",
        "localMidiPath": "/tmp/nope.mid",
        "hiddenChainOfThought": "SHOULD_NOT_LEAK",
    }


def _update_args() -> dict:
    return {
        "operation": "update_existing",
        "targetPlanId": "plan_001",
        "existingPracticePlan": {
            "planId": "plan_001",
            "title": "Old Plan",
            "durationMinutes": 20,
            "planBlocks": [{"title": "Old block", "durationMinutes": 20}],
        },
        "practicePlan": _plan(),
        "traceId": "trace_plan_persist",
    }


def test_practice_plan_persistence_candidate_contract_is_preview_only() -> None:
    spec = practice_plan_persistence_candidate_contract()
    assert spec["version"] == PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION == "v2_8_6"
    assert spec["spec_route"] == "GET /agent/practice-plan/persistence-candidate/spec"
    assert spec["preview_route"] == "POST /agent/practice-plan/persistence-candidate/preview"
    assert spec["terminal_command"] == "/practice-plan-persistence-candidate"
    assert spec["execution_status"]["candidate_payload_enabled"] is True
    assert spec["execution_status"]["confirmation_required"] is True
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["execution_status"]["llm_call_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["midi_base64_allowed_in_plan_candidate"] is False


def test_practice_plan_persistence_candidate_payload_normalizes_and_discards_sensitive_fields() -> None:
    payload_obj = build_practice_plan_persistence_candidate_payload({"practicePlan": _plan()}, trace_id="trace_test")
    payload = payload_obj.to_dict()
    summary = build_practice_plan_persistence_candidate_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_6"
    assert payload["operation"] == "save_new"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["block_count"] == 2
    assert payload["candidate_action"]["requires_user_confirmation"] is True
    assert payload["candidate_action"]["writes_now"] is False
    assert payload["confirmation_policy"]["autonomous_write_allowed"] is False
    assert payload["storage_boundary"]["owner"] == "backend_long_term_context"
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert payload["routine_start_enabled"] is False
    assert summary["plan_title"] == "Medium Swing Comping Plan"
    assert summary["block_count"] == 2
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized
    assert "apiKey" not in json.dumps(payload["normalized_practice_plan"], ensure_ascii=False)


def test_update_candidate_builds_diff_preview_without_writing() -> None:
    payload = build_practice_plan_persistence_candidate_payload(_update_args()).to_dict()
    assert payload["operation"] == "update_existing"
    assert payload["target_plan_ref"]["target_plan_id"] == "plan_001"
    assert payload["diff_preview"]["existing_plan_available"] is True
    assert payload["diff_preview"]["changed_field_count"] >= 1
    assert payload["validation"]["storage_written"] is False
    assert payload["guard_summary"]["preview_confirmation_noop_boundary"] is True


def test_context_and_runtime_manifests_advertise_persistence_candidate() -> None:
    manifest = context_profile_manifest()
    assert manifest["practice_plan_persistence_candidate_spec_route"] == "GET /agent/practice-plan/persistence-candidate/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["practice_plan_persistence_candidate_preview"] == "POST /agent/practice-plan/persistence-candidate/preview"
    assert runtime["practice_plan_persistence_candidate_boundary"]["version"] == "v2_8_6"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_practice_plan_persistence_candidate_contract"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["practice_plan_persistence_candidate_contract_version"] == "v2_8_6"


def test_api_persistence_candidate_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/practice-plan/persistence-candidate/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_6"

    response = client.post("/agent/practice-plan/persistence-candidate/preview", json=_update_args()).json()
    assert response["ok"] is True
    assert response["practice_plan_persistence_candidate_contract_version"] == "v2_8_6"
    assert response["practice_plan_persistence_candidate_summary"]["operation"] == "update_existing"
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


def test_terminal_persistence_candidate_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.practice_plan_persistence_candidate({"practicePlan": _plan()})
    assert response["ok"] is True
    assert response["practice_plan_persistence_candidate_summary"]["validation_status"] in {"candidate_ready", "candidate_ready_with_warnings"}
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/practice-plan-persistence-candidate " + json.dumps({"practicePlan": _plan()}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "PracticePlanPersistenceCandidate>" in out
    assert "version: v2_8_6" in out
    assert "storage_written: false" in out
    assert "backend_database_written: false" in out


def test_persistence_candidate_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_V2_8_6.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
