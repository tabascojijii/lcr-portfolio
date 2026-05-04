# Refactoring Proposal

目的: `UI -> UseCase -> Domain` を強制し、UIから業務判断とI/Oオーケストレーションを段階的に除去する。

## P0 (ガードレール)

- Port設計:
  - `RuntimeInventoryPort`: image存在確認/環境能力取得
  - `ExecutionGatewayPort`: 実行引数生成/実行要求
  - `ArtifactDiscoveryPort`: 出力成果物探索
  - `PathPolicyPort`: ルート相対パス正規化
- 移管先レイヤ: `lcr.core.*.use_cases` に新規UseCaseを追加し、UIは入力収集と表示更新のみ担当。
- 後方互換維持策:
  - 既存 `MainWindow` メソッド名/シグネチャは保持し、内部でUseCase呼び出しに置換する。
  - 既存監査キー (`image_digest`, `param_hash`, `log_hash`) は残しつつ標準キーを追加する。

## P1 (Phase 5中核移管)

- `RunExecutionOrchestrationUseCase` を追加し、以下を移管:
  - capability mapping
  - mismatch guard
  - forced creation flow
- 実装状況 (2026-05-04):
  - `RuntimeExecutionPreparationUseCase.prepare_run_decision(...)` を追加し、UIは `requires_compatibility_confirmation` / `requires_image_build` フラグで表示制御のみを行う構成に変更。
- UIは `can_run` と `requires_creation` の結果のみを受け取り、ボタン状態と遷移だけを担当。
- テスト戦略:
  - T5-1 mismatch時 Run無効
  - T5-2 適合時 Run有効
  - T5-3 適合環境なし時 作成導線遷移
  - T5-4 作成後即時反映

## P2 (Phase 6移管)

- `EnvironmentManagerUseCase` を追加し、以下を移管:
  - 検索/未使用抽出/二段階確認付き一括削除
  - cleanup対象限定 (dangling/unused image)
  - メタデータ編集 (内部ID不変)
- 監査連携UseCaseで削除/編集/cleanup操作ごとの監査記録を生成。
- テスト戦略:
  - T6-1〜T6-6 を `tests/test_environment_lifecycle_use_case.py` と監査系テストへ集約。

## リスク対策

- リスク: UseCase化でUIイベント接続が崩れる。
  - 対策: Signal/Slot 結線を変えず、呼び出し先のみ差し替える。
- リスク: 監査スキーマ追加で既存ログ利用が壊れる。
  - 対策: 互換キーを残す、欠落キーはデフォルト値を付与する。
- リスク: 削除処理の失敗時挙動が変化する。
  - 対策: 部分失敗継続を固定し、`rollback_on_any_failure=False` を既定とする。

## Change Impact Test Protocol (AC6.1-6)

### シナリオA: UI変更時のDomain影響最小化

- 変更シナリオ:
  - `src/lcr/ui/main_window.py` の表示文言・レイアウト・ボタン状態更新のみに限定した変更を加える。
- 期待影響範囲:
  - Domain層ファイル差分 0件
  - Domain層テスト失敗 0件
- 合否条件:
  - `pytest tests/` 実行時に Domain関連テストが全Pass
  - 依存方向違反件数が増加しない

### シナリオB: Domain変更時のUI影響最小化

- 変更シナリオ:
  - UseCase/Domainの内部ロジックをPort契約を維持したまま変更する。
- 期待影響範囲:
  - UI層修正はDTO受け渡し調整の最小範囲に限定
  - 画面イベント結線（Signal/Slot）変更なし
- 合否条件:
  - UI E2E主要導線（Run/Build/History）が回帰しない
  - `pytest tests/` 全Pass

## Fixed Numeric Acceptance Thresholds (AC6.1-7)

- 禁止依存件数: **0件**
- 循環依存件数: **0件**
- UI層業務ロジック件数: **0件**
- 境界違反テスト pass率: **100%**

上記閾値を1つでも満たさない場合は、Phase 6.1 を未達（REJECT）と判定する。

## Remaining Delta (2026-05-04)

- `MainWindow._run_container` の遷移分岐を `RunExecutionOrchestrationUseCase` にさらに移管し、UI側はダイアログ表示API呼び出しだけに限定する。
- `EnvironmentCreationDialog` への `ContainerManager` 直渡しを廃止し、`EnvironmentBuildPreparationUseCase` と Port 経由のI/Fに統一する。
- 受け入れ完了条件: `artifacts/architecture_decoupling_assessment.md` の `UI->Domain直参照` を 0件化。
