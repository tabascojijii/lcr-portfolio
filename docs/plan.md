# 実装計画（Architect）

## 0. 目的と前提
本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md`、`docs/post_mortem.md` に準拠し、過去の構造的欠陥（UI責務過多・Port未経由・設計課題の実装押し戻し）を再発不能にすることを目的とする。

最重要方針:
1. 先に設計を固定し、後で実装する（順序逆転を禁止）
2. `pytest` 合格と構造合格を独立ゲートとして運用する
3. UIからDomainへの直接参照を構造的に不可能化する

---

## 1. 対象スコープ
- 主対象:
  - `src/lcr/ui/main_window.py`
  - `src/lcr/core/use_cases/*`
  - `src/lcr/core/*/ports*`（Port定義）
  - `src/lcr/infrastructure/*`（Port実装）
- 要件対応範囲:
  - Phase 5（Validation Guardrails）
  - Phase 6（Lifecycle Management）
  - Phase 6.1〜6.4（疎結合化・型安全化・静的ゲート・契約回帰）
  - Phase 6.51/6.52（可視化・ログ標準化）

---

## 2. 失敗分析に基づく設計制約（Hard Constraints）
`post_mortem` の RC-1〜RC-3 を踏まえ、以下を設計上の強制制約とする。

1. UI層禁止事項（`main_window.py` 含む）
- 業務判断（環境適合判定、未使用判定、削除可否判定）
- 永続化直接操作（JSON更新、監査ログ組み立て）
- 外部I/O直接制御（Docker操作、subprocess実行）

2. 境界越え規約
- `UI -> UseCase -> Domain -> Infrastructure` の一方向依存を固定
- UIからDomain/Infrastructureへの直接import禁止
- すべての外部機能呼び出しはPort経由

3. 差し戻し先規約
- 構造違反の起因が設計層なら `REJECT_TO_ARCHITECT` として再設計
- 実装層へ局所修正を返す前に、設計成果物（責務表・依存図・Port契約）更新を必須化

---

## 3. アーキテクチャ再設計

### 3.1 UseCaseファサード化（MainWindow依存の遮断）
`MainWindow._run_container` と `_show_create_env_dialog` から業務判断を剥離し、以下のUseCaseへ移管する。

- `RunPreparationUseCase`
  - 入力: script解析結果、選択環境ID
  - 出力: `RunGuardDecisionDTO`（実行可否、不足import、推奨環境、誘導アクション）
- `EnvironmentCreationProposalUseCase`
  - 入力: required imports
  - 出力: `EnvironmentCreationProposalDTO`（候補package、根拠種別: knowledge/既定）
- `LifecycleManagementUseCase`
  - 入力: 削除候補/確認状態/実行理由
  - 出力: `LifecycleExecutionResultDTO`（成功/失敗明細、解放容量）

UIはDTOを受けて表示と操作導線のみ担う。

### 3.2 Port再定義（境界強制）
以下Portを明文化し、UseCaseはPort以外へ依存しない。
- `EnvironmentCapabilityPort`
- `EnvironmentRepositoryPort`
- `ContainerRuntimePort`
- `AuditLogPort`
- `ImageCleanupPort`
- `KnowledgeMappingPort`

Portは `typing.Protocol` または `abc.ABC` で型契約を固定し、戻り値型省略と `Any` の無制限利用を禁止。

### 3.3 DTO強化（Phase 6.2整合）
Pydantic v2 strict で以下を段階導入。
1. 監査DTO
2. Runtime判定DTO
3. 環境作成/更新DTO

バリデーション失敗はfail-fast。既存dict入力はアダプタ層で吸収。

---

## 4. 実装フェーズ計画（順序固定）

### Phase A: ベースライン固定（6.51）
1. 責務マップと副作用インベントリを更新
2. `main_window.py` の責務違反箇所を関数単位で証跡化
3. `pytest tests/` 現状値を保存

完了条件:
- `artifacts/phase_6_51_baseline_inventory.md` 更新済み
- `artifacts/phase_6_51_test_baseline.md` 更新済み

### Phase B: 境界再配線（6.1中核是正）
1. `MainWindow._run_container` の判定ロジックを `RunPreparationUseCase` へ移管
2. `_show_create_env_dialog` の候補生成を `EnvironmentCreationProposalUseCase` へ移管
3. UIからDomain/Infrastructure直参照を除去

完了条件:
- `UI->Domain直参照 = 0`
- Port未経由境界越え = 0

### Phase C: ガードレール実装確定（Phase 5）
1. required imports と capability 差分算出をUseCase化
2. mismatch時 `Run` 無効化（Hard Guard）
3. 適合環境なしで作成導線を強制

完了条件:
- AC-1〜AC-5 満足
- T5-1〜T5-4 自動テストPass

### Phase D: ライフサイクル管理確定（Phase 6）
1. Environment Manager導線のUseCase主導化
2. 一括削除2段階確認と部分失敗継続
3. dangling/unused image cleanup
4. 監査ログ必須項目固定

完了条件:
- AC6-1〜AC6-7 満足
- T6-1〜T6-6 Pass

### Phase E: 型・契約・静的ゲート固定（6.2〜6.4）
1. Pydantic DTO strict化
2. `mypy` ゲート導入（必要なら `pyright` 補助）
3. Port契約/監査契約/Golden回帰テスト整備

完了条件:
- AC6.2-1〜AC6.2-5
- AC6.3-1〜AC6.3-4
- AC6.4-1〜AC6.4-4

### Phase F: ログ標準化（6.52）
1. 対象範囲の `print(` を0化
2. レベル規約（DEBUG/INFO/WARNING/ERROR）統一
3. 例外経路ログ保証

完了条件:
- AC6.52-1〜AC6.52-5

---

## 5. 品質ゲート（無限ループ防止の運用分離）

### Gate-1 構造合格（先行必須）
- 禁止依存:
  - `UI->Domain直参照 = 0`
  - `逆方向依存 = 0`
  - `循環依存 = 0`
- UI層業務ロジック:
  - 主要導線で `0`（`_run_container` / `_show_create_env_dialog` を含む）
- Portバイパス:
  - `0`

### Gate-2 機能合格
- `pytest tests/` 全件Pass
- Phase別必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52）Pass

運用規則:
- Gate-1未達時はGate-2結果に関わらず先へ進まない
- Gate-1失敗はArchitect責任で設計更新、Implementerへの局所押し戻し禁止

---

## 6. 監査証跡・成果物
以下成果物を更新し、再現可能性を担保する。

- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`
- `artifacts/phase_6_52_logging_migration_report.md`
- `artifacts/phase_6_52_print_elimination_evidence.md`

監査ログ契約:
- required imports
- environment capability
- mismatch結果
- ガード発火状態
- 操作種別/時刻/対象/成否/解放容量/実行理由
- 相対パス強制
- ハッシュ完全化（入力/出力/実行ログ/主要パラメータ）

---

## 7. リスクと対策
1. 既存UIイベント配線の破断
- 対策: UI変更は最小化し、シグナル/スロット境界でUseCase呼び出しに置換

2. dict互換経路での型移行失敗
- 対策: DTOアダプタを先行導入し、段階的切替

3. テストは通るが構造違反が残る再発
- 対策: Gate-1をCIの先行ジョブ化、未達時は即fail-fast

---

## 8. Definition of Done
以下をすべて満たした場合に完了とする。
1. `pytest tests/` 全件Pass
2. 構造指標:
- `UI->Domain直参照 0`
- `逆方向依存 0`
- `循環依存 0`
- UI層業務ロジック主要導線 0
3. Port契約・DTO契約・監査契約テストPass
4. 監査成果物更新完了
5. `post_mortem` 指摘の2箇所（`_run_container` / `_show_create_env_dialog`）が設計上の責務移管完了状態である

---

## 9. 実行順序（固定）
1. 設計成果物更新（責務表/依存図/Port契約）
2. 構造ゲート試験（Gate-1）
3. 実装着手
4. 機能・回帰試験（Gate-2）
5. 監査証跡更新

この順序を破る変更要求は、再発防止方針違反として却下する。
