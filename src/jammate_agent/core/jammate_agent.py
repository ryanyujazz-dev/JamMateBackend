from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jammate_agent.capabilities.accompaniment.playback_workflow import ImmediatePlaybackWorkflow
from jammate_agent.capabilities.practice.review_engine import ReviewEngine
from jammate_agent.core.capability_registry import CapabilityRegistry
from jammate_agent.core.context import ContextBuilder
from jammate_agent.core.guardrails import PracticePlanGuardrails
from jammate_agent.core.intent_classifier import AgentIntentType, IntentClassifier
from jammate_agent.core.runloop import BoundedAgentRunLoop
from jammate_agent.core.trace import AgentTrace, TraceLogger


@dataclass
class AgentContextRuntimeResult:
    ok: bool
    task_type: str
    context_packet: dict[str, Any]
    runloop_preview: dict[str, Any]
    trace_id: str | None = None
    error_code: str | None = None
    message: str | None = None


@dataclass
class AgentResult:
    ok: bool
    intent_type: str
    plan: dict[str, Any] | None = None
    practice_session: dict[str, Any] | None = None
    asset: dict[str, Any] | None = None
    playback_instruction: dict[str, Any] | None = None
    recommendation: dict[str, Any] | None = None
    explanation: str | None = None
    error_code: str | None = None
    message: str | None = None
    options: list[dict[str, Any]] = field(default_factory=list)
    trace_id: str | None = None


class JamMateAgent:
    """JamMate's top-level music-intent orchestration layer.

    The agent can call the accompaniment engine through a provider, but the
    engine remains an independent sibling package and direct API target.
    """

    def __init__(self, capabilities: CapabilityRegistry, trace_logger: TraceLogger | None = None) -> None:
        self.capabilities = capabilities
        self.intent_classifier = IntentClassifier()
        self.context_builder = ContextBuilder()
        self.runloop = BoundedAgentRunLoop()
        self.guardrails = PracticePlanGuardrails()
        self.trace_logger = trace_logger or TraceLogger()

    def handle_message(self, user_input: str, request_id: str | None = None, available_minutes: int | None = None) -> AgentResult:
        intent = self.intent_classifier.classify(user_input)
        if intent == AgentIntentType.IMMEDIATE_PRACTICE_PLAYBACK:
            return self.prepare_playback(user_input, duration_minutes=available_minutes or self._extract_minutes(user_input) or 30, request_id=request_id)
        if intent == AgentIntentType.PRACTICE_PLAN_GENERATION:
            return self.generate_practice_plan(user_input, available_minutes=available_minutes or self._extract_minutes(user_input) or 45, request_id=request_id)
        return AgentResult(ok=False, intent_type=intent.value, message="P0 JamMate Agent 暂未实现该任务类型。")

    def generate_practice_plan(self, user_input: str, available_minutes: int = 45, instrument: str = "piano", request_id: str | None = None) -> AgentResult:
        trace = self.trace_logger.start(AgentIntentType.PRACTICE_PLAN_GENERATION.value, user_input, request_id)
        context = self.context_builder.build(AgentIntentType.PRACTICE_PLAN_GENERATION.value, user_input, available_minutes=available_minutes, instrument=instrument)
        trace.context_packet_summary = {"task_type": context.task_type, "available_minutes": available_minutes}
        self.trace_logger.add_step(trace, "context_built", trace.context_packet_summary)
        plan = self.capabilities.practice_planner.build_plan(user_input, available_minutes=available_minutes, instrument=instrument)
        self.guardrails.normalize(plan)
        errors = self.guardrails.validate(plan)
        if errors:
            self.trace_logger.finish(trace, "failed", {"errors": errors})
            return AgentResult(ok=False, intent_type=AgentIntentType.PRACTICE_PLAN_GENERATION.value, error_code="PLAN_VALIDATION_FAILED", message="PracticePlan 校验失败。", options=[{"type": "validation_error", "label": e} for e in errors], trace_id=trace.trace_id)
        self.trace_logger.add_step(trace, "plan_generated", {"plan_id": plan.plan_id, "blocks": len(plan.blocks)})
        self.trace_logger.finish(trace, "passed", {"plan_id": plan.plan_id})
        return AgentResult(ok=True, intent_type=AgentIntentType.PRACTICE_PLAN_GENERATION.value, plan=plan.to_dict(), explanation=plan.explanation, trace_id=trace.trace_id)

    def prepare_playback(self, user_input: str, duration_minutes: int = 30, request_id: str | None = None) -> AgentResult:
        trace = self.trace_logger.start(AgentIntentType.IMMEDIATE_PRACTICE_PLAYBACK.value, user_input, request_id)
        context = self.context_builder.build(AgentIntentType.IMMEDIATE_PRACTICE_PLAYBACK.value, user_input, duration_minutes=duration_minutes)
        trace.context_packet_summary = {"task_type": context.task_type, "duration_minutes": duration_minutes}
        self.trace_logger.add_step(trace, "context_built", trace.context_packet_summary)
        workflow = ImmediatePlaybackWorkflow(self.capabilities.chart_resolver, self.capabilities.accompaniment_provider)
        result = workflow.prepare(user_input, duration_minutes=duration_minutes)
        self.trace_logger.add_step(trace, "playback_workflow_completed", {"ok": result.ok, "error_code": result.error_code})
        self.trace_logger.finish(trace, "passed" if result.ok else "failed", {"intent_type": result.intent_type})
        return AgentResult(
            ok=result.ok,
            intent_type=result.intent_type,
            practice_session=result.practice_session,
            asset=result.asset,
            playback_instruction=result.playback_instruction,
            explanation=result.explanation,
            error_code=result.error_code,
            message=result.message,
            options=result.options or [],
            trace_id=trace.trace_id,
        )


    def build_llm_context_runtime(
        self,
        user_input: str,
        task_type: str | None = None,
        request_id: str | None = None,
        client_context: dict[str, Any] | None = None,
        available_minutes: int | None = None,
        duration_minutes: int | None = None,
        instrument: str = "piano",
        local_unsynced_summary: dict[str, Any] | None = None,
    ) -> AgentContextRuntimeResult:
        resolved_task_type = task_type or self.intent_classifier.classify(user_input).value
        trace = self.trace_logger.start("llm_context_runtime_preview", user_input, request_id)
        context = self.context_builder.build(
            resolved_task_type,
            user_input,
            request_id=request_id,
            client_context=client_context or {},
            available_minutes=available_minutes,
            duration_minutes=duration_minutes,
            instrument=instrument,
            local_unsynced_summary=local_unsynced_summary or {},
        )
        trace.context_packet_summary = context.summary()
        self.trace_logger.add_step(trace, "context_runtime_packet_built", trace.context_packet_summary)
        runloop_preview = self.runloop.preview(context)
        self.trace_logger.add_step(trace, "bounded_runloop_previewed", runloop_preview.to_dict())
        self.trace_logger.finish(trace, "passed", {"task_type": context.task_type, "next_action": runloop_preview.next_action})
        return AgentContextRuntimeResult(
            ok=True,
            task_type=context.task_type,
            context_packet=context.to_dict(),
            runloop_preview=runloop_preview.to_dict(),
            trace_id=trace.trace_id,
        )

    def get_trace(self, trace_id: str) -> AgentTrace | None:
        return self.trace_logger.get(trace_id)

    def list_recent_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.trace_logger.list_recent(limit=limit)

    def _extract_minutes(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*(分钟|min)", text, re.IGNORECASE)
        return int(match.group(1)) if match else None
