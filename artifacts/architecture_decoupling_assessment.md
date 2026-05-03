# Architecture Decoupling Assessment

基準: `docs/reference_standards.md` の依存方向と Humble Object 規約を評価基準とする。

## Violations

- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._run_container` + `UIがDocker実行フローを直接制御` + `UI層で `container_manager.prepare_run_config(...)` と `container_manager.get_docker_run_args(...)` を呼び出し、実行構成決定を保持している（UseCaseへ未移譲）。`
- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._run_container` + `UIが不足環境時の業務分岐を実装` + `画像未存在時の再ビルド判断・ダイアログ遷移・合成判断をUI内if分岐で実装している。`
- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._append_audit_metadata` + `UIが監査データ構築責務を保持` + `output_files収集、log_path判定、監査メタ出力整形をUIで実施している。`
- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._load_results` + `UIに業務フォーマット処理が混在` + `CSV先頭行解析・列展開・テーブル成形をUI層が直接処理している。`
- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._execute_save_and_build` + `UIが環境定義保存とビルド開始のアプリ制御を保持` + `EnvironmentBuildPreparationUseCase 呼び出し後の再読込/選択/ビルド起動制御がUIへ残存。`
- file path + class/function + violation type + evidence: `src/lcr/ui/main_window.py` + `MainWindow._to_project_relative_path` + `相対パス変換ルールがUIに分散` + `監査要件の相対パス規約実装がViewユーティリティとして配置されている。`

## Notes

- 依存方向違反（`UseCase -> Qt`、`Domain -> Infrastructure` 等）の明示的な逆流は、現状コードの範囲では主要箇所で未検出。
- 一方で、Humble Object違反（UIへの業務判断・フォーマット・実行オーケストレーション集約）は複数確認されるため、優先是正対象。
