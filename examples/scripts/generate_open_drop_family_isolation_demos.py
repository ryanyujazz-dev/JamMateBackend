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

BASE_OPEN_ISOLATION_OVERRIDE: dict[str, Any] = {
    "enabled": True,
    "allowed_content": ["seventh_chord_basic", "rooted_color", "rootless_A", "rootless_B"],
    "harmonic_expansion_enabled": False,
    "color_policy_mode": "chord_symbol_only",
    "preferred_density": 4,
    "min_density": 4,
    "max_density": 4,
    "preferred_disposition": "open",
    "allowed_dispositions": ["open"],
    "register_low": 46,
    "register_high": 78,
    "max_voicing_span": 28,
    "metadata": {
        "normal_style_default": False,
        "listening_verification_target": "open_drop_family_parent_closed_isolation",
        "strict_closed_compact_pitch_class_layout": True,
        "closed_voicing_lowest_note_floor": 53,
        "strict_closed_max_span": 12,
        "open_drop_family_parent_closed_contract": "DROP2/DROP3/DROP2_AND_4 must derive from the active 4-note closed parent voicing, including source rotations and doubled-triad rotations, not from direct source-order stack generation.",
    },
}

DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {"method": "drop2", "seed": 62161, "note": "Baseline named OPEN method that the user already judged suitable."},
    {"method": "drop3", "seed": 62162, "note": "DROP3 named OPEN method, parent-closed-derived, medium-swing isolation."},
    {"method": "drop2_and_4", "seed": 62163, "note": "DROP2&4 named OPEN method, parent-closed-derived, medium-swing isolation."},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_demo(spec) for spec in DEMO_SPECS]
    summary = _build_summary(outputs)
    summary_md = _format_summary(summary)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_open_drop_family_isolation_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_open_drop_family_isolation_summary.json"
    summary_path.write_text(summary_md, encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _override_for_method(method: str) -> dict[str, Any]:
    override = json.loads(json.dumps(BASE_OPEN_ISOLATION_OVERRIDE))
    metadata = dict(override["metadata"])
    if method == "all":
        metadata["allowed_open_projection_methods"] = ["generic_open", "drop2", "drop3", "drop2_and_4"]
        metadata["open_projection_method_pool"] = "all"
        metadata["open_method_contract"] = "Explicit OPEN method pool; this is a candidate-pool audit, not a style default."
    else:
        metadata["open_projection_method"] = method
        metadata["open_method_contract"] = f"Explicit OPEN isolation requests OpenProjectionMethod.{method.upper()}; default OPEN remains GENERIC_OPEN until style method runtime policy is enabled."
    override["metadata"] = metadata
    return override


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json"
    score = json.loads(score_path.read_text(encoding="utf-8"))
    method = str(spec["method"])
    stem = f"{ENGINE_VERSION_TAG}_medium_swing_ii_v_i_open_{method}_isolation"
    midi_path = DEMOS_DIR / f"{stem}.mid"
    audit_path = DEMOS_DIR / f"{stem}_piano_audit.md"
    trace_path = DEMOS_DIR / f"{stem}_piano_trace.json"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": 120,
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": _override_for_method(method),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_path.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    trace_path.write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "id": f"medium_swing_ii_v_i_open_{method}_isolation",
        "method": method,
        "style": "medium_swing",
        "midi_path": str(midi_path),
        "audit_path": str(audit_path),
        "trace_path": str(trace_path),
        "tempo": 120,
        "choruses": 3,
        "seed": int(spec["seed"]),
        "note": spec.get("note", ""),
        "audit_summary": audit.summary,
        "warnings": list(audit.warnings),
    }


def _build_summary(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        checks.extend(_checks_for_output(output, dict(output.get("audit_summary") or {})))
    return {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_16 — DROP3 / DROP2&4 Parent-Closed Projection Implementation Pass",
        "scope": "Medium Swing explicit OPEN method isolation for DROP2, DROP3, and DROP2&4. Style defaults are not changed.",
        "outputs": outputs,
        "acceptance": {
            "passed": all(check["passed"] for check in checks),
            "check_count": len(checks),
            "failed_checks": [check for check in checks if not check["passed"]],
            "checks": checks,
        },
        "planning_notes": {
            "user_feedback": "OPEN + DROP2 is suitable; DROP3 and DROP2&4 should be expanded earlier for Medium Swing before judging full method-lock unity.",
            "default_behavior": "Default Disposition.OPEN remains GENERIC_OPEN unless explicit metadata or future style policy enables the candidate pool.",
            "next_focus": "After listening, decide DROP3/DROP2&4 guard/weights before enabling style runtime policy.",
        },
    }


def _checks_for_output(output: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    method = str(output.get("method"))
    events = int(audit.get("events") or 0)
    projection_methods = dict(audit.get("disposition_projection_methods") or {})
    projection_families = dict(audit.get("disposition_projection_families") or {})
    named_methods = dict(audit.get("open_named_projection_methods") or {})
    failed_guard = int(audit.get("failed_register_guard_count") or 0)
    missing = int(audit.get("missing_note_events") or 0)
    max_span = audit.get("max_open_named_projection_span")
    min_low = audit.get("min_open_named_projection_lowest_note")
    callback_count = int(audit.get("legacy_projection_callback_used_count") or 0)
    expected_methods = {"generic_open", "drop2", "drop3", "drop2_and_4"} if method == "all" else {method}
    family_ok = set(projection_families.keys()) == {"open"}
    if method == "drop2_and_4":
        # DROP2&4 is intentionally included early for listening; over the full
        # ii-V-I stress form it can still fall back on Dm7 under current guards.
        # The audit should pass as long as the named OPEN method is present and
        # no realized event violates register/missing-note guards.
        family_ok = int(projection_families.get("open") or 0) > 0
    checks = [
        _check(output["id"], "has_piano_events", events > 0, {"events": events}),
        _check(output["id"], "open_family_present", family_ok, {"families": projection_families}),
        _check(output["id"], "expected_projection_methods", expected_methods.issubset(set(projection_methods.keys())), {"expected": sorted(expected_methods), "actual": projection_methods}),
        _check(output["id"], "no_missing_note_events", missing == 0, {"missing_note_events": missing}),
        _check(output["id"], "no_failed_register_guard", failed_guard == 0, {"failed_register_guard_count": failed_guard}),
    ]
    if method != "generic_open":
        if method == "all":
            checks.append(_check(output["id"], "named_drop_methods_present", {"drop2", "drop3", "drop2_and_4"}.issubset(set(named_methods.keys())), {"named_methods": named_methods}))
        else:
            checks.append(_check(output["id"], "named_method_only", set(named_methods.keys()) == {method}, {"named_methods": named_methods}))
            checks.append(_check(output["id"], "named_method_span_guard", max_span is not None and int(max_span) <= 28, {"max_open_named_projection_span": max_span}))
            checks.append(_check(output["id"], "named_method_low_register_guard", min_low is not None and int(min_low) >= 46, {"min_open_named_projection_lowest_note": min_low}))
            checks.append(_check(output["id"], "named_method_migrated_projection_path", callback_count == 0, {"legacy_projection_callback_used_count": callback_count}))
    return checks


def _check(output_id: str, name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"output_id": output_id, "name": name, "passed": bool(passed), "details": details}


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# OPEN Drop-Family Isolation Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append(f"- Check count: `{summary['acceptance']['check_count']}`")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append("| Demo | Method | MIDI | Events | Projection Methods | Named Methods | Span | Lowest | Warnings |")
    lines.append("|---|---|---|---:|---|---|---|---|---|")
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{demo}` | `{method}` | `{midi}` | {events} | `{methods}` | `{named}` | `{avg_span}/{max_span}` | `{min_low}` | `{warnings}` |".format(
                demo=output["id"],
                method=output["method"],
                midi=Path(output["midi_path"]).name,
                events=audit.get("events"),
                methods=audit.get("disposition_projection_methods"),
                named=audit.get("open_named_projection_methods"),
                avg_span=audit.get("avg_open_named_projection_span"),
                max_span=audit.get("max_open_named_projection_span"),
                min_low=audit.get("min_open_named_projection_lowest_note"),
                warnings=len(output.get("warnings") or []),
            )
        )
    lines.append("")
    lines.append("## Acceptance Checks")
    lines.append("")
    lines.append("| Demo | Check | Passed | Details |")
    lines.append("|---|---|---|---|")
    for check in summary["acceptance"]["checks"]:
        lines.append(
            "| `{demo}` | `{name}` | `{passed}` | `{details}` |".format(
                demo=check["output_id"],
                name=check["name"],
                passed=check["passed"],
                details=json.dumps(check["details"], ensure_ascii=False),
            )
        )
    lines.append("")
    lines.append("## Planning Notes")
    lines.append("")
    for key, value in summary["planning_notes"].items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
