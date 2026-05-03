# Refactoring Proposal

## Goal

`UI -> UseCase -> Domain` の依存方向を維持しつつ、`MainWindow` から業務判断・実行オーケストレーション・監査整形を移管する。

## Targeted Transfers

- 移管対象: `MainWindow._run_container` の実行判定・環境不足時分岐。
- 移管先レイヤ: UseCase (`RunExecutionOrchestrationUseCase`)。
- 必要Port:
  - `RuntimeInventoryPort`（image existence / runtime metadata取得）
  - `ExecutionGatewayPort`（docker args生成と実行要求）
  - `EnvironmentProvisioningPort`（不足時の再ビルド要求）

- 移管対象: `MainWindow._append_audit_metadata` の監査メタ構築・相対パス変換。
- 移管先レイヤ: UseCase (`BuildAuditRecordUseCase`)。
- 必要Port:
  - `AuditMetadataPort`（既存）
  - `PathPolicyPort`（project-root相対パス変換）
  - `ArtifactDiscoveryPort`（output files収集）

- 移管対象: `MainWindow._load_results` のCSVプレビュー整形。
- 移管先レイヤ: UseCase (`ResultPreviewUseCase`)。
- 必要Port:
  - `ResultReaderPort`（CSV/画像メタ読取）
  - `PreviewFormatterPort`（UI表示用DTO生成）

- 移管対象: 環境ライフサイクル操作（検索、未使用抽出、一括削除2段階確認、cleanup対象限定、メタ更新）。
- 移管先レイヤ: UseCase (`EnvironmentLifecycleUseCase`)。
- 必要Port:
  - `EnvironmentRepositoryPort`
  - `EnvironmentDeletionPort`
  - `CleanupInventoryPort`

## Phase Plan

- P0:
  - `EnvironmentLifecycleUseCase` を導入し、削除安全性・保護フラグ・cleanup対象制約をユニットテストで固定。
  - `PathPolicyPort` を定義し、UI直実装の相対パス変換を移管準備。

- P1:
  - `RunExecutionOrchestrationUseCase` を導入し、`MainWindow._run_container` の分岐ロジックを移管。
  - UIは入力収集と結果表示のみを担当。

- P2:
  - `BuildAuditRecordUseCase` / `ResultPreviewUseCase` を導入し、監査整形とCSVプレビュー整形をUIから除去。
  - `MainWindow` の関数複雑度・分岐数を削減し、Humble Object準拠を完了。

## Verification

- Structural:
  - `UI` モジュールに Docker実行分岐・監査整形・CSV業務整形が残っていないこと。
  - 層間通信が `Protocol` 経由であること。

- Functional:
  - `pytest tests/` 全Pass。
  - 一括削除の2段階確認、保護フラグ尊重、部分失敗継続、cleanup対象制約の検証Pass。

- Audit:
  - 監査メタ必須項目（`container_image_digest`、`git_commit_hash`、4区分ハッシュ）が欠落しないこと。
  - 相対パス規約違反が0件であること。
