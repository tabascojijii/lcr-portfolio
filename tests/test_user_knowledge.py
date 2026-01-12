"""
Test suite for Knowledge Persistence System (3-layer architecture).

Tests:
1. User knowledge override priority
2. Normalization consistency
3. Save functionality
4. Non-invasive fallback (missing user_knowledge.json)
5. update_mapping deprecation
"""
import pytest
import json
import os
from pathlib import Path
from lcr.core.container.manager import ContainerManager
from lcr.core.detector.analyzer import CodeAnalyzer


@pytest.fixture
def test_user_knowledge_path():
    """Fixture that ensures cleanup of test user_knowledge.json"""
    path = Path.cwd() / "user_knowledge.json"
    yield path
    # Cleanup after test
    if path.exists():
        path.unlink()


def test_user_knowledge_override(test_user_knowledge_path):
    """Test that user_knowledge.json overrides library.json mappings."""
    # Setup: Create test user_knowledge.json
    user_data = {
        "_meta": {
            "description": "Test user knowledge",
            "version": "1.0"
        },
        "numpy": {
            "pip": ["numpy-custom-build"],
            "apt": []
        }
    }
    
    with open(test_user_knowledge_path, 'w', encoding='utf-8') as f:
        json.dump(user_data, f)
    
    # Initialize manager (should load all 3 layers)
    manager = ContainerManager()
    lib_info = manager.get_library_info()
    
    # Check that numpy mapping is from user knowledge
    assert "numpy" in lib_info, "numpy should be in merged library info"
    numpy_mapping = lib_info["numpy"]
    assert numpy_mapping["pip"] == ["numpy-custom-build"], f"Expected custom build, got {numpy_mapping['pip']}"
    assert numpy_mapping.get("_source") == "User Knowledge", "Should be marked as from User Knowledge"
    
    print("[TEST PASS] User knowledge overrides base library.json")


def test_missing_user_knowledge_graceful(test_user_knowledge_path):
    """Test that system works normally without user_knowledge.json."""
    # Ensure file doesn't exist
    if test_user_knowledge_path.exists():
        test_user_knowledge_path.unlink()
    
    # Should not crash
    manager = ContainerManager()
    analyzer = CodeAnalyzer(mappings=manager.get_library_info())
    
    # Analyze simple code
    code = "import pandas"
    analysis = analyzer.summary(code)
    
    assert "pandas" in analysis["libraries"], "pandas should be detected"
    print("[TEST PASS] System works without user_knowledge.json")


def test_update_mapping_disabled(test_user_knowledge_path):
    """Test that update_mapping no longer modifies library.json."""
    analyzer = CodeAnalyzer()
    
    # Get library.json path and modification time
    mapping_path = Path(__file__).parent.parent / "src" / "lcr" / "core" / "detector" / "mappings" / "library.json"
    if not mapping_path.exists():
        pytest.skip("library.json not found")
    
    original_mtime = mapping_path.stat().st_mtime
    
    # Call the deprecated method
    analyzer.update_mapping("test_import", {"pip": ["test-pkg"], "apt": []})
    
    # Check that library.json was NOT modified
    new_mtime = mapping_path.stat().st_mtime
    assert new_mtime == original_mtime, "library.json should NOT be modified by update_mapping"
    
    print("[TEST PASS] update_mapping is disabled")


def test_save_user_knowledge(test_user_knowledge_path):
    """Test saving and reloading user knowledge."""
    # Cleanup
    if test_user_knowledge_path.exists():
        test_user_knowledge_path.unlink()
    
    # Create manager and save knowledge
    manager = ContainerManager()
    manager.save_user_knowledge("custom_lib", {
        "pip": ["custom-package==1.0.0"],
        "apt": []
    })
    
    # Verify file was created
    assert test_user_knowledge_path.exists(), "user_knowledge.json should be created"
    
    # Read and verify content
    with open(test_user_knowledge_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check normalization (aggressive: all separators removed)
    normalized_key = "customlib"  # custom_lib → customlib (underscore removed)
    assert normalized_key in data, f"Should contain normalized key '{normalized_key}'"
    assert data[normalized_key]["pip"] == ["custom-package==1.0.0"]
    
    # Create new manager instance (fresh load)
    manager2 = ContainerManager()
    lib_info = manager2.get_library_info()
    
    # Verify the mapping is available
    assert normalized_key in lib_info, "New manager should load saved knowledge"
    assert lib_info[normalized_key]["pip"] == ["custom-package==1.0.0"]
    assert lib_info[normalized_key].get("_source") == "User Knowledge"
    
    print("[TEST PASS] save_user_knowledge persists and reloads correctly")


def test_normalization_consistency(test_user_knowledge_path):
    """Test that name normalization works (aggressive: remove all separators)."""
    manager = ContainerManager()
    
    # Save with hyphenated name
    manager.save_user_knowledge("scikit-image", {
        "pip": ["scikit-image==0.19.0"],
        "apt": []
    })
    
    # Verify it was saved with normalized key
    with open(test_user_knowledge_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Should be normalized to scikitimage (all separators removed: -, _, .)
    assert "scikitimage" in data, "Should use normalized key scikitimage"
    
    # Reload and verify lookup works
    manager2 = ContainerManager()
    lib_info = manager2.get_library_info()
    
    assert "scikitimage" in lib_info, "Should be accessible with normalized key"
    
    print("[TEST PASS] Name normalization works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
