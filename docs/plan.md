# 実装計画（Architect / Structural Defect Eradication Plan）

- 作成日: 2026-05-05
- 対象: Phase 5 / Phase 6 / Phase 6.1〜6.4
- 根拠: `docs/core_philosophy.md`, `docs/requirements.md`, `docs/reference_standards.md`, `docs/post_mortem.md`
- 目的: 2026-05-04 に顕在化した監査差し戻しループの構造原因を、設計・ゲート・運用の3層で恒久的に除去する。

## 1. 失敗の再定義（post_mortem 反映）

過去失敗は「実装不足」ではなく、以下の設計運用不備だったと定義する。

1. 境界違反を禁止ルールに留め、構造的に不可能化できていない。
2. 構造違反の差し戻し先が Implementer 側へ流れ、局所修正ループ化した。
3. `pytest` Pass と構造準拠を同一ゲートとして扱い、進行判定が混線した。

本計画では上記3点を直接つぶす。

## 2. 非交渉原則（Architecture Constitution）

1. UI は Humble Object を厳守し、業務判断・永続化・外部 I/O 制御を持たない。
2. 依存方向は `UI -> UseCase -> Domain -> Infrastructure` のみ。
3. 境界越えは Port/Interface のみ。UI から Domain/Infrastructure 実装型への直接参照は禁止ではなく「経路上不可能」にする。
4. 内部IDは不変。表示名/説明/タグ/保護フラグはメタデータとして扱う。
5. 監査不変条件（相対パス、ハッシュ完全化、fail-fast）を機能要件と同格で扱う。

## 3. 先行成果物ゲート（実装開始前の必須条件）

以下が揃うまでコード実装を開始しない。

1. `artifacts/architecture_decoupling_assessment.md`
- 違反一覧（`file + class/function + 違反種別 + 根拠`）
- 実測件数（`UI->Domain直参照`, `逆方向依存`, `循環依存`, `Port未経由`）

2. `artifacts/refactoring_proposal.md`
- `MainWindow._run_container` と `_show_create_env_dialog` の責務移管先
- Port 定義（`abc.ABC` / `typing.Protocol`）
- P0/P1/P2 の段階移行順
- 変更影響テスト（UI変更時/Domain変更時）の実施手順と合否条件

3. `artifacts/traceability_matrix.md`
- 要件ID（Phase5/6/6.1/6.2/6.3/6.4）→ 実装タスク → テストID → 監査証跡 の1対1対応

未充足は即 `REJECT_TO_ARCHITECT`。

## 4. 差し戻し先の自動判定ルール

監査は原因層を必ず判定し、差し戻し先を固定する。

1. `REJECT_TO_ARCHITECT`
- 依存方向違反
- UI責務混在
- Port未経由
- 循環依存
- ゲート設計欠陥

2. `REJECT_TO_IMPLEMENT`
- 仕様未達
- テスト不備
- バグ修正不足（構造違反を伴わない）

3. 強制停止条件
- 同一構造違反が2連続で再発した場合、実装作業を停止し Architect 再設計へ自動移送。

## 5. 実施フェーズ計画

### Phase 0: Structural Freeze（即時）

目的: ループ起点の境界違反を先に封じる。

タスク:
1. `MainWindow` の責務を「入力受理・表示更新・UseCase呼び出し」に限定する設計へ固定。
2. `_run_container` の業務判断・実行制御を UseCase 側へ移管する仕様を確定。
3. `_show_create_env_dialog` の候補生成・作成制御を UseCase 側へ移管する仕様を確定。
4. UI 直参照禁止対象（Domain/Infrastructure 実装）を明文化。

完了条件:
1. 2関数の責務分離設計が成果物で承認済み。
2. `UI->Domain直参照 = 0` を達成可能な呼び出し経路図が確定。

### Phase 1: Phase 5 Guardrails 実装

目的: ミスマッチ環境実行を Hard Guard で防止。

タスク:
1. capability mapping（推定/実証）表示
2. required imports 差分算出
3. mismatch 時 Run 無効化
4. 適合環境なし時の作成導線
5. 作成後 Dynamic Refresh
6. 監査ログ（required imports/capability/mismatch/guard）記録

完了条件:
1. AC-1〜AC-5 達成
2. T5-1〜T5-4 Pass

### Phase 2: Phase 6 Lifecycle 実装

目的: 安全な環境整理を専用UIへ隔離。

タスク:
1. Environment Manager ダイアログ
2. 2段階確認付き一括削除
3. 未使用判定（最終利用日時+利用回数+保護フラグ）
4. dangling/unused image クリーンアップ
5. メタデータ編集（内部ID不変）
6. 部分失敗継続と結果分離表示
7. 監査ログ完全化

完了条件:
1. AC6-1〜AC6-7 達成
2. T6-1〜T6-6 Pass

### Phase 3: Type Safety（6.2）

目的: 境界DTOで strict/fail-fast を固定。

タスク:
1. A→B→C順で Pydantic v2 DTO 導入
2. strict validation 強制
3. fail-fast 強制
4. dict互換アダプタで段階移行

完了条件:
1. AC6.2-1〜AC6.2-5 達成
2. T6.2-1〜T6.2-5 Pass

### Phase 4: Static Type Gate（6.3）

目的: 実行前に型不整合をCIで遮断。

タスク:
1. `mypy` 設定導入（必要なら `pyright` 補助）
2. Port/UseCase の型注釈完全化
3. `Any` / `type: ignore` 管理

完了条件:
1. AC6.3-1〜AC6.3-4 達成
2. T6.3-1〜T6.3-4 Pass

### Phase 5: Contract & Regression Hardening（6.4）

目的: 将来変更での逆流防止。

タスク:
1. Port contract test
2. DTO/Audit schema contract test
3. Golden regression（Run/Build/Lifecycle/Audit）

完了条件:
1. AC6.4-1〜AC6.4-4 達成
2. T6.4-1〜T6.4-4 Pass

## 6. ダブルゲート運用（混線防止）

### 6.1 機能ゲート

1. `pytest tests/` 全件Pass
2. 当該フェーズAC全達成

### 6.2 構造ゲート

1. `UI->Domain直参照 = 0`
2. Port未経由 = 0
3. 逆方向依存 = 0
4. 循環依存 = 0
5. UI層業務ロジック = 0
6. 監査必須構造成果物の欠落 = 0

### 6.3 進行判定

1. どちらか1つでもFailなら次フェーズ進行禁止。
2. 構造ゲートFail時は実装修正を停止し、Architect 是正を先行。
3. 機能ゲートのみPassは「未完了」と明示する。

## 7. 監査・再現性固定要件（reference standards 同期）

1. 相対パス強制（絶対パスは fail-fast）。
2. ハッシュ対象完全化（入力/出力/パラメータ/ログ本体）。
3. 実行ログに `image_digest` と `git_commit` を必須記録。
4. EOLコンテナ再現性4要件を満たす。
- `FROM` digest固定
- EOLミラー切替
- `constraints.txt` 適用
- マルチステージビルド

## 8. 定量KPI（完了判定）

1. 構造KPI
- 禁止依存系（直参照/逆依存/循環/Port未経由）: すべて 0件
- `MainWindow._run_container` / `_show_create_env_dialog` の業務ロジック残存: 0件

2. 品質KPI
- `pytest tests/` Pass
- mypy エラー 0件
- DTO strict/fail-fast 違反 0件

3. 監査KPI
- 相対パス違反 0件
- ハッシュ欠落 0件
- 監査必須項目欠落 0件

## 9. Definition of Done

以下を全て満たした場合のみ完了とする。

1. Phase 5/6/6.1/6.2/6.3/6.4 の AC と必須テストを満たす。
2. 機能ゲート・構造ゲートの両方がPass。
3. `post_mortem` で特定された再発点（境界違反、差し戻し先誤り、ゲート混線）が運用ルールとして明文化され、証跡で検証可能。
4. 監査証跡（assessment/proposal/traceability/test evidence）が最新化されている。
