# Implementation Plan (Architect)

## 0. Purpose
- 本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md`、`docs/post_mortem.md` を統合し、過去の監査ループ要因（RC-1〜RC-3）を構造的に除去するための実装計画である。
- 最優先は「機能追加」ではなく「境界強制・監査完全性・ゲート分離」である。
- `git commit` は本計画の実行範囲外（禁止）。

## 1. Post-Mortem起点の再発防止原則

### 1.1 RC-1（境界強制不足）への対策
- UI層は入力受理・表示更新・UseCase呼び出し以外を禁止する。
- `MainWindow._run_container` と `_show_create_env_dialog` を優先的に責務移管し、UIからDomain/Infra直接参照を不可にする。
- 境界越えはPort（`abc.ABC` / `typing.Protocol`）経由のみ許可する。

### 1.2 RC-2（差し戻し先誤り）への対策
- 差し戻し判定に「原因層」を必須化する。
- 設計原因は `REJECT_TO_ARCHITECT`、実装原因は `REJECT_TO_IMPLEMENT` に固定する。

### 1.3 RC-3（品質ゲート混線）への対策
- 機能ゲート（`pytest`）と構造ゲート（禁止依存・UI責務・Port統制）を独立運用する。
- どちらか未達なら次工程に進めない。

## 2. Hard Constraints（緩和禁止）

### 2.1 依存方向
- 許可: `UI -> UseCase -> Domain`。
- InfrastructureはPort実装側としてのみ接続する。
- 禁止:
  - `UI -> Domain` 直接依存
  - `UseCase -> Infrastructure` 具象依存
  - `UseCase -> Qt`
  - `Domain -> Qt`
  - `Domain -> Infrastructure`
  - 循環依存

### 2.2 Humble Object
- UIで禁止: 業務判断、永続化、Docker操作、外部I/O、複雑計算、業務意味を持つ整形。

### 2.3 監査不変条件
- すべて相対パス（絶対パス検出時はfail-fast）。
- ハッシュ対象必須:
  - 入力
  - 出力
  - パラメータ
  - 実行ログ本体
- 実行ログ必須:
  - `container_image_digest`
  - `git_commit_hash`

### 2.4 Docker再現性
- `FROM` はタグ禁止、SHA256ダイジェスト固定。
- EOLリポジトリはアーカイブへ切替。
- `constraints.txt` で依存探索を固定。
- ネイティブビルドはマルチステージ必須。

## 3. フェーズ別実行計画（順序固定）

### P0: Architecture Recovery Gate（実装前必須）
1. 境界仕様確定
- UI/UseCase/Domain/Infrastructureの責務表と依存表を更新。
- `MainWindow._run_container` / `_show_create_env_dialog` の移管先UseCase・Portを設計固定。
2. ゲート実装
- 禁止依存検査（`UI->Domain`、`UseCase->Qt`、逆依存、循環）をCI化。
- UI責務違反検査をCI化。
- 監査必須項目欠落検査をCI化。
3. 監査ルーティング標準化
- REJECTテンプレートに「原因層」「差し戻し先」「修正完了条件」を必須追加。
4. DoR更新
- 実装開始条件に「境界設計承認済み」「依存違反ゼロ化経路確定」を追加。

### P1: Phase 5（Validation Guardrails）
1. Capability Mapping UseCase（推定/実証の識別表示）。
2. Mismatch判定UseCase（不足1件以上でRun無効）。
3. 適合環境なし時の強制作成導線（不足import候補の初期投入）。
4. 作成後Dynamic Refresh（再起動不要）。
5. 監査記録（required imports / capability / mismatch / guard）。

### P2: Phase 6（Lifecycle Management）
1. Environment Manager専用UI（既存画面への責務混在禁止）。
2. 一括削除2段階確認（件数・対象・推定解放容量）。
3. 部分失敗継続（成功/失敗分離表示）。
4. 未使用判定（最終利用日時+利用回数+保護フラグ）。
5. cleanup対象限定（dangling/unused imageのみ）。
6. メタ編集（表示名/説明/タグ/分類/保護フラグ、内部ID不変）。
7. 監査ログ（操作種別/時刻/対象/成否/解放容量/理由）。

### P3: Phase 6.1（Decoupling成果物）
1. `artifacts/architecture_decoupling_assessment.md`
- 違反を `file path + class/function + violation type + evidence` で列挙。
- `UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数を実測記録。
2. `artifacts/refactoring_proposal.md`
- P0/P1/P2順の段階移行計画。
- Port設計、移管先、後方互換、テスト戦略、リスク対策。
3. 収束条件
- 禁止依存0件、循環依存0件、UI層業務ロジック0件。

### P4: Phase 6.2（Pydantic段階導入）
1. A: 監査メタデータDTO。
2. B: Runtime判定DTO。
3. C: 環境作成/更新DTO。
4. strict検証 + fail-fast + 互換アダプタ（dict経路）。

## 4. Requirements Traceability
- R5-1/R5-2/R5-3: P1で充足。
- R6-1〜R6-6: P2で充足。
- Phase 6.1 AC: P3成果物と依存実測で充足。
- Phase 6.2 AC: P4で充足。

## 5. Verification Gates（独立運用）

### 5.1 Functional Gate
- `pytest tests/` 全件Pass。
- 必須テスト: T5-1〜T5-4, T6-1〜T6-6, T6.2-1〜T6.2-5。

### 5.2 Structural Gate
- `UI->Domain` 直接依存0。
- `UseCase->Qt` 0。
- Port未経由境界越え0。
- 循環依存0。
- UI責務違反0。

### 5.3 Audit Gate
- 相対パス違反0。
- ハッシュ4区分欠落0。
- `container_image_digest` 欠落0。
- `git_commit_hash` 欠落0。

### 5.4 Governance Gate
- REJECTテンプレート必須項目欠落0。
- 差し戻し先誤判定0（設計原因を実装へ返さない）。

## 6. Loop Blocking Protocol
- 構造違反が1件でもあれば機能合格でも進行停止。
- 同一違反が2回連続した場合、実装修正を停止し設計レビューへ強制遷移。
- 監査結果に関わらず、post mortem由来制約（RC-1〜RC-3）の非回帰確認を毎回実施。

## 7. Definition of Done
- Phase 5 / 6 / 6.1 / 6.2 の受け入れ基準を満たす。
- Functional / Structural / Audit / Governance の4ゲート全通過。
- 実測値として「禁止依存0・循環依存0・UI責務違反0・監査欠落0」を提示できる。
- 成果物（assessment/proposal）に証拠付きで追跡可能。

## 8. Explicit Prohibition
- 本タスクでは `git commit` を実行しない。
