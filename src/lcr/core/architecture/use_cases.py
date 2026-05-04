from dataclasses import dataclass
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
                        "acceptance_test_id": item.acceptance_test_id,
                    },
                }
            )
        return entries

    def build_change_impact_test_plan(self) -> List[Dict]:
        return [
            {
                "scenario_id": "CIT-UI-001",
                "scenario": "UI change does not impact Domain behavior",
                "steps": [
                    "Change UI widget layout/labels only.",
                    "Run domain and use case tests.",
                    "Verify no domain module was edited.",
                ],
                "expected_impact_scope": "Only UI layer files are modified.",
                "pass_condition": "All domain/use case tests pass and domain diff is zero.",
            },
            {
                "scenario_id": "CIT-DOM-001",
                "scenario": "Domain change does not require UI modification",
                "steps": [
                    "Modify domain rule implementation behind a Port contract.",
                    "Run UI integration tests.",
                    "Verify UI modules import surface is unchanged.",
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
