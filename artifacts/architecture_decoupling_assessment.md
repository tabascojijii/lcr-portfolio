# Architecture Decoupling Assessment

基準: `docs/reference_standards.md` の依存方向規約・Humble Object 規約に基づき、現行コードを評価した。

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