from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"HARNESS FAIL: {message}")
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_versions() -> None:
    version = read("VERSION").strip()
    if not re.fullmatch(r"v\d+_\d+_\d+", version):
        fail(f"VERSION has unexpected format: {version!r}")

    pyproject = read("pyproject.toml")
    expected_py = version.removeprefix("v").replace("_", ".")
    if f'version = "{expected_py}"' not in pyproject:
        fail(f"pyproject.toml version does not match {version}")

    api_version = read("src/jammate_engine/api/version.py")
    if f'ENGINE_VERSION_TAG = "{version}"' not in api_version:
        fail("api/version.py ENGINE_VERSION_TAG does not match VERSION")

    agent = read("agent.md")
    if version not in agent:
        fail("agent.md does not mention active VERSION")

    readme = read("README.md")
    if version not in readme:
        fail("README.md does not mention active VERSION")


def check_runtime_uses_central_version_tag() -> None:
    rel = "src/jammate_engine/runtime/engine_runtime.py"
    text = read(rel)
    if "ENGINE_VERSION_TAG" not in text:
        fail(f"{rel} must use centralized ENGINE_VERSION_TAG")
    if re.search(r'version\s*=\s*["\']v\d+_\d+_\d+["\']', text):
        fail(f"{rel} must not hardcode GenerationResult.version")


def check_required_docs() -> None:
    required = [
        "docs/PRD_V2.md",
        "docs/ARCHITECTURE_V2.md",
        "docs/PIPELINE_V2.md",
        "docs/SYSTEM_CONTRACTS_V2.md",
        "docs/API_CONTRACT_V2.md",
        "docs/GENERATION_RULES_SUMMARY_V2.md",
        "docs/STYLE_RULE_BASELINE_V2.md",
        "docs/STYLE_TUNING_ENTRY_POINT_V2.md",
        "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
        "docs/FUTURE_IDEAS_BACKLOG_V2.md",
        "docs/VOICING_MODULE_FILE_AUDIT_V2.md",
        "docs/PROJECT_DOCUMENTATION_AUDIT_V2.md",
        "docs/CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md",
        "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
        "docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing required doc: {rel}")


def check_future_ideas_backlog_habit_documented() -> None:
    required_phrase = "Future Ideas Backlog"
    targets = ["agent.md", "docs/DEVELOPMENT_HARNESS_V2.md", "docs/FUTURE_IDEAS_BACKLOG_V2.md"]
    for rel in targets:
        text = read(rel)
        if required_phrase not in text and "FUTURE_IDEAS_BACKLOG_V2" not in text:
            fail(f"{rel} must document the future-ideas backlog habit")


def check_block_chord_runtime_name() -> None:
    allowed_patterns = ("block_harmonization", "locked_hands", "traditional block", "block-chord")
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "block_chord" in text and not any(token in text for token in allowed_patterns):
            fail(f"runtime source appears to use block_chord instead of simultaneous_onset: {path.relative_to(ROOT)}")


def check_styles_do_not_emit_note_events() -> None:
    styles_root = ROOT / "src" / "jammate_engine" / "styles"
    forbidden = ("NoteEvent", "note_on", "note_off")
    for path in styles_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                fail(f"style file contains forbidden realization/MIDI token {token!r}: {path.relative_to(ROOT)}")


def check_core_pattern_runtime_has_no_style_libraries() -> None:
    pattern_root = ROOT / "src" / "jammate_engine" / "core" / "pattern_runtime"
    forbidden_names = ("bossa", "swing", "ballad", "latin", "funk", "rock", "pop")
    for path in pattern_root.rglob("*.py"):
        lower = path.name.lower()
        if any(name in lower for name in forbidden_names):
            fail(f"core/pattern_runtime contains style-named file: {path.relative_to(ROOT)}")


def check_piano_lh_bass_uses_shared_degree_resolver() -> None:
    rel = "src/jammate_engine/realization/piano_lh_bass_foundation_realizer.py"
    text = read(rel)
    required = ("resolve_bass_degree_token", "pitch_class_to_register_note")
    for token in required:
        if token not in text:
            fail(f"{rel} must use shared bass degree resolver token {token}")
    if 'degree == "root"' in text or "+ 7) % 12" in text:
        fail(f"{rel} appears to reimplement root/fifth degree parsing locally")


def check_no_bass_r_token_regression_test_exists() -> None:
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    required_tokens = ["R_as_root", 'metadata={"degree": "R"}', "% 12 == 0"]
    for token in required_tokens:
        if token not in tests:
            fail("missing regression test proving piano LH bass degree 'R' resolves to root")


def check_minimal_file_split_principle_documented() -> None:
    required_phrase = "Minimal File Split Principle"
    required_targets = [
        "agent.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
    ]
    for rel in required_targets:
        if required_phrase not in read(rel):
            fail(f"{rel} must document the Minimal File Split Principle")



def check_capability_reuse_before_new_construction_documented() -> None:
    required_phrase = "Capability Reuse Before New Construction"
    required_targets = [
        "agent.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/NEW_FILE_PLACEMENT_GUIDE_V2.md",
    ]
    for rel in required_targets:
        text = read(rel)
        if required_phrase not in text:
            fail(f"{rel} must document the Capability Reuse Before New Construction rule")
        for token in (
            "reuse audit",
            "local implementation",
            "adapter",
            "facade",
            "metadata",
            "core/harmony/harmonic_context.py",
        ):
            if token not in text:
                fail(f"{rel} capability-reuse rule is missing token: {token}")



def check_voicing_texture_state_architecture_documented() -> None:
    required_targets = [
        "agent.md",
        "README.md",
        "docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md",
        "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        "docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md",
        "docs/VOICING_SYSTEM_V2_DESIGN.md",
    ]
    required_tokens = [
        "VoicingTextureIntent",
        "VoicingTextureState",
        "LLM",
        "texture_plan.py",
        "family",
        "method lock",
        "Disposition Projection",
        "Capability Reuse Before New Construction",
    ]
    for rel in required_targets:
        text = read(rel)
        for token in required_tokens:
            if token not in text:
                fail(f"{rel} must document VoicingTextureState architecture token: {token}")



def check_voicing_texture_intent_state_contract_documented_and_tested() -> None:
    docs = (
        read("agent.md")
        + read("README.md")
        + read("docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md")
        + read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
    )
    for token in (
        "v2_2_21 update — VoicingTextureIntent / VoicingTextureState Contract Planning Pass",
        "derive_voicing_texture_intent",
        "derive_voicing_texture_state",
        "voicing_texture_state_engine_resolved_contract_v2_2_21",
        "default listening behavior unchanged",
        "the next engineering target should be selected by the user",
    ):
        if token not in docs:
            fail(f"v2_2_21 texture intent/state contract docs missing token: {token}")

    texture_plan = read("src/jammate_engine/core/voicing/runtime/texture_plan.py")
    for token in (
        "class VoicingTextureIntent",
        "class VoicingTextureState",
        "derive_voicing_texture_intent",
        "derive_voicing_texture_state",
        "VoicingTextureFamilySwitchPolicy",
        "VoicingTextureMethodUniformity",
    ):
        if token not in texture_plan:
            fail(f"texture_plan.py missing v2_2_21 contract token: {token}")

    candidate_generator = read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    for token in (
        "derive_voicing_texture_state",
        "voicing_texture_state",
        "voicing_texture_state_primary_family",
    ):
        if token not in candidate_generator:
            fail(f"candidate_generator.py missing v2_2_21 texture-state metadata token: {token}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_21_voicing_texture_intent_state_contract" not in tests or "voicing_texture_state_engine_resolved_contract_v2_2_21" not in tests:
        fail("missing v2_2_21 texture intent/state contract regression test")


def check_current_architecture_tree_documented() -> None:
    required_phrase = "CURRENT_PROJECT_ARCHITECTURE_TREE"
    required_targets = ["docs/ARCHITECTURE_V2.md", "docs/DEVELOPMENT_HARNESS_V2.md"]
    required_current_paths = [
        "generation/",
        "realization/",
        "midi/",
        "bass_foundation/",
        "generator.py",
        "audit.py",
        "policy.py",
        "rules.py",
        "styles/medium_swing",
        "bass_foundation_patterns.py",
        "vocabulary/melodic_foreground",
    ]
    for rel in required_targets:
        text = read(rel)
        if required_phrase not in text:
            fail(f"{rel} must include the current architecture tree")
        for token in required_current_paths:
            if token not in text:
                fail(f"{rel} architecture tree is missing current path token: {token}")
        if "#" not in text:
            fail(f"{rel} architecture tree must include short Chinese comments")


def check_target_architecture_base_alignment() -> None:
    styles_root = ROOT / "src" / "jammate_engine" / "styles"
    forbidden_style_files = {"piano_patterns.py", "bass_patterns.py", "drum_patterns.py"}
    for path in styles_root.rglob("*.py"):
        if path.name in forbidden_style_files:
            fail(f"style pattern file still uses instrument-first name: {path.relative_to(ROOT)}")

    required_style_files = ("comping_patterns.py", "bass_foundation_patterns.py", "percussion_patterns.py")
    for style_dir in (styles_root / "medium_swing", styles_root / "bossa_nova", styles_root / "jazz_ballad"):
        for filename in required_style_files:
            if not (style_dir / filename).exists():
                fail(f"missing generation-domain style pattern file: {(style_dir / filename).relative_to(ROOT)}")

    if (ROOT / "src" / "jammate_engine" / "core" / "ensemble").exists():
        fail("core/ensemble should not exist after role-system alignment; use core/roles")

    for dirname in ("generation", "realization", "midi"):
        if not (ROOT / "src" / "jammate_engine" / dirname).exists():
            fail(f"root-level {dirname}/ folder is required under src/jammate_engine")
        if (ROOT / "src" / "jammate_engine" / "core" / dirname).exists():
            fail(f"core/{dirname} should not exist after root-level architecture alignment")

    source_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    if "jammate_engine.core.ensemble" in source_text:
        fail("runtime source still imports jammate_engine.core.ensemble")
    for old_import in ("jammate_engine.core.generation", "jammate_engine.core.realization", "jammate_engine.core.midi"):
        if old_import in source_text:
            fail(f"runtime source still imports {old_import}; use root-level package")
    if "BassRealizer" in source_text or "DrumRealizer" in source_text:
        fail("runtime source still uses pre-domain realizer class names")


def check_vocabulary_is_solo_only() -> None:
    vocab_root = ROOT / "src" / "jammate_engine" / "vocabulary"
    if not vocab_root.exists():
        return
    forbidden_dirs = {"comping", "bass_foundation", "percussion", "fills", "fill"}
    for path in vocab_root.iterdir():
        if path.is_dir() and path.name in forbidden_dirs:
            fail(f"vocabulary/ is solo-only; accompaniment vocabulary directory is forbidden: {path.relative_to(ROOT)}")
    if not (vocab_root / "melodic_foreground").exists():
        fail("vocabulary/ must remain scoped to melodic_foreground when it exists")



def check_bass_foundation_span_guard_documented_and_tested() -> None:
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    if "max_region_span" not in generation:
        fail("BassFoundation generation must enforce max_region_span for one-octave chord-region bass lines")
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    if "max_region_span=12" not in docs and "max_region_span`" not in docs:
        fail("BassFoundation one-octave region span guard must be documented")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "one_octave" not in tests and "max_region_span" not in tests:
        fail("missing regression test for BassFoundation one-octave region span guard")


def check_bass_foundation_classic_fill_guard() -> None:
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    patterns = read("src/jammate_engine/styles/medium_swing/bass_foundation_patterns.py")
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    required_generation_tokens = ["classic_fill_enabled", "_try_generate_classic_fill", "classic_fill_scene", "max_region_span"]
    for token in required_generation_tokens:
        if token not in generation:
            fail(f"BassFoundation classic fill generation guard missing token: {token}")
    if "CF_TWO_BAR_TONIC_01" not in patterns or "bass_foundation_fill_scene" not in patterns:
        fail("Medium Swing classic fill candidate must be scene-triggered in bass_foundation_patterns.py")
    if "CF_TWO_BAR_TONIC_01" not in docs or "scene-triggered" not in docs:
        fail("BassFoundation classic fill contract must be documented")
    if "CF_TWO_BAR_TONIC_01" not in tests or "classic_fill_triggered" not in tests:
        fail("missing regression test for scene-triggered Classic BassFoundation fill")


def check_bass_foundation_root_echo_swing_upbeat_guard() -> None:
    patterns = read("src/jammate_engine/styles/medium_swing/bass_foundation_patterns.py")
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    render_pipeline = read("src/jammate_engine/midi/render_pipeline.py")
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "(0.5, 2.5)" not in patterns:
        fail("Medium Swing root echo must be written on logical grid upbeats 0.5 / 2.5")
    if "0.6667" in patterns or "2.6667" in patterns:
        fail("Style/generation patterns must not hardcode performed swing timing; use logical .5 grid")
    if "root_anchor_note" not in generation or "root_echo_same_as_region_root" not in generation:
        fail("BassFoundation root echo must keep the exact region-root note, not nearest re-octavized root")
    if "timing_intent" not in generation or "root_echo_swing_upbeat" not in generation:
        fail("BassFoundation root echo debug must mark logical swing-upbeat placement and timing intent")
    for token in ("apply_timing_policy", "performed_beat", "straight_even", "swing_upbeat"):
        if token not in render_pipeline:
            fail(f"render pipeline must implement timing-grid resolver token: {token}")
    if "logical grid" not in docs or "same current-root note" not in docs or "timing_intent" not in docs:
        fail("BassFoundation logical-grid same-root DI/root echo contract must be documented")
    if "test_root_echo_uses_logical_swing_upbeat_and_exact_region_root_note" not in tests:
        fail("missing regression test for logical-grid same-root DI/root echo")
    if "test_medium_swing_timing_policy_swings_logical_half_beats" not in tests:
        fail("missing regression test for render-level swing timing grid resolver")


def check_bass_foundation_audit_report_guard() -> None:
    generation_audit = read("src/jammate_engine/generation/bass_foundation/audit.py")
    script = read("examples/scripts/generate_bass_foundation_audit_report.py")
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/PIPELINE_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    for token in ("build_bass_foundation_audit", "format_bass_foundation_audit_report", "Region Decision Trace", "Root echo same-root violations"):
        if token not in generation_audit:
            fail(f"BassFoundation audit formatter missing token: {token}")
    for token in ("ENGINE_VERSION_TAG", "bass_foundation_audit_report.md", "bass_foundation_audit_trace.json"):
        if token not in script:
            fail(f"BassFoundation audit script missing versioned output token: {token}")
    if "BassFoundation Musicality Audit" not in docs or "Region Decision Trace" not in docs:
        fail("BassFoundation audit contract must be documented")
    if "test_bass_foundation_audit_report_contains_region_decision_trace" not in tests:
        fail("missing regression test for BassFoundation audit report")



def check_bass_foundation_musicality_tuning_guard() -> None:
    patterns = read("src/jammate_engine/styles/medium_swing/bass_foundation_patterns.py")
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_TASK_PLAN_V2.md") + read("agent.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    required_pattern_tokens = [
        "root_echo_probability",
        "root_echo_compact_probability_multiplier",
        "classic_fill_min_gap_regions",
        "scale_near_nextR",
    ]
    for token in required_pattern_tokens:
        if token not in patterns:
            fail(f"Medium Swing BassFoundation tuning policy missing token: {token}")
    if "_weighted_instance_choice" not in generation:
        fail("BassFoundation generation must keep the non-legacy optional in-lane weighted helper for future policies")
    for forbidden in ("_apply_register_gravity_lane_caps", "high_zone_upper_lane_cap", "very_high_zone_upper_lane_cap"):
        if forbidden in patterns or forbidden in generation:
            fail(f"temporary V2 register-gravity cap token must not return after old-engine skeleton alignment: {forbidden}")
    for token in ("root echo density", "scale_near_nextR", "old-engine lane weighting"):
        if token not in docs:
            fail(f"BassFoundation musicality/alignment contract must document: {token}")
    if "test_medium_swing_bass_foundation_tuning_policy_is_conservative" not in tests:
        fail("missing regression test for BassFoundation musicality tuning policy")


def check_bass_foundation_three_beat_alignment_guard() -> None:
    patterns = read("src/jammate_engine/styles/medium_swing/bass_foundation_patterns.py")
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    audit = read("src/jammate_engine/generation/bass_foundation/audit.py")
    docs = read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_TASK_PLAN_V2.md") + read("agent.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    required_pattern_tokens = [
        "THREE_BEAT_SKELETONS",
        "C03_R_R_Fifth",
        "C05_R_R_Third",
        "C11_R_R_Seventh",
        '"scale_near_nextR": 40.0',
        '"approach_nextR": 40.0',
        '"dominant_connection": 10.0',
        '"lane_instance_selection": "legacy_random"',
    ]
    for token in required_pattern_tokens:
        if token not in patterns:
            fail(f"Medium Swing BassFoundation old-engine three-beat alignment missing token: {token}")
    for token in ("repeated_root_exact", "repeated_root_notes", "legacy_random", "candidate_preflight", "old_engine_legal_skeleton_pool"):
        if token not in generation:
            fail(f"BassFoundation generation missing repeated-root/legacy lane/preflight alignment token: {token}")
    for token in ("repeated_root_violations", "R-R-starting skeletons"):
        if token not in audit:
            fail(f"BassFoundation audit missing repeated-root exactness token: {token}")
    for token in ("ThreeBeatSkeleton", "R-R-*", "40 : 40 : 10", "legacy random"):
        if token not in docs:
            fail(f"BassFoundation three-beat alignment contract must document: {token}")
    for token in (
        "test_repeated_root_start_keeps_exact_same_root_note",
        "test_three_beat_skeleton_table_exactly_matches_old_engine_weights",
        "test_lane_weights_are_old_engine_table_times_degree_multipliers_without_caps",
        "test_candidate_preflight_filters_illegal_skeletons_before_weighted_choice",
    ):
        if token not in tests:
            fail(f"missing regression test for old-engine BassFoundation skeleton alignment: {token}")


def check_generation_rules_summary_guard() -> None:
    doc = read("docs/GENERATION_RULES_SUMMARY_V2.md")
    harness = read("docs/DEVELOPMENT_HARNESS_V2.md") + read("agent.md")
    required_doc_tokens = [
        "生成规则梳理总结",
        "Medium Swing / BassFoundation",
        "ThreeBeatSkeleton",
        "Five-zone register model",
        "Seventh Bias Audit",
        "Target Continuity Audit",
        "代码落位",
    ]
    for token in required_doc_tokens:
        if token not in doc:
            fail(f"GENERATION_RULES_SUMMARY_V2.md must document generation rule token: {token}")
    for token in ("Generation Rule Documentation Principle", "GENERATION_RULES_SUMMARY_V2.md", "生成规则"):
        if token not in harness:
            fail(f"development harness must require generation-rule documentation token: {token}")


def check_bass_foundation_target_continuity_guard() -> None:
    generation = (
        read("src/jammate_engine/generation/bass_foundation/generator.py")
        + read("src/jammate_engine/generation/bass_foundation/policy.py")
        + read("src/jammate_engine/generation/bass_foundation/rules.py")
    )
    audit = read("src/jammate_engine/generation/bass_foundation/audit.py")
    docs = read("docs/GENERATION_RULES_SUMMARY_V2.md") + read("docs/SYSTEM_CONTRACTS_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    for token in ("target_continuity_enabled", "inherited_previous_target_nextR_note", "target_nextR_note", "previous_target_nextR_note"):
        if token not in generation:
            fail(f"BassFoundation target continuity missing generation token: {token}")
    for token in ("Seventh Bias Audit", "Target Continuity Audit", "seventh_lower_lane_ratio", "target_continuity_mismatches"):
        if token not in audit:
            fail(f"BassFoundation audit missing target-continuity/seventh-bias token: {token}")
    for token in ("target-to-target", "target_nextR_note", "Seventh lower-lane", "Target Continuity Audit"):
        if token not in docs:
            fail(f"BassFoundation target continuity / Seventh bias contract must be documented: {token}")
    for token in ("test_bass_foundation_inherits_previous_target_nextR_note", "test_bass_foundation_audit_reports_seventh_bias_and_target_continuity"):
        if token not in tests:
            fail(f"missing regression test for BassFoundation target continuity / Seventh audit: {token}")


def check_bass_foundation_rule_organization_guard() -> None:
    package_root = ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation"
    required = ["__init__.py", "policy.py", "models.py", "rules.py", "generator.py", "audit.py"]
    for filename in required:
        if not (package_root / filename).exists():
            fail(f"BassFoundation generation package missing organized module: {package_root / filename}")
    for old_flat in (
        ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation_generation.py",
        ROOT / "src" / "jammate_engine" / "generation" / "bass_foundation_audit.py",
    ):
        if old_flat.exists():
            fail(f"BassFoundation rules should be organized under generation/bass_foundation/, not flat file: {old_flat.relative_to(ROOT)}")
    docs = read("docs/ARCHITECTURE_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md") + read("docs/GENERATION_RULES_SUMMARY_V2.md")
    for token in ("generation/bass_foundation/", "policy.py", "rules.py", "generator.py", "audit.py", "BassFoundation 规则包"):
        if token not in docs:
            fail(f"BassFoundation rule organization must be documented with token: {token}")
    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_bass_foundation_runtime_rules_are_organized_as_domain_package" not in tests:
        fail("missing regression test for BassFoundation rule package organization")


def check_style_baseline_docs_guard() -> None:
    baseline = read("docs/STYLE_RULE_BASELINE_V2.md")
    entry = read("docs/STYLE_TUNING_ENTRY_POINT_V2.md")
    docs = baseline + entry + read("docs/DEVELOPMENT_TASK_PLAN_V2.md") + read("agent.md")
    for token in (
        "Medium Swing Piano Baseline",
        "Bossa Nova Piano Baseline",
        "Jazz Ballad Piano Baseline",
        "v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1",
        "piano musical audit",
        "expression audit",
    ):
        if token not in docs:
            fail(f"style baseline / tuning entry docs must contain token: {token}")



def check_three_note_closed_listening_verification_documented() -> None:
    required = [
        "examples/scripts/generate_3note_closed_listening_verification_demos.py",
        "examples/leadsheets/three_note_closed_source_stress.json",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing v2_1_40 3-note closed listening verification asset: {rel}")
    docs = read("agent.md") + read("docs/DEVELOPMENT_HARNESS_V2.md") + read("docs/VOICING_TUNING_WORKFLOW_V2.md")
    required_phrases = [
        "3-note closed listening verification",
        "root-third-fifth",
        "per-source nearest",
        "no-seventh symbols use real triad/add/sus sources",
    ]
    for phrase in required_phrases:
        if phrase not in docs:
            fail(f"v2_1_40 docs must mention: {phrase}")



def check_four_note_triad_closed_sync_documented() -> None:
    docs = read("agent.md") + read("docs/DEVELOPMENT_HARNESS_V2.md") + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
    required_phrases = [
        "4-Note Triad-Aware Closed Source Sync",
        "1351",
        "3513",
        "5135",
        "sus2, density=4, closed",
        "closed register floor down by a major third",
        "F3 / MIDI 53",
    ]
    for phrase in required_phrases:
        if phrase not in docs:
            fail(f"v2_1_42 docs must mention: {phrase}")


def check_voicing_source_balance_cleanup_documented() -> None:
    source = read("src/jammate_engine/core/voicing/sources/source_balance.py")
    if "SOURCE_BALANCE_CONTRACT_VERSION = \"v2_1_43\"" not in source:
        fail("source_balance.py must expose the v2_1_43 source balance contract")
    docs = read("docs/VOICING_MODULE_FILE_AUDIT_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md") + read("agent.md")
    required = ["source_balance.py", "No new subfolder", "Minimal File Split Principle"]
    for token in required:
        if token not in docs:
            fail(f"voicing source-balance cleanup docs missing token: {token}")


def check_project_documentation_audit_guard() -> None:
    rel = "docs/PROJECT_DOCUMENTATION_AUDIT_V2.md"
    text = read(rel)
    required = [
        "Source-of-truth matrix",
        "Documentation update policy",
        "Canonical reading path",
        "No new docs subfolder is needed",
        "v2_1_44",
    ]
    for token in required:
        if token not in text:
            fail(f"{rel} missing project documentation audit token: {token}")
    harness = read("docs/DEVELOPMENT_HARNESS_V2.md") + read("agent.md")
    if "PROJECT_DOCUMENTATION_AUDIT_V2.md" not in harness:
        fail("agent/harness docs must mention PROJECT_DOCUMENTATION_AUDIT_V2.md")


def check_closed_34note_baseline_smoke_documented() -> None:
    rel = "docs/CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md"
    text = read(rel)
    required = [
        "closed legality filter",
        "per-source nearest-motion realization",
        "F3 / MIDI 53",
        "1351 / 3513 / 5135",
        "v2_2_1 — Disposition Projection Entry Pass",
    ]
    for token in required:
        if token not in text:
            fail(f"{rel} missing closed baseline / pre-disposition token: {token}")
    script_rel = "examples/scripts/generate_closed_34note_baseline_smoke_listening.py"
    if not (ROOT / script_rel).exists():
        fail(f"missing v2_1_45 combined closed 3/4-note smoke script: {script_rel}")
    script = read(script_rel)
    for token in (
        "generate_3note_closed_listening_verification_demos.py",
        "generate_4note_source_weight_listening_verification_demos.py",
        "generate_4note_triad_closed_listening_verification_demos.py",
        "closed_34note_baseline_smoke_summary",
    ):
        if token not in script:
            fail(f"{script_rel} missing smoke token: {token}")
    docs = read("agent.md") + read("docs/DEVELOPMENT_HARNESS_V2.md") + read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
    for token in ("generate_closed_34note_baseline_smoke_listening.py", "CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md"):
        if token not in docs:
            fail(f"agent/task/harness docs must mention v2_1_45 closed baseline token: {token}")


def check_disposition_projection_taxonomy_documented() -> None:
    docs = read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
    required = [
        "DispositionFamily",
        "OpenProjectionMethod",
        "SpreadProjectionMethod",
        "DROP2",
        "legacy Disposition",
        "resolver migration is not part of v2_2_x",
        "project_source_to_disposition()",
        "DispositionProjectionResult",
        "v2_2_2 — Closed Projection Migration / No Behavior Change",
    ]
    for token in required:
        if token not in docs:
            fail(f"DISPOSITION_PROJECTION_ARCHITECTURE_V2.md missing token: {token}")

    models = read("src/jammate_engine/core/voicing/disposition/models.py")
    for token in ("DispositionFamily", "OpenProjectionMethod", "SpreadProjectionMethod", "LEGACY_DISPOSITION_PROJECTION_MAP", "DispositionProjectionResult"):
        if token not in models:
            fail(f"core/voicing/disposition/models.py missing token: {token}")

    projection = read("src/jammate_engine/core/voicing/disposition/projection.py")
    for token in ("project_source_to_disposition", "legacy_placement_callback", "legacy_projection_cleanup_required"):
        if token not in projection:
            fail(f"core/voicing/disposition/projection.py missing token: {token}")

    candidate_generator = read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    for token in ("project_source_to_disposition", "disposition_projection_family", "legacy_projection_callback_used"):
        if token not in candidate_generator:
            fail(f"candidate_generator.py must route candidates through projection entry token: {token}")


def check_closed_projection_migration_documented_and_tested() -> None:
    docs = read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md") + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    required_docs = [
        "v2_2_2 — Closed Projection Migration / No Behavior Change",
        "src/jammate_engine/core/voicing/disposition/closed.py",
        "place_compact_closed_seed_layout",
        "strict_closed_register_variants",
        "closed_projection_migrated",
        "v2_2_3 — Legacy Disposition Cleanup Pass",
    ]
    for token in required_docs:
        if token not in docs:
            fail(f"v2_2_2 closed projection migration docs missing token: {token}")

    closed = read("src/jammate_engine/core/voicing/disposition/closed.py")
    for token in ("place_compact_closed_seed_layout", "strict_closed_register_variants", "effective_closed_register_low"):
        if token not in closed:
            fail(f"closed.py missing migrated closed projection token: {token}")

    candidate_generator = read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    for forbidden in ("def _place_closed_pitch_class_seed_layout", "def _strict_closed_register_variants"):
        if forbidden in candidate_generator:
            fail(f"candidate_generator.py still owns migrated strict closed algorithm: {forbidden}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_2_closed_projection_migration" not in tests or "closed_projection_migrated" not in tests:
        fail("missing v2_2_2 closed projection migration regression test")


def check_legacy_disposition_cleanup_documented_and_tested() -> None:
    docs = read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md") + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md") + read("docs/DEVELOPMENT_HARNESS_V2.md")
    required_docs = [
        "v2_2_3 — Legacy Disposition Cleanup Pass",
        "src/jammate_engine/core/voicing/disposition/open.py",
        "src/jammate_engine/core/voicing/disposition/spread.py",
        "src/jammate_engine/core/voicing/disposition/placement_utils.py",
        "disposition/facade.py is now only a placement facade",
        "v2_2_4 — Open Projection Skeleton / DROP2 4-note Only",
    ]
    for token in required_docs:
        if token not in docs:
            fail(f"v2_2_3 legacy disposition cleanup docs missing token: {token}")

    disposition_facade = read("src/jammate_engine/core/voicing/disposition/facade.py")
    for forbidden in (
        "def _degree_to_note",
        "def _place_stack",
        "def _place_spread",
        "def _place_left_root_right_chord",
        "def _place_open_root_10th",
        "def _dedupe_by_note",
    ):
        if forbidden in disposition_facade:
            fail(f"disposition/facade.py still owns old placement algorithm: {forbidden}")
    for token in (
        "place_generic_open_projection",
        "place_lower_upper_grouped_projection",
        "place_foundation_projection",
        "place_root_10th_projection",
        "placement_facade_and_debug_contract",
    ):
        if token not in disposition_facade:
            fail(f"disposition/facade.py missing new delegation token: {token}")

    for rel, tokens in {
        "src/jammate_engine/core/voicing/disposition/open.py": ["place_generic_open_projection"],
        "src/jammate_engine/core/voicing/disposition/spread.py": ["place_lower_upper_grouped_projection", "place_foundation_projection", "place_root_10th_projection"],
        "src/jammate_engine/core/voicing/disposition/placement_utils.py": ["degree_to_note", "place_stack", "dedupe_by_note"],
    }.items():
        text = read(rel)
        for token in tokens:
            if token not in text:
                fail(f"{rel} missing v2_2_3 cleanup token: {token}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_3_legacy_disposition_cleanup" not in tests or "placement_algorithm_owner" not in tests:
        fail("missing v2_2_3 legacy disposition cleanup regression test")



def check_drop2_parent_closed_projection_documented_and_tested() -> None:
    docs = (
        read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
        + read("docs/DEVELOPMENT_HARNESS_V2.md")
    )
    for token in (
        "v2_2_5 update — DROP2 Parent-Closed Projection Correction Pass",
        "place_drop2_projection_from_closed_parent",
        "open_drop2_parent_closed_notes",
        "not from a direct source-order compact stack",
    ):
        if token not in docs:
            fail(f"v2_2_5 DROP2 parent-closed correction docs missing token: {token}")

    open_projection = read("src/jammate_engine/core/voicing/disposition/open.py")
    for token in (
        "place_drop2_projection_from_closed_parent",
        "parent_closed",
        "place_named_open_projection_from_closed_parent",
        "open_drop2_from_parent_closed_projection",
    ):
        if token not in open_projection:
            fail(f"open.py missing parent-closed DROP2 token: {token}")
    if "_ordered_offsets_from_source" in open_projection:
        fail("DROP2 must not rebuild a compact stack directly from ordered source offsets")

    projection = read("src/jammate_engine/core/voicing/disposition/projection.py")
    if "closed_parent_placement_callback" not in projection:
        fail("DROP2 projection entry must accept a closed_parent_placement_callback")

    candidate_generator = read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    if "_project_closed_parent_for_drop2" not in candidate_generator:
        fail("candidate_generator must route DROP2 parent through the CLOSED projection entry")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_5_drop2_parent_closed_projection" not in tests or "open_drop2_parent_closed_notes" not in tests:
        fail("missing v2_2_5 DROP2 parent-closed correction regression test")


def check_open_method_candidate_pool_documented_and_tested() -> None:
    docs = (
        read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
        + read("docs/DEVELOPMENT_HARNESS_V2.md")
    )
    for token in (
        "v2_2_7 update — OPEN Method Candidate Pool / DROP3-DROP2&4 Skeleton Pass",
        "Progression / Phrase-level Voicing Method Lock",
        "open_projection_method_pool",
        "DROP3",
        "DROP2_AND_4",
    ):
        if token not in docs:
            fail(f"v2_2_7 OPEN method candidate pool docs missing token: {token}")

    open_projection = read("src/jammate_engine/core/voicing/disposition/open.py")
    for token in (
        "place_drop3_projection_from_closed_parent",
        "place_drop2_and_4_projection_from_closed_parent",
        "place_named_open_projection_from_closed_parent",
    ):
        if token not in open_projection:
            fail(f"open.py missing v2_2_7 named OPEN method token: {token}")

    candidate_generator = read("src/jammate_engine/core/voicing/selection/candidate_generator.py")
    for token in (
        "open_projection_method_pool_from_metadata",
        "active_open_projection_method",
        "open_projection_method_pool_enabled",
    ):
        if token not in candidate_generator:
            fail(f"candidate_generator.py missing v2_2_7 OPEN pool token: {token}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_7_open_method_candidate_pool" not in tests or "drop2_and_4" not in tests:
        fail("missing v2_2_7 OPEN method candidate pool regression test")




def check_agent_delivery_workflow_documented() -> None:
    text = read("agent.md")
    for token in (
        "Development delivery workflow rule",
        "Do not output a continuation development document by default",
        "only when the user explicitly asks",
        "current standard-tune listening demo",
        "All the Things You Are",
        "Runtime generation logic is unchanged",
    ):
        if token not in text:
            fail(f"agent.md missing delivery workflow token: {token}")


def check_documentation_compaction_pass() -> None:
    agent = read("agent.md")
    if len(agent.splitlines()) >= 180:
        fail("agent.md should remain compact after documentation compression pass")
    for forbidden in (
        "v2_1_4 — Rooted Foundation Component Classification Correction",
        "Recommended next task: `v2_2_22 — Medium Swing OPEN Texture State Runtime Pilot`",
    ):
        docs = agent + read("README.md") + "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "docs").glob("*.md"))
        if forbidden in docs:
            fail(f"stale documentation token must not remain active: {forbidden}")
    for path in (ROOT / "docs").glob("*.md"):
        if len(path.read_text(encoding="utf-8").splitlines()) >= 220:
            fail(f"documentation file should remain compact: {path.relative_to(ROOT)}")



def check_spread_voicing_notes_recipe_plan_documented() -> None:
    docs = (
        read("agent.md")
        + read("README.md")
        + read("docs/VOICING_SYSTEM_V2_DESIGN.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
        + read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
        + read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
    )
    for token in (
        "SPREAD notes",
        "lower functional group + upper source/projection group",
        "1-note lower",
        "root only",
        "root+3",
        "root+7+upper3",
        "root+5+upper3",
        "1+4",
        "DROP2/DROP3",
        "not directly reuse a final placed closed/open voicing result",
        "notes-only",
        "expression",
        "lower/upper group-wise voice leading",
    ):
        if token not in docs:
            fail(f"SPREAD notes recipe plan missing token: {token}")



def check_spread_recipe_reuse_contract_documented_and_tested() -> None:
    docs = (
        read("agent.md")
        + read("README.md")
        + read("docs/VOICING_SYSTEM_V2_DESIGN.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
        + read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
        + read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
        + read("docs/DEVELOPMENT_HARNESS_V2.md")
    )
    for token in (
        "Spread Recipe Reuse Audit + Contract Skeleton",
        "SPREAD_RECIPE_CONTRACT_VERSION",
        "SpreadRecipeContract",
        "LowerGroupRecipeContract",
        "UpperSourceRef",
        "SpreadReuseAuditItem",
        "spread_recipe_reuse_audit",
        "spread_recipe_contract_skeleton",
        "source/orientation/projection",
        "final placed closed/open",
        "notes-only",
    ):
        if token not in docs:
            fail(f"v2_2_38 SPREAD reuse contract docs missing token: {token}")

    spread = read("src/jammate_engine/core/voicing/disposition/spread.py")
    for token in (
        "SPREAD_RECIPE_CONTRACT_VERSION",
        "class SpreadGrouping",
        "class LowerGroupRecipeContract",
        "class UpperSourceRef",
        "class SpreadRecipeContract",
        "class SpreadReuseAuditItem",
        "def spread_recipe_reuse_audit",
        "def spread_recipe_contract_skeleton",
        "final_placed_result_reuse_allowed",
    ):
        if token not in spread:
            fail(f"spread.py missing v2_2_38 contract token: {token}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_38_spread_recipe_reuse_contract" not in tests or "final_closed_or_open_voicing_candidate" not in tests:
        fail("missing v2_2_38 SPREAD reuse contract regression test")


def check_basic_spread_projection_documented_and_tested() -> None:
    docs = (
        read("agent.md")
        + read("README.md")
        + read("docs/VOICING_SYSTEM_V2_DESIGN.md")
        + read("docs/VOICING_MODULE_CORE_LOGIC_V2.md")
        + read("docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md")
        + read("docs/DEVELOPMENT_TASK_PLAN_V2.md")
        + read("docs/DEVELOPMENT_HARNESS_V2.md")
        + read("docs/GENERATION_RULES_SUMMARY_V2.md")
    )
    for token in (
        "Basic SPREAD Projection",
        "BASIC_SPREAD_PROJECTION_VERSION",
        "SpreadProjectionRegisterPolicy",
        "SpreadProjectionCandidate",
        "SpreadProjectionResult",
        "project_basic_spread_contract",
        "project_basic_spread_candidates",
        "basic_spread_projection_debug",
        "group_gap_guard",
        "span_guard",
        "lower inventory + upper source adapter",
        "runtime_enabled=false",
        "notes-only",
    ):
        if token not in docs:
            fail(f"v2_2_40 Basic SPREAD Projection docs missing token: {token}")

    spread = read("src/jammate_engine/core/voicing/disposition/spread.py")
    for token in (
        "BASIC_SPREAD_PROJECTION_VERSION",
        "class SpreadProjectionRegisterPolicy",
        "class SpreadProjectionCandidate",
        "class SpreadProjectionResult",
        "def project_basic_spread_contract",
        "def project_basic_spread_candidates",
        "def basic_spread_projection_debug",
        "def _basic_spread_projection_legality",
        "final_placed_closed_open_result_reuse_allowed",
    ):
        if token not in spread:
            fail(f"spread.py missing v2_2_40 projection token: {token}")

    tests = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "tests").rglob("test_*.py"))
    if "test_v2_2_40_basic_spread_projection" not in tests or "group_gap_guard" not in tests:
        fail("missing v2_2_40 Basic SPREAD Projection regression test")

def main() -> None:
    check_versions()
    check_documentation_compaction_pass()
    check_agent_delivery_workflow_documented()
    check_runtime_uses_central_version_tag()
    check_required_docs()
    check_disposition_projection_taxonomy_documented()
    check_closed_projection_migration_documented_and_tested()
    check_legacy_disposition_cleanup_documented_and_tested()
    check_drop2_parent_closed_projection_documented_and_tested()
    check_open_method_candidate_pool_documented_and_tested()
    check_project_documentation_audit_guard()
    check_closed_34note_baseline_smoke_documented()
    check_future_ideas_backlog_habit_documented()
    check_voicing_source_balance_cleanup_documented()
    check_three_note_closed_listening_verification_documented()
    check_four_note_triad_closed_sync_documented()
    check_block_chord_runtime_name()
    check_styles_do_not_emit_note_events()
    check_core_pattern_runtime_has_no_style_libraries()
    check_piano_lh_bass_uses_shared_degree_resolver()
    check_no_bass_r_token_regression_test_exists()
    check_minimal_file_split_principle_documented()
    check_capability_reuse_before_new_construction_documented()
    check_voicing_texture_state_architecture_documented()
    check_current_architecture_tree_documented()
    check_target_architecture_base_alignment()
    check_vocabulary_is_solo_only()
    check_bass_foundation_span_guard_documented_and_tested()
    check_bass_foundation_classic_fill_guard()
    check_bass_foundation_root_echo_swing_upbeat_guard()
    check_bass_foundation_audit_report_guard()
    check_bass_foundation_musicality_tuning_guard()
    check_bass_foundation_three_beat_alignment_guard()
    check_generation_rules_summary_guard()
    check_bass_foundation_target_continuity_guard()
    check_bass_foundation_rule_organization_guard()
    check_style_baseline_docs_guard()
    check_spread_recipe_reuse_contract_documented_and_tested()
    check_basic_spread_projection_documented_and_tested()
    print("HARNESS OK")


if __name__ == "__main__":
    main()
