import pytest
import os
from unittest.mock import MagicMock
from lcr.core.container.manager import ContainerManager

@pytest.fixture
def manager(tmp_path):
    # テスト用の manager インスタンス
    mgr = ContainerManager()
    # 定義ディレクトリを一時フォルダに向ける
    mgr.definitions_dir = str(tmp_path)
    # IMAGE_RULES をリセット
    mgr.IMAGE_RULES = [] 
    return mgr

def test_atomic_rollback(manager):
    """ビルド失敗時にファイルが消えることを確認"""
    config = {"id": "test_env_fail", "image": "base", "libs": []}
    
    # 1. 仮保存
    filepath = manager.save_definition_provisional(config)
    assert os.path.exists(filepath)
    assert manager.is_transaction_pending("test_env_fail")
    assert any(r['id'] == "test_env_fail" for r in manager.IMAGE_RULES)
    
    # 2. ロールバック実行 (ビルド失敗を想定)
    manager.rollback_definition("test_env_fail")
    
    # 3. 検証: ファイルもメモリ上のデータも消えていること
    assert not os.path.exists(filepath)
    assert not manager.is_transaction_pending("test_env_fail")
    assert not any(r['id'] == "test_env_fail" for r in manager.IMAGE_RULES)

def test_atomic_commit(manager):
    """ビルド成功時にファイルが残ることを確認"""
    config = {"id": "test_env_success", "image": "base", "libs": []}
    
    # 1. 仮保存
    filepath = manager.save_definition_provisional(config)
    
    # 2. コミット実行 (ビルド成功を想定)
    manager.commit_definition("test_env_success")
    
    # 3. 検証: ファイルが存在し、ペンディング状態が解除されていること
    assert os.path.exists(filepath)
    assert not manager.is_transaction_pending("test_env_success")
    assert any(r['id'] == "test_env_success" for r in manager.IMAGE_RULES)