from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jammate_agent.capabilities.practice.models import new_id

TRACE_API_CONTRACT_VERSION = "v2_4_13"
TRACE_DETAIL_SCHEMA_VERSION = "agent_trace_detail_v1"
TRACE_SUMMARY_SCHEMA_VERSION = "agent_trace_summary_v1"
TRACE_NOT_FOUND_ERROR_CODE = "TRACE_NOT_FOUND"


def _preview_text(value: str | None, max_chars: int = 120) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


@dataclass
class AgentTrace:
    task_type: str
    user_input: str
    request_id: str | None = None
    trace_id: str = field(default_factory=lambda: new_id("trace"))
    context_packet_summary: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    validation_result: str | None = None
    final_response_summary: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Legacy/raw JSON representation kept for persisted trace compatibility."""
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload

    def to_summary_dict(self) -> dict[str, Any]:
        """Stable list-item contract for GET /agent/traces."""
        step_count = len(self.steps)
        return {
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "trace_schema_version": TRACE_SUMMARY_SCHEMA_VERSION,
            "trace_id": self.trace_id,
            "task_type": self.task_type,
            "request_id": self.request_id,
            "user_input_preview": _preview_text(self.user_input),
            "validation_result": self.validation_result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "step_count": step_count,
            "steps": step_count,  # Backward-compatible alias for older diagnostics.
            "has_context_packet_summary": bool(self.context_packet_summary),
            "has_final_response_summary": bool(self.final_response_summary),
        }

    def to_detail_dict(self) -> dict[str, Any]:
        """Stable detail contract for GET /agent/traces/{trace_id}."""
        return {
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "trace_schema_version": TRACE_DETAIL_SCHEMA_VERSION,
            "trace_id": self.trace_id,
            "task_type": self.task_type,
            "request_id": self.request_id,
            "user_input": self.user_input,
            "context_packet_summary": dict(self.context_packet_summary),
            "steps": [dict(step) for step in self.steps],
            "validation_result": self.validation_result,
            "final_response_summary": dict(self.final_response_summary),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentTrace":
        data = dict(payload)
        # Persisted v2_4_13+ detail payloads include schema fields that are not
        # dataclass constructor inputs. Keep loading tolerant for API-exported
        # details copied back into a trace directory.
        for key in ("trace_contract_version", "trace_schema_version", "step_count", "has_context_packet_summary", "has_final_response_summary"):
            data.pop(key, None)
        if "user_input_preview" in data and "user_input" not in data:
            data["user_input"] = data.pop("user_input_preview") or ""
        else:
            data.pop("user_input_preview", None)
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class JsonTraceStore:
    """Tiny JSON trace store for local debugging and HarmonyOS integration tests."""

    def __init__(self, trace_dir: str | Path = "demos/agent_traces") -> None:
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def save(self, trace: AgentTrace) -> Path:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        trace.updated_at = datetime.now()
        path = self.trace_dir / f"{trace.trace_id}.json"
        path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, trace_id: str) -> AgentTrace | None:
        path = self.trace_dir / f"{trace_id}.json"
        if not path.exists():
            return None
        return AgentTrace.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        files = sorted(self.trace_dir.glob("trace_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        items: list[dict[str, Any]] = []
        for path in files[:limit]:
            try:
                trace = AgentTrace.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            items.append(trace.to_summary_dict())
        return items


class TraceLogger:
    def __init__(self, trace_store: JsonTraceStore | None = None) -> None:
        self._traces: dict[str, AgentTrace] = {}
        self.trace_store = trace_store

    def start(self, task_type: str, user_input: str, request_id: str | None = None) -> AgentTrace:
        trace = AgentTrace(task_type=task_type, user_input=user_input, request_id=request_id)
        self._traces[trace.trace_id] = trace
        self._persist(trace)
        return trace

    def add_step(self, trace: AgentTrace, name: str, payload: dict[str, Any] | None = None) -> None:
        trace.steps.append({"name": name, "payload": payload or {}, "at": datetime.now().isoformat()})
        self._persist(trace)

    def finish(self, trace: AgentTrace, validation_result: str, final_response_summary: dict[str, Any]) -> AgentTrace:
        trace.validation_result = validation_result
        trace.final_response_summary = final_response_summary
        self._traces[trace.trace_id] = trace
        self._persist(trace)
        return trace

    def get(self, trace_id: str) -> AgentTrace | None:
        if trace_id in self._traces:
            return self._traces[trace_id]
        if self.trace_store:
            trace = self.trace_store.load(trace_id)
            if trace:
                self._traces[trace_id] = trace
            return trace
        return None

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if self.trace_store:
            return self.trace_store.list_recent(limit=limit)
        traces = sorted(self._traces.values(), key=lambda t: t.updated_at, reverse=True)
        return [trace.to_summary_dict() for trace in traces[:limit]]

    def _persist(self, trace: AgentTrace) -> None:
        if self.trace_store:
            self.trace_store.save(trace)


def trace_api_contract() -> dict[str, Any]:
    """Stable Agent trace API contract for HarmonyOS and terminal debugging."""
    return {
        "version": TRACE_API_CONTRACT_VERSION,
        "trace_contract_version": TRACE_API_CONTRACT_VERSION,
        "routes": {
            "spec": "GET /agent/traces/spec",
            "list": "GET /agent/traces?limit=20",
            "detail": "GET /agent/traces/{trace_id}",
        },
        "storage": {
            "default_trace_dir": "demos/agent_traces",
            "terminal_trace_export_enabled_by": "--trace-dir <dir>",
            "terminal_trace_viewer": "python -m jammate_agent.cli.trace_viewer --trace-dir <dir> list|show|spec",
            "format": "JSON files named trace_<id>.json",
        },
        "list_response_schema": {
            "ok": "boolean",
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "traces": "AgentTraceSummary[]",
        },
        "detail_response_schema": {
            "ok": "boolean",
            "trace_contract_version": TRACE_API_CONTRACT_VERSION,
            "trace": "AgentTraceDetail | null",
            "error_code": f"{TRACE_NOT_FOUND_ERROR_CODE} | null",
        },
        "summary_fields": [
            "trace_contract_version",
            "trace_schema_version",
            "trace_id",
            "task_type",
            "request_id",
            "user_input_preview",
            "validation_result",
            "created_at",
            "updated_at",
            "step_count",
            "has_context_packet_summary",
            "has_final_response_summary",
        ],
        "detail_fields": [
            "trace_contract_version",
            "trace_schema_version",
            "trace_id",
            "task_type",
            "request_id",
            "user_input",
            "context_packet_summary",
            "steps",
            "validation_result",
            "final_response_summary",
            "created_at",
            "updated_at",
        ],
        "tool_call_preview_trace_contract": {
            "version": TRACE_API_CONTRACT_VERSION,
            "summary_field": "final_response_summary.tool_call_preview_trace_summary",
            "step_name": "terminal_tool_call_preview_trace_summary_recorded",
            "chain": "LLM response -> JSON candidate extraction -> tool invocation preview -> execution guard",
            "execution_enabled": False,
        },
        "tool_execution_confirmation_trace_contract": {
            "version": "v2_6_2",
            "summary_field": "final_response_summary.tool_execution_confirmation_summary",
            "step_names": [
                "terminal_tool_confirmation_envelope_created",
                "terminal_tool_confirmation_user_approved",
                "terminal_tool_confirmation_user_rejected",
            ],
            "chain": "tool invocation preview -> confirmation envelope -> user approve/reject -> execution remains disabled",
            "execution_enabled": False,
            "dispatch_enabled": False,
            "engine_adapter_dispatch_enabled": False,
        },
        "tool_executor_trace_contract": {
            "version": "v2_6_3",
            "summary_field": "final_response_summary.tool_executor_summary",
            "step_names": [
                "terminal_tool_executor_dry_run_requested",
                "terminal_tool_executor_dry_run_completed",
                "terminal_tool_executor_dry_run_blocked",
            ],
            "chain": "approved confirmation -> dry-run ToolExecutor request/result -> no-op result -> dispatcher still required",
            "dry_run_enabled": True,
            "real_execution_enabled": False,
            "dispatch_enabled": False,
            "engine_adapter_dispatch_enabled": False,
        },
        "tool_workflow_dispatcher_trace_contract": {
            "version": "v2_6_4",
            "summary_field": "final_response_summary.tool_workflow_dispatcher_summary",
            "step_names": [
                "terminal_tool_workflow_dispatch_dry_run_requested",
                "terminal_tool_workflow_descriptor_resolved",
                "terminal_tool_workflow_dispatch_dry_run_blocked",
            ],
            "chain": "dry-run ToolExecutor result -> deterministic workflow descriptor resolution -> no workflow invocation",
            "dry_run_enabled": True,
            "workflow_descriptor_resolution_enabled": True,
            "real_workflow_dispatch_enabled": False,
            "route_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
        },
        "controlled_workflow_execution_trace_contract": {
            "version": "v2_6_5",
            "summary_field": "final_response_summary.controlled_workflow_execution_summary",
            "step_names": [
                "terminal_controlled_workflow_execution_requested",
                "terminal_controlled_workflow_execution_completed",
                "terminal_controlled_workflow_execution_blocked",
            ],
            "chain": "workflow descriptor resolution -> allow-listed controlled PracticePlanner execution -> structured PracticePlan output",
            "controlled_execution_enabled": True,
            "allowed_tool_names": ["agent_practice_plan"],
            "allowed_workflow_names": ["PracticePlanner.build_plan"],
            "route_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "harmonyos_agent_action_trace_contract": {
            "version": "v2_6_6",
            "summary_field": "final_response_summary.harmonyos_agent_action_summary",
            "step_names": [
                "terminal_harmonyos_agent_action_card_built",
                "api_harmonyos_agent_action_card_built",
            ],
            "chain": "preview/confirmation/executor/dispatcher/controlled result -> Routine-facing AgentActionCard",
            "action_card_enabled": True,
            "controlled_practice_plan_execution_enabled": True,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "agent_runtime_skeleton_cleanup_trace_contract": {
            "version": "v2_6_7",
            "summary_field": "final_response_summary.agent_runtime_skeleton_summary",
            "step_names": [
                "terminal_agent_runtime_skeleton_snapshot_built",
                "api_agent_runtime_skeleton_snapshot_built",
            ],
            "chain": "runtime skeleton inspection only; no preview/confirm/execute side effects",
            "read_only_status_enabled": True,
            "controlled_practice_plan_execution_enabled": True,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "practice_plan_action_card_e2e_trace_contract": {
            "version": "v2_6_8",
            "summary_field": "final_response_summary.practice_plan_action_card_e2e_summary",
            "step_names": [
                "terminal_practice_plan_action_card_payload_built",
                "terminal_practice_plan_action_card_summary_recorded",
                "api_practice_plan_action_card_payload_built",
            ],
            "chain": "controlled agent_practice_plan result -> Routine-facing practice-plan ActionCard payload",
            "routine_payload_enabled": True,
            "open_routine_setup_enabled": True,
            "playback_execution_enabled": False,
            "accompaniment_generate_call_enabled": False,
            "engine_adapter_dispatch_enabled": False,
            "midi_asset_creation_enabled": False,
        },
        "guards": {
            "trace_api_executes_tools": False,
            "trace_api_calls_llm_provider": False,
            "trace_api_calls_engine_adapter": False,
            "trace_viewer_executes_tools": False,
            "trace_viewer_calls_llm_provider": False,
            "trace_viewer_calls_engine_adapter": False,
            "raw_trace_file_path_exposed_by_api": False,
        },
    }
