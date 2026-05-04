# Audit Report (2026-05-04)

## 1. Pytest Execution Result
- Command: `pytest tests/`
- Result: **PASS**
- Summary: `64 passed in 1.70s`
- Key log excerpt:
  - `collected 64 items`
  - `============================= 64 passed in 1.70s =============================`

## 2. Reference Standards Conformance Check (`docs/reference_standards.md`)

### 2.1 Scope Checked
- `src/`
- `tests/`
- `artifacts/`

### 2.2 Findings (Violations)
- **Violation**: UI層の責務混在（Humble Object規約違反）
  - File: `src/lcr/ui/main_window.py`
  - Function: `MainWindow._run_container`
  - Evidence: `artifacts/architecture_decoupling_assessment.md` の Violations に「確認ダイアログ表示とJIT作成導線制御が同メソッドに集中」と明記。
- **Violation**: Port未経由の境界バイパス
  - File: `src/lcr/ui/main_window.py`
  - Function: `MainWindow._show_create_env_dialog`
  - Evidence: 同成果物の Violations に「EnvironmentCreationDialogへContainerManagerを直接受け渡し」と明記。

## 3. Required Artifacts Presence
- `artifacts/architecture_decoupling_assessment.md`: **Exists**
- `artifacts/refactoring_proposal.md`: **Exists**

## 4. Phase 6.1 Acceptance Criteria Check (`docs/requirements.md`)
- AC6.1-1: **Pass**（違反を `file path + 関数/クラス + 違反種別 + 根拠` で列挙）
- AC6.1-2: **Pass**（改善方針・インターフェース設計あり）
- AC6.1-3: **Pass**（P0/P1/P2の優先度と順序あり）
- AC6.1-4: **Pass**（検証方法・テスト戦略あり）
- AC6.1-5: **Pass**（`UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数あり）
- AC6.1-6: **Pass**（変更影響テストの手順・期待影響範囲・合否条件あり）
- AC6.1-7: **Fail**
  - Required fixed thresholds:
    - 禁止依存0件
    - 循環依存0件
    - UI層業務ロジック0件
    - 境界テスト100% Pass
  - Actual findings in artifacts:
    - `UI->Domain直参照`: **2件**
    - `循環依存`: 0件
    - `Remaining Delta` として未解消項目が明記されている

## 5. Prescriptive Remediation Hints
- `MainWindow._run_container` の遷移制御・実行前分岐をUseCase層へ完全移管し、UIは表示更新のみ担当に限定すること。
- `MainWindow._show_create_env_dialog` での `ContainerManager` 直渡しを廃止し、Port経由の境界I/Fへ置換すること。
- 上記修正後に importグラフ再計測を行い、`UI->Domain直参照` を **0件** にすること。

## 6. Final Audit Decision
- `pytest tests/` はPassだが、基準違反および Phase 6.1 AC6.1-7未達のため、**REJECT_TO_IMPLEMENT**。
