from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import VOICING_CONTRACT_VERSION, generate_candidates
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as get_bossa_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy


def test_v2_2_28_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"


def test_medium_swing_consumes_texture_state_to_filter_to_open_family() -> None:
    policy = get_medium_swing_voicing_policy()
    candidates = generate_candidates("G7", policy)
    assert candidates

    runtime_debug = candidates[0].metadata["voicing_texture_state_runtime_filter"]
    assert runtime_debug["contract"] == "voicing_texture_state_runtime_filter_contract_v2_2_28"
    assert runtime_debug["enabled"] is True
    assert runtime_debug["primary_family"] == "open"
    assert runtime_debug["allowed_families"] == ["open"]
    assert runtime_debug["original_dispositions"] == ["open", "closed"]
    assert runtime_debug["effective_dispositions"] == ["open"]
    assert runtime_debug["fallback_to_original"] is False

    assert {candidate.metadata.get("disposition_projection_family") for candidate in candidates} == {"open"}
    assert all(candidate.disposition.value == "open" for candidate in candidates)


def test_medium_swing_open_method_pool_remains_available_after_texture_filter() -> None:
    candidates = generate_candidates("G7", get_medium_swing_voicing_policy())
    methods = {
        candidate.metadata.get("active_open_projection_method")
        for candidate in candidates
        if candidate.metadata.get("disposition_projection_family") == "open"
    }
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.issubset(methods)


def test_bossa_does_not_consume_medium_swing_texture_state_runtime_filter() -> None:
    candidates = generate_candidates("G7", get_bossa_voicing_policy())
    assert candidates
    runtime_debug = candidates[0].metadata["voicing_texture_state_runtime_filter"]
    assert runtime_debug["enabled"] is False
    assert runtime_debug["reason"] == "policy_metadata_did_not_enable_runtime_filtering"
