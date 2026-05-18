from __future__ import annotations

import json
import re
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from typing import Any, Callable

from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, get_tool_descriptor, validate_allowed_tools

TOOL_INVOCATION_PREVIEW_VERSION = "v2_4_13"
TOOL_CALL_CANDIDATE_EXTRACTION_VERSION = "v2_4_13"
TOOL_CALL_PREVIEW_TRACE_CONTRACT_VERSION = "v2_4_13"
TOOL_EXECUTION_CONFIRMATION_CONTRACT_VERSION = "v2_6_2"
TOOL_EXECUTOR_BOUNDARY_VERSION = "v2_6_3"
TOOL_WORKFLOW_DISPATCHER_VERSION = "v2_6_4"
CONTROLLED_WORKFLOW_EXECUTION_VERSION = "v2_6_5"


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
