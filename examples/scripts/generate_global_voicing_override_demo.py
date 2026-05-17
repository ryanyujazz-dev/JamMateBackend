from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.generation.piano_audit import build_piano_musical_audit, format_piano_musical_audit_report
from jammate_engine.runtime.generate import generate_accompaniment

ROOT = PROJECT_ROOT
SCORE_PATH = ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json"
PRESET_ID = "rootless_ab_safe"


def _write_outputs(style: str, mode: str, result) -> dict:
    stem = f"{ENGINE_VERSION_TAG}_all_the_things_you_are_{style}_global_voicing_override_{PRESET_ID}_{mode}"
    report_path = ROOT / "demos" / f"{stem}_piano_audit.md"
    trace_path = ROOT / "demos" / f"{stem}_piano_trace.json"
    report_path.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    trace_path.write_text(
        json.dumps(asdict(build_piano_musical_audit(result.debug)), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"midi_path": result.midi_path, "report_path": str(report_path), "trace_path": str(trace_path)}


def main() -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    outputs = {}

    # 1) Product behavior: keep the style's own rhythm/expression/timing, but
    # hard-force piano voicing to the selected preset.
    style_default_mode = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "bossa_nova",
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 211,
            "output_path": str(ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_bossa_nova_global_voicing_override_{PRESET_ID}_style_patterns.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {"enabled": True, "preset": PRESET_ID},
        }
    )
    outputs["bossa_nova_style_patterns"] = _write_outputs("bossa_nova", "style_patterns", style_default_mode)

    # 2) Debug behavior: freeze only piano rhythm to one region-start event for any style
    # so a voicing class can be audited chord-by-chord. Bass/drums stay style-native.
    isolation_mode = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "jazz_ballad",
            "choruses": 1,
            "tempo": int(score.get("tempo", 82)),
            "seed": 212,
            "output_path": str(ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_jazz_ballad_global_voicing_override_{PRESET_ID}_isolation.mid"),
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "preset": PRESET_ID,
                "pattern_mode": "region_start_anchor_only",
            },
        }
    )
    outputs["jazz_ballad_isolation"] = _write_outputs("jazz_ballad", "isolation", isolation_mode)

    print({"ok": True, "preset": PRESET_ID, "outputs": outputs})


if __name__ == "__main__":
    main()
