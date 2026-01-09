
import sys
import os
import shutil
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from lcr.core.container.manager import ContainerManager
from lcr.core.container.types import AnalysisResult, CodeFeature

def test_output_path_logic():
    print("Testing Output Path Logic...")
    
    manager = ContainerManager()
    
    # Mock Analysis Result
    mock_result: AnalysisResult = {
        "version": "2.7",
        "libraries": ["cv2"],
        "keywords": [],
        "validation_year": None,
        "feature_object": CodeFeature(imports=["cv2"], version_hint="2.7")
    }
    
    # Create dummy script and directories
    test_dir = Path("tests/temp_output_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    
    script_path = test_dir / "test_script.py"
    script_path.touch()
    
    input_dir = test_dir
    output_target_dir = test_dir / "custom_output"
    output_target_dir.mkdir()
    
    print(f"Input Dir: {input_dir.resolve()}")
    print(f"Target Output: {output_target_dir.resolve()}")

    # Test 1: Successful Custom Path
    print("\n[Test 1] Custom Path Validity")
    try:
        config = manager.prepare_run_config(
            mock_result,
            str(script_path),
            output_dir=str(output_target_dir)
        )
        host_work_dir = Path(config['host_work_dir'])
        print(f"Result Host Work Dir: {host_work_dir}")
        
        # Verify it is a subdir of target
        if output_target_dir.resolve() in host_work_dir.parents:
            print("PASS: Host work dir is inside custom output dir.")
        else:
            print("FAIL: Host work dir is NOT inside custom output dir.")
            
        # Verify timestamp format
        if "LCR_RUN_" in host_work_dir.name:
            print("PASS: Subdirectory created with timestamp.")
        else:
            print("FAIL: Subdirectory missing timestamp.")

    except Exception as e:
        print(f"FAIL: Exception raised: {e}")

    # Test 2: Collision Check
    print("\n[Test 2] Collision with Input")
    try:
        manager.prepare_run_config(
            mock_result,
            str(script_path),
            output_dir=str(input_dir) # Pointing to same dir as script
        )
        print("FAIL: Should have raised ValueError for collision.")
    except ValueError as e:
        print(f"PASS: Caught expected ValueError: {e}")
    except Exception as e:
        print(f"FAIL: Caught unexpected exception: {type(e).__name__}: {e}")

    # Cleanup
    # shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_output_path_logic()
