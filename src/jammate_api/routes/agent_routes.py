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
    arkts_contract_sketch,
    arkts_contract_source,
    context_profile_manifest,
    harmonyos_playback_contract,
    llm_context_runtime_contract,
    response_case_policy_manifest,
)
from jammate_agent.core.jammate_agent import JamMateAgent
from jammate_agent.core.trace import JsonTraceStore, TraceLogger
from jammate_api.schemas import AgentContextRuntimePreviewRequest, AgentMessageRequest, AgentPlanRequest, AgentPlaybackPrepareRequest, SessionReviewRequest

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


@router.get("/traces")
def list_agent_traces(limit: int = 20) -> dict:
    return {"ok": True, "traces": build_agent().list_recent_traces(limit=limit)}


@router.get("/traces/{trace_id}")
def get_agent_trace(trace_id: str) -> dict:
    trace = build_agent().get_trace(trace_id)
    if not trace:
        return {"ok": False, "error_code": "TRACE_NOT_FOUND", "message": f"Trace not found: {trace_id}"}
    return {"ok": True, "trace": trace}


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
