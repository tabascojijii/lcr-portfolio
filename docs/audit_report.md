# 監査報告書（Auditor）

## 監査対象
- `docs/roadmap.md`

## 絶対基準
- `docs/plan.md`
- `docs/reference_standards.md`

## 判定
- **REJECT_TO_PM**

## 指摘事項

1. **監査入力識別子の定義が監査入力制約と不整合**
- 失敗箇所: `docs/roadmap.md` セクション「0. 位置づけ」
- 現状記述: 監査入力識別子として `docs/plan.md` と `docs/reference_standards.md` のハッシュを固定している。
- 違反制約:
  - `docs/plan.md` 5.1「Builder/Validator 分離の運用固定（監査入力制約）」
  - `docs/roadmap.md` 5章「監査ログ入力制約（許可入力は requirements + Diff のみ）」
- 問題内容:
  - 監査入力は「要件文書（`docs/requirements.md` と承認済み要件差分）+ 変更差分（Diff）」に限定されるべきところ、`plan` と `reference_standards` を監査入力識別子として固定しており、同一文書内の制約と矛盾している。
- 具体的修正指示（最小修正単位）:
  - セクション0の「監査入力識別子を固定する」から `docs/plan.md@...` と `docs/reference_standards.md@...` を削除し、`docs/requirements.md@<hash or revision>` と `Diff識別子（PR/commit range/patch hash）` を記載すること。
- 原因層判定: **設計ではなくPMドキュメント記述（運用定義）起因**
- 差し戻し先: **REJECT_TO_PM**
- 再検証条件:
  - 監査入力識別子が「requirements版識別子 + Diff識別子 + 判定時刻 + Validatorロール」に統一され、文書内矛盾が解消されていること。

## 総括
- アーキテクチャ方針・フェーズ構成・Gate-S/Gate-F・Docker/Data Integrity/Qt規約の主要要件は概ね整合している。
- ただし上記の監査入力定義の矛盾は監査運用の根幹に関わるため、是正完了まで受理不可。
