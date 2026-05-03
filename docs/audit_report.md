# Audit Report

## 1) pytest 実行結果

実行コマンド: `pytest tests/`

結果:
- `34 passed in 1.69s`
- Fail/ERROR はなし

## 2) 基準照合結果（docs/reference_standards.md vs src/, tests/）

判定: **REJECT（基準違反あり）**

### 指摘1: Data Integrity基準（3章）の未充足
- 違反基準:
  - 「すべての入出力データ、パラメータファイル、および実行ログ自体に暗号学的ハッシュを適用」
- 根拠:
  - `AuditMetadataService.collect` が出力しているハッシュは `script_sha256` のみで、入出力データ・パラメータファイル・実行ログ自体のハッシュ記録がない。
  - 参照: `src/lcr/core/audit/metadata_service.py`（`collect` の返却キー）
  - 参照: `src/lcr/ui/main_window.py:980`-`983`（ログ出力項目が image/git/path/script の4項目のみ）
- 影響:
  - ALCOA++想定の改ざん検知範囲が不足し、証跡の完全性が不足。
- 修正指示:
  - `collect` に以下を追加すること。
    1. 実行時パラメータ（例: 実行設定JSON）のSHA-256
    2. 主要入力データ群（少なくとも実行対象として参照したファイル群）のSHA-256
    3. 主要出力成果物（生成後）のSHA-256
    4. 実行ログファイル本体のSHA-256
  - 追加項目を履歴保存先にも構造化保存し、テストで検証すること。

### 指摘2: PyQt/PySide UIアーキテクチャ基準（4章）違反の疑い（Humble Object / 依存分離）
- 違反基準:
  - Viewはロジックを極小化し、複雑処理はPresenter/ViewModel/UseCaseへ委譲すること。
  - UI層は外側レイヤーとして、内側のユースケースを通じて操作すること。
- 根拠:
  - `MainWindow` が単一クラス内で分析実行、環境解決、定義生成、ビルド起動、履歴反映、監査追記などを広くオーケストレーションしており、責務が肥大化。
  - 参照: `src/lcr/ui/main_window.py:407`（`_run_analysis`）、`src/lcr/ui/main_window.py:604`（`_run_container`）、`src/lcr/ui/main_window.py:1086`（`_execute_save_and_build`）
  - さらにUI層が `generate_dockerfile`, `save_definition` を直接呼び出している。
  - 参照: `src/lcr/ui/main_window.py:27`, `src/lcr/ui/main_window.py:1121`, `src/lcr/ui/main_window.py:1091`
- 影響:
  - Viewのテスト容易性低下、変更影響範囲拡大、回帰リスク増加。
- 修正指示:
  - ビルド準備・定義保存・Dockerfile生成・実行前判定をUseCaseへ移管し、UIは入力収集と表示更新に限定すること。
  - `MainWindow` から直接 `generate_dockerfile/save_definition` を除去し、Port経由で呼ぶ構成に統一すること。
  - 上記分離を担保するユニットテスト（UIモック＋UseCase単体）を追加すること。

## 3) 総合判定

- pytest: Pass
- 規約準拠: **Fail（上記2件）**

最終判定: **REJECT_TO_IMPLEMENT**

## 4) Implementer向け実装アドバイス（再提出時チェックリスト）

### A. Data Integrity（3章）是正の実装方針
1. `AuditMetadataService.collect` の返却モデルを拡張し、最低でも以下を構造化して保持する。  
- `input_hashes`: 実行時に参照した主要入力ファイル群の SHA-256（`{relative_path: sha256}`）  
- `output_hashes`: 生成成果物の SHA-256（`{relative_path: sha256}`）  
- `param_hash`: 実行パラメータJSON（または同等の設定シリアライズ）の SHA-256  
- `log_hash`: 実行ログファイル本体の SHA-256  
2. すべてのパスキーはプロジェクト相対パスで保存する（絶対パス禁止）。
3. 履歴保存先（`history.json` など）へ上記項目を欠落なく永続化する。
4. `main_window.py` の監査表示項目を拡張し、`script_sha256` だけでなく `param/input/output/log` の各ハッシュを確認可能にする。

### B. UI責務分離（4章）是正の実装方針
1. `MainWindow` から以下の直接呼び出しを除去し、UseCase/Port経由へ統一する。  
- `generate_dockerfile`  
- `save_definition`
2. 「ビルド準備」「定義保存」「Dockerfile生成」「実行前判定」は Application/UseCase 層へ移管する。
3. `MainWindow` は入力収集・イベント接続・表示更新に限定し、業務判断（分岐/整合性判定）を持たないようにする。

### C. 再提出前の最小検証（必須）
1. `pytest tests/` が全件Pass。  
2. 新規テストを追加する。  
- ハッシュ網羅性テスト（`param/input/output/log` が全て保存される）  
- 相対パステスト（保存データに絶対パスが混入しない）  
- UI分離テスト（UIからUseCaseをモック経由で呼ぶ構成の担保）  
3. 監査証跡サンプルを1件作り、上記ハッシュ項目が実データで埋まっていることを確認する。
