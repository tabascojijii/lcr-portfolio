# Audit Report

## 1. pytest 実行結果

実行コマンド: `pytest tests/`

結果:
- `63 passed in 1.58s`
- 失敗テスト: 0件

## 2. 監査対象と基準

参照基準:
- `docs/reference_standards.md`
- `docs/requirements.md`（Phase 6.1 受け入れ基準）

検証対象:
- `src/`
- `tests/`
- `artifacts/`

## 3. 成果物存在確認（Phase 6.1 必須）

- `artifacts/architecture_decoupling_assessment.md`: 存在確認済み
- `artifacts/refactoring_proposal.md`: 存在確認済み

## 4. 基準適合性判定

### 4.1 reference_standards.md 観点

違反あり（UI責務混在 / Humble Object規約違反）:
- 根拠: `artifacts/architecture_decoupling_assessment.md` に `UI->Domain直参照 6件` と明記
- 例示箇所:
  - `src/lcr/ui/main_window.py` `MainWindow._run_container`
  - `src/lcr/ui/main_window.py` `MainWindow._build_audit_metadata`
  - `src/lcr/ui/main_window.py` `MainWindow._load_results`

判定:
- `docs/reference_standards.md` の「UI層は業務判断を持たない」「依存方向規律」観点で未達

### 4.2 requirements.md Phase 6.1 受け入れ基準観点

- AC6.1-1: 主要違反の列挙
  - 適合（file path + 関数/クラス + 違反種別 + 根拠が記載）
- AC6.1-2: 改善方針定義
  - 適合（移管先レイヤ/Port方針あり）
- AC6.1-3: P0/P1/P2優先度
  - 適合
- AC6.1-4: 検証方法定義
  - 適合
- AC6.1-5: importグラフ結果（一覧と件数）
  - 適合
- AC6.1-6: 変更影響テスト手順
  - 適合
- AC6.1-7: 数値合否指標の固定
  - 適合（閾値定義あり）

ただし、Phase 6.1 の実質達成判定としては未達:
- `artifacts/refactoring_proposal.md` の固定閾値:
  - 禁止依存件数 0件
  - UI層業務ロジック件数 0件
- `artifacts/architecture_decoupling_assessment.md` 実測:
  - UI->Domain直参照 6件

上記より、数値閾値を満たしておらず基準違反。

## 5. 総合判定

- pytest: Pass
- 基準適合: **Fail（基準違反あり）**
- 最終判定: **REJECT_TO_IMPLEMENT**
