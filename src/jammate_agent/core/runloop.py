from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_agent.core.context import ContextPacket

RUNLOOP_CONTRACT_VERSION = "v2_4_1"


@dataclass(frozen=True)
class BoundedRunLoopPolicy:
    """Safety contract for future LLM tool execution.

    v2_4_1 does not call an LLM and does not execute autonomous tools. The policy
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
    reason: str = "LLM provider is not configured in v2_4_1; use existing deterministic workflow."
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
        }


class BoundedAgentRunLoop:
    """Preview-only runloop foundation for future LLM/tool workflows."""

    def __init__(self, policy: BoundedRunLoopPolicy | None = None) -> None:
        self.policy = policy or BoundedRunLoopPolicy()

    def preview(self, context_packet: ContextPacket) -> RunLoopPreviewResult:
        warnings: list[str] = []
        if not context_packet.allowed_tools:
            warnings.append("context_packet.allowed_tools is empty; no tool workflow can be planned.")
        if context_packet.runtime_policy.get("max_tool_steps", self.policy.max_steps) > self.policy.max_steps:
            warnings.append("context max_tool_steps exceeds policy max_steps and will be capped.")
        llm_provider_configured = bool(context_packet.runtime_policy.get("llm_provider_configured", False))
        tool_execution_enabled = False
        next_action = "llm_required_but_unavailable" if context_packet.runtime_policy.get("llm_required") else "deterministic_workflow_fallback"
        reason = (
            "This task requires an LLM, but v2_4_1 only exposes the context/runtime envelope."
            if next_action == "llm_required_but_unavailable"
            else "LLM provider is not configured in v2_4_1; use existing deterministic workflow."
        )
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
        )

    def contract(self) -> dict[str, Any]:
        return {
            "contract_version": RUNLOOP_CONTRACT_VERSION,
            "policy": self.policy.to_dict(),
            "execution_status": {
                "llm_calls_enabled": False,
                "autonomous_tool_execution_enabled": False,
                "purpose": "Expose deterministic runtime envelope before connecting any LLM provider.",
            },
        }
