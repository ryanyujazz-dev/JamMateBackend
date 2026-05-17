from __future__ import annotations

from fastapi import FastAPI

from jammate_api.routes.accompaniment_routes import router as accompaniment_router
from jammate_api.routes.agent_routes import router as agent_router
from jammate_api.routes.health_routes import router as health_router
from jammate_api.routes.practice_routes import router as practice_router

APP_VERSION = "v2_4_0_agent_llm_context_runtime_foundation"

app = FastAPI(
    title="JamMate API",
    version=APP_VERSION,
    description="Service layer exposing direct JamMate Engine APIs and JamMate Agent orchestration APIs.",
)

app.include_router(health_router)
app.include_router(accompaniment_router)
app.include_router(agent_router)
app.include_router(practice_router)
