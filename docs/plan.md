# 実装計画（Architect）

## 0. 目的と適用範囲
本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md`、`docs/post_mortem.md` を統合し、Phase 6.1 で発生した構造不適合の反復差し戻しを再発不能にするための設計主導実装計画である。

本計画の適用対象:
- Phase 5（Validation Guardrails）
- Phase 6（Lifecycle Management）
- Phase 6.1〜6.4（疎結合化・型安全化・契約固定）
- Phase 6.51〜6.54（ベースライン固定・ログ標準化・副作用分離）

## 1. 最優先原則（固定）
1. 設計固定前の実装着手を禁止する。
2. `pytest` 合格と構造合格を独立ゲートで管理する。
3. UI責務過多・Port未経由は「検出」ではなく「構造的に不可能化」する。
4. 構造違反の差し戻し先は Implementer ではなく Architect とする（`REJECT_TO_ARCHITECT`）。
5. `docs/reference_standards.md` の必須規約は「推奨」ではなく「固定要件」としてDoDに拘束する。

## 2. post_mortem 起点の是正要求（RC閉塞）
`docs/post_mortem.md` の RC-1〜RC-3 を以下で閉じる。

### RC-1 境界強制不全の是正
- 依存方向を `UI -> UseCase -> Domain -> Infrastructure` に固定。
- `src/lcr/ui` から `Domain` 直参照を禁止。
- 外部I/O（file/network/subprocess）は Port/Gateway/Repository 経由に統一。

### RC-2 差し戻し先誤りの是正
- 監査テンプレートに「原因層（設計/実装）」を必須項目化。
- 設計起因違反は実装差し戻しを禁止し、設計再作成を必須化。

### RC-3 ゲート混線の是正
- Gate-S（構造）と Gate-F（機能）を分離運用。
- Gate-S 未達時は Gate-F 合格でも進行禁止。

## 3. 境界再設計（固定仕様）

### 3.1 MainWindow 重点2箇所の責務移管
対象:
- `MainWindow._run_container`
- `MainWindow._show_create_env_dialog`

移管先:
- `RunPreparationUseCase`: required imports 抽出結果と environment capability 差分判定、Run可否判定。
- `EnvironmentCreationProposalUseCase`: 不足 import から package 候補生成。
- `LifecycleManagementUseCase`: 一括削除、2段階確認前提の実行、部分失敗継続。

UIの責務は「入力受理・表示更新・確認ダイアログ」に限定する。

### 3.2 Port/Interface 契約
必須Port:
- `EnvironmentCapabilityPort`
- `EnvironmentRepositoryPort`
- `ContainerRuntimePort`
- `AuditLogPort`
- `ImageCleanupPort`
- `KnowledgeMappingPort`
- `PackageLookupPort`

契約規約:
- `typing.Protocol` または `abc.ABC` を使用。
- 引数/戻り値型注釈を必須化。
- 境界DTOは Pydantic モデルを通す（旧dict入力はアダプタで吸収）。

### 3.3 型安全（Phase 6.2/6.3 連動）
- Pydantic v2 strict を A→B→C 順で導入。
1. 監査メタデータDTO
2. Runtime判定DTO
3. 環境作成/更新DTO
- 検証失敗は fail-fast。
- `mypy` を主ゲート化、`type: ignore` は理由コメント必須。

### 3.4 Data Integrity 固定
監査ログに以下を必須記録:
- `container_image_digest`
- `git_commit_hash`
- `input_sha256`
- `output_sha256`
- `parameter_sha256`
- `execution_log_sha256`
- `path_mode`（相対パス強制結果）

### 3.5 UIイベント命名規約（固定）
- Signal は過去分詞形（例: `environmentCreated`, `validationFailed`）を必須とする。
- Slot は動詞始まり（例: `update_environment_list`, `show_validation_error`）を必須とする。
- 新規/変更UIイベントは命名規約違反をレビューでRejectする。
- 検証方法:
  - UI層変更PRで Signal/Slot 一覧を差分提出する。
  - `tests/architecture/test_ui_signal_slot_naming.py`（追加必須）で命名パターン検査を自動化する。

## 3.6 Docker Reproducibility 固定章（必須）
`docs/reference_standards.md` 2章に基づき、以下4要件を全フェーズ共通の拘束条件として固定する。

1. `FROM` digest 固定
- `Dockerfile` の `FROM` はタグ禁止、`@sha256:` 必須。
- 検証: `tests/architecture/test_docker_reproducibility.py::test_from_uses_digest_only`

2. EOL APT リポジトリ固定
- EOL OS利用時、APTソースはアーカイブ（`old-releases.ubuntu.com` / `archive.debian.org`）へ書換必須。
- 検証: `test_eol_apt_uses_archive_mirror`

3. pip constraints 強制
- EOL/legacy依存を含む build は `constraints.txt` を必須化し、無制約installを禁止。
- 検証: `test_pip_install_has_constraints`

4. マルチステージビルド強制
- OpenCV等のネイティブビルドは build/runtime ステージ分離を必須化。
- 検証: `test_native_build_uses_multistage`

## 4. フェーズ実行順（変更禁止）

### Phase A: 6.51 Baseline Visualization
- 責務マップ、副作用インベントリ、改修対象/対象外を固定。
- `pytest tests/` 現状結果を証跡化。

### Phase B: 6.1 Boundary Refactoring（最優先）
- `_run_container` と `_show_create_env_dialog` から業務判断を除去。
- UI->Domain 直参照と Port バイパスを 0 化。

### Phase C: Phase 5 Guardrails
- capability mapping（推定/実証）表示。
- mismatch 時の Run Hard Guard。
- 適合環境なし時の新規作成導線を強制。

### Phase D: Phase 6 Lifecycle
- 専用 Environment Manager 実装。
- 一括削除2段階確認、部分失敗継続、cleanup範囲（dangling/unused）固定。

### Phase E: 6.2〜6.4 Contract Hardening
- DTO strict 化、型ゲート導入、Port/DTO/Audit 契約テスト、golden regression 固定。

### Phase F: 6.52 Logging Standardization
- `src/lcr/core/container`, `src/lcr/core/detector` の `print(` を 0 化。
- 例外/フォールバック経路で `WARNING/ERROR` 保証。

### Phase G: 6.53 Analyzer Side-Effect Porting
- `CodeAnalyzer` から direct network/file I/O を排除。
- `PackageLookupPort` と mapping Repository 経由へ統一。

### Phase H: 6.54 Container Side-Effect Porting
- 永続化、Docker照会、ファイル副作用を Repository/Gateway/Service に分離。
- エラー分類（recoverable/non-recoverable）と伝播規約を固定。

## 5. 品質ゲート（独立運用）

### Gate-S: 構造ゲート
合格条件（全て0件）:
- `UI->Domain direct import`
- `逆方向依存`
- `循環依存`
- `Portバイパス`
- `MainWindow._run_container` 業務判断残存
- `MainWindow._show_create_env_dialog` 業務判断残存
- `UseCase/Domain -> Qt依存`
- `Dockerfile FROM tag usage`（digest未使用）
- `UI Signal/Slot naming violation`

EMCS客観メトリクス（閾値固定）:
- `SRP violation hotspots`: 0件
  - 測定: UI層クラスで「UI描画以外の責務カテゴリ（判定/永続化/外部I/O）」が2種以上混在するクラス数
- `Cyclomatic complexity overflow`: 0件
  - 閾値: UseCase公開メソッド `CC <= 10`、UIメソッド `CC <= 7`
- `UI method LOC overflow`: 0件
  - 閾値: UIイベントハンドラ `<= 40 LOC`
- `Unjustified type ignore`: 0件
  - `# type: ignore` に理由コメントがないものを違反として計上

自動REJECT条件:
- 上記メトリクスのいずれかが閾値超過した時点で `REJECT_TO_ARCHITECT`。
- Gate-F未実行でもGate-S単独で差し戻し確定とする。

### Gate-F: 機能ゲート
合格条件:
- `pytest tests/` 全件Pass
- Phase別必須テスト（T5, T6, T6.2, T6.3, T6.4, T6.51, T6.52, T6.53, T6.54）Pass
- Data Integrity 必須項目テストPass
- Docker Reproducibility 4要件テストPass（3.6節）
- UI Signal/Slot命名テストPass（3.5節）

運用規則:
- Gate-S fail 時は `REJECT_TO_ARCHITECT`。
- Gate-F pass 単独は進捗扱いにしない。

## 6. 受け入れ判定（DoD）
1. Gate-S と Gate-F が同一リビジョンで同時Pass。
2. post_mortem 指摘2箇所（`_run_container`, `_show_create_env_dialog`）の責務移管完了。
3. Phase 5, 6, 6.1〜6.4, 6.51〜6.54 の受け入れ基準を満たす。
4. 監査証跡が相対パス・ハッシュ完全化・fail-fast原則に準拠。
5. 同型障害（UI責務過多/Port未経由/ゲート混線）の再発防止証跡が存在。
6. Docker Reproducibility 4要件（digest固定/EOL archive/constraints/マルチステージ）の証跡が存在。
7. EMCS客観メトリクスの実測値と閾値判定結果が監査成果物に記録されている。
8. Builder/Validator分離ルールに違反する監査入力が0件である。

## 6.1 Builder/Validator 分離運用（固定）
監査担当（Validator/Auditor）への許容入力を以下に限定する。
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

## 7. 監査成果物（必須）
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

## 8. 実行上の禁止事項
- 設計承認前の実装開始。
- Gate-S 未達状態での「テストが通っているからOK」判断。
- UI層への業務判断・外部I/Oロジック再流入。
- 監査根拠なきREJECT（処方的指示なし）。
- 絶対パス監査ログの許容。
