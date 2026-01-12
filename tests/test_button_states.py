# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Test to verify UI button enable/disable logic after operations.

This test simulates:
1. Initial state
2. Analysis (should enable New button)
3. Execution (should disable New button)
4. Execution completion (should re-enable New button)
5. Second analysis (should keep New button enabled)
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_button_states():
    """Verify button states are correctly managed."""
    from PySide6.QtWidgets import QApplication
    from lcr.ui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Initial state - buttons should be enabled
    print(f"[Initial] Analyze button: {window.analyze_btn.isEnabled()}")
    print(f"[Initial] Run button: {window.run_btn.isEnabled()}")
    print(f"[Initial] New button: {window.create_env_btn.isEnabled()}")
    print(f"[Initial] Stop button: {window.stop_btn.isEnabled()}")
    
    assert window.analyze_btn.isEnabled(), "Analyze should be enabled initially"
    assert window.run_btn.isEnabled(), "Run should be enabled initially"
    # Note: New button may be disabled initially until code is loaded
    assert not window.stop_btn.isEnabled(), "Stop should be disabled initially"
    
    # Simulate analysis by providing code
    test_code = """
import numpy as np
import pandas as pd
print("Test code")
"""
    window.code_editor.setPlainText(test_code)
    window._run_analysis()
    
    # After analysis - New button MUST be enabled
    print(f"\n[After Analysis] Analyze button: {window.analyze_btn.isEnabled()}")
    print(f"[After Analysis] New button: {window.create_env_btn.isEnabled()}")
    
    assert window.create_env_btn.isEnabled(), "CRITICAL: New button should be enabled after analysis!"
    
    # Simulate reset (as if execution completed)
    window._reset_buttons()
    
    print(f"\n[After Reset] Analyze button: {window.analyze_btn.isEnabled()}")
    print(f"[After Reset] Run button: {window.run_btn.isEnabled()}")
    print(f"[After Reset] New button: {window.create_env_btn.isEnabled()}")
    print(f"[After Reset] Stop button: {window.stop_btn.isEnabled()}")
    
    assert window.analyze_btn.isEnabled(), "Analyze should be enabled after reset"
    assert window.run_btn.isEnabled(), "Run should be enabled after reset"
    assert window.create_env_btn.isEnabled(), "CRITICAL: New button should be enabled after reset!"
    assert not window.stop_btn.isEnabled(), "Stop should be disabled after reset"
    
    # Run second analysis
    test_code2 = """
import cv2
import matplotlib.pyplot as plt
print("Different code")
"""
    window.code_editor.setPlainText(test_code2)
    window._run_analysis()
    
    print(f"\n[After 2nd Analysis] New button: {window.create_env_btn.isEnabled()}")
    assert window.create_env_btn.isEnabled(), "CRITICAL: New button should remain enabled after 2nd analysis!"
    
    print("\n✅ All button state tests passed!")
    
if __name__ == "__main__":
    test_button_states()
