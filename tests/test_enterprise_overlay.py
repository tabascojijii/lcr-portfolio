import json
import os
import pytest
from lcr.core.container.manager import ContainerManager

def test_enterprise_overlay_addition(tmp_path, monkeypatch):
    """
    Verify that enterprise.json in CWD allows adding NEW library definitions
    without affecting standard ones.
    """
    # 1. Prepare enterprise.json
    overlay_data = {
        "internal-tools": {
            "pip": ["internal-tools==1.0.0"],
            "apt": []
        }
    }
    enterprise_json = tmp_path / "enterprise.json"
    with open(enterprise_json, 'w', encoding='utf-8') as f:
        json.dump(overlay_data, f)
    
    # 2. Mock CWD to the temp directory
    monkeypatch.chdir(tmp_path)
    
    # 3. Load Manager
    mgr = ContainerManager()
    info = mgr.get_library_info()
    
    # 4. Assertions
    # New library should exist
    assert "internal-tools" in info, "Failed to load overlay library 'internal-tools'"
    assert info["internal-tools"]["pip"] == ["internal-tools==1.0.0"]
    
    # Standard library should still exist (e.g., numpy or PySide6 from standard library.json)
    # Checking PySide6 based on previous file read
    assert "PySide6" in info, "Standard library 'PySide6' missing after overlay"

def test_enterprise_overlay_deep_merge(tmp_path, monkeypatch):
    """
    Verify that enterprise.json performs a DEEP MERGE.
    It should update specific values in nested dictionaries without wiping out siblings.
    """
    # 1. Prepare enterprise.json with an override for legacy_versions
    # Standard library.json has:
    # "legacy_versions": { "3.6": { "scikit-image": "==0.17.2", ... } }
    
    overlay_data = {
        "_meta": {
            "legacy_versions": {
                "3.6": {
                    "scikit-image": "==0.19.0-custom",  # OVERRIDE existing
                    "new-lib": "==1.0.0"                # ADD new to existing dict
                }
            }
        }
    }
    
    enterprise_json = tmp_path / "enterprise.json"
    with open(enterprise_json, 'w', encoding='utf-8') as f:
        json.dump(overlay_data, f)
        
    # 2. Mock CWD
    monkeypatch.chdir(tmp_path)
    
    # 3. Load Manager
    mgr = ContainerManager()
    info = mgr.get_library_info()
    meta = info.get("_meta", {})
    legacy_36 = meta.get("legacy_versions", {}).get("3.6", {})
    
    # 4. Assertions
    # Check Override
    assert legacy_36.get("scikit-image") == "==0.19.0-custom", "Failed to override 'scikit-image' version"
    
    # Check Addition
    assert legacy_36.get("new-lib") == "==1.0.0", "Failed to add 'new-lib' to legacy_versions"
    
    # Check Preservation (Deep Merge)
    # 'matplotlib' should still be there from standard library.json
    assert "matplotlib" in legacy_36, "Deep merge failed: Sibling key 'matplotlib' was wiped out"
    assert legacy_36["matplotlib"] == "==3.3.4", "Sibling value corrupted"

def test_enterprise_overlay_invalid_json(tmp_path, monkeypatch, capsys):
    """
    Verify that invalid enterprise.json is gracefully skipped with a warning.
    """
    # 1. Create BROKEN enterprise.json
    enterprise_json = tmp_path / "enterprise.json"
    with open(enterprise_json, 'w', encoding='utf-8') as f:
        f.write("{ invalid json ...")
        
    # 2. Mock CWD
    monkeypatch.chdir(tmp_path)
    
    # 3. Load Manager
    mgr = ContainerManager()
    info = mgr.get_library_info()
    
    # 4. Assertions
    # Should still load standard libraries
    assert "PySide6" in info
    
    # Check stdout/stderr for warning (though logging might go to stderr or root logger)
    # Since print() was used in implementation:
    captured = capsys.readouterr()
    assert "[Enterprise] Warning: Invalid JSON" in captured.out or "[Enterprise] Warning: Invalid JSON" in captured.err

