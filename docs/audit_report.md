# 監査報告書: docs/roadmap.md

## 判定
REJECT_TO_PM

## 総評
`docs/roadmap.md` は全体として `docs/reference_standards.md` と `docs/plan.md` に高い整合を示すが、`docs/plan.md` で「固定仕様/必須」とされる一部拘束条件が明示的に落ちている。差分は文書仕様レベルであり、設計再構築は不要。PMによるロードマップ修正で解消可能。

## 指摘事項（重要度順）

### 1. Port契約の必須一覧が未固定
- 失敗箇所: `docs/roadmap.md` セクション `2.3 UI/Architecture Discipline`
- 違反制約: `docs/plan.md` 3.2 では必須Port（`EnvironmentCapabilityPort`, `EnvironmentRepositoryPort`, `ContainerRuntimePort`, `AuditLogPort`, `ImageCleanupPort`, `KnowledgeMappingPort`, `PackageLookupPort`）を固定指定。
- 問題内容: ロードマップでは `abc.ABC` / `typing.Protocol` 利用のみ記載され、必須Portの網羅要件が欠落。
- 最小修正指示: `docs/roadmap.md` に「必須Port一覧（7種）を固定要件」として追記。
- 原因層: 設計文書化（PM）
- 差し戻し先: `REJECT_TO_PM`
- 再検証条件: 7 Port名が文書に明示され、欠落時はGate-S不合格と読める状態であること。

### 2. DTO境界規約の要件不足（Pydantic境界通過/旧dict吸収）
- 失敗箇所: `docs/roadmap.md` セクション `Phase E: 6.2-6.4 Contract Hardening`
- 違反制約: `docs/plan.md` 3.2 契約規約「境界DTOはPydanticモデルを通す（旧dict入力はアダプタで吸収）」。
- 問題内容: strict導入順は記載されているが、DTO境界通過と旧dict互換吸収の固定規約が未記載。
- 最小修正指示: Phase E完了条件に「境界DTOはPydantic通過」「旧dict入力はアダプタ層のみで吸収」を追加。
- 原因層: 設計文書化（PM）
- 差し戻し先: `REJECT_TO_PM`
- 再検証条件: DTO境界規約が完了条件に明示され、実装時の許容経路が一意になること。

### 3. Data Integrity必須フィールドの明示不足
- 失敗箇所: `docs/roadmap.md` セクション `2.2 Data Integrity`
- 違反制約: `docs/plan.md` 3.4 は必須記録項目として `path_mode` を含む固定フィールド群を要求。
- 問題内容: digest/hash系は記載済みだが、`path_mode`（相対パス強制結果）が明示されていない。
- 最小修正指示: Data Integrity項目に `path_mode` を追加し、相対パス強制の監査証跡項目として固定化。
- 原因層: 設計文書化（PM）
- 差し戻し先: `REJECT_TO_PM`
- 再検証条件: 必須フィールドが `docs/plan.md` 3.4 と同一集合で記載されること。

### 4. Gate-S自動REJECT条件（EMCS閾値超過時）の明記不足
- 失敗箇所: `docs/roadmap.md` セクション `4. 品質ゲート`
- 違反制約: `docs/plan.md` 5 Gate-S「EMCS閾値超過時点で自動 `REJECT_TO_ARCHITECT`」。
- 問題内容: ロードマップは「Gate-S fail 時点で REJECT_TO_ARCHITECT」は記載するが、EMCS閾値超過を明示トリガーとする記述が弱い。
- 最小修正指示: Gate-S節に「EMCS各メトリクスの閾値超過をGate-S failと同値扱いし、自動 `REJECT_TO_ARCHITECT`」を追記。
- 原因層: 設計文書化（PM）
- 差し戻し先: `REJECT_TO_PM`
- 再検証条件: EMCS閾値超過時の判定経路が明文化され、運用解釈余地がないこと。

## 監査結論
本件の不整合はすべてロードマップ記述の不足であり、要件・アーキテクチャそのものの再設計を要しない。したがって最終判定は `REJECT_TO_PM` とする。