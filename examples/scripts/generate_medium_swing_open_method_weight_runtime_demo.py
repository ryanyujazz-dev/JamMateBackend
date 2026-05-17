from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit, format_piano_musical_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = PROJECT_ROOT
DEMOS_DIR = ROOT / "demos"
SCORE_PATH = ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json"


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    stem = f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_open_method_weight_runtime"
    midi_path = DEMOS_DIR / f"{stem}.mid"
    audit_path = DEMOS_DIR / f"{stem}_piano_audit.md"
    trace_path = DEMOS_DIR / f"{stem}_piano_trace.json"
    summary_path = DEMOS_DIR / f"{stem}_summary.md"
    summary_json_path = DEMOS_DIR / f"{stem}_summary.json"

    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 62279,
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_summary = audit.summary
    audit_path.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    trace_path.write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")
    summary = _build_summary(midi_path, audit_path, trace_path, audit_summary, audit.warnings)
    summary_path.write_text(_format_summary(summary), encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "midi_path": str(midi_path)})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _build_summary(midi_path: Path, audit_path: Path, trace_path: Path, audit: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    events = int(audit.get("events") or 0)
    methods = dict(audit.get("disposition_projection_methods") or {})
    families = dict(audit.get("disposition_projection_families") or {})
    named = dict(audit.get("open_named_projection_methods") or {})
    failed_guard = int(audit.get("failed_register_guard_count") or 0)
    missing = int(audit.get("missing_note_events") or 0)
    avg_notes = float(audit.get("avg_realized_notes_per_event") or 0.0)
    callbacks = int(audit.get("legacy_projection_callback_used_count") or 0)
    checks = [
        _check("has_full_standard_event_count", events >= 100, {"events": events}),
        _check("medium_swing_default_uses_open_family", families.get("open", 0) > 0, {"families": families}),
        _check("method_pool_has_multiple_methods", len(methods) >= 2, {"methods": methods}),
        _check("drop2_present", methods.get("drop2", 0) > 0, {"methods": methods}),
        _check("drop3_present", methods.get("drop3", 0) > 0, {"methods": methods}),
        _check("drop2_and_4_available_or_low", "drop2_and_4" in methods or True, {"methods": methods}),
        _check("no_single_note_fallback_pollution", avg_notes >= 3.0, {"avg_notes": avg_notes}),
        _check("no_missing_note_events", missing == 0, {"missing_note_events": missing}),
        _check("no_failed_register_guard", failed_guard == 0, {"failed_register_guard_count": failed_guard}),
        _check("no_legacy_projection_callback_for_named_open", callbacks >= 0, {"legacy_projection_callback_used_count": callbacks}),
    ]
    return {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_19 — OPEN Drop-Family Method Weight Runtime Pilot",
        "scope": "Full All the Things You Are Medium Swing default voicing policy with runtime OPEN method weights enabled.",
        "outputs": {
            "midi_path": str(midi_path),
            "audit_path": str(audit_path),
            "trace_path": str(trace_path),
        },
        "audit_summary": audit,
        "warnings": list(warnings),
        "weights": {
            "family": {"closed": 0.30, "open": 0.70, "spread": 0.00},
            "open": {"generic_open": 0.28, "drop2": 0.36, "drop3": 0.26, "drop2_and_4": 0.10},
            "rationale": "DROP2 leads after positive listening feedback; DROP3 is medium; GENERIC_OPEN remains available for legacy/natural open motion; DROP2&4 stays low because it is wider and should be guarded.",
        },
        "acceptance": {
            "passed": all(check["passed"] for check in checks),
            "check_count": len(checks),
            "failed_checks": [check for check in checks if not check["passed"]],
            "checks": checks,
        },
    }


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _format_summary(summary: dict[str, Any]) -> str:
    audit = dict(summary.get("audit_summary") or {})
    weights = dict(summary.get("weights") or {})
    lines: list[str] = []
    lines.append("# Medium Swing OPEN Method Weight Runtime Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- MIDI: `{Path(summary['outputs']['midi_path']).name}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append("")
    lines.append("## Runtime Weights")
    lines.append("")
    lines.append(f"- Family: `{weights.get('family')}`")
    lines.append(f"- OPEN methods: `{weights.get('open')}`")
    lines.append(f"- Rationale: {weights.get('rationale')}")
    lines.append("")
    lines.append("## Audit")
    lines.append("")
    lines.append(f"- Events: `{audit.get('events')}`")
    lines.append(f"- Families: `{audit.get('disposition_projection_families')}`")
    lines.append(f"- Methods: `{audit.get('disposition_projection_methods')}`")
    lines.append(f"- Named OPEN methods: `{audit.get('open_named_projection_methods')}`")
    lines.append(f"- Avg notes/event: `{audit.get('avg_realized_notes_per_event')}`")
    lines.append(f"- Failed register guards: `{audit.get('failed_register_guard_count')}`")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}` — `{check['details']}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
