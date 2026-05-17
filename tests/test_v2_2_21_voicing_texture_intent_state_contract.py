from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import (
    VOICING_CONTRACT_VERSION,
    Disposition,
    DispositionFamily,
    VoicingMethodLockMode,
    VoicingPolicy,
    VoicingTextureCharacter,
    VoicingTextureFamilySwitchPolicy,
    VoicingTextureMethodUniformity,
    derive_voicing_texture_intent,
    derive_voicing_texture_state,
    generate_candidates,
)
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as get_medium_swing_voicing_policy


def _read(rel: str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_v2_2_21_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert _read("VERSION").strip() == "v2_3_9"


def test_medium_swing_texture_state_reuses_existing_policy_metadata() -> None:
    policy = get_medium_swing_voicing_policy()

    intent = derive_voicing_texture_intent(policy)
    state = derive_voicing_texture_state(policy, intent=intent)
    debug = state.to_debug_dict()

    assert intent.character == VoicingTextureCharacter.OPEN_SWING
    assert state.primary_family == DispositionFamily.OPEN
    assert state.allowed_families == (DispositionFamily.OPEN,)
    assert debug["contract"] == "voicing_texture_state_engine_resolved_contract_v2_2_21"
    assert debug["open_method_weights"]["drop2"] == 0.50
    assert debug["open_method_weights"]["drop2_and_4"] == 0.14
    assert debug["family_stickiness"] >= 0.85
    assert state.progression_method_lock_mode == VoicingMethodLockMode.STRICT


def test_explicit_llm_like_texture_intent_resolves_to_engine_state_without_new_planner() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED, Disposition.OPEN),
        metadata={
            "voicing_texture_intent": {
                "source": "llm_intent",
                "scope_id": "bridge_A",
                "scope_type": "section",
                "character": "wide_warm_ballad",
                "preferred_family": "spread",
                "method_uniformity": "phrase_locked",
                "allow_family_switch": "forbidden",
                "avoid_methods": ["drop2_and_4"],
            },
            "disposition_method_weights": {
                "family": {"closed": 0.2, "open": 0.3, "spread": 0.5},
                "open": {"generic_open": 0.4, "drop2": 0.4, "drop2_and_4": 0.2},
                "spread": {"lower_upper_grouped": 0.7, "foundation_projection": 0.3},
            },
        },
    )

    intent = derive_voicing_texture_intent(policy)
    state = derive_voicing_texture_state(policy, intent=intent)
    debug = state.to_debug_dict()

    assert intent.character == VoicingTextureCharacter.WIDE_WARM_BALLAD
    assert intent.method_uniformity == VoicingTextureMethodUniformity.PHRASE_LOCKED
    assert intent.allow_family_switch == VoicingTextureFamilySwitchPolicy.FORBIDDEN
    assert state.primary_family == DispositionFamily.SPREAD
    assert state.scope_id == "bridge_A"
    assert debug["scope_type"] == "section"
    assert debug["family_switch_policy"] == "forbidden"
    assert debug["open_method_weights"] == {"generic_open": 0.4, "drop2": 0.4}
    assert debug["progression_method_lock_mode"] == "strict"


def test_generated_candidates_expose_texture_state_debug_metadata() -> None:
    candidates = generate_candidates("Cmaj7", get_medium_swing_voicing_policy())
    assert candidates
    debug = candidates[0].metadata["voicing_texture_state"]

    assert debug["contract"] == "voicing_texture_state_engine_resolved_contract_v2_2_21"
    assert debug["primary_family"] == "open"
    assert "method lock controls progression method continuity" in debug["architecture_boundary"]
    assert candidates[0].metadata["voicing_texture_state_primary_family"] == "open"


def test_v2_2_21_docs_record_contract_planning_pass() -> None:
    combined = "\n".join(
        _read(rel)
        for rel in (
            "agent.md",
            "README.md",
            "docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md",
            "docs/DEVELOPMENT_TASK_PLAN_V2.md",
            "docs/VOICING_MODULE_CORE_LOGIC_V2.md",
        )
    )
    for token in (
        "v2_2_21 update — VoicingTextureIntent / VoicingTextureState Contract Planning Pass",
        "derive_voicing_texture_intent",
        "derive_voicing_texture_state",
        "voicing_texture_state_engine_resolved_contract_v2_2_21",
        "default listening behavior unchanged",
        "the next engineering target should be selected by the user",
    ):
        assert token in combined
