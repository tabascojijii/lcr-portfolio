# Implementation Plan (Architect)

## 0. Plan Purpose
- 本計画は `docs/core_philosophy.md` / `docs/requirements.md` / `docs/reference_standards.md` に完全準拠し、`docs/post_mortem.md` の構造的欠陥を解消した実装順序と検証ゲートを定義する。
- 対象フェーズは Phase 5, Phase 6, Phase 6.1。
- 目的は「動作達成」ではなく「監査可能で再現可能な実装の成立」。

## 1. Non-Negotiable Architecture & Integrity Constraints

### 1.1 Dependency Direction (Hard Constraint)
- 許可依存: `UI -> UseCase -> Domain -> Infrastructure`。
- 禁止依存:
  - `UseCase -> Qt`（明示禁止）
  - `Domain -> Qt`
  - `Domain -> Infrastructure`
  - `UI -> Domain` の直接到達（UseCase経由を強制）
- 境界越えは `Port/Interface (abc.ABC or typing.Protocol)` 経由のみ。

### 1.2 Humble Object Constraint (Hard Constraint)
- UI層（例: `MainWindow`, Dialog, Widget）で以下を禁止:
  - 業務判断・分岐
  - 永続化/外部I/O直接実行
  - 複雑計算
  - フォーマット処理（業務意味を持つ整形）
- UI責務は「入力受理」「表示更新」「UseCase呼び出し」だけに限定。

### 1.3 Data Integrity Constraint (Hard Constraint)
- ハッシュ対象は以下を **全件必須** とする（限定語禁止）:
  - `all_input_files`
  - `all_output_files`
  - `all_parameter_files`
  - `audit_log_record`（ログ本体）
- あわせて実行ログに以下を必須記録:
  - コンテナイメージダイジェスト
  - Gitコミットハッシュ（`git rev-parse HEAD`）
- パス記録はプロジェクトルート相対パスのみ（絶対パスは fail-fast）。

## 2. Delivery Strategy
- 大規模一括置換は禁止。後方互換を維持した段階移行を行う。
- 各段階の完了条件:
  - 機能要件適合
  - 設計適合（依存方向/UI責務/Data Integrity全件性）
  - `pytest tests/` 全件Pass
- REJECTルーティングを厳格化:
  - 設計不備: `REJECT_TO_ARCHITECT`
  - 実装不備: `REJECT_TO_IMPLEMENT`

## 3. Work Breakdown Structure

### 3.1 P0: Governance Baseline (最優先)
1. 監査スキーマ固定
- 監査ログに必須項目を固定: 操作種別、時刻、対象一覧、成否、解放容量、実行理由、required imports、environment capability、mismatch結果、ガード発火状態、ハッシュ群、image digest、git hash。

2. アーキテクチャ境界の検査ルール追加
- 静的検査で `UseCase -> Qt` 直接依存をFail化。
- UI層での禁止行為（複雑計算/フォーマット/直接I/O）を検出するルールを追加。

3. Data Integrity実装規約の固定
- ハッシュ収集APIを「全件列挙入力」契約に統一し、`major`/`primary` 等の曖昧語を仕様・コード双方から排除。

### 3.2 P1: Phase 5 (Validation Guardrails)
1. Capability Mapping
- `user_knowledge.json`（推定）と実行実績（実証）を統合する UseCase を実装。
- UIは推定/実証を識別表示するだけに留める。

2. Mismatch Detection + Hard Guard
- required imports（import名基準）と環境capability差分をUseCaseで算出。
- 差分>0なら `Run` を無効化（オーバーライド禁止）。
- 警告表示項目（不足import、不足理由、推奨環境、新規作成導線）をViewModelで構成しUIへ渡す。

3. Forced Creation Flow
- 適合環境なし時に新規環境作成ダイアログへ強制誘導。
- 初期候補は `user_knowledge.json` 優先 + 既定候補補完。
- 作成完了後、再起動なしの即時反映（Dynamic Refresh）を保証。

### 3.3 P1: Phase 6 (Lifecycle Management)
1. Environment Manager専用UI
- 既存画面へ責務混在させず専用ダイアログを新設。
- 一覧、検索/フィルタ、複数選択、削除プレビュー（件数・対象名・推定解放容量）を提供。

2. Bulk Delete Safety
- 削除対象: 定義JSON + Docker image。
- 2段階確認完了まで削除不可。
- 対象ごと独立処理、部分失敗時も継続実行し結果分離表示。

3. Unused Extraction
- 最終利用日時 + 利用回数 + 保護フラグ（Pin/Favorite）で判定。
- 保護フラグ対象は候補から除外。

4. Cleanup Scope
- dangling + unused image を対象。
- build cache / volume は対象外。

5. Rename/Metadata Edit
- 内部ID不変。
- 表示名/説明/タグ/分類/保護フラグ編集可。
- 入力バリデーション適用。

### 3.4 P2: Phase 6.1 (Decoupling Assessment)
1. `artifacts/architecture_decoupling_assessment.md`
- 違反一覧を `file path + 関数/クラス + 違反種別 + 根拠` で列挙。

2. `artifacts/refactoring_proposal.md`
- 各違反の移管先レイヤ、必要Port設計、段階移行手順(P0/P1/P2)、検証方法を定義。

## 4. Verification Gates

### 4.1 Test Gate (Functional)
- 必須: `pytest tests/` 全件Pass。
- 最低限追加テスト:
  - Phase5: T5-1〜T5-4
  - Phase6: T6-1〜T6-6

### 4.2 Architecture Gate (Structural)
- `UseCase -> Qt` 依存0件。
- UI層の禁止行為0件（判断・直接I/O・複雑計算・フォーマット処理）。
- 境界越えのPort未経由呼び出し0件。

### 4.3 Audit Gate (Integrity)
- ハッシュ対象4区分（`all_input_files` / `all_output_files` / `all_parameter_files` / `audit_log_record`）の欠落0件。
- 相対パス強制違反0件。
- image digest / git hash 記録欠落0件。

## 5. Implementation Sequence
1. P0ガバナンス基盤を先行実装（検査ルール・監査スキーマ・ハッシュ契約）。
2. Phase5をUseCase中心に実装し、UIは表示と操作導線のみ実装。
3. Phase6を専用Environment Managerとして実装。
4. Phase6.1成果物を作成し、違反残件を段階的に閉じる。
5. 各ステップで `Functional -> Structural -> Audit` の順にゲート通過を確認。

## 6. Risk Register and Countermeasures
- リスク: UI側に判定ロジックが再流入。
  - 対策: UI lintルール + PRチェックでUI禁止行為をFail化。
- リスク: ハッシュ対象漏れの再発。
  - 対策: 監査ログ生成時に4区分未充足なら即Fail。
- リスク: 依存方向違反の潜在化。
  - 対策: import依存検査をCI必須化し、例外運用を禁止。
- リスク: 部分失敗時の運用混乱。
  - 対策: 成功/失敗対象と理由を分離した結果モデルを標準化。

## 7. Definition of Done
- 要件適合: Phase5/6/6.1の受け入れ基準を満たす。
- 設計適合: 本計画 1章のHard Constraint違反が0。
- 監査適合: `docs/audit_report.md` 相当の監査でREJECT要因が0。
- テスト適合: `pytest tests/` 全件Pass。

## 8. Explicit Prohibitions
- 本計画遂行中、git commit は実施しない。
- 設計不備を実装努力で迂回しない（設計に戻して修正）。
- 監査基準の曖昧語（例: 主要、必要に応じて、可能なら）を受け入れない。
