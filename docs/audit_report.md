# 監査レポート（Auditor）

- 監査日: 2026-05-04
- 監査対象: `docs/plan.md`
- 絶対基準: `docs/reference_standards.md`
- 総合判定: **REJECT_TO_ARCHITECT**

## 指摘事項（重大度順）

### 1. 依存方向定義がクリーンアーキテクチャ標準に抵触（重大）
- 該当箇所: `docs/plan.md` セクション「3. ターゲットアーキテクチャ」
- 記載: 「依存方向は `UI -> UseCase -> Domain -> Infrastructure` に固定する。」
- 違反基準: `docs/reference_standards.md` 4章「クリーンアーキテクチャと依存の方向」
  - 内側ビジネスルール（Entities/Use Cases）がUI等の外側技術へ依存してはならない。
- 客観的根拠:
  - 上記記載は依存方向として `Domain -> Infrastructure` を明示しており、内側から外側への依存を許容する定義になっている。
  - これは依存逆転（Port/Adapter）前提の境界規律と整合しない。
- 影響:
  - Domain純粋性の毀損、テスト容易性低下、実装時の境界逸脱再発リスク増大。
- 修正指示（処方）:
  1. 依存方向定義を「**内側は外側に依存しない**」形に明文化する。
  2. 依存関係は少なくとも `UI -> Application/UseCase -> Domain` とし、InfrastructureはPort実装として外側に配置する旨へ修正する。
  3. `docs/plan.md` の3章と6章（構造ゲート）の記述を同一モデルで整合させ、`Domain -> Infrastructure` と読める表現を削除する。

## 適合確認（参考）
- 標準1章（監査ガバナンス）: Builder/Validator分離、処方的差し戻し、EMCS観点の記述は概ね適合。
- 標準2章（Docker再現性）: ダイジェスト固定・APTアーカイブ・constraints・マルチステージの4要件は計画上に明記。
- 標準3章（データ完全性）: `image_digest`/`git_commit` 記録、SHA-256、相対パス監査の記述あり。
- 標準4章（UI/Humble Object, 命名規約, IF規律）: 多くは適合だが、上記依存方向定義の矛盾により不合格。

## 最終判定
- 問題あり: **REJECT_TO_ARCHITECT**
