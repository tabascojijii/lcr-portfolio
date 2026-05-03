# 監査報告書

## 判定
- 総合判定: **REJECT**
- ステータス: **REJECT_TO_ARCHITECT**

## 指摘事項（重大度順）

1. **[Major] PyQt/PySide シグナル・スロット命名規約の拘束が計画に未定義**  
   - 対象基準: `docs/reference_standards.md` セクション4「シグナル・スロットの命名規則」  
     - シグナルは過去分詞形（例: `dataChanged`）  
     - スロットは動作を示す動詞（例: `update_display`）
   - 事実: `docs/plan.md` では UI責務境界・Humble Object・Protocol/ABC は定義されているが、命名規約の実装拘束・検証項目（静的検査/レビュー基準/テスト）が明示されていない。
   - 影響: UI層での命名一貫性が崩れ、イベント契約の可読性・監査再現性が低下する。絶対基準の「違反時Fail」方針に照らし未充足。
   - 修正指示（処方）:
     - `docs/plan.md` に以下を明示追加すること。
       - 実装拘束: シグナル命名は過去分詞形、スロット命名は動詞開始。
       - 検証拘束: 命名規約違反を検知する静的検査またはレビュー・チェックリストを Gate とテスト計画に追加。
       - REJECT条件: 命名規約違反1件でもFail。

## 準拠確認（問題なし）
- Docker再現性4要件（digest固定 / archive apt / constraints / multistage）: 計画に明示あり。
- ALCOA++監査証跡（`image_digest`、`git_commit_hash`、各SHA-256、相対パス）: 計画に明示あり。
- EMCS客観メトリクスと閾値: 計画に明示あり。
- Builder/Validator分離および入力境界: 計画に明示あり。
- UI/UseCase/Domain/Infra の依存方向・Humble Object・Interface経由: 計画に明示あり。

## 最終結論
- `docs/plan.md` は主要論点の多くを満たすが、絶対基準である PyQt/PySide 命名規約の拘束と検証設計が欠落しているため、現時点では承認不可。
