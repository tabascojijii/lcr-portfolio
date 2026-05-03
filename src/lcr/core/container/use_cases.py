from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import subprocess

from lcr.core.container.generator import generate_dockerfile, save_definition


@dataclass
class BuildPreparationResult:
    config: Dict
    dockerfile_path: str
    build_args: List[str]
    tag: str
    apt_added_tools: List[str]
    has_opencv_pip_warning: bool


@dataclass
class EnvironmentDraft:
    initial_config: Dict[str, Any]
    recommended_rule: Dict[str, Any]
    recommendation_reason: str
    base_images: List[Dict[str, Any]]


class EnvironmentDraftUseCase:
    """Prepare environment-creation inputs from code content."""

    def __init__(self, analyzer, container_manager):
        self.analyzer = analyzer
        self.container_manager = container_manager

    def prepare(self, code_text: str) -> EnvironmentDraft:
        analysis = self.analyzer.summary(code_text)
        feature = self.analyzer.analyze(code_text)
        search_terms = feature.imports + feature.keywords
        if feature.validation_year:
            search_terms.append(f"year:{feature.validation_year}")

        recommended_rule = self.container_manager.resolve_runtime(search_terms, feature.version_hint)
        rec_id = recommended_rule["id"]
        rec_reason = recommended_rule.get("reason", "Best match")
        initial_config = self.container_manager.synthesize_definition_config(analysis, rec_id)

        return EnvironmentDraft(
            initial_config=initial_config,
            recommended_rule=recommended_rule,
            recommendation_reason=rec_reason,
            base_images=self.container_manager.get_available_runtimes(),
        )


class EnvironmentBuildPreparationUseCase:
    """Application-layer use case for dialog-side environment build preparation."""

    def __init__(self, container_manager):
        self.container_manager = container_manager

    def prepare(self, config: Dict) -> BuildPreparationResult:
        result = dict(config)
        pip_pkgs = list(result.get("pip_packages", []))
        apt_pkgs = list(result.get("apt_packages", []))
        base_image = result.get("base_image", "")

        version = "3.6" if "3.6" in base_image else ""
        if version and self.container_manager:
            pip_pkgs = self.container_manager.apply_legacy_pins(pip_pkgs, version)
            result["pip_packages"] = pip_pkgs

        if "python3-opencv" in apt_pkgs:
            unnecessary = {"build-essential", "cmake"}
            apt_pkgs = [p for p in apt_pkgs if p not in unnecessary]
            result["apt_packages"] = apt_pkgs

        has_opencv_pip_warning = any("opencv" in p and "python" in p for p in pip_pkgs)

        apt_added_tools: List[str] = []
        if pip_pkgs and "python3-opencv" not in apt_pkgs:
            needed_tools = {"build-essential", "cmake", "python3-dev"}
            missing = sorted(list(needed_tools - set(apt_pkgs)))
            if missing:
                result.setdefault("apt_packages", []).extend(missing)
                apt_added_tools = missing

        tag = result["tag"]
        json_path = save_definition(result, tag)
        _, dockerfile_path = generate_dockerfile(str(json_path))
        build_args = self.container_manager.get_build_command(dockerfile_path, tag)

        return BuildPreparationResult(
            config=result,
            dockerfile_path=dockerfile_path,
            build_args=build_args,
            tag=tag,
            apt_added_tools=apt_added_tools,
            has_opencv_pip_warning=has_opencv_pip_warning,
        )


class RuntimeExecutionPreparationUseCase:
    """Use case for runtime pre-checks before UI starts execution worker."""

    def prepare_guard(
        self,
        required_imports: Optional[List[str]],
        environment_capability: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        required = self._normalize_imports(required_imports or [])
        capability_imports = self._normalize_imports((environment_capability or {}).get("imports", []))
        capability_set = set(capability_imports)
        missing = sorted([name for name in required if name not in capability_set])
        matched = sorted([name for name in required if name in capability_set])
        mismatch = {
            "required": required,
            "capability_imports": capability_imports,
            "matched": matched,
            "missing": missing,
            "mismatch_count": len(missing),
        }
        guard_state = "blocked" if missing else "pass"
        return {
            "required_imports": required,
            "environment_capability": environment_capability or {},
            "mismatch_result": mismatch,
            "guard_state": guard_state,
            "can_run": guard_state == "pass",
        }

    def _normalize_imports(self, imports: List[str]) -> List[str]:
        normalized = []
        for name in imports:
            cleaned = str(name).strip().lower()
            if cleaned:
                normalized.append(cleaned)
        return sorted(set(normalized))

    def image_exists(self, image_name: str) -> bool:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
