from pathlib import Path

from lcr.core.architecture import SignalSlotNamingAuditUseCase


def test_signal_slot_naming_audit_detects_ui_violations(tmp_path):
    ui_file = tmp_path / "ui.py"
    ui_file.write_text(
        "\n".join(
            [
                "from PySide6.QtCore import Signal, Slot",
                "",
                "class W:",
                "    badSignal = Signal(str)",
                "",
                "    @Slot()",
                "    def finished_task(self):",
                "        return None",
            ]
        ),
        encoding="utf-8",
    )

    report = SignalSlotNamingAuditUseCase().audit_ui_paths(tmp_path)
    assert report["violation_count"] == 2
    assert sorted(v.violation_type for v in report["violations"]) == ["signal_naming", "slot_naming"]


def test_signal_slot_naming_audit_passes_existing_ui():
    report = SignalSlotNamingAuditUseCase().audit_ui_paths(Path("src/lcr/ui"))
    assert report["files_scanned"] > 0
    assert report["signals_scanned"] > 0
    assert report["slots_scanned"] > 0
    assert report["violation_count"] == 0
