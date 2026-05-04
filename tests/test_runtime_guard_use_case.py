from lcr.core.container.use_cases import RuntimeExecutionPreparationUseCase


def test_prepare_guard_blocks_when_required_import_is_missing():
    use_case = RuntimeExecutionPreparationUseCase()

    result = use_case.prepare_guard(
        required_imports=["numpy", "cv2"],
        environment_capability={"python": "3.10", "imports": ["numpy"]},
    )

    assert result["guard_state"] == "blocked"
    assert result["can_run"] is False
    assert result["mismatch_result"]["missing"] == ["cv2"]
    assert result["mismatch_result"]["mismatch_count"] == 1


def test_prepare_guard_passes_when_all_required_imports_are_supported():
    use_case = RuntimeExecutionPreparationUseCase()

    result = use_case.prepare_guard(
        required_imports=["numpy", "pandas"],
        environment_capability={"imports": ["pandas", "numpy", "matplotlib"]},
    )

    assert result["guard_state"] == "pass"
    assert result["can_run"] is True
    assert result["mismatch_result"]["missing"] == []
    assert result["mismatch_result"]["matched"] == ["numpy", "pandas"]


def test_prepare_guard_normalizes_and_deduplicates_import_names():
    use_case = RuntimeExecutionPreparationUseCase()

    result = use_case.prepare_guard(
        required_imports=[" numpy ", "numpy", "", "cv2"],
        environment_capability={"imports": ["numpy", " numpy ", " "]},
    )

    assert result["required_imports"] == ["cv2", "numpy"]
    assert result["mismatch_result"]["capability_imports"] == ["numpy"]
    assert result["mismatch_result"]["missing"] == ["cv2"]


def test_prepare_guard_matches_imports_case_insensitively():
    use_case = RuntimeExecutionPreparationUseCase()

    result = use_case.prepare_guard(
        required_imports=["NumPy", "PANDAS"],
        environment_capability={"imports": ["numpy", "pandas"]},
    )

    assert result["guard_state"] == "pass"
    assert result["mismatch_result"]["matched"] == ["numpy", "pandas"]


class _AnalyzerStub:
    class _Probe:
        version_hint = "2.7"
        imports = ["cv2"]
        keywords = ["image"]
        validation_year = None

    def analyze(self, _code_text):
        return self._Probe()

    def summary(self, _code_text):
        return {"version": "2.7", "libraries": ["cv2"]}


class _ContainerManagerStub:
    def __init__(self, definition=None):
        self._definition = definition
        self._runtime_rule = {
            "id": "env-1",
            "name": "Env 1",
            "version": "2.7",
            "libs": ["cv2"],
            "image": "env-1",
            "triggers": ["cv2"],
        }

    def is_version_compatible(self, code_ver, rule_ver):
        return code_ver == rule_ver

    def get_definition(self, _env_id):
        return self._definition

    def synthesize_definition_config(self, _analysis, base_rule_id):
        return {"id": base_rule_id, "tag": base_rule_id, "base_image": "python:2.7"}

    def resolve_runtime(self, _search_terms, _version_hint):
        return self._runtime_rule

    def prepare_run_config(
        self,
        _analysis,
        _script_path,
        data_dir=None,
        output_dir=None,
        override_image_rule=None,
    ):
        image = (override_image_rule or self._runtime_rule)["image"]
        host_dir = output_dir or "results/run-1"
        return {
            "image": image,
            "host_work_dir": host_dir,
            "script_name": "script.py",
        }

    def get_docker_run_args(self, _config):
        return ["docker", "run", "env-1"]

    def get_available_runtimes(self):
        return [self._runtime_rule]


class _HistoryManagerStub:
    def to_relative_path(self, value):
        return value


def test_prepare_manual_compatibility_check_returns_confirmation_when_mismatch():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub()
    selected_rule = {"version": "3.10"}

    result = use_case.prepare_manual_compatibility_check(
        analyzer,
        manager,
        "print('x')",
        selected_rule,
        "Manual",
    )

    assert result.requires_confirmation is True
    assert "You selected 3.10" in result.message


def test_prepare_manual_compatibility_check_skips_when_not_manual():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub()

    result = use_case.prepare_manual_compatibility_check(
        analyzer,
        manager,
        "print('x')",
        {"version": "3.10"},
        "Auto",
    )

    assert result.requires_confirmation is False
    assert result.message == ""


def test_prepare_missing_image_build_draft_prefers_existing_definition():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub(definition={"base_image": "python:3.10"})

    result = use_case.prepare_missing_image_build_draft(
        analyzer,
        manager,
        "print('x')",
        {"id": "env-1"},
    )

    assert result.env_id == "env-1"
    assert result.initial_config["id"] == "env-1"
    assert result.initial_config["tag"] == "env-1"
    assert result.recommendation_reason.startswith("Rebuilding existing definition")
    assert result.base_images == [manager._runtime_rule]


def test_prepare_missing_image_build_draft_synthesizes_when_definition_missing():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub(definition=None)

    result = use_case.prepare_missing_image_build_draft(
        analyzer,
        manager,
        "print('x')",
        {"id": "env-2"},
    )

    assert result.env_id == "env-2"
    assert result.initial_config["id"] == "env-2"
    assert result.initial_config["tag"] == "env-2"
    assert result.recommendation_reason.startswith("Synthesized from code analysis")
    assert result.base_images == [manager._runtime_rule]


def test_prepare_run_preflight_builds_draft_when_image_missing():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub(definition={"base_image": "python:3.10"})
    history = _HistoryManagerStub()
    use_case.image_exists = lambda _name: False

    result = use_case.prepare_run_preflight(
        analyzer=analyzer,
        container_manager=manager,
        history_manager=history,
        code_text="print('x')",
        script_path="script.py",
        data_dir=None,
        output_dir="results/run-1",
        selected_rule={"id": "env-1", "version": "2.7", "image": "env-1"},
        selection_mode="Manual",
    )

    assert result.image_missing is True
    assert result.missing_image_build_draft is not None
    assert result.missing_image_build_draft.env_id == "env-1"
    assert result.execution_plan.config["image"] == "env-1"


def test_prepare_run_preflight_skips_draft_when_image_exists():
    use_case = RuntimeExecutionPreparationUseCase()
    analyzer = _AnalyzerStub()
    manager = _ContainerManagerStub(definition={"base_image": "python:3.10"})
    history = _HistoryManagerStub()
    use_case.image_exists = lambda _name: True

    result = use_case.prepare_run_preflight(
        analyzer=analyzer,
        container_manager=manager,
        history_manager=history,
        code_text="print('x')",
        script_path="script.py",
        data_dir=None,
        output_dir="results/run-1",
        selected_rule={"id": "env-1", "version": "2.7", "image": "env-1"},
        selection_mode="Manual",
    )

    assert result.image_missing is False
    assert result.missing_image_build_draft is None


def test_build_execution_log_lines_formats_runtime_summary():
    use_case = RuntimeExecutionPreparationUseCase()
    plan = use_case.prepare_execution_plan(
        analyzer=_AnalyzerStub(),
        container_manager=_ContainerManagerStub(),
        history_manager=_HistoryManagerStub(),
        code_text="print('x')",
        script_path="script.py",
        data_dir=None,
        output_dir="results/run-1",
        selected_rule={"id": "env-1", "name": "Env 1", "version": "2.7", "image": "env-1"},
    )

    lines = use_case.build_execution_log_lines(plan)

    assert lines[0] == "Output Directory (Host): results/run-1"
    assert "Selected Runtime: Env 1" in lines
    assert "Image Tag: env-1" in lines


def test_build_history_selection_reason_handles_manual_and_auto_modes():
    use_case = RuntimeExecutionPreparationUseCase()

    manual = use_case.build_history_selection_reason("Manual", {"image": "env-1"})
    auto = use_case.build_history_selection_reason("Auto", None)

    assert manual == "Manual: env-1"
    assert auto == "Auto: Detected"
