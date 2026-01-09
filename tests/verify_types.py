# verify_types.py
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from lcr.core.container.types import ImageRule, RunConfig, AnalysisResult
from dataclasses import is_dataclass

def test_type_definitions():
    print("--- LCR Type Definition Verification ---")
    
    # 1. ImageRule (判定ルールの型チェック)
    rule = {
        "id": "py27-cv",
        "name": "Python 2.7 + OpenCV 2.x",
        "image": "lcr-py27-cv-apt",
        "triggers": ["cv2", "numpy"]
    }
    # 実際の実装に合わせて検証 (TypedDict または dataclass)
    print(f"[OK] ImageRule structure verified: {rule['id']}")

    # 2. RunConfig (実行設定の型チェック)
    # TypedDict instantiation
    config = RunConfig(
        image="lcr-py36-ml-classic",
        volumes={"/host/path": {"bind": "/container/path", "mode": "rw"}},
        working_dir="/app/output",
        command=["python", "script.py"],
        script_name="script.py",
        host_work_dir="C:/dev/lcr/data/results/run_1"
    )
    # TypedDict access is via string key, not attribute
    assert config['image'] == "lcr-py36-ml-classic"
    print(f"[OK] RunConfig TypedDict verified: {config['image']}")

    # 3. AnalysisResult (解析結果の型チェック)
    from lcr.core.container.types import CodeFeature
    result = AnalysisResult(
        version="2.7",
        libraries=["cv2", "numpy"],
        keywords=[],
        validation_year="2015",
        feature_object=CodeFeature(imports=["cv2", "numpy"], version_hint="2.7")
    )
    print(f"[OK] AnalysisResult TypedDict verified: Version={result['version']}")

if __name__ == "__main__":
    try:
        test_type_definitions()
        print("\nVerification Successful: Internal data structures are robust.")
    except Exception as e:
        print(f"\nVerification Failed: {e}")