from __future__ import annotations

from .generation_request import GenerationRequest
from .generation_result import GenerationResult
from .engine_runtime import EngineRuntime


def generate_accompaniment(request: GenerationRequest | dict) -> GenerationResult:
    """Public runtime entrypoint."""
    if isinstance(request, dict):
        request = GenerationRequest.from_dict(request)
    return EngineRuntime().generate(request)
