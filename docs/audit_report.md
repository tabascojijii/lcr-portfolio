# 監査報告書（Roadmap 監査）

## 判定
REJECT_TO_PM

## 総評
`docs/roadmap.md` は `docs/reference_standards.md` との整合性は高いが、絶対基準である `docs/plan.md` の必須拘束を一部未充足のため、現時点では承認不可。

## 指摘事項（重大度順）

1. **[Major] 完了条件の基準落ち（plan.md の完了定義未反映）**
- 違反箇所: `docs/roadmap.md` セクション「1. 目標と完了条件」
- 違反基準: `docs/plan.md` セクション「1. 目的と完了定義」
- 事実:
  - `plan.md` で必須の完了定義「AC-1〜AC-5 達成」「Docker再現性4要件の**静的検査・実行検証・証跡記録**すべてPass」「EMCS監査票に基づく**監査者差分0**」が、`roadmap.md` の完了条件に完全一致で固定されていない。
- 影響:
  - 完了判定が緩み、監査合格条件の解釈ぶれ（監査者間差分）を再発させる。
- 修正条件:
  - `roadmap.md` の完了条件に、`plan.md` の完了定義6項目を同等粒度で明記すること。
- 再検証手順:
  - 完了条件の各項目について `plan.md` との1対1対応表を提示し、欠落0件を確認する。

2. **[Major] UI禁止事項の拘束不足（運用境界の抜け）**
- 違反箇所: `docs/roadmap.md` セクション「Phase 4 REJECT条件」
- 違反基準: `docs/plan.md` セクション「3. RC-2 対応: UI/UseCase 境界不備」
- 事実:
  - `plan.md` のUI禁止事項は「JSON直接編集」「監査ログ直接書き込み」「Docker実行直接呼び出し」の3点。
  - `roadmap.md` では「JSON直接編集」「ガード無視実行経路」に留まり、後者2点（監査ログ直書き・Docker直接呼び出し）が明示拘束されていない。
- 影響:
  - UI層への責務逆流を防ぐ境界が不完全となり、構造劣化リスクが残存する。
- 修正条件:
  - Phase 4 のREJECT条件へ「UIから監査ログ直接書き込み」「UIからDocker実行直接呼び出し」を追加すること。
- 再検証手順:
  - UI禁止API一覧とREJECT条件の一致チェックを実施し、3/3項目一致を確認する。

3. **[Major] Docker再現性4要件の検証観点の固定不足**
- 違反箇所: `docs/roadmap.md` セクション「Phase 2: 再現性基盤実装（Gate B）」
- 違反基準: `docs/plan.md` セクション「4.1 Docker再現性4要件の固定（Critical対応）」
- 事実:
  - `plan.md` は Gate B に実装拘束だけでなく、検証拘束として「APTソース切替確認」「constraints適用ログ確認」を明示。
  - `roadmap.md` は成果物に「ビルド検証証跡」はあるが、検証観点（APT切替確認・constraintsログ確認）をREJECT条件または検証要件として明示固定していない。
- 影響:
  - 実装のみで合格と誤判定され、再現性要件が形式化されない可能性がある。
- 修正条件:
  - Phase 2 に検証要件を追加し、少なくとも「APT archive切替証跡」「constraints適用ログ」を必須化すること。
- 再検証手順:
  - Gate B チェックリストに検証2項目を追加し、証跡リンク付きでPass判定できることを確認する。

## 要確認（Open Question）
- `roadmap.md` は「`plan.md` と `reference_standards.md` を同等の絶対基準」と宣言しているため、上記欠落は意図的な簡略化か、記載漏れかをPMが明示すること。

## 結論
上記3件はいずれも絶対基準（特に `plan.md` の拘束）に対する不足であり、現版 `docs/roadmap.md` は **REJECT_TO_PM** と判定する。
