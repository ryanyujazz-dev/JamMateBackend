from __future__ import annotations

import json
from pathlib import Path

from jammate_engine.api.version import ENGINE_VERSION_TAG
from tools.demo_audit_pipeline import (
    DEMO_AUDIT_PIPELINE_VERSION,
    build_audit_summary,
    run_job,
    standard_jobs,
)

ROOT = Path(__file__).resolve().parents[1]


def test_v2_3_9_version_surfaces_are_synced() -> None:
    assert ENGINE_VERSION_TAG == "v2_3_9"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "v2_3_9"
    assert 'version = "2.3.9"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_consolidated_demo_audit_pipeline_publishes_standard_jobs() -> None:
    jobs = standard_jobs()
    assert DEMO_AUDIT_PIPELINE_VERSION == "v2_3_9"
    assert set(jobs) >= {
        "minimal_swing",
        "misty_ballad_upper_structure_altered",
        "blue_bossa_minor_altered",
        "minor_turnaround_fixture",
    }
    assert all(job.choruses == 3 for job in jobs.values())
    assert jobs["misty_ballad_upper_structure_altered"].style == "jazz_ballad"
    assert jobs["blue_bossa_minor_altered"].leadsheet == "blue_bossa.json"


def test_demo_audit_pipeline_smoke_generates_midi_and_shared_audit_shape(tmp_path: Path) -> None:
    paths = run_job(standard_jobs()["minimal_swing"], output_dir=tmp_path)
    assert paths["midi"].exists()
    assert paths["midi"].suffix == ".mid"
    assert paths["audit"].exists()
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    assert audit["demo_audit_pipeline_version"] == "v2_3_9"
    assert audit["engine_version"] == "v2_3_9"
    assert audit["request"]["choruses"] == 3
    assert audit["runtime_summary"]["performance_choruses"] == 3
    assert "piano_musical_audit" in audit
    assert "expression_foundation_audit" in audit
    assert "piano_event_summary" in audit
    assert "content_families" in audit["piano_event_summary"]


def test_build_audit_summary_keeps_runtime_and_piano_event_sections() -> None:
    class Result:
        debug = {
            "title": "Synthetic",
            "style": "medium_swing",
            "performance_choruses": 3,
            "piano_musical_audit_events": [
                {
                    "pattern_event": {"event_id": "e1", "region_id": "r1", "chord_symbol": "G7"},
                    "voicing": {
                        "notes": [55, 59, 63, 68],
                        "degrees": ["3", "b7", "b9", "#9"],
                        "content_family": "rootless_A",
                        "disposition": "closed",
                        "metadata": {
                            "score_breakdown": {
                                "details": {
                                    "altered_dominant_source_kind": "rootless_ab",
                                    "altered_dominant_intensity_score": 0.1,
                                    "upper_structure_register_score": -0.02,
                                    "upper_structure_register_refinement_version": "v2_3_9",
                                }
                            }
                        },
                    },
                }
            ],
            "piano_musical_audit": {"event_count": 1},
            "expression_foundation_audit": {"event_count": 1},
        }

    job = standard_jobs()["minimal_swing"]
    summary = build_audit_summary(job, Result(), midi_path=ROOT / "demos" / "dummy.mid")
    assert summary["piano_event_summary"]["altered_degree_events"] == 1
    assert summary["piano_event_summary"]["altered_dominant_source_kinds"] == {"rootless_ab": 1}
    assert summary["piano_event_summary"]["upper_structure_register_refinement_events"] == 1


def test_v2_3_9_docs_point_to_canonical_pipeline_tool() -> None:
    for rel in [
        "README.md",
        "agent.md",
        "docs/DEVELOPMENT_TASK_PLAN_V2.md",
        "docs/DEVELOPMENT_HARNESS_V2.md",
        "docs/DEMO_AUDIT_PIPELINE_CONSOLIDATION_V2_3_0.md",
        "docs/DEMO_MATRIX_LISTENING_REGRESSION_THRESHOLDS_V2_3_1.md",
        "docs/VOICING_REGISTER_CONTINUITY_DENSITY_RECOVERY_V2_3_2.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "v2_3_9" in text, rel
        assert "tools/demo_audit_pipeline.py" in text, rel
        assert ("Demo Matrix" in text or "Anticipation Timing Grid Contract Repair" in text), rel


def test_v2_3_9_demo_matrix_declares_thresholds_for_targeted_jobs() -> None:
    from tools.demo_audit_pipeline import standard_demo_matrix

    matrix = standard_demo_matrix()
    assert set(matrix) >= {
        "minimal_swing_smoke",
        "misty_ballad_upper_structure_altered",
        "blue_bossa_minor_altered",
        "minor_turnaround_fixture",
    }
    assert matrix["minimal_swing_smoke"].thresholds.min_piano_note_events >= 1
    assert matrix["misty_ballad_upper_structure_altered"].thresholds.min_upper_structure_events >= 1
    assert matrix["misty_ballad_upper_structure_altered"].thresholds.min_altered_degree_events >= 1
    assert matrix["misty_ballad_upper_structure_altered"].thresholds.min_non_four_density_events >= 50
    assert matrix["misty_ballad_upper_structure_altered"].thresholds.max_top_note == 74
    assert matrix["blue_bossa_minor_altered"].thresholds.min_altered_source_events >= 1
    assert matrix["minor_turnaround_fixture"].thresholds.min_altered_degree_events >= 1


def test_v2_3_9_audit_threshold_validator_reports_pass_and_fail() -> None:
    from tools.demo_audit_pipeline import AuditThresholds, validate_audit_summary

    passing_audit = {
        "runtime_summary": {
            "performance_choruses": 3,
            "note_events": 12,
            "note_events_by_track": {"piano": 6},
        },
        "piano_event_summary": {
            "event_count": 6,
            "register_guard_violations": 0,
            "altered_degree_events": 2,
            "altered_dominant_source_kinds": {"rooted_color": 1},
            "upper_structure_register_refinement_events": 4,
            "top_note_max": 72,
            "average_pitch_mean": 60.0,
        },
        "piano_musical_audit": {"densities": {"4": 2, "5": 4}},
    }
    thresholds = AuditThresholds(
        min_altered_degree_events=1,
        min_altered_source_events=1,
        min_upper_structure_events=1,
        min_non_four_density_events=1,
        max_top_note=74,
        max_average_pitch_mean=62.0,
    )
    assert validate_audit_summary(passing_audit, thresholds) == []

    failing_audit = {
        "runtime_summary": {
            "performance_choruses": 1,
            "note_events": 0,
            "note_events_by_track": {"piano": 0},
        },
        "piano_event_summary": {
            "event_count": 0,
            "register_guard_violations": 2,
            "altered_degree_events": 0,
            "altered_dominant_source_kinds": {},
            "upper_structure_register_refinement_events": 0,
            "top_note_max": 81,
            "average_pitch_mean": 66.5,
        },
        "piano_musical_audit": {"densities": {"4": 6}},
    }
    violations = validate_audit_summary(failing_audit, thresholds)
    codes = {item["code"] for item in violations}
    assert "required_choruses" in codes
    assert "min_total_note_events" in codes
    assert "min_piano_note_events" in codes
    assert "max_register_guard_violations" in codes
    assert "min_altered_degree_events" in codes
    assert "min_non_four_density_events" in codes
    assert "max_top_note" in codes
    assert "max_average_pitch_mean" in codes



def test_v2_3_9_misty_ballad_demo_recovers_density_and_register_continuity(tmp_path: Path) -> None:
    paths = run_job(standard_jobs()["misty_ballad_upper_structure_altered"], output_dir=tmp_path)
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    musical = audit["piano_musical_audit"]
    summary = audit["piano_event_summary"]
    densities = {str(key): int(value) for key, value in musical["densities"].items()}
    total_density_events = sum(densities.values())
    assert musical["top_patterns"][0][0] != "global_voicing_override_region_start_anchor"
    assert total_density_events - densities.get("4", 0) >= 50
    assert summary["top_note_max"] <= 74
    assert summary["average_pitch_mean"] <= 62.0
    assert musical["avg_realized_notes_per_event"] > 5.0

def test_v2_3_9_run_jobs_writes_manifest_validation(tmp_path: Path) -> None:
    from tools.demo_audit_pipeline import run_jobs

    outputs = run_jobs([], output_dir=tmp_path, fail_on_thresholds=True)
    manifest_path = Path(outputs["manifest"]["json"])
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["demo_audit_pipeline_version"] == "v2_3_9"
    assert manifest["validation"]["status"] == "passed"
    assert set(manifest["validation"]["required_job_ids"]) >= {
        "minimal_swing",
        "misty_ballad_upper_structure_altered",
        "blue_bossa_minor_altered",
        "minor_turnaround_fixture",
    }
    assert all(result["status"] == "passed" for result in manifest["validation"]["job_results"].values())
