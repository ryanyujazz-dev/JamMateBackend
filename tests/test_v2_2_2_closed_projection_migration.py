from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates, project_source_to_disposition
from jammate_engine.core.voicing.policy import ContentFamily

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULE_NAME = "test_v2_2_2_closed_projection_migration"


def _strict_closed_policy(content: ContentFamily = ContentFamily.SHELL_PLUS_COLOR, density: int = 3) -> VoicingPolicy:
    return VoicingPolicy(
        allowed_content=(content,),
        preferred_content=content,
        preferred_density=density,
        min_density=density,
        max_density=density,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        metadata={
            "strict_closed_compact_pitch_class_layout": True,
            "strict_closed_max_span": 12,
            "closed_voicing_lowest_note_floor": 53,
        },
    )


def test_v2_2_4_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_strict_closed_projection_bypasses_legacy_callback_when_seed_is_available() -> None:
    policy = _strict_closed_policy()
    result = project_source_to_disposition(
        disposition=Disposition.CLOSED,
        policy=policy,
        root_pc=0,
        degrees=[("3", 4), ("7", 11), ("9", 14)],
        legacy_placement_callback=lambda: [("legacy", 60)],
    )

    assert result.placed_list != [("legacy", 60)]
    assert result.spec.family.value == "closed"
    assert result.metadata["legacy_projection_callback_used"] is False
    assert result.metadata["legacy_projection_cleanup_required"] is False
    assert result.metadata["closed_projection_migrated"] is True
    assert result.metadata["migrated_projection_path"] == "core.voicing.disposition.closed.place_compact_closed_seed_layout"
    assert result.disposition_guard["migrated_projection_path"] == "core.voicing.disposition.closed.place_compact_closed_seed_layout"


def test_candidate_generation_marks_migrated_strict_closed_candidates() -> None:
    policy = _strict_closed_policy()
    candidates = generate_candidates("Cmaj9", policy)
    assert candidates
    assert {candidate.disposition for candidate in candidates} == {Disposition.CLOSED}
    assert {candidate.density for candidate in candidates} == {3}
    assert any(candidate.metadata.get("closed_projection_migrated") is True for candidate in candidates)
    for candidate in candidates:
        assert candidate.metadata["disposition_projection_family"] == "closed"
        assert candidate.metadata["disposition_projection_method"] == "compact"
        assert candidate.metadata["closed_projection_layer"] == "core.voicing.disposition.closed"
        assert max(candidate.notes) - min(candidate.notes) <= 12


def test_doubled_triad_closed_falls_back_to_ordered_source_path_without_partial_candidate() -> None:
    policy = _strict_closed_policy(ContentFamily.MAJOR_TRIAD, density=4)
    candidates = generate_candidates("C", policy)
    assert candidates
    assert {candidate.density for candidate in candidates} == {4}
    assert any(candidate.degrees == ["R", "3", "5", "R"] for candidate in candidates)
    assert any(candidate.metadata.get("legacy_projection_callback_used") is True for candidate in candidates)


def test_candidate_generator_no_longer_owns_strict_closed_algorithms() -> None:
    source = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "selection" / "candidate_generator.py").read_text(encoding="utf-8")
    assert "def _place_closed_pitch_class_seed_layout" not in source
    assert "def _strict_closed_register_variants" not in source
    closed = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "closed.py").read_text(encoding="utf-8")
    assert "def place_compact_closed_seed_layout" in closed
    assert "def strict_closed_register_variants" in closed
