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
