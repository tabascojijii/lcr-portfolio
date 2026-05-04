from lcr.core.architecture import DecouplingAssessmentUseCase, ViolationRecord


def test_build_violation_entries_include_id_and_remediation_contract():
    use_case = DecouplingAssessmentUseCase()
    violations = [
        ViolationRecord(
            violation_id="V-001",
            file_path="src/lcr/ui/main_window.py",
            symbol="MainWindow._run_script",
            violation_type="UI->Domain direct reference",
            evidence="MainWindow imports domain entity directly.",
            target_layer="UseCase",
            port_name="ScriptExecutionPort",
            acceptance_test_id="AT-DEC-001",
        )
    ]

    entries = use_case.build_violation_entries(violations)
    assert entries[0]["violation_id"] == "V-001"
    assert entries[0]["remediation"] == {
        "target_layer": "UseCase",
        "port_name": "ScriptExecutionPort",
        "interface_design": "Introduce/extend Port `ScriptExecutionPort` for boundary isolation.",
        "acceptance_test_id": "AT-DEC-001",
        "completion_criteria": "No direct boundary bypass remains and acceptance test passes.",
    }


def test_build_verification_matrix_has_test_level_pass_fail_metrics():
    use_case = DecouplingAssessmentUseCase()
    matrix = use_case.build_verification_matrix(
        [
            {
                "test_id": "T61-001",
                "test_type": "updated",
                "pass_condition": "Forbidden dependency count is zero.",
                "fail_condition": "Any UI->Domain direct dependency detected.",
                "metric_key": "forbidden_dependency_count",
            }
        ]
    )

    assert matrix == [
        {
            "test_id": "T61-001",
            "test_type": "updated",
            "pass_condition": "Forbidden dependency count is zero.",
            "fail_condition": "Any UI->Domain direct dependency detected.",
            "metric_key": "forbidden_dependency_count",
        }
    ]


def test_change_impact_test_plan_includes_ui_and_domain_scenarios():
    use_case = DecouplingAssessmentUseCase()
    plan = use_case.build_change_impact_test_plan()

    scenario_ids = {item["scenario_id"] for item in plan}
    assert scenario_ids == {"CIT-UI-001", "CIT-DOM-001"}
    for item in plan:
        assert item["preconditions"]
        assert item["operations"]
        assert item["expected_impact_scope"]
        assert item["pass_condition"]


def test_evaluate_fixed_kpis_uses_numeric_fixed_thresholds():
    use_case = DecouplingAssessmentUseCase()
    result = use_case.evaluate_fixed_kpis(
        {
            "forbidden_dependency_count": 0,
            "circular_dependency_count": 0,
            "ui_business_logic_count": 0,
            "boundary_test_pass_rate": 100,
        }
    )

    assert result["forbidden_dependency_count"]["threshold"] == 0
    assert result["circular_dependency_count"]["threshold"] == 0
    assert result["ui_business_logic_count"]["threshold"] == 0
    assert result["boundary_test_pass_rate"]["threshold"] == 100
    assert result["all_passed"] is True


def test_import_graph_summary_has_reproducible_procedure_and_counts():
    use_case = DecouplingAssessmentUseCase()
    summary = use_case.summarize_import_graph_counts(
        ui_to_domain_direct=["src/lcr/ui/main_window.py -> src/lcr/core/history/types.py"],
        reverse_dependencies=["src/lcr/core/container/manager.py -> src/lcr/ui/ports.py"],
        circular_dependencies=[],
    )

    assert summary["ui_to_domain_direct"]["count"] == 1
    assert summary["reverse_dependencies"]["count"] == 1
    assert summary["circular_dependencies"]["count"] == 0
    assert "pydeps src/lcr" in summary["procedure"]["extract_command"]
    assert "Count UI->Domain direct edges" in summary["procedure"]["judgement_method"]
