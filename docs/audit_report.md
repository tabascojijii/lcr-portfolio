# Audit Report

## 判定
- REJECT (`REJECT_TO_ARCHITECT`)

## 指摘事項（重大度順）

1. **Critical: 依存方向制約が内部矛盾しており、設計規約を機械的に検証不能**
- 対象: `docs/plan.md` 1.1 Dependency Direction (Hard Constraint)
- 観測事実:
  - 許可依存として `UI -> UseCase -> Domain -> Infrastructure` を定義。
  - 同セクションで禁止依存として `Domain -> Infrastructure` を定義。
- 違反制約:
  - `docs/reference_standards.md` 4章「クリーンアーキテクチャと依存の方向」
  - 監査可能性要件（1章 客観的評価）に対し、ルール自己矛盾により判定基準が不定になる。
- 影響:
  - 実装者・検証者で解釈が分岐し、同一差分に対してPass/Failが揺れる。
  - CI静的検査ルールを一意に定義できず、ガバナンス破綻リスクが高い。
- 修正指示（処方）:
  - 1.1 の依存方向を **単一の整合した表現** に修正すること。
  - 推奨修正案:
    - 許可依存を `UI -> UseCase -> Domain` とし、`Infrastructure` は `UseCase/Domain` が定義する Port を実装する外側層として扱う（内側は外側へ依存しない）。
    - もしくは依存矢印の意味を「実行時呼び出し」か「静的import依存」か明示し、禁止規則と衝突しないよう再定義する。
  - 併せて 4.2 Architecture Gate の検査式（何を0件判定するか）を修正版に同期すること。
- 再検証条件:
  - `docs/plan.md` 内で依存方向規則に論理矛盾がないこと。
  - 依存違反のFail条件が単一解釈で実装可能であること。

## 総括
- `docs/reference_standards.md` への準拠意図は全体として高いが、上記Criticalにより現行計画は監査基準上「問題あり」。
- 本件は実装着手前にArchitect差し戻しが必要。
