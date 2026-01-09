
import sys
import os
import json
import uuid
import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from lcr.core.container.manager import ContainerManager
from lcr.core.history.manager import HistoryManager
from lcr.core.history.types import ExecutionHistory
from lcr.core.container.types import AnalysisResult, CodeFeature

def test_integration():
    print("--- LCR Backend Integration Verification ---")
    
    # 1. Setup Managers
    container_mgr = ContainerManager()
    history_mgr = HistoryManager()
    
    # 2. Prepare Mock Data
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "data/samples/test_artifact_gen.py"
    
    if not script_path.exists():
        print(f"[Skip] Mock script not found at {script_path}")
        return

    mock_result: AnalysisResult = {
        "version": "2.7",
        "libraries": ["cv2", "numpy"],
        "keywords": [],
        "validation_year": None,
        "feature_object": CodeFeature(imports=["cv2", "numpy"], version_hint="2.7")
    }
    
    print(f"Target Script: {script_path}")
    
    # 3. Simulate Run Preparation (Trigger Snapshot)
    print("\n[Step A] Verifying Snapshot Creation...")
    try:
        config = container_mgr.prepare_run_config(
            mock_result,
            str(script_path)
        )
        host_work_dir = Path(config['host_work_dir'])
        print(f"Generated Output Dir: {host_work_dir}")
        
        snapshot = host_work_dir / "source_snapshot.py"
        if snapshot.exists():
            print(f"[PASS] source_snapshot.py created successfully.")
        else:
            print(f"[FAIL] source_snapshot.py NOT found.")
            
    except Exception as e:
        print(f"[FAIL] Exception during prepare_run_config: {e}")
        return

    # 4. Simulate History Saving
    print("\n[Step B] Verifying History JSON Relative Paths...")
    
    record_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    record: ExecutionHistory = {
        "id": record_id,
        "timestamp": timestamp,
        "script_path": str(script_path), # Absolute path provided
        "runtime_name": "Test Runtime",
        "image_tag": config['image'],
        "output_dir": str(host_work_dir), # Absolute path provided
        "status": "success"
    }
    
    history_mgr.save_record(record)
    print("Record saved.")
    
    # 5. Check JSON content directly
    json_path = history_mgr.storage_path
    print(f"Checking {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        saved_record = next((r for r in data if r['id'] == record_id), None)
        
        if saved_record:
            saved_script = saved_record['script_path']
            saved_output = saved_record['output_dir']
            
            print(f"Saved Script Path: {saved_script}")
            print(f"Saved Output Path: {saved_output}")
            
            if not Path(saved_script).is_absolute() and not Path(saved_output).is_absolute():
                print("[PASS] Paths are relative.")
            else:
                print("[FAIL] Paths are ABSOLUTE (Should be relative).")
        else:
            print("[FAIL] Record not found in JSON.")

if __name__ == "__main__":
    test_integration()
