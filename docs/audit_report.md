# Audit Report

## 1) pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **34 passed, 0 failed**
- 抜粋ログ:
  - `collected 34 items`
  - `============================= 34 passed in 1.43s ==============================`

## 2) reference_standards.md 照合結果（src/・tests/）

### 判定: **REJECT**（基準違反あり）

### 違反1: Humble Object違反（UIに業務ロジックが集中）
- 対象基準: `4. PyQt / PySide モダンUIアーキテクチャ標準` の `Humble Object パターンの適用`
- 根拠:
  - `src/lcr/ui/main_window.py:377` `_run_analysis` 内で、コード解析・SLOC算出・ランタイム解決まで実施
  - `src/lcr/ui/main_window.py:628` `_run_container` 内で、実行前判定・設定準備・実行制御まで実施
  - `src/lcr/ui/main_window.py:999` `_append_audit_metadata` で監査メタデータ収集をUIが直接実行
- 指摘:
  - View層が表示責務を超え、ユースケース実行・監査処理まで保持している。
- 処方的修正指示:
  - 解析・実行準備・監査情報収集をUseCase/Presenter層へ分離し、UIは入力受付と表示更新に限定すること。

### 違反2: クリーンアーキテクチャの依存方向違反（UIが具象実装に直接依存）
- 対象基準: `4. PyQt / PySide モダンUIアーキテクチャ標準` の `クリーンアーキテクチャと依存の方向` および `インターフェースによる規律`
- 根拠:
  - `src/lcr/ui/main_window.py:26` `CodeAnalyzer` 具象を直接import
  - `src/lcr/ui/main_window.py:27` `ContainerManager` 具象を直接import
  - `src/lcr/ui/main_window.py:30` `HistoryManager` 具象を直接import
  - `src/lcr/ui/main_window.py:53-57` UIクラス内部で具象を直接newして依存確定
- 指摘:
  - UIがProtocol境界を越えて内側実装に直結し、層分離と置換可能性が弱い。
- 処方的修正指示:
  - UI側で必要な操作を `typing.Protocol` / `abc.ABC` に集約し、具象インスタンス生成はComposition Rootへ移すこと。

### 違反3: 相対パス運用基準違反の可能性（絶対パスを保存し得る）
- 対象基準: `3. データ完全性と監査証跡` の `相対パスによるポータビリティ`
- 根拠:
  - `src/lcr/core/history/manager.py:150-157` `_to_relative` は project root 外パスで `path_str` をそのまま返却
- 指摘:
  - project root外入力時に絶対パスが履歴へ残り得るため、「すべて相対パス」の基準を満たさない。
- 処方的修正指示:
  - 保存前に必ず相対化できるルートへコピー/再配置するか、相対化不能時は保存拒否して明示エラーにすること。

## 3) 総合判定
- pytestは全件Pass。
- ただし `reference_standards.md` に対して上記のアーキテクチャ規約違反を確認。
- 最終判定: **REJECT_TO_IMPLEMENT**
