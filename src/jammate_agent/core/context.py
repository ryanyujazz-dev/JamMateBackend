from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONTEXT_RUNTIME_VERSION = "v2_4_1"


@dataclass
class CapabilityManifest:
    available_styles: list[str] = field(default_factory=lambda: ["medium_swing", "bossa_nova", "jazz_ballad"])
    available_practice_modes: list[str] = field(default_factory=lambda: ["general_practice", "piano_comping", "solo_improvisation", "time_feel", "repertoire"])
    can_mute_roles: list[str] = field(default_factory=lambda: ["piano", "bass", "drums", "melody"])
    supports_loop_count: bool = True
    supports_harmonic_expansion: bool = True
    supports_llm_context_runtime_preview: bool = True
    supports_bounded_tool_loop_preview: bool = True
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
            "output_schema": self.output_schema,
            "llm_required": self.llm_required,
            "deterministic_fallback": self.deterministic_fallback,
        }


CONTEXT_PROFILES: dict[str, ContextProfile] = {
    "practice_plan_generation": ContextProfile(
        task_type="practice_plan_generation",
        required_context_layers=("system_product_context", "capability_manifest", "user_request", "client_context"),
        optional_context_layers=("learner_summary", "active_goal", "relevant_history", "routine_templates"),
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
    "coach_qa": ContextProfile(
        task_type="coach_qa",
        required_context_layers=("system_product_context", "capability_manifest", "user_question", "client_context"),
        optional_context_layers=("music_concept_context", "relevant_history", "current_screen_or_session"),
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
        context = ContextPacket(
            task_type=profile.task_type,
            user_request={"text": user_input, **self._request_metadata(kwargs)},
            client_context=client_context,
            user_profile={"instrument": kwargs.get("instrument", "piano"), "level": "unknown"},
            learner_context=self._clean_dict(kwargs.get("learner_context") or {"recent_focus": [], "recent_weak_points": [], "note": "P0 placeholder; replace with LearnerModel summary."}),
            active_context=self._clean_dict(kwargs.get("active_context") or {}),
            material_context=self._clean_dict(kwargs.get("material_context") or {}),
            constraints=constraints,
            system_product_context=self._system_product_context(),
            selected_context_layers=[*profile.required_context_layers, *profile.optional_context_layers],
            allowed_tools=list(profile.allowed_tools),
            output_contract={"schema": profile.output_schema, "response_case": "snake_case", "client_domain_case": "camelCase"},
            runtime_policy={
                "llm_required": profile.llm_required,
                "llm_provider_configured": False,
                "deterministic_fallback": profile.deterministic_fallback,
                "max_tool_steps": 4,
                "tool_loop_mode": "bounded_preview",
            },
            routing_hints={
                "direct_client_callable": profile.task_type in {"practice_plan_generation", "immediate_practice_playback", "session_review"},
                "preferred_route": self._preferred_route(profile.task_type),
                "engine_boundary": "Agent may use engine only through jammate_agent.adapters.",
            },
        )
        return context

    def profile_manifest(self) -> dict[str, Any]:
        return {key: profile.to_dict() for key, profile in CONTEXT_PROFILES.items()}

    def _request_metadata(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for key in ("request_id", "available_minutes", "duration_minutes", "instrument"):
            if kwargs.get(key) is not None:
                metadata[key] = kwargs[key]
        if kwargs.get("local_unsynced_summary"):
            metadata["local_unsynced_summary"] = kwargs["local_unsynced_summary"]
        return metadata

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
