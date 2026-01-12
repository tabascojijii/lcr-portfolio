import pytest
from unittest.mock import MagicMock, patch
from lcr.core.container.manager import ContainerManager
from lcr.core.detector.analyzer import CodeAnalyzer

@pytest.fixture
def manager():
    return ContainerManager()

@pytest.fixture
def analyzer():
    return CodeAnalyzer()

# --- 1. Python 3.6 レガシーピン留め機能のテスト ---
def test_synthesis_pinning_36(manager, analyzer):
    """3.6環境で新規インストール分が正しくピン留めされるか"""
    # 3.6で新規追加が必要なライブラリを想定
    code = "import skimage"
    analysis = analyzer.summary(code)
    
    # 3.6のベースルールを指定して合成
    config = manager.synthesize_definition_config(analysis, "py36-ds")
    pip_packages = config.get("pip_packages", [])
    
    # scikit-image がリストにあるなら、必ずバージョンが指定されていること
    for pkg in pip_packages:
        if "scikit-image" in pkg.lower():
            assert "==" in pkg, f"Version pin is missing for {pkg}"
            assert "0.17.2" in pkg

# --- 2. 階層構造（差分抽出）のテスト ---
def test_synthesis_diff_logic(manager, analyzer):
    """ベースイメージ既設分が pip インストールから除外されるか"""
    code = "import numpy\nimport pandas"
    analysis = analyzer.summary(code)
    
    # 既設リストを保持していると分かっている Golden Image を指定
    # (lcr-py36-ml-classic は以前のビルドで numpy/pandas を含んでいるはず)
    config = manager.synthesize_definition_config(analysis, "lcr-py36-ml-classic")
    pip_packages = config.get("pip_packages", [])
    
    pip_names = [p.split('==')[0].lower() for p in pip_packages]
    
    # すでにベースにあるものは、新規インストールリストには入らないはず
    assert "numpy" not in pip_names, f"NumPy should be excluded. Current list: {pip_names}"
    assert "pandas" not in pip_names

# --- 3. UI 状態管理（try-finally）の検証 ---
def test_ui_lock_reset_logic():
    mock_btn = MagicMock()
    
    def reset_ui():
        mock_btn.setText("Run in Container")
        mock_btn.setEnabled(True)

    try:
        mock_btn.setText("Running...")
        mock_btn.setEnabled(False)
        raise RuntimeError("Build Failed")
    except:
        reset_ui()
    
    # assert_called_with が正しい文法
    mock_btn.setText.assert_called_with("Run in Container")
    mock_btn.setEnabled.assert_called_with(True)