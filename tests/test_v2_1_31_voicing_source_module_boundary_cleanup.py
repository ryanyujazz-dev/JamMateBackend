from __future__ import annotations

from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from jammate_engine.core.voicing import ContentFamily
from jammate_engine.core.voicing.sources.color_permission import (
    ColorPermissionContext,
    build_color_permission_context,
    four_note_color_permission_notes,
    is_half_diminished_like,
)
from jammate_engine.core.voicing.sources.content_planner import plan_content_recipes
from jammate_engine.core.voicing.sources.four_note_sources import (
    degree_order_token,
    functional_source_rotation_options,
    role_order_token,
)
from jammate_engine.core.voicing.runtime.override import VOICING_OVERRIDE_CONTRACT_VERSION
from jammate_engine.core.voicing.policy import ContentFamily, Disposition, RootSupportPolicy, VoicingPolicy
from jammate_engine.core.harmony.chord_parser import parse_chord

ROOT = Path(__file__).resolve().parents[1]


def _policy() -> VoicingPolicy:
    return VoicingPolicy(
        root_support=RootSupportPolicy.ROOTLESS_ALLOWED,
        allowed_content=(ContentFamily.SEVENTH_BASIC, ContentFamily.ROOTED_COLOR, ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B),
        preferred_content=ContentFamily.ROOTLESS_A,
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        min_density=4,
        preferred_density=4,
        max_density=4,
    )


def test_v2_1_37_contract_versions_are_current() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert VOICING_OVERRIDE_CONTRACT_VERSION == "v2_1_43"


def test_v2_1_37_color_permission_boundary_is_extracted_and_still_operational() -> None:
    chord = parse_chord("Cmaj9")
    context = build_color_permission_context(explicit={"9"}, expansion=(), expansion_enabled=False)
    assert isinstance(context, ColorPermissionContext)
    notes = four_note_color_permission_notes(chord, ("3", "5", "7", "9"), context)
    assert "four_note_color_gate_open_explicit_chord_symbol_color" in notes
    assert "chart_color_fidelity_contains_explicit_color" in notes
    assert not is_half_diminished_like(chord)
    assert is_half_diminished_like(parse_chord("Bm7b5"))


def test_v2_1_37_four_note_source_boundary_is_extracted_and_still_operational() -> None:
    assert role_order_token(("root", "third", "fifth", "seventh")) == "root_third_fifth_seventh"
    assert degree_order_token(("b9", "#11")) == "flat9_sharp11"
    options = functional_source_rotation_options(
        source=("R", "3", "5", "7"),
        source_roles=("root", "third", "fifth", "seventh"),
        note_prefix="boundary_test",
        family_notes=("boundary_test_source",),
    )
    assert len(options) == 4
    assert options[0][0][0][0] == "R"
    assert "boundary_test_degree_role_order_root_third_fifth_seventh" in options[0][1]


def test_v2_1_37_content_planner_uses_boundaries_without_behavior_change() -> None:
    recipes = plan_content_recipes("Cmaj9", _policy())
    rootless = [recipe for recipe in recipes if recipe.family in {ContentFamily.ROOTLESS_A, ContentFamily.ROOTLESS_B}]
    assert rootless
    assert any("four_note_allowed_color_set_contract_v2_1_27" in recipe.validity_notes for recipe in rootless)
    assert any("rootless_ab_source_role_order_third_fifth_seventh_ninth" in recipe.validity_notes for recipe in rootless)


def test_v2_1_37_content_planner_no_longer_owns_extracted_helpers() -> None:
    text = (ROOT / "src" / "jammate_engine" / "core" / "voicing" / "sources" / "content_planner.py").read_text(encoding="utf-8")
    assert "class ColorPermissionContext" not in text
    assert "def _four_note_color_permission_notes" not in text
    assert "def _functional_source_rotation_options" not in text
    assert "from .color_permission import" in text
    assert "from .four_note_sources import" in text


def test_v2_1_37_docs_describe_boundary_cleanup() -> None:
    required_docs = [
        ROOT / "README.md",
        ROOT / "agent.md",
        ROOT / "docs" / "VOICING_MODULE_CORE_LOGIC_V2.md",
        ROOT / "docs" / "VOICING_SYSTEM_V2_DESIGN.md",
        ROOT / "docs" / "DEVELOPMENT_TASK_PLAN_V2.md",
    ]
    for path in required_docs:
        text = path.read_text(encoding="utf-8")
        assert "v2_1_37" in text, path
        assert "Voicing Source Module Boundary Cleanup" in text, path
        assert "color_permission.py" in text, path
        assert "four_note_sources.py" in text, path
