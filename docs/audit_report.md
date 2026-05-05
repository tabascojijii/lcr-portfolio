# 監査報告書（Auditor）

対象:
- 基準: `docs/reference_standards.md`
- 監査対象: `docs/plan.md`

判定:
- REJECT_TO_ARCHITECT

## 指摘事項（重大度順）

1. [重大] PyQt/PySide 命名規約の固定不足
- 失敗箇所: `docs/plan.md` 全体（シグナル/スロット命名規則の明文化なし）
- 違反規約: `docs/reference_standards.md` 4章「シグナルは過去分詞形、スロットは動詞」
- 根拠: 基準は「絶対的な技術基準」として命名規則の順守を要求。計画に検証項目・移行方針・DoD反映がないため、準拠を担保できない。
- 最小修正指示: Phase 6.2〜6.4 もしくは Gate-S に以下を追加すること。
  - 既存シグナル/スロット名の棚卸し
  - 命名規約違反をFailにする静的チェック（または監査チェックリスト）
  - DoDに「命名規約違反0件」を明記
- 原因層: 設計
- 差し戻し先: Architect

2. [重大] Builder/Validator分離の「差分限定レビュー」規定が未固定
- 失敗箇所: `docs/plan.md` 7章（役割分担）
- 違反規約: `docs/reference_standards.md` 1章「Builder/Validatorの分離（要件と生成差分のみでレビュー）」
- 根拠: 役割分担に「敵対的かつ厳格レビュー」はあるが、レビュー入力を「要件とDiffのみに限定」する運用制約が明示されていない。
- 最小修正指示: 監査プロセス定義へ以下を追加。
  - Auditor入力: 要件定義＋差分(Diff)＋テスト結果のみ
  - Implementer思考過程・補助メモの参照禁止
  - 違反時は監査無効として再監査
- 原因層: 設計
- 差し戻し先: Architect

3. [中] EMCSの客観メトリクス定義不足
- 失敗箇所: `docs/plan.md` 4章 Gate-S
- 違反規約: `docs/reference_standards.md` 1章「EMCSモデルに基づく客観的メトリクス評価」
- 根拠: Gate-Sは違反項目列挙があるが、EMCS観点での測定可能指標（例: 複雑度閾値、SRP逸脱判定基準、閾値超過時処理）が未定義。
- 最小修正指示: Gate-Sに定量メトリクスを追加。
  - 例: サイクロマティック複雑度上限、UI層メソッド行数上限、責務違反判定ルール
  - しきい値とFail条件を明記
- 原因層: 設計
- 差し戻し先: Architect

4. [中] 監査証跡のGitハッシュ取得方法が未規定
- 失敗箇所: `docs/plan.md` 5章
- 違反規約: `docs/reference_standards.md` 3章「git rev-parse HEAD を必ず記録」
- 根拠: `git_commit_hash` 項目はあるが、取得方法（`git rev-parse HEAD`）の明記がない。監査再現時に実装差異を招く。
- 最小修正指示: 必須実装として `git rev-parse HEAD` の取得・記録を明文化。
- 原因層: 設計
- 差し戻し先: Architect

## 総括
`docs/plan.md` は基準の主要方針（UI責務分離、Port化、Gate-S/Gate-F分離、Docker再現性、監査証跡項目）を広く包含している。一方で、絶対基準で要求される運用拘束と客観メトリクスの固定が不足しており、現状では基準完全準拠を証明できない。よって判定は `REJECT_TO_ARCHITECT` とする。