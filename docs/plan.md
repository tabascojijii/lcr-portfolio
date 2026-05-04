# 実装計画（Architect / Loop Break Plan）

- 作成日: 2026-05-04
- 対象: Phase 5, Phase 6, Phase 6.1, 6.2, 6.3, 6.4
- 根拠: `docs/core_philosophy.md`, `docs/requirements.md`, `docs/reference_standards.md`, `docs/post_mortem.md`

## 1. 計画目的

過去の失敗（2026-05-04 時点の監査差し戻し反復）を、実装テクニックではなく工程設計そのものの是正で終わらせる。  
中核は次の2点。

1. 設計課題を実装へ返さない（Architect先行で境界を固定）
2. 機能ゲートと構造ゲートを分離し、両方合格まで進行禁止

## 2. 再発防止の固定原則（Post Mortem反映）

1. `MainWindow` は Humble Object とし、判断・分岐・永続化・外部I/Oを保持しない。
2. `UI -> UseCase -> Domain` の依存方向を固定し、境界越えは Port のみ。
3. `UI->Domain` 直参照は「禁止」ではなく「経路上不可能」な設計にする。
4. 差し戻し区分を強制運用する。
- 構造違反: `REJECT_TO_ARCHITECT`
- 機能不備: `REJECT_TO_IMPLEMENT`
5. 同一構造違反2回連続で、実装作業を停止し Architect 再設計へ自動移送する。

## 3. 完了KPI（固定）

### 3.1 構造KPI

- `UI->Domain` 直参照: 0件
- Port未経由の境界越え: 0件
- 逆方向依存（内側→外側）: 0件
- 循環依存: 0件
- Qtシグナル命名規則違反（過去分詞形以外）: 0件
- Qtスロット命名規則違反（動詞開始以外）: 0件
- 関数サイクロマティック複雑度（CC）閾値超過（`CC > 10`）: 0件
- 巨大関数閾値超過（`LOC > 80`）: 0件
- `MainWindow._run_container` の業務ロジック: 0件
- `MainWindow._show_create_env_dialog` の候補生成/環境作成制御: 0件

### 3.2 品質KPI

- `pytest tests/` 全件Pass
- Phase 6.2 DTO strict/fail-fast違反: 0件
- Phase 6.3 mypyエラー: 0件
- `type: ignore` 無理由コメント: 0件

### 3.3 監査KPI

- 相対パス違反: 0件
- ハッシュ対象欠落: 0件
- 実行ログへの `image_digest` / `git_commit` 記録欠落: 0件
- Docker/EOL再現性4要件違反: 0件
- Phase 5/6 監査必須項目欠落: 0件

## 3.4 Docker/EOL再現性KPI（reference準拠）

- `FROM` タグ使用: 0件（`@sha256:` digest必須）
- EOL APTミラー未切替: 0件（`old-releases` / `archive.debian.org` 以外をFail）
- `constraints.txt` 未適用ビルド: 0件
- C/C++ビルドの非マルチステージ構成: 0件

## 4. 先行設計成果物（実装着手条件）

以下が揃うまで、実装着手を禁止する。

1. `artifacts/architecture_decoupling_assessment.md`
- 違反一覧（`file + class/function + 違反種別 + 根拠`）
- 実測件数（`UI->Domain`, 逆依存, 循環依存）

2. `artifacts/refactoring_proposal.md`
- `_run_container` / `_show_create_env_dialog` の責務移管先
- Port定義（`abc.ABC` or `typing.Protocol`）
- P0/P1/P2 優先度と段階移行順
- 変更影響テスト（UI変更時/Domain変更時）

3. トレーサビリティ表
- 要件（core/requirements/reference）と実装タスク・テスト・監査項目を1対1対応で記録

## 5. 実行フェーズ

### Phase A: Architecture Lock（最優先）

目的: 監査差し戻し原因を設計で先に除去。

タスク:
1. `MainWindow` 責務をイベント中継/表示更新のみに限定
2. 実行導線を `RunContainerUseCase` へ集約
3. 環境作成導線を `CreateEnvironmentFlowUseCase` へ集約
4. UIからDomain/Infrastructure実装型への直接importを除去
5. Port境界を定義し、UIからの呼び出し先をFacade/UseCaseに固定

完了条件:
1. `_run_container` が「UseCase呼び出し + UI反映」のみ
2. `_show_create_env_dialog` が「ダイアログI/O + UseCase呼び出し」のみ
3. 構造KPIが全項目0件
4. CC/巨大関数の閾値超過が0件

### Phase A.5: Reproducible Build Lock（監査重大指摘の是正）

目的: EOLスタック再現性を計画段階で拘束し、実装後の監査差し戻しを防止。

タスク:
1. `Dockerfile` の `FROM` を digest固定（`@sha256:`）へ統一し、タグ指定を禁止
2. EOL向けAPTソースを archive/old-releases へ強制切替
3. `constraints.txt` をビルド必須入力に固定し、未適用時Failにする
4. OpenCV等のC/C++ビルドをマルチステージへ固定し、runtimeにbuild toolを残さない

完了条件:
1. digest未固定 `FROM` 0件
2. EOL APT未切替 0件
3. `constraints.txt` 未適用 0件
4. 単一ステージでのC/C++ビルド 0件

### Phase B: Phase 5 Guardrails 実装

目的: ミスマッチ実行をHard Guardで防止。

タスク:
1. capability mapping（推定/実証）表示
2. required imports差分検知
3. mismatch時のRun無効化
4. 適合環境なし時の作成導線
5. 作成後Dynamic Refresh
6. 監査ログへ required imports / capability / mismatch / guard状態を記録

完了条件:
1. AC-1〜AC-5 達成
2. T5-1〜T5-4 Pass

### Phase C: Phase 6 Lifecycle 実装

目的: 安全な整理運用を専用UIで実現。

タスク:
1. Environment Manager ダイアログ実装
2. 2段階確認による一括削除
3. 未使用判定（最終利用日時+利用回数+保護フラグ）
4. dangling/unused imageクリーンアップ
5. 表示名/説明/タグ/分類/保護フラグ編集（内部ID不変）
6. 部分失敗継続と結果分離表示
7. 監査ログ完全化（種別/時刻/対象/成否/容量/理由）

完了条件:
1. AC6-1〜AC6-7 達成
2. T6-1〜T6-6 Pass

### Phase D: Type Safety（6.2）+ Static Gate（6.3）

目的: 実行時/静的型の二重ゲート化。

タスク:
1. DTOを A→B→C 順でPydantic v2化
2. strict + fail-fast を強制
3. dict互換アダプタを境界に配置
4. mypyをCIゲート化
5. Any/ignore管理（理由必須、増加監視）

完了条件:
1. AC6.2-1〜AC6.2-5, T6.2-1〜T6.2-5 Pass
2. AC6.3-1〜AC6.3-4, T6.3-1〜T6.3-4 Pass

### Phase E: Contract & Regression Hardening（6.4）

目的: 将来変更での逆流を防止。

タスク:
1. Port contract test
2. DTO/Audit schema contract test
3. Golden regression（Run/Build/Lifecycle/Audit）

完了条件:
1. AC6.4-1〜AC6.4-4 達成
2. T6.4-1〜T6.4-4 Pass

## 6. ゲート運用（進行制御）

監査独立性を担保するため、Builder/Validator分離を全フェーズで強制する。
- 監査入力は「要件仕様 + 生成Diff + テスト結果」に限定する。
- 実装時の思考ログ、口頭補足、意図説明メモを監査判定入力に使用しない。
- Builder/Validator分離チェックが `No` の場合は自動Fail（次フェーズ進行禁止）。

### 6.1 機能ゲート

- `pytest tests/` 全件Pass
- フェーズAC達成

### 6.2 構造ゲート

- 禁止依存0件
- 循環依存0件
- UI責務混在0件
- Port未経由0件
- Qtシグナル命名規則違反0件（過去分詞形）
- Qtスロット命名規則違反0件（動詞開始）
- `CC > 10` 0件
- `LOC > 80` 0件
- `_run_container` / `_show_create_env_dialog` 再発監査0件

### 6.3 進行ルール

1. どちらか1つでもFailしたら次フェーズ進行禁止
2. 構造ゲートFailは実装継続禁止、Architect是正タスクを先行
3. 成果物未更新（assessment/proposal/traceability）はFail扱い
4. Docker/EOL再現性4要件のいずれか1件でもFailなら全実装フェーズ停止
5. ハッシュ完全性（対象・保存・再計算比較）未達は監査Fail

### 6.4 監査データ完全性ゲート（Data Integrity固定）

ハッシュ対象の正規リスト（欠落時Fail）:
1. 入力データ（実行対象ファイル群）
2. 出力データ（成果物ファイル群）
3. 実行パラメータ（設定JSON/YAML/CLI引数相当）
4. 監査ログ本体ファイル

保存先・命名規約:
1. 保存先は `artifacts/audit/hashes/` に固定
2. 命名は `<run_id>_<target_kind>_<relative_path_normalized>.sha256`
3. すべてプロジェクトルート相対パスで記録（絶対パス禁止）

検証手順（再計算比較）:
1. 実行完了後に各対象のSHA-256を再計算
2. 保存済み `.sha256` と一致比較
3. 不一致または未生成が1件でもあればFail-fastで監査Fail

## 7. 監査証跡テンプレート（必須）

各フェーズ完了時に以下を保存。

1. 実測メトリクス
- 禁止依存件数
- 循環依存件数
- UI責務違反件数
- Qtシグナル命名規則違反件数（過去分詞形以外）
- Qtスロット命名規則違反件数（動詞開始以外）

2. テスト証跡
- `pytest tests/` 結果
- mypy結果（Phase D以降）

3. 監査ログ完全性
- 相対パス検証結果
- 入出力/パラメータ/ログ本体ハッシュ
- `image_digest`, `git_commit`
- ハッシュ再計算比較結果（一致/不一致）

4. Docker/EOL再現性証跡
- `FROM @sha256` 検証結果
- EOL APT切替検証結果
- `constraints.txt` 適用検証結果
- マルチステージ検証結果

5. 差し戻し判定記録
- 原因層（設計/実装）
- 判定区分（TO_ARCHITECT / TO_IMPLEMENT）
- 処方的修正指示

6. 監査独立性証跡
- Builder/Validator分離チェック（Yes/No）
- 監査入力一覧（要件仕様 / Diff / テスト結果のみであること）

## 8. 主要リスクと対策

1. リスク: UIへ業務ロジック再混入
- 対策: `MainWindow` 対象レビュー項目を固定し、違反時は構造Fail

2. リスク: 要件達成を急ぐあまりPort bypass発生
- 対策: Port経由率100%をゲート化し、例外禁止

3. リスク: `pytest` Passをもって進行してしまう
- 対策: 構造ゲート未達なら進行停止を工程ルール化

4. リスク: 監査ログ欠落
- 対策: DTO strict + fail-fastで欠落を実行時に停止

5. リスク: EOL環境ビルドの再現不能化
- 対策: digest固定・archive切替・constraints・マルチステージの4要件を実装前ゲート化

6. リスク: 構造健全性の主観判定化
- 対策: CC/LOC閾値を固定し、超過時は自動で `REJECT_TO_ARCHITECT`

## 9. Definition of Done

以下を全て満たしたときのみ完了。

1. 全フェーズのAC/必須テスト合格
2. 構造KPI・品質KPI・監査KPI 全達成
3. 既知再発点（`_run_container`, `_show_create_env_dialog`）の違反0件維持
4. 設計成果物・監査証跡・トレーサビリティが最新化されている
5. Builder/Validator分離チェックが全フェーズでYes
