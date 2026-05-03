# 監査報告書（Roadmap 検証）

## 判定
REJECT_TO_PM

## 監査対象
- `docs/roadmap.md`

## 絶対基準
- `docs/plan.md`
- `docs/reference_standards.md`

## 総評
`docs/roadmap.md` は `reference_standards` への整合性は高い一方で、`docs/plan.md` に明示された必須拘束（特に監査スキーマ固定要件と差し戻し経路要件）の記述が不足しており、絶対基準に対するトレーサビリティが未充足。

## 指摘事項（REJECT根拠）

### 1) plan の絶対基準性を弱める優先規則の記述
- 違反箇所:
  - `docs/roadmap.md` 0章
  - 「`docs/plan.md` は実行順序・実装粒度の参照とし、不一致時は `reference_standards` を優先」と定義
- 違反基準:
  - `docs/plan.md` は本監査依頼上「絶対基準」であり、参照扱いへの格下げは不可。
- 影響:
  - `plan` 側拘束（Gate、RC対応、必須項目）の一部を、解釈上スキップ可能にしてしまう。
- 修正条件:
  - 0章を修正し、`plan.md` と `reference_standards.md` を同等の絶対拘束として明記すること。
  - 不一致時の裁定ルールを追加する場合は「双方を満たす統合方針（不足があれば roadmap を拡張）」とし、片側優先で他方拘束を弱めないこと。
- 再検証手順:
  - 0章の文言修正後、各Phase/Gateに `plan` 要件が欠落なく反映されているかを再監査する。

### 2) 監査ログ最小スキーマ（plan RC-1）の必須キー固定が不十分
- 違反箇所:
  - `docs/roadmap.md` Phase 5（Gate G, H）
- 違反基準:
  - `docs/plan.md` 3章 RC-1で定義された監査ログ必須キーの固定要件。
  - 必須キー例: `required_imports`, `environment_capability`, `mismatch_result`, `guard_state`, `image_digest`, `git_commit_hash`, `input_sha256`, `output_sha256`, `parameter_sha256`, `log_sha256`, `relative_paths`。
- 影響:
  - 監査成立条件が曖昧になり、実装完了判定の客観性・再現性を損なう。
- 修正条件:
  - Phase 1（Gate A）またはPhase 5（Gate G）に、上記必須キーを明示列挙して固定すること。
  - 「キー欠落時は監査不成立（Fail）」を明記すること。
- 再検証手順:
  - `roadmap.md` 修正後、必須キーが網羅列挙されているかを機械的チェックで確認。

### 3) 差し戻し経路の分類要件（plan RC-3）が未反映
- 違反箇所:
  - `docs/roadmap.md` 全体（REJECT運用記述）
- 違反基準:
  - `docs/plan.md` RC-3で要求される判定系統分離:
    - `REJECT_TO_ARCHITECT`（境界/契約/スキーマ/標準違反）
    - `REJECT_TO_IMPLEMENT`（実装欠陥/テスト欠陥）
  - 監査票への「違反原因レイヤー（Requirement / Architecture / Implementation）」必須化。
- 影響:
  - 差し戻し先が曖昧となり、是正ループの効率と再現性が低下する。
- 修正条件:
  - ガバナンス運用ルールに、REJECT分類と違反原因レイヤー記録を追記すること。
  - 各PhaseのREJECT条件を上記分類にマッピングすること。
- 再検証手順:
  - REJECT例を2件（Architecture系/Implementation系）作成し、分類規則で一意に振り分け可能か確認。

## 良好点
- Docker再現性4要件（digest/APT archive/constraints/multi-stage）の明示は `reference_standards` と整合。
- UI境界（Humble Object、依存方向、Protocol/ABC、命名規約）は概ね整合。
- REJECT時の処方的記載要件（違反箇所/基準/修正条件/再検証手順）を運用ルールとして保持。

## 是正優先度
1. 0章の基準優先規則修正（最優先）
2. 監査ログ必須キーの明示固定
3. REJECT分類（TO_ARCHITECT/TO_IMPLEMENT）と原因レイヤー記録の追加

## 再監査受入条件
- 上記3点が `docs/roadmap.md` に反映済みであること。
- 反映後、`plan` と `reference_standards` の拘束に対し欠落項目0件であること。
