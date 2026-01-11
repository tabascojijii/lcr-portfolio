"""
Entry point for Legacy Code Reviver GUI.
"""
# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

import sys
import os
from pathlib import Path

# Add src to path (dev mode only)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Import path helper early
from lcr.utils.path_helper import get_log_path

# Check Execution Mode: Conditional logging redirection
# - Frozen Mode (EXE): Redirect stdout/stderr to lcr_debug.log for persistent debugging
# - Dev Mode (Source): DO NOT redirect - keep logs printing to terminal console
try:
    if getattr(sys, 'frozen', False):
        # Running as packaged EXE - redirect all output to log file
        log_path = get_log_path('lcr_debug.log')
        log_file = open(log_path, 'w', encoding='utf-8')
        sys.stdout = log_file
        sys.stderr = log_file
        print(f"[LCR] Application starting (Frozen Mode)... Logs redirected to: {log_path}")
        print(f"[LCR] Python: {sys.version}")
        print(f"[LCR] Frozen: True")
    else:
        # Running from source - preserve normal terminal output for development workflow
        print(f"[LCR] Application starting (Dev Mode)... Logging to terminal console")
        print(f"[LCR] Python: {sys.version}")
        print(f"[LCR] Frozen: False")
except Exception as e:
    # Fallback: if logging setup fails, continue without it
    print(f"Warning: Could not setup logging: {e}", file=sys.__stderr__)

from PySide6.QtWidgets import QApplication
from lcr.ui.main_window import MainWindow


def main():
    print("[LCR] Initializing Qt Application...")
    app = QApplication(sys.argv)
    print("[LCR] Creating Main Window...")
    window = MainWindow()
    window.show()
    print("[LCR] Entering event loop...")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
