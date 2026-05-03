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

    def analyze(self, _code_text):
        return self._Probe()

    def summary(self, _code_text):
        return {"version": "2.7", "libraries": ["cv2"]}


class _ContainerManagerStub:
    def __init__(self, definition=None):
        self._definition = definition

    def is_version_compatible(self, code_ver, rule_ver):
        return code_ver == rule_ver

    def get_definition(self, _env_id):
        return self._definition

    def synthesize_definition_config(self, _analysis, base_rule_id):
        return {"id": base_rule_id, "tag": base_rule_id, "base_image": "python:2.7"}


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
