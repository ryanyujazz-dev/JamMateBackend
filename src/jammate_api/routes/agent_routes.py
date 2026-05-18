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
    playback_prepare_guarded_design_contract,
    routine_config_prepare_contract,
    practice_plan_to_routine_candidate_bridge_contract,
    routine_history_context_intake_contract,
    active_practice_plan_context_intake_contract,
    practice_context_assembly_policy_contract,
    today_practice_context_e2e_contract,
    today_practice_guidance_prompt_contract,
    user_capability_map_and_intent_taxonomy_contract,
    today_practice_guidance_output_validation_contract,
    today_practice_guidance_provider_boundary_e2e_contract,
    today_practice_guidance_action_card_contract,
    today_practice_guidance_terminal_chat_e2e_contract,
    context_and_guidance_skeleton_cleanup_contract,
    user_practice_profile_context_intake_contract,
    practice_context_storage_boundary_contract,
    today_practice_guidance_profile_aware_e2e_contract,
    practice_plan_persistence_candidate_contract,
    context_engineering_skeleton_contract,
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
    build_playback_prepare_guarded_design_summary,
    build_routine_config_prepare_summary,
    build_practice_plan_to_routine_candidate_bridge_summary,
    build_routine_history_context_intake_payload,
    build_routine_history_context_intake_summary,
    build_active_practice_plan_context_intake_payload,
    build_active_practice_plan_context_intake_summary,
    build_user_practice_profile_context_intake_payload,
    build_user_practice_profile_context_intake_summary,
    build_practice_context_storage_boundary_payload,
    build_practice_context_storage_boundary_summary,
    build_today_practice_guidance_profile_aware_e2e_payload,
    build_today_practice_guidance_profile_aware_e2e_summary,
    build_practice_plan_persistence_candidate_payload,
    build_practice_plan_persistence_candidate_summary,
    build_practice_context_assembly_policy_payload,
    build_practice_context_assembly_policy_summary,
    build_today_practice_context_e2e_payload,
    build_today_practice_context_e2e_summary,
    build_today_practice_guidance_prompt_contract_payload,
    build_today_practice_guidance_prompt_contract_summary,
    build_user_capability_map_and_intent_taxonomy_payload,
    build_user_capability_map_and_intent_taxonomy_summary,
    build_today_practice_guidance_output_validation_payload,
    build_today_practice_guidance_output_validation_summary,
    build_today_practice_guidance_provider_boundary_e2e_payload,
    build_today_practice_guidance_provider_boundary_e2e_summary,
    build_today_practice_guidance_action_card_payload,
    build_today_practice_guidance_action_card_summary,
    build_today_practice_guidance_terminal_chat_e2e_payload,
    build_today_practice_guidance_terminal_chat_e2e_summary,
    build_context_and_guidance_skeleton_cleanup_payload,
    build_context_and_guidance_skeleton_cleanup_summary,
    build_confirmation_envelope,
    build_tool_executor_summary,
    build_tool_workflow_dispatcher_summary,
    confirm_tool_invocation,
    dispatch_deterministic_workflow_dry_run,
    execute_controlled_workflow,
    build_routine_config_prepare_action_payload,
    build_practice_plan_to_routine_candidate_bridge_payload,
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


@router.get("/capabilities/user-intents/spec")
def get_user_capability_map_and_intent_taxonomy_spec() -> dict:
    return {"ok": True, "spec": user_capability_map_and_intent_taxonomy_contract()}


@router.post("/capabilities/user-intents/preview")
def preview_user_capability_map_and_intent_taxonomy_request(request: dict) -> dict:
    """Return the user-facing LLM capability map and intent taxonomy.

    This route is a planning/contract surface only. It does not call the LLM,
    execute tools, start Routine, call /accompaniment/generate, call engine
    adapters, or create MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_user_capability_map_and_intent_taxonomy_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_user_capability_map_and_intent_taxonomy",
    )
    summary = build_user_capability_map_and_intent_taxonomy_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "user_capability_map_and_intent_taxonomy_version": user_capability_map_and_intent_taxonomy_contract()["version"],
        "user_capability_map_payload": payload.to_dict(),
        "user_capability_map_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/routine-history/spec")
def get_routine_history_context_intake_spec() -> dict:
    return {"ok": True, "spec": routine_history_context_intake_contract()}


@router.post("/context/routine-history/intake")
def intake_routine_history_context_request(request: dict) -> dict:
    """Normalize HarmonyOS Routine history summaries for future Agent ContextPackets.

    This route is context intake only. It does not create a post-session
    recommendation card, does not call /accompaniment/generate, does not call
    engine adapters, and does not create MIDI assets or playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_routine_history_context_intake_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_routine_history_context_intake",
    )
    summary = build_routine_history_context_intake_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "routine_history_context_intake_version": routine_history_context_intake_contract()["version"],
        "routine_history_context_payload": payload.to_dict(),
        "routine_history_context_intake_summary": summary,
        "recommendation_card_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/active-practice-plan/spec")
def get_active_practice_plan_context_intake_spec() -> dict:
    return {"ok": True, "spec": active_practice_plan_context_intake_contract()}


@router.post("/context/active-practice-plan/intake")
def intake_active_practice_plan_context_request(request: dict) -> dict:
    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_active_practice_plan_context_intake_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_active_practice_plan_context_intake",
    )
    summary = build_active_practice_plan_context_intake_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "active_practice_plan_context_intake_version": active_practice_plan_context_intake_contract()["version"],
        "active_practice_plan_context_payload": payload.to_dict(),
        "active_practice_plan_context_intake_summary": summary,
        "recommendation_created": False,
        "llm_called": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/user-practice-profile/spec")
def get_user_practice_profile_context_intake_spec() -> dict:
    return {"ok": True, "spec": user_practice_profile_context_intake_contract()}


@router.post("/context/user-practice-profile/intake")
def intake_user_practice_profile_context_request(request: dict) -> dict:
    """Normalize durable user practice preferences for future Agent ContextPackets.

    This route is context intake only. It does not call the LLM, execute tools,
    write storage, start Routine, call /accompaniment/generate, call engine
    adapters, or create MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_user_practice_profile_context_intake_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_user_practice_profile_context_intake",
    )
    summary = build_user_practice_profile_context_intake_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "user_practice_profile_context_intake_version": user_practice_profile_context_intake_contract()["version"],
        "user_practice_profile_context_payload": payload.to_dict(),
        "user_practice_profile_context_intake_summary": summary,
        "recommendation_created": False,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/storage-boundary/spec")
def get_practice_context_storage_boundary_spec() -> dict:
    return {"ok": True, "spec": practice_context_storage_boundary_contract()}


@router.post("/context/storage-boundary/preview")
def preview_practice_context_storage_boundary_request(request: dict) -> dict:
    """Preview practice-context storage ownership without writing storage.

    This route classifies local/backend/request/trace context boundaries only.
    It does not call the LLM, execute tools, write storage, start Routine, call
    /accompaniment/generate, call engine adapters, or create MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_practice_context_storage_boundary_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_practice_context_storage_boundary",
    )
    summary = build_practice_context_storage_boundary_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "practice_context_storage_boundary_version": practice_context_storage_boundary_contract()["version"],
        "practice_context_storage_boundary_payload": payload.to_dict(),
        "practice_context_storage_boundary_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/practice-assembly/spec")
def get_practice_context_assembly_policy_spec() -> dict:
    return {"ok": True, "spec": practice_context_assembly_policy_contract()}


@router.post("/context/practice-assembly/build")
def build_practice_context_assembly_request(request: dict) -> dict:
    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_practice_context_assembly_policy_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_practice_context_assembly",
    )
    summary = build_practice_context_assembly_policy_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "practice_context_assembly_policy_version": practice_context_assembly_policy_contract()["version"],
        "practice_context_assembly_payload": payload.to_dict(),
        "practice_context_assembly_summary": summary,
        "recommendation_created": False,
        "llm_called": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice/spec")
def get_today_practice_context_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_context_e2e_contract()}


@router.post("/context/today-practice/preview")
def preview_today_practice_context_request(request: dict) -> dict:
    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_context_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_context_e2e",
    )
    summary = build_today_practice_context_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_context_e2e_version": today_practice_context_e2e_contract()["version"],
        "today_practice_context_payload": payload.to_dict(),
        "today_practice_context_summary": summary,
        "recommendation_created": False,
        "llm_called": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/spec")
def get_today_practice_guidance_prompt_contract_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_prompt_contract()}


@router.post("/context/today-practice-guidance/prompt-preview")
def preview_today_practice_guidance_prompt_contract_request(request: dict) -> dict:
    """Build the prompt/output contract for future LLM today-practice guidance.

    This route does not call the LLM and does not create a final guidance answer.
    It only exposes the provider-boundary-ready prompt, output schema, and guard
    policy for the next user-initiated "今天该练什么" turn.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_prompt_contract_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_prompt_contract",
    )
    summary = build_today_practice_guidance_prompt_contract_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_prompt_contract_version": today_practice_guidance_prompt_contract()["version"],
        "today_practice_guidance_prompt_payload": payload.to_dict(),
        "today_practice_guidance_prompt_summary": summary,
        "llm_called": False,
        "guidance_response_created": False,
        "recommendation_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/output-validation/spec")
def get_today_practice_guidance_output_validation_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_output_validation_contract()}


@router.post("/context/today-practice-guidance/output-validation/validate")
def validate_today_practice_guidance_output_request(request: dict) -> dict:
    """Validate a future LLM TodayPracticeGuidanceOutput without executing anything.

    The validator accepts only guidance/candidate data for client display. It
    blocks attempts to start Routine, call /accompaniment/generate, invoke
    engine adapters, create MIDI assets, or bypass user confirmation.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_output_validation_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_output_validation",
    )
    summary = build_today_practice_guidance_output_validation_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_output_validation_version": today_practice_guidance_output_validation_contract()["version"],
        "today_practice_guidance_output_validation_payload": payload.to_dict(),
        "today_practice_guidance_output_validation_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/provider-boundary/spec")
def get_today_practice_guidance_provider_boundary_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_provider_boundary_e2e_contract()}


@router.post("/context/today-practice-guidance/provider-boundary/e2e-preview")
def preview_today_practice_guidance_provider_boundary_e2e_request(request: dict) -> dict:
    """Run prompt contract + provider-result preview + output validation.

    This route accepts either context inputs plus a supplied providerResult / llmOutput
    fixture, or an explicitly gated provider call in a configured environment. It
    never starts Routine, calls /accompaniment/generate, invokes engine adapters,
    or creates MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_provider_boundary_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_provider_boundary_e2e",
    )
    summary = build_today_practice_guidance_provider_boundary_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_provider_boundary_e2e_version": today_practice_guidance_provider_boundary_e2e_contract()["version"],
        "today_practice_guidance_provider_boundary_e2e_payload": payload.to_dict(),
        "today_practice_guidance_provider_boundary_e2e_summary": summary,
        "llm_called": payload.llm_called,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/action-card/spec")
def get_today_practice_guidance_action_card_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_action_card_contract()}


@router.post("/context/today-practice-guidance/action-card/preview")
def preview_today_practice_guidance_action_card_request(request: dict) -> dict:
    """Build a display-only Routine ActionCard from validated today guidance.

    This route may use a supplied providerResult / llmOutput or an explicitly
    gated provider boundary call. It only returns a display card and Routine
    candidates; it never starts Routine, calls /accompaniment/generate, invokes
    engine adapters, or creates MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_action_card_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_action_card",
    )
    summary = build_today_practice_guidance_action_card_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_action_card_version": today_practice_guidance_action_card_contract()["version"],
        "today_practice_guidance_action_card_payload": payload.to_dict(),
        "today_practice_guidance_action_card_summary": summary,
        "llm_called": payload.llm_called,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/terminal-chat/spec")
def get_today_practice_guidance_terminal_chat_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_terminal_chat_e2e_contract()}


@router.post("/context/today-practice-guidance/terminal-chat/e2e-preview")
def preview_today_practice_guidance_terminal_chat_e2e_request(request: dict) -> dict:
    """Preview ordinary terminal-chat today guidance routing without side effects.

    This route mirrors the terminal chat behavior for user turns such as
    "今天该练什么？". It may use a supplied providerResult / llmOutput fixture or
    an explicitly gated provider boundary call, but it still returns only a
    display ActionCard and candidate data.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_terminal_chat_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_terminal_chat_e2e",
    )
    summary = build_today_practice_guidance_terminal_chat_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_terminal_chat_e2e_version": today_practice_guidance_terminal_chat_e2e_contract()["version"],
        "today_practice_guidance_terminal_chat_e2e_payload": payload.to_dict(),
        "today_practice_guidance_terminal_chat_e2e_summary": summary,
        "llm_called": payload.llm_called,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }




@router.get("/practice-plan/persistence-candidate/spec")
def get_practice_plan_persistence_candidate_spec() -> dict:
    return {"ok": True, "spec": practice_plan_persistence_candidate_contract()}


@router.post("/practice-plan/persistence-candidate/preview")
def preview_practice_plan_persistence_candidate_request(request: dict) -> dict:
    """Preview a save/update PracticePlan candidate without writing storage.

    This route is a persistence-candidate contract only. It does not call the
    LLM, execute tools, write backend storage, write local device state, start
    Routine, call /accompaniment/generate, call engine adapters, or create MIDI
    assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_practice_plan_persistence_candidate_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_practice_plan_persistence_candidate",
    )
    summary = build_practice_plan_persistence_candidate_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "practice_plan_persistence_candidate_contract_version": practice_plan_persistence_candidate_contract()["version"],
        "practice_plan_persistence_candidate_payload": payload.to_dict(),
        "practice_plan_persistence_candidate_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/profile-aware/spec")
def get_today_practice_guidance_profile_aware_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_profile_aware_e2e_contract()}


@router.post("/context/today-practice-guidance/profile-aware/e2e-preview")
def preview_today_practice_guidance_profile_aware_e2e_request(request: dict) -> dict:
    """Preview profile-aware today-practice guidance without side effects.

    This route injects UserPracticeProfileContext into the existing guarded
    today-practice guidance chain. It may use a supplied providerResult fixture
    or an explicitly gated provider boundary call, but it still returns only a
    display ActionCard and candidate data.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_profile_aware_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_profile_aware_e2e",
    )
    summary = build_today_practice_guidance_profile_aware_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_profile_aware_e2e_version": today_practice_guidance_profile_aware_e2e_contract()["version"],
        "today_practice_guidance_profile_aware_e2e_payload": payload.to_dict(),
        "today_practice_guidance_profile_aware_e2e_summary": summary,
        "llm_called": payload.llm_called,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/engineering-skeleton")
def get_context_engineering_skeleton_spec() -> dict:
    return {"ok": True, "context_engineering_skeleton": context_engineering_skeleton_contract()}


@router.get("/context/guidance-skeleton-cleanup")
def get_context_and_guidance_skeleton_cleanup_spec() -> dict:
    payload = build_context_and_guidance_skeleton_cleanup_payload(source="agent_api_context_guidance_cleanup")
    summary = build_context_and_guidance_skeleton_cleanup_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_and_guidance_skeleton_cleanup_version": context_and_guidance_skeleton_cleanup_contract()["version"],
        "context_and_guidance_skeleton_cleanup_contract": context_and_guidance_skeleton_cleanup_contract(),
        "context_and_guidance_skeleton_cleanup_payload": payload.to_dict(),
        "context_and_guidance_skeleton_cleanup_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


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


@router.get("/actions/playback-prepare/spec")
def get_playback_prepare_guarded_design_spec() -> dict:
    return {"ok": True, "spec": playback_prepare_guarded_design_contract()}


@router.post("/actions/playback-prepare/guarded-preview")
def preview_playback_prepare_guarded_design_request(request: dict) -> dict:
    """Guarded Routine-facing design payload for agent_playback_prepare.

    This route runs only preview -> confirmation -> executor dry-run -> workflow
    descriptor resolution. It never calls /accompaniment/generate, never calls
    engine adapters, never creates MIDI assets, and never starts playback.
    """

    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "immediate_practice_playback"
    tool_name = request.get("tool_name") or request.get("toolName") or "agent_playback_prepare"
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    trace_id = request.get("trace_id") or request.get("traceId")
    context = agent.context_builder.build(
        task_type,
        user_input or f"Playback prepare guarded design: {tool_name}",
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
    action_card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=confirmation_result,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=None,
        trace_id=trace_id,
    )
    action_summary = build_harmonyos_agent_action_summary(action_card=action_card, source="agent_api")
    guarded_summary = build_playback_prepare_guarded_design_summary(action_card=action_card, source="agent_api")
    return {
        "ok": bool(workflow_dispatch_result.ok and tool_name == "agent_playback_prepare"),
        "playback_prepare_guarded_design_version": playback_prepare_guarded_design_contract()["version"],
        "harmonyos_agent_action_contract_version": action_card.action_contract_version,
        "action_card": action_card.to_dict(),
        "harmonyos_agent_action_summary": action_summary,
        "playback_prepare_guarded_design_summary": guarded_summary,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "context_packet_summary": context.summary(),
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }


@router.get("/actions/practice-plan/routine-candidate/spec")
def get_practice_plan_to_routine_candidate_bridge_spec() -> dict:
    return {"ok": True, "spec": practice_plan_to_routine_candidate_bridge_contract()}


@router.post("/actions/practice-plan/routine-candidate/prepare")
def prepare_practice_plan_to_routine_candidate_bridge_request(request: dict) -> dict:
    """UI-flow-agnostic Routine candidate from a practice-plan block.

    The route accepts an existing routine_practice_plan_payload/action_card/raw
    practice plan/block and returns candidate data only. HarmonyOS decides
    whether to render a setup page, bottom sheet, current-form fill, queue item,
    template, or any future client flow. No playback or accompaniment generation
    is started here.
    """

    arguments = request.get("arguments") or request.get("payload") or {}
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    if "block_id" in request and "block_id" not in arguments:
        arguments["block_id"] = request.get("block_id")
    if "blockId" in request and "blockId" not in arguments:
        arguments["blockId"] = request.get("blockId")
    if "block_index" in request and "block_index" not in arguments:
        arguments["block_index"] = request.get("block_index")
    if "blockIndex" in request and "blockIndex" not in arguments:
        arguments["blockIndex"] = request.get("blockIndex")
    payload = build_practice_plan_to_routine_candidate_bridge_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_practice_plan_to_routine_candidate_bridge",
    )
    summary = build_practice_plan_to_routine_candidate_bridge_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "practice_plan_to_routine_candidate_bridge_version": practice_plan_to_routine_candidate_bridge_contract()["version"],
        "routine_candidate_bridge_payload": payload.to_dict(),
        "practice_plan_to_routine_candidate_bridge_summary": summary,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/actions/routine-config/spec")
def get_routine_config_prepare_spec() -> dict:
    return {"ok": True, "spec": routine_config_prepare_contract()}


@router.post("/actions/routine-config/prepare")
def prepare_routine_config_action_request(request: dict) -> dict:
    """Routine-facing editable RoutineConfig candidate.

    This route runs preview -> confirmation -> executor dry-run -> workflow
    descriptor resolution for agent_routine_config_prepare, then shapes an
    editable RoutineConfig draft. It never calls /accompaniment/generate, never
    calls engine adapters, never creates MIDI assets, and never starts playback.
    """

    agent = build_agent()
    task_type = request.get("task_type") or request.get("taskType") or "coach_qa"
    tool_name = request.get("tool_name") or request.get("toolName") or "agent_routine_config_prepare"
    arguments = request.get("arguments") or {}
    user_approved = bool(request.get("user_approved", request.get("userApproved", False)))
    request_id = request.get("request_id") or request.get("requestId")
    user_input = request.get("user_input") or request.get("userInput") or arguments.get("user_input") or arguments.get("userInput")
    client_context = request.get("client_context") or request.get("clientContext") or {}
    trace_id = request.get("trace_id") or request.get("traceId")
    context = agent.context_builder.build(
        task_type,
        user_input or f"RoutineConfig prepare: {tool_name}",
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
    action_card = build_harmonyos_agent_action_card(
        preview=preview,
        confirmation=confirmation,
        confirmation_result=confirmation_result,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=None,
        trace_id=trace_id,
    )
    payload = build_routine_config_prepare_action_payload(
        arguments,
        tool_name=tool_name,
        trace_id=trace_id,
        source="agent_api_routine_config_prepare",
    )
    action_summary = build_harmonyos_agent_action_summary(action_card=action_card, source="agent_api")
    routine_config_summary = build_routine_config_prepare_summary(action_card=action_card, payload=payload, source="agent_api")
    return {
        "ok": bool(workflow_dispatch_result.ok and tool_name == "agent_routine_config_prepare"),
        "routine_config_prepare_contract_version": routine_config_prepare_contract()["version"],
        "harmonyos_agent_action_contract_version": action_card.action_contract_version,
        "action_card": action_card.to_dict(),
        "routine_config_prepare_payload": payload.to_dict(),
        "harmonyos_agent_action_summary": action_summary,
        "routine_config_prepare_summary": routine_config_summary,
        "preview": preview.to_dict(),
        "confirmation": confirmation.to_dict(),
        "confirmation_result": confirmation_result.to_dict() if confirmation_result else None,
        "execution_result": execution_result.to_dict(),
        "workflow_dispatch_result": workflow_dispatch_result.to_dict(),
        "context_packet_summary": context.summary(),
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
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
