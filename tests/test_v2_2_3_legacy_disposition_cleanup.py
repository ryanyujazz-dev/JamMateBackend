from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import Disposition, VoicingPolicy, generate_candidates
from jammate_engine.core.voicing.disposition.open import place_generic_open_projection
from jammate_engine.core.voicing.disposition.spread import (
    place_foundation_projection,
    place_lower_upper_grouped_projection,
    place_root_10th_projection,
)
from jammate_engine.core.voicing.disposition.facade import describe_disposition_placement, place_degree_notes

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULE_NAME = "test_v2_2_4_legacy_disposition_cleanup"


def test_v2_2_4_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_disposition_facade_delegates_to_open_projection_module() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))
    degrees = [("R", 0), ("3", 4), ("5", 7), ("7", 11)]

    wrapped = place_degree_notes(0, degrees, policy.register_low, policy.register_high, Disposition.OPEN, policy)
    direct = place_generic_open_projection(0, degrees, policy.register_low, policy.register_high, policy)

    assert wrapped == direct
    assert wrapped
    debug = describe_disposition_placement(wrapped, Disposition.OPEN, policy)
    assert debug["placement_algorithm_owner"] == "core.voicing.disposition"
    assert debug["disposition_planner_role"] == "placement_facade_and_debug_contract"


def test_legacy_spread_inputs_delegate_to_new_spread_projection_module() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.SPREAD, allowed_dispositions=(Disposition.SPREAD,))
    degrees = [("R", 0), ("3", 4), ("5", 7), ("7", 11)]

    wrapped = place_degree_notes(0, degrees, policy.register_low, policy.register_high, Disposition.SPREAD, policy)
    direct = place_lower_upper_grouped_projection(0, degrees, policy.register_low, policy.register_high, policy)
    assert wrapped == direct

    foundation = place_degree_notes(0, degrees, policy.register_low, policy.register_high, Disposition.LEFT_ROOT_RIGHT_CHORD, policy)
    assert foundation == place_foundation_projection(0, degrees, policy)

    root_10th = place_degree_notes(0, degrees, policy.register_low, policy.register_high, Disposition.OPEN_ROOT_10TH, policy)
    assert root_10th == place_root_10th_projection(0, degrees, policy)


def test_candidate_metadata_marks_disposition_projection_as_single_owner_for_generic_open() -> None:
    policy = VoicingPolicy(preferred_disposition=Disposition.OPEN, allowed_dispositions=(Disposition.OPEN,))
    candidates = generate_candidates("Cmaj7", policy)
    assert candidates
    assert any(candidate.metadata["legacy_projection_callback_used"] is True for candidate in candidates)
    assert all(candidate.disposition_guard["placement_algorithm_owner"] == "core.voicing.disposition" for candidate in candidates)
    assert all(candidate.metadata["disposition_projection_family"] == "open" for candidate in candidates)
    assert all(candidate.metadata["disposition_projection_method"] == "generic_open" for candidate in candidates)


def test_disposition_facade_no_longer_owns_private_open_or_spread_algorithms() -> None:
    text = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "disposition" / "facade.py").read_text(encoding="utf-8")
    forbidden = [
        "def _degree_to_note",
        "def _place_stack",
        "def _place_spread",
        "def _place_left_root_right_chord",
        "def _place_open_root_10th",
        "def _dedupe_by_note",
    ]
    for token in forbidden:
        assert token not in text

    assert "place_generic_open_projection" in text
    assert "place_lower_upper_grouped_projection" in text
    assert "place_foundation_projection" in text
    assert "place_root_10th_projection" in text

# Historical harness token retained after v2_2_4 version bump:
# test_v2_2_3_legacy_disposition_cleanup
