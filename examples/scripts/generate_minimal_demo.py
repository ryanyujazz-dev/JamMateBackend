from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment


def main() -> None:
    leadsheet_path = PROJECT_ROOT / "examples" / "leadsheets" / "minimal_ii_v_i.json"
    leadsheet = json.loads(leadsheet_path.read_text(encoding="utf-8"))
    result = generate_accompaniment(
        {
            "leadsheet": leadsheet,
            "style": "medium_swing",
            "tempo": 132,
            "choruses": 3,
            "seed": 42,
            "output_path": str(PROJECT_ROOT / "demos" / f"{ENGINE_VERSION_TAG}_minimal_demo.mid"),
            "ensemble": {"bass_present": True},
        }
    )
    print(result)


if __name__ == "__main__":
    main()
