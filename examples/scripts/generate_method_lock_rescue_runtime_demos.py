from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit, format_piano_musical_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = PROJECT_ROOT
DEMOS_DIR = ROOT / "demos"
SCORE_PATH = ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json"

BASIC_4NOTE_OPEN = {
    "enabled": True,
    "preset": "basic_4note_1357",
    "preferred_disposition": "open",
    "allowed_dispositions": ["open"],
    "preferred_density": 4,
    "min_density": 4,
    "max_density": 4,
}

DROP2_LOCK_OVERRIDE = {
    **BASIC_4NOTE_OPEN,
    "metadata": {
        "voicing_method_lock": {
            "enabled": True,
            "mode": "strict",
            "scope": "progression",
            "pattern": "ii_v_i",
            "family": "open",
            "method": "drop2",
            "runtime_filtering_enabled": True,
        }
    },
}

RESCUE_TO_CLOSED_OVERRIDE = {
    **BASIC_4NOTE_OPEN,
    "metadata": {
        "voicing_method_lock": {
            "enabled": True,
            "mode": "strict",
            "scope": "progression",
            "pattern": "ii_v_i",
            "family": "spread",
            "method": "lower_upper_grouped",
            "runtime_filtering_enabled": True,
            "method_lock_rescue_runtime_enabled": True,
        }
    },
}

DEMO_SPECS = [
    {
        "id": "medium_swing_ii_v_i_open_drop2_method_lock",
        "style": "medium_swing",
        "tempo": 132,
        "choruses": 3,
        "seed": 22151,
        "override": DROP2_LOCK_OVERRIDE,
        "description": "Strict progression method lock: OPEN + DROP2. No rescue should be needed.",
    },
    {
        "id": "medium_swing_ii_v_i_method_lock_rescue_closed",
        "style": "medium_swing",
        "tempo": 132,
        "choruses": 3,
        "seed": 22152,
        "override": RESCUE_TO_CLOSED_OVERRIDE,
        "description": "Explicit runtime rescue: impossible SPREAD lock falls back audibly to CLOSED + COMPACT.",
    },
    {
        "id": "bossa_ii_v_i_method_lock_rescue_closed",
        "style": "bossa_nova",
        "tempo": 128,
        "choruses": 3,
        "seed": 22153,
        "override": RESCUE_TO_CLOSED_OVERRIDE,
        "description": "Bossa rhythm with the same explicit rescue path, to confirm style pattern preservation.",
    },
]


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    outputs = [_generate_one(score, spec) for spec in DEMO_SPECS]
    summary = _build_summary(outputs)
    summary_md = _format_summary(summary)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_method_lock_rescue_runtime_demo_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_method_lock_rescue_runtime_demo_summary.json"
    summary_path.write_text(summary_md, encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": summary["acceptance"]["passed"], "summary": str(summary_path), "outputs": outputs}, indent=2, ensure_ascii=False))
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_one(score: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    stem = f"{ENGINE_VERSION_TAG}_{spec['id']}"
    midi_path = DEMOS_DIR / f"{stem}.mid"
    audit_path = DEMOS_DIR / f"{stem}_piano_audit.md"
    trace_path = DEMOS_DIR / f"{stem}_piano_trace.json"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": spec["style"],
            "tempo": int(spec["tempo"]),
            "choruses": int(spec["choruses"]),
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(spec["override"]),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_path.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    trace_path.write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")
    rescue_events = 0
    rescue_actions: dict[str, int] = {}
    for event in result.debug.get("piano_musical_audit_events") or []:
        metadata = dict((event.get("voicing") or {}).get("metadata") or {})
        if metadata.get("voicing_method_lock_rescue_runtime_executed"):
            rescue_events += 1
            action = str(metadata.get("voicing_method_lock_rescue_runtime_action") or "unknown")
            rescue_actions[action] = rescue_actions.get(action, 0) + 1
    return {
        "id": spec["id"],
        "style": spec["style"],
        "tempo": int(spec["tempo"]),
        "choruses": int(spec["choruses"]),
        "seed": int(spec["seed"]),
        "description": spec["description"],
        "midi_path": str(midi_path),
        "audit_path": str(audit_path),
        "trace_path": str(trace_path),
        "audit_summary": audit.summary,
        "warnings": list(audit.warnings),
        "rescue_events": rescue_events,
        "rescue_actions": rescue_actions,
    }


def _build_summary(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        audit = dict(output.get("audit_summary") or {})
        output_id = str(output["id"])
        events = int(audit.get("events") or 0)
        failed_guard = int(audit.get("failed_register_guard_count") or 0)
        methods = dict(audit.get("disposition_projection_methods") or {})
        families = dict(audit.get("disposition_projection_families") or {})
        rescue_events = int(output.get("rescue_events") or 0)
        checks.append(_check(output_id, "has_piano_events", events > 0, {"events": events}))
        checks.append(_check(output_id, "no_failed_register_guard", failed_guard == 0, {"failed_register_guard_count": failed_guard}))
        if "open_drop2_method_lock" in output_id:
            checks.append(_check(output_id, "drop2_lock_method_only", set(methods) == {"drop2"}, {"methods": methods}))
            checks.append(_check(output_id, "drop2_lock_family_only", set(families) == {"open"}, {"families": families}))
            checks.append(_check(output_id, "drop2_lock_no_rescue", rescue_events == 0, {"rescue_events": rescue_events}))
        if "rescue_closed" in output_id:
            checks.append(_check(output_id, "rescue_runtime_executed", rescue_events == events and events > 0, {"rescue_events": rescue_events, "events": events}))
            checks.append(_check(output_id, "rescue_to_closed_family", set(families) == {"closed"}, {"families": families}))
            checks.append(_check(output_id, "rescue_to_compact_method", set(methods) == {"compact"}, {"methods": methods}))
    return {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_15 — Method Lock Rescue Runtime Pilot / Explicit Fallback Execution Pass",
        "score": str(SCORE_PATH),
        "outputs": outputs,
        "acceptance": {
            "passed": all(check["passed"] for check in checks),
            "check_count": len(checks),
            "failed_checks": [check for check in checks if not check["passed"]],
            "checks": checks,
        },
    }


def _check(output_id: str, name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"output_id": output_id, "name": name, "passed": bool(passed), "details": details}


def _format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Method Lock Rescue Runtime Demo Summary",
        "",
        f"- Contract version: `{summary['contract_version']}`",
        f"- Milestone: `{summary['milestone']}`",
        f"- Acceptance passed: `{summary['acceptance']['passed']}`",
        f"- Check count: `{summary['acceptance']['check_count']}`",
        "",
        "## Demo Outputs",
        "",
        "| Demo | Style | MIDI | Events | Families | Methods | Rescue Events | Rescue Actions | Warnings |",
        "|---|---|---|---:|---|---|---:|---|---:|",
    ]
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{id}` | `{style}` | `{midi}` | {events} | `{families}` | `{methods}` | {rescue_events} | `{actions}` | {warnings} |".format(
                id=output["id"],
                style=output["style"],
                midi=Path(output["midi_path"]).name,
                events=audit.get("events"),
                families=audit.get("disposition_projection_families"),
                methods=audit.get("disposition_projection_methods"),
                rescue_events=output.get("rescue_events"),
                actions=output.get("rescue_actions"),
                warnings=len(output.get("warnings") or []),
            )
        )
    lines.extend([
        "",
        "## Acceptance Checks",
        "",
        "| Demo | Check | Passed | Details |",
        "|---|---|---|---|",
    ])
    for check in summary["acceptance"]["checks"]:
        lines.append(f"| `{check['output_id']}` | `{check['name']}` | `{check['passed']}` | `{json.dumps(check['details'], ensure_ascii=False)}` |")
    lines.extend([
        "",
        "## Reading Notes",
        "",
        "- The DROP2 method-lock demo confirms strict OPEN/DROP2 filtering without rescue.",
        "- The rescue demos intentionally request an unavailable SPREAD lock from an OPEN-only voicing override, then execute the explicit runtime fallback to CLOSED/COMPACT.",
        "- These demos are verification artifacts only; default style output is unchanged.",
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
