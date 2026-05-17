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
MIDI_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_voicing_tuning_{PRESET_ID}.mid"
REPORT_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_voicing_tuning_{PRESET_ID}_piano_audit.md"
TRACE_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_voicing_tuning_{PRESET_ID}_piano_trace.json"


def main() -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            # The score form already repeats the full chart three times.
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
            "output_path": str(MIDI_OUTPUT_PATH),
            # Keep bass_present true so rootless shell voicings are legal.
            # The global override below freezes only piano rhythm; bass/drums remain style-native.
            "ensemble": {"bass_present": True},
            "voicing_override": {
                "enabled": True,
                "preset": PRESET_ID,
                "pattern_mode": "region_start_anchor_only",
            },
        }
    )
    REPORT_OUTPUT_PATH.write_text(format_piano_musical_audit_report(result.debug), encoding="utf-8")
    TRACE_OUTPUT_PATH.write_text(
        json.dumps(asdict(build_piano_musical_audit(result.debug)), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        {
            "ok": True,
            "preset": PRESET_ID,
            "midi_path": str(MIDI_OUTPUT_PATH),
            "report_path": str(REPORT_OUTPUT_PATH),
            "trace_path": str(TRACE_OUTPUT_PATH),
        }
    )


if __name__ == "__main__":
    main()
