from __future__ import annotations

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from jammate_agent.cli.terminal_chat import TerminalChatSession
from jammate_agent.core.context import CONTEXT_PROFILES
from jammate_agent.core.tool_invocation import (
    ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
    ToolInvocationProposal,
    build_confirmation_envelope,
    build_harmonyos_agent_action_card,
    build_routine_config_prepare_action_payload,
    build_routine_config_prepare_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_tool_dry_run,
    preview_tool_invocation,
    routine_config_prepare_contract,
)
from jammate_agent.core.tool_registry import get_tool_descriptor
from jammate_agent.core.trace import trace_api_contract
from jammate_api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _routine_config_chain(arguments: dict | None = None):
    proposal = ToolInvocationProposal(
        tool_name="agent_routine_config_prepare",
        arguments=arguments
        or {
            "userInput": "帮我建一个 30 分钟 Blue Bossa bossa routine，速度 132，只留 bass drums",
            "durationMinutes": 30,
            "style": "bossa_nova",
            "tempo": 132,
            "tuneTitle": "Blue Bossa",
            "mutedRoles": ["piano"],
        },
        task_type="coach_qa",
    )
    preview = preview_tool_invocation(
        proposal,
        allowed_tools=["agent_practice_plan", "agent_playback_prepare", "agent_routine_config_prepare"],
    )
    confirmation = build_confirmation_envelope(preview, proposal_id="proposal_v270")
    approved = confirm_tool_invocation(confirmation, user_approved=True)
    execution = execute_tool_dry_run(approved)
    dispatch = dispatch_deterministic_workflow_dry_run(execution)
    return preview, confirmation, approved, execution, dispatch


def test_routine_config_prepare_contract_is_draft_only() -> None:
    spec = routine_config_prepare_contract()
    assert spec["version"] == ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION == "v2_7_0"
    assert spec["spec_route"] == "GET /agent/actions/routine-config/spec"
    assert spec["prepare_route"] == "POST /agent/actions/routine-config/prepare"
    assert spec["execution_status"]["routine_config_payload_enabled"] is True
    assert spec["execution_status"]["open_routine_setup_enabled"] is True
    assert spec["execution_status"]["routine_start_enabled"] is False
    assert spec["execution_status"]["accompaniment_generate_call_enabled"] is False
    assert spec["guards"]["payload_calls_accompaniment_generate"] is False
    assert spec["guards"]["payload_starts_playback"] is False


def test_registry_and_context_allow_agent_routine_config_prepare_without_engine_execution() -> None:
    descriptor = get_tool_descriptor("agent_routine_config_prepare")
    assert descriptor is not None
    assert descriptor.deterministic_workflow == "RoutineConfigPreparer.prepare_candidate"
    assert descriptor.side_effect_level == "none"
    assert descriptor.route == "POST /agent/actions/routine-config/prepare"
    assert descriptor.execution_enabled is False
    assert "agent_routine_config_prepare" not in CONTEXT_PROFILES["practice_plan_generation"].allowed_tools
    assert "agent_routine_config_prepare" not in CONTEXT_PROFILES["immediate_practice_playback"].allowed_tools
    assert "agent_routine_config_prepare" not in CONTEXT_PROFILES["coach_qa"].allowed_tools


def test_core_payload_derives_editable_routine_config_from_user_intent() -> None:
    _, _, _, _, dispatch = _routine_config_chain()
    assert dispatch.ok is True
    assert dispatch.workflow_descriptor.workflow_name == "RoutineConfigPreparer.prepare_candidate"
    payload = build_routine_config_prepare_action_payload(
        dispatch.execution_result.request.arguments_preview,
        trace_id="trace_v270",
    ).to_dict()
    candidate = payload["routine_config_candidate"]
    assert payload["payload_contract_version"] == "v2_7_0"
    assert candidate["routine_name"] == "Blue Bossa Routine"
    assert candidate["duration_minutes"] == 30
    assert candidate["style"] == "bossa_nova"
    assert candidate["tempo"] == 132
    assert candidate["tune_title"] == "Blue Bossa"
    assert candidate["editable"] is True
    assert candidate["requires_user_start_confirmation"] is True
    assert candidate["accompaniment_generate_call_enabled"] is False
    assert candidate["playback_execution_enabled"] is False
    assert candidate["accompaniment_request_candidate"]["call_enabled_now"] is False
    assert payload["validation"]["call_enabled_now"] is False
    assert "open_routine_setup" in payload["next_client_actions"]
    assert payload["midi_asset_created"] is False
    assert payload["playback_started"] is False


def test_core_payload_can_derive_from_practice_plan_block() -> None:
    plan = {
        "title": "Blue Bossa Comping 30",
        "duration_minutes": 30,
        "main_focus": "Comping with rhythm section",
        "blocks": [
            {"block_id": "warmup", "title": "Warmup", "duration_minutes": 5, "intent": "light voicing"},
            {
                "block_id": "play",
                "title": "Blue Bossa comping",
                "duration_minutes": 20,
                "intent": "comp with bass and drums",
                "material": {"type": "tune", "tune": "Blue Bossa"},
                "style": "bossa_nova",
                "tempo": 118,
                "accompaniment_config": {
                    "enabled": True,
                    "style": "bossa_nova",
                    "tempo": 118,
                    "muted_roles": ["piano"],
                    "count_in": True,
                    "section_loop": True,
                    "output_format": "midi_base64",
                },
            },
            {"block_id": "review", "title": "Review", "duration_minutes": 5},
        ],
    }
    payload = build_routine_config_prepare_action_payload({"practicePlan": plan}, trace_id="trace_plan").to_dict()
    candidate = payload["routine_config_candidate"]
    assert candidate["routine_name"] == "Blue Bossa Comping 30"
    assert candidate["practice_goal"] == "Comping with rhythm section"
    assert candidate["duration_minutes"] == 30
    assert candidate["style"] == "bossa_nova"
    assert candidate["tempo"] == 118
    assert candidate["tune_title"] == "Blue Bossa"
    assert len(payload["routine_blocks"]) == 3
    assert payload["source_inputs"]["practice_plan_block_count"] == 3
    assert payload["source_inputs"]["derived_from_playable_block"] is True
    assert payload["routine_blocks"][1]["accompaniment_request_candidate"]["call_enabled_now"] is False
    assert payload["accompaniment_generate_call_enabled"] is False


def test_action_card_embeds_routine_config_prepare_payload_after_descriptor_resolution() -> None:
    preview, confirmation, approved, execution, dispatch = _routine_config_chain()
    card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=approved,
        execution_result=execution,
        workflow_dispatch_result=dispatch,
        trace_id="trace_action_v270",
    )
    data = card.to_dict()
    payload = data["result_preview"]["routine_config_prepare_payload"]
    assert data["tool_name"] == "agent_routine_config_prepare"
    assert data["execution_status"] == "workflow_descriptor_resolved"
    assert "open_routine_setup" in data["available_client_actions"]
    assert "execute_controlled" not in data["available_client_actions"]
    assert payload["payload_contract_version"] == "v2_7_0"
    assert payload["routine_config_candidate"]["editable"] is True
    assert payload["routine_config_candidate"]["accompaniment_generate_call_enabled"] is False
    assert data["route_called"] is False
    assert data["engine_adapter_called"] is False
    assert data["midi_asset_created"] is False

    summary = build_routine_config_prepare_summary(action_card=card, source="test")
    assert summary["routine_config_prepare_contract_version"] == "v2_7_0"
    assert summary["has_routine_config_prepare_payload"] is True
    assert summary["routine_start_enabled"] is False
    assert summary["midi_asset_created"] is False


def test_terminal_routine_config_prepare_command_traces_payload(tmp_path: Path) -> None:
    from jammate_agent.core.trace import JsonTraceStore, TraceLogger

    session = TerminalChatSession(task_type="coach_qa", trace_logger=TraceLogger(JsonTraceStore(tmp_path)))
    session.preview_tool_call(
        "agent_routine_config_prepare",
        {"userInput": "练 30 分钟 Blue Bossa bossa", "durationMinutes": 30, "style": "bossa_nova", "tempo": 132},
    )
    session.confirm_pending_tool()
    session.execute_confirmed_tool_dry_run()
    session.dispatch_confirmed_tool_workflow_dry_run()
    response = session.routine_config_prepare()

    assert response["ok"] is True
    payload = response["routine_config_prepare_payload"]
    assert payload["payload_contract_version"] == "v2_7_0"
    assert payload["routine_config_candidate"]["style"] == "bossa_nova"
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False

    traces = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(tmp_path.glob("trace_*.json"))]
    matches = [item for item in traces if item["task_type"] == "terminal_routine_config_prepare"]
    assert len(matches) == 1
    step_names = [step["name"] for step in matches[0]["steps"]]
    assert "terminal_routine_config_prepare_payload_built" in step_names
    assert matches[0]["final_response_summary"]["routine_config_prepare_summary"]["has_routine_config_prepare_payload"] is True


def test_api_routine_config_prepare_route_returns_editable_payload() -> None:
    client = TestClient(app)
    spec = client.get("/agent/actions/routine-config/spec").json()["spec"]
    assert spec["version"] == "v2_7_0"
    assert spec["execution_status"]["routine_start_enabled"] is False

    response = client.post(
        "/agent/actions/routine-config/prepare",
        json={
            "taskType": "coach_qa",
            "toolName": "agent_routine_config_prepare",
            "arguments": {
                "userInput": "帮我建 30 分钟 Blue Bossa bossa routine",
                "durationMinutes": 30,
                "style": "bossa_nova",
                "tempo": 132,
                "tuneTitle": "Blue Bossa",
            },
            "userApproved": True,
            "traceId": "trace_api_v270",
        },
    ).json()
    assert response["ok"] is True
    payload = response["routine_config_prepare_payload"]
    candidate = payload["routine_config_candidate"]
    assert response["routine_config_prepare_contract_version"] == "v2_7_0"
    assert candidate["style"] == "bossa_nova"
    assert candidate["tempo"] == 132
    assert candidate["duration_minutes"] == 30
    assert candidate["accompaniment_generate_call_enabled"] is False
    assert payload["client_button_semantics"]["primary"]["does_call_accompaniment_generate"] is False
    assert response["route_called"] is False
    assert response["engine_adapter_called"] is False
    assert response["midi_asset_created"] is False
    assert response["playback_started"] is False


def test_trace_spec_exposes_routine_config_prepare_boundary() -> None:
    trace_spec = trace_api_contract()
    contract = trace_spec["routine_config_prepare_trace_contract"]
    assert contract["version"] == "v2_7_0"
    assert contract["routine_config_payload_enabled"] is True
    assert contract["routine_start_enabled"] is False
    assert contract["accompaniment_generate_call_enabled"] is False
    assert contract["midi_asset_creation_enabled"] is False

    client = TestClient(app)
    runtime_spec = client.get("/agent/context/runtime/spec").json()["spec"]
    boundary = runtime_spec["routine_config_prepare_boundary"]
    assert boundary["version"] == "v2_7_0"
    assert boundary["execution_status"]["routine_start_enabled"] is False


def test_routine_config_prepare_stays_agent_only_and_does_not_import_engine_or_network_clients() -> None:
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
        assert "jammate_engine" not in imported
        assert "requests" not in imported
        assert "httpx" not in imported
