# Audit Report

## Verdict
- 判定: **REJECT**
- ルーティング先: `REJECT_TO_ARCHITECT`

## Findings (High Severity)
1. **PyQt/PySideのシグナル・スロット命名規則が計画に未定義**
- 失敗箇所: `docs/plan.md` 全体（該当規約の記載なし）
- 違反制約: `docs/reference_standards.md` セクション4「シグナル・スロットの命名規則」
  - シグナルは過去分詞形（例: `dataChanged`）
  - スロットは動作を示す動詞（例: `update_display`）
- 観測証拠:
  - `docs/plan.md` には依存方向、Humble Object、Port経由、Docker再現性、監査証跡等の規定はあるが、シグナル/スロット命名規則に関する明示要件・ゲート・検証項目が存在しない。
- 修正ヒント:
  - `docs/plan.md` の Hard Constraints または Structural Gate に、命名規約を必須制約として追加する。
  - CI/静的検査/レビュー観点として「シグナル=過去分詞、スロット=動詞」を検証項目化する。
  - テストまたはlintルールで規約逸脱をFailにする。
- 再検証条件:
  - 計画文書上で命名規約が明文化され、検証可能なゲート（CI・lint・レビュー基準）が追加されていること。
  - 追加後、`docs/reference_standards.md` セクション4との完全一致を再監査で確認できること。

## Compliance Notes
- 以下は準拠を確認:
  - Docker再現性4要件（digest固定、APT archive、constraints、multi-stage）
  - Data Integrity（hash4区分、相対パス、container digest、git hash）
  - 依存方向・Port経由・Humble Object
  - Builder/Validator分離、処方的REJECT要件
  - EMCS指標の明示

## Final Decision Basis
- `docs/reference_standards.md` は「絶対的技術基準」であり、1項目でも未充足なら許容不可。
- 上記欠落により、現行 `docs/plan.md` は **REJECT_TO_ARCHITECT** 相当。
