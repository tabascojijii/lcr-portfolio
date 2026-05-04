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

## Import Graph Findings (2026-05-04)

### UI->Domain直参照（一覧）

- `src/lcr/ui/main_window.py` -> 実行前後のUI制御とダイアログ遷移分岐（実行判定は `RuntimeExecutionPreparationUseCase.prepare_run_decision(...)` に移管済み）
- `src/lcr/ui/main_window.py` -> 環境作成ダイアログへの `ContainerManager` 受け渡し（Port化未完了）

### 逆方向依存（一覧）

- `UseCase -> UI`: 検出 0件
- `Domain -> UI`: 検出 0件
- `Domain -> Infrastructure`: 検出 0件

### 循環依存（一覧）

- 循環依存サイクル: 検出 0件

## Violations (file path + class/function + violation type + evidence)

- `src/lcr/ui/main_window.py` + `MainWindow._run_container` + `UI責務過多` + `実行可否判定はUseCase移管済みだが、確認ダイアログ表示とJIT作成導線制御が同メソッドに集中している。`
- `src/lcr/ui/main_window.py` + `MainWindow._show_create_env_dialog` + `境界越えPort未経由` + `EnvironmentCreationDialogへContainerManagerを直接受け渡している。`

## Summary Counts

- `UI->Domain直参照`: 2件
- `逆方向依存 (UseCase->UI / Domain->UI / Domain->Infrastructure)`: 0件
- `循環依存`: 0件

## Assessment

依存方向の明示的逆流・循環は検出されなかった。監査メタデータ整形・結果プレビュー整形・実行前判定はUseCaseへ移管済み。残課題はUIイベントハンドラに残る遷移制御と、環境作成ダイアログ境界のPort未経由部分である。
