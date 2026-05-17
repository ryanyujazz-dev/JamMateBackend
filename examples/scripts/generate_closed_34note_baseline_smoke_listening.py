from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG

ROOT = PROJECT_ROOT
DEMOS_DIR = ROOT / "demos"
SCRIPT_DIR = Path(__file__).resolve().parent

SMOKE_INPUT_SCRIPTS: tuple[str, ...] = (
    "generate_3note_closed_listening_verification_demos.py",
    "generate_4note_source_weight_listening_verification_demos.py",
    "generate_4note_triad_closed_listening_verification_demos.py",
)

SUMMARY_FILES: tuple[tuple[str, str], ...] = (
    ("3note_closed", f"{ENGINE_VERSION_TAG}_3note_closed_listening_verification_summary.json"),
    ("4note_color_source", f"{ENGINE_VERSION_TAG}_4note_source_weight_listening_verification_summary.json"),
    ("4note_triad_source", f"{ENGINE_VERSION_TAG}_4note_triad_closed_listening_verification_summary.json"),
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    for script_name in SMOKE_INPUT_SCRIPTS:
        runpy.run_path(str(SCRIPT_DIR / script_name), run_name="__main__")

    sections = [_load_summary(section_id, filename) for section_id, filename in SUMMARY_FILES]
    acceptance = _build_acceptance(sections)
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_1_45 — Closed 3/4-Note Baseline Smoke Listening / Pre-Disposition Planning Pass",
        "scope": "closed 3-note and 4-note baseline smoke acceptance before open/drop2/spread planning",
        "excluded_scope": ["open", "drop2", "spread", "5-note", "6-note", "7-note+", "upper-structure", "quartal"],
        "input_scripts": list(SMOKE_INPUT_SCRIPTS),
        "sections": sections,
        "acceptance": acceptance,
    }
    out_json = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_closed_34note_baseline_smoke_summary.json"
    out_md = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_closed_34note_baseline_smoke_summary.md"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(_format_summary(summary), encoding="utf-8")
    print({"ok": acceptance["passed"], "summary_path": str(out_md), "summary_json_path": str(out_json)})
    if not acceptance["passed"]:
        raise SystemExit(1)


def _load_summary(section_id: str, filename: str) -> dict[str, Any]:
    path = DEMOS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"missing generated smoke input summary: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "section_id": section_id,
        "summary_path": str(path),
        "summary": data,
    }


def _build_acceptance(sections: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in sections:
        section_id = section["section_id"]
        summary = section["summary"]
        expected_density = 3 if section_id == "3note_closed" else 4
        for output in summary.get("outputs", []):
            audit = dict(output.get("audit_summary") or {})
            checks.extend(_checks_for_output(section_id, output, audit, expected_density))
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "passed": passed,
        "check_count": len(checks),
        "failed_checks": [check for check in checks if not check["passed"]],
        "checks": checks,
    }


def _checks_for_output(section_id: str, output: dict[str, Any], audit: dict[str, Any], expected_density: int) -> list[dict[str, Any]]:
    demo_id = str(output.get("id"))
    warnings = list(output.get("warnings") or [])
    densities = dict(audit.get("densities") or {})
    dispositions = dict(audit.get("dispositions") or {})
    min_low = audit.get("min_closed_voicing_lowest_note")
    max_span = audit.get("max_closed_voicing_span")
    missing = int(audit.get("missing_note_events") or 0)
    failed_guard = int(audit.get("failed_register_guard_count") or 0)
    density_ok = set(str(k) for k in densities.keys()) == {str(expected_density)}
    disposition_ok = set(str(k) for k in dispositions.keys()) == {"closed"}
    low_ok = min_low is not None and int(min_low) >= 53
    span_ok = max_span is not None and int(max_span) <= 12
    return [
        _check(section_id, demo_id, "expected_density", density_ok, {"densities": densities, "expected": expected_density}),
        _check(section_id, demo_id, "closed_disposition_only", disposition_ok, {"dispositions": dispositions}),
        _check(section_id, demo_id, "closed_floor_f3_or_higher", low_ok, {"min_low": min_low}),
        _check(section_id, demo_id, "closed_span_12_or_lower", span_ok, {"max_span": max_span}),
        _check(section_id, demo_id, "no_missing_note_events", missing == 0, {"missing_note_events": missing}),
        _check(section_id, demo_id, "no_failed_register_guard", failed_guard == 0, {"failed_register_guard_count": failed_guard}),
        _check(section_id, demo_id, "no_piano_audit_warnings", not warnings, {"warnings": warnings}),
    ]


def _check(section_id: str, demo_id: str, name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"section_id": section_id, "demo_id": demo_id, "name": name, "passed": bool(passed), "details": details}


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Closed 3/4-Note Baseline Smoke Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Excluded scope: `{', '.join(summary['excluded_scope'])}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append(f"- Check count: `{summary['acceptance']['check_count']}`")
    lines.append("")
    lines.append("## Input Sections")
    lines.append("")
    lines.append("| Section | Summary | Demo count | Scope |")
    lines.append("|---|---|---:|---|")
    for section in summary["sections"]:
        inner = section["summary"]
        lines.append(
            "| `{section}` | `{summary_path}` | {demo_count} | {scope} |".format(
                section=section["section_id"],
                summary_path=Path(section["summary_path"]).name,
                demo_count=inner.get("demo_count"),
                scope=inner.get("scope"),
            )
        )
    lines.append("")
    lines.append("## Acceptance Checks")
    lines.append("")
    lines.append("| Section | Demo | Check | Passed | Details |")
    lines.append("|---|---|---|---|---|")
    for check in summary["acceptance"]["checks"]:
        lines.append(
            "| `{section}` | `{demo}` | `{name}` | `{passed}` | `{details}` |".format(
                section=check["section_id"],
                demo=check["demo_id"],
                name=check["name"],
                passed=check["passed"],
                details=json.dumps(check["details"], ensure_ascii=False),
            )
        )
    lines.append("")
    lines.append("## Listening / Planning Decision")
    lines.append("")
    lines.append("- Closed 3-note baseline remains accepted when every focused demo is density=3, disposition=closed, F3/MIDI 53 floor or higher, and span<=12.")
    lines.append("- Closed 4-note color-source baseline remains accepted when the color-rich demos stay density=4/closed with no warnings.")
    lines.append("- Closed 4-note triad-aware baseline remains accepted when doubled triad/sus/add/six sources stay density=4/closed with no partial fallback.")
    lines.append("- This smoke pass only confirms the closed baseline. Open/drop2/spread planning must be implemented as a separate disposition layer after this point.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
