import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from lcr.core.container.manager import ContainerManager
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.detector.analyzer import CodeFeature

def verify():
    print("--- Verifying Runtime Logic for Python 3.6 ML ---")
    
    manager = ContainerManager()
    
    # 1. Mock Analysis Result for test_py36_ds.py
    # Code content implies: pandas usage, python 3 syntax
    print("\n1. Resolving Runtime...")
    
    # Simulating what analyzer.analyze() would return
    search_terms = ['pandas', 'sklearn', 'numpy', 'year:2017']
    version_hint = '3.x'
    
    rule = manager.resolve_runtime(search_terms, version_hint)
    print(f"Selected Rule: {rule['name']}")
    print(f"Image: {rule['image']}")
    print(f"Prepend Python (Rule Config): {rule.get('prepend_python')}")
    
    if rule['image'] != 'lcr-py36-ml-classic':
        print("❌ FAILED: Wrong image selected.")
        return

    # 2. Check Command Generation
    print("\n2. Checking Command Generation...")
    
    # Mock analysis result dict (legacy format for prepare_run_config)
    analysis_legacy = {
        "version": "3.x",
        "libraries": ["pandas", "sklearn"],
        "keywords": []
    }
    
    script_path = str(Path("data/samples/test_py36_ds.py").resolve())
    
    try:
        config = manager.prepare_run_config(analysis_legacy, script_path)
        command = config['command']
        print(f"Generated Command: {command}")
        
        # Verification Logic
        if command[0] == 'python':
            print("[FAIL] 'python' detected at start of command.")
            print("   LCR images with ENTRYPOINT ['python'] should NOT have 'python' in command.")
        else:
            print("[OK] SUCCESS: Command does not start with 'python'.")
            print(f"   Target script: {command[0]}")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    verify()
