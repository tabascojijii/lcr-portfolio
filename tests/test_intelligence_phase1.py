import pytest
from unittest.mock import patch, MagicMock
from lcr.core.detector.analyzer import CodeAnalyzer
from lcr.core.container.manager import ContainerManager

@pytest.fixture
def analyzer():
    return CodeAnalyzer()

@pytest.fixture
def container_manager():
    return ContainerManager()

# --- 1. パッケージ解決の検証 ---
@patch("urllib.request.urlopen")
def test_resolve_packages_via_pypi(mock_urlopen, analyzer):
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = b'{"info": {"name": "requests"}}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response
    
    result = analyzer.resolve_packages(["requests"])
    pip_list = [p.lower() for p in result.get("pip", [])]
    
    # 候補として見つかっているなら、pipリストに入っているべき
    assert "requests" in pip_list

# --- 2. 推奨ロジックの検証（表記揺れ対応） ---
def test_base_recommendation_legacy(container_manager):
    mock_analysis = {"version": "2.7", "imports": ["cv2"], "year": 2015}
    res = container_manager.resolve_runtime(mock_analysis)
    rid = str(res.get("id") or "").lower()
    
    # '2.7' または '27' が含まれていれば合格
    assert "2.7" in rid or "27" in rid

def test_base_recommendation_py3(container_manager):
    mock_analysis = {"version": "3.10", "imports": ["numpy"], "year": 2024}
    res = container_manager.resolve_runtime(mock_analysis)
    rid = str(res.get("id") or "").lower()
    
    # Python 3系に対して 2系を勧めないこと
    assert "2" not in rid or "3" in rid
    assert "3" in rid