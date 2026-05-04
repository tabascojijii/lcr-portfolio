# LCR ロードマップ（PM）

- 作成日: 2026-05-04
- 絶対基準: `docs/reference_standards.md`
- 参照計画: `docs/plan.md`
- 目的: 監査でREJECTされない実装順序を固定し、構造逸脱と再発を防ぎながら Phase 5/6/6.2/6.3 を完了する。

## 0. ロードマップ原則（逸脱禁止）

1. **基準優先**: 判断が衝突した場合は常に `docs/reference_standards.md` を優先する。
2. **構造先行**: 機能追加より先に UI分離・依存方向・Port境界を固定する。
3. **監査可能性優先**: 実装完了条件は「動作」だけでなく「監査証跡の完全性」を含む。
4. **Builder/Validator分離**: 実装と監査は役割分離し、Diffベースで判定する。

## 1. マイルストーン

### M1: アーキテクチャ固定（Phase A-B）

- 期間目安: Week 1-2
- 成果物:
  - 依存方向図、責務表、Port一覧（`artifacts/refactoring_proposal.md`）
  - 違反一覧と是正方針（`artifacts/architecture_decoupling_assessment.md`）
  - 変更影響テスト仕様（UI変更時/Domain変更時、監査可能形式）
  - 標準条項トレーサビリティマトリクス（KPI ↔ `docs/reference_standards.md`、監査可能形式）
  - 標準条項トレーサビリティマトリクス保存先: `artifacts/standards_traceability_matrix.md`
  - `MainWindow._run_container` / `_show_create_env_dialog` の責務分離完了
  - `_run_container`（必要に応じて `_show_create_env_dialog` を含む）移管前後の責務差分表
  - 既知再発2メソッド（`_run_container`, `_show_create_env_dialog`）の専用監査チェックリスト証跡
- 完了条件:
  - UI->Domain 直参照 0
  - Port未経由 0
  - 循環依存 0
  - MainWindow業務ロジック 0
  - `MainWindow._run_container` は UseCase呼び出し + UI表示更新以外を保持しない
  - `MainWindow._run_container` から Domain/Infrastructure実装型への直接import 0
  - `MainWindow._show_create_env_dialog` は Port/UseCase非経由で環境生成ロジックへ到達しない
  - 「不足import→候補生成→作成→再評価」の制御フローは1つのUseCase境界で完結する
  - Dynamic Refresh（再起動不要反映）が実装されている
  - 変更影響テスト仕様（UI変更時/Domain変更時）が監査可能な形式で保存済み
  - 標準条項トレーサビリティマトリクス作成完了（`artifacts/standards_traceability_matrix.md`、監査可能）
  - 標準条項トレーサビリティマトリクス更新タイミングは M1完了時および各Phase遷移判定前
  - Phase遷移ゲートで KPI/標準条項対応を照合し、欠落があれば `REJECT_TO_PM`
  - 移管前後の責務差分表が監査証跡として保存済み
  - 既知再発2メソッドの専用監査チェックリスト保存完了
  - Architect承認済み（未承認時は Phase C 以降へ遷移不可）

### M2: Validation Guardrails 完了（Phase C）

- 期間目安: Week 3
- 成果物:
  - capability mapping（推定/実証の明示）
  - mismatch時 Hard Guard（Run無効化）
  - 不適合時の強制作成導線
  - ALCOA++ 監査ログ必須項目記録
- 完了条件:
  - AC-1〜AC-5, T5-1〜T5-4 を満たす
  - `image_digest`, `git_commit`, 各種ハッシュ欠落 0

### M3: Lifecycle Management 完了（Phase D）

- 期間目安: Week 4-5
- 成果物:
  - Environment Manager
  - 一括削除2段階確認
  - 未使用判定・クリーンアップ・メタデータ編集
  - 部分失敗継続と結果分離表示
  - Docker再現性4要件の実装
- 完了条件:
  - AC6-1〜AC6-7, T6-1〜T6-6 を満たす
  - Docker基準（Digest固定、Archive APT、constraints、Multi-stage）全合格

### M4: 型安全ゲート完了（Phase E）

- 期間目安: Week 6
- 成果物:
  - DTOのPydantic v2 strict化（段階移行）
  - dict互換アダプタ
  - mypyゲート
  - `type: ignore` 理由必須運用
- 完了条件:
  - AC6.2-1〜AC6.2-5, T6.2-1〜T6.2-5
  - AC6.3-1〜AC6.3-4, T6.3-1〜T6.3-4
  - mypy error 0

## 2. 実行順序（固定）

1. Phase A: 設計固定
2. Phase B: 境界リファクタ
3. Phase C: Validation Guardrails
4. Phase D: Lifecycle Management
5. Phase E: Type Safety + Static Gate

## 3. ガバナンス・ゲート運用

### 3.1 ダブルゲート（両方必須）

- 機能ゲート:
  - `pytest tests/` 全件Pass
  - 各PhaseのAC/T項目達成
- 構造ゲート:
  - 禁止依存/循環依存 0
  - Humble Object準拠（UI業務ロジック 0）
  - Port経由率 100%（測定: importグラフ + 呼び出し経路監査）
  - 内側層（UseCase/Domain）から外側層（UI/Infrastructure）への直接依存 0（測定: importグラフ）
  - Port定義が `abc.ABC` または `typing.Protocol`
  - シグナル/スロット命名規約違反 0
  - 既知再発ポイント監査（`_run_container`, `_show_create_env_dialog`）違反 0（測定: 専用責務チェックリスト）

### 3.2 差し戻し規約

- 構造違反: `REJECT_TO_ARCHITECT`
- 機能違反: `REJECT_TO_IMPLEMENT`
- 同一構造違反の連続発生: Architect是正完了まで後続実装停止
- フェーズ遷移停止条件: Architect承認がない場合、Phase C/D/E への遷移を禁止

### 3.3 監査判定記録（EMCS必須）

- Validatorは全判定をEMCS観点で記録する。
- 必須記録項目: 構造違反、複雑度、依存違反、影響度
- 判定ログはDiff根拠と対応づけ、処方的差し戻し指示とセットで保存する。

## 4. 監査証跡要件（ALCOA++）

全マイルストーンで以下を必須記録とする。

- 環境・コード: `image_digest`, `git_commit`
- 改ざん検知: `input_hashes`, `output_hashes`, `param_hash`, `log_hash`
- 検証性: `relative_path_check`
- 判定根拠: required imports, capability, mismatch, guard発火状態

欠落時は fail-fast とし、完了判定を認めない。

## 5. リスク管理（重点）

1. UIへのロジック逆流
- 対策: MainWindow責務チェックを固定監査項目化

2. Docker再現性ドリフト
- 対策: 4要件をCI監査項目に固定

3. 監査ログ不備
- 対策: 監査DTO必須化 + 欠落時fail-fast

4. 型移行時の互換破壊
- 対策: DTO段階導入 + 互換アダプタ併用

## 6. 完了定義（DoD）

以下をすべて満たした時点で、ロードマップ完了とする。

1. 全PhaseのAC/T項目が達成済み
2. 構造KPI・品質KPI・監査KPIが全達成
3. 既知再発箇所（`_run_container`, `_show_create_env_dialog`）で違反0
4. 監査証跡が再実行可能な粒度で保存済み
5. 監査判定が連続してREJECTなし
