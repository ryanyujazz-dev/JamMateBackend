from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION
from jammate_engine.core.voicing.disposition.models import OpenProjectionMethod
from jammate_engine.core.voicing.disposition.open import place_named_open_projection_from_closed_parents


def test_v2_2_20_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_drop2_and_4_projects_all_parents_before_register_filtering() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=46,
        register_high=84,
        max_voicing_span=28,
    )
    too_low_parent = [("fifth", 57), ("seventh", 60), ("root", 62), ("third", 65)]
    legal_parent = [("root", 62), ("third", 65), ("fifth", 69), ("seventh", 72)]

    selected = place_named_open_projection_from_closed_parents(
        [too_low_parent, legal_parent],
        policy,
        OpenProjectionMethod.DROP2_AND_4,
    )

    assert selected.placed == [("root", 50), ("fifth", 57), ("third", 65), ("seventh", 72)]
    assert selected.parent_index == 1
    assert selected.candidate_count == 2
    assert selected.legal_candidate_count == 2
    assert min(note for _, note in selected.placed) >= 36


def test_drop2_and_4_dm7_no_longer_falls_back_to_single_note() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=46,
        register_high=84,
        max_voicing_span=28,
        metadata={
            "open_projection_method": "drop2_and_4",
            "strict_closed_compact_pitch_class_layout": True,
            "closed_voicing_lowest_note_floor": 53,
            "strict_closed_max_span": 12,
        },
    )
    candidates = generate_candidates("Dm7", policy)
    real = [candidate for candidate in candidates if not candidate.metadata.get("fallback")]

    assert real
    assert all(len(candidate.notes) == 4 for candidate in real)
    assert all(min(candidate.notes) >= 36 for candidate in real)
    assert {candidate.metadata.get("disposition_projection_method") for candidate in real} == {"drop2_and_4"}
    assert all(candidate.metadata.get("open_named_projection_project_then_filter_selection") is True for candidate in real)
    assert all(candidate.metadata.get("open_named_projection_legal_candidate_count", 0) > 0 for candidate in real)
    assert all(candidate.recipe_id != "d1__ungrouped__fallback" for candidate in real)


def test_drop_family_register_floor_defaults_to_c2() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        register_low=46,
        register_high=84,
        max_voicing_span=28,
        metadata={
            "open_projection_method": "drop3",
            "strict_closed_compact_pitch_class_layout": True,
        },
    )
    candidates = [candidate for candidate in generate_candidates("Cmaj7", policy) if not candidate.metadata.get("fallback")]
    assert candidates
    assert all(candidate.metadata.get("open_named_projection_drop_register_low") == 36 for candidate in candidates)
    assert all(candidate.metadata.get("open_named_projection_drop_register_low_offset_semitones") == 0 for candidate in candidates)
    assert all(candidate.metadata.get("open_named_projection_drop_register_low_source") == "default_c2_floor" for candidate in candidates)
