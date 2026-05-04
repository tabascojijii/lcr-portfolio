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
- Qt命名規約（reference standards 第4章）を強制する。
  - Signal: 過去分詞形（例: `dataChanged`, `executionFinished`）
  - Slot: 動詞開始のlower_snake_case（例: `update_display`, `refresh_capabilities`）
  - UIイベント接続時に、命名規約外のSignal/Slotは新規追加禁止。

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
- Signal/Slot命名検査をCI化（違反0件を必須）。
  - 最低実装: `src/lcr/ui/**/*.py` を対象に、`Signal(...)` 定義名と `@Slot` / 接続先メソッド名を静的走査。
  - 判定規則:
    - Signal名: lowerCamelCase かつ過去分詞終端（`...ed` / `...en` を基本ルールとし、例外語彙は許可リスト管理）
    - Slot名: lower_snake_case かつ動詞語彙で開始（例外は監査承認付きで許可）
  - 検査結果を `artifacts/signal_slot_naming_report.md` に出力し、CIで保存。
- 監査必須項目欠落検査をCI化。
3. 監査ルーティング標準化
- REJECTテンプレートに「失敗箇所」「違反制約」「具体修正指示」「原因層」「差し戻し先」「修正完了条件」を必須追加。
4. DoR更新
- 実装開始条件に「境界設計承認済み」「依存違反ゼロ化経路確定」を追加。

### P0.1: EMCS監査モデル固定（実装前必須）
1. EMCS評価表を監査仕様として固定
- 監査判定は以下メトリクスの合算ではなく、`critical項目の即時REJECT` + `総合しきい値` の二重判定で行う。

| metric_id | メトリクス名 | 測定方法 | 信頼性重み(R) | 影響度重み(I) | REJECT条件 |
|---|---|---|---:|---:|---|
| EMCS-01 | UI責務違反件数 | 静的解析 + レビュー証跡 | 3 | 3 | 1件以上で即REJECT |
| EMCS-02 | 禁止依存件数（UI->Domain, UseCase->Qt 等） | importグラフ検査 | 3 | 3 | 1件以上で即REJECT |
| EMCS-03 | 循環依存件数 | importグラフ検査 | 3 | 3 | 1件以上で即REJECT |
| EMCS-04 | Port未経由境界越え件数 | 静的解析 + 境界テスト | 3 | 2 | 1件以上で即REJECT |
| EMCS-05 | 監査証跡欠落件数（相対パス/ハッシュ4区分/digest/commit） | ログ検査テスト | 2 | 3 | 1件以上で即REJECT |
| EMCS-06 | 構造ゲート誤判定件数 | CIゲート監査 | 2 | 2 | 1件以上でREJECT |
- 補助指標として `EMCS_score = Σ(件数 × R × I)` を併記し、`EMCS_score > 0` は REJECT とする。
2. 判定再現性の担保
- 監査結果には `metric_id`・実測値・証拠パス・判定理由を必須記録し、監査者依存の自由記述判定を禁止する。

### P0.2: Builder/Validator分離プロトコル（実装前必須）
1. Auditor入力境界の固定
- Auditorが参照可能な入力は以下のみに限定する。
  - `docs/requirements.md`
  - `docs/reference_standards.md`
  - 変更Diff
  - テスト結果証跡
  - 監査証跡（ログ・メトリクス）
2. 参照禁止情報
- 実装者メモ、思考過程、口頭説明、チャット補足文脈を監査入力として使用してはならない。
3. 入力境界遵守チェック
- 監査記録テンプレートに `input_boundary_check: pass/fail` を必須項目として追加する。

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
- Signal命名規約違反0（過去分詞形）。
- Slot命名規約違反0（動詞開始）。

### 5.3 Audit Gate
- 相対パス違反0。
- ハッシュ4区分欠落0。
- `container_image_digest` 欠落0。
- `git_commit_hash` 欠落0。

### 5.4 Governance Gate
- REJECTテンプレート必須項目欠落0。
- 差し戻し先誤判定0（設計原因を実装へ返さない）。
- `input_boundary_check` fail 0（Builder/Validator分離違反なし）。

## 6. Loop Blocking Protocol
- 構造違反が1件でもあれば機能合格でも進行停止。
- 同一違反が2回連続した場合、実装修正を停止し設計レビューへ強制遷移。
- 監査結果に関わらず、post mortem由来制約（RC-1〜RC-3）の非回帰確認を毎回実施。

## 7. Definition of Done
- Phase 5 / 6 / 6.1 / 6.2 の受け入れ基準を満たす。
- Functional / Structural / Audit / Governance の4ゲート全通過。
- 実測値として「禁止依存0・循環依存0・UI責務違反0・監査欠落0」を提示できる。
- EMCS評価表に基づく全メトリクス 0件（`EMCS_score = 0`）を提示できる。
- 成果物（assessment/proposal）に証拠付きで追跡可能。

## 8. REJECT Template（必須）
- `failure_location`（file/class/function/line）
- `violated_constraint`（基準章・条項ID）
- 命名規約違反時は `docs/reference_standards.md` 第4章「シグナル・スロットの命名規則」を必ず参照する。
- `prescriptive_fix`（実施手順または最小修正案）
- `cause_layer`（design / implementation）
- `reject_target`（REJECT_TO_ARCHITECT / REJECT_TO_IMPLEMENT）
- `done_condition`（再監査でPASSとなる客観条件）
- `input_boundary_check`（pass/fail）

## 9. Explicit Prohibition
- 本タスクでは `git commit` を実行しない。
