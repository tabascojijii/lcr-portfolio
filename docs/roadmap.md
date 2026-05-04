# Roadmap（Reference Standards Absolute Baseline）

- 作成日: 2026-05-05
- 対象期間: 2026-05-05 〜 2026-05-31
- 上位基準: `docs/reference_standards.md`（絶対基準）
- 参照計画: `docs/plan.md`
- 目的: Phase 5/6/6.1/6.2/6.3/6.4 を、監査・再現性・アーキテクチャ規約に100%整合させて完了させる。

## 0. 運用原則（全フェーズ共通）

1. 判定基準は常に `docs/reference_standards.md` を最優先する。
2. 機能完了（pytest Pass）と構造完了（依存/責務準拠）を分離判定する。
3. 構造違反は `REJECT_TO_ARCHITECT`、実装不足は `REJECT_TO_IMPLEMENT` とする。
4. Builder/Validator 分離を強制し、要件文書・差分(Diff)・テスト結果・監査証跡のみで監査する。
5. すべての差し戻しは以下5要素を必須とする。
- `failure_location`
- `violated_standard`
- `evidence`
- `required_fix`
- `retest_condition`

## 1. マイルストーン

### M0: Structural Freeze and Governance Fix（2026-05-05 〜 2026-05-08）

目的: 失敗ループの構造原因を先に除去する。

成果物:
1. `artifacts/architecture_decoupling_assessment.md`
2. `artifacts/refactoring_proposal.md`
3. `artifacts/traceability_matrix.md`

完了条件:
1. `UI->Domain 直参照 = 0` にできる設計経路が確定。
2. `MainWindow._run_container` / `_show_create_env_dialog` の責務移管先が確定。
3. REJECT 判定テンプレート運用を監査フローへ組み込み済み。
4. `artifacts/architecture_decoupling_assessment.md` / `artifacts/refactoring_proposal.md` / `artifacts/traceability_matrix.md` の3成果物が揃うまで M1 以降の実装着手を禁止する。
5. 上記3成果物のいずれか未充足時は即 `REJECT_TO_ARCHITECT` とする。

### M1: Phase 5 Guardrails（2026-05-09 〜 2026-05-14）

目的: ミスマッチ環境実行を防止する。

実装範囲:
1. capability mapping 表示
2. required imports 差分検出
3. mismatch 時の Run 無効化
4. 適合環境なし時の作成導線
5. 作成後 Dynamic Refresh
6. 監査ログ記録（required imports / capability / mismatch / guard）

ゲート:
1. AC-1〜AC-5 達成
2. T5-1〜T5-4 Pass

### M2: Phase 6 Lifecycle（2026-05-15 〜 2026-05-20）

目的: 安全な環境整理を専用UIに隔離する。

実装範囲:
1. Environment Manager ダイアログ
2. 2段階確認付き一括削除
3. 未使用判定（最終利用日時・利用回数・保護フラグ）
4. dangling/unused image cleanup
5. メタデータ編集（内部ID不変）
6. 部分失敗継続と結果分離表示
7. 監査ログ完全化

ゲート:
1. AC6-1〜AC6-7 達成
2. T6-1〜T6-6 Pass

### M3: Phase 6.1 Decoupling Completion（2026-05-21 〜 2026-05-22）

目的: Phase 5/6 の機能をクリーンアーキテクチャ境界へ収束させ、以降の型・契約強化の前提を固定する。

実装範囲:
1. `MainWindow._run_container` の業務判断・実行制御を UseCase 側へ完全移管
2. `_show_create_env_dialog` の候補生成・作成制御を UseCase 側へ完全移管
3. UI から Domain/Infrastructure 実装型への直接参照を除去し Port/Interface 経由へ統一
4. 変更影響テスト（UI変更時/Domain変更時）を実施し境界退行を検知可能化

ゲート:
1. AC6.1-1〜AC6.1-4 達成
2. T6.1-1〜T6.1-4 Pass

依存関係:
1. 前提: M2 完了
2. 後続: M4（Phase 6.2）開始条件

### M4: Phase 6.2 Type Safety（2026-05-23 〜 2026-05-25）

目的: DTO 境界で strict / fail-fast を固定する。

実装範囲:
1. Pydantic v2 DTO を A→B→C 順で導入
2. strict validation 強制
3. fail-fast 強制
4. dict 互換アダプタで段階移行

ゲート:
1. AC6.2-1〜AC6.2-5 達成
2. T6.2-1〜T6.2-5 Pass

### M5: Phase 6.3 Static Type Gate（2026-05-26 〜 2026-05-28）

目的: 実行前に型不整合をCIで遮断する。

実装範囲:
1. `mypy` 設定導入（必要時 `pyright` 補助）
2. Port / UseCase の型注釈完全化
3. `Any` / `type: ignore` 管理

ゲート:
1. AC6.3-1〜AC6.3-4 達成
2. T6.3-1〜T6.3-4 Pass
3. mypy エラー 0

### M6: Phase 6.4 Contract and Regression Hardening（2026-05-29 〜 2026-05-31）

目的: 将来変更での逆流を防止する。

実装範囲:
1. Port contract test
2. DTO / Audit schema contract test
3. Golden regression（Run / Build / Lifecycle / Audit）

ゲート:
1. AC6.4-1〜AC6.4-4 達成
2. T6.4-1〜T6.4-4 Pass

## 2. Reference Standards トレーサビリティ

### 2.1 監査・ガバナンス標準（第1章）

必須適用:
1. EMCSベースの客観評価
2. Builder/Validator 分離
3. 処方的 REJECT

KPI:
1. 判定根拠なし REJECT = 0
2. 差し戻しテンプレート欠落 = 0

### 2.2 EOLコンテナ再現性標準（第2章）

必須適用:
1. `FROM` digest 固定
2. EOLアーカイブミラー切替
3. `constraints.txt` 適用
4. マルチステージビルド

KPI:
1. 再現性要件未達 = 0

### 2.3 データ完全性・監査証跡（第3章）

必須適用:
1. `image_digest` / `git_commit` 実行ログ記録
2. 相対パス強制（絶対パス fail-fast）
3. 入出力/パラメータ/ログ本体のハッシュ記録

KPI:
1. 相対パス違反 = 0
2. ハッシュ欠落 = 0
3. 実行証跡欠落 = 0

### 2.4 PyQt/PySide アーキテクチャ標準（第4章）

必須適用:
1. Humble Object 厳守
2. 依存方向 `UI -> UseCase -> Domain -> Infrastructure`
3. Port/Interface 経由の通信
4. シグナル/スロット命名規約準拠
5. シグナル/スロット命名規約を lint もしくは静的チェックに組み込み、CIで自動検出する

KPI:
1. UI業務ロジック残存 = 0
2. Port未経由 = 0
3. 命名規約違反 = 0

## 3. フェーズ横断ゲート

### 3.1 機能ゲート

1. `pytest tests/` 全件Pass
2. 当該Phaseの AC 全達成

### 3.2 構造ゲート

1. `UI->Domain 直参照 = 0`
2. 逆方向依存 = 0
3. 循環依存 = 0
4. Port未経由 = 0
5. UI層業務ロジック = 0
6. 監査必須成果物欠落 = 0
7. M0 の3成果物が未充足の場合は `REJECT_TO_ARCHITECT` とし、M1 以降着手禁止

### 3.3 進行ルール

1. いずれか1つでもFailなら次フェーズへ進まない。
2. 構造ゲートFail時は実装停止し、Architect再設計を先行する。
3. 機能ゲートのみPassは未完了扱いとする。
4. M0 成果物ゲート未充足時は即 `REJECT_TO_ARCHITECT` とし、M1 以降へ進行しない。

## 4. リスク管理

1. リスク: 局所修正の再発
- 対応: 同一構造違反の2連続発生で強制停止し、Architectへ自動移送。

2. リスク: 監査の主観化
- 対応: `violated_standard` と `evidence` の記載がない判定を無効化。

3. リスク: 再現性欠落
- 対応: image digest / git commit / hash / 相対パスを CI チェック対象へ固定。

## 5. Definition of Done

1. Phase 5/6/6.1/6.2/6.3/6.4 の AC・テストを全て達成。
2. 機能ゲート・構造ゲートの両方を連続でPass。
3. `docs/reference_standards.md` 第1〜4章の必須項目に未充足がない。
4. `artifacts` 証跡（assessment/proposal/traceability/test evidence）が最新化されている。
