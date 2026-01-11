
# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional
from .types import ExecutionHistory
from lcr.utils.path_helper import get_user_data_path, get_log_path

class HistoryManager:
    """
    Manages persistence of execution history.
    Ensures portability by storing paths relative to the project root.
    
    Compatible with both development and PyInstaller frozen modes.
    Uses atomic writes to prevent data corruption.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Args:
            storage_path: Path to the JSON file. Defaults to data/history.json (uses path_helper).
        """
        if storage_path:
            self.storage_path = Path(storage_path).resolve()
        else:
            # CRITICAL FIX: Use 'data/history.json' NOT 'src/data/history.json'
            # This ensures correct paths in both dev (c:/dev/lcr/data/history.json)
            # and frozen modes (dist/LCR/data/history.json)
            self.storage_path = get_user_data_path('data/history.json')
            
        self.project_root = self._find_project_root()
        
        # Self-Healing: Ensure directory and file exist
        self._ensure_storage_ready()
        
        print(f"[HistoryManager] Initialized successfully")
        print(f"[HistoryManager] Storage Path: {self.storage_path}")
        print(f"[HistoryManager] Project Root: {self.project_root}")

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
    
    def _ensure_storage_ready(self) -> None:
        """
        Self-Healing: Create directory and empty history file if missing.
        """
        try:
            # Create data/ directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create empty history.json if it doesn't exist
            if not self.storage_path.exists():
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False)
                print(f"[HistoryManager] Created new history file: {self.storage_path}")
        except Exception as e:
            self._log_error(f"Failed to initialize storage: {e}")

    def load_history(self) -> List[ExecutionHistory]:
        """
        Load history records with UTF-8 encoding.
        """
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self._log_error(f"Failed to load history: {e}")
            return []

    def save_record(self, record: ExecutionHistory) -> None:
        """
        Save a new execution record using atomic writes.
        Converts absolute paths to relative paths before saving.
        Uses temporary file + os.replace() to prevent corruption.
        """
        try:
            history = self.load_history()
            
            # Portable Path Conversion
            portable_record = record.copy()
            portable_record['script_path'] = self._to_relative(record['script_path'])
            portable_record['output_dir'] = self._to_relative(record['output_dir'])
            
            history.append(portable_record)
            
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # ATOMIC WRITE: Write to temporary file first, then replace
            # This prevents corruption if app crashes during save
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.storage_path.parent,
                prefix='.history_temp_',
                suffix='.json',
                text=True
            )
            
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
                
                # Atomic replace (overwrites target if exists)
                os.replace(temp_path, self.storage_path)
                
                print(f"[HistoryManager] Record saved successfully ({len(history)} total entries)")
                
            except Exception as e:
                # Clean up temp file if save failed
                try:
                    os.remove(temp_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            self._log_error(
                f"Failed to save history record:\n"
                f"  Path: {self.storage_path}\n"
                f"  Error: {e}\n"
                f"  Record: {record}"
            )

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
    
    def _log_error(self, message: str) -> None:
        """
        Log error to both stderr and lcr_debug.log.
        Essential for --noconsole mode troubleshooting.
        """
        error_msg = f"[HistoryManager ERROR] {message}"
        
        # Log to stderr
        print(error_msg, file=sys.stderr)
        
        # Log to lcr_debug.log for frozen mode
        try:
            log_path = get_log_path('lcr_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {error_msg}\n")
        except Exception:
            # Don't let logging failures break the app
            pass
