import sys
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from lcr.ui.main_window import MainWindow


def test_execute_save_and_build_uses_build_preparation_usecase(monkeypatch):
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()

    called = {"value": False}

    def fake_prepare_execution_plan(config, available_runtimes):
        called["value"] = True
        return SimpleNamespace(
            tag="env-test",
            build_args=["docker", "build", "."],
            selected_runtime_image="env-test",
        )

    monkeypatch.setattr(
        window.environment_build_preparation_use_case,
        "prepare_execution_plan",
        fake_prepare_execution_plan,
    )
    monkeypatch.setattr(
        window.environment_build_preparation_use_case,
        "list_available_runtimes",
        lambda: [],
    )
    monkeypatch.setattr(
        window.environment_build_preparation_use_case,
        "reload_runtime_definitions",
        lambda: None,
    )
    monkeypatch.setattr(window, "_populate_runtime_combo", lambda: None)
    monkeypatch.setattr(window, "_select_runtime_by_image_tag", lambda _: "env-test")
    monkeypatch.setattr(window, "_start_worker", lambda args, script_name: None)

    window._execute_save_and_build({"tag": "env-test"})

    assert called["value"] is True
    app.quit()
