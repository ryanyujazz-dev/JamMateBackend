from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession, run_interactive_chat
from jammate_agent.core.context import CapabilityManifest, ContextBuilder
from jammate_agent.core.contracts import context_profile_manifest, llm_context_runtime_contract
from jammate_agent.core.tool_invocation import (
    CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
    build_context_persistence_storage_adapter_design_payload,
    build_context_persistence_storage_adapter_design_summary,
    context_persistence_storage_adapter_design_contract,
)
from jammate_api.app import app


def test_storage_adapter_design_contract_is_design_only_no_write() -> None:
    spec = context_persistence_storage_adapter_design_contract()
    assert spec["version"] == CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION == "v2_8_10"
    assert spec["spec_route"] == "GET /agent/context/persistence-storage-adapter/spec"
    assert spec["preview_route"] == "POST /agent/context/persistence-storage-adapter/design-preview"
    assert spec["terminal_command"] == "/context-persistence-storage-adapter"
    assert spec["execution_status"]["design_preview_enabled"] is True
    assert spec["execution_status"]["real_storage_adapter_implemented"] is False
    assert spec["execution_status"]["backend_write_enabled"] is False
    assert spec["guards"]["payload_writes_storage"] is False
    assert spec["guards"]["database_connection_created"] is False
    assert spec["guards"]["midi_base64_allowed_in_adapter_payload"] is False


def test_storage_adapter_design_payload_defines_future_interface_without_writes() -> None:
    payload_obj = build_context_persistence_storage_adapter_design_payload(
        {
            "adapterKind": "postgres_backend_adapter",
            "entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary"],
            "apiKey": "SHOULD_NOT_LEAK",
            "midiBase64": "SHOULD_NOT_LEAK",
            "localMidiPath": "/tmp/nope.mid",
        },
        trace_id="trace_storage_adapter_design",
    )
    payload = payload_obj.to_dict()
    summary = build_context_persistence_storage_adapter_design_summary(payload=payload_obj)

    assert payload["payload_contract_version"] == "v2_8_10"
    assert payload["adapter_mode"] == "design_contract_only_no_database_write"
    assert payload["adapter_interface"]["interface_name"] == "ContextPersistenceStorageAdapter"
    assert payload["adapter_interface"]["methods"]["write_confirmed_context"]["implemented_now"] is False
    assert payload["supported_entity_contracts"]["active_practice_plan"]["owner"] == "backend_long_term_context"
    assert payload["operation_contracts"]["practice_plan_persistence_candidate"]["future_operation"] == "upsert_active_practice_plan"
    assert payload["backend_storage_options"]["real_storage_adapter_configured_now"] is False
    assert payload["write_readiness_gate"]["status"] == "design_only_not_write_ready"
    assert payload["validation"]["accepted"] is True
    assert payload["validation"]["design_only"] is True
    assert payload["validation"]["real_adapter_implemented"] is False
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["local_device_written"] is False
    assert payload["llm_called"] is False
    assert payload["tool_executed"] is False
    assert payload["engine_adapter_called"] is False
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False
    assert summary["validation_status"] == "design_only_not_write_ready"
    assert summary["real_adapter_implemented"] is False
    assert summary["real_write_enabled"] is False
    assert summary["storage_written"] is False
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "SHOULD_NOT_LEAK" not in serialized
    assert "/tmp/nope.mid" not in serialized


def test_storage_adapter_design_marks_harmonyos_local_storage_as_client_owned_warning() -> None:
    payload = build_context_persistence_storage_adapter_design_payload({"adapterKind": "harmonyos_local_only"}).to_dict()
    assert payload["validation"]["accepted"] is True
    assert "harmonyos_local_storage_is_client_owned_not_backend_adapter_owned" in payload["validation"]["warnings"]
    assert payload["storage_boundary_alignment"]["harmonyos_local_only_entities"]
    assert payload["guard_summary"]["harmonyos_local_write_enabled"] is False


def test_storage_adapter_design_disabled_kind_blocks_but_still_no_side_effects() -> None:
    payload = build_context_persistence_storage_adapter_design_payload({"adapterKind": "disabled"}).to_dict()
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["status"] == "design_blocked"
    assert "storage_adapter_kind_disabled" in payload["validation"]["blocked_reasons"]
    assert payload["storage_written"] is False
    assert payload["backend_database_written"] is False
    assert payload["tool_executed"] is False


def test_context_and_runtime_manifests_advertise_storage_adapter_design() -> None:
    manifest = context_profile_manifest()
    assert manifest["context_persistence_storage_adapter_design_spec_route"] == "GET /agent/context/persistence-storage-adapter/spec"
    runtime = llm_context_runtime_contract()
    assert runtime["routes"]["context_persistence_storage_adapter_design_preview"] == "POST /agent/context/persistence-storage-adapter/design-preview"
    assert runtime["context_persistence_storage_adapter_design"]["version"] == "v2_8_10"

    capability = CapabilityManifest().to_dict()
    assert capability["supports_context_persistence_storage_adapter_design"] is True
    packet = ContextBuilder().build("today_practice_guidance", "今天该练什么？")
    assert packet.routing_hints["context_persistence_storage_adapter_design_version"] == "v2_8_10"


def test_api_storage_adapter_design_preview_is_side_effect_free() -> None:
    client = TestClient(app)
    spec = client.get("/agent/context/persistence-storage-adapter/spec").json()
    assert spec["ok"] is True
    assert spec["spec"]["version"] == "v2_8_10"

    response = client.post(
        "/agent/context/persistence-storage-adapter/design-preview",
        json={"adapterKind": "sqlite_dev_adapter", "entities": ["active_practice_plan", "routine_history_summary"]},
    ).json()
    assert response["ok"] is True
    assert response["context_persistence_storage_adapter_design_version"] == "v2_8_10"
    assert response["context_persistence_storage_adapter_design_summary"]["validation_status"] == "design_only_not_write_ready"
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


def test_terminal_storage_adapter_design_command_and_once_output(capsys) -> None:  # noqa: ANN001 - pytest fixture.
    session = TerminalChatSession()
    response = session.context_persistence_storage_adapter_design({"adapterKind": "sqlite_dev_adapter"})
    assert response["ok"] is True
    assert response["context_persistence_storage_adapter_design_summary"]["validation_status"] == "design_only_not_write_ready"
    assert response["storage_written"] is False

    exit_code = run_interactive_chat([
        "--once",
        "/context-persistence-storage-adapter " + json.dumps({"adapterKind": "sqlite_dev_adapter"}, ensure_ascii=False),
    ])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ContextPersistenceStorageAdapterDesign>" in out
    assert "version: v2_8_10" in out
    assert "design_only: true" in out
    assert "storage_written: false" in out


def test_storage_adapter_design_does_not_import_engine_or_touch_shared_docs() -> None:
    root = Path(__file__).resolve().parents[1]
    tool_invocation = (root / "src" / "jammate_agent" / "core" / "tool_invocation.py").read_text(encoding="utf-8")
    terminal_chat = (root / "src" / "jammate_agent" / "cli" / "terminal_chat.py").read_text(encoding="utf-8")
    doc_path = root / "docs" / "AGENT_CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_V2_8_10.md"
    assert "from jammate_engine" not in tool_invocation
    assert "from jammate_engine" not in terminal_chat
    assert doc_path.exists()
