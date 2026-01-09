"""
Entry point for Legacy Code Reviver GUI.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from PySide6.QtWidgets import QApplication
from lcr.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
