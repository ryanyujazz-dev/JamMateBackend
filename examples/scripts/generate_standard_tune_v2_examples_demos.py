from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment

LEADSHEET_DIR = PROJECT_ROOT / "examples" / "leadsheets"
DEMOS_DIR = PROJECT_ROOT / "demos"

STANDARD_TUNE_DEMO_SPECS: tuple[dict[str, Any], ...] = (
    {
        "slug": "autumn_leaves",
        "leadsheet": "autumn_leaves.json",
        "style": "medium_swing",
        "seed": 22701,
    },
    {
        "slug": "blue_bossa",
        "leadsheet": "blue_bossa.json",
        "style": "bossa_nova",
        "seed": 22702,
    },
    {
        "slug": "misty",
        "leadsheet": "misty.json",
        "style": "jazz_ballad",
        "seed": 22703,
    },
)


def main() -> None:
    DEMOS_DIR.mkdir(exist_ok=True)
    outputs = [_generate_demo(spec) for spec in STANDARD_TUNE_DEMO_SPECS]
    summary = {
        "contract_version": ENGINE_VERSION_TAG,
        "milestone": "v2_2_27 — Standard Tune V2 LeadSheet Examples Pass",
        "scope": "Generate three-chorus standard-tune demos from V2 sections + written_form examples.",
        "outputs": outputs,
        "acceptance": {"passed": all(item["ok"] for item in outputs)},
    }
    summary_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_standard_tune_v2_examples_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({"ok": summary["acceptance"]["passed"], "summary_path": str(summary_path), "outputs": outputs})
    if not summary["acceptance"]["passed"]:
        raise SystemExit(1)


def _generate_demo(spec: dict[str, Any]) -> dict[str, Any]:
    score_path = LEADSHEET_DIR / str(spec["leadsheet"])
    score = json.loads(score_path.read_text(encoding="utf-8"))
    slug = str(spec["slug"])
    style = str(spec["style"])
    midi_path = DEMOS_DIR / f"{ENGINE_VERSION_TAG}_{slug}_{style}_demo.mid"
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": style,
            "tempo": int(score.get("tempo", 120)),
            "choruses": 3,
            "seed": int(spec["seed"]),
            "output_path": str(midi_path),
            "ensemble": {"bass_present": True},
        }
    )
    debug = dict(result.debug)
    return {
        "ok": bool(result.ok),
        "title": score.get("title"),
        "style": style,
        "midi_path": str(midi_path.relative_to(PROJECT_ROOT)),
        "written_bars": debug.get("written_bars"),
        "performance_choruses": debug.get("performance_choruses"),
        "performance_bars": debug.get("performance_bars"),
        "regions": debug.get("regions"),
    }


if __name__ == "__main__":
    main()
