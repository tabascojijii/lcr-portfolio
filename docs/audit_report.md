# Audit Report

## 1) pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **34 passed, 0 failed**
- 抜粋ログ:
  - `collected 34 items`
  - `============================= 34 passed in 1.66s ==============================`

## 2) reference_standards.md 照合結果（src/・tests/）

### 判定: **REJECT**（基準違反あり）

### 違反1: UI層のHumble Object違反（UIに業務ロジック集中）
- 対象基準: `4. PyQt / PySide モダンUIアーキテクチャ標準`
  - `Humble Object パターンの適用`
- 根拠:
  - `src/lcr/ui/main_window.py:368` `_run_analysis` が解析実行、SLOC計算、ランタイム選択まで実施
  - `src/lcr/ui/main_window.py:726` `prepare_run_config` 呼び出しと実行前判定をUIクラス内で実施
  - `src/lcr/ui/main_window.py:741` `subprocess.run(["docker", "image", "inspect", ...])` をUIクラス内で直接実施
  - `src/lcr/ui/main_window.py:901` 履歴保存 `save_record` までUIクラス内で実施
- 指摘:
  - Viewが表示責務を超えて、解析・実行制御・永続化制御を保持している。
- 処方的修正指示:
  - 解析/実行オーケストレーションをUseCase/Presenterへ分離し、UIは入力受け取りと表示更新に限定すること。

### 違反2: 依存方向違反（Core層がQtに依存）
- 対象基準: `4. PyQt / PySide モダンUIアーキテクチャ標準`
  - `クリーンアーキテクチャと依存の方向`
- 根拠:
  - `src/lcr/core/container/worker.py:18` `from PySide6.QtCore import QThread, Signal`
  - `src/lcr/core/container/worker.py:21` `class ContainerWorker(QThread)`
- 指摘:
  - Core配下モジュールがUIフレームワーク(Qt)へ直接依存している。
- 処方的修正指示:
  - `core` からQt依存を除去し、実行処理は純粋Pythonサービスに分離すること。
  - Qtスレッド/シグナル連携は `ui` 層アダプタ（例: `ui/workers.py`）へ移譲すること。

### 違反3: インターフェース規律不足（具象依存）
- 対象基準: `4. PyQt / PySide モダンUIアーキテクチャ標準`
  - `インターフェースによる規律`
- 根拠:
  - `src/lcr/ui/main_window.py` で `ContainerManager`, `CodeAnalyzer`, `HistoryManager` 等の具象へ直接依存
  - `src/lcr/ui/create_env_dialog.py` で `ContainerManager` 具象型を直接受け取り
- 指摘:
  - `abc.ABC` / `typing.Protocol` ベースのポートを介した境界が不十分。
- 処方的修正指示:
  - UIが依存する操作を `Protocol` で定義し、具象実装はDIで注入すること。
  - テストではそのProtocolモックを使用してUI単体検証を可能にすること。

## 3) 総合判定
- pytestは全件Passだが、`reference_standards.md` のアーキテクチャ規約に対する重大違反を確認。
- 最終判定: **REJECT_TO_IMPLEMENT**
