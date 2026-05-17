from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.harmony.harmonic_context import HarmonicContext, classify_functional_motion
from jammate_engine.core.voicing import (
    Disposition,
    DispositionFamily,
    OpenProjectionMethod,
    VOICING_CONTRACT_VERSION,
    VoicingMethodLockMode,
    VoicingMethodLockPattern,
    VoicingPolicy,
    generate_candidates,
    method_lock_scope_plan_from_functional_motion,
    method_lock_scope_plan_from_harmonic_context,
    method_lock_scope_plan_from_symbols,
    method_lock_spec_from_scope_plan,
)


def test_v2_2_12_version_is_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_CONTRACT_VERSION == "v2_2_21"
    assert Path("VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"


def test_method_lock_scope_adapter_reuses_harmonic_context_for_ii_v_i() -> None:
    context = HarmonicContext.from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
    )
    assert context.functional_motion.is_ii_v_i

    plan = method_lock_scope_plan_from_harmonic_context(
        context,
        previous_region_id="bar1_Dm7",
        current_region_id="bar2_G7",
        next_region_id="bar3_Cmaj7",
    )
    debug = plan.to_debug_dict()

    assert plan.enabled is True
    assert plan.pattern == VoicingMethodLockPattern.II_V_I
    assert plan.mode == VoicingMethodLockMode.STRICT
    assert plan.region_ids == ("bar1_Dm7", "bar2_G7", "bar3_Cmaj7")
    assert plan.seed_region_id == "bar1_Dm7"
    assert plan.needs_seed_method is True
    assert debug["contract"] == "harmonic_context_backed_method_lock_scope_adapter_v2_2_14"
    assert debug["source"] == "harmonic_context_adapter"
    assert debug["harmonic_window_type"] == "major_ii_v_i"
    assert "ii_v_i" in debug["functional_motion_tags"]


def test_scope_adapter_prefers_three_chord_scope_over_pair_split() -> None:
    motion = classify_functional_motion(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
    )
    assert motion.previous_to_current_type == "ii_v"
    assert motion.current_to_next_type == "v_i_major"

    plan = method_lock_scope_plan_from_functional_motion(motion)
    assert plan.pattern == VoicingMethodLockPattern.II_V_I
    assert plan.region_ids == ("previous", "current", "next")


def test_scope_adapter_supports_pair_level_ii_v_and_v_i_without_new_recognizer() -> None:
    ii_v = method_lock_scope_plan_from_symbols(chord_symbol="Dm7", next_chord_symbol="G7")
    v_i = method_lock_scope_plan_from_symbols(chord_symbol="G7", next_chord_symbol="Cmaj7")

    assert ii_v.enabled is True
    assert ii_v.pattern == VoicingMethodLockPattern.II_V
    assert ii_v.region_ids == ("current", "next")
    assert v_i.enabled is True
    assert v_i.pattern == VoicingMethodLockPattern.V_I
    assert v_i.region_ids == ("current", "next")


def test_scope_adapter_can_seed_a_runtime_strict_open_drop2_spec_after_seed_selection() -> None:
    plan = method_lock_scope_plan_from_symbols(
        previous_chord_symbol="Dm7",
        chord_symbol="G7",
        next_chord_symbol="Cmaj7",
        previous_region_id="r1",
        current_region_id="r2",
        next_region_id="r3",
    )
    spec = method_lock_spec_from_scope_plan(
        plan,
        family=DispositionFamily.OPEN,
        open_method=OpenProjectionMethod.DROP2,
        locked_from_region_id=plan.seed_region_id,
    )

    assert spec.enabled is True
    assert spec.pattern == VoicingMethodLockPattern.II_V_I
    assert spec.family == DispositionFamily.OPEN
    assert spec.open_method == OpenProjectionMethod.DROP2
    assert spec.locked_from_region_id == "r1"
    assert spec.source == "scope_plan_seed"


def test_candidate_metadata_can_expose_harmonic_context_scope_adapter_without_filtering() -> None:
    policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        preferred_density=4,
        min_density=4,
        max_density=4,
        metadata={
            "auto_method_lock_scope_enabled": True,
            "previous_chord_symbol": "Dm7",
            "next_chord_symbol": "Cmaj7",
            "previous_region_id": "bar1_Dm7",
            "current_region_id": "bar2_G7",
            "next_region_id": "bar3_Cmaj7",
        },
    )
    candidates = generate_candidates("G7", policy)
    assert candidates
    metadata = candidates[0].metadata
    assert metadata["voicing_method_lock_scope_adapter_enabled"] is True
    assert metadata["voicing_method_lock_scope_adapter_pattern"] == "ii_v_i"
    assert metadata["voicing_method_lock_scope_adapter_needs_seed_method"] is True
    assert metadata["voicing_method_lock_scope_adapter_plan"]["source"] == "metadata_harmonic_context_adapter"
    assert metadata["voicing_method_lock_runtime_filtering_enabled"] is False


def test_v2_2_12_docs_record_reuse_not_new_recognizer() -> None:
    docs = Path("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md").read_text(encoding="utf-8")
    harness = Path("docs/DEVELOPMENT_HARNESS_V2.md").read_text(encoding="utf-8")
    assert "v2_2_12" in docs
    assert "HarmonicContext-backed Method Lock Scope Adapter" in docs
    assert "not a new progression recognizer" in docs
    assert "core/harmony/harmonic_context.py" in docs
    assert "Capability Reuse Before New Construction" in harness
