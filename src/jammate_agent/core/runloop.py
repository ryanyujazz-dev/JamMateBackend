from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_agent.core.context import ContextPacket
from jammate_agent.core.llm_provider import LLMProvider, build_llm_provider_from_env, build_request_envelope
from jammate_agent.core.tool_invocation import TOOL_INVOCATION_PREVIEW_VERSION
from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, validate_allowed_tools

RUNLOOP_CONTRACT_VERSION = "v2_4_12"


@dataclass(frozen=True)
class BoundedRunLoopPolicy:
    """Safety contract for future LLM tool execution.

    v2_4_12 keeps LLM calls preview/config-guarded and does not execute autonomous tools. The policy
    is made explicit now so future LLM providers have a deterministic envelope:
    bounded steps, task-scoped tool allow-list, and workflow fallbacks.
    """

    max_steps: int = 4
    stop_conditions: tuple[str, ...] = (
        "final_response_ready",
        "tool_limit_reached",
        "requires_user_clarification",
        "deterministic_workflow_selected",
    )
    default_runtime_mode: str = "preview_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": RUNLOOP_CONTRACT_VERSION,
            "max_steps": self.max_steps,
            "stop_conditions": list(self.stop_conditions),
            "default_runtime_mode": self.default_runtime_mode,
        }


@dataclass
class RunLoopPreviewResult:
    ok: bool
    runtime_mode: str
    llm_provider_configured: bool
    tool_execution_enabled: bool
    max_steps: int
    allowed_tools: list[str] = field(default_factory=list)
    next_action: str = "deterministic_workflow_fallback"
    reason: str = "LLM provider boundary is disabled; use existing deterministic workflow."
    llm_provider_status: dict[str, Any] = field(default_factory=dict)
    request_envelope_summary: dict[str, Any] = field(default_factory=dict)
    tool_registry_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": RUNLOOP_CONTRACT_VERSION,
            "ok": self.ok,
            "runtime_mode": self.runtime_mode,
            "llm_provider_configured": self.llm_provider_configured,
            "tool_execution_enabled": self.tool_execution_enabled,
            "max_steps": self.max_steps,
            "allowed_tools": list(self.allowed_tools),
            "next_action": self.next_action,
            "reason": self.reason,
            "warnings": list(self.warnings),
            "llm_provider_status": self.llm_provider_status,
            "request_envelope_summary": self.request_envelope_summary,
            "tool_registry_summary": self.tool_registry_summary,
        }


class BoundedAgentRunLoop:
    """Preview-only runloop foundation for future LLM/tool workflows."""

    def __init__(self, policy: BoundedRunLoopPolicy | None = None, llm_provider: LLMProvider | None = None) -> None:
        self.policy = policy or BoundedRunLoopPolicy()
        self.llm_provider = llm_provider or build_llm_provider_from_env()

    def preview(self, context_packet: ContextPacket) -> RunLoopPreviewResult:
        warnings: list[str] = []
        if not context_packet.allowed_tools:
            warnings.append("context_packet.allowed_tools is empty; no tool workflow can be planned.")
        tool_validation = validate_allowed_tools(context_packet.allowed_tools)
        if not tool_validation["all_known"]:
            warnings.append(f"Unknown tools in context allow-list: {tool_validation['unknown_tools']}.")
        if context_packet.runtime_policy.get("max_tool_steps", self.policy.max_steps) > self.policy.max_steps:
            warnings.append("context max_tool_steps exceeds policy max_steps and will be capped.")

        provider_status = self.llm_provider.status()
        llm_provider_configured = bool(provider_status.get("provider_configured", False))
        tool_execution_enabled = False
        envelope = build_request_envelope(context_packet)
        envelope_summary = {
            "message_count": len(envelope.messages),
            "allowed_tools": list(envelope.allowed_tools),
            "output_schema": envelope.output_contract.get("schema"),
            "max_prompt_chars": provider_status.get("max_prompt_chars"),
            "tool_registry_version": TOOL_REGISTRY_VERSION,
            "tool_descriptor_count": len(getattr(context_packet, "tool_descriptors", [])),
            "tool_invocation_preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
            "tool_invocation_preview_enabled": True,
        }

        llm_required = bool(context_packet.runtime_policy.get("llm_required"))
        if llm_required and llm_provider_configured:
            next_action = "llm_provider_configured_but_preview_only"
            reason = "LLM provider config is present, but v2_4_12 only exposes the provider boundary, request envelope, and tool invocation preview contract; no LLM call is executed."
        elif llm_required:
            next_action = "llm_required_but_provider_unavailable"
            reason = "This task requires an LLM, but the provider boundary is not configured; use deterministic fallback only when available."
        else:
            next_action = "deterministic_workflow_fallback"
            reason = "LLM provider boundary is preview-only; use existing deterministic workflow."

        return RunLoopPreviewResult(
            ok=True,
            runtime_mode=self.policy.default_runtime_mode,
            llm_provider_configured=llm_provider_configured,
            tool_execution_enabled=tool_execution_enabled,
            max_steps=self.policy.max_steps,
            allowed_tools=list(context_packet.allowed_tools),
            next_action=next_action,
            reason=reason,
            warnings=warnings,
            llm_provider_status=provider_status,
            request_envelope_summary=envelope_summary,
            tool_registry_summary=tool_validation,
        )

    def contract(self) -> dict[str, Any]:
        return {
            "contract_version": RUNLOOP_CONTRACT_VERSION,
            "policy": self.policy.to_dict(),
            "execution_status": {
                "llm_calls_enabled": False,
                "autonomous_tool_execution_enabled": False,
                "provider_boundary_available": True,
                "provider_status": self.llm_provider.status(),
                "tool_registry_version": TOOL_REGISTRY_VERSION,
                "tool_registry_mode": "descriptor_registry_only",
                "tool_invocation_preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
                "tool_invocation_preview_enabled": True,
                "purpose": "Expose deterministic provider boundary, runtime envelope, and tool-call preview validation before enabling real LLM tool execution.",
            },
        }
