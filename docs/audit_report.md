# Audit Report

## 1. Pytest Result

Command: `pytest tests/`

Result summary:
- collected: 34
- passed: 34
- failed: 0
- error: 0

Execution log (excerpt):
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\dev\lcr
collected 34 items
...
============================= 34 passed in 1.54s ==============================
```

## 2. Standards Compliance Audit (docs/reference_standards.md)

### Finding A (REJECT): PyQt/PySide Humble Object pattern violation
- Standard: `4. PyQt / PySide モダンUIアーキテクチャ標準` の `Humble Object パターンの適用`
- Reason:
  - View(UI) がユースケース調停・環境選定・ビルド分岐・履歴保存指示まで直接実行しており、UI層に業務ロジックが集中している。
  - `MainWindow` が肥大化しており、Presenter/ViewModel相当への移譲が不十分。
- Evidence:
  - `src/lcr/ui/main_window.py:617` (`_run_container`) で runtime解決、互換判定、build/run分岐を実行
  - `src/lcr/ui/main_window.py:446` (`_show_create_env_dialog`) で推奨環境解決・定義合成を直接実行
  - `src/lcr/ui/main_window.py:879` で履歴保存ユースケースをUIから直接実行
- Required fix:
  - 実行準備・環境解決・JIT build判定・履歴保存指示を Presenter / Application Service に移し、Viewは入力収集と表示更新に限定すること。

### Finding B (REJECT): Interface discipline erosion via private API call from UI
- Standard: `4. ... インターフェースによる規律`
- Reason:
  - UIから `ContainerManager` の private 相当メソッドへ直接アクセスしており、抽象境界が破れている。
- Evidence:
  - `src/lcr/ui/main_window.py:692` で `self.container_manager._check_version_compat(...)` を直接呼び出し
  - `src/lcr/ui/ports.py` の `ContainerManagerPort` に private 由来メソッドが含まれている (`_check_version_compat`, `_apply_legacy_pins`)
- Required fix:
  - 公開ユースケース/公開メソッドへ再設計し、UIから private/内部詳細を呼ばないこと。

## 3. Final Judgment

- `pytest`: PASS
- standards compliance: FAIL (重大違反あり)

Conclusion: **REJECT**
