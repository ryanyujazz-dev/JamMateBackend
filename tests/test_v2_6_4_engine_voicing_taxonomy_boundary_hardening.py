from __future__ import annotations

import ast
from pathlib import Path

from jammate_engine.core.voicing import (
    ColorPolicyMode,
    ContentFamily,
    Disposition,
    DispositionFamily,
    FunctionalGrouping,
    OpenProjectionMethod,
    RootSupportPolicy,
    SpreadProjectionMethod,
    VoicingGroupRole,
    VoicingPolicy,
    generate_candidates,
)
from jammate_engine.styles.bossa_nova.voicing_policy import get_voicing_policy as bossa_voicing_policy
from jammate_engine.styles.jazz_ballad.voicing_policy import get_voicing_policy as ballad_voicing_policy
from jammate_engine.styles.medium_swing.voicing_policy import get_voicing_policy as swing_voicing_policy

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ENGINE_VOICING_TAXONOMY_AND_BOUNDARY_HARDENING_V2_6_4.md"


def _imports_from(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _py_files(path: Path) -> list[Path]:
    return [p for p in path.rglob("*.py") if "__pycache__" not in p.parts]


def test_v2_6_4_voicing_taxonomy_doc_exists_and_syncs_with_enum_values() -> None:
    text = DOC.read_text(encoding="utf-8")

    required_axis_tokens = [
        "ContentFamily",
        "RootSupportPolicy",
        "BassRelation",
        "FunctionalGrouping",
        "Disposition",
        "ProjectionMethod",
        "ColorPolicy",
        "Altered dominant",
        "Register",
        "Selector",
        "Voice-leading",
        "VoicingPlan",
    ]
    for token in required_axis_tokens:
        assert token in text

    enum_values = []
    enum_values.extend(item.value for item in ContentFamily)
    enum_values.extend(item.value for item in RootSupportPolicy)
    enum_values.extend(item.value for item in FunctionalGrouping)
    enum_values.extend(item.value for item in VoicingGroupRole)
    enum_values.extend(item.value for item in DispositionFamily)
    enum_values.extend(item.value for item in OpenProjectionMethod)
    enum_values.extend(item.value for item in SpreadProjectionMethod)
    enum_values.extend(item.value for item in ColorPolicyMode)
    for value in enum_values:
        assert value in text

    assert "Pattern       = horizontal pitchless rhythm" in text
    assert "Voicing       = concrete vertical pitch content" in text
    assert "pattern chooses MIDI notes" in text
    assert "MIDI writer repairs bad voicing after the fact" in text


def test_v2_6_4_voicing_core_does_not_import_cross_layer_owners() -> None:
    """Voicing may depend on harmony, but not on style/pattern/expression/MIDI owners."""

    forbidden_prefixes = (
        "jammate_engine.styles",
        "jammate_engine.generation",
        "jammate_engine.realization",
        "jammate_engine.midi",
        "jammate_engine.core.pattern_runtime",
        "jammate_engine.core.expression",
        "jammate_engine.core.anticipation",
    )
    for path in _py_files(ROOT / "src" / "jammate_engine" / "core" / "voicing"):
        imports = _imports_from(path)
        forbidden = [module for module in imports if module.startswith(forbidden_prefixes)]
        assert forbidden == [], f"{path.relative_to(ROOT)} imports cross-layer owners: {forbidden}"


def test_v2_6_4_non_voicing_layers_do_not_import_voicing_selection_internals() -> None:
    """Pattern, anticipation, and expression layers must not make voicing choices."""

    forbidden_exact_or_prefix = (
        "jammate_engine.core.voicing.selection",
        "jammate_engine.core.voicing.sources",
        "jammate_engine.core.voicing.disposition",
        "jammate_engine.core.voicing.runtime.voicing_resolver",
    )
    checked_roots = [
        ROOT / "src" / "jammate_engine" / "core" / "pattern_runtime",
        ROOT / "src" / "jammate_engine" / "core" / "anticipation",
        ROOT / "src" / "jammate_engine" / "core" / "expression",
    ]
    for root in checked_roots:
        for path in _py_files(root):
            imports = _imports_from(path)
            forbidden = [module for module in imports if module.startswith(forbidden_exact_or_prefix)]
            assert forbidden == [], f"{path.relative_to(ROOT)} imports voicing internals: {forbidden}"


def test_v2_6_4_style_patterns_do_not_import_core_voicing_or_concrete_voicing_objects() -> None:
    """Style pattern vocabulary can be pitchless; only style voicing_policy.py owns policy bias."""

    forbidden_modules = (
        "jammate_engine.core.voicing",
        "jammate_engine.core.voicing.selection",
        "jammate_engine.core.voicing.sources",
        "jammate_engine.core.voicing.disposition",
        "jammate_engine.core.voicing.runtime",
    )
    forbidden_source_tokens = [
        "VoicingResolver",
        "VoicingRequest",
        "VoicingPlan",
        "VoicingCandidate",
        "generate_candidates",
        "ContentFamily.",
        "Disposition.",
        "RootSupportPolicy.",
    ]
    for path in _py_files(ROOT / "src" / "jammate_engine" / "styles"):
        if path.name in {"voicing_policy.py", "profile.py", "base.py"}:
            continue
        imports = _imports_from(path)
        forbidden_imports = [module for module in imports if module.startswith(forbidden_modules)]
        assert forbidden_imports == [], f"{path.relative_to(ROOT)} imports voicing policy/selection: {forbidden_imports}"
        if path.name != "gesture_policy.py":
            source = path.read_text(encoding="utf-8")
            forbidden_tokens = [token for token in forbidden_source_tokens if token in source]
            assert forbidden_tokens == [], f"{path.relative_to(ROOT)} contains concrete voicing tokens: {forbidden_tokens}"


def test_v2_6_4_style_voicing_policies_are_policy_only_and_generate_taxonomy_candidates() -> None:
    policies = [swing_voicing_policy(), bossa_voicing_policy(), ballad_voicing_policy()]
    assert all(isinstance(policy, VoicingPolicy) for policy in policies)

    for policy in policies:
        candidates = generate_candidates("Cmaj9", policy)
        assert candidates, policy.metadata.get("style")
        assert any(candidate.content_family is not None for candidate in candidates)
        assert any(candidate.functional_grouping is not None for candidate in candidates)
        assert any(candidate.recipe_id for candidate in candidates)
        assert any("content_recipe" in candidate.metadata for candidate in candidates)
        assert any("register_guard" in candidate.metadata for candidate in candidates)


def test_v2_6_4_disposition_projection_taxonomy_remains_candidate_visible() -> None:
    open_policy = VoicingPolicy(
        preferred_disposition=Disposition.OPEN,
        allowed_dispositions=(Disposition.OPEN,),
        metadata={"open_projection_methods": ["generic_open", "drop2", "drop3", "drop2_and_4"]},
    )
    open_candidates = generate_candidates("G7", open_policy)
    assert open_candidates
    methods = {candidate.metadata.get("disposition_projection_method") for candidate in open_candidates}
    assert {"generic_open", "drop2", "drop3", "drop2_and_4"}.intersection(methods)
    assert all(candidate.disposition == Disposition.OPEN for candidate in open_candidates)

    closed_policy = VoicingPolicy(
        preferred_disposition=Disposition.CLOSED,
        allowed_dispositions=(Disposition.CLOSED,),
        metadata={"strict_closed_compact_pitch_class_layout": True},
    )
    closed_candidates = generate_candidates("Cmaj7", closed_policy)
    assert closed_candidates
    assert all(candidate.disposition == Disposition.CLOSED for candidate in closed_candidates)
    assert any(candidate.metadata.get("disposition_projection_family") == "closed" for candidate in closed_candidates)
