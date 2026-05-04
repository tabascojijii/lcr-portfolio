# Audit Report (Roadmap Verification)

## 監査対象
- 被監査: `docs/roadmap.md`
- 絶対基準: `docs/plan.md`, `docs/reference_standards.md`

## 判定
- 総合判定: **REJECT_TO_PM**

## 指摘事項

### 1. P0 Signal/Slot命名検査の成果物要件が未記載
- failure_location: `docs/roadmap.md` Phase P0
- violated_constraint: `docs/plan.md` 3章 P0「検査結果を artifacts/signal_slot_naming_report.md に出力し、CIで保存」
- 内容:
  - `docs/plan.md` では、Signal/Slot命名検査について「最低実装」「判定規則」「レポート出力先（`artifacts/signal_slot_naming_report.md`）」まで必須化されている。
  - `docs/roadmap.md` では命名違反検査の実施は記載されているが、上記の成果物出力要件が欠落している。
- prescriptive_fix:
  - Phase P0に以下を明示追記すること。
    - `artifacts/signal_slot_naming_report.md` の生成・CI保存を完了条件に含める。
    - 少なくとも `src/lcr/ui/**/*.py` を対象とした静的走査であることを記載する。
- cause_layer: design
- reject_target: REJECT_TO_PM
- done_condition:
  - `docs/roadmap.md` に当該成果物要件と対象範囲が明記され、P0完了条件として検証可能になっていること。
- input_boundary_check: pass

### 2. P3成果物の必須記載粒度が不足
- failure_location: `docs/roadmap.md` Phase P3
- violated_constraint: `docs/plan.md` 3章 P3
- 内容:
  - `docs/plan.md` は `artifacts/architecture_decoupling_assessment.md` に対し「file path + class/function + violation type + evidence」での列挙を要求している。
  - さらに `artifacts/refactoring_proposal.md` に対し「P0/P1/P2順の移行計画、Port設計、移管先、後方互換、テスト戦略、リスク対策」を必須としている。
  - `docs/roadmap.md` は成果物ファイル名の列挙に留まり、必須内容の粒度が欠落している。
- prescriptive_fix:
  - Phase P3に、各成果物の必須記載項目を `docs/plan.md` と同等粒度で追記すること。
- cause_layer: design
- reject_target: REJECT_TO_PM
- done_condition:
  - P3節に成果物ごとの必須記載項目が明文化され、監査時に内容充足を機械的に判定できること。
- input_boundary_check: pass

## 準拠している点（参考）
- `docs/reference_standards.md` 第1〜4章の主要要求（EMCS、Builder/Validator分離、Docker再現性、監査証跡、UI/依存規約）は概ね時系列に再編されている。
- 4ゲート（Functional/Structural/Audit/Governance）と停止条件、DoDの骨子は `docs/plan.md` と整合している。

## 結論
- `docs/roadmap.md` は骨格整合は良好だが、`docs/plan.md` で必須化された成果物要件の記述粒度が不足しているため、現時点では **REJECT_TO_PM** とする。
