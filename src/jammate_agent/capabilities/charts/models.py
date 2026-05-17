from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChartStatus(str, Enum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    NEED_USER_INPUT = "need_user_input"


@dataclass
class ChartResolveRequest:
    tune: str | None = None
    key: str | None = None
    user_provided_progression: str | None = None


@dataclass
class ChartResolveResult:
    chart_status: ChartStatus
    source: str | None = None
    leadsheet: dict[str, Any] | None = None
    confidence: str = "low"
    requires_user_confirmation: bool = False
    message: str | None = None
    options: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_status": self.chart_status.value,
            "source": self.source,
            "leadsheet": self.leadsheet,
            "confidence": self.confidence,
            "requires_user_confirmation": self.requires_user_confirmation,
            "message": self.message,
            "options": list(self.options),
        }
