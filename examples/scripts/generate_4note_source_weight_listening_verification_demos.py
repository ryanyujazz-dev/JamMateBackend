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

FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE: dict[str, Any] = {
    "enabled": True,
    # Keep style rhythm/expression/timing native; isolate only the vertical
    # source layer so v2_1_37 listens to 4-note closed source balance rather
    # than open/spread/density side effects.
    "allowed_content": ["seventh_chord_basic", "rooted_color", "rootless_A", "rootless_B"],
    "preferred_density": 4,
    "min_density": 4,
    "max_density": 4,
    "preferred_disposition": "closed",
    "allowed_dispositions": ["closed"],
    "max_voicing_span": 16,
    "register_low": 46,
    "right_hand_low": 50,
    "top_voice_low": 55,
    "comfort_register_low": 52,
    "metadata": {
        "normal_style_default": False,
        "listening_verification_target": "4_note_strict_closed_position_source_weight",
        "excluded_scope": "drop2/open/spread/5-note/6-note",
        "closed_voicing_lowest_note_floor": 53,
        "closed_voicing_register_rule": "closed-only lowest note floor lowered by a minor third from C4/MIDI 60 to F3/MIDI 53 after v2_1_36; open/spread/drop2 are not affected",
        "strict_closed_compact_pitch_class_layout": True,
        "strict_closed_compactness_rule": "closed means practical closed pitch-class span, with per-source nearest-position selection deciding the concrete inversion/register",
        "strict_closed_max_span": 12,
        "closed_4note_per_source_minimum_motion": True,
        "closed_4note_per_source_minimum_motion_rule": "for each semantic 4-note closed source, generate closed inversions/register variants and keep the top-1 nearest realization before source-level selection",
    },
}

DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "medium_swing_all_the_things_you_are",
        "style": "medium_swing",
        "score": "all_the_things_you_are.json",
        "tempo": None,
        "choruses": 1,
        "seed": 341,
        "note": "Real-standard smoke check; score form already repeats three times.",
    },
    {
        "id": "medium_swing_color_rich_251_stress",
        "style": "medium_swing",
        "score": "color_rich_251_stress.json",
        "tempo": 132,
        "choruses": 3,
        "seed": 342,
        "note": "Compact swing 251 stress chart with explicit 9/11/13/#11/alt color.",
    },
    {
        "id": "bossa_color_rich_progression",
        "style": "bossa_nova",
        "score": "color_rich_bossa_progression.json",
        "tempo": 128,
        "choruses": 3,
        "seed": 343,
        "note": "Bossa source-weight check: light syncopated comping over explicit colors.",
    },
    {
        "id": "ballad_color_rich_warm_voicing",
        "style": "jazz_ballad",
        "score": "color_rich_ballad_voicing_progression.json",
        "tempo": 76,
        "choruses": 3,
        "seed": 344,
        "note": "Ballad source-weight check under forced 4-note closed isolation, not 5/6-note spread tuning.",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs: list[dict[str, Any]] = []
    for spec in DEMO_SPECS:
        outputs.append(_generate_demo(spec))
    summary = _build_summary(outputs)
    summary_md = _format_summary(summary)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_source_weight_listening_verification_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_source_weight_listening_verification_summary.json"
    summary_path.write_text(summary_md, encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": True, "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "outputs": outputs})


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = ROOT / "examples" / "leadsheets" / str(spec["score"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    tempo = int(spec["tempo"] or score.get("tempo", 120))
    stem = f"{ENGINE_VERSION_TAG}_{spec['id']}_4note_source_weight_listening"
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
            "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
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
        "milestone": "v2_1_37 — Closed 4-Note Minimum-Motion Voicing Pass",
        "scope": "4-note closed-position source weight listening verification only",
        "excluded_scope": ["drop2", "open", "spread", "5-note", "6-note", "7-note+", "upper-structure", "quartal"],
        "voicing_override": dict(FOUR_NOTE_CLOSED_ISOLATION_OVERRIDE),
        "demo_count": len(outputs),
        "outputs": outputs,
    }


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 4-Note Source Weight Listening Verification Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Excluded scope: `{', '.join(summary['excluded_scope'])}`")
    lines.append(f"- Demo count: `{summary['demo_count']}`")
    lines.append("")
    lines.append("## Demo Outputs")
    lines.append("")
    lines.append("| Demo | Style | Tempo | Choruses | MIDI | Piano audit | Source gates | Source keys | Warnings |")
    lines.append("|---|---|---:|---:|---|---|---|---|---:|")
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{id}` | `{style}` | {tempo} | {choruses} | `{midi}` | `{audit_path}` | `{gates}` | `{keys}` | {warnings} |".format(
                id=output["id"],
                style=output["style"],
                tempo=output["tempo"],
                choruses=output["choruses"],
                midi=Path(output["midi_path"]).name,
                audit_path=Path(output["audit_path"]).name,
                gates=audit.get("four_note_source_balance_gate_modes", {}),
                keys=audit.get("four_note_source_balance_keys", {}),
                warnings=len(output.get("warnings") or []),
            )
        )
    lines.append("")
    lines.append("## Listening Checklist")
    lines.append("")
    lines.append("- Plain seventh chords should not sound either too bare or artificially colored.")
    lines.append("- Written 9/11/13/#11/altered colors should be audible in the selected 4-note source when legal.")
    lines.append("- Medium Swing should keep enough jazz color without becoming constantly modern/rootless-heavy.")
    lines.append("- Bossa should remain light and clean; with_13/altered sources should not dominate the syncopated comping texture.")
    lines.append("- Ballad should sound warm in this forced 4-note isolation, while true 5/6-note spread ballad tuning remains explicitly out of scope.")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- Every demo keeps style rhythm, expression, anticipation, timing, bass, and drums native.")
    lines.append("- The runtime override only freezes piano voicing to 4-note closed-position source selection so source weights can be heard before open/spread/density tuning.")
    lines.append("- The per-demo piano trace includes selected source gate, source key, source-balance score, and chart-color-fidelity score for every piano event.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
