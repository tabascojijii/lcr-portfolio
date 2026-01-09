"""
Test script for CodeAnalyzer.

Tests the analyzer against sample Python files to verify:
- Python 2.7 detection
- Python 3.x detection
- Library import detection (especially cv2)
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from lcr.core.detector.analyzer import CodeAnalyzer, analyze_code_file


def print_separator(title: str):
    """Print a formatted separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_file(filepath: str, expected_version: str = None, expected_libs: list = None):
    """
    Test a single file with the analyzer.
    
    Args:
        filepath: Path to the file to analyze
        expected_version: Expected Python version (for validation)
        expected_libs: Expected libraries to be detected
    """
    print(f"\n[FILE] Analyzing: {filepath}")
    print("-" * 70)
    
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            code_text = f.read()
        
        # Analyze
        analyzer = CodeAnalyzer()
        result = analyzer.summary(code_text)
        
        # Display results
        print(f"  Python Version: {result['version']}")
        print(f"  Libraries: {', '.join(result['libraries']) if result['libraries'] else 'None'}")
        
        if result['library_hints']:
            print(f"  Library Hints:")
            for lib, hint in result['library_hints'].items():
                if hint:
                    print(f"    - {lib}: {hint}")
        
        # Validation
        if expected_version:
            if result['version'] == expected_version:
                print(f"[PASS] Version check (expected: {expected_version})")
            else:
                print(f"[FAIL] Version check (expected: {expected_version}, got: {result['version']})")
        
        if expected_libs:
            missing = set(expected_libs) - set(result['libraries'])
            if not missing:
                print(f"[PASS] Library check (found all expected: {expected_libs})")
            else:
                print(f"[FAIL] Library check (missing: {list(missing)})")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all analyzer tests."""
    print_separator("CodeAnalyzer Test Suite")
    
    # Define test cases
    samples_dir = project_root / 'data' / 'samples'
    
    test_cases = [
        {
            'file': samples_dir / 'python2_basic.py',
            'expected_version': '2.7',
            'expected_libs': ['sys'],
            'description': 'Python 2.7 basic syntax (print without parentheses, except with comma)'
        },
        {
            'file': samples_dir / 'python3_modern.py',
            'expected_version': '3.x',
            'expected_libs': ['os'],
            'description': 'Python 3.x modern syntax (type hints, f-strings)'
        },
        {
            'file': samples_dir / 'legacy_cv_calc.py',
            'expected_version': '2.7',
            'expected_libs': ['cv2', 'numpy'],
            'description': 'Legacy OpenCV code with Python 2 syntax'
        },
    ]
    
    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print_separator(f"Test Case {i}: {test_case['description']}")
        result = test_file(
            str(test_case['file']),
            test_case.get('expected_version'),
            test_case.get('expected_libs')
        )
        results.append({
            'file': test_case['file'].name,
            'result': result,
            'passed': result is not None
        })
    
    # Summary
    print_separator("Test Summary")
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    print(f"\n[RESULTS] {passed}/{total} tests completed successfully")
    
    for r in results:
        status = "[PASS]" if r['passed'] else "[FAIL]"
        print(f"  {status}: {r['file']}")
    
    print("\n" + "=" * 70)
    
    # Additional validation checks
    print_separator("Validation Summary")
    
    print("\n[VALIDATION] Key Validation Points:")
    print("1. python2_basic.py detected as '2.7'? ", end="")
    py2_result = next((r for r in results if 'python2_basic' in r['file']), None)
    if py2_result and py2_result['result'] and py2_result['result']['version'] == '2.7':
        print("[YES]")
    else:
        print("[NO]")
    
    print("2. legacy_cv_calc.py detected cv2 import? ", end="")
    legacy_result = next((r for r in results if 'legacy_cv_calc' in r['file']), None)
    if legacy_result and legacy_result['result'] and 'cv2' in legacy_result['result']['libraries']:
        print("[YES]")
    else:
        print("[NO]")
    
    print("3. python3_modern.py detected as '3.x'? ", end="")
    py3_result = next((r for r in results if 'python3_modern' in r['file']), None)
    if py3_result and py3_result['result'] and py3_result['result']['version'] == '3.x':
        print("[YES]")
    else:
        print("[NO]")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
