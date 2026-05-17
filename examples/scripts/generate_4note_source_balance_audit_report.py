from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    build_four_note_source_balance_audit,
    format_four_note_source_balance_audit_report,
)
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_policy

ROOT = PROJECT_ROOT
REPORT_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_4note_source_balance_decision_audit.md"
JSON_OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_4note_source_balance_decision_audit.json"

SYMBOLS = (
    # Plain / explicit color major-family sources.
    "Cmaj7",
    "Cmaj9",
    "Cmaj7#11",
    "C6/9",
    # Minor-family explicit color coverage.
    "Dm7",
    "Dm9",
    "Dm11",
    "Dm13",
    # Dominant baseline, natural color, #11, single altered, compound altered, alt palette.
    "G7",
    "G9",
    "G13",
    "G7#11",
    "G7b9",
    "G7#9",
    "G7b13",
    "G7b9b13",
    "G7alt",
    # Half-diminished baseline and explicit color coverage.
    "Bm7b5",
    "Bm9b5",
    "Bm11b5",
    # Extra regression symbols retained from previous audits.
    "Cm11",
    "Cm13",
    "Fmaj9",
    "Fmaj13",
    "G13#11",
    "C6",
    "G7sus4",
    "Cdim7",
)


def _policy_chord_symbol_only_probe() -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.SEVENTH_BASIC,
        harmonic_expansion_enabled=False,
        color_policy_mode=ColorPolicyMode.CHORD_SYMBOL_ONLY,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
        preferred_density=4,
        min_density=4,
        max_density=4,
        selection_pool_size=8,
        selector_temperature=0.20,
        metadata={"audit_probe": "chord_symbol_only_all_4note_families"},
    )


def _policy_expansion_probe() -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(
            ContentFamily.SEVENTH_BASIC,
            ContentFamily.ROOTED_COLOR,
            ContentFamily.ROOTLESS_A,
            ContentFamily.ROOTLESS_B,
        ),
        preferred_content=ContentFamily.ROOTLESS_A,
        harmonic_expansion_enabled=True,
        color_policy_mode=ColorPolicyMode.STYLE_SAFE_EXTENSIONS,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
        preferred_density=4,
        min_density=4,
        max_density=4,
        selection_pool_size=8,
        selector_temperature=0.20,
        metadata={"audit_probe": "harmonic_expansion_all_4note_families"},
    )


def main() -> None:
    policies = {
        "probe_chord_symbol_only": _policy_chord_symbol_only_probe(),
        "probe_harmonic_expansion": _policy_expansion_probe(),
        "style_medium_swing": swing_policy(),
        "style_bossa_nova": bossa_policy(),
        "style_jazz_ballad": ballad_policy(),
    }
    audit = build_four_note_source_balance_audit(SYMBOLS, policies)
    REPORT_OUTPUT_PATH.write_text(format_four_note_source_balance_audit_report(audit), encoding="utf-8")
    JSON_OUTPUT_PATH.write_text(json.dumps(audit.to_debug_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": True, "report_path": str(REPORT_OUTPUT_PATH), "json_path": str(JSON_OUTPUT_PATH)})


if __name__ == "__main__":
    main()
