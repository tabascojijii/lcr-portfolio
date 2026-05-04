# 監査レポート (2026-05-04)

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **PASS**
- サマリ: `64 passed in 1.80s`
- 主要ログ:
  - `collected 64 items`
  - `============================= 64 passed in 1.80s =============================`

## 2. 基準照合 (docs/reference_standards.md)

### 2.1 src/・tests/・artifacts/ の確認
- `artifacts/architecture_decoupling_assessment.md` 存在: **OK**
- `artifacts/refactoring_proposal.md` 存在: **OK**
- `tests/` 自動テスト一式存在 + `pytest tests/` 全件Pass: **OK**

### 2.2 違反判定
以下は `docs/reference_standards.md` の「UIはロジックを持たない」「依存境界をPortで統制」に照らして未達:

1. `src/lcr/ui/main_window.py` / `MainWindow._run_container`
- 違反種別: UI責務過多
- 根拠: `artifacts/architecture_decoupling_assessment.md` にて「確認ダイアログ表示とJIT作成導線制御が同メソッドに集中」と明記。

2. `src/lcr/ui/main_window.py` / `MainWindow._show_create_env_dialog`
- 違反種別: 境界越えPort未経由
- 根拠: `artifacts/architecture_decoupling_assessment.md` にて「EnvironmentCreationDialogへContainerManagerを直接受け渡し」と明記。

## 3. requirements.md Phase 6.1 適合性確認

### 3.1 成果物必須要件
- AC6.1-1〜AC6.1-6 のための記載要素（違反一覧、改善方針、P0/P1/P2、検証方法、importグラフ一覧/件数、変更影響テスト手順）は文書上 **確認済み**。

### 3.2 受け入れ基準の未達
- AC6.1-7（数値合否指標の固定）で提示された閾値に対し、実測値が未達。
  - `artifacts/refactoring_proposal.md` の固定閾値:
    - 禁止依存件数: 0件
    - 循環依存件数: 0件
    - UI層業務ロジック件数: 0件
    - 境界違反テストpass率: 100%
  - `artifacts/architecture_decoupling_assessment.md` の実測:
    - UI->Domain直参照: 2件
- 判定: **Phase 6.1 は未達 (REJECT)**

## 4. 総合判定
- `pytest tests/` はPassだが、基準違反（UI責務混在/Port未経由）およびPhase 6.1 数値基準未達があるため、監査判定は **REJECT_TO_IMPLEMENT**。
