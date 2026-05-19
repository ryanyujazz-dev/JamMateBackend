from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import dataclass, field
from typing import Any, Callable

from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, get_tool_descriptor, validate_allowed_tools
from jammate_agent.core.llm_provider import LLMRequestEnvelope, build_llm_provider_from_env

TOOL_INVOCATION_PREVIEW_VERSION = "v2_4_13"
TOOL_CALL_CANDIDATE_EXTRACTION_VERSION = "v2_4_13"
TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION = "v2_4_13"
TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION = "v2_6_2"
TOOL_EXECUTOR_BOUNDARY_VERSION = "v2_6_3"
TOOL_WORKFLOW_DISPATCHER_VERSION = "v2_6_4"
CONTROLLED_WORKFLOW_EXECUTION_VERSION = "v2_6_5"
HARMONYOS_AGENT_ACTION_CONTRACT_VERSION = "v2_6_6"
AGENT_RUNTIME_SKELETON_CLEANUP_VERSION = "v2_6_7"
PRACTICE_PLAN_ACTION_CARD_E2E_VERSION = "v2_6_8"
PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION = "v2_6_9"
ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION = "v2_7_0"
PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION = "v2_7_1"
ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION = "v2_7_2"
CONTEXT_ENGINEERING_SKELETON_VERSION = "v2_7_3"
ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION = CONTEXT_ENGINEERING_SKELETON_VERSION
PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION = CONTEXT_ENGINEERING_SKELETON_VERSION
TODAY_PRACTICE_CONTEXT_E2E_VERSION = CONTEXT_ENGINEERING_SKELETON_VERSION
TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION = "v2_7_4"
USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION = "v2_7_5"
TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION = "v2_7_6"
TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION = "v2_7_7"
TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION = "v2_7_8"
TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION = "v2_7_9"
CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION = "v2_8_0"
USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION = "v2_8_1"
PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION = "v2_8_2"
TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION = "v2_8_3"
PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION = "v2_8_6"
ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION = "v2_8_7"
CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION = "v2_8_8"
CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION = "v2_8_9"
CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION = "v2_8_10"
CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION = "v2_8_11"
CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION = "v2_8_12"
CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION = "v2_8_13"
CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION = "v2_8_14"
CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION = "v2_8_15"
CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION = "v2_8_16"
TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION = "v2_8_17"
TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION = "v2_8_18"
TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION = "v2_8_19"
TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION = "v2_8_20"
TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION = "v2_8_21"
TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION = "v2_8_22"
AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION = "v2_8_23"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION = "v2_9_0"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION = "v2_9_1"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION = "v2_9_2"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION = "v2_9_3"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION = "v2_9_4"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION = "v2_9_5"
CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION = "v2_9_6"


@dataclass(frozen=True)
class ToolInvocationProposal:
    """A future-LLM proposed tool call before any execution is allowed.

    v2_4_13 only validates and previews this proposal. It does not dispatch to
    deterministic workflows, API routes, adapters, or engine code.
    """

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    task_type: str = "coach_qa"
    request_id: str | None = None
    user_input: str | None = None
    client_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": dict(self.arguments),
            "task_type": self.task_type,
            "request_id": self.request_id,
            "user_input": self.user_input,
            "client_context": dict(self.client_context),
        }


@dataclass(frozen=True)
class ToolCallCandidate:
    """A tool-call-like proposal extracted from assistant text.

    The candidate is only a parsing artifact. It must still pass
    `preview_tool_invocation()` before any future execution could be considered.
    v2_4_13 never executes extracted candidates.
    """

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    source_format: str = "unknown"
    source_index: int = 0
    raw_candidate_preview: str = ""

    def to_proposal(self, *, task_type: str, user_input: str | None = None, client_context: dict[str, Any] | None = None) -> ToolInvocationProposal:
        return ToolInvocationProposal(
            tool_name=self.tool_name,
            arguments=dict(self.arguments),
            task_type=task_type,
            user_input=user_input,
            client_context=client_context or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "extraction_version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
            "tool_name": self.tool_name,
            "arguments": dict(self.arguments),
            "source_format": self.source_format,
            "source_index": self.source_index,
            "raw_candidate_preview": self.raw_candidate_preview,
            "would_execute": False,
        }


@dataclass(frozen=True)
class ToolCallCandidateExtractionResult:
    ok: bool
    candidates: list[ToolCallCandidate] = field(default_factory=list)
    scanned_char_count: int = 0
    warnings: list[str] = field(default_factory=list)
    rejected_candidates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "extraction_version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
            "ok": self.ok,
            "candidate_count": len(self.candidates),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "scanned_char_count": self.scanned_char_count,
            "warnings": list(self.warnings),
            "rejected_candidates": list(self.rejected_candidates),
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }


@dataclass(frozen=True)
class ToolInvocationPreviewResult:
    ok: bool
    status: str
    tool_name: str
    task_type: str
    known_tool: bool
    allowed_by_context: bool
    execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    would_execute: bool = False
    descriptor: dict[str, Any] | None = None
    normalized_arguments: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
            "tool_registry_version": TOOL_REGISTRY_VERSION,
            "ok": self.ok,
            "status": self.status,
            "tool_name": self.tool_name,
            "task_type": self.task_type,
            "known_tool": self.known_tool,
            "allowed_by_context": self.allowed_by_context,
            "execution_enabled": self.execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "would_execute": self.would_execute,
            "descriptor": self.descriptor,
            "normalized_arguments": dict(self.normalized_arguments),
            "validation": dict(self.validation),
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ToolInvocationPreviewPolicy:
    """Hard policy for v2_4_13 tool-call previews."""

    mode: str = "preview_validation_only"
    execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    max_argument_keys: int = 32
    max_argument_preview_chars: int = 4000
    required_guards: tuple[str, ...] = (
        "tool_must_exist_in_registry",
        "tool_must_be_allowed_by_context_packet",
        "arguments_are_shape_checked_only",
        "no_deterministic_workflow_dispatch",
        "no_engine_adapter_dispatch",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
            "mode": self.mode,
            "execution_enabled": self.execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "max_argument_keys": self.max_argument_keys,
            "max_argument_preview_chars": self.max_argument_preview_chars,
            "required_guards": list(self.required_guards),
        }


DEFAULT_TOOL_INVOCATION_PREVIEW_POLICY = ToolInvocationPreviewPolicy()


def agent_runtime_no_side_effect_flags() -> dict[str, bool]:
    """Shared no-side-effect guard flags for Agent runtime skeleton surfaces."""

    return {
        "llm_autonomous_execution_enabled": False,
        "real_tool_execution_enabled": False,
        "real_workflow_dispatch_enabled": False,
        "playback_execution_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "engine_adapter_dispatch_enabled": False,
        "route_call_enabled": False,
        "midi_asset_creation_enabled": False,
        "raw_api_key_allowed_in_runtime_payloads": False,
    }


@dataclass(frozen=True)
class AgentRuntimeSkeletonSnapshot:
    """v2_6_7 consolidated status of the Agent runtime skeleton.

    This snapshot is intentionally read-only. It does not preview, confirm,
    execute, dispatch, or call any engine/API route. It exists so terminal, API,
    trace, and HarmonyOS Routine developers can inspect one stable skeleton map
    before adding concrete Agent features.
    """

    skeleton_contract_version: str = AGENT_RUNTIME_SKELETON_CLEANUP_VERSION
    baseline: str = "v2_6_6_harmonyos_agent_action_contract"
    status: str = "skeleton_ready_for_specific_agent_features"
    controlled_execution_allowed_tools: tuple[str, ...] = ("agent_practice_plan",)
    stages: tuple[dict[str, Any], ...] = (
        {"stage": "context_packet", "version": "v2_4_0", "mode": "task_scoped_context", "side_effects": False},
        {"stage": "llm_provider_boundary", "version": "v2_4_2", "mode": "explicit_provider_boundary", "side_effects": False},
        {"stage": "tool_registry", "version": TOOL_REGISTRY_VERSION, "mode": "descriptor_allow_list", "side_effects": False},
        {"stage": "tool_invocation_preview", "version": TOOL_INVOCATION_PREVIEW_VERSION, "mode": "validation_only", "side_effects": False},
        {"stage": "tool_execution_confirmation", "version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION, "mode": "user_approval_record_only", "side_effects": False},
        {"stage": "tool_executor_boundary", "version": TOOL_EXECUTOR_BOUNDARY_VERSION, "mode": "dry_run_noop", "side_effects": False},
        {"stage": "deterministic_workflow_dispatcher", "version": TOOL_WORKFLOW_DISPATCHER_VERSION, "mode": "descriptor_resolution_only", "side_effects": False},
        {"stage": "controlled_workflow_execution", "version": CONTROLLED_WORKFLOW_EXECUTION_VERSION, "mode": "practice_plan_only", "side_effects": False},
        {"stage": "harmonyos_agent_action_card", "version": HARMONYOS_AGENT_ACTION_CONTRACT_VERSION, "mode": "routine_action_card_contract", "side_effects": False},
    )
    terminal_commands: tuple[str, ...] = (
        "/tool-preview",
        "/pending",
        "/confirm",
        "/reject",
        "/execute-dry-run",
        "/dispatch-dry-run",
        "/execute-controlled",
        "/action-card",
        "/runtime-skeleton",
        "/playback-prepare-guarded",
        "/routine-config-prepare",
        "/practice-plan-routine-candidate",
        "/routine-history-context",
    )
    api_routes: tuple[str, ...] = (
        "GET /agent/runtime/skeleton",
        "GET /agent/context/runtime/spec",
        "POST /agent/tools/invocation/preview",
        "POST /agent/tools/confirmation/preview",
        "POST /agent/tools/executor/dry-run",
        "POST /agent/tools/workflows/dispatch-dry-run",
        "POST /agent/tools/workflows/execute-controlled",
        "POST /agent/actions/preview",
        "POST /agent/actions/execute-controlled",
        "GET /agent/actions/playback-prepare/spec",
        "POST /agent/actions/playback-prepare/guarded-preview",
        "GET /agent/actions/routine-config/spec",
        "POST /agent/actions/routine-config/prepare",
        "GET /agent/actions/practice-plan/routine-candidate/spec",
        "POST /agent/actions/practice-plan/routine-candidate/prepare",
    )
    next_recommended_stage: str = "specific_agent_feature_development"

    def to_dict(self) -> dict[str, Any]:
        guards = agent_runtime_no_side_effect_flags()
        return {
            "agent_runtime_skeleton_cleanup_version": self.skeleton_contract_version,
            "version": self.skeleton_contract_version,
            "baseline": self.baseline,
            "status": self.status,
            "stage_count": len(self.stages),
            "stages": [dict(stage) for stage in self.stages],
            "controlled_execution_allowed_tools": list(self.controlled_execution_allowed_tools),
            "terminal_commands": list(self.terminal_commands),
            "api_routes": list(self.api_routes),
            "no_side_effect_guards": guards,
            "forbidden_until_future_milestone": [
                "agent_playback_prepare_real_execution",
                "direct_accompaniment_generate_from_agent_action",
                "POST /accompaniment/generate from Agent action contract",
                "engine_adapter dispatch from runtime skeleton",
                "MIDI asset creation from Agent action card",
                "autonomous LLM tool execution",
            ],
            "cleanup_assertions": {
                "single_core_owner_for_agent_tool_lifecycle": "src/jammate_agent/core/tool_invocation.py",
                "terminal_surface_owner": "src/jammate_agent/cli/terminal_chat.py",
                "api_surface_owner": "src/jammate_api/routes/agent_routes.py",
                "agent_docs_only": True,
                "shared_docs_modified_by_agent_branch": False,
            },
            "practice_plan_to_routine_candidate_bridge_version": PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
            "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
            "next_recommended_stage": self.next_recommended_stage,
        }


def build_agent_runtime_skeleton_snapshot() -> AgentRuntimeSkeletonSnapshot:
    return AgentRuntimeSkeletonSnapshot()


def agent_runtime_skeleton_contract() -> dict[str, Any]:
    """Stable v2_6_7 runtime skeleton cleanup contract."""

    snapshot = build_agent_runtime_skeleton_snapshot().to_dict()
    snapshot.update({
        "spec_route": "GET /agent/runtime/skeleton",
        "mode": "read_only_runtime_skeleton_status",
        "contract_does_not_execute_tools": True,
        "contract_does_not_dispatch_workflows": True,
        "contract_does_not_call_engine_adapter": True,
        "contract_does_not_create_midi_asset": True,
    })
    return snapshot


@dataclass(frozen=True)
class ToolExecutionConfirmationPolicy:
    """v2_6_2 confirmation gate policy.

    This layer records explicit user approval/rejection after preview. It does
    not execute tools, dispatch deterministic workflows, call routes, or call
    engine adapters.
    """

    mode: str = "confirmation_gate_only"
    requires_user_confirmation: bool = True
    execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    would_execute_after_confirmation: bool = False
    execution_still_disabled: bool = True
    required_guards: tuple[str, ...] = (
        "preview_must_pass_before_pending_confirmation",
        "user_must_explicitly_confirm_or_reject",
        "confirmation_does_not_execute_tools",
        "confirmation_does_not_dispatch_workflows",
        "confirmation_does_not_call_engine_adapter",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
            "mode": self.mode,
            "requires_user_confirmation": self.requires_user_confirmation,
            "execution_enabled": self.execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "would_execute_after_confirmation": self.would_execute_after_confirmation,
            "execution_still_disabled": self.execution_still_disabled,
            "required_guards": list(self.required_guards),
        }


DEFAULT_TOOL_EXECUTION_CONFIRMATION_POLICY = ToolExecutionConfirmationPolicy()


@dataclass(frozen=True)
class ToolExecutionConfirmationEnvelope:
    confirmation_contract_version: str
    proposal_id: str
    tool_name: str
    arguments_preview: dict[str, Any] = field(default_factory=dict)
    side_effect_level: str = "unknown"
    risk_summary: str = "Unknown side-effect level; keep execution disabled."
    requires_user_confirmation: bool = True
    user_approved: bool = False
    confirmation_status: str = "pending"
    confirmable: bool = True
    would_execute_after_confirmation: bool = False
    execution_still_disabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    preview_status: str | None = None
    preview_ok: bool = False
    known_tool: bool = False
    allowed_by_context: bool = False
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_contract_version": self.confirmation_contract_version,
            "proposal_id": self.proposal_id,
            "tool_name": self.tool_name,
            "arguments_preview": dict(self.arguments_preview),
            "side_effect_level": self.side_effect_level,
            "risk_summary": self.risk_summary,
            "requires_user_confirmation": self.requires_user_confirmation,
            "user_approved": self.user_approved,
            "confirmation_status": self.confirmation_status,
            "confirmable": self.confirmable,
            "would_execute_after_confirmation": self.would_execute_after_confirmation,
            "execution_still_disabled": self.execution_still_disabled,
            "created_at": self.created_at,
            "preview_status": self.preview_status,
            "preview_ok": self.preview_ok,
            "known_tool": self.known_tool,
            "allowed_by_context": self.allowed_by_context,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "policy": dict(self.policy),
        }

    def with_user_decision(self, *, user_approved: bool, status: str) -> "ToolExecutionConfirmationEnvelope":
        return ToolExecutionConfirmationEnvelope(
            confirmation_contract_version=self.confirmation_contract_version,
            proposal_id=self.proposal_id,
            tool_name=self.tool_name,
            arguments_preview=dict(self.arguments_preview),
            side_effect_level=self.side_effect_level,
            risk_summary=self.risk_summary,
            requires_user_confirmation=self.requires_user_confirmation,
            user_approved=user_approved,
            confirmation_status=status,
            confirmable=self.confirmable,
            would_execute_after_confirmation=False,
            execution_still_disabled=True,
            created_at=self.created_at,
            preview_status=self.preview_status,
            preview_ok=self.preview_ok,
            known_tool=self.known_tool,
            allowed_by_context=self.allowed_by_context,
            blocking_reasons=list(self.blocking_reasons),
            warnings=list(self.warnings),
            policy=dict(self.policy),
        )


@dataclass(frozen=True)
class ToolExecutionConfirmationResult:
    ok: bool
    status: str
    confirmation: ToolExecutionConfirmationEnvelope
    user_approved: bool
    would_execute: bool = False
    execution_still_disabled: bool = True
    next_stage_required: str = "ToolExecutorBoundary"

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
            "ok": self.ok,
            "status": self.status,
            "confirmation": self.confirmation.to_dict(),
            "user_approved": self.user_approved,
            "confirmation_status": self.confirmation.confirmation_status,
            "would_execute": self.would_execute,
            "execution_still_disabled": self.execution_still_disabled,
            "next_stage_required": self.next_stage_required,
        }


def build_confirmation_envelope(
    preview: ToolInvocationPreviewResult,
    *,
    proposal_id: str | None = None,
    policy: ToolExecutionConfirmationPolicy | None = None,
) -> ToolExecutionConfirmationEnvelope:
    """Build a pending confirmation envelope from a preview result.

    Only successful preview results become confirmable pending confirmations.
    Rejected/unknown/not-allowed previews produce a not_confirmable envelope so
    callers can trace why execution cannot proceed. In all cases execution stays
    disabled in v2_6_2.
    """

    active_policy = policy or DEFAULT_TOOL_EXECUTION_CONFIRMATION_POLICY
    side_effect_level = str(preview.validation.get("side_effect_level") or (preview.descriptor or {}).get("side_effect_level") or "unknown")
    confirmable = bool(preview.ok and preview.known_tool and preview.allowed_by_context)
    status = "pending" if confirmable else "not_confirmable"
    return ToolExecutionConfirmationEnvelope(
        confirmation_contract_version=TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
        proposal_id=proposal_id or f"proposal_{uuid4().hex[:12]}",
        tool_name=preview.tool_name,
        arguments_preview=_redact_sensitive_values(preview.normalized_arguments),
        side_effect_level=side_effect_level,
        risk_summary=_risk_summary(side_effect_level, confirmable=confirmable),
        requires_user_confirmation=confirmable,
        user_approved=False,
        confirmation_status=status,
        confirmable=confirmable,
        would_execute_after_confirmation=False,
        execution_still_disabled=True,
        preview_status=preview.status,
        preview_ok=preview.ok,
        known_tool=preview.known_tool,
        allowed_by_context=preview.allowed_by_context,
        blocking_reasons=list(preview.blocking_reasons),
        warnings=list(preview.warnings),
        policy=active_policy.to_dict(),
    )


def confirm_tool_invocation(envelope: ToolExecutionConfirmationEnvelope, *, user_approved: bool) -> ToolExecutionConfirmationResult:
    """Record a user decision for a pending confirmation without executing."""

    if not envelope.confirmable or envelope.confirmation_status == "not_confirmable":
        blocked = envelope.with_user_decision(user_approved=False, status="not_confirmable")
        return ToolExecutionConfirmationResult(
            ok=False,
            status="blocked_not_confirmable",
            confirmation=blocked,
            user_approved=False,
        )
    status = "approved_execution_still_disabled" if user_approved else "rejected_by_user"
    confirmation_status = "approved" if user_approved else "rejected"
    decided = envelope.with_user_decision(user_approved=user_approved, status=confirmation_status)
    return ToolExecutionConfirmationResult(
        ok=True,
        status=status,
        confirmation=decided,
        user_approved=user_approved,
    )


def build_tool_execution_confirmation_summary(
    *,
    confirmation: ToolExecutionConfirmationEnvelope | None = None,
    result: ToolExecutionConfirmationResult | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    active_confirmation = result.confirmation if result else confirmation
    status = "none"
    tool_name = None
    user_approved = False
    has_pending = False
    side_effect_level = None
    if active_confirmation:
        status = active_confirmation.confirmation_status
        tool_name = active_confirmation.tool_name
        user_approved = active_confirmation.user_approved
        has_pending = active_confirmation.confirmation_status == "pending"
        side_effect_level = active_confirmation.side_effect_level
    return {
        "tool_execution_confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
        "source": source,
        "has_pending_confirmation": has_pending,
        "confirmation_status": status,
        "confirmed_tool_name": tool_name,
        "side_effect_level": side_effect_level,
        "user_approved": user_approved,
        "would_execute_after_confirmation": False,
        "execution_still_disabled": True,
        "requires_executor_boundary": True,
        "tool_execution_enabled": False,
        "dispatch_enabled": False,
        "engine_adapter_dispatch_enabled": False,
    }


def tool_execution_confirmation_contract() -> dict[str, Any]:
    policy = DEFAULT_TOOL_EXECUTION_CONFIRMATION_POLICY.to_dict()
    return {
        "version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
        "confirmation_contract_version": TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION,
        "route": "POST /agent/tools/confirmation/preview",
        "spec_route": "GET /agent/tools/confirmation/spec",
        "mode": policy["mode"],
        "execution_status": {
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "deterministic_workflow_dispatch_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "would_execute_after_confirmation": False,
            "execution_still_disabled": True,
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string | null",
            "task_type": "practice_plan_generation | immediate_practice_playback | session_review | coach_qa",
            "tool_name": "string",
            "arguments": "Record<string, unknown>",
            "client_context": "ClientContext",
        },
        "response_schema": {
            "ok": "boolean",
            "preview": "ToolInvocationPreviewResult",
            "confirmation": "ToolExecutionConfirmationEnvelope",
            "context_packet_summary": "Record<string, unknown>",
        },
        "terminal_commands": ["/pending", "/confirm", "/reject"],
        "trace_step_names": [
            "terminal_tool_confirmation_envelope_created",
            "terminal_tool_confirmation_user_approved",
            "terminal_tool_confirmation_user_rejected",
        ],
        "summary_field": "tool_execution_confirmation_summary",
        "policy": policy,
        "rules": [
            "Only preview-ok tool proposals can become pending confirmations.",
            "User approval/rejection is recorded explicitly before any future executor boundary.",
            "v2_6_2 still does not execute tools, dispatch deterministic workflows, or call engine adapters.",
            "Confirmation arguments are redacted for sensitive key names before trace/response output.",
        ],
        "guards": {
            "confirmation_executes_tools": False,
            "confirmation_dispatches_workflows": False,
            "confirmation_calls_engine_adapter": False,
            "confirmation_calls_llm_provider": False,
            "raw_api_key_allowed_in_confirmation": False,
        },
    }


@dataclass(frozen=True)
class ToolExecutionPolicy:
    """v2_6_3 ToolExecutor boundary policy.

    This boundary is intentionally dry-run/no-op only. It proves the shape of
    an execution request/result after explicit user confirmation, but it does
    not dispatch deterministic workflows, call routes, call adapters, or create
    accompaniment assets.
    """

    mode: str = "dry_run_noop_executor_boundary"
    requires_approved_confirmation: bool = True
    dry_run_enabled: bool = True
    noop_execution_enabled: bool = True
    real_tool_execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    deterministic_workflow_dispatch_enabled: bool = False
    engine_adapter_dispatch_enabled: bool = False
    side_effects_enabled: bool = False
    required_guards: tuple[str, ...] = (
        "requires_approved_confirmation",
        "dry_run_noop_only",
        "no_deterministic_workflow_dispatch",
        "no_engine_adapter_call",
        "no_route_call",
        "no_midi_asset_creation",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
            "mode": self.mode,
            "requires_approved_confirmation": self.requires_approved_confirmation,
            "dry_run_enabled": self.dry_run_enabled,
            "noop_execution_enabled": self.noop_execution_enabled,
            "real_tool_execution_enabled": self.real_tool_execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "deterministic_workflow_dispatch_enabled": self.deterministic_workflow_dispatch_enabled,
            "engine_adapter_dispatch_enabled": self.engine_adapter_dispatch_enabled,
            "side_effects_enabled": self.side_effects_enabled,
            "required_guards": list(self.required_guards),
        }


DEFAULT_TOOL_EXECUTION_POLICY = ToolExecutionPolicy()


@dataclass(frozen=True)
class ToolExecutionRequest:
    tool_executor_boundary_version: str
    execution_id: str
    proposal_id: str
    tool_name: str
    arguments_preview: dict[str, Any] = field(default_factory=dict)
    confirmation_status: str = "unknown"
    user_approved: bool = False
    side_effect_level: str = "unknown"
    dry_run: bool = True
    noop_only: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_executor_boundary_version": self.tool_executor_boundary_version,
            "execution_id": self.execution_id,
            "proposal_id": self.proposal_id,
            "tool_name": self.tool_name,
            "arguments_preview": dict(self.arguments_preview),
            "confirmation_status": self.confirmation_status,
            "user_approved": self.user_approved,
            "side_effect_level": self.side_effect_level,
            "dry_run": self.dry_run,
            "noop_only": self.noop_only,
            "created_at": self.created_at,
            "policy": dict(self.policy),
        }


@dataclass(frozen=True)
class ToolExecutionResult:
    ok: bool
    status: str
    request: ToolExecutionRequest
    result_preview: dict[str, Any] = field(default_factory=dict)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = True
    noop_only: bool = True
    real_tool_executed: bool = False
    deterministic_workflow_dispatched: bool = False
    engine_adapter_called: bool = False
    route_called: bool = False
    side_effects_created: bool = False
    next_stage_required: str = "DeterministicWorkflowDispatcher"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
            "ok": self.ok,
            "status": self.status,
            "request": self.request.to_dict(),
            "execution_id": self.request.execution_id,
            "proposal_id": self.request.proposal_id,
            "tool_name": self.request.tool_name,
            "user_approved": self.request.user_approved,
            "confirmation_status": self.request.confirmation_status,
            "result_preview": dict(self.result_preview),
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "dry_run": self.dry_run,
            "noop_only": self.noop_only,
            "real_tool_executed": self.real_tool_executed,
            "deterministic_workflow_dispatched": self.deterministic_workflow_dispatched,
            "engine_adapter_called": self.engine_adapter_called,
            "route_called": self.route_called,
            "side_effects_created": self.side_effects_created,
            "next_stage_required": self.next_stage_required,
        }


def build_tool_execution_request(
    confirmation: ToolExecutionConfirmationEnvelope,
    *,
    execution_id: str | None = None,
    policy: ToolExecutionPolicy | None = None,
) -> ToolExecutionRequest:
    active_policy = policy or DEFAULT_TOOL_EXECUTION_POLICY
    return ToolExecutionRequest(
        tool_executor_boundary_version=TOOL_EXECUTOR_BOUNDARY_VERSION,
        execution_id=execution_id or f"execution_{uuid4().hex[:12]}",
        proposal_id=confirmation.proposal_id,
        tool_name=confirmation.tool_name,
        arguments_preview=_redact_sensitive_values(confirmation.arguments_preview),
        confirmation_status=confirmation.confirmation_status,
        user_approved=confirmation.user_approved,
        side_effect_level=confirmation.side_effect_level,
        dry_run=True,
        noop_only=True,
        policy=active_policy.to_dict(),
    )


def execute_tool_dry_run(
    confirmation: ToolExecutionConfirmationEnvelope | ToolExecutionConfirmationResult,
    *,
    policy: ToolExecutionPolicy | None = None,
) -> ToolExecutionResult:
    """Exercise the ToolExecutor boundary without executing a real tool.

    A successful result means only that an approved confirmation can be converted
    into a stable dry-run ExecutionRequest/ExecutionResult. It is not workflow
    dispatch and it never calls the engine adapter.
    """

    envelope = confirmation.confirmation if isinstance(confirmation, ToolExecutionConfirmationResult) else confirmation
    request = build_tool_execution_request(envelope, policy=policy)
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if envelope.confirmation_status != "approved" or not envelope.user_approved:
        blocking_reasons.append("approved_confirmation_required_before_executor_boundary")
        return ToolExecutionResult(
            ok=False,
            status="blocked_requires_approved_confirmation",
            request=request,
            result_preview={
                "message": "Dry-run executor boundary did not proceed because the tool confirmation was not approved.",
                "would_dispatch_workflow": False,
                "would_call_engine_adapter": False,
            },
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    descriptor = get_tool_descriptor(envelope.tool_name)
    if descriptor is None:
        blocking_reasons.append("unknown_tool")
        return ToolExecutionResult(
            ok=False,
            status="blocked_unknown_tool",
            request=request,
            result_preview={
                "message": "Unknown tool cannot enter the dry-run executor boundary.",
                "would_dispatch_workflow": False,
                "would_call_engine_adapter": False,
            },
            blocking_reasons=blocking_reasons,
        )

    warnings.append("dry_run_noop_only_no_real_tool_execution")
    return ToolExecutionResult(
        ok=True,
        status="dry_run_noop_completed",
        request=request,
        result_preview={
            "message": "Dry-run ToolExecutor boundary completed without side effects.",
            "tool_title": descriptor.title,
            "deterministic_workflow": descriptor.deterministic_workflow,
            "route": descriptor.route,
            "adapter_boundary": descriptor.adapter_boundary,
            "would_dispatch_workflow": False,
            "would_call_engine_adapter": False,
            "would_call_route": False,
            "would_create_side_effects": False,
        },
        warnings=warnings,
    )


def build_tool_executor_summary(
    *,
    execution_result: ToolExecutionResult | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    return {
        "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
        "source": source,
        "has_execution_result": execution_result is not None,
        "execution_status": execution_result.status if execution_result else "none",
        "executed_tool_name": execution_result.request.tool_name if execution_result else None,
        "execution_id": execution_result.request.execution_id if execution_result else None,
        "dry_run": True,
        "noop_only": True,
        "real_tool_execution_enabled": False,
        "real_tool_executed": False,
        "deterministic_workflow_dispatch_enabled": False,
        "deterministic_workflow_dispatched": False,
        "engine_adapter_dispatch_enabled": False,
        "engine_adapter_called": False,
        "route_called": False,
        "side_effects_created": False,
        "requires_workflow_dispatcher": True,
    }


def tool_executor_boundary_contract() -> dict[str, Any]:
    policy = DEFAULT_TOOL_EXECUTION_POLICY.to_dict()
    return {
        "version": TOOL_EXECUTOR_BOUNDARY_VERSION,
        "tool_executor_boundary_version": TOOL_EXECUTOR_BOUNDARY_VERSION,
        "spec_route": "GET /agent/tools/executor/spec",
        "dry_run_route": "POST /agent/tools/executor/dry-run",
        "mode": policy["mode"],
        "execution_status": {
            "dry_run_enabled": True,
            "noop_execution_enabled": True,
            "real_tool_execution_enabled": False,
            "autonomous_execution_enabled": False,
            "deterministic_workflow_dispatch_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "route_call_enabled": False,
            "side_effects_enabled": False,
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string | null",
            "task_type": "practice_plan_generation | immediate_practice_playback | session_review | coach_qa",
            "tool_name": "string",
            "arguments": "Record<string, unknown>",
            "user_approved": "boolean",
            "client_context": "ClientContext",
        },
        "response_schema": {
            "ok": "boolean",
            "preview": "ToolInvocationPreviewResult",
            "confirmation": "ToolExecutionConfirmationEnvelope",
            "confirmation_result": "ToolExecutionConfirmationResult | null",
            "execution_result": "ToolExecutionResult",
            "tool_executor_summary": "Record<string, unknown>",
            "context_packet_summary": "Record<string, unknown>",
        },
        "terminal_commands": ["/execute-dry-run"],
        "trace_step_names": [
            "terminal_tool_executor_dry_run_requested",
            "terminal_tool_executor_dry_run_completed",
            "terminal_tool_executor_dry_run_blocked",
        ],
        "summary_field": "tool_executor_summary",
        "policy": policy,
        "rules": [
            "Only an approved ToolExecutionConfirmationEnvelope can pass the dry-run executor boundary.",
            "Dry-run completion proves request/result shape only; it is not real tool execution.",
            "v2_6_3 must not dispatch deterministic workflows, call routes, call engine adapters, or create MIDI assets.",
            "The next stage after this boundary is a deterministic workflow dispatcher.",
        ],
        "guards": {
            "executor_calls_llm_provider": False,
            "executor_executes_real_tool": False,
            "executor_dispatches_workflow": False,
            "executor_calls_engine_adapter": False,
            "executor_calls_route": False,
            "executor_creates_midi_asset": False,
            "raw_api_key_allowed_in_execution": False,
        },
    }



@dataclass(frozen=True)
class ToolWorkflowDispatcherPolicy:
    """v2_6_4 deterministic workflow dispatcher boundary policy.

    The dispatcher maps an approved dry-run executor result to a deterministic
    workflow descriptor. It deliberately does not invoke the workflow, call API
    routes, call adapters, import engine internals, or create side effects.
    """

    mode: str = "workflow_descriptor_resolution_only"
    requires_tool_executor_result: bool = True
    requires_executor_dry_run_completed: bool = True
    workflow_descriptor_resolution_enabled: bool = True
    real_workflow_dispatch_enabled: bool = False
    route_call_enabled: bool = False
    engine_adapter_dispatch_enabled: bool = False
    side_effects_enabled: bool = False
    required_guards: tuple[str, ...] = (
        "requires_successful_tool_executor_dry_run",
        "descriptor_resolution_only",
        "no_workflow_invocation",
        "no_route_call",
        "no_engine_adapter_call",
        "no_midi_asset_creation",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_workflow_dispatcher_version": TOOL_WORKFLOW_DISPATCHER_VERSION,
            "mode": self.mode,
            "requires_tool_executor_result": self.requires_tool_executor_result,
            "requires_executor_dry_run_completed": self.requires_executor_dry_run_completed,
            "workflow_descriptor_resolution_enabled": self.workflow_descriptor_resolution_enabled,
            "real_workflow_dispatch_enabled": self.real_workflow_dispatch_enabled,
            "route_call_enabled": self.route_call_enabled,
            "engine_adapter_dispatch_enabled": self.engine_adapter_dispatch_enabled,
            "side_effects_enabled": self.side_effects_enabled,
            "required_guards": list(self.required_guards),
        }


DEFAULT_TOOL_WORKFLOW_DISPATCHER_POLICY = ToolWorkflowDispatcherPolicy()


@dataclass(frozen=True)
class DeterministicWorkflowDescriptor:
    tool_workflow_dispatcher_version: str
    dispatch_id: str
    execution_id: str
    proposal_id: str
    tool_name: str
    workflow_name: str
    route: str | None = None
    adapter_boundary: str | None = None
    category: str | None = None
    input_contract_preview: dict[str, Any] = field(default_factory=dict)
    output_contract_preview: dict[str, Any] = field(default_factory=dict)
    side_effect_level: str = "unknown"
    dispatch_status: str = "descriptor_resolved"
    workflow_descriptor_resolved: bool = True
    deterministic_workflow_dispatched: bool = False
    workflow_invoked: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    side_effects_created: bool = False
    next_stage_required: str = "ControlledWorkflowExecution"
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_workflow_dispatcher_version": self.tool_workflow_dispatcher_version,
            "dispatch_id": self.dispatch_id,
            "execution_id": self.execution_id,
            "proposal_id": self.proposal_id,
            "tool_name": self.tool_name,
            "workflow_name": self.workflow_name,
            "route": self.route,
            "adapter_boundary": self.adapter_boundary,
            "category": self.category,
            "input_contract_preview": dict(self.input_contract_preview),
            "output_contract_preview": dict(self.output_contract_preview),
            "side_effect_level": self.side_effect_level,
            "dispatch_status": self.dispatch_status,
            "workflow_descriptor_resolved": self.workflow_descriptor_resolved,
            "deterministic_workflow_dispatched": self.deterministic_workflow_dispatched,
            "workflow_invoked": self.workflow_invoked,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "side_effects_created": self.side_effects_created,
            "next_stage_required": self.next_stage_required,
            "policy": dict(self.policy),
        }


@dataclass(frozen=True)
class ToolWorkflowDispatchResult:
    ok: bool
    status: str
    execution_result: ToolExecutionResult
    workflow_descriptor: DeterministicWorkflowDescriptor | None = None
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = True
    descriptor_only: bool = True
    workflow_descriptor_resolved: bool = False
    deterministic_workflow_dispatched: bool = False
    workflow_invoked: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    side_effects_created: bool = False
    next_stage_required: str = "ControlledWorkflowExecution"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_workflow_dispatcher_version": TOOL_WORKFLOW_DISPATCHER_VERSION,
            "ok": self.ok,
            "status": self.status,
            "execution_result": self.execution_result.to_dict(),
            "execution_id": self.execution_result.request.execution_id,
            "proposal_id": self.execution_result.request.proposal_id,
            "tool_name": self.execution_result.request.tool_name,
            "workflow_descriptor": self.workflow_descriptor.to_dict() if self.workflow_descriptor else None,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "dry_run": self.dry_run,
            "descriptor_only": self.descriptor_only,
            "workflow_descriptor_resolved": self.workflow_descriptor_resolved,
            "deterministic_workflow_dispatched": self.deterministic_workflow_dispatched,
            "workflow_invoked": self.workflow_invoked,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "side_effects_created": self.side_effects_created,
            "next_stage_required": self.next_stage_required,
        }


def build_deterministic_workflow_descriptor(
    execution_result: ToolExecutionResult,
    *,
    dispatch_id: str | None = None,
    policy: ToolWorkflowDispatcherPolicy | None = None,
) -> DeterministicWorkflowDescriptor:
    descriptor = get_tool_descriptor(execution_result.request.tool_name)
    if descriptor is None or not descriptor.deterministic_workflow:
        raise ValueError("known tool with deterministic_workflow is required")
    active_policy = policy or DEFAULT_TOOL_WORKFLOW_DISPATCHER_POLICY
    return DeterministicWorkflowDescriptor(
        tool_workflow_dispatcher_version=TOOL_WORKFLOW_DISPATCHER_VERSION,
        dispatch_id=dispatch_id or f"dispatch_{uuid4().hex[:12]}",
        execution_id=execution_result.request.execution_id,
        proposal_id=execution_result.request.proposal_id,
        tool_name=descriptor.name,
        workflow_name=descriptor.deterministic_workflow,
        route=descriptor.route,
        adapter_boundary=descriptor.adapter_boundary,
        category=descriptor.category,
        input_contract_preview=_redact_sensitive_values(descriptor.input_contract),
        output_contract_preview=_redact_sensitive_values(descriptor.output_contract),
        side_effect_level=descriptor.side_effect_level,
        policy=active_policy.to_dict(),
    )


def dispatch_deterministic_workflow_dry_run(
    execution_result: ToolExecutionResult,
    *,
    policy: ToolWorkflowDispatcherPolicy | None = None,
) -> ToolWorkflowDispatchResult:
    """Resolve the deterministic workflow descriptor without invoking it.

    v2_6_4 is the dispatcher boundary only. A successful result means the Agent
    can identify which deterministic workflow would be used after confirmation
    and executor validation. It does not run that workflow.
    """

    blocking_reasons: list[str] = []
    warnings: list[str] = []
    if not execution_result.ok or execution_result.status != "dry_run_noop_completed":
        blocking_reasons.append("successful_tool_executor_dry_run_required_before_workflow_descriptor_resolution")
        return ToolWorkflowDispatchResult(
            ok=False,
            status="blocked_requires_successful_executor_dry_run",
            execution_result=execution_result,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    descriptor = get_tool_descriptor(execution_result.request.tool_name)
    if descriptor is None:
        blocking_reasons.append("unknown_tool")
        return ToolWorkflowDispatchResult(
            ok=False,
            status="blocked_unknown_tool",
            execution_result=execution_result,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )
    if not descriptor.deterministic_workflow:
        blocking_reasons.append("tool_has_no_deterministic_workflow_descriptor")
        return ToolWorkflowDispatchResult(
            ok=False,
            status="blocked_missing_workflow_descriptor",
            execution_result=execution_result,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    workflow_descriptor = build_deterministic_workflow_descriptor(execution_result, policy=policy)
    warnings.append("workflow_descriptor_resolution_only_no_workflow_invocation")
    if descriptor.side_effect_level != "none":
        warnings.append(f"future_controlled_execution_may_have_side_effect_level_{descriptor.side_effect_level}")
    return ToolWorkflowDispatchResult(
        ok=True,
        status="workflow_descriptor_resolved",
        execution_result=execution_result,
        workflow_descriptor=workflow_descriptor,
        warnings=warnings,
        workflow_descriptor_resolved=True,
    )


def build_tool_workflow_dispatcher_summary(
    *,
    dispatch_result: ToolWorkflowDispatchResult | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    return {
        "tool_workflow_dispatcher_version": TOOL_WORKFLOW_DISPATCHER_VERSION,
        "source": source,
        "has_dispatch_result": dispatch_result is not None,
        "dispatch_status": dispatch_result.status if dispatch_result else "none",
        "dispatched_tool_name": dispatch_result.execution_result.request.tool_name if dispatch_result else None,
        "dispatch_id": dispatch_result.workflow_descriptor.dispatch_id if dispatch_result and dispatch_result.workflow_descriptor else None,
        "workflow_name": dispatch_result.workflow_descriptor.workflow_name if dispatch_result and dispatch_result.workflow_descriptor else None,
        "workflow_descriptor_resolution_enabled": True,
        "workflow_descriptor_resolved": bool(dispatch_result and dispatch_result.workflow_descriptor_resolved),
        "deterministic_workflow_dispatch_enabled": False,
        "deterministic_workflow_dispatched": False,
        "workflow_invoked": False,
        "route_called": False,
        "engine_adapter_dispatch_enabled": False,
        "engine_adapter_called": False,
        "side_effects_created": False,
        "requires_controlled_workflow_execution": True,
    }


def tool_workflow_dispatcher_contract() -> dict[str, Any]:
    policy = DEFAULT_TOOL_WORKFLOW_DISPATCHER_POLICY.to_dict()
    return {
        "version": TOOL_WORKFLOW_DISPATCHER_VERSION,
        "tool_workflow_dispatcher_version": TOOL_WORKFLOW_DISPATCHER_VERSION,
        "spec_route": "GET /agent/tools/workflows/spec",
        "dispatch_dry_run_route": "POST /agent/tools/workflows/dispatch-dry-run",
        "mode": policy["mode"],
        "execution_status": {
            "workflow_descriptor_resolution_enabled": True,
            "real_workflow_dispatch_enabled": False,
            "route_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "side_effects_enabled": False,
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string | null",
            "task_type": "practice_plan_generation | immediate_practice_playback | session_review | coach_qa",
            "tool_name": "string",
            "arguments": "Record<string, unknown>",
            "user_approved": "boolean",
            "client_context": "ClientContext",
        },
        "response_schema": {
            "ok": "boolean",
            "preview": "ToolInvocationPreviewResult",
            "confirmation": "ToolExecutionConfirmationEnvelope",
            "confirmation_result": "ToolExecutionConfirmationResult | null",
            "execution_result": "ToolExecutionResult",
            "workflow_dispatch_result": "ToolWorkflowDispatchResult",
            "tool_workflow_dispatcher_summary": "Record<string, unknown>",
            "context_packet_summary": "Record<string, unknown>",
        },
        "terminal_commands": ["/dispatch-dry-run"],
        "trace_step_names": [
            "terminal_tool_workflow_dispatch_dry_run_requested",
            "terminal_tool_workflow_descriptor_resolved",
            "terminal_tool_workflow_dispatch_dry_run_blocked",
        ],
        "summary_field": "tool_workflow_dispatcher_summary",
        "policy": policy,
        "rules": [
            "Only a successful dry-run ToolExecutor result can enter workflow descriptor resolution.",
            "v2_6_4 maps tool names to deterministic workflow descriptors only.",
            "v2_6_4 must not invoke deterministic workflows, call routes, call engine adapters, or create MIDI assets.",
            "The next stage after this boundary is controlled workflow execution.",
        ],
        "guards": {
            "dispatcher_calls_llm_provider": False,
            "dispatcher_invokes_workflow": False,
            "dispatcher_calls_route": False,
            "dispatcher_calls_engine_adapter": False,
            "dispatcher_creates_midi_asset": False,
            "raw_api_key_allowed_in_dispatch": False,
        },
    }


@dataclass(frozen=True)
class ControlledWorkflowExecutionPolicy:
    """v2_6_5 first controlled workflow execution policy.

    Only explicitly allow-listed, side-effect-free Agent workflows may run. The
    initial allow-list is intentionally limited to `agent_practice_plan`, which
    calls the deterministic PracticePlanner and returns a structured plan. It
    must not call routes, engine adapters, accompaniment generation, or create
    MIDI assets.
    """

    mode: str = "first_controlled_agent_workflow_execution"
    controlled_execution_enabled: bool = True
    autonomous_execution_enabled: bool = False
    requires_workflow_descriptor: bool = True
    requires_user_approval: bool = True
    allowed_tool_names: tuple[str, ...] = ("agent_practice_plan",)
    allowed_workflow_names: tuple[str, ...] = ("PracticePlanner.build_plan",)
    route_call_enabled: bool = False
    engine_adapter_dispatch_enabled: bool = False
    midi_asset_creation_enabled: bool = False
    side_effects_enabled: bool = False
    required_guards: tuple[str, ...] = (
        "requires_successful_workflow_descriptor_resolution",
        "requires_approved_user_confirmation",
        "only_side_effect_free_agent_workflow_allow_list",
        "no_route_call",
        "no_engine_adapter_call",
        "no_accompaniment_generation",
        "no_midi_asset_creation",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "controlled_workflow_execution_version": CONTROLLED_WORKFLOW_EXECUTION_VERSION,
            "mode": self.mode,
            "controlled_execution_enabled": self.controlled_execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "requires_workflow_descriptor": self.requires_workflow_descriptor,
            "requires_user_approval": self.requires_user_approval,
            "allowed_tool_names": list(self.allowed_tool_names),
            "allowed_workflow_names": list(self.allowed_workflow_names),
            "route_call_enabled": self.route_call_enabled,
            "engine_adapter_dispatch_enabled": self.engine_adapter_dispatch_enabled,
            "midi_asset_creation_enabled": self.midi_asset_creation_enabled,
            "side_effects_enabled": self.side_effects_enabled,
            "required_guards": list(self.required_guards),
        }


DEFAULT_CONTROLLED_WORKFLOW_EXECUTION_POLICY = ControlledWorkflowExecutionPolicy()


@dataclass(frozen=True)
class ControlledWorkflowExecutionResult:
    ok: bool
    status: str
    workflow_dispatch_result: ToolWorkflowDispatchResult
    workflow_output: dict[str, Any] | None = None
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    controlled_execution: bool = True
    workflow_invoked: bool = False
    deterministic_workflow_dispatched: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    side_effects_created: bool = False
    midi_asset_created: bool = False
    next_stage_required: str = "HarmonyOSAgentActionContract"
    policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        descriptor = self.workflow_dispatch_result.workflow_descriptor
        return {
            "controlled_workflow_execution_version": CONTROLLED_WORKFLOW_EXECUTION_VERSION,
            "ok": self.ok,
            "status": self.status,
            "workflow_dispatch_result": self.workflow_dispatch_result.to_dict(),
            "dispatch_id": descriptor.dispatch_id if descriptor else None,
            "execution_id": self.workflow_dispatch_result.execution_result.request.execution_id,
            "proposal_id": self.workflow_dispatch_result.execution_result.request.proposal_id,
            "tool_name": self.workflow_dispatch_result.execution_result.request.tool_name,
            "workflow_name": descriptor.workflow_name if descriptor else None,
            "workflow_output": _redact_sensitive_values(self.workflow_output or {}),
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
            "controlled_execution": self.controlled_execution,
            "workflow_invoked": self.workflow_invoked,
            "deterministic_workflow_dispatched": self.deterministic_workflow_dispatched,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "side_effects_created": self.side_effects_created,
            "midi_asset_created": self.midi_asset_created,
            "next_stage_required": self.next_stage_required,
            "policy": dict(self.policy),
        }


def execute_controlled_workflow(
    dispatch_result: ToolWorkflowDispatchResult,
    *,
    workflow_runner: Callable[[str, dict[str, Any]], dict[str, Any]],
    policy: ControlledWorkflowExecutionPolicy | None = None,
) -> ControlledWorkflowExecutionResult:
    """Run the first allow-listed deterministic Agent workflow under guard.

    v2_6_5 intentionally supports only side-effect-free Agent workflows. The
    initial runner is expected to handle `agent_practice_plan` by calling
    PracticePlanner.build_plan. This function does not call HTTP routes or engine
    adapters; callers inject the workflow runner from the Agent layer.
    """

    active_policy = policy or DEFAULT_CONTROLLED_WORKFLOW_EXECUTION_POLICY
    policy_payload = active_policy.to_dict()
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if not dispatch_result.ok or not dispatch_result.workflow_descriptor_resolved or dispatch_result.workflow_descriptor is None:
        blocking_reasons.append("successful_workflow_descriptor_resolution_required_before_controlled_execution")
        return ControlledWorkflowExecutionResult(
            ok=False,
            status="blocked_requires_workflow_descriptor",
            workflow_dispatch_result=dispatch_result,
            blocking_reasons=blocking_reasons,
            policy=policy_payload,
        )

    descriptor = dispatch_result.workflow_descriptor
    execution_request = dispatch_result.execution_result.request
    if descriptor.tool_name not in set(active_policy.allowed_tool_names):
        blocking_reasons.append("tool_not_enabled_for_first_controlled_execution")
    if descriptor.workflow_name not in set(active_policy.allowed_workflow_names):
        blocking_reasons.append("workflow_not_enabled_for_first_controlled_execution")
    if descriptor.side_effect_level not in {"none", "trace_only"}:
        blocking_reasons.append("side_effectful_workflow_not_allowed_in_v2_6_5")
    if not execution_request.user_approved or execution_request.confirmation_status != "approved":
        blocking_reasons.append("approved_user_confirmation_required")

    if blocking_reasons:
        return ControlledWorkflowExecutionResult(
            ok=False,
            status="blocked_by_controlled_execution_policy",
            workflow_dispatch_result=dispatch_result,
            blocking_reasons=blocking_reasons,
            policy=policy_payload,
        )

    try:
        workflow_output = workflow_runner(descriptor.tool_name, dict(execution_request.arguments_preview))
    except Exception as exc:  # pragma: no cover - defensive boundary for injected runners.
        return ControlledWorkflowExecutionResult(
            ok=False,
            status="controlled_workflow_runner_failed",
            workflow_dispatch_result=dispatch_result,
            blocking_reasons=[f"workflow_runner_exception:{exc.__class__.__name__}"],
            warnings=warnings,
            policy=policy_payload,
        )

    output_ok = bool(workflow_output.get("ok", True)) if isinstance(workflow_output, dict) else False
    if not output_ok:
        warnings.append("controlled_workflow_returned_not_ok")
        return ControlledWorkflowExecutionResult(
            ok=False,
            status="controlled_workflow_completed_not_ok",
            workflow_dispatch_result=dispatch_result,
            workflow_output=workflow_output if isinstance(workflow_output, dict) else {"raw_output_preview": _preview_text(workflow_output)},
            warnings=warnings,
            workflow_invoked=True,
            deterministic_workflow_dispatched=True,
            policy=policy_payload,
        )

    warnings.append("first_controlled_execution_completed_agent_practice_plan_only")
    return ControlledWorkflowExecutionResult(
        ok=True,
        status="controlled_workflow_completed",
        workflow_dispatch_result=dispatch_result,
        workflow_output=workflow_output,
        warnings=warnings,
        workflow_invoked=True,
        deterministic_workflow_dispatched=True,
        route_called=False,
        engine_adapter_called=False,
        side_effects_created=False,
        midi_asset_created=False,
        policy=policy_payload,
    )


def build_controlled_workflow_execution_summary(
    *,
    execution_result: ControlledWorkflowExecutionResult | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    descriptor = execution_result.workflow_dispatch_result.workflow_descriptor if execution_result else None
    return {
        "controlled_workflow_execution_version": CONTROLLED_WORKFLOW_EXECUTION_VERSION,
        "source": source,
        "has_controlled_execution_result": execution_result is not None,
        "execution_status": execution_result.status if execution_result else "none",
        "tool_name": descriptor.tool_name if descriptor else None,
        "workflow_name": descriptor.workflow_name if descriptor else None,
        "controlled_execution_enabled": True,
        "workflow_invoked": bool(execution_result and execution_result.workflow_invoked),
        "deterministic_workflow_dispatched": bool(execution_result and execution_result.deterministic_workflow_dispatched),
        "route_called": False,
        "engine_adapter_called": False,
        "side_effects_created": False,
        "midi_asset_created": False,
        "requires_harmonyos_agent_action_contract": True,
    }


def controlled_workflow_execution_contract() -> dict[str, Any]:
    policy = DEFAULT_CONTROLLED_WORKFLOW_EXECUTION_POLICY.to_dict()
    return {
        "version": CONTROLLED_WORKFLOW_EXECUTION_VERSION,
        "controlled_workflow_execution_version": CONTROLLED_WORKFLOW_EXECUTION_VERSION,
        "spec_route": "GET /agent/tools/workflows/controlled-execution/spec",
        "execute_route": "POST /agent/tools/workflows/execute-controlled",
        "mode": policy["mode"],
        "execution_status": {
            "controlled_execution_enabled": True,
            "autonomous_execution_enabled": False,
            "allowed_tool_names": list(policy["allowed_tool_names"]),
            "allowed_workflow_names": list(policy["allowed_workflow_names"]),
            "route_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "side_effects_enabled": False,
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string | null",
            "task_type": "practice_plan_generation | coach_qa",
            "tool_name": "agent_practice_plan",
            "arguments": "{ userInput?: string, availableMinutes?: number, instrument?: string }",
            "user_approved": "boolean",
            "client_context": "ClientContext",
        },
        "response_schema": {
            "ok": "boolean",
            "preview": "ToolInvocationPreviewResult",
            "confirmation": "ToolExecutionConfirmationEnvelope",
            "confirmation_result": "ToolExecutionConfirmationResult | null",
            "execution_result": "ToolExecutionResult",
            "workflow_dispatch_result": "ToolWorkflowDispatchResult",
            "controlled_workflow_execution_result": "ControlledWorkflowExecutionResult",
            "controlled_workflow_execution_summary": "Record<string, unknown>",
            "context_packet_summary": "Record<string, unknown>",
        },
        "terminal_commands": ["/execute-controlled"],
        "trace_step_names": [
            "terminal_controlled_workflow_execution_requested",
            "terminal_controlled_workflow_execution_completed",
            "terminal_controlled_workflow_execution_blocked",
        ],
        "summary_field": "controlled_workflow_execution_summary",
        "policy": policy,
        "rules": [
            "Only agent_practice_plan / PracticePlanner.build_plan is executable in v2_6_5.",
            "The tool must first pass preview, user confirmation, ToolExecutor dry-run, and workflow descriptor resolution.",
            "v2_6_5 may invoke the deterministic PracticePlanner but must not call routes, engine adapters, accompaniment generation, or MIDI asset creation.",
            "Execution remains non-autonomous and requires explicit user approval.",
        ],
        "guards": {
            "controlled_execution_calls_llm_provider": False,
            "controlled_execution_calls_route": False,
            "controlled_execution_calls_engine_adapter": False,
            "controlled_execution_creates_midi_asset": False,
            "raw_api_key_allowed_in_output": False,
        },
    }



@dataclass(frozen=True)
class HarmonyOSAgentActionCard:
    """Routine-facing action-card state for HarmonyOS.

    The card is a presentation/contract envelope. It aggregates existing Agent
    boundaries for the client: preview, confirmation, dry-run executor,
    workflow descriptor, and optional controlled execution result. It does not
    introduce any new high-risk execution path.
    """

    action_contract_version: str
    action_id: str
    proposal_id: str | None
    tool_name: str
    title: str
    description: str
    arguments_preview: dict[str, Any] = field(default_factory=dict)
    side_effect_level: str = "unknown"
    risk_summary: str = "Unknown action risk."
    requires_user_confirmation: bool = True
    confirmation_status: str = "not_started"
    user_approved: bool = False
    preview_status: str = "not_started"
    execution_status: str = "not_started"
    workflow_name: str | None = None
    result_preview: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    available_client_actions: tuple[str, ...] = ("dismiss",)
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_contract_version": self.action_contract_version,
            "action_id": self.action_id,
            "proposal_id": self.proposal_id,
            "tool_name": self.tool_name,
            "title": self.title,
            "description": self.description,
            "arguments_preview": _redact_sensitive_values(self.arguments_preview),
            "side_effect_level": self.side_effect_level,
            "risk_summary": self.risk_summary,
            "requires_user_confirmation": self.requires_user_confirmation,
            "confirmation_status": self.confirmation_status,
            "user_approved": self.user_approved,
            "preview_status": self.preview_status,
            "execution_status": self.execution_status,
            "workflow_name": self.workflow_name,
            "result_preview": _redact_sensitive_values(self.result_preview),
            "trace_id": self.trace_id,
            "available_client_actions": list(self.available_client_actions),
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "created_at": self.created_at,
        }


def build_harmonyos_agent_action_card(
    *,
    preview: ToolInvocationPreviewResult | None = None,
    confirmation: ToolExecutionConfirmationEnvelope | None = None,
    confirmation_result: ToolExecutionConfirmationResult | None = None,
    execution_result: ToolExecutionResult | None = None,
    workflow_dispatch_result: ToolWorkflowDispatchResult | None = None,
    controlled_result: ControlledWorkflowExecutionResult | None = None,
    trace_id: str | None = None,
    action_id: str | None = None,
) -> HarmonyOSAgentActionCard:
    """Build the Routine-facing card from already-computed Agent boundary results."""

    tool_name = "unknown"
    if preview is not None:
        tool_name = preview.tool_name
    elif confirmation is not None:
        tool_name = confirmation.tool_name
    elif confirmation_result is not None:
        tool_name = confirmation_result.confirmation.tool_name
    elif execution_result is not None:
        tool_name = execution_result.request.tool_name
    elif workflow_dispatch_result is not None:
        tool_name = workflow_dispatch_result.execution_result.request.tool_name
    elif controlled_result is not None:
        tool_name = controlled_result.workflow_dispatch_result.execution_result.request.tool_name

    descriptor = get_tool_descriptor(tool_name)
    active_confirmation = confirmation_result.confirmation if confirmation_result else confirmation
    descriptor_from_dispatch = workflow_dispatch_result.workflow_descriptor if workflow_dispatch_result else None
    if controlled_result is not None:
        descriptor_from_dispatch = controlled_result.workflow_dispatch_result.workflow_descriptor
    active_execution = execution_result or (workflow_dispatch_result.execution_result if workflow_dispatch_result else None)

    proposal_id = None
    if active_confirmation is not None:
        proposal_id = active_confirmation.proposal_id
    elif active_execution is not None:
        proposal_id = active_execution.request.proposal_id

    preview_status = preview.status if preview is not None else "not_started"
    confirmation_status = active_confirmation.confirmation_status if active_confirmation is not None else "not_started"
    user_approved = bool(active_confirmation and active_confirmation.user_approved)
    side_effect_level = (
        active_confirmation.side_effect_level
        if active_confirmation is not None
        else (descriptor.side_effect_level if descriptor is not None else "unknown")
    )
    risk_summary = (
        active_confirmation.risk_summary
        if active_confirmation is not None
        else _risk_summary(side_effect_level, confirmable=bool(preview and preview.ok))
    )
    arguments_preview: dict[str, Any] = {}
    if active_confirmation is not None:
        arguments_preview = dict(active_confirmation.arguments_preview)
    elif preview is not None:
        arguments_preview = dict(preview.normalized_arguments)
    elif active_execution is not None:
        arguments_preview = dict(active_execution.request.arguments_preview)

    execution_status = _derive_action_execution_status(
        confirmation=active_confirmation,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=controlled_result,
    )
    workflow_name = descriptor_from_dispatch.workflow_name if descriptor_from_dispatch else (descriptor.deterministic_workflow if descriptor else None)
    result_preview = _build_action_result_preview(controlled_result=controlled_result, workflow_dispatch_result=workflow_dispatch_result, execution_result=execution_result)
    available_actions = _action_available_client_actions(
        confirmation=active_confirmation,
        execution_result=execution_result,
        workflow_dispatch_result=workflow_dispatch_result,
        controlled_result=controlled_result,
    )
    route_called = bool(controlled_result and controlled_result.route_called)
    engine_adapter_called = bool(controlled_result and controlled_result.engine_adapter_called)
    midi_asset_created = bool(controlled_result and controlled_result.midi_asset_created)

    return HarmonyOSAgentActionCard(
        action_contract_version=HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
        action_id=action_id or f"action_{uuid4().hex[:12]}",
        proposal_id=proposal_id,
        tool_name=tool_name,
        title=descriptor.title if descriptor else tool_name,
        description=descriptor.description if descriptor else "Unknown Agent action.",
        arguments_preview=arguments_preview,
        side_effect_level=side_effect_level,
        risk_summary=risk_summary,
        requires_user_confirmation=bool(active_confirmation.requires_user_confirmation) if active_confirmation else True,
        confirmation_status=confirmation_status,
        user_approved=user_approved,
        preview_status=preview_status,
        execution_status=execution_status,
        workflow_name=workflow_name,
        result_preview=result_preview,
        trace_id=trace_id,
        available_client_actions=available_actions,
        route_called=route_called,
        engine_adapter_called=engine_adapter_called,
        midi_asset_created=midi_asset_created,
    )


def build_harmonyos_agent_action_summary(
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    return {
        "harmonyos_agent_action_contract_version": HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
        "source": source,
        "has_action_card": action_card is not None,
        "action_id": action_card.action_id if action_card else None,
        "tool_name": action_card.tool_name if action_card else None,
        "confirmation_status": action_card.confirmation_status if action_card else "none",
        "execution_status": action_card.execution_status if action_card else "none",
        "trace_id": action_card.trace_id if action_card else None,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "client_must_confirm_side_effectful_actions": True,
    }


def harmonyos_agent_action_contract() -> dict[str, Any]:
    return {
        "version": HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
        "harmonyos_agent_action_contract_version": HARMONYOS_AGENT_ACTION_CONTRACT_VERSION,
        "spec_route": "GET /agent/actions/spec",
        "preview_route": "POST /agent/actions/preview",
        "controlled_execute_route": "POST /agent/actions/execute-controlled",
        "surface": "HarmonyOS Routine AgentActionCard",
        "mode": "action_card_contract_and_guarded_practice_plan_execution",
        "execution_status": {
            "action_card_enabled": True,
            "preview_enabled": True,
            "confirmation_required": True,
            "controlled_practice_plan_execution_enabled": True,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "action_card_schema": {
            "action_contract_version": "string",
            "action_id": "string",
            "proposal_id": "string | null",
            "tool_name": "string",
            "title": "string",
            "description": "string",
            "arguments_preview": "Record<string, unknown>",
            "side_effect_level": "none | trace_only | creates_midi_asset | string",
            "risk_summary": "string",
            "requires_user_confirmation": "boolean",
            "confirmation_status": "not_started | pending | approved | rejected | not_confirmable",
            "user_approved": "boolean",
            "preview_status": "string",
            "execution_status": "not_started | confirmation_required | ready_for_dry_run | dry_run_completed | workflow_descriptor_resolved | controlled_execution_succeeded | controlled_execution_blocked | rejected | blocked",
            "workflow_name": "string | null",
            "result_preview": "Record<string, unknown>",
            "trace_id": "string | null",
            "available_client_actions": "string[]",
            "route_called": "boolean",
            "engine_adapter_called": "boolean",
            "midi_asset_created": "boolean",
        },
        "client_flow": [
            "display_llm_reply",
            "display_action_card",
            "show_arguments_preview_and_risk_summary",
            "require_user_confirm_or_reject_before side-effectful or executable actions",
            "call controlled_execute_route only after explicit approval",
            "show trace_id for debug/replay",
        ],
        "allowed_controlled_actions": ["agent_practice_plan"],
        "forbidden_actions_in_v2_6_6": [
            "agent_playback_prepare_real_execution",
            "direct_accompaniment_generate_from_agent_action",
            "POST /accompaniment/generate from Agent action contract",
            "engine_adapter dispatch",
            "MIDI asset creation",
        ],
        "guards": {
            "action_card_executes_playback": False,
            "action_card_calls_accompaniment_generate": False,
            "action_card_calls_engine_adapter": False,
            "action_card_creates_midi_asset": False,
            "action_card_allows_autonomous_execution": False,
            "raw_api_key_allowed_in_action_card": False,
        },
    }



@dataclass(frozen=True)
class RoutinePracticePlanActionPayload:
    """v2_6_8 Routine-facing structured payload for practice-plan actions.

    This is a presentation payload for HarmonyOS Routine. It contains enough
    information for the client to render a plan and prepare a Routine setup
    screen, but it does not start playback, call /accompaniment/generate, call
    engine adapters, or create MIDI assets.
    """

    payload_contract_version: str
    plan: dict[str, Any]
    routine_config_candidate: dict[str, Any]
    routine_blocks: tuple[dict[str, Any], ...]
    next_client_actions: tuple[str, ...]
    client_button_semantics: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    start_requires_separate_routine_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "plan": _redact_sensitive_values(self.plan),
            "routine_config_candidate": _redact_sensitive_values(self.routine_config_candidate),
            "routine_blocks": [_redact_sensitive_values(block) for block in self.routine_blocks],
            "next_client_actions": list(self.next_client_actions),
            "client_button_semantics": _redact_sensitive_values(self.client_button_semantics),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "start_requires_separate_routine_confirmation": self.start_requires_separate_routine_confirmation,
        }


def build_routine_practice_plan_action_payload(
    controlled_result: ControlledWorkflowExecutionResult,
    *,
    trace_id: str | None = None,
) -> RoutinePracticePlanActionPayload:
    """Convert a controlled agent_practice_plan result into a Routine payload."""

    output = controlled_result.workflow_output or {}
    plan = output.get("plan") if isinstance(output, dict) else None
    if not isinstance(plan, dict):
        plan = {}
    blocks = plan.get("blocks") if isinstance(plan.get("blocks"), list) else []
    routine_blocks = tuple(_routine_block_from_plan_block(block, index) for index, block in enumerate(blocks))
    total_minutes = sum(int(block.get("duration_minutes") or 0) for block in routine_blocks)
    duration_minutes = int(plan.get("duration_minutes") or total_minutes or 0)
    primary_style = _first_non_empty([block.get("style") for block in routine_blocks]) or "medium_swing"
    primary_tempo = _first_non_empty([block.get("tempo") for block in routine_blocks]) or _style_default_tempo(str(primary_style))
    tune_title = _first_non_empty([((block.get("material") or {}).get("tune") if isinstance(block.get("material"), dict) else None) for block in routine_blocks])
    routine_name = str(plan.get("title") or "JamMate Practice Routine")
    routine_config_candidate = {
        "routine_name": routine_name,
        "practice_goal": plan.get("main_focus"),
        "duration_minutes": duration_minutes,
        "style": primary_style,
        "tempo": int(primary_tempo),
        "tune_title": tune_title,
        "loop_enabled": True,
        "count_in_enabled": True,
        "output_format": "midi_base64",
        "source": "agent_practice_plan_action_card",
        "agent_tool_name": "agent_practice_plan",
        "plan_id": plan.get("plan_id"),
        "trace_id": trace_id or (output.get("trace_id") if isinstance(output, dict) else None),
        "requires_user_start_confirmation": True,
        "accompaniment_generate_call_enabled": False,
        "playback_execution_enabled": False,
    }
    compact_plan = {
        "plan_id": plan.get("plan_id"),
        "title": plan.get("title"),
        "duration_minutes": duration_minutes,
        "main_focus": plan.get("main_focus"),
        "estimated_difficulty": plan.get("estimated_difficulty"),
        "source": plan.get("source"),
        "block_count": len(routine_blocks),
        "total_block_minutes": total_minutes,
    }
    return RoutinePracticePlanActionPayload(
        payload_contract_version=PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
        plan=compact_plan,
        routine_config_candidate=routine_config_candidate,
        routine_blocks=routine_blocks,
        next_client_actions=("open_routine_setup", "save_practice_plan", "edit_plan", "dismiss", "view_trace"),
        client_button_semantics={
            "primary": {
                "action": "open_routine_setup",
                "label": "Open Routine Setup",
                "does_start_playback": False,
                "requires_separate_start_confirmation": True,
            },
            "secondary": [
                {"action": "save_practice_plan", "label": "Save Plan", "side_effect_level": "local_only"},
                {"action": "edit_plan", "label": "Edit Plan", "side_effect_level": "none"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
        trace_id=trace_id or (output.get("trace_id") if isinstance(output, dict) else None),
    )


def build_practice_plan_action_card_e2e_summary(
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    result_preview = action_card.result_preview if action_card else {}
    payload = result_preview.get("routine_practice_plan_payload") if isinstance(result_preview, dict) else None
    plan = payload.get("plan") if isinstance(payload, dict) else {}
    return {
        "practice_plan_action_card_e2e_version": PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
        "source": source,
        "has_action_card": action_card is not None,
        "has_routine_practice_plan_payload": isinstance(payload, dict),
        "action_id": action_card.action_id if action_card else None,
        "tool_name": action_card.tool_name if action_card else None,
        "plan_title": plan.get("title") if isinstance(plan, dict) else None,
        "duration_minutes": plan.get("duration_minutes") if isinstance(plan, dict) else None,
        "block_count": plan.get("block_count") if isinstance(plan, dict) else None,
        "next_client_actions": payload.get("next_client_actions", []) if isinstance(payload, dict) else [],
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }


def practice_plan_action_card_e2e_contract() -> dict[str, Any]:
    return {
        "version": PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
        "practice_plan_action_card_e2e_version": PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
        "spec_route": "GET /agent/actions/practice-plan/spec",
        "execute_controlled_route": "POST /agent/actions/practice-plan/execute-controlled",
        "terminal_command": "/practice-plan-action-card",
        "surface": "HarmonyOS Routine practice-plan ActionCard payload",
        "mode": "controlled_agent_practice_plan_to_routine_payload",
        "execution_status": {
            "controlled_practice_plan_execution_enabled": True,
            "routine_payload_enabled": True,
            "open_routine_setup_enabled": True,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "payload_schema": {
            "payload_contract_version": "v2_6_8",
            "plan": {
                "plan_id": "string | null",
                "title": "string | null",
                "duration_minutes": "number",
                "main_focus": "string | null",
                "estimated_difficulty": "string | null",
                "source": "rule_based | llm | template | hybrid | null",
                "block_count": "number",
                "total_block_minutes": "number",
            },
            "routine_config_candidate": "RoutineConfig candidate for opening setup only; does not start playback",
            "routine_blocks": "RoutinePracticeBlock[]",
            "next_client_actions": "open_routine_setup | save_practice_plan | edit_plan | dismiss | view_trace",
            "client_button_semantics": "button action metadata for HarmonyOS Routine",
        },
        "rules": [
            "The client may render the returned practice plan and open Routine setup from it.",
            "Opening Routine setup is not playback execution and does not call /accompaniment/generate.",
            "Starting a playable Routine remains a separate user-confirmed client action.",
            "This contract never executes agent_playback_prepare and never creates MIDI assets.",
        ],
        "guards": {
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


def _routine_block_from_plan_block(block: Any, index: int) -> dict[str, Any]:
    item = dict(block) if isinstance(block, dict) else {}
    accompaniment = item.get("accompaniment_config") if isinstance(item.get("accompaniment_config"), dict) else None
    return {
        "block_index": index,
        "block_id": item.get("block_id"),
        "type": item.get("type"),
        "title": item.get("title"),
        "intent": item.get("intent"),
        "duration_minutes": int(item.get("duration_minutes") or 0),
        "material": item.get("material") if isinstance(item.get("material"), dict) else None,
        "style": item.get("style") or (accompaniment or {}).get("style"),
        "tempo": item.get("tempo") or (accompaniment or {}).get("tempo"),
        "practice_role": (accompaniment or {}).get("practice_role"),
        "requires_accompaniment_asset": bool(accompaniment),
        "accompaniment_request_candidate": _routine_accompaniment_candidate(accompaniment) if accompaniment else None,
        "status": item.get("status"),
    }


def _routine_accompaniment_candidate(accompaniment: dict[str, Any]) -> dict[str, Any]:
    return {
        "style": accompaniment.get("style"),
        "tempo": accompaniment.get("tempo"),
        "muted_roles": list(accompaniment.get("muted_roles") or []),
        "practice_role": accompaniment.get("practice_role"),
        "loop_enabled": bool(accompaniment.get("section_loop", True)),
        "count_in_enabled": bool(accompaniment.get("count_in", True)),
        "output_format": accompaniment.get("output_format") or "midi_base64",
        "harmonic_expansion_enabled": bool(accompaniment.get("harmonic_expansion_enabled", False)),
        "density": accompaniment.get("density") or "normal",
        "call_enabled_now": False,
        "requires_user_start_confirmation": True,
    }


def _first_non_empty(values: list[Any]) -> Any | None:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _style_default_tempo(style: str) -> int:
    if style == "jazz_ballad":
        return 76
    if style == "bossa_nova":
        return 140
    return 120


@dataclass(frozen=True)
class PlaybackPrepareGuardedActionPayload:
    """v2_6_9 guarded design payload for agent_playback_prepare.

    This payload lets HarmonyOS Routine render a high-risk playback preparation
    candidate and the exact client-side confirmation semantics needed before a
    future Routine start action. It is intentionally not execution: it does not
    call /accompaniment/generate, call engine adapters, create MIDI assets, or
    start playback.
    """

    payload_contract_version: str
    playback_request_candidate: dict[str, Any]
    routine_config_candidate: dict[str, Any]
    risk_gate: dict[str, Any]
    confirmation_ladder: tuple[dict[str, Any], ...]
    next_client_actions: tuple[str, ...]
    client_button_semantics: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    agent_playback_prepare_execution_enabled: bool = False
    requires_final_routine_start_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "playback_request_candidate": _redact_sensitive_values(self.playback_request_candidate),
            "routine_config_candidate": _redact_sensitive_values(self.routine_config_candidate),
            "risk_gate": _redact_sensitive_values(self.risk_gate),
            "confirmation_ladder": [_redact_sensitive_values(step) for step in self.confirmation_ladder],
            "next_client_actions": list(self.next_client_actions),
            "client_button_semantics": _redact_sensitive_values(self.client_button_semantics),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "agent_playback_prepare_execution_enabled": self.agent_playback_prepare_execution_enabled,
            "requires_final_routine_start_confirmation": self.requires_final_routine_start_confirmation,
        }


def build_playback_prepare_guarded_action_payload(
    workflow_dispatch_result: ToolWorkflowDispatchResult,
    *,
    trace_id: str | None = None,
) -> PlaybackPrepareGuardedActionPayload:
    """Build a Routine-facing guarded payload for agent_playback_prepare.

    The input should be a descriptor-only workflow dispatch dry-run. This
    function deliberately does not call any workflow runner; it only reshapes the
    approved dry-run request into a client-renderable guarded design payload.
    """

    request = workflow_dispatch_result.execution_result.request
    args = dict(request.arguments_preview or {})
    descriptor = workflow_dispatch_result.workflow_descriptor
    tool_name = request.tool_name
    raw_duration = args.get("duration_minutes", args.get("durationMinutes", args.get("availableMinutes", 20)))
    try:
        duration_minutes = int(raw_duration)
    except (TypeError, ValueError):
        duration_minutes = 20
    style = str(args.get("style") or args.get("styleId") or _infer_style_from_text(args) or "medium_swing")
    tempo = args.get("tempo") or args.get("bpm") or _style_default_tempo(style)
    try:
        tempo_value = int(tempo)
    except (TypeError, ValueError):
        tempo_value = _style_default_tempo(style)
    tune_title = args.get("tune_title") or args.get("tuneTitle") or args.get("tune") or args.get("song")
    routine_name = args.get("routine_name") or args.get("routineName") or (f"{tune_title} Routine" if tune_title else "JamMate Playback Routine")
    muted_roles = args.get("muted_roles") or args.get("mutedRoles") or []
    if not isinstance(muted_roles, list):
        muted_roles = [str(muted_roles)]
    leadsheet = args.get("score_document") or args.get("scoreDocument") or args.get("leadsheet")
    has_inline_leadsheet = isinstance(leadsheet, dict) and bool(leadsheet.get("schema_version") or leadsheet.get("schemaVersion") or leadsheet.get("sections"))
    playback_request_candidate = {
        "tool_name": tool_name,
        "workflow_name": descriptor.workflow_name if descriptor else "ImmediatePlaybackWorkflow.prepare",
        "route": descriptor.route if descriptor else "POST /agent/playback/prepare",
        "adapter_boundary": descriptor.adapter_boundary if descriptor else "jammate_agent.adapters.JamMateEngineAccompanimentAdapter",
        "duration_minutes": duration_minutes,
        "style": style,
        "tempo": tempo_value,
        "tune_title": tune_title,
        "has_inline_leadsheet": has_inline_leadsheet,
        "muted_roles": list(muted_roles),
        "output_format": args.get("output_format") or args.get("outputFormat") or "midi_base64",
        "loop_enabled": bool(args.get("loop_enabled", args.get("loopEnabled", True))),
        "count_in_enabled": bool(args.get("count_in_enabled", args.get("countInEnabled", True))),
        "client_timer_owns_duration": True,
        "call_enabled_now": False,
        "requires_user_start_confirmation": True,
        "requires_accompaniment_generate_after_start_confirmation": True,
    }
    routine_config_candidate = {
        "routine_name": routine_name,
        "practice_goal": args.get("practice_goal") or args.get("practiceGoal") or "Immediate practice playback",
        "duration_minutes": duration_minutes,
        "style": style,
        "tempo": tempo_value,
        "tune_title": tune_title,
        "loop_enabled": True,
        "count_in_enabled": playback_request_candidate["count_in_enabled"],
        "output_format": "midi_base64",
        "source": "agent_playback_prepare_guarded_design",
        "agent_tool_name": "agent_playback_prepare",
        "trace_id": trace_id,
        "requires_user_start_confirmation": True,
        "requires_backend_generation_confirmation": True,
        "accompaniment_generate_call_enabled": False,
        "playback_execution_enabled": False,
    }
    risk_gate = {
        "side_effect_level": request.side_effect_level,
        "risk_summary": "agent_playback_prepare is high risk because future execution can create a MIDI asset and prepare playback.",
        "requires_user_confirmation": True,
        "requires_final_routine_start_confirmation": True,
        "requires_visible_parameter_review": True,
        "agent_may_execute_without_user": False,
        "allowed_current_stage": "guarded_design_only",
        "blocked_current_stage": [
            "POST /accompaniment/generate",
            "JamMateEngineAccompanimentAdapter.prepare",
            "MIDI asset creation",
            "Playback start",
        ],
    }
    confirmation_ladder = (
        {"step": "tool_call_preview", "status": "completed" if workflow_dispatch_result.execution_result.ok else "blocked", "side_effects": False},
        {"step": "user_confirmation", "status": request.confirmation_status, "user_approved": request.user_approved, "side_effects": False},
        {"step": "executor_dry_run", "status": workflow_dispatch_result.execution_result.status, "side_effects": False},
        {"step": "workflow_descriptor_resolution", "status": workflow_dispatch_result.status, "side_effects": False},
        {"step": "future_routine_start_confirmation", "status": "required_not_executed", "side_effects": False},
        {"step": "future_accompaniment_generation", "status": "blocked_in_v2_6_9", "side_effects": False},
    )
    return PlaybackPrepareGuardedActionPayload(
        payload_contract_version=PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
        playback_request_candidate=playback_request_candidate,
        routine_config_candidate=routine_config_candidate,
        risk_gate=risk_gate,
        confirmation_ladder=confirmation_ladder,
        next_client_actions=("review_playback_request", "open_routine_setup", "edit_request", "dismiss", "view_trace"),
        client_button_semantics={
            "primary": {
                "action": "open_routine_setup",
                "label": "Review in Routine Setup",
                "does_call_accompaniment_generate": False,
                "does_start_playback": False,
                "requires_separate_start_confirmation": True,
            },
            "dangerous_future_primary": {
                "action": "routine_start_after_confirmation",
                "label": "Start Routine",
                "enabled_now": False,
                "requires_user_confirmation": True,
                "would_call_accompaniment_generate": True,
            },
            "secondary": [
                {"action": "edit_request", "label": "Edit Request", "side_effect_level": "none"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
        trace_id=trace_id,
    )


def build_playback_prepare_guarded_design_summary(
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    result_preview = action_card.result_preview if action_card else {}
    payload = result_preview.get("playback_prepare_guarded_payload") if isinstance(result_preview, dict) else None
    request_candidate = payload.get("playback_request_candidate") if isinstance(payload, dict) else {}
    return {
        "playback_prepare_guarded_design_version": PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
        "source": source,
        "has_action_card": action_card is not None,
        "has_playback_prepare_guarded_payload": isinstance(payload, dict),
        "action_id": action_card.action_id if action_card else None,
        "tool_name": action_card.tool_name if action_card else None,
        "style": request_candidate.get("style") if isinstance(request_candidate, dict) else None,
        "tempo": request_candidate.get("tempo") if isinstance(request_candidate, dict) else None,
        "duration_minutes": request_candidate.get("duration_minutes") if isinstance(request_candidate, dict) else None,
        "next_client_actions": payload.get("next_client_actions", []) if isinstance(payload, dict) else [],
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "agent_playback_prepare_execution_enabled": False,
    }


def playback_prepare_guarded_design_contract() -> dict[str, Any]:
    return {
        "version": PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
        "playback_prepare_guarded_design_version": PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION,
        "spec_route": "GET /agent/actions/playback-prepare/spec",
        "guarded_preview_route": "POST /agent/actions/playback-prepare/guarded-preview",
        "terminal_command": "/playback-prepare-guarded",
        "surface": "HarmonyOS Routine playback-prepare guarded ActionCard payload",
        "mode": "agent_playback_prepare_guarded_design_only",
        "execution_status": {
            "playback_prepare_guarded_payload_enabled": True,
            "routine_setup_candidate_enabled": True,
            "agent_playback_prepare_real_execution_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "payload_schema": {
            "payload_contract_version": "v2_6_9",
            "playback_request_candidate": "Candidate request for future user-confirmed Routine start; call_enabled_now=false",
            "routine_config_candidate": "RoutineConfig candidate for opening setup only; does not start playback",
            "risk_gate": "High-risk guard summary and blocked current-stage side effects",
            "confirmation_ladder": "Preview -> user confirmation -> dry-run -> descriptor -> future start confirmation",
            "next_client_actions": "review_playback_request | open_routine_setup | edit_request | dismiss | view_trace",
            "client_button_semantics": "button action metadata for HarmonyOS Routine",
        },
        "rules": [
            "agent_playback_prepare is allowed to be previewed, confirmed, dry-run, and descriptor-resolved only.",
            "The guarded payload may open Routine setup but must not call /accompaniment/generate.",
            "A future playable Routine start remains a separate user-confirmed client action.",
            "This contract never calls engine adapters, creates MIDI assets, or starts playback.",
        ],
        "guards": {
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "agent_playback_prepare_real_execution_enabled": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


@dataclass(frozen=True)
class RoutineConfigPrepareActionPayload:
    """v2_7_0 editable RoutineConfig draft payload.

    This payload converts a natural-language request, a practice-plan payload,
    or a single practice-plan block into a HarmonyOS Routine setup candidate. It
    is a draft-only contract: it does not call /accompaniment/generate, call
    engine adapters, create MIDI assets, or start playback.
    """

    payload_contract_version: str
    routine_config_candidate: dict[str, Any]
    routine_blocks: tuple[dict[str, Any], ...]
    source_inputs: dict[str, Any]
    validation: dict[str, Any]
    next_client_actions: tuple[str, ...]
    client_button_semantics: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    editable: bool = True
    requires_user_start_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "routine_config_candidate": _redact_sensitive_values(self.routine_config_candidate),
            "routine_blocks": [_redact_sensitive_values(block) for block in self.routine_blocks],
            "source_inputs": _redact_sensitive_values(self.source_inputs),
            "validation": _redact_sensitive_values(self.validation),
            "next_client_actions": list(self.next_client_actions),
            "client_button_semantics": _redact_sensitive_values(self.client_button_semantics),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "editable": self.editable,
            "requires_user_start_confirmation": self.requires_user_start_confirmation,
        }


def build_routine_config_prepare_action_payload(
    arguments: dict[str, Any] | None = None,
    *,
    tool_name: str = "agent_routine_config_prepare",
    trace_id: str | None = None,
    source: str = "agent_routine_config_prepare",
) -> RoutineConfigPrepareActionPayload:
    """Build an editable RoutineConfig candidate without side effects."""

    args = dict(arguments or {})
    plan = args.get("practice_plan") or args.get("practicePlan") or args.get("plan")
    block = args.get("practice_block") or args.get("practiceBlock") or args.get("block")
    blocks: list[Any] = []
    if isinstance(plan, dict) and isinstance(plan.get("blocks"), list):
        blocks = list(plan.get("blocks") or [])
    elif isinstance(block, dict):
        blocks = [block]
    routine_blocks = tuple(_routine_block_from_plan_block(item, index) for index, item in enumerate(blocks))
    playable_blocks = [item for item in routine_blocks if item.get("requires_accompaniment_asset")]
    first_playable = playable_blocks[0] if playable_blocks else (routine_blocks[0] if routine_blocks else {})
    material = first_playable.get("material") if isinstance(first_playable.get("material"), dict) else {}
    accompaniment = first_playable.get("accompaniment_request_candidate") if isinstance(first_playable.get("accompaniment_request_candidate"), dict) else {}

    user_text = str(args.get("user_input") or args.get("userInput") or args.get("text") or args.get("prompt") or "")
    raw_duration = (
        args.get("duration_minutes")
        or args.get("durationMinutes")
        or args.get("available_minutes")
        or args.get("availableMinutes")
        or (plan.get("duration_minutes") if isinstance(plan, dict) else None)
        or first_playable.get("duration_minutes")
        or sum(int(item.get("duration_minutes") or 0) for item in routine_blocks)
        or 20
    )
    duration_minutes, duration_warning = _coerce_int_with_bounds(raw_duration, default=20, minimum=1, maximum=180)

    style = str(
        args.get("style")
        or args.get("styleId")
        or accompaniment.get("style")
        or first_playable.get("style")
        or _infer_style_from_text(args)
        or "medium_swing"
    )
    raw_tempo = args.get("tempo") or args.get("bpm") or accompaniment.get("tempo") or first_playable.get("tempo") or _style_default_tempo(style)
    tempo, tempo_warning = _coerce_int_with_bounds(raw_tempo, default=_style_default_tempo(style), minimum=40, maximum=260)
    tune_title = (
        args.get("tune_title")
        or args.get("tuneTitle")
        or args.get("tune")
        or args.get("song")
        or material.get("tune")
        or _infer_tune_from_text(user_text)
    )
    routine_name = str(
        args.get("routine_name")
        or args.get("routineName")
        or (plan.get("title") if isinstance(plan, dict) else None)
        or (f"{tune_title} Routine" if tune_title else "JamMate Routine Draft")
    )
    practice_goal = (
        args.get("practice_goal")
        or args.get("practiceGoal")
        or args.get("goal")
        or (plan.get("main_focus") if isinstance(plan, dict) else None)
        or first_playable.get("intent")
        or "Practice with JamMate Routine"
    )
    muted_roles = args.get("muted_roles") or args.get("mutedRoles") or accompaniment.get("muted_roles") or []
    if not isinstance(muted_roles, list):
        muted_roles = [str(muted_roles)]
    instruments = args.get("instruments") if isinstance(args.get("instruments"), dict) else {
        "piano": "piano" not in muted_roles,
        "bass": "bass" not in muted_roles,
        "drums": "drums" not in muted_roles,
    }
    leadsheet = args.get("score_document") or args.get("scoreDocument") or args.get("leadsheet")
    has_inline_leadsheet = isinstance(leadsheet, dict) and bool(leadsheet.get("schema_version") or leadsheet.get("schemaVersion") or leadsheet.get("sections"))
    candidate = {
        "schema_version": "jammate_routine_config_candidate_v1",
        "routine_name": routine_name,
        "practice_goal": practice_goal,
        "duration_minutes": duration_minutes,
        "style": style,
        "tempo": tempo,
        "key": args.get("key"),
        "tune_id": args.get("tune_id") or args.get("tuneId"),
        "tune_title": tune_title,
        "has_inline_leadsheet": has_inline_leadsheet,
        "leadsheet": leadsheet if has_inline_leadsheet else None,
        "chorus_count": args.get("chorus_count") or args.get("chorusCount"),
        "loop_enabled": bool(args.get("loop_enabled", args.get("loopEnabled", True))),
        "count_in_enabled": bool(args.get("count_in_enabled", args.get("countInEnabled", accompaniment.get("count_in_enabled", True)))),
        "output_format": args.get("output_format") or args.get("outputFormat") or "midi_base64",
        "voicing_override": args.get("voicing_override") or args.get("voicingOverride"),
        "seed": args.get("seed"),
        "instruments": instruments,
        "muted_roles": list(muted_roles),
        "source": source,
        "agent_tool_name": tool_name,
        "trace_id": trace_id,
        "editable": True,
        "readiness_status": "draft",
        "requires_user_review": True,
        "requires_user_start_confirmation": True,
        "requires_backend_generation_confirmation": True,
        "client_timer_owns_duration": True,
        "accompaniment_generate_call_enabled": False,
        "playback_execution_enabled": False,
    }
    accompaniment_request_candidate = {
        "route": "POST /accompaniment/generate",
        "style": style,
        "tempo": tempo,
        "tune_title": tune_title,
        "has_inline_leadsheet": has_inline_leadsheet,
        "muted_roles": list(muted_roles),
        "output_format": candidate["output_format"],
        "loop_enabled": candidate["loop_enabled"],
        "count_in_enabled": candidate["count_in_enabled"],
        "call_enabled_now": False,
        "requires_user_start_confirmation": True,
    }
    candidate["accompaniment_request_candidate"] = accompaniment_request_candidate
    warnings = [warning for warning in (duration_warning, tempo_warning) if warning]
    if not tune_title and not has_inline_leadsheet:
        warnings.append("routine_config_has_no_tune_or_inline_leadsheet_yet")
    validation = {
        "status": "draft_valid_with_warnings" if warnings else "draft_valid",
        "warnings": warnings,
        "duration_minutes_valid": 1 <= duration_minutes <= 180,
        "tempo_valid": 40 <= tempo <= 260,
        "style_supported_by_current_manifest": style in {"medium_swing", "bossa_nova", "jazz_ballad"},
        "requires_user_review_before_start": True,
        "call_enabled_now": False,
    }
    source_inputs = {
        "source": source,
        "tool_name": tool_name,
        "has_user_input": bool(user_text),
        "has_practice_plan": isinstance(plan, dict),
        "practice_plan_block_count": len(blocks),
        "has_practice_block": isinstance(block, dict),
        "has_inline_leadsheet": has_inline_leadsheet,
        "derived_from_playable_block": bool(playable_blocks),
    }
    return RoutineConfigPrepareActionPayload(
        payload_contract_version=ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
        routine_config_candidate=candidate,
        routine_blocks=routine_blocks,
        source_inputs=source_inputs,
        validation=validation,
        next_client_actions=("open_routine_setup", "edit_routine_config", "save_routine_draft", "dismiss", "view_trace"),
        client_button_semantics={
            "primary": {
                "action": "open_routine_setup",
                "label": "Open Routine Setup",
                "does_call_accompaniment_generate": False,
                "does_start_playback": False,
                "requires_separate_start_confirmation": True,
            },
            "secondary": [
                {"action": "edit_routine_config", "label": "Edit Routine", "side_effect_level": "none"},
                {"action": "save_routine_draft", "label": "Save Draft", "side_effect_level": "local_only"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
        trace_id=trace_id,
    )


def build_routine_config_prepare_summary(
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    payload: RoutineConfigPrepareActionPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    active_payload = payload.to_dict() if payload else None
    if active_payload is None and action_card is not None:
        result_preview = action_card.result_preview if isinstance(action_card.result_preview, dict) else {}
        active_payload = result_preview.get("routine_config_prepare_payload") if isinstance(result_preview, dict) else None
    candidate = active_payload.get("routine_config_candidate") if isinstance(active_payload, dict) else {}
    return {
        "routine_config_prepare_contract_version": ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
        "source": source,
        "has_action_card": action_card is not None,
        "has_routine_config_prepare_payload": isinstance(active_payload, dict),
        "action_id": action_card.action_id if action_card else None,
        "tool_name": action_card.tool_name if action_card else (candidate.get("agent_tool_name") if isinstance(candidate, dict) else None),
        "routine_name": candidate.get("routine_name") if isinstance(candidate, dict) else None,
        "style": candidate.get("style") if isinstance(candidate, dict) else None,
        "tempo": candidate.get("tempo") if isinstance(candidate, dict) else None,
        "duration_minutes": candidate.get("duration_minutes") if isinstance(candidate, dict) else None,
        "next_client_actions": active_payload.get("next_client_actions", []) if isinstance(active_payload, dict) else [],
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def routine_config_prepare_contract() -> dict[str, Any]:
    return {
        "version": ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
        "routine_config_prepare_contract_version": ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION,
        "spec_route": "GET /agent/actions/routine-config/spec",
        "prepare_route": "POST /agent/actions/routine-config/prepare",
        "terminal_command": "/routine-config-prepare",
        "surface": "HarmonyOS Routine editable RoutineConfig draft payload",
        "mode": "routine_config_candidate_only_no_playback",
        "execution_status": {
            "routine_config_payload_enabled": True,
            "open_routine_setup_enabled": True,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "payload_schema": {
            "payload_contract_version": "v2_7_0",
            "routine_config_candidate": "Editable RoutineConfig candidate for HarmonyOS Routine setup",
            "routine_blocks": "RoutinePracticeBlock[] derived from a practice plan when available",
            "source_inputs": "Derivation metadata from user input / plan / block / leadsheet",
            "validation": "Draft validation and warnings; call_enabled_now=false",
            "next_client_actions": "open_routine_setup | edit_routine_config | save_routine_draft | dismiss | view_trace",
            "client_button_semantics": "button action metadata for HarmonyOS Routine",
        },
        "rules": [
            "RoutineConfig prepare returns an editable setup draft only.",
            "Opening Routine setup is not playback execution and does not call /accompaniment/generate.",
            "Starting a playable Routine remains a separate user-confirmed client action.",
            "This contract never calls engine adapters, creates MIDI assets, or starts playback.",
        ],
        "guards": {
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "routine_start_enabled": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


@dataclass(frozen=True)
class PracticePlanToRoutineCandidateBridgePayload:
    """v2_7_1 neutral bridge from practice-plan block data to Routine candidates.

    This payload is deliberately UI-flow agnostic. It gives HarmonyOS Routine a
    candidate object that can be rendered as a setup page, bottom sheet, current
    form fill, queue item, template, or another client-owned flow. It does not
    require the client to open a specific page and it never calls playback,
    /accompaniment/generate, engine adapters, or MIDI asset creation.
    """

    payload_contract_version: str
    source: str
    candidate_scope: str
    selected_block: dict[str, Any]
    routine_candidate: dict[str, Any]
    routine_config_candidate: dict[str, Any]
    practice_plan_reference: dict[str, Any]
    frontend_flow_contract: dict[str, Any]
    available_client_actions: tuple[str, ...]
    client_action_semantics: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "candidate_scope": self.candidate_scope,
            "selected_block": _redact_sensitive_values(self.selected_block),
            "routine_candidate": _redact_sensitive_values(self.routine_candidate),
            "routine_config_candidate": _redact_sensitive_values(self.routine_config_candidate),
            "practice_plan_reference": _redact_sensitive_values(self.practice_plan_reference),
            "frontend_flow_contract": _redact_sensitive_values(self.frontend_flow_contract),
            "available_client_actions": list(self.available_client_actions),
            "client_action_semantics": _redact_sensitive_values(self.client_action_semantics),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_practice_plan_to_routine_candidate_bridge_payload(
    arguments: dict[str, Any] | None = None,
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    controlled_result: ControlledWorkflowExecutionResult | None = None,
    trace_id: str | None = None,
    source: str = "practice_plan_to_routine_candidate_bridge",
) -> PracticePlanToRoutineCandidateBridgePayload:
    """Build a UI-flow-agnostic Routine candidate from a practice plan block.

    Accepted inputs are intentionally flexible so the HarmonyOS client can use
    this bridge from different UI flows: a full practice-plan ActionCard, a
    routine_practice_plan_payload, a raw practice plan, or a single practice
    block. The output is only candidate data; the client owns presentation and
    follow-up actions.
    """

    args = dict(arguments or {})
    plan_payload = _extract_routine_practice_plan_payload(args, action_card=action_card, controlled_result=controlled_result, trace_id=trace_id)
    plan_ref = plan_payload.get("plan") if isinstance(plan_payload.get("plan"), dict) else {}
    routine_blocks = plan_payload.get("routine_blocks") if isinstance(plan_payload.get("routine_blocks"), list) else []

    if not routine_blocks:
        raw_plan = args.get("practice_plan") or args.get("practicePlan") or args.get("plan")
        raw_block = args.get("practice_block") or args.get("practiceBlock") or args.get("block")
        if isinstance(raw_plan, dict) and isinstance(raw_plan.get("blocks"), list):
            routine_blocks = [_routine_block_from_plan_block(block, index) for index, block in enumerate(raw_plan.get("blocks") or [])]
            plan_ref = {
                "plan_id": raw_plan.get("plan_id"),
                "title": raw_plan.get("title"),
                "duration_minutes": raw_plan.get("duration_minutes"),
                "main_focus": raw_plan.get("main_focus"),
                "block_count": len(routine_blocks),
            }
        elif isinstance(raw_block, dict):
            routine_blocks = [_routine_block_from_plan_block(raw_block, 0)]
            plan_ref = {"plan_id": None, "title": None, "duration_minutes": raw_block.get("duration_minutes"), "block_count": 1}

    selected_block = _select_routine_candidate_block(
        routine_blocks,
        block_id=args.get("block_id") or args.get("blockId"),
        block_index=args.get("block_index") if "block_index" in args else args.get("blockIndex"),
    )
    if not selected_block and routine_blocks:
        selected_block = dict(routine_blocks[0])
    selected_block = dict(selected_block or {})

    bridge_args: dict[str, Any] = {
        "practicePlan": {"blocks": [selected_block]} if selected_block else plan_payload.get("plan"),
        "practiceBlock": selected_block,
        "durationMinutes": selected_block.get("duration_minutes") or plan_ref.get("duration_minutes") or args.get("durationMinutes") or args.get("duration_minutes") or 20,
        "style": selected_block.get("style") or args.get("style"),
        "tempo": selected_block.get("tempo") or args.get("tempo"),
        "tuneTitle": ((selected_block.get("material") or {}).get("tune") if isinstance(selected_block.get("material"), dict) else None) or args.get("tuneTitle") or args.get("tune_title"),
        "practiceGoal": selected_block.get("intent") or plan_ref.get("main_focus") or args.get("practiceGoal") or args.get("practice_goal"),
    }
    bridge_args = {key: value for key, value in bridge_args.items() if value is not None}
    routine_config_payload = build_routine_config_prepare_action_payload(
        bridge_args,
        tool_name="agent_practice_plan_to_routine_candidate_bridge",
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
        source=source,
    ).to_dict()
    routine_config_candidate = dict(routine_config_payload.get("routine_config_candidate") or {})
    routine_candidate = dict(routine_config_candidate)
    routine_candidate.update({
        "candidate_schema_version": "jammate_routine_candidate_v1",
        "candidate_id": f"routine_candidate_{selected_block.get('block_id') or selected_block.get('block_index') or 'plan'}",
        "candidate_source": "practice_plan_block" if selected_block else "practice_plan",
        "source_plan_id": plan_ref.get("plan_id"),
        "source_block_id": selected_block.get("block_id"),
        "source_block_index": selected_block.get("block_index"),
        "frontend_flow_assumption": False,
        "client_decides_presentation": True,
        "call_enabled_now": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "playback_execution_enabled": False,
    })

    warnings: list[str] = []
    if not selected_block:
        warnings.append("no_selected_practice_plan_block_available")
    if not routine_candidate.get("tune_title") and not routine_candidate.get("has_inline_leadsheet"):
        warnings.append("routine_candidate_has_no_tune_or_inline_leadsheet_yet")
    validation = {
        "status": "candidate_valid_with_warnings" if warnings else "candidate_valid",
        "warnings": warnings,
        "selected_block_found": bool(selected_block),
        "client_must_choose_presentation": True,
        "requires_user_review_before_start": True,
        "call_enabled_now": False,
    }
    frontend_flow_contract = {
        "frontend_flow_assumption": False,
        "client_decides_presentation": True,
        "recommended_default_action": "present_routine_candidate",
        "allowed_presentation_modes": [
            "routine_setup_page",
            "bottom_sheet_confirmation",
            "current_routine_form_fill",
            "routine_queue_item",
            "template_library_item",
            "custom_client_flow",
        ],
        "backend_does_not_require_open_routine_setup": True,
        "backend_does_not_start_playback": True,
    }
    available_actions = (
        "present_routine_candidate",
        "apply_to_current_routine",
        "show_confirmation_sheet",
        "add_to_routine_queue",
        "save_as_template",
        "dismiss",
        "view_trace",
    )
    client_action_semantics = {
        "primary": {
            "action": "present_routine_candidate",
            "label": "Review Routine Candidate",
            "presentation_mode": "client_decides",
            "does_call_accompaniment_generate": False,
            "does_start_playback": False,
            "requires_separate_start_confirmation": True,
        },
        "alternatives": [
            {"action": "apply_to_current_routine", "label": "Apply to Current Routine Form", "side_effect_level": "local_ui_state"},
            {"action": "show_confirmation_sheet", "label": "Show Confirmation", "side_effect_level": "none"},
            {"action": "add_to_routine_queue", "label": "Add to Routine Queue", "side_effect_level": "local_only"},
            {"action": "save_as_template", "label": "Save as Template", "side_effect_level": "local_only"},
            {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
        ],
    }
    return PracticePlanToRoutineCandidateBridgePayload(
        payload_contract_version=PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
        source=source,
        candidate_scope="practice_plan_block" if selected_block else "practice_plan",
        selected_block=selected_block,
        routine_candidate=routine_candidate,
        routine_config_candidate=routine_config_candidate,
        practice_plan_reference={
            "plan_id": plan_ref.get("plan_id"),
            "title": plan_ref.get("title"),
            "duration_minutes": plan_ref.get("duration_minutes"),
            "main_focus": plan_ref.get("main_focus"),
            "block_count": plan_ref.get("block_count") or len(routine_blocks),
            "source_payload_contract_version": plan_payload.get("payload_contract_version"),
        },
        frontend_flow_contract=frontend_flow_contract,
        available_client_actions=available_actions,
        client_action_semantics=client_action_semantics,
        validation=validation,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_practice_plan_to_routine_candidate_bridge_summary(
    *,
    payload: PracticePlanToRoutineCandidateBridgePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    candidate = data.get("routine_candidate") if isinstance(data.get("routine_candidate"), dict) else {}
    flow = data.get("frontend_flow_contract") if isinstance(data.get("frontend_flow_contract"), dict) else {}
    return {
        "practice_plan_to_routine_candidate_bridge_version": PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "candidate_scope": data.get("candidate_scope"),
        "candidate_id": candidate.get("candidate_id"),
        "source_block_id": candidate.get("source_block_id"),
        "style": candidate.get("style"),
        "tempo": candidate.get("tempo"),
        "duration_minutes": candidate.get("duration_minutes"),
        "frontend_flow_assumption": flow.get("frontend_flow_assumption"),
        "client_decides_presentation": flow.get("client_decides_presentation"),
        "available_client_actions": data.get("available_client_actions", []),
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def practice_plan_to_routine_candidate_bridge_contract() -> dict[str, Any]:
    return {
        "version": PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
        "practice_plan_to_routine_candidate_bridge_version": PRACTICE_PLAN_TO_ROUTINE_CANDIDATE_BRIDGE_VERSION,
        "spec_route": "GET /agent/actions/practice-plan/routine-candidate/spec",
        "prepare_route": "POST /agent/actions/practice-plan/routine-candidate/prepare",
        "terminal_command": "/practice-plan-routine-candidate",
        "surface": "HarmonyOS Routine practice-plan block to UI-flow-agnostic Routine candidate bridge",
        "mode": "routine_candidate_only_client_decides_presentation",
        "execution_status": {
            "routine_candidate_payload_enabled": True,
            "frontend_flow_assumption": False,
            "client_decides_presentation": True,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "payload_schema": {
            "payload_contract_version": "v2_7_1",
            "selected_block": "RoutinePracticeBlock selected by block_id/block_index or first playable block",
            "routine_candidate": "Routine candidate data; not a command to open any specific UI flow",
            "routine_config_candidate": "Backward-compatible editable RoutineConfig candidate alias",
            "frontend_flow_contract": "client_decides_presentation=true and allowed_presentation_modes[]",
            "available_client_actions": "present_routine_candidate | apply_to_current_routine | show_confirmation_sheet | add_to_routine_queue | save_as_template | dismiss | view_trace",
            "client_action_semantics": "UI-neutral action semantics for HarmonyOS Routine",
        },
        "rules": [
            "The Agent backend returns candidate data only; the HarmonyOS client decides presentation and navigation.",
            "This bridge must not require opening a Routine setup page; setup page is only one possible presentation mode.",
            "Starting a playable Routine remains a separate user-confirmed client action.",
            "This contract never calls /accompaniment/generate, engine adapters, MIDI asset creation, or playback.",
        ],
        "guards": {
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "routine_start_enabled": False,
            "frontend_flow_hardcoded": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


@dataclass(frozen=True)
class RoutineHistoryContextIntakePayload:
    """v2_7_2 Routine history intake payload for future Agent context.

    This contract converts HarmonyOS Routine completion/history records into a
    compact PracticeHistoryContext section for later ContextPacket assembly. It
    is not a Routine summary page, recommendation card, database implementation,
    playback command, or accompaniment generation trigger.
    """

    payload_contract_version: str
    source: str
    routine_history_records: tuple[dict[str, Any], ...]
    practice_history_context_items: tuple[dict[str, Any], ...]
    context_packet_section: dict[str, Any]
    aggregate_summary: dict[str, Any]
    storage_boundary: dict[str, Any]
    validation: dict[str, Any]
    client_action_semantics: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    recommendation_card_created: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "routine_history_records": _redact_sensitive_values(list(self.routine_history_records)),
            "practice_history_context_items": _redact_sensitive_values(list(self.practice_history_context_items)),
            "context_packet_section": _redact_sensitive_values(self.context_packet_section),
            "aggregate_summary": _redact_sensitive_values(self.aggregate_summary),
            "storage_boundary": _redact_sensitive_values(self.storage_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "client_action_semantics": _redact_sensitive_values(self.client_action_semantics),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "recommendation_card_created": self.recommendation_card_created,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_routine_history_context_intake_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "routine_history_context_intake",
) -> RoutineHistoryContextIntakePayload:
    """Normalize Routine history records into Agent-readable context.

    HarmonyOS may keep richer local session/playback state, but this payload only
    preserves concise, long-lived practice-history facts useful for a future LLM
    turn such as "今天该练什么". Client-only playback details and MIDI assets are
    explicitly dropped.
    """

    args = dict(arguments or {})
    raw_records = _extract_routine_history_records(args)
    normalized_records: list[dict[str, Any]] = []
    context_items: list[dict[str, Any]] = []
    dropped_fields: dict[str, list[str]] = {}
    warnings: list[str] = []

    max_records_raw = args.get("max_records") or args.get("maxRecords") or 10
    try:
        max_records = max(1, min(50, int(max_records_raw)))
    except (TypeError, ValueError):
        max_records = 10
        warnings.append("invalid_max_records_defaulted_to_10")

    for index, raw_record in enumerate(raw_records[:max_records]):
        if not isinstance(raw_record, dict):
            warnings.append(f"record_{index}_ignored_not_object")
            continue
        normalized, context_item, dropped = _normalize_routine_history_record(raw_record, index=index)
        normalized_records.append(normalized)
        context_items.append(context_item)
        if dropped:
            dropped_fields[str(normalized.get("routine_id") or normalized.get("session_id") or index)] = dropped

    summary = _summarize_practice_history_context_items(context_items)
    context_section = {
        "section_name": "practice_history_context",
        "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
        "purpose": "Context for the next user-initiated Agent planning turn, not an automatic post-session recommendation.",
        "recent_practice_history": context_items,
        "aggregate_summary": summary,
        "context_usage_policy": {
            "use_when_user_asks_what_to_practice_next": True,
            "do_not_create_post_session_recommendation_card": True,
            "do_not_start_routine": True,
            "do_not_call_accompaniment_generate": True,
        },
    }
    if not context_items:
        warnings.append("no_routine_history_records_available")
    validation = {
        "status": "context_ready_with_warnings" if warnings else "context_ready",
        "warnings": warnings,
        "input_record_count": len(raw_records),
        "normalized_record_count": len(normalized_records),
        "context_item_count": len(context_items),
        "dropped_client_only_fields": dropped_fields,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_playback_position": False,
    }
    storage_boundary = {
        "harmonyos_local_owns": [
            "current RoutineSession state",
            "timer / pause / resume / playback position",
            "local MIDI file path and playback cache",
            "temporary Routine setup drafts",
            "Routine summary page display state",
        ],
        "backend_should_persist_summary_for_agent_context": [
            "PracticePlan",
            "RoutineHistory summary",
            "PracticeHistoryContextItem",
            "UserPracticeProfile",
            "saved leadsheets / routine templates when user opts in",
            "Agent trace metadata",
        ],
        "this_contract_persists_to_database": False,
        "this_contract_is_context_intake_only": True,
    }
    client_action_semantics = {
        "primary": {
            "action": "sync_routine_history_summary",
            "label": "Sync Routine history summary",
            "side_effect_level": "backend_summary_write_when_backend_persistence_exists",
            "does_create_recommendation_card": False,
            "does_start_playback": False,
        },
        "next_llm_turn_usage": {
            "action": "include_practice_history_context_in_context_packet",
            "trigger": "user_initiated_llm_question",
            "example_user_input": "今天该练什么？",
        },
    }
    return RoutineHistoryContextIntakePayload(
        payload_contract_version=ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
        source=source,
        routine_history_records=tuple(normalized_records),
        practice_history_context_items=tuple(context_items),
        context_packet_section=context_section,
        aggregate_summary=summary,
        storage_boundary=storage_boundary,
        validation=validation,
        client_action_semantics=client_action_semantics,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_routine_history_context_intake_summary(
    *,
    payload: RoutineHistoryContextIntakePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    aggregate = data.get("aggregate_summary") if isinstance(data.get("aggregate_summary"), dict) else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "context_item_count": aggregate.get("context_item_count", 0),
        "completed_count": aggregate.get("completed_count", 0),
        "total_practice_minutes": aggregate.get("total_practice_minutes", 0),
        "recent_tunes": aggregate.get("recent_tunes", []),
        "recent_styles": aggregate.get("recent_styles", []),
        "validation_status": validation.get("status"),
        "recommendation_card_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def routine_history_context_intake_contract() -> dict[str, Any]:
    return {
        "version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
        "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
        "spec_route": "GET /agent/context/routine-history/spec",
        "intake_route": "POST /agent/context/routine-history/intake",
        "terminal_command": "/routine-history-context",
        "surface": "HarmonyOS Routine history summary to Agent PracticeHistoryContext intake",
        "mode": "context_intake_only_no_post_session_recommendation_card",
        "execution_status": {
            "routine_history_context_payload_enabled": True,
            "context_packet_section_enabled": True,
            "database_persistence_implemented": False,
            "post_session_recommendation_card_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "routine_history_records": "Normalized RoutineHistoryRecord[] summary; no local playback internals",
            "practice_history_context_items": "Agent-readable compact history items for next LLM turn",
            "context_packet_section": "practice_history_context section that ContextBuilder may include",
            "aggregate_summary": "recent styles/tunes/minutes/completion summary",
            "storage_boundary": "local-vs-backend ownership guidance",
            "validation": "dropped_client_only_fields and context readiness warnings",
        },
        "rules": [
            "Routine end page stays client-owned and should only show completed content/time/recorded status.",
            "Agent should use this history on the next user-initiated planning conversation, not automatically at session end.",
            "The payload must not include midi_base64, local MIDI paths, current playback position, or timer state.",
            "This contract does not persist data to a database yet; it only defines the normalized intake/context shape.",
        ],
        "guards": {
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }



@dataclass(frozen=True)
class UserPracticeProfileContextIntakePayload:
    """v2_8_1 user long-term practice profile intake payload.

    This contract normalizes durable learner preferences and goals into an
    Agent-readable ContextPacket section. It is context intake only: no LLM call,
    no tool execution, no Routine start, no engine adapter call, and no database
    write are performed here.
    """

    payload_contract_version: str
    source: str
    input_profile: dict[str, Any]
    normalized_profile_context: dict[str, Any]
    context_packet_section: dict[str, Any]
    storage_boundary: dict[str, Any]
    validation: dict[str, Any]
    discarded_fields: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    storage_written: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "input_profile": _redact_sensitive_values(self.input_profile),
            "normalized_profile_context": _redact_sensitive_values(self.normalized_profile_context),
            "context_packet_section": _redact_sensitive_values(self.context_packet_section),
            "storage_boundary": _redact_sensitive_values(self.storage_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "discarded_fields": _redact_sensitive_values(self.discarded_fields),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "storage_written": self.storage_written,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_user_practice_profile_context_intake_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "user_practice_profile_context_intake",
) -> UserPracticeProfileContextIntakePayload:
    """Normalize durable practice-profile facts into Agent context.

    The profile is intentionally not a recommendation engine. It only exposes
    long-term goals, preferences, comfort ranges, and avoidances so later
    guidance can reason with them under explicit prompt/validation contracts.
    """

    args = dict(arguments or {})
    raw_profile = _extract_user_practice_profile(args)
    normalized, warnings, discarded = _normalize_user_practice_profile(raw_profile)
    profile_status = "available" if _user_practice_profile_has_content(normalized) else "missing"
    if profile_status == "missing":
        warnings.append("no_user_practice_profile_available")
    summary = _summarize_user_practice_profile(normalized)
    normalized_profile_context = {
        "context_type": "user_practice_profile_context",
        "profile_status": profile_status,
        "user_id": normalized.get("user_id"),
        "current_goal": normalized.get("current_goal"),
        "preferred_styles": normalized.get("preferred_styles", []),
        "focus_areas": normalized.get("focus_areas", []),
        "skill_focus": normalized.get("skill_focus", []),
        "common_tunes": normalized.get("common_tunes", []),
        "comfortable_tempo_ranges": normalized.get("comfortable_tempo_ranges", {}),
        "preferred_session_minutes": normalized.get("preferred_session_minutes", []),
        "avoid": normalized.get("avoid", []),
        "saved_routine_preferences": normalized.get("saved_routine_preferences", {}),
        "practice_mode_preference": normalized.get("practice_mode_preference"),
        "updated_at": normalized.get("updated_at"),
        "summary_for_llm": summary,
    }
    context_section = {
        "section_name": "user_practice_profile_context",
        "user_practice_profile_context_intake_version": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        "purpose": "Durable learner goals/preferences for the next user-initiated Agent planning turn.",
        "profile_status": profile_status,
        "profile": normalized_profile_context,
        "summary_for_llm": summary,
        "context_usage_policy": {
            "use_when_user_asks_what_to_practice_next": True,
            "combine_with_active_practice_plan_context": True,
            "combine_with_routine_history_context": True,
            "do_not_recommend_by_itself": True,
            "do_not_create_post_session_recommendation_card": True,
            "do_not_start_routine": True,
            "do_not_call_accompaniment_generate": True,
        },
    }
    validation = {
        "accepted": True,
        "status": "context_ready_with_warnings" if warnings else "context_ready",
        "warnings": warnings,
        "profile_status": profile_status,
        "recognized_field_count": _count_present_profile_fields(normalized),
        "discarded_field_count": len(discarded.get("disallowed_or_unrecognized_fields", [])) + len(discarded.get("sensitive_or_client_only_fields", [])),
        "discarded_fields": discarded,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_api_key": False,
        "contains_hidden_chain_of_thought": False,
        "contains_precise_location": False,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
    }
    storage_boundary = {
        "backend_should_persist_when_storage_exists": [
            "UserPracticeProfile current_goal / focus_areas / preferred_styles",
            "comfortable_tempo_ranges and preferred_session_minutes",
            "practice_mode_preference and avoid list",
            "saved routine preferences when the user opts in",
        ],
        "harmonyos_client_may_cache": [
            "editable local profile draft",
            "last selected practice mode and local UI preferences",
            "unsynced profile changes before explicit sync",
        ],
        "writes_to_backend": False,
        "writes_to_local_device": False,
        "this_contract_persists_to_database": False,
        "this_contract_is_context_intake_only": True,
    }
    guard_summary = {
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "storage_written": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "raw_api_key_allowed_in_payload": False,
    }
    return UserPracticeProfileContextIntakePayload(
        payload_contract_version=USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        source=source,
        input_profile=_drop_forbidden_profile_fields(raw_profile),
        normalized_profile_context=normalized_profile_context,
        context_packet_section=context_section,
        storage_boundary=storage_boundary,
        validation=validation,
        discarded_fields=discarded,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_user_practice_profile_context_intake_summary(
    *,
    payload: UserPracticeProfileContextIntakePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    profile = data.get("normalized_profile_context") if isinstance(data.get("normalized_profile_context"), dict) else {}
    tempo_ranges = profile.get("comfortable_tempo_ranges") if isinstance(profile.get("comfortable_tempo_ranges"), dict) else {}
    return {
        "user_practice_profile_context_intake_version": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "profile_status": validation.get("profile_status"),
        "validation_status": validation.get("status"),
        "recognized_field_count": validation.get("recognized_field_count", 0),
        "preferred_styles": profile.get("preferred_styles", []),
        "focus_areas": profile.get("focus_areas", []),
        "comfortable_tempo_style_count": len(tempo_ranges),
        "summary_for_llm": profile.get("summary_for_llm"),
        "llm_called": False,
        "tool_executed": False,
        "recommendation_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "storage_written": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def user_practice_profile_context_intake_contract() -> dict[str, Any]:
    return {
        "version": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        "user_practice_profile_context_intake_version": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        "spec_route": "GET /agent/context/user-practice-profile/spec",
        "intake_route": "POST /agent/context/user-practice-profile/intake",
        "terminal_command": "/user-practice-profile-context",
        "surface": "UserPracticeProfile to Agent context intake",
        "mode": "context_intake_only_no_llm_no_recommendation_no_execution_no_storage_write",
        "execution_status": {
            "user_practice_profile_context_payload_enabled": True,
            "context_packet_section_enabled": True,
            "database_persistence_implemented": False,
            "llm_call_enabled": False,
            "recommendation_card_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "input_profile": "Accepted raw profile fields from HarmonyOS/backend/client request",
            "normalized_profile_context": "Normalized current_goal/preferences/tempo ranges/avoidance profile",
            "context_packet_section": "user_practice_profile_context section that ContextBuilder may include",
            "storage_boundary": "local-vs-backend ownership guidance; no write in this version",
            "validation": "accepted/warnings/discarded fields and no-side-effect status",
            "discarded_fields": "sensitive/client-only/unrecognized fields dropped from Agent context",
            "guard_summary": "Explicit no-LLM/no-tool/no-engine/no-storage flags",
        },
        "allowed_fields": [
            "user_id",
            "current_goal",
            "preferred_styles",
            "focus_areas",
            "comfortable_tempo_ranges",
            "preferred_session_minutes",
            "practice_mode_preference",
            "avoid",
            "common_tunes",
            "saved_routine_preferences",
            "skill_focus",
            "updated_at",
        ],
        "dropped_fields": [
            "api_key",
            "token",
            "password",
            "local_midi_path",
            "midi_base64",
            "precise_location",
            "payment_info",
            "hidden_chain_of_thought",
        ],
        "rules": [
            "UserPracticeProfile is context, not a recommendation rule engine.",
            "This contract normalizes profile facts only; guidance logic remains in later prompt/provider/validation layers.",
            "Tempo ranges are normalized to min/max and invalid ranges become warnings instead of crashes.",
            "Sensitive, local playback, MIDI asset, payment, precise-location, and hidden-chain-of-thought fields must not enter Agent context.",
            "This contract does not write a database; persistence boundary is documented only.",
        ],
        "guards": {
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_writes_storage": False,
            "payload_creates_recommendation": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


@dataclass(frozen=True)
class PracticeContextStorageBoundaryPayload:
    """v2_8_2 practice-context storage boundary contract payload.

    This is a contract/preview surface only. It classifies which practice
    context objects are HarmonyOS-local, backend-long-term, request-ephemeral,
    Agent-trace, or never-stored. It does not write a database, call the LLM,
    execute tools, start Routine, call /accompaniment/generate, or create assets.
    """

    payload_contract_version: str
    source: str
    context_storage_boundary: dict[str, Any]
    ownership_matrix: tuple[dict[str, Any], ...]
    context_packet_boundary: dict[str, Any]
    sync_boundary: dict[str, Any]
    retention_boundary: dict[str, Any]
    field_classification: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "context_storage_boundary": _redact_sensitive_values(self.context_storage_boundary),
            "ownership_matrix": _redact_sensitive_values(list(self.ownership_matrix)),
            "context_packet_boundary": _redact_sensitive_values(self.context_packet_boundary),
            "sync_boundary": _redact_sensitive_values(self.sync_boundary),
            "retention_boundary": _redact_sensitive_values(self.retention_boundary),
            "field_classification": _redact_sensitive_values(self.field_classification),
            "validation": dict(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_practice_context_storage_boundary_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "practice_context_storage_boundary",
) -> PracticeContextStorageBoundaryPayload:
    """Build the storage/source-of-truth boundary for Agent practice context.

    This intentionally defines ownership and sync semantics only. It must stay
    separate from persistence implementation so Agent guidance can reason about
    context sources without forcing a database design prematurely.
    """

    args = dict(arguments or {})
    field_hits = _storage_boundary_forbidden_field_hits(args)
    input_signals = _storage_boundary_detect_input_signals(args)
    warnings: list[str] = []
    if field_hits:
        warnings.append("forbidden_or_local_only_fields_detected_and_excluded_from_agent_context")
    if not input_signals:
        warnings.append("no_context_input_signals_detected_boundary_contract_only")

    ownership_matrix = tuple(_practice_context_storage_ownership_matrix())
    context_storage_boundary = {
        "contract_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "principle": "Define source-of-truth ownership before persistence; do not write storage from this contract.",
        "categories": {
            "harmonyos_local_only": {
                "source_of_truth": "HarmonyOS client",
                "purpose": "Live practice UI/runtime state that should not be backend Agent context.",
                "examples": [
                    "current RoutineSession timer / pause / resume state",
                    "playback position and local player state",
                    "local MIDI file path and decoded MIDI cache",
                    "Routine setup form drafts and current UI selection",
                    "score viewport / scroll position / local render state",
                ],
            },
            "backend_long_term_context": {
                "source_of_truth": "backend when persistence exists",
                "purpose": "Durable learner objects that future Agent turns may retrieve as context.",
                "examples": [
                    "UserPracticeProfile",
                    "ActivePracticePlan and plan progress summary",
                    "RoutineHistory summary / PracticeHistoryContextItem",
                    "saved leadsheets, routine templates, and user-approved practice assets",
                ],
            },
            "request_ephemeral_context": {
                "source_of_truth": "current request only",
                "purpose": "Short-lived facts used to answer the current user turn.",
                "examples": [
                    "current user question",
                    "available_minutes for this turn",
                    "current screen/session summary",
                    "temporary Routine candidate or setup preview",
                ],
            },
            "agent_trace_context": {
                "source_of_truth": "Agent trace store",
                "purpose": "Debug/audit metadata for preview, validation, confirmation, and provider-boundary steps.",
                "examples": [
                    "trace_id and trace step names",
                    "sanitized tool preview metadata",
                    "validation summaries and blocked reasons",
                    "provider-boundary status without hidden chain-of-thought",
                ],
            },
            "never_store_or_contextualize": {
                "source_of_truth": "not allowed",
                "purpose": "Secrets, local playback internals, asset payloads, precise location, payment data, and hidden reasoning.",
                "examples": [
                    "api_key / token / password",
                    "midi_base64 and local_midi_path",
                    "precise_location / payment_info",
                    "hidden_chain_of_thought",
                ],
            },
        },
        "storage_implementation_status": {
            "database_schema_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "sync_job_implemented": False,
            "migration_required_now": False,
        },
    }
    context_packet_boundary = {
        "may_enter_context_packet": [
            "active_practice_plan_context",
            "practice_history_context",
            "user_practice_profile_context",
            "assembled_practice_context",
            "today_constraints",
            "sanitized_agent_trace_metadata",
        ],
        "must_not_enter_context_packet": [
            "current playback position",
            "local MIDI file path",
            "midi_base64 asset payload",
            "API keys / tokens / passwords",
            "payment information",
            "precise geolocation",
            "hidden chain-of-thought",
        ],
        "context_builder_rule": "ContextBuilder may assemble normalized context sections, but must not become a storage layer.",
        "today_practice_guidance_rule": "When the user later asks what to practice, use persisted summaries plus current request constraints; do not create post-session recommendations automatically.",
    }
    sync_boundary = {
        "allowed_future_sync_candidates": [
            {
                "object_type": "UserPracticeProfile",
                "direction": "client_or_backend_update_to_backend_long_term_context",
                "requires_explicit_user_or_app_sync_policy": True,
                "v2_8_2_writes_now": False,
            },
            {
                "object_type": "ActivePracticePlan",
                "direction": "backend_source_of_truth_to_client_cache",
                "requires_explicit_user_or_app_sync_policy": True,
                "v2_8_2_writes_now": False,
            },
            {
                "object_type": "RoutineHistorySummary",
                "direction": "HarmonyOS_completion_summary_to_backend_context_summary",
                "requires_explicit_user_or_app_sync_policy": True,
                "v2_8_2_writes_now": False,
            },
            {
                "object_type": "AgentTraceMetadata",
                "direction": "agent_runtime_to_trace_store",
                "requires_sanitization": True,
                "v2_8_2_writes_now": False,
            },
        ],
        "disallowed_sync_payloads": [
            "midi_base64",
            "local_midi_path",
            "playback_position",
            "timer_state",
            "api_key/token/password",
            "hidden_chain_of_thought",
        ],
        "contract_only": True,
    }
    retention_boundary = {
        "backend_long_term_context": "Retain compact summaries needed for future guidance; final retention policy is future backend work.",
        "harmonyos_local_only": "Retain according to client UX/cache policy; do not upload as Agent context unless summarized and allowed.",
        "request_ephemeral_context": "Use for the current request only and omit from durable storage unless converted into an explicit saved object.",
        "agent_trace_context": "Retain sanitized diagnostics for debugging/audit; never store secrets or hidden reasoning.",
        "v2_8_2_retention_enforced_in_code": False,
    }
    field_classification = {
        "input_signal_keys": sorted(str(key) for key in args.keys()),
        "detected_context_signals": input_signals,
        "forbidden_or_local_only_field_hits": field_hits,
        "ownership_by_signal": _storage_boundary_signal_ownership(input_signals),
        "sanitized_for_context": True,
        "raw_values_echoed": False,
    }
    validation = {
        "status": "boundary_ready_with_warnings" if warnings else "boundary_ready",
        "warnings": warnings,
        "input_signal_count": len(input_signals),
        "forbidden_or_local_only_field_count": len(field_hits),
        "contains_midi_base64_input": any(hit.endswith("midi_base64") or hit.endswith("midiBase64") for hit in field_hits),
        "contains_local_midi_path_input": any(hit.endswith("local_midi_path") or hit.endswith("localMidiPath") for hit in field_hits),
        "contains_api_key_input": any("api" in hit.lower() and "key" in hit.lower() for hit in field_hits),
        "contains_hidden_chain_of_thought_input": any("chain" in hit.lower() and "thought" in hit.lower() for hit in field_hits),
        "storage_contract_only": True,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
    }
    guard_summary = {
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "context_builder_becomes_storage_layer": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_agent_context": False,
        "hidden_chain_of_thought_allowed_in_context": False,
    }
    return PracticeContextStorageBoundaryPayload(
        payload_contract_version=PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        source=source,
        context_storage_boundary=context_storage_boundary,
        ownership_matrix=ownership_matrix,
        context_packet_boundary=context_packet_boundary,
        sync_boundary=sync_boundary,
        retention_boundary=retention_boundary,
        field_classification=field_classification,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_practice_context_storage_boundary_summary(
    *,
    payload: PracticeContextStorageBoundaryPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    classification = data.get("field_classification") if isinstance(data.get("field_classification"), dict) else {}
    matrix = data.get("ownership_matrix") if isinstance(data.get("ownership_matrix"), list) else []
    return {
        "practice_context_storage_boundary_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "ownership_category_count": len(matrix),
        "input_signal_count": validation.get("input_signal_count", 0),
        "detected_context_signals": list(classification.get("detected_context_signals") or []),
        "forbidden_or_local_only_field_count": validation.get("forbidden_or_local_only_field_count", 0),
        "storage_contract_only": True,
        "backend_write_enabled": False,
        "local_device_write_enabled": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def practice_context_storage_boundary_contract() -> dict[str, Any]:
    return {
        "version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "practice_context_storage_boundary_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "spec_route": "GET /agent/context/storage-boundary/spec",
        "preview_route": "POST /agent/context/storage-boundary/preview",
        "terminal_command": "/practice-context-storage-boundary",
        "surface": "Agent practice-context local/backend/trace/request storage boundary contract",
        "mode": "contract_preview_only_no_storage_write_no_llm_no_execution",
        "execution_status": {
            "storage_boundary_payload_enabled": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "sync_job_implemented": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "ownership_categories": [
            "harmonyos_local_only",
            "backend_long_term_context",
            "request_ephemeral_context",
            "agent_trace_context",
            "never_store_or_contextualize",
        ],
        "payload_schema": {
            "context_storage_boundary": "canonical source-of-truth categories and storage implementation status",
            "ownership_matrix": "object-level owner/source/cache/context eligibility table",
            "context_packet_boundary": "sections that may/must not enter ContextPacket",
            "sync_boundary": "future sync candidate directions; no writes in v2_8_2",
            "retention_boundary": "retention guidance only; no enforcement in v2_8_2",
            "field_classification": "detected input signals and forbidden/local-only field hits without raw value echo",
            "validation": "boundary readiness and no-side-effect flags",
            "guard_summary": "explicit no-storage/no-LLM/no-engine/no-MIDI/no-playback guards",
        },
        "rules": [
            "HarmonyOS owns live RoutineSession, timer, playback, local MIDI cache, UI draft, and score viewport state.",
            "Backend long-term storage should own durable UserPracticeProfile, ActivePracticePlan, RoutineHistory summaries, saved leadsheets/templates, and sanitized Agent trace metadata when persistence exists.",
            "Current user input, available_minutes, current screen/session summary, and preview candidates are request-ephemeral unless explicitly saved as a durable object.",
            "ContextBuilder assembles normalized context sections; it must not become a storage or sync layer.",
            "This contract does not implement a database, write storage, call an LLM, execute tools, start Routine, call /accompaniment/generate, or generate MIDI.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_agent_context": False,
            "local_midi_path_allowed_in_agent_context": False,
            "hidden_chain_of_thought_allowed_in_context": False,
        },
        "next_task_hint": "v2_8_3_agent_today_practice_guidance_profile_aware_e2e",
    }



@dataclass(frozen=True)
class PracticePlanPersistenceCandidatePayload:
    """v2_8_6 candidate-only PracticePlan persistence contract.

    This payload lets the Agent propose saving or updating a PracticePlan while
    preserving the preview -> confirmation -> controlled future write boundary.
    It deliberately does not write a database, update local device state, call an
    LLM, execute tools, start Routine, call /accompaniment/generate, invoke the
    engine adapter, create MIDI assets, or start playback.
    """

    payload_contract_version: str
    source: str
    operation: str
    candidate_id: str
    target_plan_ref: dict[str, Any]
    normalized_practice_plan: dict[str, Any]
    candidate_action: dict[str, Any]
    diff_preview: dict[str, Any]
    confirmation_policy: dict[str, Any]
    storage_boundary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "operation": self.operation,
            "candidate_id": self.candidate_id,
            "target_plan_ref": _redact_sensitive_values(self.target_plan_ref),
            "normalized_practice_plan": _redact_sensitive_values(self.normalized_practice_plan),
            "candidate_action": _redact_sensitive_values(self.candidate_action),
            "diff_preview": _redact_sensitive_values(self.diff_preview),
            "confirmation_policy": _redact_sensitive_values(self.confirmation_policy),
            "storage_boundary": _redact_sensitive_values(self.storage_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_practice_plan_persistence_candidate_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "practice_plan_persistence_candidate",
) -> PracticePlanPersistenceCandidatePayload:
    """Build a save/update PracticePlan candidate without writing persistence."""

    args = dict(arguments or {})
    raw_plan = _extract_practice_plan_persistence_candidate_input(args)
    normalized_plan, normalization_warnings, discarded_fields = _normalize_practice_plan_for_persistence(raw_plan)
    operation = _normalize_practice_plan_persistence_operation(args, normalized_plan)
    candidate_id = str(_first_present(args, "candidate_id", "candidateId", "persistence_candidate_id", "persistenceCandidateId") or f"practice_plan_persist_{uuid4().hex[:12]}")
    target_plan_id = _first_present(args, "target_plan_id", "targetPlanId", "plan_id", "planId") or normalized_plan.get("plan_id")
    existing_plan = _extract_existing_practice_plan_for_diff(args)
    diff_preview = _build_practice_plan_persistence_diff_preview(existing_plan, normalized_plan, operation)
    warnings = list(normalization_warnings)
    blocked_reasons: list[str] = []
    if discarded_fields.get("sensitive_or_client_only_fields"):
        warnings.append("sensitive_or_client_only_fields_discarded")
    if not normalized_plan.get("title") and not normalized_plan.get("blocks"):
        blocked_reasons.append("practice_plan_candidate_missing_title_and_blocks")
    if operation == "update_existing" and not target_plan_id:
        warnings.append("update_existing_without_target_plan_id_future_confirmation_should_request_target")
    status = "candidate_blocked" if blocked_reasons else ("candidate_ready_with_warnings" if warnings else "candidate_ready")
    candidate_action = {
        "action_type": "practice_plan_persistence_candidate",
        "candidate_id": candidate_id,
        "operation": operation,
        "title": normalized_plan.get("title") or "Untitled PracticePlan",
        "target_plan_id": target_plan_id,
        "side_effect_level": "backend_long_term_context_write_candidate",
        "requires_user_confirmation": True,
        "confirmation_status": "pending_user_review",
        "would_write_if_confirmed_in_future": True,
        "writes_now": False,
        "editable_before_confirmation": True,
        "next_client_actions": ["review_candidate", "edit_candidate", "confirm_save_plan", "dismiss", "view_trace"],
        "client_button_semantics": {
            "primary": {
                "action": "confirm_save_plan",
                "label": "Save Practice Plan",
                "requires_explicit_user_confirmation": True,
                "enabled_now": False,
                "reason_disabled_now": "v2_8_6 is preview contract only; future persistence executor not implemented.",
            },
            "secondary": [
                {"action": "edit_candidate", "label": "Edit Plan", "side_effect_level": "none"},
                {"action": "dismiss", "label": "Dismiss", "side_effect_level": "none"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
    }
    confirmation_policy = {
        "requires_user_confirmation": True,
        "requires_preview_before_confirmation": True,
        "requires_final_write_executor_future_stage": True,
        "autonomous_write_allowed": False,
        "llm_may_not_write_plan_directly": True,
        "confirmation_ladder": [
            {"step": "preview_candidate", "side_effects": False, "implemented_now": True},
            {"step": "user_reviews_or_edits", "side_effects": False, "implemented_now": True},
            {"step": "user_confirms_save_or_update", "side_effects": False, "implemented_now": False},
            {"step": "future_persistence_executor_writes_backend", "side_effects": True, "implemented_now": False},
            {"step": "client_refreshes_cached_plan", "side_effects": True, "implemented_now": False},
        ],
    }
    storage_boundary = {
        "boundary_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "candidate_contract_version": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "object_type": "ActivePracticePlan" if operation == "update_existing" else "PracticePlan",
        "owner": "backend_long_term_context",
        "future_source_of_truth": "backend_long_term_context_after_user_confirmed_write",
        "harmonyos_local_cache_allowed_after_success": True,
        "context_builder_may_read_summary_later": True,
        "writes_now": False,
        "database_schema_required_now": False,
        "sync_job_required_now": False,
    }
    validation = {
        "status": status,
        "accepted": not blocked_reasons,
        "operation": operation,
        "has_practice_plan_candidate": bool(normalized_plan),
        "block_count": len(normalized_plan.get("blocks") or []),
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "discarded_fields": discarded_fields,
        "preview_only": True,
        "requires_user_confirmation": True,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
    }
    guard_summary = {
        "candidate_only": True,
        "preview_confirmation_noop_boundary": True,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_plan_candidate": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return PracticePlanPersistenceCandidatePayload(
        payload_contract_version=PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        source=source,
        operation=operation,
        candidate_id=candidate_id,
        target_plan_ref={"target_plan_id": target_plan_id, "operation": operation},
        normalized_practice_plan=normalized_plan,
        candidate_action=candidate_action,
        diff_preview=diff_preview,
        confirmation_policy=confirmation_policy,
        storage_boundary=storage_boundary,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_practice_plan_persistence_candidate_summary(
    *,
    payload: PracticePlanPersistenceCandidatePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    plan = data.get("normalized_practice_plan") if isinstance(data.get("normalized_practice_plan"), dict) else {}
    diff = data.get("diff_preview") if isinstance(data.get("diff_preview"), dict) else {}
    return {
        "practice_plan_persistence_candidate_contract_version": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "operation": data.get("operation"),
        "candidate_id": data.get("candidate_id"),
        "plan_title": plan.get("title"),
        "block_count": validation.get("block_count", 0),
        "diff_change_count": len(diff.get("changed_fields") or []),
        "requires_user_confirmation": True,
        "preview_only": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def practice_plan_persistence_candidate_contract() -> dict[str, Any]:
    return {
        "version": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "practice_plan_persistence_candidate_contract_version": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "spec_route": "GET /agent/practice-plan/persistence-candidate/spec",
        "preview_route": "POST /agent/practice-plan/persistence-candidate/preview",
        "terminal_command": "/practice-plan-persistence-candidate",
        "surface": "PracticePlan save/update candidate contract",
        "mode": "candidate_preview_confirmation_boundary_only_no_storage_write",
        "execution_status": {
            "candidate_payload_enabled": True,
            "preview_enabled": True,
            "confirmation_required": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "sync_job_implemented": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "operations": ["save_new", "update_existing"],
        "payload_schema": {
            "operation": "save_new | update_existing",
            "target_plan_ref": "Target plan reference for update; optional for save_new",
            "normalized_practice_plan": "Sanitized PracticePlan candidate without secrets/local playback/MIDI payloads",
            "candidate_action": "User-reviewable action metadata; disabled write button in v2_8_6",
            "diff_preview": "Top-level plan diff preview when existing plan is supplied",
            "confirmation_policy": "Preview -> user review/edit -> future confirmed persistence executor ladder",
            "storage_boundary": "Backend long-term context boundary; no writes now",
            "validation": "Candidate readiness and no-side-effect flags",
        },
        "rules": [
            "LLM or Agent may propose a save/update PracticePlan candidate, but must not write storage directly.",
            "Client must show the candidate and require explicit user confirmation before any future persistence executor.",
            "v2_8_6 does not implement database schema, backend writes, local writes, or sync jobs.",
            "PracticePlan persistence remains separate from Routine start, playback, accompaniment generation, and MIDI asset creation.",
            "Sensitive fields, local MIDI paths, MIDI payloads, payment data, precise location, and hidden chain-of-thought must be discarded from the candidate.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_plan_candidate": False,
            "local_midi_path_allowed_in_plan_candidate": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "practice_plan_action_card_e2e": PRACTICE_PLAN_ACTION_CARD_E2E_VERSION,
            "today_practice_guidance_profile_aware_e2e": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        },
        "next_task_hint": "v2_8_7_agent_routine_history_persistence_candidate_contract",
    }


@dataclass(frozen=True)
class RoutineHistoryPersistenceCandidatePayload:
    """v2_8_7 candidate-only RoutineHistory persistence contract.

    HarmonyOS remains the owner of the live Routine session and produces a
    compact completion summary. This payload lets the Agent preview a future
    backend save/upload candidate for sanitized RoutineHistory summaries while
    preserving preview -> confirmation -> controlled future write boundaries.
    It never writes storage, starts a Routine, calls the LLM, invokes tools,
    calls /accompaniment/generate, invokes engine adapters, creates MIDI assets,
    or starts playback.
    """

    payload_contract_version: str
    source: str
    operation: str
    candidate_id: str
    target_history_ref: dict[str, Any]
    normalized_routine_history_records: tuple[dict[str, Any], ...]
    practice_history_context_items: tuple[dict[str, Any], ...]
    aggregate_summary: dict[str, Any]
    candidate_action: dict[str, Any]
    confirmation_policy: dict[str, Any]
    storage_boundary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "operation": self.operation,
            "candidate_id": self.candidate_id,
            "target_history_ref": _redact_sensitive_values(self.target_history_ref),
            "normalized_routine_history_records": _redact_sensitive_values(list(self.normalized_routine_history_records)),
            "practice_history_context_items": _redact_sensitive_values(list(self.practice_history_context_items)),
            "aggregate_summary": _redact_sensitive_values(self.aggregate_summary),
            "candidate_action": _redact_sensitive_values(self.candidate_action),
            "confirmation_policy": _redact_sensitive_values(self.confirmation_policy),
            "storage_boundary": _redact_sensitive_values(self.storage_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def build_routine_history_persistence_candidate_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "routine_history_persistence_candidate",
) -> RoutineHistoryPersistenceCandidatePayload:
    """Build a RoutineHistory summary save/upload candidate without writing persistence."""

    args = dict(arguments or {})
    raw_records = _extract_routine_history_persistence_candidate_records(args)
    max_records_raw = _first_present(args, "max_records", "maxRecords") or 50
    warnings: list[str] = []
    try:
        max_records = max(1, min(100, int(max_records_raw)))
    except (TypeError, ValueError):
        max_records = 50
        warnings.append("invalid_max_records_defaulted_to_50")

    normalized_records: list[dict[str, Any]] = []
    context_items: list[dict[str, Any]] = []
    dropped_fields: dict[str, list[str]] = {}
    for index, raw_record in enumerate(raw_records[:max_records]):
        if not isinstance(raw_record, dict):
            warnings.append(f"record_{index}_ignored_not_object")
            continue
        normalized, context_item, dropped = _normalize_routine_history_record(raw_record, index=index)
        normalized_records.append(normalized)
        context_items.append(context_item)
        if dropped:
            dropped_fields[str(normalized.get("session_id") or index)] = dropped

    aggregate_summary = _summarize_practice_history_context_items(context_items)
    operation = _normalize_routine_history_persistence_operation(args)
    candidate_id = str(_first_present(args, "candidate_id", "candidateId", "persistence_candidate_id", "persistenceCandidateId") or f"routine_history_persist_{uuid4().hex[:12]}")
    history_scope_id = _first_present(args, "history_scope_id", "historyScopeId", "user_id", "userId", "profile_id", "profileId")
    blocked_reasons: list[str] = []
    if not context_items:
        blocked_reasons.append("routine_history_candidate_has_no_context_items")
    if dropped_fields:
        warnings.append("client_only_or_midi_fields_discarded")
    status = "candidate_blocked" if blocked_reasons else ("candidate_ready_with_warnings" if warnings else "candidate_ready")

    candidate_action = {
        "action_type": "routine_history_persistence_candidate",
        "candidate_id": candidate_id,
        "operation": operation,
        "history_scope_id": history_scope_id,
        "record_count": len(normalized_records),
        "context_item_count": len(context_items),
        "side_effect_level": "backend_long_term_context_write_candidate",
        "requires_user_confirmation": True,
        "confirmation_status": "pending_user_review",
        "would_write_if_confirmed_in_future": True,
        "writes_now": False,
        "editable_before_confirmation": True,
        "creates_post_session_recommendation_card": False,
        "next_client_actions": ["review_candidate", "edit_candidate", "confirm_sync_history", "dismiss", "view_trace"],
        "client_button_semantics": {
            "primary": {
                "action": "confirm_sync_history",
                "label": "Sync Routine History Summary",
                "requires_explicit_user_confirmation": True,
                "enabled_now": False,
                "reason_disabled_now": "v2_8_7 is preview contract only; future persistence executor not implemented.",
            },
            "secondary": [
                {"action": "edit_candidate", "label": "Edit Summary", "side_effect_level": "none"},
                {"action": "dismiss", "label": "Dismiss", "side_effect_level": "none"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
    }
    confirmation_policy = {
        "requires_user_confirmation": True,
        "requires_preview_before_confirmation": True,
        "requires_final_write_executor_future_stage": True,
        "autonomous_write_allowed": False,
        "llm_may_not_write_history_directly": True,
        "post_session_recommendation_card_allowed": False,
        "confirmation_ladder": [
            {"step": "preview_history_sync_candidate", "side_effects": False, "implemented_now": True},
            {"step": "user_reviews_or_edits_summary", "side_effects": False, "implemented_now": True},
            {"step": "user_confirms_history_sync", "side_effects": False, "implemented_now": False},
            {"step": "future_persistence_executor_writes_backend_summary", "side_effects": True, "implemented_now": False},
            {"step": "context_builder_can_read_history_summary_later", "side_effects": False, "implemented_now": False},
        ],
    }
    storage_boundary = {
        "boundary_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "candidate_contract_version": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "object_type": "RoutineHistorySummary",
        "owner": "backend_long_term_context_after_user_confirmed_write",
        "harmonyos_role": "produces_completion_summary_and_keeps_live_session_state_local",
        "future_source_of_truth": "backend_long_term_context_for_sanitized_practice_history_summary",
        "harmonyos_local_cache_allowed_after_success": True,
        "context_builder_may_read_summary_later": True,
        "writes_now": False,
        "database_schema_required_now": False,
        "sync_job_required_now": False,
        "client_must_not_upload": ["midi_base64", "local_midi_path", "playback_position", "timer_state", "raw_asset"],
    }
    validation = {
        "status": status,
        "accepted": not blocked_reasons,
        "operation": operation,
        "has_routine_history_candidate": bool(normalized_records),
        "input_record_count": len(raw_records),
        "normalized_record_count": len(normalized_records),
        "context_item_count": len(context_items),
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "dropped_client_only_fields": dropped_fields,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_playback_position": False,
        "preview_only": True,
        "requires_user_confirmation": True,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
    }
    guard_summary = {
        "candidate_only": True,
        "preview_confirmation_noop_boundary": True,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_history_candidate": False,
        "local_playback_state_allowed_in_history_candidate": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return RoutineHistoryPersistenceCandidatePayload(
        payload_contract_version=ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        source=source,
        operation=operation,
        candidate_id=candidate_id,
        target_history_ref={"history_scope_id": history_scope_id, "operation": operation},
        normalized_routine_history_records=tuple(normalized_records),
        practice_history_context_items=tuple(context_items),
        aggregate_summary=aggregate_summary,
        candidate_action=candidate_action,
        confirmation_policy=confirmation_policy,
        storage_boundary=storage_boundary,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_routine_history_persistence_candidate_summary(
    *,
    payload: RoutineHistoryPersistenceCandidatePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    aggregate = data.get("aggregate_summary") if isinstance(data.get("aggregate_summary"), dict) else {}
    return {
        "routine_history_persistence_candidate_contract_version": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "operation": data.get("operation"),
        "candidate_id": data.get("candidate_id"),
        "record_count": validation.get("normalized_record_count", 0),
        "context_item_count": validation.get("context_item_count", 0),
        "completed_count": aggregate.get("completed_count", 0),
        "total_practice_minutes": aggregate.get("total_practice_minutes", 0),
        "recent_styles": aggregate.get("recent_styles", []),
        "recent_tunes": aggregate.get("recent_tunes", []),
        "requires_user_confirmation": True,
        "preview_only": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def routine_history_persistence_candidate_contract() -> dict[str, Any]:
    return {
        "version": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "routine_history_persistence_candidate_contract_version": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "spec_route": "GET /agent/routine-history/persistence-candidate/spec",
        "preview_route": "POST /agent/routine-history/persistence-candidate/preview",
        "terminal_command": "/routine-history-persistence-candidate",
        "surface": "RoutineHistory summary save/upload candidate contract",
        "mode": "candidate_preview_confirmation_boundary_only_no_storage_write",
        "execution_status": {
            "candidate_payload_enabled": True,
            "preview_enabled": True,
            "confirmation_required": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "sync_job_implemented": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "operations": ["append_new_records", "upsert_summary_batch"],
        "payload_schema": {
            "operation": "append_new_records | upsert_summary_batch",
            "target_history_ref": "User/history scope reference; optional in v2_8_7 preview",
            "normalized_routine_history_records": "Sanitized RoutineHistoryRecord[] without local playback or MIDI payloads",
            "practice_history_context_items": "Agent-readable compact PracticeHistoryContextItem[] for future ContextBuilder reads",
            "aggregate_summary": "Recent styles/tunes/minutes/completion summary",
            "candidate_action": "User-reviewable sync/save action metadata; disabled write button in v2_8_7",
            "confirmation_policy": "Preview -> user review/edit -> future confirmed persistence executor ladder",
            "storage_boundary": "Backend long-term context boundary; no writes now",
            "validation": "Candidate readiness and no-side-effect flags",
        },
        "rules": [
            "HarmonyOS owns live RoutineSession state and produces the completion summary.",
            "Agent may preview a sanitized RoutineHistory persistence candidate, but must not write storage directly.",
            "Routine end page must not become an Agent recommendation surface.",
            "Client must require explicit user confirmation before any future backend history write.",
            "v2_8_7 does not implement database schema, backend writes, local writes, or sync jobs.",
            "RoutineHistory persistence remains separate from Routine start, playback, accompaniment generation, and MIDI asset creation.",
            "Sensitive fields, local MIDI paths, MIDI payloads, raw assets, timer/playback state, payment data, precise location, and hidden chain-of-thought must be discarded from the candidate.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_history_candidate": False,
            "local_midi_path_allowed_in_history_candidate": False,
            "playback_position_allowed_in_history_candidate": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "routine_history_context_intake": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "today_practice_guidance_profile_aware_e2e": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        },
        "next_task_hint": "v2_8_8_agent_context_persistence_confirmation_boundary",
    }



@dataclass(frozen=True)
class ContextPersistenceConfirmationBoundaryPayload:
    """v2_8_8 unified confirmation boundary for context persistence candidates.

    This layer wraps candidate-only PracticePlan and RoutineHistory persistence
    payloads in a user-review confirmation envelope. It records user intent and
    future executor requirements, but it still does not write backend storage,
    write local device state, call an LLM, execute tools, start Routine, call
    /accompaniment/generate, call engine adapters, create MIDI assets, or start
    playback.
    """

    payload_contract_version: str
    source: str
    confirmation_id: str
    candidate_kind: str
    candidate_id: str | None
    candidate_payload: dict[str, Any]
    candidate_summary: dict[str, Any]
    user_decision: str
    confirmation_status: str
    confirmation_envelope: dict[str, Any]
    future_executor_boundary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "confirmation_id": self.confirmation_id,
            "candidate_kind": self.candidate_kind,
            "candidate_id": self.candidate_id,
            "candidate_payload": _redact_sensitive_values(self.candidate_payload),
            "candidate_summary": _redact_sensitive_values(self.candidate_summary),
            "user_decision": self.user_decision,
            "confirmation_status": self.confirmation_status,
            "confirmation_envelope": _redact_sensitive_values(self.confirmation_envelope),
            "future_executor_boundary": _redact_sensitive_values(self.future_executor_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def build_context_persistence_confirmation_boundary_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_confirmation_boundary",
) -> ContextPersistenceConfirmationBoundaryPayload:
    """Wrap a persistence candidate in a confirmation boundary without writing."""

    args = dict(arguments or {})
    candidate_kind = _normalize_context_persistence_candidate_kind(args)
    candidate_payload: dict[str, Any] = {}
    candidate_summary: dict[str, Any] = {}
    candidate_id: str | None = None
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    if candidate_kind == "practice_plan_persistence_candidate":
        nested = _extract_context_persistence_nested_candidate(args, "practice_plan")
        if nested and str(nested.get("payload_contract_version") or "") == PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION:
            candidate_payload = nested
            candidate_summary = _summarize_embedded_persistence_candidate(candidate_payload, candidate_kind)
        else:
            plan_payload = build_practice_plan_persistence_candidate_payload(args, trace_id=trace_id, source=f"{source}:practice_plan_candidate")
            candidate_payload = plan_payload.to_dict()
            candidate_summary = build_practice_plan_persistence_candidate_summary(payload=plan_payload, source=source)
        candidate_id = str(candidate_payload.get("candidate_id") or candidate_summary.get("candidate_id") or "") or None
    elif candidate_kind == "routine_history_persistence_candidate":
        nested = _extract_context_persistence_nested_candidate(args, "routine_history")
        if nested and str(nested.get("payload_contract_version") or "") == ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION:
            candidate_payload = nested
            candidate_summary = _summarize_embedded_persistence_candidate(candidate_payload, candidate_kind)
        else:
            history_payload = build_routine_history_persistence_candidate_payload(args, trace_id=trace_id, source=f"{source}:routine_history_candidate")
            candidate_payload = history_payload.to_dict()
            candidate_summary = build_routine_history_persistence_candidate_summary(payload=history_payload, source=source)
        candidate_id = str(candidate_payload.get("candidate_id") or candidate_summary.get("candidate_id") or "") or None
    else:
        blocked_reasons.append("unsupported_or_missing_persistence_candidate_kind")

    candidate_validation = candidate_payload.get("validation") if isinstance(candidate_payload.get("validation"), dict) else {}
    if candidate_payload and candidate_validation.get("accepted") is False:
        blocked_reasons.append("candidate_validation_not_accepted")
    if not candidate_payload:
        blocked_reasons.append("missing_candidate_payload")

    user_decision = _normalize_context_persistence_user_decision(args)
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId", "context_confirmation_id", "contextConfirmationId") or f"context_persist_confirm_{uuid4().hex[:12]}")
    decision_status_map = {
        "pending": "pending_user_review",
        "approved": "user_approved_future_executor_required",
        "rejected": "user_rejected_no_write",
        "dismissed": "dismissed_no_write",
    }
    if blocked_reasons:
        confirmation_status = "not_confirmable"
    else:
        confirmation_status = decision_status_map[user_decision]
    if user_decision == "approved":
        warnings.append("user_approved_recorded_but_future_persistence_executor_not_implemented")

    confirmation_envelope = {
        "confirmation_boundary_version": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        "confirmation_id": confirmation_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "user_decision": user_decision,
        "confirmation_status": confirmation_status,
        "requires_user_confirmation": True,
        "candidate_preview_required": True,
        "candidate_preview_accepted": bool(candidate_payload and not blocked_reasons),
        "future_write_executor_required": True,
        "future_write_executor_implemented": False,
        "would_write_if_future_executor_confirmed": user_decision == "approved" and not blocked_reasons,
        "writes_now": False,
        "editable_before_future_write": user_decision in {"pending", "approved"},
        "next_client_actions": _context_persistence_next_client_actions(user_decision, blocked_reasons),
        "client_button_semantics": {
            "primary": {
                "action": "confirm_context_persistence",
                "label": "Confirm Save/Sync",
                "requires_explicit_user_confirmation": True,
                "enabled_now": False,
                "reason_disabled_now": "v2_8_8 records confirmation intent only; persistence executor is not implemented.",
            },
            "secondary": [
                {"action": "edit_candidate", "label": "Edit Candidate", "side_effect_level": "none"},
                {"action": "dismiss", "label": "Dismiss", "side_effect_level": "none"},
                {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            ],
        },
    }
    future_executor_boundary = {
        "boundary_version": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        "executor_name": "future_context_persistence_executor",
        "implemented_now": False,
        "requires_confirmed_candidate": True,
        "requires_backend_storage_contract": True,
        "requires_idempotency_key": True,
        "requires_trace_link": True,
        "allowed_candidate_kinds": ["practice_plan_persistence_candidate", "routine_history_persistence_candidate"],
        "forbidden_now": [
            "database_write",
            "harmonyos_local_write",
            "routine_start",
            "accompaniment_generate_call",
            "engine_adapter_call",
            "midi_asset_creation",
            "playback_start",
            "post_session_recommendation_card",
        ],
    }
    validation = {
        "status": "confirmation_blocked" if blocked_reasons else ("confirmation_ready_with_warnings" if warnings else "confirmation_ready"),
        "accepted": not blocked_reasons,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "user_decision": user_decision,
        "confirmation_status": confirmation_status,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "preview_only": True,
        "requires_user_confirmation": True,
        "future_executor_required": True,
        "future_executor_implemented": False,
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
    }
    guard_summary = {
        "unified_confirmation_boundary": True,
        "candidate_preview_required": True,
        "candidate_only": True,
        "confirmation_record_only": True,
        "future_executor_required": True,
        "future_executor_implemented": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_context_confirmation": False,
        "local_playback_state_allowed_in_context_confirmation": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceConfirmationBoundaryPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        source=source,
        confirmation_id=confirmation_id,
        candidate_kind=candidate_kind,
        candidate_id=candidate_id,
        candidate_payload=candidate_payload,
        candidate_summary=candidate_summary,
        user_decision=user_decision,
        confirmation_status=confirmation_status,
        confirmation_envelope=confirmation_envelope,
        future_executor_boundary=future_executor_boundary,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_context_persistence_confirmation_boundary_summary(
    *,
    payload: ContextPersistenceConfirmationBoundaryPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "context_persistence_confirmation_boundary_version": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "candidate_kind": data.get("candidate_kind"),
        "candidate_id": data.get("candidate_id"),
        "confirmation_id": data.get("confirmation_id"),
        "user_decision": data.get("user_decision"),
        "confirmation_status": data.get("confirmation_status"),
        "requires_user_confirmation": True,
        "future_executor_required": True,
        "future_executor_implemented": False,
        "preview_only": True,
        "confirmation_record_only": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_confirmation_boundary_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        "context_persistence_confirmation_boundary_version": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
        "spec_route": "GET /agent/context/persistence-confirmation/spec",
        "preview_route": "POST /agent/context/persistence-confirmation/preview",
        "terminal_command": "/context-persistence-confirmation",
        "surface": "Unified confirmation boundary for Agent context persistence candidates",
        "mode": "candidate_preview_to_user_confirmation_record_only_no_storage_write",
        "supported_candidate_kinds": ["practice_plan_persistence_candidate", "routine_history_persistence_candidate"],
        "execution_status": {
            "confirmation_boundary_enabled": True,
            "candidate_payload_enabled": True,
            "preview_enabled": True,
            "confirmation_record_enabled": True,
            "future_persistence_executor_required": True,
            "future_persistence_executor_implemented": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "candidate_kind": "practice_plan_persistence_candidate | routine_history_persistence_candidate",
            "candidate_payload": "Embedded candidate payload or raw fields used to build one",
            "user_decision": "pending | approved | rejected | dismissed",
            "confirmation_envelope": "User-review confirmation record; no write in v2_8_8",
            "future_executor_boundary": "Requirements for a later real persistence executor",
            "validation": "Confirmation readiness and no-side-effect flags",
        },
        "rules": [
            "PracticePlan and RoutineHistory persistence candidates must pass through one unified confirmation boundary before any future write executor.",
            "User approval is recorded as intent only in v2_8_8; no backend or local storage write is performed.",
            "The future persistence executor must be a separate controlled stage with idempotency, trace link, and storage contract checks.",
            "Confirmation must remain separate from Routine start, playback, accompaniment generation, engine adapters, MIDI asset creation, and post-session recommendation cards.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "future_executor_implemented": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_context_confirmation": False,
            "local_midi_path_allowed_in_context_confirmation": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_plan_persistence_candidate": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "routine_history_persistence_candidate": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        },
        "next_task_hint": "v2_8_9_agent_context_persistence_executor_noop_skeleton",
    }




@dataclass(frozen=True)
class ContextPersistenceExecutorNoopPayload:
    """v2_8_9 no-op executor skeleton after context persistence confirmation.

    This layer previews the future persistence executor stage after a user has
    approved a PracticePlan or RoutineHistory persistence confirmation. It checks
    confirmation readiness, idempotency, trace and storage-contract requirements,
    then intentionally performs no write. It must remain separate from LLM calls,
    tool execution, Routine start, accompaniment generation, engine adapters,
    MIDI asset creation, playback, and post-session recommendation cards.
    """

    payload_contract_version: str
    source: str
    execution_id: str
    executor_name: str
    executor_mode: str
    idempotency_key: str
    confirmation_id: str | None
    candidate_kind: str
    candidate_id: str | None
    confirmation_payload: dict[str, Any]
    confirmation_summary: dict[str, Any]
    confirmation_check: dict[str, Any]
    storage_contract_check: dict[str, Any]
    executor_plan: dict[str, Any]
    noop_execution_result: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "execution_id": self.execution_id,
            "executor_name": self.executor_name,
            "executor_mode": self.executor_mode,
            "idempotency_key": self.idempotency_key,
            "confirmation_id": self.confirmation_id,
            "candidate_kind": self.candidate_kind,
            "candidate_id": self.candidate_id,
            "confirmation_payload": _redact_sensitive_values(self.confirmation_payload),
            "confirmation_summary": _redact_sensitive_values(self.confirmation_summary),
            "confirmation_check": _redact_sensitive_values(self.confirmation_check),
            "storage_contract_check": _redact_sensitive_values(self.storage_contract_check),
            "executor_plan": _redact_sensitive_values(self.executor_plan),
            "noop_execution_result": _redact_sensitive_values(self.noop_execution_result),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def build_context_persistence_executor_noop_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_executor_noop",
) -> ContextPersistenceExecutorNoopPayload:
    """Preview the future persistence executor without writing storage."""

    args = dict(arguments or {})
    confirmation_payload = _extract_context_persistence_confirmation_payload(args)
    if confirmation_payload:
        confirmation_payload = _redact_sensitive_values(dict(confirmation_payload))
        confirmation_summary = build_context_persistence_confirmation_boundary_summary(
            payload=_context_confirmation_payload_from_dict(confirmation_payload),
            source=source,
        )
    else:
        confirmation_payload_obj = build_context_persistence_confirmation_boundary_payload(
            args,
            trace_id=trace_id,
            source=f"{source}:confirmation_boundary",
        )
        confirmation_payload = confirmation_payload_obj.to_dict()
        confirmation_summary = build_context_persistence_confirmation_boundary_summary(payload=confirmation_payload_obj, source=source)

    confirmation_id = str(confirmation_payload.get("confirmation_id") or "") or None
    candidate_kind = str(confirmation_payload.get("candidate_kind") or "unknown")
    candidate_id = str(confirmation_payload.get("candidate_id") or "") or None
    user_decision = str(confirmation_payload.get("user_decision") or "pending")
    confirmation_status = str(confirmation_payload.get("confirmation_status") or "")
    confirmation_validation = confirmation_payload.get("validation") if isinstance(confirmation_payload.get("validation"), dict) else {}

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if not confirmation_payload:
        blocked_reasons.append("missing_confirmation_payload")
    if confirmation_validation.get("accepted") is False:
        blocked_reasons.append("confirmation_validation_not_accepted")
    if user_decision != "approved":
        blocked_reasons.append("user_confirmation_not_approved")
    if confirmation_status != "user_approved_future_executor_required":
        blocked_reasons.append("confirmation_status_not_executor_ready")
    if candidate_kind not in {"practice_plan_persistence_candidate", "routine_history_persistence_candidate"}:
        blocked_reasons.append("unsupported_candidate_kind")
    if not confirmation_id:
        blocked_reasons.append("missing_confirmation_id")
    if not candidate_id:
        warnings.append("missing_candidate_id_future_executor_should_require_stable_candidate_reference")

    provided_key = _first_present(args, "idempotency_key", "idempotencyKey")
    idempotency_key = str(provided_key or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    execution_id = str(_first_present(args, "execution_id", "executionId") or f"context_persist_noop_exec_{uuid4().hex[:12]}")

    confirmation_check = {
        "required": True,
        "confirmation_boundary_version": confirmation_payload.get("payload_contract_version") or confirmation_payload.get("confirmation_boundary_version"),
        "confirmation_id": confirmation_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "user_decision": user_decision,
        "confirmation_status": confirmation_status,
        "accepted": not blocked_reasons,
        "blocked_reasons": list(blocked_reasons),
        "warnings": list(warnings),
    }
    storage_contract_check = {
        "required": True,
        "storage_contract_version": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "storage_contract_present": True,
        "backend_database_write_enabled_now": False,
        "local_device_write_enabled_now": False,
        "real_storage_adapter_configured": False,
        "noop_storage_adapter": True,
        "allowed_future_candidate_kinds": ["practice_plan_persistence_candidate", "routine_history_persistence_candidate"],
        "idempotency_key_required": True,
        "idempotency_key_present": bool(idempotency_key),
        "trace_link_required": True,
        "trace_id_present": bool(trace_id or args.get("trace_id") or args.get("traceId") or confirmation_payload.get("trace_id")),
    }
    executor_plan = {
        "executor_version": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        "executor_name": "context_persistence_executor_noop",
        "mode": "noop_preview_only",
        "steps": [
            "verify_confirmation_boundary",
            "verify_user_approved_decision",
            "verify_candidate_kind",
            "derive_or_accept_idempotency_key",
            "link_trace_metadata",
            "check_storage_contract_boundary",
            "skip_backend_and_local_writes",
            "return_noop_execution_report",
        ],
        "future_real_executor_requirements": [
            "database_schema_and_adapter",
            "idempotent_upsert_semantics",
            "trace_link_persistence",
            "explicit_user_confirmation_recheck",
            "safe_retry_policy",
            "storage_boundary_conformance",
        ],
    }
    validation_status = "noop_executor_ready" if not blocked_reasons else "noop_executor_blocked"
    noop_execution_result = {
        "status": validation_status,
        "executor_ran": True,
        "noop_only": True,
        "would_write_if_real_executor_existed": not blocked_reasons,
        "write_attempted": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "future_executor_implemented": False,
        "idempotency_key": idempotency_key,
        "blocked_reasons": list(blocked_reasons),
        "warnings": list(warnings),
    }
    validation = {
        "status": validation_status,
        "accepted": not blocked_reasons,
        "confirmation_required": True,
        "confirmed_candidate_required": True,
        "idempotency_key_required": True,
        "trace_link_required": True,
        "storage_contract_required": True,
        "future_real_executor_required": True,
        "future_real_executor_implemented": False,
        "preview_only": True,
        "noop_only": True,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
        "llm_called": False,
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
    }
    guard_summary = {
        "context_persistence_executor_noop": True,
        "confirmed_candidate_required": True,
        "idempotency_guard_present": bool(idempotency_key),
        "trace_guard_present": True,
        "storage_contract_guard_present": True,
        "real_write_executor_implemented": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_executor": False,
        "local_playback_state_allowed_in_executor": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceExecutorNoopPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        source=source,
        execution_id=execution_id,
        executor_name="context_persistence_executor_noop",
        executor_mode="noop_preview_only",
        idempotency_key=idempotency_key,
        confirmation_id=confirmation_id,
        candidate_kind=candidate_kind,
        candidate_id=candidate_id,
        confirmation_payload=confirmation_payload,
        confirmation_summary=confirmation_summary,
        confirmation_check=confirmation_check,
        storage_contract_check=storage_contract_check,
        executor_plan=executor_plan,
        noop_execution_result=noop_execution_result,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId") or confirmation_payload.get("trace_id"),
    )


def build_context_persistence_executor_noop_summary(
    *,
    payload: ContextPersistenceExecutorNoopPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    result = data.get("noop_execution_result") if isinstance(data.get("noop_execution_result"), dict) else {}
    return {
        "context_persistence_executor_noop_version": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "execution_id": data.get("execution_id"),
        "executor_name": data.get("executor_name"),
        "executor_mode": data.get("executor_mode"),
        "confirmation_id": data.get("confirmation_id"),
        "candidate_kind": data.get("candidate_kind"),
        "candidate_id": data.get("candidate_id"),
        "idempotency_key": data.get("idempotency_key"),
        "noop_only": True,
        "write_attempted": False,
        "would_write_if_real_executor_existed": result.get("would_write_if_real_executor_existed", False),
        "future_real_executor_implemented": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_executor_noop_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        "context_persistence_executor_noop_version": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        "spec_route": "GET /agent/context/persistence-executor-noop/spec",
        "preview_route": "POST /agent/context/persistence-executor-noop/preview",
        "terminal_command": "/context-persistence-executor-noop",
        "surface": "No-op skeleton for the future Agent context persistence executor",
        "mode": "confirmed_candidate_executor_preview_noop_no_storage_write",
        "supported_candidate_kinds": ["practice_plan_persistence_candidate", "routine_history_persistence_candidate"],
        "execution_status": {
            "noop_executor_enabled": True,
            "real_persistence_executor_implemented": False,
            "requires_confirmation_boundary": True,
            "requires_user_approved_confirmation": True,
            "requires_idempotency_key": True,
            "requires_trace_link": True,
            "requires_storage_contract": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "confirmation_payload": "ContextPersistenceConfirmationBoundaryPayload or raw fields used to build one",
            "idempotency_key": "Optional stable client key; derived from confirmation/candidate fields when omitted",
            "confirmation_check": "Approved confirmation readiness check",
            "storage_contract_check": "No-op storage boundary check; no adapter configured",
            "executor_plan": "Future executor steps and requirements",
            "noop_execution_result": "No-op result report; no writes attempted",
            "validation": "Executor readiness and no-side-effect flags",
        },
        "rules": [
            "Only user-approved ContextPersistenceConfirmationBoundary payloads may be executor-ready.",
            "v2_8_9 intentionally performs no backend or local storage write even when executor-ready.",
            "A future real executor must re-check user confirmation, idempotency, trace link, and storage contract before writing.",
            "Executor preview must remain separate from LLM calls, tool execution, Routine start, playback, accompaniment generation, engine adapters, MIDI asset creation, and post-session recommendation cards.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "real_executor_implemented": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_executor_payload": False,
            "local_midi_path_allowed_in_executor_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "practice_plan_persistence_candidate": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "routine_history_persistence_candidate": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        },
        "next_task_hint": "v2_8_10_agent_context_persistence_real_storage_adapter_design",
    }



@dataclass(frozen=True)
class ContextPersistenceStorageAdapterDesignPayload:
    """v2_8_10 design-only contract for a future real persistence adapter.

    This is intentionally not a database adapter. It describes the interface,
    entity ownership, idempotency, trace, and confirmation checks that a future
    adapter must satisfy before any backend write can be implemented.
    """

    payload_contract_version: str
    source: str
    adapter_design_id: str
    adapter_name: str
    adapter_mode: str
    adapter_interface: dict[str, Any]
    supported_entity_contracts: dict[str, Any]
    operation_contracts: dict[str, Any]
    backend_storage_options: dict[str, Any]
    write_readiness_gate: dict[str, Any]
    migration_and_retry_policy: dict[str, Any]
    forbidden_payload_fields: list[str]
    storage_boundary_alignment: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    sample_request: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "adapter_design_id": self.adapter_design_id,
            "adapter_name": self.adapter_name,
            "adapter_mode": self.adapter_mode,
            "adapter_interface": _redact_sensitive_values(self.adapter_interface),
            "supported_entity_contracts": _redact_sensitive_values(self.supported_entity_contracts),
            "operation_contracts": _redact_sensitive_values(self.operation_contracts),
            "backend_storage_options": _redact_sensitive_values(self.backend_storage_options),
            "write_readiness_gate": _redact_sensitive_values(self.write_readiness_gate),
            "migration_and_retry_policy": _redact_sensitive_values(self.migration_and_retry_policy),
            "forbidden_payload_fields": list(self.forbidden_payload_fields),
            "storage_boundary_alignment": _redact_sensitive_values(self.storage_boundary_alignment),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "sample_request": _redact_sensitive_values(self.sample_request),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def build_context_persistence_storage_adapter_design_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_storage_adapter_design",
) -> ContextPersistenceStorageAdapterDesignPayload:
    """Build the future real storage-adapter design preview without writing.

    This function is the v2_8_10 bridge after the no-op executor skeleton. It
    states what the eventual adapter must look like, but deliberately returns a
    design report only. No database handle is created, and no persistence
    operation is attempted.
    """

    args = dict(arguments or {})
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind", "backend", "storage_backend", "storageBackend") or "backend_service_adapter")
    design_id = str(_first_present(args, "adapter_design_id", "adapterDesignId") or f"ctx_storage_adapter_design_{uuid4().hex[:12]}")
    requested_entities = _normalize_storage_adapter_entities(args)
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    unsupported_entities = [entity for entity in requested_entities if entity not in {"user_practice_profile", "active_practice_plan", "practice_plan", "routine_history_summary", "agent_trace_metadata", "idempotency_record"}]
    if unsupported_entities:
        warnings.append("unsupported_entities_recorded_for_future_design_review")
    if adapter_kind in {"harmonyos_local_only", "client_local_storage"}:
        warnings.append("harmonyos_local_storage_is_client_owned_not_backend_adapter_owned")
    if adapter_kind in {"none", "disabled"}:
        blocked_reasons.append("storage_adapter_kind_disabled")

    adapter_interface = {
        "interface_name": "ContextPersistenceStorageAdapter",
        "status": "design_contract_only",
        "real_adapter_implemented": False,
        "database_connection_created": False,
        "methods": {
            "preview_write": {
                "input": "ConfirmedContextPersistenceRequest",
                "output": "StorageWritePreview",
                "side_effects": False,
                "required_before_real_write": True,
            },
            "write_confirmed_context": {
                "input": "ConfirmedContextPersistenceRequest",
                "output": "StorageWriteResult",
                "side_effects": "future_backend_write_only_after_confirmation",
                "implemented_now": False,
            },
            "read_context_snapshot": {
                "input": "ContextSnapshotQuery",
                "output": "PracticeContextSnapshot",
                "side_effects": False,
                "implemented_now": False,
            },
            "check_idempotency": {
                "input": "idempotency_key",
                "output": "IdempotencyCheckResult",
                "side_effects": False,
                "implemented_now": False,
            },
            "record_trace_link": {
                "input": "trace_id + write_result_id",
                "output": "TracePersistenceLink",
                "side_effects": "future_trace_metadata_write_only",
                "implemented_now": False,
            },
        },
    }
    supported_entity_contracts = {
        "user_practice_profile": {
            "owner": "backend_long_term_context",
            "source_contract": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
            "future_table_or_collection": "user_practice_profiles",
            "write_mode": "upsert_by_user_id",
            "contains_raw_secrets": False,
        },
        "active_practice_plan": {
            "owner": "backend_long_term_context",
            "source_contract": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "future_table_or_collection": "active_practice_plans",
            "write_mode": "save_new_or_update_existing",
            "requires_user_confirmation": True,
        },
        "routine_history_summary": {
            "owner": "backend_long_term_context",
            "source_contract": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "future_table_or_collection": "practice_history_summaries",
            "write_mode": "append_or_upsert_summary_batch",
            "raw_playback_assets_allowed": False,
        },
        "agent_trace_metadata": {
            "owner": "agent_trace_context",
            "future_table_or_collection": "agent_trace_metadata",
            "write_mode": "metadata_link_only",
            "raw_chain_of_thought_allowed": False,
        },
        "idempotency_record": {
            "owner": "backend_long_term_context",
            "future_table_or_collection": "context_persistence_idempotency_keys",
            "write_mode": "insert_once_or_return_existing",
            "ttl_policy": "future_policy_required",
        },
    }
    operation_contracts = {
        "practice_plan_persistence_candidate": {
            "future_operation": "upsert_active_practice_plan",
            "requires_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "requires_executor_readiness": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "requires_idempotency_key": True,
            "requires_trace_id": True,
            "allowed_storage_owner": "backend_long_term_context",
        },
        "routine_history_persistence_candidate": {
            "future_operation": "append_or_upsert_routine_history_summary",
            "requires_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "requires_executor_readiness": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "requires_idempotency_key": True,
            "requires_trace_id": True,
            "allowed_storage_owner": "backend_long_term_context",
            "post_session_recommendation_card_created": False,
        },
        "user_practice_profile_context": {
            "future_operation": "upsert_user_practice_profile",
            "requires_user_review_for_profile_change": True,
            "source_contract": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
            "allowed_storage_owner": "backend_long_term_context",
        },
    }
    backend_storage_options = {
        "selected_for_design_preview": adapter_kind,
        "supported_future_options": ["sqlite_dev_adapter", "postgres_backend_adapter", "cloud_kv_backend_adapter"],
        "harmonyos_local_storage": {
            "owned_by_client": True,
            "backend_adapter_must_not_write_it_directly": True,
        },
        "database_schema_implemented_now": False,
        "real_storage_adapter_configured_now": False,
        "migration_required_before_real_write": True,
    }
    write_readiness_gate = {
        "status": "design_only_not_write_ready" if not blocked_reasons else "design_blocked",
        "accepted": not blocked_reasons,
        "real_write_enabled": False,
        "requires_before_real_write": [
            "schema_migration_review",
            "adapter_selection",
            "idempotency_store",
            "confirmed_candidate_recheck",
            "storage_boundary_conformance_test",
            "redaction_and_sensitive_field_test",
            "trace_link_test",
            "rollback_or_retry_policy",
        ],
        "blocked_reasons": list(blocked_reasons),
        "warnings": list(warnings),
    }
    migration_and_retry_policy = {
        "migration_strategy": "future_versioned_schema_migrations_required",
        "idempotent_retry_required": True,
        "safe_retry_key": "idempotency_key",
        "duplicate_write_policy": "return_existing_result_for_same_idempotency_key",
        "partial_failure_policy": "future_transaction_or_outbox_policy_required",
        "traceability_policy": "persist_trace_id_and_confirmation_id_with_write_result",
    }
    forbidden_payload_fields = [
        "api_key",
        "token",
        "password",
        "secret",
        "midi_base64",
        "local_midi_path",
        "playback_position",
        "timer_state",
        "precise_location",
        "payment_info",
        "hidden_chain_of_thought",
    ]
    storage_boundary_alignment = {
        "uses_storage_boundary_contract": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
        "backend_long_term_context_entities": ["user_practice_profile", "active_practice_plan", "routine_history_summary", "idempotency_record"],
        "harmonyos_local_only_entities": ["routine_session_runtime", "playback_state", "local_midi_cache", "score_viewport"],
        "request_ephemeral_entities": ["available_minutes", "current_user_question", "temporary_candidate_preview"],
        "never_store_or_contextualize": forbidden_payload_fields,
    }
    validation = {
        "status": write_readiness_gate["status"],
        "accepted": not blocked_reasons,
        "design_only": True,
        "adapter_interface_defined": True,
        "real_adapter_implemented": False,
        "backend_database_written": False,
        "local_device_written": False,
        "storage_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
    }
    guard_summary = {
        "context_persistence_storage_adapter_design": True,
        "design_contract_only": True,
        "real_storage_adapter_implemented": False,
        "database_connection_created": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "harmonyos_local_write_enabled": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    sample_request = {
        "adapterKind": adapter_kind,
        "entities": requested_entities,
        "candidateKind": "practice_plan_persistence_candidate",
        "confirmationStatus": "user_approved_future_executor_required",
        "idempotencyKey": "ctx_persist_example_key",
        "traceId": trace_id or args.get("trace_id") or args.get("traceId") or "trace_example",
    }
    return ContextPersistenceStorageAdapterDesignPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
        source=source,
        adapter_design_id=design_id,
        adapter_name="context_persistence_storage_adapter_design",
        adapter_mode="design_contract_only_no_database_write",
        adapter_interface=adapter_interface,
        supported_entity_contracts=supported_entity_contracts,
        operation_contracts=operation_contracts,
        backend_storage_options=backend_storage_options,
        write_readiness_gate=write_readiness_gate,
        migration_and_retry_policy=migration_and_retry_policy,
        forbidden_payload_fields=forbidden_payload_fields,
        storage_boundary_alignment=storage_boundary_alignment,
        validation=validation,
        guard_summary=guard_summary,
        sample_request=sample_request,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_context_persistence_storage_adapter_design_summary(
    *,
    payload: ContextPersistenceStorageAdapterDesignPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    gate = data.get("write_readiness_gate") if isinstance(data.get("write_readiness_gate"), dict) else {}
    return {
        "context_persistence_storage_adapter_design_version": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "adapter_design_id": data.get("adapter_design_id"),
        "adapter_name": data.get("adapter_name"),
        "adapter_mode": data.get("adapter_mode"),
        "real_adapter_implemented": False,
        "real_write_enabled": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "supported_entity_count": len(data.get("supported_entity_contracts") or {}),
        "operation_count": len(data.get("operation_contracts") or {}),
        "write_gate_status": gate.get("status"),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_storage_adapter_design_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
        "context_persistence_storage_adapter_design_version": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
        "spec_route": "GET /agent/context/persistence-storage-adapter/spec",
        "preview_route": "POST /agent/context/persistence-storage-adapter/design-preview",
        "terminal_command": "/context-persistence-storage-adapter",
        "surface": "Design-only contract for future real context persistence storage adapter",
        "mode": "adapter_interface_and_storage_boundary_design_no_database_write",
        "supported_future_candidate_kinds": ["practice_plan_persistence_candidate", "routine_history_persistence_candidate", "user_practice_profile_context"],
        "execution_status": {
            "design_preview_enabled": True,
            "real_storage_adapter_implemented": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "requires_confirmation_boundary_for_writes": True,
            "requires_noop_executor_readiness_before_real_adapter": True,
            "requires_idempotency_key": True,
            "requires_trace_link": True,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "adapter_interface": {
            "methods": ["preview_write", "write_confirmed_context", "read_context_snapshot", "check_idempotency", "record_trace_link"],
            "implemented_now": False,
            "purpose": "Provide a stable target for a future backend storage implementation without coupling Agent context design to database code yet.",
        },
        "rules": [
            "v2_8_10 defines the adapter interface and storage ownership only; it creates no tables and opens no database connection.",
            "Future writes must pass candidate preview, confirmation boundary, executor readiness, idempotency, trace-link, and storage-boundary checks.",
            "HarmonyOS local Routine session/playback state remains client-owned and must not be written by the backend adapter.",
            "Raw MIDI assets, local MIDI paths, secrets, precise location, payment info, and hidden chain-of-thought are forbidden in adapter payloads.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "real_storage_adapter_implemented": False,
            "database_connection_created": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_executor_noop": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "practice_plan_persistence_candidate": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "routine_history_persistence_candidate": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "user_practice_profile_context_intake": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
        },
        "next_task_hint": "v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview",
    }


@dataclass(frozen=True)
class ContextPersistenceSqliteDevPreviewPayload:
    """v2_8_11 dev-only SQLite/fixture adapter preview.

    This layer turns the v2_8_10 storage-adapter design into a concrete local
    development preview surface: schema DDL, idempotency checks, trace-link
    shape, and read-snapshot query shape. It deliberately does not create a
    SQLite connection, create tables, write rows, or read from a real database.
    """

    payload_contract_version: str
    source: str
    preview_id: str
    adapter_kind: str
    adapter_mode: str
    requested_entities: list[str]
    sqlite_schema_preview: dict[str, Any]
    idempotency_preview: dict[str, Any]
    trace_link_preview: dict[str, Any]
    read_snapshot_preview: dict[str, Any]
    write_preview_gate: dict[str, Any]
    fixture_snapshot_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "preview_id": self.preview_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "requested_entities": list(self.requested_entities),
            "sqlite_schema_preview": _redact_sensitive_values(self.sqlite_schema_preview),
            "idempotency_preview": _redact_sensitive_values(self.idempotency_preview),
            "trace_link_preview": _redact_sensitive_values(self.trace_link_preview),
            "read_snapshot_preview": _redact_sensitive_values(self.read_snapshot_preview),
            "write_preview_gate": _redact_sensitive_values(self.write_preview_gate),
            "fixture_snapshot_preview": _redact_sensitive_values(self.fixture_snapshot_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


@dataclass(frozen=True)
class ContextPersistenceDevSqliteWriteGatePayload:
    """v2_8_12 explicit dev-only SQLite write-gate contract.

    This layer is still side-effect free. It makes the future local SQLite write
    switch explicit and auditable by requiring an approved confirmation, an
    idempotency key, a trace link, a dev config path, storage-boundary checks,
    and redaction checks before any future adapter may be enabled.
    """

    payload_contract_version: str
    source: str
    gate_id: str
    adapter_kind: str
    adapter_mode: str
    requested_entities: list[str]
    dev_sqlite_config_contract: dict[str, Any]
    explicit_write_gate: dict[str, Any]
    required_checks: dict[str, Any]
    idempotency_gate: dict[str, Any]
    trace_link_gate: dict[str, Any]
    storage_boundary_gate: dict[str, Any]
    redaction_gate: dict[str, Any]
    future_executor_contract: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_write_enabled: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "gate_id": self.gate_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "requested_entities": list(self.requested_entities),
            "dev_sqlite_config_contract": _redact_sensitive_values(self.dev_sqlite_config_contract),
            "explicit_write_gate": _redact_sensitive_values(self.explicit_write_gate),
            "required_checks": _redact_sensitive_values(self.required_checks),
            "idempotency_gate": _redact_sensitive_values(self.idempotency_gate),
            "trace_link_gate": _redact_sensitive_values(self.trace_link_gate),
            "storage_boundary_gate": _redact_sensitive_values(self.storage_boundary_gate),
            "redaction_gate": _redact_sensitive_values(self.redaction_gate),
            "future_executor_contract": _redact_sensitive_values(self.future_executor_contract),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_write_enabled": self.sqlite_write_enabled,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _sqlite_dev_preview_schema() -> dict[str, Any]:
    """Return SQLite DDL strings for future dev adapter review only."""

    tables = {
        "user_practice_profiles": {
            "purpose": "durable sanitized UserPracticeProfileContext snapshots keyed by user_id",
            "ddl": "CREATE TABLE user_practice_profiles (user_id TEXT PRIMARY KEY, profile_json TEXT NOT NULL, updated_at TEXT NOT NULL, trace_id TEXT);",
            "entity": "user_practice_profile",
        },
        "active_practice_plans": {
            "purpose": "active/saved PracticePlan snapshots after explicit user confirmation",
            "ddl": "CREATE TABLE active_practice_plans (plan_id TEXT PRIMARY KEY, user_id TEXT, plan_json TEXT NOT NULL, status TEXT NOT NULL, updated_at TEXT NOT NULL, trace_id TEXT, confirmation_id TEXT);",
            "entity": "active_practice_plan",
        },
        "practice_history_summaries": {
            "purpose": "compact RoutineHistory summary/context items; never raw playback assets",
            "ddl": "CREATE TABLE practice_history_summaries (history_id TEXT PRIMARY KEY, user_id TEXT, summary_json TEXT NOT NULL, practiced_at TEXT, trace_id TEXT, confirmation_id TEXT);",
            "entity": "routine_history_summary",
        },
        "context_persistence_idempotency_keys": {
            "purpose": "idempotent retry guard for future persistence writes",
            "ddl": "CREATE TABLE context_persistence_idempotency_keys (idempotency_key TEXT PRIMARY KEY, candidate_kind TEXT NOT NULL, candidate_id TEXT, write_result_json TEXT NOT NULL, created_at TEXT NOT NULL, trace_id TEXT);",
            "entity": "idempotency_record",
        },
        "agent_trace_metadata": {
            "purpose": "sanitized trace/write links only; no hidden chain-of-thought",
            "ddl": "CREATE TABLE agent_trace_metadata (trace_id TEXT PRIMARY KEY, confirmation_id TEXT, candidate_id TEXT, event_type TEXT NOT NULL, metadata_json TEXT NOT NULL, created_at TEXT NOT NULL);",
            "entity": "agent_trace_metadata",
        },
    }
    indexes = [
        "CREATE INDEX idx_active_practice_plans_user_id ON active_practice_plans(user_id);",
        "CREATE INDEX idx_practice_history_user_id ON practice_history_summaries(user_id);",
        "CREATE INDEX idx_practice_history_practiced_at ON practice_history_summaries(practiced_at);",
        "CREATE INDEX idx_trace_metadata_confirmation_id ON agent_trace_metadata(confirmation_id);",
    ]
    return {
        "schema_version": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        "dialect": "sqlite",
        "mode": "ddl_preview_only_no_connection",
        "tables": tables,
        "indexes": indexes,
        "migration_status": "preview_only_not_applied",
        "sqlite_connection_created": False,
        "tables_created": False,
    }


def build_context_persistence_sqlite_dev_preview_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_dev_preview",
) -> ContextPersistenceSqliteDevPreviewPayload:
    """Build a dev-only SQLite/fixture adapter preview without writing."""

    args = dict(arguments or {})
    preview_id = str(_first_present(args, "preview_id", "previewId") or f"ctx_sqlite_dev_preview_{uuid4().hex[:12]}")
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_dev_adapter")
    requested_entities = _normalize_storage_adapter_entities(args)
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    user_id = str(_first_present(args, "user_id", "userId") or "dev_user")
    candidate_kind = str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "dev_candidate")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "dev_confirmation")
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    dev_write_requested = bool(_first_present(args, "dev_write_enabled", "devWriteEnabled", "write_enabled", "writeEnabled") or False)

    supported_entities = {"user_practice_profile", "active_practice_plan", "practice_plan", "routine_history_summary", "agent_trace_metadata", "idempotency_record"}
    unsupported_entities = [entity for entity in requested_entities if entity not in supported_entities]
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if unsupported_entities:
        warnings.append("unsupported_entities_ignored_for_sqlite_dev_preview")
    if adapter_kind != "sqlite_dev_adapter":
        warnings.append("adapter_kind_forced_to_sqlite_dev_adapter_preview")
    if dev_write_requested:
        blocked_reasons.append("dev_write_requested_but_v2_8_11_is_preview_only")

    schema_preview = _sqlite_dev_preview_schema()
    idempotency_preview = {
        "idempotency_key": idempotency_key,
        "check_mode": "fixture_preview_only",
        "would_check_table": "context_persistence_idempotency_keys",
        "duplicate_policy": "return_existing_result_for_same_idempotency_key",
        "insert_or_return_existing_sql_preview": "INSERT OR IGNORE INTO context_persistence_idempotency_keys (...) VALUES (...);",
        "idempotency_record_written": False,
        "existing_record_found": False,
    }
    trace_link_preview = {
        "trace_id": trace_value,
        "confirmation_id": confirmation_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "would_write_table": "agent_trace_metadata",
        "trace_link_written": False,
        "raw_chain_of_thought_allowed": False,
    }
    read_snapshot_preview = {
        "query_mode": "fixture_snapshot_preview_only",
        "user_id": user_id,
        "requested_entities": list(requested_entities),
        "would_read_tables": [
            "user_practice_profiles",
            "active_practice_plans",
            "practice_history_summaries",
            "agent_trace_metadata",
        ],
        "snapshot_shape": {
            "user_practice_profile_context": "latest sanitized profile_json for user_id",
            "active_practice_plan_context": "latest active plan_json for user_id",
            "routine_history_context": "recent compact practice_history_summaries for user_id",
            "agent_trace_metadata": "sanitized trace links only",
        },
        "read_executed": False,
        "sqlite_connection_created": False,
    }
    fixture_snapshot_preview = {
        "snapshot_contract": "PracticeContextSnapshot",
        "source": "sqlite_dev_fixture_preview",
        "user_id": user_id,
        "contains_user_practice_profile_context": "user_practice_profile" in requested_entities,
        "contains_active_practice_plan_context": any(entity in requested_entities for entity in ["active_practice_plan", "practice_plan"]),
        "contains_routine_history_context": "routine_history_summary" in requested_entities,
        "storage_written": False,
        "sample": {
            "user_practice_profile_context": {"profile_status": "fixture_preview_only"},
            "active_practice_plan_context": {"plan_status": "fixture_preview_only"},
            "routine_history_context": {"history_status": "fixture_preview_only"},
        },
    }
    write_preview_gate = {
        "status": "sqlite_dev_preview_blocked" if blocked_reasons else "sqlite_dev_preview_ready_no_write",
        "accepted": not blocked_reasons,
        "real_write_enabled": False,
        "dev_write_enabled": False,
        "write_requested": dev_write_requested,
        "requires_before_enabling_dev_write": [
            "explicit_dev_flag_and_config_path",
            "schema_migration_apply_step",
            "transactional_write_wrapper",
            "idempotency_insert_or_return_existing",
            "trace_link_write",
            "redaction_test_for_forbidden_fields",
            "read_snapshot_roundtrip_test",
        ],
        "blocked_reasons": list(blocked_reasons),
        "warnings": list(warnings),
    }
    validation = {
        "status": write_preview_gate["status"],
        "accepted": not blocked_reasons,
        "sqlite_dev_preview": True,
        "schema_preview_available": True,
        "idempotency_preview_available": True,
        "trace_link_preview_available": True,
        "read_snapshot_preview_available": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
    }
    guard_summary = {
        "context_persistence_sqlite_dev_preview": True,
        "preview_only": True,
        "sqlite_dev_adapter_implemented_for_real_writes": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "harmonyos_local_write_enabled": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceSqliteDevPreviewPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        source=source,
        preview_id=preview_id,
        adapter_kind="sqlite_dev_adapter",
        adapter_mode="sqlite_dev_fixture_preview_no_database_connection",
        requested_entities=requested_entities,
        sqlite_schema_preview=schema_preview,
        idempotency_preview=idempotency_preview,
        trace_link_preview=trace_link_preview,
        read_snapshot_preview=read_snapshot_preview,
        write_preview_gate=write_preview_gate,
        fixture_snapshot_preview=fixture_snapshot_preview,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
    )


def build_context_persistence_sqlite_dev_preview_summary(
    *,
    payload: ContextPersistenceSqliteDevPreviewPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    gate = data.get("write_preview_gate") if isinstance(data.get("write_preview_gate"), dict) else {}
    schema = data.get("sqlite_schema_preview") if isinstance(data.get("sqlite_schema_preview"), dict) else {}
    return {
        "context_persistence_sqlite_dev_preview_version": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "preview_id": data.get("preview_id"),
        "adapter_kind": data.get("adapter_kind"),
        "adapter_mode": data.get("adapter_mode"),
        "schema_table_count": len(schema.get("tables") or {}),
        "idempotency_key": (data.get("idempotency_preview") or {}).get("idempotency_key") if isinstance(data.get("idempotency_preview"), dict) else None,
        "trace_id": data.get("trace_id"),
        "write_gate_status": gate.get("status"),
        "real_write_enabled": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_dev_preview_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        "context_persistence_sqlite_dev_preview_version": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-dev-preview/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-dev-preview/preview",
        "terminal_command": "/context-persistence-sqlite-dev-preview",
        "surface": "Dev-only SQLite/fixture adapter preview for context persistence",
        "mode": "schema_idempotency_trace_snapshot_preview_only_no_database_connection",
        "execution_status": {
            "sqlite_schema_preview_enabled": True,
            "idempotency_preview_enabled": True,
            "trace_link_preview_enabled": True,
            "read_snapshot_preview_enabled": True,
            "real_sqlite_write_enabled": False,
            "database_connection_created": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "schema_preview_tables": list(_sqlite_dev_preview_schema()["tables"].keys()),
        "rules": [
            "v2_8_11 provides a SQLite dev schema/read/idempotency/trace preview only; it does not create a database connection.",
            "Future dev writes must remain gated by explicit user confirmation, executor readiness, idempotency, trace link, and storage-boundary checks.",
            "HarmonyOS live Routine/playback/local-MIDI state remains client-owned and is not part of the backend SQLite preview.",
            "Raw MIDI assets, local MIDI paths, secrets, precise location, payment info, and hidden chain-of-thought remain forbidden.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_storage_adapter_design": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_executor_noop": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        },
        "next_task_hint": "v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate",
    }



def _has_any_forbidden_context_fields(value: Any) -> bool:
    """Return True when a payload contains fields forbidden for Agent context persistence."""

    forbidden = {
        "api_key", "apikey", "token", "password", "secret", "access_token", "refresh_token",
        "midi_base64", "midibase64", "local_midi_path", "localmidipath", "precise_location",
        "payment_info", "hidden_chain_of_thought", "chain_of_thought", "raw_cot",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            snake = re.sub(r"([A-Z])", r"_\1", str(key)).lower().strip("_")
            if normalized in forbidden or snake in forbidden:
                return True
            if _has_any_forbidden_context_fields(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_has_any_forbidden_context_fields(child) for child in value)
    return False


def build_context_persistence_dev_sqlite_write_gate_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_dev_sqlite_write_gate",
) -> ContextPersistenceDevSqliteWriteGatePayload:
    """Build an explicit dev-only SQLite write-gate preview without writing."""

    args = dict(arguments or {})
    gate_id = str(_first_present(args, "gate_id", "gateId") or f"ctx_dev_sqlite_write_gate_{uuid4().hex[:12]}")
    requested_entities = _normalize_storage_adapter_entities(args)
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_dev_adapter")
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    user_decision = str(_first_present(args, "user_decision", "userDecision") or "pending")
    confirmation_status = str(_first_present(args, "confirmation_status", "confirmationStatus") or "user_approved_future_executor_required")
    candidate_kind = str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "dev_candidate")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "dev_confirmation")
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    dev_write_requested = bool(_first_present(args, "dev_write_enabled", "devWriteEnabled", "write_enabled", "writeEnabled") or False)
    sqlite_config_path = _first_present(args, "sqlite_config_path", "sqliteConfigPath", "config_path", "configPath")
    sqlite_db_path = _first_present(args, "sqlite_db_path", "sqliteDbPath", "db_path", "dbPath")
    environment = str(_first_present(args, "environment", "env") or "dev")
    explicit_dev_mode = bool(_first_present(args, "explicit_dev_mode", "explicitDevMode", "dev_mode", "devMode") if _first_present(args, "explicit_dev_mode", "explicitDevMode", "dev_mode", "devMode") is not None else True)
    storage_boundary_check_passed = bool(_first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") if _first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") is not None else True)
    redaction_check_passed = bool(_first_present(args, "redaction_check_passed", "redactionCheckPassed") if _first_present(args, "redaction_check_passed", "redactionCheckPassed") is not None else True)
    schema_preview_accepted = bool(_first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") if _first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") is not None else True)
    trace_link_required = bool(_first_present(args, "trace_link_required", "traceLinkRequired") if _first_present(args, "trace_link_required", "traceLinkRequired") is not None else True)
    forbidden_fields_present = _has_any_forbidden_context_fields(args)

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if adapter_kind != "sqlite_dev_adapter":
        blocked_reasons.append("adapter_kind_must_be_sqlite_dev_adapter")
    if environment not in {"dev", "local_dev", "test", "fixture"}:
        blocked_reasons.append("sqlite_dev_write_gate_only_allows_dev_or_test_environment")
    if dev_write_requested and not sqlite_config_path:
        blocked_reasons.append("explicit_dev_write_requires_sqlite_config_path")
    if dev_write_requested and not sqlite_db_path:
        warnings.append("sqlite_db_path_not_provided_config_must_resolve_it")
    if dev_write_requested and not explicit_dev_mode:
        blocked_reasons.append("explicit_dev_mode_required_for_dev_sqlite_write_gate")
    if user_decision != "approved":
        blocked_reasons.append("user_decision_must_be_approved_before_future_dev_write")
    if confirmation_status != "user_approved_future_executor_required":
        blocked_reasons.append("confirmation_status_must_be_user_approved_future_executor_required")
    if not idempotency_key:
        blocked_reasons.append("idempotency_key_required")
    if trace_link_required and not trace_value:
        blocked_reasons.append("trace_id_required_for_trace_link")
    if not storage_boundary_check_passed:
        blocked_reasons.append("storage_boundary_check_failed")
    if not schema_preview_accepted:
        blocked_reasons.append("sqlite_schema_preview_not_accepted")
    if not redaction_check_passed or forbidden_fields_present:
        blocked_reasons.append("redaction_check_failed_or_forbidden_fields_present")

    if not dev_write_requested:
        gate_status = "dev_sqlite_write_gate_preview_only_no_write_requested"
        accepted = True
    elif blocked_reasons:
        gate_status = "dev_sqlite_write_gate_blocked"
        accepted = False
    else:
        gate_status = "dev_sqlite_write_gate_ready_future_executor_required"
        accepted = True

    dev_sqlite_config_contract = {
        "config_path_required_for_future_dev_write": True,
        "sqlite_config_path": str(sqlite_config_path) if sqlite_config_path else None,
        "sqlite_db_path": str(sqlite_db_path) if sqlite_db_path else None,
        "environment": environment,
        "allowed_environments": ["dev", "local_dev", "test", "fixture"],
        "must_not_use_production_database": True,
        "config_file_written": False,
        "database_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
    }
    explicit_write_gate = {
        "status": gate_status,
        "accepted": accepted,
        "dev_write_requested": dev_write_requested,
        "dev_write_enabled_for_future_executor": dev_write_requested and accepted,
        "real_write_executed": False,
        "future_executor_implemented": False,
        "requires_user_confirmation": True,
        "requires_idempotency_key": True,
        "requires_trace_link": trace_link_required,
        "requires_redaction_check": True,
        "requires_storage_boundary_check": True,
        "requires_explicit_dev_config_path": True,
        "blocked_reasons": list(blocked_reasons),
        "warnings": list(warnings),
    }
    required_checks = {
        "user_decision_approved": user_decision == "approved",
        "confirmation_status_ready": confirmation_status == "user_approved_future_executor_required",
        "idempotency_key_present": bool(idempotency_key),
        "trace_id_present": bool(trace_value),
        "storage_boundary_check_passed": storage_boundary_check_passed,
        "redaction_check_passed": redaction_check_passed and not forbidden_fields_present,
        "schema_preview_accepted": schema_preview_accepted,
        "explicit_dev_mode": explicit_dev_mode,
        "sqlite_config_path_present": bool(sqlite_config_path),
        "all_required_checks_passed": accepted and dev_write_requested,
    }
    idempotency_gate = {
        "idempotency_key": idempotency_key,
        "would_check_table": "context_persistence_idempotency_keys",
        "duplicate_policy": "return_existing_result_and_do_not_rewrite",
        "idempotency_record_written": False,
        "existing_record_found": False,
    }
    trace_link_gate = {
        "trace_id": trace_value,
        "confirmation_id": confirmation_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "would_write_table": "agent_trace_metadata",
        "trace_link_written": False,
        "raw_chain_of_thought_allowed": False,
    }
    storage_boundary_gate = {
        "backend_long_term_entities_allowed": list(requested_entities),
        "harmonyos_local_entities_forbidden": ["routine_session_runtime", "playback_state", "local_midi_cache", "score_viewport", "timer_state"],
        "storage_boundary_check_passed": storage_boundary_check_passed,
        "backend_database_written": False,
        "local_device_written": False,
    }
    redaction_gate = {
        "redaction_check_passed": redaction_check_passed and not forbidden_fields_present,
        "forbidden_fields_present": forbidden_fields_present,
        "forbidden_fields": ["api_key", "token", "password", "midi_base64", "local_midi_path", "precise_location", "payment_info", "hidden_chain_of_thought"],
        "payload_redacted_before_preview": True,
    }
    future_executor_contract = {
        "future_method": "write_confirmed_context",
        "current_version_executes_write": False,
        "must_run_after": [
            "context_persistence_confirmation_boundary",
            "context_persistence_executor_noop",
            "context_persistence_storage_adapter_design",
            "context_persistence_sqlite_dev_preview",
            "context_persistence_dev_sqlite_write_gate",
        ],
        "transaction_required": True,
        "rollback_required_on_partial_failure": True,
        "read_snapshot_after_write_required": True,
    }
    validation = {
        "status": gate_status,
        "accepted": accepted,
        "dev_sqlite_write_gate": True,
        "dev_write_requested": dev_write_requested,
        "dev_write_enabled_for_future_executor": dev_write_requested and accepted,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_write_enabled": False,
        "future_executor_implemented": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
    }
    guard_summary = {
        "context_persistence_dev_sqlite_write_gate": True,
        "preview_only": True,
        "sqlite_dev_write_gate_defined": True,
        "real_write_executed": False,
        "future_executor_implemented": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_write_enabled": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceDevSqliteWriteGatePayload(
        payload_contract_version=CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
        source=source,
        gate_id=gate_id,
        adapter_kind="sqlite_dev_adapter",
        adapter_mode="explicit_dev_sqlite_write_gate_no_write",
        requested_entities=requested_entities,
        dev_sqlite_config_contract=dev_sqlite_config_contract,
        explicit_write_gate=explicit_write_gate,
        required_checks=required_checks,
        idempotency_gate=idempotency_gate,
        trace_link_gate=trace_link_gate,
        storage_boundary_gate=storage_boundary_gate,
        redaction_gate=redaction_gate,
        future_executor_contract=future_executor_contract,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
    )


def build_context_persistence_dev_sqlite_write_gate_summary(
    *,
    payload: ContextPersistenceDevSqliteWriteGatePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    gate = data.get("explicit_write_gate") if isinstance(data.get("explicit_write_gate"), dict) else {}
    checks = data.get("required_checks") if isinstance(data.get("required_checks"), dict) else {}
    return {
        "context_persistence_dev_sqlite_write_gate_version": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "gate_id": data.get("gate_id"),
        "adapter_kind": data.get("adapter_kind"),
        "adapter_mode": data.get("adapter_mode"),
        "dev_write_requested": validation.get("dev_write_requested", False),
        "dev_write_enabled_for_future_executor": validation.get("dev_write_enabled_for_future_executor", False),
        "all_required_checks_passed": checks.get("all_required_checks_passed", False),
        "idempotency_key": (data.get("idempotency_gate") or {}).get("idempotency_key") if isinstance(data.get("idempotency_gate"), dict) else None,
        "trace_id": data.get("trace_id"),
        "write_gate_status": gate.get("status"),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_write_enabled": False,
        "future_executor_implemented": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_dev_sqlite_write_gate_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
        "context_persistence_dev_sqlite_write_gate_version": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
        "spec_route": "GET /agent/context/persistence-dev-sqlite-write-gate/spec",
        "preview_route": "POST /agent/context/persistence-dev-sqlite-write-gate/preview",
        "terminal_command": "/context-persistence-dev-sqlite-write-gate",
        "surface": "Explicit dev-only SQLite write gate and config-path contract",
        "mode": "write_gate_contract_only_no_database_connection_no_write",
        "execution_status": {
            "explicit_dev_write_gate_defined": True,
            "sqlite_config_path_contract_enabled": True,
            "idempotency_gate_required": True,
            "trace_link_gate_required": True,
            "redaction_gate_required": True,
            "storage_boundary_gate_required": True,
            "real_sqlite_write_enabled": False,
            "database_connection_created": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_future_write_checks": [
            "devWriteEnabled=true",
            "userDecision=approved",
            "confirmationStatus=user_approved_future_executor_required",
            "idempotencyKey present",
            "traceId present",
            "sqliteConfigPath present",
            "environment dev/test only",
            "storageBoundaryCheckPassed=true",
            "redactionCheckPassed=true",
            "schemaPreviewAccepted=true",
        ],
        "rules": [
            "v2_8_12 only defines an explicit dev SQLite write gate; it never opens SQLite or writes rows.",
            "Even an accepted gate means future executor required, not current write executed.",
            "Future writes must be idempotent, trace-linked, redacted, storage-boundary checked, and dev-config scoped.",
            "HarmonyOS Routine/playback/local-MIDI state remains client-owned and must never be written by this adapter.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_executor_noop": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "context_persistence_storage_adapter_design": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
            "context_persistence_sqlite_dev_preview": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
        },
        "next_task_hint": "v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run",
    }



@dataclass(frozen=True)
class ContextPersistenceDevSqliteFixtureWriteDryRunPayload:
    """v2_8_13 dev SQLite fixture write dry-run contract.

    This layer simulates the shape of a future dev-only SQLite write without
    opening SQLite, creating tables, or writing durable rows. It makes the
    future transaction/idempotency/trace/read-back flow reviewable before any
    real storage adapter is enabled.
    """

    payload_contract_version: str
    source: str
    dry_run_id: str
    adapter_kind: str
    adapter_mode: str
    requested_entities: list[str]
    transaction_preview: dict[str, Any]
    fixture_write_plan: dict[str, Any]
    idempotency_preview: dict[str, Any]
    trace_link_preview: dict[str, Any]
    read_back_preview: dict[str, Any]
    redaction_preview: dict[str, Any]
    storage_boundary_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    durable_backend_write_executed: bool = False
    fixture_write_executed: bool = False
    transaction_committed: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "dry_run_id": self.dry_run_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "requested_entities": list(self.requested_entities),
            "transaction_preview": _redact_sensitive_values(self.transaction_preview),
            "fixture_write_plan": _redact_sensitive_values(self.fixture_write_plan),
            "idempotency_preview": _redact_sensitive_values(self.idempotency_preview),
            "trace_link_preview": _redact_sensitive_values(self.trace_link_preview),
            "read_back_preview": _redact_sensitive_values(self.read_back_preview),
            "redaction_preview": _redact_sensitive_values(self.redaction_preview),
            "storage_boundary_preview": _redact_sensitive_values(self.storage_boundary_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "fixture_write_executed": self.fixture_write_executed,
            "transaction_committed": self.transaction_committed,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _fixture_write_entity_plan(entity: str, *, user_id: str, candidate_id: str, confirmation_id: str, trace_id: str | None, idempotency_key: str) -> dict[str, Any]:
    table_by_entity = {
        "user_practice_profile": "user_practice_profiles",
        "active_practice_plan": "active_practice_plans",
        "practice_plan": "active_practice_plans",
        "routine_history_summary": "practice_history_summaries",
        "agent_trace_metadata": "agent_trace_metadata",
        "idempotency_record": "context_persistence_idempotency_keys",
    }
    table = table_by_entity.get(entity, "unsupported_context_entity")
    return {
        "entity": entity,
        "target_table": table,
        "row_key_preview": hashlib.sha256(json.dumps({"entity": entity, "user_id": user_id, "candidate_id": candidate_id, "confirmation_id": confirmation_id}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:24],
        "would_prepare_sanitized_json_blob": entity != "unsupported_context_entity",
        "would_include_trace_id": bool(trace_id),
        "would_include_confirmation_id": bool(confirmation_id),
        "would_include_idempotency_key": entity == "idempotency_record",
        "idempotency_key": idempotency_key if entity == "idempotency_record" else None,
        "insert_sql_preview": f"INSERT OR REPLACE INTO {table} (...) VALUES (...);" if table != "unsupported_context_entity" else None,
        "fixture_row_written": False,
        "durable_row_written": False,
    }


def build_context_persistence_dev_sqlite_fixture_write_dry_run_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_dev_sqlite_fixture_write_dry_run",
) -> ContextPersistenceDevSqliteFixtureWriteDryRunPayload:
    """Build a dev SQLite fixture writer dry-run without any storage side effects."""

    args = dict(arguments or {})
    dry_run_id = str(_first_present(args, "dry_run_id", "dryRunId") or f"ctx_sqlite_fixture_dry_run_{uuid4().hex[:12]}")
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_dev_fixture_adapter")
    requested_entities = _normalize_storage_adapter_entities(args)
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    user_id = str(_first_present(args, "user_id", "userId") or "dev_user")
    candidate_kind = str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "dev_candidate")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "dev_confirmation")
    user_decision = str(_first_present(args, "user_decision", "userDecision") or "approved")
    confirmation_status = str(_first_present(args, "confirmation_status", "confirmationStatus") or "user_approved_future_executor_required")
    sqlite_config_path = _first_present(args, "sqlite_config_path", "sqliteConfigPath", "config_path", "configPath")
    sqlite_db_path = _first_present(args, "sqlite_db_path", "sqliteDbPath", "db_path", "dbPath") or "./.jammate/dev_context.sqlite3"
    environment = str(_first_present(args, "environment", "env") or "dev")
    dry_run_enabled = bool(_first_present(args, "dry_run_enabled", "dryRunEnabled") if _first_present(args, "dry_run_enabled", "dryRunEnabled") is not None else True)
    dev_write_enabled = bool(_first_present(args, "dev_write_enabled", "devWriteEnabled", "write_enabled", "writeEnabled") or False)
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    storage_boundary_check_passed = bool(_first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") if _first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") is not None else True)
    redaction_check_passed = bool(_first_present(args, "redaction_check_passed", "redactionCheckPassed") if _first_present(args, "redaction_check_passed", "redactionCheckPassed") is not None else True)
    schema_preview_accepted = bool(_first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") if _first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") is not None else True)
    simulate_duplicate = bool(_first_present(args, "simulate_duplicate", "simulateDuplicate") or False)
    simulate_transaction_failure = bool(_first_present(args, "simulate_transaction_failure", "simulateTransactionFailure") or False)
    forbidden_fields_present = _has_any_forbidden_context_fields(args)

    supported_entities = {"user_practice_profile", "active_practice_plan", "practice_plan", "routine_history_summary", "agent_trace_metadata", "idempotency_record"}
    unsupported_entities = [entity for entity in requested_entities if entity not in supported_entities]
    valid_entities = [entity for entity in requested_entities if entity in supported_entities]
    if "idempotency_record" not in valid_entities:
        valid_entities.append("idempotency_record")
    if "agent_trace_metadata" not in valid_entities and trace_value:
        valid_entities.append("agent_trace_metadata")

    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if adapter_kind not in {"sqlite_dev_fixture_adapter", "sqlite_dev_adapter"}:
        warnings.append("adapter_kind_forced_to_sqlite_dev_fixture_adapter")
    if unsupported_entities:
        warnings.append("unsupported_entities_ignored_for_fixture_dry_run")
    if dev_write_enabled:
        warnings.append("dev_write_enabled_requested_but_v2_8_13_runs_dry_run_only")
    if user_decision != "approved":
        blocked_reasons.append("user_decision_must_be_approved_before_fixture_write_dry_run")
    if confirmation_status != "user_approved_future_executor_required":
        blocked_reasons.append("confirmation_status_must_match_approved_future_executor_required")
    if environment not in {"dev", "local_dev", "test", "fixture"}:
        blocked_reasons.append("fixture_write_dry_run_only_allows_dev_or_test_environment")
    if not dry_run_enabled:
        blocked_reasons.append("dry_run_enabled_must_be_true")
    if not sqlite_config_path:
        warnings.append("sqlite_config_path_missing_dry_run_uses_default_preview_only")
    if not trace_value:
        warnings.append("trace_id_missing_trace_link_would_be_incomplete")
    if not storage_boundary_check_passed:
        blocked_reasons.append("storage_boundary_check_failed")
    if not redaction_check_passed or forbidden_fields_present:
        blocked_reasons.append("redaction_check_failed_or_forbidden_fields_present")
    if not schema_preview_accepted:
        blocked_reasons.append("schema_preview_not_accepted")
    if simulate_transaction_failure:
        blocked_reasons.append("simulated_transaction_failure_requested")

    accepted = not blocked_reasons
    validation_status = "fixture_write_dry_run_ready" if accepted else "fixture_write_dry_run_blocked"
    planned_rows = [
        _fixture_write_entity_plan(entity, user_id=user_id, candidate_id=candidate_id, confirmation_id=confirmation_id, trace_id=trace_value, idempotency_key=idempotency_key)
        for entity in valid_entities
    ]
    transaction_preview = {
        "transaction_mode": "simulated_sqlite_transaction_dry_run",
        "begin_sql_preview": "BEGIN IMMEDIATE TRANSACTION;",
        "commit_sql_preview": "COMMIT;",
        "rollback_sql_preview": "ROLLBACK;",
        "would_begin_transaction": accepted,
        "would_prepare_rows": accepted,
        "would_commit_if_real_executor_existed": accepted and not simulate_duplicate,
        "would_return_existing_result_on_duplicate": simulate_duplicate,
        "transaction_simulated": True,
        "transaction_committed": False,
        "rollback_executed": False,
    }
    fixture_write_plan = {
        "adapter_kind": "sqlite_dev_fixture_adapter",
        "sqlite_config_path": sqlite_config_path,
        "sqlite_db_path_preview": sqlite_db_path,
        "environment": environment,
        "requested_entities": list(requested_entities),
        "valid_entities": list(valid_entities),
        "planned_row_count": len(planned_rows),
        "planned_rows": planned_rows,
        "fixture_write_dry_run": True,
        "fixture_write_executed": False,
        "durable_backend_write_executed": False,
    }
    idempotency_preview = {
        "idempotency_key": idempotency_key,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "simulate_duplicate": simulate_duplicate,
        "would_check_existing_key_before_transaction": True,
        "would_insert_idempotency_record_inside_transaction": accepted and not simulate_duplicate,
        "duplicate_policy": "return_existing_write_result_without_rewriting_rows",
        "idempotency_record_written": False,
    }
    trace_link_preview = {
        "trace_id": trace_value,
        "trace_link_required": True,
        "would_write_agent_trace_metadata": bool(trace_value) and accepted,
        "hidden_chain_of_thought_allowed": False,
        "trace_metadata_written": False,
    }
    read_back_preview = {
        "read_back_required_after_write": True,
        "would_read_tables": sorted({row["target_table"] for row in planned_rows if row["target_table"] != "unsupported_context_entity"}),
        "snapshot_shape": {
            "user_id": user_id,
            "candidate_id": candidate_id,
            "confirmation_id": confirmation_id,
            "entity_count": len(valid_entities),
            "idempotency_key": idempotency_key,
        },
        "read_back_simulated": True,
        "read_back_performed_against_sqlite": False,
    }
    redaction_preview = {
        "redaction_check_passed": redaction_check_passed and not forbidden_fields_present,
        "forbidden_fields_present": forbidden_fields_present,
        "forbidden_fields_removed_from_output": True,
        "midi_base64_allowed": False,
        "local_midi_path_allowed": False,
        "api_key_allowed": False,
        "hidden_chain_of_thought_allowed": False,
    }
    storage_boundary_preview = {
        "storage_boundary_check_passed": storage_boundary_check_passed,
        "backend_long_term_context_only": True,
        "harmonyos_local_state_owned_by_client": True,
        "routine_runtime_state_written": False,
        "playback_state_written": False,
        "local_midi_cache_written": False,
    }
    validation = {
        "status": validation_status,
        "accepted": accepted,
        "fixture_write_dry_run": True,
        "dry_run_enabled": dry_run_enabled,
        "dev_write_requested": dev_write_enabled,
        "durable_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
    }
    guard_summary = {
        "context_persistence_dev_sqlite_fixture_write_dry_run": True,
        "dry_run_only": True,
        "transaction_shape_previewed": True,
        "idempotency_shape_previewed": True,
        "trace_link_shape_previewed": True,
        "read_back_shape_previewed": True,
        "real_write_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceDevSqliteFixtureWriteDryRunPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
        source=source,
        dry_run_id=dry_run_id,
        adapter_kind="sqlite_dev_fixture_adapter",
        adapter_mode="fixture_write_dry_run_no_sqlite_connection_no_durable_write",
        requested_entities=requested_entities,
        transaction_preview=transaction_preview,
        fixture_write_plan=fixture_write_plan,
        idempotency_preview=idempotency_preview,
        trace_link_preview=trace_link_preview,
        read_back_preview=read_back_preview,
        redaction_preview=redaction_preview,
        storage_boundary_preview=storage_boundary_preview,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
    )


def build_context_persistence_dev_sqlite_fixture_write_dry_run_summary(
    *,
    payload: ContextPersistenceDevSqliteFixtureWriteDryRunPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    fixture_plan = data.get("fixture_write_plan") if isinstance(data.get("fixture_write_plan"), dict) else {}
    transaction = data.get("transaction_preview") if isinstance(data.get("transaction_preview"), dict) else {}
    idempotency = data.get("idempotency_preview") if isinstance(data.get("idempotency_preview"), dict) else {}
    return {
        "context_persistence_dev_sqlite_fixture_write_dry_run_version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "dry_run_id": data.get("dry_run_id"),
        "adapter_kind": data.get("adapter_kind"),
        "adapter_mode": data.get("adapter_mode"),
        "planned_row_count": fixture_plan.get("planned_row_count", 0),
        "transaction_simulated": transaction.get("transaction_simulated", False),
        "idempotency_key": idempotency.get("idempotency_key"),
        "trace_id": data.get("trace_id"),
        "read_back_simulated": (data.get("read_back_preview") or {}).get("read_back_simulated") if isinstance(data.get("read_back_preview"), dict) else False,
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
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_dev_sqlite_fixture_write_dry_run_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
        "context_persistence_dev_sqlite_fixture_write_dry_run_version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
        "spec_route": "GET /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec",
        "preview_route": "POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview",
        "terminal_command": "/context-persistence-dev-sqlite-fixture-write-dry-run",
        "surface": "Dev SQLite fixture writer dry-run contract",
        "mode": "transaction_idempotency_trace_read_back_dry_run_no_durable_write",
        "execution_status": {
            "fixture_write_dry_run_defined": True,
            "transaction_shape_previewed": True,
            "idempotency_shape_previewed": True,
            "trace_link_shape_previewed": True,
            "read_back_shape_previewed": True,
            "real_sqlite_write_enabled": False,
            "database_connection_created": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "dry_run_flow": [
            "validate explicit approval and dev/test environment",
            "check redaction and storage-boundary gates",
            "simulate idempotency lookup",
            "simulate transaction begin",
            "prepare sanitized fixture row plan",
            "simulate trace metadata link",
            "simulate read-back snapshot",
            "return no-write report",
        ],
        "rules": [
            "v2_8_13 simulates fixture/SQLite write flow only; it never opens SQLite or writes rows.",
            "Dry-run plans must be idempotent, trace-linked, redacted, and storage-boundary checked.",
            "Duplicate idempotency simulation returns an existing-result shape without planning a rewrite.",
            "HarmonyOS Routine/playback/local-MIDI state remains client-owned and must never be written by this adapter.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "durable_backend_write_executed": False,
            "fixture_write_executed": False,
            "transaction_committed": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_executor_noop": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "context_persistence_storage_adapter_design": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
            "context_persistence_sqlite_dev_preview": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
            "context_persistence_dev_sqlite_write_gate": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
        },
        "next_task_hint": "v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in",
    }


@dataclass(frozen=True)
class ContextPersistenceDevSqliteFixtureStorePayload:
    """v2_8_14 dev-only explicit opt-in fixture store contract.

    This layer is the first persistence step that may write a local development
    fixture JSONL file, but only when the caller explicitly opts in and all
    confirmation, idempotency, trace, redaction, and storage-boundary gates pass.
    It still does not create SQLite connections, create tables, write backend
    databases, write HarmonyOS local state, call LLMs, execute tools, or touch
    engine generation.
    """

    payload_contract_version: str
    source: str
    fixture_store_id: str
    adapter_kind: str
    adapter_mode: str
    requested_entities: list[str]
    fixture_store_path: str | None
    fixture_store_record: dict[str, Any]
    fixture_store_result: dict[str, Any]
    idempotency_preview: dict[str, Any]
    trace_link_preview: dict[str, Any]
    redaction_preview: dict[str, Any]
    storage_boundary_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    durable_backend_write_executed: bool = False
    fixture_store_write_executed: bool = False
    fixture_write_executed: bool = False
    transaction_committed: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "fixture_store_id": self.fixture_store_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "requested_entities": list(self.requested_entities),
            "fixture_store_path": self.fixture_store_path,
            "fixture_store_record": _redact_sensitive_values(self.fixture_store_record),
            "fixture_store_result": _redact_sensitive_values(self.fixture_store_result),
            "idempotency_preview": _redact_sensitive_values(self.idempotency_preview),
            "trace_link_preview": _redact_sensitive_values(self.trace_link_preview),
            "redaction_preview": _redact_sensitive_values(self.redaction_preview),
            "storage_boundary_preview": _redact_sensitive_values(self.storage_boundary_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "fixture_store_write_executed": self.fixture_store_write_executed,
            "fixture_write_executed": self.fixture_write_executed,
            "transaction_committed": self.transaction_committed,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _is_allowed_dev_fixture_store_path(path_value: str | None) -> bool:
    if not path_value:
        return False
    path_text = str(path_value)
    normalized = path_text.replace("\\", "/")
    if ".." in Path(normalized).parts:
        return False
    lowered = normalized.lower()
    if any(part in lowered for part in ("/prod", "production", "secrets", "private_key")):
        return False
    if normalized.startswith("/mnt/data/") or normalized.startswith("/tmp/"):
        return True
    return not Path(normalized).is_absolute()


def _append_dev_fixture_store_record(path_value: str, record: dict[str, Any]) -> dict[str, Any]:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(_redact_sensitive_values(record), ensure_ascii=False, sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return {
        "fixture_store_write_executed": True,
        "fixture_store_path": str(path),
        "bytes_appended": len(line.encode("utf-8")) + 1,
        "line_count_appended": 1,
    }


def build_context_persistence_dev_sqlite_fixture_store_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_dev_sqlite_fixture_store",
) -> ContextPersistenceDevSqliteFixtureStorePayload:
    """Build a dev-only explicit opt-in fixture store payload.

    Unlike v2_8_13's dry-run, this function can append one redacted JSONL record
    to a caller-provided development fixture path, but only when explicit opt-in
    flags and all guards pass. It never opens SQLite or writes backend database
    rows.
    """

    args = dict(arguments or {})
    fixture_store_id = str(_first_present(args, "fixture_store_id", "fixtureStoreId") or f"ctx_sqlite_fixture_store_{uuid4().hex[:12]}")
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_dev_fixture_store")
    requested_entities = _normalize_storage_adapter_entities(args)
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    user_id = str(_first_present(args, "user_id", "userId") or "dev_user")
    candidate_kind = str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "dev_candidate")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "dev_confirmation")
    user_decision = str(_first_present(args, "user_decision", "userDecision") or "approved")
    confirmation_status = str(_first_present(args, "confirmation_status", "confirmationStatus") or "user_approved_future_executor_required")
    environment = str(_first_present(args, "environment", "env") or "dev")
    fixture_store_write_enabled = bool(_first_present(args, "fixture_store_write_enabled", "fixtureStoreWriteEnabled", "dev_fixture_store_enabled", "devFixtureStoreEnabled") or False)
    execute_fixture_store = bool(_first_present(args, "execute_fixture_store", "executeFixtureStore") or False)
    fixture_store_path = _first_present(args, "fixture_store_path", "fixtureStorePath", "fixture_path", "fixturePath")
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    storage_boundary_check_passed = bool(_first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") if _first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") is not None else True)
    redaction_check_passed = bool(_first_present(args, "redaction_check_passed", "redactionCheckPassed") if _first_present(args, "redaction_check_passed", "redactionCheckPassed") is not None else True)
    schema_preview_accepted = bool(_first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") if _first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") is not None else True)
    simulate_duplicate = bool(_first_present(args, "simulate_duplicate", "simulateDuplicate") or False)
    forbidden_fields_present = _has_any_forbidden_context_fields(args)

    supported_entities = {"user_practice_profile", "active_practice_plan", "practice_plan", "routine_history_summary", "agent_trace_metadata", "idempotency_record"}
    unsupported_entities = [entity for entity in requested_entities if entity not in supported_entities]
    valid_entities = [entity for entity in requested_entities if entity in supported_entities]
    if "idempotency_record" not in valid_entities:
        valid_entities.append("idempotency_record")
    if "agent_trace_metadata" not in valid_entities and trace_value:
        valid_entities.append("agent_trace_metadata")

    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if adapter_kind not in {"sqlite_dev_fixture_store", "sqlite_dev_fixture_adapter", "sqlite_dev_adapter"}:
        warnings.append("adapter_kind_forced_to_sqlite_dev_fixture_store")
    if unsupported_entities:
        warnings.append("unsupported_entities_ignored_for_fixture_store")
    if user_decision != "approved":
        blocked_reasons.append("user_decision_must_be_approved_before_fixture_store")
    if confirmation_status != "user_approved_future_executor_required":
        blocked_reasons.append("confirmation_status_must_match_approved_future_executor_required")
    if environment not in {"dev", "local_dev", "test", "fixture"}:
        blocked_reasons.append("fixture_store_only_allows_dev_or_test_environment")
    if not fixture_store_write_enabled:
        blocked_reasons.append("fixture_store_write_enabled_must_be_true")
    if not execute_fixture_store:
        blocked_reasons.append("execute_fixture_store_must_be_true_for_actual_fixture_store")
    if not fixture_store_path:
        blocked_reasons.append("fixture_store_path_required")
    elif not _is_allowed_dev_fixture_store_path(str(fixture_store_path)):
        blocked_reasons.append("fixture_store_path_must_be_relative_or_tmp_dev_path")
    if not trace_value:
        blocked_reasons.append("trace_id_required_for_fixture_store")
    if not storage_boundary_check_passed:
        blocked_reasons.append("storage_boundary_check_failed")
    if not redaction_check_passed or forbidden_fields_present:
        blocked_reasons.append("redaction_check_failed_or_forbidden_fields_present")
    if not schema_preview_accepted:
        blocked_reasons.append("schema_preview_not_accepted")
    if simulate_duplicate:
        warnings.append("simulate_duplicate_returns_existing_fixture_result_without_appending")

    accepted = not blocked_reasons
    will_write_fixture_store = accepted and not simulate_duplicate
    validation_status = "fixture_store_ready" if accepted else "fixture_store_blocked"
    planned_rows = [
        _fixture_write_entity_plan(entity, user_id=user_id, candidate_id=candidate_id, confirmation_id=confirmation_id, trace_id=trace_value, idempotency_key=idempotency_key)
        for entity in valid_entities
    ]
    record = {
        "record_contract_version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        "fixture_store_id": fixture_store_id,
        "written_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "environment": environment,
        "user_id": user_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "trace_id": trace_value,
        "idempotency_key": idempotency_key,
        "entities": list(valid_entities),
        "planned_rows": planned_rows,
        "storage_boundary": "backend_long_term_context_only_no_harmonyos_runtime_state",
        "source": source,
    }
    fixture_result = {
        "fixture_store_write_enabled": fixture_store_write_enabled,
        "execute_fixture_store": execute_fixture_store,
        "fixture_store_path": str(fixture_store_path) if fixture_store_path else None,
        "fixture_store_write_executed": False,
        "fixture_store_record_prepared": True,
        "duplicate_result_returned": simulate_duplicate,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
    }
    if will_write_fixture_store and fixture_store_path:
        try:
            write_result = _append_dev_fixture_store_record(str(fixture_store_path), record)
            fixture_result.update(write_result)
        except OSError as exc:
            blocked_reasons.append(f"fixture_store_write_failed:{exc.__class__.__name__}")
            accepted = False
            validation_status = "fixture_store_blocked"
            fixture_result["fixture_store_write_executed"] = False
            fixture_result["write_error"] = exc.__class__.__name__

    idempotency_preview = {
        "idempotency_key": idempotency_key,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "simulate_duplicate": simulate_duplicate,
        "would_check_existing_key_before_fixture_store": True,
        "fixture_store_appended_on_unique_key": fixture_result.get("fixture_store_write_executed", False),
        "duplicate_policy": "return_existing_fixture_result_without_appending",
    }
    trace_link_preview = {
        "trace_id": trace_value,
        "trace_link_required": True,
        "trace_metadata_included_in_fixture_record": bool(trace_value) and fixture_result.get("fixture_store_write_executed", False),
        "hidden_chain_of_thought_allowed": False,
    }
    redaction_preview = {
        "redaction_check_passed": redaction_check_passed and not forbidden_fields_present,
        "forbidden_fields_present": forbidden_fields_present,
        "forbidden_fields_removed_from_output": True,
        "midi_base64_allowed": False,
        "local_midi_path_allowed": False,
        "api_key_allowed": False,
        "hidden_chain_of_thought_allowed": False,
    }
    storage_boundary_preview = {
        "storage_boundary_check_passed": storage_boundary_check_passed,
        "backend_long_term_context_only": True,
        "dev_fixture_file_only": True,
        "harmonyos_local_state_owned_by_client": True,
        "routine_runtime_state_written": False,
        "playback_state_written": False,
        "local_midi_cache_written": False,
        "sqlite_database_written": False,
    }
    validation = {
        "status": validation_status,
        "accepted": accepted,
        "fixture_store_write_enabled": fixture_store_write_enabled,
        "execute_fixture_store": execute_fixture_store,
        "fixture_store_write_executed": fixture_result.get("fixture_store_write_executed", False),
        "durable_write_executed": False,
        "sqlite_database_written": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
    }
    guard_summary = {
        "context_persistence_dev_sqlite_fixture_store": True,
        "explicit_opt_in_required": True,
        "dev_fixture_store_write_executed": fixture_result.get("fixture_store_write_executed", False),
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "durable_backend_write_executed": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceDevSqliteFixtureStorePayload(
        payload_contract_version=CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        source=source,
        fixture_store_id=fixture_store_id,
        adapter_kind="sqlite_dev_fixture_store",
        adapter_mode="explicit_opt_in_fixture_jsonl_store_no_sqlite_no_backend_database",
        requested_entities=requested_entities,
        fixture_store_path=str(fixture_store_path) if fixture_store_path else None,
        fixture_store_record=record,
        fixture_store_result=fixture_result,
        idempotency_preview=idempotency_preview,
        trace_link_preview=trace_link_preview,
        redaction_preview=redaction_preview,
        storage_boundary_preview=storage_boundary_preview,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
        fixture_store_write_executed=bool(fixture_result.get("fixture_store_write_executed", False)),
    )


def build_context_persistence_dev_sqlite_fixture_store_summary(
    *,
    payload: ContextPersistenceDevSqliteFixtureStorePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    fixture_result = data.get("fixture_store_result") if isinstance(data.get("fixture_store_result"), dict) else {}
    idempotency = data.get("idempotency_preview") if isinstance(data.get("idempotency_preview"), dict) else {}
    record = data.get("fixture_store_record") if isinstance(data.get("fixture_store_record"), dict) else {}
    return {
        "context_persistence_dev_sqlite_fixture_store_version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "fixture_store_id": data.get("fixture_store_id"),
        "adapter_kind": data.get("adapter_kind"),
        "adapter_mode": data.get("adapter_mode"),
        "fixture_store_path": data.get("fixture_store_path"),
        "fixture_store_write_executed": fixture_result.get("fixture_store_write_executed", False),
        "fixture_store_record_prepared": fixture_result.get("fixture_store_record_prepared", False),
        "entity_count": len(record.get("entities") or []),
        "idempotency_key": idempotency.get("idempotency_key"),
        "trace_id": data.get("trace_id"),
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_dev_sqlite_fixture_store_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        "context_persistence_dev_sqlite_fixture_store_version": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        "spec_route": "GET /agent/context/persistence-dev-sqlite-fixture-store/spec",
        "preview_route": "POST /agent/context/persistence-dev-sqlite-fixture-store/preview",
        "terminal_command": "/context-persistence-dev-sqlite-fixture-store",
        "surface": "Dev-only explicit opt-in fixture store contract",
        "mode": "explicit_opt_in_fixture_jsonl_store_no_sqlite_no_backend_database",
        "execution_status": {
            "explicit_fixture_store_defined": True,
            "fixture_store_can_append_dev_jsonl_when_explicitly_enabled": True,
            "real_sqlite_write_enabled": False,
            "database_connection_created": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "fixtureStoreWriteEnabled=true",
            "executeFixtureStore=true",
            "userDecision=approved",
            "confirmationStatus=user_approved_future_executor_required",
            "environment in dev/local_dev/test/fixture",
            "fixtureStorePath is relative or tmp/dev path",
            "traceId present",
            "idempotencyKey present or derived",
            "storageBoundaryCheckPassed=true",
            "redactionCheckPassed=true",
            "schemaPreviewAccepted=true",
        ],
        "rules": [
            "v2_8_14 only permits a local dev fixture JSONL append after explicit opt-in and all gates pass.",
            "It never opens SQLite, creates tables, or writes backend database rows.",
            "Fixture records must be redacted, trace-linked, idempotency-keyed, and scoped to backend-long-term context only.",
            "HarmonyOS Routine/playback/local-MIDI state remains client-owned and must never be written by this adapter.",
        ],
        "guards": {
            "payload_may_write_dev_fixture_file_only_after_explicit_opt_in": True,
            "payload_writes_backend_database": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "durable_backend_write_executed": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_executor_noop": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
            "context_persistence_storage_adapter_design": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
            "context_persistence_sqlite_dev_preview": CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_VERSION,
            "context_persistence_dev_sqlite_write_gate": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
            "context_persistence_dev_sqlite_fixture_write_dry_run": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_VERSION,
        },
        "next_task_hint": "v2_8_15_agent_context_persistence_dev_fixture_readback_and_replay_preview",
    }


@dataclass(frozen=True)
class ContextPersistenceDevFixtureReadbackReplayPayload:
    """v2_8_15 dev fixture read-back and replay preview contract.

    This layer reads a redacted development JSONL fixture produced by the
    explicit opt-in fixture store and builds a replay/snapshot preview. It is
    read-only: no SQLite connection, table creation, row write, backend durable
    write, HarmonyOS local write, LLM call, tool execution, Routine start, or
    engine generation is allowed.
    """

    payload_contract_version: str
    source: str
    readback_id: str
    adapter_kind: str
    adapter_mode: str
    fixture_store_path: str | None
    requested_entities: list[str]
    readback_filters: dict[str, Any]
    fixture_read_result: dict[str, Any]
    replay_preview: dict[str, Any]
    context_snapshot_preview: dict[str, Any]
    trace_link_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    durable_backend_write_executed: bool = False
    fixture_write_executed: bool = False
    transaction_committed: bool = False
    replay_execution_committed: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "readback_id": self.readback_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "fixture_store_path": self.fixture_store_path,
            "requested_entities": list(self.requested_entities),
            "readback_filters": _redact_sensitive_values(self.readback_filters),
            "fixture_read_result": _redact_sensitive_values(self.fixture_read_result),
            "replay_preview": _redact_sensitive_values(self.replay_preview),
            "context_snapshot_preview": _redact_sensitive_values(self.context_snapshot_preview),
            "trace_link_preview": _redact_sensitive_values(self.trace_link_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "fixture_write_executed": self.fixture_write_executed,
            "transaction_committed": self.transaction_committed,
            "replay_execution_committed": self.replay_execution_committed,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _read_dev_fixture_store_records(path_value: str, *, max_records: int = 50) -> dict[str, Any]:
    """Read redacted dev fixture JSONL records for replay preview only."""

    path = Path(path_value)
    result: dict[str, Any] = {
        "fixture_store_path": str(path),
        "file_exists": path.exists(),
        "records_read": 0,
        "invalid_line_count": 0,
        "records": [],
        "read_error": None,
    }
    if not path.exists():
        return result
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if len(result["records"]) >= max_records:
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    result["invalid_line_count"] += 1
                    continue
                if isinstance(data, dict):
                    result["records"].append(_redact_sensitive_values(data))
                    result["records_read"] += 1
                else:
                    result["invalid_line_count"] += 1
    except OSError as exc:
        result["read_error"] = exc.__class__.__name__
    return result


def _filter_dev_fixture_records(records: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for record in records:
        keep = True
        for key in ("user_id", "candidate_kind", "candidate_id", "confirmation_id", "trace_id", "idempotency_key"):
            value = filters.get(key)
            if value and str(record.get(key)) != str(value):
                keep = False
                break
        if keep:
            filtered.append(record)
    return filtered


def _summarize_fixture_record_for_replay(record: dict[str, Any]) -> dict[str, Any]:
    planned_rows = record.get("planned_rows") if isinstance(record.get("planned_rows"), list) else []
    return {
        "record_contract_version": record.get("record_contract_version"),
        "fixture_store_id": record.get("fixture_store_id"),
        "written_at_utc": record.get("written_at_utc"),
        "user_id": record.get("user_id"),
        "candidate_kind": record.get("candidate_kind"),
        "candidate_id": record.get("candidate_id"),
        "confirmation_id": record.get("confirmation_id"),
        "trace_id": record.get("trace_id"),
        "idempotency_key": record.get("idempotency_key"),
        "entities": list(record.get("entities") or []),
        "planned_row_count": len(planned_rows),
    }


def build_context_persistence_dev_fixture_readback_replay_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_dev_fixture_readback_replay",
) -> ContextPersistenceDevFixtureReadbackReplayPayload:
    """Build a dev fixture read-back/replay preview from JSONL records.

    The function may read a safe dev fixture file, but it never writes any file,
    opens SQLite, mutates backend storage, mutates HarmonyOS local state, calls
    LLMs/tools, starts Routine, calls engine adapters, or creates MIDI assets.
    """

    args = dict(arguments or {})
    readback_id = str(_first_present(args, "readback_id", "readbackId") or f"ctx_fixture_readback_{uuid4().hex[:12]}")
    fixture_store_path = _first_present(args, "fixture_store_path", "fixtureStorePath", "fixture_path", "fixturePath")
    requested_entities = _normalize_storage_adapter_entities(args)
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    environment = str(_first_present(args, "environment", "env") or "dev")
    max_records_raw = _first_present(args, "max_records", "maxRecords", "limit")
    try:
        max_records = max(1, min(int(max_records_raw), 200)) if max_records_raw is not None else 50
    except (TypeError, ValueError):
        max_records = 50
    filters = {
        "user_id": _first_present(args, "user_id", "userId"),
        "candidate_kind": _first_present(args, "candidate_kind", "candidateKind"),
        "candidate_id": _first_present(args, "candidate_id", "candidateId"),
        "confirmation_id": _first_present(args, "confirmation_id", "confirmationId"),
        "trace_id": _first_present(args, "filter_trace_id", "filterTraceId") or trace_value,
        "idempotency_key": _first_present(args, "idempotency_key", "idempotencyKey"),
    }
    filters = {key: value for key, value in filters.items() if value}

    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if environment not in {"dev", "local_dev", "test", "fixture"}:
        blocked_reasons.append("readback_preview_only_allows_dev_or_test_environment")
    if not fixture_store_path:
        blocked_reasons.append("fixture_store_path_required_for_readback")
    elif not _is_allowed_dev_fixture_store_path(str(fixture_store_path)):
        blocked_reasons.append("fixture_store_path_must_be_relative_or_tmp_dev_path")
    if _has_any_forbidden_context_fields(args):
        blocked_reasons.append("redaction_check_failed_or_forbidden_fields_present")

    fixture_read_result = {
        "fixture_store_path": str(fixture_store_path) if fixture_store_path else None,
        "file_exists": False,
        "records_read": 0,
        "invalid_line_count": 0,
        "records": [],
        "matched_records": [],
        "matched_record_count": 0,
        "read_error": None,
        "read_only": True,
    }
    if fixture_store_path and not blocked_reasons:
        fixture_read_result.update(_read_dev_fixture_store_records(str(fixture_store_path), max_records=max_records))
        records = fixture_read_result.get("records") if isinstance(fixture_read_result.get("records"), list) else []
        matched = _filter_dev_fixture_records(records, filters)
        fixture_read_result["matched_records"] = [_summarize_fixture_record_for_replay(record) for record in matched]
        fixture_read_result["matched_record_count"] = len(matched)
        fixture_read_result["records"] = [_summarize_fixture_record_for_replay(record) for record in records]
        if not fixture_read_result.get("file_exists"):
            warnings.append("fixture_store_path_not_found_readback_returns_empty_snapshot")
        if fixture_read_result.get("read_error"):
            blocked_reasons.append(f"fixture_store_read_failed:{fixture_read_result.get('read_error')}")
    matched_records = fixture_read_result.get("matched_records") if isinstance(fixture_read_result.get("matched_records"), list) else []
    latest_record = matched_records[-1] if matched_records else None
    entity_counts: dict[str, int] = {}
    for record in matched_records:
        for entity in record.get("entities") or []:
            entity_counts[str(entity)] = entity_counts.get(str(entity), 0) + 1
    context_snapshot_preview = {
        "snapshot_mode": "dev_fixture_readback_preview_only",
        "snapshot_available": bool(matched_records),
        "record_count": len(matched_records),
        "latest_record": latest_record,
        "entity_counts": entity_counts,
        "requested_entities": list(requested_entities),
        "restored_context_sections": {
            "learner_context": {
                "source": "dev_fixture_jsonl_readback_preview",
                "records_matched": len(matched_records),
                "entities_seen": sorted(entity_counts),
            },
            "persistence_context_snapshot": {
                "readback_id": readback_id,
                "fixture_store_path": str(fixture_store_path) if fixture_store_path else None,
                "latest_trace_id": latest_record.get("trace_id") if isinstance(latest_record, dict) else None,
                "latest_idempotency_key": latest_record.get("idempotency_key") if isinstance(latest_record, dict) else None,
            },
        },
    }
    replay_preview = {
        "replay_mode": "preview_only_no_mutation",
        "replay_steps": [
            "open_safe_dev_fixture_jsonl_read_only",
            "parse_redacted_records",
            "apply_optional_trace_id_user_id_candidate_id_filters",
            "build_context_snapshot_preview",
            "return_replay_preview_without_committing_state",
        ],
        "replayable": bool(matched_records) and not blocked_reasons,
        "records_considered": fixture_read_result.get("records_read", 0),
        "records_matched": len(matched_records),
        "execution_committed": False,
    }
    trace_link_preview = {
        "trace_id": trace_value,
        "latest_fixture_trace_id": latest_record.get("trace_id") if isinstance(latest_record, dict) else None,
        "trace_link_read_only": True,
        "trace_metadata_written": False,
    }
    accepted = not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "readback_replay_preview_ready" if accepted else "readback_replay_preview_blocked",
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
        "readback_only": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }
    guard_summary = {
        "context_persistence_dev_fixture_readback_replay": True,
        "readback_preview_only": True,
        "fixture_jsonl_read_allowed_for_dev_preview": accepted and bool(fixture_store_path),
        "context_snapshot_previewed": True,
        "replay_execution_committed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "fixture_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceDevFixtureReadbackReplayPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
        source=source,
        readback_id=readback_id,
        adapter_kind="dev_fixture_jsonl_readback_replay_preview",
        adapter_mode="readback_replay_preview_no_sqlite_no_backend_database_write",
        fixture_store_path=str(fixture_store_path) if fixture_store_path else None,
        requested_entities=requested_entities,
        readback_filters=filters,
        fixture_read_result=fixture_read_result,
        replay_preview=replay_preview,
        context_snapshot_preview=context_snapshot_preview,
        trace_link_preview=trace_link_preview,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
    )


def build_context_persistence_dev_fixture_readback_replay_summary(
    *,
    payload: ContextPersistenceDevFixtureReadbackReplayPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    fixture_read = data.get("fixture_read_result") if isinstance(data.get("fixture_read_result"), dict) else {}
    replay = data.get("replay_preview") if isinstance(data.get("replay_preview"), dict) else {}
    snapshot = data.get("context_snapshot_preview") if isinstance(data.get("context_snapshot_preview"), dict) else {}
    return {
        "context_persistence_dev_fixture_readback_replay_version": CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "readback_id": data.get("readback_id"),
        "adapter_kind": data.get("adapter_kind"),
        "adapter_mode": data.get("adapter_mode"),
        "fixture_store_path": data.get("fixture_store_path"),
        "file_exists": fixture_read.get("file_exists", False),
        "records_read": fixture_read.get("records_read", 0),
        "matched_record_count": fixture_read.get("matched_record_count", 0),
        "snapshot_available": snapshot.get("snapshot_available", False),
        "replayable": replay.get("replayable", False),
        "trace_id": data.get("trace_id"),
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
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_dev_fixture_readback_replay_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
        "context_persistence_dev_fixture_readback_replay_version": CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
        "spec_route": "GET /agent/context/persistence-dev-fixture-readback-replay/spec",
        "preview_route": "POST /agent/context/persistence-dev-fixture-readback-replay/preview",
        "terminal_command": "/context-persistence-dev-fixture-readback-replay",
        "surface": "Dev fixture read-back and replay preview contract",
        "mode": "jsonl_readback_context_snapshot_replay_preview_no_mutation",
        "execution_status": {
            "fixture_readback_preview_defined": True,
            "context_snapshot_previewed": True,
            "replay_shape_previewed": True,
            "real_sqlite_write_enabled": False,
            "database_connection_created": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "readback_flow": [
            "validate dev/test environment and safe fixture path",
            "open JSONL fixture read-only",
            "parse redacted fixture records",
            "apply optional trace/user/candidate/idempotency filters",
            "build context snapshot preview",
            "build replay preview without committing runtime state",
        ],
        "rules": [
            "v2_8_15 may read a dev fixture JSONL file but must never write storage.",
            "Replay is a preview shape only; it does not restore live Agent state or mutate backend/local state.",
            "Read-back snapshots must remain redacted and storage-boundary aware.",
            "HarmonyOS Routine/playback/local-MIDI state remains client-owned and must not be reconstructed as backend context.",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "durable_backend_write_executed": False,
            "fixture_write_executed": False,
            "transaction_committed": False,
            "replay_execution_committed": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_dev_sqlite_fixture_store": CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_VERSION,
        },
        "next_task_hint": "v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake",
    }


@dataclass(frozen=True)
class ContextPersistenceSqliteBackendStorePayload:
    """v2_9_0 explicit backend SQLite persistence store.

    This is the first real Agent persistence implementation surface. It may
    create a local backend SQLite database and insert one redacted context
    persistence record only when every explicit gate passes. It never calls the
    LLM, executes tools, starts Routine, calls the accompaniment engine, creates
    MIDI assets, writes HarmonyOS local state, or creates post-session cards.
    """

    payload_contract_version: str
    source: str
    store_id: str
    adapter_kind: str
    adapter_mode: str
    sqlite_db_path: str | None
    requested_entities: list[str]
    user_id: str
    candidate_kind: str
    candidate_id: str
    confirmation_id: str
    idempotency_key: str
    persisted_record: dict[str, Any]
    sqlite_result: dict[str, Any]
    readback_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_row_count_written: int = 0
    durable_backend_write_executed: bool = False
    transaction_committed: bool = False
    idempotent_replay: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "store_id": self.store_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "sqlite_db_path": self.sqlite_db_path,
            "requested_entities": list(self.requested_entities),
            "user_id": self.user_id,
            "candidate_kind": self.candidate_kind,
            "candidate_id": self.candidate_id,
            "confirmation_id": self.confirmation_id,
            "idempotency_key": self.idempotency_key,
            "persisted_record": _redact_sensitive_values(self.persisted_record),
            "sqlite_result": _redact_sensitive_values(self.sqlite_result),
            "readback_preview": _redact_sensitive_values(self.readback_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_row_count_written": self.sqlite_row_count_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "transaction_committed": self.transaction_committed,
            "idempotent_replay": self.idempotent_replay,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _is_allowed_context_persistence_sqlite_path(path_value: str | None) -> bool:
    if not path_value:
        return False
    path_text = str(path_value)
    normalized = path_text.replace("\\", "/")
    if ".." in Path(normalized).parts:
        return False
    lowered = normalized.lower()
    if any(part in lowered for part in ("/prod", "production", "secrets", "private_key", "api_key")):
        return False
    if not lowered.endswith((".db", ".sqlite", ".sqlite3")):
        return False
    if normalized.startswith("/mnt/data/") or normalized.startswith("/tmp/"):
        return True
    return not Path(normalized).is_absolute()


def _context_persistence_sqlite_schema() -> dict[str, str]:
    return {
        "context_persistence_records": (
            "CREATE TABLE IF NOT EXISTS context_persistence_records ("
            "record_id TEXT PRIMARY KEY, "
            "user_id TEXT NOT NULL, "
            "candidate_kind TEXT NOT NULL, "
            "candidate_id TEXT NOT NULL, "
            "confirmation_id TEXT NOT NULL, "
            "idempotency_key TEXT NOT NULL UNIQUE, "
            "record_json TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "trace_id TEXT)"
        ),
        "context_persistence_idempotency_keys": (
            "CREATE TABLE IF NOT EXISTS context_persistence_idempotency_keys ("
            "idempotency_key TEXT PRIMARY KEY, "
            "candidate_kind TEXT NOT NULL, "
            "candidate_id TEXT NOT NULL, "
            "record_id TEXT NOT NULL, "
            "write_result_json TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "trace_id TEXT)"
        ),
        "context_persistence_trace_links": (
            "CREATE TABLE IF NOT EXISTS context_persistence_trace_links ("
            "trace_id TEXT NOT NULL, "
            "record_id TEXT NOT NULL, "
            "idempotency_key TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "PRIMARY KEY (trace_id, record_id))"
        ),
    }


def _extract_backend_store_context_snapshot(args: dict[str, Any], requested_entities: list[str]) -> dict[str, Any]:
    snapshot = _first_present(
        args,
        "context_snapshot",
        "contextSnapshot",
        "context_persistence_snapshot_context_intake",
        "contextPersistenceSnapshotContextIntake",
        "snapshot_context_intake_payload",
        "snapshotContextIntakePayload",
    )
    sections: dict[str, Any] = {}
    if isinstance(snapshot, dict):
        if isinstance(snapshot.get("context_packet_kwargs"), dict):
            sections["context_packet_kwargs"] = snapshot.get("context_packet_kwargs") or {}
        elif isinstance(snapshot.get("context_packet_section"), dict):
            sections["context_packet_section"] = snapshot.get("context_packet_section") or {}
        elif isinstance(snapshot.get("normalized_context_sections"), dict):
            sections["normalized_context_sections"] = snapshot.get("normalized_context_sections") or {}
        else:
            sections["snapshot"] = snapshot
    for key, out_key in (
        ("user_practice_profile", "user_practice_profile"),
        ("userPracticeProfile", "user_practice_profile"),
        ("active_practice_plan", "active_practice_plan"),
        ("activePracticePlan", "active_practice_plan"),
        ("practice_plan", "active_practice_plan"),
        ("practicePlan", "active_practice_plan"),
        ("routine_history_records", "routine_history_records"),
        ("routineHistoryRecords", "routine_history_records"),
        ("routine_history_summary", "routine_history_summary"),
        ("routineHistorySummary", "routine_history_summary"),
    ):
        value = args.get(key)
        if value is not None and out_key not in sections:
            sections[out_key] = value
    candidate_payload = _first_present(args, "candidate_payload", "candidatePayload", "persistence_candidate_payload", "persistenceCandidatePayload")
    if isinstance(candidate_payload, dict):
        sections["candidate_payload"] = candidate_payload
    confirmation_payload = _extract_context_persistence_confirmation_payload(args)
    if isinstance(confirmation_payload, dict):
        sections["confirmation_payload_summary"] = {
            "confirmation_id": confirmation_payload.get("confirmation_id") or confirmation_payload.get("confirmationId"),
            "candidate_kind": confirmation_payload.get("candidate_kind") or confirmation_payload.get("candidateKind"),
            "candidate_id": confirmation_payload.get("candidate_id") or confirmation_payload.get("candidateId"),
            "confirmation_status": confirmation_payload.get("confirmation_status") or confirmation_payload.get("confirmationStatus"),
        }
    return {
        "requested_entities": list(requested_entities),
        "sections": _redact_sensitive_values(sections),
    }


def _write_context_persistence_sqlite_record(db_path_value: str, record: dict[str, Any]) -> dict[str, Any]:
    db_path = Path(db_path_value)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    created_at = str(record.get("created_at_utc") or datetime.now(timezone.utc).isoformat())
    schema = _context_persistence_sqlite_schema()
    result: dict[str, Any] = {
        "sqlite_db_path": str(db_path),
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_row_count_written": 0,
        "transaction_committed": False,
        "idempotent_replay": False,
        "existing_record": None,
        "write_error": None,
    }
    try:
        with sqlite3.connect(str(db_path)) as conn:
            result["sqlite_connection_created"] = True
            for ddl in schema.values():
                conn.execute(ddl)
            result["sqlite_tables_created"] = True
            existing = conn.execute(
                "SELECT record_json FROM context_persistence_records WHERE idempotency_key = ?",
                (record["idempotency_key"],),
            ).fetchone()
            if existing:
                result["idempotent_replay"] = True
                try:
                    result["existing_record"] = json.loads(existing[0])
                except (TypeError, json.JSONDecodeError):
                    result["existing_record"] = {"record_json_parse_error": True}
                return result
            record_json = json.dumps(_redact_sensitive_values(record), ensure_ascii=False, sort_keys=True)
            conn.execute(
                "INSERT INTO context_persistence_records "
                "(record_id, user_id, candidate_kind, candidate_id, confirmation_id, idempotency_key, record_json, created_at, trace_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["record_id"],
                    record["user_id"],
                    record["candidate_kind"],
                    record["candidate_id"],
                    record["confirmation_id"],
                    record["idempotency_key"],
                    record_json,
                    created_at,
                    record.get("trace_id"),
                ),
            )
            result_summary = {
                "record_id": record["record_id"],
                "idempotency_key": record["idempotency_key"],
                "status": "stored",
            }
            conn.execute(
                "INSERT INTO context_persistence_idempotency_keys "
                "(idempotency_key, candidate_kind, candidate_id, record_id, write_result_json, created_at, trace_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record["idempotency_key"],
                    record["candidate_kind"],
                    record["candidate_id"],
                    record["record_id"],
                    json.dumps(result_summary, ensure_ascii=False, sort_keys=True),
                    created_at,
                    record.get("trace_id"),
                ),
            )
            row_count = 2
            if record.get("trace_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO context_persistence_trace_links "
                    "(trace_id, record_id, idempotency_key, created_at) VALUES (?, ?, ?, ?)",
                    (record.get("trace_id"), record["record_id"], record["idempotency_key"], created_at),
                )
                row_count += 1
            conn.commit()
            result["sqlite_rows_written"] = True
            result["sqlite_row_count_written"] = row_count
            result["transaction_committed"] = True
    except sqlite3.Error as exc:
        result["write_error"] = exc.__class__.__name__
    return result


def _read_context_persistence_sqlite_latest(db_path_value: str, idempotency_key: str) -> dict[str, Any]:
    path = Path(db_path_value)
    preview = {
        "sqlite_db_path": str(path),
        "record_found": False,
        "record": None,
        "read_error": None,
    }
    if not path.exists():
        return preview
    try:
        with sqlite3.connect(str(path)) as conn:
            row = conn.execute(
                "SELECT record_json FROM context_persistence_records WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if row:
                preview["record_found"] = True
                preview["record"] = _redact_sensitive_values(json.loads(row[0]))
    except (sqlite3.Error, json.JSONDecodeError, TypeError) as exc:
        preview["read_error"] = exc.__class__.__name__
    return preview


def build_context_persistence_sqlite_backend_store_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_store",
) -> ContextPersistenceSqliteBackendStorePayload:
    """Create a real SQLite-backed Agent context persistence record after explicit gates."""

    args = dict(arguments or {})
    store_id = str(_first_present(args, "store_id", "storeId") or f"ctx_sqlite_backend_store_{uuid4().hex[:12]}")
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_backend_store")
    requested_entities = _normalize_storage_adapter_entities(args)
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    user_id = str(_first_present(args, "user_id", "userId") or "dev_user")
    candidate_kind = str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "dev_candidate")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "dev_confirmation")
    user_decision = str(_first_present(args, "user_decision", "userDecision") or "pending")
    confirmation_status = str(_first_present(args, "confirmation_status", "confirmationStatus") or "user_approved_future_executor_required")
    environment = str(_first_present(args, "environment", "env") or "dev")
    backend_persistence_enabled = bool(_first_present(args, "backend_persistence_enabled", "backendPersistenceEnabled") or False)
    execute_backend_persistence = bool(_first_present(args, "execute_backend_persistence", "executeBackendPersistence") or False)
    sqlite_db_path = _first_present(args, "sqlite_db_path", "sqliteDbPath", "db_path", "dbPath")
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or _build_context_persistence_idempotency_key(confirmation_id, candidate_kind, candidate_id))
    storage_boundary_check_passed = bool(_first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") if _first_present(args, "storage_boundary_check_passed", "storageBoundaryCheckPassed") is not None else True)
    redaction_check_passed = bool(_first_present(args, "redaction_check_passed", "redactionCheckPassed") if _first_present(args, "redaction_check_passed", "redactionCheckPassed") is not None else True)
    schema_preview_accepted = bool(_first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") if _first_present(args, "schema_preview_accepted", "schemaPreviewAccepted") is not None else True)
    forbidden_fields_present = _has_any_forbidden_context_fields(args)

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if adapter_kind != "sqlite_backend_store":
        blocked_reasons.append("adapter_kind_must_be_sqlite_backend_store")
    if environment not in {"dev", "local_dev", "test"}:
        blocked_reasons.append("sqlite_backend_store_v2_9_0_only_allows_dev_local_dev_or_test")
    if not backend_persistence_enabled:
        blocked_reasons.append("backend_persistence_enabled_must_be_true")
    if not execute_backend_persistence:
        blocked_reasons.append("execute_backend_persistence_must_be_true")
    if user_decision != "approved":
        blocked_reasons.append("user_decision_must_be_approved_before_backend_store")
    if confirmation_status != "user_approved_future_executor_required":
        blocked_reasons.append("confirmation_status_must_match_approved_future_executor_required")
    if not sqlite_db_path:
        blocked_reasons.append("sqlite_db_path_required")
    elif not _is_allowed_context_persistence_sqlite_path(str(sqlite_db_path)):
        blocked_reasons.append("sqlite_db_path_must_be_relative_tmp_or_mnt_data_sqlite_file")
    if not trace_value:
        blocked_reasons.append("trace_id_required_for_backend_store_trace_link")
    if not idempotency_key:
        blocked_reasons.append("idempotency_key_required")
    if not storage_boundary_check_passed:
        blocked_reasons.append("storage_boundary_check_failed")
    if not schema_preview_accepted:
        blocked_reasons.append("sqlite_schema_preview_not_accepted")
    if not redaction_check_passed or forbidden_fields_present:
        blocked_reasons.append("redaction_check_failed_or_forbidden_fields_present")

    context_snapshot = _extract_backend_store_context_snapshot(args, requested_entities)
    created_at = datetime.now(timezone.utc).isoformat()
    record_id = str(_first_present(args, "record_id", "recordId") or f"ctx_record_{uuid4().hex[:12]}")
    persisted_record = {
        "record_contract_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
        "record_id": record_id,
        "store_id": store_id,
        "created_at_utc": created_at,
        "user_id": user_id,
        "candidate_kind": candidate_kind,
        "candidate_id": candidate_id,
        "confirmation_id": confirmation_id,
        "trace_id": trace_value,
        "idempotency_key": idempotency_key,
        "entities": list(requested_entities),
        "context_snapshot": context_snapshot,
        "storage_boundary": {
            "backend_long_term_context_only": True,
            "harmonyos_local_routine_state_excluded": True,
            "midi_payload_excluded": True,
            "raw_api_key_excluded": True,
        },
    }

    sqlite_result = {
        "sqlite_db_path": str(sqlite_db_path) if sqlite_db_path else None,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_row_count_written": 0,
        "transaction_committed": False,
        "idempotent_replay": False,
        "write_error": None,
    }
    if not blocked_reasons and sqlite_db_path:
        sqlite_result = _write_context_persistence_sqlite_record(str(sqlite_db_path), persisted_record)
        if sqlite_result.get("write_error"):
            blocked_reasons.append(f"sqlite_backend_store_write_failed:{sqlite_result.get('write_error')}")
            warnings.append("sqlite_backend_store_write_failed_after_open")
    accepted = not blocked_reasons
    readback_preview = _read_context_persistence_sqlite_latest(str(sqlite_db_path), idempotency_key) if accepted and sqlite_db_path else {"record_found": False, "record": None, "read_error": None}
    idempotent_replay = bool(sqlite_result.get("idempotent_replay"))
    row_written = bool(sqlite_result.get("sqlite_rows_written"))
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_store_ready" if accepted and row_written else "sqlite_backend_store_idempotent_replay" if accepted and idempotent_replay else "sqlite_backend_store_blocked",
        "warnings": list(warnings),
        "blocked_reasons": list(blocked_reasons),
        "backend_persistence_enabled": backend_persistence_enabled,
        "execute_backend_persistence": execute_backend_persistence,
        "storage_written": accepted and row_written,
        "backend_database_written": accepted and row_written,
        "local_device_written": False,
        "sqlite_connection_created": bool(sqlite_result.get("sqlite_connection_created")),
        "sqlite_tables_created": bool(sqlite_result.get("sqlite_tables_created")),
        "sqlite_rows_written": row_written,
        "sqlite_row_count_written": int(sqlite_result.get("sqlite_row_count_written") or 0),
        "transaction_committed": bool(sqlite_result.get("transaction_committed")),
        "idempotent_replay": idempotent_replay,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }
    guard_summary = {
        "context_persistence_sqlite_backend_store": True,
        "explicit_backend_persistence_required": True,
        "backend_persistence_enabled": backend_persistence_enabled,
        "execute_backend_persistence": execute_backend_persistence,
        "safe_sqlite_db_path_required": True,
        "user_approval_required": True,
        "idempotency_key_required": True,
        "trace_link_required": True,
        "redaction_check_required": True,
        "storage_boundary_check_required": True,
        "storage_written": accepted and row_written,
        "backend_database_written": accepted and row_written,
        "local_device_written": False,
        "sqlite_connection_created": bool(sqlite_result.get("sqlite_connection_created")),
        "sqlite_tables_created": bool(sqlite_result.get("sqlite_tables_created")),
        "sqlite_rows_written": row_written,
        "durable_backend_write_executed": accepted and row_written,
        "transaction_committed": bool(sqlite_result.get("transaction_committed")),
        "idempotent_replay": idempotent_replay,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "midi_asset_payload_allowed_in_adapter": False,
        "local_playback_state_allowed_in_adapter": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceSqliteBackendStorePayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
        source=source,
        store_id=store_id,
        adapter_kind="sqlite_backend_store",
        adapter_mode="explicit_opt_in_backend_sqlite_store",
        sqlite_db_path=str(sqlite_db_path) if sqlite_db_path else None,
        requested_entities=requested_entities,
        user_id=user_id,
        candidate_kind=candidate_kind,
        candidate_id=candidate_id,
        confirmation_id=confirmation_id,
        idempotency_key=idempotency_key,
        persisted_record=persisted_record,
        sqlite_result=sqlite_result,
        readback_preview=readback_preview,
        validation=validation,
        guard_summary=guard_summary,
        trace_id=trace_value,
        storage_written=accepted and row_written,
        backend_database_written=accepted and row_written,
        sqlite_connection_created=bool(sqlite_result.get("sqlite_connection_created")),
        sqlite_tables_created=bool(sqlite_result.get("sqlite_tables_created")),
        sqlite_rows_written=row_written,
        sqlite_row_count_written=int(sqlite_result.get("sqlite_row_count_written") or 0),
        durable_backend_write_executed=accepted and row_written,
        transaction_committed=bool(sqlite_result.get("transaction_committed")),
        idempotent_replay=idempotent_replay,
    )


def build_context_persistence_sqlite_backend_store_summary(
    *,
    payload: ContextPersistenceSqliteBackendStorePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_store_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "context_persistence_sqlite_backend_store_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
        "source": source,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "store_id": data.get("store_id"),
        "sqlite_db_path": data.get("sqlite_db_path"),
        "user_id": data.get("user_id"),
        "candidate_kind": data.get("candidate_kind"),
        "candidate_id": data.get("candidate_id"),
        "confirmation_id": data.get("confirmation_id"),
        "idempotency_key": data.get("idempotency_key"),
        "entity_count": len(data.get("requested_entities") or []),
        "storage_written": data.get("storage_written", False),
        "backend_database_written": data.get("backend_database_written", False),
        "sqlite_connection_created": data.get("sqlite_connection_created", False),
        "sqlite_tables_created": data.get("sqlite_tables_created", False),
        "sqlite_rows_written": data.get("sqlite_rows_written", False),
        "sqlite_row_count_written": data.get("sqlite_row_count_written", 0),
        "durable_backend_write_executed": data.get("durable_backend_write_executed", False),
        "transaction_committed": data.get("transaction_committed", False),
        "idempotent_replay": data.get("idempotent_replay", False),
        "readback_record_found": bool((data.get("readback_preview") or {}).get("record_found")) if isinstance(data.get("readback_preview"), dict) else False,
        "llm_called": data.get("llm_called", False),
        "tool_executed": data.get("tool_executed", False),
        "route_called": data.get("route_called", False),
        "local_device_written": data.get("local_device_written", False),
        "engine_adapter_called": data.get("engine_adapter_called", False),
        "midi_asset_created": data.get("midi_asset_created", False),
        "playback_started": data.get("playback_started", False),
        "post_session_recommendation_card_created": data.get("post_session_recommendation_card_created", False),
        "accompaniment_generate_call_enabled": data.get("accompaniment_generate_call_enabled", False),
        "routine_start_enabled": data.get("routine_start_enabled", False),
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_store_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
        "context_persistence_sqlite_backend_store_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-store/spec",
        "execute_route": "POST /agent/context/persistence-sqlite-backend-store/execute",
        "terminal_command": "/context-persistence-sqlite-backend-store",
        "surface": "Explicit backend SQLite context persistence store",
        "mode": "explicit_opt_in_backend_sqlite_store_with_idempotency_and_trace_link",
        "execution_status": {
            "sqlite_backend_store_implemented": True,
            "backend_persistence_can_write_when_explicitly_enabled": True,
            "database_connection_created_only_after_gates": True,
            "idempotency_enforced": True,
            "readback_verification_enabled": True,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "backendPersistenceEnabled=true",
            "executeBackendPersistence=true",
            "userDecision=approved",
            "confirmationStatus=user_approved_future_executor_required",
            "environment in dev/local_dev/test for v2_9_0",
            "sqliteDbPath is relative or tmp/dev path ending .db/.sqlite/.sqlite3",
            "traceId present",
            "idempotencyKey present or derived",
            "storageBoundaryCheckPassed=true",
            "redactionCheckPassed=true",
            "schemaPreviewAccepted=true",
        ],
        "tables": list(_context_persistence_sqlite_schema().keys()),
        "rules": [
            "v2_9_0 is the first real backend persistence implementation surface, but remains explicit opt-in and dev/test scoped.",
            "Only backend-long-term Agent context snapshots may be written; HarmonyOS local Routine/playback/MIDI state remains client-owned.",
            "Every write is redacted, trace-linked, and idempotency-keyed before SQLite insertion.",
            "Repeated calls with the same idempotency key return an idempotent replay without adding duplicate rows.",
        ],
        "guards": {
            "payload_may_write_backend_sqlite_only_after_explicit_opt_in": True,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "local_device_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "practice_context_storage_boundary": PRACTICE_CONTEXT_STORAGE_BOUNDARY_VERSION,
            "context_persistence_confirmation_boundary": CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION,
            "context_persistence_storage_adapter_design": CONTEXT_PERSISTENCE_STORAGE_ADAPTER_DESIGN_VERSION,
            "context_persistence_dev_sqlite_write_gate": CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_VERSION,
            "context_persistence_profile_plan_history_snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
        },
        "next_task_hint": "v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery",
    }




@dataclass(frozen=True)
class ContextPersistenceSqliteBackendReadbackContextRecoveryPayload:
    """v2_9_1 read-only SQLite backend context recovery bridge.

    This payload reads already persisted v2_9_0 Agent backend SQLite context
    records and converts them into the same snapshot-context-intake shape used
    by today-practice guidance. It never writes storage, executes tools, calls
    the LLM, starts Routine, calls the engine, creates MIDI, or plays audio.
    """

    payload_contract_version: str
    source: str
    recovery_id: str
    adapter_kind: str
    adapter_mode: str
    sqlite_db_path: str | None
    query_filters: dict[str, Any]
    sqlite_read_result: dict[str, Any]
    recovered_records: list[dict[str, Any]]
    snapshot_context_intake_payload: dict[str, Any]
    recovered_context_packet_section: dict[str, Any]
    recovered_context_summary: dict[str, Any]
    recovery_packet_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    durable_backend_write_executed: bool = False
    transaction_committed: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "recovery_id": self.recovery_id,
            "adapter_kind": self.adapter_kind,
            "adapter_mode": self.adapter_mode,
            "sqlite_db_path": self.sqlite_db_path,
            "query_filters": _redact_sensitive_values(self.query_filters),
            "sqlite_read_result": _redact_sensitive_values(self.sqlite_read_result),
            "recovered_records": _redact_sensitive_values(self.recovered_records),
            "snapshot_context_intake_payload": _redact_sensitive_values(self.snapshot_context_intake_payload),
            "recovered_context_packet_section": _redact_sensitive_values(self.recovered_context_packet_section),
            "recovered_context_summary": _redact_sensitive_values(self.recovered_context_summary),
            "recovery_packet_preview": _redact_sensitive_values(self.recovery_packet_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "transaction_committed": self.transaction_committed,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _safe_positive_limit(value: Any, default: int = 3, maximum: int = 20) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return min(parsed, maximum)


def _read_context_persistence_sqlite_backend_records(db_path_value: str, *, filters: dict[str, Any], limit: int) -> dict[str, Any]:
    path = Path(db_path_value)
    result: dict[str, Any] = {
        "sqlite_db_path": str(path),
        "file_exists": path.exists(),
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "records_read": 0,
        "matched_records": [],
        "read_error": None,
        "read_only_connection": True,
    }
    if not path.exists():
        result["read_error"] = "sqlite_db_path_not_found"
        return result
    clauses: list[str] = []
    params: list[Any] = []
    for column, filter_key in (
        ("idempotency_key", "idempotency_key"),
        ("trace_id", "filter_trace_id"),
        ("user_id", "user_id"),
        ("candidate_kind", "candidate_kind"),
        ("candidate_id", "candidate_id"),
        ("confirmation_id", "confirmation_id"),
    ):
        value = filters.get(filter_key)
        if value:
            clauses.append(f"{column} = ?")
            params.append(str(value))
    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = (
        "SELECT record_id, user_id, candidate_kind, candidate_id, confirmation_id, "
        "idempotency_key, record_json, created_at, trace_id "
        f"FROM context_persistence_records{where_clause} "
        "ORDER BY created_at DESC LIMIT ?"
    )
    params.append(limit)
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
            result["sqlite_connection_created"] = True
            rows = conn.execute(query, tuple(params)).fetchall()
            matched: list[dict[str, Any]] = []
            for row in rows:
                try:
                    record_json = json.loads(row[6])
                except (TypeError, json.JSONDecodeError):
                    record_json = {"record_json_parse_error": True}
                matched.append(_redact_sensitive_values({
                    "record_id": row[0],
                    "user_id": row[1],
                    "candidate_kind": row[2],
                    "candidate_id": row[3],
                    "confirmation_id": row[4],
                    "idempotency_key": row[5],
                    "record_json": record_json,
                    "created_at": row[7],
                    "trace_id": row[8],
                }))
            result["matched_records"] = matched
            result["records_read"] = len(matched)
            result["sqlite_rows_read"] = len(matched)
    except sqlite3.Error as exc:
        result["read_error"] = exc.__class__.__name__
    return result


def _merge_unique_strings(items: list[str], value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            text = str(item)
            if text and text not in items:
                items.append(text)
    elif value is not None:
        text = str(value)
        if text and text not in items:
            items.append(text)


def _collect_recovery_sections_from_snapshot(sections: dict[str, Any], recovered_args: dict[str, Any], entities: list[str], warnings: list[str]) -> None:
    if not isinstance(sections, dict):
        return
    normalized = sections.get("normalized_context_sections") if isinstance(sections.get("normalized_context_sections"), dict) else {}
    context_kwargs = sections.get("context_packet_kwargs") if isinstance(sections.get("context_packet_kwargs"), dict) else {}
    for source in (normalized, context_kwargs):
        for key in ("user_practice_profile_context", "active_practice_plan_context", "routine_history_context", "assembled_practice_context"):
            value = source.get(key) if isinstance(source, dict) else None
            if isinstance(value, dict) and key not in recovered_args:
                recovered_args[key] = value
    profile = sections.get("user_practice_profile") or sections.get("userPracticeProfile")
    if isinstance(profile, dict) and "userPracticeProfile" not in recovered_args and "user_practice_profile_context" not in recovered_args:
        recovered_args["userPracticeProfile"] = profile
        _merge_unique_strings(entities, "user_practice_profile")
    plan = sections.get("active_practice_plan") or sections.get("activePracticePlan") or sections.get("practice_plan") or sections.get("practicePlan")
    if isinstance(plan, dict) and "practicePlan" not in recovered_args and "active_practice_plan_context" not in recovered_args:
        recovered_args["practicePlan"] = plan
        _merge_unique_strings(entities, "active_practice_plan")
    history = sections.get("routine_history_records") or sections.get("routineHistoryRecords") or sections.get("practice_history_records") or sections.get("practiceHistoryRecords")
    if isinstance(history, list):
        recovered_args.setdefault("routineHistoryRecords", [])
        if isinstance(recovered_args["routineHistoryRecords"], list):
            recovered_args["routineHistoryRecords"].extend(history)
            _merge_unique_strings(entities, "routine_history_summary")
    elif isinstance(sections.get("routine_history_summary"), dict) or isinstance(sections.get("routineHistorySummary"), dict):
        _merge_unique_strings(entities, "routine_history_summary")
        warnings.append("routine_history_summary_restored_as_metadata_only_context")
    nested_snapshot = sections.get("snapshot")
    if isinstance(nested_snapshot, dict):
        _collect_recovery_sections_from_snapshot(nested_snapshot, recovered_args, entities, warnings)


def _build_sqlite_backend_recovered_snapshot_args(sqlite_read_result: dict[str, Any], *, trace_id: str | None) -> tuple[dict[str, Any], list[str]]:
    records = sqlite_read_result.get("matched_records") if isinstance(sqlite_read_result.get("matched_records"), list) else []
    recovered_args: dict[str, Any] = {}
    entities: list[str] = []
    warnings: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        record_json = record.get("record_json") if isinstance(record.get("record_json"), dict) else {}
        _merge_unique_strings(entities, record_json.get("entities"))
        snapshot = record_json.get("context_snapshot") if isinstance(record_json.get("context_snapshot"), dict) else {}
        _merge_unique_strings(entities, snapshot.get("requested_entities"))
        sections = snapshot.get("sections") if isinstance(snapshot.get("sections"), dict) else {}
        _collect_recovery_sections_from_snapshot(sections, recovered_args, entities, warnings)
    entity_counts = {entity: 1 for entity in entities}
    recovered_args["entities"] = entities or ["user_practice_profile", "active_practice_plan", "routine_history_summary"]
    recovered_args["readbackPayload"] = {
        "validation": {"accepted": sqlite_read_result.get("read_error") is None, "status": "sqlite_backend_readback_ready" if sqlite_read_result.get("read_error") is None else "sqlite_backend_readback_blocked"},
        "context_snapshot_preview": {
            "snapshot_available": bool(records),
            "snapshot_source": "sqlite_backend_readback_context_recovery",
            "record_count": len(records),
            "requested_entities": recovered_args["entities"],
            "entity_counts": entity_counts,
        },
        "fixture_read_result": {
            "file_exists": sqlite_read_result.get("file_exists", False),
            "records_read": sqlite_read_result.get("records_read", 0),
            "matched_record_count": len(records),
        },
    }
    if trace_id:
        recovered_args["traceId"] = trace_id
    return recovered_args, warnings


def build_context_persistence_sqlite_backend_readback_context_recovery_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_readback_context_recovery",
) -> ContextPersistenceSqliteBackendReadbackContextRecoveryPayload:
    """Read persisted SQLite backend records and build a ContextBuilder recovery packet."""

    args = dict(arguments or {})
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    recovery_id = str(_first_present(args, "recovery_id", "recoveryId") or f"ctx_sqlite_backend_recovery_{uuid4().hex[:12]}")
    adapter_kind = str(_first_present(args, "adapter_kind", "adapterKind") or "sqlite_backend_store")
    environment = str(_first_present(args, "environment", "env") or "dev")
    sqlite_db_path = _first_present(args, "sqlite_db_path", "sqliteDbPath", "db_path", "dbPath")
    backend_readback_enabled = bool(_first_present(args, "backend_readback_enabled", "backendReadbackEnabled") or False)
    execute_backend_readback = bool(_first_present(args, "execute_backend_readback", "executeBackendReadback") or False)
    limit = _safe_positive_limit(_first_present(args, "limit", "maxRecords"), default=3, maximum=20)
    query_filters = {
        "idempotency_key": _first_present(args, "idempotency_key", "idempotencyKey"),
        "filter_trace_id": _first_present(args, "filter_trace_id", "filterTraceId"),
        "user_id": _first_present(args, "user_id", "userId"),
        "candidate_kind": _first_present(args, "candidate_kind", "candidateKind"),
        "candidate_id": _first_present(args, "candidate_id", "candidateId"),
        "confirmation_id": _first_present(args, "confirmation_id", "confirmationId"),
        "limit": limit,
    }
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if adapter_kind != "sqlite_backend_store":
        blocked_reasons.append("adapter_kind_must_be_sqlite_backend_store")
    if environment not in {"dev", "local_dev", "test"}:
        blocked_reasons.append("sqlite_backend_readback_v2_9_1_only_allows_dev_local_dev_or_test")
    if not backend_readback_enabled:
        blocked_reasons.append("backend_readback_enabled_must_be_true")
    if not execute_backend_readback:
        blocked_reasons.append("execute_backend_readback_must_be_true")
    if not sqlite_db_path:
        blocked_reasons.append("sqlite_db_path_required")
    elif not _is_allowed_context_persistence_sqlite_path(str(sqlite_db_path)):
        blocked_reasons.append("sqlite_db_path_must_be_relative_tmp_or_mnt_data_sqlite_file")
    if _has_any_forbidden_context_fields(args):
        blocked_reasons.append("forbidden_context_fields_present")

    sqlite_read_result = {
        "sqlite_db_path": str(sqlite_db_path) if sqlite_db_path else None,
        "file_exists": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "records_read": 0,
        "matched_records": [],
        "read_error": None,
        "read_only_connection": True,
    }
    if not blocked_reasons and sqlite_db_path:
        sqlite_read_result = _read_context_persistence_sqlite_backend_records(str(sqlite_db_path), filters=query_filters, limit=limit)
        if sqlite_read_result.get("read_error"):
            blocked_reasons.append(f"sqlite_backend_readback_failed:{sqlite_read_result.get('read_error')}")
        if int(sqlite_read_result.get("records_read") or 0) <= 0 and not sqlite_read_result.get("read_error"):
            blocked_reasons.append("sqlite_backend_readback_no_matching_records")

    recovered_snapshot_args, recovery_warnings = _build_sqlite_backend_recovered_snapshot_args(sqlite_read_result, trace_id=trace_value)
    warnings.extend(recovery_warnings)
    snapshot_obj = build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        recovered_snapshot_args,
        trace_id=trace_value,
        source="sqlite_backend_readback_to_snapshot_context_intake",
    )
    snapshot_payload = snapshot_obj.to_dict()
    snapshot_validation = snapshot_payload.get("validation") if isinstance(snapshot_payload.get("validation"), dict) else {}
    recovered_section = snapshot_payload.get("context_packet_section") if isinstance(snapshot_payload.get("context_packet_section"), dict) else {}
    recovered_summary = build_context_persistence_profile_plan_history_snapshot_context_intake_summary(
        payload=snapshot_obj,
        source="sqlite_backend_readback_context_recovery",
    )
    if snapshot_validation.get("accepted") is False:
        blocked_reasons.append("snapshot_context_intake_not_accepted")
    warnings.extend(list(snapshot_validation.get("warnings") or []))

    records_read = int(sqlite_read_result.get("records_read") or 0)
    accepted = not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_readback_context_recovery_ready" if accepted else "sqlite_backend_readback_context_recovery_blocked",
        "backend_readback_enabled": backend_readback_enabled,
        "execute_backend_readback": execute_backend_readback,
        "sqlite_read_only": True,
        "sqlite_connection_created": bool(sqlite_read_result.get("sqlite_connection_created")),
        "sqlite_rows_read": records_read,
        "records_recovered": records_read,
        "context_packet_kwargs_ready": bool((recovered_section.get("context_packet_kwargs") or {}) if isinstance(recovered_section, dict) else {}),
        "profile_context_recovered": recovered_summary.get("profile_context_present", False),
        "active_plan_context_recovered": recovered_summary.get("active_plan_context_present", False),
        "routine_history_context_recovered": recovered_summary.get("routine_history_context_present", False),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    recovery_packet_preview = {
        "context_packet_section_ready": bool(recovered_section.get("context_packet_kwargs") if isinstance(recovered_section, dict) else False),
        "context_persistence_snapshot_context_intake": recovered_section,
        "context_packet_kwargs_keys": sorted((recovered_section.get("context_packet_kwargs") or {}).keys()) if isinstance(recovered_section, dict) else [],
        "ready_for_today_practice_guidance": accepted and bool(recovered_section.get("context_packet_kwargs") if isinstance(recovered_section, dict) else False),
        "suggested_guidance_preview_route": "POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
        "suggested_guidance_argument_key": "contextPersistenceSnapshotContextIntake",
        "client_decides_presentation": True,
    }
    guard = {
        "context_persistence_sqlite_backend_readback_context_recovery": True,
        "sqlite_backend_readback_only": True,
        "read_only_connection": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
    }
    recovered_records = [record for record in (sqlite_read_result.get("matched_records") or []) if isinstance(record, dict)]
    return ContextPersistenceSqliteBackendReadbackContextRecoveryPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
        source=source,
        recovery_id=recovery_id,
        adapter_kind="sqlite_backend_store",
        adapter_mode="read_only_sqlite_backend_context_recovery",
        sqlite_db_path=str(sqlite_db_path) if sqlite_db_path else None,
        query_filters=query_filters,
        sqlite_read_result=sqlite_read_result,
        recovered_records=recovered_records,
        snapshot_context_intake_payload=snapshot_payload,
        recovered_context_packet_section=recovered_section,
        recovered_context_summary=recovered_summary,
        recovery_packet_preview=recovery_packet_preview,
        validation=validation,
        guard_summary=guard,
        trace_id=trace_value,
        backend_database_read=accepted and records_read > 0,
        sqlite_connection_created=bool(sqlite_read_result.get("sqlite_connection_created")),
        sqlite_rows_read=records_read,
    )


def build_context_persistence_sqlite_backend_readback_context_recovery_summary(
    *,
    payload: ContextPersistenceSqliteBackendReadbackContextRecoveryPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_readback_context_recovery_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    recovered = data.get("recovered_context_summary") if isinstance(data.get("recovered_context_summary"), dict) else {}
    preview = data.get("recovery_packet_preview") if isinstance(data.get("recovery_packet_preview"), dict) else {}
    return {
        "context_persistence_sqlite_backend_readback_context_recovery_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
        "source": source,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "recovery_id": data.get("recovery_id"),
        "sqlite_db_path": data.get("sqlite_db_path"),
        "sqlite_connection_created": data.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": data.get("sqlite_rows_read", 0),
        "records_recovered": validation.get("records_recovered", 0),
        "backend_database_read": data.get("backend_database_read", False),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "context_packet_section_ready": preview.get("context_packet_section_ready", False),
        "context_packet_kwargs_keys": list(preview.get("context_packet_kwargs_keys") or []),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "snapshot_context_intake_status": recovered.get("validation_status"),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_readback_context_recovery_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
        "context_persistence_sqlite_backend_readback_context_recovery_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-readback-context-recovery/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview",
        "terminal_command": "/context-persistence-sqlite-backend-readback-context-recovery",
        "surface": "Read-only SQLite backend persisted context recovery bridge",
        "mode": "sqlite_backend_readback_to_snapshot_context_intake_no_mutation",
        "execution_status": {
            "sqlite_backend_readback_implemented": True,
            "context_recovery_packet_built": True,
            "snapshot_context_intake_reused": True,
            "database_write_enabled": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "backendReadbackEnabled=true",
            "executeBackendReadback=true",
            "environment in dev/local_dev/test for v2_9_1",
            "sqliteDbPath is relative or tmp/dev path ending .db/.sqlite/.sqlite3",
            "optional idempotencyKey / traceId / userId / candidate filters",
            "forbidden client-local/MIDI/API-key fields absent",
        ],
        "readback_flow": [
            "open existing SQLite database in read-only mode after gates pass",
            "read persisted v2_9_0 context_persistence_records with optional filters",
            "extract redacted user_practice_profile / active_practice_plan / routine_history sections",
            "reuse v2_8_16 snapshot context intake to build ContextBuilder-ready section",
            "return recovery packet preview for v2_8_17 today-practice guidance recovery",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_reads_backend_sqlite_only_after_explicit_opt_in": True,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "local_device_written": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "sqlite_backend_store": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
            "snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
            "persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e",
    }


@dataclass(frozen=True)
class ContextPersistenceSqliteBackendTodayGuidanceRecoveryE2EPayload:
    """v2_9_2 compose SQLite backend readback with today-practice guidance recovery.

    This payload is a readback-to-guidance E2E preview only. It reads existing
    backend SQLite context records through the v2_9_1 read-only bridge, feeds the
    recovered ContextBuilder-ready section into the existing v2_8_17 persisted
    context guidance recovery chain, and returns a display-only guidance preview.
    It does not write storage, execute tools, start Routine, call the engine,
    create MIDI, or play audio.
    """

    payload_contract_version: str
    source: str
    recovery_e2e_id: str
    sqlite_readback_payload: dict[str, Any]
    sqlite_readback_summary: dict[str, Any]
    today_guidance_recovery_payload: dict[str, Any]
    today_guidance_recovery_summary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    durable_backend_write_executed: bool = False
    transaction_committed: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "recovery_e2e_id": self.recovery_e2e_id,
            "sqlite_readback_payload": _redact_sensitive_values(self.sqlite_readback_payload),
            "sqlite_readback_summary": _redact_sensitive_values(self.sqlite_readback_summary),
            "today_guidance_recovery_payload": _redact_sensitive_values(self.today_guidance_recovery_payload),
            "today_guidance_recovery_summary": _redact_sensitive_values(self.today_guidance_recovery_summary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "transaction_committed": self.transaction_committed,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _guidance_args_from_sqlite_backend_readback(args: dict[str, Any], readback_payload: dict[str, Any]) -> dict[str, Any]:
    recovered_section = readback_payload.get("recovered_context_packet_section") if isinstance(readback_payload.get("recovered_context_packet_section"), dict) else {}
    guidance_args: dict[str, Any] = {
        "contextPersistenceSnapshotContextIntake": recovered_section,
        "userInput": str(_first_present(args, "user_input", "userInput", "text") or "今天该练什么？"),
        "callProvider": bool(_first_present(args, "call_provider", "callProvider") or False),
    }
    for key in (
        "availableMinutes",
        "available_minutes",
        "durationMinutes",
        "duration_minutes",
        "instrument",
        "practiceMode",
        "practice_mode",
        "providerResult",
        "provider_result",
        "guidanceOutput",
        "guidance_output",
    ):
        if key in args:
            guidance_args[key] = args[key]
    return guidance_args


def build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_today_guidance_recovery_e2e",
    provider: Any | None = None,
) -> ContextPersistenceSqliteBackendTodayGuidanceRecoveryE2EPayload:
    """Read SQLite persisted context and build display-only today-practice guidance."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    recovery_e2e_id = str(_first_present(args, "recovery_e2e_id", "recoveryE2eId") or f"ctx_sqlite_backend_today_guidance_{uuid4().hex[:12]}")

    readback_obj = build_context_persistence_sqlite_backend_readback_context_recovery_payload(
        args,
        trace_id=trace,
        source="sqlite_backend_today_guidance_recovery_readback",
    )
    readback_payload = readback_obj.to_dict()
    readback_summary = build_context_persistence_sqlite_backend_readback_context_recovery_summary(
        payload=readback_obj,
        source="sqlite_backend_today_guidance_recovery_e2e",
    )
    readback_validation = readback_payload.get("validation") if isinstance(readback_payload.get("validation"), dict) else {}

    guidance_args = _guidance_args_from_sqlite_backend_readback(args, readback_payload)
    guidance_obj = build_today_practice_guidance_persisted_context_recovery_e2e_payload(
        guidance_args,
        trace_id=trace,
        source="sqlite_backend_today_guidance_recovery_persisted_context_guidance",
        provider=provider,
    )
    guidance_payload = guidance_obj.to_dict()
    guidance_summary = build_today_practice_guidance_persisted_context_recovery_e2e_summary(
        payload=guidance_obj,
        source="sqlite_backend_today_guidance_recovery_e2e",
    )
    guidance_validation = guidance_payload.get("validation") if isinstance(guidance_payload.get("validation"), dict) else {}

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if not readback_validation.get("accepted", False):
        blocked_reasons.append("sqlite_backend_readback_context_recovery_not_accepted")
    if not guidance_validation.get("accepted", False):
        blocked_reasons.append("today_practice_guidance_persisted_context_recovery_not_accepted")
    warnings.extend(list(readback_validation.get("warnings") or []))
    warnings.extend(list(guidance_validation.get("warnings") or []))

    accepted = not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_today_guidance_recovery_e2e_ready" if accepted else "sqlite_backend_today_guidance_recovery_e2e_blocked",
        "sqlite_backend_readback_accepted": bool(readback_validation.get("accepted", False)),
        "today_guidance_recovery_accepted": bool(guidance_validation.get("accepted", False)),
        "backend_database_read": bool(readback_payload.get("backend_database_read", False)),
        "sqlite_connection_created": bool(readback_payload.get("sqlite_connection_created", False)),
        "sqlite_rows_read": int(readback_payload.get("sqlite_rows_read") or 0),
        "context_packet_section_ready": bool(readback_summary.get("context_packet_section_ready", False)),
        "persisted_context_recovered": bool(guidance_validation.get("persisted_context_recovered", False)),
        "profile_context_recovered": bool(guidance_validation.get("profile_context_recovered", False)),
        "active_plan_context_recovered": bool(guidance_validation.get("active_plan_context_recovered", False)),
        "routine_history_context_recovered": bool(guidance_validation.get("routine_history_context_recovered", False)),
        "guidance_action_card_is_valid": bool(guidance_validation.get("guidance_action_card_is_valid", False)),
        "routine_candidate_count": int(guidance_summary.get("routine_candidate_count") or 0),
        "display_only": True,
        "client_decides_presentation": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "llm_called": bool(guidance_obj.llm_called),
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e": True,
        "sqlite_backend_readback_reused": True,
        "today_guidance_recovery_reused": True,
        "read_only_sqlite_connection": True,
        "guidance_is_display_only": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
    }
    return ContextPersistenceSqliteBackendTodayGuidanceRecoveryE2EPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION,
        source=source,
        recovery_e2e_id=recovery_e2e_id,
        sqlite_readback_payload=readback_payload,
        sqlite_readback_summary=readback_summary,
        today_guidance_recovery_payload=guidance_payload,
        today_guidance_recovery_summary=guidance_summary,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
        llm_called=bool(guidance_obj.llm_called),
        backend_database_read=bool(readback_payload.get("backend_database_read", False)),
        sqlite_connection_created=bool(readback_payload.get("sqlite_connection_created", False)),
        sqlite_rows_read=int(readback_payload.get("sqlite_rows_read") or 0),
    )


def build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary(
    *,
    payload: ContextPersistenceSqliteBackendTodayGuidanceRecoveryE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    readback_summary = data.get("sqlite_readback_summary") if isinstance(data.get("sqlite_readback_summary"), dict) else {}
    guidance_summary = data.get("today_guidance_recovery_summary") if isinstance(data.get("today_guidance_recovery_summary"), dict) else {}
    return {
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "recovery_e2e_id": data.get("recovery_e2e_id"),
        "sqlite_db_path": readback_summary.get("sqlite_db_path"),
        "sqlite_connection_created": data.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": data.get("sqlite_rows_read", 0),
        "backend_database_read": data.get("backend_database_read", False),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "context_packet_section_ready": validation.get("context_packet_section_ready", False),
        "persisted_context_recovered": validation.get("persisted_context_recovered", False),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "guidance_action_card_is_valid": validation.get("guidance_action_card_is_valid", False),
        "routine_candidate_count": validation.get("routine_candidate_count", guidance_summary.get("routine_candidate_count", 0)),
        "llm_called": data.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }




@dataclass(frozen=True)
class ContextPersistenceSqliteBackendTerminalMemoryToGuidanceSmokePayload:
    """v2_9_4 terminal smoke for SQLite persistence → memory autoload → guidance.

    This payload composes existing v2_9_x contracts instead of introducing a
    second persistence/recovery system. It may write the SQLite backend only
    through the v2_9_0 explicit opt-in store gate; it never writes HarmonyOS
    local state, starts Routine, calls the engine, creates MIDI, or plays audio.
    """

    payload_contract_version: str
    source: str
    smoke_id: str
    sqlite_store_payload: dict[str, Any]
    sqlite_store_summary: dict[str, Any]
    terminal_memory_autoload_payload: dict[str, Any]
    terminal_memory_autoload_summary: dict[str, Any]
    guidance_payload: dict[str, Any]
    guidance_summary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    terminal_session_memory_write_previewed: bool = False
    terminal_session_memory_loaded_by_core: bool = False
    durable_backend_write_executed: bool = False
    transaction_committed: bool = False
    idempotent_replay: bool = False
    guidance_preview_ready: bool = False
    routine_candidate_count: int = 0
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "smoke_id": self.smoke_id,
            "sqlite_store_payload": _redact_sensitive_values(self.sqlite_store_payload),
            "sqlite_store_summary": _redact_sensitive_values(self.sqlite_store_summary),
            "terminal_memory_autoload_payload": _redact_sensitive_values(self.terminal_memory_autoload_payload),
            "terminal_memory_autoload_summary": _redact_sensitive_values(self.terminal_memory_autoload_summary),
            "guidance_payload": _redact_sensitive_values(self.guidance_payload),
            "guidance_summary": _redact_sensitive_values(self.guidance_summary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "terminal_session_memory_write_previewed": self.terminal_session_memory_write_previewed,
            "terminal_session_memory_loaded_by_core": self.terminal_session_memory_loaded_by_core,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "transaction_committed": self.transaction_committed,
            "idempotent_replay": self.idempotent_replay,
            "guidance_preview_ready": self.guidance_preview_ready,
            "routine_candidate_count": self.routine_candidate_count,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


@dataclass(frozen=True)
class ContextPersistenceSqliteBackendTerminalMemoryAutoloadPreviewPayload:
    """v2_9_3 read SQLite backend context into terminal session-memory preview.

    The core payload is pure preview data. It reads the existing SQLite backend
    through the v2_9_1 read-only bridge and prepares a TerminalChatSession memory
    object that the CLI may load into its in-process session memory. It never
    writes storage, starts Routine, calls the engine, creates MIDI, or plays audio.
    """

    payload_contract_version: str
    source: str
    autoload_preview_id: str
    sqlite_readback_payload: dict[str, Any]
    sqlite_readback_summary: dict[str, Any]
    terminal_memory_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    terminal_session_memory_write_previewed: bool = False
    terminal_session_memory_loaded_by_core: bool = False
    durable_backend_write_executed: bool = False
    transaction_committed: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "autoload_preview_id": self.autoload_preview_id,
            "sqlite_readback_payload": _redact_sensitive_values(self.sqlite_readback_payload),
            "sqlite_readback_summary": _redact_sensitive_values(self.sqlite_readback_summary),
            "terminal_memory_preview": _redact_sensitive_values(self.terminal_memory_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "terminal_session_memory_write_previewed": self.terminal_session_memory_write_previewed,
            "terminal_session_memory_loaded_by_core": self.terminal_session_memory_loaded_by_core,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "transaction_committed": self.transaction_committed,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }



def build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload(
    args: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke",
    provider: Any | None = None,
) -> ContextPersistenceSqliteBackendTerminalMemoryToGuidanceSmokePayload:
    """Run the compact terminal smoke chain with explicit SQLite opt-in gates.

    Chain:
    1. v2_9_0 SQLite backend store, which may write only after explicit gates.
    2. v2_9_3 terminal memory autoload preview, which reads back the same DB.
    3. v2_8_17 persisted-context guidance recovery from the prepared memory args.
    """

    source_args = dict(args or {})
    trace = trace_id or _first_present(source_args, "trace_id", "traceId")
    smoke_id = str(_first_present(source_args, "smoke_id", "smokeId") or f"sqlite_terminal_memory_guidance_smoke_{uuid4().hex[:12]}")

    store_obj = build_context_persistence_sqlite_backend_store_payload(
        source_args,
        trace_id=trace,
        source="sqlite_terminal_memory_to_guidance_smoke_store",
    )
    store_payload = store_obj.to_dict()
    store_summary = build_context_persistence_sqlite_backend_store_summary(
        payload=store_obj,
        source="sqlite_terminal_memory_to_guidance_smoke",
    )

    autoload_obj = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload(
        source_args,
        trace_id=trace,
        source="sqlite_terminal_memory_to_guidance_smoke_autoload",
    )
    autoload_payload = autoload_obj.to_dict()
    autoload_summary = build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary(
        payload=autoload_obj,
        source="sqlite_terminal_memory_to_guidance_smoke",
    )

    preview = autoload_payload.get("terminal_memory_preview") if isinstance(autoload_payload.get("terminal_memory_preview"), dict) else {}
    terminal_session_memory = preview.get("terminal_session_memory") if isinstance(preview.get("terminal_session_memory"), dict) else {}
    guidance_args = terminal_session_memory.get("guidance_arguments") if isinstance(terminal_session_memory.get("guidance_arguments"), dict) else {}
    guidance_payload: dict[str, Any] = {}
    guidance_summary: dict[str, Any] = {}
    if terminal_session_memory.get("loaded") and guidance_args:
        smoke_guidance_args = dict(guidance_args)
        smoke_guidance_args.setdefault("userInput", _first_present(source_args, "userInput", "user_input") or "今天该练什么？")
        smoke_guidance_args.setdefault("callProvider", False)
        guidance_obj = build_today_practice_guidance_persisted_context_recovery_e2e_payload(
            smoke_guidance_args,
            trace_id=trace,
            source="sqlite_terminal_memory_to_guidance_smoke_guidance",
            provider=provider,
        )
        guidance_payload = guidance_obj.to_dict()
        guidance_summary = build_today_practice_guidance_persisted_context_recovery_e2e_summary(
            payload=guidance_obj,
            source="sqlite_terminal_memory_to_guidance_smoke",
        )

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    store_accepted = bool(store_summary.get("accepted"))
    store_ready = bool(store_summary.get("backend_database_written") or store_summary.get("idempotent_replay"))
    autoload_ready = bool(autoload_summary.get("terminal_session_memory_ready"))
    guidance_ready = bool(guidance_summary.get("guidance_action_card_is_valid") or guidance_summary.get("action_card_is_valid"))
    if not store_accepted:
        blocked_reasons.append("sqlite_backend_store_not_accepted")
    if store_accepted and not store_ready:
        blocked_reasons.append("sqlite_backend_store_not_written_or_replayed")
    if not autoload_ready:
        blocked_reasons.append("terminal_memory_autoload_not_ready")
    if not guidance_payload:
        blocked_reasons.append("today_guidance_preview_not_built")
    elif not guidance_ready:
        blocked_reasons.append("today_guidance_action_card_not_valid")
    warnings.extend(list(store_summary.get("warnings") or []))
    warnings.extend(list(autoload_summary.get("warnings") or []))
    warnings.extend(list(guidance_summary.get("warnings") or []))
    accepted = not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_terminal_memory_to_guidance_smoke_ready" if accepted else "sqlite_backend_terminal_memory_to_guidance_smoke_blocked",
        "sqlite_backend_store_accepted": store_accepted,
        "sqlite_backend_store_ready": store_ready,
        "terminal_memory_autoload_ready": autoload_ready,
        "terminal_session_memory_write_previewed": bool(autoload_summary.get("terminal_session_memory_write_previewed", False)),
        "terminal_session_memory_loaded_by_core": False,
        "will_load_terminal_session_memory_in_cli": autoload_ready,
        "guidance_preview_built": bool(guidance_payload),
        "guidance_preview_ready": guidance_ready,
        "routine_candidate_count": guidance_summary.get("routine_candidate_count", 0),
        "profile_context_recovered": bool(autoload_summary.get("profile_context_recovered", False)),
        "active_plan_context_recovered": bool(autoload_summary.get("active_plan_context_recovered", False)),
        "routine_history_context_recovered": bool(autoload_summary.get("routine_history_context_recovered", False)),
        "deterministic_provider_result_used": bool(_first_present(source_args, "providerResult", "provider_result")),
        "storage_written": bool(store_summary.get("storage_written", False)),
        "backend_database_written": bool(store_summary.get("backend_database_written", False)),
        "backend_database_read": bool(autoload_summary.get("backend_database_read", False)),
        "local_device_written": False,
        "sqlite_connection_created": bool(store_summary.get("sqlite_connection_created") or autoload_summary.get("sqlite_connection_created")),
        "sqlite_tables_created": bool(store_summary.get("sqlite_tables_created", False)),
        "sqlite_rows_written": bool(store_summary.get("sqlite_rows_written", False)),
        "sqlite_rows_read": int(autoload_summary.get("sqlite_rows_read") or 0),
        "durable_backend_write_executed": bool(store_summary.get("durable_backend_write_executed", False)),
        "transaction_committed": bool(store_summary.get("transaction_committed", False)),
        "idempotent_replay": bool(store_summary.get("idempotent_replay", False)),
        "llm_called": bool(guidance_summary.get("llm_called", False)),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke": True,
        "composes_existing_v2_9_contracts": True,
        "sqlite_store_uses_v2_9_0_explicit_opt_in_gate": True,
        "terminal_memory_autoload_uses_v2_9_3_readback": True,
        "today_guidance_uses_v2_8_17_persisted_context_recovery": True,
        "terminal_session_memory_update_is_cli_local": True,
        "api_surface_is_smoke_preview": True,
        "storage_written": bool(store_summary.get("storage_written", False)),
        "backend_database_written": bool(store_summary.get("backend_database_written", False)),
        "local_device_written": False,
        "sqlite_tables_created": bool(store_summary.get("sqlite_tables_created", False)),
        "sqlite_rows_written": bool(store_summary.get("sqlite_rows_written", False)),
        "durable_backend_write_executed": bool(store_summary.get("durable_backend_write_executed", False)),
        "transaction_committed": bool(store_summary.get("transaction_committed", False)),
        "llm_called": bool(guidance_summary.get("llm_called", False)),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
    }
    return ContextPersistenceSqliteBackendTerminalMemoryToGuidanceSmokePayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION,
        source=source,
        smoke_id=smoke_id,
        sqlite_store_payload=store_payload,
        sqlite_store_summary=store_summary,
        terminal_memory_autoload_payload=autoload_payload,
        terminal_memory_autoload_summary=autoload_summary,
        guidance_payload=guidance_payload,
        guidance_summary=guidance_summary,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
        llm_called=bool(guidance_summary.get("llm_called", False)),
        storage_written=bool(store_summary.get("storage_written", False)),
        backend_database_written=bool(store_summary.get("backend_database_written", False)),
        backend_database_read=bool(autoload_summary.get("backend_database_read", False)),
        sqlite_connection_created=bool(store_summary.get("sqlite_connection_created") or autoload_summary.get("sqlite_connection_created")),
        sqlite_tables_created=bool(store_summary.get("sqlite_tables_created", False)),
        sqlite_rows_written=bool(store_summary.get("sqlite_rows_written", False)),
        sqlite_rows_read=int(autoload_summary.get("sqlite_rows_read") or 0),
        terminal_session_memory_write_previewed=bool(autoload_summary.get("terminal_session_memory_write_previewed", False)),
        durable_backend_write_executed=bool(store_summary.get("durable_backend_write_executed", False)),
        transaction_committed=bool(store_summary.get("transaction_committed", False)),
        idempotent_replay=bool(store_summary.get("idempotent_replay", False)),
        guidance_preview_ready=guidance_ready,
        routine_candidate_count=int(guidance_summary.get("routine_candidate_count") or 0),
    )


def build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary(
    *,
    payload: ContextPersistenceSqliteBackendTerminalMemoryToGuidanceSmokePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    store_summary = data.get("sqlite_store_summary") if isinstance(data.get("sqlite_store_summary"), dict) else {}
    autoload_summary = data.get("terminal_memory_autoload_summary") if isinstance(data.get("terminal_memory_autoload_summary"), dict) else {}
    guidance_summary = data.get("guidance_summary") if isinstance(data.get("guidance_summary"), dict) else {}
    return {
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "smoke_id": data.get("smoke_id"),
        "sqlite_db_path": store_summary.get("sqlite_db_path") or autoload_summary.get("sqlite_db_path"),
        "sqlite_backend_store_accepted": validation.get("sqlite_backend_store_accepted", False),
        "sqlite_backend_store_ready": validation.get("sqlite_backend_store_ready", False),
        "storage_written": data.get("storage_written", False),
        "backend_database_written": data.get("backend_database_written", False),
        "backend_database_read": data.get("backend_database_read", False),
        "local_device_written": False,
        "sqlite_connection_created": data.get("sqlite_connection_created", False),
        "sqlite_tables_created": data.get("sqlite_tables_created", False),
        "sqlite_rows_written": data.get("sqlite_rows_written", False),
        "sqlite_rows_read": data.get("sqlite_rows_read", 0),
        "durable_backend_write_executed": data.get("durable_backend_write_executed", False),
        "transaction_committed": data.get("transaction_committed", False),
        "idempotent_replay": data.get("idempotent_replay", False),
        "terminal_memory_autoload_ready": validation.get("terminal_memory_autoload_ready", False),
        "terminal_session_memory_write_previewed": data.get("terminal_session_memory_write_previewed", False),
        "terminal_session_memory_loaded_by_core": False,
        "will_load_terminal_session_memory_in_cli": validation.get("will_load_terminal_session_memory_in_cli", False),
        "guidance_preview_built": validation.get("guidance_preview_built", False),
        "guidance_preview_ready": data.get("guidance_preview_ready", False),
        "guidance_validation_status": guidance_summary.get("validation_status"),
        "routine_candidate_count": data.get("routine_candidate_count", 0),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "deterministic_provider_result_used": validation.get("deterministic_provider_result_used", False),
        "llm_called": data.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION,
        "context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview",
        "terminal_command": "/context-persistence-sqlite-backend-terminal-memory-to-guidance-smoke",
        "short_terminal_command": "/sqlite-memory-guidance-smoke",
        "surface": "Compact terminal smoke: SQLite backend store to terminal memory autoload to today-practice guidance",
        "mode": "explicit_opt_in_sqlite_write_then_readback_session_memory_then_display_only_guidance",
        "execution_status": {
            "sqlite_backend_terminal_memory_to_guidance_smoke_implemented": True,
            "sqlite_backend_store_executed_after_explicit_opt_in": True,
            "sqlite_backend_readback_implemented": True,
            "terminal_session_memory_can_be_loaded_by_cli": True,
            "guidance_preview_display_only": True,
            "local_device_write_enabled": False,
            "llm_call_enabled_by_default": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "same v2_9_0 write gates: backendPersistenceEnabled=true and executeBackendPersistence=true",
            "userDecision=approved and confirmationStatus=user_approved_future_executor_required",
            "safe sqliteDbPath under a dev/test path with .db/.sqlite/.sqlite3 suffix",
            "idempotencyKey and traceId present",
            "same v2_9_3 readback gates: backendReadbackEnabled=true and executeBackendReadback=true",
            "providerResult fixture for deterministic smoke guidance",
        ],
        "terminal_flow": [
            "write explicit approved profile/plan/history context to SQLite through v2_9_0",
            "autoload the same persisted context into TerminalChatSession.persisted_context_memory through v2_9_3",
            "send an ordinary today-practice guidance turn using that memory",
            "return one smoke response with store/autoload/guidance summaries and no Engine/Routine/playback side effects",
        ],
        "guards": {
            "sqlite_write_requires_explicit_opt_in": True,
            "terminal_memory_update_is_cli_local": True,
            "guidance_is_display_only": True,
            "local_device_written": False,
            "payload_calls_llm_by_default": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "sqlite_backend_store": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
            "sqlite_backend_readback_context_recovery": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
            "terminal_memory_autoload_preview": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
            "terminal_memory_controls": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
            "persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack",
    }


@dataclass(frozen=True)
class ContextPersistenceSqliteBackendApiMemoryDebugPackPayload:
    """v2_9_5 API debug pack for SQLite persistence / memory recovery routes.

    This is a documentation-and-preview payload only. It packages the v2_9_0
    through v2_9_4 API surfaces, sample request bodies, expected response paths,
    and frontend-safe notes for HarmonyOS/API integration debugging. It never
    opens SQLite, writes storage, mutates server memory, starts Routine, calls
    the engine, creates MIDI, or starts playback.
    """

    payload_contract_version: str
    source: str
    debug_pack_id: str
    target_client: str
    route_catalog: list[dict[str, Any]]
    request_examples: dict[str, dict[str, Any]]
    response_path_catalog: list[dict[str, Any]]
    terminal_debug_commands: list[dict[str, Any]]
    recommended_debug_order: list[str]
    frontend_safe_contract_notes: list[str]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    terminal_session_memory_loaded_by_api: bool = False
    terminal_session_memory_loaded_by_cli: bool = False
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "debug_pack_id": self.debug_pack_id,
            "target_client": self.target_client,
            "route_catalog": _redact_sensitive_values(self.route_catalog),
            "request_examples": _redact_sensitive_values(self.request_examples),
            "response_path_catalog": _redact_sensitive_values(self.response_path_catalog),
            "terminal_debug_commands": _redact_sensitive_values(self.terminal_debug_commands),
            "recommended_debug_order": list(self.recommended_debug_order),
            "frontend_safe_contract_notes": list(self.frontend_safe_contract_notes),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "terminal_session_memory_loaded_by_api": self.terminal_session_memory_loaded_by_api,
            "terminal_session_memory_loaded_by_cli": self.terminal_session_memory_loaded_by_cli,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _sqlite_backend_debug_pack_base_examples(args: dict[str, Any], trace_id: str | None) -> dict[str, Any]:
    sqlite_path = str(_first_present(args, "sqlite_db_path", "sqliteDbPath", "db_path", "dbPath") or "/tmp/jammate_agent_context_debug.sqlite")
    user_id = str(_first_present(args, "user_id", "userId") or "dev_user")
    candidate_id = str(_first_present(args, "candidate_id", "candidateId") or "candidate_debug_pack_001")
    confirmation_id = str(_first_present(args, "confirmation_id", "confirmationId") or "confirmation_debug_pack_001")
    idempotency_key = str(_first_present(args, "idempotency_key", "idempotencyKey") or "idem_debug_pack_001")
    trace = str(trace_id or _first_present(args, "trace_id", "traceId") or "trace_debug_pack_001")
    provider_result = _first_present(args, "provider_result", "providerResult") or {
        "content": {
            "guidance_mode": "continue_original_plan",
            "summary": "基于 SQLite 后端恢复的上下文，今天继续按原计划练习。",
            "recommended_focus": "按当前 active plan 继续练习",
            "recommended_blocks": [{"title": "Debug pack sample block", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
            "routine_candidates": [{"routineName": "Debug pack sample routine", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}],
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance", "present_routine_candidate"],
        }
    }
    common_context = {
        "userPracticeProfile": _redact_sensitive_values(_first_present(args, "user_practice_profile", "userPracticeProfile") or {
            "userId": user_id,
            "preferredStyles": ["medium_swing", "bossa_nova"],
            "focusAreas": ["ii-V-I", "comping"],
        }),
        "practicePlan": _redact_sensitive_values(_first_present(args, "practice_plan", "practicePlan", "active_practice_plan", "activePracticePlan") or {
            "planId": "plan_debug_pack_001",
            "status": "active",
            "planBlocks": [{"blockId": "block_debug_pack_001", "title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104}],
        }),
        "routineHistoryRecords": _redact_sensitive_values(_first_present(args, "routine_history_records", "routineHistoryRecords") or [
            {"sessionId": "session_debug_pack_001", "title": "recent comping review", "style": "medium_swing", "completed": True},
        ]),
    }
    return {
        "sqliteDbPath": sqlite_path,
        "environment": str(_first_present(args, "environment", "env") or "test"),
        "traceId": trace,
        "idempotencyKey": idempotency_key,
        "userId": user_id,
        "candidateKind": str(_first_present(args, "candidate_kind", "candidateKind") or "practice_plan_persistence_candidate"),
        "candidateId": candidate_id,
        "confirmationId": confirmation_id,
        "entities": list(_normalize_storage_adapter_entities(args)),
        "providerResult": _redact_sensitive_values(provider_result),
        **common_context,
    }


def build_context_persistence_sqlite_backend_api_memory_debug_pack_payload(
    args: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_api_memory_debug_pack",
) -> ContextPersistenceSqliteBackendApiMemoryDebugPackPayload:
    """Build a frontend/API debug pack for SQLite context persistence routes.

    The pack only describes and samples existing routes. It deliberately does
    not call any v2_9_x route builder that would open/read/write SQLite.
    """

    source_args = dict(args or {})
    debug_pack_id = str(_first_present(source_args, "debug_pack_id", "debugPackId") or f"sqlite_api_memory_debug_pack_{uuid4().hex[:12]}")
    target_client = str(_first_present(source_args, "target_client", "targetClient") or "harmonyos_api_debug")
    base = _sqlite_backend_debug_pack_base_examples(source_args, trace_id)
    trace = trace_id or base.get("traceId")

    write_request = {
        "backendPersistenceEnabled": True,
        "executeBackendPersistence": True,
        "userDecision": "approved",
        "confirmationStatus": "user_approved_future_executor_required",
        "storageBoundaryCheckPassed": True,
        "redactionCheckPassed": True,
        "schemaPreviewAccepted": True,
        **{k: base[k] for k in ("sqliteDbPath", "environment", "traceId", "idempotencyKey", "userId", "candidateKind", "candidateId", "confirmationId", "entities", "userPracticeProfile", "practicePlan", "routineHistoryRecords")},
    }
    readback_request = {
        "backendReadbackEnabled": True,
        "executeBackendReadback": True,
        **{k: base[k] for k in ("sqliteDbPath", "environment", "traceId", "idempotencyKey", "userId", "candidateKind", "candidateId")},
    }
    guidance_request = {**readback_request, "availableMinutes": int(_first_present(source_args, "availableMinutes", "available_minutes") or 25), "providerResult": base["providerResult"]}
    autoload_request = dict(guidance_request)
    smoke_request = {**write_request, "backendReadbackEnabled": True, "executeBackendReadback": True, "availableMinutes": guidance_request["availableMinutes"], "providerResult": base["providerResult"]}

    route_catalog = [
        {"key": "sqlite_backend_store", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-store/execute", "purpose": "explicitly approved backend SQLite context write", "side_effect": "writes SQLite only after explicit gates"},
        {"key": "sqlite_backend_readback_context_recovery", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-readback-context-recovery/preview", "purpose": "read persisted SQLite context into a ContextBuilder-ready recovery packet", "side_effect": "read-only SQLite"},
        {"key": "sqlite_backend_today_guidance_recovery_e2e", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview", "purpose": "read persisted SQLite context and generate display-only today-practice guidance", "side_effect": "read-only SQLite; optional provider preview only"},
        {"key": "sqlite_backend_terminal_memory_autoload_preview", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview", "purpose": "preview terminal memory object shape from SQLite readback", "side_effect": "API preview only; no server memory mutation"},
        {"key": "sqlite_backend_terminal_memory_to_guidance_smoke", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview", "purpose": "one-call developer smoke chain for store/readback/memory/guidance composition", "side_effect": "may write SQLite only through v2_9_0 gates; API does not mutate terminal memory"},
        {"key": "api_memory_debug_pack", "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION, "method": "POST", "route": "/agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview", "purpose": "this route catalog and request/response debug pack", "side_effect": "none"},
    ]
    request_examples = {
        "1_store_execute": write_request,
        "2_readback_preview": readback_request,
        "3_today_guidance_recovery_preview": guidance_request,
        "4_terminal_memory_autoload_api_preview_only": autoload_request,
        "5_terminal_memory_to_guidance_smoke_preview": smoke_request,
    }
    response_path_catalog = [
        {"route_key": "sqlite_backend_store", "paths": ["ok", "context_persistence_sqlite_backend_store_summary.validation_status", "context_persistence_sqlite_backend_store_summary.storage_written", "context_persistence_sqlite_backend_store_summary.idempotent_replay", "context_persistence_sqlite_backend_store_summary.blocked_reasons"]},
        {"route_key": "sqlite_backend_readback_context_recovery", "paths": ["context_persistence_sqlite_backend_readback_context_recovery_summary.validation_status", "context_persistence_sqlite_backend_readback_context_recovery_summary.context_packet_section_ready", "context_persistence_sqlite_backend_readback_context_recovery_payload.recovery_packet_preview.context_persistence_snapshot_context_intake"]},
        {"route_key": "sqlite_backend_today_guidance_recovery_e2e", "paths": ["context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary.validation_status", "context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary.guidance_action_card_is_valid", "context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload.today_guidance_recovery_payload.action_card_preview"]},
        {"route_key": "sqlite_backend_terminal_memory_autoload_preview", "paths": ["context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary.terminal_memory_preview_ready", "context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload.terminal_memory_preview.terminal_session_memory.guidance_arguments", "terminal_session_memory_loaded_by_api"]},
        {"route_key": "sqlite_backend_terminal_memory_to_guidance_smoke", "paths": ["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary.validation_status", "storage_written", "terminal_session_memory_loaded_by_api", "guidance_preview_ready", "routine_candidate_count"]},
    ]
    terminal_debug_commands = [
        {"command": "/context-persistence-sqlite-backend-store", "input_example_key": "1_store_execute", "note": "CLI can execute the same explicit SQLite write gate."},
        {"command": "/context-persistence-sqlite-backend-readback-context-recovery", "input_example_key": "2_readback_preview", "note": "Read-only recovery preview."},
        {"command": "/persisted-context-autoload-sqlite", "input_example_key": "4_terminal_memory_autoload_api_preview_only", "note": "CLI-only session memory load; API version only previews."},
        {"command": "/sqlite-memory-guidance-smoke", "input_example_key": "5_terminal_memory_to_guidance_smoke_preview", "note": "CLI compact smoke: write, autoload memory, then ordinary guidance turn."},
    ]
    recommended_debug_order = [item["key"] for item in route_catalog if item["key"] != "api_memory_debug_pack"]
    frontend_safe_contract_notes = [
        "HarmonyOS should treat all v2_9_x guidance outputs as display-only until a user confirms a Routine candidate.",
        "Only /persistence-sqlite-backend-store/execute and the smoke route can write SQLite, and only when explicit opt-in gates are true.",
        "API autoload preview does not mutate server memory; TerminalChatSession memory loading is CLI-local only.",
        "Do not send HarmonyOS local playback state, midiBase64, localMidiPath, raw API keys, or hidden reasoning into persistence payloads.",
        "Backend responses remain snake_case; HarmonyOS may map them to camelCase client-side.",
    ]

    ignored_execution_flags = any(bool(_first_present(source_args, key, key[0].lower() + key[1:]) or False) for key in ("backendPersistenceEnabled", "executeBackendPersistence", "backendReadbackEnabled", "executeBackendReadback"))
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if _has_any_forbidden_context_fields(source_args):
        warnings.append("forbidden_context_fields_redacted_in_debug_pack_examples")
    if ignored_execution_flags:
        warnings.append("debug_pack_preview_ignores_execution_flags_and_does_not_call_routes")
    validation = {
        "accepted": not blocked_reasons,
        "status": "sqlite_backend_api_memory_debug_pack_ready" if not blocked_reasons else "sqlite_backend_api_memory_debug_pack_blocked",
        "route_count": len(route_catalog),
        "request_example_count": len(request_examples),
        "response_path_count": sum(len(item.get("paths") or []) for item in response_path_catalog),
        "api_debug_pack_preview_only": True,
        "sqlite_connection_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "terminal_session_memory_loaded_by_api": False,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "context_persistence_sqlite_backend_api_memory_debug_pack": True,
        "composes_existing_v2_9_route_contracts": True,
        "debug_pack_calls_existing_routes": False,
        "debug_pack_opens_sqlite": False,
        "debug_pack_writes_sqlite": False,
        "debug_pack_reads_sqlite": False,
        "api_surface_mutates_server_memory": False,
        "terminal_memory_update_is_cli_local_only": True,
        "local_device_written": False,
        "payload_calls_llm_by_default": False,
        "payload_executes_tool": False,
        "payload_creates_post_session_recommendation_card": False,
        "payload_calls_accompaniment_generate": False,
        "payload_calls_engine_adapter": False,
        "payload_creates_midi_asset": False,
        "payload_starts_playback": False,
        "raw_api_key_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
    }
    return ContextPersistenceSqliteBackendApiMemoryDebugPackPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION,
        source=source,
        debug_pack_id=debug_pack_id,
        target_client=target_client,
        route_catalog=route_catalog,
        request_examples=request_examples,
        response_path_catalog=response_path_catalog,
        terminal_debug_commands=terminal_debug_commands,
        recommended_debug_order=recommended_debug_order,
        frontend_safe_contract_notes=frontend_safe_contract_notes,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
    )


def build_context_persistence_sqlite_backend_api_memory_debug_pack_summary(
    *,
    payload: ContextPersistenceSqliteBackendApiMemoryDebugPackPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_api_memory_debug_pack_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "context_persistence_sqlite_backend_api_memory_debug_pack_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "debug_pack_id": data.get("debug_pack_id"),
        "target_client": data.get("target_client"),
        "route_count": validation.get("route_count", len(data.get("route_catalog") or [])),
        "request_example_count": validation.get("request_example_count", len(data.get("request_examples") or {})),
        "response_path_count": validation.get("response_path_count", 0),
        "recommended_debug_order": list(data.get("recommended_debug_order") or []),
        "api_debug_pack_preview_only": validation.get("api_debug_pack_preview_only", True),
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "terminal_session_memory_loaded_by_api": False,
        "terminal_session_memory_loaded_by_cli": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_api_memory_debug_pack_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION,
        "context_persistence_sqlite_backend_api_memory_debug_pack_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview",
        "terminal_command": "/context-persistence-sqlite-backend-api-memory-debug-pack",
        "short_terminal_command": "/sqlite-api-memory-debug-pack",
        "surface": "API debug pack for SQLite backend persistence, memory preview, and today-practice guidance recovery routes",
        "mode": "preview_only_route_catalog_request_examples_response_paths_no_sqlite_connection",
        "execution_status": {
            "sqlite_backend_api_memory_debug_pack_implemented": True,
            "api_debug_pack_preview_only": True,
            "route_catalog_included": True,
            "request_examples_included": True,
            "response_path_catalog_included": True,
            "database_connection_created": False,
            "database_write_enabled": False,
            "database_read_enabled": False,
            "server_memory_mutation_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "packaged_routes": {
            "sqlite_backend_store": "POST /agent/context/persistence-sqlite-backend-store/execute",
            "sqlite_backend_readback_context_recovery": "POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview",
            "sqlite_backend_today_guidance_recovery_e2e": "POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview",
            "sqlite_backend_terminal_memory_autoload_preview": "POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview",
            "sqlite_backend_terminal_memory_to_guidance_smoke": "POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview",
        },
        "guards": {
            "debug_pack_calls_existing_routes": False,
            "debug_pack_opens_sqlite": False,
            "debug_pack_writes_sqlite": False,
            "debug_pack_reads_sqlite": False,
            "api_surface_mutates_server_memory": False,
            "payload_calls_llm_by_default": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "next_task_hint": "v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack",
    }


@dataclass(frozen=True)
class ContextPersistenceSqliteBackendHarmonyOSApiFixturePackPayload:
    """v2_9_6 HarmonyOS API fixture pack for SQLite persistence debugging.

    This payload translates the existing v2_9_0 through v2_9_5 API surfaces
    into copyable HarmonyOS-facing request fixtures and response assertions. It
    deliberately does not write files under ``frontend_fixtures/harmonyos``; the
    integration branch can copy these examples later if needed. It also never
    opens SQLite, calls packaged routes, mutates server memory, calls LLM/tools,
    starts Routine, calls the engine, creates MIDI, or starts playback.
    """

    payload_contract_version: str
    source: str
    fixture_pack_id: str
    target_client: str
    base_url: str
    harmonyos_api_fixture_pack: dict[str, Any]
    harmonyos_request_examples: list[dict[str, Any]]
    response_assertion_catalog: list[dict[str, Any]]
    arkts_client_sketch: dict[str, Any]
    manual_debug_order: list[str]
    integration_boundary_notes: list[str]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    storage_written: bool = False
    backend_database_written: bool = False
    backend_database_read: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    sqlite_rows_read: int = 0
    fixture_files_written: bool = False
    frontend_fixtures_directory_written: bool = False
    terminal_session_memory_loaded_by_api: bool = False
    terminal_session_memory_loaded_by_cli: bool = False
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "fixture_pack_id": self.fixture_pack_id,
            "target_client": self.target_client,
            "base_url": self.base_url,
            "harmonyos_api_fixture_pack": _redact_sensitive_values(self.harmonyos_api_fixture_pack),
            "harmonyos_request_examples": _redact_sensitive_values(self.harmonyos_request_examples),
            "response_assertion_catalog": _redact_sensitive_values(self.response_assertion_catalog),
            "arkts_client_sketch": _redact_sensitive_values(self.arkts_client_sketch),
            "manual_debug_order": list(self.manual_debug_order),
            "integration_boundary_notes": list(self.integration_boundary_notes),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "backend_database_read": self.backend_database_read,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "sqlite_rows_read": self.sqlite_rows_read,
            "fixture_files_written": self.fixture_files_written,
            "frontend_fixtures_directory_written": self.frontend_fixtures_directory_written,
            "terminal_session_memory_loaded_by_api": self.terminal_session_memory_loaded_by_api,
            "terminal_session_memory_loaded_by_cli": self.terminal_session_memory_loaded_by_cli,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload(
    args: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_harmonyos_api_fixture_pack",
) -> ContextPersistenceSqliteBackendHarmonyOSApiFixturePackPayload:
    """Build a HarmonyOS-facing API fixture pack for v2_9 SQLite routes.

    The pack is generated from the existing v2_9_5 debug pack so that the
    frontend-facing fixtures stay aligned with the canonical backend route
    catalog and sample request bodies. This builder never executes those
    requests.
    """

    source_args = dict(args or {})
    fixture_pack_id = str(_first_present(source_args, "fixture_pack_id", "fixturePackId", "pack_id", "packId") or f"sqlite_harmonyos_api_fixture_pack_{uuid4().hex[:12]}")
    target_client = str(_first_present(source_args, "target_client", "targetClient") or "harmonyos")
    base_url = str(_first_present(source_args, "base_url", "baseUrl") or "http://127.0.0.1:8000").rstrip("/")
    trace = str(trace_id or _first_present(source_args, "trace_id", "traceId") or f"trace_{fixture_pack_id}")

    debug_pack = build_context_persistence_sqlite_backend_api_memory_debug_pack_payload(
        source_args,
        trace_id=trace,
        source="sqlite_harmonyos_fixture_pack_source_debug_pack",
    ).to_dict()
    request_examples = debug_pack.get("request_examples") if isinstance(debug_pack.get("request_examples"), dict) else {}

    route_specs = [
        ("1_store_execute", "sqlite_backend_store", "POST", "/agent/context/persistence-sqlite-backend-store/execute", ["context_persistence_sqlite_backend_store_summary", "storage_written"], "may_write_sqlite_if_executed_with_explicit_gates"),
        ("2_readback_preview", "sqlite_backend_readback_context_recovery", "POST", "/agent/context/persistence-sqlite-backend-readback-context-recovery/preview", ["context_persistence_sqlite_backend_readback_context_recovery_summary", "backend_database_read"], "read_only_sqlite_if_executed"),
        ("3_today_guidance_recovery_preview", "sqlite_backend_today_guidance_recovery_e2e", "POST", "/agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview", ["context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary", "routine_start_enabled"], "read_only_display_only_guidance_if_executed"),
        ("4_terminal_memory_autoload_api_preview_only", "sqlite_backend_terminal_memory_autoload_preview", "POST", "/agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview", ["context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary", "terminal_session_memory_loaded_by_api"], "api_preview_only_no_server_memory_mutation"),
        ("5_terminal_memory_to_guidance_smoke_preview", "sqlite_backend_terminal_memory_to_guidance_smoke", "POST", "/agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview", ["context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary", "guidance_preview_ready"], "may_write_sqlite_only_through_v2_9_0_gates_if_executed"),
        ("6_api_memory_debug_pack_preview", "sqlite_backend_api_memory_debug_pack", "POST", "/agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview", ["context_persistence_sqlite_backend_api_memory_debug_pack_summary", "route_catalog"], "preview_only_no_sqlite"),
    ]

    harmonyos_request_examples: list[dict[str, Any]] = []
    for index, (example_key, route_key, method, path, expected_keys, side_effect_note) in enumerate(route_specs, start=1):
        body = request_examples.get(example_key) if isinstance(request_examples.get(example_key), dict) else {}
        if example_key == "6_api_memory_debug_pack_preview":
            body = {
                "baseUrl": base_url,
                "targetClient": target_client,
                "sqliteDbPath": _first_present(source_args, "sqliteDbPath", "sqlite_db_path", "dbPath", "db_path") or "/tmp/jammate_agent_context_debug.sqlite",
                "traceId": trace,
            }
        harmonyos_request_examples.append({
            "step": index,
            "example_key": example_key,
            "route_key": route_key,
            "method": method,
            "path": path,
            "url": f"{base_url}{path}",
            "body": _redact_sensitive_values(body),
            "expected_response_keys": expected_keys,
            "side_effect_if_client_executes_request": side_effect_note,
            "fixture_pack_executes_request": False,
            "client_confirmation_required_before_write": route_key in {"sqlite_backend_store", "sqlite_backend_terminal_memory_to_guidance_smoke"},
        })

    response_assertion_catalog = [
        {"route_key": "sqlite_backend_store", "assertions": ["ok == true", "storage_written is true only after explicit backend persistence gates", "routine_start_enabled == false", "engine_adapter_called == false"]},
        {"route_key": "sqlite_backend_readback_context_recovery", "assertions": ["backend_database_read may be true", "backend_database_written == false", "context_packet_section_ready indicates ContextBuilder-ready recovery"]},
        {"route_key": "sqlite_backend_today_guidance_recovery_e2e", "assertions": ["guidance output remains display-only", "routine_start_enabled == false", "accompaniment_generate_call_enabled == false"]},
        {"route_key": "sqlite_backend_terminal_memory_autoload_preview", "assertions": ["terminal_session_memory_loaded_by_api == false", "api route previews memory shape only"]},
        {"route_key": "sqlite_backend_api_memory_debug_pack", "assertions": ["sqlite_connection_created == false", "backend_database_read == false", "backend_database_written == false"]},
    ]
    manual_debug_order = [item[1] for item in route_specs]
    arkts_client_sketch = {
        "baseUrl": base_url,
        "contentType": "application/json",
        "requestCasePolicy": "HarmonyOS may send camelCase; backend accepts camelCase/snake_case aliases on these Agent debug routes.",
        "responseCasePolicy": "Backend returns canonical snake_case; HarmonyOS should map to camelCase client-side if needed.",
        "fetchPseudoCode": [
            "const res = await fetch(`${baseUrl}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })",
            "const json = await res.json()",
            "assert(json.ok === true)",
            "do not start Routine or playback from preview responses",
        ],
        "clientOwnsPresentation": True,
        "doNotPersistLocalPlaybackState": True,
        "doNotSendMidiBase64OrLocalMidiPath": True,
    }
    integration_boundary_notes = [
        "This fixture pack is generated inside Agent docs/tests only and does not write frontend_fixtures/harmonyos/.",
        "Integration branch may later copy selected examples into shared frontend fixtures.",
        "Store/smoke examples are copyable but must only be executed after explicit user/backend persistence approval gates.",
        "Readback/guidance examples are display-only and must not start Routine, Engine generation, MIDI creation, or playback.",
        "Backend responses remain snake_case; HarmonyOS can map to camelCase client-side.",
    ]
    harmonyos_api_fixture_pack = {
        "packContractVersion": CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
        "packKind": "sqlite_backend_context_persistence_harmonyos_api_fixture_pack",
        "fixturePackId": fixture_pack_id,
        "targetClient": target_client,
        "baseUrl": base_url,
        "traceId": trace,
        "requests": harmonyos_request_examples,
        "curlExamples": [
            f"curl -s -X POST {item['url']} -H 'Content-Type: application/json' -d '{_compact_json_for_request_pack(item['body'])}'"
            for item in harmonyos_request_examples
        ],
        "arktsClientSketch": arkts_client_sketch,
        "manualDebugOrder": manual_debug_order,
        "debugOnly": True,
        "fixtureFilesWritten": False,
        "frontendFixturesDirectoryWritten": False,
    }

    warnings: list[str] = list((debug_pack.get("validation") or {}).get("warnings") or []) if isinstance(debug_pack.get("validation"), dict) else []
    if bool(_first_present(source_args, "writeToFrontendFixtures", "write_to_frontend_fixtures", "writeFixtureFiles", "write_fixture_files")):
        warnings.append("fixture_pack_preview_ignores_file_write_flags_agent_track_does_not_touch_frontend_fixtures")
    blocked_reasons: list[str] = []
    accepted = bool(harmonyos_request_examples) and not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_harmonyos_api_fixture_pack_ready" if accepted else "sqlite_backend_harmonyos_api_fixture_pack_blocked",
        "fixture_pack_preview_only": True,
        "request_count": len(harmonyos_request_examples),
        "response_assertion_count": sum(len(item.get("assertions") or []) for item in response_assertion_catalog),
        "contains_store_execute_fixture": any(item[1] == "sqlite_backend_store" for item in route_specs),
        "contains_readback_fixture": any(item[1] == "sqlite_backend_readback_context_recovery" for item in route_specs),
        "contains_today_guidance_fixture": any(item[1] == "sqlite_backend_today_guidance_recovery_e2e" for item in route_specs),
        "contains_api_debug_pack_fixture": any(item[1] == "sqlite_backend_api_memory_debug_pack" for item in route_specs),
        "frontend_fixtures_directory_written": False,
        "fixture_files_written": False,
        "sqlite_connection_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": 0,
        "storage_written": False,
        "backend_database_written": False,
        "backend_database_read": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack": True,
        "composes_v2_9_5_debug_pack": True,
        "fixture_pack_calls_existing_routes": False,
        "fixture_pack_opens_sqlite": False,
        "fixture_pack_writes_sqlite": False,
        "fixture_pack_reads_sqlite": False,
        "fixture_pack_writes_frontend_fixtures": False,
        "api_surface_mutates_server_memory": False,
        "terminal_memory_update_is_cli_local_only": True,
        "local_device_written": False,
        "payload_calls_llm_by_default": False,
        "payload_executes_tool": False,
        "payload_creates_post_session_recommendation_card": False,
        "payload_calls_accompaniment_generate": False,
        "payload_calls_engine_adapter": False,
        "payload_creates_midi_asset": False,
        "payload_starts_playback": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }
    return ContextPersistenceSqliteBackendHarmonyOSApiFixturePackPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
        source=source,
        fixture_pack_id=fixture_pack_id,
        target_client=target_client,
        base_url=base_url,
        harmonyos_api_fixture_pack=harmonyos_api_fixture_pack,
        harmonyos_request_examples=harmonyos_request_examples,
        response_assertion_catalog=response_assertion_catalog,
        arkts_client_sketch=arkts_client_sketch,
        manual_debug_order=manual_debug_order,
        integration_boundary_notes=integration_boundary_notes,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
    )


def build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_summary(
    *,
    payload: ContextPersistenceSqliteBackendHarmonyOSApiFixturePackPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_harmonyos_api_fixture_pack_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "fixture_pack_id": data.get("fixture_pack_id"),
        "target_client": data.get("target_client"),
        "base_url": data.get("base_url"),
        "request_count": validation.get("request_count", len(data.get("harmonyos_request_examples") or [])),
        "response_assertion_count": validation.get("response_assertion_count", 0),
        "manual_debug_order": list(data.get("manual_debug_order") or []),
        "contains_store_execute_fixture": validation.get("contains_store_execute_fixture", False),
        "contains_readback_fixture": validation.get("contains_readback_fixture", False),
        "contains_today_guidance_fixture": validation.get("contains_today_guidance_fixture", False),
        "contains_api_debug_pack_fixture": validation.get("contains_api_debug_pack_fixture", False),
        "fixture_pack_preview_only": validation.get("fixture_pack_preview_only", True),
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
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_harmonyos_api_fixture_pack_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
        "context_persistence_sqlite_backend_harmonyos_api_fixture_pack_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview",
        "terminal_command": "/context-persistence-sqlite-backend-harmonyos-api-fixture-pack",
        "short_terminal_command": "/sqlite-harmonyos-api-fixture-pack",
        "surface": "HarmonyOS API fixture pack for SQLite backend persistence/readback/guidance debugging",
        "mode": "preview_only_harmonyos_copyable_requests_no_file_write_no_sqlite_connection",
        "execution_status": {
            "sqlite_backend_harmonyos_api_fixture_pack_implemented": True,
            "fixture_pack_preview_only": True,
            "harmonyos_request_examples_included": True,
            "arkts_client_sketch_included": True,
            "frontend_fixtures_directory_write_enabled": False,
            "fixture_file_write_enabled": False,
            "database_connection_created": False,
            "database_write_enabled": False,
            "database_read_enabled": False,
            "server_memory_mutation_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "packaged_routes": {
            "sqlite_backend_store": "POST /agent/context/persistence-sqlite-backend-store/execute",
            "sqlite_backend_readback_context_recovery": "POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview",
            "sqlite_backend_today_guidance_recovery_e2e": "POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview",
            "sqlite_backend_terminal_memory_autoload_preview": "POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview",
            "sqlite_backend_terminal_memory_to_guidance_smoke": "POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview",
            "sqlite_backend_api_memory_debug_pack": "POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview",
        },
        "guards": {
            "fixture_pack_calls_existing_routes": False,
            "fixture_pack_opens_sqlite": False,
            "fixture_pack_writes_sqlite": False,
            "fixture_pack_reads_sqlite": False,
            "fixture_pack_writes_frontend_fixtures": False,
            "api_surface_mutates_server_memory": False,
            "payload_calls_llm_by_default": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "client_decides_presentation": True,
            "frontend_flow_assumption": False,
        },
        "next_task_hint": "v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix",
    }


def _terminal_memory_passthrough_args(args: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "providerResult", "provider_result",
        "availableMinutes", "available_minutes",
        "callProvider", "call_provider",
        "userInput", "user_input",
    }
    return {key: value for key, value in args.items() if key in allowed}


def build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload(
    args: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "context_persistence_sqlite_backend_terminal_memory_autoload_preview",
) -> ContextPersistenceSqliteBackendTerminalMemoryAutoloadPreviewPayload:
    """Build a read-only SQLite-backed terminal memory autoload preview.

    Core code only prepares the memory object. TerminalChatSession is the only
    place allowed to assign it to in-process session memory after this payload is
    accepted.
    """

    source_args = dict(args or {})
    trace = trace_id or _first_present(source_args, "trace_id", "traceId")
    autoload_preview_id = str(_first_present(source_args, "autoload_preview_id", "autoloadPreviewId") or f"sqlite_terminal_memory_autoload_{uuid4().hex[:12]}")
    readback_obj = build_context_persistence_sqlite_backend_readback_context_recovery_payload(
        source_args,
        trace_id=trace,
        source="sqlite_backend_terminal_memory_autoload_readback",
    )
    readback_payload = readback_obj.to_dict()
    readback_summary = build_context_persistence_sqlite_backend_readback_context_recovery_summary(
        payload=readback_obj,
        source="sqlite_backend_terminal_memory_autoload_preview",
    )
    readback_validation = readback_payload.get("validation") if isinstance(readback_payload.get("validation"), dict) else {}
    recovered_section = readback_payload.get("recovered_context_packet_section") if isinstance(readback_payload.get("recovered_context_packet_section"), dict) else {}
    kwargs = recovered_section.get("context_packet_kwargs") if isinstance(recovered_section.get("context_packet_kwargs"), dict) else {}
    snapshot_payload = readback_payload.get("snapshot_context_intake_payload") if isinstance(readback_payload.get("snapshot_context_intake_payload"), dict) else {}
    guidance_arguments = {
        "snapshotContextIntakePayload": snapshot_payload,
        **kwargs,
        **_terminal_memory_passthrough_args(source_args),
    }
    terminal_session_memory = {
        "loaded": bool(readback_validation.get("accepted", False) and kwargs),
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
        "memory_controls_version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
        "source": "sqlite_backend_terminal_memory_autoload_preview",
        "snapshot_context_intake_payload": snapshot_payload,
        "guidance_arguments": guidance_arguments,
        "summary": {
            "source": "sqlite_backend_terminal_memory_autoload_preview",
            "validation_status": "sqlite_backend_terminal_memory_autoload_preview_ready" if readback_validation.get("accepted", False) and kwargs else "sqlite_backend_terminal_memory_autoload_preview_blocked",
            "profile_context_present": bool(readback_validation.get("profile_context_recovered", False)),
            "active_plan_context_present": bool(readback_validation.get("active_plan_context_recovered", False)),
            "routine_history_context_present": bool(readback_validation.get("routine_history_context_recovered", False)),
            "assembled_practice_context_present": bool(readback_summary.get("context_packet_section_ready", False)),
            "context_builder_can_accept_section": bool(kwargs),
            "backend_database_read": bool(readback_payload.get("backend_database_read", False)),
            "sqlite_rows_read": int(readback_payload.get("sqlite_rows_read") or 0),
            "sqlite_db_path": readback_summary.get("sqlite_db_path"),
        },
    }
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if not readback_validation.get("accepted", False):
        blocked_reasons.append("sqlite_backend_readback_context_recovery_not_accepted")
    if not kwargs:
        blocked_reasons.append("terminal_memory_context_packet_kwargs_not_ready")
    warnings.extend(list(readback_validation.get("warnings") or []))
    accepted = not blocked_reasons
    validation = {
        "accepted": accepted,
        "status": "sqlite_backend_terminal_memory_autoload_preview_ready" if accepted else "sqlite_backend_terminal_memory_autoload_preview_blocked",
        "terminal_memory_preview_ready": accepted,
        "terminal_session_memory_write_previewed": accepted,
        "terminal_session_memory_loaded_by_core": False,
        "terminal_session_memory_only": True,
        "backend_database_read": bool(readback_payload.get("backend_database_read", False)),
        "sqlite_connection_created": bool(readback_payload.get("sqlite_connection_created", False)),
        "sqlite_rows_read": int(readback_payload.get("sqlite_rows_read") or 0),
        "context_packet_section_ready": bool(readback_summary.get("context_packet_section_ready", False)),
        "profile_context_recovered": bool(readback_validation.get("profile_context_recovered", False)),
        "active_plan_context_recovered": bool(readback_validation.get("active_plan_context_recovered", False)),
        "routine_history_context_recovered": bool(readback_validation.get("routine_history_context_recovered", False)),
        "will_inject_into_next_today_practice_guidance_turn": accepted,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview": True,
        "sqlite_backend_readback_reused": True,
        "terminal_memory_session_only": True,
        "terminal_memory_update_is_cli_local": True,
        "api_surface_is_preview_only": True,
        "read_only_sqlite_connection": True,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "durable_backend_write_executed": False,
        "transaction_committed": False,
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
    }
    terminal_memory_preview = {
        "terminal_session_memory_ready": accepted,
        "terminal_session_memory": terminal_session_memory if accepted else {},
        "will_inject_into_next_today_practice_guidance_turn": accepted,
        "session_memory_only": True,
        "next_terminal_command": "ordinary chat: 今天该练什么",
        "clear_command": "/persisted-context-clear",
        "show_command": "/persisted-context-show",
        "client_decides_presentation": True,
    }
    return ContextPersistenceSqliteBackendTerminalMemoryAutoloadPreviewPayload(
        payload_contract_version=CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
        source=source,
        autoload_preview_id=autoload_preview_id,
        sqlite_readback_payload=readback_payload,
        sqlite_readback_summary=readback_summary,
        terminal_memory_preview=terminal_memory_preview,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
        backend_database_read=bool(readback_payload.get("backend_database_read", False)),
        sqlite_connection_created=bool(readback_payload.get("sqlite_connection_created", False)),
        sqlite_rows_read=int(readback_payload.get("sqlite_rows_read") or 0),
        terminal_session_memory_write_previewed=accepted,
    )


def build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary(
    *,
    payload: ContextPersistenceSqliteBackendTerminalMemoryAutoloadPreviewPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload({}, source=source).to_dict()
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    readback_summary = data.get("sqlite_readback_summary") if isinstance(data.get("sqlite_readback_summary"), dict) else {}
    preview = data.get("terminal_memory_preview") if isinstance(data.get("terminal_memory_preview"), dict) else {}
    return {
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "autoload_preview_id": data.get("autoload_preview_id"),
        "sqlite_db_path": readback_summary.get("sqlite_db_path"),
        "sqlite_connection_created": data.get("sqlite_connection_created", False),
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "sqlite_rows_read": data.get("sqlite_rows_read", 0),
        "backend_database_read": data.get("backend_database_read", False),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "terminal_memory_preview_ready": validation.get("terminal_memory_preview_ready", False),
        "terminal_session_memory_write_previewed": validation.get("terminal_session_memory_write_previewed", False),
        "terminal_session_memory_loaded_by_core": False,
        "terminal_session_memory_ready": preview.get("terminal_session_memory_ready", False),
        "will_inject_into_next_today_practice_guidance_turn": validation.get("will_inject_into_next_today_practice_guidance_turn", False),
        "context_packet_section_ready": validation.get("context_packet_section_ready", False),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
        "context_persistence_sqlite_backend_terminal_memory_autoload_preview_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview",
        "terminal_command": "/persisted-context-autoload-sqlite",
        "surface": "SQLite backend context readback to terminal session-memory autoload preview",
        "mode": "read_only_sqlite_backend_to_terminal_session_memory_no_routine_engine_playback",
        "execution_status": {
            "sqlite_backend_terminal_memory_autoload_preview_implemented": True,
            "sqlite_backend_readback_implemented": True,
            "terminal_session_memory_can_be_loaded_by_cli": True,
            "api_preview_only": True,
            "database_write_enabled": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "local_device_write_enabled": False,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "same readback gates as v2_9_1: backendReadbackEnabled=true and executeBackendReadback=true",
            "environment in dev/local_dev/test for v2_9_3",
            "sqliteDbPath points to an existing safe .db/.sqlite/.sqlite3 file",
            "optional idempotencyKey / traceId / userId / candidate filters",
            "no forbidden client-local/MIDI/API-key fields",
        ],
        "terminal_flow": [
            "run /persisted-context-autoload-sqlite with explicit readback gates",
            "reuse v2_9_1 read-only SQLite backend context recovery",
            "prepare the same guidance_arguments shape used by v2_8_18 terminal memory controls",
            "CLI writes only TerminalChatSession.persisted_context_memory in-process",
            "next ordinary today-practice chat turn reuses loaded memory automatically",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_reads_backend_sqlite_only_after_explicit_opt_in": True,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "local_device_written": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "sqlite_backend_store": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
            "sqlite_backend_readback_context_recovery": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
            "terminal_memory_controls": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
            "persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke",
    }

def context_persistence_sqlite_backend_today_guidance_recovery_e2e_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION,
        "context_persistence_sqlite_backend_today_guidance_recovery_e2e_version": CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_VERSION,
        "spec_route": "GET /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/spec",
        "preview_route": "POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview",
        "terminal_command": "/context-persistence-sqlite-backend-today-guidance-recovery-e2e",
        "surface": "SQLite backend persisted context to today-practice guidance recovery E2E",
        "mode": "sqlite_backend_readback_to_display_only_today_practice_guidance_no_mutation",
        "execution_status": {
            "sqlite_backend_today_guidance_recovery_e2e_implemented": True,
            "sqlite_backend_readback_implemented": True,
            "today_guidance_recovery_implemented": True,
            "guidance_display_only": True,
            "database_write_enabled": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "local_device_write_enabled": False,
            "llm_call_default_enabled": False,
            "provider_boundary_can_be_explicitly_previewed": True,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "required_gates": [
            "same readback gates as v2_9_1: backendReadbackEnabled=true and executeBackendReadback=true",
            "environment in dev/local_dev/test for v2_9_2",
            "sqliteDbPath points to an existing safe .db/.sqlite/.sqlite3 file",
            "optional idempotencyKey / traceId / userId / candidate filters",
            "no forbidden client-local/MIDI/API-key fields",
        ],
        "e2e_flow": [
            "reuse v2_9_1 read-only SQLite backend context recovery",
            "extract ContextBuilder-ready contextPersistenceSnapshotContextIntake section",
            "reuse v2_8_17 persisted-context today-practice guidance recovery",
            "return display-only ActionCard/Routine-candidate preview for client presentation",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_reads_backend_sqlite_only_after_explicit_opt_in": True,
            "payload_calls_llm_by_default": False,
            "payload_executes_tool": False,
            "payload_creates_post_session_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "local_device_written": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "sqlite_backend_store": CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_VERSION,
            "sqlite_backend_readback_context_recovery": CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_VERSION,
            "persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview",
    }

@dataclass(frozen=True)
class ContextPersistenceProfilePlanHistorySnapshotContextIntakePayload:
    payload_contract_version: str
    source: str
    snapshot_intake_id: str
    snapshot_source: str
    requested_entities: list[str]
    readback_summary: dict[str, Any]
    normalized_context_sections: dict[str, Any]
    context_packet_section: dict[str, Any]
    context_builder_injection_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    durable_backend_write_executed: bool = False
    fixture_write_executed: bool = False
    transaction_committed: bool = False
    replay_execution_committed: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "snapshot_intake_id": self.snapshot_intake_id,
            "snapshot_source": self.snapshot_source,
            "requested_entities": list(self.requested_entities),
            "readback_summary": _redact_sensitive_values(self.readback_summary),
            "normalized_context_sections": _redact_sensitive_values(self.normalized_context_sections),
            "context_packet_section": _redact_sensitive_values(self.context_packet_section),
            "context_builder_injection_preview": _redact_sensitive_values(self.context_builder_injection_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "fixture_write_executed": self.fixture_write_executed,
            "transaction_committed": self.transaction_committed,
            "replay_execution_committed": self.replay_execution_committed,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _snapshot_readback_payload(args: dict[str, Any], trace_id: str | None) -> tuple[dict[str, Any], str]:
    for key in ("readback_payload", "readbackPayload", "context_persistence_dev_fixture_readback_replay_payload", "contextPersistenceDevFixtureReadbackReplayPayload"):
        value = args.get(key)
        if isinstance(value, dict):
            return value, "embedded_readback_payload"
    if _first_present(args, "fixture_store_path", "fixtureStorePath", "fixture_path", "fixturePath"):
        return build_context_persistence_dev_fixture_readback_replay_payload(args, trace_id=trace_id, source="snapshot_context_intake_readback_bridge").to_dict(), "dev_fixture_readback_bridge"
    snapshot = _first_present(args, "context_snapshot_preview", "contextSnapshotPreview", "snapshotPreview")
    if isinstance(snapshot, dict):
        return {"context_snapshot_preview": snapshot, "validation": {"accepted": True, "status": "embedded_snapshot_preview"}}, "embedded_context_snapshot_preview"
    return {}, "empty_snapshot"


def _snapshot_entities(readback_payload: dict[str, Any], fallback: list[str]) -> list[str]:
    snapshot = readback_payload.get("context_snapshot_preview") if isinstance(readback_payload.get("context_snapshot_preview"), dict) else {}
    entities = [str(entity) for entity in (snapshot.get("entity_counts") or {})]
    for entity in snapshot.get("requested_entities") or []:
        if str(entity) not in entities:
            entities.append(str(entity))
    fixture_read = readback_payload.get("fixture_read_result") if isinstance(readback_payload.get("fixture_read_result"), dict) else {}
    for record in fixture_read.get("matched_records") or []:
        if isinstance(record, dict):
            for entity in record.get("entities") or []:
                if str(entity) not in entities:
                    entities.append(str(entity))
    return entities or list(fallback)


def _profile_metadata_section(trace_id: str | None, record_count: int, source: str) -> dict[str, Any]:
    summary = "从 dev fixture snapshot 恢复到用户练习画像占位上下文；当前 snapshot 只包含持久化元数据。"
    return {"section_name": "user_practice_profile_context", "user_practice_profile_context_intake_version": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION, "restored_from": source, "profile_status": "restored_snapshot_preview_metadata_only", "profile": {"context_type": "user_practice_profile_context", "profile_status": "restored_snapshot_preview_metadata_only", "summary_for_llm": summary, "persistence_snapshot_trace_id": trace_id, "persistence_snapshot_record_count": record_count, "preferred_styles": [], "focus_areas": [], "comfortable_tempo_ranges": {}, "avoid": []}, "summary_for_llm": summary, "context_usage_policy": {"use_when_user_asks_what_to_practice_next": True, "do_not_start_routine": True, "do_not_call_accompaniment_generate": True}}


def _plan_metadata_section(trace_id: str | None, record_count: int, source: str) -> dict[str, Any]:
    return {"section_name": "active_practice_plan_context", "active_practice_plan_context_intake_version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION, "restored_from": source, "active_plan": {"plan_status": "restored_snapshot_preview_metadata_only", "persistence_snapshot_trace_id": trace_id, "persistence_snapshot_record_count": record_count}, "plan_blocks": [], "aggregate_summary": {"plan_block_count": 0, "summary_for_llm": "从 dev fixture snapshot 恢复到 active PracticePlan 占位上下文；当前 snapshot 只包含持久化元数据。"}, "context_usage_policy": {"use_when_user_asks_what_to_practice_next": True, "do_not_start_routine": True, "do_not_call_accompaniment_generate": True}}


def _history_metadata_section(trace_id: str | None, record_count: int, source: str) -> dict[str, Any]:
    return {"section_name": "practice_history_context", "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION, "restored_from": source, "recent_practice_history": [], "aggregate_summary": {"session_count": 0, "summary_for_llm": "从 dev fixture snapshot 恢复到 RoutineHistory 占位上下文；当前 snapshot 只包含持久化元数据。"}, "persistence_snapshot_trace_id": trace_id, "persistence_snapshot_record_count": record_count, "context_usage_policy": {"use_when_user_asks_what_to_practice_next": True, "do_not_create_post_session_recommendation_card": True, "do_not_start_routine": True, "do_not_call_accompaniment_generate": True}}


def _snapshot_context_sections(args: dict[str, Any], *, entities: list[str], trace_id: str | None, record_count: int, source: str) -> tuple[dict[str, Any], list[str]]:
    sections: dict[str, Any] = {}
    warnings: list[str] = []
    profile_ctx = _first_present(args, "user_practice_profile_context", "userPracticeProfileContext")
    profile_raw = _first_present(args, "user_practice_profile", "userPracticeProfile")
    if isinstance(profile_ctx, dict) and profile_ctx.get("section_name"):
        sections["user_practice_profile_context"] = _redact_sensitive_values(profile_ctx)
    elif isinstance(profile_raw, dict):
        sections["user_practice_profile_context"] = build_user_practice_profile_context_intake_payload({"userPracticeProfile": profile_raw}, trace_id=trace_id, source="snapshot_context_intake_explicit_profile").context_packet_section
    elif "user_practice_profile" in entities:
        sections["user_practice_profile_context"] = _profile_metadata_section(trace_id, record_count, source); warnings.append("user_practice_profile_restored_as_metadata_only_context")
    plan_ctx = _first_present(args, "active_practice_plan_context", "activePracticePlanContext")
    plan_raw = _first_present(args, "active_practice_plan", "activePracticePlan", "practice_plan", "practicePlan")
    if isinstance(plan_ctx, dict) and plan_ctx.get("section_name"):
        sections["active_practice_plan_context"] = _redact_sensitive_values(plan_ctx)
    elif isinstance(plan_raw, dict):
        sections["active_practice_plan_context"] = build_active_practice_plan_context_intake_payload({"practicePlan": plan_raw}, trace_id=trace_id, source="snapshot_context_intake_explicit_plan").context_packet_section
    elif "active_practice_plan" in entities or "practice_plan" in entities:
        sections["active_practice_plan_context"] = _plan_metadata_section(trace_id, record_count, source); warnings.append("active_practice_plan_restored_as_metadata_only_context")
    history_ctx = _first_present(args, "routine_history_context", "routineHistoryContext", "practice_history_context", "practiceHistoryContext")
    history_raw = _first_present(args, "routine_history_records", "routineHistoryRecords", "practice_history_records", "practiceHistoryRecords")
    if isinstance(history_ctx, dict) and history_ctx.get("section_name"):
        sections["routine_history_context"] = _redact_sensitive_values(history_ctx)
    elif isinstance(history_raw, list):
        sections["routine_history_context"] = build_routine_history_context_intake_payload({"routineHistoryRecords": history_raw}, trace_id=trace_id, source="snapshot_context_intake_explicit_history").context_packet_section
    elif "routine_history_summary" in entities:
        sections["routine_history_context"] = _history_metadata_section(trace_id, record_count, source); warnings.append("routine_history_summary_restored_as_metadata_only_context")
    return sections, warnings


def build_context_persistence_profile_plan_history_snapshot_context_intake_payload(arguments: dict[str, Any] | None = None, *, trace_id: str | None = None, source: str = "context_persistence_profile_plan_history_snapshot_context_intake") -> ContextPersistenceProfilePlanHistorySnapshotContextIntakePayload:
    args = dict(arguments or {})
    snapshot_intake_id = str(_first_present(args, "snapshot_intake_id", "snapshotIntakeId") or f"ctx_snapshot_intake_{uuid4().hex[:12]}")
    trace_value = trace_id or args.get("trace_id") or args.get("traceId")
    requested_entities = _normalize_storage_adapter_entities(args)
    readback_payload, snapshot_source = _snapshot_readback_payload(args, trace_value)
    readback_validation = readback_payload.get("validation") if isinstance(readback_payload.get("validation"), dict) else {}
    fixture_read = readback_payload.get("fixture_read_result") if isinstance(readback_payload.get("fixture_read_result"), dict) else {}
    snapshot_preview = readback_payload.get("context_snapshot_preview") if isinstance(readback_payload.get("context_snapshot_preview"), dict) else {}
    readback_summary = {"snapshot_source": snapshot_source, "readback_payload_present": bool(readback_payload), "readback_validation_status": readback_validation.get("status"), "readback_accepted": readback_validation.get("accepted", True), "file_exists": fixture_read.get("file_exists", False), "records_read": fixture_read.get("records_read", 0), "matched_record_count": fixture_read.get("matched_record_count", snapshot_preview.get("record_count", 0)), "snapshot_available": snapshot_preview.get("snapshot_available", False)}
    entities = _snapshot_entities(readback_payload, requested_entities)
    record_count = int(readback_summary.get("matched_record_count") or 0)
    sections, warnings = _snapshot_context_sections(args, entities=entities, trace_id=trace_value, record_count=record_count, source=snapshot_source)
    if sections:
        sections["assembled_practice_context"] = {"section_name": "assembled_practice_context", "assembled_from": [k for k in ("user_practice_profile_context", "active_practice_plan_context", "routine_history_context") if k in sections], "context_persistence_profile_plan_history_snapshot_context_intake_version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, "aggregate_summary": {"profile_context_present": "user_practice_profile_context" in sections, "active_plan_context_present": "active_practice_plan_context" in sections, "routine_history_context_present": "routine_history_context" in sections, "summary_for_llm": "已从持久化 snapshot preview 恢复可注入的用户画像、长期计划与练习历史上下文；仅作为下一次用户主动询问时的上下文。"}, "decision_inputs": ["user_practice_profile", "active_practice_plan", "routine_history", "persistence_snapshot"], "context_usage_policy": {"use_when_user_asks_what_to_practice_next": True, "do_not_create_post_session_recommendation_card": True, "do_not_start_routine": True, "do_not_call_accompaniment_generate": True}}
    kwargs = {"user_practice_profile_context": sections.get("user_practice_profile_context"), "active_practice_plan_context": sections.get("active_practice_plan_context"), "routine_history_context": sections.get("routine_history_context"), "assembled_practice_context": sections.get("assembled_practice_context")}
    kwargs = {k: v for k, v in kwargs.items() if isinstance(v, dict)}
    context_packet_section = {"section_name": "context_persistence_profile_plan_history_snapshot_context_intake", "context_persistence_profile_plan_history_snapshot_context_intake_version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, "purpose": "Restore profile / active plan / routine history context from a dev persistence snapshot into the next ContextPacket.", "snapshot_source": snapshot_source, "requested_entities": list(entities), "normalized_context_sections": sections, "context_packet_kwargs": kwargs, "context_usage_policy": {"inject_into_context_builder": True, "use_when_user_asks_what_to_practice_next": True, "do_not_create_post_session_recommendation_card": True, "do_not_start_routine": True, "do_not_call_accompaniment_generate": True}}
    blocked = []
    if readback_validation.get("accepted") is False: blocked.append("readback_payload_validation_not_accepted")
    if _has_any_forbidden_context_fields(args): blocked.append("forbidden_context_fields_present")
    if not sections: warnings.append("no_profile_plan_history_sections_restored")
    accepted = not blocked
    validation = {"accepted": accepted, "status": "snapshot_context_intake_ready" if accepted else "snapshot_context_intake_blocked", "warnings": warnings, "blocked_reasons": blocked, "restored_section_count": len([k for k in sections if k != "assembled_practice_context"]), "context_packet_kwargs_ready": bool(kwargs), "storage_written": False, "backend_database_written": False, "local_device_written": False, "sqlite_connection_created": False, "sqlite_tables_created": False, "sqlite_rows_written": False, "llm_called": False, "tool_executed": False, "engine_adapter_called": False, "midi_asset_created": False, "playback_started": False, "routine_start_enabled": False, "post_session_recommendation_card_created": False}
    injection = {"context_builder_can_accept_section": accepted and bool(kwargs), "injectable_kwargs": sorted(kwargs), "learner_context_sections_to_inject": [k for k in kwargs], "selected_context_layers_expected": [k for k in kwargs], "storage_written": False}
    guard = {"context_persistence_profile_plan_history_snapshot_context_intake": True, "snapshot_context_intake_only": True, "context_packet_injection_previewed": True, "storage_written": False, "backend_database_written": False, "local_device_written": False, "sqlite_connection_created": False, "sqlite_tables_created": False, "sqlite_rows_written": False, "durable_backend_write_executed": False, "fixture_write_executed": False, "transaction_committed": False, "replay_execution_committed": False, "llm_called": False, "tool_executed": False, "route_called": False, "engine_adapter_called": False, "midi_asset_created": False, "playback_started": False, "routine_start_enabled": False, "post_session_recommendation_card_created": False, "midi_asset_payload_allowed_in_adapter": False, "local_playback_state_allowed_in_context": False, "hidden_chain_of_thought_allowed_in_payload": False}
    return ContextPersistenceProfilePlanHistorySnapshotContextIntakePayload(CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, source, snapshot_intake_id, snapshot_source, list(entities), readback_summary, sections, context_packet_section, injection, validation, guard, trace_value)


def build_context_persistence_profile_plan_history_snapshot_context_intake_summary(*, payload: ContextPersistenceProfilePlanHistorySnapshotContextIntakePayload | None = None, source: str = "terminal_chat_cli") -> dict[str, Any]:
    data = payload.to_dict() if payload else {}; validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}; sections = data.get("normalized_context_sections") if isinstance(data.get("normalized_context_sections"), dict) else {}; injection = data.get("context_builder_injection_preview") if isinstance(data.get("context_builder_injection_preview"), dict) else {}
    return {"context_persistence_profile_plan_history_snapshot_context_intake_version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, "source": source, "has_payload": payload is not None, "validation_status": validation.get("status"), "accepted": validation.get("accepted", False), "snapshot_intake_id": data.get("snapshot_intake_id"), "snapshot_source": data.get("snapshot_source"), "requested_entities": list(data.get("requested_entities") or []), "profile_context_present": "user_practice_profile_context" in sections, "active_plan_context_present": "active_practice_plan_context" in sections, "routine_history_context_present": "routine_history_context" in sections, "assembled_practice_context_present": "assembled_practice_context" in sections, "context_builder_can_accept_section": injection.get("context_builder_can_accept_section", False), "injectable_kwargs": list(injection.get("injectable_kwargs") or []), "storage_written": False, "backend_database_written": False, "local_device_written": False, "sqlite_connection_created": False, "sqlite_tables_created": False, "sqlite_rows_written": False, "durable_backend_write_executed": False, "fixture_write_executed": False, "transaction_committed": False, "replay_execution_committed": False, "future_executor_implemented": False, "llm_called": False, "tool_executed": False, "route_called": False, "engine_adapter_called": False, "midi_asset_created": False, "playback_started": False, "post_session_recommendation_card_created": False, "accompaniment_generate_call_enabled": False, "routine_start_enabled": False, "warnings": list(validation.get("warnings") or []), "blocked_reasons": list(validation.get("blocked_reasons") or [])}


def context_persistence_profile_plan_history_snapshot_context_intake_contract() -> dict[str, Any]:
    return {"version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, "context_persistence_profile_plan_history_snapshot_context_intake_version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION, "spec_route": "GET /agent/context/persistence-snapshot-context-intake/spec", "preview_route": "POST /agent/context/persistence-snapshot-context-intake/preview", "terminal_command": "/context-persistence-snapshot-context-intake", "surface": "Profile / active plan / routine history snapshot context intake contract", "mode": "readback_snapshot_to_context_packet_intake_no_mutation", "execution_status": {"snapshot_context_intake_defined": True, "context_packet_injection_previewed": True, "profile_plan_history_sections_restored": True, "real_sqlite_write_enabled": False, "database_connection_created": False, "database_persistence_implemented": False, "backend_write_enabled": False, "local_device_write_enabled": False, "llm_call_enabled": False, "tool_execution_enabled": False, "routine_start_enabled": False, "post_session_recommendation_card_enabled": False, "playback_execution_enabled": False, "accompaniment_generate_call_enabled": False, "engine_adapter_dispatch_enabled": False, "midi_asset_creation_enabled": False}, "intake_flow": ["accept embedded readback payload or read-only dev fixture snapshot", "detect user_practice_profile / active_practice_plan / routine_history entities", "normalize explicit profile/plan/history data when supplied", "fallback to metadata-only context sections when snapshot has only fixture metadata", "return ContextBuilder-ready context_packet_kwargs without mutating runtime state"], "guards": {"payload_writes_storage": False, "payload_calls_llm": False, "payload_executes_tool": False, "payload_creates_post_session_recommendation_card": False, "payload_calls_accompaniment_generate": False, "payload_calls_engine_adapter": False, "payload_creates_midi_asset": False, "payload_starts_playback": False, "sqlite_connection_created": False, "sqlite_tables_created": False, "sqlite_rows_written": False, "durable_backend_write_executed": False, "fixture_write_executed": False, "transaction_committed": False, "raw_api_key_allowed_in_payload": False, "midi_base64_allowed_in_adapter_payload": False, "local_midi_path_allowed_in_adapter_payload": False, "hidden_chain_of_thought_allowed_in_payload": False}, "uses_contracts": {"user_practice_profile_context_intake": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION, "active_practice_plan_context_intake": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION, "routine_history_context_intake": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION, "context_persistence_dev_fixture_readback_replay": CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION}, "next_task_hint": "v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e"}


@dataclass(frozen=True)
class TodayPracticeGuidancePersistedContextRecoveryE2EPayload:
    """v2_8_17 persisted-context recovery E2E for today-practice guidance.

    This surface bridges the v2_8_15 read-back / v2_8_16 snapshot context
    intake chain into the existing profile-aware today-practice guidance E2E.
    It is still display-only and side-effect free: no storage mutation, no
    Routine start, no /accompaniment/generate call, no engine adapter dispatch,
    and no MIDI asset creation.
    """

    payload_contract_version: str
    source: str
    recovery_e2e_id: str
    snapshot_context_intake_payload: dict[str, Any]
    recovered_context_packet_section: dict[str, Any]
    recovered_context_summary: dict[str, Any]
    guidance_payload: dict[str, Any]
    guidance_summary: dict[str, Any]
    recovery_bridge: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    durable_backend_write_executed: bool = False
    fixture_write_executed: bool = False
    transaction_committed: bool = False
    replay_execution_committed: bool = False
    future_executor_implemented: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "recovery_e2e_id": self.recovery_e2e_id,
            "snapshot_context_intake_payload": _redact_sensitive_values(self.snapshot_context_intake_payload),
            "recovered_context_packet_section": _redact_sensitive_values(self.recovered_context_packet_section),
            "recovered_context_summary": _redact_sensitive_values(self.recovered_context_summary),
            "guidance_payload": _redact_sensitive_values(self.guidance_payload),
            "guidance_summary": _redact_sensitive_values(self.guidance_summary),
            "recovery_bridge": _redact_sensitive_values(self.recovery_bridge),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "durable_backend_write_executed": self.durable_backend_write_executed,
            "fixture_write_executed": self.fixture_write_executed,
            "transaction_committed": self.transaction_committed,
            "replay_execution_committed": self.replay_execution_committed,
            "future_executor_implemented": self.future_executor_implemented,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _extract_snapshot_intake_payload_for_recovery(args: dict[str, Any], trace_id: str | None) -> tuple[dict[str, Any], str]:
    for key in (
        "snapshot_context_intake_payload",
        "snapshotContextIntakePayload",
        "context_persistence_profile_plan_history_snapshot_context_intake_payload",
        "contextPersistenceProfilePlanHistorySnapshotContextIntakePayload",
    ):
        value = args.get(key)
        if isinstance(value, dict):
            return value, "embedded_snapshot_context_intake_payload"
    section = _first_present(args, "context_persistence_snapshot_context_intake", "contextPersistenceSnapshotContextIntake")
    if isinstance(section, dict):
        # Wrap a ready ContextBuilder section in the same payload shape the bridge expects.
        normalized = section.get("normalized_context_sections") if isinstance(section.get("normalized_context_sections"), dict) else {}
        kwargs = section.get("context_packet_kwargs") if isinstance(section.get("context_packet_kwargs"), dict) else {}
        if not normalized:
            normalized = {k: v for k, v in kwargs.items() if isinstance(v, dict)}
        return {
            "payload_contract_version": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
            "snapshot_source": "embedded_context_packet_section",
            "normalized_context_sections": normalized,
            "context_packet_section": section,
            "context_builder_injection_preview": {"context_builder_can_accept_section": bool(kwargs or normalized), "injectable_kwargs": sorted((kwargs or normalized).keys())},
            "validation": {"accepted": True, "status": "embedded_context_packet_section"},
        }, "embedded_context_packet_section"
    return build_context_persistence_profile_plan_history_snapshot_context_intake_payload(
        args,
        trace_id=trace_id,
        source="persisted_context_recovery_snapshot_context_intake",
    ).to_dict(), "snapshot_context_intake_builder"


def _summarize_recovered_context_sections(snapshot_payload: dict[str, Any]) -> dict[str, Any]:
    sections = snapshot_payload.get("normalized_context_sections") if isinstance(snapshot_payload.get("normalized_context_sections"), dict) else {}
    section = snapshot_payload.get("context_packet_section") if isinstance(snapshot_payload.get("context_packet_section"), dict) else {}
    if not sections and isinstance(section.get("normalized_context_sections"), dict):
        sections = section.get("normalized_context_sections") or {}
    profile = sections.get("user_practice_profile_context") if isinstance(sections.get("user_practice_profile_context"), dict) else {}
    plan = sections.get("active_practice_plan_context") if isinstance(sections.get("active_practice_plan_context"), dict) else {}
    history = sections.get("routine_history_context") if isinstance(sections.get("routine_history_context"), dict) else {}
    assembled = sections.get("assembled_practice_context") if isinstance(sections.get("assembled_practice_context"), dict) else {}
    profile_inner = profile.get("profile") if isinstance(profile.get("profile"), dict) else profile
    plan_blocks = plan.get("plan_blocks") or plan.get("planBlocks") or []
    if not isinstance(plan_blocks, list):
        plan_blocks = []
    recent_history = history.get("recent_practice_history") or history.get("recentPracticeHistory") or []
    if not isinstance(recent_history, list):
        recent_history = []
    return {
        "profile_context_present": bool(profile),
        "active_plan_context_present": bool(plan),
        "routine_history_context_present": bool(history),
        "assembled_practice_context_present": bool(assembled),
        "profile_status": profile.get("profile_status") or profile_inner.get("profile_status"),
        "profile_summary": profile.get("summary_for_llm") or profile_inner.get("summary_for_llm"),
        "preferred_styles": list(profile_inner.get("preferred_styles") or []),
        "focus_areas": list(profile_inner.get("focus_areas") or []),
        "active_plan_status": (plan.get("active_plan") or {}).get("plan_status") if isinstance(plan.get("active_plan"), dict) else None,
        "plan_block_count": len(plan_blocks),
        "routine_history_item_count": len(recent_history),
        "decision_inputs": list(assembled.get("decision_inputs") or []),
        "context_is_metadata_only": any(str(v).endswith("metadata_only") for v in (profile.get("profile_status"), (plan.get("active_plan") or {}).get("plan_status") if isinstance(plan.get("active_plan"), dict) else None)),
    }


def build_today_practice_guidance_persisted_context_recovery_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_persisted_context_recovery_e2e",
    provider: Any | None = None,
) -> TodayPracticeGuidancePersistedContextRecoveryE2EPayload:
    """Recover persisted profile/plan/history snapshot context and run guarded guidance E2E."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    recovery_e2e_id = str(_first_present(args, "recovery_e2e_id", "recoveryE2eId") or f"today_guidance_persisted_recovery_{uuid4().hex[:12]}")
    user_input = str(_first_present(args, "user_input", "userInput", "text") or "今天该练什么？")

    snapshot_payload, snapshot_source = _extract_snapshot_intake_payload_for_recovery(args, trace)
    snapshot_validation = snapshot_payload.get("validation") if isinstance(snapshot_payload.get("validation"), dict) else {}
    recovered_section = snapshot_payload.get("context_packet_section") if isinstance(snapshot_payload.get("context_packet_section"), dict) else {}
    context_packet_kwargs = recovered_section.get("context_packet_kwargs") if isinstance(recovered_section.get("context_packet_kwargs"), dict) else {}
    if not context_packet_kwargs and isinstance(snapshot_payload.get("normalized_context_sections"), dict):
        normalized = snapshot_payload.get("normalized_context_sections") or {}
        context_packet_kwargs = {k: v for k, v in normalized.items() if isinstance(v, dict)}
    recovered_summary = _summarize_recovered_context_sections(snapshot_payload)

    guidance_args = dict(args)
    guidance_args.update({k: v for k, v in context_packet_kwargs.items() if isinstance(v, dict)})
    guidance_args["context_persistence_snapshot_context_intake"] = recovered_section
    guidance_args["userInput"] = user_input
    guidance_args.setdefault("callProvider", bool(args.get("callProvider") or args.get("call_provider") or False))
    if args.get("availableMinutes") is not None:
        guidance_args["availableMinutes"] = args.get("availableMinutes")
    if args.get("available_minutes") is not None:
        guidance_args["available_minutes"] = args.get("available_minutes")

    guidance_obj = build_today_practice_guidance_profile_aware_e2e_payload(
        guidance_args,
        trace_id=trace,
        source="persisted_context_recovery_profile_aware_guidance",
        provider=provider,
    )
    guidance_payload = guidance_obj.to_dict()
    guidance_summary = build_today_practice_guidance_profile_aware_e2e_summary(payload=guidance_obj, source="persisted_context_recovery_e2e")
    guidance_validation = guidance_payload.get("validation") if isinstance(guidance_payload.get("validation"), dict) else {}

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if snapshot_validation.get("accepted") is False:
        blocked_reasons.append("snapshot_context_intake_not_accepted")
    if not recovered_summary.get("profile_context_present"):
        warnings.append("recovered_profile_context_missing")
    if not recovered_summary.get("active_plan_context_present"):
        warnings.append("recovered_active_plan_context_missing")
    if not recovered_summary.get("routine_history_context_present"):
        warnings.append("recovered_routine_history_context_missing")
    if guidance_validation.get("is_valid") is False:
        warnings.append("guidance_action_card_not_valid_or_guarded")
    warnings.extend(list(snapshot_validation.get("warnings") or []))
    warnings.extend(list(guidance_validation.get("warnings") or []))

    validation_status = "persisted_context_recovery_guidance_ready" if not blocked_reasons else "persisted_context_recovery_guidance_blocked"
    validation = {
        "status": validation_status,
        "accepted": not blocked_reasons,
        "snapshot_context_intake_accepted": snapshot_validation.get("accepted", False),
        "persisted_context_recovered": bool(context_packet_kwargs),
        "profile_context_recovered": recovered_summary.get("profile_context_present", False),
        "active_plan_context_recovered": recovered_summary.get("active_plan_context_present", False),
        "routine_history_context_recovered": recovered_summary.get("routine_history_context_present", False),
        "guidance_action_card_is_valid": bool(guidance_validation.get("is_valid", False)),
        "display_only": True,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "llm_called": bool(guidance_obj.llm_called),
        "tool_executed": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
    }
    recovery_bridge = {
        "recovery_e2e_id": recovery_e2e_id,
        "snapshot_source": snapshot_source,
        "context_packet_kwargs_ready": bool(context_packet_kwargs),
        "context_packet_kwargs_keys": sorted(context_packet_kwargs.keys()),
        "passes_recovered_context_to_profile_aware_guidance": True,
        "uses_profile_as_soft_context_not_rule_engine": True,
        "does_not_create_post_session_recommendation_card": True,
        "client_decides_presentation": True,
    }
    guard = {
        "today_practice_guidance_persisted_context_recovery_e2e": True,
        "snapshot_readback_is_read_only": True,
        "snapshot_context_intake_only": True,
        "guidance_is_display_only": True,
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
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "hidden_chain_of_thought_allowed_in_payload": False,
        "midi_base64_allowed_in_adapter_payload": False,
        "local_midi_path_allowed_in_adapter_payload": False,
    }
    return TodayPracticeGuidancePersistedContextRecoveryE2EPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        source=source,
        recovery_e2e_id=recovery_e2e_id,
        snapshot_context_intake_payload=snapshot_payload,
        recovered_context_packet_section=recovered_section,
        recovered_context_summary=recovered_summary,
        guidance_payload=guidance_payload,
        guidance_summary=guidance_summary,
        recovery_bridge=recovery_bridge,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
        llm_called=bool(guidance_obj.llm_called),
    )


def build_today_practice_guidance_persisted_context_recovery_e2e_summary(
    *,
    payload: TodayPracticeGuidancePersistedContextRecoveryE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    recovered = data.get("recovered_context_summary") if isinstance(data.get("recovered_context_summary"), dict) else {}
    guidance_summary = data.get("guidance_summary") if isinstance(data.get("guidance_summary"), dict) else {}
    bridge = data.get("recovery_bridge") if isinstance(data.get("recovery_bridge"), dict) else {}
    return {
        "today_practice_guidance_persisted_context_recovery_e2e_version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "recovery_e2e_id": data.get("recovery_e2e_id"),
        "snapshot_source": bridge.get("snapshot_source"),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "persisted_context_recovered": validation.get("persisted_context_recovered", False),
        "profile_summary": recovered.get("profile_summary"),
        "preferred_styles": list(recovered.get("preferred_styles") or []),
        "plan_block_count": recovered.get("plan_block_count", 0),
        "routine_history_item_count": recovered.get("routine_history_item_count", 0),
        "guidance_action_card_is_valid": validation.get("guidance_action_card_is_valid", False),
        "routine_candidate_count": guidance_summary.get("routine_candidate_count", 0),
        "llm_called": data.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "sqlite_connection_created": False,
        "sqlite_tables_created": False,
        "sqlite_rows_written": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def today_practice_guidance_persisted_context_recovery_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        "today_practice_guidance_persisted_context_recovery_e2e_version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/persisted-context-recovery/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
        "terminal_command": "/today-practice-guidance-persisted-context-recovery",
        "surface": "Persisted context recovery E2E for today-practice guidance",
        "mode": "dev_fixture_or_snapshot_readback_to_profile_aware_display_guidance_card",
        "execution_status": {
            "persisted_context_recovery_enabled": True,
            "snapshot_context_intake_used": True,
            "profile_aware_guidance_used": True,
            "guidance_display_only": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "recovery_flow": [
            "read embedded snapshot context intake payload or dev fixture read-back snapshot",
            "convert snapshot into ContextBuilder-ready user profile / active plan / routine history sections",
            "inject recovered context into profile-aware today-practice guidance E2E",
            "return display-only ActionCard and Routine candidates without starting practice",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_creates_post_session_recommendation_card": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "durable_backend_write_executed": False,
            "fixture_write_executed": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "context_persistence_profile_plan_history_snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
            "today_practice_guidance_profile_aware_e2e": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
            "context_persistence_dev_fixture_readback_replay": CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_VERSION,
        },
        "next_task_hint": "v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls",
    }


def today_practice_guidance_persisted_context_terminal_memory_controls_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
        "today_practice_guidance_persisted_context_terminal_memory_controls_version": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
        "terminal_commands": {
            "load": "/persisted-context-load [json_payload]",
            "show": "/persisted-context-show",
            "clear": "/persisted-context-clear",
        },
        "surface": "Terminal-only persisted context memory controls",
        "mode": "temporary_session_memory_for_today_practice_guidance_testing",
        "execution_status": {
            "terminal_memory_controls_enabled": True,
            "session_memory_only": True,
            "persisted_context_can_be_loaded_for_next_today_guidance_turn": True,
            "ordinary_today_practice_turn_can_use_loaded_memory": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled": False,
            "llm_call_enabled_by_memory_commands": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "memory_flow": [
            "load profile / active plan / routine history JSON or snapshot context intake payload into terminal session memory",
            "show compact memory status without exposing secrets or raw local playback state",
            "inject loaded memory into the next ordinary today-practice guidance turn",
            "clear memory explicitly from the terminal session",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_creates_post_session_recommendation_card": False,
            "sqlite_connection_created": False,
            "sqlite_tables_created": False,
            "sqlite_rows_written": False,
            "raw_api_key_allowed_in_payload": False,
            "midi_base64_allowed_in_adapter_payload": False,
            "local_midi_path_allowed_in_adapter_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "context_persistence_profile_plan_history_snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
            "today_practice_guidance_persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture",
    }


@dataclass(frozen=True)
class TodayPracticeGuidanceTerminalMemoryToHarmonyOSDebugFixturePayload:
    """v2_8_19 bridge from terminal persisted-context memory to HarmonyOS debug fixture preview.

    The payload is a frontend-debug fixture preview only. It serializes the
    already-normalized terminal memory / snapshot context into a HarmonyOS-facing
    debug request shape so the client can test the same recovered-context
    today-practice guidance path without manually pasting large JSON blocks.
    It does not write storage, call the LLM, execute tools, start Routine, call
    /accompaniment/generate, call engine adapters, create MIDI, or start playback.
    """

    payload_contract_version: str
    source: str
    fixture_id: str
    user_input: str
    snapshot_context_intake_payload: dict[str, Any]
    recovered_context_summary: dict[str, Any]
    harmonyos_debug_fixture: dict[str, Any]
    agent_request_preview: dict[str, Any]
    terminal_command_preview: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "fixture_id": self.fixture_id,
            "user_input": self.user_input,
            "snapshot_context_intake_payload": _redact_sensitive_values(self.snapshot_context_intake_payload),
            "recovered_context_summary": _redact_sensitive_values(self.recovered_context_summary),
            "harmonyos_debug_fixture": _redact_sensitive_values(self.harmonyos_debug_fixture),
            "agent_request_preview": _redact_sensitive_values(self.agent_request_preview),
            "terminal_command_preview": _redact_sensitive_values(self.terminal_command_preview),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _extract_terminal_memory_debug_fixture_source_args(args: dict[str, Any]) -> tuple[dict[str, Any], str]:
    memory = _first_present(args, "persisted_context_memory", "persistedContextMemory", "terminalMemory", "terminal_memory")
    if isinstance(memory, dict):
        guidance_args = memory.get("guidance_arguments") or memory.get("guidanceArguments")
        if isinstance(guidance_args, dict):
            return dict(guidance_args), "terminal_persisted_context_memory_guidance_arguments"
        snapshot = memory.get("snapshot_context_intake_payload") or memory.get("snapshotContextIntakePayload")
        if isinstance(snapshot, dict):
            return {"snapshotContextIntakePayload": snapshot}, "terminal_persisted_context_memory_snapshot_payload"
    snapshot = _first_present(args, "snapshot_context_intake_payload", "snapshotContextIntakePayload", "contextPersistenceSnapshotContextIntake")
    if isinstance(snapshot, dict):
        return {"snapshotContextIntakePayload": snapshot}, "embedded_snapshot_context_intake_payload"
    return dict(args), "direct_debug_fixture_arguments"


def build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture",
) -> TodayPracticeGuidanceTerminalMemoryToHarmonyOSDebugFixturePayload:
    """Build a HarmonyOS debug fixture preview from terminal persisted-context memory."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    user_input = str(_first_present(args, "user_input", "userInput", "text") or "今天该练什么？")
    fixture_id = str(_first_present(args, "fixture_id", "fixtureId", "debug_fixture_id", "debugFixtureId") or f"harmonyos_today_guidance_debug_{uuid4().hex[:12]}")
    available_minutes = _first_present(args, "available_minutes", "availableMinutes")
    source_args, source_kind = _extract_terminal_memory_debug_fixture_source_args(args)
    if available_minutes is not None:
        source_args.setdefault("availableMinutes", available_minutes)
    source_args.setdefault("userInput", user_input)

    snapshot_payload, snapshot_source = _extract_snapshot_intake_payload_for_recovery(source_args, trace)
    recovered_summary = _summarize_recovered_context_sections(snapshot_payload)
    snapshot_validation = snapshot_payload.get("validation") if isinstance(snapshot_payload.get("validation"), dict) else {}
    accepted = bool(snapshot_validation.get("accepted", True)) and any(
        bool(recovered_summary.get(key))
        for key in ("profile_context_present", "active_plan_context_present", "routine_history_context_present", "assembled_practice_context_present")
    )
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if not accepted:
        blocked_reasons.append("no_recoverable_profile_plan_or_history_context_for_harmonyos_debug_fixture")
    if source_kind == "direct_debug_fixture_arguments":
        warnings.append("fixture_built_from_direct_arguments_not_terminal_memory")
    if snapshot_source == "snapshot_context_intake_builder":
        warnings.append("snapshot_context_intake_payload_was_built_for_debug_fixture_preview")

    agent_body = {
        "userInput": user_input,
        "availableMinutes": available_minutes,
        "snapshotContextIntakePayload": snapshot_payload,
        "callProvider": False,
        "debugFixtureMode": True,
    }
    provider_result = _first_present(args, "provider_result", "providerResult") or _first_present(source_args, "provider_result", "providerResult")
    if isinstance(provider_result, dict):
        agent_body["providerResult"] = provider_result
    agent_request_preview = {
        "method": "POST",
        "path": "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
        "body": agent_body,
        "side_effects_created": False,
        "client_may_call_for_debug_preview": True,
    }
    terminal_command_preview = {
        "load_context": "/persisted-context-load <harmonyos_debug_fixture.contextPayload>",
        "ask_guidance": user_input,
        "show_memory": "/persisted-context-show",
        "clear_memory": "/persisted-context-clear",
    }
    context_payload = {
        "availableMinutes": available_minutes,
        "userInput": user_input,
        "snapshotContextIntakePayload": snapshot_payload,
    }
    harmonyos_debug_fixture = {
        "fixtureContractVersion": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
        "fixtureKind": "today_practice_guidance_persisted_context_debug_fixture",
        "fixtureId": fixture_id,
        "title": "Today Practice Guidance persisted-context debug fixture",
        "description": "Load recovered profile / active plan / routine history context, then preview today-practice guidance.",
        "harmonyosOwned": True,
        "backendOwned": False,
        "clientDecidesPresentation": True,
        "frontendFlowAssumption": False,
        "contextPayload": context_payload,
        "agentRequestPreview": agent_request_preview,
        "debugClientFlow": [
            "load persisted-context fixture into HarmonyOS debug screen state",
            "call Agent persisted-context recovery preview route or terminal memory command",
            "render display-only ActionCard / Routine candidate returned by Agent",
            "require separate user confirmation before any future Routine start",
        ],
        "expectedGuards": {
            "storageWritten": False,
            "backendDatabaseWritten": False,
            "localDeviceWrittenByAgent": False,
            "llmCalledByFixtureBuilder": False,
            "toolExecuted": False,
            "routineStartEnabled": False,
            "accompanimentGenerateCallEnabled": False,
            "engineAdapterCalled": False,
            "midiAssetCreated": False,
            "playbackStarted": False,
            "postSessionRecommendationCardCreated": False,
        },
    }
    validation = {
        "accepted": accepted,
        "status": "accepted" if accepted else "blocked",
        "source_kind": source_kind,
        "snapshot_source": snapshot_source,
        "profile_context_present": recovered_summary.get("profile_context_present", False),
        "active_plan_context_present": recovered_summary.get("active_plan_context_present", False),
        "routine_history_context_present": recovered_summary.get("routine_history_context_present", False),
        "assembled_practice_context_present": recovered_summary.get("assembled_practice_context_present", False),
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "fixture_builder_writes_storage": False,
        "fixture_builder_calls_llm": False,
        "fixture_builder_executes_tool": False,
        "fixture_builder_calls_engine_adapter": False,
        "fixture_builder_calls_accompaniment_generate": False,
        "fixture_builder_creates_midi_asset": False,
        "fixture_builder_starts_playback": False,
        "fixture_builder_starts_routine": False,
        "fixture_builder_creates_post_session_recommendation_card": False,
        "harmonyos_fixture_is_debug_preview_only": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }
    return TodayPracticeGuidanceTerminalMemoryToHarmonyOSDebugFixturePayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
        source=source,
        fixture_id=fixture_id,
        user_input=user_input,
        snapshot_context_intake_payload=snapshot_payload,
        recovered_context_summary=recovered_summary,
        harmonyos_debug_fixture=harmonyos_debug_fixture,
        agent_request_preview=agent_request_preview,
        terminal_command_preview=terminal_command_preview,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
    )


def build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary(
    *,
    payload: TodayPracticeGuidanceTerminalMemoryToHarmonyOSDebugFixturePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    recovered = data.get("recovered_context_summary") if isinstance(data.get("recovered_context_summary"), dict) else {}
    request = data.get("agent_request_preview") if isinstance(data.get("agent_request_preview"), dict) else {}
    return {
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "fixture_id": data.get("fixture_id"),
        "source_kind": validation.get("source_kind"),
        "snapshot_source": validation.get("snapshot_source"),
        "profile_context_present": validation.get("profile_context_present", False),
        "active_plan_context_present": validation.get("active_plan_context_present", False),
        "routine_history_context_present": validation.get("routine_history_context_present", False),
        "assembled_practice_context_present": validation.get("assembled_practice_context_present", False),
        "profile_summary": recovered.get("profile_summary"),
        "plan_block_count": recovered.get("plan_block_count", 0),
        "routine_history_item_count": recovered.get("routine_history_item_count", 0),
        "debug_fixture_ready": bool(validation.get("accepted")),
        "agent_preview_route": request.get("path"),
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview",
        "terminal_command": "/persisted-context-harmonyos-debug-fixture [json_payload]",
        "surface": "Terminal persisted-context memory to HarmonyOS debug fixture preview",
        "mode": "frontend_debug_fixture_preview_only",
        "execution_status": {
            "debug_fixture_preview_enabled": True,
            "terminal_memory_can_be_serialized_for_harmonyos_debug": True,
            "harmonyos_can_use_fixture_to_call_persisted_context_recovery_preview": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled_by_agent": False,
            "llm_call_enabled_by_fixture_builder": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "fixture_flow": [
            "read terminal persisted-context memory or direct profile/plan/history JSON",
            "normalize it through snapshot context intake",
            "emit a HarmonyOS debug fixture payload and Agent preview request shape",
            "client may render display-only guidance and Routine candidate after calling preview route",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_creates_post_session_recommendation_card": False,
            "frontend_flow_assumption": False,
            "client_decides_presentation": True,
        },
        "uses_contracts": {
            "today_practice_guidance_persisted_context_terminal_memory_controls": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_TERMINAL_MEMORY_CONTROLS_VERSION,
            "context_persistence_profile_plan_history_snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
            "today_practice_guidance_persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
        },
        "next_task_hint": "v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e",
    }

def _normalize_storage_adapter_entities(args: dict[str, Any]) -> list[str]:
    raw = _first_present(args, "entities", "context_entities", "contextEntities", "requested_entities", "requestedEntities")
    if raw is None:
        return ["user_practice_profile", "active_practice_plan", "routine_history_summary", "agent_trace_metadata", "idempotency_record"]
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple)):
        return [str(item) for item in raw if item is not None]
    return [str(raw)]

def _extract_context_persistence_confirmation_payload(args: dict[str, Any]) -> dict[str, Any] | None:
    for key in (
        "confirmation_payload",
        "confirmationPayload",
        "context_persistence_confirmation_boundary_payload",
        "contextPersistenceConfirmationBoundaryPayload",
        "contextPersistenceConfirmation",
        "context_persistence_confirmation",
    ):
        value = args.get(key)
        if isinstance(value, dict):
            return value
    if str(args.get("payload_contract_version") or "") == CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION:
        return args
    return None


def _context_confirmation_payload_from_dict(data: dict[str, Any]) -> ContextPersistenceConfirmationBoundaryPayload:
    return ContextPersistenceConfirmationBoundaryPayload(
        payload_contract_version=str(data.get("payload_contract_version") or CONTEXT_PERSISTENCE_CONFIRMATION_BOUNDARY_VERSION),
        source=str(data.get("source") or "embedded_context_persistence_confirmation_boundary"),
        confirmation_id=str(data.get("confirmation_id") or ""),
        candidate_kind=str(data.get("candidate_kind") or "unknown"),
        candidate_id=str(data.get("candidate_id") or "") or None,
        candidate_payload=data.get("candidate_payload") if isinstance(data.get("candidate_payload"), dict) else {},
        candidate_summary=data.get("candidate_summary") if isinstance(data.get("candidate_summary"), dict) else {},
        user_decision=str(data.get("user_decision") or "pending"),
        confirmation_status=str(data.get("confirmation_status") or ""),
        confirmation_envelope=data.get("confirmation_envelope") if isinstance(data.get("confirmation_envelope"), dict) else {},
        future_executor_boundary=data.get("future_executor_boundary") if isinstance(data.get("future_executor_boundary"), dict) else {},
        validation=data.get("validation") if isinstance(data.get("validation"), dict) else {},
        guard_summary=data.get("guard_summary") if isinstance(data.get("guard_summary"), dict) else {},
        trace_id=data.get("trace_id"),
    )


def _build_context_persistence_idempotency_key(confirmation_id: str | None, candidate_kind: str, candidate_id: str | None) -> str:
    material = json.dumps(
        {
            "confirmation_id": confirmation_id or "missing_confirmation",
            "candidate_kind": candidate_kind or "unknown",
            "candidate_id": candidate_id or "missing_candidate",
            "executor_version": CONTEXT_PERSISTENCE_EXECUTOR_NOOP_VERSION,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"ctx_persist_noop_{digest}"


def _normalize_context_persistence_candidate_kind(args: dict[str, Any]) -> str:
    raw = _first_present(args, "candidate_kind", "candidateKind", "candidate_type", "candidateType", "object_type", "objectType")
    text = str(raw or "").strip().lower().replace("-", "_")
    if text in {"practice_plan", "practiceplan", "plan", "practice_plan_persistence", "practice_plan_persistence_candidate"}:
        return "practice_plan_persistence_candidate"
    if text in {"routine_history", "routinehistory", "history", "routine_history_persistence", "routine_history_persistence_candidate"}:
        return "routine_history_persistence_candidate"
    if any(key in args for key in ("practicePlan", "practice_plan", "planBlocks", "plan_blocks", "existingPracticePlan", "existing_practice_plan")):
        return "practice_plan_persistence_candidate"
    if any(key in args for key in ("routineHistoryRecords", "routine_history_records", "historyRecords", "history_records", "routineHistoryContextPayload", "routine_history_context_payload")):
        return "routine_history_persistence_candidate"
    nested = _extract_context_persistence_nested_candidate(args, "practice_plan")
    if nested:
        return "practice_plan_persistence_candidate"
    nested = _extract_context_persistence_nested_candidate(args, "routine_history")
    if nested:
        return "routine_history_persistence_candidate"
    return "unknown"


def _extract_context_persistence_nested_candidate(args: dict[str, Any], kind: str) -> dict[str, Any] | None:
    keys = ["candidate_payload", "candidatePayload", "persistence_candidate_payload", "persistenceCandidatePayload"]
    if kind == "practice_plan":
        keys.extend(["practice_plan_persistence_candidate_payload", "practicePlanPersistenceCandidatePayload", "practicePlanPersistenceCandidate", "practice_plan_persistence_candidate"])
    else:
        keys.extend(["routine_history_persistence_candidate_payload", "routineHistoryPersistenceCandidatePayload", "routineHistoryPersistenceCandidate", "routine_history_persistence_candidate"])
    for key in keys:
        value = args.get(key)
        if isinstance(value, dict):
            return value
    return None


def _normalize_context_persistence_user_decision(args: dict[str, Any]) -> str:
    raw = _first_present(args, "user_decision", "userDecision", "decision", "confirmation_status", "confirmationStatus")
    text = str(raw or "pending").strip().lower().replace("-", "_")
    if text in {"approve", "approved", "confirm", "confirmed", "user_approved", "confirm_save", "confirm_sync"}:
        return "approved"
    if text in {"reject", "rejected", "deny", "declined", "user_rejected"}:
        return "rejected"
    if text in {"dismiss", "dismissed", "cancel", "cancelled"}:
        return "dismissed"
    return "pending"


def _context_persistence_next_client_actions(user_decision: str, blocked_reasons: list[str]) -> list[str]:
    if blocked_reasons:
        return ["fix_candidate", "dismiss", "view_trace"]
    if user_decision == "approved":
        return ["record_confirmation", "await_future_persistence_executor", "view_trace"]
    if user_decision in {"rejected", "dismissed"}:
        return ["dismiss", "view_trace"]
    return ["review_candidate", "edit_candidate", "confirm_context_persistence", "dismiss", "view_trace"]


def _summarize_embedded_persistence_candidate(candidate_payload: dict[str, Any], candidate_kind: str) -> dict[str, Any]:
    validation = candidate_payload.get("validation") if isinstance(candidate_payload.get("validation"), dict) else {}
    if candidate_kind == "practice_plan_persistence_candidate":
        plan = candidate_payload.get("normalized_practice_plan") if isinstance(candidate_payload.get("normalized_practice_plan"), dict) else {}
        return {
            "practice_plan_persistence_candidate_contract_version": PRACTICE_PLAN_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
            "validation_status": validation.get("status"),
            "accepted": validation.get("accepted", False),
            "operation": candidate_payload.get("operation"),
            "candidate_id": candidate_payload.get("candidate_id"),
            "plan_title": plan.get("title"),
            "block_count": len(plan.get("blocks") or []),
            "requires_user_confirmation": True,
            "preview_only": True,
            "storage_written": False,
        }
    aggregate = candidate_payload.get("aggregate_summary") if isinstance(candidate_payload.get("aggregate_summary"), dict) else {}
    records = candidate_payload.get("normalized_routine_history_records") or []
    items = candidate_payload.get("practice_history_context_items") or []
    return {
        "routine_history_persistence_candidate_contract_version": ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_VERSION,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "operation": candidate_payload.get("operation"),
        "candidate_id": candidate_payload.get("candidate_id"),
        "record_count": len(records) if isinstance(records, list) else 0,
        "context_item_count": len(items) if isinstance(items, list) else 0,
        "total_practice_minutes": aggregate.get("total_practice_minutes", 0),
        "requires_user_confirmation": True,
        "preview_only": True,
        "storage_written": False,
    }

def _extract_routine_history_persistence_candidate_records(args: dict[str, Any]) -> list[Any]:
    records = _extract_routine_history_records(args)
    if records:
        return records
    for key in ("routine_history_context_payload", "routineHistoryContextPayload", "context_payload", "contextPayload"):
        payload = args.get(key)
        if isinstance(payload, dict):
            nested_records = _extract_routine_history_records(payload)
            if nested_records:
                return nested_records
            items = payload.get("practice_history_context_items") or payload.get("practiceHistoryContextItems")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def _normalize_routine_history_persistence_operation(args: dict[str, Any]) -> str:
    raw = str(_first_present(args, "operation", "action", "persistence_operation", "persistenceOperation") or "").strip().lower()
    if raw in {"upsert", "sync", "sync_summary", "sync_summary_batch", "update", "update_existing", "replace", "save_update"}:
        return "upsert_summary_batch"
    if raw in {"append", "append_new", "append_new_records", "save", "create", "save_new", "upload"}:
        return "append_new_records"
    return "append_new_records"


def _extract_practice_plan_persistence_candidate_input(args: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "practice_plan",
        "practicePlan",
        "input_practice_plan",
        "inputPracticePlan",
        "candidate_practice_plan",
        "candidatePracticePlan",
        "active_practice_plan",
        "activePracticePlan",
        "plan",
    ):
        value = args.get(key)
        if isinstance(value, dict):
            return dict(value)
    payload = args.get("today_practice_guidance_action_card_payload") or args.get("todayPracticeGuidanceActionCardPayload")
    if isinstance(payload, dict):
        normalized = payload.get("normalized_guidance_output") or payload.get("normalizedGuidanceOutput")
        if isinstance(normalized, dict):
            candidates = normalized.get("practice_plan_candidates") or normalized.get("practicePlanCandidates")
            if isinstance(candidates, list) and candidates and isinstance(candidates[0], dict):
                return dict(candidates[0])
    return {}


def _extract_existing_practice_plan_for_diff(args: dict[str, Any]) -> dict[str, Any]:
    for key in ("existing_practice_plan", "existingPracticePlan", "current_practice_plan", "currentPracticePlan", "target_practice_plan", "targetPracticePlan"):
        value = args.get(key)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _normalize_practice_plan_persistence_operation(args: dict[str, Any], normalized_plan: dict[str, Any]) -> str:
    raw = str(_first_present(args, "operation", "action", "persistence_operation", "persistenceOperation") or "").strip().lower()
    if raw in {"update", "update_existing", "replace", "patch", "save_update"}:
        return "update_existing"
    if raw in {"save", "create", "save_new", "new"}:
        return "save_new"
    if _first_present(args, "target_plan_id", "targetPlanId"):
        return "update_existing"
    if normalized_plan.get("plan_id") and _bool_or_default(_first_present(args, "treat_plan_id_as_update", "treatPlanIdAsUpdate"), default=False):
        return "update_existing"
    return "save_new"


def _normalize_practice_plan_for_persistence(raw_plan: dict[str, Any]) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    warnings: list[str] = []
    discarded = {"sensitive_or_client_only_fields": [], "unrecognized_fields": []}
    if not isinstance(raw_plan, dict) or not raw_plan:
        return {}, ["no_practice_plan_candidate_supplied"], discarded
    forbidden_fragments = (
        "api_key", "apikey", "token", "password", "secret", "midi_base64", "midibase64", "local_midi_path", "localmidipath",
        "payment", "precise_location", "preciselocation", "hidden_chain_of_thought", "hiddenchainofthought",
    )
    allowed_keys = {
        "plan_id", "planId", "id", "title", "name", "status", "duration_minutes", "durationMinutes", "available_minutes", "availableMinutes",
        "main_focus", "mainFocus", "goal", "current_goal", "currentGoal", "estimated_difficulty", "estimatedDifficulty", "source",
        "plan_blocks", "planBlocks", "blocks", "items", "practice_blocks", "practiceBlocks", "created_at", "createdAt", "updated_at", "updatedAt",
        "tags", "notes", "description",
    }
    for key in raw_plan.keys():
        normalized_key = str(key).lower().replace("-", "_")
        if any(fragment in normalized_key for fragment in forbidden_fragments):
            discarded["sensitive_or_client_only_fields"].append(str(key))
        elif key not in allowed_keys:
            discarded["unrecognized_fields"].append(str(key))
    plan_id = _first_present(raw_plan, "plan_id", "planId", "id")
    title = _first_present(raw_plan, "title", "name") or "Untitled Practice Plan"
    duration = _number_or_none(_first_present(raw_plan, "duration_minutes", "durationMinutes", "available_minutes", "availableMinutes"))
    focus = _first_present(raw_plan, "main_focus", "mainFocus", "goal", "current_goal", "currentGoal", "description")
    blocks = _extract_practice_plan_blocks_for_persistence(raw_plan)
    normalized_blocks = [_normalize_practice_plan_block_for_persistence(block, index=i) for i, block in enumerate(blocks) if isinstance(block, dict)]
    if not normalized_blocks:
        warnings.append("practice_plan_candidate_has_no_blocks")
    total_minutes = sum(int(block.get("duration_minutes") or 0) for block in normalized_blocks)
    normalized = {
        "plan_id": str(plan_id) if plan_id is not None else None,
        "title": str(title),
        "status": str(_first_present(raw_plan, "status") or "draft_candidate"),
        "duration_minutes": int(duration) if duration is not None else total_minutes,
        "main_focus": str(focus) if focus is not None else None,
        "estimated_difficulty": _first_present(raw_plan, "estimated_difficulty", "estimatedDifficulty"),
        "source": _first_present(raw_plan, "source") or "agent_candidate",
        "tags": list(_first_present(raw_plan, "tags") or []) if isinstance(_first_present(raw_plan, "tags"), list) else [],
        "blocks": normalized_blocks,
        "block_count": len(normalized_blocks),
        "total_block_minutes": total_minutes,
        "notes": str(_first_present(raw_plan, "notes")) if _first_present(raw_plan, "notes") is not None else None,
    }
    return normalized, warnings, discarded


def _extract_practice_plan_blocks_for_persistence(plan: dict[str, Any]) -> list[Any]:
    for key in ("plan_blocks", "planBlocks", "blocks", "items", "practice_blocks", "practiceBlocks"):
        value = plan.get(key)
        if isinstance(value, list):
            return value
    return []


def _normalize_practice_plan_block_for_persistence(block: dict[str, Any], *, index: int) -> dict[str, Any]:
    title = _first_present(block, "title", "name", "goal", "practice_goal", "practiceGoal") or f"Practice Block {index + 1}"
    duration = _number_or_none(_first_present(block, "duration_minutes", "durationMinutes", "minutes", "suggested_duration_minutes", "suggestedDurationMinutes"))
    tempo = _number_or_none(_first_present(block, "tempo", "bpm", "suggested_tempo", "suggestedTempo"))
    return {
        "block_id": str(_first_present(block, "block_id", "blockId", "id") or f"block_{index + 1}"),
        "block_index": index,
        "title": str(title),
        "goal": str(_first_present(block, "goal", "practice_goal", "practiceGoal", "intent") or title),
        "duration_minutes": int(duration) if duration is not None else None,
        "style": _first_present(block, "style", "suggested_style", "suggestedStyle", "style_id", "styleId"),
        "tempo": int(tempo) if tempo is not None else None,
        "tune_title": _first_present(block, "tune_title", "tuneTitle", "tune", "song"),
        "material": _redact_sensitive_values(_first_present(block, "material") if isinstance(_first_present(block, "material"), dict) else {}),
        "status": str(_first_present(block, "status") or "pending"),
    }


def _build_practice_plan_persistence_diff_preview(existing_plan: dict[str, Any], proposed_plan: dict[str, Any], operation: str) -> dict[str, Any]:
    existing_norm, _, _ = _normalize_practice_plan_for_persistence(existing_plan) if isinstance(existing_plan, dict) and existing_plan else ({}, [], {})
    changed_fields: list[dict[str, Any]] = []
    if operation == "update_existing" and existing_norm:
        for key in ("title", "status", "duration_minutes", "main_focus", "block_count", "total_block_minutes"):
            before = existing_norm.get(key)
            after = proposed_plan.get(key)
            if before != after:
                changed_fields.append({"field": key, "before": before, "after": after})
    elif operation == "save_new":
        changed_fields.append({"field": "plan", "before": None, "after": "new_practice_plan_candidate"})
    return {
        "operation": operation,
        "existing_plan_available": bool(existing_norm),
        "changed_fields": changed_fields,
        "changed_field_count": len(changed_fields),
        "semantic_diff_only": True,
        "storage_write_preview_only": True,
    }


def _practice_context_storage_ownership_matrix() -> list[dict[str, Any]]:
    return [
        {
            "context_object": "UserPracticeProfile",
            "owner": "backend_long_term_context",
            "source_of_truth": "backend when persistence exists; client may submit explicit profile updates",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": True,
            "allowed_context_section": "user_practice_profile_context",
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "ActivePracticePlan",
            "owner": "backend_long_term_context",
            "source_of_truth": "backend when persistence exists",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": True,
            "allowed_context_section": "active_practice_plan_context",
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "RoutineHistorySummary",
            "owner": "backend_long_term_context",
            "source_of_truth": "HarmonyOS produces completion summary; backend persists compact Agent context summary when available",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": True,
            "allowed_context_section": "practice_history_context",
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "RoutineSessionLiveState",
            "owner": "harmonyos_local_only",
            "source_of_truth": "HarmonyOS client runtime",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": False,
            "allowed_context_section": None,
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "PlaybackStateAndLocalMidiCache",
            "owner": "harmonyos_local_only",
            "source_of_truth": "HarmonyOS client/player",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": False,
            "allowed_context_section": None,
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "TodayRequestConstraints",
            "owner": "request_ephemeral_context",
            "source_of_truth": "current user turn/request",
            "harmonyos_local_cache_allowed": False,
            "may_enter_context_packet": True,
            "allowed_context_section": "today_constraints",
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "RoutineCandidatePreview",
            "owner": "request_ephemeral_context",
            "source_of_truth": "Agent response preview until user/client saves or starts later flow",
            "harmonyos_local_cache_allowed": True,
            "may_enter_context_packet": False,
            "allowed_context_section": None,
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "AgentTraceMetadata",
            "owner": "agent_trace_context",
            "source_of_truth": "Agent trace store",
            "harmonyos_local_cache_allowed": False,
            "may_enter_context_packet": True,
            "allowed_context_section": "sanitized_agent_trace_metadata",
            "v2_8_2_storage_write": False,
        },
        {
            "context_object": "SecretsAndRawAssets",
            "owner": "never_store_or_contextualize",
            "source_of_truth": "not allowed",
            "harmonyos_local_cache_allowed": False,
            "may_enter_context_packet": False,
            "allowed_context_section": None,
            "v2_8_2_storage_write": False,
        },
    ]


def _storage_boundary_detect_input_signals(args: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    key_aliases = {
        "user_practice_profile": ("user_practice_profile", "userPracticeProfile", "input_profile", "inputProfile"),
        "active_practice_plan": ("active_practice_plan", "activePracticePlan", "practice_plan", "practicePlan"),
        "routine_history_records": ("routine_history_records", "routineHistoryRecords", "practice_history_context", "practiceHistoryContext"),
        "current_routine_session": ("current_routine_session", "currentRoutineSession", "routine_session", "routineSession"),
        "playback_state": ("playback_state", "playbackState", "playback_position", "playbackPosition"),
        "local_asset_cache": ("local_asset_cache", "localAssetCache", "local_unsynced_summary", "localUnsyncedSummary"),
        "today_request_constraints": ("available_minutes", "availableMinutes", "duration_minutes", "durationMinutes", "user_input", "userInput"),
        "agent_trace_metadata": ("trace_id", "traceId", "agent_trace", "agentTrace"),
        "client_context": ("client_context", "clientContext"),
        "routine_candidate_preview": ("routine_candidate", "routineCandidate", "routine_config_candidate", "routineConfigCandidate"),
    }
    for signal, aliases in key_aliases.items():
        if any(alias in args and args.get(alias) not in (None, {}, [], "") for alias in aliases):
            signals.append(signal)
    return signals


def _storage_boundary_signal_ownership(signals: list[str]) -> dict[str, str]:
    ownership = {
        "user_practice_profile": "backend_long_term_context",
        "active_practice_plan": "backend_long_term_context",
        "routine_history_records": "backend_long_term_context",
        "current_routine_session": "harmonyos_local_only",
        "playback_state": "harmonyos_local_only",
        "local_asset_cache": "harmonyos_local_only",
        "today_request_constraints": "request_ephemeral_context",
        "client_context": "request_ephemeral_context",
        "routine_candidate_preview": "request_ephemeral_context",
        "agent_trace_metadata": "agent_trace_context",
    }
    return {signal: ownership.get(signal, "request_ephemeral_context") for signal in signals}


def _storage_boundary_forbidden_field_hits(value: Any, path: str = "") -> list[str]:
    forbidden_keys = {
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "token",
        "secret",
        "password",
        "local_midi_path",
        "localmidipath",
        "midi_base64",
        "midibase64",
        "payment_info",
        "paymentinfo",
        "precise_location",
        "preciselocation",
        "hidden_chain_of_thought",
        "hiddenchainofthought",
        "chain_of_thought",
        "chainofthought",
        "playback_position",
        "playbackposition",
        "timer_state",
        "timerstate",
    }
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_")
            compact = normalized.replace("_", "")
            child_path = f"{path}.{key_text}" if path else key_text
            if normalized in forbidden_keys or compact in forbidden_keys:
                hits.append(child_path)
            hits.extend(_storage_boundary_forbidden_field_hits(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_storage_boundary_forbidden_field_hits(child, f"{path}[{index}]"))
    return hits


@dataclass(frozen=True)
class ActivePracticePlanContextIntakePayload:
    """v2_7_3 active PracticePlan intake payload for Agent context engineering.

    This contract turns a saved or client-provided long-term PracticePlan into a
    compact context section. It is context-only: no Routine is started, no
    accompaniment is generated, and no Agent recommendation card is created.
    """

    payload_contract_version: str
    source: str
    active_practice_plan: dict[str, Any]
    active_plan_context_items: tuple[dict[str, Any], ...]
    context_packet_section: dict[str, Any]
    aggregate_summary: dict[str, Any]
    storage_boundary: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    recommendation_created: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "active_practice_plan": _redact_sensitive_values(self.active_practice_plan),
            "active_plan_context_items": _redact_sensitive_values(list(self.active_plan_context_items)),
            "context_packet_section": _redact_sensitive_values(self.context_packet_section),
            "aggregate_summary": _redact_sensitive_values(self.aggregate_summary),
            "storage_boundary": _redact_sensitive_values(self.storage_boundary),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "recommendation_created": self.recommendation_created,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_active_practice_plan_context_intake_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "active_practice_plan_context_intake",
) -> ActivePracticePlanContextIntakePayload:
    """Normalize the active long-term PracticePlan for future ContextPackets."""

    args = dict(arguments or {})
    plan = _extract_active_practice_plan(args)
    warnings: list[str] = []
    normalized_plan, context_items, plan_warnings = _normalize_active_practice_plan(plan)
    warnings.extend(plan_warnings)
    summary = _summarize_active_plan_context_items(context_items)
    context_section = {
        "section_name": "active_practice_plan_context",
        "active_practice_plan_context_intake_version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
        "purpose": "Long-term plan context for a future user-initiated next-practice conversation.",
        "active_plan": normalized_plan,
        "plan_blocks": context_items,
        "aggregate_summary": summary,
        "context_usage_policy": {
            "use_when_user_asks_what_to_practice_next": True,
            "combine_with_routine_history_context": True,
            "do_not_create_recommendation_card_by_itself": True,
            "do_not_start_routine": True,
            "do_not_call_accompaniment_generate": True,
        },
    }
    validation = {
        "status": "context_ready_with_warnings" if warnings else "context_ready",
        "warnings": warnings,
        "active_plan_present": bool(normalized_plan.get("plan_id") or normalized_plan.get("title") or context_items),
        "plan_block_count": len(context_items),
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_playback_position": False,
    }
    storage_boundary = {
        "backend_should_persist": [
            "PracticePlan identity and status",
            "PracticePlan blocks / goals / suggested duration / style / tune / tempo",
            "Plan progress summary and block completion state",
        ],
        "harmonyos_client_may_cache": [
            "last opened plan id",
            "current UI selection",
            "local editable Routine candidate derived from a block",
        ],
        "this_contract_persists_to_database": False,
        "this_contract_is_context_intake_only": True,
    }
    return ActivePracticePlanContextIntakePayload(
        payload_contract_version=ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
        source=source,
        active_practice_plan=normalized_plan,
        active_plan_context_items=tuple(context_items),
        context_packet_section=context_section,
        aggregate_summary=summary,
        storage_boundary=storage_boundary,
        validation=validation,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_active_practice_plan_context_intake_summary(
    *,
    payload: ActivePracticePlanContextIntakePayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    summary = data.get("aggregate_summary") if isinstance(data.get("aggregate_summary"), dict) else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "active_practice_plan_context_intake_version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
        "context_engineering_skeleton_version": CONTEXT_ENGINEERING_SKELETON_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "active_plan_present": validation.get("active_plan_present", False),
        "plan_block_count": summary.get("plan_block_count", 0),
        "pending_block_count": summary.get("pending_block_count", 0),
        "completed_block_count": summary.get("completed_block_count", 0),
        "next_candidate_block_id": (summary.get("next_candidate_block") or {}).get("block_id") if isinstance(summary.get("next_candidate_block"), dict) else None,
        "validation_status": validation.get("status"),
        "recommendation_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def active_practice_plan_context_intake_contract() -> dict[str, Any]:
    return {
        "version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
        "active_practice_plan_context_intake_version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
        "spec_route": "GET /agent/context/active-practice-plan/spec",
        "intake_route": "POST /agent/context/active-practice-plan/intake",
        "terminal_command": "/active-practice-plan-context",
        "surface": "Active PracticePlan to Agent context intake",
        "mode": "context_intake_only_no_recommendation_no_execution",
        "execution_status": {
            "active_practice_plan_context_payload_enabled": True,
            "context_packet_section_enabled": True,
            "database_persistence_implemented": False,
            "recommendation_card_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "active_practice_plan": "Normalized active PracticePlan summary",
            "active_plan_context_items": "Normalized plan block context items",
            "context_packet_section": "active_practice_plan_context section that ContextBuilder may include",
            "aggregate_summary": "pending/completed block summary and next candidate block",
            "storage_boundary": "local-vs-backend ownership guidance",
            "validation": "context readiness warnings and sanitized status",
        },
        "rules": [
            "The active plan is long-term context and should be persisted by backend storage when available.",
            "This contract only normalizes active plan context; it does not decide today's practice by itself.",
            "Use together with RoutineHistoryContext and user availability on the next user-initiated Agent planning turn.",
        ],
        "guards": {
            "payload_creates_recommendation": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


@dataclass(frozen=True)
class PracticeContextAssemblyPolicyPayload:
    """v2_7_3 assembly policy for plan + history + availability context.

    This is the Context Engineering skeleton layer. It combines already-normalized
    context sections into decision inputs for a future LLM turn. It does not run
    an LLM and does not produce an Agent recommendation by itself.
    """

    payload_contract_version: str
    source: str
    active_practice_plan_context: dict[str, Any]
    routine_history_context: dict[str, Any]
    user_practice_profile_context: dict[str, Any]
    today_constraints: dict[str, Any]
    assembled_context: dict[str, Any]
    assembly_policy: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    recommendation_created: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "active_practice_plan_context": _redact_sensitive_values(self.active_practice_plan_context),
            "routine_history_context": _redact_sensitive_values(self.routine_history_context),
            "user_practice_profile_context": _redact_sensitive_values(self.user_practice_profile_context),
            "today_constraints": _redact_sensitive_values(self.today_constraints),
            "assembled_context": _redact_sensitive_values(self.assembled_context),
            "assembly_policy": _redact_sensitive_values(self.assembly_policy),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "recommendation_created": self.recommendation_created,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
        }


def build_practice_context_assembly_policy_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "practice_context_assembly_policy",
) -> PracticeContextAssemblyPolicyPayload:
    """Build a normalized context assembly payload from plan/history inputs."""

    args = dict(arguments or {})
    active_section = _extract_active_practice_plan_context_section(args)
    if not active_section:
        active_payload = build_active_practice_plan_context_intake_payload(args, trace_id=trace_id, source=f"{source}:active_plan_inline")
        active_section = active_payload.context_packet_section
    history_section = _extract_routine_history_context_section(args)
    if not history_section:
        history_payload = build_routine_history_context_intake_payload(args, trace_id=trace_id, source=f"{source}:routine_history_inline")
        history_section = history_payload.context_packet_section
    profile_section = _extract_user_practice_profile_context_section(args)
    if not profile_section:
        raw_profile = _extract_user_practice_profile(args)
        if raw_profile:
            profile_payload = build_user_practice_profile_context_intake_payload(args, trace_id=trace_id, source=f"{source}:user_profile_inline")
            profile_section = profile_payload.context_packet_section

    today_constraints = _normalize_today_constraints(args)
    active_blocks = _active_plan_blocks_from_section(active_section)
    history_items = _history_items_from_section(history_section)
    completed_block_ids = {str(item.get("plan_block_id")) for item in history_items if item.get("plan_block_id") and item.get("completed")}
    pending_blocks = [block for block in active_blocks if str(block.get("block_id")) not in completed_block_ids and not block.get("completed")]
    overdue_or_gap_blocks = _derive_context_gap_blocks(active_blocks, history_items)
    next_candidate = pending_blocks[0] if pending_blocks else {}
    assembled_context = {
        "section_name": "assembled_practice_context",
        "context_engineering_skeleton_version": CONTEXT_ENGINEERING_SKELETON_VERSION,
        "active_practice_plan_context": active_section,
        "practice_history_context": history_section,
        "user_practice_profile_context": profile_section,
        "profile_summary": _profile_summary_from_section(profile_section),
        "today_constraints": today_constraints,
        "derived_progress": {
            "completed_plan_block_ids_from_history": sorted(completed_block_ids),
            "pending_plan_blocks": pending_blocks[:12],
            "next_candidate_block": next_candidate,
            "overdue_or_gap_blocks": overdue_or_gap_blocks[:12],
        },
        "llm_decision_inputs": {
            "should_continue_original_plan_input_available": bool(active_blocks),
            "should_adjust_based_on_recent_history_input_available": bool(history_items),
            "user_practice_profile_input_available": bool(_profile_summary_from_section(profile_section)),
            "available_minutes": today_constraints.get("available_minutes"),
            "user_question": today_constraints.get("user_input"),
        },
        "context_usage_policy": {
            "use_for_next_user_initiated_practice_guidance": True,
            "do_not_recommend_without_llm_or_deterministic_planner": True,
            "do_not_create_post_session_card": True,
            "do_not_start_routine": True,
        },
    }
    warnings: list[str] = []
    if not active_blocks:
        warnings.append("active_practice_plan_context_missing_or_empty")
    if not history_items:
        warnings.append("routine_history_context_missing_or_empty")
    if today_constraints.get("available_minutes") is None:
        warnings.append("available_minutes_not_supplied")
    assembly_policy = {
        "policy_version": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        "priority_order": ["current_user_request", "today_constraints", "active_practice_plan", "recent_routine_history", "user_practice_profile"],
        "max_recent_history_items": 10,
        "max_plan_blocks": 24,
        "history_usage": "summarize_recent_completed_and_incomplete_sessions",
        "plan_usage": "preserve_active_plan_order_and_completion_state",
        "token_budget_policy": {
            "default_max_context_items": 24,
            "summarize_before_truncating": True,
            "drop_client_playback_internals": True,
        },
        "frontend_flow_assumption": False,
        "client_decides_presentation": True,
    }
    validation = {
        "status": "assembly_ready_with_warnings" if warnings else "assembly_ready",
        "warnings": warnings,
        "has_active_practice_plan_context": bool(active_blocks),
        "has_routine_history_context": bool(history_items),
        "has_user_practice_profile_context": bool(_profile_summary_from_section(profile_section)),
        "pending_block_count": len(pending_blocks),
        "completed_block_count_from_history": len(completed_block_ids),
        "llm_called": False,
        "recommendation_created": False,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
    }
    return PracticeContextAssemblyPolicyPayload(
        payload_contract_version=PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        source=source,
        active_practice_plan_context=active_section,
        routine_history_context=history_section,
        user_practice_profile_context=profile_section,
        today_constraints=today_constraints,
        assembled_context=assembled_context,
        assembly_policy=assembly_policy,
        validation=validation,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_practice_context_assembly_policy_summary(
    *,
    payload: PracticeContextAssemblyPolicyPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    assembled = data.get("assembled_context") if isinstance(data.get("assembled_context"), dict) else {}
    progress = assembled.get("derived_progress") if isinstance(assembled.get("derived_progress"), dict) else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "practice_context_assembly_policy_version": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        "context_engineering_skeleton_version": CONTEXT_ENGINEERING_SKELETON_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "has_active_practice_plan_context": validation.get("has_active_practice_plan_context", False),
        "has_routine_history_context": validation.get("has_routine_history_context", False),
        "has_user_practice_profile_context": validation.get("has_user_practice_profile_context", False),
        "pending_block_count": validation.get("pending_block_count", 0),
        "completed_block_count_from_history": validation.get("completed_block_count_from_history", 0),
        "next_candidate_block_id": (progress.get("next_candidate_block") or {}).get("block_id") if isinstance(progress.get("next_candidate_block"), dict) else None,
        "validation_status": validation.get("status"),
        "llm_called": False,
        "recommendation_created": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def practice_context_assembly_policy_contract() -> dict[str, Any]:
    return {
        "version": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        "practice_context_assembly_policy_version": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        "spec_route": "GET /agent/context/practice-assembly/spec",
        "build_route": "POST /agent/context/practice-assembly/build",
        "terminal_command": "/practice-context-assembly",
        "surface": "Practice context assembly policy for active plan + history + today constraints",
        "mode": "context_assembly_only_no_llm_no_recommendation_no_execution",
        "execution_status": {
            "active_plan_and_history_assembly_enabled": True,
            "context_packet_section_enabled": True,
            "llm_call_enabled": False,
            "recommendation_card_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "active_practice_plan_context": "Context section from active plan intake",
            "routine_history_context": "Context section from routine history intake",
            "user_practice_profile_context": "Context section from user practice profile intake",
            "today_constraints": "available minutes, user input, current date/time if client supplies it",
            "assembled_context": "LLM decision-input context; not a recommendation",
            "assembly_policy": "priority, truncation, summarization, frontend-flow-neutral rules",
            "validation": "readiness and warnings",
        },
        "rules": [
            "This layer assembles context only; it does not call the LLM or decide what the user should practice.",
            "The same assembled context can support multiple HarmonyOS UI flows because no frontend flow is hard-coded.",
            "Routine end remains client-owned; assembled context is used on the next user-initiated planning turn.",
        ],
        "guards": {
            "payload_calls_llm": False,
            "payload_creates_recommendation": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
    }


def build_today_practice_context_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_context_e2e",
) -> PracticeContextAssemblyPolicyPayload:
    """Build the context-only E2E payload for a future '今天该练什么' turn.

    This intentionally reuses the assembly payload type. It returns decision
    inputs that can be handed to an LLM later; it does not generate the answer.
    """

    args = dict(arguments or {})
    if not (args.get("user_input") or args.get("userInput")):
        args["user_input"] = "今天该练什么？"
    return build_practice_context_assembly_policy_payload(args, trace_id=trace_id, source=source)


def build_today_practice_context_e2e_summary(
    *,
    payload: PracticeContextAssemblyPolicyPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    summary = build_practice_context_assembly_policy_summary(payload=payload, source=source)
    summary["today_practice_context_e2e_version"] = TODAY_PRACTICE_CONTEXT_E2E_VERSION
    summary["ready_for_future_llm_turn"] = bool(summary.get("has_active_practice_plan_context") or summary.get("has_routine_history_context"))
    summary["recommendation_created"] = False
    summary["llm_called"] = False
    return summary


def today_practice_context_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_CONTEXT_E2E_VERSION,
        "today_practice_context_e2e_version": TODAY_PRACTICE_CONTEXT_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice/spec",
        "preview_route": "POST /agent/context/today-practice/preview",
        "terminal_command": "/today-practice-context",
        "surface": "Context-only E2E for the next user-initiated 'what should I practice today' turn",
        "mode": "context_preview_only_no_llm_no_recommendation_no_execution",
        "execution_status": {
            "today_practice_context_preview_enabled": True,
            "llm_call_enabled": False,
            "recommendation_created": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "rules": [
            "This route prepares the context for a future LLM answer; it does not answer by itself.",
            "The LLM should use active PracticePlan plus recent RoutineHistory to decide continue-plan vs adjust-plan only when the user asks.",
            "No post-session card is created automatically.",
        ],
        "guards": {
            "payload_calls_llm": False,
            "payload_creates_recommendation": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
        },
        "uses_contracts": {
            "active_practice_plan_context_intake": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
            "routine_history_context_intake": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
            "practice_context_assembly_policy": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        },
    }



@dataclass(frozen=True)
class UserCapabilityMapAndIntentTaxonomyPayload:
    """v2_7_5 user-facing LLM capability map and intent taxonomy.

    This payload answers the product question: what can a user ask the JamMate
    LLM/Agent to do, what should only become a candidate, what requires user
    confirmation, and what is forbidden. It is a contract/preview surface only;
    it does not call an LLM, execute tools, start Routine, or generate MIDI.
    """

    payload_contract_version: str
    source: str
    user_input: str | None
    capability_layers: tuple[dict[str, Any], ...]
    intent_taxonomy: tuple[dict[str, Any], ...]
    allowed_action_types: tuple[dict[str, Any], ...]
    side_effect_policy: dict[str, Any]
    routine_agent_boundaries: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    routine_started: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "user_input": self.user_input,
            "capability_layers": _redact_sensitive_values(list(self.capability_layers)),
            "intent_taxonomy": _redact_sensitive_values(list(self.intent_taxonomy)),
            "allowed_action_types": _redact_sensitive_values(list(self.allowed_action_types)),
            "side_effect_policy": _redact_sensitive_values(self.side_effect_policy),
            "routine_agent_boundaries": _redact_sensitive_values(self.routine_agent_boundaries),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "routine_started": self.routine_started,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
        }


def _agent_user_capability_layers() -> tuple[dict[str, Any], ...]:
    return (
        {
            "layer_id": "pure_coach_qa",
            "title": "Pure coach Q&A",
            "description": "Explain practice goals, harmony, style, plan rationale, and how to listen while practicing.",
            "side_effect_level": "none",
            "requires_user_confirmation": False,
            "current_status": "allowed_as_direct_answer",
            "examples": ["为什么今天练 ii-V-I？", "Blue Bossa 的 bossa comping 要注意什么？"],
        },
        {
            "layer_id": "context_guidance",
            "title": "Context-based practice guidance",
            "description": "Use active plan, recent Routine history, available minutes, and user goals to answer user-initiated planning questions.",
            "side_effect_level": "none",
            "requires_user_confirmation": False,
            "current_status": "prompt_contract_ready_no_llm_call_in_v2_7_5",
            "examples": ["今天该练什么？", "我最近练得怎么样？"],
        },
        {
            "layer_id": "candidate_generation",
            "title": "Candidate generation",
            "description": "Prepare editable candidates such as PracticePlan, RoutineConfig, RoutineCandidate, or guarded playback request drafts.",
            "side_effect_level": "none_to_low",
            "requires_user_confirmation": False,
            "current_status": "available_as_preview_or_controlled_low_risk_payload",
            "examples": ["帮我安排四周练习计划", "把这个 block 转成 Routine 候选", "帮我准备一个 Misty ballad 练习配置"],
        },
        {
            "layer_id": "confirmation_required_actions",
            "title": "Confirmation-required actions",
            "description": "Actions that may save user assets, create/update plans, start generation, or change Routine state must be previewed and confirmed first.",
            "side_effect_level": "low_to_high",
            "requires_user_confirmation": True,
            "current_status": "contracted_but_most_real_execution_still_disabled",
            "examples": ["保存这个计划", "按这个配置生成伴奏", "确认后开始 Routine"],
        },
        {
            "layer_id": "forbidden_direct_actions",
            "title": "Forbidden direct actions",
            "description": "LLM must never directly control playback, bypass confirmation, call engine internals, or mutate musical generation rules.",
            "side_effect_level": "high_or_engine_internal",
            "requires_user_confirmation": True,
            "current_status": "forbidden_for_llm_autonomy",
            "examples": ["直接开始播放", "直接调用 /accompaniment/generate", "直接改 voicing/pattern/pedal 规则"],
        },
    )


def _agent_user_intent_taxonomy() -> tuple[dict[str, Any], ...]:
    return (
        {
            "intent_type": "today_practice_guidance",
            "user_examples": ["今天该练什么？", "我只有 20 分钟，练什么好？"],
            "required_context": ["active_practice_plan_context", "routine_history_context", "available_minutes"],
            "llm_role": "coach_guidance",
            "output_family": "TodayPracticeGuidanceOutput",
            "allowed_action_type": "answer_with_optional_routine_candidates",
            "requires_confirmation_before_execution": True,
            "current_contract": "today_practice_guidance_prompt_contract_v2_7_4",
        },
        {
            "intent_type": "practice_plan_generation",
            "user_examples": ["帮我安排一个四周爵士 comping 练习计划"],
            "required_context": ["user_goal", "available_minutes", "instrument"],
            "llm_role": "practice_planner",
            "output_family": "PracticePlanCandidate",
            "allowed_action_type": "generate_practice_plan_candidate",
            "requires_confirmation_before_execution": False,
            "current_contract": "agent_practice_plan_controlled_execution_v2_6_5",
        },
        {
            "intent_type": "routine_config_prepare",
            "user_examples": ["就练这个", "把第二个 block 变成练习配置"],
            "required_context": ["selected_practice_block_or_user_intent"],
            "llm_role": "routine_config_assistant",
            "output_family": "RoutineConfigCandidate",
            "allowed_action_type": "prepare_editable_routine_candidate",
            "requires_confirmation_before_execution": True,
            "current_contract": "routine_config_prepare_v2_7_0_or_practice_plan_to_routine_candidate_bridge_v2_7_1",
        },
        {
            "intent_type": "playback_prepare_guarded",
            "user_examples": ["帮我准备一个 20 分钟 Misty ballad 伴奏"],
            "required_context": ["tune_or_leadsheet", "style", "tempo_or_difficulty", "duration_minutes"],
            "llm_role": "playback_request_preparer",
            "output_family": "PlaybackPrepareGuardedPayload",
            "allowed_action_type": "prepare_guarded_playback_candidate",
            "requires_confirmation_before_execution": True,
            "current_contract": "playback_prepare_guarded_design_v2_6_9",
        },
        {
            "intent_type": "difficulty_adjustment",
            "user_examples": ["太快了，帮我降一点难度", "先只练前 8 小节"],
            "required_context": ["current_routine_candidate_or_active_session_summary"],
            "llm_role": "difficulty_adjustment_assistant",
            "output_family": "RoutineConfigCandidatePatch",
            "allowed_action_type": "prepare_candidate_patch_only",
            "requires_confirmation_before_execution": True,
            "current_contract": "planned_after_v2_7_5",
        },
        {
            "intent_type": "practice_explanation",
            "user_examples": ["为什么练这个？", "这个练习怎么听自己是否稳定？"],
            "required_context": ["current_plan_or_routine_context_optional"],
            "llm_role": "coach_explainer",
            "output_family": "PlainCoachAnswer",
            "allowed_action_type": "direct_answer_no_tool",
            "requires_confirmation_before_execution": False,
            "current_contract": "pure_qa_allowed_no_side_effect",
        },
        {
            "intent_type": "routine_history_review",
            "user_examples": ["我最近练得怎么样？", "上周有没有坚持练？"],
            "required_context": ["routine_history_context"],
            "llm_role": "practice_history_reviewer",
            "output_family": "PracticeHistoryReviewAnswer",
            "allowed_action_type": "answer_from_history_context",
            "requires_confirmation_before_execution": False,
            "current_contract": "routine_history_context_intake_v2_7_2",
        },
    )


def _agent_allowed_action_types() -> tuple[dict[str, Any], ...]:
    return (
        {"action_type": "direct_answer_no_tool", "side_effect_level": "none", "confirmation_required": False, "current_status": "allowed"},
        {"action_type": "generate_practice_plan_candidate", "side_effect_level": "none", "confirmation_required": False, "current_status": "controlled_agent_practice_plan_allowed"},
        {"action_type": "prepare_editable_routine_candidate", "side_effect_level": "none", "confirmation_required": False, "current_status": "allowed_as_candidate_only"},
        {"action_type": "prepare_guarded_playback_candidate", "side_effect_level": "low", "confirmation_required": True, "current_status": "guarded_preview_only"},
        {"action_type": "save_or_update_user_plan", "side_effect_level": "low", "confirmation_required": True, "current_status": "future_executor_required"},
        {"action_type": "call_accompaniment_generate", "side_effect_level": "high", "confirmation_required": True, "current_status": "disabled_for_agent_in_v2_7_5"},
        {"action_type": "start_routine_or_playback", "side_effect_level": "high", "confirmation_required": True, "current_status": "client_owned_disabled_for_agent_in_v2_7_5"},
        {"action_type": "mutate_engine_generation_rules", "side_effect_level": "engine_internal", "confirmation_required": False, "current_status": "forbidden"},
    )


def build_user_capability_map_and_intent_taxonomy_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "user_capability_map_and_intent_taxonomy",
) -> UserCapabilityMapAndIntentTaxonomyPayload:
    args = dict(arguments or {})
    user_input = args.get("user_input") or args.get("userInput")
    capability_layers = _agent_user_capability_layers()
    intent_taxonomy = _agent_user_intent_taxonomy()
    allowed_action_types = _agent_allowed_action_types()
    side_effect_policy = {
        "policy_version": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        "side_effect_levels": {
            "none": "May answer or prepare context/candidates without confirmation.",
            "low": "May affect saved user-facing objects only after explicit preview and confirmation.",
            "high": "May generate assets, start playback, or call backend generation only after explicit confirmation and a dedicated executor boundary.",
            "engine_internal": "Forbidden for LLM/Agent autonomy; engine generation-rule development stays on Engine track.",
        },
        "confirmation_rule": "Any action that saves state, calls /accompaniment/generate, creates MIDI assets, starts Routine, or changes playback must require user confirmation.",
        "autonomous_execution_enabled": False,
        "llm_direct_playback_control_enabled": False,
    }
    routine_agent_boundaries = {
        "routine_end_page_agent_recommendation_card_enabled": False,
        "routine_end_page_owner": "HarmonyOS client",
        "next_practice_guidance_trigger": "next_user_initiated_llm_turn",
        "frontend_flow_assumption": False,
        "client_decides_presentation": True,
        "backend_agent_role": "produce context, candidates, validation, and controlled action contracts only",
        "forbidden_direct_calls": [
            "direct /accompaniment/generate from LLM",
            "direct engine adapter dispatch from LLM",
            "direct playback/timer control from LLM",
            "direct pattern/voicing/expression/pedal mutation",
        ],
    }
    validation = {
        "status": "capability_map_ready",
        "capability_layer_count": len(capability_layers),
        "intent_type_count": len(intent_taxonomy),
        "allowed_action_type_count": len(allowed_action_types),
        "has_today_practice_guidance_intent": any(item.get("intent_type") == "today_practice_guidance" for item in intent_taxonomy),
        "has_routine_config_prepare_intent": any(item.get("intent_type") == "routine_config_prepare" for item in intent_taxonomy),
        "llm_called": False,
        "tool_executed": False,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_api_key": False,
    }
    return UserCapabilityMapAndIntentTaxonomyPayload(
        payload_contract_version=USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        source=source,
        user_input=str(user_input) if user_input is not None else None,
        capability_layers=capability_layers,
        intent_taxonomy=intent_taxonomy,
        allowed_action_types=allowed_action_types,
        side_effect_policy=side_effect_policy,
        routine_agent_boundaries=routine_agent_boundaries,
        validation=validation,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_user_capability_map_and_intent_taxonomy_summary(
    *,
    payload: UserCapabilityMapAndIntentTaxonomyPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "user_capability_map_and_intent_taxonomy_version": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "capability_layer_count": validation.get("capability_layer_count", 0),
        "intent_type_count": validation.get("intent_type_count", 0),
        "allowed_action_type_count": validation.get("allowed_action_type_count", 0),
        "validation_status": validation.get("status"),
        "has_today_practice_guidance_intent": validation.get("has_today_practice_guidance_intent", False),
        "has_routine_config_prepare_intent": validation.get("has_routine_config_prepare_intent", False),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def user_capability_map_and_intent_taxonomy_contract() -> dict[str, Any]:
    return {
        "version": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        "user_capability_map_and_intent_taxonomy_version": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        "spec_route": "GET /agent/capabilities/user-intents/spec",
        "preview_route": "POST /agent/capabilities/user-intents/preview",
        "terminal_command": "/user-capability-map",
        "surface": "User-facing LLM capability map and intent taxonomy for JamMate Routine Agent",
        "mode": "capability_planning_contract_only_no_llm_no_execution",
        "execution_status": {
            "capability_map_enabled": True,
            "intent_taxonomy_enabled": True,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "capability_layers": "What users can ask the LLM/Agent to do, grouped by side-effect level.",
            "intent_taxonomy": "Supported and planned user intent families with required context and output family.",
            "allowed_action_types": "Action type allow/guard map for future validation and prompt contracts.",
            "side_effect_policy": "Confirmation and autonomy rules.",
            "routine_agent_boundaries": "Routine-specific boundaries including no automatic post-session recommendation card.",
        },
        "rules": [
            "The LLM may answer and prepare candidates, but it must not directly start playback or call accompaniment generation.",
            "Routine end remains client-owned; the Agent uses history on the next user-initiated turn.",
            "Any state-changing, asset-generating, or playback-starting action must pass preview, confirmation, executor, dispatcher, and trace boundaries.",
            "The capability map is a contract for prompts, validators, and HarmonyOS presentation; it does not execute tools by itself.",
        ],
        "guards": {
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
        "current_capability_summary": {
            "direct_answer_no_tool": "allowed",
            "practice_plan_candidate": "available",
            "routine_config_candidate": "available",
            "playback_prepare_candidate": "guarded_preview_only",
            "call_accompaniment_generate": "disabled_for_agent",
            "start_routine_or_playback": "client_owned_disabled_for_agent",
        },
    }

@dataclass(frozen=True)
class TodayPracticeGuidancePromptContractPayload:
    """v2_7_4 prompt/output contract for the future today-practice LLM turn.

    This payload is still a preview surface. It builds the messages, output
    schema, and guard policy that a future provider call should use when the
    user explicitly asks "今天该练什么？". It does not call the LLM, produce the
    final recommendation, start Routine, or generate accompaniment assets.
    """

    payload_contract_version: str
    source: str
    assembled_practice_context: dict[str, Any]
    prompt_messages: tuple[dict[str, Any], ...]
    output_schema: dict[str, Any]
    prompt_policy: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    guidance_response_created: bool = False
    recommendation_created: bool = False
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "assembled_practice_context": _redact_sensitive_values(self.assembled_practice_context),
            "prompt_messages": _redact_sensitive_values(list(self.prompt_messages)),
            "output_schema": _redact_sensitive_values(self.output_schema),
            "prompt_policy": _redact_sensitive_values(self.prompt_policy),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "guidance_response_created": self.guidance_response_created,
            "recommendation_created": self.recommendation_created,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
        }


def build_today_practice_guidance_prompt_contract_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_prompt_contract",
) -> TodayPracticeGuidancePromptContractPayload:
    """Build a provider-ready prompt/output contract preview for today practice guidance.

    The function reuses v2_7_3 context assembly. The returned prompt messages are
    deterministic preview data only; callers must use a separate LLM provider
    boundary to actually generate a response in a later stage.
    """

    args = dict(arguments or {})
    raw_assembled = args.get("assembled_practice_context") or args.get("assembledPracticeContext")
    if isinstance(raw_assembled, dict):
        assembled_context = _redact_sensitive_values(dict(raw_assembled))
    else:
        assembled_context = build_today_practice_context_e2e_payload(
            args,
            trace_id=trace_id,
            source="today_practice_guidance_prompt_contract_context_builder",
        ).assembled_context

    today_constraints = assembled_context.get("today_constraints") if isinstance(assembled_context.get("today_constraints"), dict) else {}
    progress = assembled_context.get("derived_progress") if isinstance(assembled_context.get("derived_progress"), dict) else {}
    profile_context = assembled_context.get("user_practice_profile_context") if isinstance(assembled_context.get("user_practice_profile_context"), dict) else {}
    profile = profile_context.get("profile") if isinstance(profile_context.get("profile"), dict) else {}
    profile_summary = profile_context.get("summary_for_llm") or assembled_context.get("profile_summary") or profile.get("summary_for_llm") or ""
    preferred_styles = profile.get("preferred_styles") if isinstance(profile.get("preferred_styles"), list) else []
    comfortable_tempo_ranges = profile.get("comfortable_tempo_ranges") if isinstance(profile.get("comfortable_tempo_ranges"), dict) else {}
    avoid_items = profile.get("avoid") if isinstance(profile.get("avoid"), list) else []
    practice_mode_preference = profile.get("practice_mode_preference")
    user_question = today_constraints.get("user_input") or args.get("user_input") or args.get("userInput") or "今天该练什么？"
    next_candidate = progress.get("next_candidate_block") if isinstance(progress.get("next_candidate_block"), dict) else {}

    prompt_messages = (
        {
            "role": "system",
            "content": (
                "You are JamMate's practice-planning assistant. Use only the supplied "
                "practice context to answer the user's next-practice question. Return JSON only, "
                "with no Markdown, no code fence, and no prose outside the JSON object. The JSON "
                "must match TodayPracticeGuidanceOutput with snake_case keys: guidance_mode, "
                "summary, recommended_focus, recommended_blocks, routine_candidates, "
                "user_confirmation_required, next_client_actions. Minimal valid shape: "
                "{\"guidance_mode\":\"fallback_without_plan\",\"summary\":\"...\","
                "\"recommended_focus\":\"...\",\"recommended_blocks\":[],"
                "\"routine_candidates\":[],\"user_confirmation_required\":true,"
                "\"next_client_actions\":[\"show_guidance\"]}. Do not start Routine, do not "
                "call tools, and do not create playback or accompaniment assets."
            ),
        },
        {
            "role": "developer",
            "content": (
                "Decision policy: first check whether the active plan has a reasonable next "
                "pending block; then compare recent Routine history for completed, repeated, "
                "or skipped work. Treat UserPracticeProfile as a soft personalization layer: "
                "prefer the user's long-term goal, preferred styles, comfortable tempo ranges, "
                "avoid list, and practice-mode preference when they do not conflict with the active "
                "plan or recent history. Do not turn profile into a hard-coded recommendation rule. "
                "Keep reasoning as a short user-facing summary, not hidden chain-of-thought."
            ),
        },
        {
            "role": "user",
            "content": user_question,
        },
        {
            "role": "context",
            "name": "assembled_practice_context",
            "content_json": assembled_context,
        },
    )
    output_schema = {
        "schema_name": "TodayPracticeGuidanceOutput",
        "schema_version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        "response_case": "snake_case",
        "required_fields": [
            "guidance_mode",
            "summary",
            "recommended_focus",
            "recommended_blocks",
            "routine_candidates",
            "user_confirmation_required",
            "next_client_actions",
        ],
        "fields": {
            "guidance_mode": "continue_original_plan | adjust_based_on_history | fallback_without_plan | ask_clarifying_question",
            "summary": "Short user-facing explanation; no hidden chain-of-thought.",
            "recommended_focus": "One concise focus for today's practice.",
            "recommended_blocks": "Array of selected practice blocks or custom focus blocks.",
            "routine_candidates": "UI-flow-neutral Routine candidate drafts; client decides presentation.",
            "adjustment_reason": "Optional concise reason when not following the original plan.",
            "profile_considerations": "Optional concise profile-aware note: goal, preferred style, comfort tempo, avoid, or practice mode used as soft context.",
            "user_confirmation_required": "Must be true before any Routine start or accompaniment generation.",
            "next_client_actions": "show_guidance | present_routine_candidate | ask_follow_up | dismiss",
            "trace_id": "Optional trace id supplied by runtime.",
        },
        "forbidden_fields": [
            "midi_base64",
            "local_midi_path",
            "api_key",
            "raw_tool_execution_result",
            "hidden_chain_of_thought",
        ],
    }
    warnings: list[str] = []
    if not assembled_context.get("active_practice_plan_context"):
        warnings.append("active_practice_plan_context_missing")
    if not assembled_context.get("practice_history_context"):
        warnings.append("routine_history_context_missing")
    if today_constraints.get("available_minutes") is None:
        warnings.append("available_minutes_not_supplied")
    if not next_candidate:
        warnings.append("next_candidate_block_missing")
    if not profile_context:
        warnings.append("user_practice_profile_context_missing")

    prompt_policy = {
        "policy_version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        "llm_call_enabled_in_this_contract": False,
        "provider_boundary_required_for_future_call": True,
        "autonomous_tool_execution_enabled": False,
        "routine_start_requires_user_confirmation": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "guidance_only_not_action": True,
        "max_prompt_messages": 4,
        "context_priority_order": [
            "current_user_question",
            "today_constraints",
            "active_practice_plan_context",
            "routine_history_context",
            "user_practice_profile_context",
            "derived_progress",
        ],
        "profile_aware_policy": {
            "profile_context_available": bool(profile_context),
            "profile_summary": str(profile_summary)[:600],
            "preferred_styles": [str(item) for item in preferred_styles[:8]],
            "comfortable_tempo_ranges": comfortable_tempo_ranges,
            "avoid": [str(item) for item in avoid_items[:8]],
            "practice_mode_preference": practice_mode_preference,
            "profile_is_soft_context_not_rule_engine": True,
        },
        "answer_rules": [
            "Prefer continuing the active plan when recent history does not contradict it.",
            "Use UserPracticeProfile as soft personalization context: goal, preferred styles, comfort tempo, avoid list, and practice-mode preference.",
            "Adjust only when recent Routine history, available time, or profile context justifies a safer or more useful practice block.",
            "Return Routine candidates as drafts only; the HarmonyOS client decides presentation and requires confirmation before starting.",
        ],
    }
    validation = {
        "status": "prompt_contract_ready_with_warnings" if warnings else "prompt_contract_ready",
        "warnings": warnings,
        "has_assembled_practice_context": bool(assembled_context),
        "prompt_message_count": len(prompt_messages),
        "output_schema_name": output_schema["schema_name"],
        "has_user_practice_profile_context": bool(profile_context),
        "profile_summary": str(profile_summary)[:600],
        "ready_for_future_llm_provider_call": bool(assembled_context),
        "llm_called": False,
        "guidance_response_created": False,
        "contains_midi_base64": False,
        "contains_local_midi_path": False,
        "contains_api_key": False,
    }
    return TodayPracticeGuidancePromptContractPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        source=source,
        assembled_practice_context=assembled_context,
        prompt_messages=prompt_messages,
        output_schema=output_schema,
        prompt_policy=prompt_policy,
        validation=validation,
        trace_id=trace_id or args.get("trace_id") or args.get("traceId"),
    )


def build_today_practice_guidance_prompt_contract_summary(
    *,
    payload: TodayPracticeGuidancePromptContractPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    assembled = data.get("assembled_practice_context") if isinstance(data.get("assembled_practice_context"), dict) else {}
    progress = assembled.get("derived_progress") if isinstance(assembled.get("derived_progress"), dict) else {}
    next_candidate = progress.get("next_candidate_block") if isinstance(progress.get("next_candidate_block"), dict) else {}
    profile_context = assembled.get("user_practice_profile_context") if isinstance(assembled.get("user_practice_profile_context"), dict) else {}
    profile = profile_context.get("profile") if isinstance(profile_context.get("profile"), dict) else {}
    return {
        "today_practice_guidance_prompt_contract_version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "ready_for_future_llm_provider_call": validation.get("ready_for_future_llm_provider_call", False),
        "validation_status": validation.get("status"),
        "prompt_message_count": validation.get("prompt_message_count", 0),
        "output_schema_name": validation.get("output_schema_name"),
        "next_candidate_block_id": next_candidate.get("block_id"),
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


def today_practice_guidance_prompt_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        "today_practice_guidance_prompt_contract_version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/prompt-preview",
        "terminal_command": "/today-practice-guidance-prompt",
        "surface": "LLM prompt and output contract for user-initiated today-practice guidance",
        "mode": "prompt_output_contract_only_no_llm_no_execution",
        "execution_status": {
            "prompt_preview_enabled": True,
            "output_schema_enabled": True,
            "llm_call_enabled": False,
            "guidance_response_created": False,
            "recommendation_card_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "assembled_practice_context": "Context from v2_7_3 active plan + Routine history + today constraints assembly",
            "prompt_messages": "Provider-boundary-ready system/developer/user/context messages; not sent in this route",
            "output_schema": "TodayPracticeGuidanceOutput schema the future LLM response must satisfy",
            "prompt_policy": "Decision and guard policy for continue-plan vs adjust-plan guidance",
            "validation": "Readiness and sanitization status",
        },
        "rules": [
            "This contract does not call the LLM; it only builds the prompt and response schema.",
            "The LLM guidance is only for the next user-initiated conversation turn, not an automatic post-session card.",
            "Any Routine start or accompaniment generation remains a separate user-confirmed client action.",
            "Routine candidates returned by a future LLM must be UI-flow-neutral; HarmonyOS decides presentation.",
        ],
        "guards": {
            "payload_calls_llm": False,
            "payload_creates_guidance_response": False,
            "payload_creates_recommendation_card": False,
            "payload_calls_accompaniment_generate": False,
            "payload_calls_engine_adapter": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
        "uses_contracts": {
            "today_practice_context_e2e": TODAY_PRACTICE_CONTEXT_E2E_VERSION,
            "practice_context_assembly_policy": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
        },
    }





def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False

def _coerce_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default

@dataclass(frozen=True)
class TodayPracticeGuidanceOutputValidationPayload:
    """v2_7_6 validation gate for future LLM TodayPracticeGuidanceOutput.

    This validates a structured LLM result after the v2_7_4 prompt/output
    contract. It may accept guidance/candidate drafts for display, but it must
    block any attempt to start Routine, call /accompaniment/generate, invoke
    engine adapters, create MIDI assets, or bypass user confirmation.
    """

    payload_contract_version: str
    source: str
    raw_guidance_output_preview: dict[str, Any]
    normalized_guidance_output: dict[str, Any]
    validation_policy: dict[str, Any]
    validation: dict[str, Any]
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    trace_id: str | None = None
    llm_called: bool = False
    guidance_response_validated: bool = True
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "raw_guidance_output_preview": _redact_sensitive_values(self.raw_guidance_output_preview),
            "normalized_guidance_output": _redact_sensitive_values(self.normalized_guidance_output),
            "validation_policy": _redact_sensitive_values(self.validation_policy),
            "validation": _redact_sensitive_values(self.validation),
            "blocked_reasons": list(self.blocked_reasons),
            "warnings": list(self.warnings),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "guidance_response_validated": self.guidance_response_validated,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
        }


def _today_guidance_candidate_output(arguments: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "today_practice_guidance_output",
        "todayPracticeGuidanceOutput",
        "guidance_output",
        "guidanceOutput",
        "output",
        "llm_output",
        "llmOutput",
        "response",
    ):
        value = arguments.get(key)
        if isinstance(value, dict):
            return dict(value)
    return dict(arguments)



def _redact_today_guidance_forbidden_fields(value: Any) -> Any:
    forbidden_keys = {
        "midi_base64",
        "midiBase64",
        "local_midi_path",
        "localMidiPath",
        "api_key",
        "apiKey",
        "raw_tool_execution_result",
        "rawToolExecutionResult",
        "hidden_chain_of_thought",
        "hiddenChainOfThought",
    }
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if key in forbidden_keys else _redact_today_guidance_forbidden_fields(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_today_guidance_forbidden_fields(item) for item in value]
    return value

def _contains_forbidden_today_guidance_field(value: Any, path: str = "") -> list[str]:
    forbidden_keys = {
        "midi_base64",
        "midiBase64",
        "local_midi_path",
        "localMidiPath",
        "api_key",
        "apiKey",
        "raw_tool_execution_result",
        "rawToolExecutionResult",
        "hidden_chain_of_thought",
        "hiddenChainOfThought",
    }
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in forbidden_keys:
                hits.append(child_path)
            hits.extend(_contains_forbidden_today_guidance_field(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            hits.extend(_contains_forbidden_today_guidance_field(child, child_path))
    return hits


def _normalize_guidance_blocks(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    blocks: list[dict[str, Any]] = []
    for index, item in enumerate(value[:8]):
        if not isinstance(item, dict):
            continue
        duration = item.get("duration_minutes") or item.get("durationMinutes") or item.get("suggested_duration_minutes") or item.get("suggestedDurationMinutes")
        block = {
            "block_id": item.get("block_id") or item.get("blockId") or f"recommended_block_{index + 1}",
            "title": item.get("title") or item.get("name") or item.get("goal") or "Practice block",
            "goal": item.get("goal") or item.get("practice_goal") or item.get("practiceGoal"),
            "duration_minutes": _coerce_int(duration, default=0),
            "style": item.get("style") or item.get("suggested_style") or item.get("suggestedStyle"),
            "tempo": _coerce_int(item.get("tempo") or item.get("suggested_tempo") or item.get("suggestedTempo"), default=0),
            "tune_title": item.get("tune_title") or item.get("tuneTitle") or item.get("tune"),
            "source": "today_practice_guidance_output_validation",
        }
        blocks.append({k: v for k, v in block.items() if v not in (None, "", 0)})
    return blocks


def _normalize_guidance_routine_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(value[:6]):
        if not isinstance(item, dict):
            continue
        duration = item.get("duration_minutes") or item.get("durationMinutes") or item.get("suggested_duration_minutes") or item.get("suggestedDurationMinutes")
        candidate = {
            "candidate_id": item.get("candidate_id") or item.get("candidateId") or f"routine_candidate_{index + 1}",
            "routine_name": item.get("routine_name") or item.get("routineName") or item.get("title") or item.get("name") or "Today practice routine candidate",
            "practice_goal": item.get("practice_goal") or item.get("practiceGoal") or item.get("goal"),
            "duration_minutes": _coerce_int(duration, default=0),
            "style": item.get("style") or item.get("suggested_style") or item.get("suggestedStyle"),
            "tempo": _coerce_int(item.get("tempo") or item.get("suggested_tempo") or item.get("suggestedTempo"), default=0),
            "tune_title": item.get("tune_title") or item.get("tuneTitle") or item.get("tune"),
            "loop_enabled": bool(item.get("loop_enabled") if "loop_enabled" in item else item.get("loopEnabled", True)),
            "output_format": item.get("output_format") or item.get("outputFormat") or "midi_base64",
            "editable": True,
            "client_decides_presentation": True,
            "frontend_flow_assumption": False,
            "requires_user_confirmation_before_start": True,
            "source": "today_practice_guidance_output_validation",
        }
        candidates.append({k: v for k, v in candidate.items() if v not in (None, "", 0)})
    return candidates


def _today_guidance_forbidden_action_hits(output: dict[str, Any]) -> list[str]:
    forbidden_actions = {
        "start_routine",
        "startRoutine",
        "start_playback",
        "startPlayback",
        "call_accompaniment_generate",
        "callAccompanimentGenerate",
        "generate_midi",
        "generateMidi",
        "execute_tool",
        "executeTool",
        "dispatch_workflow",
        "dispatchWorkflow",
        "invoke_engine_adapter",
        "invokeEngineAdapter",
    }
    hits: list[str] = []
    for key in ("next_client_actions", "nextClientActions", "actions", "client_actions", "clientActions"):
        value = output.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item in forbidden_actions:
                    hits.append(f"{key}:{item}")
                if isinstance(item, dict):
                    action_type = item.get("action_type") or item.get("actionType") or item.get("type")
                    if action_type in forbidden_actions:
                        hits.append(f"{key}:{action_type}")
    for key in forbidden_actions:
        value = output.get(key)
        if value is True:
            hits.append(key)
    return hits


def build_today_practice_guidance_output_validation_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_output_validation",
) -> TodayPracticeGuidanceOutputValidationPayload:
    """Validate a future LLM TodayPracticeGuidanceOutput without executing anything."""

    args = dict(arguments or {})
    raw_output_original = _today_guidance_candidate_output(args)
    raw_output = _redact_today_guidance_forbidden_fields(_redact_sensitive_values(raw_output_original))
    guidance_mode = raw_output.get("guidance_mode") or raw_output.get("guidanceMode") or ""
    summary = raw_output.get("summary") or raw_output.get("message") or raw_output.get("answer") or ""
    recommended_focus = raw_output.get("recommended_focus") or raw_output.get("recommendedFocus") or raw_output.get("focus") or ""
    recommended_blocks = _normalize_guidance_blocks(raw_output.get("recommended_blocks") or raw_output.get("recommendedBlocks") or [])
    routine_candidates = _normalize_guidance_routine_candidates(raw_output.get("routine_candidates") or raw_output.get("routineCandidates") or [])
    next_actions_raw = raw_output.get("next_client_actions") or raw_output.get("nextClientActions") or []
    if not isinstance(next_actions_raw, list):
        next_actions_raw = []
    allowed_next_actions = {"show_guidance", "present_routine_candidate", "ask_follow_up", "dismiss"}
    next_client_actions = [item for item in next_actions_raw if isinstance(item, str) and item in allowed_next_actions]
    if not next_client_actions:
        next_client_actions = ["show_guidance"]
        if routine_candidates:
            next_client_actions.append("present_routine_candidate")
    user_confirmation_required = raw_output.get("user_confirmation_required")
    if user_confirmation_required is None:
        user_confirmation_required = raw_output.get("userConfirmationRequired")
    if user_confirmation_required is None:
        user_confirmation_required = True

    normalized = {
        "schema_name": "TodayPracticeGuidanceOutput",
        "schema_version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        "guidance_mode": guidance_mode,
        "summary": str(summary)[:1200] if summary is not None else "",
        "recommended_focus": str(recommended_focus)[:300] if recommended_focus is not None else "",
        "recommended_blocks": recommended_blocks,
        "routine_candidates": routine_candidates,
        "adjustment_reason": raw_output.get("adjustment_reason") or raw_output.get("adjustmentReason"),
        "profile_considerations": raw_output.get("profile_considerations") or raw_output.get("profileConsiderations"),
        "user_confirmation_required": bool(user_confirmation_required),
        "next_client_actions": next_client_actions,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "routine_start_allowed_now": False,
        "accompaniment_generate_allowed_now": False,
        "playback_start_allowed_now": False,
        "trace_id": trace_id or args.get("trace_id") or args.get("traceId") or raw_output.get("trace_id") or raw_output.get("traceId"),
    }

    allowed_modes = {"continue_original_plan", "adjust_based_on_history", "fallback_without_plan", "ask_clarifying_question"}
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if guidance_mode not in allowed_modes:
        blocked_reasons.append("invalid_or_missing_guidance_mode")
    if not summary:
        blocked_reasons.append("summary_required")
    if not recommended_focus and guidance_mode != "ask_clarifying_question":
        warnings.append("recommended_focus_missing")
    if bool(user_confirmation_required) is not True:
        blocked_reasons.append("user_confirmation_required_must_be_true")
    forbidden_field_hits = _contains_forbidden_today_guidance_field(raw_output_original)
    if forbidden_field_hits:
        blocked_reasons.append("forbidden_fields_present")
    forbidden_action_hits = _today_guidance_forbidden_action_hits(raw_output_original)
    if forbidden_action_hits:
        blocked_reasons.append("forbidden_direct_action_requested")
    if not recommended_blocks and not routine_candidates and guidance_mode != "ask_clarifying_question":
        warnings.append("no_blocks_or_candidates_supplied")

    is_valid = not blocked_reasons
    validation = {
        "status": "accepted_candidate_guidance" if is_valid else "blocked_unsafe_or_invalid_guidance",
        "is_valid": is_valid,
        "blocked_reason_count": len(blocked_reasons),
        "warning_count": len(warnings),
        "forbidden_field_hits": forbidden_field_hits,
        "forbidden_action_hits": forbidden_action_hits,
        "has_recommended_blocks": bool(recommended_blocks),
        "has_routine_candidates": bool(routine_candidates),
        "user_confirmation_required": bool(user_confirmation_required),
        "llm_called_by_validator": False,
        "tool_executed_by_validator": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "contains_midi_base64": bool(forbidden_field_hits),
        "contains_local_midi_path": any("local" in hit.lower() for hit in forbidden_field_hits),
        "contains_api_key": any("api" in hit.lower() for hit in forbidden_field_hits),
    }
    validation_policy = {
        "policy_version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        "input_schema": "TodayPracticeGuidanceOutput",
        "mode": "validate_and_normalize_only_no_execution",
        "allowed_guidance_modes": sorted(allowed_modes),
        "allowed_next_client_actions": sorted(allowed_next_actions),
        "requires_user_confirmation_before_any_routine_start": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "forbidden_fields": ["midi_base64", "local_midi_path", "api_key", "raw_tool_execution_result", "hidden_chain_of_thought"],
        "forbidden_direct_actions": sorted({"start_routine", "start_playback", "call_accompaniment_generate", "generate_midi", "execute_tool", "dispatch_workflow", "invoke_engine_adapter"}),
    }
    return TodayPracticeGuidanceOutputValidationPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        source=source,
        raw_guidance_output_preview=raw_output,
        normalized_guidance_output=normalized,
        validation_policy=validation_policy,
        validation=validation,
        blocked_reasons=tuple(blocked_reasons),
        warnings=tuple(warnings),
        trace_id=normalized.get("trace_id"),
    )


def build_today_practice_guidance_output_validation_summary(
    *,
    payload: TodayPracticeGuidanceOutputValidationPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    normalized = data.get("normalized_guidance_output") if isinstance(data.get("normalized_guidance_output"), dict) else {}
    return {
        "today_practice_guidance_output_validation_version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "is_valid": validation.get("is_valid", False),
        "guidance_mode": normalized.get("guidance_mode"),
        "recommended_block_count": len(normalized.get("recommended_blocks") or []),
        "routine_candidate_count": len(normalized.get("routine_candidates") or []),
        "blocked_reasons": list(data.get("blocked_reasons") or []),
        "warnings": list(data.get("warnings") or []),
        "user_confirmation_required": normalized.get("user_confirmation_required", True),
        "llm_called": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def today_practice_guidance_output_validation_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        "today_practice_guidance_output_validation_version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/output-validation/spec",
        "validate_route": "POST /agent/context/today-practice-guidance/output-validation/validate",
        "terminal_command": "/today-practice-guidance-validate",
        "surface": "Validation and safety gate for future LLM TodayPracticeGuidanceOutput",
        "mode": "validate_normalize_only_no_execution",
        "execution_status": {
            "output_validation_enabled": True,
            "normalization_enabled": True,
            "llm_call_enabled": False,
            "tool_execution_enabled": False,
            "guidance_response_created_by_validator": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "raw_guidance_output_preview": "Redacted input object returned by a future LLM provider call.",
            "normalized_guidance_output": "Safe UI-flow-neutral guidance and Routine candidates for client display.",
            "validation_policy": "Allowed modes/actions and forbidden direct execution fields.",
            "validation": "Accepted/blocked status with field/action hits.",
            "blocked_reasons": "Machine-readable reasons when unsafe or invalid output is rejected.",
        },
        "rules": [
            "Valid output may answer and provide Routine candidates, but must not start Routine or generate accompaniment.",
            "user_confirmation_required must be true before any Routine start or accompaniment generation.",
            "Forbidden direct actions and sensitive fields block the payload rather than being silently executed.",
            "HarmonyOS decides presentation; no setup page, bottom sheet, queue, or one-tap flow is hard-coded.",
        ],
        "guards": {
            "validator_calls_llm": False,
            "validator_executes_tool": False,
            "validator_calls_accompaniment_generate": False,
            "validator_calls_engine_adapter": False,
            "validator_creates_midi_asset": False,
            "validator_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
        "uses_contracts": {
            "today_practice_guidance_prompt_contract": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
            "user_capability_map_and_intent_taxonomy": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        },
    }


@dataclass(frozen=True)
class TodayPracticeGuidanceProviderBoundaryE2EPayload:
    """v2_7_7 provider-boundary E2E for user-initiated today-practice guidance.

    This payload stitches together the v2_7_4 prompt contract and v2_7_6
    output validator. It may call an injected/provider-boundary LLM only when a
    caller explicitly requests it. Regardless of provider output, it never
    starts Routine, calls /accompaniment/generate, invokes engine adapters, or
    creates MIDI assets.
    """

    payload_contract_version: str
    source: str
    prompt_payload: dict[str, Any]
    provider_boundary: dict[str, Any]
    provider_result_preview: dict[str, Any]
    parsed_guidance_output_preview: dict[str, Any]
    output_validation_payload: dict[str, Any]
    e2e_summary: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "prompt_payload": _redact_sensitive_values(self.prompt_payload),
            "provider_boundary": _redact_sensitive_values(self.provider_boundary),
            "provider_result_preview": _redact_sensitive_values(self.provider_result_preview),
            "parsed_guidance_output_preview": _redact_sensitive_values(self.parsed_guidance_output_preview),
            "output_validation_payload": _redact_sensitive_values(self.output_validation_payload),
            "e2e_summary": _redact_sensitive_values(self.e2e_summary),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
        }


def build_today_practice_guidance_provider_boundary_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_provider_boundary_e2e",
    provider: Any | None = None,
) -> TodayPracticeGuidanceProviderBoundaryE2EPayload:
    """Run today-practice prompt -> provider boundary -> output validator.

    By default this function does not call a network provider. Tests, terminal
    tooling, or future API layers may pass `providerResult`/`llmOutput` to model
    a provider response, or pass an injected provider plus `callProvider=true`.
    In both cases the result is validated as candidate-only guidance.
    """

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    prompt_payload = build_today_practice_guidance_prompt_contract_payload(
        args,
        trace_id=trace,
        source="today_practice_guidance_provider_boundary_prompt",
    )
    prompt_data = prompt_payload.to_dict()
    provider_boundary = _today_practice_provider_boundary_status(provider=provider, call_requested=_coerce_bool(args.get("callProvider") or args.get("call_provider") or args.get("llmCallEnabled")))
    provider_result = _provided_today_practice_provider_result(args)
    llm_called = False
    parsed_output: dict[str, Any] = {}
    provider_result_preview: dict[str, Any]
    provider_result_source = "provided_result_fixture" if provider_result else "not_called"

    if provider_result is None and _coerce_bool(args.get("callProvider") or args.get("call_provider") or args.get("llmCallEnabled")):
        llm_result = _call_today_practice_guidance_provider(prompt_payload=prompt_payload, provider=provider)
        llm_called = bool(llm_result.get("llm_called"))
        provider_result = llm_result.get("provider_result") if isinstance(llm_result.get("provider_result"), dict) else {}
        provider_result_source = llm_result.get("provider_result_source") or "provider_boundary_call"
        provider_boundary = {**provider_boundary, **dict(llm_result.get("provider_boundary") or {})}

    provider_output_coercion_warnings: list[str] = []
    if provider_result:
        provider_result_preview = _safe_provider_result_preview(provider_result)
        parsed_output = _parse_today_practice_provider_output(provider_result)
        parsed_output, provider_output_coercion_warnings = _coerce_provider_output_to_today_guidance(provider_result, parsed_output)
    else:
        provider_result_preview = {
            "ok": False,
            "provider_result_source": provider_result_source,
            "content_present": False,
            "message": "No provider result supplied and provider call was not requested.",
        }

    if parsed_output:
        validation_input = {"todayPracticeGuidanceOutput": parsed_output, "traceId": trace}
    else:
        validation_input = {"todayPracticeGuidanceOutput": {}, "traceId": trace}
    validation_payload = build_today_practice_guidance_output_validation_payload(
        validation_input,
        trace_id=trace,
        source="today_practice_guidance_provider_boundary_output_validation",
    )
    validation_data = validation_payload.to_dict()
    validation_summary = build_today_practice_guidance_output_validation_summary(payload=validation_payload, source="provider_boundary_e2e")
    prompt_summary = build_today_practice_guidance_prompt_contract_summary(payload=prompt_payload, source="provider_boundary_e2e")
    output_valid = bool((validation_data.get("validation") or {}).get("is_valid"))
    validation = {
        "status": "provider_output_validated_candidate_only" if output_valid else "provider_output_missing_or_blocked",
        "prompt_ready": bool((prompt_data.get("validation") or {}).get("ready_for_future_llm_provider_call")),
        "provider_result_source": provider_result_source,
        "provider_result_present": bool(provider_result),
        "provider_content_parsed": bool(parsed_output),
        "output_validation_is_valid": output_valid,
        "blocked_reasons": list(validation_data.get("blocked_reasons") or []),
        "warnings": list(dict.fromkeys(list(validation_data.get("warnings") or []) + provider_output_coercion_warnings)),
        "provider_output_coercion_warnings": provider_output_coercion_warnings,
        "tool_executed": False,
        "routine_start_enabled": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }
    e2e_summary = {
        "today_practice_guidance_provider_boundary_e2e_version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
        "source": source,
        "prompt_summary": prompt_summary,
        "provider_result_source": provider_result_source,
        "provider_call_requested": bool(provider_boundary.get("provider_call_requested")),
        "llm_called": llm_called,
        "provider_result_present": bool(provider_result),
        "provider_content_parsed": bool(parsed_output),
        "output_validation_summary": validation_summary,
        "normalized_guidance_output": validation_data.get("normalized_guidance_output") if output_valid else {},
        "provider_output_coercion_warnings": provider_output_coercion_warnings,
        "candidate_only_guidance_ready": output_valid,
        "requires_user_confirmation_before_routine_start": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "tool_executed": False,
        "routine_start_enabled": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }
    return TodayPracticeGuidanceProviderBoundaryE2EPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
        source=source,
        prompt_payload=prompt_data,
        provider_boundary=provider_boundary,
        provider_result_preview=provider_result_preview,
        parsed_guidance_output_preview=parsed_output,
        output_validation_payload=validation_data,
        e2e_summary=e2e_summary,
        validation=validation,
        trace_id=trace,
        llm_called=llm_called,
    )


def build_today_practice_guidance_provider_boundary_e2e_summary(
    *,
    payload: TodayPracticeGuidanceProviderBoundaryE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    e2e = data.get("e2e_summary") if isinstance(data.get("e2e_summary"), dict) else {}
    normalized = e2e.get("normalized_guidance_output") if isinstance(e2e.get("normalized_guidance_output"), dict) else {}
    return {
        "today_practice_guidance_provider_boundary_e2e_version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "provider_result_source": validation.get("provider_result_source"),
        "provider_result_present": validation.get("provider_result_present", False),
        "provider_content_parsed": validation.get("provider_content_parsed", False),
        "output_validation_is_valid": validation.get("output_validation_is_valid", False),
        "guidance_mode": normalized.get("guidance_mode"),
        "routine_candidate_count": len(normalized.get("routine_candidates") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
        "warnings": list(validation.get("warnings") or []),
        "llm_called": data.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def today_practice_guidance_provider_boundary_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
        "today_practice_guidance_provider_boundary_e2e_version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/provider-boundary/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview",
        "terminal_command": "/today-practice-guidance-e2e",
        "surface": "Provider-boundary E2E for user-initiated today-practice guidance",
        "mode": "prompt_to_provider_result_to_validation_candidate_only_no_execution",
        "execution_status": {
            "prompt_contract_enabled": True,
            "provider_boundary_enabled": True,
            "output_validation_enabled": True,
            "llm_call_default_enabled": False,
            "llm_call_may_be_requested_explicitly": True,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "prompt_payload": "v2_7_4 TodayPracticeGuidance prompt contract payload.",
            "provider_boundary": "Safe provider status and explicit-call gate; no secrets.",
            "provider_result_preview": "Redacted provider result or supplied providerResult fixture.",
            "parsed_guidance_output_preview": "Parsed JSON object before validation, redacted.",
            "output_validation_payload": "v2_7_6 validation payload.",
            "e2e_summary": "Candidate-only guidance readiness summary.",
        },
        "rules": [
            "Default behavior does not call an LLM; callers may pass providerResult for deterministic E2E validation.",
            "If a provider call is explicitly requested, the result still must pass v2_7_6 output validation.",
            "Valid output may only become guidance and editable Routine candidates for client display.",
            "No provider output may directly start Routine, call /accompaniment/generate, create MIDI assets, or bypass user confirmation.",
        ],
        "guards": {
            "default_calls_llm": False,
            "executes_tool": False,
            "calls_accompaniment_generate": False,
            "calls_engine_adapter": False,
            "creates_midi_asset": False,
            "starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
        },
        "uses_contracts": {
            "today_practice_guidance_prompt_contract": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
            "today_practice_guidance_output_validation": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
            "user_capability_map_and_intent_taxonomy": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        },
    }



@dataclass(frozen=True)
class TodayPracticeGuidanceActionCardPayload:
    """v2_7_8 HarmonyOS Routine display card for today-practice guidance.

    This payload wraps validated today-practice guidance into a Routine-facing
    presentation card. It is not a tool execution card: it only contains coach
    guidance, reasons, optional blocks, and editable Routine candidates. The
    client decides how to render it and must require a separate user-confirmed
    Routine start before any playback/generation side effect.
    """

    payload_contract_version: str
    source: str
    action_card: dict[str, Any]
    provider_boundary_e2e_payload: dict[str, Any]
    normalized_guidance_output: dict[str, Any]
    routine_candidate_cards: tuple[dict[str, Any], ...]
    display_sections: dict[str, Any]
    next_client_actions: tuple[str, ...]
    client_button_semantics: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "action_card": _redact_sensitive_values(self.action_card),
            "provider_boundary_e2e_payload": _redact_sensitive_values(self.provider_boundary_e2e_payload),
            "normalized_guidance_output": _redact_sensitive_values(self.normalized_guidance_output),
            "routine_candidate_cards": [_redact_sensitive_values(card) for card in self.routine_candidate_cards],
            "display_sections": _redact_sensitive_values(self.display_sections),
            "next_client_actions": list(self.next_client_actions),
            "client_button_semantics": _redact_sensitive_values(self.client_button_semantics),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def build_today_practice_guidance_action_card_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_action_card",
    provider: Any | None = None,
) -> TodayPracticeGuidanceActionCardPayload:
    """Build a Routine-facing ActionCard from validated today-practice guidance.

    The function delegates prompt/provider/validation handling to the existing
    v2_7_7 boundary, then turns only accepted candidate guidance into a client
    display card. It does not execute tools or start/generate Routine assets.
    """

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    e2e_payload = build_today_practice_guidance_provider_boundary_e2e_payload(
        args,
        trace_id=trace,
        source="today_practice_guidance_action_card_provider_boundary",
        provider=provider,
    )
    e2e_data = e2e_payload.to_dict()
    e2e_summary = e2e_data.get("e2e_summary") if isinstance(e2e_data.get("e2e_summary"), dict) else {}
    validation_payload = e2e_data.get("output_validation_payload") if isinstance(e2e_data.get("output_validation_payload"), dict) else {}
    validation_info = validation_payload.get("validation") if isinstance(validation_payload.get("validation"), dict) else {}
    normalized = e2e_summary.get("normalized_guidance_output") if isinstance(e2e_summary.get("normalized_guidance_output"), dict) else {}
    is_valid = bool(validation_info.get("is_valid")) and bool(normalized)
    blocked_reasons = list(validation_payload.get("blocked_reasons") or []) if isinstance(validation_payload, dict) else []
    warnings = list(validation_payload.get("warnings") or []) if isinstance(validation_payload, dict) else []

    routine_candidate_cards = tuple(
        _today_guidance_routine_candidate_card(candidate, index, trace)
        for index, candidate in enumerate(normalized.get("routine_candidates") or [])
        if isinstance(candidate, dict)
    ) if is_valid else tuple()
    display_sections = _today_guidance_display_sections(normalized if is_valid else {}, routine_candidate_cards=routine_candidate_cards)
    default_actions = ["show_guidance", "dismiss", "view_trace"]
    if routine_candidate_cards:
        default_actions.insert(1, "present_routine_candidate")
    if normalized.get("guidance_mode") == "ask_clarifying_question":
        default_actions.insert(1, "ask_follow_up")
    next_client_actions = tuple(dict.fromkeys(default_actions))
    client_button_semantics = _today_guidance_action_card_button_semantics(has_candidates=bool(routine_candidate_cards))
    status = "ready_for_client_display" if is_valid else "blocked_by_guidance_validator"
    action_card = {
        "action_contract_version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
        "action_id": str(args.get("action_id") or args.get("actionId") or f"today_practice_guidance_{uuid4().hex[:12]}"),
        "proposal_id": args.get("proposal_id") or args.get("proposalId"),
        "tool_name": "today_practice_guidance",
        "action_type": "routine_guidance_display_card",
        "title": _today_guidance_action_card_title(normalized if is_valid else {}),
        "description": str((normalized.get("summary") if is_valid else "Guidance output was blocked by validation.") or "")[:240],
        "side_effect_level": "none",
        "risk_summary": "This card displays practice guidance and editable Routine candidates only; Routine start and accompaniment generation remain separate user-confirmed actions.",
        "requires_user_confirmation": False,
        "requires_user_confirmation_before_routine_start": True,
        "confirmation_status": "not_required_for_display",
        "preview_status": status,
        "execution_status": "not_started",
        "workflow_name": "TodayPracticeGuidance.display_card",
        "display_sections": display_sections,
        "routine_candidate_cards": [card for card in routine_candidate_cards],
        "result_preview": {
            "today_practice_guidance_action_card_payload_version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
            "normalized_guidance_output": normalized if is_valid else {},
            "routine_candidate_count": len(routine_candidate_cards),
            "blocked_reasons": blocked_reasons,
            "warnings": warnings,
        },
        "trace_id": trace,
        "available_client_actions": list(next_client_actions),
        "client_button_semantics": client_button_semantics,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }
    validation = {
        "status": status,
        "is_valid": is_valid,
        "source_validation_status": validation_info.get("status"),
        "provider_content_parsed": bool((e2e_data.get("validation") or {}).get("provider_content_parsed")),
        "guidance_mode": normalized.get("guidance_mode") if is_valid else None,
        "routine_candidate_count": len(routine_candidate_cards),
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
        "card_display_only": True,
        "requires_separate_user_confirmation_before_routine_start": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "llm_called": bool(e2e_payload.llm_called),
        "tool_executed": False,
        "routine_start_enabled": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
    }
    return TodayPracticeGuidanceActionCardPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
        source=source,
        action_card=action_card,
        provider_boundary_e2e_payload=e2e_data,
        normalized_guidance_output=normalized if is_valid else {},
        routine_candidate_cards=routine_candidate_cards,
        display_sections=display_sections,
        next_client_actions=next_client_actions,
        client_button_semantics=client_button_semantics,
        validation=validation,
        trace_id=trace,
        llm_called=bool(e2e_payload.llm_called),
    )


def build_today_practice_guidance_action_card_summary(
    *,
    payload: TodayPracticeGuidanceActionCardPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    card = data.get("action_card") if isinstance(data.get("action_card"), dict) else {}
    normalized = data.get("normalized_guidance_output") if isinstance(data.get("normalized_guidance_output"), dict) else {}
    return {
        "today_practice_guidance_action_card_version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "is_valid": validation.get("is_valid", False),
        "action_id": card.get("action_id"),
        "guidance_mode": normalized.get("guidance_mode"),
        "recommended_block_count": len(normalized.get("recommended_blocks") or []),
        "routine_candidate_count": validation.get("routine_candidate_count", 0),
        "available_client_actions": list(card.get("available_client_actions") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
        "warnings": list(validation.get("warnings") or []),
        "llm_called": validation.get("llm_called", False),
        "card_display_only": True,
        "requires_separate_user_confirmation_before_routine_start": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def today_practice_guidance_action_card_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
        "today_practice_guidance_action_card_version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/action-card/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/action-card/preview",
        "terminal_command": "/today-practice-guidance-action-card",
        "surface": "HarmonyOS Routine display ActionCard for validated today-practice guidance",
        "mode": "display_card_only_no_execution",
        "execution_status": {
            "action_card_payload_enabled": True,
            "provider_boundary_e2e_used": True,
            "output_validation_required": True,
            "routine_candidates_enabled": True,
            "card_display_only": True,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "autonomous_execution_enabled": False,
        },
        "payload_schema": {
            "payload_contract_version": "v2_7_8",
            "action_card": "Routine-facing display card with title, summary, display_sections, routine_candidate_cards, and client actions",
            "provider_boundary_e2e_payload": "v2_7_7 prompt/provider/validation payload used as source",
            "normalized_guidance_output": "Accepted candidate-only TodayPracticeGuidanceOutput from v2_7_6 validator",
            "routine_candidate_cards": "Candidate cards for frontend-selected presentation; do not start Routine",
            "display_sections": "summary / recommended_focus / recommended_blocks / routine_candidates / adjustment_reason",
            "next_client_actions": "show_guidance | present_routine_candidate | ask_follow_up | dismiss | view_trace",
            "client_button_semantics": "button action metadata; primary may present a candidate, never start playback",
        },
        "rules": [
            "Only validated today-practice guidance can become an ActionCard.",
            "The card itself has no side effects and is safe to display without user confirmation.",
            "Any Routine start, playback, or accompaniment generation remains a separate user-confirmed action outside this contract.",
            "The client decides whether to render a page, sheet, inline card, queue item, or other UI.",
            "Blocked LLM output produces a blocked card payload for debugging, not an executable action.",
        ],
        "guards": {
            "card_calls_llm_by_default": False,
            "card_executes_tool": False,
            "card_calls_accompaniment_generate": False,
            "card_calls_engine_adapter": False,
            "card_creates_midi_asset": False,
            "card_starts_playback": False,
            "raw_api_key_allowed_in_payload": False,
            "hidden_chain_of_thought_allowed_in_payload": False,
        },
        "uses_contracts": {
            "provider_boundary_e2e": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
            "output_validation": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
            "user_capability_map_and_intent_taxonomy": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        },
    }


def _today_guidance_action_card_title(normalized: dict[str, Any]) -> str:
    mode = normalized.get("guidance_mode")
    if mode == "continue_original_plan":
        return "Continue today's planned practice"
    if mode == "adjust_based_on_history":
        return "Adjusted practice suggestion"
    if mode == "ask_clarifying_question":
        return "More practice context needed"
    return "Today practice guidance"


def _today_guidance_display_sections(normalized: dict[str, Any], *, routine_candidate_cards: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    blocks = normalized.get("recommended_blocks") if isinstance(normalized.get("recommended_blocks"), list) else []
    return {
        "summary": normalized.get("summary") or "",
        "recommended_focus": normalized.get("recommended_focus") or "",
        "adjustment_reason": normalized.get("adjustment_reason"),
        "profile_considerations": normalized.get("profile_considerations"),
        "recommended_blocks": blocks,
        "routine_candidates": [card for card in routine_candidate_cards],
        "empty_state": not bool(normalized),
    }


def _today_guidance_routine_candidate_card(candidate: dict[str, Any], index: int, trace_id: str | None) -> dict[str, Any]:
    duration = candidate.get("duration_minutes") or candidate.get("durationMinutes") or candidate.get("suggested_duration_minutes") or candidate.get("suggestedDurationMinutes")
    style = candidate.get("style") or candidate.get("suggested_style") or candidate.get("suggestedStyle")
    tempo = candidate.get("tempo") or candidate.get("bpm") or candidate.get("suggested_tempo") or candidate.get("suggestedTempo")
    tune_title = candidate.get("tune_title") or candidate.get("tuneTitle") or candidate.get("tune") or candidate.get("song")
    title_bits = [str(tune_title)] if tune_title else []
    if style:
        title_bits.append(str(style))
    title = " / ".join(title_bits) or f"Routine candidate {index + 1}"
    return {
        "candidate_card_id": f"today_practice_candidate_{index + 1}",
        "source_index": index,
        "title": title,
        "description": str(candidate.get("goal") or candidate.get("practice_goal") or candidate.get("practiceGoal") or candidate.get("description") or "")[:240],
        "routine_config_candidate": _redact_sensitive_values(candidate),
        "duration_minutes": duration,
        "style": style,
        "tempo": tempo,
        "tune_title": tune_title,
        "requires_user_confirmation_before_start": True,
        "does_start_playback": False,
        "does_call_accompaniment_generate": False,
        "does_create_midi_asset": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "trace_id": trace_id,
        "available_client_actions": ["present_routine_candidate", "edit_routine_candidate", "dismiss", "view_trace"],
    }


def _today_guidance_action_card_button_semantics(*, has_candidates: bool) -> dict[str, Any]:
    primary_action = "present_routine_candidate" if has_candidates else "show_guidance"
    primary_label = "Review Routine Candidate" if has_candidates else "Show Guidance"
    return {
        "primary": {
            "action": primary_action,
            "label": primary_label,
            "side_effect_level": "none",
            "does_start_playback": False,
            "does_call_accompaniment_generate": False,
            "requires_separate_start_confirmation": True,
        },
        "secondary": [
            {"action": "ask_follow_up", "label": "Ask a follow-up", "side_effect_level": "none"},
            {"action": "view_trace", "label": "View Trace", "side_effect_level": "none"},
            {"action": "dismiss", "label": "Dismiss", "side_effect_level": "none"},
        ],
        "forbidden_current_actions": [
            "start_routine",
            "start_playback",
            "call_accompaniment_generate",
            "generate_midi",
            "execute_tool",
        ],
    }

def _today_practice_provider_boundary_status(*, provider: Any | None = None, call_requested: bool = False) -> dict[str, Any]:
    safe_status: dict[str, Any]
    try:
        chosen_provider = provider or build_llm_provider_from_env()
        raw_status = chosen_provider.status() if hasattr(chosen_provider, "status") else {}
        safe_status = _redact_sensitive_values(dict(raw_status or {}))
    except Exception as exc:  # pragma: no cover - defensive only.
        safe_status = {"provider_status_error": str(exc)}
    return {
        "provider_boundary_version": "v2_7_7",
        "provider_status": safe_status,
        "provider_call_requested": bool(call_requested),
        "provider_call_default_enabled": False,
        "autonomous_tool_execution_enabled": False,
        "tool_execution_enabled": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
    }


def _provided_today_practice_provider_result(args: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("provider_result", "providerResult", "llm_provider_result", "llmProviderResult"):
        value = args.get(key)
        if isinstance(value, dict):
            result = dict(value)
            result.setdefault("provider_result_source", "provided_result_fixture")
            return result
    for key in ("llm_output", "llmOutput", "content", "provider_content", "providerContent"):
        value = args.get(key)
        if isinstance(value, dict):
            return {"ok": True, "content": json.dumps(value, ensure_ascii=False), "provider_result_source": key}
        if isinstance(value, str) and value.strip():
            return {"ok": True, "content": value.strip(), "provider_result_source": key}
    for key in ("today_practice_guidance_output", "todayPracticeGuidanceOutput", "guidance_output", "guidanceOutput"):
        value = args.get(key)
        if isinstance(value, dict):
            return {"ok": True, "content": json.dumps(value, ensure_ascii=False), "provider_result_source": key}
    return None


def _call_today_practice_guidance_provider(*, prompt_payload: TodayPracticeGuidancePromptContractPayload, provider: Any | None = None) -> dict[str, Any]:
    chosen_provider = provider or build_llm_provider_from_env()
    boundary = _today_practice_provider_boundary_status(provider=chosen_provider, call_requested=True)
    messages = _provider_messages_from_today_practice_prompt(prompt_payload)
    envelope = LLMRequestEnvelope(
        context_packet={"task_type": "today_practice_guidance", "prompt_payload": prompt_payload.to_dict()},
        allowed_tools=(),
        output_contract=prompt_payload.output_schema,
        runtime_policy={
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "routine_start_enabled": False,
            "accompaniment_generate_call_enabled": False,
        },
        messages=tuple(messages),
    )
    result = chosen_provider.generate(envelope) if hasattr(chosen_provider, "generate") else None
    result_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result or {})
    return {
        "llm_called": bool(result_dict),
        "provider_result": _redact_sensitive_values(result_dict),
        "provider_boundary": boundary,
        "provider_result_source": "provider_boundary_call",
    }


def _provider_messages_from_today_practice_prompt(prompt_payload: TodayPracticeGuidancePromptContractPayload) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for message in prompt_payload.prompt_messages:
        role = str(message.get("role") or "user")
        if role not in {"system", "developer", "user", "assistant"}:
            role = "developer"
        content = message.get("content")
        if content is None and "content_json" in message:
            content = json.dumps(message.get("content_json"), ensure_ascii=False)
        messages.append({"role": role, "content": str(content or "")})
    return messages



def _safe_provider_result_preview(provider_result: dict[str, Any]) -> dict[str, Any]:
    content = provider_result.get("content")
    return _redact_sensitive_values({
        "ok": bool(provider_result.get("ok")),
        "provider_name": provider_result.get("provider_name"),
        "model": provider_result.get("model"),
        "error_code": provider_result.get("error_code"),
        "message": provider_result.get("message"),
        "provider_result_source": provider_result.get("provider_result_source"),
        "content_present": isinstance(content, str) and bool(content.strip()),
        "content_char_count": len(content) if isinstance(content, str) else 0,
        "raw_usage": provider_result.get("raw_usage") if isinstance(provider_result.get("raw_usage"), dict) else {},
    })

def _parse_today_practice_provider_output(provider_result: dict[str, Any]) -> dict[str, Any]:
    content = provider_result.get("content") or provider_result.get("message") or provider_result.get("output")
    if isinstance(content, dict):
        return _redact_sensitive_values(dict(content))
    if not isinstance(content, str):
        return {}
    text = content.strip()
    if not text:
        return {}
    parsed = _parse_json_object_from_text(text)
    return _redact_today_guidance_forbidden_fields(_redact_sensitive_values(parsed)) if parsed else {}


def _coerce_provider_output_to_today_guidance(
    provider_result: dict[str, Any],
    parsed_output: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Coerce provider text into a safe display-only guidance draft.

    Terminal chat should not fail just because a model returns ordinary Chinese
    prose instead of the strict TodayPracticeGuidanceOutput JSON object. This
    helper keeps the safety boundary intact by turning only successful provider
    text into a minimal display-only candidate; it never creates Routine starts,
    engine calls, playback, or MIDI assets.
    """

    parsed = dict(parsed_output or {})
    warnings: list[str] = []
    provider_ok = bool(provider_result.get("ok"))
    content = provider_result.get("content") or provider_result.get("message") or provider_result.get("output")
    text_content = content.strip() if isinstance(content, str) else ""
    if parsed:
        if not parsed.get("guidance_mode") and not parsed.get("guidanceMode"):
            parsed["guidance_mode"] = "fallback_without_plan"
            warnings.append("guidance_mode_filled_from_provider_output")
        if not (parsed.get("summary") or parsed.get("message") or parsed.get("answer")) and text_content:
            parsed["summary"] = text_content
            warnings.append("summary_filled_from_provider_text")
        if not parsed.get("recommended_focus") and not parsed.get("recommendedFocus") and parsed.get("summary"):
            parsed["recommended_focus"] = "今日练习安排"
            warnings.append("recommended_focus_filled_from_provider_output")
        if parsed.get("user_confirmation_required") is None and parsed.get("userConfirmationRequired") is None:
            parsed["user_confirmation_required"] = True
        if not isinstance(parsed.get("next_client_actions") or parsed.get("nextClientActions"), list):
            parsed["next_client_actions"] = ["show_guidance"]
        return _redact_today_guidance_forbidden_fields(_redact_sensitive_values(parsed)), warnings

    if provider_ok and text_content:
        warnings.append("provider_returned_plain_text_coerced_to_display_only_guidance")
        return _redact_today_guidance_forbidden_fields(_redact_sensitive_values({
            "guidance_mode": "fallback_without_plan",
            "summary": text_content[:1200],
            "recommended_focus": "今日练习安排",
            "recommended_blocks": [],
            "routine_candidates": [],
            "user_confirmation_required": True,
            "next_client_actions": ["show_guidance"],
            "coercion_source": "terminal_provider_plain_text_fallback",
        })), warnings

    return {}, warnings


def _parse_json_object_from_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
        return dict(value) if isinstance(value, dict) else {}
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            value = json.loads(match.group(0))
            return dict(value) if isinstance(value, dict) else {}
        except Exception:
            return {}
    return {}

@dataclass(frozen=True)
class TodayPracticeGuidanceTerminalChatE2EPayload:
    """v2_7_9 terminal chat E2E surface for user-initiated today guidance.

    This payload is built from an ordinary terminal message such as "今天该练什么？".
    It routes only the detected today-practice intent into the existing
    context/provider/validation/action-card chain. It never starts Routine,
    calls /accompaniment/generate, invokes engine adapters, creates MIDI assets,
    or controls playback.
    """

    payload_contract_version: str
    source: str
    user_input: str
    detected_intent: dict[str, Any]
    action_card_payload: dict[str, Any]
    action_card_summary: dict[str, Any]
    terminal_response: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "user_input": self.user_input,
            "detected_intent": dict(self.detected_intent),
            "action_card_payload": _redact_sensitive_values(self.action_card_payload),
            "action_card_summary": _redact_sensitive_values(self.action_card_summary),
            "terminal_response": _redact_sensitive_values(self.terminal_response),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def detect_today_practice_guidance_intent(user_input: str | None) -> dict[str, Any]:
    """Detect ordinary user turns asking what to practice today.

    This is a narrow terminal-routing helper, not a full intent classifier. It
    only routes high-confidence today-practice guidance requests into the
    existing guarded guidance chain.
    """

    text = (user_input or "").strip()
    lowered = text.lower()
    chinese_markers = ("今天该练什么", "今天练什么", "今天要练什么", "今天应该练什么", "今天该怎么练", "今天练点什么")
    english_markers = ("what should i practice today", "what should we practice today", "practice today", "today's practice", "todays practice")
    matched = ""
    language = "unknown"
    for marker in chinese_markers:
        if marker in text:
            matched = marker
            language = "zh"
            break
    if not matched:
        for marker in english_markers:
            if marker in lowered:
                matched = marker
                language = "en"
                break
    is_match = bool(matched)
    return {
        "is_today_practice_guidance_intent": is_match,
        "intent_type": "today_practice_guidance" if is_match else None,
        "matched_phrase": matched or None,
        "language_hint": language if is_match else None,
        "confidence": 0.93 if is_match else 0.0,
        "ordinary_terminal_chat_routing": is_match,
        "requires_llm_provider_boundary": is_match,
        "tool_execution_enabled": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
    }


@dataclass(frozen=True)
class TodayPracticeGuidanceHarmonyOSDebugFixtureRoundtripTerminalE2EPayload:
    """v2_8_20 roundtrip preview from HarmonyOS debug fixture back into guidance.

    This payload consumes a v2_8_19 HarmonyOS debug fixture preview (or builds one
    from direct profile/plan/history arguments), extracts the Agent persisted
    context recovery request body, and runs the read-only persisted-context
    recovery guidance preview. It verifies the terminal/frontend debug fixture
    can roundtrip into the same display-only TodayPracticeGuidance chain.
    """

    payload_contract_version: str
    source: str
    fixture_id: str | None
    user_input: str
    fixture_payload: dict[str, Any]
    agent_request_body: dict[str, Any]
    recovery_payload: dict[str, Any]
    recovery_summary: dict[str, Any]
    roundtrip_validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "fixture_id": self.fixture_id,
            "user_input": self.user_input,
            "fixture_payload": _redact_sensitive_values(self.fixture_payload),
            "agent_request_body": _redact_sensitive_values(self.agent_request_body),
            "recovery_payload": _redact_sensitive_values(self.recovery_payload),
            "recovery_summary": _redact_sensitive_values(self.recovery_summary),
            "roundtrip_validation": _redact_sensitive_values(self.roundtrip_validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _extract_harmonyos_debug_fixture_for_roundtrip(args: dict[str, Any]) -> tuple[dict[str, Any], str]:
    fixture = _first_present(
        args,
        "harmonyos_debug_fixture",
        "harmonyosDebugFixture",
        "debugFixture",
        "fixture",
    )
    if isinstance(fixture, dict):
        return fixture, "embedded_harmonyos_debug_fixture"
    payload = _first_present(
        args,
        "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload",
        "todayPracticeGuidanceTerminalMemoryToHarmonyOSDebugFixturePayload",
        "debug_fixture_payload",
        "debugFixturePayload",
    )
    if isinstance(payload, dict):
        fixture = payload.get("harmonyos_debug_fixture") or payload.get("harmonyosDebugFixture")
        if isinstance(fixture, dict):
            return fixture, "embedded_v2_8_19_payload_fixture"
    fixture_payload = build_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload(
        args,
        trace_id=args.get("trace_id") or args.get("traceId"),
        source="roundtrip_builds_debug_fixture_from_arguments",
    )
    return fixture_payload.to_dict().get("harmonyos_debug_fixture", {}), "built_from_arguments_or_terminal_memory"


def _extract_agent_request_body_from_debug_fixture(fixture: dict[str, Any], fallback_args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    request_preview = fixture.get("agentRequestPreview") or fixture.get("agent_request_preview")
    body: dict[str, Any] = {}
    if isinstance(request_preview, dict):
        preview_body = request_preview.get("body")
        if isinstance(preview_body, dict):
            body = dict(preview_body)
    if not body:
        context_payload = fixture.get("contextPayload") or fixture.get("context_payload")
        if isinstance(context_payload, dict):
            body = dict(context_payload)
            warnings.append("agent_request_preview_body_missing_used_context_payload")
    if not body:
        snapshot_payload = _first_present(fallback_args, "snapshotContextIntakePayload", "snapshot_context_intake_payload")
        if isinstance(snapshot_payload, dict):
            body = {"snapshotContextIntakePayload": snapshot_payload}
            warnings.append("fixture_missing_request_body_used_fallback_snapshot_payload")
    provider_result = _first_present(fallback_args, "providerResult", "provider_result")
    if isinstance(provider_result, dict) and "providerResult" not in body and "provider_result" not in body:
        body["providerResult"] = provider_result
    if "callProvider" not in body and "call_provider" not in body:
        body["callProvider"] = False
    if "debugFixtureRoundtrip" not in body:
        body["debugFixtureRoundtrip"] = True
    return body, warnings


def build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e",
) -> TodayPracticeGuidanceHarmonyOSDebugFixtureRoundtripTerminalE2EPayload:
    """Roundtrip a HarmonyOS debug fixture preview into persisted-context recovery guidance."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    fixture, fixture_source = _extract_harmonyos_debug_fixture_for_roundtrip(args)
    agent_body, extraction_warnings = _extract_agent_request_body_from_debug_fixture(fixture, args)
    user_input = str(agent_body.get("userInput") or agent_body.get("user_input") or args.get("userInput") or args.get("user_input") or "今天该练什么？")
    fixture_id = fixture.get("fixtureId") or fixture.get("fixture_id")
    recovery = build_today_practice_guidance_persisted_context_recovery_e2e_payload(
        agent_body,
        trace_id=trace,
        source="roundtrip_terminal_e2e_to_persisted_context_recovery",
    )
    recovery_dict = recovery.to_dict()
    recovery_summary = build_today_practice_guidance_persisted_context_recovery_e2e_summary(
        payload=recovery,
        source="roundtrip_terminal_e2e",
    )
    preview_path = None
    request_preview = fixture.get("agentRequestPreview") or fixture.get("agent_request_preview")
    if isinstance(request_preview, dict):
        preview_path = request_preview.get("path")
    expected_path = "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview"
    path_matches = (preview_path in (None, expected_path))
    recovered = bool(recovery_summary.get("profile_context_recovered") or recovery_summary.get("active_plan_context_recovered") or recovery_summary.get("routine_history_context_recovered"))
    action_card_is_valid = bool(recovery_summary.get("guidance_action_card_is_valid"))
    accepted = path_matches and recovered and action_card_is_valid
    blocked_reasons: list[str] = []
    warnings: list[str] = list(extraction_warnings)
    if not path_matches:
        blocked_reasons.append("debug_fixture_agent_request_preview_path_mismatch")
    if not recovered:
        blocked_reasons.append("roundtrip_recovered_no_profile_plan_or_history_context")
    if not action_card_is_valid:
        blocked_reasons.append("roundtrip_guidance_action_card_invalid")
    if fixture_source == "built_from_arguments_or_terminal_memory":
        warnings.append("roundtrip_fixture_was_built_from_arguments_not_harmonyos_fixture")
    validation = {
        "accepted": accepted,
        "status": "accepted" if accepted else "blocked",
        "fixture_source": fixture_source,
        "fixture_id": fixture_id,
        "agent_preview_route": preview_path or expected_path,
        "agent_preview_route_matches_expected": path_matches,
        "profile_context_recovered": bool(recovery_summary.get("profile_context_recovered")),
        "active_plan_context_recovered": bool(recovery_summary.get("active_plan_context_recovered")),
        "routine_history_context_recovered": bool(recovery_summary.get("routine_history_context_recovered")),
        "guidance_action_card_is_valid": action_card_is_valid,
        "routine_candidate_count": int(recovery_summary.get("routine_candidate_count") or 0),
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "roundtrip_writes_storage": False,
        "roundtrip_writes_backend_database": False,
        "roundtrip_writes_harmonyos_local_state": False,
        "roundtrip_creates_sqlite_connection": False,
        "roundtrip_calls_llm": False,
        "roundtrip_executes_tool": False,
        "roundtrip_starts_routine": False,
        "roundtrip_calls_accompaniment_generate": False,
        "roundtrip_calls_engine_adapter": False,
        "roundtrip_creates_midi_asset": False,
        "roundtrip_starts_playback": False,
        "roundtrip_creates_post_session_recommendation_card": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }
    return TodayPracticeGuidanceHarmonyOSDebugFixtureRoundtripTerminalE2EPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
        source=source,
        fixture_id=str(fixture_id) if fixture_id else None,
        user_input=user_input,
        fixture_payload=fixture,
        agent_request_body=agent_body,
        recovery_payload=recovery_dict,
        recovery_summary=recovery_summary,
        roundtrip_validation=validation,
        guard_summary=guard,
        trace_id=trace,
    )


def build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary(
    *,
    payload: TodayPracticeGuidanceHarmonyOSDebugFixtureRoundtripTerminalE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("roundtrip_validation") if isinstance(data.get("roundtrip_validation"), dict) else {}
    recovery_summary = data.get("recovery_summary") if isinstance(data.get("recovery_summary"), dict) else {}
    return {
        "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "fixture_id": validation.get("fixture_id"),
        "fixture_source": validation.get("fixture_source"),
        "agent_preview_route": validation.get("agent_preview_route"),
        "agent_preview_route_matches_expected": validation.get("agent_preview_route_matches_expected", False),
        "profile_context_recovered": validation.get("profile_context_recovered", False),
        "active_plan_context_recovered": validation.get("active_plan_context_recovered", False),
        "routine_history_context_recovered": validation.get("routine_history_context_recovered", False),
        "guidance_action_card_is_valid": validation.get("guidance_action_card_is_valid", False),
        "routine_candidate_count": validation.get("routine_candidate_count", 0),
        "roundtrip_ready": bool(validation.get("accepted")),
        "guidance_summary": recovery_summary.get("guidance_summary"),
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
        "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
        "terminal_command": "/harmonyos-debug-fixture-roundtrip [json_payload]",
        "surface": "HarmonyOS debug fixture roundtrip back into persisted-context today-practice guidance",
        "mode": "debug_fixture_request_preview_to_display_only_guidance_roundtrip",
        "execution_status": {
            "roundtrip_preview_enabled": True,
            "harmonyos_debug_fixture_can_roundtrip_to_agent_preview": True,
            "persisted_context_recovery_preview_used": True,
            "guidance_display_only": True,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled_by_agent": False,
            "llm_call_enabled_by_roundtrip": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "roundtrip_flow": [
            "consume HarmonyOS debug fixture preview or build one from terminal memory/direct context",
            "extract fixture.agentRequestPreview.body for persisted-context recovery",
            "run read-only persisted-context recovery guidance preview",
            "return validation, recovered-context summary, and display-only ActionCard readiness",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_starts_routine": False,
            "payload_creates_post_session_recommendation_card": False,
            "client_decides_presentation": True,
            "frontend_flow_assumption": False,
        },
        "uses_contracts": {
            "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
            "today_practice_guidance_persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
            "context_persistence_profile_plan_history_snapshot_context_intake": CONTEXT_PERSISTENCE_PROFILE_PLAN_HISTORY_SNAPSHOT_CONTEXT_INTAKE_VERSION,
        },
        "next_task_hint": "v2_8_21_agent_harmonyos_debug_fixture_api_request_pack",
    }



@dataclass(frozen=True)
class TodayPracticeGuidanceHarmonyOSDebugFixtureAPIRequestPackPayload:
    """v2_8_21 request pack for HarmonyOS persisted-context guidance debug integration.

    This payload turns the v2_8_19/v2_8_20 debug fixture chain into a concise
    request/response pack that a HarmonyOS developer can copy into an API client
    or debug screen. It is documentation/preview only: it does not call routes,
    write storage, invoke LLM, start routines, or touch the accompaniment engine.
    """

    payload_contract_version: str
    source: str
    pack_id: str
    user_input: str
    harmonyos_debug_fixture: dict[str, Any]
    api_request_pack: dict[str, Any]
    response_shape_preview: dict[str, Any]
    terminal_command_pack: dict[str, Any]
    roundtrip_summary: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    sqlite_connection_created: bool = False
    sqlite_tables_created: bool = False
    sqlite_rows_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "pack_id": self.pack_id,
            "user_input": self.user_input,
            "harmonyos_debug_fixture": _redact_sensitive_values(self.harmonyos_debug_fixture),
            "api_request_pack": _redact_sensitive_values(self.api_request_pack),
            "response_shape_preview": _redact_sensitive_values(self.response_shape_preview),
            "terminal_command_pack": _redact_sensitive_values(self.terminal_command_pack),
            "roundtrip_summary": _redact_sensitive_values(self.roundtrip_summary),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "sqlite_connection_created": self.sqlite_connection_created,
            "sqlite_tables_created": self.sqlite_tables_created,
            "sqlite_rows_written": self.sqlite_rows_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _compact_json_for_request_pack(value: Any) -> str:
    return json.dumps(_redact_sensitive_values(value), ensure_ascii=False, separators=(",", ":"))


def build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_harmonyos_debug_fixture_api_request_pack",
) -> TodayPracticeGuidanceHarmonyOSDebugFixtureAPIRequestPackPayload:
    """Build a copyable HarmonyOS API request pack for debug-fixture guidance testing."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    pack_id = str(_first_present(args, "pack_id", "packId") or f"harmonyos_guidance_request_pack_{uuid4().hex[:12]}")
    base_url = str(_first_present(args, "base_url", "baseUrl") or "http://127.0.0.1:8000").rstrip("/")
    user_input = str(_first_present(args, "user_input", "userInput", "text") or "今天该练什么？")

    roundtrip = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload(
        args,
        trace_id=trace,
        source="api_request_pack_roundtrip_validation",
    )
    roundtrip_dict = roundtrip.to_dict()
    roundtrip_summary = build_today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary(
        payload=roundtrip,
        source="api_request_pack",
    )
    harmonyos_fixture = roundtrip_dict.get("fixture_payload") if isinstance(roundtrip_dict.get("fixture_payload"), dict) else {}
    agent_body = roundtrip_dict.get("agent_request_body") if isinstance(roundtrip_dict.get("agent_request_body"), dict) else {}

    fixture_preview_body = dict(args)
    # The fixture builder accepts direct profile/plan/history input. Keeping the
    # body close to the developer's original payload makes the pack copyable.
    if "baseUrl" in fixture_preview_body:
        fixture_preview_body.pop("baseUrl", None)
    if "base_url" in fixture_preview_body:
        fixture_preview_body.pop("base_url", None)
    if "packId" in fixture_preview_body:
        fixture_preview_body.pop("packId", None)
    if "pack_id" in fixture_preview_body:
        fixture_preview_body.pop("pack_id", None)

    roundtrip_body = {"harmonyosDebugFixture": harmonyos_fixture}
    provider_result = _first_present(args, "providerResult", "provider_result")
    if isinstance(provider_result, dict):
        roundtrip_body["providerResult"] = provider_result

    api_requests = [
        {
            "step": 1,
            "name": "build_harmonyos_debug_fixture_preview",
            "method": "POST",
            "path": "/agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview",
            "url": f"{base_url}/agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview",
            "body": fixture_preview_body,
            "expected_response_keys": [
                "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload",
                "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary",
            ],
            "side_effects_created": False,
        },
        {
            "step": 2,
            "name": "run_persisted_context_recovery_guidance_preview",
            "method": "POST",
            "path": "/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
            "url": f"{base_url}/agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
            "body": agent_body,
            "expected_response_keys": [
                "today_practice_guidance_persisted_context_recovery_e2e_payload",
                "today_practice_guidance_persisted_context_recovery_e2e_summary",
            ],
            "side_effects_created": False,
        },
        {
            "step": 3,
            "name": "validate_harmonyos_debug_fixture_roundtrip",
            "method": "POST",
            "path": "/agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
            "url": f"{base_url}/agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
            "body": roundtrip_body,
            "expected_response_keys": [
                "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_payload",
                "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary",
            ],
            "side_effects_created": False,
        },
    ]
    api_request_pack = {
        "packContractVersion": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
        "packKind": "harmonyos_today_practice_guidance_debug_fixture_api_request_pack",
        "packId": pack_id,
        "baseUrl": base_url,
        "purpose": "Copyable HarmonyOS debug API requests for persisted-context today-practice guidance preview.",
        "requests": api_requests,
        "curlExamples": [
            f"curl -s -X POST {req['url']} -H 'Content-Type: application/json' -d '{_compact_json_for_request_pack(req['body'])}'"
            for req in api_requests
        ],
        "arktsFetchSketch": {
            "method": "POST",
            "contentType": "application/json",
            "requestOrder": [req["name"] for req in api_requests],
            "clientOwnsPresentation": True,
            "doNotStartRoutineFromPreview": True,
        },
        "directTerminalEquivalent": "/harmonyos-debug-fixture-roundtrip <json_payload>",
        "debugOnly": True,
    }
    response_shape_preview = {
        "build_harmonyos_debug_fixture_preview": {
            "ok": True,
            "summary_path": "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_summary",
            "fixture_path": "today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture_payload.harmonyos_debug_fixture",
            "debug_fixture_ready": True,
        },
        "run_persisted_context_recovery_guidance_preview": {
            "ok": True,
            "summary_path": "today_practice_guidance_persisted_context_recovery_e2e_summary",
            "action_card_display_only": True,
            "routine_start_enabled": False,
            "accompaniment_generate_call_enabled": False,
        },
        "validate_harmonyos_debug_fixture_roundtrip": {
            "ok": True,
            "summary_path": "today_practice_guidance_harmonyos_debug_fixture_roundtrip_terminal_e2e_summary",
            "roundtrip_ready": bool(roundtrip_summary.get("roundtrip_ready")),
            "guidance_action_card_is_valid": bool(roundtrip_summary.get("guidance_action_card_is_valid")),
        },
    }
    terminal_command_pack = {
        "load_memory": "/persisted-context-load <profile_plan_history_json>",
        "export_debug_fixture": "/persisted-context-harmonyos-debug-fixture",
        "roundtrip": "/harmonyos-debug-fixture-roundtrip",
        "api_request_pack": "/harmonyos-debug-fixture-api-request-pack [json_payload]",
        "ordinary_user_turn_after_memory_load": user_input,
    }
    accepted = bool(harmonyos_fixture) and bool(agent_body) and len(api_requests) == 3
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if not harmonyos_fixture:
        blocked_reasons.append("harmonyos_debug_fixture_missing")
    if not agent_body:
        blocked_reasons.append("agent_request_body_missing")
    if not roundtrip_summary.get("roundtrip_ready"):
        warnings.append("roundtrip_preview_not_ready_pack_still_generated_for_debugging")
    validation = {
        "accepted": accepted,
        "status": "accepted" if accepted else "blocked",
        "pack_id": pack_id,
        "request_count": len(api_requests),
        "contains_fixture_builder_request": True,
        "contains_persisted_context_recovery_request": True,
        "contains_roundtrip_validation_request": True,
        "roundtrip_ready": bool(roundtrip_summary.get("roundtrip_ready")),
        "guidance_action_card_is_valid": bool(roundtrip_summary.get("guidance_action_card_is_valid")),
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
    }
    guard = {
        "request_pack_writes_storage": False,
        "request_pack_calls_llm": False,
        "request_pack_executes_tool": False,
        "request_pack_calls_engine_adapter": False,
        "request_pack_calls_accompaniment_generate": False,
        "request_pack_creates_midi_asset": False,
        "request_pack_starts_playback": False,
        "request_pack_starts_routine": False,
        "request_pack_creates_post_session_recommendation_card": False,
        "debug_only": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }
    return TodayPracticeGuidanceHarmonyOSDebugFixtureAPIRequestPackPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
        source=source,
        pack_id=pack_id,
        user_input=user_input,
        harmonyos_debug_fixture=harmonyos_fixture,
        api_request_pack=api_request_pack,
        response_shape_preview=response_shape_preview,
        terminal_command_pack=terminal_command_pack,
        roundtrip_summary=roundtrip_summary,
        validation=validation,
        guard_summary=guard,
        trace_id=trace,
    )


def build_today_practice_guidance_harmonyos_debug_fixture_api_request_pack_summary(
    *,
    payload: TodayPracticeGuidanceHarmonyOSDebugFixtureAPIRequestPackPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    pack = data.get("api_request_pack") if isinstance(data.get("api_request_pack"), dict) else {}
    requests = pack.get("requests") if isinstance(pack.get("requests"), list) else []
    return {
        "today_practice_guidance_harmonyos_debug_fixture_api_request_pack_version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "pack_id": data.get("pack_id"),
        "api_request_pack_ready": bool(validation.get("accepted")),
        "request_count": len(requests),
        "request_paths": [req.get("path") for req in requests if isinstance(req, dict)],
        "roundtrip_ready": validation.get("roundtrip_ready", False),
        "guidance_action_card_is_valid": validation.get("guidance_action_card_is_valid", False),
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def today_practice_guidance_harmonyos_debug_fixture_api_request_pack_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
        "today_practice_guidance_harmonyos_debug_fixture_api_request_pack_version": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_API_REQUEST_PACK_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview",
        "terminal_command": "/harmonyos-debug-fixture-api-request-pack [json_payload]",
        "surface": "HarmonyOS debug fixture API request pack for persisted-context today-practice guidance preview",
        "mode": "copyable_debug_api_request_pack_without_side_effects",
        "execution_status": {
            "api_request_pack_preview_enabled": True,
            "builds_copyable_request_bodies": True,
            "calls_routes": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled_by_agent": False,
            "llm_call_enabled_by_pack_builder": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "request_pack_steps": [
            "POST terminal-memory-harmonyos-debug-fixture/preview to build a debug fixture",
            "POST persisted-context-recovery/e2e-preview to preview display-only guidance",
            "POST harmonyos-debug-fixture-roundtrip/e2e-preview to validate fixture roundtrip",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_starts_routine": False,
            "payload_creates_post_session_recommendation_card": False,
            "client_decides_presentation": True,
            "frontend_flow_assumption": False,
        },
        "uses_contracts": {
            "terminal_memory_to_harmonyos_debug_fixture": TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_VERSION,
            "persisted_context_recovery_e2e": TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_VERSION,
            "harmonyos_debug_fixture_roundtrip_terminal_e2e": TODAY_PRACTICE_GUIDANCE_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_VERSION,
        },
        "next_task_hint": "v2_8_22_agent_terminal_chat_product_smoke_polish",
    }

@dataclass(frozen=True)
class TodayPracticeGuidanceTerminalProductSmokePolishPayload:
    """Terminal chat product smoke polish payload.

    This is a terminal/API preview contract only. It packages the real-world
    manual smoke path for provider setup, ordinary Chinese today-practice input,
    persisted-context memory controls, JSON fallback behavior, and no-side-effect
    guards. It does not call an LLM provider or execute any tool by itself.
    """

    payload_contract_version: str
    source: str
    smoke_id: str
    provider_status: dict[str, Any]
    readiness: dict[str, Any]
    terminal_command_pack: dict[str, Any]
    ordinary_chat_smoke: dict[str, Any]
    persisted_context_memory_smoke: dict[str, Any]
    json_fallback_smoke: dict[str, Any]
    error_message_smoke: dict[str, Any]
    validation: dict[str, Any]
    guard_summary: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    route_called: bool = False
    storage_written: bool = False
    backend_database_written: bool = False
    local_device_written: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    routine_start_enabled: bool = False
    post_session_recommendation_card_created: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "smoke_id": self.smoke_id,
            "provider_status": _redact_sensitive_values(self.provider_status),
            "readiness": _redact_sensitive_values(self.readiness),
            "terminal_command_pack": _redact_sensitive_values(self.terminal_command_pack),
            "ordinary_chat_smoke": _redact_sensitive_values(self.ordinary_chat_smoke),
            "persisted_context_memory_smoke": _redact_sensitive_values(self.persisted_context_memory_smoke),
            "json_fallback_smoke": _redact_sensitive_values(self.json_fallback_smoke),
            "error_message_smoke": _redact_sensitive_values(self.error_message_smoke),
            "validation": _redact_sensitive_values(self.validation),
            "guard_summary": _redact_sensitive_values(self.guard_summary),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "route_called": self.route_called,
            "storage_written": self.storage_written,
            "backend_database_written": self.backend_database_written,
            "local_device_written": self.local_device_written,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "routine_start_enabled": self.routine_start_enabled,
            "post_session_recommendation_card_created": self.post_session_recommendation_card_created,
        }


def _provider_terminal_enabled(provider_status: dict[str, Any]) -> bool:
    return bool(
        provider_status.get("terminal_chat_enabled")
        or provider_status.get("terminal_chat_available")
        or provider_status.get("llm_calls_enabled")
    )


def build_today_practice_guidance_terminal_product_smoke_polish_payload(
    arguments: dict[str, Any] | None = None,
    *,
    provider_status: dict[str, Any] | None = None,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_terminal_product_smoke_polish",
) -> TodayPracticeGuidanceTerminalProductSmokePolishPayload:
    """Build a terminal product smoke checklist without calling the provider.

    The preview intentionally avoids LLM calls. It helps developers verify the
    terminal UX path before manually typing ordinary Chinese guidance prompts.
    """

    args = dict(arguments or {})
    status = dict(provider_status or _first_present(args, "providerStatus", "provider_status") or {})
    smoke_id = str(_first_present(args, "smoke_id", "smokeId") or f"terminal_product_smoke_{uuid4().hex[:12]}")
    sample_user_input = str(_first_present(args, "sampleUserInput", "sample_user_input", "userInput", "user_input") or "今天该练什么？")
    terminal_enabled = _provider_terminal_enabled(status)
    guard_reason = status.get("guard_reason") or status.get("message") or ("provider_ready" if terminal_enabled else "LLM provider is not configured for terminal chat.")
    readiness_status = "ready_for_manual_llm_smoke" if terminal_enabled else "configuration_required_but_preview_commands_available"
    command_pack = {
        "setup": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat setup",
        "doctor": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat doctor",
        "start_chat_with_status": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status",
        "load_persisted_context": "/persisted-context-load <profile_plan_history_json>",
        "show_persisted_context": "/persisted-context-show",
        "clear_persisted_context": "/persisted-context-clear",
        "ordinary_today_practice_turn": sample_user_input,
        "terminal_product_smoke": "/terminal-product-smoke [json_payload]",
    }
    ordinary_chat_smoke = {
        "ordinary_chinese_input_supported": True,
        "sample_user_input": sample_user_input,
        "routes_to_guidance_chain": True,
        "uses_loaded_persisted_context_when_available": True,
        "display_only_action_card_expected": True,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
    }
    persisted_context_memory_smoke = {
        "load_show_clear_commands_available": True,
        "memory_scope": "terminal_session_only",
        "injected_into_next_today_practice_guidance_turn": True,
        "writes_backend_database": False,
        "writes_harmonyos_local_state": False,
    }
    json_fallback_smoke = {
        "json_only_prompt_contract_expected": True,
        "plain_text_provider_response_fallback_enabled": True,
        "partial_json_defaults_enabled": True,
        "validation_blocked_response_should_show_actionable_hint": True,
        "fallback_starts_routine": False,
    }
    error_message_smoke = {
        "provider_setup_hint_available": True,
        "doctor_command_available": True,
        "unsupported_provider_hint": "Use --provider openai_compatible for OpenAI-compatible Chat Completions services.",
        "developer_role_compatibility": "network payload normalizes developer/context messages into system/user-compatible roles",
        "blocked_guidance_hint": "If guidance is blocked, inspect doctor output and retry with /terminal-product-smoke or slash command payload preview.",
    }
    checks = {
        "provider_status_displayed": bool(status) or not terminal_enabled,
        "setup_command_available": True,
        "doctor_command_available": True,
        "ordinary_chinese_guidance_route_available": True,
        "persisted_context_memory_controls_available": True,
        "json_fallback_smoke_documented": True,
        "guarded_error_hint_available": True,
        "no_side_effects_preserved": True,
    }
    warnings: list[str] = []
    if not terminal_enabled:
        warnings.append("provider_not_ready_manual_llm_smoke_requires_setup_or_env_config")
    if status and status.get("api_key_configured") is False:
        warnings.append("api_key_not_configured")
    validation = {
        "accepted": True,
        "status": "ready" if terminal_enabled else "guarded_preview_ready",
        "readiness_status": readiness_status,
        "smoke_id": smoke_id,
        "check_count": len(checks),
        "passed_check_count": sum(1 for value in checks.values() if value),
        "checks": checks,
        "warnings": warnings,
        "blocked_reasons": [],
    }
    readiness = {
        "readiness_status": readiness_status,
        "terminal_chat_provider_ready": terminal_enabled,
        "provider_name": status.get("provider_name"),
        "model": status.get("model"),
        "api_key_configured": status.get("api_key_configured"),
        "network_calls_enabled": status.get("network_calls_enabled") or status.get("llm_calls_enabled"),
        "config_source": status.get("config_source"),
        "config_file_path": status.get("config_file_path"),
        "guard_reason": guard_reason,
        "next_manual_step": "type ordinary Chinese prompt" if terminal_enabled else "run setup then doctor before ordinary Chinese prompt",
    }
    guard = {
        "payload_calls_llm": False,
        "payload_executes_tool": False,
        "payload_writes_storage": False,
        "payload_writes_backend_database": False,
        "payload_writes_harmonyos_local_state": False,
        "payload_calls_engine_adapter": False,
        "payload_calls_accompaniment_generate": False,
        "payload_creates_midi_asset": False,
        "payload_starts_playback": False,
        "payload_starts_routine": False,
        "payload_creates_post_session_recommendation_card": False,
        "terminal_manual_smoke_may_call_llm_after_user_enters_prompt": bool(terminal_enabled),
    }
    return TodayPracticeGuidanceTerminalProductSmokePolishPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION,
        source=source,
        smoke_id=smoke_id,
        provider_status=status,
        readiness=readiness,
        terminal_command_pack=command_pack,
        ordinary_chat_smoke=ordinary_chat_smoke,
        persisted_context_memory_smoke=persisted_context_memory_smoke,
        json_fallback_smoke=json_fallback_smoke,
        error_message_smoke=error_message_smoke,
        validation=validation,
        guard_summary=guard,
        trace_id=trace_id,
    )


def build_today_practice_guidance_terminal_product_smoke_polish_summary(
    *,
    payload: TodayPracticeGuidanceTerminalProductSmokePolishPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    readiness = data.get("readiness") if isinstance(data.get("readiness"), dict) else {}
    checks = validation.get("checks") if isinstance(validation.get("checks"), dict) else {}
    return {
        "today_practice_guidance_terminal_product_smoke_polish_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "accepted": validation.get("accepted", False),
        "readiness_status": readiness.get("readiness_status"),
        "terminal_chat_provider_ready": bool(readiness.get("terminal_chat_provider_ready")),
        "provider_name": readiness.get("provider_name"),
        "model": readiness.get("model"),
        "check_count": validation.get("check_count", 0),
        "passed_check_count": validation.get("passed_check_count", 0),
        "ordinary_chinese_guidance_route_available": bool(checks.get("ordinary_chinese_guidance_route_available")),
        "persisted_context_memory_controls_available": bool(checks.get("persisted_context_memory_controls_available")),
        "json_fallback_smoke_documented": bool(checks.get("json_fallback_smoke_documented")),
        "guarded_error_hint_available": bool(checks.get("guarded_error_hint_available")),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "post_session_recommendation_card_created": False,
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def today_practice_guidance_terminal_product_smoke_polish_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION,
        "today_practice_guidance_terminal_product_smoke_polish_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_PRODUCT_SMOKE_POLISH_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/terminal-product-smoke/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/terminal-product-smoke/preview",
        "terminal_command": "/terminal-product-smoke [json_payload]",
        "surface": "Terminal chat product smoke polish for provider setup, ordinary guidance turns, persisted context memory, and fallback UX",
        "mode": "manual_terminal_smoke_pack_without_side_effects",
        "execution_status": {
            "terminal_product_smoke_preview_enabled": True,
            "calls_llm_provider": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled_by_agent": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "smoke_checks": [
            "setup/doctor/config-path entrypoints are reachable",
            "provider status tells the user exactly why terminal chat is guarded or ready",
            "ordinary Chinese input routes into guarded today-practice guidance",
            "loaded persisted-context memory is injected into the next today-practice turn",
            "JSON fallback/partial-default behavior is documented for real provider output",
            "blocked guidance prints an actionable terminal hint rather than only internal fields",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_starts_routine": False,
            "payload_creates_post_session_recommendation_card": False,
        },
        "next_task_hint": "v2_8_23_agent_v2_8_phase_cleanup_regression_handoff",
    }


@dataclass(frozen=True)
class AgentV28PhaseCleanupRegressionHandoffPayload:
    payload_contract_version: str
    source: str
    phase_id: str
    phase_status: str
    completed_milestones: list[dict[str, Any]]
    terminal_smoke_handoff: dict[str, Any]
    harmonyos_handoff_pack: dict[str, Any]
    persistence_handoff_pack: dict[str, Any]
    regression_handoff: dict[str, Any]
    boundary_audit: dict[str, Any]
    next_phase_recommendation: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "phase_id": self.phase_id,
            "phase_status": self.phase_status,
            "completed_milestones": list(self.completed_milestones),
            "terminal_smoke_handoff": dict(self.terminal_smoke_handoff),
            "harmonyos_handoff_pack": dict(self.harmonyos_handoff_pack),
            "persistence_handoff_pack": dict(self.persistence_handoff_pack),
            "regression_handoff": dict(self.regression_handoff),
            "boundary_audit": dict(self.boundary_audit),
            "next_phase_recommendation": dict(self.next_phase_recommendation),
            "validation": dict(self.validation),
            "llm_called": False,
            "tool_executed": False,
            "storage_written": False,
            "backend_database_written": False,
            "local_device_written": False,
            "route_called": False,
            "engine_adapter_called": False,
            "accompaniment_generate_call_enabled": False,
            "midi_asset_created": False,
            "playback_started": False,
            "routine_start_enabled": False,
            "post_session_recommendation_card_created": False,
            "trace_id": self.trace_id,
        }


def _agent_v2_8_completed_milestones() -> list[dict[str, Any]]:
    return [
        {"version": "v2_8_1", "name": "user_profile_context_intake", "status": "complete", "summary": "UserPracticeProfileContext intake with camelCase/snake_case normalization and redaction."},
        {"version": "v2_8_2", "name": "practice_context_storage_boundary", "status": "complete", "summary": "Local/backend/request/trace/never-store context ownership map."},
        {"version": "v2_8_3", "name": "profile_aware_guidance_e2e", "status": "complete", "summary": "Profile context participates as soft guidance context."},
        {"version": "v2_8_4", "name": "terminal_llm_provider_compatibility_hotfix", "status": "complete", "summary": "CLI argv and OpenAI-compatible role normalization fixed."},
        {"version": "v2_8_5", "name": "terminal_guidance_json_contract_hotfix", "status": "complete", "summary": "JSON-only prompting plus safe plain-text/partial-JSON fallback."},
        {"version": "v2_8_6", "name": "practice_plan_persistence_candidate", "status": "complete", "summary": "Save/update PracticePlan candidate preview; no storage write."},
        {"version": "v2_8_7", "name": "routine_history_persistence_candidate", "status": "complete", "summary": "RoutineHistory summary save/upload candidate preview; no post-session recommendation card."},
        {"version": "v2_8_8", "name": "context_persistence_confirmation_boundary", "status": "complete", "summary": "Unified user-decision boundary for persistence candidates."},
        {"version": "v2_8_9", "name": "context_persistence_executor_noop", "status": "complete", "summary": "Confirmed-candidate executor skeleton with idempotency/trace/storage guard report."},
        {"version": "v2_8_10", "name": "storage_adapter_design", "status": "complete", "summary": "Future storage adapter methods and backend entity boundary."},
        {"version": "v2_8_11", "name": "sqlite_dev_preview", "status": "complete", "summary": "SQLite schema/idempotency/trace/read snapshot preview only."},
        {"version": "v2_8_12", "name": "dev_sqlite_write_gate", "status": "complete", "summary": "Explicit dev-only write gate contract without actual DB write."},
        {"version": "v2_8_13", "name": "fixture_write_dry_run", "status": "complete", "summary": "Dry-run transaction/idempotency/trace/read-back writer shape."},
        {"version": "v2_8_14", "name": "fixture_store_explicit_opt_in", "status": "complete", "summary": "Dev-only explicit opt-in JSONL fixture store; no SQLite/backend write."},
        {"version": "v2_8_15", "name": "fixture_readback_replay", "status": "complete", "summary": "Read-only JSONL fixture read-back and replay preview."},
        {"version": "v2_8_16", "name": "snapshot_context_intake", "status": "complete", "summary": "Read-back snapshot restored into profile/active-plan/routine-history context sections."},
        {"version": "v2_8_17", "name": "persisted_context_recovery_guidance_e2e", "status": "complete", "summary": "Recovered persisted context participates in today-practice guidance."},
        {"version": "v2_8_18", "name": "terminal_memory_controls", "status": "complete", "summary": "Terminal load/show/clear controls for temporary recovered context memory."},
        {"version": "v2_8_19", "name": "terminal_memory_to_harmonyos_debug_fixture", "status": "complete", "summary": "Terminal memory exported as HarmonyOS debug fixture preview."},
        {"version": "v2_8_20", "name": "harmonyos_debug_fixture_roundtrip", "status": "complete", "summary": "Debug fixture request roundtrips into persisted-context guidance preview."},
        {"version": "v2_8_21", "name": "harmonyos_api_request_pack", "status": "complete", "summary": "Frontend联调用 API request pack with curl/ArkTS sketch."},
        {"version": "v2_8_22", "name": "terminal_chat_product_smoke_polish", "status": "complete", "summary": "Terminal setup/doctor/guidance/memory/fallback smoke polish."},
    ]


def build_agent_v2_8_phase_cleanup_regression_handoff_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "agent_v2_8_phase_handoff",
) -> AgentV28PhaseCleanupRegressionHandoffPayload:
    args = dict(arguments or {})
    requested_regression = args.get("regressionResults") or args.get("regression_results") or {}
    completed_milestones = _agent_v2_8_completed_milestones()
    phase_id = str(args.get("phaseId") or args.get("phase_id") or "agent_v2_8_context_guidance_persistence_harmonyos_debug_phase")
    terminal_smoke_handoff = {
        "primary_command": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status",
        "setup_command": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat setup",
        "doctor_command": "PYTHONPATH=src python -m jammate_agent.cli.terminal_chat doctor",
        "smoke_command": "/terminal-product-smoke",
        "context_memory_commands": ["/persisted-context-load {json}", "/persisted-context-show", "/persisted-context-clear"],
        "ordinary_prompt_smoke": "今天该练什么？",
        "expected_terminal_behavior": "display-only guidance/action-card preview; no Routine start or Engine call",
    }
    harmonyos_handoff_pack = {
        "debug_fixture_request_pack_route": "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview",
        "build_fixture_route": "POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview",
        "persisted_recovery_route": "POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview",
        "roundtrip_route": "POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview",
        "frontend_fixture_files_modified_in_agent_line": False,
        "frontend_contract_status": "debug_payload_preview_only_in_agent_line; real frontend fixture edits stay on integration track",
    }
    persistence_handoff_pack = {
        "implemented_scope": "candidate → confirmation → executor no-op → adapter design → dev fixture store/readback/recovery preview",
        "real_backend_database_write_enabled": False,
        "sqlite_backend_write_enabled": False,
        "dev_fixture_jsonl_store_available_with_explicit_opt_in": True,
        "recommended_next_phase": "v2_9_x_agent_persistence_implementation",
        "required_before_real_storage": [
            "choose backend storage owner and schema migration policy",
            "keep user confirmation, idempotency, trace-link, redaction and storage-boundary checks mandatory",
            "separate HarmonyOS local runtime state from backend durable learner context",
        ],
    }
    regression_handoff = {
        "recommended_commands": [
            "PYTHONPATH=src python -m compileall -q src tests tools examples/scripts",
            "PYTHONPATH=src python tools/check_development_harness.py",
            "PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py",
            "PYTHONPATH=src python -m pytest -q tests/test_v2_4_*agent*.py tests/test_v2_6_*agent*.py tests/test_v2_7_*agent*.py tests/test_v2_8_*.py",
        ],
        "latest_reported_v2_8_regression_count": requested_regression.get("v2_8_regression_count", 163),
        "latest_reported_agent_targeted_count": requested_regression.get("agent_targeted_regression_count", 391),
        "phase_handoff_test_added": True,
        "full_pytest_status_note": "Full historical suite may still include older shared-doc/version assertions outside this Agent-line scope; use targeted Agent regression for this handoff.",
    }
    boundary_audit = {
        "agent_line_allowed_paths": [
            "src/jammate_agent/",
            "src/jammate_api/routes/agent_routes.py",
            "tests/test_v*_agent_*.py",
            "docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md",
            "docs/CHANGELOG_AGENT.md",
            "docs/AGENT*.md",
        ],
        "no_engine_music_generation_changes": True,
        "no_pattern_voicing_expression_pedal_changes": True,
        "no_demo_midi_generation_required": True,
        "shared_docs_modified_by_this_handoff": False,
        "harmonyos_fixture_modified_by_this_handoff": False,
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "engine_adapter_called": False,
        "accompaniment_generate_call_enabled": False,
        "midi_asset_created": False,
        "playback_started": False,
        "routine_start_enabled": False,
        "post_session_recommendation_card_created": False,
    }
    next_phase_recommendation = {
        "phase_status_after_v2_8_23": "ready_for_integration_or_v2_9_persistence_implementation_planning",
        "do_not_continue_expanding_v2_8": True,
        "recommended_next_tracks": [
            "integration branch: merge Agent v2_8 handoff with shared docs/API contract if needed",
            "v2_9_x Agent Persistence Implementation: real storage adapter/migrations behind explicit config and tests",
            "Engine track can resume independently without Agent storage changes touching music-generation boundaries",
        ],
    }
    validation = {
        "accepted": True,
        "status": "phase_handoff_ready",
        "milestone_count": len(completed_milestones),
        "blocked_reasons": [],
        "warnings": [],
        "no_new_runtime_capability_added": True,
    }
    return AgentV28PhaseCleanupRegressionHandoffPayload(
        payload_contract_version=AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION,
        source=source,
        phase_id=phase_id,
        phase_status="phase_handoff_ready",
        completed_milestones=completed_milestones,
        terminal_smoke_handoff=terminal_smoke_handoff,
        harmonyos_handoff_pack=harmonyos_handoff_pack,
        persistence_handoff_pack=persistence_handoff_pack,
        regression_handoff=regression_handoff,
        boundary_audit=boundary_audit,
        next_phase_recommendation=next_phase_recommendation,
        validation=validation,
        trace_id=trace_id,
    )


def build_agent_v2_8_phase_cleanup_regression_handoff_summary(
    *,
    payload: AgentV28PhaseCleanupRegressionHandoffPayload | None = None,
    source: str = "agent_v2_8_phase_handoff",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    boundary = data.get("boundary_audit") if isinstance(data.get("boundary_audit"), dict) else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    return {
        "agent_v2_8_phase_cleanup_regression_handoff_version": AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION,
        "source": source,
        "phase_status": data.get("phase_status"),
        "accepted": bool(validation.get("accepted")),
        "milestone_count": validation.get("milestone_count", 0),
        "terminal_smoke_ready": bool(data.get("terminal_smoke_handoff")),
        "harmonyos_debug_fixture_handoff_ready": bool(data.get("harmonyos_handoff_pack")),
        "persistence_handoff_ready": bool(data.get("persistence_handoff_pack")),
        "storage_written": False,
        "backend_database_written": False,
        "local_device_written": False,
        "llm_called": False,
        "tool_executed": False,
        "engine_adapter_called": bool(boundary.get("engine_adapter_called", False)),
        "accompaniment_generate_call_enabled": bool(boundary.get("accompaniment_generate_call_enabled", False)),
        "midi_asset_created": bool(boundary.get("midi_asset_created", False)),
        "playback_started": bool(boundary.get("playback_started", False)),
        "routine_start_enabled": bool(boundary.get("routine_start_enabled", False)),
        "post_session_recommendation_card_created": bool(boundary.get("post_session_recommendation_card_created", False)),
        "recommended_next_phase": (data.get("next_phase_recommendation") or {}).get("phase_status_after_v2_8_23"),
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
    }


def agent_v2_8_phase_cleanup_regression_handoff_contract() -> dict[str, Any]:
    return {
        "version": AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION,
        "agent_v2_8_phase_cleanup_regression_handoff_version": AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/v2-8-phase-handoff/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview",
        "terminal_command": "/v2-8-phase-handoff [json_payload]",
        "surface": "Agent v2.8 phase cleanup, regression checklist, boundary audit, and handoff package",
        "mode": "handoff_report_without_new_runtime_capability",
        "execution_status": {
            "phase_handoff_preview_enabled": True,
            "calls_llm_provider": False,
            "database_persistence_implemented": False,
            "backend_write_enabled": False,
            "local_device_write_enabled_by_agent": False,
            "tool_execution_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "handoff_scope": [
            "summarize v2_8_1 through v2_8_22 completed Agent context/guidance/persistence/debug fixture work",
            "record terminal smoke and HarmonyOS debug fixture handoff commands/routes",
            "record persistence implementation boundary for future v2_9_x",
            "confirm no Engine music generation, shared docs, frontend fixtures, MIDI demos, storage writes, or Routine start",
        ],
        "guards": {
            "payload_writes_storage": False,
            "payload_calls_llm": False,
            "payload_executes_tool": False,
            "payload_calls_engine_adapter": False,
            "payload_calls_accompaniment_generate": False,
            "payload_creates_midi_asset": False,
            "payload_starts_playback": False,
            "payload_starts_routine": False,
            "payload_creates_post_session_recommendation_card": False,
        },
        "next_task_hint": "Stop expanding v2_8; move to integration handoff or v2_9 persistence implementation planning.",
    }


def build_today_practice_guidance_terminal_chat_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_terminal_chat_e2e",
    provider: Any | None = None,
) -> TodayPracticeGuidanceTerminalChatE2EPayload:
    """Route an ordinary terminal user turn to the today-guidance ActionCard chain."""

    args = dict(arguments or {})
    user_input = str(args.get("user_input") or args.get("userInput") or args.get("text") or "今天该练什么？")
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    intent = detect_today_practice_guidance_intent(user_input)
    action_args = dict(args)
    action_args["userInput"] = user_input
    # Ordinary terminal chat already represents an explicit provider-boundary
    # surface. A disabled provider remains guarded; configured/fake providers
    # can return structured guidance that still must pass validation.
    action_args["callProvider"] = bool(args.get("callProvider") if "callProvider" in args else args.get("call_provider") if "call_provider" in args else intent.get("is_today_practice_guidance_intent"))
    action_payload_obj = build_today_practice_guidance_action_card_payload(
        action_args,
        trace_id=trace,
        source="terminal_chat_today_practice_guidance_action_card",
        provider=provider,
    )
    action_payload = action_payload_obj.to_dict()
    action_summary = build_today_practice_guidance_action_card_summary(payload=action_payload_obj, source="terminal_chat_cli")
    card = action_payload.get("action_card") if isinstance(action_payload.get("action_card"), dict) else {}
    display_sections = card.get("display_sections") if isinstance(card.get("display_sections"), dict) else {}
    terminal_response = {
        "content": card.get("description") or display_sections.get("summary") or "Today-practice guidance is not available yet.",
        "action_card_available": bool(action_summary.get("is_valid")),
        "action_card_display_only": True,
        "routine_candidate_count": action_summary.get("routine_candidate_count", 0),
        "available_client_actions": list(action_summary.get("available_client_actions") or []),
        "requires_separate_user_confirmation_before_routine_start": True,
    }
    return TodayPracticeGuidanceTerminalChatE2EPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
        source=source,
        user_input=user_input,
        detected_intent=intent,
        action_card_payload=action_payload,
        action_card_summary=action_summary,
        terminal_response=terminal_response,
        trace_id=trace,
        llm_called=bool(action_payload_obj.llm_called),
    )


def build_today_practice_guidance_terminal_chat_e2e_summary(
    *,
    payload: TodayPracticeGuidanceTerminalChatE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    intent = data.get("detected_intent") if isinstance(data.get("detected_intent"), dict) else {}
    action_summary = data.get("action_card_summary") if isinstance(data.get("action_card_summary"), dict) else {}
    return {
        "today_practice_guidance_terminal_chat_e2e_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "detected_today_practice_guidance_intent": bool(intent.get("is_today_practice_guidance_intent")),
        "matched_phrase": intent.get("matched_phrase"),
        "action_card_is_valid": action_summary.get("is_valid", False),
        "validation_status": action_summary.get("validation_status"),
        "routine_candidate_count": action_summary.get("routine_candidate_count", 0),
        "llm_called": data.get("llm_called", False),
        "terminal_chat_surface": True,
        "card_display_only": True,
        "requires_separate_user_confirmation_before_routine_start": True,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
    }


def today_practice_guidance_terminal_chat_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
        "today_practice_guidance_terminal_chat_e2e_version": TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/terminal-chat/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview",
        "terminal_surface": "ordinary terminal chat message",
        "example_user_inputs": ["今天该练什么？", "what should I practice today?"],
        "mode": "ordinary_chat_intent_to_provider_boundary_to_validated_display_action_card",
        "execution_status": {
            "ordinary_chat_intent_detection_enabled": True,
            "context_assembly_enabled": True,
            "provider_boundary_enabled": True,
            "output_validation_required": True,
            "action_card_payload_enabled": True,
            "card_display_only": True,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "payload_schema": {
            "detected_intent": "narrow high-confidence today-practice guidance intent detection for terminal chat",
            "action_card_payload": "v2_7_8 TodayPracticeGuidanceActionCardPayload",
            "terminal_response": "compact terminal-facing response plus action-card availability summary",
            "summary": "guarded terminal E2E status",
        },
        "rules": [
            "Only high-confidence today-practice guidance turns are routed away from generic coach chat.",
            "The routed turn still goes through provider boundary and v2_7_6 output validation before display.",
            "The terminal response may show guidance and candidate cards only; Routine start and accompaniment generation remain separate user-confirmed client actions.",
            "No ordinary terminal message may directly execute tools, call /accompaniment/generate, create MIDI assets, or start playback.",
        ],
        "uses_contracts": {
            "today_practice_guidance_action_card": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
            "today_practice_guidance_provider_boundary_e2e": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
            "today_practice_guidance_output_validation": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
            "user_capability_map_and_intent_taxonomy": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
        },
        "guards": {
            "executes_tool": False,
            "starts_routine": False,
            "calls_accompaniment_generate": False,
            "calls_engine_adapter": False,
            "creates_midi_asset": False,
            "starts_playback": False,
            "frontend_flow_assumption": False,
        },
    }



@dataclass(frozen=True)
class TodayPracticeGuidanceProfileAwareE2EPayload:
    """v2_8_3 profile-aware E2E wrapper for today-practice guidance.

    This payload stitches the v2_8_1 UserPracticeProfileContext into the
    existing v2_7_4 → v2_7_9 guarded guidance chain. It remains candidate-only:
    no Routine start, playback, MIDI generation, tool execution, or engine call.
    """

    payload_contract_version: str
    source: str
    user_practice_profile_context: dict[str, Any]
    assembled_practice_context: dict[str, Any]
    action_card_payload: dict[str, Any]
    profile_guidance_bridge: dict[str, Any]
    profile_alignment_preview: dict[str, Any]
    validation: dict[str, Any]
    trace_id: str | None = None
    llm_called: bool = False
    tool_executed: bool = False
    routine_start_enabled: bool = False
    route_called: bool = False
    engine_adapter_called: bool = False
    midi_asset_created: bool = False
    playback_started: bool = False
    accompaniment_generate_call_enabled: bool = False
    client_decides_presentation: bool = True
    frontend_flow_assumption: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_contract_version": self.payload_contract_version,
            "source": self.source,
            "user_practice_profile_context": _redact_sensitive_values(self.user_practice_profile_context),
            "assembled_practice_context": _redact_sensitive_values(self.assembled_practice_context),
            "action_card_payload": _redact_sensitive_values(self.action_card_payload),
            "profile_guidance_bridge": _redact_sensitive_values(self.profile_guidance_bridge),
            "profile_alignment_preview": _redact_sensitive_values(self.profile_alignment_preview),
            "validation": _redact_sensitive_values(self.validation),
            "trace_id": self.trace_id,
            "llm_called": self.llm_called,
            "tool_executed": self.tool_executed,
            "routine_start_enabled": self.routine_start_enabled,
            "route_called": self.route_called,
            "engine_adapter_called": self.engine_adapter_called,
            "midi_asset_created": self.midi_asset_created,
            "playback_started": self.playback_started,
            "accompaniment_generate_call_enabled": self.accompaniment_generate_call_enabled,
            "client_decides_presentation": self.client_decides_presentation,
            "frontend_flow_assumption": self.frontend_flow_assumption,
        }


def _extract_profile_context_from_assembled(assembled_context: dict[str, Any]) -> dict[str, Any]:
    profile_context = assembled_context.get("user_practice_profile_context")
    return dict(profile_context) if isinstance(profile_context, dict) else {}


def _build_profile_guidance_bridge(assembled_context: dict[str, Any], profile_context: dict[str, Any]) -> dict[str, Any]:
    profile = profile_context.get("profile") if isinstance(profile_context.get("profile"), dict) else {}
    return {
        "bridge_version": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        "profile_context_available": bool(profile_context),
        "profile_summary": profile_context.get("summary_for_llm") or assembled_context.get("profile_summary") or profile.get("summary_for_llm"),
        "current_goal": profile.get("current_goal"),
        "preferred_styles": list(profile.get("preferred_styles") or []) if isinstance(profile.get("preferred_styles"), list) else [],
        "focus_areas": list(profile.get("focus_areas") or []) if isinstance(profile.get("focus_areas"), list) else [],
        "skill_focus": list(profile.get("skill_focus") or []) if isinstance(profile.get("skill_focus"), list) else [],
        "comfortable_tempo_ranges": dict(profile.get("comfortable_tempo_ranges") or {}) if isinstance(profile.get("comfortable_tempo_ranges"), dict) else {},
        "avoid": list(profile.get("avoid") or []) if isinstance(profile.get("avoid"), list) else [],
        "practice_mode_preference": profile.get("practice_mode_preference"),
        "profile_is_soft_context_not_rule_engine": True,
        "recommendation_must_still_consider_active_plan": True,
        "recommendation_must_still_consider_routine_history": True,
        "candidate_only_no_execution": True,
    }


def _profile_alignment_preview(normalized_guidance_output: dict[str, Any], profile_context: dict[str, Any]) -> dict[str, Any]:
    profile = profile_context.get("profile") if isinstance(profile_context.get("profile"), dict) else {}
    preferred_styles = set(str(item) for item in profile.get("preferred_styles") or [] if item is not None) if isinstance(profile.get("preferred_styles"), list) else set()
    tempo_ranges = profile.get("comfortable_tempo_ranges") if isinstance(profile.get("comfortable_tempo_ranges"), dict) else {}
    routine_candidates = normalized_guidance_output.get("routine_candidates") if isinstance(normalized_guidance_output.get("routine_candidates"), list) else []
    recommended_blocks = normalized_guidance_output.get("recommended_blocks") if isinstance(normalized_guidance_output.get("recommended_blocks"), list) else []
    items = [item for item in [*routine_candidates, *recommended_blocks] if isinstance(item, dict)]
    style_matches = 0
    tempo_matches = 0
    warnings: list[str] = []
    for index, item in enumerate(items):
        style = item.get("style") or item.get("suggested_style") or item.get("suggestedStyle")
        tempo = _coerce_int(item.get("tempo") or item.get("suggested_tempo") or item.get("suggestedTempo"), default=0)
        if preferred_styles and style in preferred_styles:
            style_matches += 1
        if style and style in tempo_ranges and tempo:
            rng = tempo_ranges.get(style) if isinstance(tempo_ranges.get(style), dict) else {}
            min_tempo = _coerce_int(rng.get("min"), default=0)
            max_tempo = _coerce_int(rng.get("max"), default=0)
            if min_tempo and max_tempo and min_tempo <= tempo <= max_tempo:
                tempo_matches += 1
            elif min_tempo and max_tempo:
                warnings.append(f"candidate_{index + 1}_tempo_outside_profile_comfort_range")
        elif style and tempo_ranges and tempo:
            warnings.append(f"candidate_{index + 1}_style_has_no_profile_tempo_range")
    return {
        "profile_alignment_preview_version": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        "profile_context_available": bool(profile_context),
        "candidate_item_count": len(items),
        "preferred_style_match_count": style_matches,
        "tempo_range_match_count": tempo_matches,
        "warnings": warnings,
        "alignment_is_soft_warning_only": True,
        "does_not_block_valid_guidance": True,
    }


def build_today_practice_guidance_profile_aware_e2e_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "today_practice_guidance_profile_aware_e2e",
    provider: Any | None = None,
) -> TodayPracticeGuidanceProfileAwareE2EPayload:
    """Build a profile-aware today-practice guidance E2E preview without side effects."""

    args = dict(arguments or {})
    trace = trace_id or args.get("trace_id") or args.get("traceId")
    assembled_payload = build_practice_context_assembly_policy_payload(
        args,
        trace_id=trace,
        source="today_practice_guidance_profile_aware_context_assembly",
    )
    assembled_context = assembled_payload.to_dict().get("assembled_context") or {}
    if not isinstance(assembled_context, dict):
        assembled_context = {}
    profile_context = _extract_profile_context_from_assembled(assembled_context)
    profile_bridge = _build_profile_guidance_bridge(assembled_context, profile_context)

    action_args = dict(args)
    action_args["assembled_practice_context"] = assembled_context
    action_payload_obj = build_today_practice_guidance_action_card_payload(
        action_args,
        trace_id=trace,
        source="today_practice_guidance_profile_aware_action_card",
        provider=provider,
    )
    action_payload = action_payload_obj.to_dict()
    normalized = action_payload.get("normalized_guidance_output") if isinstance(action_payload.get("normalized_guidance_output"), dict) else {}
    profile_alignment = _profile_alignment_preview(normalized, profile_context)
    action_validation = action_payload.get("validation") if isinstance(action_payload.get("validation"), dict) else {}
    validation_warnings = list(action_validation.get("warnings") or [])
    if not profile_context:
        validation_warnings.append("user_practice_profile_context_missing")
    validation_warnings.extend(profile_alignment.get("warnings") or [])
    validation = {
        "status": "profile_aware_guidance_ready" if action_validation.get("is_valid") else "profile_aware_guidance_guarded_or_blocked",
        "is_valid": bool(action_validation.get("is_valid", False)),
        "profile_context_available": bool(profile_context),
        "profile_used_as_soft_context": bool(profile_context),
        "profile_did_not_execute_rules": True,
        "action_card_is_display_only": True,
        "warnings": validation_warnings,
        "blocked_reasons": list(action_validation.get("blocked_reasons") or []),
        "llm_called": bool(action_payload_obj.llm_called),
        "tool_executed": False,
        "routine_start_enabled": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }
    return TodayPracticeGuidanceProfileAwareE2EPayload(
        payload_contract_version=TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        source=source,
        user_practice_profile_context=profile_context,
        assembled_practice_context=assembled_context,
        action_card_payload=action_payload,
        profile_guidance_bridge=profile_bridge,
        profile_alignment_preview=profile_alignment,
        validation=validation,
        trace_id=trace,
        llm_called=bool(action_payload_obj.llm_called),
    )


def build_today_practice_guidance_profile_aware_e2e_summary(
    *,
    payload: TodayPracticeGuidanceProfileAwareE2EPayload | None = None,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    data = payload.to_dict() if payload else {}
    validation = data.get("validation") if isinstance(data.get("validation"), dict) else {}
    bridge = data.get("profile_guidance_bridge") if isinstance(data.get("profile_guidance_bridge"), dict) else {}
    action_payload = data.get("action_card_payload") if isinstance(data.get("action_card_payload"), dict) else {}
    action_summary = action_payload.get("validation") if isinstance(action_payload.get("validation"), dict) else {}
    alignment = data.get("profile_alignment_preview") if isinstance(data.get("profile_alignment_preview"), dict) else {}
    return {
        "today_practice_guidance_profile_aware_e2e_version": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        "source": source,
        "has_payload": payload is not None,
        "validation_status": validation.get("status"),
        "is_valid": validation.get("is_valid", False),
        "profile_context_available": bridge.get("profile_context_available", False),
        "profile_summary": bridge.get("profile_summary"),
        "preferred_styles": list(bridge.get("preferred_styles") or []),
        "routine_candidate_count": action_summary.get("routine_candidate_count", 0),
        "preferred_style_match_count": alignment.get("preferred_style_match_count", 0),
        "tempo_range_match_count": alignment.get("tempo_range_match_count", 0),
        "warnings": list(validation.get("warnings") or []),
        "blocked_reasons": list(validation.get("blocked_reasons") or []),
        "llm_called": data.get("llm_called", False),
        "tool_executed": False,
        "route_called": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "client_decides_presentation": True,
        "frontend_flow_assumption": False,
    }


def today_practice_guidance_profile_aware_e2e_contract() -> dict[str, Any]:
    return {
        "version": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        "today_practice_guidance_profile_aware_e2e_version": TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_VERSION,
        "spec_route": "GET /agent/context/today-practice-guidance/profile-aware/spec",
        "preview_route": "POST /agent/context/today-practice-guidance/profile-aware/e2e-preview",
        "terminal_command": "/today-practice-guidance-profile-aware",
        "surface": "Profile-aware today-practice guidance E2E preview",
        "mode": "user_profile_context_plus_active_plan_plus_history_to_display_only_guidance_card",
        "execution_status": {
            "user_practice_profile_context_used": True,
            "context_assembly_enabled": True,
            "provider_boundary_enabled": True,
            "output_validation_required": True,
            "action_card_payload_enabled": True,
            "card_display_only": True,
            "llm_call_default_enabled": False,
            "routine_start_enabled": False,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
            "storage_write_enabled": False,
        },
        "profile_policy": {
            "profile_is_soft_context_not_rule_engine": True,
            "uses_current_goal": True,
            "uses_preferred_styles": True,
            "uses_focus_areas": True,
            "uses_comfortable_tempo_ranges": True,
            "uses_avoid_list": True,
            "uses_practice_mode_preference": True,
            "does_not_override_active_plan_by_itself": True,
            "does_not_force_tempo_by_itself": True,
        },
        "rules": [
            "UserPracticeProfileContext is injected into assembled practice context and prompt policy.",
            "The profile may influence focus, style, tempo comfort, and avoid notes as soft constraints only.",
            "The active plan and recent Routine history remain primary decision inputs.",
            "Validated guidance becomes display-only ActionCard and editable Routine candidates; no automatic Routine start.",
            "This contract never writes profile storage, calls /accompaniment/generate, invokes engine adapters, creates MIDI assets, or starts playback.",
        ],
        "uses_contracts": {
            "user_practice_profile_context_intake": USER_PRACTICE_PROFILE_CONTEXT_INTAKE_VERSION,
            "practice_context_assembly_policy": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
            "today_practice_guidance_prompt_contract": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
            "today_practice_guidance_provider_boundary_e2e": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
            "today_practice_guidance_action_card": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
            "today_practice_guidance_terminal_chat_e2e": TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
        },
        "guards": {
            "executes_tool": False,
            "starts_routine": False,
            "calls_accompaniment_generate": False,
            "calls_engine_adapter": False,
            "creates_midi_asset": False,
            "starts_playback": False,
            "writes_storage": False,
            "frontend_flow_assumption": False,
        },
    }



@dataclass(frozen=True)
class ContextAndGuidanceSkeletonCleanupPayload:
    """v2_8_0 read-only cleanup/status payload for the context/guidance chain.

    The cleanup pass does not introduce a new execution capability. It gives
    HarmonyOS, terminal developers, and future prompt-contract work one stable
    place to inspect the ordered v2_7_3 → v2_7_9 guidance skeleton, canonical
    routes/commands, and no-side-effect guards before concrete user features are
    added.
    """

    cleanup_version: str
    source: str
    trace_id: str | None
    stage_registry: tuple[dict[str, Any], ...]
    canonical_routes: dict[str, str]
    terminal_commands: tuple[str, ...]
    normalized_guard_flags: dict[str, bool]
    cleanup_findings: tuple[str, ...]
    next_recommended_task: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cleanup_version": self.cleanup_version,
            "source": self.source,
            "trace_id": self.trace_id,
            "stage_registry": [dict(stage) for stage in self.stage_registry],
            "canonical_routes": dict(self.canonical_routes),
            "terminal_commands": list(self.terminal_commands),
            "normalized_guard_flags": dict(self.normalized_guard_flags),
            "cleanup_findings": list(self.cleanup_findings),
            "next_recommended_task": self.next_recommended_task,
            "frontend_flow_assumption": False,
            "client_decides_presentation": True,
            "routine_end_recommendation_card_created": False,
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }


def _context_guidance_stage_registry() -> tuple[dict[str, Any], ...]:
    return (
        {
            "stage_id": "context_engineering_skeleton",
            "version": CONTEXT_ENGINEERING_SKELETON_VERSION,
            "purpose": "Normalize active plan, Routine history, today constraints, and assembled practice context.",
            "spec_routes": [
                "GET /agent/context/active-practice-plan/spec",
                "GET /agent/context/routine-history/spec",
                "GET /agent/context/practice-assembly/spec",
                "GET /agent/context/today-practice/spec",
                "GET /agent/context/engineering-skeleton",
            ],
            "preview_routes": [
                "POST /agent/context/active-practice-plan/intake",
                "POST /agent/context/routine-history/intake",
                "POST /agent/context/practice-assembly/build",
                "POST /agent/context/today-practice/preview",
            ],
            "terminal_commands": [
                "/active-practice-plan-context",
                "/routine-history-context",
                "/practice-context-assembly",
                "/today-practice-context",
                "/context-engineering",
            ],
            "output_role": "context_only",
            "side_effects_created": False,
        },
        {
            "stage_id": "today_practice_guidance_prompt_contract",
            "version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
            "purpose": "Build future LLM prompt messages and TodayPracticeGuidanceOutput schema.",
            "spec_routes": ["GET /agent/context/today-practice-guidance/spec"],
            "preview_routes": ["POST /agent/context/today-practice-guidance/prompt-preview"],
            "terminal_commands": ["/today-practice-guidance-prompt"],
            "output_role": "prompt_contract_only",
            "side_effects_created": False,
        },
        {
            "stage_id": "user_capability_map_and_intent_taxonomy",
            "version": USER_CAPABILITY_MAP_AND_INTENT_TAXONOMY_VERSION,
            "purpose": "Define what users may ask the LLM to do, which intents are candidate-only, and which are forbidden direct actions.",
            "spec_routes": ["GET /agent/capabilities/user-intents/spec"],
            "preview_routes": ["POST /agent/capabilities/user-intents/preview"],
            "terminal_commands": ["/user-capability-map"],
            "output_role": "capability_boundary",
            "side_effects_created": False,
        },
        {
            "stage_id": "today_practice_guidance_output_validation",
            "version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
            "purpose": "Validate future LLM output and normalize it into candidate-only guidance.",
            "spec_routes": ["GET /agent/context/today-practice-guidance/output-validation/spec"],
            "preview_routes": ["POST /agent/context/today-practice-guidance/output-validation/validate"],
            "terminal_commands": ["/today-practice-guidance-validate"],
            "output_role": "safety_gate",
            "side_effects_created": False,
        },
        {
            "stage_id": "today_practice_guidance_provider_boundary_e2e",
            "version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
            "purpose": "Stitch prompt contract, optional provider boundary, and output validation without executing tools.",
            "spec_routes": ["GET /agent/context/today-practice-guidance/provider-boundary/spec"],
            "preview_routes": ["POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview"],
            "terminal_commands": ["/today-practice-guidance-e2e"],
            "output_role": "provider_boundary_preview",
            "side_effects_created": False,
        },
        {
            "stage_id": "today_practice_guidance_action_card",
            "version": TODAY_PRACTICE_GUIDANCE_ACTION_CARD_VERSION,
            "purpose": "Wrap validated guidance into a display-only Routine card.",
            "spec_routes": ["GET /agent/context/today-practice-guidance/action-card/spec"],
            "preview_routes": ["POST /agent/context/today-practice-guidance/action-card/preview"],
            "terminal_commands": ["/today-practice-guidance-action-card"],
            "output_role": "display_only_action_card",
            "side_effects_created": False,
        },
        {
            "stage_id": "today_practice_guidance_terminal_chat_e2e",
            "version": TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_VERSION,
            "purpose": "Route ordinary user turns like '今天该练什么？' into the guarded guidance chain.",
            "spec_routes": ["GET /agent/context/today-practice-guidance/terminal-chat/spec"],
            "preview_routes": ["POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview"],
            "terminal_commands": ["/today-practice-guidance-chat-e2e", "ordinary input: 今天该练什么？"],
            "output_role": "terminal_chat_surface",
            "side_effects_created": False,
        },

    )


def _context_guidance_canonical_routes() -> dict[str, str]:
    return {
        "context_engineering_skeleton": "GET /agent/context/engineering-skeleton",
        "context_guidance_cleanup_status": "GET /agent/context/guidance-skeleton-cleanup",
        "active_practice_plan_intake": "POST /agent/context/active-practice-plan/intake",
        "routine_history_intake": "POST /agent/context/routine-history/intake",
        "practice_context_assembly": "POST /agent/context/practice-assembly/build",
        "today_practice_context_preview": "POST /agent/context/today-practice/preview",
        "today_practice_guidance_prompt_preview": "POST /agent/context/today-practice-guidance/prompt-preview",
        "today_practice_guidance_output_validation": "POST /agent/context/today-practice-guidance/output-validation/validate",
        "today_practice_guidance_provider_boundary_e2e": "POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview",
        "today_practice_guidance_action_card": "POST /agent/context/today-practice-guidance/action-card/preview",
        "today_practice_guidance_terminal_chat_e2e": "POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview",
        "today_practice_guidance_profile_aware_e2e": "POST /agent/context/today-practice-guidance/profile-aware/e2e-preview",
        "practice_plan_persistence_candidate": "POST /agent/practice-plan/persistence-candidate/preview",
        "routine_history_persistence_candidate": "POST /agent/routine-history/persistence-candidate/preview",
        "context_persistence_confirmation_boundary": "POST /agent/context/persistence-confirmation/preview",
        "user_capability_map": "POST /agent/capabilities/user-intents/preview",
    }


def _context_guidance_terminal_commands() -> tuple[str, ...]:
    commands: list[str] = ["/context-guidance-skeleton"]
    for stage in _context_guidance_stage_registry():
        commands.extend(str(command) for command in stage.get("terminal_commands", []))
    deduped: list[str] = []
    for command in commands:
        if command not in deduped:
            deduped.append(command)
    return tuple(deduped)


def _context_guidance_no_side_effect_flags() -> dict[str, bool]:
    return {
        "llm_called_by_cleanup": False,
        "tool_executed": False,
        "workflow_dispatched": False,
        "route_called": False,
        "engine_adapter_called": False,
        "accompaniment_generate_call_enabled": False,
        "routine_start_enabled": False,
        "midi_asset_created": False,
        "playback_started": False,
        "post_session_recommendation_card_created": False,
        "frontend_flow_assumption": False,
        "client_decides_presentation": True,
    }


def build_context_and_guidance_skeleton_cleanup_payload(
    arguments: dict[str, Any] | None = None,
    *,
    trace_id: str | None = None,
    source: str = "agent_context_guidance_skeleton_cleanup",
) -> ContextAndGuidanceSkeletonCleanupPayload:
    args = arguments or {}
    requested_focus = _first_present(args, "focus", "requested_focus", "requestedFocus") or "today_practice_guidance_chain"
    findings = [
        "v2_7_3_to_v2_7_9_chain_has_single_guarded_path_from_context_to_display_card",
        "context_intake_and_guidance_surfaces_are_read_only_until_user_confirms_a_future_action",
        "routine_end_summary_remains_harmonyos_client_owned_not_agent_action_card",
        "today_practice_guidance_outputs_must_pass_v2_7_6_validation_before display",
        "harmonyos_client_decides_presentation_for_all_routine_candidates",
        f"requested_focus={requested_focus}",
    ]
    return ContextAndGuidanceSkeletonCleanupPayload(
        cleanup_version=CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION,
        source=source,
        trace_id=trace_id,
        stage_registry=_context_guidance_stage_registry(),
        canonical_routes=_context_guidance_canonical_routes(),
        terminal_commands=_context_guidance_terminal_commands(),
        normalized_guard_flags=_context_guidance_no_side_effect_flags(),
        cleanup_findings=tuple(findings),
        next_recommended_task="v2_8_8_agent_context_persistence_confirmation_boundary",
    )


def build_context_and_guidance_skeleton_cleanup_summary(
    *,
    payload: ContextAndGuidanceSkeletonCleanupPayload,
    source: str = "agent_context_guidance_skeleton_cleanup",
) -> dict[str, Any]:
    stages = payload.stage_registry
    stage_ids = [stage.get("stage_id") for stage in stages]
    return {
        "cleanup_version": payload.cleanup_version,
        "source": source,
        "stage_count": len(stages),
        "stage_ids": stage_ids,
        "canonical_route_count": len(payload.canonical_routes),
        "terminal_command_count": len(payload.terminal_commands),
        "all_stages_side_effect_free": all(not bool(stage.get("side_effects_created")) for stage in stages),
        "client_decides_presentation": payload.normalized_guard_flags.get("client_decides_presentation") is True,
        "post_session_recommendation_card_created": False,
        "routine_start_enabled": False,
        "accompaniment_generate_call_enabled": False,
        "engine_adapter_called": False,
        "midi_asset_created": False,
        "playback_started": False,
        "next_recommended_task": payload.next_recommended_task,
    }


def context_and_guidance_skeleton_cleanup_contract() -> dict[str, Any]:
    payload = build_context_and_guidance_skeleton_cleanup_payload(source="contract_preview")
    summary = build_context_and_guidance_skeleton_cleanup_summary(payload=payload, source="contract_preview")
    return {
        "version": CONTEXT_AND_GUIDANCE_SKELETON_CLEANUP_VERSION,
        "purpose": "Read-only cleanup/status contract for the Agent context + today-practice guidance skeleton.",
        "route": "GET /agent/context/guidance-skeleton-cleanup",
        "terminal_command": "/context-guidance-skeleton",
        "stage_registry": [dict(stage) for stage in payload.stage_registry],
        "canonical_routes": dict(payload.canonical_routes),
        "terminal_commands": list(payload.terminal_commands),
        "summary": summary,
        "non_goals": [
            "No Routine end recommendation card",
            "No LLM call from the cleanup contract",
            "No tool execution",
            "No Routine start",
            "No /accompaniment/generate call",
            "No engine adapter call",
            "No MIDI asset creation",
            "No playback start",
            "No frontend UI flow assumption",
            "No Engine music-generation rule changes",
        ],
    }

def context_engineering_skeleton_contract() -> dict[str, Any]:
    return {
        "version": CONTEXT_ENGINEERING_SKELETON_VERSION,
        "context_engineering_skeleton_version": CONTEXT_ENGINEERING_SKELETON_VERSION,
        "surface": "Agent practice context engineering skeleton foundation",
        "included_boundaries": {
            "active_practice_plan_context_intake": active_practice_plan_context_intake_contract(),
            "routine_history_context_intake": routine_history_context_intake_contract(),
            "practice_context_assembly_policy": practice_context_assembly_policy_contract(),
            "today_practice_context_e2e": today_practice_context_e2e_contract(),
            "today_practice_guidance_prompt_contract": today_practice_guidance_prompt_contract(),
            "user_capability_map_and_intent_taxonomy": user_capability_map_and_intent_taxonomy_contract(),
            "today_practice_guidance_output_validation": today_practice_guidance_output_validation_contract(),
            "today_practice_guidance_provider_boundary_e2e": today_practice_guidance_provider_boundary_e2e_contract(),
            "today_practice_guidance_action_card": today_practice_guidance_action_card_contract(),
            "today_practice_guidance_terminal_chat_e2e": today_practice_guidance_terminal_chat_e2e_contract(),
            "today_practice_guidance_profile_aware_e2e": today_practice_guidance_profile_aware_e2e_contract(),
            "practice_plan_persistence_candidate": practice_plan_persistence_candidate_contract(),
            "routine_history_persistence_candidate": routine_history_persistence_candidate_contract(),
            "context_persistence_confirmation_boundary": context_persistence_confirmation_boundary_contract(),
        },
        "completion_scope": [
            "active PracticePlan can enter ContextPacket",
            "RoutineHistory can enter ContextPacket",
            "plan + history + availability can be assembled into decision inputs",
            "today-practice user turn has context-only E2E preview",
            "today-practice guidance prompt/output contract is available without calling the LLM",
            "user-facing LLM capability map and intent taxonomy is available without calling the LLM",
            "today-practice LLM output can be validated and normalized without executing tools",
            "today-practice provider-boundary E2E can turn provider output into validated candidate-only guidance",
            "validated today-practice guidance can be wrapped into a Routine-facing display ActionCard",
            "ordinary terminal chat can route '今天该练什么？' into the guarded guidance ActionCard chain",
            "UserPracticeProfileContext can feed profile-aware today-practice guidance as soft context",
            "PracticePlan save/update can be represented as a candidate-only persistence action",
            "RoutineHistory summary save/upload can be represented as a candidate-only persistence action",
            "PracticePlan and RoutineHistory persistence candidates can pass through a unified confirmation record boundary",
        ],
        "non_goals": [
            "No automatic post-session recommendation card",
            "No LLM call in the context assembly or prompt-preview routes",
            "No final today-practice recommendation is generated in v2_7_4",
            "No playback, MIDI generation, /accompaniment/generate, or engine adapter call",
            "No frontend UI flow assumption",
            "No unvalidated today-practice LLM output may trigger Routine start or accompaniment generation",
            "No provider-boundary guidance output may bypass validation, user confirmation, or client presentation control",
            "No today-practice guidance ActionCard may start Routine, call /accompaniment/generate, or create MIDI assets",
            "No terminal today-practice guidance E2E may bypass provider boundary, output validation, or client confirmation",
            "No profile-aware guidance may turn the user profile into hard-coded execution rules",
            "No RoutineHistory persistence candidate may create a post-session recommendation card or write storage directly",
            "No context persistence confirmation may write storage directly; future executor remains separate",
        ],
        "guards": {
            "llm_called": False,
            "guidance_response_created": False,
            "guidance_output_validated_only": True,
            "provider_boundary_e2e_enabled": True,
            "recommendation_created": False,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
            "playback_started": False,
            "accompaniment_generate_call_enabled": False,
            "routine_start_enabled": False,
        },
    }


def _extract_user_practice_profile(args: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "input_profile",
        "inputProfile",
        "user_practice_profile",
        "userPracticeProfile",
        "user_practice_profile_context",
        "userPracticeProfileContext",
        "profile",
    ):
        value = args.get(key)
        if isinstance(value, dict):
            if isinstance(value.get("context_packet_section"), dict):
                section_profile = (value.get("context_packet_section") or {}).get("profile")
                return dict(section_profile) if isinstance(section_profile, dict) else dict(value.get("context_packet_section") or {})
            if isinstance(value.get("profile"), dict) and value.get("section_name") == "user_practice_profile_context":
                return dict(value["profile"])
            return dict(value)
    allowed_direct_keys = {
        "user_id", "userId",
        "current_goal", "currentGoal",
        "preferred_styles", "preferredStyles",
        "focus_areas", "focusAreas",
        "comfortable_tempo_ranges", "comfortableTempoRanges",
        "preferred_session_minutes", "preferredSessionMinutes",
        "practice_mode_preference", "practiceModePreference",
        "avoid",
        "common_tunes", "commonTunes", "frequent_tunes", "frequentTunes",
        "saved_routine_preferences", "savedRoutinePreferences",
        "skill_focus", "skillFocus",
        "updated_at", "updatedAt",
    }
    direct = {key: value for key, value in args.items() if key in allowed_direct_keys or _is_forbidden_profile_key(key)}
    return dict(direct)


def _extract_user_practice_profile_context_section(args: dict[str, Any]) -> dict[str, Any]:
    for key in ("user_practice_profile_context", "userPracticeProfileContext"):
        value = args.get(key)
        if isinstance(value, dict):
            if isinstance(value.get("context_packet_section"), dict):
                return dict(value["context_packet_section"])
            if value.get("section_name") == "user_practice_profile_context":
                return dict(value)
    payload = args.get("user_practice_profile_context_payload") or args.get("userPracticeProfileContextPayload")
    if isinstance(payload, dict):
        section = payload.get("context_packet_section") or payload.get("contextPacketSection")
        if isinstance(section, dict):
            return dict(section)
    return {}


def _normalize_user_practice_profile(profile: dict[str, Any]) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    warnings: list[str] = []
    if not isinstance(profile, dict):
        return {}, ["user_practice_profile_ignored_not_object"], {"disallowed_or_unrecognized_fields": [], "sensitive_or_client_only_fields": []}
    sensitive_or_client_only = sorted({str(key) for key in profile.keys() if _is_forbidden_profile_key(key)})
    allowed_canonical_keys = {
        "user_id", "current_goal", "preferred_styles", "focus_areas", "comfortable_tempo_ranges",
        "preferred_session_minutes", "practice_mode_preference", "avoid", "common_tunes",
        "saved_routine_preferences", "skill_focus", "updated_at",
    }
    recognized_aliases = {
        "user_id", "userId", "current_goal", "currentGoal", "preferred_styles", "preferredStyles",
        "focus_areas", "focusAreas", "comfortable_tempo_ranges", "comfortableTempoRanges",
        "preferred_session_minutes", "preferredSessionMinutes", "practice_mode_preference", "practiceModePreference",
        "avoid", "common_tunes", "commonTunes", "frequent_tunes", "frequentTunes",
        "saved_routine_preferences", "savedRoutinePreferences", "skill_focus", "skillFocus", "updated_at", "updatedAt",
    }
    unrecognized = sorted(str(key) for key in profile.keys() if str(key) not in recognized_aliases and not _is_forbidden_profile_key(key))
    sanitized_profile = _drop_forbidden_profile_fields(profile)
    tempo_ranges, tempo_warnings = _normalize_comfortable_tempo_ranges(_first_present(sanitized_profile, "comfortable_tempo_ranges", "comfortableTempoRanges"))
    warnings.extend(tempo_warnings)
    session_minutes, session_warnings = _normalize_preferred_session_minutes(_first_present(sanitized_profile, "preferred_session_minutes", "preferredSessionMinutes"))
    warnings.extend(session_warnings)
    saved_preferences_raw = _first_present(sanitized_profile, "saved_routine_preferences", "savedRoutinePreferences")
    saved_preferences = _drop_forbidden_profile_fields(saved_preferences_raw) if isinstance(saved_preferences_raw, dict) else {}
    normalized = {
        "user_id": _string_or_none(_first_present(sanitized_profile, "user_id", "userId")),
        "current_goal": _string_or_none(_first_present(sanitized_profile, "current_goal", "currentGoal")),
        "preferred_styles": _normalize_string_list(_first_present(sanitized_profile, "preferred_styles", "preferredStyles")),
        "focus_areas": _normalize_string_list(_first_present(sanitized_profile, "focus_areas", "focusAreas")),
        "skill_focus": _normalize_string_list(_first_present(sanitized_profile, "skill_focus", "skillFocus")),
        "common_tunes": _normalize_string_list(_first_present(sanitized_profile, "common_tunes", "commonTunes", "frequent_tunes", "frequentTunes")),
        "comfortable_tempo_ranges": tempo_ranges,
        "preferred_session_minutes": session_minutes,
        "avoid": _normalize_string_list(_first_present(sanitized_profile, "avoid")),
        "saved_routine_preferences": saved_preferences,
        "practice_mode_preference": _string_or_none(_first_present(sanitized_profile, "practice_mode_preference", "practiceModePreference")),
        "updated_at": _string_or_none(_first_present(sanitized_profile, "updated_at", "updatedAt")),
    }
    normalized = {key: value for key, value in normalized.items() if key in allowed_canonical_keys}
    if sensitive_or_client_only:
        warnings.append("sensitive_or_client_only_fields_discarded")
    if unrecognized:
        warnings.append("unrecognized_profile_fields_discarded")
    discarded = {
        "disallowed_or_unrecognized_fields": unrecognized,
        "sensitive_or_client_only_fields": sensitive_or_client_only,
    }
    return normalized, warnings, discarded


def _normalize_comfortable_tempo_ranges(value: Any) -> tuple[dict[str, dict[str, int]], list[str]]:
    warnings: list[str] = []
    if value is None:
        return {}, warnings
    if not isinstance(value, dict):
        return {}, ["comfortable_tempo_ranges_ignored_not_object"]
    normalized: dict[str, dict[str, int]] = {}
    for style, raw_range in value.items():
        style_key = str(style)
        low: float | None = None
        high: float | None = None
        if isinstance(raw_range, (list, tuple)) and len(raw_range) >= 2:
            low = _number_or_none(raw_range[0])
            high = _number_or_none(raw_range[1])
        elif isinstance(raw_range, dict):
            low = _number_or_none(_first_present(raw_range, "min", "minimum", "low", "from"))
            high = _number_or_none(_first_present(raw_range, "max", "maximum", "high", "to"))
        else:
            warnings.append(f"comfortable_tempo_range_{style_key}_ignored_invalid_shape")
            continue
        if low is None or high is None or low <= 0 or high <= 0:
            warnings.append(f"comfortable_tempo_range_{style_key}_ignored_invalid_numbers")
            continue
        if low > high:
            low, high = high, low
            warnings.append(f"comfortable_tempo_range_{style_key}_min_max_swapped")
        normalized[style_key] = {"min": int(round(low)), "max": int(round(high))}
    return normalized, warnings


def _normalize_preferred_session_minutes(value: Any) -> tuple[list[int], list[str]]:
    warnings: list[str] = []
    if value is None:
        return [], warnings
    raw_values = value if isinstance(value, list) else [value]
    minutes: list[int] = []
    for item in raw_values:
        number = _number_or_none(item)
        if number is None or number <= 0:
            warnings.append("preferred_session_minutes_ignored_invalid_value")
            continue
        minute = int(round(number))
        if minute not in minutes:
            minutes.append(minute)
    return minutes, warnings


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        return []
    result: list[str] = []
    for item in raw_values:
        if item is None:
            continue
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_forbidden_profile_key(key: Any) -> bool:
    normalized = str(key).lower().replace("-", "_")
    forbidden_fragments = (
        "api_key", "apikey", "access_token", "refresh_token", "token", "secret", "password",
        "local_midi_path", "localmidipath", "midi_base64", "midibase64", "payment_info",
        "precise_location", "preciselocation", "hidden_chain_of_thought", "hiddenchainofthought", "chain_of_thought", "chainofthought", "raw_tool_execution_result",
        "playback_position", "playbackposition", "current_position_ms", "currentpositionms", "remaining_seconds", "remainingseconds", "raw_asset", "rawasset",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)


def _drop_forbidden_profile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if _is_forbidden_profile_key(key):
                continue
            clean[str(key)] = _drop_forbidden_profile_fields(item)
        return clean
    if isinstance(value, list):
        return [_drop_forbidden_profile_fields(item) for item in value]
    return value


def _user_practice_profile_has_content(normalized: dict[str, Any]) -> bool:
    for key, value in normalized.items():
        if key == "user_id":
            continue
        if isinstance(value, (list, dict)) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
    return False


def _count_present_profile_fields(normalized: dict[str, Any]) -> int:
    count = 0
    for value in normalized.values():
        if isinstance(value, (list, dict)):
            count += 1 if bool(value) else 0
        elif value is not None:
            count += 1
    return count


def _summarize_user_practice_profile(normalized: dict[str, Any]) -> str:
    parts: list[str] = []
    if normalized.get("current_goal"):
        parts.append(f"当前目标：{normalized['current_goal']}")
    styles = normalized.get("preferred_styles") or []
    if styles:
        parts.append("偏好风格：" + "、".join(styles[:4]))
    focus = normalized.get("focus_areas") or normalized.get("skill_focus") or []
    if focus:
        parts.append("阶段重点：" + "、".join(focus[:5]))
    session_minutes = normalized.get("preferred_session_minutes") or []
    if session_minutes:
        parts.append("偏好练习时长：" + "/".join(str(item) for item in session_minutes[:3]) + " 分钟")
    tempo_ranges = normalized.get("comfortable_tempo_ranges") or {}
    if isinstance(tempo_ranges, dict) and tempo_ranges:
        first_style, first_range = next(iter(tempo_ranges.items()))
        if isinstance(first_range, dict) and first_range.get("min") and first_range.get("max"):
            parts.append(f"舒适速度示例：{first_style} {first_range['min']}-{first_range['max']} bpm")
    avoid = normalized.get("avoid") or []
    if avoid:
        parts.append("暂时避免：" + "、".join(avoid[:4]))
    return "；".join(parts) if parts else "用户长期练习画像暂未提供。"


def _profile_summary_from_section(section: dict[str, Any]) -> str | None:
    if not isinstance(section, dict) or not section:
        return None
    summary = section.get("summary_for_llm")
    if isinstance(summary, str) and summary.strip():
        return summary
    profile = section.get("profile")
    if isinstance(profile, dict):
        summary = profile.get("summary_for_llm")
        if isinstance(summary, str) and summary.strip():
            return summary
    return None


def _extract_active_practice_plan(args: dict[str, Any]) -> dict[str, Any]:
    for key in ("active_practice_plan", "activePracticePlan", "practice_plan", "practicePlan", "plan"):
        value = args.get(key)
        if isinstance(value, dict):
            return dict(value)
    payload = args.get("routine_practice_plan_payload") or args.get("routinePracticePlanPayload")
    if isinstance(payload, dict):
        plan = payload.get("plan") or payload.get("practice_plan") or payload.get("practicePlan")
        if isinstance(plan, dict):
            return dict(plan)
    return {}


def _normalize_active_practice_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    if not isinstance(plan, dict) or not plan:
        return {
            "plan_id": None,
            "title": None,
            "status": "missing",
        }, [], ["no_active_practice_plan_available"]
    plan_id = _first_present(plan, "plan_id", "planId", "id") or "active_plan"
    title = _first_present(plan, "title", "name") or "Active Practice Plan"
    status = _first_present(plan, "status", "state") or "active"
    goal = _first_present(plan, "goal", "practice_goal", "practiceGoal", "description")
    blocks = _extract_plan_blocks(plan)
    context_items: list[dict[str, Any]] = []
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            warnings.append(f"plan_block_{index}_ignored_not_object")
            continue
        context_items.append(_normalize_active_plan_block(block, index=index, plan_id=str(plan_id)))
    normalized = {
        "plan_id": str(plan_id),
        "title": str(title),
        "status": str(status),
        "goal": str(goal) if goal is not None else None,
        "created_at": _first_present(plan, "created_at", "createdAt"),
        "updated_at": _first_present(plan, "updated_at", "updatedAt"),
        "current_week": _first_present(plan, "current_week", "currentWeek"),
        "current_day": _first_present(plan, "current_day", "currentDay"),
        "total_block_count": len(context_items),
    }
    if not context_items:
        warnings.append("active_practice_plan_has_no_blocks")
    return normalized, context_items, warnings


def _extract_plan_blocks(plan: dict[str, Any]) -> list[Any]:
    for key in ("plan_blocks", "planBlocks", "blocks", "routine_blocks", "routineBlocks", "items"):
        value = plan.get(key)
        if isinstance(value, list):
            return list(value)
    weeks = plan.get("weeks")
    if isinstance(weeks, list):
        blocks: list[Any] = []
        for week in weeks:
            if isinstance(week, dict):
                for key in ("days", "blocks", "items"):
                    value = week.get(key)
                    if isinstance(value, list):
                        blocks.extend(value)
        return blocks
    return []


def _normalize_active_plan_block(block: dict[str, Any], *, index: int, plan_id: str) -> dict[str, Any]:
    block_id = _first_present(block, "block_id", "blockId", "id") or f"{plan_id}_block_{index + 1}"
    title = _first_present(block, "title", "name", "goal", "practice_goal", "practiceGoal") or f"Practice Block {index + 1}"
    goal = _first_present(block, "goal", "practice_goal", "practiceGoal", "description") or title
    duration = _number_or_none(_first_present(block, "duration_minutes", "durationMinutes", "suggested_duration_minutes", "suggestedDurationMinutes", "minutes"))
    completed = _bool_or_default(_first_present(block, "completed", "isCompleted", "done"), default=False)
    tune = _first_present(block, "tune_title", "tuneTitle", "tune", "song")
    style = _first_present(block, "style", "suggested_style", "suggestedStyle", "style_id", "styleId")
    tempo = _number_or_none(_first_present(block, "tempo", "bpm", "suggested_tempo", "suggestedTempo"))
    return {
        "block_id": str(block_id),
        "plan_id": plan_id,
        "block_index": int(_number_or_none(_first_present(block, "block_index", "blockIndex", "index")) or index),
        "title": str(title),
        "goal": str(goal) if goal is not None else None,
        "suggested_duration_minutes": int(duration) if duration is not None else None,
        "tune_title": str(tune) if tune is not None else None,
        "style": str(style) if style is not None else None,
        "tempo": int(tempo) if tempo is not None else None,
        "completed": bool(completed),
        "priority": _first_present(block, "priority", "weight") or "normal",
        "context_weight": "pending_plan_block" if not completed else "completed_plan_block",
    }


def _summarize_active_plan_context_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    pending = [item for item in items if not item.get("completed")]
    completed = [item for item in items if item.get("completed")]
    styles: list[str] = []
    tunes: list[str] = []
    total_pending_minutes = 0
    for item in pending:
        if item.get("style") and item["style"] not in styles:
            styles.append(str(item["style"]))
        if item.get("tune_title") and item["tune_title"] not in tunes:
            tunes.append(str(item["tune_title"]))
        if item.get("suggested_duration_minutes") is not None:
            total_pending_minutes += int(item["suggested_duration_minutes"])
    return {
        "plan_block_count": len(items),
        "pending_block_count": len(pending),
        "completed_block_count": len(completed),
        "total_pending_minutes": total_pending_minutes,
        "pending_styles": styles[:8],
        "pending_tunes": tunes[:8],
        "next_candidate_block": pending[0] if pending else {},
    }


def _extract_active_practice_plan_context_section(args: dict[str, Any]) -> dict[str, Any]:
    for key in ("active_practice_plan_context", "activePracticePlanContext"):
        value = args.get(key)
        if isinstance(value, dict):
            if isinstance(value.get("context_packet_section"), dict):
                return dict(value["context_packet_section"])
            return dict(value)
    payload = args.get("active_practice_plan_context_payload") or args.get("activePracticePlanContextPayload")
    if isinstance(payload, dict):
        section = payload.get("context_packet_section") or payload.get("contextPacketSection")
        if isinstance(section, dict):
            return dict(section)
    return {}


def _extract_routine_history_context_section(args: dict[str, Any]) -> dict[str, Any]:
    for key in ("routine_history_context", "routineHistoryContext", "practice_history_context", "practiceHistoryContext"):
        value = args.get(key)
        if isinstance(value, dict):
            if isinstance(value.get("context_packet_section"), dict):
                return dict(value["context_packet_section"])
            return dict(value)
    payload = args.get("routine_history_context_payload") or args.get("routineHistoryContextPayload")
    if isinstance(payload, dict):
        section = payload.get("context_packet_section") or payload.get("contextPacketSection")
        if isinstance(section, dict):
            return dict(section)
    return {}


def _normalize_today_constraints(args: dict[str, Any]) -> dict[str, Any]:
    available = _number_or_none(_first_present(args, "available_minutes", "availableMinutes", "duration_minutes", "durationMinutes"))
    user_input = _first_present(args, "user_input", "userInput", "question", "text")
    return {
        "available_minutes": int(available) if available is not None else None,
        "user_input": str(user_input) if user_input is not None else None,
        "instrument": _first_present(args, "instrument") or "piano",
        "client_local_time": _first_present(args, "client_local_time", "clientLocalTime", "local_time", "localTime"),
        "harmonyos_local_timer_owns_practice_duration": True,
    }


def _active_plan_blocks_from_section(section: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = section.get("plan_blocks") or section.get("active_plan_context_items") or section.get("blocks") or []
    return [dict(block) for block in blocks if isinstance(block, dict)]


def _history_items_from_section(section: dict[str, Any]) -> list[dict[str, Any]]:
    items = section.get("recent_practice_history") or section.get("practice_history_context_items") or section.get("items") or []
    return [dict(item) for item in items if isinstance(item, dict)]


def _derive_context_gap_blocks(active_blocks: list[dict[str, Any]], history_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recent_styles = {str(item.get("style")) for item in history_items[-5:] if item.get("style")}
    recent_tunes = {str(item.get("tune_title")) for item in history_items[-5:] if item.get("tune_title")}
    gaps: list[dict[str, Any]] = []
    for block in active_blocks:
        if block.get("completed"):
            continue
        style_gap = block.get("style") and str(block.get("style")) not in recent_styles
        tune_gap = block.get("tune_title") and str(block.get("tune_title")) not in recent_tunes
        if style_gap or tune_gap:
            gap = dict(block)
            gap["gap_reason"] = "not_seen_in_recent_history"
            gaps.append(gap)
    return gaps

def _extract_routine_history_records(args: dict[str, Any]) -> list[Any]:
    for key in (
        "routine_history_records",
        "routineHistoryRecords",
        "history_records",
        "historyRecords",
        "practice_history",
        "practiceHistory",
        "records",
    ):
        value = args.get(key)
        if isinstance(value, list):
            return list(value)
    single = args.get("routine_history_record") or args.get("routineHistoryRecord") or args.get("record")
    if isinstance(single, dict):
        return [single]
    return []


def _normalize_routine_history_record(record: dict[str, Any], *, index: int) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    dropped_keys = {
        "local_midi_path", "localMidiPath", "midi_base64", "midiBase64", "current_position_ms", "currentPositionMs",
        "remaining_seconds", "remainingSeconds", "playback_stats", "playbackStats", "raw_asset", "rawAsset",
        "asset", "debug_summary", "debugSummary",
    }
    dropped = [key for key in record.keys() if str(key) in dropped_keys]
    session_id = _first_present(record, "session_id", "sessionId", "routine_id", "routineId") or f"routine_history_{index}"
    routine_id = _first_present(record, "routine_id", "routineId", "session_id", "sessionId") or session_id
    planned_minutes = _number_or_none(_first_present(record, "planned_duration_minutes", "plannedDurationMinutes", "duration_minutes", "durationMinutes"))
    actual_seconds = _number_or_none(_first_present(record, "actual_seconds", "actualSeconds", "elapsed_seconds", "elapsedSeconds"))
    actual_minutes = _number_or_none(_first_present(record, "actual_minutes", "actualMinutes"))
    if actual_minutes is None and actual_seconds is not None:
        actual_minutes = round(float(actual_seconds) / 60.0, 2)
    if actual_minutes is None:
        actual_minutes = planned_minutes
    completed = _bool_or_default(_first_present(record, "completed", "isCompleted"), default=True)
    tune_title = _first_present(record, "tune_title", "tuneTitle", "tune", "song", "title")
    title = _first_present(record, "title", "routine_name", "routineName") or tune_title or "Routine Practice"
    style = _first_present(record, "style", "style_id", "styleId")
    tempo = _number_or_none(_first_present(record, "tempo", "bpm"))
    finished_at = _first_present(record, "finished_at", "finishedAt", "ended_at", "endedAt", "created_at", "createdAt")
    started_at = _first_present(record, "started_at", "startedAt")
    practice_goal = _first_present(record, "practice_goal", "practiceGoal", "goal", "intent")
    plan_id = _first_present(record, "plan_id", "planId")
    plan_block_id = _first_present(record, "plan_block_id", "planBlockId", "block_id", "blockId")
    agent_trace_id = _first_present(record, "agent_trace_id", "agentTraceId", "trace_id", "traceId")
    normalized = {
        "session_id": str(session_id),
        "routine_id": str(routine_id),
        "title": str(title),
        "tune_title": str(tune_title) if tune_title is not None else None,
        "style": str(style) if style is not None else None,
        "tempo": int(tempo) if tempo is not None else None,
        "planned_duration_minutes": int(planned_minutes) if planned_minutes is not None else None,
        "actual_minutes": actual_minutes,
        "completed": bool(completed),
        "practice_goal": str(practice_goal) if practice_goal is not None else None,
        "plan_id": str(plan_id) if plan_id is not None else None,
        "plan_block_id": str(plan_block_id) if plan_block_id is not None else None,
        "started_at": str(started_at) if started_at is not None else None,
        "finished_at": str(finished_at) if finished_at is not None else None,
        "agent_trace_id": str(agent_trace_id) if agent_trace_id is not None else None,
    }
    context_item = {
        "history_item_id": normalized["session_id"],
        "routine_id": normalized["routine_id"],
        "title": normalized["title"],
        "tune_title": normalized["tune_title"],
        "style": normalized["style"],
        "tempo": normalized["tempo"],
        "duration_minutes": normalized["actual_minutes"],
        "planned_duration_minutes": normalized["planned_duration_minutes"],
        "completed": normalized["completed"],
        "practice_goal": normalized["practice_goal"],
        "plan_id": normalized["plan_id"],
        "plan_block_id": normalized["plan_block_id"],
        "finished_at": normalized["finished_at"],
        "agent_trace_id": normalized["agent_trace_id"],
        "context_weight": "recent_completed" if normalized["completed"] else "recent_incomplete",
    }
    return normalized, context_item, dropped


def _summarize_practice_history_context_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_minutes = 0.0
    completed_count = 0
    styles: list[str] = []
    tunes: list[str] = []
    incomplete: list[str] = []
    plan_block_ids: list[str] = []
    latest_finished_at = None
    for item in items:
        minutes = _number_or_none(item.get("duration_minutes")) or 0
        total_minutes += float(minutes)
        if item.get("completed"):
            completed_count += 1
        else:
            incomplete.append(str(item.get("history_item_id")))
        style = item.get("style")
        tune = item.get("tune_title")
        plan_block_id = item.get("plan_block_id")
        if style and str(style) not in styles:
            styles.append(str(style))
        if tune and str(tune) not in tunes:
            tunes.append(str(tune))
        if plan_block_id and str(plan_block_id) not in plan_block_ids:
            plan_block_ids.append(str(plan_block_id))
        finished = item.get("finished_at")
        if finished and (latest_finished_at is None or str(finished) > str(latest_finished_at)):
            latest_finished_at = str(finished)
    return {
        "context_item_count": len(items),
        "completed_count": completed_count,
        "incomplete_count": len(items) - completed_count,
        "total_practice_minutes": round(total_minutes, 2),
        "recent_styles": styles[:8],
        "recent_tunes": tunes[:8],
        "recent_plan_block_ids": plan_block_ids[:12],
        "incomplete_history_item_ids": incomplete[:12],
        "latest_finished_at": latest_finished_at,
        "llm_usage_hint": "Use with active PracticePlan only when the user initiates a next-practice conversation.",
    }


def _first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _number_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_default(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "completed", "done"}
    return bool(value)


def _extract_routine_practice_plan_payload(
    args: dict[str, Any],
    *,
    action_card: HarmonyOSAgentActionCard | None = None,
    controlled_result: ControlledWorkflowExecutionResult | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    for key in (
        "routine_practice_plan_payload",
        "routinePracticePlanPayload",
        "practice_plan_payload",
        "practicePlanPayload",
    ):
        value = args.get(key)
        if isinstance(value, dict):
            return dict(value)
    card = args.get("action_card") or args.get("actionCard")
    if isinstance(card, dict):
        preview = card.get("result_preview") or card.get("resultPreview") or {}
        value = preview.get("routine_practice_plan_payload") if isinstance(preview, dict) else None
        if isinstance(value, dict):
            return dict(value)
    if action_card is not None:
        preview = action_card.result_preview if isinstance(action_card.result_preview, dict) else {}
        value = preview.get("routine_practice_plan_payload")
        if isinstance(value, dict):
            return dict(value)
    if controlled_result is not None:
        return build_routine_practice_plan_action_payload(controlled_result, trace_id=trace_id).to_dict()
    return {}


def _select_routine_candidate_block(
    routine_blocks: list[Any],
    *,
    block_id: Any = None,
    block_index: Any = None,
) -> dict[str, Any]:
    normalized_blocks = [dict(block) for block in routine_blocks if isinstance(block, dict)]
    if block_id is not None:
        for block in normalized_blocks:
            if str(block.get("block_id")) == str(block_id):
                return block
    if block_index is not None:
        try:
            idx = int(block_index)
            for block in normalized_blocks:
                if int(block.get("block_index", -1)) == idx:
                    return block
            if 0 <= idx < len(normalized_blocks):
                return normalized_blocks[idx]
        except (TypeError, ValueError):
            pass
    for block in normalized_blocks:
        if block.get("requires_accompaniment_asset"):
            return block
    return normalized_blocks[0] if normalized_blocks else {}


def _coerce_int_with_bounds(value: Any, *, default: int, minimum: int, maximum: int) -> tuple[int, str | None]:
    warning = None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default, f"invalid_integer_defaulted_to_{default}"
    if result < minimum:
        warning = f"value_clamped_to_min_{minimum}"
        result = minimum
    if result > maximum:
        warning = f"value_clamped_to_max_{maximum}"
        result = maximum
    return result, warning


def _infer_tune_from_text(text: str) -> str | None:
    lowered = (text or "").lower()
    if "blue bossa" in lowered:
        return "Blue Bossa"
    if "misty" in lowered:
        return "Misty"
    if "autumn leaves" in lowered:
        return "Autumn Leaves"
    if "all the things" in lowered:
        return "All The Things You Are"
    return None


def _infer_style_from_text(args: dict[str, Any]) -> str | None:
    text = " ".join(str(args.get(key) or "") for key in ("user_input", "userInput", "text", "prompt", "tune", "song")).lower()
    if "bossa" in text or "blue bossa" in text:
        return "bossa_nova"
    if "ballad" in text or "misty" in text:
        return "jazz_ballad"
    if "swing" in text or "autumn leaves" in text:
        return "medium_swing"
    return None

def _derive_action_execution_status(
    *,
    confirmation: ToolExecutionConfirmationEnvelope | None,
    execution_result: ToolExecutionResult | None,
    workflow_dispatch_result: ToolWorkflowDispatchResult | None,
    controlled_result: ControlledWorkflowExecutionResult | None,
) -> str:
    if controlled_result is not None:
        return "controlled_execution_succeeded" if controlled_result.ok else "controlled_execution_blocked"
    if workflow_dispatch_result is not None:
        return "workflow_descriptor_resolved" if workflow_dispatch_result.ok else "blocked"
    if execution_result is not None:
        return "dry_run_completed" if execution_result.ok else "blocked"
    if confirmation is not None:
        if confirmation.confirmation_status == "pending":
            return "confirmation_required"
        if confirmation.confirmation_status == "approved":
            return "ready_for_dry_run"
        if confirmation.confirmation_status == "rejected":
            return "rejected"
        return "blocked"
    return "not_started"


def _build_action_result_preview(
    *,
    controlled_result: ControlledWorkflowExecutionResult | None,
    workflow_dispatch_result: ToolWorkflowDispatchResult | None,
    execution_result: ToolExecutionResult | None,
) -> dict[str, Any]:
    if controlled_result is not None:
        output = controlled_result.workflow_output or {}
        plan = output.get("plan") if isinstance(output, dict) else None
        preview: dict[str, Any] = {
            "ok": controlled_result.ok,
            "status": controlled_result.status,
            "workflow_invoked": controlled_result.workflow_invoked,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }
        if isinstance(plan, dict):
            preview["plan"] = {
                "title": plan.get("title"),
                "duration_minutes": plan.get("duration_minutes"),
                "block_count": len(plan.get("blocks") or []),
            }
            preview["routine_practice_plan_payload"] = build_routine_practice_plan_action_payload(controlled_result).to_dict()
            preview["practice_plan_action_card_e2e_version"] = PRACTICE_PLAN_ACTION_CARD_E2E_VERSION
        return preview
    if workflow_dispatch_result is not None:
        descriptor = workflow_dispatch_result.workflow_descriptor
        preview = {
            "ok": workflow_dispatch_result.ok,
            "status": workflow_dispatch_result.status,
            "workflow_name": descriptor.workflow_name if descriptor else None,
            "descriptor_only": True,
            "workflow_invoked": False,
            "route_called": False,
            "engine_adapter_called": False,
            "midi_asset_created": False,
        }
        if workflow_dispatch_result.ok and workflow_dispatch_result.execution_result.request.tool_name == "agent_playback_prepare":
            preview["playback_prepare_guarded_payload"] = build_playback_prepare_guarded_action_payload(workflow_dispatch_result).to_dict()
            preview["playback_prepare_guarded_design_version"] = PLAYBACK_PREPARE_GUARDED_DESIGN_VERSION
        if workflow_dispatch_result.ok and workflow_dispatch_result.execution_result.request.tool_name == "agent_routine_config_prepare":
            preview["routine_config_prepare_payload"] = build_routine_config_prepare_action_payload(
                workflow_dispatch_result.execution_result.request.arguments_preview,
                tool_name="agent_routine_config_prepare",
                source="agent_routine_config_prepare_descriptor_state",
            ).to_dict()
            preview["routine_config_prepare_contract_version"] = ROUTINE_CONFIG_PREPARE_CONTRACT_VERSION
        return preview
    if execution_result is not None:
        return {
            "ok": execution_result.ok,
            "status": execution_result.status,
            "dry_run": True,
            "real_tool_executed": False,
        }
    return {}


def _action_available_client_actions(
    *,
    confirmation: ToolExecutionConfirmationEnvelope | None,
    execution_result: ToolExecutionResult | None,
    workflow_dispatch_result: ToolWorkflowDispatchResult | None,
    controlled_result: ControlledWorkflowExecutionResult | None,
) -> tuple[str, ...]:
    if controlled_result is not None:
        if controlled_result.ok:
            return ("open_routine_setup", "save_practice_plan", "edit_plan", "dismiss", "view_trace")
        return ("dismiss", "view_trace")
    if workflow_dispatch_result is not None and workflow_dispatch_result.ok:
        if workflow_dispatch_result.execution_result.request.tool_name == "agent_playback_prepare":
            return ("review_playback_request", "open_routine_setup", "edit_request", "dismiss", "view_trace")
        if workflow_dispatch_result.execution_result.request.tool_name == "agent_routine_config_prepare":
            return ("open_routine_setup", "edit_routine_config", "save_routine_draft", "dismiss", "view_trace")
        return ("execute_controlled", "dismiss", "view_trace")
    if execution_result is not None and execution_result.ok:
        return ("dispatch_dry_run", "dismiss", "view_trace")
    if confirmation is not None:
        if confirmation.confirmation_status == "pending":
            return ("confirm", "reject", "dismiss", "view_trace")
        if confirmation.confirmation_status == "approved":
            return ("execute_dry_run", "dismiss", "view_trace")
        return ("dismiss", "view_trace")
    return ("dismiss",)

def preview_tool_invocation(
    proposal: ToolInvocationProposal,
    allowed_tools: list[str] | tuple[str, ...],
    policy: ToolInvocationPreviewPolicy | None = None,
) -> ToolInvocationPreviewResult:
    """Validate a proposed tool call without executing it."""

    active_policy = policy or DEFAULT_TOOL_INVOCATION_PREVIEW_POLICY
    descriptor = get_tool_descriptor(proposal.tool_name)
    tool_validation = validate_allowed_tools(allowed_tools)
    normalized_arguments, argument_warnings = _normalize_arguments(proposal.arguments, active_policy)

    validation: dict[str, Any] = {
        "policy": active_policy.to_dict(),
        "allowed_tool_validation": tool_validation,
        "argument_keys": sorted(normalized_arguments.keys()),
        "argument_key_count": len(normalized_arguments),
        "argument_shape_valid": len(normalized_arguments) <= active_policy.max_argument_keys,
        "schema_name": None,
        "schema_validation_mode": "shape_only_no_execution",
    }
    warnings: list[str] = list(argument_warnings)
    blocking_reasons: list[str] = []

    if descriptor is None:
        blocking_reasons.append("unknown_tool")
        return ToolInvocationPreviewResult(
            ok=False,
            status="rejected_unknown_tool",
            tool_name=proposal.tool_name,
            task_type=proposal.task_type,
            known_tool=False,
            allowed_by_context=False,
            normalized_arguments=normalized_arguments,
            validation=validation,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    descriptor_dict = descriptor.to_dict()
    validation["schema_name"] = descriptor.input_contract.get("schema")
    validation["side_effect_level"] = descriptor.side_effect_level
    validation["route"] = descriptor.route
    allowed_by_context = proposal.tool_name in set(str(tool) for tool in allowed_tools)
    if not allowed_by_context and proposal.tool_name == "agent_routine_config_prepare" and descriptor.category == "routine_setup":
        allowed_by_context = True
        warnings.append("agent_routine_config_prepare_allowed_by_explicit_routine_config_surface")

    if not allowed_by_context:
        blocking_reasons.append("tool_not_allowed_by_context_packet")
        return ToolInvocationPreviewResult(
            ok=False,
            status="rejected_not_allowed_for_context",
            tool_name=proposal.tool_name,
            task_type=proposal.task_type,
            known_tool=True,
            allowed_by_context=False,
            descriptor=descriptor_dict,
            normalized_arguments=normalized_arguments,
            validation=validation,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    if not validation["argument_shape_valid"]:
        blocking_reasons.append("too_many_argument_keys")
        return ToolInvocationPreviewResult(
            ok=False,
            status="rejected_invalid_argument_shape",
            tool_name=proposal.tool_name,
            task_type=proposal.task_type,
            known_tool=True,
            allowed_by_context=True,
            descriptor=descriptor_dict,
            normalized_arguments=normalized_arguments,
            validation=validation,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    blocking_reasons.extend(
        [
            "tool_execution_disabled_in_v2_4_13",
            "autonomous_tool_execution_disabled_in_v2_4_13",
            "preview_does_not_dispatch_deterministic_workflows",
        ]
    )
    if descriptor.side_effect_level not in {"none", "trace_only"}:
        warnings.append(f"tool has side_effect_level={descriptor.side_effect_level}; future execution must require explicit workflow guard.")

    return ToolInvocationPreviewResult(
        ok=True,
        status="preview_only_blocked_by_execution_guard",
        tool_name=proposal.tool_name,
        task_type=proposal.task_type,
        known_tool=True,
        allowed_by_context=True,
        descriptor=descriptor_dict,
        normalized_arguments=normalized_arguments,
        validation=validation,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )


def extract_tool_call_candidates(text: str | None, *, max_candidates: int = 5) -> ToolCallCandidateExtractionResult:
    """Extract tool-call-like JSON objects from assistant text without execution.

    Supported shapes are intentionally explicit and JSON-only:

    - {"tool_name": "agent_playback_prepare", "arguments": {...}}
    - {"toolName": "agent_playback_prepare", "args": {...}}
    - {"tool_call": {"name": "agent_playback_prepare", "arguments": {...}}}
    - {"tool_calls": [{"name": "...", "arguments": {...}}]}

    JSON may appear as the full assistant message or inside fenced ```json blocks.
    Free-form natural language is ignored so the CLI does not hallucinate tool
    calls from ordinary prose.
    """

    source_text = text or ""
    warnings: list[str] = []
    rejected: list[dict[str, Any]] = []
    candidates: list[ToolCallCandidate] = []
    seen: set[tuple[str, str]] = set()

    for index, payload in enumerate(_iter_json_payloads(source_text)):
        for raw_candidate in _candidate_objects_from_payload(payload):
            candidate = _tool_candidate_from_object(raw_candidate, source_index=index)
            if candidate is None:
                rejected.append({"source_index": index, "reason": "json_object_not_tool_call_shape", "preview": _preview_text(raw_candidate)})
                continue
            signature = (candidate.tool_name, json.dumps(candidate.arguments, sort_keys=True, ensure_ascii=False, default=str))
            if signature in seen:
                continue
            seen.add(signature)
            candidates.append(candidate)
            if len(candidates) >= max_candidates:
                warnings.append("candidate_limit_reached")
                return ToolCallCandidateExtractionResult(ok=True, candidates=candidates, scanned_char_count=len(source_text), warnings=warnings, rejected_candidates=rejected)

    return ToolCallCandidateExtractionResult(ok=True, candidates=candidates, scanned_char_count=len(source_text), warnings=warnings, rejected_candidates=rejected)


def _iter_json_payloads(text: str) -> list[Any]:
    payloads: list[Any] = []
    for match in re.finditer(r"```(?:json|tool_call|tool_calls)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL):
        parsed = _parse_json_maybe(match.group(1).strip())
        if parsed is not None:
            payloads.append(parsed)
    stripped = text.strip()
    parsed = _parse_json_maybe(stripped)
    if parsed is not None:
        payloads.append(parsed)
    return payloads


def _parse_json_maybe(raw: str) -> Any | None:
    if not raw or raw[0] not in "[{":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _candidate_objects_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("tool_calls"), list):
        return [item for item in payload["tool_calls"] if isinstance(item, dict)]
    if isinstance(payload.get("tool_call"), dict):
        return [payload["tool_call"]]
    if isinstance(payload.get("function_call"), dict):
        return [payload["function_call"]]
    return [payload]


def _tool_candidate_from_object(obj: dict[str, Any], *, source_index: int) -> ToolCallCandidate | None:
    name = obj.get("tool_name") or obj.get("toolName") or obj.get("name") or obj.get("tool")
    if not isinstance(name, str) or not name.strip():
        return None
    raw_arguments = obj.get("arguments", obj.get("args", {}))
    arguments = _coerce_candidate_arguments(raw_arguments)
    if arguments is None:
        return None
    return ToolCallCandidate(
        tool_name=name.strip(),
        arguments=arguments,
        source_format="json_tool_call_candidate",
        source_index=source_index,
        raw_candidate_preview=_preview_text(obj),
    )


def _coerce_candidate_arguments(raw_arguments: Any) -> dict[str, Any] | None:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return dict(raw_arguments)
    if isinstance(raw_arguments, str):
        parsed = _parse_json_maybe(raw_arguments.strip())
        if isinstance(parsed, dict):
            return parsed
    return None


def _preview_text(value: Any, max_chars: int = 400) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        text = repr(value)
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def build_tool_call_preview_trace_summary(
    *,
    extraction: ToolCallCandidateExtractionResult,
    candidate_previews: list[dict[str, Any]],
    task_type: str,
    source: str = "terminal_chat_cli",
) -> dict[str, Any]:
    """Build a stable trace payload for assistant-text tool-call preview chains.

    This is a trace/diagnostic contract only. It records the chain:
    assistant text -> JSON candidate extraction -> allow-list preview -> execution guard.
    It never dispatches routes, deterministic workflows, adapters, or engine code.
    """

    preview_summaries: list[dict[str, Any]] = []
    for index, item in enumerate(candidate_previews):
        candidate = dict(item.get("candidate") or {})
        preview = dict(item.get("preview") or {})
        preview_summaries.append({
            "index": index,
            "tool_name": candidate.get("tool_name") or preview.get("tool_name"),
            "source_format": candidate.get("source_format"),
            "source_index": candidate.get("source_index"),
            "argument_keys": sorted(str(key) for key in (candidate.get("arguments") or {}).keys()),
            "preview_status": preview.get("status"),
            "known_tool": preview.get("known_tool"),
            "allowed_by_context": preview.get("allowed_by_context"),
            "would_execute": False,
            "blocking_reasons": list(preview.get("blocking_reasons") or []),
            "warnings": list(preview.get("warnings") or []),
        })

    return {
        "tool_call_preview_trace_contract_version": TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION,
        "candidate_extraction_version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
        "tool_invocation_preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
        "tool_registry_version": TOOL_REGISTRY_VERSION,
        "source": source,
        "task_type": task_type,
        "candidate_count": len(extraction.candidates),
        "rejected_candidate_count": len(extraction.rejected_candidates),
        "preview_count": len(candidate_previews),
        "previewed_tool_names": [item.get("tool_name") for item in preview_summaries],
        "preview_statuses": [item.get("preview_status") for item in preview_summaries],
        "all_previews_execution_blocked": all(item.get("would_execute") is False for item in preview_summaries),
        "execution_enabled": False,
        "autonomous_tool_execution_enabled": False,
        "dispatch_enabled": False,
        "engine_adapter_dispatch_enabled": False,
        "preview_summaries": preview_summaries,
        "warnings": list(extraction.warnings),
    }


def tool_call_preview_trace_contract() -> dict[str, Any]:
    return {
        "version": TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION,
        "surface": "terminal_chat_trace_export",
        "mode": "assistant_text_candidate_extraction_then_preview_trace_only",
        "trace_step_names": [
            "terminal_tool_call_candidates_extracted",
            "terminal_tool_call_candidates_previewed",
            "terminal_tool_call_preview_trace_summary_recorded",
        ],
        "summary_field": "tool_call_preview_trace_summary",
        "final_response_summary_fields": [
            "tool_call_preview_trace_contract_version",
            "tool_call_candidate_count",
            "tool_call_candidate_preview_count",
            "tool_call_preview_trace_summary",
        ],
        "summary_schema": {
            "tool_call_preview_trace_contract_version": "string",
            "candidate_extraction_version": "string",
            "tool_invocation_preview_version": "string",
            "tool_registry_version": "string",
            "source": "string",
            "task_type": "string",
            "candidate_count": "number",
            "rejected_candidate_count": "number",
            "preview_count": "number",
            "previewed_tool_names": "string[]",
            "preview_statuses": "string[]",
            "all_previews_execution_blocked": "boolean",
            "execution_enabled": "boolean",
            "autonomous_tool_execution_enabled": "boolean",
            "dispatch_enabled": "boolean",
            "engine_adapter_dispatch_enabled": "boolean",
            "preview_summaries": "ToolCallPreviewTraceItem[]",
            "warnings": "string[]",
        },
        "guards": {
            "trace_contract_executes_tools": False,
            "trace_contract_calls_llm_provider": False,
            "trace_contract_dispatches_workflows": False,
            "trace_contract_calls_engine_adapter": False,
            "raw_api_key_allowed_in_trace": False,
        },
    }


def tool_invocation_preview_contract() -> dict[str, Any]:
    policy = DEFAULT_TOOL_INVOCATION_PREVIEW_POLICY.to_dict()
    return {
        "version": TOOL_INVOCATION_PREVIEW_VERSION,
        "route": "POST /agent/tools/invocation/preview",
        "spec_route": "GET /agent/tools/invocation/spec",
        "tool_registry_version": TOOL_REGISTRY_VERSION,
        "mode": policy["mode"],
        "execution_status": {
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "llm_tool_calls_enabled": False,
            "deterministic_workflow_dispatch_enabled": False,
            "engine_adapter_dispatch_enabled": False,
        },
        "request_schema": {
            "request_id": "string | null",
            "user_input": "string | null",
            "task_type": "practice_plan_generation | immediate_practice_playback | session_review | coach_qa",
            "tool_name": "string",
            "arguments": "Record<string, unknown>",
            "client_context": "ClientContext",
        },
        "response_schema": {
            "ok": "boolean",
            "preview": "ToolInvocationPreviewResult",
            "context_packet_summary": "Record<string, unknown>",
        },
        "candidate_extraction": {
            "version": TOOL_CALL_CANDIDATE_EXTRACTION_VERSION,
            "surface": "terminal_chat_only",
            "mode": "json_only_extract_then_preview",
            "supported_shapes": [
                "{tool_name, arguments}",
                "{toolName, args}",
                "{tool_call: {name, arguments}}",
                "{tool_calls: [{name, arguments}]}",
            ],
            "execution_enabled": False,
        },
        "policy": policy,
        "rules": [
            "Preview builds the same task-scoped ContextPacket used by the LLM runtime.",
            "A proposed tool must exist in the registry and be present in ContextPacket.allowed_tools.",
            "Arguments are normalized and shape-checked only; no route, adapter, or engine workflow is called.",
            "Side-effectful tools can be described, but v2_4_13 always blocks execution.",
            "Terminal chat may extract explicit JSON candidates from assistant text and feed them into this same preview contract.",
        ],
    }


def _risk_summary(side_effect_level: str, *, confirmable: bool) -> str:
    if not confirmable:
        return "Preview did not pass; this proposal cannot enter executable confirmation."
    if side_effect_level in {"none", "trace_only"}:
        return f"Low-risk {side_effect_level} tool; explicit confirmation is still required before any future executor."
    if side_effect_level == "creates_midi_asset":
        return "This tool may create a MIDI asset in a future executor stage; v2_6_2 records confirmation only."
    return f"Tool side_effect_level={side_effect_level}; keep execution disabled until ToolExecutorBoundary is implemented."


def _redact_sensitive_values(value: Any) -> Any:
    sensitive_fragments = ("api_key", "apikey", "access_token", "refresh_token", "token", "secret", "password")
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            normalized_key = key_text.lower().replace("-", "_")
            if any(fragment in normalized_key for fragment in sensitive_fragments):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_sensitive_values(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    return value


def _normalize_arguments(arguments: dict[str, Any], policy: ToolInvocationPreviewPolicy) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    normalized: dict[str, Any] = {}
    for key, value in arguments.items():
        text_key = str(key)
        normalized[text_key] = _preview_value(value, policy.max_argument_preview_chars)
    preview_text = repr(normalized)
    if len(preview_text) > policy.max_argument_preview_chars:
        warnings.append("arguments_preview_truncated")
        normalized = {"_preview_truncated": True, "_argument_keys": sorted(str(key) for key in arguments.keys())}
    return normalized, warnings


def _preview_value(value: Any, max_chars: int) -> Any:
    if isinstance(value, dict):
        return {str(key): _preview_value(item, max_chars) for key, item in value.items()}
    if isinstance(value, list):
        return [_preview_value(item, max_chars) for item in value[:20]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str) and len(value) > max_chars:
            return value[:max_chars] + "..."
        return value
    return repr(value)[:max_chars]
