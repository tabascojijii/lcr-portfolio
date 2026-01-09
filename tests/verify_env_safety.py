# verify_env_safety.py
import sys
import os
import shutil
from pathlib import Path

# Add src to path
# We are in tests/, so src is ../src
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from lcr.core.container.manager import ContainerManager, DockerUnavailableError
from lcr.core.container.types import AnalysisResult, CodeFeature

def test_environment_and_safety():
    print("--- LCR Environment & Safety Verification ---")
    manager = ContainerManager()

    # 1. Docker Daemon Check
    print("Checking Docker status...")
    try:
        manager.validate_environment()
        print("[OK] Docker daemon is reachable.")
    except DockerUnavailableError:
        print("[CAUTION] Docker is NOT running. This is expected if you turned it off.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    # 2. Path Conflict Safety Test
    print("\nChecking path conflict safety...")
    
    # Setup dummy data
    input_path = os.path.abspath("data/samples")
    dummy_feature = CodeFeature(
        validation_year="2020",
        imports=["os"],
        keywords=[],
        version_hint="3.x"
    )
    dummy_result: AnalysisResult = {
        "version": "3.x",
        "libraries": ["os"],
        "keywords": [],
        "validation_year": "2020",
        "feature_object": dummy_feature
    }
    
    # Make sure invalid script path survives the 'exists' check if possible, or use a real file
    # The manager checks `if not script_path_obj.exists(): raise FileNotFoundError`
    # So we need a real file.
    real_script_path = os.path.join(input_path, "test.py")
    if not os.path.exists(real_script_path):
        # Create a dummy file if it doesn't exist
        os.makedirs(input_path, exist_ok=True)
        with open(real_script_path, 'w') as f:
            f.write("print('hello')")
    
    try:
        # Attempt to set output dir to the same as input dir
        print(f"Attempting to set output to: {input_path}")
        
        # Note: The manager derives host_input_dir from script_path.parent
        # script_path is data/samples/test.py -> parent is data/samples
        # output_dir is data/samples -> Collision!
        
        manager.prepare_run_config(
            analysis_result=dummy_result,
            script_path=real_script_path,
            output_dir=input_path
        )
        print("[FAIL] Safety check bypassed! (This is bad)")
    except ValueError as e:
        print(f"[OK] Safety check blocked the run: {e}")
    except Exception as e:
        print(f"[ERROR] Wrong exception type: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_environment_and_safety()
