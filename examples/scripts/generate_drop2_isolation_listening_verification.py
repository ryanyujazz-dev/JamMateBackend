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

DROP2_ISOLATION_OVERRIDE: dict[str, Any] = {
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
    "register_high": 76,
    "right_hand_low": 50,
    "top_voice_low": 55,
    "comfort_register_low": 52,
    "max_voicing_span": 24,
    "metadata": {
        "normal_style_default": False,
        "listening_verification_target": "open_drop2_parent_closed_isolation",
        "excluded_scope": "style defaults/drop3/drop2_and_4/generic_open/spread/5-note/6-note",
        "open_projection_method": "drop2",
        "open_method_contract": "OPEN family isolation explicitly requests OpenProjectionMethod.DROP2; default OPEN remains GENERIC_OPEN until style method weights are planned.",
        "drop2_parent_closed_contract": "DROP2 must derive from the active 4-note closed parent voicing, including source rotations and doubled-triad rotations, not from direct source-order stack generation.",
        "strict_closed_compact_pitch_class_layout": True,
        "closed_voicing_lowest_note_floor": 53,
        "strict_closed_max_span": 12,
    },
}

DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "medium_swing_minimal_ii_v_i_drop2_isolation",
        "style": "medium_swing",
        "score": "minimal_ii_v_i.json",
        "tempo": 120,
        "choruses": 3,
        "seed": 6261,
        "note": "Medium Swing OPEN/DROP2 isolation over a compact ii-V-I stress form.",
    },
    {
        "id": "bossa_minimal_ii_v_i_drop2_isolation",
        "style": "bossa_nova",
        "score": "minimal_ii_v_i.json",
        "tempo": 128,
        "choruses": 3,
        "seed": 6262,
        "note": "Bossa OPEN/DROP2 isolation; rhythm stays Bossa while only vertical disposition is forced to DROP2.",
    },
    {
        "id": "ballad_minimal_ii_v_i_drop2_isolation",
        "style": "jazz_ballad",
        "score": "minimal_ii_v_i.json",
        "tempo": 76,
        "choruses": 3,
        "seed": 6263,
        "note": "Jazz Ballad OPEN/DROP2 isolation; useful for checking warmth/register before style weights are enabled.",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_demo(spec) for spec in DEMO_SPECS]
    summary = _build_summary(outputs)
    summary_md = _format_summary(summary)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_drop2_isolation_listening_verification_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_drop2_isolation_listening_verification_summary.json"
    summary_path.write_text(summary_md, encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = ROOT / "examples" / "leadsheets" / str(spec["score"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    tempo = int(spec["tempo"] or score.get("tempo", 120))
    stem = f"{ENGINE_VERSION_TAG}_{spec['id']}"
    midi_path = DEMOS_DIR / f"{stem}.mid"
    audit_path = DEMOS_DIR / f"{stem}_piano_audit.md"
    trace_path = DEMOS_DIR / f"{stem}_piano_trace.json"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": str(spec["style"]),
            "tempo": tempo,
            "choruses": int(spec["choruses"]),
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
            "voicing_override": dict(DROP2_ISOLATION_OVERRIDE),
        }
    )
    audit = build_piano_musical_audit(result.debug)
    audit_path.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    trace_path.write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "id": spec["id"],
        "style": spec["style"],
        "score_path": str(score_path),
        "midi_path": str(midi_path),
        "audit_path": str(audit_path),
        "trace_path": str(trace_path),
        "tempo": tempo,
        "choruses": int(spec["choruses"]),
        "seed": int(spec["seed"]),
        "note": spec.get("note", ""),
        "audit_summary": audit.summary,
        "warnings": list(audit.warnings),
    }


def _build_summary(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for output in outputs:
        audit = dict(output.get("audit_summary") or {})
        checks.extend(_checks_for_output(output, audit))
    return {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_6 — DROP2 Isolation Listening / Guard Pass",
        "scope": "OPEN family / OpenProjectionMethod.DROP2 isolation only; style defaults are not changed.",
        "excluded_scope": ["drop3", "drop2_and_4", "generic_open retune", "spread", "style default disposition weighting", "5-note", "6-note", "7-note"],
        "override_contract": DROP2_ISOLATION_OVERRIDE,
        "outputs": outputs,
        "acceptance": {
            "passed": all(check["passed"] for check in checks),
            "check_count": len(checks),
            "failed_checks": [check for check in checks if not check["passed"]],
            "checks": checks,
        },
        "future_policy_notes": {
            "open_method_candidate_pool": ["drop2", "drop3", "drop2_and_4", "generic_open"],
            "method_selection_rule": "Future style policy should allow multiple OPEN methods to enter the same candidate pool; v2_2_6 only isolates DROP2 for guard/listening.",
            "progression_method_lock_rule": "For ii-V, V-I, ii-V-I, turnaround, or arrangement-defined phrase scopes, the first selected voicing family/method should be locked or heavily biased through the scope unless gesture/arrangement intent explicitly breaks it.",
        },
    }


def _checks_for_output(output: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    output_id = str(output.get("id"))
    events = int(audit.get("events") or 0)
    projection_methods = dict(audit.get("disposition_projection_methods") or {})
    projection_families = dict(audit.get("disposition_projection_families") or {})
    densities = dict(audit.get("densities") or {})
    dispositions = dict(audit.get("dispositions") or {})
    drop2_events = int(audit.get("open_drop2_events") or 0)
    max_span = audit.get("max_open_drop2_span")
    min_low = audit.get("min_open_drop2_lowest_note")
    missing = int(audit.get("missing_note_events") or 0)
    failed_guard = int(audit.get("failed_register_guard_count") or 0)
    callback_count = int(audit.get("legacy_projection_callback_used_count") or 0)
    return [
        _check(output_id, "has_piano_events", events > 0, {"events": events}),
        _check(output_id, "open_family_only", set(projection_families.keys()) == {"open"}, {"families": projection_families}),
        _check(output_id, "drop2_method_only", set(projection_methods.keys()) == {"drop2"}, {"methods": projection_methods}),
        _check(output_id, "every_event_is_drop2", drop2_events == events and events > 0, {"drop2_events": drop2_events, "events": events}),
        _check(output_id, "density_4_only", set(str(k) for k in densities.keys()) == {"4"}, {"densities": densities}),
        _check(output_id, "legacy_disposition_open_only", set(dispositions.keys()) == {"open"}, {"dispositions": dispositions}),
        _check(output_id, "no_missing_note_events", missing == 0, {"missing_note_events": missing}),
        _check(output_id, "no_failed_register_guard", failed_guard == 0, {"failed_register_guard_count": failed_guard}),
        _check(output_id, "drop2_span_guard", max_span is not None and int(max_span) <= 24, {"max_open_drop2_span": max_span}),
        _check(output_id, "drop2_low_register_guard", min_low is not None and int(min_low) >= 46, {"min_open_drop2_lowest_note": min_low}),
        _check(output_id, "drop2_migrated_projection_path", callback_count == 0, {"legacy_projection_callback_used_count": callback_count}),
    ]


def _check(output_id: str, name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"output_id": output_id, "name": name, "passed": bool(passed), "details": details}


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# DROP2 Isolation Listening / Guard Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Excluded scope: `{', '.join(summary['excluded_scope'])}`")
    lines.append(f"- Acceptance passed: `{summary['acceptance']['passed']}`")
    lines.append(f"- Check count: `{summary['acceptance']['check_count']}`")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append("| Demo | Style | MIDI | Events | Methods | DROP2 Events | Span | Lowest | Warnings |")
    lines.append("|---|---|---|---:|---|---:|---|---|---|")
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{demo}` | `{style}` | `{midi}` | {events} | `{methods}` | {drop2_events} | `{avg_span}/{max_span}` | `{min_low}` | `{warnings}` |".format(
                demo=output["id"],
                style=output["style"],
                midi=Path(output["midi_path"]).name,
                events=audit.get("events"),
                methods=audit.get("disposition_projection_methods"),
                drop2_events=audit.get("open_drop2_events"),
                avg_span=audit.get("avg_open_drop2_span"),
                max_span=audit.get("max_open_drop2_span"),
                min_low=audit.get("min_open_drop2_lowest_note"),
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
    for key, value in summary["future_policy_notes"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- This pass isolates DROP2 through `metadata={\"open_projection_method\": \"drop2\"}`. It does not change normal style defaults.")
    lines.append("- DROP2 remains an `OPEN` family method. Future `DROP3`, `DROP2_AND_4`, and `GENERIC_OPEN` should join the same OPEN method candidate pool, not become separate disposition systems.")
    lines.append("- Future ii-V / V-I / ii-V-I / phrase-level method lock should preserve the first chosen family/method across the progression scope unless a higher-level gesture or arrangement intent breaks it.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
