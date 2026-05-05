# 監査レポート（Auditor）

## 総合判定
REJECT_TO_ARCHITECT

## 監査対象
- 基準: `docs/reference_standards.md`（絶対基準）
- 計画: `docs/plan.md`

## 指摘事項（重大度順）

### 1) Clean Architecture の依存方向に関する重大違反
- 失敗箇所: `docs/plan.md` セクション「1. 失敗分析起点の設計制約」
  - 記載: `UI -> UseCase -> Domain -> Infrastructure` のみ許可
- 違反した制約:
  - `docs/reference_standards.md` 4章「クリーンアーキテクチャと依存の方向」
  - 内側のビジネスルール（Entities, Use Cases）がUIフレームワーク等の外側要素へ依存してはならない。
- 客観根拠:
  - `Domain -> Infrastructure` を許可すると、内側レイヤー（Domain）が外側レイヤー（Infrastructure）へ依存する構図になり、依存方向が逆転する。
  - これは「内側は外側に依存しない」という基準に反する。
- 原因層: 設計
- 差し戻し先: Architect
- 最小修正指示（処方）:
  1. 依存許可方向を `UI -> UseCase -> Domain` とし、Infrastructure は「内側インターフェース実装として外側から内側へ依存」に修正すること。
  2. 文書上で「Domain は Infrastructure を import しない」ことを明記すること。
  3. Port/Repository の定義主体を内側（UseCase/Domain）に固定し、実装主体を Infrastructure に固定すること。

## 適合確認（主要項目）
- EMCS による客観評価、REJECT時の処方的記載要求: 計画内に反映あり。
- Builder/Validator 分離（差分限定レビュー）: 計画内に反映あり。
- Docker再現性要件（digest固定、EOL archive、constraints、マルチステージ）: 計画内に反映あり。
- 監査証跡（`git rev-parse HEAD`、相対パス、各種ハッシュ）: 計画内に反映あり。
- PyQt/PySide 命名規約（Signal過去分詞、Slot動詞）: 計画内に反映あり。

## 結論
上記の依存方向違反はアーキテクチャ根幹に関わるため、現行 `docs/plan.md` は基準適合と認められない。`REJECT_TO_ARCHITECT` とする。
