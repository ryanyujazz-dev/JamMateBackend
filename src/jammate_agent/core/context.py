from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jammate_agent.core.llm_provider import LLMProviderConfig
from jammate_agent.core.tool_invocation import (
    TOOL_INVOCATION_PREVIEW_VERSION,
    DEFAULT_TOOL_INVOCATION_PREVIEW_POLICY,
    ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
    CONTEXT_ENGINEERING_SKELETON_VERSION,
    ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
    PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
    TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
    TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
    TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
    build_routine_history_context_intake_payload,
    build_active_practice_plan_context_intake_payload,
    build_practice_context_assembly_policy_payload,
)
from jammate_agent.core.tool_registry import TOOL_REGISTRY_VERSION, summarize_tools_for_names, validate_allowed_tools

CONTEXT_RUNTIME_VERSION = "v2_4_13"


@dataclass
class CapabilityManifest:
    available_styles: list[str] = field(default_factory=lambda: ["medium_swing", "bossa_nova", "jazz_ballad"])
    available_practice_modes: list[str] = field(default_factory=lambda: ["general_practice", "piano_comping", "solo_improvisation", "time_feel", "repertoire"])
    can_mute_roles: list[str] = field(default_factory=lambda: ["piano", "bass", "drums", "melody"])
    supports_loop_count: bool = True
    supports_harmonic_expansion: bool = True
    supports_llm_context_runtime_preview: bool = True
    supports_bounded_tool_loop_preview: bool = True
    supports_llm_provider_boundary: bool = True
    supports_tool_registry_boundary: bool = True
    supports_tool_invocation_preview: bool = True
    supports_routine_history_context_intake: bool = True
    supports_active_practice_plan_context_intake: bool = True
    supports_practice_context_assembly_policy: bool = True
    supports_today_practice_context_e2e: bool = True
    supports_today_practice_guidance_prompt_contract: bool = True
    supports_today_practice_guidance_provider_boundary_e2e: bool = True
    direct_client_paths: list[str] = field(default_factory=lambda: ["/accompaniment/generate", "/agent/practice/plan", "/agent/playback/prepare"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "available_styles": list(self.available_styles),
            "available_practice_modes": list(self.available_practice_modes),
            "can_mute_roles": list(self.can_mute_roles),
            "supports_loop_count": self.supports_loop_count,
            "supports_harmonic_expansion": self.supports_harmonic_expansion,
            "supports_llm_context_runtime_preview": self.supports_llm_context_runtime_preview,
            "supports_bounded_tool_loop_preview": self.supports_bounded_tool_loop_preview,
            "supports_llm_provider_boundary": self.supports_llm_provider_boundary,
            "supports_tool_registry_boundary": self.supports_tool_registry_boundary,
            "supports_tool_invocation_preview": self.supports_tool_invocation_preview,
            "supports_routine_history_context_intake": self.supports_routine_history_context_intake,
            "supports_active_practice_plan_context_intake": self.supports_active_practice_plan_context_intake,
            "supports_practice_context_assembly_policy": self.supports_practice_context_assembly_policy,
            "supports_today_practice_context_e2e": self.supports_today_practice_context_e2e,
            "supports_today_practice_guidance_prompt_contract": self.supports_today_practice_guidance_prompt_contract,
            "supports_today_practice_guidance_provider_boundary_e2e": self.supports_today_practice_guidance_provider_boundary_e2e,
            "direct_client_paths": list(self.direct_client_paths),
        }


@dataclass(frozen=True)
class ContextProfile:
    task_type: str
    required_context_layers: tuple[str, ...]
    optional_context_layers: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    output_schema: str
    llm_required: bool = False
    deterministic_fallback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "required_context_layers": list(self.required_context_layers),
            "optional_context_layers": list(self.optional_context_layers),
            "allowed_tools": list(self.allowed_tools),
            "tool_descriptor_count": len(summarize_tools_for_names(self.allowed_tools)),
            "output_schema": self.output_schema,
            "llm_required": self.llm_required,
            "deterministic_fallback": self.deterministic_fallback,
        }


CONTEXT_PROFILES: dict[str, ContextProfile] = {
    "practice_plan_generation": ContextProfile(
        task_type="practice_plan_generation",
        required_context_layers=("system_product_context", "capability_manifest", "user_request", "client_context"),
        optional_context_layers=("learner_summary", "active_goal", "active_practice_plan_context", "relevant_history", "routine_history_context", "assembled_practice_context", "routine_templates"),
        allowed_tools=("agent_practice_plan",),
        output_schema="PracticePlan",
        llm_required=False,
        deterministic_fallback="PracticePlanner.build_plan",
    ),
    "immediate_practice_playback": ContextProfile(
        task_type="immediate_practice_playback",
        required_context_layers=("system_product_context", "capability_manifest", "user_request", "client_context", "chart_resolution_context"),
        optional_context_layers=("arrangement_intent", "active_session", "local_asset_cache_summary"),
        allowed_tools=("chart_resolve", "agent_playback_prepare"),
        output_schema="PlaybackPrepareResult",
        llm_required=False,
        deterministic_fallback="ImmediatePlaybackWorkflow.prepare",
    ),
    "session_review": ContextProfile(
        task_type="session_review",
        required_context_layers=("system_product_context", "session_review", "current_session"),
        optional_context_layers=("relevant_past_reviews", "active_goal", "learner_summary"),
        allowed_tools=("session_review_recommendation",),
        output_schema="NextStepRecommendation",
        llm_required=False,
        deterministic_fallback="ReviewEngine.recommend_next_step",
    ),
    "today_practice_guidance": ContextProfile(
        task_type="today_practice_guidance",
        required_context_layers=("system_product_context", "capability_manifest", "user_question", "client_context"),
        optional_context_layers=("active_practice_plan_context", "routine_history_context", "assembled_practice_context", "learner_summary", "active_goal"),
        allowed_tools=("agent_practice_plan",),
        output_schema="TodayPracticeGuidanceOutput",
        llm_required=True,
        deterministic_fallback=None,
    ),
    "coach_qa": ContextProfile(
        task_type="coach_qa",
        required_context_layers=("system_product_context", "capability_manifest", "user_question", "client_context"),
        optional_context_layers=("music_concept_context", "active_practice_plan_context", "relevant_history", "routine_history_context", "assembled_practice_context", "current_screen_or_session"),
        allowed_tools=("agent_practice_plan", "agent_playback_prepare"),
        output_schema="CoachResponse",
        llm_required=True,
        deterministic_fallback=None,
    ),
}


@dataclass
class ContextPacket:
    task_type: str
    user_request: dict[str, Any]
    user_profile: dict[str, Any] = field(default_factory=dict)
    learner_context: dict[str, Any] = field(default_factory=dict)
    active_context: dict[str, Any] = field(default_factory=dict)
    material_context: dict[str, Any] = field(default_factory=dict)
    capabilities: CapabilityManifest = field(default_factory=CapabilityManifest)
    constraints: dict[str, Any] = field(default_factory=dict)
    client_context: dict[str, Any] = field(default_factory=dict)
    system_product_context: dict[str, Any] = field(default_factory=dict)
    context_runtime_version: str = CONTEXT_RUNTIME_VERSION
    selected_context_layers: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    tool_descriptors: list[dict[str, Any]] = field(default_factory=list)
    output_contract: dict[str, Any] = field(default_factory=dict)
    runtime_policy: dict[str, Any] = field(default_factory=dict)
    routing_hints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_runtime_version": self.context_runtime_version,
            "task_type": self.task_type,
            "selected_context_layers": list(self.selected_context_layers),
            "system_product_context": self.system_product_context,
            "user_request": self.user_request,
            "client_context": self.client_context,
            "user_profile": self.user_profile,
            "learner_context": self.learner_context,
            "active_context": self.active_context,
            "material_context": self.material_context,
            "capabilities": self.capabilities.to_dict(),
            "constraints": self.constraints,
            "allowed_tools": list(self.allowed_tools),
            "tool_descriptors": list(self.tool_descriptors),
            "output_contract": self.output_contract,
            "runtime_policy": self.runtime_policy,
            "routing_hints": self.routing_hints,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "context_runtime_version": self.context_runtime_version,
            "task_type": self.task_type,
            "selected_context_layers": list(self.selected_context_layers),
            "allowed_tools": list(self.allowed_tools),
            "tool_descriptor_count": len(self.tool_descriptors),
            "output_schema": self.output_contract.get("schema"),
            "llm_required": self.runtime_policy.get("llm_required"),
            "deterministic_fallback": self.runtime_policy.get("deterministic_fallback"),
        }


class ContextBuilder:
    """Build task-scoped context packets for deterministic workflows and future LLM calls.

    The builder intentionally stays inside `jammate_agent.core`: it only packages
    practice/user/client context and public tool contracts. It never imports or
    reasons over engine internals.
    """

    def build(self, task_type: str, user_input: str, **kwargs: Any) -> ContextPacket:
        profile = CONTEXT_PROFILES.get(task_type, CONTEXT_PROFILES["practice_plan_generation"])
        client_context = self._clean_dict(kwargs.get("client_context") or {})
        constraints = self._build_constraints(kwargs, client_context)
        allowed_tools = list(profile.allowed_tools)
        tool_descriptors = summarize_tools_for_names(allowed_tools)
        routine_history_context = self._routine_history_context(kwargs, client_context)
        active_practice_plan_context = self._active_practice_plan_context(kwargs, client_context)
        assembled_practice_context = self._assembled_practice_context(kwargs, client_context, routine_history_context, active_practice_plan_context)
        learner_context = self._clean_dict(kwargs.get("learner_context") or {"recent_focus": [], "recent_weak_points": [], "note": "P0 placeholder; replace with LearnerModel summary."})
        selected_layers = [*profile.required_context_layers, *profile.optional_context_layers]
        if active_practice_plan_context:
            learner_context["active_practice_plan_context"] = active_practice_plan_context
            if "active_practice_plan_context" not in selected_layers:
                selected_layers.append("active_practice_plan_context")
        if routine_history_context:
            learner_context["routine_history_context"] = routine_history_context
            if "routine_history_context" not in selected_layers:
                selected_layers.append("routine_history_context")
        if assembled_practice_context:
            learner_context["assembled_practice_context"] = assembled_practice_context
            if "assembled_practice_context" not in selected_layers:
                selected_layers.append("assembled_practice_context")
        context = ContextPacket(
            task_type=profile.task_type,
            user_request={"text": user_input, **self._request_metadata(kwargs)},
            client_context=client_context,
            user_profile={"instrument": kwargs.get("instrument", "piano"), "level": "unknown"},
            learner_context=learner_context,
            active_context=self._clean_dict(kwargs.get("active_context") or {}),
            material_context=self._clean_dict(kwargs.get("material_context") or {}),
            constraints=constraints,
            system_product_context=self._system_product_context(),
            selected_context_layers=selected_layers,
            allowed_tools=allowed_tools,
            tool_descriptors=tool_descriptors,
            output_contract={"schema": profile.output_schema, "response_case": "snake_case", "client_domain_case": "camelCase"},
            runtime_policy=self._runtime_policy(profile),
            routing_hints={
                "direct_client_callable": profile.task_type in {"practice_plan_generation", "immediate_practice_playback", "session_review"},
                "preferred_route": self._preferred_route(profile.task_type),
                "routine_history_context_intake_version": ROUTINE_HISTORY_CONTEXT_INTAKE_VERSION,
                "active_practice_plan_context_intake_version": ACTIVE_PRACTICE_PLAN_CONTEXT_INTAKE_VERSION,
                "practice_context_assembly_policy_version": PRACTICE_CONTEXT_ASSEMBLY_POLICY_VERSION,
                "context_engineering_skeleton_version": CONTEXT_ENGINEERING_SKELETON_VERSION,
                "today_practice_guidance_prompt_contract_version": TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_VERSION,
                "today_practice_guidance_output_validation_version": TODAY_PRACTICE_GUIDANCE_OUTPUT_VALIDATION_VERSION,
                "today_practice_guidance_provider_boundary_e2e_version": TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_VERSION,
                "routine_history_context_present": bool(routine_history_context),
                "active_practice_plan_context_present": bool(active_practice_plan_context),
                "assembled_practice_context_present": bool(assembled_practice_context),
                "engine_boundary": "Agent may use engine only through jammate_agent.adapters.",
            },
        )
        return context

    def profile_manifest(self) -> dict[str, Any]:
        return {key: profile.to_dict() for key, profile in CONTEXT_PROFILES.items()}


    def _runtime_policy(self, profile: ContextProfile) -> dict[str, Any]:
        provider_config = LLMProviderConfig.from_env()
        provider_status = provider_config.to_dict()
        return {
            "llm_required": profile.llm_required,
            "llm_provider_configured": provider_config.provider_configured,
            "llm_provider_boundary_version": provider_status["boundary_version"],
            "llm_provider_status": provider_status,
            "tool_registry_boundary_version": TOOL_REGISTRY_VERSION,
            "tool_invocation_preview_version": TOOL_INVOCATION_PREVIEW_VERSION,
            "tool_invocation_preview_policy": DEFAULT_TOOL_INVOCATION_PREVIEW_POLICY.to_dict(),
            "allowed_tool_validation": validate_allowed_tools(profile.allowed_tools),
            "deterministic_fallback": profile.deterministic_fallback,
            "max_tool_steps": 4,
            "tool_loop_mode": "bounded_preview",
            "llm_call_mode": "provider_boundary_preview_only",
            "tool_execution_enabled": False,
            "autonomous_tool_execution_enabled": False,
        }

    def _request_metadata(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for key in ("request_id", "available_minutes", "duration_minutes", "instrument"):
            if kwargs.get(key) is not None:
                metadata[key] = kwargs[key]
        if kwargs.get("local_unsynced_summary"):
            metadata["local_unsynced_summary"] = kwargs["local_unsynced_summary"]
        if kwargs.get("routine_history_context") or kwargs.get("practice_history_context"):
            metadata["routine_history_context_supplied"] = True
        if kwargs.get("active_practice_plan_context") or kwargs.get("active_practice_plan") or kwargs.get("practice_plan"):
            metadata["active_practice_plan_context_supplied"] = True
        if kwargs.get("assembled_practice_context") or kwargs.get("practice_context_assembly"):
            metadata["assembled_practice_context_supplied"] = True
        return metadata

    def _routine_history_context(self, kwargs: dict[str, Any], client_context: dict[str, Any]) -> dict[str, Any]:
        direct = kwargs.get("routine_history_context") or kwargs.get("practice_history_context")
        if isinstance(direct, dict):
            if direct.get("context_packet_section"):
                return self._clean_dict(direct.get("context_packet_section") or {})
            return self._clean_dict(direct)
        client_direct = client_context.get("routine_history_context") or client_context.get("practice_history_context")
        if isinstance(client_direct, dict):
            if client_direct.get("context_packet_section"):
                return self._clean_dict(client_direct.get("context_packet_section") or {})
            return self._clean_dict(client_direct)
        records = kwargs.get("routine_history_records") or kwargs.get("routineHistoryRecords") or client_context.get("routine_history_records") or client_context.get("routineHistoryRecords")
        if isinstance(records, list):
            return build_routine_history_context_intake_payload({"routineHistoryRecords": records}, source="context_builder").context_packet_section
        return {}

    def _active_practice_plan_context(self, kwargs: dict[str, Any], client_context: dict[str, Any]) -> dict[str, Any]:
        direct = kwargs.get("active_practice_plan_context") or kwargs.get("activePracticePlanContext")
        if isinstance(direct, dict):
            if direct.get("context_packet_section"):
                return self._clean_dict(direct.get("context_packet_section") or {})
            return self._clean_dict(direct)
        client_direct = client_context.get("active_practice_plan_context") or client_context.get("activePracticePlanContext")
        if isinstance(client_direct, dict):
            if client_direct.get("context_packet_section"):
                return self._clean_dict(client_direct.get("context_packet_section") or {})
            return self._clean_dict(client_direct)
        plan = kwargs.get("active_practice_plan") or kwargs.get("activePracticePlan") or kwargs.get("practice_plan") or kwargs.get("practicePlan") or client_context.get("active_practice_plan") or client_context.get("activePracticePlan") or client_context.get("practice_plan") or client_context.get("practicePlan")
        if isinstance(plan, dict):
            return build_active_practice_plan_context_intake_payload({"active_practice_plan": plan}, source="context_builder").context_packet_section
        return {}

    def _assembled_practice_context(self, kwargs: dict[str, Any], client_context: dict[str, Any], routine_history_context: dict[str, Any], active_practice_plan_context: dict[str, Any]) -> dict[str, Any]:
        direct = kwargs.get("assembled_practice_context") or kwargs.get("practice_context_assembly") or kwargs.get("practiceContextAssembly")
        if isinstance(direct, dict):
            if direct.get("assembled_context"):
                return self._clean_dict(direct.get("assembled_context") or {})
            return self._clean_dict(direct)
        client_direct = client_context.get("assembled_practice_context") or client_context.get("practice_context_assembly") or client_context.get("practiceContextAssembly")
        if isinstance(client_direct, dict):
            if client_direct.get("assembled_context"):
                return self._clean_dict(client_direct.get("assembled_context") or {})
            return self._clean_dict(client_direct)
        if active_practice_plan_context or routine_history_context:
            args: dict[str, Any] = {
                "active_practice_plan_context": active_practice_plan_context,
                "routine_history_context": routine_history_context,
            }
            if kwargs.get("available_minutes") is not None:
                args["available_minutes"] = kwargs.get("available_minutes")
            if kwargs.get("user_input") is not None:
                args["user_input"] = kwargs.get("user_input")
            return build_practice_context_assembly_policy_payload(args, source="context_builder").assembled_context
        return {}

    def _build_constraints(self, kwargs: dict[str, Any], client_context: dict[str, Any]) -> dict[str, Any]:
        available = kwargs.get("available_minutes") or client_context.get("available_minutes")
        duration = kwargs.get("duration_minutes") or client_context.get("available_minutes")
        return {
            "available_minutes": available,
            "duration_minutes": duration,
            "must_preserve_engine_independence": True,
            "harmonyos_local_timer_owns_practice_duration": True,
            "backend_response_case": "snake_case",
        }

    def _system_product_context(self) -> dict[str, Any]:
        return {
            "product": "JamMate",
            "architecture": "engine_agent_api_sibling_packages",
            "principles": [
                "LLM/Agent is an enhancement path, not required for direct accompaniment.",
                "HarmonyOS local practice workspace must run without LLM.",
                "Context packets are task-scoped and should not include unnecessary history.",
                "Routine history is used on the next user-initiated Agent planning turn, not as an automatic post-session card.",
            ],
            "package_boundaries": {
                "jammate_engine": "independent accompaniment generation kernel",
                "jammate_agent": "practice orchestration and future LLM/tool workflow layer",
                "jammate_api": "FastAPI assembly boundary",
            },
        }

    def _preferred_route(self, task_type: str) -> str | None:
        return {
            "practice_plan_generation": "POST /agent/practice/plan",
            "immediate_practice_playback": "POST /agent/playback/prepare",
            "session_review": "POST /agent/session/review",
            "coach_qa": None,
        }.get(task_type)

    def _clean_dict(self, value: dict[str, Any]) -> dict[str, Any]:
        return {str(key): item for key, item in value.items() if item is not None}
