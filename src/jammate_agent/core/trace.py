from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jammate_agent.capabilities.practice.models import new_id


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
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentTrace":
        data = dict(payload)
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
                trace = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            items.append(
                {
                    "trace_id": trace.get("trace_id"),
                    "task_type": trace.get("task_type"),
                    "validation_result": trace.get("validation_result"),
                    "created_at": trace.get("created_at"),
                    "steps": len(trace.get("steps", [])),
                }
            )
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
        return [
            {
                "trace_id": trace.trace_id,
                "task_type": trace.task_type,
                "validation_result": trace.validation_result,
                "created_at": trace.created_at.isoformat(),
                "steps": len(trace.steps),
            }
            for trace in traces[:limit]
        ]

    def _persist(self, trace: AgentTrace) -> None:
        if self.trace_store:
            self.trace_store.save(trace)
