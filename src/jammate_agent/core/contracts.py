from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_agent.core.context import CONTEXT_PROFILES, CONTEXT_RUNTIME_VERSION
from jammate_agent.core.llm_provider import LLM_PROVIDER_BOUNDARY_VERSION, build_llm_provider_from_env
from jammate_agent.core.runloop import BoundedAgentRunLoop, RUNLOOP_CONTRACT_VERSION
from jammate_agent.core.tool_invocation import (
    TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
    CONTROLLED_WORKFLOW_EXECUTION_VERSION,
    HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
    AGENT_RUNTIME_SKELETON_CLEANUP_VERSION,
    PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
    PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
    ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
    PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
    ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
    CONTEXT_ENGINEERING_SKELETON_VERSION,
    ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
    PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
    TODAY_PRACTICE_CONTEXT_E2E_VERSION,
    TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
    USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
    TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
    TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
    TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
    TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
    CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION,
    TOOL_INVOCATION_PREVIEW_VERSION,
    agent_runtime_skeleton_contract,
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
    context_engineering_skeleton_contract,
    tool_call_preview_trace_contract,
    tool_execution_confirmation_contract,
    tool_executor_boundary_contract,
    tool_invocation_preview_contract,
    tool_workflow_dispatcher_contract,
)
from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, tool_registry_manifest
from jammate_agent.core.trace import trace_api_contract


@dataclass(frozen=True)
class AgentToolContract:
    name: str
    description: str
    requires_llm: bool = False
    direct_client_callable: bool = False
    input_contract: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requires_llm": self.requires_llm,
            "direct_client_callable": self.direct_client_callable,
            "input_contract": self.input_contract,
            "output_contract": self.output_contract,
        }


@dataclass(frozen=True)
class ContextProfileContract:
    task_type: str
    required_context_layers: list[str]
    optional_context_layers: list[str] = field(default_factory=list)
    output_schema: str | None = None
    llm_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "required_context_layers": list(self.required_context_layers),
            "optional_context_layers": list(self.optional_context_layers),
            "output_schema": self.output_schema,
            "llm_required": self.llm_required,
        }


def agent_capability_manifest() -> dict[str, Any]:
    """Machine-readable manifest for HarmonyOS and future LLM context packets."""
    registry = tool_registry_manifest()
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "agent_name": "JamMateAgent",
        "principle": "LLM/Agent is an enhancement path, not a required path. Direct accompaniment remains callable without LLM.",
        "available_styles": ["medium_swing", "bossa_nova", "jazz_ballad"],
        "available_tools": registry["tools"],
        "tool_registry": {
            "registry_version": registry["registry_version"],
            "route": "GET /agent/tools/registry",
            "execution_status": registry["execution_status"],
            "task_allow_lists": registry["task_allow_lists"],
        },
        "dependency_boundary": {
            "jammate_engine_imports_jammate_agent": False,
            "jammate_agent_uses_engine_only_through_adapter": True,
            "jammate_api_assembles_engine_and_agent": True,
        },
    }


def tool_registry_contract() -> dict[str, Any]:
    return tool_registry_manifest()


def context_profile_manifest() -> dict[str, Any]:
    profiles = [profile.to_dict() for profile in CONTEXT_PROFILES.values()]
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "context_rule": "LLM receives a task-scoped ContextPacket selected by task type; HarmonyOS sends current input, client state, and object ids only.",
        "runtime_preview_route": "POST /agent/context/runtime/preview",
        "runtime_spec_route": "GET /agent/context/runtime/spec",
        "provider_boundary_spec_route": "GET /agent/llm/provider/spec",
        "tool_registry_spec_route": "GET /agent/tools/registry",
        "tool_invocation_preview_spec_route": "GET /agent/tools/invocation/spec",
        "tool_execution_confirmation_spec_route": "GET /agent/tools/confirmation/spec",
        "tool_executor_spec_route": "GET /agent/tools/executor/spec",
        "tool_workflow_dispatcher_spec_route": "GET /agent/tools/workflows/spec",
        "controlled_workflow_execution_spec_route": "GET /agent/tools/workflows/controlled-execution/spec",
        "harmonyos_agent_action_spec_route": "GET /agent/actions/spec",
        "agent_runtime_skeleton_spec_route": "GET /agent/runtime/skeleton",
        "practice_plan_action_card_e2e_spec_route": "GET /agent/actions/practice-plan/spec",
        "playback_prepare_guarded_design_spec_route": "GET /agent/actions/playback-prepare/spec",
        "routine_config_prepare_spec_route": "GET /agent/actions/routine-config/spec",
        "practice_plan_to_routine_candidate_bridge_spec_route": "GET /agent/actions/practice-plan/routine-candidate/spec",
        "routine_history_context_intake_spec_route": "GET /agent/context/routine-history/spec",
        "active_practice_plan_context_intake_spec_route": "GET /agent/context/active-practice-plan/spec",
        "practice_context_assembly_policy_spec_route": "GET /agent/context/practice-assembly/spec",
        "today_practice_context_e2e_spec_route": "GET /agent/context/today-practice/spec",
        "today_practice_guidance_prompt_contract_spec_route": "GET /agent/context/today-practice-guidance/spec",
        "user_capability_map_and_intent_taxonomy_spec_route": "GET /agent/capabilities/user-intents/spec",
        "today_practice_guidance_output_validation_spec_route": "GET /agent/context/today-practice-guidance/output-validation/spec",
        "today_practice_guidance_provider_boundary_e2e_spec_route": "GET /agent/context/today-practice-guidance/provider-boundary/spec",
        "today_practice_guidance_action_card_spec_route": "GET /agent/context/today-practice-guidance/action-card/spec",
        "today_practice_guidance_terminal_chat_e2e_spec_route": "GET /agent/context/today-practice-guidance/terminal-chat/spec",
        "context_and_guidance_skeleton_cleanup_spec_route": "GET /agent/context/guidance-skeleton-cleanup",
        "context_engineering_skeleton_spec_route": "GET /agent/context/engineering-skeleton",
        "trace_api_spec_route": "GET /agent/traces/spec",
        "trace_list_route": "GET /agent/traces",
        "trace_detail_route": "GET /agent/traces/{trace_id}",
        "profiles": profiles,
    }


def llm_context_runtime_contract() -> dict[str, Any]:
    runloop_contract = BoundedAgentRunLoop().contract()
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "context_runtime_version": CONTEXT_RUNTIME_VERSION,
        "runloop_contract_version": RUNLOOP_CONTRACT_VERSION,
        "routes": {
            "preview": "POST /agent/context/runtime/preview",
            "spec": "GET /agent/context/runtime/spec",
            "provider": "GET /agent/llm/provider/spec",
            "tool_registry": "GET /agent/tools/registry",
            "tool_invocation_preview_spec": "GET /agent/tools/invocation/spec",
            "tool_invocation_preview": "POST /agent/tools/invocation/preview",
            "tool_execution_confirmation_spec": "GET /agent/tools/confirmation/spec",
            "tool_execution_confirmation_preview": "POST /agent/tools/confirmation/preview",
            "tool_executor_spec": "GET /agent/tools/executor/spec",
            "tool_executor_dry_run": "POST /agent/tools/executor/dry-run",
            "tool_workflow_dispatcher_spec": "GET /agent/tools/workflows/spec",
            "tool_workflow_dispatcher_dry_run": "POST /agent/tools/workflows/dispatch-dry-run",
            "controlled_workflow_execution_spec": "GET /agent/tools/workflows/controlled-execution/spec",
            "controlled_workflow_execution": "POST /agent/tools/workflows/execute-controlled",
            "harmonyos_agent_action_spec": "GET /agent/actions/spec",
            "harmonyos_agent_action_preview": "POST /agent/actions/preview",
            "harmonyos_agent_action_execute_controlled": "POST /agent/actions/execute-controlled",
            "agent_runtime_skeleton": "GET /agent/runtime/skeleton",
            "practice_plan_action_card_e2e_spec": "GET /agent/actions/practice-plan/spec",
            "practice_plan_action_card_e2e_execute_controlled": "POST /agent/actions/practice-plan/execute-controlled",
            "playback_prepare_guarded_design_spec": "GET /agent/actions/playback-prepare/spec",
            "playback_prepare_guarded_design_preview": "POST /agent/actions/playback-prepare/guarded-preview",
            "routine_config_prepare_spec": "GET /agent/actions/routine-config/spec",
            "routine_config_prepare": "POST /agent/actions/routine-config/prepare",
            "practice_plan_to_routine_candidate_bridge_spec": "GET /agent/actions/practice-plan/routine-candidate/spec",
            "practice_plan_to_routine_candidate_bridge_prepare": "POST /agent/actions/practice-plan/routine-candidate/prepare",
            "routine_history_context_intake_spec": "GET /agent/context/routine-history/spec",
            "routine_history_context_intake": "POST /agent/context/routine-history/intake",
            "active_practice_plan_context_intake_spec": "GET /agent/context/active-practice-plan/spec",
            "active_practice_plan_context_intake": "POST /agent/context/active-practice-plan/intake",
            "practice_context_assembly_policy_spec": "GET /agent/context/practice-assembly/spec",
            "practice_context_assembly_policy_build": "POST /agent/context/practice-assembly/build",
            "today_practice_context_e2e_spec": "GET /agent/context/today-practice/spec",
            "today_practice_context_e2e_preview": "POST /agent/context/today-practice/preview",
            "today_practice_guidance_prompt_contract_spec": "GET /agent/context/today-practice-guidance/spec",
            "today_practice_guidance_prompt_contract_preview": "POST /agent/context/today-practice-guidance/prompt-preview",
            "user_capability_map_and_intent_taxonomy_spec": "GET /agent/capabilities/user-intents/spec",
            "user_capability_map_and_intent_taxonomy_preview": "POST /agent/capabilities/user-intents/preview",
            "today_practice_guidance_output_validation_spec": "GET /agent/context/today-practice-guidance/output-validation/spec",
            "today_practice_guidance_output_validation_validate": "POST /agent/context/today-practice-guidance/output-validation/validate",
            "today_practice_guidance_provider_boundary_e2e_spec": "GET /agent/context/today-practice-guidance/provider-boundary/spec",
            "today_practice_guidance_provider_boundary_e2e_preview": "POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview",
            "today_practice_guidance_action_card_spec": "GET /agent/context/today-practice-guidance/action-card/spec",
            "today_practice_guidance_action_card_preview": "POST /agent/context/today-practice-guidance/action-card/preview",
            "today_practice_guidance_terminal_chat_e2e_spec": "GET /agent/context/today-practice-guidance/terminal-chat/spec",
            "today_practice_guidance_terminal_chat_e2e_preview": "POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview",
            "context_and_guidance_skeleton_cleanup": "GET /agent/context/guidance-skeleton-cleanup",
            "context_engineering_skeleton": "GET /agent/context/engineering-skeleton",
            "trace_spec": "GET /agent/traces/spec",
            "trace_list": "GET /agent/traces",
            "trace_detail": "GET /agent/traces/{trace_id}",
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string",
            "task_type": "practice_plan_generation | immediate_practice_playback | session_review | coach_qa | null",
            "client_context": "ClientContext",
            "available_minutes": "number | null",
            "duration_minutes": "number | null",
            "instrument": "string",
            "local_unsynced_summary": "Record<string, unknown>",
        },
        "response_schema": {
            "ok": "boolean",
            "task_type": "string",
            "context_packet": "ContextPacket",
            "runloop_preview": "RunLoopPreview",
            "trace_id": "string | null",
        },
        "context_packet_layers": {
            "system_product_context": "Stable JamMate architecture and boundary principles.",
            "user_request": "Current user input plus request metadata only.",
            "client_context": "HarmonyOS screen/session/material ids and local availability.",
            "capability_manifest": "Current allowed styles, practice modes, routes, and tool boundaries.",
            "constraints": "Runtime constraints such as response case, local timer ownership, and engine independence.",
            "allowed_tools": "Task-specific tool allow-list for future bounded LLM tool calls.",
            "output_contract": "Expected response schema and case policy.",
        },
        "runloop": runloop_contract,
        "llm_provider_boundary": llm_provider_boundary_contract(),
        "tool_registry_boundary": tool_registry_contract(),
        "tool_invocation_preview_boundary": tool_invocation_preview_contract(),
        "tool_execution_confirmation_boundary": tool_execution_confirmation_contract(),
        "tool_executor_boundary": tool_executor_boundary_contract(),
        "tool_workflow_dispatcher_boundary": tool_workflow_dispatcher_contract(),
        "controlled_workflow_execution_boundary": controlled_workflow_execution_contract(),
        "harmonyos_agent_action_boundary": harmonyos_agent_action_contract(),
        "agent_runtime_skeleton_cleanup_boundary": agent_runtime_skeleton_contract(),
        "practice_plan_action_card_e2e_boundary": practice_plan_action_card_e2e_contract(),
        "playback_prepare_guarded_design_boundary": playback_prepare_guarded_design_contract(),
        "routine_config_prepare_boundary": routine_config_prepare_contract(),
        "practice_plan_to_routine_candidate_bridge_boundary": practice_plan_to_routine_candidate_bridge_contract(),
        "routine_history_context_intake_boundary": routine_history_context_intake_contract(),
        "active_practice_plan_context_intake_boundary": active_practice_plan_context_intake_contract(),
        "practice_context_assembly_policy_boundary": practice_context_assembly_policy_contract(),
        "today_practice_context_e2e_boundary": today_practice_context_e2e_contract(),
        "context_engineering_skeleton_boundary": context_engineering_skeleton_contract(),
        "user_capability_map_and_intent_taxonomy_boundary": user_capability_map_and_intent_taxonomy_contract(),
        "today_practice_guidance_output_validation_boundary": today_practice_guidance_output_validation_contract(),
        "today_practice_guidance_provider_boundary_e2e_boundary": today_practice_guidance_provider_boundary_e2e_contract(),
        "today_practice_guidance_action_card_boundary": today_practice_guidance_action_card_contract(),
        "today_practice_guidance_terminal_chat_e2e_boundary": today_practice_guidance_terminal_chat_e2e_contract(),
        "context_and_guidance_skeleton_cleanup_boundary": context_and_guidance_skeleton_cleanup_contract(),
        "terminal_tool_call_candidate_extraction": {
            "version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
            "surface": "terminal_chat_only",
            "mode": "json_only_extract_then_preview",
            "execution_enabled": False,
            "rules": [
                "Only explicit JSON tool-call candidates are extracted from successful assistant replies.",
                "Extracted candidates are validated by preview_tool_invocation using the current ContextPacket.allowed_tools.",
                "Candidate extraction never dispatches workflows, routes, adapters, or engine code.",
            ],
        },
        "trace_api_boundary": trace_api_contract(),
        "tool_call_preview_trace_boundary": tool_call_preview_trace_contract(),
        "non_goals": [
            "No real LLM network call from the API runloop preview in v2_4_13.",
            "No autonomous tool execution in v2_4_13.",
            "No runloop-driven tool execution in v2_4_13; tools are descriptor-only.",
            "No runloop-driven tool execution in v2_4_13; tools are descriptor-only and invocation preview is validation-only.",
            "No accompaniment engine generation-rule changes in feature/agent-workflow.",
            "ToolExecutor boundary in v2_6_3 is dry-run/no-op only and does not dispatch workflows or call engine adapters.",
            "Workflow dispatcher boundary in v2_6_4 resolves deterministic workflow descriptors only and does not invoke workflows, routes, or engine adapters.",
            "Controlled workflow execution in v2_6_5 is limited to agent_practice_plan / PracticePlanner.build_plan and must not call routes, engine adapters, accompaniment generation, or MIDI asset creation.",
            "HarmonyOS Agent Action Contract in v2_6_6 exposes Routine-facing action cards and must not call /accompaniment/generate, engine adapters, or create MIDI assets.",
            "Practice-plan ActionCard E2E in v2_6_8 only converts controlled agent_practice_plan output into a Routine-facing payload; it does not start playback, call /accompaniment/generate, call engine adapters, or create MIDI assets.",
            "Playback-prepare guarded design in v2_6_9 only converts agent_playback_prepare descriptor state into a Routine setup candidate; it does not call /accompaniment/generate, call engine adapters, create MIDI assets, or start playback.",
            "RoutineConfig prepare in v2_7_0 converts user intent, practice plans, or practice blocks into editable Routine setup drafts only; it does not start playback, call /accompaniment/generate, call engine adapters, or create MIDI assets.",
            "Practice-plan to Routine candidate bridge in v2_7_1 converts a selected practice-plan block into UI-flow-agnostic Routine candidate data; the client decides presentation and no playback/generation starts.",
            "Context engineering skeleton in v2_7_3 normalizes active PracticePlan context, assembles plan/history/today constraints, and previews today-practice decision inputs only; it does not call the LLM, create recommendations, start playback, call /accompaniment/generate, or call engine adapters.",
            "User capability map and intent taxonomy in v2_7_5 defines what users can ask the LLM to do, which actions are candidate-only, which require confirmation, and which are forbidden; it does not call LLMs or execute tools.",
            "Today-practice guidance output validation in v2_7_6 validates and normalizes future LLM outputs; it blocks unsafe direct actions and does not execute tools, start Routine, or generate accompaniment.",
            "Today-practice terminal chat E2E in v2_7_9 routes ordinary user turns like ‘今天该练什么？’ into the guarded provider/validation/display-card chain only; it does not start Routine or generate accompaniment.",
            "Context and guidance skeleton cleanup in v2_8_0 is a read-only registry/status surface for the v2_7_3→v2_7_9 chain; it does not create recommendations, call LLMs, execute tools, or touch Engine music-generation rules.",
            "Trace API and terminal trace viewer only shape/read trace list/detail/spec responses; tool-call preview trace contract only shapes terminal candidate/preview summaries; they do not execute tools, call LLM providers, dispatch workflows, or call the engine adapter.",
        ],
    }


def llm_provider_boundary_contract() -> dict[str, Any]:
    provider = build_llm_provider_from_env()
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "boundary_version": LLM_PROVIDER_BOUNDARY_VERSION,
        "route": "GET /agent/llm/provider/spec",
        "status": provider.status(),
        "config_env": {
            "provider": "JAMMATE_LLM_PROVIDER",
            "model": "JAMMATE_LLM_MODEL",
            "api_key_env_var": "JAMMATE_LLM_API_KEY_ENV_VAR, defaults to JAMMATE_LLM_API_KEY",
            "api_key": "JAMMATE_LLM_API_KEY or the env var named by JAMMATE_LLM_API_KEY_ENV_VAR",
            "base_url": "JAMMATE_LLM_BASE_URL, defaults to https://api.openai.com/v1",
            "chat_completions_path": "JAMMATE_LLM_CHAT_COMPLETIONS_PATH, defaults to /chat/completions",
            "enable_network_calls": "JAMMATE_LLM_ENABLE_NETWORK_CALLS",
            "max_prompt_chars": "JAMMATE_LLM_MAX_PROMPT_CHARS",
            "max_output_tokens": "JAMMATE_LLM_MAX_OUTPUT_TOKENS",
            "temperature": "JAMMATE_LLM_TEMPERATURE",
        },
        "terminal_chat": {
            "entrypoint": "python -m jammate_agent.cli.terminal_chat",
            "console_script": "jammate-agent-chat",
            "supported_providers": ["openai", "openai_compatible"],
            "requires_explicit_network_gate": True,
            "tool_execution_enabled": False,
            "candidate_extraction": {
                "version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
                "mode": "json_only_extract_then_preview",
                "execution_enabled": False,
                "source": "successful assistant text",
            },
            "slash_commands": ["/help", "/session", "/context [full]", "/profiles", "/profile [task_type]", "/task-type [task_type]", "/instrument [instrument]", "/reset", "/tools", "/tool-preview <tool_name> [json_object_arguments]", "/pending", "/confirm", "/reject", "/execute-dry-run", "/trace", "/traces", "/exit"],
            "context_controls": {"profile_switch_clears_history": True, "provider_call_enabled": False, "tool_execution_enabled": False, "commands": ["/context", "/profiles", "/profile", "/task-type", "/instrument", "/session", "/reset"]},
            "tool_preview_example": 'python -m jammate_agent.cli.terminal_chat --task-type immediate_practice_playback --once \'/tool-preview agent_playback_prepare {"durationMinutes":20}\'',
            "trace_export": {
                "enabled_by": "--trace-dir <dir>",
                "commands": ["/trace", "/traces"],
                "format": "AgentTrace JSON",
                "execution_enabled": False,
                "viewer_entrypoint": "python -m jammate_agent.cli.trace_viewer",
                "viewer_console_script": "jammate-agent-traces",
                "viewer_read_only": True,
            },
        },
        "guards": {
            "api_runloop_llm_calls_enabled": False,
            "terminal_chat_llm_calls_enabled_when_configured": True,
            "autonomous_tool_execution_enabled": False,
            "default_provider_class": "DisabledLLMProvider",
            "network_rule": "API runloop preview never calls the provider; terminal chat may call only when provider, model, API key, and JAMMATE_LLM_ENABLE_NETWORK_CALLS are configured.",
            "tool_rule": "Terminal chat may include allowed tool descriptors as context and may preview extracted JSON tool-call candidates, but must not execute tools.",
        },
        "tool_invocation_preview": {
            "version": TOOL_INVOCATION_PREVIEW_VERSION,
            "route": "POST /agent/tools/invocation/preview",
            "execution_enabled": False,
        },
        "future_provider_contract": {
            "protocol": "LLMProvider.status() + LLMProvider.generate(LLMRequestEnvelope)",
            "request_envelope": ["context_packet", "allowed_tools", "output_contract", "runtime_policy", "messages"],
            "response": ["ok", "content", "provider_name", "model", "error_code", "message", "raw_usage"],
        },
    }


def arkts_contract_sketch() -> dict[str, Any]:
    """Compact contract sketch for HarmonyOS codegen/reference."""
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "note": "This is a reference sketch. ArkTS source should define equivalent interfaces in PracticeTypes.ets / AgentTypes.ets.",
        "interfaces": {
            "ClientContext": {
                "timezone": "string",
                "locale": "string",
                "currentScreen": "string | null",
                "availableMinutes": "number | null",
                "activeSessionId": "string | null",
                "activePlanId": "string | null",
                "selectedMaterialId": "string | null",
            },
            "AgentPlanRequest": {
                "userInput": "string",
                "availableMinutes": "number",
                "instrument": "string",
                "activeGoalId": "string | null",
            },
            "AgentPlaybackPrepareRequest": {
                "userInput": "string",
                "durationMinutes": "number",
                "clientContext": "ClientContext",
            },
            "AgentContextRuntimePreviewRequest": {
                "requestId": "string | null",
                "userInput": "string",
                "taskType": "string | null",
                "clientContext": "ClientContext",
                "availableMinutes": "number | null",
                "durationMinutes": "number | null",
                "instrument": "string",
                "localUnsyncedSummary": "Record<string, Object>",
            },
            "ContextPacket": {
                "contextRuntimeVersion": "string",
                "taskType": "string",
                "selectedContextLayers": "string[]",
                "allowedTools": "string[]",
                "runtimePolicy": "Record<string, Object>",
                "outputContract": "Record<string, Object>",
                "routingHints": "Record<string, Object>",
            },
            "RunLoopPreview": {
                "runtimeMode": "preview_only | string",
                "llmProviderConfigured": "boolean",
                "toolExecutionEnabled": "boolean",
                "allowedTools": "string[]",
                "nextAction": "string",
            },
            "PracticePlan": {
                "planId": "string",
                "title": "string",
                "durationMinutes": "number",
                "mainFocus": "string",
                "blocks": "ExerciseBlock[]",
                "estimatedDifficulty": "string",
                "explanation": "string | null",
                "source": "rule_based | llm | template | hybrid",
            },
            "PlaybackInstruction": {
                "autoStart": "boolean",
                "targetDurationMinutes": "number",
                "clientLoopUntilTargetDuration": "boolean",
            },
            "AccompanimentAsset": {
                "assetId": "string",
                "format": "midi_base64",
                "midiBase64": "string",
                "midiPath": "string | null",
                "durationSeconds": "number | null",
                "cacheKey": "string | null",
                "debugSummary": "Record<string, Object>",
            },
            "AgentResponse": {
                "ok": "boolean",
                "intentType": "string",
                "plan": "PracticePlan | null",
                "practiceSession": "Record<string, Object> | null",
                "asset": "AccompanimentAsset | null",
                "playbackInstruction": "PlaybackInstruction | null",
                "recommendation": "NextStepRecommendation | null",
                "traceId": "string | null",
                "errorCode": "string | null",
                "message": "string | null",
                "options": "AgentOption[]",
            },
        },
    }

def harmonyos_playback_contract() -> dict[str, Any]:
    """Playback and cache rules for HarmonyOS client implementation."""
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "response_case": "snake_case",
        "request_case": "snake_case_or_camelCase",
        "principle": "Agent/LLM is an enhancement path. HarmonyOS can run the local practice workspace without LLM and can directly call /accompaniment/generate when parameters are explicit.",
        "playback_instruction_contract": {
            "auto_start": "If true, client may start playback after caching/decoding the returned asset.",
            "target_duration_minutes": "Practice timer target. This is not the rendered MIDI length.",
            "client_loop_until_target_duration": "If true, loop the returned asset locally until target_duration_minutes is reached or user stops.",
            "asset_loop_mode": "loop_until_target_duration",
            "requires_local_timer": True,
            "stop_condition": "practice_timer_reaches_target_duration_or_user_stops",
        },
        "asset_cache_policy": {
            "canonical_field": "asset.cache_key",
            "fallback_key": "asset.asset_id",
            "cache_payload": ["midi_base64", "midi_path", "duration_seconds", "debug_summary"],
            "reuse_rule": "Reuse cached asset when cache_key matches the current request signature and the user has not requested regeneration.",
            "scope": "recent_practice_asset",
        },
        "recommended_client_state_machine": [
            "idle",
            "preparing_remote_asset",
            "ready_cached",
            "playing",
            "paused",
            "completed",
            "failed",
        ],
        "non_llm_paths": [
            "local practice task / routine / timer / review",
            "POST /accompaniment/generate for explicit manual accompaniment settings",
            "POST /accompaniment/generate prefers inline jammate_leadsheet_v2 with sections + written_form; tune is fallback only",
        ],
        "agent_paths": [
            "POST /agent/practice/plan for natural-language planning",
            "POST /agent/playback/prepare for natural-language immediate practice playback",
            "POST /agent/context/runtime/preview for preview-only future LLM context/runtime inspection",
        ],
    }


def agent_api_usage_examples() -> dict[str, Any]:
    """Machine-readable HarmonyOS integration examples."""
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "examples": {
            "health_check": {
                "method": "GET",
                "path": "/health",
                "expected_ok": True,
            },
            "direct_accompaniment_no_llm": {
                "method": "POST",
                "path": "/accompaniment/generate",
                "request": {
                    "leadsheet": {
                        "schema_version": "jammate_leadsheet_v2",
                        "title": "HarmonyOS Inline Smoke",
                        "key": "C",
                        "sections": {
                            "A": {
                                "label": "A",
                                "bars": [
                                    {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}, {"beat": 3.0, "symbol": "Dm7"}]},
                                    {"chords": [{"beat": 1.0, "symbol": "G7"}, {"beat": 3.0, "symbol": "Cmaj7"}]},
                                ],
                            }
                        },
                        "written_form": ["A"],
                    },
                    "tune": "Blue Bossa",
                    "style": "bossa_nova",
                    "tempo": 120,
                    "choruses": 1,
                    "seed": 42,
                    "outputFormat": "midi_base64",
                },
                "response_focus": ["ok", "asset.midi_base64", "asset.cache_key"],
            },
            "agent_immediate_playback": {
                "method": "POST",
                "path": "/agent/playback/prepare",
                "request": {
                    "userInput": "我想练 Blue Bossa 20分钟，钢琴和声色彩丰富一些",
                    "durationMinutes": 20,
                },
                "response_focus": [
                    "ok",
                    "asset.midi_base64",
                    "asset.cache_key",
                    "playback_instruction.client_loop_until_target_duration",
                    "playback_instruction.cache_policy.cache_key",
                    "trace_id",
                ],
            },
            "agent_practice_plan": {
                "method": "POST",
                "path": "/agent/practice/plan",
                "request": {
                    "userInput": "我今天有45分钟，想练Misty的ballad comping",
                    "availableMinutes": 45,
                    "instrument": "piano",
                },
                "response_focus": ["ok", "plan.blocks", "trace_id"],
            },
            "agent_context_runtime_preview": {
                "method": "POST",
                "path": "/agent/context/runtime/preview",
                "request": {
                    "requestId": "ctx_preview_001",
                    "userInput": "我想练 Blue Bossa 20分钟，帮我安排一下",
                    "taskType": "immediate_practice_playback",
                    "durationMinutes": 20,
                },
                "response_focus": ["ok", "context_packet.allowed_tools", "runloop_preview.runtime_mode", "trace_id"],
            },
        },
    }


def arkts_contract_source() -> dict[str, Any]:
    """ArkTS source sketch that HarmonyOS can copy into AgentTypes.ets / PracticeTypes.ets."""
    source = r'''
// JamMate Agent / Practice API Contract v2_4_13
// Requests may be sent as camelCase. Current backend responses are canonical snake_case.

export type JamMateStyle = 'medium_swing' | 'bossa_nova' | 'jazz_ballad'
export type AgentIntentType = 'practice_plan_generation' | 'immediate_practice_playback' | string
export type AssetLoopMode = 'loop_until_target_duration'

export interface ClientContext {
  timezone?: string
  locale?: string
  currentScreen?: string | null
  availableMinutes?: number | null
  activeSessionId?: string | null
  activePlanId?: string | null
  selectedMaterialId?: string | null
}

export interface AgentPlanRequest {
  userInput: string
  availableMinutes?: number
  instrument?: string
  activeGoalId?: string | null
}

export interface AgentPlaybackPrepareRequest {
  userInput: string
  durationMinutes?: number
  clientContext?: ClientContext
}

export interface AgentContextRuntimePreviewRequest {
  requestId?: string | null
  userInput: string
  taskType?: AgentIntentType | null
  clientContext?: ClientContext
  availableMinutes?: number | null
  durationMinutes?: number | null
  instrument?: string
  localUnsyncedSummary?: Record<string, Object>
}

export interface ContextPacket {
  contextRuntimeVersion: string
  taskType: AgentIntentType | string
  selectedContextLayers: string[]
  systemProductContext: Record<string, Object>
  userRequest: Record<string, Object>
  clientContext: Record<string, Object>
  capabilities: Record<string, Object>
  constraints: Record<string, Object>
  allowedTools: string[]
  outputContract: Record<string, Object>
  runtimePolicy: Record<string, Object>
  routingHints: Record<string, Object>
}

export interface RunLoopPreview {
  contractVersion: string
  ok: boolean
  runtimeMode: 'preview_only' | string
  llmProviderConfigured: boolean
  toolExecutionEnabled: boolean
  maxSteps: number
  allowedTools: string[]
  nextAction: string
  reason: string
  warnings: string[]
}

export interface AgentContextRuntimePreviewResponse {
  ok: boolean
  taskType: AgentIntentType | string
  contextPacket: ContextPacket
  runloopPreview: RunLoopPreview
  traceId?: string | null
  errorCode?: string | null
  message?: string | null
}

export interface JamMateLeadsheetV2 {
  schema_version: 'jammate_leadsheet_v2'
  title: string
  key?: string
  sections: Record<string, Object> | Array<Record<string, Object>>
  written_form: Array<string | Record<string, Object>>
  metadata?: Record<string, Object>
}

export interface DirectAccompanimentGenerateRequest {
  leadsheet?: JamMateLeadsheetV2 | Record<string, Object> | null
  tune?: string | null // fallback only; inline leadsheet is preferred for custom charts
  style?: JamMateStyle
  tempo?: number
  choruses?: number
  seed?: number
  outputPath?: string | null
  ensemble?: Record<string, Object>
  voicingOverride?: Record<string, Object>
  outputFormat?: 'midi_base64'
}

export interface PracticeMaterial {
  type: string
  tune?: string | null
  section?: string | null
  key?: string | null
  progression?: string | null
  bars?: number | null
  raw?: Record<string, Object>
}

export interface AccompanimentPracticeConfig {
  enabled: boolean
  style: JamMateStyle | string
  tempo: number
  loop_count?: number | null
  duration_minutes?: number | null
  section_loop: boolean
  muted_roles: string[]
  count_in: boolean
  harmonic_expansion_enabled: boolean
  density: string
  practice_role: string
  output_format: 'midi_base64' | 'asset_id'
  arrangement_intent: Record<string, Object>
}

export interface ExerciseBlock {
  block_id: string
  type: string
  title: string
  intent: string
  duration_minutes: number
  material?: PracticeMaterial | null
  tempo?: number | null
  style?: string | null
  accompaniment_config?: AccompanimentPracticeConfig | null
  success_criteria: string[]
  review_prompt?: string | null
  status: 'pending' | 'active' | 'completed' | 'skipped' | string
}

export interface PracticePlan {
  plan_id: string
  title: string
  duration_minutes: number
  main_focus: string
  blocks: ExerciseBlock[]
  estimated_difficulty: string
  explanation?: string | null
  source: 'rule_based' | 'llm' | 'template' | 'hybrid' | string
}

export interface AccompanimentAsset {
  asset_id?: string
  format: 'midi_base64'
  midi_base64: string
  midi_path?: string | null
  duration_seconds?: number | null
  cache_key?: string | null
  debug_summary?: Record<string, Object>
}

export interface PlaybackInstruction {
  auto_start: boolean
  target_duration_minutes: number
  client_loop_until_target_duration: boolean
  asset_loop_mode?: AssetLoopMode | string
  stop_condition?: string
  requires_local_timer?: boolean
  cache_policy?: {
    cache_key?: string | null
    scope?: string
    reuse_when_request_signature_matches?: boolean
  }
}

export interface AgentOption {
  type: string
  label: string
}

export interface AgentResponse {
  ok: boolean
  intent_type: AgentIntentType
  plan?: PracticePlan | null
  practice_session?: Record<string, Object> | null
  asset?: AccompanimentAsset | null
  playback_instruction?: PlaybackInstruction | null
  recommendation?: Record<string, Object> | null
  explanation?: string | null
  error_code?: string | null
  message?: string | null
  options?: AgentOption[]
  trace_id?: string | null
}
'''.strip()
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "filename_suggestion": "AgentTypes.ets",
        "response_case": "snake_case",
        "request_case": "camelCase_or_snake_case",
        "source": source,
    }


def response_case_policy_manifest() -> dict[str, Any]:
    """Canonical API case policy for Python backend and HarmonyOS client-domain mapping."""
    return {
        "version": CONTEXT_RUNTIME_VERSION,
        "canonical_backend_response_case": "snake_case",
        "accepted_request_cases": ["snake_case", "camelCase"],
        "harmonyos_client_domain_case": "camelCase",
        "adapter_file": "CaseAdapter.ets",
        "api_client_file": "JamMateApiClient.ets",
        "principles": [
            "Backend API responses remain canonical snake_case for Python/Pydantic stability.",
            "HarmonyOS may send camelCase or snake_case requests; FastAPI schemas accept both.",
            "HarmonyOS UI/store code should consume camelCase domain objects after CaseAdapter mapping.",
            "Do not maintain two backend response formats unless a future compatibility requirement makes it necessary.",
        ],
        "examples": {
            "backend_raw": {
                "trace_id": "trace_001",
                "playback_instruction": {
                    "target_duration_minutes": 30,
                    "client_loop_until_target_duration": True,
                },
            },
            "harmonyos_domain": {
                "traceId": "trace_001",
                "playbackInstruction": {
                    "targetDurationMinutes": 30,
                    "clientLoopUntilTargetDuration": True,
                },
            },
        },
    }
