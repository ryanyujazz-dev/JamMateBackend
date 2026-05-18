from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOOL_REGISTRY_VERSION = "v2_4_7"


@dataclass(frozen=True)
class AgentToolDescriptor:
    """Declarative descriptor for deterministic Agent tools/workflows.

    This registry is intentionally descriptive in v2_4_7. It does not execute
    tools and does not import engine internals. Future LLM/tool-loop code should
    treat this as the source of truth for what a task may describe to a model.
    """

    name: str
    title: str
    description: str
    category: str
    task_types: tuple[str, ...] = ()
    requires_llm: bool = False
    direct_client_callable: bool = False
    deterministic_workflow: str | None = None
    route: str | None = None
    input_contract: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)
    adapter_boundary: str | None = None
    side_effect_level: str = "none"
    execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    guardrails: tuple[str, ...] = (
        "descriptor_only_in_v2_4_7",
        "no_autonomous_tool_execution",
        "must_be_allowed_by_task_context",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_version": TOOL_REGISTRY_VERSION,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "task_types": list(self.task_types),
            "requires_llm": self.requires_llm,
            "direct_client_callable": self.direct_client_callable,
            "deterministic_workflow": self.deterministic_workflow,
            "route": self.route,
            "input_contract": dict(self.input_contract),
            "output_contract": dict(self.output_contract),
            "adapter_boundary": self.adapter_boundary,
            "side_effect_level": self.side_effect_level,
            "execution_enabled": self.execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "guardrails": list(self.guardrails),
        }

    def context_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "route": self.route,
            "requires_llm": self.requires_llm,
            "direct_client_callable": self.direct_client_callable,
            "deterministic_workflow": self.deterministic_workflow,
            "execution_enabled": self.execution_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "input_schema": self.input_contract.get("schema"),
            "output_schema": self.output_contract.get("schema") or self.output_contract.get("asset_format"),
        }


_TOOL_DESCRIPTORS: tuple[AgentToolDescriptor, ...] = (
    AgentToolDescriptor(
        name="direct_accompaniment_generate",
        title="Direct Accompaniment Generate",
        description="Direct client-callable accompaniment generation path; does not require Agent/LLM.",
        category="direct_engine_api",
        task_types=("immediate_practice_playback",),
        direct_client_callable=True,
        deterministic_workflow="POST /accompaniment/generate",
        route="POST /accompaniment/generate",
        input_contract={
            "route": "POST /accompaniment/generate",
            "schema": "DirectAccompanimentGenerateRequest",
            "preferred_chart_input": "inline jammate_leadsheet_v2",
            "fallback_chart_input": "tune",
            "request_case": "camelCase_or_snake_case",
        },
        output_contract={
            "schema": "DirectAccompanimentGenerateResponse",
            "asset_format": "midi_base64",
            "requires_client_looping": False,
            "response_case": "snake_case",
        },
        adapter_boundary="jammate_api.routes.accompaniment_routes -> jammate_engine",
        side_effect_level="creates_midi_asset",
    ),
    AgentToolDescriptor(
        name="chart_resolve",
        title="Chart Resolve",
        description="Resolve a tune name or chart hint to a local chart/material context for Agent playback workflows.",
        category="chart_context",
        task_types=("immediate_practice_playback",),
        deterministic_workflow="ChartResolver.resolve",
        route="internal:ChartResolver.resolve",
        input_contract={"schema": "ChartResolveRequest", "user_input": "string"},
        output_contract={"schema": "ChartResolution", "contains_leadsheet_or_tune_context": True},
        adapter_boundary="jammate_agent.capabilities.charts",
        side_effect_level="none",
    ),
    AgentToolDescriptor(
        name="agent_playback_prepare",
        title="Agent Playback Prepare",
        description="Natural-language immediate practice playback workflow. Agent resolves chart, arrangement intent, and accompaniment asset.",
        category="practice_playback",
        task_types=("immediate_practice_playback", "coach_qa"),
        direct_client_callable=True,
        deterministic_workflow="ImmediatePlaybackWorkflow.prepare",
        route="POST /agent/playback/prepare",
        input_contract={"route": "POST /agent/playback/prepare", "schema": "AgentPlaybackPrepareRequest"},
        output_contract={"schema": "PlaybackPrepareResult", "asset_format": "midi_base64", "playback_instruction": "client_loop_until_target_duration"},
        adapter_boundary="jammate_agent.adapters.JamMateEngineAccompanimentAdapter",
        side_effect_level="creates_midi_asset",
    ),
    AgentToolDescriptor(
        name="agent_practice_plan",
        title="Agent Practice Plan",
        description="Natural-language practice-plan generation. P0 is deterministic; future LLM planner can replace the planner provider.",
        category="practice_planning",
        task_types=("practice_plan_generation", "coach_qa"),
        direct_client_callable=True,
        deterministic_workflow="PracticePlanner.build_plan",
        route="POST /agent/practice/plan",
        input_contract={"route": "POST /agent/practice/plan", "schema": "AgentPlanRequest"},
        output_contract={"schema": "PracticePlan"},
        adapter_boundary="jammate_agent.capabilities.practice",
        side_effect_level="none",
    ),
    AgentToolDescriptor(
        name="session_review_recommendation",
        title="Session Review Recommendation",
        description="Session review to next-step recommendation. P0 is rule-based.",
        category="practice_review",
        task_types=("session_review",),
        direct_client_callable=True,
        deterministic_workflow="ReviewEngine.recommend_next_step",
        route="POST /agent/session/review",
        input_contract={"route": "POST /agent/session/review", "schema": "SessionReviewRequest"},
        output_contract={"schema": "NextStepRecommendation"},
        adapter_boundary="jammate_agent.capabilities.practice",
        side_effect_level="none",
    ),
    AgentToolDescriptor(
        name="agent_llm_context_runtime_preview",
        title="Agent LLM Context Runtime Preview",
        description="Preview task-scoped ContextPacket and bounded runloop envelope before any real LLM provider is connected.",
        category="agent_diagnostics",
        task_types=(),
        direct_client_callable=True,
        deterministic_workflow="JamMateAgent.build_llm_context_runtime",
        route="POST /agent/context/runtime/preview",
        input_contract={"route": "POST /agent/context/runtime/preview", "schema": "AgentContextRuntimePreviewRequest"},
        output_contract={"schema": "AgentContextRuntimePreviewResponse", "runtime_mode": "preview_only"},
        adapter_boundary="jammate_agent.core.context + jammate_agent.core.runloop",
        side_effect_level="trace_only",
    ),
    AgentToolDescriptor(
        name="agent_llm_provider_boundary_spec",
        title="Agent LLM Provider Boundary Spec",
        description="Inspect optional LLM provider configuration guard without making network calls.",
        category="agent_diagnostics",
        direct_client_callable=True,
        deterministic_workflow="llm_provider_boundary_contract",
        route="GET /agent/llm/provider/spec",
        input_contract={"route": "GET /agent/llm/provider/spec", "schema": "none"},
        output_contract={"schema": "LLMProviderBoundarySpec", "llm_calls_enabled": False},
        adapter_boundary="jammate_agent.core.llm_provider",
        side_effect_level="none",
    ),

    AgentToolDescriptor(
        name="agent_tool_invocation_preview",
        title="Agent Tool Invocation Preview",
        description="Validate a future LLM-proposed tool call against the task allow-list and argument shape without executing it.",
        category="agent_diagnostics",
        direct_client_callable=True,
        deterministic_workflow="tool_invocation_preview_contract",
        route="POST /agent/tools/invocation/preview",
        input_contract={"route": "POST /agent/tools/invocation/preview", "schema": "AgentToolInvocationPreviewRequest"},
        output_contract={"schema": "ToolInvocationPreviewResult", "execution_enabled": False},
        adapter_boundary="jammate_agent.core.tool_invocation",
        side_effect_level="none",
    ),
    AgentToolDescriptor(
        name="agent_tool_registry_spec",
        title="Agent Tool Registry Spec",
        description="Inspect deterministic Agent tool descriptors and task-specific allow-lists without executing tools.",
        category="agent_diagnostics",
        direct_client_callable=True,
        deterministic_workflow="tool_registry_contract",
        route="GET /agent/tools/registry",
        input_contract={"route": "GET /agent/tools/registry", "schema": "none"},
        output_contract={"schema": "AgentToolRegistrySpec", "autonomous_execution_enabled": False},
        adapter_boundary="jammate_agent.core.tool_registry",
        side_effect_level="none",
    ),
)

_TOOL_MAP: dict[str, AgentToolDescriptor] = {descriptor.name: descriptor for descriptor in _TOOL_DESCRIPTORS}


def get_agent_tool_registry() -> tuple[AgentToolDescriptor, ...]:
    return _TOOL_DESCRIPTORS


def get_tool_descriptor(name: str) -> AgentToolDescriptor | None:
    return _TOOL_MAP.get(name)


def summarize_tools_for_names(names: tuple[str, ...] | list[str]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for name in names:
        descriptor = get_tool_descriptor(str(name))
        if descriptor:
            summaries.append(descriptor.context_summary())
    return summaries


def tools_for_task(task_type: str) -> list[AgentToolDescriptor]:
    return [descriptor for descriptor in _TOOL_DESCRIPTORS if task_type in descriptor.task_types]


def validate_allowed_tools(names: tuple[str, ...] | list[str]) -> dict[str, Any]:
    requested = [str(name) for name in names]
    unknown = [name for name in requested if name not in _TOOL_MAP]
    descriptors = summarize_tools_for_names(requested)
    return {
        "registry_version": TOOL_REGISTRY_VERSION,
        "all_known": not unknown,
        "requested_tools": requested,
        "unknown_tools": unknown,
        "descriptor_count": len(descriptors),
        "autonomous_execution_enabled": False,
        "tool_execution_enabled": False,
    }


def tool_registry_manifest() -> dict[str, Any]:
    return {
        "version": TOOL_REGISTRY_VERSION,
        "registry_version": TOOL_REGISTRY_VERSION,
        "purpose": "Descriptor-only registry for deterministic Agent workflows, future bounded LLM tool planning, and tool-call preview validation.",
        "execution_status": {
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
            "llm_tool_calls_enabled": False,
            "mode": "descriptor_registry_only",
        },
        "rules": [
            "Only tools listed in ContextPacket.allowed_tools may be described to a future LLM for a task.",
            "v2_4_7 does not execute tools from the runloop; deterministic API workflows remain the only execution path.",
            "Engine access remains adapter/API-boundary only; the registry must not import jammate_engine.",
        ],
        "tools": [descriptor.to_dict() for descriptor in _TOOL_DESCRIPTORS],
        "tool_names": [descriptor.name for descriptor in _TOOL_DESCRIPTORS],
        "task_allow_lists": {
            task_type: [descriptor.name for descriptor in tools_for_task(task_type)]
            for task_type in (
                "practice_plan_generation",
                "immediate_practice_playback",
                "session_review",
                "coach_qa",
            )
        },
    }
