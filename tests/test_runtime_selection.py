import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / 'src'))

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
from lcr.core.container.manager import ContainerManager

@pytest.fixture
def manager():
    return ContainerManager()

def test_load_definitions_valid(manager):
    """Test loading valid JSON definitions."""
    # Mock path_helper.get_resource_path
    with patch('lcr.utils.path_helper.get_resource_path') as mock_get_path:
        # Create a real temporary directory for globbing
        mock_dir = MagicMock()
        mock_get_path.return_value = mock_dir
        
        # Mock glob to return a list of path objects
        json_path = MagicMock()
        json_path.stem = "test_env"
        json_path.name = "test_env.json"
        mock_dir.glob.return_value = [json_path]
        mock_dir.exists.return_value = True

        # Mock open/json loading
        mock_data = '{"tag": "test-image:1.0", "base_image": "python:3.8"}'
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch("json.load", return_value=json.loads(mock_data)):
                manager._load_definitions()
        
        # Verify rule was added
        rules = manager.get_available_runtimes()
        matching = [r for r in rules if r['id'] == "test_env"]
        assert len(matching) == 1
        assert matching[0]['image'] == "test-image:1.0"

def test_load_definitions_invalid(manager):
    """Test skipping invalid JSON definitions."""
    with patch('lcr.utils.path_helper.get_resource_path') as mock_get_path:
        mock_dir = MagicMock()
        mock_get_path.return_value = mock_dir
        mock_dir.exists.return_value = True
        
        json_path = MagicMock()
        json_path.stem = "broken_env"
        mock_dir.glob.return_value = [json_path]

        # Missing 'tag'
        mock_data = '{"base_image": "python:3.8"}' 
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch("json.load", return_value=json.loads(mock_data)):
                manager._load_definitions()
        
        # Verify rule was NOT added
        rules = manager.get_available_runtimes()
        matching = [r for r in rules if r['id'] == "broken_env"]
        assert len(matching) == 0

def test_override_run_config(manager):
    """Test prepare_run_config with manual override."""
    analysis = {'version': '3.x', 'libraries': []}
    
    # Override Rule
    override_rule = {
        "id": "override",
        "name": "Override",
        "version": "2.7",
        "libs": [],
        "image": "override-image",
        "triggers": []
    }
    
    # Mock script path existence
    # Note: We must NOT mock Path.resolve globally as it breaks internal logic (finding project root)
    with patch('pathlib.Path.exists', return_value=True):
         with patch('lcr.core.container.manager.ContainerManager.select_image') as mock_select:
            config = manager.prepare_run_config(
                analysis, 
                "C:/mock/data/script.py", # Absolute path to avoid resolve issues
                override_image_rule=override_rule
            )
            
            # Verify select_image was NOT called (or result ignored)
            # Actually logic is: if override provided, don't call select_image?
            # My implementation calls it only in else block.
            mock_select.assert_not_called()
            
            # Verify image is override image
            assert config['image'] == "override-image"
