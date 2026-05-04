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


@dataclass
class ManualCompatibilityCheckResult:
    requires_confirmation: bool
    message: str


@dataclass
class MissingImageBuildDraft:
    env_id: str
    initial_config: Dict[str, Any]
    recommendation_reason: str
    base_images: List[Dict[str, Any]]


@dataclass
class RuntimeExecutionPlan:
    selected_rule: Dict[str, Any]
    reason_text: str
    config: Dict[str, Any]
    docker_args: List[str]
    run_context: Dict[str, Any]
    output_dir_rel: str
    runtime_name: str


@dataclass
class RuntimePreflightResult:
    compatibility: ManualCompatibilityCheckResult
    execution_plan: RuntimeExecutionPlan
    image_missing: bool
    missing_image_build_draft: Optional[MissingImageBuildDraft]


@dataclass
class RuntimeRunDecision:
    compatibility: ManualCompatibilityCheckResult
    execution_plan: RuntimeExecutionPlan
    requires_compatibility_confirmation: bool
    requires_image_build: bool
    missing_image_build_draft: Optional[MissingImageBuildDraft]


@dataclass
class BuildExecutionPlan:
    tag: str
    build_args: List[str]
    selected_runtime_image: str


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

    def prepare_execution_plan(self, config: Dict, available_runtimes: List[Dict[str, Any]]) -> BuildExecutionPlan:
        prepared = self.prepare(config)
        selected_image = prepared.tag
        for runtime in available_runtimes:
            if runtime.get("image") == prepared.tag:
                selected_image = runtime.get("image", prepared.tag)
                break
        return BuildExecutionPlan(
            tag=prepared.tag,
            build_args=prepared.build_args,
            selected_runtime_image=selected_image,
        )

    def list_available_runtimes(self) -> List[Dict[str, Any]]:
        return self.container_manager.get_available_runtimes()

    def reload_runtime_definitions(self) -> None:
        self.container_manager.reload_definitions()

    def validate_runtime_environment(self) -> None:
        self.container_manager.validate_environment()

    def get_definition(self, env_id: str) -> Optional[Dict]:
        return self.container_manager.get_definition(env_id)

    def synthesize_definition_config(self, analysis: Dict[str, Any], rec_id: str) -> Dict[str, Any]:
        return self.container_manager.synthesize_definition_config(analysis, rec_id)


class RuntimeExecutionPreparationUseCase:
    """Use case for runtime pre-checks before UI starts execution worker."""
    def __init__(self, analyzer=None, container_manager=None, history_manager=None):
        self._analyzer = analyzer
        self._container_manager = container_manager
        self._history_manager = history_manager

    def _resolve_analyzer(self, analyzer=None):
        resolved = analyzer or self._analyzer
        if resolved is None:
            raise ValueError("analyzer is required")
        return resolved

    def _resolve_container_manager(self, container_manager=None):
        resolved = container_manager or self._container_manager
        if resolved is None:
            raise ValueError("container_manager is required")
        return resolved

    def _resolve_history_manager(self, history_manager=None):
        resolved = history_manager or self._history_manager
        if resolved is None:
            raise ValueError("history_manager is required")
        return resolved

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

    def prepare_manual_compatibility_check(
        self,
        analyzer,
        container_manager,
        code_text: str,
        selected_rule: Optional[Dict[str, Any]],
        selection_mode: str,
    ) -> ManualCompatibilityCheckResult:
        analyzer = self._resolve_analyzer(analyzer)
        container_manager = self._resolve_container_manager(container_manager)
        if selection_mode != "Manual" or not selected_rule:
            return ManualCompatibilityCheckResult(False, "")

        probe = analyzer.analyze(code_text)
        rule_ver = selected_rule.get("version", "unknown")
        compatible = container_manager.is_version_compatible(probe.version_hint, rule_ver)
        if compatible:
            return ManualCompatibilityCheckResult(False, "")

        message = (
            f"You selected {rule_ver} but the code appears to be {probe.version_hint}.\n\n"
            "Usage mistakes may cause errors. Continue?"
        )
        return ManualCompatibilityCheckResult(True, message)

    def prepare_missing_image_build_draft(
        self,
        analyzer,
        container_manager,
        code_text: str,
        selected_rule: Dict[str, Any],
    ) -> MissingImageBuildDraft:
        analyzer = self._resolve_analyzer(analyzer)
        container_manager = self._resolve_container_manager(container_manager)
        env_id = selected_rule["id"]
        existing_config = container_manager.get_definition(env_id)
        if existing_config:
            initial_config = dict(existing_config)
            initial_config["id"] = env_id
            initial_config["tag"] = env_id
            return MissingImageBuildDraft(
                env_id=env_id,
                initial_config=initial_config,
                recommendation_reason="Rebuilding existing definition (Image not built)",
                base_images=container_manager.get_available_runtimes(),
            )

        analysis = analyzer.summary(code_text)
        synthesized_config = container_manager.synthesize_definition_config(analysis, env_id)
        synthesized_config["id"] = env_id
        synthesized_config["tag"] = env_id
        return MissingImageBuildDraft(
            env_id=env_id,
            initial_config=synthesized_config,
            recommendation_reason="Synthesized from code analysis (Missing Image)",
            base_images=container_manager.get_available_runtimes(),
        )

    def prepare_execution(
        self,
        code_text: str,
        script_path: str,
        data_dir: Optional[str],
        output_dir: Optional[str],
        selected_rule: Optional[Dict[str, Any]],
        analyzer=None,
        container_manager=None,
    ) -> Dict[str, Any]:
        analyzer = self._resolve_analyzer(analyzer)
        container_manager = self._resolve_container_manager(container_manager)
        feature = analyzer.analyze(code_text)
        search_terms = feature.imports + feature.keywords
        if feature.validation_year:
            search_terms.append(f"year:{feature.validation_year}")

        runtime_rule = selected_rule or container_manager.resolve_runtime(search_terms, feature.version_hint)
        reasons: List[str] = []
        if feature.validation_year:
            reasons.append(f"Validation Year ({feature.validation_year}) detected")
        matches = [t for t in runtime_rule.get("triggers", []) if t in search_terms]
        if matches:
            reasons.append(f"Triggers {matches} detected")
        match_libs = set(runtime_rule.get("libs", [])).intersection(set(search_terms))
        if match_libs:
            reasons.append(f"Libraries {sorted(match_libs)} matched")

        config = container_manager.prepare_run_config(
            analyzer.summary(code_text),
            script_path,
            data_dir=data_dir,
            output_dir=output_dir,
            override_image_rule=runtime_rule,
        )
        return {
            "feature": feature,
            "selected_rule": runtime_rule,
            "config": config,
            "reason_text": " / ".join(reasons) if reasons else "Default selection",
        }

    def prepare_execution_plan(
        self,
        code_text: str,
        script_path: str,
        data_dir: Optional[str],
        output_dir: Optional[str],
        selected_rule: Optional[Dict[str, Any]],
        analyzer=None,
        container_manager=None,
        history_manager=None,
    ) -> RuntimeExecutionPlan:
        history_manager = self._resolve_history_manager(history_manager)
        prepared = self.prepare_execution(
            code_text,
            script_path,
            data_dir=data_dir,
            output_dir=output_dir,
            selected_rule=selected_rule,
            analyzer=analyzer,
            container_manager=container_manager,
        )
        config = prepared["config"]
        image_name = config["image"]
        output_dir_abs = config["host_work_dir"]
        return RuntimeExecutionPlan(
            selected_rule=prepared["selected_rule"],
            reason_text=prepared["reason_text"],
            config=config,
            docker_args=container_manager.get_docker_run_args(config),
            run_context={
                "image_name": image_name,
                "script_path": script_path,
                "param_payload": config,
                "input_files": [script_path],
            },
            output_dir_rel=history_manager.to_relative_path(output_dir_abs),
            runtime_name=prepared["selected_rule"].get("name", image_name),
        )

    def prepare_run_preflight(
        self,
        code_text: str,
        script_path: str,
        data_dir: Optional[str],
        output_dir: Optional[str],
        selected_rule: Optional[Dict[str, Any]],
        selection_mode: str,
        analyzer=None,
        container_manager=None,
        history_manager=None,
    ) -> RuntimePreflightResult:
        analyzer = self._resolve_analyzer(analyzer)
        container_manager = self._resolve_container_manager(container_manager)
        history_manager = self._resolve_history_manager(history_manager)
        compatibility = self.prepare_manual_compatibility_check(
            code_text=code_text,
            selected_rule=selected_rule,
            selection_mode=selection_mode,
            analyzer=analyzer,
            container_manager=container_manager,
        )
        execution_plan = self.prepare_execution_plan(
            code_text=code_text,
            script_path=script_path,
            data_dir=data_dir,
            output_dir=output_dir,
            selected_rule=selected_rule,
            analyzer=analyzer,
            container_manager=container_manager,
            history_manager=history_manager,
        )
        image_missing = not self.image_exists(execution_plan.config["image"])
        build_draft = None
        if image_missing:
            build_draft = self.prepare_missing_image_build_draft(
                code_text=code_text,
                selected_rule=execution_plan.selected_rule,
                analyzer=analyzer,
                container_manager=container_manager,
            )
        return RuntimePreflightResult(
            compatibility=compatibility,
            execution_plan=execution_plan,
            image_missing=image_missing,
            missing_image_build_draft=build_draft,
        )

    def prepare_run_decision(
        self,
        code_text: str,
        script_path: str,
        data_dir: Optional[str],
        output_dir: Optional[str],
        selected_rule: Optional[Dict[str, Any]],
        selection_mode: str,
        analyzer=None,
        container_manager=None,
        history_manager=None,
    ) -> RuntimeRunDecision:
        analyzer = self._resolve_analyzer(analyzer)
        container_manager = self._resolve_container_manager(container_manager)
        history_manager = self._resolve_history_manager(history_manager)
        preflight = self.prepare_run_preflight(
            code_text=code_text,
            script_path=script_path,
            data_dir=data_dir,
            output_dir=output_dir,
            selected_rule=selected_rule,
            selection_mode=selection_mode,
            analyzer=analyzer,
            container_manager=container_manager,
            history_manager=history_manager,
        )
        return RuntimeRunDecision(
            compatibility=preflight.compatibility,
            execution_plan=preflight.execution_plan,
            requires_compatibility_confirmation=preflight.compatibility.requires_confirmation,
            requires_image_build=preflight.image_missing,
            missing_image_build_draft=preflight.missing_image_build_draft,
        )

    def build_execution_log_lines(self, execution_plan: RuntimeExecutionPlan) -> List[str]:
        """Return presentation-ready execution summary lines."""
        config = execution_plan.config
        return [
            f"Output Directory (Host): {execution_plan.output_dir_rel}",
            "\n[Environment Decision Engine]",
            f"Selected Runtime: {execution_plan.runtime_name}",
            f"Reason: {execution_plan.reason_text}",
            f"Image Tag: {config['image']}",
        ]

    def build_history_selection_reason(
        self,
        selection_mode: str,
        selected_rule: Optional[Dict[str, Any]],
    ) -> str:
        """Build a stable history reason string from selection context."""
        if selection_mode == "Manual":
            image_tag = (selected_rule or {}).get("image", "unknown")
            return f"Manual: {image_tag}"
        return "Auto: Detected"
