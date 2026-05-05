# LCR Roadmap（Reference Standards 絶対準拠版）

## 0. 位置づけ
本ロードマップは `docs/reference_standards.md` を絶対基準として、`docs/plan.md` の実装計画を実行順・完了条件・監査条件まで運用可能な形に固定したものである。

優先順位は常に以下とする。
1. `docs/reference_standards.md`
2. `docs/plan.md`

上位基準との不整合が発生した場合、実装を停止し、Architectに設計差し戻し（`REJECT_TO_ARCHITECT`）を行う。

## 1. 絶対ガバナンス（全フェーズ共通）
- EMCS客観メトリクスでのみ構造判定を行う（主観判断禁止）。
- Builder/Validator分離を厳守し、監査入力は要件・差分・テスト証跡に限定する。
- REJECTは処方的に記述する（失敗箇所、違反制約、最小修正指示、原因層、差し戻し先、再検証条件）。
- Gate-S（構造）と Gate-F（機能）を独立運用し、Gate-S未達時は進行禁止とする。

### 1.1 Builder/Validator 分離運用（固定）
監査担当（Validator/Auditor）への許容入力:
- `docs/requirements.md`
- `docs/reference_standards.md`
- `git diff`（または同等差分）
- テスト証跡（`pytest` / 型検査 / Gate-S測定結果）

監査担当への禁止入力:
- 実装者の思考過程メモ
- 口頭/チャットでの主観的補足説明
- 「意図したからOK」という非検証主張
- 差分に存在しない将来対応の約束

違反時規則:
- 禁止入力が監査判定に混入した場合、その監査は無効化し再監査を必須とする。
- 無効化時は `artifacts/audit_reject_template.md` に「監査I/O境界違反」として記録する。

## 2. 不変の技術拘束（全フェーズ共通）

### 2.1 Docker Reproducibility
- `Dockerfile` の `FROM` はタグ禁止、`@sha256:` 固定必須。
- EOL OS はAPTソースをアーカイブミラーへ固定。
- EOL/legacy依存ビルドは `constraints.txt` 必須。
- ネイティブビルドはマルチステージを必須化。

### 2.2 Data Integrity
- 監査ログに `container_image_digest` と `git_commit_hash` を必須記録。
- 入力/出力/パラメータ/実行ログのSHA-256を必須記録。
- 監査ログに `path_mode`（相対パス強制結果）を必須記録。
- パスはプロジェクトルート相対のみを許容（絶対パス禁止）。

### 2.3 UI/Architecture Discipline
- UIはHumble Objectを厳守し、業務判断・外部I/Oを持たない。
- 依存方向は `UI -> UseCase -> Domain -> Infrastructure` に固定。
- Port/Interface は `abc.ABC` または `typing.Protocol` を必須利用。
- 必須Port一覧を固定要件とする: `EnvironmentCapabilityPort`, `EnvironmentRepositoryPort`, `ContainerRuntimePort`, `AuditLogPort`, `ImageCleanupPort`, `KnowledgeMappingPort`, `PackageLookupPort`（欠落はGate-S不合格）。
- Signal は過去分詞、Slot は動詞始まりを必須化。

## 3. フェーズロードマップ（変更禁止）

### Phase A: 6.51 Baseline Visualization
目的:
- 現状アーキテクチャと副作用分布を可視化し、後続フェーズの固定比較基準を作る。

主要成果物:
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`

完了条件:
- 責務マップ・副作用インベントリ・改修対象/対象外が明示されている。
- `pytest tests/` の現状証跡が保存されている。

### Phase B: 6.1 Boundary Refactoring（最優先）
目的:
- `MainWindow._run_container` と `MainWindow._show_create_env_dialog` の業務判断をUseCaseへ完全移管する。

主要成果物:
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`

完了条件:
- UIからDomain直参照が0件。
- Portバイパスが0件。
- 上記2メソッドに業務判断が残存しない。

### Phase C: Phase 5 Validation Guardrails
目的:
- 実行前整合性チェックを強制し、ミスマッチ時の実行を構造的に防止する。

完了条件:
- capability mapping（推定/実証）が表示される。
- mismatch時にRun Hard Guardが発火する。
- 適合環境なし時に新規作成導線が強制される。

### Phase D: Phase 6 Lifecycle Management
目的:
- ライフサイクル操作を専用UseCase/Managerに集約し、UIから副作用制御を分離する。

完了条件:
- 一括削除の2段階確認が強制される。
- 部分失敗継続ポリシーが実装される。
- cleanup範囲（dangling/unused）が固定される。

### Phase E: 6.2-6.4 Contract Hardening
目的:
- DTO/Port契約を型レベルで固定し、逸脱を実行前に検出する。

完了条件:
- Pydantic v2 strictを監査DTO→Runtime DTO→環境DTOの順で適用。
- 境界DTOは必ずPydanticモデルを通過させ、旧dict入力はアダプタ層のみで吸収する。
- `mypy` を主ゲート化し、理由なき `type: ignore` を0件化。
- Port/DTO/Audit契約テストとgolden regressionが安定運用される。

### Phase F: 6.52 Logging Standardization
目的:
- ログ出力を監査可能な構造へ統一し、`print(` を排除する。

主要成果物:
- `artifacts/phase_6_52_logging_migration_report.md`
- `artifacts/phase_6_52_print_elimination_evidence.md`

完了条件:
- `src/lcr/core/container` と `src/lcr/core/detector` の `print(` が0件。
- 例外/フォールバック経路で `WARNING/ERROR` ログが保証される。

### Phase G: 6.53 Analyzer Side-Effect Porting
目的:
- Analyzerの直接I/Oを排除し、Port経由に統一する。

主要成果物:
- `artifacts/phase_6_53_analyzer_porting_report.md`
- `artifacts/phase_6_53_analyzer_failure_policy.md`

完了条件:
- `CodeAnalyzer` のdirect network/file I/Oが0件。
- `PackageLookupPort` と mapping Repository 経由に統一される。

### Phase H: 6.54 Container Side-Effect Porting
目的:
- Container関連副作用をRepository/Gateway/Serviceへ分離し、障害分類を固定する。

主要成果物:
- `artifacts/phase_6_54_container_porting_report.md`
- `artifacts/phase_6_54_container_error_model.md`

完了条件:
- 永続化/Docker照会/ファイル副作用がUI・UseCaseから分離される。
- recoverable/non-recoverableの分類と伝播規約が適用される。

## 4. 品質ゲート

### Gate-S（構造）
合格条件（全て0件）:
- `UI->Domain direct import`
- 逆方向依存
- 循環依存
- Portバイパス
- `MainWindow._run_container` 業務判断残存
- `MainWindow._show_create_env_dialog` 業務判断残存
- `UseCase/Domain -> Qt依存`
- `Dockerfile FROM tag usage`
- `UI Signal/Slot naming violation`
- `Unjustified type ignore`

EMCS閾値:
- SRP violation hotspots: 0件
- Cyclomatic complexity overflow: 0件（UseCase公開 `CC <= 10`、UIメソッド `CC <= 7`）
- UI method LOC overflow: 0件（UIイベントハンドラ `<= 40 LOC`）

### Gate-F（機能）
合格条件:
- `pytest tests/` 全件Pass
- フェーズ別必須テスト（T5, T6, T6.2, T6.3, T6.4, T6.51, T6.52, T6.53, T6.54）Pass
- Data Integrity 必須項目テストPass
- Docker Reproducibility 4要件テストPass
- UI Signal/Slot命名テストPass

運用規則:
- EMCS各メトリクスの閾値超過はGate-S failと同値とし、検出時点で自動 `REJECT_TO_ARCHITECT` とする。
- Gate-S fail 時点で `REJECT_TO_ARCHITECT`。
- Gate-F pass単独は進捗として扱わない。

## 5. 監査成果物（必須）
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`
- `artifacts/phase_6_52_logging_migration_report.md`
- `artifacts/phase_6_52_print_elimination_evidence.md`
- `artifacts/phase_6_53_analyzer_porting_report.md`
- `artifacts/phase_6_53_analyzer_failure_policy.md`
- `artifacts/phase_6_54_container_porting_report.md`
- `artifacts/phase_6_54_container_error_model.md`
- `artifacts/post_mortem_closure_checklist.md`
- `artifacts/audit_reject_template.md`

`post_mortem_closure_checklist.md` 必須項目:
1. RC-1〜RC-3 の閉塞証跡
2. Gate-S/Gate-F 独立運用記録
3. 差し戻し先判定ログ（Architect/Implementer）

`audit_reject_template.md` 必須項目:
1. 失敗箇所（file path + 関数/クラス）
2. 違反制約（規約/受け入れ基準）
3. 最小修正単位の指示
4. 原因層（設計/実装）
5. 差し戻し先（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）
6. 再検証条件

## 6. 最終受け入れ条件（DoD）
1. Gate-S と Gate-F が同一リビジョンで同時Passしている。
2. RC-1〜RC-3（境界強制不全、差し戻し先誤り、ゲート混線）の閉塞証跡がある。
3. `MainWindow._run_container` と `MainWindow._show_create_env_dialog` の責務移管が完了している。
4. Data Integrity（相対パス・ハッシュ完全化・不変識別子記録）に違反がない。
5. Docker Reproducibility 4要件（digest/EOL archive/constraints/マルチステージ）に違反がない。
6. EMCS実測値と閾値判定結果が監査成果物に記録されている。
7. Builder/Validator分離に違反する監査入力が0件である。

## 7. 禁止事項
- 設計承認前に実装へ着手すること。
- Gate-S未達で「テスト合格」を理由に進行すること。
- UI層へ業務判断・外部I/Oを再流入させること。
- 根拠なきREJECT（処方的指示なし）を行うこと。
- 監査証跡に絶対パスを残すこと。
