import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class ViolationRecord:
    violation_id: str
    file_path: str
    symbol: str
    violation_type: str
    evidence: str
    target_layer: str
    port_name: str
    acceptance_test_id: str


@dataclass(frozen=True)
class NamingViolation:
    file_path: str
    symbol: str
    violation_type: str
    evidence: str


class DecouplingAssessmentUseCase:
    """Builds Phase 6.1 assessment data with fixed, auditable structure."""

    FIXED_KPI_THRESHOLDS = {
        "forbidden_dependency_count": 0,
        "circular_dependency_count": 0,
        "ui_business_logic_count": 0,
        "boundary_test_pass_rate": 100,
    }

    IMPORT_GRAPH_PROCEDURE = {
        "extract_command": "pydeps src/lcr --noshow --show-deps --max-bacon 2",
        "judgement_method": (
            "Count UI->Domain direct edges, reverse-direction edges, and cycle reports "
            "from the extracted dependency graph."
        ),
    }

    def build_violation_entries(self, violations: Sequence[ViolationRecord]) -> List[Dict]:
        entries = []
        for item in violations:
            entries.append(
                {
                    "violation_id": item.violation_id,
                    "file_path": item.file_path,
                    "symbol": item.symbol,
                    "violation_type": item.violation_type,
                    "evidence": item.evidence,
                    "remediation": {
                        "target_layer": item.target_layer,
                        "port_name": item.port_name,
                        "interface_design": f"Introduce/extend Port `{item.port_name}` for boundary isolation.",
                        "acceptance_test_id": item.acceptance_test_id,
                        "completion_criteria": (
                            "No direct boundary bypass remains and acceptance test passes."
                        ),
                    },
                }
            )
        return entries

    def build_verification_matrix(self, test_specs: Sequence[Dict]) -> List[Dict]:
        matrix = []
        for item in test_specs:
            matrix.append(
                {
                    "test_id": item["test_id"],
                    "test_type": item["test_type"],
                    "pass_condition": item["pass_condition"],
                    "fail_condition": item["fail_condition"],
                    "metric_key": item["metric_key"],
                }
            )
        return matrix

    def build_change_impact_test_plan(self) -> List[Dict]:
        return [
            {
                "scenario_id": "CIT-UI-001",
                "scenario": "UI change does not impact Domain behavior",
                "preconditions": [
                    "Current main branch test suite is green.",
                    "Baseline import graph snapshot is available.",
                ],
                "operations": [
                    "Change UI widget layout/labels only.",
                    "Run domain and use case tests.",
                    "Compare changed files against domain modules.",
                ],
                "expected_impact_scope": "Only UI layer files are modified.",
                "pass_condition": "All domain/use case tests pass and domain diff is zero.",
            },
            {
                "scenario_id": "CIT-DOM-001",
                "scenario": "Domain change does not require UI modification",
                "preconditions": [
                    "A Port contract exists between UI and the target Domain behavior.",
                    "Baseline UI import graph snapshot is available.",
                ],
                "operations": [
                    "Modify domain rule implementation behind a Port contract.",
                    "Run UI integration tests.",
                    "Compare UI import graph with baseline.",
                ],
                "expected_impact_scope": "Domain and use case layers only.",
                "pass_condition": "UI tests pass and UI import graph diff is zero.",
            },
        ]

    def evaluate_fixed_kpis(self, measured: Dict[str, int]) -> Dict:
        result = {}
        for key, threshold in self.FIXED_KPI_THRESHOLDS.items():
            value = measured.get(key)
            if value is None:
                result[key] = {"threshold": threshold, "actual": None, "passed": False}
                continue
            if key == "boundary_test_pass_rate":
                passed = value >= threshold
            else:
                passed = value <= threshold
            result[key] = {"threshold": threshold, "actual": value, "passed": passed}
        result["all_passed"] = all(item["passed"] for item in result.values())
        return result

    def summarize_import_graph_counts(
        self,
        ui_to_domain_direct: Sequence[str],
        reverse_dependencies: Sequence[str],
        circular_dependencies: Sequence[str],
    ) -> Dict:
        return {
            "ui_to_domain_direct": {
                "items": list(ui_to_domain_direct),
                "count": len(ui_to_domain_direct),
            },
            "reverse_dependencies": {
                "items": list(reverse_dependencies),
                "count": len(reverse_dependencies),
            },
            "circular_dependencies": {
                "items": list(circular_dependencies),
                "count": len(circular_dependencies),
            },
            "procedure": dict(self.IMPORT_GRAPH_PROCEDURE),
        }


class SignalSlotNamingAuditUseCase:
    """Static audit for Signal/Slot naming in src/lcr/ui."""

    _SIGNAL_ALLOWED_SUFFIXES = ("ed", "en", "n")
    _SLOT_ALLOWED_PREFIXES = (
        "on_",
        "run",
        "update",
        "select",
        "open",
        "refresh",
        "load",
        "save",
        "prepare",
        "handle",
        "start",
        "stop",
        "clear",
        "render",
        "build",
        "confirm",
        "apply",
        "populate",
        "reset",
        "execute",
        "close",
        "show",
        "append",
        "ensure",
    )

    def audit_ui_paths(self, root: Path) -> Dict:
        files = sorted(root.rglob("*.py"))
        violations: List[NamingViolation] = []
        signal_count = 0
        slot_count = 0

        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and self._is_signal_call(node.value):
                    signal_count += 1
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            if not self._is_valid_signal_name(name):
                                violations.append(
                                    NamingViolation(
                                        file_path=str(path).replace("\\", "/"),
                                        symbol=name,
                                        violation_type="signal_naming",
                                        evidence="Signal name must be past-participle style.",
                                    )
                                )
                if isinstance(node, ast.FunctionDef) and self._has_slot_decorator(node):
                    slot_count += 1
                    name = node.name.lstrip("_")
                    if not self._is_valid_slot_name(name):
                        violations.append(
                            NamingViolation(
                                file_path=str(path).replace("\\", "/"),
                                symbol=node.name,
                                violation_type="slot_naming",
                                evidence="Slot name must start with an action verb.",
                            )
                        )

        return {
            "files_scanned": len(files),
            "signals_scanned": signal_count,
            "slots_scanned": slot_count,
            "violations": violations,
            "violation_count": len(violations),
        }

    @classmethod
    def _is_signal_call(cls, value: ast.AST) -> bool:
        if not isinstance(value, ast.Call):
            return False
        func = value.func
        if isinstance(func, ast.Name):
            return func.id == "Signal"
        return isinstance(func, ast.Attribute) and func.attr == "Signal"

    @classmethod
    def _has_slot_decorator(cls, func: ast.FunctionDef) -> bool:
        for deco in func.decorator_list:
            if isinstance(deco, ast.Name) and deco.id == "Slot":
                return True
            if isinstance(deco, ast.Call):
                inner = deco.func
                if isinstance(inner, ast.Name) and inner.id == "Slot":
                    return True
                if isinstance(inner, ast.Attribute) and inner.attr == "Slot":
                    return True
        return False

    @classmethod
    def _is_valid_signal_name(cls, name: str) -> bool:
        lowered = name.lower().replace("_", "")
        return lowered.endswith(cls._SIGNAL_ALLOWED_SUFFIXES)

    @classmethod
    def _is_valid_slot_name(cls, name: str) -> bool:
        lowered = name.lower()
        return lowered.startswith(cls._SLOT_ALLOWED_PREFIXES)


class StandardsTraceabilityUseCase:
    """Builds auditable traceability and regression checklist records."""

    def build_standards_traceability_matrix(self, rows: Sequence[Dict]) -> List[Dict]:
        matrix = []
        for item in rows:
            matrix.append(
                {
                    "standard_section": item["standard_section"],
                    "kpi": item["kpi"],
                    "evidence_artifact": item["evidence_artifact"],
                    "verification_method": item["verification_method"],
                    "gate_timing": item["gate_timing"],
                }
            )
        return matrix

    def build_mainwindow_responsibility_diff(self) -> List[Dict]:
        return [
            {
                "method": "MainWindow._run_container",
                "before": [
                    "Runtime compatibility decision",
                    "Environment creation orchestration",
                    "Build/run command assembly",
                ],
                "after": [
                    "Collect input from UI widgets",
                    "Call runtime preparation/use case",
                    "Update dialogs and button states",
                ],
                "moved_to": [
                    "RuntimeExecutionPreparationUseCase",
                    "EnvironmentBuildPreparationUseCase",
                ],
            },
            {
                "method": "MainWindow._show_create_env_dialog",
                "before": [
                    "Concrete dialog invocation and option shaping",
                    "Runtime definition lifecycle handling",
                ],
                "after": [
                    "Delegate to EnvironmentDialogPort",
                    "Reflect returned state to UI only",
                ],
                "moved_to": [
                    "EnvironmentDialogPort",
                    "EnvironmentBuildPreparationUseCase",
                ],
            },
        ]

    def build_known_regression_checklist(self) -> List[Dict]:
        return [
            {
                "method": "MainWindow._run_container",
                "checks": [
                    "Direct import to Domain/Infrastructure concrete types is absent.",
                    "Decision flow is completed in one UseCase boundary.",
                    "UI responsibility is limited to input collection and view updates.",
                ],
            },
            {
                "method": "MainWindow._show_create_env_dialog",
                "checks": [
                    "Environment creation logic is not executed without Port/UseCase.",
                    "Dialog result handling updates UI state only.",
                    "No runtime definition mutation is implemented in MainWindow.",
                ],
            },
        ]
