# Audit Report (2026-05-04)

## 1. Pytest Execution Result
- Command: `pytest tests/`
- Result: **PASS**
- Summary: `64 passed in 1.96s`
- Key log excerpt:
  - `collected 64 items`
  - `============================= 64 passed in 1.96s =============================`

## 2. Reference Standards Conformance Check (`docs/reference_standards.md`)

### 2.1 Scope Checked
- `src/`
- `tests/`
- `artifacts/`

### 2.2 Findings
- **Violation**: UI層の責務混在（Humble Object規約違反）
  - File: `src/lcr/ui/main_window.py`
  - Function: `MainWindow._run_container`
  - Evidence: `artifacts/architecture_decoupling_assessment.md` の Violations に「確認ダイアログ表示とJIT作成導線制御が同メソッドに集中」と記載。
- **Violation**: Port未経由の境界バイパス
  - File: `src/lcr/ui/main_window.py`
  - Function: `MainWindow._show_create_env_dialog`
  - Evidence: 同成果物に「EnvironmentCreationDialogへContainerManagerを直接受け渡し」と記載。

## 3. Required Artifacts Presence
- `artifacts/architecture_decoupling_assessment.md`: **Exists**
- `artifacts/refactoring_proposal.md`: **Exists**

## 4. Phase 6.1 Acceptance Criteria Check (`docs/requirements.md`)
- AC6.1-1: **Pass**（違反を `file/class(or function)/type/evidence` で列挙）
- AC6.1-2: **Pass**（改善方針とPort設計を提示）
- AC6.1-3: **Pass**（P0/P1/P2優先度あり）
- AC6.1-4: **Pass**（検証方法・テスト戦略あり）
- AC6.1-5: **Pass**（importグラフ種別と件数提示あり）
- AC6.1-6: **Pass**（変更影響テスト手順あり）
- AC6.1-7: **Fail**
  - Required fixed thresholds include:
    - 禁止依存0件
    - 循環依存0件
    - UI層業務ロジック0件
    - 境界違反テスト100% Pass
  - Actual (from `artifacts/architecture_decoupling_assessment.md` / `artifacts/refactoring_proposal.md`):
    - `UI->Domain直参照`: **2件**
    - `循環依存`: 0件
    - Remaining Deltaに未解消課題を明記
  - Therefore fixed numeric acceptance is not met.

## 5. Final Audit Decision
- Pytestは全件Passだが、`reference_standards` 違反（UI責務混在/Port未経由）および Phase 6.1 AC6.1-7 未達があるため、**REJECT**。
