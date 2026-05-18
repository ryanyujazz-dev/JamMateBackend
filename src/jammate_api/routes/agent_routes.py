from __future__ import annotations

from fastapi import APIRouter

from jammate_agent.adapters.jammate_engine_accompaniment_adapter import JamMateEngineAccompanimentAdapter
from jammate_agent.capabilities.charts.chart_resolver import ChartResolver
from jammate_agent.capabilities.practice.models import SessionReview
from jammate_agent.capabilities.practice.planner import PracticePlanner
from jammate_agent.capabilities.practice.review_engine import ReviewEngine
from jammate_agent.core.capability_registry import CapabilityRegistry
from jammate_agent.core.contract_codegen import (
    arkts_contract_files,
    frontend_fixture_pack,
    frontend_fixture_pack_files,
    harmonyos_api_smoke_pack,
    harmonyos_api_smoke_pack_files,
)
from jammate_agent.core.contracts import (
    agent_api_usage_examples,
    agent_capability_manifest,
    agent_runtime_skeleton_contract,
    arkts_contract_sketch,
    arkts_contract_source,
    context_profile_manifest,
    harmonyos_playback_contract,
    llm_context_runtime_contract,
    llm_provider_boundary_contract,
    response_case_policy_manifest,
    controlled_workflow_execution_contract,
    harmonyos_agent_action_contract,
    practice_plan_action_card_e2e_contract,
    tool_execution_confirmation_contract,
    tool_executor_boundary_contract,
    tool_invocation_preview_contract,
    tool_workflow_dispatcher_contract,
    tool_registry_contract,
)
from jammate_agent.core.jammate_agent import JamMateAgent
from jammate_agent.core.tool_invocation import (
    ToolInvocationProposal,
    build_controlled_workflow_execution_summary,
    build_harmonyos_agent_action_card,
    build_harmonyos_agent_action_summary,
    build_practice_plan_action_card_e2e_summary,
    build_confirmation_envelope,
    build_tool_executor_summary,
    build_tool_workflow_dispatcher_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    execute_tool_dry_run,
    preview_tool_invocation,
)
from jammate_agent.core.trace import TRACE_API_CONTRACT_VERSION, JsonTraceStore, TraceLogger, trace_api_contract
from jammate_api.schemas import AgentContextRuntimePreviewRequest, AgentMessageRequest, AgentPlanRequest, AgentPlaybackPrepareRequest, AgentToolInvocationPreviewRequest, SessionReviewRequest

router = APIRouter(prefix="/agent", tags=["jammate-agent"])

_AGENT: JamMateAgent | None = None


def build_agent() -> JamMateAgent:
    """Build a shared API-process JamMateAgent instance.

    The agent remains stateless for business data, but the shared TraceLogger
    makes trace lookup possible after a request returns its trace_id.
    """
    global _AGENT
    if _AGENT is None:
        registry = CapabilityRegistry(
            practice_planner=PracticePlanner(),
            chart_resolver=ChartResolver(),
            accompaniment_provider=JamMateEngineAccompanimentAdapter(),
            review_engine=ReviewEngine(),
        )
        trace_logger = TraceLogger(trace_store=JsonTraceStore("demos/agent_traces"))
        _AGENT = JamMateAgent(registry, trace_logger=trace_logger)
    return _AGENT


@router.get("/capabilities")
def get_agent_capabilities() -> dict:
    return {"ok": True, "manifest": agent_capability_manifest()}


@router.get("/runtime/skeleton")
def get_agent_runtime_skeleton_status() -> dict:
    spec = agent_runtime_skeleton_contract()
    return {
        "ok": True,
        "agent_runtime_skeleton_cleanup_version": spec["agent_runtime_skeleton_cleanup_version"],
        "runtime_skeleton": spec,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
    }


@router.get("/context/profiles")
def get_context_profiles() -> dict:
    return {"ok": True, "manifest": context_profile_manifest()}


@router.get("/contracts/arkts")
def get_arkts_contract_sketch() -> dict:
    return {"ok": True, "contract": arkts_contract_sketch()}


@router.get("/context/runtime/spec")
def get_context_runtime_spec() -> dict:
    return {"ok": True, "spec": llm_context_runtime_contract()}


@router.post("/context/runtime/preview")
def preview_context_runtime(request: AgentContextRuntimePreviewRequest) -> dict:
    result = build_agent().build_llm_context_runtime(
        request.user_input,
        task_type=request.task_type,
        request_id=request.request_id,
        client_context=request.client_context.model_dump(),
        available_minutes=request.available_minutes,
        duration_minutes=request.duration_minutes,
        instrument=request.instrument,
        local_unsynced_summary=request.local_unsynced_summary,
    )
    return result.__dict__


@router.get("/llm/provider/spec")
def get_llm_provider_boundary_spec() -> dict:
    return {"ok": True, "spec": llm_provider_boundary_contract()}


@router.get("/tools/registry")
def get_agent_tool_registry_spec() -> dict:
    return {"ok": True, "registry": tool_registry_contract()}


@router.get("/tools/invocation/spec")
def get_tool_invocation_preview_spec() -> dict:
    return {"ok": True, "spec": tool_invocation_preview_contract()}


@router.post("/tools/invocation/preview")
def preview_tool_invocation_request(request: AgentToolInvocationPreviewRequest) -> dict:
    agent = build_agent()
    context = agent.context_builder.build(
        request.task_type,
        request.user_input or f"Preview tool call: {request.tool_name}",
        request_id=request.request_id,
        client_context=request.client_context.model_dump(),
    )
    proposal = ToolInvocationProposal(
        tool_name=request.tool_name,
        arguments=request.arguments,
        task_type=context.task_type,
        request_id=request.request_id,
        user_input=request.user_input,
        client_context=request.client_context.model_dump(),
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    return {
        "ok": preview.ok,
        "preview": preview.to_dict(),
        "context_packet_summary": context.summary(),
    }


@router.get("/tools/confirmation/spec")
def get_tool_execution_confirmation_spec() -> dict:
    return {"ok": True, "spec": tool_execution_confirmation_contract()}


@router.post("/tools/confirmation/preview")
def preview_tool_execution_confirmation_request(request: AgentToolInvocationPreviewRequest) -> dict:
    agent = build_agent()
    context = agent.context_builder.build(
        request.task_type,
        request.user_input or f"Preview tool confirmation: {request.tool_name}",
        request_id=request.request_id,
        client_context=request.client_context.model_dump(),
    )
    proposal = ToolInvocationProposal(
        tool_name=request.tool_name,
        arguments=request.arguments,
        task_type=context.task_type,
        request_id=request.request_id,
        user_input=request.user_input,
        client_context=request.client_context.model_dump(),
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    return {
        "ok": confirmation.confirmable,
        "confirmation_contract_version": confirmation.confirmation_contract_version,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "context_packet_summary": context.summary(),
    }


@router.get("/tools/executor/spec")
def get_tool_executor_boundary_spec() -> dict:
    return {"ok": True, "spec": tool_executor_boundary_contract()}


@router.post("/tools/executor/dry-run")
def dry_run_tool_executor_request(request: dict) -> dict:
    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "coach_qa"
    tool_name = request.get("tool_name") or request.get("toolName") or ""
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    context = agent.context_builder.build(
        task_type,
        user_input or f"Dry-run tool executor: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    confirmation_result = confirm_tool_invocation(confirmation, user_approved=True) if user_approved else None
    execution_input = confirmation_result if confirmation_result else confirmation
    execution_result = execute_tool_dry_run(execution_input)
    summary = build_tool_executor_summary(execution_result=execution_result, source="agent_api")
    return {
        "ok": execution_result.ok,
        "tool_executor_boundary_version": execution_result.to_dict()["tool_executor_boundary_version"],
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "tool_executor_summary": summary,
        "context_packet_summary": context.summary(),
    }


@router.get("/tools/workflows/spec")
def get_tool_workflow_dispatcher_spec() -> dict:
    return {"ok": True, "spec": tool_workflow_dispatcher_contract()}


@router.post("/tools/workflows/dispatch-dry-run")
def dry_run_tool_workflow_dispatch_request(request: dict) -> dict:
    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "coach_qa"
    tool_name = request.get("tool_name") or request.get("toolName") or ""
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    context = agent.context_builder.build(
        task_type,
        user_input or f"Dry-run workflow dispatcher: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    confirmation_result = confirm_tool_invocation(confirmation, user_approved=True) if user_approved else None
    execution_input = confirmation_result if confirmation_result else confirmation
    execution_result = execute_tool_dry_run(execution_input)
    workflow_dispatch_result = dispatch_deterministic_workflow_dry_run(execution_result)
    summary = build_tool_workflow_dispatcher_summary(dispatch_result=workflow_dispatch_result, source="agent_api")
    return {
        "ok": workflow_dispatch_result.ok,
        "tool_workflow_dispatcher_version": workflow_dispatch_result.to_dict()["tool_workflow_dispatcher_version"],
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "tool_workflow_dispatcher_summary": summary,
        "context_packet_summary": context.summary(),
    }


@router.get("/tools/workflows/controlled-execution/spec")
def get_controlled_workflow_execution_spec() -> dict:
    return {"ok": True, "spec": controlled_workflow_execution_contract()}


@router.post("/tools/workflows/execute-controlled")
def execute_controlled_workflow_request(request: dict) -> dict:
    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "practice_plan_generation"
    tool_name = request.get("tool_name") or request.get("toolName") or ""
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    context = agent.context_builder.build(
        task_type,
        user_input or f"Controlled workflow execution: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    confirmation_result = confirm_tool_invocation(confirmation, user_approved=True) if user_approved else None
    execution_input = confirmation_result if confirmation_result else confirmation
    execution_result = execute_tool_dry_run(execution_input)
    workflow_dispatch_result = dispatch_deterministic_workflow_dry_run(execution_result)

    def _runner(tool_name_: str, args_: dict) -> dict:
        if tool_name_ != "agent_practice_plan":
            return {
                "ok": False,
                "error_code": "CONTROLLED_TOOL_NOT_SUPPORTED",
                "message": f"v2_6_5 controlled execution only supports agent_practice_plan, got {tool_name_}.",
            }
        planned_input = str(args_.get("user_input") or args_.get("userInput") or user_input or "Build a balanced JamMate practice plan.")
        raw_minutes = args_.get("available_minutes", args_.get("availableMinutes", args_.get("durationMinutes", request.get("availableMinutes", 45))))
        try:
            available_minutes = int(raw_minutes)
        except (TypeError, ValueError):
            available_minutes = 45
        instrument = str(args_.get("instrument") or request.get("instrument") or "piano")
        result = agent.generate_practice_plan(planned_input, available_minutes=available_minutes, instrument=instrument, request_id=request_id)
        return {
            "ok": result.ok,
            "intent_type": result.intent_type,
            "plan": result.plan,
            "explanation": result.explanation,
            "error_code": result.error_code,
            "message": result.message,
            "trace_id": result.trace_id,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }

    controlled_result = execute_controlled_workflow(workflow_dispatch_result, workflow_runner=_runner)
    summary = build_controlled_workflow_execution_summary(execution_result=controlled_result, source="agent_api")
    return {
        "ok": controlled_result.ok,
        "controlled_workflow_execution_version": controlled_result.to_dict()["controlled_workflow_execution_version"],
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "controlled_workflow_execution_result": controlled_result.to_dict(),
        "controlled_workflow_execution_summary": summary,
        "context_packet_summary": context.summary(),
    }


@router.get("/actions/spec")
def get_harmonyos_agent_action_spec() -> dict:
    return {"ok": True, "spec": harmonyos_agent_action_contract()}


@router.post("/actions/preview")
def preview_harmonyos_agent_action_request(request: dict) -> dict:
    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "practice_plan_generation"
    tool_name = request.get("tool_name") or request.get("toolName") or ""
    arguments = request.get("arguments") or {}
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    trace_id = request.get("trace_id") or request.get("traceId")
    context = agent.context_builder.build(
        task_type,
        user_input or f"HarmonyOS Agent action preview: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    action_card = build_harmonyos_agent_action_card(preview=preview, confirmation=confirmation, trace_id=trace_id)
    summary = build_harmonyos_agent_action_summary(action_card=action_card, source="agent_api")
    return {
        "ok": preview.ok,
        "harmonyos_agent_action_contract_version": action_card.action_contract_version,
        "action_card": action_card.to_dict(),
        "harmonyos_agent_action_summary": summary,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "context_packet_summary": context.summary(),
    }


@router.post("/actions/execute-controlled")
def execute_harmonyos_agent_action_controlled_request(request: dict) -> dict:
    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "practice_plan_generation"
    tool_name = request.get("tool_name") or request.get("toolName") or ""
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    trace_id = request.get("trace_id") or request.get("traceId")
    context = agent.context_builder.build(
        task_type,
        user_input or f"HarmonyOS Agent controlled action: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    confirmation_result = confirm_tool_invocation(confirmation, user_approved=True) if user_approved else None
    execution_input = confirmation_result if confirmation_result else confirmation
    execution_result = execute_tool_dry_run(execution_input)
    workflow_dispatch_result = dispatch_deterministic_workflow_dry_run(execution_result)

    def _runner(tool_name_: str, args_: dict) -> dict:
        if tool_name_ != "agent_practice_plan":
            return {
                "ok": False,
                "error_code": "CONTROLLED_TOOL_NOT_SUPPORTED",
                "message": f"v2_6_6 HarmonyOS action contract only supports controlled execution for agent_practice_plan, got {tool_name_}.",
            }
        planned_input = str(args_.get("user_input") or args_.get("userInput") or user_input or "Build a balanced JamMate practice plan.")
        raw_minutes = args_.get("available_minutes", args_.get("availableMinutes", args_.get("durationMinutes", request.get("availableMinutes", 45))))
        try:
            available_minutes = int(raw_minutes)
        except (TypeError, ValueError):
            available_minutes = 45
        instrument = str(args_.get("instrument") or request.get("instrument") or "piano")
        result = agent.generate_practice_plan(planned_input, available_minutes=available_minutes, instrument=instrument, request_id=request_id)
        return {
            "ok": result.ok,
            "intent_type": result.intent_type,
            "plan": result.plan,
            "explanation": result.explanation,
            "error_code": result.error_code,
            "message": result.message,
            "trace_id": result.trace_id,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }

    controlled_result = execute_controlled_workflow(workflow_dispatch_result, workflow_runner=_runner)
    action_card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=confirmation_result,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=controlled_result,
        trace_id=trace_id or (controlled_result.workflow_output or {}).get("trace_id"),
    )
    summary = build_harmonyos_agent_action_summary(action_card=action_card, source="agent_api")
    return {
        "ok": controlled_result.ok,
        "harmonyos_agent_action_contract_version": action_card.action_contract_version,
        "action_card": action_card.to_dict(),
        "harmonyos_agent_action_summary": summary,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "controlled_workflow_execution_result": controlled_result.to_dict(),
        "context_packet_summary": context.summary(),
    }


@router.get("/actions/practice-plan/spec")
def get_practice_plan_action_card_e2e_spec() -> dict:
    return {"ok": True, "spec": practice_plan_action_card_e2e_contract()}


@router.post("/actions/practice-plan/execute-controlled")
def execute_practice_plan_action_card_e2e_request(request: dict) -> dict:
    """Controlled agent_practice_plan execution with Routine payload shaping.

    This route is a narrow Routine-facing convenience surface. It follows the
    same preview -> confirmation -> executor dry-run -> descriptor -> controlled
    execution chain as /agent/actions/execute-controlled, then enriches the
    ActionCard result preview with routine_practice_plan_payload. It does not
    start playback, call /accompaniment/generate, call engine adapters, or create
    MIDI assets.
    """

    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "practice_plan_generation"
    tool_name = request.get("tool_name") or request.get("toolName") or "agent_practice_plan"
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    trace_id = request.get("trace_id") or request.get("traceId")
    context = agent.context_builder.build(
        task_type,
        user_input or f"Practice plan ActionCard E2E: {tool_name}",
        request_id=request_id,
        client_context=client_context,
    )
    proposal = ToolInvocationProposal(
        tool_name=tool_name,
        arguments=arguments,
        task_type=context.task_type,
        request_id=request_id,
        user_input=user_input,
        client_context=client_context,
    )
    preview = preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
    confirmation = build_confirmation_envelope(preview)
    confirmation_result = confirm_tool_invocation(confirmation, user_approved=True) if user_approved else None
    execution_input = confirmation_result if confirmation_result else confirmation
    execution_result = execute_tool_dry_run(execution_input)
    workflow_dispatch_result = dispatch_deterministic_workflow_dry_run(execution_result)

    def _runner(tool_name_: str, args_: dict) -> dict:
        if tool_name_ != "agent_practice_plan":
            return {
                "ok": False,
                "error_code": "PRACTICE_PLAN_ACTION_CARD_ONLY_SUPPORTS_AGENT_PRACTICE_PLAN",
                "message": f"v2_6_8 practice-plan ActionCard E2E only supports agent_practice_plan, got {tool_name_}.",
            }
        planned_input = str(args_.get("user_input") or args_.get("userInput") or user_input or "Build a balanced JamMate practice plan.")
        raw_minutes = args_.get("available_minutes", args_.get("availableMinutes", args_.get("durationMinutes", request.get("availableMinutes", 45))))
        try:
            available_minutes = int(raw_minutes)
        except (TypeError, ValueError):
            available_minutes = 45
        instrument = str(args_.get("instrument") or request.get("instrument") or "piano")
        result = agent.generate_practice_plan(planned_input, available_minutes=available_minutes, instrument=instrument, request_id=request_id)
        return {
            "ok": result.ok,
            "intent_type": result.intent_type,
            "plan": result.plan,
            "explanation": result.explanation,
            "error_code": result.error_code,
            "message": result.message,
            "trace_id": result.trace_id,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }

    controlled_result = execute_controlled_workflow(workflow_dispatch_result, workflow_runner=_runner)
    action_card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=confirmation_result,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=controlled_result,
        trace_id=trace_id or (controlled_result.workflow_output or {}).get("trace_id"),
    )
    action_summary = build_harmonyos_agent_action_summary(action_card=action_card, source="agent_api")
    practice_plan_summary = build_practice_plan_action_card_e2e_summary(action_card=action_card, source="agent_api")
    return {
        "ok": controlled_result.ok,
        "practice_plan_action_card_e2e_version": practice_plan_action_card_e2e_contract()["version"],
        "harmonyos_agent_action_contract_version": action_card.action_contract_version,
        "action_card": action_card.to_dict(),
        "harmonyos_agent_action_summary": action_summary,
        "practice_plan_action_card_e2e_summary": practice_plan_summary,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "controlled_workflow_execution_result": controlled_result.to_dict(),
        "context_packet_summary": context.summary(),
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
    }


@router.get("/contracts/arkts/source")
def get_arkts_contract_source() -> dict:
    return {"ok": True, "contract": arkts_contract_source()}


@router.get("/contracts/examples")
def get_agent_api_usage_examples() -> dict:
    return {"ok": True, "examples": agent_api_usage_examples()}


@router.get("/contracts/arkts/files")
def get_arkts_contract_files() -> dict:
    return {"ok": True, **arkts_contract_files()}


@router.get("/contracts/fixtures")
def get_frontend_fixture_pack() -> dict:
    return {"ok": True, **frontend_fixture_pack()}


@router.get("/contracts/frontend-pack")
def get_frontend_fixture_pack_files() -> dict:
    return {"ok": True, **frontend_fixture_pack_files()}




@router.get("/contracts/smoke-pack")
def get_harmonyos_api_smoke_pack() -> dict:
    return {"ok": True, **harmonyos_api_smoke_pack()}


@router.get("/contracts/smoke-pack/files")
def get_harmonyos_api_smoke_pack_files() -> dict:
    return {"ok": True, **harmonyos_api_smoke_pack_files()}


@router.get("/contracts/case-policy")
def get_response_case_policy() -> dict:
    return {"ok": True, "policy": response_case_policy_manifest()}


@router.get("/playback/spec")
def get_playback_integration_spec() -> dict:
    return {"ok": True, "spec": harmonyos_playback_contract()}


@router.get("/traces/spec")
def get_agent_trace_api_spec() -> dict:
    return {"ok": True, "spec": trace_api_contract()}


@router.get("/traces")
def list_agent_traces(limit: int = 20) -> dict:
    return {"ok": True, "trace_contract_version": TRACE_API_CONTRACT_VERSION, "traces": build_agent().list_recent_traces(limit=limit)}


@router.get("/traces/{trace_id}")
def get_agent_trace(trace_id: str) -> dict:
    trace = build_agent().get_trace(trace_id)
    if not trace:
        return {
            "ok": False,
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "error_code": "TRACE_NOT_FOUND",
            "message": f"Trace not found: {trace_id}",
            "trace": None,
        }
    return {"ok": True, "trace_contract_version": TRACE_API_CONTRACT_VERSION, "trace": trace.to_detail_dict()}


@router.post("/message")
def agent_message(request: AgentMessageRequest) -> dict:
    result = build_agent().handle_message(
        request.user_input,
        request_id=request.request_id,
        available_minutes=request.client_context.available_minutes,
    )
    return result.__dict__


@router.post("/practice/plan")
def generate_practice_plan(request: AgentPlanRequest) -> dict:
    result = build_agent().generate_practice_plan(
        request.user_input,
        available_minutes=request.available_minutes,
        instrument=request.instrument,
    )
    return result.__dict__


@router.post("/playback/prepare")
def prepare_playback(request: AgentPlaybackPrepareRequest) -> dict:
    result = build_agent().prepare_playback(request.user_input, duration_minutes=request.duration_minutes)
    return result.__dict__


@router.post("/session/review")
def submit_session_review(request: SessionReviewRequest) -> dict:
    review = SessionReview(**request.model_dump())
    recommendation = build_agent().capabilities.review_engine.recommend_next_step(review)
    return {"ok": True, "recommendation": recommendation.to_dict()}
