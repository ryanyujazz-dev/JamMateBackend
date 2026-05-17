from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.core.voicing.disposition.models import OpenProjectionMethod
from jammate_engine.core.voicing.selection.scorer import score_candidate
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy


def test_v2_2_20_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_medium_swing_enables_open_drop_family_pool_and_runtime_weight_scoring() -> None:
    policy = get_medium_swing_voicing_policy()
    metadata = dict(policy.metadata or {})
    assert metadata["open_projection_method_pool"] == ["generic_open", "drop2", "drop3", "drop2_and_4"]
    assert metadata["disposition_method_weights_enabled_for_scoring"] is True
    assert metadata["disposition_method_weights"]["open"] == {
        "generic_open": 0.0,
        "drop2": 0.50,
        "drop3": 0.36,
        "drop2_and_4": 0.14,
    }

    candidates = generate_candidates("G7", policy)
    methods = {c.metadata.get("active_open_projection_method") for c in candidates if c.metadata.get("disposition_projection_family") == "open"}
    assert {m.value for m in OpenProjectionMethod}.issubset(methods)
    assert any(c.metadata.get("disposition_method_weight_scoring_enabled") is True for c in candidates)


def test_disposition_method_weight_enters_score_breakdown_only_when_enabled() -> None:
    medium_policy = get_medium_swing_voicing_policy()
    candidate = next(
        c for c in generate_candidates("G7", medium_policy)
        if c.metadata.get("active_open_projection_method") == "drop2"
    )
    score = score_candidate(candidate, medium_policy)
    assert score.disposition_method != 0.0
    assert score.to_metadata()["disposition_method"] == round(score.disposition_method, 4)
    assert score.details["disposition_method_score"] == round(score.disposition_method, 4)
    assert score.details["disposition_method_weight"] == candidate.metadata["disposition_method_weight"]

    bossa_policy = get_bossa_voicing_policy()
    bossa_candidate = generate_candidates("G7", bossa_policy)[0]
    bossa_score = score_candidate(bossa_candidate, bossa_policy)
    assert bossa_candidate.metadata.get("disposition_method_weight_scoring_enabled") is False
    assert bossa_score.disposition_method == 0.0
