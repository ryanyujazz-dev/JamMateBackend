from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.tool_invocation import (
    PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_harmonyos_agent_action_card,
    build_playback_prepare_guarded_action_payload,
    build_playback_prepare_guarded_design_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_tool_dry_run,
    playback_prepare_guarded_design_contract,
    preview_tool_invocation,
)
from jammate_agent.core.trace import JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _playback_prepare_chain():
    proposal = ToolInvocationProposal(
        tool_name="agent_playback_prepare",
        arguments={
            "userInput": "帮我练 20 分钟 Blue Bossa，bossa，慢一点",
            "durationMinutes": 20,
            "style": "bossa_nova",
            "tempo": 112,
            "tuneTitle": "Blue Bossa",
            "mutedRoles": ["piano"],
            "outputFormat": "midi_base64",
        },
        task_type="immediate_practice_playback",
    )
    preview = preview_tool_invocation(proposal, allowed_tools=["chart_resolve", "agent_playback_prepare"])
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_v269")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)
    return preview, confirmation, approved, execution, dispatch


def test_playback_prepare_guarded_design_contract_blocks_generation_and_playback() -> None:
    spec = playback_prepare_guarded_design_contract()
    assert spec["version"] == PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION == "v2_6_9"
    assert spec["spec_route"] == "GET /agent/actions/playback-prepare/spec"
    assert spec["guarded_preview_route"] == "POST /agent/actions/playback-prepare/guarded-preview"
    assert spec["execution_status"]["playback_prepare_guarded_payload_enabled"] is True
    assert spec["execution_status"]["agent_playback_prepare_real_execution_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["execution_status"]["engine_adapter_dispatch_enabled"] is False
    assert spec["execution_status"]["midi_asset_creation_enabled"] is False
    assert spec["guards"]["payload_calls_accompaniment_generate"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_core_guarded_payload_shapes_routine_candidate_without_side_effects() -> None:
    preview, confirmation, approved, execution, dispatch = _playback_prepare_chain()
    assert preview.ok is True
    assert approved.ok is True
    assert execution.ok is True
    assert dispatch.ok is True
    assert dispatch.workflow_descriptor.workflow_name == "ImmediatePlaybackWorkflow.prepare"

    payload = build_playback_prepare_guarded_action_payload(dispatch, trace_id="trace_v269").to_dict()
    candidate = payload["playback_request_candidate"]
    routine = payload["routine_config_candidate"]

    assert payload["payload_contract_version"] == "v2_6_9"
    assert candidate["tool_name"] == "agent_playback_prepare"
    assert candidate["style"] == "bossa_nova"
    assert candidate["tempo"] == 112
    assert candidate["duration_minutes"] == 20
    assert candidate["tune_title"] == "Blue Bossa"
    assert candidate["call_enabled_now"] is False
    assert candidate["requires_user_start_confirmation"] is True
    assert routine["requires_backend_generation_confirmation"] is True
    assert routine["accompaniment_generate_call_enabled"] is False
    assert routine["playback_execution_enabled"] is False
    assert payload["risk_gate"]["requires_final_routine_start_confirmation"] is True
    assert payload["risk_gate"]["agent_may_execute_without_user"] is False
    assert "POST /accompaniment/generate" in payload["risk_gate"]["blocked_current_stage"]
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False


def test_action_card_embeds_playback_prepare_guarded_payload_after_descriptor_resolution() -> None:
    preview, confirmation, approved, execution, dispatch = _playback_prepare_chain()
    card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=approved,
        execution_result=execution,
        workflow_dispatch_result=dispatch,
        trace_id="trace_action",
    )
    data = card.to_dict()
    payload = data["result_preview"]["playback_prepare_guarded_payload"]
    assert data["tool_name"] == "agent_playback_prepare"
    assert data["execution_status"] == "workflow_descriptor_resolved"
    assert "open_routine_setup" in data["available_client_actions"]
    assert "execute_controlled" not in data["available_client_actions"]
    assert payload["payload_contract_version"] == "v2_6_9"
    assert payload["playback_request_candidate"]["call_enabled_now"] is False
    assert data["route_called"] is False
    assert data["engine_adapter_called"] is False
    assert data["midi_asset_created"] is False

    summary = build_playback_prepare_guarded_design_summary(action_card=card, source="test")
    assert summary["playback_prepare_guarded_design_version"] == "v2_6_9"
    assert summary["has_playback_prepare_guarded_payload"] is True
    assert summary["agent_playback_prepare_execution_enabled"] is False
    assert summary["midi_asset_created"] is False


def test_terminal_playback_prepare_guarded_command_traces_payload(tmp_path: Path) -> None:
    session = TerminalChatSession(task_type="immediate_practice_playback", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    session.preview_tool_call("agent_playback_prepare", {"userInput": "练 20 分钟 Blue Bossa", "durationMinutes": 20, "style": "bossa_nova", "tempo": 112})
    session.confirm_pending_tool()
    session.execute_confirmed_tool_dry_run()
    session.dispatch_confirmed_tool_workflow_dry_run()
    response = session.playback_prepare_guarded_design()

    assert response["ok"] is True
    card = response["action_card"]
    payload = card["result_preview"]["playback_prepare_guarded_payload"]
    assert payload["payload_contract_version"] == "v2_6_9"
    assert payload["playback_request_candidate"]["call_enabled_now"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    matches = [item for item in traces if item["task_type"] == "terminal_playback_prepare_guarded_design"]
    assert len(matches) == 1
    step_names = [step["name"] for step in matches[0]["steps"]]
    assert "terminal_playback_prepare_guarded_payload_built" in step_names
    assert matches[0]["final_response_summary"]["playback_prepare_guarded_design_summary"]["midi_asset_created"] is False


def test_api_playback_prepare_guarded_preview_route() -> None:
    client = TestClient(app)
    spec = client.get("/agent/actions/playback-prepare/spec").json()["spec"]
    assert spec["version"] == "v2_6_9"
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False

    response = client.post(
        "/agent/actions/playback-prepare/guarded-preview",
        json={
            "taskType": "immediate_practice_playback",
            "toolName": "agent_playback_prepare",
            "arguments": {"userInput": "练 20 分钟 Blue Bossa", "durationMinutes": 20, "style": "bossa_nova", "tempo": 112},
            "userApproved": True,
            "traceId": "trace_from_routine",
        },
    ).json()
    assert response["ok"] is True
    card = response["action_card"]
    payload = card["result_preview"]["playback_prepare_guarded_payload"]
    assert payload["payload_contract_version"] == "v2_6_9"
    assert payload["playback_request_candidate"]["style"] == "bossa_nova"
    assert payload["playback_request_candidate"]["tempo"] == 112
    assert payload["playback_request_candidate"]["call_enabled_now"] is False
    assert payload["client_button_semantics"]["primary"]["does_call_accompaniment_generate"] is False
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_trace_and_runtime_specs_expose_playback_prepare_guarded_boundary() -> None:
    trace_spec = trace_api_contract()
    guarded_trace = trace_spec["playback_prepare_guarded_design_trace_contract"]
    assert guarded_trace["version"] == "v2_6_9"
    assert guarded_trace["guarded_payload_enabled"] is True
    assert guarded_trace["agent_playback_prepare_real_execution_enabled"] is False
    assert guarded_trace["accompaniment_generate_call_enabled"] is False
    assert guarded_trace["midi_asset_creation_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["playback_prepare_guarded_design_boundary"]
    assert boundary["version"] == "v2_6_9"
    assert boundary["execution_status"]["agent_playback_prepare_real_execution_enabled"] is False


def test_guarded_design_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
    for rel in [
        "src/jammate_agent/core/tool_invocation.py",
        "src/jammate_agent/cli/terminal_chat.py",
        "src/jammate_agent/core/trace.py",
    ]:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(module == "jammate_engine" or module.startswith("jammate_engine.") for module in imported)
        assert not any(module in {"openai", "anthropic", "requests", "httpx"} or module.startswith(("openai.", "anthropic.")) for module in imported)
