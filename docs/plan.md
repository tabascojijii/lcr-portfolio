# LCR 実装計画 (Architect Plan)

- **作成日**: 2026-05-02
- **作成者**: Architect
- **対象ブランチ**: `codex/ai-agent-system-trial`
- **必須達成条件**: `pytest tests/` 全件 PASS（SKIPPED 許容、FAILED/ERROR は 0）

---

## 1. 現状分析

### 1.1 テスト状態（`pytest tests/` 実行結果）

| テストファイル | 状態 | 根本原因 |
|---|---|---|
| `test_dialog_reason_display.py` | **CRASH** | ヘッドレス環境で `from PySide6.QtWidgets import QApplication` を実行 → DLL ロード失敗（0xC0000139） |
| `test_analyzer.py::test_file` | **ERROR** | `def test_file(filepath: str, ...)` の引数 `filepath` を pytest が fixture として解釈、fixture が未定義でエラー |
| `test_button_states.py::test_button_states` | **FAIL** | 同様のPySide6 DLL クラッシュ |
| `test_intelligence_phase1.py::test_resolve_packages_via_pypi` | **FAIL** | `requests` が `apt-first` ルートを通り `python3-requests` として分類され、`pip` リストに入らない |
| `test_synthesis_intelligence.py::test_synthesis_diff_logic` | **FAIL** | テストが `"lcr-py36-ml-classic"` をルール ID として渡しているが、正しいルール ID は `"py36-ds"` のため差分抽出が機能しない |

21件 PASSED、3件 FAILED、1件 ERROR、1件 CRASH。

### 1.2 Phase 4 実装状態

| 機能 | 実装状況 | 所在 |
|---|---|---|
| Knowledge Update（ビルド成功時の自動追記） | 実装済 | `ContainerManager.save_user_knowledge()` ・アトミック書き込み（`os.replace`）実装済 |
| Real-time Feedback（ビルドログ逐次表示） | 実装済 | `ContainerWorker.log_updated` Signal、1行ごとに emit |
| Dynamic Refresh（再起動不要な即時反映） | 実装済 | ダイアログ終了後に `reload_definitions()` + `_refresh_env_list()` |

実装は存在するが、**再検証シナリオ**（ID消失・フリーズ・ロールバック）の自動テストが不足している。

### 1.3 `reference_standards.md` 準拠状況

| 基準 | 状態 | 詳細 |
|---|---|---|
| Dockerfile `FROM` ダイジェスト固定（§2） | **未実装** | `base.Dockerfile.j2` が可変タグを使用 |
| ALCOA++ 実行ハッシュ記録（§3） | **部分実装** | スナップショットコピーはあるが、`git_commit` / `source_hash` の記録なし |
| Humble Object パターン（§4） | **違反** | `main_window.py` 1252行・UI クラスが Docker コマンド構築・`subprocess.run` を直接実行 |
| インターフェース規律（§4） | **未実装** | `abc.ABC` / `typing.Protocol` 未使用 |
| `constraints.txt` による pip デッドロック回避（§2） | **未実装** | Dockerfile テンプレートに `constraints.txt` の仕組みがない |
| アーカイブ・リポジトリへのリダイレクト（§2） | **条件付き実装済** | `base.Dockerfile.j2` に `{% if use_archive_repo %}` 分岐あり（`archive.debian.org` 対応）。EOL スタックビルド時に `use_archive_repo=True` が正しく渡されることの検証が必要 |
| マルチステージビルド（§2） | **未実装** | `base.Dockerfile.j2` にマルチステージ構成（`FROM ... AS builder` / `COPY --from`）が存在しない |
| シグナル・スロット命名規則（§4） | **調査済・概ね準拠** | `ContainerWorker`: `log_updated`, `error_occurred`, `finished_with_code`（過去分詞）、スロット `_on_worker_output`, `_on_worker_finished`（動詞形）— §4 準拠。P2-2 で新規追加するシグナル・スロットにも同規則を適用すること |

---

## 2. 問題分類と優先度

### P0 — Blocker（テスト全件 PASS に必須）

| No. | 問題 | 修正場所 |
|---|---|---|
| P0-1 | `test_dialog_reason_display.py` クラッシュ | `tests/test_dialog_reason_display.py` |
| P0-2 | `test_analyzer.py::test_file` の ERROR | `tests/test_analyzer.py` |
| P0-3 | `test_button_states.py` DLL クラッシュ | `tests/test_button_states.py` |
| P0-4 | `test_resolve_packages_via_pypi` FAIL | `src/lcr/core/detector/analyzer.py` または `library.json` |
| P0-5 | `test_synthesis_diff_logic` FAIL | `tests/test_synthesis_intelligence.py` |

### P1 — 重要（業界標準準拠・`reference_standards.md` §2, §3）

| No. | 問題 |
|---|---|
| P1-1 | Dockerfile `FROM` 句への SHA256 ダイジェスト固定 |
| P1-2 | ALCOA++ 監査証跡（`execution_manifest.json` への `git_commit` + `source_hash` + `image_digest` + 入力ファイルハッシュ記録） |
| P1-3 | `constraints.txt` による pip デッドロック回避 |
| P1-4 | アーカイブ・リポジトリの EOL ビルド時デフォルト有効化検証 |
| P1-5 | マルチステージビルド対応（OpenCV 等 C++ ライブラリ） |

### P2 — 品質（`reference_standards.md` §4）

| No. | 問題 |
|---|---|
| P2-1 | `IContainerWorker(abc.ABC)` インターフェース定義 |
| P2-2 | `MainWindow` から Docker コマンド構築ロジックを `Presenter` に移譲（Humble Object） |

---

## 3. フェーズ別実装計画

### Step 1: テスト全件 PASS（P0）

**担当: Implementer**  
**合格判定: Auditor（`pytest tests/ -v` にて 0 FAILED, 0 ERROR を確認）**

---

#### P0-1: `tests/test_dialog_reason_display.py` の修正

このファイルは `QApplication` を直接起動する統合スクリプトであり、自動テストとして設計されていない。  
pytest が収集しても GUI 環境がなければ即クラッシュする。

**修正方針**: ファイル冒頭で PySide6 が利用不可の環境では pytest 収集をスキップさせる。

```python
# tests/test_dialog_reason_display.py の先頭に追加
pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 Qt widgets not available in headless environment"
)
```

---

#### P0-2: `tests/test_analyzer.py::test_file` の修正

現状の `def test_file(filepath: str, ...)` は pytest に `filepath` という fixture を要求する関数として誤検知される。  
この関数はスクリプト実行用のヘルパーであり、pytest の discovery 対象外にする必要がある。

**修正方針**: 関数名を `test_` プレフィックスから外す。

```python
# 変更前
def test_file(filepath: str, expected_version: str = None, expected_libs: list = None):

# 変更後
def _analyze_file(filepath: str, expected_version: str = None, expected_libs: list = None):
```

`main()` 内の呼び出し箇所も `_analyze_file(...)` に合わせて修正する。

---

#### P0-3: `tests/test_button_states.py` の修正

P0-1 と同様の DLL クラッシュ。

**修正方針**:

```python
# tests/test_button_states.py の先頭に追加
pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 Qt widgets not available in headless environment"
)
```

---

#### P0-4: `test_resolve_packages_via_pypi` の修正

`analyzer.resolve_packages(["requests"])` が `pip` リストに `requests` を返さない。  
原因: `CodeAnalyzer` の内部ロジックが `requests` を `apt-first` として分類し `python3-requests` を返す。

**調査手順**:
1. `src/lcr/core/detector/mappings/library.json` で `requests` の定義を確認
2. `CodeAnalyzer.resolve_packages()` の `apt-first` 判定ロジックを確認

**修正方針（優先順）**:
- `library.json` に `requests` のエントリが `apt: ["python3-requests"]` のみであれば、`pip: ["requests"]` を追加する
- または `CodeAnalyzer.resolve_packages()` が `apt` と `pip` の両方に候補があるとき、`pip` を優先するよう修正する

**テストの期待値**:
```python
result = analyzer.resolve_packages(["requests"])
pip_list = [p.lower() for p in result.get("pip", [])]
assert "requests" in pip_list  # pip 経由でインストール可能であること
```

---

#### P0-5: `test_synthesis_diff_logic` の修正

テストが `synthesize_definition_config(analysis, "lcr-py36-ml-classic")` を呼び出しているが、  
`"lcr-py36-ml-classic"` はイメージタグであり、ルール ID ではない。

`IMAGE_RULES` のハードコード定義:
```python
{"id": "py36-ds", "image": "lcr-py36-ml-classic", "installed_packages": ["numpy", "pandas", ...]}
```

`synthesize_definition_config` はルール ID で検索するため、`"lcr-py36-ml-classic"` をキーとした場合はマッチしない。  
結果としてデフォルトルール（`py310-slim`、`installed_packages=[]`）が選択され、差分抽出が機能しない。

**修正方針**: テスト側の呼び出しを正しいルール ID に修正する。

```python
# 変更前
config = manager.synthesize_definition_config(analysis, "lcr-py36-ml-classic")

# 変更後
config = manager.synthesize_definition_config(analysis, "py36-ds")
```

---

### Step 2: Phase 4 再検証

**担当: Implementer**  
**合格判定: Auditor（下記チェックリストによる手動確認 + 自動テスト）**

#### 再検証シナリオ

| シナリオ | 確認手順 | 合格基準 |
|---|---|---|
| 1. 過去の遺産の救済テスト | 既存環境 ID（例: `3.10test5`）を選択してビルドを実行 | 環境 ID が `custom-env` 等に化けず、`user_knowledge.json` の知識が発動してビルド成功 |
| 2. 新規作成の即時反映テスト | 「New」ボタンで新規環境を作成し、ダイアログ終了後にコンボボックスを確認 | アプリ再起動不要で即座にリストへ追加される |
| 3. 失敗とキャンセルの安全性テスト | ビルド中に「Stop」押下、または意図的に失敗する定義でビルド | クラッシュなし・`rollback_definition()` が呼ばれ JSON ファイルが削除される |

#### 追加する自動テスト

Phase 4 の核心となるメソッドに単体テストを追加する（`tests/test_user_knowledge.py` を拡張または新規作成）:

```python
# atomic write の検証
def test_save_user_knowledge_atomic(tmp_path, monkeypatch):
    """アトミック書き込みで一時ファイルが最終ファイルに置き換わることを確認"""
    ...

# キャッシュ無効化の検証
def test_metadata_cache_invalidation():
    """save_user_knowledge 後に _metadata キャッシュが None になること"""
    ...

# ロールバックの検証
def test_rollback_definition(tmp_path):
    """rollback_definition が JSON ファイルを削除し IMAGE_RULES から除去すること"""
    ...
```

---

### Step 3: 業界標準準拠（P1/P2）

**担当: Implementer**  
**合格判定: Auditor（コードレビュー＋テスト）**

---

#### P1-1: Dockerfile `FROM` ダイジェスト固定（`reference_standards.md` §2）

**現状**: `base.Dockerfile.j2` が `FROM {{ base_image }}` （可変タグ）を使用

**修正方針**:

1. `library.json` の `_meta.golden_images` に各ベースイメージの `digest` を追加:
   ```json
   "golden_images": {
     "python:2.7-slim": {
       "digest": "sha256:c1234...",
       "pre_installed": [...]
     }
   }
   ```

2. `base.Dockerfile.j2` テンプレートを修正（`else` フォールバックを**削除**し、ダイジェストなしビルドを禁止）:
   ```dockerfile
   FROM {{ base_image }}@{{ base_image_digest }}
   ```
   ※ JSON 側に `sha256:` プレフィックスを含めることで二重プレフィックス問題を回避する。

3. `render_dockerfile(config)` が `base_image_digest` を `library.json` から自動解決するよう `generator.py` を修正。`base_image_digest` が空または未定義の場合は **ビルド前に `ValueError` を raise** し、可変タグでのビルドを防止する:
   ```python
   if not config.get("base_image_digest"):
       raise ValueError(
           f"base_image_digest is required for image '{config['base_image']}'. "
           "Add SHA256 digest to library.json golden_images."
       )
   ```

**Auditor 確認基準**: 
- 生成された Dockerfile の `FROM` 行に `@sha256:` が含まれること
- `base_image_digest` 未設定時にジェネレータが `ValueError` を送出すること
- `{% else %}` フォールバック分岐が存在しないこと

---

#### P1-2: ALCOA++ 監査証跡（`reference_standards.md` §3）

**現状**: `prepare_run_config()` でスナップショットコピーはあるが暗号学的ハッシュ未記録

**修正方針**: `prepare_run_config()` の末尾で `execution_manifest.json` を出力ディレクトリに書き出す:

```python
manifest = {
    "timestamp": datetime.datetime.now().isoformat(),
    "git_commit": _get_git_commit_hash(),         # git rev-parse HEAD
    "source_hash": hashlib.sha256(script_content.encode()).hexdigest(),
    "image": config["image"],
    "image_digest": _get_image_digest(config["image"]),  # docker image inspect
    "script_path": str(script_path_obj),           # プロジェクトルートからの相対パス
    "input_file_hashes": _hash_input_files(input_files),  # 入力データファイルの SHA-256
}
with open(host_output_dir / "execution_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
```

ヘルパー関数:
```python
def _get_git_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def _get_image_digest(image: str) -> str:
    """実行時のコンテナイメージダイジェストを取得する（ALCOA++ §3 準拠）"""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", "--format={{index .RepoDigests 0}}", image],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def _hash_input_files(input_files: list) -> dict:
    """入力ファイルの SHA-256 ハッシュを計算する"""
    hashes = {}
    for f in input_files or []:
        try:
            hashes[str(f)] = hashlib.sha256(Path(f).read_bytes()).hexdigest()
        except Exception:
            hashes[str(f)] = "error"
    return hashes
```

**Auditor 確認基準**: 
- 実行後、`data/results/<timestamp>/execution_manifest.json` に `git_commit`, `source_hash`, `image_digest` が存在すること
- `image_digest` が `sha256:` で始まるダイジェスト値であること（`unknown` は REJECT）
- 入力ファイルが存在する場合、`input_file_hashes` に各ファイルの SHA-256 が含まれること

---

---

#### P1-3: `constraints.txt` による pip デッドロック回避（`reference_standards.md` §2）

**現状**: `base.Dockerfile.j2` の `pip install` に `--constraint` オプションが存在しない

**修正方針**:

1. `generator.py` で `constraints.txt` をビルドコンテキストにコピーし、`pip install` コマンドに `--constraint /app/constraints.txt` を追加する:
   ```python
   # generator.py の render_dockerfile() 内
   if config.get("constraints_file"):
       shutil.copy(config["constraints_file"], build_context_dir / "constraints.txt")
       config["use_constraints"] = True
   ```

2. `base.Dockerfile.j2` テンプレートに制約ファイルのコピーと適用を追加:
   ```dockerfile
   # constraints.txt によるデッドロック回避
   {% if use_constraints %}
   COPY constraints.txt /app/constraints.txt
   {% endif %}

   # 4. Python Libraries
   {% if pip_packages %}
   RUN pip install --no-cache-dir \
   {% if use_constraints %}    --constraint /app/constraints.txt \
   {% endif -%}
   ...
   ```

**Auditor 確認基準**: 生成済み Dockerfile の `pip install` コマンドに `--constraint` オプションが含まれること

---

#### P1-4: アーカイブ・リポジトリの EOL ビルド時デフォルト有効化検証（`reference_standards.md` §2）

**現状**: `base.Dockerfile.j2` に `{% if use_archive_repo %}` 分岐あり（`archive.debian.org` 対応済み）。ただし EOL スタック（Python 2.7、Python 3.6 等）のビルド時に `use_archive_repo=True` が確実に渡されることが検証されていない。

**修正方針**: `generator.py` の `render_dockerfile()` で、ベースイメージが EOL スタックと判定される場合（`library.json` の `golden_images` に `eol: true` フラグがある、またはイメージ名が `python:2.7` / `python:3.6` 等のパターン）に `use_archive_repo` を自動的に `True` にセットする:
```python
EOL_IMAGE_PATTERNS = ["python:2.", "python:3.5", "python:3.6"]
if any(config["base_image"].startswith(p) for p in EOL_IMAGE_PATTERNS):
    config.setdefault("use_archive_repo", True)
```

**Auditor 確認基準**: Python 2.7 ベースイメージを使用するビルドで生成された Dockerfile に `archive.debian.org` のソース設定が含まれること

---

#### P1-5: マルチステージビルド対応（`reference_standards.md` §2）

**現状**: `base.Dockerfile.j2` はシングルステージのみ。OpenCV 等 C++ ライブラリのビルドツールチェーンが実行イメージに残存するリスクがある。

**修正方針**: `library.json` の `golden_images` に `multi_stage: true` フラグが設定されたイメージに対し、マルチステージ構成を持つ専用テンプレート `multistage.Dockerfile.j2` を生成で選択する:

```dockerfile
# multistage.Dockerfile.j2 の構造（例: OpenCV ビルド）
FROM {{ base_image }}@{{ base_image_digest }} AS builder
RUN apt-get update && apt-get install -y cmake g++ libopencv-dev ...
RUN <ビルドコマンド>

FROM {{ base_image }}@{{ base_image_digest }} AS runtime
COPY --from=builder /usr/local/lib/python*/dist-packages/cv2* /usr/local/lib/...
...
```

`generator.py` で `config.get("multi_stage")` が真の場合に `multistage.Dockerfile.j2` を選択するよう分岐を追加する。

**Auditor 確認基準**: OpenCV を含む定義のビルドで生成された Dockerfile に `AS builder` と `COPY --from=builder` が含まれること

---

#### P2-1: `IContainerWorker` インターフェース定義（`reference_standards.md` §4）

**修正方針**: `src/lcr/core/interface.py` を更新し、`IContainerWorker` を定義する:

```python
# src/lcr/core/interface.py
import abc
from typing import Protocol

class IContainerWorker(abc.ABC):
    """コンテナ実行ワーカーの抽象インターフェース。
    テスト用モックはこのインターフェースを実装すること。
    """
    @abc.abstractmethod
    def start(self) -> None: ...

    @abc.abstractmethod
    def stop(self) -> None: ...
```

`ContainerWorker(QThread, IContainerWorker)` として継承を追加。

---

#### P2-2: Humble Object パターン適用（`reference_standards.md` §4）

**現状**: `MainWindow._run_container()` が以下のロジックを直接実行している（UIクラスにビジネスロジックが混在）:
- `subprocess.run(["docker", "image", "inspect", ...])` の呼び出し
- `prepare_run_config()` の呼び出し
- `ContainerWorker` の生成と起動

**修正方針**: `MainWindow` は「謙虚なオブジェクト」とし、ロジックを `MainWindowPresenter` に移譲する。

移譲対象:
- `_run_container()` 内の Docker コマンド構築・イメージ存在確認ロジック → `Presenter.prepare_execution(script_path, selected_rule)`
- `_on_worker_finished()` 内の History 保存ロジック → `Presenter.on_execution_finished(exit_code, record_data)`

`MainWindow` は `Presenter` のコールバックを受けて UI 更新のみを行う。

**シグナル・スロット命名規則（`reference_standards.md` §4）**: `Presenter` や `MainWindowPresenter` で新規追加するシグナル・スロットは §4 命名規則に必ず準拠すること:
- シグナル: 過去分詞形（例: `execution_started`, `execution_finished`, `status_changed`）
- スロット: 動作を示す動詞形（例: `update_status`, `show_result`, `reset_ui`）

**Auditor 確認基準**: 
- P2-2 で追加したシグナル名がすべて過去分詞形であること
- P2-2 で追加したスロット名がすべて動作動詞形であること
- `MainWindow` が `subprocess.run` を直接呼び出していないこと

---

## 4. 合格基準チェックリスト（Auditor 用）

### 4.1 テスト

- [ ] `pytest tests/ -v` → **0 FAILED, 0 ERROR**
- [ ] SKIPPED は `pytest.importorskip` によるヘッドレス環境スキップのみ許容
- [ ] 追加した Phase 4 の単体テスト（atomic write、キャッシュ無効化、ロールバック）が PASSED

### 4.2 Phase 4 機能（manual 確認）

- [ ] 既存環境 ID を選択してビルドした際、ID が `custom-env` に変化しない
- [ ] Docker ビルドログが GUI コンソールにリアルタイム表示される（フリーズなし）
- [ ] `user_knowledge.json` への書き込みがアトミックである（一時ファイル経由）
- [ ] 新規環境作成後、アプリ再起動なしでコンボボックスに反映される
- [ ] ビルドキャンセル・失敗時にロールバックが動作しクラッシュしない

### 4.3 業界標準準拠

- [ ] 生成された Dockerfile の `FROM` 行に `@sha256:` ダイジェストが含まれる（P1-1）
- [ ] `base_image_digest` 未設定時に `generator.py` が `ValueError` を raise する（P1-1）
- [ ] 実行後に `execution_manifest.json` が `git_commit`, `source_hash`, `image_digest` を含む（P1-2）
- [ ] `image_digest` フィールドが `sha256:` で始まるダイジェスト値である（P1-2）
- [ ] 入力ファイルが存在する場合、`input_file_hashes` が manifest に含まれる（P1-2）
- [ ] 生成された Dockerfile の `pip install` に `--constraint` オプションが含まれる（P1-3）
- [ ] Python 2.7 ベースイメージのビルドで `archive.debian.org` ソース設定が生成される（P1-4）
- [ ] OpenCV 含む定義のビルドで生成 Dockerfile に `AS builder` / `COPY --from=builder` が含まれる（P1-5）
- [ ] `ContainerWorker` が `IContainerWorker(abc.ABC)` を実装している（P2-1）
- [ ] `MainWindow` が `subprocess.run` を直接呼び出していない（P2-2）
- [ ] P2-2 追加シグナルが過去分詞形、追加スロットが動作動詞形の命名規則に準拠している（P2-2）

---

## 5. Auditor 判定基準（EMCSモデル準拠）

Auditor は主観的判断を排し、以下の客観的メトリクスで PASS / REJECT を判定すること:

| 違反カテゴリ | REJECT 判定基準 | ヒント（修正指示） |
|---|---|---|
| テスト合格 | `pytest tests/` に FAILED または ERROR が 1 件でも存在する | 上記 P0-1〜P0-5 の修正を適用せよ |
| データ完全性 | 実行後に `execution_manifest.json` が存在しない、または `git_commit` / `source_hash` / `image_digest` フィールドのいずれかが欠落 | `ContainerManager.prepare_run_config()` に manifest 書き出しと `_get_image_digest()` を追加せよ |
| インターフェース規律 | `ContainerWorker` が `abc.ABC` または `Protocol` を継承していない | `src/lcr/core/interface.py` に `IContainerWorker` を定義し継承させよ |
| 単一責任の原則 | `MainWindow` が `subprocess.run` / Docker コマンド構築を直接実行している | `MainWindowPresenter` へのロジック移譲が未完了 |
| ビルド再現性 | 生成 Dockerfile の `FROM` 行にダイジェストがなく可変タグのみ、または `else` フォールバックが存在する | `base.Dockerfile.j2` の `{% else %}` を削除し、`generator.py` に `ValueError` バリデーションを追加せよ |
| pip デッドロック回避 | 生成 Dockerfile の `pip install` に `--constraint` オプションが存在しない | `generator.py` と `base.Dockerfile.j2` に `constraints.txt` 組み込みを追加せよ（P1-3） |
| アーカイブリポジトリ | EOL スタック（Python 2.7 等）のビルドで `archive.debian.org` ソース設定が存在しない | `generator.py` に EOL イメージ自動検出と `use_archive_repo=True` デフォルト設定を追加せよ（P1-4） |
| マルチステージビルド | OpenCV 等 C++ ライブラリを含むビルドで `COPY --from=builder` が使用されていない | `multistage.Dockerfile.j2` を作成し、`generator.py` で `multi_stage` フラグによるテンプレート選択を追加せよ（P1-5） |
| 命名規則 | P2-2 追加シグナルが過去分詞形でない、またはスロットが動作動詞形でない | `reference_standards.md` §4 の命名規則に従いリネームせよ |

---

## 6. 実装順序サマリー

```
[Step 1] P0 テスト修正 (P0-1〜P0-5)
    → Auditor: pytest 0 FAILED, 0 ERROR を確認
         ↓
[Step 2] Phase 4 再検証 + 追加テスト
    → Auditor: manual シナリオ 3件 + 自動テストで合格確認
         ↓
[Step 3-a] P1-2 ALCOA++ manifest 記録 (最小変更・高価値)
           ※ image_digest + input_file_hashes を含む
[Step 3-b] P1-1 Dockerfile ダイジェスト固定
           ※ else フォールバック削除 + ValueError バリデーション
[Step 3-c] P1-3 constraints.txt によるpipデッドロック回避
[Step 3-d] P1-4 アーカイブリポジトリの EOL ビルド時自動有効化
[Step 3-e] P1-5 マルチステージビルド対応（OpenCV 等）
[Step 3-f] P2-1 IContainerWorker インターフェース
[Step 3-g] P2-2 Humble Object（規模大・慎重に実施）
           ※ 新規シグナル・スロットは §4 命名規則に準拠
    → Auditor: 各チェックリスト項目を検証
```

各ステップ完了後、Implementer は差分（Diff）を提出し、Auditor は本計画の合格基準に基づいて PASS / REJECT を判定する。  
REJECT の際は、違反箇所・違反した制約・修正ヒントを含む処方的メッセージを返すこと（`reference_standards.md` §1 準拠）。
