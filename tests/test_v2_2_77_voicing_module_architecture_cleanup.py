from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import VoicingPolicy, generate_candidates

ROOT = Path(__file__).resolve().parents[1]


def test_v2_2_82_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_voicing_files_are_grouped_by_runtime_responsibility() -> None:
    voicing = ROOT / "src" / "jammate_engine" / "core" / "voicing"
    expected = {
        "sources/content_planner.py",
        "sources/source_balance.py",
        "taxonomy/recipes.py",
        "taxonomy/projection_map.py",
        "disposition/facade.py",
        "selection/candidate_generator.py",
        "selection/selector.py",
        "runtime/voicing_resolver.py",
        "runtime/texture_plan.py",
    }
    for rel in expected:
        assert (voicing / rel).exists(), rel

    removed_flat_files = {
        "candidate_generator.py",
        "content_planner.py",
        "source_balance.py",
        "disposition_planner.py",
        "voice_motion.py",
    }
    for name in removed_flat_files:
        assert not (voicing / name).exists(), name


def test_top_level_voicing_api_still_resolves_after_cleanup() -> None:
    candidates = generate_candidates("Cmaj7", VoicingPolicy())
    assert candidates
    assert candidates[0].notes
