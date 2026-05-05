# 実装計画（Architect）

## 0. 方針
本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md`、`docs/post_mortem.md` を統合し、Phase 6.1 で発生した反復差し戻しを再発不能にする。

最重要ルール:
1. 設計固定前の実装着手を禁止する
2. `pytest` 合格と構造合格を独立ゲート化する
3. UI責務過多と Port 未経由を「注意」ではなく「構造で不可能化」する
4. 構造違反は `REJECT_TO_ARCHITECT` 扱いで設計へ返す

## 1. post_mortem 起点の必達課題
`docs/post_mortem.md` の RC-1〜RC-3 を以下で閉じる。

1. RC-1（境界を強制できていない）
- `UI -> UseCase -> Domain -> Infrastructure` 以外の依存を禁止
- UI から Domain / Infrastructure への直接 import を禁止
- 外部I/O呼び出しを Port 経由へ統一

2. RC-2（差し戻し先の誤り）
- 監査テンプレートに「原因層（設計/実装）」を必須化
- 設計起因の違反は実装へ押し戻さない

3. RC-3（品質ゲート混線）
- 構造ゲート（Gate-S）と機能ゲート（Gate-F）を分離
- Gate-S 未達時は Gate-F を実施しても進行不可

## 2. 境界再設計（固定仕様）
### 2.1 MainWindow の責務除去
対象:
- `MainWindow._run_container`
- `MainWindow._show_create_env_dialog`

移管先:
- `RunPreparationUseCase`（required imports と capability 差分判定、実行可否決定）
- `EnvironmentCreationProposalUseCase`（不足 import から作成候補 package 提案）
- `LifecycleManagementUseCase`（削除/クリーンアップ/部分失敗継続）

UI の責務を「入力受理・状態表示・確認ダイアログ」に限定する。

### 2.2 Port 契約固定
必須 Port:
- `EnvironmentCapabilityPort`
- `EnvironmentRepositoryPort`
- `ContainerRuntimePort`
- `AuditLogPort`
- `ImageCleanupPort`
- `KnowledgeMappingPort`
- `PackageLookupPort`（Phase 6.53: Analyzer 外部照会分離）

規約:
- `typing.Protocol` または `abc.ABC` を必須化
- 引数/戻り値型注釈を必須化
- 境界 DTO は dict 直渡し禁止（アダプタ経由を除く）

### 2.3 DTO・型の固定（Phase 6.2/6.3）
- Pydantic v2 strict を A→B→C 順に導入
1. 監査DTO
2. Runtime判定DTO
3. 環境作成/更新DTO
- 検証失敗は fail-fast
- `mypy` を CI 主ゲート化、`type: ignore` は理由コメント必須

### 2.4 Qt 命名規約固定（reference_standards 4章準拠）
- シグナル命名は過去分詞形（例: `dataChanged`, `executionFinished`）を必須とする
- スロット命名は動詞開始（例: `update_display`, `start_cleanup`）を必須とする
- 命名違反は警告扱いにせず Gate-S 失敗（fail-fast）とする
- 機械検証ルールを固定する
  - Signal: `Signal(...)` を持つ属性名が過去分詞規則に適合すること
  - Slot: `@Slot` デコレータ対象メソッド名が動詞開始規則に適合すること
  - 既存 Qt 命名規約例外は `artifacts/qt_naming_exceptions.md` に理由付きで明示し、無理由例外を禁止する

## 3. フェーズ別実装計画
### Phase A: 6.51 ベースライン固定
- 責務マップ、副作用インベントリ、改修対象/対象外を確定
- `pytest tests/` 現状結果を証跡化

成果物:
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`

### Phase B: 6.1 境界再配線（最優先）
- `_run_container` と `_show_create_env_dialog` の業務判断を UseCase へ移管
- UI 直参照・Port バイパスを全廃

完了条件:
- `UI->Domain直参照 = 0`
- `Port未経由境界越え = 0`
- 対象2関数の UI 業務ロジック = 0

### Phase C: Phase 5 Guardrails 固定
- capability mapping 表示（推定/実証を区別）
- mismatch 時 Run 無効化（Hard Guard）
- 適合環境なし時の新規作成導線強制

完了条件:
- AC-1〜AC-5
- T5-1〜T5-4

### Phase D: Phase 6 Lifecycle 固定
- 専用 Environment Manager で一括削除/2段階確認/部分失敗継続
- dangling + unused image cleanup
- 監査ログ必須項目固定

完了条件:
- AC6-1〜AC6-7
- T6-1〜T6-6

### Phase E: 6.2〜6.4 契約・回帰固定
- DTO strict 化
- static type gate 導入
- Port/DTO/Audit の contract test と golden regression 整備

完了条件:
- AC6.2-1〜AC6.2-5
- AC6.3-1〜AC6.3-4
- AC6.4-1〜AC6.4-4

### Phase F: 6.52 Logging 標準化
- 対象範囲 (`src/lcr/core/container`, `src/lcr/core/detector`) の `print(` を 0 化
- 例外経路の `WARNING/ERROR` 保証

完了条件:
- AC6.52-1〜AC6.52-5

### Phase G: 6.53 Analyzer 境界分離
- `CodeAnalyzer` から直接 network/file I/O を排除
- PyPI照会を `PackageLookupPort` 経由へ移管
- mapping 読み込みを Repository/Port 経由へ移管

完了条件:
- AC6.53-1〜AC6.53-5

### Phase H: Docker再現性標準の固定（reference_standards準拠）
- `Dockerfile` の `FROM` をタグ指定禁止とし、`@sha256:` ダイジェスト固定を必須化
- EOL OS 利用時は APT ソースを `old-releases.ubuntu.com` / `archive.debian.org` へ書き換える
- `constraints.txt` を導入し、pip 依存解決範囲を固定（バックトラッキング暴走防止）
- OpenCV 等のビルド依存を持つ環境はマルチステージビルドを強制（build/runtime 分離）

完了条件:
- ダイジェスト未固定 `FROM` = 0
- EOLベースイメージ利用時のAPTアーカイブ未設定 = 0
- 対象Dockerビルドで `constraints.txt` 未使用 = 0
- C/C++ビルド依存イメージでマルチステージ未適用 = 0

証跡:
- `artifacts/docker_reproducibility_checklist.md`
- `artifacts/docker_digest_lock_evidence.md`
- `artifacts/docker_multistage_evidence.md`

## 4. 品質ゲート（再発防止コア）
### Gate-S（構造）
- `UI->Domain直参照 = 0`
- `逆方向依存 = 0`
- `循環依存 = 0`
- `Portバイパス = 0`
- `MainWindow._run_container` と `_show_create_env_dialog` の業務ロジック = 0
- インターフェース非経由通信 = 0
- EMCS-M1（責務密度）: UIクラスごとの業務判断分岐数（`if/elif` + 判定分岐）<= 2、逸脱件数 = 0
- EMCS-M2（複雑度）: 主要UseCase公開メソッドの循環的複雑度 <= 10、超過件数 = 0
- EMCS-M3（SRP逸脱）: 1クラス内で `UI描画 + 永続化 + 外部I/O` の3責務同居件数 = 0
- EMCS-M4（境界純度）: UI層の外部I/O直接呼び出し件数 = 0
- `UseCase->Qt dependency = 0`
- `Domain->Qt dependency = 0`
- `Qt signal naming violation = 0`
- `Qt slot naming violation = 0`

Gate-S 検査対象パス（固定）:
- UI: `src/lcr/ui`
- UseCase: `src/lcr/core/use_cases`
- Domain: `src/lcr/core/domain`

Gate-S 機械検証ルール（固定）:
- 依存検査（AST/import lint）で `src/lcr/core/use_cases` と `src/lcr/core/domain` から `PyQt*` / `PySide*` import を検出した場合 fail
- 命名検査（AST）で Qt Signal/Slot 規約違反を検出した場合 fail
- 例外は `artifacts/qt_naming_exceptions.md` に記載済みかつ理由付きの場合のみ許可

### Gate-F（機能）
- `pytest tests/` 全件 Pass
- 各Phase必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52/T6.53）Pass
- 監査ログ必須項目テスト Pass
- Docker再現性テスト Pass（ダイジェスト固定/apt書換/constraints/マルチステージ）
- Data Integrity 必須項目テスト Pass（digest/commit hash/全対象SHA-256）
- Qt 命名規約検証テスト Pass（T-UI-NAME-1/2）
- Qt 非依存検証テスト Pass（T-ARCH-QT-1/2）

運用:
- Gate-S fail は設計再作成を必須化
- Gate-F pass 単独では進捗扱いにしない

## 5. 監査・証跡成果物
必須更新:
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`
- `artifacts/phase_6_52_logging_migration_report.md`
- `artifacts/phase_6_52_print_elimination_evidence.md`
- `artifacts/phase_6_53_analyzer_porting_report.md`
- `artifacts/phase_6_53_analyzer_failure_policy.md`
- `artifacts/post_mortem_closure_checklist.md`（新規）
- `artifacts/docker_reproducibility_checklist.md`
- `artifacts/docker_digest_lock_evidence.md`
- `artifacts/docker_multistage_evidence.md`
- `artifacts/data_integrity_field_matrix.md`
- `artifacts/audit_reject_template.md`

`post_mortem_closure_checklist.md` の必須項目:
1. 既知2欠陥の閉塞証跡
2. Gate-S / Gate-F 独立運用記録
3. 差し戻し先判定ログ（Architect/Implementer）

`audit_reject_template.md` の必須項目:
1. 失敗箇所（file path + 関数/クラス + 行動）
2. 違反制約（どの規約/受け入れ基準に違反したか）
3. 具体的修正指示（最小修正単位のヒント）
4. 原因層（設計/実装）の判定
5. 差し戻し先（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）
6. 再検証条件（何を満たせば再提出可能か）

監査運用ルール:
- 上記必須項目が1つでも欠けるREJECTは監査失格として無効化する。

## 6. Definition of Done
1. Gate-S, Gate-F の両方が同一リビジョンで Pass
2. `post_mortem` 指摘2箇所の責務移管完了
3. Phase 5, 6, 6.1〜6.4, 6.51, 6.52, 6.53 の受け入れ基準を満たす
4. 監査証跡が相対パス・ハッシュ完全化・fail-fast 原則に準拠
5. 同型差し戻し（UI責務過多/Port未経由/ゲート混線）が再発しない運用が証跡で確認できる
6. Docker再現性4要件（digest固定/apt書換/constraints/マルチステージ）が証跡付きで満たされる
7. Data Integrity 必須記録項目（コンテナdigest・git commit hash・入力/出力/パラメータ/実行ログSHA-256）が自動テストで担保される
8. Qt 命名規約（Signal/Slot）と UseCase/Domain の Qt 非依存が機械検証で 0 violation

## 7. Data Integrity 実装固定仕様（監査必須）
監査ログの必須記録項目:
1. `container_image_digest`（実行イメージのSHA256ダイジェスト）
2. `git_commit_hash`（`git rev-parse HEAD` の値）
3. `input_sha256`（入力データ）
4. `output_sha256`（出力データ）
5. `parameter_sha256`（パラメータファイル）
6. `execution_log_sha256`（実行ログ本体）
7. `path_mode`（相対パス強制の検証結果）

テスト固定（Gate-F必須）:
- T-DI-1: 上記7項目の存在検証（欠落0件）
- T-DI-2: すべてのハッシュ値がSHA-256形式であることを検証
- T-DI-3: `git_commit_hash` が40桁16進であることを検証
- T-DI-4: パスが絶対パスを含む場合 fail-fast で失敗することを検証

## 8. 追加固定テスト（監査差し戻し是正）
Qt 命名規約:
- T-UI-NAME-1: Signal 命名検証（過去分詞形違反 = 0）
- T-UI-NAME-2: Slot 命名検証（動詞開始違反 = 0）

Qt 非依存:
- T-ARCH-QT-1: UseCase 層の Qt import 検証（`PyQt*` / `PySide*` 依存 = 0）
- T-ARCH-QT-2: Domain 層の Qt import 検証（`PyQt*` / `PySide*` 依存 = 0）

合格条件:
- 上記4テストは Gate-F 必須Pass
- いずれか1件でも失敗した場合は `REJECT_TO_ARCHITECT`
