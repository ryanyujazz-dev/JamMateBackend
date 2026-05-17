from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit, format_piano_musical_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"

SPECS: tuple[dict[str, Any], ...] = (
    {"slug": "all_the_things_you_are", "leadsheet": "all_the_things_you_are.json", "seed": 3300},
    {"slug": "autumn_leaves", "leadsheet": "autumn_leaves.json", "seed": 3301},
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_and_audit(spec) for spec in SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_38 — Medium Swing Generic Open Fallback-Only",
        "scope": "Audit actual Medium Swing OPEN-method selections by texture contrast role across three-chorus standard-tune demos.",
        "outputs": outputs,
        "acceptance": _acceptance(outputs),
    }
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_medium_swing_texture_method_audit_summary.json"
    report_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_medium_swing_texture_method_audit_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(_format_report(summary), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "report_path": str(report_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_and_audit(spec: Mapping[str, Any]) -> dict[str, Any]:
    score_path = LEADSHEET_DIR / str(spec["leadsheet"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    midi_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_{slug}_medium_swing_demo.mid"
    audit_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_{slug}_medium_swing_texture_piano_audit.md"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            "tempo": int(score.get("tempo", 132)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_path.write_text(format_piano_musical_audit_report(result.debug, max_events=80), encoding="utf-8")
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "slug": slug,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "audit_path": str(audit_path.relative_to(PROJECT_ROOT)),
        "events": audit.summary.get("events"),
        "methods": audit.summary.get("disposition_projection_methods"),
        "families": audit.summary.get("disposition_projection_families"),
        "contrast_roles": audit.summary.get("voicing_texture_contrast_roles"),
        "methods_by_contrast_role": audit.summary.get("voicing_texture_methods_by_contrast_role"),
        "method_percentages_by_contrast_role": audit.summary.get("voicing_texture_method_percentages_by_contrast_role"),
        "open_method_weight_plans_by_contrast_role": audit.summary.get("voicing_texture_open_method_weight_plans_by_contrast_role"),
        "failed_register_guard_count": audit.summary.get("failed_register_guard_count"),
        "missing_note_events": audit.summary.get("missing_note_events"),
    }


def _acceptance(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for item in outputs:
        slug = str(item.get("slug"))
        methods = dict(item.get("methods") or {})
        families = dict(item.get("families") or {})
        roles = dict(item.get("contrast_roles") or {})
        percentages = dict(item.get("method_percentages_by_contrast_role") or {})
        baseline = dict(percentages.get("baseline_open_swing") or {})
        bridge = dict(percentages.get("bridge_open_contrast") or {})
        final = dict(percentages.get("final_chorus_open_lift") or {})
        checks.extend(
            [
                _check(f"{slug}: generated", bool(item.get("ok")), {"ok": item.get("ok")}),
                _check(f"{slug}: enough three-chorus piano events", int(item.get("events") or 0) >= 100, {"events": item.get("events")}),
                _check(f"{slug}: open family only", set(families.keys()) == {"open"}, {"families": families}),
                _check(
                    f"{slug}: all texture contrast roles present",
                    all(roles.get(role, 0) > 0 for role in ("baseline_open_swing", "bridge_open_contrast", "final_chorus_open_lift")),
                    {"roles": roles},
                ),
                _check(f"{slug}: multiple open methods realized", len(methods) >= 3, {"methods": methods}),
                _check(
                    f"{slug}: bridge increases drop3 share over baseline",
                    _ratio(bridge, "drop3") > _ratio(baseline, "drop3"),
                    {"baseline_drop3": _ratio(baseline, "drop3"), "bridge_drop3": _ratio(bridge, "drop3")},
                ),
                _check(
                    f"{slug}: final chorus increases drop3 share over baseline after generic-open removal",
                    _ratio(final, "drop3") > _ratio(baseline, "drop3"),
                    {"baseline_drop3": _ratio(baseline, "drop3"), "final_drop3": _ratio(final, "drop3")},
                ),
                _check(
                    f"{slug}: drop2_and_4 remains controlled",
                    _ratio_sum(_total_percentages(methods), ("drop2_and_4",)) <= 0.20,
                    {"methods": methods, "drop2_and_4_total_ratio": _ratio_sum(_total_percentages(methods), ("drop2_and_4",))},
                ),
                _check(f"{slug}: no failed register guards", int(item.get("failed_register_guard_count") or 0) == 0, {"failed": item.get("failed_register_guard_count")}),
                _check(f"{slug}: no missing piano note events", int(item.get("missing_note_events") or 0) == 0, {"missing": item.get("missing_note_events")}),
            ]
        )
    return {"passed": all(check["passed"] for check in checks), "check_count": len(checks), "failed_checks": [check for check in checks if not check["passed"]], "checks": checks}


def _ratio(mapping: Mapping[str, Any], key: str) -> float:
    try:
        return float(mapping.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ratio_sum(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> float:
    return sum(_ratio(mapping, key) for key in keys)


def _total_percentages(methods: Mapping[str, Any]) -> dict[str, float]:
    total = sum(int(value or 0) for value in methods.values()) or 1
    return {str(key): float(value or 0) / float(total) for key, value in methods.items()}


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _format_report(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Medium Swing Generic Open Fallback-Only Audit")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append("")
    for item in summary["outputs"]:
        lines.append(f"## {item['title']}")
        lines.append("")
        lines.append(f"- MIDI: `{item['midi_path']}`")
        lines.append(f"- Events: `{item['events']}`")
        lines.append(f"- Families: `{item['families']}`")
        lines.append(f"- Methods: `{item['methods']}`")
        lines.append(f"- Contrast roles: `{item['contrast_roles']}`")
        lines.append(f"- Methods by contrast role: `{item['methods_by_contrast_role']}`")
        lines.append(f"- Percentages by contrast role: `{item['method_percentages_by_contrast_role']}`")
        lines.append(f"- OPEN method weight plans: `{item['open_method_weight_plans_by_contrast_role']}`")
        lines.append("")
    lines.append("## Acceptance checks")
    lines.append("")
    for check in summary["acceptance"]["checks"]:
        lines.append(f"- `{check['name']}`: `{check['passed']}` — `{check['details']}`")
    lines.append("")
    lines.append("## Reading note")
    lines.append("")
    lines.append("This is an observational audit: it verifies actual selected projection methods from runtime debug, not just policy metadata. Medium Swing still stays in OPEN family; generic_open has zero normal runtime weight and remains available only for explicit rescue/fallback; MethodLock and nearest-motion rescue remain responsible for local continuity.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
