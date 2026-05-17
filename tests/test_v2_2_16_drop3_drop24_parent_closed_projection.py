from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, OpenProjectionMethod, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION
from jammate_engine.core.voicing.disposition.open import (
    named_open_projection_metadata,
    place_drop2_and_4_projection_from_closed_parent,
    place_drop3_projection_from_closed_parent,
)


def test_v2_2_20_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_drop3_and_drop2_and_4_named_projection_metadata_aliases() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=48,
        register_high=84,
        max_voicing_span=28,
    )
    parent = [("root", 60), ("third", 64), ("fifth", 67), ("seventh", 71)]

    drop3 = place_drop3_projection_from_closed_parent(parent, policy)
    assert drop3 == [("third", 52), ("root", 60), ("fifth", 67), ("seventh", 71)]
    drop3_meta = named_open_projection_metadata(drop3, OpenProjectionMethod.DROP3, parent)
    assert drop3_meta["open_named_projection_method"] == "drop3"
    assert drop3_meta["open_drop3_projection"] is True
    assert drop3_meta["open_drop3_from_parent_closed_projection"] is True
    assert drop3_meta["open_drop3_parent_closed_notes"] == [60, 64, 67, 71]

    # v2_2_20 lowers the named drop-family floor to C2, so this
    # single-parent DROP2&4 result is now legal. Production still enumerates
    # multiple parents before selection.
    assert place_drop2_and_4_projection_from_closed_parent(parent, policy) == [("root", 48), ("fifth", 55), ("third", 64), ("seventh", 71)]
    policy_without_raise = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        register_low=48,
        register_high=84,
        max_voicing_span=28,
        metadata={"drop_family_register_low_offset_semitones": 0},
    )
    drop24 = place_drop2_and_4_projection_from_closed_parent(parent, policy_without_raise)
    assert drop24 == [("root", 48), ("fifth", 55), ("third", 64), ("seventh", 71)]
    drop24_meta = named_open_projection_metadata(drop24, OpenProjectionMethod.DROP2_AND_4, parent, policy=policy_without_raise)
    assert drop24_meta["open_named_projection_method"] == "drop2_and_4"
    assert drop24_meta["open_drop2_and_4_projection"] is True
    assert drop24_meta["open_drop2_and_4_from_parent_closed_projection"] is True
    assert drop24_meta["open_drop2_and_4_parent_closed_notes"] == [60, 64, 67, 71]


def test_drop3_and_drop2_and_4_generate_candidates_from_closed_parent_projection() -> None:
    for method in ("drop3", "drop2_and_4"):
        policy = VoicingPolicy(
            preferred_disposition=Disposition.OPEN,
            allowed_dispositions=(Disposition.OPEN,),
            preferred_density=4,
            min_density=4,
            max_density=4,
            register_low=46,
            register_high=84,
            max_voicing_span=28,
            metadata={"open_projection_method": method, "strict_closed_compact_pitch_class_layout": True},
        )
        candidates = generate_candidates("Cmaj7", policy)
        real = [candidate for candidate in candidates if not candidate.metadata.get("fallback")]
        assert real, method
        methods = {candidate.metadata.get("disposition_projection_method") for candidate in real}
        assert methods == {method}
        assert all(candidate.metadata.get("open_named_projection") is True for candidate in real)
        assert all(candidate.metadata.get("open_named_projection_method") == method for candidate in real)
        assert all(candidate.metadata.get("open_named_projection_parent_closed_notes") for candidate in real)
        assert all(candidate.metadata.get(f"open_{method}_from_parent_closed_projection") is True for candidate in real)
        assert all(candidate.metadata.get("legacy_projection_callback_used") is False for candidate in real)


def test_default_open_still_stays_generic_after_drop3_drop24_implementation() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
    )
    candidates = generate_candidates("Cmaj7", policy)
    assert candidates
    assert {candidate.metadata["disposition_projection_method"] for candidate in candidates} == {"generic_open"}
