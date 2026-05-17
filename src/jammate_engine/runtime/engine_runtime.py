from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.engine import JamMateEngine
from jammate_engine.runtime.generation_request import GenerationRequest
from jammate_engine.runtime.generation_result import GenerationResult


class EngineRuntime:
    def generate(self, request: GenerationRequest) -> GenerationResult:
        engine = JamMateEngine()
        output_path = request.output_path or f"demos/{ENGINE_VERSION_TAG}_minimal_demo.mid"
        midi_path, debug = engine.generate(request, Path(output_path))
        return GenerationResult(
            ok=True,
            midi_path=str(midi_path),
            version=ENGINE_VERSION_TAG,
            style=request.style,
            tempo=request.tempo,
            debug=debug,
        )
