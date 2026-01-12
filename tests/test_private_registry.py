import json
import pytest
from lcr.core.container.manager import ContainerManager
from lcr.core.container.generator import render_dockerfile

def test_private_registry_integration(tmp_path, monkeypatch):
    """
    Verify that pip_config in enterprise.json is correctly propagated to the Dockerfile.
    """
    # 1. Prepare enterprise.json with Private Registry settings
    overlay_data = {
        "_meta": {
            "pip_config": {
                "index_url": "https://pypi.my-company.com/simple",
                "trusted_host": "pypi.my-company.com"
            }
        }
    }
    
    enterprise_json = tmp_path / "enterprise.json"
    with open(enterprise_json, 'w', encoding='utf-8') as f:
        json.dump(overlay_data, f)
        
    # 2. Mock CWD so ContainerManager finds the enterprise.json
    monkeypatch.chdir(tmp_path)
    
    # 3. Initialize Manager and synthesize config
    mgr = ContainerManager()
    
    # Simulate an analysis result that requires some packages
    analysis_result = {
        "libraries": ["requests", "numpy"],
        "version": "3.10"
    }
    
    # Use a dummy base rule ID (or rely on fallback)
    # We need to make sure we have at least one rule or fallback works
    # The default manager usually has hardcoded rules.
    config = mgr.synthesize_definition_config(analysis_result, base_rule_id="py310-slim")
    
    # Check if pip_config is present in the synthesized config
    assert "pip_config" in config
    assert config["pip_config"]["index_url"] == "https://pypi.my-company.com/simple"
    assert config["pip_config"]["trusted_host"] == "pypi.my-company.com"
    
    # 4. Generate Dockerfile content
    dockerfile_content = render_dockerfile(config)
    
    # 5. Verify Dockerfile content
    print("\n--- Generated Dockerfile ---")
    print(dockerfile_content)
    print("----------------------------\n")
    
    # Check for the flags
    assert "--index-url https://pypi.my-company.com/simple" in dockerfile_content
    assert "--trusted-host pypi.my-company.com" in dockerfile_content
    
    # Check that packages are also installed
    assert "requests" in dockerfile_content
    assert "numpy" in dockerfile_content

def test_private_registry_fallback(tmp_path, monkeypatch):
    """
    Verify standard behavior when pip_config is missing.
    """
    # 1. Prepare enterprise.json WITHOUT pip_config
    overlay_data = {
        "some-lib": {"pip": ["v1.0"]}
    }
    
    enterprise_json = tmp_path / "enterprise.json"
    with open(enterprise_json, 'w', encoding='utf-8') as f:
        json.dump(overlay_data, f)
        
    # 2. Mock CWD
    monkeypatch.chdir(tmp_path)
    
    # 3. Generate
    mgr = ContainerManager()
    analysis_result = {"libraries": ["requests"], "version": "3.10"}
    config = mgr.synthesize_definition_config(analysis_result, base_rule_id="py310-slim")
    
    dockerfile_content = render_dockerfile(config)
    
    # 4. Assertions
    assert "--index-url" not in dockerfile_content
    assert "--trusted-host" not in dockerfile_content
    assert "requests" in dockerfile_content
