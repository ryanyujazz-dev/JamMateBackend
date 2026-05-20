from __future__ import annotations

import json
import os
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
    routine_history_persistence_candidate_contract,
    context_persistence_confirmation_boundary_contract,
    context_persistence_executor_noop_contract,
    context_persistence_storage_adapter_design_contract,
    context_persistence_sqlite_dev_preview_contract,
    context_persistence_dev_sqlite_write_gate_contract,
    context_persistence_dev_sqlite_fixture_write_dry_run_contract,
    context_persistence_dev_sqlite_fixture_store_contract,
    context_persistence_dev_fixture_readback_replay_contract,
    context_persistence_profile_plan_history_snapshot_context_intake_contract,
    today_practice_guidance_persisted_context_recovery_e2e_contract,
    today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract,
    today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract,
    today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract,
    today_practice_guidance_terminal_product_smoke_polish_contract,
    agent_v2_8_phase_cleanup_regression_handoff_contract,
    context_persistence_sqlite_backend_store_contract,
    context_persistence_sqlite_backend_readback_context_recovery_contract,
    context_persistence_sqlite_backend_today_guidance_recovery_e2e_contract,
    context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract,
    context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract,
    context_persistence_sqlite_backend_api_memory_debug_pack_contract,
    context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract,
    context_persistence_sqlite_backend_api_error_shape_matrix_contract,
    context_persistence_sqlite_backend_harmonyos_error_fixture_pack_contract,
    context_persistence_sqlite_backend_handoff_completion_pack_contract,
    context_persistence_backend_db_path_policy_and_migration_guard_contract,
    context_persistence_backend_schema_metadata_table_preview_contract,
    agent_usable_today_practice_guidance_mvp_contract,
    agent_routine_completion_record_to_backend_context_write_mvp_contract,
    agent_routine_completion_to_today_guidance_product_smoke_contract,
    agent_harmonyos_today_guidance_api_contract_alignment_contract,
    context_engineering_skeleton_contract,
    tool_execution_confirmation_contract,
    tool_executor_boundary_contract,
    tool_invocation_preview_contract,
    tool_workflow_dispatcher_contract,
    tool_registry_contract,
)
from jammate_agent.core.jammate_agent import JamMateAgent
from jammate_agent.core.llm_provider import _normalize_messages_for_chat_completions, build_llm_provider_from_env
from jammate_agent.core.practice_coach_session import (
    build_practice_coach_context_builder_preview,
    build_practice_coach_conversation_state_store_execute,
    build_practice_coach_plan_proposal_contract_execute,
    build_practice_coach_profile_sheet_intent_contract_execute,
    build_practice_coach_routine_card_contract_execute,
    build_practice_coach_unified_message_action_router_execute,
    PRACTICE_COACH_REAL_LLM_PROVIDER_GUARDED_SMOKE_VERSION,
    PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_VERSION,
    PRACTICE_COACH_SQLITE_PATH_GUARD_MACOS_TEMPDIR_HOTFIX_VERSION,
    PRACTICE_COACH_PLAN_REVISION_INTENT_ROUTING_HOTFIX_VERSION,
    PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION,
    PRACTICE_COACH_ROUTINE_CARD_COMPLETION_LOOP_SMOKE_VERSION,
    PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION,
)
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
    build_routine_history_persistence_candidate_payload,
    build_routine_history_persistence_candidate_summary,
    build_context_persistence_confirmation_boundary_payload,
    build_context_persistence_confirmation_boundary_summary,
    build_context_persistence_executor_noop_payload,
    build_context_persistence_executor_noop_summary,
    build_context_persistence_storage_adapter_design_payload,
    build_context_persistence_storage_adapter_design_summary,
    build_context_persistence_sqlite_dev_preview_payload,
    build_context_persistence_sqlite_dev_preview_summary,
    build_context_persistence_dev_sqlite_write_gate_payload,
    build_context_persistence_dev_sqlite_write_gate_summary,
    build_context_persistence_dev_sqlite_fixture_write_dry_run_payload,
    build_context_persistence_dev_sqlite_fixture_write_dry_run_summary,
    build_context_persistence_dev_sqlite_fixture_store_payload,
    build_context_persistence_dev_sqlite_fixture_store_summary,
    build_context_persistence_dev_fixture_readback_replay_payload,
    build_context_persistence_dev_fixture_readback_replay_summary,
    build_context_persistence_profile_plan_history_snapshot_context_intake_payload,
    build_context_persistence_profile_plan_history_snapshot_context_intake_summary,
    build_today_practice_guidance_persisted_context_recovery_e2e_payload,
    build_today_practice_guidance_persisted_context_recovery_e2e_summary,
    build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload,
    build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary,
    build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload,
    build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary,
    build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload,
    build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary,
    build_today_practice_guidance_terminal_product_smoke_polish_payload,
    build_today_practice_guidance_terminal_product_smoke_polish_summary,
    build_agent_v2_8_phase_cleanup_regression_handoff_payload,
    build_agent_v2_8_phase_cleanup_regression_handoff_summary,
    build_context_persistence_sqlite_backend_store_payload,
    build_context_persistence_sqlite_backend_store_summary,
    build_context_persistence_sqlite_backend_readback_context_recovery_payload,
    build_context_persistence_sqlite_backend_readback_context_recovery_summary,
    build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload,
    build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary,
    build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload,
    build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary,
    build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload,
    build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary,
    build_context_persistence_sqlite_backend_api_memory_debug_pack_payload,
    build_context_persistence_sqlite_backend_api_memory_debug_pack_summary,
    build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload,
    build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary,
    build_context_persistence_sqlite_backend_api_error_shape_matrix_payload,
    build_context_persistence_sqlite_backend_api_error_shape_matrix_summary,
    build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload,
    build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary,
    build_context_persistence_sqlite_backend_handoff_completion_pack_payload,
    build_context_persistence_sqlite_backend_handoff_completion_pack_summary,
    build_context_persistence_backend_db_path_policy_and_migration_guard_payload,
    build_context_persistence_backend_db_path_policy_and_migration_guard_summary,
    build_context_persistence_backend_schema_metadata_table_preview_payload,
    build_context_persistence_backend_schema_metadata_table_preview_summary,
    build_agent_usable_today_practice_guidance_mvp_payload,
    build_agent_usable_today_practice_guidance_mvp_summary,
    build_agent_routine_completion_record_to_backend_context_write_mvp_payload,
    build_agent_routine_completion_record_to_backend_context_write_mvp_summary,
    build_agent_routine_completion_to_today_guidance_product_smoke_payload,
    build_agent_routine_completion_to_today_guidance_product_smoke_summary,
    build_agent_harmonyos_today_guidance_api_contract_alignment_payload,
    build_agent_harmonyos_today_guidance_api_contract_alignment_summary,
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


@router.get("/context/today-practice-guidance/persisted-context-recovery/spec")
def get_today_practice_guidance_persisted_context_recovery_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_persisted_context_recovery_e2e_contract()}


@router.post("/context/today-practice-guidance/persisted-context-recovery/e2e-preview")
def preview_today_practice_guidance_persisted_context_recovery_e2e_request(request: dict) -> dict:
    """Recover persisted snapshot context into display-only today-practice guidance.

    This route is a read/preview bridge only. It can consume a dev fixture
    read-back snapshot or embedded snapshot context intake payload, then passes
    recovered profile/plan/history context to the profile-aware guidance chain.
    It does not write storage, start Routine, call /accompaniment/generate, call
    engine adapters, create MIDI assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_persisted_context_recovery_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_persisted_context_recovery_e2e",
    )
    summary = build_today_practice_guidance_persisted_context_recovery_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_persisted_context_recovery_e2e_version": today_practice_guidance_persisted_context_recovery_e2e_contract()["version"],
        "today_practice_guidance_persisted_context_recovery_e2e_payload": payload.to_dict(),
        "today_practice_guidance_persisted_context_recovery_e2e_summary": summary,
        "llm_called": payload.llm_called,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "replay_execution_committed": False,
        "future_executor_implemented": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec")
def get_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract()}


@router.post("/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview")
def preview_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_request(request: dict) -> dict:
    """Build a HarmonyOS debug fixture preview from terminal persisted-context memory.

    This route returns a frontend-debug fixture and an Agent request preview only.
    It does not write storage, call LLM, execute tools, start Routine, call
    /accompaniment/generate, call engine adapters, create MIDI assets, or start
    playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture",
    )
    summary = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_version": today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract()["version"],
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload": payload.to_dict(),
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary": summary,
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
        "post_session_recommendation_card_created": False,
    }



@router.get("/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec")
def get_context_persistence_sqlite_backend_terminal_memory_autoload_preview_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract()}


@router.post("/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview")
def preview_context_persistence_sqlite_backend_terminal_memory_autoload_preview_request(request: dict) -> dict:
    """Preview read-only SQLite backend context as terminal session memory."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_terminal_memory_autoload_preview",
    )
    summary = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview_version": context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract()["version"],
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "terminal_session_memory_write_previewed": summary.get("terminal_session_memory_write_previewed", False),
        "terminal_session_memory_loaded_by_api": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec")
def get_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract()}


@router.post("/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview")
def preview_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_request(request: dict) -> dict:
    """Run compact SQLite store → memory autoload → guidance smoke preview."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke",
    )
    summary = build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_version": context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract()["version"],
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary": summary,
        "llm_called": summary.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "storage_written": summary.get("storage_written", False),
        "backend_database_written": summary.get("backend_database_written", False),
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": summary.get("sqlite_tables_created", False),
        "sqlite_rows_written": summary.get("sqlite_rows_written", False),
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "terminal_session_memory_write_previewed": summary.get("terminal_session_memory_write_previewed", False),
        "terminal_session_memory_loaded_by_api": False,
        "guidance_preview_ready": summary.get("guidance_preview_ready", False),
        "routine_candidate_count": summary.get("routine_candidate_count", 0),
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-sqlite-backend-api-memory-debug-pack/spec")
def get_context_persistence_sqlite_backend_api_memory_debug_pack_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_api_memory_debug_pack_contract()}


@router.post("/context/persistence-sqlite-backend-api-memory-debug-pack/preview")
def preview_context_persistence_sqlite_backend_api_memory_debug_pack_request(request: dict) -> dict:
    """Build an API debug pack for SQLite persistence/readback/guidance routes."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_api_memory_debug_pack_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_api_memory_debug_pack",
    )
    summary = build_context_persistence_sqlite_backend_api_memory_debug_pack_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_api_memory_debug_pack_version": context_persistence_sqlite_backend_api_memory_debug_pack_contract()["version"],
        "context_persistence_sqlite_backend_api_memory_debug_pack_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_api_memory_debug_pack_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "terminal_session_memory_loaded_by_api": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }

@router.get("/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec")
def get_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract()}


@router.post("/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview")
def preview_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_request(request: dict) -> dict:
    """Build a HarmonyOS API fixture pack for SQLite persistence routes.

    This route prepares copyable endpoint/body/response-shape examples only. It
    does not call those routes, open SQLite, write/read storage, mutate API
    memory, write frontend fixtures, call LLM, execute tools, start Routine,
    call /accompaniment/generate, call engine adapters, create MIDI assets, or
    start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_harmonyos_api_fixture_pack",
    )
    summary = build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack_version": context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract()["version"],
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-sqlite-backend-api-error-shape-matrix/spec")
def get_context_persistence_sqlite_backend_api_error_shape_matrix_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_api_error_shape_matrix_contract()}


@router.post("/context/persistence-sqlite-backend-api-error-shape-matrix/preview")
def preview_context_persistence_sqlite_backend_api_error_shape_matrix_request(request: dict) -> dict:
    """Preview SQLite backend persistence API blocked/error response shapes.

    This route only returns a stable matrix for frontend/API debugging. It does
    not execute packaged routes, open SQLite, read/write storage, mutate memory,
    call LLM, execute tools, start Routine, call the engine, create MIDI, or
    start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_api_error_shape_matrix_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_api_error_shape_matrix",
    )
    summary = build_context_persistence_sqlite_backend_api_error_shape_matrix_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_api_error_shape_matrix_version": context_persistence_sqlite_backend_api_error_shape_matrix_contract()["version"],
        "context_persistence_sqlite_backend_api_error_shape_matrix_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_api_error_shape_matrix_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec")
def get_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_harmonyos_error_fixture_pack_contract()}


@router.post("/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview")
def preview_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_request(request: dict) -> dict:
    """Build HarmonyOS bad-request/error fixtures for SQLite persistence routes.

    This route returns copyable client fixtures only. It does not execute those
    requests, open/read/write SQLite, mutate API memory, write frontend fixture
    files, call LLM/tools/Engine, start Routine, create MIDI, or play audio.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_harmonyos_error_fixture_pack",
    )
    summary = build_context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_harmonyos_error_fixture_pack_version": context_persistence_sqlite_backend_harmonyos_error_fixture_pack_contract()["version"],
        "context_persistence_sqlite_backend_harmonyos_error_fixture_pack_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_harmonyos_error_fixture_pack_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-sqlite-backend-today-guidance-recovery-e2e/spec")
def get_context_persistence_sqlite_backend_today_guidance_recovery_e2e_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_today_guidance_recovery_e2e_contract()}


@router.post("/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview")
def preview_context_persistence_sqlite_backend_today_guidance_recovery_e2e_request(request: dict) -> dict:
    """Read SQLite backend context and preview today-practice guidance without side effects."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_today_guidance_recovery_e2e",
    )
    summary = build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e_version": context_persistence_sqlite_backend_today_guidance_recovery_e2e_contract()["version"],
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary": summary,
        "llm_called": summary.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-snapshot-context-intake/spec")
def get_context_persistence_profile_plan_history_snapshot_context_intake_spec() -> dict:
    return {"ok": True, "spec": context_persistence_profile_plan_history_snapshot_context_intake_contract()}


@router.post("/context/persistence-snapshot-context-intake/preview")
def preview_context_persistence_profile_plan_history_snapshot_context_intake_request(request: dict) -> dict:
    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_profile_plan_history_snapshot_context_intake",
    )
    summary = build_context_persistence_profile_plan_history_snapshot_context_intake_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_profile_plan_history_snapshot_context_intake_version": context_persistence_profile_plan_history_snapshot_context_intake_contract()["version"],
        "context_persistence_profile_plan_history_snapshot_context_intake_payload": payload.to_dict(),
        "context_persistence_profile_plan_history_snapshot_context_intake_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "replay_execution_committed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec")
def get_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract()}


@router.post("/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview")
def preview_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_request(request: dict) -> dict:
    """Roundtrip a HarmonyOS debug fixture into persisted-context guidance preview.

    This route verifies the frontend debug fixture request body can be fed back
    into the Agent persisted-context recovery E2E. It does not write storage,
    call LLM, execute tools, start Routine, call /accompaniment/generate, call
    engine adapters, create MIDI assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e",
    )
    summary = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_version": today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract()["version"],
        "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload": payload.to_dict(),
        "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary": summary,
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
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec")
def get_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract()}


@router.post("/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview")
def preview_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_request(request: dict) -> dict:
    """Build a copyable HarmonyOS API request pack for debug fixture guidance tests.

    This route prepares endpoint/body/response-shape examples only. It does not
    call those routes, write storage, call LLM, execute tools, start Routine,
    call /accompaniment/generate, call engine adapters, create MIDI assets, or
    start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_harmonyos_debug_fixture_api_request_pack",
    )
    summary = build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_harmonyos_debug_fixture_api_request_pack_version": today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract()["version"],
        "today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload": payload.to_dict(),
        "today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary": summary,
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
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/today-practice-guidance/v2-8-phase-handoff/spec")
def get_agent_v2_8_phase_cleanup_regression_handoff_spec() -> dict:
    return {"ok": True, "spec": agent_v2_8_phase_cleanup_regression_handoff_contract()}


@router.post("/context/today-practice-guidance/v2-8-phase-handoff/preview")
def preview_agent_v2_8_phase_cleanup_regression_handoff_request(request: dict) -> dict:
    """Build a side-effect-free v2.8 phase handoff report."""

    payload = build_agent_v2_8_phase_cleanup_regression_handoff_payload(
        request,
        source="agent_route_v2_8_phase_handoff_preview",
    )
    summary = build_agent_v2_8_phase_cleanup_regression_handoff_summary(
        payload=payload,
        source="agent_route_v2_8_phase_handoff_preview",
    )
    return {
        "ok": True,
        "agent_v2_8_phase_cleanup_regression_handoff_version": payload.payload_contract_version,
        "agent_v2_8_phase_cleanup_regression_handoff_payload": payload.to_dict(),
        "agent_v2_8_phase_cleanup_regression_handoff_summary": summary,
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
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/today-practice-guidance/terminal-product-smoke/spec")
def get_today_practice_guidance_terminal_product_smoke_polish_spec() -> dict:
    return {"ok": True, "spec": today_practice_guidance_terminal_product_smoke_polish_contract()}


@router.post("/context/today-practice-guidance/terminal-product-smoke/preview")
def preview_today_practice_guidance_terminal_product_smoke_polish_request(request: dict) -> dict:
    """Build a side-effect-free terminal product smoke pack for guidance testing."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_today_practice_guidance_terminal_product_smoke_polish_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_today_practice_guidance_terminal_product_smoke_polish",
    )
    summary = build_today_practice_guidance_terminal_product_smoke_polish_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "today_practice_guidance_terminal_product_smoke_polish_version": today_practice_guidance_terminal_product_smoke_polish_contract()["version"],
        "today_practice_guidance_terminal_product_smoke_polish_payload": payload.to_dict(),
        "today_practice_guidance_terminal_product_smoke_polish_summary": summary,
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
        "post_session_recommendation_card_created": False,
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


@router.get("/context/persistence-sqlite-backend-handoff-completion-pack/spec")
def get_context_persistence_sqlite_backend_handoff_completion_pack_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_handoff_completion_pack_contract()}


@router.post("/context/persistence-sqlite-backend-handoff-completion-pack/preview")
def preview_context_persistence_sqlite_backend_handoff_completion_pack_request(request: dict) -> dict:
    """Build the v2_9 SQLite backend persistence handoff completion pack.

    This is a preview-only report. It does not execute stored sample requests,
    open/read/write SQLite, mutate API memory, write frontend fixture files,
    call LLM/tools/Engine, start Routine, create MIDI, or play audio.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_handoff_completion_pack_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_handoff_completion_pack",
    )
    summary = build_context_persistence_sqlite_backend_handoff_completion_pack_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_handoff_completion_pack_version": context_persistence_sqlite_backend_handoff_completion_pack_contract()["version"],
        "context_persistence_sqlite_backend_handoff_completion_pack_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_handoff_completion_pack_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-backend-db-path-policy-migration-guard/spec")
def get_context_persistence_backend_db_path_policy_and_migration_guard_spec() -> dict:
    return {"ok": True, "spec": context_persistence_backend_db_path_policy_and_migration_guard_contract()}


@router.post("/context/persistence-backend-db-path-policy-migration-guard/preview")
def preview_context_persistence_backend_db_path_policy_and_migration_guard_request(request: dict) -> dict:
    """Preview DB path, schema, and migration guard without opening SQLite.

    This route only validates proposed backend persistence configuration. It
    never opens/reads/writes SQLite, creates tables, runs migrations, mutates
    API memory, writes frontend fixtures or HarmonyOS local state, calls LLMs
    or tools, starts Routine/playback, calls Engine, or creates MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_backend_db_path_policy_and_migration_guard_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_backend_db_path_policy_and_migration_guard",
    )
    summary = build_context_persistence_backend_db_path_policy_and_migration_guard_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_backend_db_path_policy_and_migration_guard_version": context_persistence_backend_db_path_policy_and_migration_guard_contract()["version"],
        "context_persistence_backend_db_path_policy_and_migration_guard_payload": payload.to_dict(),
        "context_persistence_backend_db_path_policy_and_migration_guard_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "migration_execution_performed": False,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/persistence-backend-schema-metadata-table-preview/spec")
def get_context_persistence_backend_schema_metadata_table_preview_spec() -> dict:
    return {"ok": True, "spec": context_persistence_backend_schema_metadata_table_preview_contract()}


@router.post("/context/persistence-backend-schema-metadata-table-preview/preview")
def preview_context_persistence_backend_schema_metadata_table_preview_request(request: dict) -> dict:
    """Preview future schema metadata/registry tables without SQLite side effects."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_backend_schema_metadata_table_preview_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_backend_schema_metadata_table_preview",
    )
    summary = build_context_persistence_backend_schema_metadata_table_preview_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_backend_schema_metadata_table_preview_version": context_persistence_backend_schema_metadata_table_preview_contract()["version"],
        "context_persistence_backend_schema_metadata_table_preview_payload": payload.to_dict(),
        "context_persistence_backend_schema_metadata_table_preview_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "migration_execution_performed": False,
        "schema_creation_performed": False,
        "fixture_files_written": False,
        "frontend_fixtures_directory_written": False,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
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

@router.get("/routine-history/persistence-candidate/spec")
def get_routine_history_persistence_candidate_spec() -> dict:
    return {"ok": True, "spec": routine_history_persistence_candidate_contract()}


@router.post("/routine-history/persistence-candidate/preview")
def preview_routine_history_persistence_candidate_request(request: dict) -> dict:
    """Preview a RoutineHistory summary save/upload candidate without writing storage.

    This route is a persistence-candidate contract only. It does not call the
    LLM, execute tools, write backend storage, write local device state, create
    a post-session recommendation card, start Routine, call /accompaniment/generate,
    call engine adapters, or create MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_routine_history_persistence_candidate_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_routine_history_persistence_candidate",
    )
    summary = build_routine_history_persistence_candidate_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "routine_history_persistence_candidate_contract_version": routine_history_persistence_candidate_contract()["version"],
        "routine_history_persistence_candidate_payload": payload.to_dict(),
        "routine_history_persistence_candidate_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }



@router.get("/context/persistence-confirmation/spec")
def get_context_persistence_confirmation_boundary_spec() -> dict:
    return {"ok": True, "spec": context_persistence_confirmation_boundary_contract()}


@router.post("/context/persistence-confirmation/preview")
def preview_context_persistence_confirmation_boundary_request(request: dict) -> dict:
    """Preview a unified confirmation record for context persistence candidates.

    This route can wrap PracticePlan and RoutineHistory persistence candidates in
    a confirmation boundary. It records user decision intent only; it does not
    call the LLM, execute tools, write backend storage, write local device state,
    create post-session recommendation cards, start Routine, call
    /accompaniment/generate, call engine adapters, or create MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_confirmation_boundary_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_confirmation_boundary",
    )
    summary = build_context_persistence_confirmation_boundary_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_confirmation_boundary_version": context_persistence_confirmation_boundary_contract()["version"],
        "context_persistence_confirmation_boundary_payload": payload.to_dict(),
        "context_persistence_confirmation_boundary_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-executor-noop/spec")
def get_context_persistence_executor_noop_spec() -> dict:
    return {"ok": True, "spec": context_persistence_executor_noop_contract()}


@router.post("/context/persistence-executor-noop/preview")
def preview_context_persistence_executor_noop_request(request: dict) -> dict:
    """Preview the future persistence executor without writing storage.

    This route validates the confirmed-candidate executor boundary and returns a
    no-op execution report. It does not call the LLM, execute tools, write
    backend storage, write local device state, create post-session
    recommendation cards, start Routine, call /accompaniment/generate, call
    engine adapters, create MIDI assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_executor_noop_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_executor_noop",
    )
    summary = build_context_persistence_executor_noop_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_executor_noop_version": context_persistence_executor_noop_contract()["version"],
        "context_persistence_executor_noop_payload": payload.to_dict(),
        "context_persistence_executor_noop_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-storage-adapter/spec")
def get_context_persistence_storage_adapter_design_spec() -> dict:
    return {"ok": True, "spec": context_persistence_storage_adapter_design_contract()}


@router.post("/context/persistence-storage-adapter/design-preview")
def preview_context_persistence_storage_adapter_design_request(request: dict) -> dict:
    """Return the future real storage-adapter design preview only.

    This route intentionally does not create a database connection, write
    backend storage, write HarmonyOS local state, call an LLM, execute tools,
    start Routine, call /accompaniment/generate, dispatch engine adapters,
    create MIDI assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_storage_adapter_design_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_storage_adapter_design",
    )
    summary = build_context_persistence_storage_adapter_design_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_storage_adapter_design_version": context_persistence_storage_adapter_design_contract()["version"],
        "context_persistence_storage_adapter_design_payload": payload.to_dict(),
        "context_persistence_storage_adapter_design_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-sqlite-dev-preview/spec")
def get_context_persistence_sqlite_dev_preview_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_dev_preview_contract()}


@router.post("/context/persistence-sqlite-dev-preview/preview")
def preview_context_persistence_sqlite_dev_preview_request(request: dict) -> dict:
    """Return a dev-only SQLite/fixture adapter preview without writing.

    This route exposes schema DDL, idempotency, trace-link, and read-snapshot
    preview shapes. It intentionally does not create a SQLite connection, apply
    migrations, write rows, write HarmonyOS local state, call an LLM, execute
    tools, start Routine, call /accompaniment/generate, dispatch engine
    adapters, create MIDI assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_dev_preview_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_dev_preview",
    )
    summary = build_context_persistence_sqlite_dev_preview_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_dev_preview_version": context_persistence_sqlite_dev_preview_contract()["version"],
        "context_persistence_sqlite_dev_preview_payload": payload.to_dict(),
        "context_persistence_sqlite_dev_preview_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-dev-sqlite-write-gate/spec")
def get_context_persistence_dev_sqlite_write_gate_spec() -> dict:
    return {"ok": True, "spec": context_persistence_dev_sqlite_write_gate_contract()}


@router.post("/context/persistence-dev-sqlite-write-gate/preview")
def preview_context_persistence_dev_sqlite_write_gate_request(request: dict) -> dict:
    """Return an explicit dev-only SQLite write-gate preview without writing.

    This route validates the future write gate/config path shape only. It does
    not create a SQLite connection, apply migrations, write rows, write
    HarmonyOS local state, call an LLM, execute tools, start Routine, call
    /accompaniment/generate, dispatch engine adapters, create MIDI assets, or
    start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_dev_sqlite_write_gate_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_dev_sqlite_write_gate",
    )
    summary = build_context_persistence_dev_sqlite_write_gate_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_dev_sqlite_write_gate_version": context_persistence_dev_sqlite_write_gate_contract()["version"],
        "context_persistence_dev_sqlite_write_gate_payload": payload.to_dict(),
        "context_persistence_dev_sqlite_write_gate_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_write_enabled": False,
        "future_executor_implemented": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-dev-sqlite-fixture-write-dry-run/spec")
def get_context_persistence_dev_sqlite_fixture_write_dry_run_spec() -> dict:
    return {"ok": True, "spec": context_persistence_dev_sqlite_fixture_write_dry_run_contract()}


@router.post("/context/persistence-dev-sqlite-fixture-write-dry-run/preview")
def preview_context_persistence_dev_sqlite_fixture_write_dry_run_request(request: dict) -> dict:
    """Return a dev SQLite fixture writer dry-run without storage side effects.

    This route simulates transaction, idempotency, trace-link, and read-back
    shapes only. It does not create a SQLite connection, apply migrations,
    write rows, write HarmonyOS local state, call an LLM, execute tools, start
    Routine, call /accompaniment/generate, dispatch engine adapters, create MIDI
    assets, or start playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_dev_sqlite_fixture_write_dry_run_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_dev_sqlite_fixture_write_dry_run",
    )
    summary = build_context_persistence_dev_sqlite_fixture_write_dry_run_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_dev_sqlite_fixture_write_dry_run_version": context_persistence_dev_sqlite_fixture_write_dry_run_contract()["version"],
        "context_persistence_dev_sqlite_fixture_write_dry_run_payload": payload.to_dict(),
        "context_persistence_dev_sqlite_fixture_write_dry_run_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "future_executor_implemented": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }



@router.get("/context/persistence-dev-sqlite-fixture-store/spec")
def get_context_persistence_dev_sqlite_fixture_store_spec() -> dict:
    return {"ok": True, "spec": context_persistence_dev_sqlite_fixture_store_contract()}


@router.post("/context/persistence-dev-sqlite-fixture-store/preview")
def preview_context_persistence_dev_sqlite_fixture_store_request(request: dict) -> dict:
    """Return an explicit dev-only fixture store payload.

    The route may append one redacted JSONL record only when the caller passes
    fixtureStoreWriteEnabled=true, executeFixtureStore=true, an approved
    confirmation, a dev/test environment, a safe fixture path, a trace id, and
    redaction/storage-boundary gates. It never opens SQLite, writes backend
    database rows, writes HarmonyOS local state, calls an LLM, executes tools,
    starts Routine, calls /accompaniment/generate, dispatches engine adapters,
    creates MIDI assets, or starts playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_dev_sqlite_fixture_store_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_dev_sqlite_fixture_store",
    )
    summary = build_context_persistence_dev_sqlite_fixture_store_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_dev_sqlite_fixture_store_version": context_persistence_dev_sqlite_fixture_store_contract()["version"],
        "context_persistence_dev_sqlite_fixture_store_payload": payload.to_dict(),
        "context_persistence_dev_sqlite_fixture_store_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_store_write_executed": summary.get("fixture_store_write_executed", False),
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


@router.get("/context/persistence-sqlite-backend-store/spec")
def get_context_persistence_sqlite_backend_store_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_store_contract()}


@router.post("/context/persistence-sqlite-backend-store/execute")
def execute_context_persistence_sqlite_backend_store_request(request: dict) -> dict:
    """Execute explicit backend SQLite context persistence after all gates pass.

    This route may create/write a local backend SQLite database only when the
    request has backendPersistenceEnabled=true, executeBackendPersistence=true,
    user approval, a safe dev/test SQLite path, trace id, idempotency, redaction,
    and storage-boundary checks. It never calls LLMs/tools/Engine, starts
    Routine/playback, creates MIDI, or writes HarmonyOS local state.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_store_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_store",
    )
    summary = build_context_persistence_sqlite_backend_store_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_store_version": context_persistence_sqlite_backend_store_contract()["version"],
        "context_persistence_sqlite_backend_store_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_store_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": summary.get("storage_written", False),
        "backend_database_written": summary.get("backend_database_written", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": summary.get("sqlite_tables_created", False),
        "sqlite_rows_written": summary.get("sqlite_rows_written", False),
        "sqlite_row_count_written": summary.get("sqlite_row_count_written", 0),
        "durable_backend_write_executed": summary.get("durable_backend_write_executed", False),
        "transaction_committed": summary.get("transaction_committed", False),
        "idempotent_replay": summary.get("idempotent_replay", False),
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }

@router.get("/context/persistence-sqlite-backend-readback-context-recovery/spec")
def get_context_persistence_sqlite_backend_readback_context_recovery_spec() -> dict:
    return {"ok": True, "spec": context_persistence_sqlite_backend_readback_context_recovery_contract()}


@router.post("/context/persistence-sqlite-backend-readback-context-recovery/preview")
def preview_context_persistence_sqlite_backend_readback_context_recovery_request(request: dict) -> dict:
    """Read persisted SQLite backend context into a recovery packet without writes.

    This route opens an existing dev/test SQLite backend store in read-only mode
    after explicit readback gates pass, then builds the same snapshot-context
    section used by today-practice guidance recovery. It never writes storage,
    calls LLMs/tools/Engine, starts Routine/playback, or creates MIDI assets.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_sqlite_backend_readback_context_recovery_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_sqlite_backend_readback_context_recovery",
    )
    summary = build_context_persistence_sqlite_backend_readback_context_recovery_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_sqlite_backend_readback_context_recovery_version": context_persistence_sqlite_backend_readback_context_recovery_contract()["version"],
        "context_persistence_sqlite_backend_readback_context_recovery_payload": payload.to_dict(),
        "context_persistence_sqlite_backend_readback_context_recovery_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }



@router.get("/context/persistence-dev-fixture-readback-replay/spec")
def get_context_persistence_dev_fixture_readback_replay_spec() -> dict:
    return {"ok": True, "spec": context_persistence_dev_fixture_readback_replay_contract()}


@router.post("/context/persistence-dev-fixture-readback-replay/preview")
def preview_context_persistence_dev_fixture_readback_replay_request(request: dict) -> dict:
    """Return a read-only dev fixture read-back/replay preview.

    The route may read a safe development JSONL fixture and build a context
    snapshot/replay preview. It never writes files, opens SQLite, writes backend
    database rows, writes HarmonyOS local state, calls an LLM, executes tools,
    starts Routine, calls /accompaniment/generate, dispatches engine adapters,
    creates MIDI assets, or starts playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_context_persistence_dev_fixture_readback_replay_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_context_persistence_dev_fixture_readback_replay",
    )
    summary = build_context_persistence_dev_fixture_readback_replay_summary(payload=payload, source="agent_api")
    return {
        "ok": True,
        "context_persistence_dev_fixture_readback_replay_version": context_persistence_dev_fixture_readback_replay_contract()["version"],
        "context_persistence_dev_fixture_readback_replay_payload": payload.to_dict(),
        "context_persistence_dev_fixture_readback_replay_summary": summary,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "replay_execution_committed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }

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





def _harmonyos_nested_get(source: dict, path: tuple[str, ...]) -> dict:
    current: object = source
    for key in path:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _extract_harmonyos_today_guidance_prompt_payload(agent_payload: dict, *, context_source: str | None = None) -> tuple[dict, str]:
    """Return the provider-prompt payload used by the HarmonyOS guidance chain.

    The ordinary product response intentionally hides this deep nesting. The
    trace endpoint surfaces it explicitly so product and frontend debugging can
    answer: "what would be sent to the LLM if provider calls were enabled?"
    """

    if not isinstance(agent_payload, dict):
        return {}, "none"
    sqlite_prompt = _harmonyos_nested_get(
        agent_payload,
        (
            "sqlite_today_guidance_payload",
            "today_guidance_recovery_payload",
            "guidance_payload",
            "action_card_payload",
            "provider_boundary_e2e_payload",
            "prompt_payload",
        ),
    )
    ordinary_prompt = _harmonyos_nested_get(
        agent_payload,
        (
            "ordinary_guidance_payload",
            "action_card_payload",
            "provider_boundary_e2e_payload",
            "prompt_payload",
        ),
    )
    if context_source == "sqlite_backend" and sqlite_prompt:
        return sqlite_prompt, "sqlite_backend"
    if ordinary_prompt:
        return ordinary_prompt, "plain_fallback"
    if sqlite_prompt:
        return sqlite_prompt, "sqlite_readback_attempt"
    return {}, "none"


def _harmonyos_provider_envelope_messages_from_prompt(prompt_payload: dict) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    raw_messages = prompt_payload.get("prompt_messages") if isinstance(prompt_payload, dict) else None
    if not isinstance(raw_messages, list):
        return messages
    for raw_message in raw_messages:
        if not isinstance(raw_message, dict):
            continue
        role = str(raw_message.get("role") or "user")
        if role not in {"system", "developer", "user", "assistant", "context"}:
            role = "developer"
        content = raw_message.get("content")
        if content is None and "content_json" in raw_message:
            content = json.dumps(raw_message.get("content_json"), ensure_ascii=False)
        messages.append({"role": role, "content": str(content or "")})
    return messages


def _build_harmonyos_llm_request_trace(agent_payload: dict, summary: dict, product_arguments: dict) -> dict:
    prompt_payload, prompt_source = _extract_harmonyos_today_guidance_prompt_payload(agent_payload, context_source=str(summary.get("context_source") or ""))
    provider_status = {}
    try:
        provider = build_llm_provider_from_env()
        provider_status = provider.status() if hasattr(provider, "status") else {}
    except Exception as exc:  # pragma: no cover - defensive only.
        provider_status = {"provider_status_error": str(exc)}

    provider_envelope_messages = _harmonyos_provider_envelope_messages_from_prompt(prompt_payload)
    max_prompt_chars = int(provider_status.get("max_prompt_chars") or 12000)
    chat_messages = _normalize_messages_for_chat_completions(tuple(provider_envelope_messages), max_prompt_chars)
    request_body_preview = {
        "model": provider_status.get("model"),
        "messages": chat_messages,
        "temperature": provider_status.get("temperature"),
        "max_tokens": provider_status.get("max_output_tokens"),
    }
    assembled_context = prompt_payload.get("assembled_practice_context") if isinstance(prompt_payload.get("assembled_practice_context"), dict) else {}
    output_schema = prompt_payload.get("output_schema") if isinstance(prompt_payload.get("output_schema"), dict) else {}
    prompt_policy = prompt_payload.get("prompt_policy") if isinstance(prompt_payload.get("prompt_policy"), dict) else {}
    return {
        "traceVersion": "v2_10_10",
        "routePurpose": "debug_preview_only_no_llm_call",
        "userMessage": product_arguments.get("userInput"),
        "contextSource": summary.get("context_source"),
        "promptSource": prompt_source,
        "providerStatus": provider_status,
        "internalPromptMessages": prompt_payload.get("prompt_messages") if isinstance(prompt_payload.get("prompt_messages"), list) else [],
        "providerEnvelopeMessages": provider_envelope_messages,
        "chatCompletionsMessagesIfCalled": chat_messages,
        "chatCompletionsRequestBodyPreview": request_body_preview,
        "assembledPracticeContext": assembled_context,
        "outputSchema": output_schema,
        "promptPolicy": prompt_policy,
        "contextSummary": {
            "sqliteReadbackAttempted": bool(summary.get("sqlite_readback_attempted", False)),
            "backendDatabaseRead": bool(summary.get("backend_database_read", False)),
            "sqliteRowsRead": int(summary.get("sqlite_rows_read") or 0),
            "routineCandidateCount": int(summary.get("routine_candidate_count") or 0),
            "guidanceActionCardIsValid": bool(summary.get("guidance_action_card_is_valid", False)),
        },
        "roleNormalization": {
            "internalRolesMayInclude": ["system", "developer", "user", "context"],
            "networkPayloadUsesCompatibleRoles": True,
            "developerAndContextMergedIntoSystem": True,
            "allowedNetworkRoles": ["system", "user", "assistant"],
        },
        "safety": {
            "llmCalledByThisTraceRoute": False,
            "networkCallExecuted": False,
            "toolExecutionEnabled": False,
            "routineStartEnabled": False,
            "accompanimentGenerateCallEnabled": False,
            "engineAdapterCalled": False,
            "midiAssetCreated": False,
            "playbackStarted": False,
            "rawApiKeyIncluded": False,
        },
    }


def _extract_harmonyos_action_card_payload(agent_payload: dict) -> dict:
    if not isinstance(agent_payload, dict):
        return {}
    sqlite_payload = agent_payload.get("sqlite_today_guidance_payload")
    if isinstance(sqlite_payload, dict):
        nested = sqlite_payload.get("today_guidance_recovery_payload")
        if isinstance(nested, dict):
            guidance_payload = nested.get("guidance_payload")
            if isinstance(guidance_payload, dict):
                action_card = guidance_payload.get("action_card_payload")
                if isinstance(action_card, dict):
                    return action_card
    ordinary_payload = agent_payload.get("ordinary_guidance_payload")
    if isinstance(ordinary_payload, dict):
        action_card = ordinary_payload.get("action_card_payload")
        if isinstance(action_card, dict):
            return action_card
    return {}




_HARMONYOS_AGENT_CONTEXT_DB_PATH_ENV_VAR = "JAMMATE_AGENT_CONTEXT_DB_PATH"
_HARMONYOS_AGENT_DEFAULT_CONTEXT_DB_PATH = "/tmp/jammate_agent_harmonyos_context.sqlite3"


def _harmonyos_first_present(source: dict, *keys: str):
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return None


def _harmonyos_backend_context_db_path(arguments: dict) -> str:
    candidate = _harmonyos_first_present(
        arguments,
        "sqliteDbPath",
        "sqlite_db_path",
        "dbPath",
        "db_path",
        "contextDbPath",
        "agentContextDbPath",
    )
    if candidate is None:
        candidate = os.environ.get(_HARMONYOS_AGENT_CONTEXT_DB_PATH_ENV_VAR)
    text = str(candidate or "").strip()
    return text or _HARMONYOS_AGENT_DEFAULT_CONTEXT_DB_PATH


def _harmonyos_product_arguments(arguments: dict, *, route_kind: str) -> dict:
    """Normalize HarmonyOS black-box product payloads before internal builders.

    The real HarmonyOS client treats the Agent as a black-box HTTP API and does
    not send internal sqliteDbPath or persistence gate fields. Those are backend
    concerns: the backend uses JAMMATE_AGENT_CONTEXT_DB_PATH when configured, or
    a safe local-dev default path for Mac/device smoke.
    """

    normalized = dict(arguments or {})
    normalized.setdefault("environment", "local_dev")
    normalized.setdefault("sqliteDbPath", _harmonyos_backend_context_db_path(normalized))

    if route_kind == "today_guidance":
        if _harmonyos_first_present(normalized, "userInput", "user_input", "text") is None:
            user_message = _harmonyos_first_present(normalized, "userMessage", "user_message", "message")
            if user_message is not None:
                normalized["userInput"] = user_message
            else:
                normalized["userInput"] = "今天该练什么？"
    elif route_kind == "routine_completion":
        # The product route itself is the user's/client's explicit submission of
        # a finished practice record. Do not require HarmonyOS to know internal
        # write-gate fields; inject them only when the client did not specify a
        # contrary value for debugging.
        normalized.setdefault("clientConfirmedRecordWrite", True)
        normalized.setdefault("backendPersistenceEnabled", True)
        normalized.setdefault("executeBackendPersistence", True)
        normalized.setdefault("userDecision", "approved")
        normalized.setdefault("confirmationStatus", "user_approved_future_executor_required")

    return normalized

def _harmonyos_safety(*, writes_backend_sqlite: bool = False, llm_called: bool = False, network_call_executed: bool = False) -> dict:
    return {
        "displayOnly": not writes_backend_sqlite,
        "backendSQLiteWriteMayOccur": writes_backend_sqlite,
        "llmCalled": llm_called,
        "networkCallExecuted": network_call_executed,
        "writesHarmonyOSLocalState": False,
        "startsRoutine": False,
        "callsAccompanimentGenerate": False,
        "callsEngineAdapter": False,
        "createsMidiAsset": False,
        "startsPlayback": False,
        "createsPostSessionRecommendationCard": False,
        "clientDecidesPresentation": True,
        "frontendFlowAssumption": False,
    }



def _compact_preview(value: object, *, limit: int = 96) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _short_digest(value: object) -> str:
    try:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError:
        payload = str(value)
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _list_keys(value: object) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key in value.keys())


def _practice_coach_device_feedback_trace_pack(
    *,
    product_arguments: dict,
    execution: dict,
    agent_action: dict,
    response_type: str,
    content: str,
    persisted: bool,
    code: str,
) -> dict:
    """Compact, frontend-copyable trace pack for HarmonyOS device feedback.

    This pack intentionally summarizes the Practice Coach decision path without
    asking the client to understand Python internals. It is safe to copy into a
    frontend/backend issue report; verbose LLM payload previews remain available
    in data/debug separately for developer inspection.
    """

    state_before = execution.get("stateBefore") if isinstance(execution.get("stateBefore"), dict) else {}
    state_after = execution.get("stateAfter") if isinstance(execution.get("stateAfter"), dict) else {}
    plan = execution.get("planProposal") if isinstance(execution.get("planProposal"), dict) else None
    card = execution.get("routineCardPayload") if isinstance(execution.get("routineCardPayload"), dict) else None
    sheet = execution.get("sheetIntent") if isinstance(execution.get("sheetIntent"), dict) else None
    safety = execution.get("safety") if isinstance(execution.get("safety"), dict) else {}
    io = execution.get("io") if isinstance(execution.get("io"), dict) else {}
    read_io = io.get("read") if isinstance(io.get("read"), dict) else {}
    write_io = io.get("write") if isinstance(io.get("write"), dict) else {}
    validation = execution.get("llmActionDecisionValidation") if isinstance(execution.get("llmActionDecisionValidation"), dict) else {}
    repair = execution.get("llmActionDecisionRepairReport") if isinstance(execution.get("llmActionDecisionRepairReport"), dict) else {}
    user_message = _harmonyos_first_present(product_arguments, "userMessage", "user_message", "userInput", "user_input", "message")
    trace_pack_core = {
        "endpoint": "POST /agent/harmonyos/practice-coach-session/message/execute",
        "userId": _harmonyos_first_present(product_arguments, "userId", "user_id"),
        "sessionId": _harmonyos_first_present(product_arguments, "sessionId", "session_id"),
        "responseType": response_type,
        "stateDigestAfter": execution.get("stateDigestAfter"),
        "code": code,
    }
    return {
        "tracePackVersion": PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION,
        "purpose": "Copy this object when reporting HarmonyOS Practice Coach device feedback.",
        "copyThisForBackendIssue": True,
        "tracePackId": "pcfb-" + _short_digest(trace_pack_core),
        "endpoint": "POST /agent/harmonyos/practice-coach-session/message/execute",
        "requestSummary": {
            "userId": _harmonyos_first_present(product_arguments, "userId", "user_id"),
            "sessionId": _harmonyos_first_present(product_arguments, "sessionId", "session_id"),
            "deviceId": _harmonyos_first_present(product_arguments, "deviceId", "device_id"),
            "clientLocalDate": _harmonyos_first_present(product_arguments, "clientLocalDate", "client_local_date"),
            "clientTimezone": _harmonyos_first_present(product_arguments, "clientTimezone", "client_timezone"),
            "locale": _harmonyos_first_present(product_arguments, "locale"),
            "userMessagePreview": _compact_preview(user_message),
            "userMessageDigest": _short_digest(user_message),
            "hasProfileFormResult": isinstance(product_arguments.get("profileFormResult"), dict) or isinstance(product_arguments.get("profile_form_result"), dict),
            "productRequestMustNotContainInternalFields": [
                "dbPath",
                "sqliteDbPath",
                "clientConfirmedRecordWrite",
                "providerResult",
                "llmActionDecisionResult",
                "apiKey",
            ],
        },
        "responseSummary": {
            "ok": bool(persisted),
            "code": code,
            "responseType": response_type,
            "messagePreview": _compact_preview(content),
            "nextClientActions": list(agent_action.get("nextClientActions") or []),
            "conversationStatePersisted": bool(persisted),
            "planProposalReady": response_type in {"practice_plan_proposal", "practice_plan_revision"} and isinstance(plan, dict),
            "routineCardReady": response_type == "routine_card_ready" and isinstance(card, dict),
            "profileSheetIntentReady": response_type == "request_profile_sheet" and isinstance(sheet, dict),
            "routineStartEnabled": response_type == "routine_card_ready" and isinstance(card, dict),
            "requiresUserTapToStart": response_type == "routine_card_ready" and isinstance(card, dict),
        },
        "decisionTrace": {
            "decisionMode": execution.get("decisionMode"),
            "selectedActionExecutor": execution.get("selectedActionExecutor"),
            "routerDecisionReason": execution.get("routerDecisionReason"),
            "llmCalled": bool(safety.get("llmCalled", False)),
            "networkCallExecuted": bool(safety.get("networkCallExecuted", False)),
            "llmActionDecisionSource": execution.get("llmActionDecisionSource"),
            "deterministicFallbackUsed": bool(execution.get("deterministicFallbackUsed", False)),
            "deterministicFallbackReason": execution.get("deterministicFallbackReason"),
            "llmActionDecisionValidationOk": bool(validation.get("ok", False)),
            "llmActionDecisionValidationReason": validation.get("reason"),
            "repairAnyApplied": bool(repair.get("anyRepairApplied", False)),
            "repairWarnings": list((repair.get("parseWarnings") or [])) + list((repair.get("schemaWarnings") or [])),
        },
        "stateTrace": {
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "turnCountBefore": state_before.get("turn_count"),
            "turnCountAfter": state_after.get("turn_count"),
            "awaitingConfirmationBefore": bool(state_before.get("awaiting_confirmation", False)) if state_before else False,
            "awaitingConfirmationAfter": bool(state_after.get("awaiting_confirmation", False)) if state_after else False,
            "lastAgentActionAfter": state_after.get("last_agent_action"),
            "pendingMissingFieldsAfter": list(state_after.get("pending_missing_fields") or []),
            "collectedFieldKeysAfter": _list_keys(state_after.get("collected_fields")),
            "draftPlanDigestBefore": _short_digest(state_before.get("draft_plan")) if isinstance(state_before.get("draft_plan"), dict) else None,
            "draftPlanDigestAfter": _short_digest(state_after.get("draft_plan")) if isinstance(state_after.get("draft_plan"), dict) else None,
            "draftPlanSummaryAfter": _practice_coach_plan_summary(state_after.get("draft_plan")),
        },
        "artifactTrace": {
            "sheetType": sheet.get("sheetType") if isinstance(sheet, dict) else None,
            "planProposalId": plan.get("proposalId") if isinstance(plan, dict) else None,
            "planProposalTotalDurationMinutes": plan.get("totalDurationMinutes") if isinstance(plan, dict) else None,
            "planProposalPracticeFocus": plan.get("practiceFocus") if isinstance(plan, dict) else None,
            "routineCardId": card.get("routineCardId") if isinstance(card, dict) else None,
            "routineId": card.get("routineId") if isinstance(card, dict) else None,
        },
        "ioTrace": {
            "sqliteReadBlockedReasons": list(read_io.get("blockedReasons") or []),
            "sqliteWriteBlockedReasons": list(write_io.get("blockedReasons") or []),
            "sqliteConnectionCreated": bool(write_io.get("sqliteConnectionCreated", False) or read_io.get("sqliteConnectionCreated", False)),
            "sqliteTablesCreated": bool(write_io.get("sqliteTablesCreated", False) or read_io.get("sqliteTablesCreated", False)),
            "sqliteRowsWritten": bool(write_io.get("sqliteRowsWritten", False)),
            "sqliteRowCountWritten": int(write_io.get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(write_io.get("transactionCommitted", False)),
            "readError": read_io.get("readError"),
            "writeError": write_io.get("writeError"),
        },
        "safetyTrace": {
            "startsRoutine": False,
            "callsEngineAdapter": False,
            "createsMidiAsset": False,
            "startsPlayback": False,
            "writesHarmonyOSLocalState": False,
            "backendValidatesLlmActionContract": True,
            "clientMustStartRoutineExplicitly": response_type == "routine_card_ready",
        },
        "frontendFeedbackChecklist": [
            "request URL and baseUrl",
            "request JSON without internal fields",
            "HTTP status and response JSON",
            "mapped UI state kind",
            "visible message/content",
            "whether sheet/proposal/routine card rendered",
            "whether Routine auto-start was avoided",
            "deviceFeedbackTracePack object",
        ],
    }


def _practice_coach_frontend_ui_action(
    *,
    response_type: str,
    content: str,
    agent_action: dict,
    sheet_intent: dict | None,
    plan_proposal: dict | None,
    routine_card: dict | None,
    persisted: bool,
) -> dict:
    """Normalized HarmonyOS UI action hint for Practice Coach rendering.

    The backend still returns the canonical response fields. This compact object
    is a stable frontend integration aid: HarmonyOS may render by responseType
    directly, or consume this object to avoid re-inferring whether a plan card
    should be replaced, whether a sheet may open, or whether a routine card is
    display-only. It is not an instruction to auto-start Routine.
    """

    status_by_type = {
        "ask_clarifying_question": "clarifying",
        "request_profile_sheet": "profile_sheet",
        "practice_plan_proposal": "plan_proposal",
        "practice_plan_revision": "plan_proposal",
        "routine_card_ready": "routine_card",
        "chat_message": "chat_message",
        "cannot_proceed": "cannot_proceed",
    }
    render_mode_by_type = {
        "ask_clarifying_question": "append_assistant_message",
        "request_profile_sheet": "open_or_show_profile_sheet_prompt",
        "practice_plan_proposal": "show_plan_proposal_card",
        "practice_plan_revision": "replace_plan_proposal_card",
        "routine_card_ready": "show_routine_card",
        "chat_message": "append_assistant_message",
        "cannot_proceed": "show_blocking_message",
    }
    next_client_actions = list(agent_action.get("nextClientActions") or [])
    return {
        "version": PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION,
        "purpose": "Frontend-facing normalized UI action hint; canonical source remains data.responseType and payload fields.",
        "responseType": response_type,
        "status": status_by_type.get(response_type, "chat_message"),
        "renderMode": render_mode_by_type.get(response_type, "append_assistant_message"),
        "visibleContent": content,
        "nextClientActions": next_client_actions,
        "shouldAppendAssistantMessage": response_type in {"ask_clarifying_question", "chat_message", "cannot_proceed"},
        "shouldOpenProfileSheet": response_type == "request_profile_sheet" and isinstance(sheet_intent, dict),
        "shouldRenderPlanProposalCard": response_type in {"practice_plan_proposal", "practice_plan_revision"} and isinstance(plan_proposal, dict),
        "shouldReplaceCurrentProposal": response_type == "practice_plan_revision" and isinstance(plan_proposal, dict),
        "shouldRenderRoutineCard": response_type == "routine_card_ready" and isinstance(routine_card, dict),
        "shouldShowRecordedSummary": False,
        "canStartRoutineByUserTap": response_type == "routine_card_ready" and isinstance(routine_card, dict) and bool(routine_card.get("startEnabled", False)),
        "safeToAutostartRoutine": False,
        "backendStartsRoutine": False,
        "requiresUserTapToStart": response_type == "routine_card_ready" and isinstance(routine_card, dict),
        "conversationStatePersisted": bool(persisted),
        "payloadRefs": {
            "sheetIntent": "data.sheetIntent" if isinstance(sheet_intent, dict) else None,
            "planProposal": "data.planProposal" if isinstance(plan_proposal, dict) else None,
            "routineCardPayload": "data.routineCardPayload" if isinstance(routine_card, dict) else None,
            "deviceFeedbackTracePack": "data.deviceFeedbackTracePack",
        },
        "frontendRules": [
            "Never auto-start Routine from Practice Coach response.",
            "Render practice_plan_revision by replacing the current proposal card, not by stacking a second proposal card.",
            "Render routine_card_ready as a display card with a user-tap start button only.",
            "If request_profile_sheet is returned, the frontend owns native bindSheet rendering.",
        ],
    }


def _routine_completion_frontend_ui_action(*, persisted: bool, content: str, record: dict | None) -> dict:
    return {
        "version": PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION,
        "purpose": "Frontend-facing normalized UI action hint for Routine completion summary rendering.",
        "responseType": "routine_completion_recorded" if persisted else "routine_completion_record_failed",
        "status": "completion_recorded" if persisted else "backend_error",
        "renderMode": "show_routine_summary_recorded" if persisted else "show_completion_error",
        "visibleContent": content,
        "shouldShowRecordedSummary": bool(persisted),
        "shouldOpenPracticeCoach": False,
        "shouldShowPostSessionRecommendationCard": False,
        "safeToAutostartRoutine": False,
        "backendStartsRoutine": False,
        "nextClientActions": ["show_completion_recorded_summary"] if persisted else ["show_completion_record_error"],
        "payloadRefs": {
            "routineCompletionRecord": "data.routineCompletionRecord" if isinstance(record, dict) else None,
        },
        "frontendRules": [
            "RoutineSummaryPage should show that the practice was recorded.",
            "Do not auto-open Practice Coach after practice completion.",
            "The next Practice Coach guidance happens only when the user asks again.",
        ],
    }


def _practice_coach_plan_summary(plan: object) -> dict | None:
    if not isinstance(plan, dict):
        return None
    return {
        "proposalId": plan.get("proposalId"),
        "title": plan.get("title"),
        "practiceFocus": plan.get("practiceFocus"),
        "totalDurationMinutes": plan.get("totalDurationMinutes"),
        "blockCount": len(plan.get("blocks") or []) if isinstance(plan.get("blocks"), list) else 0,
        "confirmationStatus": plan.get("confirmationStatus"),
    }


@router.get("/harmonyos/today-guidance-api-contract-alignment/spec")
def get_agent_harmonyos_today_guidance_api_contract_alignment_spec() -> dict:
    return {"ok": True, "spec": agent_harmonyos_today_guidance_api_contract_alignment_contract()}


@router.post("/harmonyos/today-guidance-api-contract-alignment/preview")
def preview_agent_harmonyos_today_guidance_api_contract_alignment_request(request: dict) -> dict:
    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_agent_harmonyos_today_guidance_api_contract_alignment_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_harmonyos_today_guidance_api_contract_alignment",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_harmonyos_today_guidance_api_contract_alignment_summary(payload=payload, source="agent_api")
    return {
        "ok": bool(summary.get("accepted", False)),
        "agentHarmonyOSTodayGuidanceApiContractAlignmentVersion": agent_harmonyos_today_guidance_api_contract_alignment_contract()["version"],
        "payload": payload_dict,
        "summary": summary,
        "routeCatalog": payload_dict.get("route_catalog"),
        "requestContracts": payload_dict.get("request_contracts"),
        "responseContracts": payload_dict.get("response_contracts"),
        "safety": _harmonyos_safety(),
    }


@router.post("/harmonyos/today-practice-guidance/preview")
def preview_harmonyos_today_practice_guidance_request(request: dict) -> dict:
    """HarmonyOS-facing wrapper for ordinary today-practice guidance.

    This route hides the internal v2_10_2 payload name and returns a stable
    {ok, code, message, data, debug, safety} response. It may read SQLite
    context but never writes storage, starts Routine, calls the engine, creates
    MIDI, or starts playback.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    payload = build_agent_usable_today_practice_guidance_mvp_payload(
        product_arguments,
        trace_id=trace_id,
        source="agent_api_harmonyos_today_practice_guidance_preview",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_usable_today_practice_guidance_mvp_summary(payload=payload, source="agent_api_harmonyos")
    terminal_response = payload_dict.get("terminal_response") if isinstance(payload_dict.get("terminal_response"), dict) else {}
    content = str(terminal_response.get("content") or "今天练什么暂时不可用，请检查上下文数据库或 provider 配置。")
    guidance_ready = bool(summary.get("guidance_action_card_is_valid", False))
    ok = bool(summary.get("accepted", False) or content)
    code = "today_guidance_ready" if guidance_ready else "today_guidance_needs_context_or_provider"
    action_card_payload = _extract_harmonyos_action_card_payload(payload_dict)
    return {
        "ok": ok,
        "code": code,
        "message": content,
        "data": {
            "content": content,
            "guidancePreviewReady": guidance_ready,
            "contextSource": summary.get("context_source"),
            "actionCardPayload": action_card_payload,
            "routineCandidateCount": int(summary.get("routine_candidate_count") or 0),
            "requiresUserConfirmationBeforeRoutineStart": True,
        },
        "debug": {
            "agentHarmonyOSTodayGuidanceApiContractAlignmentVersion": agent_harmonyos_today_guidance_api_contract_alignment_contract()["version"],
            "underlyingVersion": summary.get("agent_usable_today_practice_guidance_mvp_version"),
            "validationStatus": summary.get("validation_status"),
            "sqliteReadbackAttempted": bool(summary.get("sqlite_readback_attempted", False)),
            "backendDatabaseRead": bool(summary.get("backend_database_read", False)),
            "sqliteConnectionCreated": bool(summary.get("sqlite_connection_created", False)),
            "sqliteRowsRead": int(summary.get("sqlite_rows_read") or 0),
            "llmCalled": bool(summary.get("llm_called", False)),
            "blockedReasons": list(summary.get("blocked_reasons") or []),
            "warnings": list(summary.get("warnings") or []),
            "agentPayload": payload_dict if bool(product_arguments.get("includeDebugPayload") or product_arguments.get("include_debug_payload")) else None,
        },
        "safety": _harmonyos_safety(),
    }


@router.post("/harmonyos/today-practice-guidance/llm-payload-trace")
def preview_harmonyos_today_practice_guidance_llm_payload_trace(request: dict) -> dict:
    """HarmonyOS debug route showing the exact today-guidance LLM payload preview.

    This endpoint is intentionally read-only and provider-call-free. It answers
    product/debug questions such as: after the user taps "今天该练什么", what
    messages would JamMate prepare for the model if provider execution were
    enabled? The route uses the same black-box product request body as
    /harmonyos/today-practice-guidance/preview.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    payload = build_agent_usable_today_practice_guidance_mvp_payload(
        product_arguments,
        trace_id=trace_id,
        source="agent_api_harmonyos_today_practice_guidance_llm_payload_trace",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_usable_today_practice_guidance_mvp_summary(payload=payload, source="agent_api_harmonyos_llm_payload_trace")
    llm_request_trace = _build_harmonyos_llm_request_trace(payload_dict, summary, product_arguments)
    prompt_ready = bool(llm_request_trace.get("internalPromptMessages")) and bool(llm_request_trace.get("chatCompletionsMessagesIfCalled"))
    return {
        "ok": prompt_ready,
        "code": "today_guidance_llm_payload_trace_ready" if prompt_ready else "today_guidance_llm_payload_trace_unavailable",
        "message": "已生成今日练习建议的 LLM 请求预览；本接口不会调用大模型。" if prompt_ready else "暂时无法生成 LLM 请求预览，请检查 today guidance 链路。",
        "data": {
            "llmPayloadTraceReady": prompt_ready,
            "content": "这是调试预览：展示如果调用大模型，将发送哪些 messages；本接口没有真正调用大模型。",
            "userMessage": product_arguments.get("userInput"),
            "contextSource": summary.get("context_source"),
            "llmRequestPreview": llm_request_trace,
        },
        "debug": {
            "agentHarmonyOSTodayGuidanceApiContractAlignmentVersion": agent_harmonyos_today_guidance_api_contract_alignment_contract()["version"],
            "underlyingVersion": summary.get("agent_usable_today_practice_guidance_mvp_version"),
            "traceVersion": "v2_10_10",
            "validationStatus": summary.get("validation_status"),
            "sqliteReadbackAttempted": bool(summary.get("sqlite_readback_attempted", False)),
            "backendDatabaseRead": bool(summary.get("backend_database_read", False)),
            "sqliteRowsRead": int(summary.get("sqlite_rows_read") or 0),
            "llmCalled": False,
            "networkCallExecuted": False,
            "blockedReasons": list(summary.get("blocked_reasons") or []),
            "warnings": list(summary.get("warnings") or []),
        },
        "safety": _harmonyos_safety(),
    }



@router.post("/harmonyos/practice-coach-session/message/execute")
def execute_harmonyos_practice_coach_session_unified_message_request(request: dict) -> dict:
    """Unified HarmonyOS Practice Coach message/action router.

    This route lets HarmonyOS send one Practice Coach message and then render by
    `responseType` / `nextClientActions`. Since v2_10_17, the route is
    LLM-action-decision-first when a provider or injected smoke result is
    available; deterministic routing is only fallback. It never starts Routine,
    calls Engine, creates MIDI, starts playback, or writes HarmonyOS local state.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    execution = build_practice_coach_unified_message_action_router_execute(product_arguments, trace_id=trace_id)
    persisted = bool(execution.get("statePersisted", False))
    agent_action = execution.get("agentActionPreview") if isinstance(execution.get("agentActionPreview"), dict) else {}
    response_type = str(agent_action.get("responseType") or execution.get("responseType") or "cannot_proceed")
    content = str(agent_action.get("message") or "已处理 Practice Coach Session 消息。")
    code_by_type = {
        "ask_clarifying_question": "practice_coach_message_ask_clarifying_question",
        "chat_message": "practice_coach_message_recorded",
        "request_profile_sheet": "practice_coach_message_profile_sheet_intent_ready",
        "practice_plan_proposal": "practice_coach_message_plan_proposal_ready",
        "practice_plan_revision": "practice_coach_message_plan_revision_ready",
        "routine_card_ready": "practice_coach_message_routine_card_ready",
        "cannot_proceed": "practice_coach_message_cannot_proceed",
    }
    routine_card = execution.get("routineCardPayload") if isinstance(execution.get("routineCardPayload"), dict) else None
    sheet_intent = execution.get("sheetIntent") if isinstance(execution.get("sheetIntent"), dict) else None
    plan_proposal = execution.get("planProposal") if isinstance(execution.get("planProposal"), dict) else None
    frontend_ui_action = _practice_coach_frontend_ui_action(
        response_type=response_type,
        content=content,
        agent_action=agent_action,
        sheet_intent=sheet_intent,
        plan_proposal=plan_proposal,
        routine_card=routine_card,
        persisted=persisted,
    )
    device_feedback_trace_pack = _practice_coach_device_feedback_trace_pack(
        product_arguments=product_arguments,
        execution=execution,
        agent_action=agent_action,
        response_type=response_type,
        content=content,
        persisted=persisted,
        code=code_by_type.get(response_type, "practice_coach_message_processed"),
    )
    return {
        "ok": persisted,
        "code": code_by_type.get(response_type, "practice_coach_message_processed"),
        "message": content,
        "data": {
            "content": content,
            "responseType": response_type,
            "selectedActionExecutor": execution.get("selectedActionExecutor"),
            "routerDecisionReason": execution.get("routerDecisionReason"),
            "nextClientActions": list(agent_action.get("nextClientActions") or []),
            "conversationStatePersisted": persisted,
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateBefore": execution.get("stateBefore"),
            "stateAfter": execution.get("stateAfter"),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "extractedFieldsFromCurrentTurn": execution.get("extractedFieldsFromCurrentTurn") or {},
            "agentActionPreview": agent_action,
            "sheetIntent": sheet_intent,
            "profileSheetIntentReady": response_type == "request_profile_sheet" and sheet_intent is not None,
            "planProposal": plan_proposal,
            "planProposalReady": response_type in {"practice_plan_proposal", "practice_plan_revision"} and plan_proposal is not None,
            "routineCardPayload": routine_card,
            "routineCardReady": response_type == "routine_card_ready" and routine_card is not None,
            "routineStartEnabled": bool(response_type == "routine_card_ready" and routine_card is not None),
            "requiresUserTapToStart": bool(response_type == "routine_card_ready" and routine_card is not None),
            "backendStartsRoutine": False,
            "llmRequestPreview": execution.get("llmRequestPreview"),
            "llmActionRequestPreview": execution.get("llmActionRequestPreview"),
            "deviceFeedbackTracePack": device_feedback_trace_pack,
            "frontendUiAction": frontend_ui_action,
        },
        "debug": {
            "traceVersion": "v2_10_16",
            "frontendUiActionVersion": PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION,
            "frontendUiAction": frontend_ui_action,
            "deviceFeedbackTracePackVersion": PRACTICE_COACH_DEVICE_FEEDBACK_TRACE_PACK_VERSION,
            "deviceFeedbackTracePack": device_feedback_trace_pack,
            "llmActionDecisionTraceVersion": "v2_10_17",
            "realLlmProviderGuardedSmokeVersion": PRACTICE_COACH_REAL_LLM_PROVIDER_GUARDED_SMOKE_VERSION,
            "llmResponseRepairSchemaHardeningVersion": PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_VERSION,
            "sqlitePathGuardMacOSTempdirHotfixVersion": PRACTICE_COACH_SQLITE_PATH_GUARD_MACOS_TEMPDIR_HOTFIX_VERSION,
            "planRevisionIntentRoutingHotfixVersion": PRACTICE_COACH_PLAN_REVISION_INTENT_ROUTING_HOTFIX_VERSION,
            "llmCalled": bool((execution.get("safety") or {}).get("llmCalled", False)),
            "networkCallExecuted": bool((execution.get("safety") or {}).get("networkCallExecuted", False)),
            "decisionMode": execution.get("decisionMode"),
            "llmActionDecisionSource": execution.get("llmActionDecisionSource"),
            "llmProviderStatus": execution.get("llmProviderStatus"),
            "llmProviderResult": execution.get("llmProviderResult"),
            "llmActionDecisionValidation": execution.get("llmActionDecisionValidation"),
            "llmActionDecisionRepairReport": execution.get("llmActionDecisionRepairReport"),
            "deterministicFallbackUsed": bool(execution.get("deterministicFallbackUsed", False)),
            "deterministicFallbackReason": execution.get("deterministicFallbackReason"),
            "selectedActionExecutor": execution.get("selectedActionExecutor"),
            "routerDecisionReason": execution.get("routerDecisionReason"),
            "routerReadBeforeDecision": execution.get("routerReadBeforeDecision"),
            "sqliteConnectionCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteConnectionCreated")),
            "sqliteTablesCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteTablesCreated")),
            "sqliteRowsWritten": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteRowsWritten")),
            "sqliteRowCountWritten": int(((execution.get("io") or {}).get("write") or {}).get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(((execution.get("io") or {}).get("write") or {}).get("transactionCommitted")),
            "stateStoreIo": execution.get("io"),
            "practiceCoachStateStoreIo": execution.get("io"),
        },
        "safety": _harmonyos_safety(
            writes_backend_sqlite=persisted,
            llm_called=bool((execution.get("safety") or {}).get("llmCalled", False)),
            network_call_executed=bool((execution.get("safety") or {}).get("networkCallExecuted", False)),
        ) | {
            "unifiedRouterOnlyDelegatesDeterministicContracts": False,
            "deterministicFallbackUsed": bool(execution.get("deterministicFallbackUsed", False)),
            "llmActionDecisionValidated": bool(((execution.get("llmActionDecisionValidation") or {}).get("ok", False))),
            "backendValidatesLlmActionContract": True,
            "backendRepairsLlmActionSchema": True,
            "frontendMayOpenNativeSheet": bool(sheet_intent),
            "frontendOwnsNativeSheetRendering": bool(sheet_intent),
            "llmDoesNotRenderUi": bool(sheet_intent),
        },
    }

@router.post("/harmonyos/practice-coach-session/context-builder-preview")
def preview_harmonyos_practice_coach_session_context_builder(request: dict) -> dict:
    """HarmonyOS debug route for the cache-friendly Practice Coach context builder.

    This endpoint previews the new Practice Coach Session context engineering
    shape. It is read-only: it may read backend SQLite context, but it never
    calls an LLM/provider, starts Routine, calls Engine, creates MIDI, starts
    playback, or writes HarmonyOS local state.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    preview = build_practice_coach_context_builder_preview(product_arguments)
    return {
        "ok": True,
        "code": "practice_coach_context_builder_preview_ready",
        "message": "已生成 Practice Coach Session 上下文工程预览；本接口不会调用大模型。",
        "data": {
            "contextBuilderPreviewReady": True,
            "content": "这是调试预览：展示 Practice Coach Session 如何组织可缓存的上下文 messages；本接口没有真正调用大模型。",
            "userMessage": preview.get("userMessage"),
            "llmRequestPreview": preview,
        },
        "debug": {
            "traceVersion": "v2_10_11",
            "llmCalled": False,
            "networkCallExecuted": False,
            "sqliteReadOnlyConnectionCreated": bool((preview.get("sourceProjection") or {}).get("sqliteReadOnlyConnectionCreated")),
            "sqliteRowsRead": int((preview.get("sourceProjection") or {}).get("sqliteRowsRead") or 0),
            "stablePrefixDigest": (preview.get("debugMetadata") or {}).get("stable_prefix_digest"),
            "contextPacketDigest": (preview.get("debugMetadata") or {}).get("context_packet_digest"),
            "currentTurnDigest": (preview.get("debugMetadata") or {}).get("current_turn_digest"),
        },
        "safety": _harmonyos_safety(),
    }


@router.post("/harmonyos/practice-coach-session/message-state/execute")
def execute_harmonyos_practice_coach_session_message_state_request(request: dict) -> dict:
    """HarmonyOS route for Practice Coach Session conversation state continuity.

    This route records one user message, restores the previous session state,
    applies a deterministic state update for missing-info continuity, persists
    the updated state to backend SQLite, and returns a cache-aware context
    preview. It does not call an LLM/provider.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    execution = build_practice_coach_conversation_state_store_execute(product_arguments, trace_id=trace_id)
    persisted = bool(execution.get("conversationStatePersisted", False))
    agent_action = execution.get("agentActionPreview") if isinstance(execution.get("agentActionPreview"), dict) else {}
    content = str(agent_action.get("message") or "已处理 Practice Coach Session 对话状态。")
    return {
        "ok": persisted,
        "code": "practice_coach_session_state_persisted" if persisted else "practice_coach_session_state_not_persisted",
        "message": content,
        "data": {
            "content": content,
            "conversationStatePersisted": persisted,
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateBefore": execution.get("stateBefore"),
            "stateAfter": execution.get("stateAfter"),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "extractedFieldsFromCurrentTurn": execution.get("extractedFieldsFromCurrentTurn") or {},
            "agentActionPreview": agent_action,
            "llmRequestPreview": execution.get("llmRequestPreview"),
            "llmActionRequestPreview": execution.get("llmActionRequestPreview"),
        },
        "debug": {
            "traceVersion": "v2_10_12",
            "llmCalled": False,
            "networkCallExecuted": False,
            "sqliteConnectionCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteConnectionCreated")),
            "sqliteTablesCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteTablesCreated")),
            "sqliteRowsWritten": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteRowsWritten")),
            "sqliteRowCountWritten": int(((execution.get("io") or {}).get("write") or {}).get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(((execution.get("io") or {}).get("write") or {}).get("transactionCommitted")),
            "stateStoreIo": execution.get("io"),
            "practiceCoachStateStoreIo": execution.get("io"),
        },
        "safety": _harmonyos_safety(writes_backend_sqlite=persisted),
    }


@router.post("/harmonyos/practice-coach-session/plan-proposal/execute")
def execute_harmonyos_practice_coach_session_plan_proposal_request(request: dict) -> dict:
    """HarmonyOS route for Practice Coach practice-plan proposal contract.

    This route reads/restores the Practice Coach Session state, merges the
    current user turn, and returns either a missing-info clarification action or
    a structured `practice_plan_proposal` awaiting explicit user confirmation.
    It never starts a Routine or creates a Routine card.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    execution = build_practice_coach_plan_proposal_contract_execute(product_arguments, trace_id=trace_id)
    persisted = bool(execution.get("planProposalStatePersisted", False))
    agent_action = execution.get("agentActionPreview") if isinstance(execution.get("agentActionPreview"), dict) else {}
    response_type = str(agent_action.get("responseType") or "cannot_proceed")
    content = str(agent_action.get("message") or "已处理 Practice Coach 练习计划草案请求。")
    proposal_ready = response_type == "practice_plan_proposal" and isinstance(agent_action.get("planProposal"), dict)
    return {
        "ok": persisted,
        "code": "practice_coach_plan_proposal_ready" if proposal_ready else "practice_coach_plan_proposal_needs_more_context",
        "message": content,
        "data": {
            "content": content,
            "planProposalReady": proposal_ready,
            "planProposalStatePersisted": persisted,
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateBefore": execution.get("stateBefore"),
            "stateAfter": execution.get("stateAfter"),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "extractedFieldsFromCurrentTurn": execution.get("extractedFieldsFromCurrentTurn") or {},
            "agentActionPreview": agent_action,
            "planProposal": agent_action.get("planProposal") if isinstance(agent_action.get("planProposal"), dict) else None,
            "requiresUserConfirmationBeforeRoutineCard": True,
            "routineCardPayload": None,
            "routineStartEnabled": False,
            "llmRequestPreview": execution.get("llmRequestPreview"),
            "llmActionRequestPreview": execution.get("llmActionRequestPreview"),
        },
        "debug": {
            "traceVersion": "v2_10_13",
            "llmCalled": False,
            "networkCallExecuted": False,
            "sqliteConnectionCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteConnectionCreated")),
            "sqliteTablesCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteTablesCreated")),
            "sqliteRowsWritten": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteRowsWritten")),
            "sqliteRowCountWritten": int(((execution.get("io") or {}).get("write") or {}).get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(((execution.get("io") or {}).get("write") or {}).get("transactionCommitted")),
            "stateStoreIo": execution.get("io"),
            "practiceCoachStateStoreIo": execution.get("io"),
        },
        "safety": _harmonyos_safety(writes_backend_sqlite=persisted),
    }



@router.post("/harmonyos/practice-coach-session/profile-sheet/execute")
def execute_harmonyos_practice_coach_session_profile_sheet_request(request: dict) -> dict:
    """HarmonyOS route for Practice Coach native profile sheet intent.

    The route either returns `request_profile_sheet` / `sheetIntent` so the
    frontend can open a native bindSheet, or records a submitted
    `profileFormResult` into backend Practice Coach session state. It never
    calls an LLM, starts Routine, calls Engine, creates MIDI, or writes
    HarmonyOS local state.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    execution = build_practice_coach_profile_sheet_intent_contract_execute(product_arguments, trace_id=trace_id)
    persisted = bool(execution.get("profileSheetStatePersisted", False))
    agent_action = execution.get("agentActionPreview") if isinstance(execution.get("agentActionPreview"), dict) else {}
    response_type = str(agent_action.get("responseType") or "cannot_proceed")
    content = str(agent_action.get("message") or "已处理 Practice Coach 基础信息表单请求。")
    sheet_intent_ready = response_type == "request_profile_sheet" and isinstance(agent_action.get("sheetIntent"), dict)
    profile_recorded = response_type == "chat_message" and not sheet_intent_ready
    return {
        "ok": persisted,
        "code": "practice_coach_profile_sheet_intent_ready" if sheet_intent_ready else "practice_coach_profile_sheet_result_recorded" if profile_recorded else "practice_coach_profile_sheet_not_ready",
        "message": content,
        "data": {
            "content": content,
            "profileSheetStatePersisted": persisted,
            "profileSheetIntentReady": sheet_intent_ready,
            "profileFormResultRecorded": profile_recorded,
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateBefore": execution.get("stateBefore"),
            "stateAfter": execution.get("stateAfter"),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "extractedFieldsFromCurrentTurn": execution.get("extractedFieldsFromCurrentTurn") or {},
            "agentActionPreview": agent_action,
            "sheetIntent": agent_action.get("sheetIntent") if isinstance(agent_action.get("sheetIntent"), dict) else None,
            "planProposal": None,
            "routineCardPayload": None,
            "routineStartEnabled": False,
            "llmRequestPreview": execution.get("llmRequestPreview"),
            "llmActionRequestPreview": execution.get("llmActionRequestPreview"),
        },
        "debug": {
            "traceVersion": "v2_10_15",
            "llmCalled": False,
            "networkCallExecuted": False,
            "sqliteConnectionCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteConnectionCreated")),
            "sqliteTablesCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteTablesCreated")),
            "sqliteRowsWritten": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteRowsWritten")),
            "sqliteRowCountWritten": int(((execution.get("io") or {}).get("write") or {}).get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(((execution.get("io") or {}).get("write") or {}).get("transactionCommitted")),
            "stateStoreIo": execution.get("io"),
            "practiceCoachStateStoreIo": execution.get("io"),
        },
        "safety": _harmonyos_safety(writes_backend_sqlite=persisted) | {
            "frontendMayOpenNativeSheet": sheet_intent_ready,
            "frontendOwnsNativeSheetRendering": True,
            "llmDoesNotRenderUi": True,
        },
    }

@router.post("/harmonyos/practice-coach-session/routine-card/execute")
def execute_harmonyos_practice_coach_session_routine_card_request(request: dict) -> dict:
    """HarmonyOS route for confirmed plan -> frontend Routine card payload.

    This route only converts a previously saved draft plan into a
    HarmonyOS-presentable card after an explicit confirmation message. It does
    not start a Routine, call Engine, create MIDI, or write HarmonyOS local
    state; the frontend remains responsible for rendering and local start.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="today_guidance")
    execution = build_practice_coach_routine_card_contract_execute(product_arguments, trace_id=trace_id)
    persisted = bool(execution.get("routineCardStatePersisted", False))
    agent_action = execution.get("agentActionPreview") if isinstance(execution.get("agentActionPreview"), dict) else {}
    response_type = str(agent_action.get("responseType") or "cannot_proceed")
    content = str(agent_action.get("message") or "已处理 Practice Coach 练习卡片请求。")
    routine_card_ready = response_type == "routine_card_ready" and isinstance(agent_action.get("routineCard"), dict)
    return {
        "ok": persisted,
        "code": "practice_coach_routine_card_ready" if routine_card_ready else "practice_coach_routine_card_needs_confirmation_or_plan",
        "message": content,
        "data": {
            "content": content,
            "routineCardReady": routine_card_ready,
            "routineCardStatePersisted": persisted,
            "stateFoundBeforeTurn": bool(execution.get("stateFoundBeforeTurn", False)),
            "stateBefore": execution.get("stateBefore"),
            "stateAfter": execution.get("stateAfter"),
            "stateDigestBefore": execution.get("stateDigestBefore"),
            "stateDigestAfter": execution.get("stateDigestAfter"),
            "extractedFieldsFromCurrentTurn": execution.get("extractedFieldsFromCurrentTurn") or {},
            "agentActionPreview": agent_action,
            "planProposal": agent_action.get("planProposal") if isinstance(agent_action.get("planProposal"), dict) else None,
            "routineCardPayload": agent_action.get("routineCard") if isinstance(agent_action.get("routineCard"), dict) else None,
            "routineStartEnabled": bool(routine_card_ready),
            "requiresUserTapToStart": bool(routine_card_ready),
            "backendStartsRoutine": False,
            "llmRequestPreview": execution.get("llmRequestPreview"),
            "llmActionRequestPreview": execution.get("llmActionRequestPreview"),
        },
        "debug": {
            "traceVersion": "v2_10_14",
            "llmCalled": False,
            "networkCallExecuted": False,
            "sqliteConnectionCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteConnectionCreated")),
            "sqliteTablesCreated": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteTablesCreated")),
            "sqliteRowsWritten": bool(((execution.get("io") or {}).get("write") or {}).get("sqliteRowsWritten")),
            "sqliteRowCountWritten": int(((execution.get("io") or {}).get("write") or {}).get("sqliteRowCountWritten") or 0),
            "transactionCommitted": bool(((execution.get("io") or {}).get("write") or {}).get("transactionCommitted")),
            "stateStoreIo": execution.get("io"),
            "practiceCoachStateStoreIo": execution.get("io"),
        },
        "safety": _harmonyos_safety(writes_backend_sqlite=persisted),
    }


@router.post("/harmonyos/routine-completion-record/execute")
def execute_harmonyos_routine_completion_record_request(request: dict) -> dict:
    """HarmonyOS-facing wrapper for completed Routine record persistence."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    product_arguments = _harmonyos_product_arguments(arguments, route_kind="routine_completion")
    payload = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(
        product_arguments,
        trace_id=trace_id,
        source="agent_api_harmonyos_routine_completion_record_execute",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_routine_completion_record_to_backend_context_write_mvp_summary(payload=payload, source="agent_api_harmonyos")
    terminal_response = payload_dict.get("terminal_response") if isinstance(payload_dict.get("terminal_response"), dict) else {}
    content = str(terminal_response.get("content") or "本次练习记录写入不可用。")
    persisted = bool(summary.get("completion_record_persisted", False))
    code = "routine_completion_record_persisted" if persisted else "routine_completion_record_blocked"
    routine_completion_record = payload_dict.get("routine_completion_record") if isinstance(payload_dict.get("routine_completion_record"), dict) else None
    frontend_ui_action = _routine_completion_frontend_ui_action(
        persisted=persisted,
        content=content,
        record=routine_completion_record,
    )
    return {
        "ok": persisted,
        "code": code,
        "message": content,
        "data": {
            "content": content,
            "completionRecordPersisted": persisted,
            "nextTodayGuidanceCanReadHistory": bool(summary.get("next_today_guidance_can_read_history", False)),
            "idempotentReplay": bool(summary.get("idempotent_replay", False)),
            "routineCompletionRecord": routine_completion_record,
            "frontendUiAction": frontend_ui_action,
        },
        "debug": {
            "agentHarmonyOSTodayGuidanceApiContractAlignmentVersion": agent_harmonyos_today_guidance_api_contract_alignment_contract()["version"],
            "frontendUiActionVersion": PRACTICE_COACH_HARMONYOS_UI_INTEGRATION_FEEDBACK_FIT_VERSION,
            "frontendUiAction": frontend_ui_action,
            "underlyingVersion": summary.get("agent_routine_completion_record_to_backend_context_write_mvp_version"),
            "validationStatus": summary.get("validation_status"),
            "backendDatabaseWritten": bool(summary.get("backend_database_written", False)),
            "backendDatabaseRead": bool(summary.get("backend_database_read", False)),
            "sqliteConnectionCreated": bool(summary.get("sqlite_connection_created", False)),
            "sqliteTablesCreated": bool(summary.get("sqlite_tables_created", False)),
            "sqliteRowsWritten": bool(summary.get("sqlite_rows_written", False)),
            "sqliteRowCountWritten": int(summary.get("sqlite_row_count_written") or 0),
            "sqliteRowsRead": int(summary.get("sqlite_rows_read") or 0),
            "durableBackendWriteExecuted": bool(summary.get("durable_backend_write_executed", False)),
            "transactionCommitted": bool(summary.get("transaction_committed", False)),
            "blockedReasons": list(summary.get("blocked_reasons") or []),
            "warnings": list(summary.get("warnings") or []),
            "agentPayload": payload_dict if bool(product_arguments.get("includeDebugPayload") or product_arguments.get("include_debug_payload")) else None,
        },
        "safety": _harmonyos_safety(writes_backend_sqlite=True),
    }


@router.get("/context/routine-completion-record-to-backend-context-write-mvp/spec")
def get_agent_routine_completion_record_to_backend_context_write_mvp_spec() -> dict:
    return {"ok": True, "spec": agent_routine_completion_record_to_backend_context_write_mvp_contract()}


@router.post("/context/routine-completion-record-to-backend-context-write-mvp/execute")
def execute_agent_routine_completion_record_to_backend_context_write_mvp_request(request: dict) -> dict:
    """Persist one Routine completion record into backend Agent context.

    This route is the product-facing write side of the usable Agent MVP. It may
    write SQLite only when the client supplies clientConfirmedRecordWrite=true
    or the underlying v2_9_0 explicit backend persistence gates. It never writes
    HarmonyOS local state, starts Routine, calls LLM/tools/Engine, creates MIDI,
    or plays audio.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_agent_routine_completion_record_to_backend_context_write_mvp_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_routine_completion_record_to_backend_context_write_mvp",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_routine_completion_record_to_backend_context_write_mvp_summary(payload=payload, source="agent_api")
    return {
        "ok": bool(summary.get("completion_record_persisted", False)),
        "agent_routine_completion_record_to_backend_context_write_mvp_version": agent_routine_completion_record_to_backend_context_write_mvp_contract()["version"],
        "agent_routine_completion_record_to_backend_context_write_mvp_payload": payload_dict,
        "agent_routine_completion_record_to_backend_context_write_mvp_summary": summary,
        "terminal_response": payload_dict.get("terminal_response"),
        "content": (payload_dict.get("terminal_response") or {}).get("content") if isinstance(payload_dict.get("terminal_response"), dict) else None,
        "completion_record_persisted": summary.get("completion_record_persisted", False),
        "next_today_guidance_can_read_history": summary.get("next_today_guidance_can_read_history", False),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": summary.get("storage_written", False),
        "backend_database_written": summary.get("backend_database_written", False),
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": summary.get("sqlite_tables_created", False),
        "sqlite_rows_written": summary.get("sqlite_rows_written", False),
        "sqlite_row_count_written": summary.get("sqlite_row_count_written", 0),
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "durable_backend_write_executed": summary.get("durable_backend_write_executed", False),
        "transaction_committed": summary.get("transaction_committed", False),
        "idempotent_replay": summary.get("idempotent_replay", False),
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }


@router.get("/context/routine-completion-to-today-guidance-product-smoke/spec")
def get_agent_routine_completion_to_today_guidance_product_smoke_spec() -> dict:
    return {"ok": True, "spec": agent_routine_completion_to_today_guidance_product_smoke_contract()}


@router.post("/context/routine-completion-to-today-guidance-product-smoke/execute")
def execute_agent_routine_completion_to_today_guidance_product_smoke_request(request: dict) -> dict:
    """Run product smoke: completion record write then ordinary today guidance."""

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_agent_routine_completion_to_today_guidance_product_smoke_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_routine_completion_to_today_guidance_product_smoke",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_routine_completion_to_today_guidance_product_smoke_summary(payload=payload, source="agent_api")
    return {
        "ok": bool(summary.get("accepted", False)),
        "agent_routine_completion_to_today_guidance_product_smoke_version": agent_routine_completion_to_today_guidance_product_smoke_contract()["version"],
        "agent_routine_completion_to_today_guidance_product_smoke_payload": payload_dict,
        "agent_routine_completion_to_today_guidance_product_smoke_summary": summary,
        "terminal_response": payload_dict.get("terminal_response"),
        "content": (payload_dict.get("terminal_response") or {}).get("content") if isinstance(payload_dict.get("terminal_response"), dict) else None,
        "completion_record_persisted": summary.get("completion_record_persisted", False),
        "guidance_preview_ready": summary.get("guidance_preview_ready", False),
        "recent_completion_history_read_by_guidance": summary.get("recent_completion_history_read_by_guidance", False),
        "routine_candidate_count": summary.get("routine_candidate_count", 0),
        "llm_called": summary.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "storage_written": summary.get("storage_written", False),
        "backend_database_written": summary.get("backend_database_written", False),
        "backend_database_read": summary.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": summary.get("sqlite_connection_created", False),
        "sqlite_tables_created": summary.get("sqlite_tables_created", False),
        "sqlite_rows_written": summary.get("sqlite_rows_written", False),
        "sqlite_row_count_written": summary.get("sqlite_row_count_written", 0),
        "sqlite_rows_read": summary.get("sqlite_rows_read", 0),
        "durable_backend_write_executed": summary.get("durable_backend_write_executed", False),
        "transaction_committed": summary.get("transaction_committed", False),
        "idempotent_replay": summary.get("idempotent_replay", False),
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }

@router.get("/context/usable-today-practice-guidance-mvp/spec")
def get_agent_usable_today_practice_guidance_mvp_spec() -> dict:
    return {"ok": True, "spec": agent_usable_today_practice_guidance_mvp_contract()}


@router.post("/context/usable-today-practice-guidance-mvp/preview")
def preview_agent_usable_today_practice_guidance_mvp_request(request: dict) -> dict:
    """Preview the product-facing today-practice guidance MVP.

    This route accepts ordinary userInput and an optional sqliteDbPath. It may
    read an existing SQLite context backend when a safe path is supplied, but it
    never writes storage, starts Routine, calls the engine, creates MIDI, or
    plays audio.
    """

    arguments = request.get("arguments") or request.get("payload") or request
    if not isinstance(arguments, dict):
        arguments = {}
    trace_id = request.get("trace_id") or request.get("traceId") or arguments.get("trace_id") or arguments.get("traceId")
    payload = build_agent_usable_today_practice_guidance_mvp_payload(
        arguments,
        trace_id=trace_id,
        source="agent_api_usable_today_practice_guidance_mvp",
    )
    payload_dict = payload.to_dict()
    summary = build_agent_usable_today_practice_guidance_mvp_summary(payload=payload, source="agent_api")
    validation = payload_dict.get("validation") if isinstance(payload_dict.get("validation"), dict) else {}
    return {
        "ok": bool(validation.get("accepted", False)),
        "agent_usable_today_practice_guidance_mvp_version": agent_usable_today_practice_guidance_mvp_contract()["version"],
        "agent_usable_today_practice_guidance_mvp_payload": payload_dict,
        "agent_usable_today_practice_guidance_mvp_summary": summary,
        "terminal_response": payload_dict.get("terminal_response"),
        "content": (payload_dict.get("terminal_response") or {}).get("content") if isinstance(payload_dict.get("terminal_response"), dict) else None,
        "context_source": validation.get("context_source"),
        "sqlite_readback_attempted": validation.get("sqlite_readback_attempted", False),
        "guidance_preview_ready": validation.get("guidance_action_card_is_valid", False),
        "routine_candidate_count": validation.get("routine_candidate_count", 0),
        "llm_called": validation.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": validation.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": validation.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": validation.get("sqlite_rows_read", 0),
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }
