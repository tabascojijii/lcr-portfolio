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

## 4. 品質ゲート（再発防止コア）
### Gate-S（構造）
- `UI->Domain直参照 = 0`
- `逆方向依存 = 0`
- `循環依存 = 0`
- `Portバイパス = 0`
- `MainWindow._run_container` と `_show_create_env_dialog` の業務ロジック = 0
- インターフェース非経由通信 = 0

### Gate-F（機能）
- `pytest tests/` 全件 Pass
- 各Phase必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52/T6.53）Pass
- 監査ログ必須項目テスト Pass

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

`post_mortem_closure_checklist.md` の必須項目:
1. 既知2欠陥の閉塞証跡
2. Gate-S / Gate-F 独立運用記録
3. 差し戻し先判定ログ（Architect/Implementer）

## 6. Definition of Done
1. Gate-S, Gate-F の両方が同一リビジョンで Pass
2. `post_mortem` 指摘2箇所の責務移管完了
3. Phase 5, 6, 6.1〜6.4, 6.51, 6.52, 6.53 の受け入れ基準を満たす
4. 監査証跡が相対パス・ハッシュ完全化・fail-fast 原則に準拠
5. 同型差し戻し（UI責務過多/Port未経由/ゲート混線）が再発しない運用が証跡で確認できる
