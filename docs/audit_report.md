# 監査レポート（Auditor）

## 判定
REJECT_TO_ARCHITECT

## 監査対象
- 基準: `docs/reference_standards.md`（絶対基準）
- 計画: `docs/plan.md`

## 主要指摘（重大度順）

### 1) Clean Architecture の依存方向に関する重大不整合（Critical）
- 該当箇所: `docs/plan.md` 1章「依存方向は UI -> UseCase -> Domain -> Infrastructure を厳守する。」
- 違反基準: `docs/reference_standards.md` 4章「UI層は最外層であり、内側のビジネスルール（Entities, Use Cases）がUIフレームワーク（Qt）に依存してはならない。」
- 監査根拠:
  - 計画文面の「依存方向」がそのまま依存関係の向きを示すなら、`Domain -> Infrastructure` となり、内側が外側へ依存する解釈となる。
  - これはクリーンアーキテクチャの依存規則（依存は外側から内側へ）と矛盾しうるため、監査上は不合格。
- 是正指示:
  - 依存規則を明示的に再定義すること（例: 「依存は外側→内側のみ。Domain/UseCase は Infrastructure/UI に依存しない」）。
  - 呼び出しフローとコンパイル時依存を文書上で分離して記述すること。

### 2) 監査ガバナンス要件（Builder/Validator分離）の明文化不足（Major）
- 該当箇所: `docs/plan.md` 全体
- 違反基準: `docs/reference_standards.md` 1章「Builder/Validatorの分離: 実装役と思考プロセスを共有せず、要件と差分のみから敵対的かつ厳格にレビュー」
- 監査根拠:
  - 計画内に「Builder/Validator 分離運用」の具体規則（入力物、禁止共有情報、レビュー観点固定）が定義されていない。
- 是正指示:
  - 監査プロセスとして、Validator(Auditor)の入力を「要件+差分+成果物」に限定する規約を追加。
  - 実装時の思考過程共有禁止、レビュー証跡のテンプレート化を追加。

### 3) 監査ガバナンス要件（EMCS等の客観メトリクス）の明文化不足（Major）
- 該当箇所: `docs/plan.md` 5章（テスト・監査ゲート）
- 違反基準: `docs/reference_standards.md` 1章「客観的アーキテクチャ評価 (EMCSモデル)」
- 監査根拠:
  - ゲートは列挙されているが、NG判定を下すための定量メトリクス（閾値、違反度、影響度）が未定義。
- 是正指示:
  - 少なくとも以下を定量化して閾値を記載: 依存違反件数、UI層ロジック混入件数、禁止API呼び出し件数、循環依存件数。
  - 各メトリクスに「Fail条件」「証拠取得方法」を明示すること。

### 4) REJECT時の処方的メッセージ要件の不足（Major）
- 該当箇所: `docs/plan.md` 2.3節（REJECTルーティング）
- 違反基準: `docs/reference_standards.md` 1章「処方的なエラーハンドリング（失敗箇所、違反制約、具体修正指示を含む）」
- 監査根拠:
  - ルーティング先は定義されているが、差し戻しメッセージの必須構成が仕様化されていない。
- 是正指示:
  - `REJECT` テンプレートを定義し、必須項目（失敗箇所/違反制約/修正ヒント/再検証条件）をCI出力要件に追加すること。

## 適合している点（参考）
- Docker再現性4要件（digest固定、EOLアーカイブ、constraints、マルチステージ）は計画に明記されている。
- 監査証跡として `git_commit_hash`・image digest・相対パス強制・SHA-256対象は概ね網羅されている。
- Humble Object、Port抽象（`abc.ABC`/`typing.Protocol`）、signal/slot命名規約は計画に反映されている。

## 結論
`docs/plan.md` は絶対基準に対して、依存規則の解釈不整合（Critical）および監査ガバナンス要件の明文化不足（Major）が残存しているため、現時点では承認不可。`REJECT_TO_ARCHITECT` と判定する。