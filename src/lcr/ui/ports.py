from typing import Any, Callable, Dict, List, Optional, Protocol


class ContainerManagerPort(Protocol):
    def get_available_runtimes(self) -> List[Dict[str, Any]]: ...
    def resolve_runtime(self, search_terms: List[str], version_hint: str) -> Dict[str, Any]: ...
    def synthesize_definition_config(self, analysis: Dict, rec_id: str) -> Dict: ...
    def reload_definitions(self) -> None: ...
    def validate_environment(self) -> None: ...
    def is_version_compatible(self, code_ver: str, rule_ver: str) -> bool: ...
    def prepare_run_config(
        self,
        analysis_result: Dict[str, Any],
        script_path: str,
        data_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        override_image_rule: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...
    def get_docker_run_args(self, config: RunConfig) -> List[str]: ...
    def get_definition(self, env_id: str) -> Optional[Dict]: ...
    def get_build_command(self, dockerfile_path: str, tag: str) -> List[str]: ...
    def commit_definition(self, def_id: str) -> bool: ...
    def rollback_definition(self, def_id: str) -> None: ...
    def apply_legacy_pins(self, pip_pkgs: List[str], version: str) -> List[str]: ...


class AnalyzerPort(Protocol):
    def summary(self, code_text: str) -> Dict[str, Any]: ...
    def analyze(self, code_text: Optional[str] = None) -> Any: ...


class AuditMetadataPort(Protocol):
    def collect(
        self,
        image_name: str,
        script_path: str,
        script_path_rel: str,
        param_payload: Optional[Dict] = None,
        input_files: Optional[List[str]] = None,
        input_files_rel: Optional[List[str]] = None,
        output_files: Optional[List[str]] = None,
        output_files_rel: Optional[List[str]] = None,
        log_path: Optional[str] = None,
        log_path_rel: Optional[str] = None,
    ) -> Dict[str, Any]: ...


class HistoryManagerPort(Protocol):
    def save_record(self, record: Dict[str, Any]) -> None: ...
    def load_history(self) -> List[Dict[str, Any]]: ...
    def get_absolute_path(self, relative_path: str) -> str: ...
    def to_relative_path(self, path_str: str) -> str: ...


class EnvironmentDialogPort(Protocol):
    def open_creation_dialog(
        self,
        *,
        parent: Any,
        base_images: List[Dict[str, Any]],
        initial_config: Dict[str, Any],
        recommended_base_id: str,
        recommendation_reason: str,
    ) -> Optional[Dict[str, Any]]: ...


class ContainerExecutionGatewayPort(Protocol):
    def execute(
        self,
        on_log: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> int: ...
    def stop(self) -> None: ...


class ContainerExecutionGatewayFactoryPort(Protocol):
    def __call__(
        self,
        *,
        docker_args: List[str],
        script_name: str,
    ) -> ContainerExecutionGatewayPort: ...
