"""
Headless verification for LCR GUI components.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from PySide6.QtWidgets import QApplication
    from lcr.ui.main_window import MainWindow
    
    # Create app
    app = QApplication(sys.argv)
    
    # Create window (do not show)
    window = MainWindow()
    
    # Verify components exist
    assert window.script_path_edit is not None, "Script selection widget missing"
    assert window.code_editor is not None, "Code editor widget missing"
    assert window.run_btn is not None, "Run button missing"
    assert window.console_log is not None, "Console log missing"
    
    print("[SUCCESS] MainWindow instantiated with all components.")
    
except Exception as e:
    print(f"[ERROR] GUI Verification Failed: {e}")
    sys.exit(1)
