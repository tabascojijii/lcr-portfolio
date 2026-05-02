# 統合レポート（PM原因分析）

- 作成日: 2026-05-03
- 対象: `docs/roadmap.md`（M5: 最終統合監査）
- 参照: `docs/plan.md`, `docs/reference_standards.md`, 既存 `docs/audit_report.md`
- 総合判定: **REJECT（是正必須）**

## 1. 事象サマリ

既存監査指摘は1件（重大）であり、内容は「Validator入力制約の不一致」。
`docs/roadmap.md` 側で Validator 入力が `requirement + diff` と定義され、`docs/plan.md` の必須要件 `requirement + diff + test evidence` から逸脱している。

## 2. 原因分析

### 2.1 直接原因

- Roadmap更新時に、監査入力の最終定義を `docs/plan.md` ではなく `reference_standards` の要約解釈に寄せた。
- その結果、`test evidence` が欠落したまま M5 の「実施内容」と「完了条件」に二重転記された。

### 2.2 根本原因

- 要件文書間の優先順位（どの文書を最終正とするか）が運用として明文化されていない。
- マイルストーン記述に対する「整合性チェック項目（入力3点セットの有無）」がレビュー観点として固定化されていない。
- 監査設計で「証拠ベース判定（test evidence）」を必須制御点として扱う合意が、Roadmap反映プロセスに埋め込まれていない。

### 2.3 影響評価

- 合否判定の客観性が低下し、監査再現性が担保できない。
- 再検証時に判定根拠が不足し、手戻りコストが増大する。
- Builder/Validator分離運用の信頼性が毀損する。

## 3. 是正方針（必須）

1. `docs/roadmap.md` の M5 該当2箇所を、Validator入力が `requirement + diff + test evidence` のみに限定される記述へ修正する。  
2. M5 完了条件に「test evidence 不備時は自動的に未完了」と明記する。  
3. 文書更新時のレビュー項目として、以下の整合チェックを固定化する。  
`plan要件` と `roadmap記述` の入力制約一致、完了条件への同値反映、証拠欠落時の扱い定義。

## 4. 再発防止策

1. 文書優先順位ルールを定義する。  
優先順: `plan.md` > `roadmap.md` > 補助標準（reference）。
2. 「監査入力制約チェックリスト」をテンプレート化し、M5更新PRの必須添付にする。  
3. 監査観点の最小セットを固定する。  
`requirement`、`diff`、`test evidence` の3要素が1つでも欠けた場合は REJECT。

## 5. 最終結論

- 現状ステータス: `REJECT_TO_PM`
- 解除条件: 上記「是正方針（必須）」3点の反映完了と再監査通過。
