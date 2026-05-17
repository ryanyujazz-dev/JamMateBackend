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

FOUR_NOTE_TRIAD_CLOSED_ISOLATION_OVERRIDE: dict[str, Any] = {
    "enabled": True,
    # Keep style rhythm/expression/timing native; isolate only the 4-note closed
    # vertical source layer so plain triad/add/sus doubled rotations can be heard.
    "allowed_content": ["seventh_chord_basic", "rooted_color", "rootless_A", "rootless_B"],
    "harmonic_expansion_enabled": False,
    "color_policy_mode": "chord_symbol_only",
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
        "listening_verification_target": "4_note_triad_aware_closed_source",
        "excluded_scope": "open/drop2/spread/5-note/6-note",
        "closed_voicing_lowest_note_floor": 53,
        "closed_voicing_register_rule": "closed-only floor is F3/MIDI 53 for 3-note/4-note strict closed listening; open/spread/drop2 are not affected",
        "strict_closed_compact_pitch_class_layout": True,
        "strict_closed_compactness_rule": "first filter legal closed candidates, then choose the nearest realization within each semantic source",
        "strict_closed_max_span": 12,
        "closed_4note_per_source_minimum_motion": True,
        "closed_4note_per_source_minimum_motion_rule": "for each semantic 4-note closed source, generate closed inversions/register variants and keep the top-1 nearest realization before source-level selection",
        "closed_4note_triad_doubled_rotation_contract": "plain triads use 1351/3513/5135; sus2=1251/2512/5125; sus4=1451/4514/5145",
    },
}

DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "medium_swing_four_note_triad_closed_source_stress",
        "style": "medium_swing",
        "score": "four_note_triad_closed_source_stress.json",
        "tempo": 120,
        "choruses": 3,
        "seed": 421,
        "note": "Medium Swing check for 4-note closed doubled triad/sus/add/sixth source behavior.",
    },
    {
        "id": "bossa_four_note_triad_closed_source_stress",
        "style": "bossa_nova",
        "score": "four_note_triad_closed_source_stress.json",
        "tempo": 128,
        "choruses": 3,
        "seed": 422,
        "note": "Bossa check for light syncopated comping over 4-note closed triad-aware sources.",
    },
    {
        "id": "ballad_four_note_triad_closed_source_stress",
        "style": "jazz_ballad",
        "score": "four_note_triad_closed_source_stress.json",
        "tempo": 76,
        "choruses": 3,
        "seed": 423,
        "note": "Ballad check for warm but strictly closed 4-note triad-aware source behavior.",
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs: list[dict[str, Any]] = []
    for spec in DEMO_SPECS:
        outputs.append(_generate_demo(spec))
    summary = _build_summary(outputs)
    summary_md = _format_summary(summary)
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_triad_closed_listening_verification_summary.md"
    summary_json_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_4note_triad_closed_listening_verification_summary.json"
    summary_path.write_text(summary_md, encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": True, "summary_path": str(summary_path), "summary_json_path": str(summary_json_path), "outputs": outputs})


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = ROOT / "examples" / "leadsheets" / str(spec["score"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    tempo = int(spec["tempo"] or score.get("tempo", 120))
    stem = f"{ENGINE_VERSION_TAG}_{spec['id']}_4note_triad_closed_listening"
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
            "voicing_override": dict(FOUR_NOTE_TRIAD_CLOSED_ISOLATION_OVERRIDE),
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
        "milestone": "v2_1_42 — 4-Note Triad-Aware Closed Listening Verification Pass",
        "scope": "4-note closed triad/add/sus/doubled-rotation listening verification only",
        "excluded_scope": ["drop2", "open", "spread", "5-note", "6-note", "7-note+", "upper-structure", "quartal"],
        "voicing_override": dict(FOUR_NOTE_TRIAD_CLOSED_ISOLATION_OVERRIDE),
        "demo_count": len(outputs),
        "outputs": outputs,
    }


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 4-Note Triad-Aware Closed Listening Verification Summary")
    lines.append("")
    lines.append(f"- Contract version: `{summary['contract_version']}`")
    lines.append(f"- Milestone: `{summary['milestone']}`")
    lines.append(f"- Scope: `{summary['scope']}`")
    lines.append(f"- Excluded scope: `{', '.join(summary['excluded_scope'])}`")
    lines.append(f"- Demo count: `{summary['demo_count']}`")
    lines.append("")
    lines.append("## Demo Outputs")
    lines.append("")
    lines.append("| Demo | Style | Tempo | Choruses | MIDI | Piano audit | Density | Disposition | Triad 4-note source types | Min low | Max span | Warnings |")
    lines.append("|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|")
    for output in summary["outputs"]:
        audit = dict(output.get("audit_summary") or {})
        lines.append(
            "| `{id}` | `{style}` | {tempo} | {choruses} | `{midi}` | `{audit_path}` | `{densities}` | `{dispositions}` | `{triad_types}` | {min_low} | {max_span} | {warnings} |".format(
                id=output["id"],
                style=output["style"],
                tempo=output["tempo"],
                choruses=output["choruses"],
                midi=Path(output["midi_path"]).name,
                audit_path=Path(output["audit_path"]).name,
                densities=audit.get("densities", {}),
                dispositions=audit.get("dispositions", {}),
                triad_types=audit.get("triad_4note_source_types", {}),
                min_low=audit.get("min_closed_voicing_lowest_note"),
                max_span=audit.get("max_closed_voicing_span"),
                warnings=len(output.get("warnings") or []),
            )
        )
    lines.append("")
    lines.append("## Listening Checklist")
    lines.append("")
    lines.append("- Global harmonic expansion is disabled in this isolation pass so plain major/minor/sus triads should sound like closed doubled triads, not jazz rootless extensions.")
    lines.append("- Sus2 should realize the 1251/2512/5125 family; sus4 should realize 1451/4514/5145.")
    lines.append("- Add9/sixth/6-9 symbols should preserve their explicit source without fallback to partial two/three-note voicings.")
    lines.append("- All voicings should remain density=4, disposition=closed, floor>=F3/MIDI 53, span<=12 in this isolation pass.")
    lines.append("- Style rhythm/expression/timing/bass/drums remain native; this pass isolates only vertical triad-aware closed source behavior.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
