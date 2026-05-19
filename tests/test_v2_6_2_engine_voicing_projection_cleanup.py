from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing.selection.content_placement import place_content_recipe_for_projection
from jammate_engine.core.voicing.selection.register_variants import register_variants
from jammate_engine.core.voicing.selection.source_rotation_metadata import source_rotation_metadata

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_generator_no_longer_owns_projection_detail_helpers() -> None:
    """Candidate generation should orchestrate, not own placement/metadata/variants."""

    source = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "selection" / "candidate_generator.py").read_text(encoding="utf-8")
    forbidden = [
        "def _place_content_recipe",
        "def _place_rootless_ab_ordered_stack",
        "def _place_basic_4note_ordered_stack",
        "def _rootless_ab_orientation_metadata",
        "def _basic_4note_metadata",
        "def _rooted_color_4note_metadata",
        "def _triad_4note_metadata",
        "def _register_variants",
        "def _policy_for_disposition_guard",
    ]
    for token in forbidden:
        assert token not in source

    assert callable(place_content_recipe_for_projection)
    assert callable(register_variants)
    assert callable(source_rotation_metadata)


def test_voicing_candidate_contract_survives_projection_cleanup() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        metadata={"open_projection_methods": ["generic_open", "drop2", "drop3", "drop2_and_4"]},
    )
    candidates = generate_candidates("Cmaj7", policy)
    assert candidates

    methods = {candidate.metadata.get("disposition_projection_method") for candidate in candidates}
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.intersection(methods)
    for candidate in candidates:
        assert candidate.notes
        assert candidate.metadata["disposition_projection_entry"].endswith("project_source_to_disposition")
        assert "content_recipe" in candidate.metadata
        assert "register_guard" in candidate.metadata
        assert "canonical_closed_source" in candidate.metadata


def test_source_rotation_metadata_stays_available_after_module_split() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        metadata={"strict_closed_compact_pitch_class_layout": True},
    )
    candidates = generate_candidates("G7", policy)
    assert candidates
    # At least some candidates should keep source-family audit metadata supplied
    # by the extracted source_rotation_metadata module.
    assert any(
        key in candidate.metadata
        for candidate in candidates
        for key in ("basic_4note_source_contract", "rootless_ab_orientation_contract", "triad_4note_rotation_contract")
    )
