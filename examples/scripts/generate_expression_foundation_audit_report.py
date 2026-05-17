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
from jammate_engine.core.expression.audit import (
    ExpressionFoundationAudit,
    format_expression_foundation_audit_report,
)
from jammate_engine.runtime.generate import generate_accompaniment


ROOT = PROJECT_ROOT
SCORE_PATH = ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json"
MIDI_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_demo.mid"
REPORT_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_expression_foundation_audit_report.md"
TRACE_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_expression_foundation_audit_trace.json"


def main() -> None:
    score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            # Audit scripts may intentionally render one written-form chorus; delivery demos render three via GenerationRequest.choruses.
            "choruses": 1,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
            "output_path": str(MIDI_OUTPUT_PATH),
            "ensemble": {"bass_present": True},
        }
    )
    audit = ExpressionFoundationAudit(
        summary=dict(result.debug.get("expression_foundation_audit") or {}),
        event_rows=list(result.debug.get("expression_foundation_audit_events") or []),
        warnings=[],
    )
    # Reconstruct warnings from diagnostic flags for script output.  The runtime
    # debug stores rows + summary so downstream callers do not need dataclass
    # imports; this script formats that stable payload.
    warnings = []
    report_warning_flags = {"crosses_next_same_track_event", "crosses_region_end", "short_overlaps_next_event", "sustain_chop_risk", "missing_expression", "non_positive_duration", "velocity_out_of_midi_range"}
    for row in audit.event_rows:
        for flag in row.get("flags") or []:
            if flag in report_warning_flags:
                warnings.append(f"Event {row.get('event_id')} ({row.get('chord_symbol')}) expression diagnostic flag: {flag}")
    audit = ExpressionFoundationAudit(summary=audit.summary, event_rows=audit.event_rows, warnings=warnings)
    REPORT_OUTPUT_PATH.write_text(format_expression_foundation_audit_report(audit), encoding="utf-8")
    TRACE_OUTPUT_PATH.write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": True, "midi_path": str(MIDI_OUTPUT_PATH), "report_path": str(REPORT_OUTPUT_PATH), "trace_path": str(TRACE_OUTPUT_PATH)})


if __name__ == "__main__":
    main()
