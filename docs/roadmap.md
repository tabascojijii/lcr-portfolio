# LCR Roadmap (PM)

## 0. Purpose and Priority
- 本ロードマップは `docs/reference_standards.md` を絶対基準として、`docs/plan.md` の実装順序と検証条件を実行可能な計画へ落とし込む。
- 最優先は再発防止（RC-1〜RC-4）であり、機能追加はガバナンス固定後にのみ実施する。
- 本書の判定基準は「要件充足」ではなく「基準逸脱ゼロ」である。

## 1. Absolute Standards (Non-Negotiable)
以下は全フェーズで常時適用し、1件でも違反があれば即REJECTとする。

1. Data Integrity
- 実行ログに `container_image_digest` と `git_commit_hash` を必須記録。
- ハッシュ対象を `all_input_files` / `all_output_files` / `all_parameter_files` / `audit_log_record` の4区分で全件記録。
- パスは全てプロジェクトルート相対。絶対パスは fail-fast。

2. Dependency Boundary
- 許可依存方向は `UI -> UseCase -> Domain`。
- `Infrastructure` は Port 実装方向のみ許可。
- 禁止依存: `UseCase -> Qt` / `Domain -> Qt` / `Domain -> Infrastructure` / `UI -> Domain`（直参照）/ `UseCase -> Infrastructure`（具象依存）。
- 境界越え通信は `abc.ABC` または `typing.Protocol` 経由のみ許可。

3. Humble Object
- UIクラス（Window/Dialog/Widget）で業務判断、永続化、外部I/O、Docker操作、複雑計算、業務フォーマット処理を禁止。
- UIは入力受理、表示更新、UseCase呼び出しのみに限定。

4. Signal/Slot Naming
- Signal: 過去分詞形（例: `dataChanged`）。
- Slot: 動作動詞（例: `update_display`）。
- 命名規約はレビュー観点ではなくCI/Lintで機械検証。

5. Docker Reproducibility
- `FROM` は SHA256 digest 固定（タグ禁止）。
- EOL OS のAPTは archive リポジトリへリダイレクト。
- pip依存解決は `constraints.txt` 必須。
- ネイティブビルドはマルチステージ必須。

6. Auditor Governance
- Builder/Validator の入力境界を分離。
- Auditor 入力は要件とDiffのみ。
- REJECTには失敗箇所、違反制約、証拠、修正ヒント、再検証条件、ルーティング先（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）を必須記載。

## 2. Phase Roadmap (Order is Mandatory)

### Phase P0: Governance Baseline (Start Gate)
- 監査ログスキーマ固定（plan記載の必須フィールドを完全一致で実装）。
- 依存方向CIゲート追加（禁止依存を全検出）。
- UI責務CIゲート追加（Humble Object違反を全検出）。
- ハッシュ全件性CIゲート追加（4区分欠落/絶対パス違反をFail）。
- Docker再現性CIゲート追加（digest/archive/constraints/multi-stage）。
- Builder/Validator分離ゲート追加。
- REJECTテンプレート必須項目チェック追加。
- Signal/Slot命名CIゲート追加。
- Architect事前承認ゲート追加（RC-1〜RC-3と監査ルーティング分離の実装一致確認）。

Exit Criteria:
- P0各ゲートがCIで自動判定可能。
- 手動レビュー依存の必須判定が残っていない。

### Phase P1: Phase 5 Delivery
- Capability Mapping UseCase 実装（knowledge=推定、execution=実証）。
- Mismatch Guard UseCase 実装（差分1件以上で `Run` 無効）。
- Forced Creation Flow 実装（適合環境0件時の作成導線、候補自動投入、作成後即時反映）。
- 監査ログ連携（required imports/capability/mismatch/guard）。

Exit Criteria:
- R5-1〜R5-3を満たし、T5系テストが全Pass。

### Phase P2: Phase 6 Delivery
- Environment Manager専用UI実装。
- 2段階確認付き一括削除（部分失敗継続）実装。
- 未使用抽出ロジック実装（最終利用日時、利用回数、保護フラグ）。
- dangling/unused image限定クリーンアップ実装。
- メタデータ編集実装（内部ID不変）。
- 削除/編集/クリーンアップ監査ログ実装。

Exit Criteria:
- R6-1〜R6-6を満たし、T6系テストが全Pass。

### Phase P3: Phase 6.1 Artifacts
- `artifacts/architecture_decoupling_assessment.md` 作成。
- `artifacts/refactoring_proposal.md` 作成。
- 違反列挙は `file path + class/function + violation type + evidence` 形式で統一。
- `UI->Domain直参照` / `逆方向依存` / `循環依存` の件数と一覧を明示。
- 提案はP0/P1/P2優先でPort設計、移管先、後方互換、テスト戦略、リスク対策を明示。

Exit Criteria:
- 成果物が監査可能な形式で揃い、構造指標にトレーサブルである。

## 3. Verification Gates

### 3.1 Functional Gate
- `pytest tests/` 全件Pass。
- 必須追加テスト: T5-1〜T5-4, T6-1〜T6-6。

### 3.2 Structural Gate
- 禁止依存 0件。
- UI禁止行為 0件。
- Port未経由境界越え 0件。
- 循環依存 0件。
- Signal/Slot命名違反 0件。

### 3.3 Audit Gate
- ハッシュ4区分欠落 0件。
- 相対パス違反 0件。
- `container_image_digest` 欠落 0件。
- `git_commit_hash` 欠落 0件。
- REJECTテンプレート必須項目欠落 0件。

### 3.4 Objective Metrics (EMCS)
- M1: 依存方向違反件数 = 0
- M2: UI SRP違反件数 = 0
- M3: 複雑度超過（CC > 10）件数 = 0
- M4: 監査証跡欠落件数 = 0
- M5: Docker再現性違反件数 = 0
- M6: Signal/Slot命名規約違反件数 = 0

## 4. Loop Prevention and Routing
- 設計不備は常に `REJECT_TO_ARCHITECT` へ返却。
- 実装不備は常に `REJECT_TO_IMPLEMENT` へ返却。
- `docs/plan.md` と監査基準の差分が解消されるまで実装着手禁止。
- PASS時でもRC-1〜RC-3の非回帰確認を毎回実施し、未充足が1件でもあれば `REJECT_TO_ARCHITECT`。

## 5. Definition of Done
- Phase 5 / 6 / 6.1 の受け入れ基準を満たす。
- Hard Constraints 違反 0件。
- `pytest tests/` 全件Pass。
- EMCS（M1〜M6）全て閾値内。
- 監査証跡（hash4区分、digest、git hash、相対パス）完全充足。
- Builder/Validator分離の入力境界違反 0件。

## 6. Explicit Prohibition
- 本作業では `git commit` を実行しない。
