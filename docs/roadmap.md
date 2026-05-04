# Roadmap (PM)

## 0. 目的と前提
- 本ロードマップは `docs/reference_standards.md` を絶対基準として策定する。
- `docs/plan.md` の実行順序と達成条件を維持しつつ、監査可能性・再現可能性・疎結合性を同時達成する。
- いかなる実装判断も、基準逸脱時は機能優先より是正を優先する。

## 1. 絶対遵守基準（reference_standards 固定）

### 1.1 ガバナンス / 監査
- 監査は EMCS による客観メトリクスで判定する。
- Builder/Validator を入力境界で分離し、要件と差分のみで審査する。
- REJECT は処方的に返す（失敗箇所、違反制約、証拠、修正ヒント、再検証条件、ルーティング先）。

### 1.2 Docker 再現性
- `FROM` は SHA256 ダイジェスト固定（タグ禁止）。
- EOL OS は APT をアーカイブリポジトリへリダイレクトする。
- pip 解決は `constraints.txt` で探索範囲を固定する。
- ネイティブビルドはマルチステージビルドを強制する。

### 1.3 Data Integrity
- 監査ログへ `container_image_digest` と `git_commit_hash` を必須記録する。
- パスはプロジェクトルート相対のみ許可し、絶対パスは Fail とする。
- `all_input_files` / `all_output_files` / `all_parameter_files` / `audit_log_record` を全件ハッシュ対象にする。

### 1.4 UI / 依存方向
- 依存方向は `UI -> UseCase -> Domain` のみ許可する。
- `UseCase -> Qt`、`Domain -> Qt`、`Domain -> Infrastructure`、`UI -> Domain` 直参照、`UseCase -> Infrastructure` 具象依存を禁止する。
- 境界越えは `abc.ABC` / `typing.Protocol` の Port 経由のみ許可する。
- Humble Object を徹底し、UI の業務判断・I/O・複雑計算・業務フォーマット処理を禁止する。
- Signal/Slot 命名規約（Signal=過去分詞、Slot=動詞）を機械検証する。

## 2. 実行ロードマップ（順序固定）

### Phase P0: Governance Baseline（着手ゲート）
1. 監査ログスキーマを固定する。
2. 依存方向 CI ゲートを導入する（`UseCase -> Qt` 含む禁止依存）。
3. UI 責務 CI ゲートを導入する（業務判断/I-O/複雑計算/業務フォーマット禁止）。
4. ハッシュ全件性 CI ゲートを導入する（4区分欠落・絶対パス違反を Fail）。
5. Docker 再現性 CI ゲートを導入する（digest/APT archive/constraints/multi-stage）。
6. Builder/Validator の入力境界ゲートを導入する。
7. REJECT テンプレート必須項目チェックを導入する。
8. Signal/Slot 命名 CI ゲートを導入する。
9. 実装開始前の Architect 承認を必須化する。

### Phase P1: Phase 5 実装
1. Capability Mapping UseCase を実装する（knowledge=推定、execution=実証）。
2. Mismatch Guard UseCase を実装する（差分1件以上で `Run` 無効）。
3. Forced Creation Flow を実装する（適合0件時の作成導線と即時反映）。
4. required imports/capability/mismatch/guard を監査ログへ連携する。

### Phase P2: Phase 6 実装
1. Environment Manager 専用 UI を実装する。
2. 2段階確認付き一括削除を実装する（部分失敗継続）。
3. 未使用抽出ロジックを実装する（最終利用日時+利用回数+保護フラグ）。
4. dangling/unused image 限定のクリーンアップを実装する。
5. メタデータ編集を実装する（内部ID不変）。
6. 削除/編集/クリーンアップの監査ログを実装する。

### Phase P3: Phase 6.1 成果物
1. `artifacts/architecture_decoupling_assessment.md` を作成・更新する。
2. `artifacts/refactoring_proposal.md` を作成する。
3. 依存違反、直参照、循環依存を件数付きで証跡化する。

### Phase P3.1: REJECT 収束（UI->Domain 0件化）
1. **アセスメント再測定を先行実施**し、`artifacts/architecture_decoupling_assessment.md` を実コード現状へ同期する。  
   - `_show_create_env_dialog` / `_open_environment_creation_dialog` の Port 経由実装を再確認し、誤検知を除去する。
2. **固定対象を明示**し、以下を UI 内業務責務の移管対象として固定する。  
   - `MainWindow._run_container`
   - `MainWindow._build_audit_metadata`
   - `MainWindow._load_results`
   - `MainWindow._execute_save_and_build`
   - `MainWindow._to_project_relative_path`
3. **Step A（優先）**: `_run_container` 系の残留業務判断を `RunExecutionOrchestrationUseCase` へ移管する。  
   - 特に `_handle_missing_runtime_image` の不足時分岐・遷移判定を UseCase 側へ移す。
   - `PathPolicyPort` を導入し、相対パス正規化（`_to_project_relative_path` 相当）を UI 外へ移管する。
4. **Step B**: `_build_audit_metadata` の監査整形責務を `BuildAuditRecordUseCase` へ完全移管する。
5. **Step B**: `_load_results` のCSV解析/整形責務を `ResultPreviewUseCase` へ完全移管する。
6. **Step C**: `_execute_save_and_build` の業務制御を `EnvironmentLifecycleUseCase` へ移管する。
7. UI を「入力収集・表示更新・UseCase 呼び出し」のみへ収束させる。

完了条件（P3.1専用）:
- `UI->Domain直参照` 件数 = 0
- `UseCase -> Qt` 件数 = 0
- `循環依存` 件数 = 0
- `pytest tests/` 全件Pass
- `artifacts/architecture_decoupling_assessment.md` を更新し、実測0件を証跡化
- `artifacts/refactoring_proposal.md` の固定閾値（禁止依存0、循環依存0、UI業務ロジック0、境界テスト100%Pass）を追加条件として実測で充足

## 3. 検証ゲート

### 3.1 Functional Gate
- `pytest tests/` 全件 Pass。
- T5-1〜T5-4、T6-1〜T6-6 の受け入れテストを全件 Pass。

### 3.2 Structural Gate
- 禁止依存 0件（`UseCase -> Qt` 含む）。
- UI 禁止行為 0件。
- Port 未経由境界越え 0件。
- 循環依存 0件。
- Signal/Slot 命名違反 0件。

### 3.3 Audit Gate
- ハッシュ4区分欠落 0件。
- 相対パス違反 0件。
- `container_image_digest` 欠落 0件。
- `git_commit_hash` 欠落 0件。
- REJECT テンプレート必須項目欠落 0件。

### 3.4 EMCS Objective Metrics
- M1: 依存方向違反件数 = 0
- M2: UI SRP 違反件数 = 0
- M3: 複雑度超過（CC > 10）件数 = 0
- M4: 監査証跡欠落件数 = 0
- M5: Docker再現性違反件数 = 0
- M6: Signal/Slot命名規約違反件数 = 0

## 4. ループ防止プロトコル
- 設計不備は `REJECT_TO_ARCHITECT` に固定する。
- 実装不備は `REJECT_TO_IMPLEMENT` に固定する。
- `docs/plan.md` と監査基準に差分が残る限り実装着手を禁止する。
- PASS 判定時でも RC-1〜RC-3 の非回帰確認を毎回実施する。
- 非回帰未充足が1件でもあれば総合判定に関係なく `REJECT_TO_ARCHITECT` とする。

## 5. 完了条件（Definition of Done）
- Phase 5 / Phase 6 / Phase 6.1 の受け入れ基準を充足。
- Hard Constraints 違反 0件。
- `pytest tests/` 全件 Pass。
- EMCS（M1〜M6）全項目が閾値内。
- 監査証跡（hash4区分、digest、git hash、相対パス）が全件充足。
- Builder/Validator 分離の入力境界違反 0件。

## 6. 作業上の禁止事項
- 本作業では `git commit` を含む Git 更新系コマンドを実行しない。
