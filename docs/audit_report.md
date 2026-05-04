# 監査報告書（Roadmap Compliance Audit）

- 監査日: 2026-05-05
- 監査対象: `docs/roadmap.md`
- 絶対基準: `docs/plan.md`, `docs/reference_standards.md`
- 総合判定: **問題あり（REJECT_TO_PM）**

## 指摘事項

### 1) Builder/Validator 分離における監査入力条件の記載不足
- failure_location: `docs/roadmap.md` 「0. 運用原則（全フェーズ共通）」4
- violated_standard: `docs/plan.md` 8.1-2（監査入力は「要件文書・差分(Diff)・テスト結果・監査証跡」のみ）
- evidence: `roadmap` の記載は「差分・証跡・要件のみで監査する」であり、`テスト結果` が監査入力として明示されていない。
- required_fix: 当該項目を `要件文書・差分(Diff)・テスト結果・監査証跡のみ` に修正し、監査入力の欠落解釈余地をなくすこと。
- retest_condition: `docs/roadmap.md` を再読し、監査入力4要素（要件文書/差分/テスト結果/監査証跡）が明示されていることを確認する。

### 2) UI命名規約のCI検出要件が未固定
- failure_location: `docs/roadmap.md` 「2.4 PyQt/PySide アーキテクチャ標準」
- violated_standard: `docs/plan.md` 9-4（命名規約を lint または静的チェック対象に含め、CIで検出可能状態を維持）
- evidence: `roadmap` 2.4 は「命名規約準拠」「命名規約違反=0」のKPIはあるが、`lint/静的チェック` と `CI検出` の実装要件が明文化されていない。
- required_fix: 2.4 に「シグナル/スロット命名規約を lint もしくは静的チェックに組み込み、CIで自動検出する」を必須適用項目として追加すること。
- retest_condition: `docs/roadmap.md` 再監査時に、命名規約の自動検出手段（lint/静的チェック）とCI適用が明示されていることを確認する。

## 判定理由

`docs/roadmap.md` は全体として高い整合性を有するものの、`docs/plan.md` で必須化された運用要件の一部（監査入力の4要素明示、命名規約CI検出固定）が未記載である。絶対基準運用上、解釈余地を残すため現時点では合格不可。
