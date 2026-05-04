# Roadmap (PM)

本ロードマップは `docs/reference_standards.md` を絶対基準として策定し、`docs/plan.md` の実行計画を基準準拠で時系列に再編したものである。基準違反は進行停止（REJECT）とする。

## 0. Roadmap原則

- 絶対基準: `docs/reference_standards.md`。
- 実行順序は「構造是正を先、機能追加を後」とし、監査可能性を常時維持する。
- 各フェーズ完了条件は Functional / Structural / Audit / Governance の4ゲート通過を前提とする。
- `docs/audit_report.md` がPASSであっても、未実装の構造統制は省略しない。

## 1. 基準トレーサビリティ（Reference Standards準拠マップ）

### 1.1 監査・ガバナンス標準（第1章）

- EMCSモデルを監査判定の唯一の客観基盤として固定。
- Builder/Validator分離を監査プロトコルに明文化。
- REJECTは処方的（失敗箇所、違反制約、修正指示、完了条件）を必須化。

### 1.2 Docker再現性標準（第2章）

- `FROM` ダイジェスト固定、EOLリポジトリのアーカイブ切替、`constraints.txt` 固定、マルチステージビルドを強制。

### 1.3 データ完全性・監査証跡（第3章）

- 相対パス強制。
- ハッシュ4区分（入力/出力/パラメータ/実行ログ）必須。
- 実行ログに `container_image_digest` と `git_commit_hash` を必須記録。

### 1.4 UIアーキテクチャ標準（第4章）

- Humble Object徹底（UIから業務判断・外部I/O・複雑計算を排除）。
- 依存方向を `UI -> UseCase -> Domain` に固定し、内側からQt非依存を保証。
- 境界越えは `abc.ABC` / `typing.Protocol` 経由のみ許可。
- Signal/Slot命名規約（Signal:過去分詞、Slot:動詞開始）をCIで検査。

## 2. フェーズ計画（順序固定）

### Phase P0: Architecture Recovery Gate（着手必須）

目的: RC-1〜RC-3を再発不能化する構造統制を先行実装する。

実施項目:
- 境界仕様確定（責務表・依存表更新、UI責務移管先UseCase/Port定義）。
- 構造ゲート実装（禁止依存、循環依存、UI責務違反、Signal/Slot命名違反）。
- 監査ルーティング標準化（原因層に応じた差し戻し先固定）。
- DoR更新（境界設計承認・ゼロ化経路確定を実装開始条件へ追加）。
- PASS維持チェックリスト化（基準章1〜4との整合を毎回確認）。

完了条件:
- 禁止依存0件、循環依存0件、UI責務違反0件、命名違反0件。

### Phase P0.1: EMCS監査モデル固定（実装前必須）

目的: 監査判定の再現性を保証する。

実施項目:
- EMCS-01〜06を監査仕様として固定。
- critical項目は1件で即REJECT。
- 監査記録へ `metric_id` / 実測値 / 証拠パス / 判定理由を必須化。

完了条件:
- `EMCS_score = 0`。
- 監査者自由記述依存の判定プロセスが排除されていること。

### Phase P0.2: Builder/Validator分離プロトコル（実装前必須）

目的: 監査入力境界を固定し、サイレント逸脱を防止する。

実施項目:
- Auditor入力を要件、基準、Diff、テスト証跡、監査証跡に限定。
- 実装者メモ・思考過程・チャット補足の参照を禁止。
- 監査記録へ `input_boundary_check` を必須追加。

完了条件:
- `input_boundary_check: pass` 以外はREJECT。

### Phase P1: Validation Guardrails（Phase 5実装）

目的: 実行前整合性の未充足を遮断する。

実施項目:
- Capability Mapping UseCase（推定/実証の識別表示）。
- Mismatch判定UseCase（不足1件以上でRun無効）。
- 非適合時の環境作成導線（不足import候補初期投入）。
- 作成後Dynamic Refresh（再起動不要）。
- 監査証跡の記録項目追加。

完了条件:
- R5-1/R5-2/R5-3 充足。

### Phase P2: Lifecycle Management（Phase 6実装）

目的: 環境ライフサイクル運用を安全・監査可能にする。

実施項目:
- Environment Manager専用UI。
- 一括削除2段階確認。
- 部分失敗継続処理。
- 未使用判定（最終利用日時+利用回数+保護フラグ）。
- cleanup対象限定（dangling/unused imageのみ）。
- メタ編集機能（内部ID不変）。
- 操作監査ログ拡張。

完了条件:
- R6-1〜R6-6 充足。

### Phase P3: Decoupling成果物（Phase 6.1）

目的: 構造是正の結果を証拠付きで可視化する。

成果物:
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`

完了条件:
- `UI->Domain` 直参照0、逆方向依存0、循環依存0を実測提示。

### Phase P4: Pydantic段階導入（Phase 6.2）

目的: 境界データの型安全とfail-fastを標準化する。

実施項目:
- 監査メタデータDTO。
- Runtime判定DTO。
- 環境作成/更新DTO。
- strict検証 + 互換アダプタ（dict経路）。

完了条件:
- Phase 6.2 AC 充足（T6.2-1〜T6.2-5 PASS）。

## 3. 横断ゲート（全フェーズ共通）

### 3.1 Functional Gate

- `pytest tests/` 全件PASS。
- 必須テスト: T5-1〜T5-4, T6-1〜T6-6, T6.2-1〜T6.2-5。

### 3.2 Structural Gate

- `UI->Domain` 直接依存0。
- `UseCase->Qt` 依存0。
- Port未経由境界越え0。
- 循環依存0。
- UI責務違反0。
- Signal/Slot命名違反0。

### 3.3 Audit Gate

- 相対パス違反0。
- ハッシュ4区分欠落0。
- `container_image_digest` 欠落0。
- `git_commit_hash` 欠落0。

### 3.4 Governance Gate

- REJECTテンプレート必須項目欠落0。
- 差し戻し先誤判定0。
- `input_boundary_check` fail 0。

## 4. マイルストーン

- M1: P0/P0.1/P0.2完了（構造・監査統制が実装前に有効化済み）。
- M2: P1完了（Validation Guardrails運用開始）。
- M3: P2完了（Lifecycle運用機能本番相当）。
- M4: P3完了（Decoupling証拠提出）。
- M5: P4完了（型安全統制の段階導入完了）。
- M6: 4ゲート全通過 + `EMCS_score = 0` を提示しDoD達成。

## 5. リスクと停止条件

- 構造違反1件でも進行停止（機能合格のみでは進めない）。
- 同一違反が2回連続で再発した場合、実装修正を停止し設計レビューへ強制遷移。
- 監査PASSでも、P0未完了・4ゲート未計測・証跡欠落のいずれかがあれば停止。

## 6. Definition of Done

- Phase 5 / 6 / 6.1 / 6.2 の受け入れ基準を満たす。
- Functional / Structural / Audit / Governance の4ゲートを全通過。
- 実測で以下を提示可能であること:
  - 禁止依存0
  - 循環依存0
  - UI責務違反0
  - 監査欠落0
  - `EMCS_score = 0`
- 成果物に証拠パスを付与し追跡可能であること。

## 7. 明示的禁止事項

- 本作業および関連実行で `git commit` を含むGit更新系コマンドを実行しない。