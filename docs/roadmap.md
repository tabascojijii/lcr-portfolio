# Roadmap (PM)

## 0. Purpose and Absolute Baseline
- 本ロードマップは `docs/reference_standards.md` を絶対基準とし、`docs/plan.md` の実装順序・検証条件・完了条件をPM視点で実行管理可能な形に再編したものである。
- 逸脱判定は Auditor が `reference_standards` に基づき実施し、例外運用は認めない。
- 目的は Phase 5 / Phase 6 / Phase 6.1 を、再現性・監査可能性・疎結合性を同時満足して完了させること。

## 1. Non-Negotiable Standards Gate
以下は全フェーズ共通の絶対条件（違反時即REJECT）。

1. 監査・ガバナンス
- Builder/Validator 分離を維持し、Auditor 入力は `requirements` と `diff` に限定する。
- REJECT は処方的形式（失敗箇所、違反制約、観測証拠、修正ヒント、再検証条件、ルーティング先）を必須化する。

2. Docker再現性
- `Dockerfile` の `FROM` は SHA256 digest 固定。
- EOL OS のAPTは archive repository にリダイレクト。
- pip依存は `constraints.txt` で固定。
- OpenCV等のネイティブビルドは multi-stage build を強制。

3. データ完全性
- ハッシュ対象4区分を全件必須化:
  - `all_input_files`
  - `all_output_files`
  - `all_parameter_files`
  - `audit_log_record`
- 監査ログへ `container_image_digest` と `git_commit_hash` を必須記録。
- すべての記録パスはプロジェクトルート相対パス（絶対パス禁止）。

4. UI/アーキテクチャ規律
- 依存方向は `UI -> UseCase -> Domain` のみ許可。
- `Infrastructure` は Port 実装側としてのみ接続。
- 禁止依存:
  - `UseCase -> Qt`
  - `Domain -> Qt`
  - `Domain -> Infrastructure`
  - `UI -> Domain`（直参照）
  - `UseCase -> Infrastructure`（具象依存）
- 境界越え通信は `abc.ABC` / `typing.Protocol` 経由のみ。
- Humble Object を強制し、UIクラスでの業務判断・I/O・Docker操作・複雑計算・業務フォーマットを禁止。
- Signal/Slot 命名規約:
  - Signal: 過去分詞形
  - Slot: 動詞

## 2. Delivery Scope
1. Phase 5
- Capability Mapping
- Mismatch Guard
- Forced Creation Flow
- 監査ログ連携（required imports / capability / mismatch / guard）

2. Phase 6
- Environment Manager専用UI
- 2段階確認付き一括削除（部分失敗継続）
- 未使用抽出（最終利用日時+利用回数+保護フラグ）
- dangling/unused image 限定クリーンアップ
- メタデータ編集（内部ID不変）
- 削除/編集/クリーンアップ監査ログ

3. Phase 6.1
- `artifacts/architecture_decoupling_assessment.md` 作成
- `artifacts/refactoring_proposal.md` 作成

## 3. Execution Roadmap (Mandatory Order)

### P0: Governance Baseline (Start Gate)
実装着手前に以下を完了し、1件でも未充足なら着手禁止。

1. 監査ログスキーマ固定
- 必須フィールド:
  - `operation_type`
  - `timestamp`
  - `targets`
  - `result`
  - `released_size`
  - `reason`
  - `required_imports`
  - `environment_capability`
  - `mismatch_result`
  - `guard_triggered`
  - `hashes.all_input_files`
  - `hashes.all_output_files`
  - `hashes.all_parameter_files`
  - `hashes.audit_log_record`
  - `container_image_digest`
  - `git_commit_hash`

2. CI/Lint ゲート投入
- 依存方向違反検出（`UseCase -> Qt` 含む）
- UI禁止行為検出
- ハッシュ4区分欠落・絶対パス検出
- Docker再現性違反検出
- Builder/Validator 入力境界違反検出
- REJECTテンプレート必須項目欠落検出
- Signal/Slot 命名規約違反検出

3. アーキテクト事前確認
- RC-1/RC-2/RC-3 と監査ルーティング分離が、plan・schema・test・checklist で整合していること。

### P1: Phase 5 Implementation
1. Capability Mapping UseCase 実装
2. Mismatch Guard UseCase 実装
3. Forced Creation Flow 実装
4. 監査ログ項目接続

### P2: Phase 6 Implementation
1. Environment Manager UI 実装
2. 2段階確認付き一括削除実装
3. 未使用抽出ロジック実装
4. 限定クリーンアップ実装
5. メタデータ編集実装
6. 監査ログ実装

### P3: Phase 6.1 Deliverables
1. `artifacts/architecture_decoupling_assessment.md`
- `file path + class/function + violation type + evidence` 形式で違反列挙。
- `UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数を明示。

2. `artifacts/refactoring_proposal.md`
- P0/P1/P2優先度で段階移行計画を提示。
- Port設計、移管先レイヤ、後方互換維持策、テスト戦略、リスク対策を明示。

## 4. Verification Gates

### 4.1 Functional Gate
- `pytest tests/` 全件Pass必須。
- 最低追加テスト:
  - T5-1 mismatch時 `Run` 無効化
  - T5-2 適合時 `Run` 有効 + 実行可能
  - T5-3 適合環境なし時 作成導線遷移
  - T5-4 作成後即時反映
  - T6-1 2段階確認未完了時 削除不可
  - T6-2 未使用判定（日時+回数+保護フラグ）
  - T6-3 一括削除部分失敗継続
  - T6-4 編集時 内部ID不変
  - T6-5 クリーンアップ対象限定
  - T6-6 監査ログ完全性

### 4.2 Structural Gate
- 禁止依存0件
- UI禁止行為0件
- Port未経由境界越え0件
- 循環依存0件
- Signal/Slot命名規約違反0件

### 4.3 Audit Gate
- ハッシュ4区分欠落0件
- 相対パス違反0件
- `container_image_digest` 欠落0件
- `git_commit_hash` 欠落0件
- REJECTテンプレート必須項目欠落0件

### 4.4 Objective Metrics (EMCS)
- M1: 依存方向違反件数 = 0
- M2: UI SRP違反件数 = 0
- M3: 複雑度超過（CC > 10）件数 = 0
- M4: 監査証跡欠落件数 = 0
- M5: Docker再現性違反件数 = 0
- M6: Signal/Slot命名規約違反件数 = 0

## 5. RACI and Routing
- Architect: P0整合性承認、設計差し戻し対応。
- PM: フェーズ進行管理、ゲート通過判定、依存解消の優先順位制御。
- Implementer: P1/P2実装とテスト修正。
- Auditor: `reference_standards` 準拠監査、REJECT/PASS判定。

ルーティング規則:
- 設計不備: `REJECT_TO_ARCHITECT`
- 実装不備: `REJECT_TO_IMPLEMENT`

## 6. Timeline Control (Milestone)
- M0: P0完了（着手許可）
- M1: Phase 5完了（機能+監査ログ+テスト）
- M2: Phase 6完了（管理UI+安全削除+監査）
- M3: Phase 6.1成果物完了（評価+移行計画）
- M4: 全Gate通過、DoD成立

## 7. Definition of Done
- Phase 5 / Phase 6 / Phase 6.1 の受け入れ基準を満たす。
- 本文書 Section 1 の絶対条件違反が0件。
- `pytest tests/` 全件Pass。
- EMCS（M1〜M6）全項目が閾値内。
- 監査証跡（hash4区分、digest、git hash、相対パス）が全件充足。
- Builder/Validator分離の入力境界違反0件。

## 8. Change Control
- `docs/reference_standards.md` と矛盾する変更要求は受理しない。
- `docs/plan.md` と本 `docs/roadmap.md` に差分が生じた場合、実装を停止し PM が整合改訂を実施する。
- PASS判定時もRC-1〜RC-3非回帰確認を省略しない。

## 9. Explicit Prohibition
- 本作業では `git commit` を実行しない。
