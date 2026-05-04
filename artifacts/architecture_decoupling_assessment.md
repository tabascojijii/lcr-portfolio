# Architecture Decoupling Assessment

基準: `docs/reference_standards.md` の依存方向規約・Humble Object 規約に基づき、現行コードを評価した。

## Import Graph Extraction Procedure

- 目的: 依存方向違反、逆方向依存、循環依存を機械的に抽出する。
- 抽出手順（例）:
  1. `src/lcr` 配下の `.py` を対象に import 文を収集する。
  2. モジュールを `UI / UseCase / Domain / Infrastructure` に分類する。
  3. `A -> B` の依存エッジを生成し、禁止依存ルールに照合する。
  4. 深さ優先探索で循環依存を検出する。
- 監査に提出する最小証跡:
  - 依存エッジ一覧（違反/非違反）
  - 禁止依存ヒット一覧
  - 循環依存検出結果（サイクル一覧）

## Import Graph Findings (一覧)

### UI->Domain直参照（一覧）

- `src/lcr/ui/main_window.py` -> `container_manager.prepare_run_config(...)`
- `src/lcr/ui/main_window.py` -> `container_manager.get_docker_run_args(...)`
- `src/lcr/ui/main_window.py` -> `container_manager.reload_definitions(...)`
- `src/lcr/ui/main_window.py` -> 監査メタ構築ロジック（ファイル探索・整形）
- `src/lcr/ui/main_window.py` -> 結果CSVの解析/整形ロジック
- `src/lcr/ui/main_window.py` -> 相対パス正規化ロジック

### 逆方向依存（一覧）

- `UseCase -> UI`: 検出 0件
- `Domain -> UI`: 検出 0件
- `Domain -> Infrastructure`: 検出 0件

### 循環依存（一覧）

- 循環依存サイクル: 検出 0件

## Violations (file path + class/function + violation type + evidence)

- `src/lcr/ui/main_window.py` + `MainWindow._run_container` + `UI->Domain直参照` + `UIが `container_manager.prepare_run_config(...)` / `container_manager.get_docker_run_args(...)` を直接呼び、実行構成決定を担っている。`
- `src/lcr/ui/main_window.py` + `MainWindow._run_container` + `UI->Domain直参照` + `UIが image 未存在時の再ビルド分岐・作成導線遷移判断を保持している。`
- `src/lcr/ui/main_window.py` + `MainWindow._build_audit_metadata` + `UI->Domain直参照` + `監査対象ファイル収集と監査項目整形をUI層で実施している。`
- `src/lcr/ui/main_window.py` + `MainWindow._load_results` + `UI->Domain直参照` + `CSV先頭行解析・プレビュー整形など業務フォーマット処理をUI層で実施している。`
- `src/lcr/ui/main_window.py` + `MainWindow._execute_save_and_build` + `UI->Domain直参照` + `環境定義保存後の再読込・選択更新・ビルド起動制御をUIが保持している。`
- `src/lcr/ui/main_window.py` + `MainWindow._to_project_relative_path` + `UI->Domain直参照` + `監査要件の相対パス正規化規則がUIユーティリティとして配置されている。`

## Summary Counts

- `UI->Domain直参照`: 6件
- `逆方向依存 (UseCase->UI / Domain->UI / Domain->Infrastructure)`: 0件
- `循環依存`: 0件

## Assessment

依存方向の明示的逆流・循環は検出されなかった。一方でUI層に業務判断・監査整形・実行オーケストレーションが集中しており、Humble Object規約違反が継続している。
