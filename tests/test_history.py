
import unittest
import sys
import os
import shutil
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from lcr.core.history.manager import HistoryManager
from lcr.core.history.types import ExecutionHistory

class TestHistoryManager(unittest.TestCase):
    
    def setUp(self):
        # Create a temp history file
        self.test_dir = Path("tests/temp_history_test")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)
        self.history_file = self.test_dir / "test_history.json"
        
        self.manager = HistoryManager(str(self.history_file))
        
        # Override project root for consistent testing
        self.manager.project_root = Path.cwd()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_and_load_relative(self):
        """Test that paths are saved relatively and restored absolutely."""
        
        # Create dummy record with absolute paths
        abs_script = (self.manager.project_root / "data/samples/test.py").resolve()
        abs_output = (self.manager.project_root / "data/results/run1").resolve()
        
        record: ExecutionHistory = {
            "id": "123-456",
            "timestamp": "2026-01-01T12:00:00",
            "script_path": str(abs_script),
            "runtime_name": "Test Runtime",
            "image_tag": "test-image",
            "output_dir": str(abs_output),
            "status": "success"
        }
        
        # Save
        self.manager.save_record(record)
        
        # Verify JSON content is relative
        with open(self.history_file, 'r') as f:
            data = json.load(f)
            saved_script = data[0]['script_path']
            # Expecting normalized separators
            expected_rel = str(Path("data/samples/test.py"))
            self.assertEqual(Path(saved_script).as_posix(), Path(expected_rel).as_posix())
            
        # Load and Restore
        loaded_history = self.manager.load_history()
        loaded_record = loaded_history[0]
        
        # Check relative status in loaded object
        self.assertEqual(Path(loaded_record['script_path']).as_posix(), Path("data/samples/test.py").as_posix())
        
        # Check absolute restoration method
        restored_script = self.manager.get_absolute_path(loaded_record['script_path'])
        self.assertEqual(Path(restored_script).resolve(), abs_script)

    def test_outside_project_root(self):
        """Test that paths outside project root remain absolute."""
        outside_path = "C:/Outside/file.py" if os.name == 'nt' else "/tmp/file.py"
        
        record: ExecutionHistory = {
             "id": "789",
             "timestamp": "2026",
             "script_path": outside_path,
             "runtime_name": "test",
             "image_tag": "test",
             "output_dir": "test",
             "status": "success"
        }
        
        self.manager.save_record(record)
        
        loaded = self.manager.load_history()[0]
        self.assertEqual(loaded['script_path'], outside_path)

if __name__ == '__main__':
    unittest.main()
