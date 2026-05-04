# Audit Report

## Verdict
- REJECT_TO_ARCHITECT

## Scope
- Baseline: `docs/reference_standards.md`（絶対基準）
- Target: `docs/plan.md`

## Findings (Objective, Prescriptive)

### 1. PyQt/PySide命名規約の計画欠落（シグナル・スロット）
- failure_location: `docs/plan.md`（全体。該当規約の実装方針・検証ゲートが未定義）
- violated_constraint: `docs/reference_standards.md` 第4章「PyQt / PySide モダンUIアーキテクチャ標準」内「シグナル・スロットの命名規則」
- evidence:
  - 基準では、シグナルは過去分詞形（例: `dataChanged`）、スロットは動詞（例: `update_display`）を要求。
  - `docs/plan.md` には当該命名規約の強制方針、検査方法、ゲート条件（違反0件等）が記載されていない。
- impact:
  - 基準4章の必須規約を満たす保証が計画上成立していないため、実装後の監査で一貫性不備が再発するリスクが高い。
- prescriptive_fix:
  1. `docs/plan.md` に「Signal/Slot Naming Gate」を追加する。
  2. ルールを明文化する（signal: past participle、slot: verb）。
  3. 静的検査または命名lint手順を定義し、CIに組み込む。
  4. Verification Gatesに「命名規約違反0件」を追加する。
  5. REJECT Templateの `violated_constraint` で第4章命名規約を参照可能にする。
- cause_layer: design
- reject_target: REJECT_TO_ARCHITECT
- done_condition:
  - `docs/plan.md` に命名規約の実装方針・検査方法・ゲート条件が追加され、客観的に違反0件を判定可能な状態であること。

## Pass/Fail Summary by Standard
- 第1章（監査/ガバナンス）: 概ね適合
- 第2章（Docker再現性）: 適合
- 第3章（データ完全性/監査証跡）: 適合
- 第4章（PyQt/PySide）: **不適合（命名規約統制の欠落）**

## Final Decision
- 単一でも絶対基準違反があるため、総合判定は **REJECT_TO_ARCHITECT**。
