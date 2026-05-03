# LCR ロードマップ（PM）

## 0. 目的と絶対基準
- 本ロードマップは `docs/plan.md` の実行計画を、`docs/reference_standards.md` の絶対基準に準拠させて運用するための実行文書である。
- 以後の全フェーズで、基準逸脱は例外なく `REJECT` とする。
- 判定・実装・監査の優先順は以下で固定する。
  1. 監査/ガバナンス標準（EMCS、Builder/Validator分離、処方的REJECT）
  2. 再現性標準（Docker/EOLスタック固定化）
  3. データ完全性標準（ALCOA++監査証跡）
  4. UIアーキテクチャ標準（Humble Object/Clean Architecture）

## 1. 非交渉ルール（全フェーズ共通）
- 呼び出しフロー: `UI -> UseCase -> Domain` および `UI -> UseCase -> Port -> Infrastructure` のみ許可。
- 依存方向: 外側 -> 内側のみ許可。`Domain -> Infrastructure/UI/UseCase` と `UseCase -> UI/Qt` は禁止。
- UI責務: UIはイベント受理と表示更新のみ。判断、I/O、永続化、複雑計算、整形ロジックは禁止。
- 抽象化規律: 境界越え通信は `abc.ABC` または `typing.Protocol` を必須とする。
- 監査証跡: `git_commit_hash`、image digest、相対パス、SHA-256（入力/出力/パラメータ/監査ログ）を必須化。
- 再現性: Docker `FROM` digest固定、EOL向けAPTアーカイブ、`constraints.txt`、マルチステージビルドを必須化。
- 危険操作統制: 削除/強制削除はデフォルト禁止。明示解除は承認済みUseCase経由のみ許可し、解除理由、承認者、対象ID、実行ID、UTC時刻、解除スコープを監査ログへ必須記録する。
- Builder/Validator分離運用: Auditor入力は「要件文書」「参照規約」「変更差分+成果物」の3点に限定し、Builderの思考過程/下書き/私的メモ共有を禁止する。証拠なき口頭補足による合否変更を禁止する。

## 2. フェーズ計画

### Phase A: 設計固定（実装前ゲート）
目的:
- 監査スキーマ、責務境界、再現性ポリシーを実装前に固定し、差し戻しループを防止する。

成果物:
- `docs/audit_log_schema.md`
- `docs/ui_usecase_boundary.md`
- `docs/allowed_ui_operations.md`
- `docs/container_reproducibility_policy.md`
- `docs/architecture_decoupling_assessment.md`
- `docs/refactoring_proposal.md`

完了条件:
- 監査必須項目と採取タイミングが文書化され、欠落時fail条件が定義済み。
- UI/UseCase/Infra違反が `file path + class/function + violation + evidence` 形式で列挙済み。
- 改善項目に優先度（P0/P1/P2）と移管先レイヤーが付与済み。
- Docker再現性4要件が非交渉ルールとして明文化済み。
- `docs/audit_report.md` にフェーズ単位の `checked_constraints` と `evidence` 追記ルールが明文化され、以後の進行条件を「証拠付きPASS」に固定済み。

### Phase B: Phase 5（Validation Guardrails）
目的:
- 実行前ミスマッチを機械的に遮断し、監査可能な実行判定にする。

実装対象:
- capability統合（knowledge + 実績）
- required imports差分判定UseCase
- Hard Guard（mismatch > 0 で Run 無効）
- 不足理由表示、推奨環境提示、作成導線
- 適合環境なし時の強制作成フローとDynamic Refresh
- required/capability/mismatch/guard の監査記録

完了条件:
- AC-1〜AC-5 充足。
- T5-1〜T5-4 追加・pass。
- 監査レコードで required/capability/mismatch/guard 欠落0件。

### Phase C: Phase 6（Lifecycle Management）
目的:
- 破壊的操作を安全化し、運用時の管理負債を制御可能にする。

実装対象:
- 専用Environment Manager UI
- 複数選択削除 + 2段階確認
- 未使用判定（最終利用日時、利用回数、保護フラグ）
- dangling/unused image クリーンアップ
- 表示名/説明/タグ/分類/保護フラグ編集（内部ID不変）
- 部分失敗継続 + 結果分離表示
- 操作監査ログ（対象、成否、容量、理由）

完了条件:
- AC6-1〜AC6-7 充足。
- T6-1〜T6-6 追加・pass。
- 削除/編集/クリーンアップ監査レコードの必須項目欠落0件。
- 危険操作（削除/強制削除）のデフォルト禁止が有効であり、明示解除時は解除条件と監査証跡必須項目の欠落0件。

### Phase D: Phase 6.1（アーキテクチャ収束）
目的:
- UI過密責務を解消し、依存違反の再流入を恒久的に防止する。

実装対象:
- `MainWindow` から業務処理をUseCaseへ段階移管
- Port未使用箇所の排除
- 全Portの `abc.ABC` / `typing.Protocol` 化
- 循環依存解消

完了条件:
- 依存方向違反0件。
- UI層の外部I/O直接呼び出し0件。
- 主要UseCaseのUI非依存単体テストpass。
- Architecture分類の未解決finding 0件。

## 3. ゲート設計（リリース必須）

### 3.1 機能ゲート
- `pytest tests/` 全件pass。

### 3.2 アーキテクチャゲート
- UI禁止API呼び出し検出: 0件。
- 依存方向違反検出: 0件。
- UseCase層のQt import検出: 0件。
- Port抽象化違反（具象直参照）: 0件。
- UI内計算/整形ロジック検出: 0件。
- シグナル/スロット命名規約違反: 0件。

### 3.3 監査・完全性ゲート
- 監査ログ必須スキーマ完全性: 欠落0件。
- ハッシュ対象一致: `all_input_files` / `all_output_files` / `all_parameter_files` / `audit_log_record` の不一致0件。
- 相対パス強制: 絶対パス検出0件。

### 3.4 再現性ゲート
- `git_commit_hash` 記録必須。
- container image digest 記録必須。
- Docker `FROM` digestなし: fail。
- EOL標準APTミラー残存: fail。
- `constraints.txt` 未使用pip install: fail。
- 単一ステージでビルドツール同梱実行イメージ: fail。

### 3.5 ガバナンスゲート（EMCS）
- M1 依存違反件数 = 0
- M2 UI層ロジック混入件数 = 0
- M3 禁止API呼び出し件数 = 0
- M4 循環依存件数 = 0
- M5 REJECTテンプレート欠落項目数 = 0
- Builder/Validator分離違反（監査入力3点逸脱、思考過程共有、証拠なき合否変更）: 1件以上でfail。
- `docs/audit_report.md` フェーズ追記義務違反（`checked_constraints` または `evidence` 欠落）: 1件以上でfail。
- いずれか閾値超過時は `REJECT_TO_ARCHITECT` を返却。

## 4. REJECT運用標準
- 監査指摘は `Requirement / Architecture / Implementation` に分類する。
- 実装不備は `REJECT_TO_IMPLEMENT`、設計不備は `REJECT_TO_ARCHITECT` とする。
- REJECTメッセージ必須項目:
  - `失敗箇所(file:line)`
  - `違反制約ID`
  - `観測証拠(ログ/差分)`
  - `修正ヒント`
  - `再検証条件`
  - `ルーティング先`
- 必須項目欠落は監査ジョブfail。

## 5. 実施順序
1. Phase A完了まで実装変更を最小化する。
2. Phase Bで実行ガードと監査証跡の信頼性を先に確立する。
3. Phase Cで削除/クリーンアップ系の安全運用を確立する。
4. Phase DでUI責務分離と依存収束を完了する。

## 6. Definition of Done
- Phase 5/6/6.1 の受入基準と必須テストをすべて満たす。
- RC-1/RC-2/RC-3 の恒久対策がコード・文書・CIゲートへ反映済み。
- 監査で設計不備が検出された場合、`REJECT_TO_ARCHITECT` へ正しくルーティングされる。
- 成果物が「動作」だけでなく「監査可能・再現可能・再発防止可能」を満たす。
