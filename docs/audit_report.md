# Audit Report (2026-05-04)

## 1) Pytest Result
- Command: `pytest tests/`
- Result: **PASS**
- Evidence: `64 passed in 1.71s`

## 2) Reference Standards Compliance Check (`docs/reference_standards.md`)

### Scope: `src/`, `tests/`, `artifacts/`

#### 2.1 `tests/`
- `pytest tests/` 全件Passのため、テストゲート自体は適合。

#### 2.2 `artifacts/` 必須成果物存在確認
- `artifacts/architecture_decoupling_assessment.md`: 存在を確認。
- `artifacts/refactoring_proposal.md`: 存在を確認。

#### 2.3 `Phase 6.1` 受け入れ基準適合性
- 判定対象: `docs/requirements.md` の `Phase 6.1` AC6.1-1〜AC6.1-7。

**適合**
- AC6.1-1: 違反一覧が `file path + 関数/クラス + 違反種別 + 根拠` 形式で記載あり。
- AC6.1-2: 各違反への改善方針（移管先・Port方針）が記載あり。
- AC6.1-3: P0/P1/P2 の優先度・実施順序が記載あり。
- AC6.1-4: テスト戦略・検証方法の記載あり。
- AC6.1-5: importグラフ結果として一覧と件数が提示あり。
- AC6.1-6: 変更影響テスト手順（シナリオ/期待範囲/合否条件）記載あり。
- AC6.1-7: 数値指標の閾値定義（0件/100%）が記載あり。

**不適合（重大）**
- `artifacts/architecture_decoupling_assessment.md` の実測値にて以下を確認:
  - `UI->Domain直参照`: **2件**
  - `循環依存`: 0件
  - `逆方向依存`: 0件
- `artifacts/refactoring_proposal.md` の固定閾値:
  - 禁止依存件数: **0件**
  - UI層業務ロジック件数: **0件**
- よって、実測値が閾値を満たさず `Phase 6.1` は未達。

## 3) 指摘事項（REJECT根拠）

1. `Phase 6.1` 数値合否指標違反
- 違反基準: AC6.1-7（禁止依存0件、UI層業務ロジック0件）
- 根拠: `architecture_decoupling_assessment.md` に `UI->Domain直参照 2件` が明記。
- 影響: 依存方向規律が完全達成されておらず、Humble Object/境界分離の完了条件を満たさない。

2. 依存方向違反の残存（成果物自己申告ベース）
- 対象: `src/lcr/ui/main_window.py` (`MainWindow._run_container`, `MainWindow._show_create_env_dialog`)
- 根拠: `architecture_decoupling_assessment.md` の Violations セクション。
- 影響: UI層責務過多・Port未経由が残存し、保守性/テスト容易性の劣化要因。

## 4) 最終判定
- **REJECT_TO_IMPLEMENT**
- 理由: テストはPassだが、`Phase 6.1` 受け入れ基準（特にAC6.1-7）に対して実測値が未達。
