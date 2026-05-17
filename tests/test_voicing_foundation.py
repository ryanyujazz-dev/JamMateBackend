from __future__ import annotations

from jammate_engine.core.gestures import simultaneous_onset
from jammate_engine.core.voicing import (
    ContentFamily,
    Disposition,
    RootSupportPolicy,
    VoicingPolicy,
    VoicingRequest,
    VoicingResolver,
    generate_candidates,
)
from jammate_engine.styles.registry import get_style


def test_core_voicing_includes_basic_triad_families() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOT_REQUIRED,
        preferred_disposition=Disposition.CLOSED,
        preferred_density=3,
    )
    expected = {
        "C": (ContentFamily.MAJOR_TRIAD, {"R", "3", "5"}),
        "Cm": (ContentFamily.MINOR_TRIAD, {"R", "b3", "5"}),
        "Cdim": (ContentFamily.DIMINISHED_TRIAD, {"R", "b3", "b5"}),
        "Caug": (ContentFamily.AUGMENTED_TRIAD, {"R", "3", "#5"}),
        "Csus2": (ContentFamily.SUS2_TRIAD, {"R", "2", "5"}),
        "Csus4": (ContentFamily.SUS4_TRIAD, {"R", "4", "5"}),
    }
    for symbol, (family, degrees) in expected.items():
        candidate = generate_candidates(symbol, policy)[0]
        assert candidate.content_family == family
        assert set(candidate.degrees) == degrees
        assert candidate.root_included is True


def test_rootless_policy_can_generate_rootless_jazz_voicing() -> None:
    policy = VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_PREFERRED,
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.OPEN,
        preferred_density=4,
        harmonic_expansion_enabled=True,
    )
    candidate = generate_candidates("G7", policy)[0]
    assert candidate.content_family == ContentFamily.ROOTLESS_A
    assert "R" not in candidate.degrees
    assert candidate.root_included is False
    assert len(candidate.notes) >= 3


def test_no_bass_default_uses_piano_rh_comping_not_root_stuffing() -> None:
    request = VoicingRequest(
        event_id="e_no_bass",
        chord_symbol="Dm7",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="sustain",
        ensemble_context={"bass_present": False},
        policy=VoicingPolicy(root_support=RootSupportPolicy.ROOTLESS_PREFERRED),
    )
    plan = VoicingResolver().resolve(request)
    assert plan.root_support == "rootless_allowed"
    assert plan.ensemble_role == "piano_rh_harmonic_comping"
    assert plan.metadata["ensemble_context"]["needs_piano_lh_bass_foundation"] is True
    assert all(note.hand == "right" for note in plan.notes)


def test_no_bass_without_split_role_keeps_root_required_fallback() -> None:
    request = VoicingRequest(
        event_id="e_no_bass_fallback",
        chord_symbol="Dm7",
        track="piano",
        gesture_type="simultaneous_onset",
        gesture=simultaneous_onset(),
        expression_articulation="sustain",
        ensemble_context={"bass_present": False, "piano_split_role_enabled": False},
        policy=VoicingPolicy(root_support=RootSupportPolicy.ROOTLESS_PREFERRED),
    )
    plan = VoicingResolver().resolve(request)
    assert plan.root_support == "root_required"
    assert plan.root_included is True
    assert "R" in [note.degree for note in plan.notes]
    assert plan.disposition == "left_root_right_chord"


def test_style_profiles_expose_typed_voicing_policy_not_inline_dict() -> None:
    style = get_style("bossa_nova")
    assert isinstance(style.voicing_policy, VoicingPolicy)
    assert style.voicing_policy.root_support == RootSupportPolicy.ROOTLESS_ALLOWED
    assert style.voicing_policy.allowed_content
