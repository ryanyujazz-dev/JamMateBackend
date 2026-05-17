from __future__ import annotations

from fastapi import APIRouter

from jammate_engine.api.version import ENGINE_VERSION_TAG

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "jammate-api", "engine_version": ENGINE_VERSION_TAG, "agent_version": "v0_1"}
