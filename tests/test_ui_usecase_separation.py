import sys
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from lcr.ui.main_window import MainWindow


def test_execute_save_and_build_uses_build_preparation_usecase(monkeypatch):
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()

    called = {"value": False}

    def fake_prepare(config):
        called["value"] = True
        return SimpleNamespace(
            tag="env-test",
            build_args=["docker", "build", "."],
        )

    monkeypatch.setattr(window.environment_build_preparation_use_case, "prepare", fake_prepare)
    monkeypatch.setattr(window.container_manager, "reload_definitions", lambda: None)
    monkeypatch.setattr(window, "_populate_runtime_combo", lambda: None)
    monkeypatch.setattr(window, "_start_worker", lambda args, script_name: None)

    window._execute_save_and_build({"tag": "env-test"})

    assert called["value"] is True
    app.quit()
