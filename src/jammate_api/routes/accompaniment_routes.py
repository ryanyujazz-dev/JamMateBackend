from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from jammate_agent.capabilities.charts.chart_resolver import ChartResolver
from jammate_agent.capabilities.charts.models import ChartResolveRequest, ChartStatus
from jammate_engine.core.leadsheet.validation import LeadsheetValidationError
from jammate_engine.runtime.generate import generate_accompaniment
from jammate_api.schemas import DirectAccompanimentGenerateRequest

router = APIRouter(prefix="/accompaniment", tags=["accompaniment"])


@router.get("/styles")
def list_styles() -> dict[str, bool | list[str]]:
    return {"ok": True, "styles": ["medium_swing", "bossa_nova", "jazz_ballad"]}


@router.get("/capabilities")
def capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "capabilities": {
            "direct_engine_generation": True,
            "requires_llm": False,
            "styles": ["medium_swing", "bossa_nova", "jazz_ballad"],
            "supports_choruses": True,
            "supports_voicing_override": True,
            "supports_ensemble": True,
            "supports_inline_leadsheet_v2": True,
            "inline_leadsheet_schema_version": "jammate_leadsheet_v2",
            "inline_leadsheet_fields": ["sections", "written_form"],
            "response_case": "snake_case",
            "request_case": "snake_case_or_camelCase",
            "llm_required": False,
        },
    }


@router.post("/generate")
def generate_direct_accompaniment(request: DirectAccompanimentGenerateRequest) -> dict[str, Any]:
    leadsheet = request.leadsheet
    chart_source = "request.leadsheet"
    if leadsheet is None and request.tune:
        resolved = ChartResolver().resolve(ChartResolveRequest(tune=request.tune))
        if resolved.chart_status != ChartStatus.RESOLVED:
            return {
                "ok": False,
                "error_code": "CHART_NOT_FOUND",
                "message": resolved.message,
                "options": resolved.options,
            }
        leadsheet = resolved.leadsheet
        chart_source = resolved.source or "chart_resolver"
    if leadsheet is None:
        return {"ok": False, "error_code": "MISSING_LEADSHEET", "message": "Provide leadsheet or tune."}

    output_path = request.output_path or _default_output_path(leadsheet, request.style, request.tempo)
    generation_request = {
        "leadsheet": leadsheet,
        "style": request.style,
        "tempo": request.tempo,
        "choruses": request.choruses,
        "seed": request.seed,
        "output_path": output_path,
        "ensemble": _deep_camel_to_snake(request.ensemble),
        "voicing_override": _deep_camel_to_snake(request.voicing_override),
    }
    try:
        result = generate_accompaniment(generation_request)
    except LeadsheetValidationError as exc:
        return {
            "ok": False,
            "error_code": "INVALID_LEADSHEET",
            "message": str(exc),
            "issues": [issue.__dict__ for issue in exc.issues],
        }
    except ValueError as exc:
        return {"ok": False, "error_code": "INVALID_GENERATION_REQUEST", "message": str(exc)}
    if not result.ok or not result.midi_path:
        return {"ok": False, "error_code": "GENERATION_FAILED", "message": "JamMateEngine generation failed.", "debug": result.debug}
    midi_path = Path(result.midi_path)
    midi_base64 = base64.b64encode(midi_path.read_bytes()).decode("ascii")
    debug_summary = {
        "path": "direct_accompaniment_api",
        "chart_source": chart_source,
        "inline_leadsheet_schema_version": leadsheet.get("schema_version"),
        "leadsheet_signature": _leadsheet_signature(leadsheet),
        "engine_version": result.version,
        "style": result.style,
        "tempo": result.tempo,
        "choruses": request.choruses,
    }
    return {
        "ok": True,
        "asset": {
            "format": "midi_base64",
            "midi_base64": midi_base64,
            "midi_path": str(midi_path),
            "cache_key": _cache_key(leadsheet, request.style, request.tempo, request.choruses),
            "debug_summary": debug_summary,
        },
        "debug_summary": debug_summary,
    }


def _default_output_path(leadsheet: dict[str, Any], style: str, tempo: int) -> str:
    title = str(leadsheet.get("title", "direct_accompaniment"))
    safe_title = _safe_slug(title)
    signature = _leadsheet_signature(leadsheet)
    return f"demos/v2_4_13_direct_{safe_title}_{signature}_{style}_{tempo}.mid"


def _cache_key(leadsheet: dict[str, Any], style: str, tempo: int, choruses: int) -> str:
    title = str(leadsheet.get("title", "direct_accompaniment"))
    safe_title = _safe_slug(title)
    signature = _leadsheet_signature(leadsheet)
    return f"direct_accomp:{safe_title}:{signature}:{style}:{tempo}:choruses{choruses}"


def _safe_slug(value: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in value).strip("_") or "direct_accompaniment"


def _leadsheet_signature(leadsheet: dict[str, Any]) -> str:
    payload = json.dumps(leadsheet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _deep_camel_to_snake(value: Any) -> Any:
    if isinstance(value, list):
        return [_deep_camel_to_snake(item) for item in value]
    if isinstance(value, dict):
        return {_camel_to_snake_key(str(key)): _deep_camel_to_snake(item) for key, item in value.items()}
    return value


def _camel_to_snake_key(key: str) -> str:
    output: list[str] = []
    for char in key:
        if char.isupper():
            output.append("_")
            output.append(char.lower())
        else:
            output.append(char)
    return "".join(output).lstrip("_")
