from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.runtime.generate import generate_accompaniment


ROOT = Path(__file__).resolve().parents[2]
SCORE_PATH = ROOT / "examples" / "leadsheets" / "all_the_things_you_are.json"
OUTPUT_PATH = ROOT / "demos" / f"{ENGINE_VERSION_TAG}_all_the_things_you_are_medium_swing_demo.mid"


def main() -> None:
    score = json.loads(SCORE_PATH.read_text())
    result = generate_accompaniment(
        {
            "leadsheet": score,
            "style": "medium_swing",
            # V2 keeps written form in the leadsheet and performance repetitions
            # in GenerationRequest. This yields a three-chorus standard demo.
            "choruses": 3,
            "tempo": int(score.get("tempo", 132)),
            "seed": 1,
            "output_path": str(OUTPUT_PATH),
        }
    )
    print(result)


if __name__ == "__main__":
    main()
