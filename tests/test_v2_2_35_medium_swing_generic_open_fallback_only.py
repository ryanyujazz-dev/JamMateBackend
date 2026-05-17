from __future__ import annotations

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing.selection.candidate_generator import generate_candidates
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy
from jammate_engine.core.voicing.disposition.models import Disposition
from jammate_engine.core.voicing.policy import VoicingPolicy


def test_v2_2_38_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"


def test_medium_swing_generic_open_has_zero_weight_but_remains_generated_for_fallback_coverage() -> None:
    policy = get_voicing_policy()
    metadata = dict(policy.metadata or {})

    assert metadata["open_projection_method_pool"] == ["generic_open", "drop2", "drop3", "drop2_and_4"]
    assert metadata["disposition_method_weights"]["open"]["generic_open"] == 0.0

    candidates = generate_candidates("G7", policy)
    methods = {
        candidate.metadata.get("active_open_projection_method")
        for candidate in candidates
        if candidate.metadata.get("disposition_projection_family") == "open"
    }
    assert methods
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.issubset(methods)
    generic = [
        candidate for candidate in candidates
        if candidate.metadata.get("active_open_projection_method") == "generic_open"
        and candidate.metadata.get("disposition_projection_family") == "open"
    ]
    assert generic
    assert all(candidate.metadata.get("disposition_method_weight") == 0.0 for candidate in generic)


def test_generic_open_is_still_available_when_explicitly_requested_as_rescue_safe_method() -> None:
    base = get_voicing_policy()
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=base.preferred_density,
        min_density=base.min_density,
        max_density=base.max_density,
        register_low=base.register_low,
        register_high=base.register_high,
        max_voicing_span=base.max_voicing_span,
        metadata={
            **dict(base.metadata or {}),
            "allowed_open_projection_methods": ["generic_open"],
            "open_projection_method": "generic_open",
            "method_lock_rescue_runtime_attempt": True,
            "method_lock_rescue_runtime_attempt_family": "open",
            "method_lock_rescue_runtime_attempt_method": "generic_open",
        },
    )

    candidates = generate_candidates("G7", policy)
    methods = {
        candidate.metadata.get("active_open_projection_method")
        for candidate in candidates
        if candidate.metadata.get("disposition_projection_family") == "open"
    }
    assert methods == {"generic_open"}
