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

THREE_NOTE_CLOSED_ISOLATION_OVERRIDE: dict[str, Any] = {
    "enabled": True,
    "preset": "shell_plus_specified_color",
    "allowed_content": ["shell_plus_color", "shell_plus_5"],
    "preferred_content": "shell_plus_color",
    "preferred_density": 3,
    "min_density": 3,
    "max_density": 3,
    "preferred_disposition": "closed",
    "allowed_dispositions": ["closed"],
    "max_voicing_span": 16,
    "register_low": 51,
    "right_hand_low": 51,
    "top_voice_low": 56,
    "comfort_register_low": 53,
    "metadata": {
        "normal_style_default": False,
        "listening_verification_target": "3_note_strict_closed_functional_source",
        "excluded_scope": "open/drop2/spread/4-note/5-note/6-note",
        "strict_closed_compact_pitch_class_layout": True,
        "strict_closed_max_span": 12,
        "closed_voicing_lowest_note_floor": 53,
        "closed_voicing_register_rule": "closed-only 3-note isolation uses F3/MIDI 53 floor; open/spread/drop2 are not affected",
        "closed_3note_per_source_minimum_motion": True,
        "closed_3note_closed_legality_then_nearest_motion": True,
        "closed_3note_per_source_minimum_motion_rule": "for each semantic 3-note closed source, generate legal closed variants first, then keep the top-1 nearest realization before source-level selection",
        "triad_aware_source_rule": "non-seventh symbols use root-third-fifth/root-third-ninth/root-third-sixth/root-second-fifth/root-fourth-fifth sources, not two-note partial fallback",
    },
}

DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "medium_swing_all_the_things_you_are",
        "style": "medium_swing",
        "score": "all_the_things_you_are.json",
        "tempo": None,
        "choruses": 1,
        "seed": 401,
        "note": "Real-standard smoke check under forced 3-note closed source isolation.",
    },
    {
        "id": "medium_swing_three_note_closed_source_stress",
        "style": "medium_swing",
        "score": "three_note_closed_source_stress.json",
        "tempo": 132,
        "choruses": 3,
        "seed": 402,
        "note": "Triad/add/sus plus seventh-shell stress chart for 3-note closed source coverage.",
    },
    {
        "id": "bossa_three_note_closed_source_stress",
        "style": "bossa_nova",
        "score": "three_note_closed_source_stress.json",
        "tempo": 128,
        "choruses": 3,
        "seed": 403,
        "note": "Bossa rhythm/expression with forced 3-note closed voicing source isolation.",
    },
    {
        "id": "ballad_three_note_closed_source_stress",
        "style": "jazz_ballad",
        "score": "three_note_closed_source_stress.json",
        "tempo": 76,
        "choruses": 3,
        "seed": 404,
        "note": "Ballad rhythm/expression with forced 3-note closed voicing source isolation.",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_demo(spec) for spec in DEMO_SPECS]
    summary = _build_summary(outputs)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_3note_closed_listening_verification_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_3note_closed_listening_verification_summary.json"
    summary_path.write_text(_format_summary(summary), encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": True, "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "outputs": outputs})


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = ROOT / "examples" / "leadsheets" / str(spec["score"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    tempo = int(spec["tempo"] or score.get("tempo", 120))
    stem = f"{ENGINE_VERSION_TAG}_{spec['id']}_3note_closed_listening"
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
            "voicing_override": dict(THREE_NOTE_CLOSED_ISOLATION_OVERRIDE),
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
    return {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_1_40 — 3-Note Closed Listening Verification Pass",
        "scope": "3-note strict closed functional-source listening verification only",
        "excluded_scope": ["open", "drop2", "spread", "4-note", "5-note", "6-note", "7-note+", "upper-structure", "quartal"],
        "voicing_override": dict(THREE_NOTE_CLOSED_ISOLATION_OVERRIDE),
        "demo_count": len(outputs),
        "outputs": outputs,
    }


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 3-Note Closed Listening Verification Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Excluded scope: `{', '.join(summary['excluded_scope'])}`")
    lines.append(f"- Demo count: `{summary['demo_count']}`")
    lines.append("")
    lines.append("## Demo Outputs")
    lines.append("")
    lines.append("| Demo | Style | Tempo | Choruses | MIDI | Piano audit | 3-note sources | Densities | Dispositions | Min low | Max span | Warnings |")
    lines.append("|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|")
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{id}` | `{style}` | {tempo} | {choruses} | `{midi}` | `{audit_path}` | `{sources}` | `{densities}` | `{dispositions}` | {low} | {span} | {warnings} |".format(
                id=output["id"],
                style=output["style"],
                tempo=output["tempo"],
                choruses=output["choruses"],
                midi=Path(output["midi_path"]).name,
                audit_path=Path(output["audit_path"]).name,
                sources=audit.get("three_note_source_types", {}),
                densities=audit.get("densities", {}),
                dispositions=audit.get("dispositions", {}),
                low=audit.get("min_closed_voicing_lowest_note"),
                span=audit.get("max_closed_voicing_span"),
                warnings=len(output.get("warnings") or []),
            )
        )
    lines.append("")
    lines.append("## Listening Checklist")
    lines.append("")
    lines.append("- `C/Cm` should sound like real 3-note triads, not two-note partial shell fallbacks.")
    lines.append("- `Cadd9/Cmadd9/C6/Csus4` should expose add/sus/sixth material through rooted 3-note functional sources.")
    lines.append("- Seventh chords should use guide-tone shell families such as `third-seventh-fifth`, `third-seventh-ninth`, and `third-seventh-altered-color`.")
    lines.append("- All piano voicings in these demos should remain density 3 and disposition closed.")
    lines.append("- Per-source nearest motion should reduce jumps without reintroducing open/drop2/spread behavior.")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- Every demo keeps style rhythm, expression, anticipation, timing, bass, and drums native.")
    lines.append("- The runtime override only freezes piano voicing to 3-note closed-position functional source selection.")
    lines.append("- The per-demo piano trace includes selected 3-note source type, role order, degree order, collapse distance, region reuse, register guard, and realized MIDI notes.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
