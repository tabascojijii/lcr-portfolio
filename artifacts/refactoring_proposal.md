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
n  - mismatch guard
  - forced creation flow
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