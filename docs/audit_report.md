# docs/roadmap.md 監査報告

## 監査基準
- 絶対基準1: `docs/plan.md`
- 絶対基準2: `docs/reference_standards.md`

## 総合判定
REJECT_TO_PM

## 指摘事項（重要度順）

1. **Builder/Validator分離の運用規則が一部欠落**
- 根拠（基準）: `docs/plan.md` 6.1節
  - 監査許容入力の明示（`requirements.md` / `reference_standards.md` / diff / テスト証跡）
  - 禁止入力の明示（思考過程メモ、主観補足、将来約束など）
  - 違反時の監査無効化と `artifacts/audit_reject_template.md` 記録義務
- 現状（roadmap）: `docs/roadmap.md` 1章・6章で分離原則は触れているが、**禁止入力の具体列挙**と**違反時の監査無効化規則**が未規定。
- 影響: 監査I/O境界違反の再発防止ルールが運用に落ちず、判定の再現性が低下する。
- 最小修正指示:
  - `docs/roadmap.md` に `plan.md` 6.1節相当の「許容入力」「禁止入力」「違反時無効化手順」を明文化すること。

2. **`audit_reject_template.md` の必須記載項目定義が欠落**
- 根拠（基準）: `docs/plan.md` 7節
  - `artifacts/audit_reject_template.md` 必須項目（失敗箇所、違反制約、最小修正単位、原因層、差し戻し先、再検証条件）
- 現状（roadmap）: `docs/roadmap.md` 5章で成果物ファイル名は列挙されるが、**テンプレートに必要な記載項目**が未固定。
- 影響: REJECT時の処方的品質（reference_standards 1章要求）にばらつきが出る。
- 最小修正指示:
  - `docs/roadmap.md` に `audit_reject_template.md` の必須項目を明記すること。

3. **`post_mortem_closure_checklist.md` の必須項目定義が欠落**
- 根拠（基準）: `docs/plan.md` 7節
  - RC-1〜RC-3閉塞証跡、Gate-S/Gate-F独立運用記録、差し戻し先判定ログを必須化
- 現状（roadmap）: 成果物名の列挙のみで、**チェックリストの必須中身**が未規定。
- 影響: RC閉塞の検証粒度が監査者依存になる。
- 最小修正指示:
  - `docs/roadmap.md` に `post_mortem_closure_checklist.md` の必須項目を明記すること。

## 準拠確認（問題なし）
- Docker Reproducibility 4要件（digest/EOL archive/constraints/multi-stage）の拘束は整合。
- Data Integrity（digest/hash/path_mode/相対パス）要求は整合。
- UI/依存方向/Port必須化/Signal-Slot命名規約は整合。
- Gate-S/Gate-F分離、EMCS閾値、Gate-S fail時の `REJECT_TO_ARCHITECT` は整合。
- フェーズ順序（A→H）および主要完了条件は概ね整合。

## 判定理由
- 不足はいずれも**ロードマップ記述の具体化不足**であり、設計原則そのものの破綻ではない。
- したがって差し戻し先は Architect ではなく PM と判断する。
