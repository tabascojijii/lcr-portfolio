
# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

import json
import os
from pathlib import Path
from typing import List, Optional
from .types import ExecutionHistory
from lcr.utils.path_helper import get_user_data_path

class HistoryManager:
    """
    Manages persistence of execution history.
    Ensures portability by storing paths relative to the project root.
    
    Compatible with both development and PyInstaller frozen modes.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Args:
            storage_path: Path to the JSON file. Defaults to data/history.json (uses path_helper).
        """
        if storage_path:
            self.storage_path = Path(storage_path).resolve()
        else:
            # Use path_helper to resolve data/history.json in both dev and frozen modes
            self.storage_path = get_user_data_path('src/data/history.json')
            
        self.project_root = self._find_project_root()
        print(f"[HistoryManager] Initialized. Storage Path: {self.storage_path}")

    def _find_project_root(self) -> Path:
        """Find project root (folder containing src)."""
        # Heuristic: go up until we find 'src' folder or 'run_gui.py'
        # Starting from this file: src/lcr/core/history/manager.py
        current = Path(__file__).resolve().parent
        for _ in range(5):
            if (current / "src").exists() or (current / "run_gui.py").exists():
                return current
            current = current.parent
        return Path.cwd() # Fallback

    def load_history(self) -> List[ExecutionHistory]:
        """Load history records."""
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_record(self, record: ExecutionHistory) -> None:
        """
        Save a new execution record.
        Converts absolute paths to relative paths before saving.
        """
        history = self.load_history()
        
        # Portable Path Conversion
        portable_record = record.copy()
        portable_record['script_path'] = self._to_relative(record['script_path'])
        portable_record['output_dir'] = self._to_relative(record['output_dir'])
        
        history.append(portable_record)
        
        # Create dir if not exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def _to_relative(self, path_str: str) -> str:
        """Convert absolute path to relative if within project root."""
        try:
            p = Path(path_str).resolve()
            return str(p.relative_to(self.project_root))
        except ValueError:
            # Path is not inside project root, keep as absolute
            return path_str
            
    def get_absolute_path(self, relative_path: str) -> str:
        """Evaluate stored relative path to absolute path on current system."""
        p = Path(relative_path)
        if p.is_absolute():
            return str(p)
        return str((self.project_root / p).resolve())
