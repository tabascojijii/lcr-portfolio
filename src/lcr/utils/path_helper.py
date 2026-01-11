# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Path resolution helper for PyInstaller frozen and development modes.

Provides utilities to correctly locate resources (templates, definitions)
and user data (history, results) in both modes.
"""

import os
import sys
from pathlib import Path


def is_frozen():
    """Check if running in PyInstaller frozen mode."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource file or directory.
    
    Resources are read-only assets bundled with the application
    (templates, definitions, LICENSE, etc.).
    
    Args:
        relative_path: Path relative to the bundled resources root.
                      Example: 'templates', 'definitions/py36_ml.json'
    
    Returns:
        Absolute Path object pointing to the resource.
    
    Example:
        >>> get_resource_path('templates')
        # Frozen: C:/dist/LCR/_internal/templates
        # Dev: C:/dev/lcr/src/lcr/core/container/templates
    """
    if is_frozen():
        # In frozen mode, resources are extracted to sys._MEIPASS
        base_path = Path(sys._MEIPASS)
        return base_path / relative_path
    else:
        # In development mode, locate resources from source structure
        # Actual locations:
        # - templates: src/lcr/core/container/templates
        # - definitions: src/lcr/core/container/definitions
        
        # Get project root (where run_gui.py is located)
        project_root = Path(__file__).resolve().parents[3]  # path_helper.py -> utils -> lcr -> src -> root
        
        # Map known resources to their actual locations
        if relative_path.startswith('templates'):
            base = project_root / 'src' / 'lcr' / 'core' / 'container'
            return base / relative_path
        elif relative_path.startswith('definitions'):
            base = project_root / 'src' / 'lcr' / 'core' / 'container'
            return base / relative_path
        else:
            # For other resources (like LICENSE), check from project root
            return project_root / relative_path


def get_user_data_path(relative_path: str) -> Path:
    """
    Get absolute path to a user data file or directory.
    
    User data includes writable files like history.json, results/, etc.
    These are stored next to the executable in frozen mode for portability.
    
    Args:
        relative_path: Path relative to the user data root.
                      Example: 'data/history.json', 'data/results'
    
    Returns:
        Absolute Path object pointing to the user data location.
    
    Example:
        >>> get_user_data_path('data/history.json')
        # Frozen: C:/dist/LCR/data/history.json (next to LCR.exe)
        # Dev: C:/dev/lcr/src/data/history.json
    """
    if is_frozen():
        # In frozen mode, use directory containing the executable
        exe_dir = Path(sys.executable).parent
        return exe_dir / relative_path
    else:
        # In development mode, use project root
        project_root = Path(__file__).resolve().parents[3]  # path_helper.py -> utils -> lcr -> src -> root
        return project_root / relative_path


def get_log_path(log_filename: str = 'lcr_debug.log') -> Path:
    """
    Get the path for the application log file.
    
    Always writes to a writable location (next to exe in frozen mode).
    
    Args:
        log_filename: Name of the log file.
    
    Returns:
        Absolute Path object for the log file.
    """
    if is_frozen():
        # Write next to the executable
        return Path(sys.executable).parent / log_filename
    else:
        # Write to project root in dev mode
        project_root = Path(__file__).resolve().parents[3]
        return project_root / log_filename
