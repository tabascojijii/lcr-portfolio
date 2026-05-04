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

## Import Graph Findings (2026-05-04, 再測定)

### UI->Domain直参照（一覧）

- 検出 0件

### 逆方向依存（一覧）

- `UseCase -> UI`: 検出 0件
- `Domain -> UI`: 検出 0件
- `Domain -> Infrastructure`: 検出 0件

### 循環依存（一覧）

- 循環依存サイクル: 検出 0件

## Violations (file path + class/function + violation type + evidence)

- 検出 0件

## Summary Counts

- `UI->Domain直参照`: 0件
- `逆方向依存 (UseCase->UI / Domain->UI / Domain->Infrastructure)`: 0件
- `循環依存`: 0件

## Assessment

依存方向の逆流・循環・境界越え直参照は検出されなかった。`MainWindow` は入力収集・表示更新・UseCase呼び出しに収束しており、実行判定/監査整形/結果整形はUseCase側で処理される。P3.1完了条件（`UI->Domain直参照 0件`、`UseCase -> Qt 0件`、`循環依存 0件`）を満たす。
