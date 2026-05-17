from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    """API model that accepts both snake_case and ArkTS-friendly camelCase."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ClientContext(ApiModel):
    timezone: str = "America/New_York"
    locale: str = "zh-CN"
    current_screen: str | None = None
    available_minutes: int | None = None
    active_session_id: str | None = None
    active_plan_id: str | None = None
    selected_material_id: str | None = None


class AgentMessageRequest(ApiModel):
    request_id: str | None = None
    user_input: str
    client_context: ClientContext = Field(default_factory=ClientContext)
    local_unsynced_summary: dict[str, Any] = Field(default_factory=dict)


class AgentPlanRequest(ApiModel):
    user_input: str
    available_minutes: int = 45
    instrument: str = "piano"
    active_goal_id: str | None = None


class AgentPlaybackPrepareRequest(ApiModel):
    user_input: str
    duration_minutes: int = 30
    client_context: ClientContext = Field(default_factory=ClientContext)


class SessionReviewRequest(ApiModel):
    session_id: str
    completed: bool = True
    difficulty: str = "good_challenge"
    focus_score: int | None = None
    time_feel: str | None = None
    tempo_result: dict[str, Any] | None = None
    stuck_points: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None
    next_action_preference: str | None = None


class DirectAccompanimentGenerateRequest(ApiModel):
    leadsheet: dict[str, Any] | None = None
    tune: str | None = None
    style: str = "medium_swing"
    tempo: int = 120
    choruses: int = 3
    seed: int = 42
    output_path: str | None = None
    ensemble: dict[str, Any] = Field(default_factory=dict)
    voicing_override: dict[str, Any] = Field(default_factory=dict)
    output_format: Literal["midi_base64"] = "midi_base64"


class ApiResponse(ApiModel):
    ok: bool
    payload: dict[str, Any] | None = None
    error_code: str | None = None
    message: str | None = None
