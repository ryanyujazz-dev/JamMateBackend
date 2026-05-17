from __future__ import annotations

from pathlib import Path

from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.runtime.override import build_voicing_override_policy
from jammate_engine.core.voicing.selection.selector import select_candidate

ROOT = Path(__file__).resolve().parents[1]


def _rootless_policy():
    return build_voicing_override_policy({}, {"enabled": True, "preset": "rootless_ab_safe"}, style_name="medium_swing")


def test_v2_1_16_rootless_ab_source_rotations_use_8_to_2_prior() -> None:
    policy = _rootless_policy()
    candidates = [
        candidate
        for candidate in generate_candidates("Cmaj7", policy)
        if candidate.content_family == ContentFamily.ROOTLESS_A
        and candidate.metadata.get("rootless_ab_content_type") == "with_5"
        and candidate.disposition.value == "closed"
        and candidate.metadata.get("register_variant") == 0
    ]
    by_index = {candidate.metadata["rootless_ab_inversion_index"]: candidate for candidate in candidates}

    assert {index: by_index[index].metadata["rootless_ab_inversion_weight"] for index in sorted(by_index)} == {
        0: 8,
        1: 2,
        2: 8,
        3: 2,
    }
    assert by_index[0].metadata["rootless_ab_preferred_source_rotation"] is True
    assert by_index[2].metadata["rootless_ab_preferred_source_rotation"] is True
    assert by_index[1].metadata["rootless_ab_preferred_source_rotation"] is False
    assert by_index[3].metadata["rootless_ab_preferred_source_rotation"] is False

    scored_preferred = select_candidate([by_index[0]], policy=policy)
    scored_secondary = select_candidate([by_index[1]], policy=policy)
    preferred_prior = scored_preferred.metadata["score_breakdown"]["details"]["rootless_ab_inversion_prior_score"]
    secondary_prior = scored_secondary.metadata["score_breakdown"]["details"]["rootless_ab_inversion_prior_score"]

    assert preferred_prior > secondary_prior
    assert round(preferred_prior - secondary_prior, 3) == 0.277


def test_v2_1_16_with_13_uses_the_same_preferred_rotation_prior() -> None:
    policy = _rootless_policy()
    candidates = [
        candidate
        for candidate in generate_candidates("Cmaj7", policy)
        if candidate.content_family == ContentFamily.ROOTLESS_A
        and candidate.metadata.get("rootless_ab_content_type") == "with_13"
        and candidate.disposition.value == "closed"
        and candidate.metadata.get("register_variant") == 0
    ]
    assert {candidate.metadata["rootless_ab_inversion_index"]: candidate.metadata["rootless_ab_inversion_weight"] for candidate in candidates} == {
        0: 8,
        1: 2,
        2: 8,
        3: 2,
    }


def test_v2_1_16_voicing_module_core_logic_doc_exists() -> None:
    doc = ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md"
    text = doc.read_text(encoding="utf-8")
    assert "v2_1_16" in text
    assert "VoicingTexturePlan" in text
    assert "Content Recipe" in text
    assert "CanonicalClosedSource" in text
    assert "Disposition" in text
    assert "VoiceLeadingScorer" in text
    assert "8:2" in text
    assert "3-5-7-9" in text and "7-9-3-5" in text
