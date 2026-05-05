from pathlib import Path

from lcr.core.architecture import StandardsTraceabilityUseCase


def test_required_roadmap_artifact_list_matches_reference():
    use_case = StandardsTraceabilityUseCase()

    assert use_case.list_required_roadmap_artifacts() == [
        "artifacts/architecture_decoupling_assessment.md",
        "artifacts/refactoring_proposal.md",
        "artifacts/phase_6_51_baseline_inventory.md",
        "artifacts/phase_6_51_test_baseline.md",
        "artifacts/phase_6_52_logging_migration_report.md",
        "artifacts/phase_6_52_print_elimination_evidence.md",
        "artifacts/post_mortem_closure_checklist.md",
    ]


def test_required_roadmap_artifacts_exist():
    use_case = StandardsTraceabilityUseCase()

    for relative_path in use_case.list_required_roadmap_artifacts():
        path = Path(relative_path)
        assert path.exists()
        assert path.is_file()
