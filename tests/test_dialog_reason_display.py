# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Quick test to verify the recommendation reason display in the Create Environment Dialog.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager
from lcr.ui.create_env_dialog import EnvironmentCreationDialog

def test_dialog_with_reason():
    """Test dialog shows recommendation reason properly."""
    app = QApplication(sys.argv)
    
    # Sample Python 3 code with ML libraries
    sample_code = """
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage import filters

def analyze_otolith(image_path):
    img = cv2.imread(image_path, 0)
    edges = filters.sobel(img)
    df = pd.DataFrame(edges)
    print("Analysis complete. Data shape:", df.shape)
"""
    
    # Analyze
    analyzer = CodeAnalyzer()
    manager = ContainerManager()
    
    analysis = analyzer.summary(sample_code)
    feature = analyzer.analyze(sample_code)
    
    search_terms = feature.imports + feature.keywords
    if feature.validation_year:
        search_terms.append(f"year:{feature.validation_year}")
    
    # Get recommendation
    recommended_rule = manager.resolve_runtime(search_terms, feature.version_hint)
    rec_id = recommended_rule['id']
    rec_reason = recommended_rule.get('reason', 'Best match')
    
    print(f"\n[Test] Recommended Rule: {recommended_rule['name']}")
    print(f"[Test] Reason: {rec_reason}")
    
    # Synthesize config
    initial_config = manager.synthesize_definition_config(analysis, rec_id)
    
    print(f"[Test] Config pip packages: {initial_config.get('pip_packages', [])}")
    print(f"[Test] Config skipped packages: {initial_config.get('_skipped_packages', [])}")
    
    # Show dialog
    dialog = EnvironmentCreationDialog(
        None,
        manager.get_available_runtimes(),
        initial_config,
        rec_id,
        rec_reason
    )
    
    print("\n[Test] Dialog created successfully. Opening...")
    dialog.exec()
    
    sys.exit(0)

if __name__ == "__main__":
    test_dialog_with_reason()
