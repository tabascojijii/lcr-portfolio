from lcr.core.architecture import StandardsTraceabilityUseCase


def test_traceability_matrix_keeps_required_audit_fields():
    use_case = StandardsTraceabilityUseCase()
    matrix = use_case.build_standards_traceability_matrix(
        [
            {
                "standard_section": "Section 4",
                "kpi": "UI->Domain direct reference count",
                "evidence_artifact": "artifacts/architecture_decoupling_assessment.md",
                "verification_method": "Import graph check",
                "gate_timing": "M1 completion",
            }
        ]
    )

    assert matrix == [
        {
            "standard_section": "Section 4",
            "kpi": "UI->Domain direct reference count",
            "evidence_artifact": "artifacts/architecture_decoupling_assessment.md",
            "verification_method": "Import graph check",
            "gate_timing": "M1 completion",
        }
    ]


def test_mainwindow_responsibility_diff_covers_regression_methods():
    use_case = StandardsTraceabilityUseCase()
    diff = use_case.build_mainwindow_responsibility_diff()

    methods = {item["method"] for item in diff}
    assert methods == {"MainWindow._run_container", "MainWindow._show_create_env_dialog"}
    for item in diff:
        assert item["before"]
        assert item["after"]
        assert item["moved_to"]


def test_known_regression_checklist_has_non_empty_checks():
    use_case = StandardsTraceabilityUseCase()
    checklist = use_case.build_known_regression_checklist()

    methods = {item["method"] for item in checklist}
    assert methods == {"MainWindow._run_container", "MainWindow._show_create_env_dialog"}
    for item in checklist:
        assert len(item["checks"]) >= 3
