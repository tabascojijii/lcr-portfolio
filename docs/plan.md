# LCR 実装計画（Architect）

## 0. 計画の目的
- `docs/core_philosophy.md`・`docs/requirements.md`・`docs/reference_standards.md`・`docs/post_mortem.md` を統合し、Phase 5/6/6.1 を監査可能かつ再発防止可能な順序で実装する。
- 過去の失敗ループ（実装差し戻しの反復）を断ち切るため、実装着手前に「監査スキーマ」「責務境界」「ゲート」を固定する。

## 1. 最上位方針（非交渉）
- 呼び出しフローと依存規則を分離して定義する。
  - 呼び出しフロー（実行時）: `UI -> UseCase -> Domain` および `UI -> UseCase -> Port -> Infrastructure`
  - コンパイル時依存（参照可能方向）: **外側 -> 内側のみ**（Infrastructure は UseCase/Domain の Port を実装するのみ）
  - 非許可依存: `Domain -> Infrastructure`、`Domain -> UseCase/UI`、`UseCase -> UI`、`Domain -> Qt`
  - 対応表（固定）:
    - Domain: 純粋ロジックのみ。外部I/O呼び出し禁止。
    - UseCase: Domain をオーケストレーションし、外部I/Oは Port 経由で委譲。
    - Infrastructure: Port 実装を提供。UseCase/Domain の具象実装へ逆参照しない。
- UI（`MainWindow`/Dialog）は Humble Object とし、判断・分岐・永続化・外部I/Oを保持しない。
- 監査証跡は ALCOA++ 準拠で、相対パス強制・ハッシュ対象完全化・再現性を満たす。
- 危険操作（削除/強制削除）はデフォルト禁止、明示解除時のみ許可。
- `pytest tests/` pass に加え、アーキテクチャゲート pass をリリース必須条件にする。

## 2. Post Mortem 起点の構造対策

### 2.1 RC-1 対策: 監査ログ最小スキーマの先行固定
実装前に以下を Architecture 成果物として確定し、変更は ADR（Architecture Decision Record）必須とする。
- 必須フィールド
  - 実行ID、UTC時刻、操作種別、実行理由、対象環境ID一覧
  - `git_commit_hash`（`git rev-parse HEAD`）
  - container image digest（`sha256:...`）
  - required imports / capability / mismatch 判定 / ガード発火状態
  - 入力・出力・主要パラメータ・実行ログ本体の SHA-256
  - 成功/失敗、失敗理由、解放容量（該当時）
- ハッシュ採取タイミング
  - 実行前: 入力・パラメータ・required imports
  - 実行後: 出力・実行ログ本体・結果サマリ
- 保存形式
  - JSON Lines（1操作1レコード、追記専用）
- 検証方式
  - 監査レコード完全性テスト（必須キー欠落時 fail）

### 2.2 RC-2 対策: UI/UseCase/Infra 境界の先行固定
- UI から直接呼び出してよいのは UseCase 入出力 DTO のみ。
- UI 直下禁止事項
  - Docker 実行、ファイル削除/保存、監査ログ書き込み、未使用判定ロジック、mismatch 判定ロジック
- Port 定義を先に作成
  - `CapabilityRepositoryPort`
  - `ExecutionAuditPort`
  - `EnvironmentLifecyclePort`
  - `ContainerImagePort`
  - すべて `abc.ABC` または `typing.Protocol` で定義し、UI/UseCase から具象実装を直接参照しない。
- `MainWindow`/Environment Manager はイベント受理と表示更新のみを担当。
- `docs/allowed_ui_operations.md` に signal/slot 命名規約（signal: 過去分詞、slot: 動詞）を明記する。

### 2.3 RC-3 対策: REJECT ルーティングの明確化
- 監査指摘を `Requirement / Architecture / Implementation` の3レイヤーで分類。
- 判定系
  - 実装不備: `REJECT_TO_IMPLEMENT`
  - 設計不備: `REJECT_TO_ARCHITECT`
- CI 監査レポートに「違反原因レイヤー」を必須出力項目として追加。
- REJECTメッセージは処方的テンプレートを必須化する。
  - 必須項目: `失敗箇所(file:line)`、`違反制約ID`、`観測証拠(ログ/差分)`、`修正ヒント`、`再検証条件`、`ルーティング先`
  - いずれか欠落時は監査ジョブを fail とする。

### 2.4 監査ガバナンス対策: Builder/Validator 分離
- Validator（Auditor）入力を以下3点に限定する。
  - 要件文書（`docs/requirements.md` ほか）
  - 参照規約（`docs/reference_standards.md`）
  - 変更差分 + 成果物（テスト結果、生成ドキュメント、CIログ）
- 禁止事項:
  - Builder（Implementer）の思考過程・下書き・私的メモの共有
  - 口頭補足だけでの合否変更（証拠なき例外運用）
- 監査証跡テンプレートを固定する。
  - `input_artifacts` / `checked_constraints` / `findings` / `severity` / `routing` / `recheck_conditions`

### 2.5 Audit Report 反映: 「重大指摘なし」を維持する予防統制
- `docs/audit_report.md` の検証結果（ガバナンス/再現性/データ完全性/UI境界の4系統）を、各フェーズ完了条件にトレースして維持する。
- 監査結果が PASS でも「未対策扱い」を禁止し、以下を継続義務とする。
  - EMCS（M1-M5）を CI で定量出力し、閾値逸脱時は即 fail
  - REJECT 処方テンプレートの必須項目欠落を schema 検証で fail
  - Docker 再現性4要件（digest固定/アーカイブAPT/constraints/マルチステージ）を静的検査で fail-fast
  - ALCOA++ 監査証跡（相対パス・ハッシュ完全化・`git_commit_hash`・image digest）の欠落を fail
- 監査レポート運用ルール:
  - 各フェーズ完了時に `docs/audit_report.md` を更新し、`checked_constraints` と `evidence` をフェーズ単位で追記する。
  - 判定が PASS の場合でも、次フェーズへは「証拠付き PASS」のみ進行可とする。

## 3. 実装フェーズ計画

### Phase A: 設計固定（実装前ゲート）
成果物:
- `docs/audit_log_schema.md`
- `docs/ui_usecase_boundary.md`
- `docs/allowed_ui_operations.md`
- `docs/container_reproducibility_policy.md`
- `docs/architecture_decoupling_assessment.md`（Requirements 6.1）
- `docs/refactoring_proposal.md`（Requirements 6.1）

完了条件:
- 監査必須スキーマが固定され、必須キー一覧と採取タイミングが明文化済み。
- `file path + class/function + violation + evidence` 形式で違反一覧化済み。
- 改善項目に P0/P1/P2 優先度と移管先レイヤーが定義済み。
- EOLコンテナ再現性ポリシーとして以下4点が非交渉ルール化済み。
  - Dockerfile `FROM` の SHA256 ダイジェスト固定
  - EOL向けAPTアーカイブリポジトリへのリダイレクト
  - `constraints.txt` による pip 依存解決範囲固定
  - OpenCV等を想定したマルチステージビルド強制
- 監査エビデンス出力（`docs/audit_report.md`）に、4系統基準ごとの `checked_constraints` と証拠リンクが追記済み。

### Phase B: Phase 5（Validation Guardrails）実装
実装対象:
- 環境 capability 統合（knowledge + 実績）
- required imports 差分判定 UseCase
- Hard Guard（mismatch > 0 で Run 無効）
- 不足理由表示（未対応/未検証）、推奨環境提示、作成導線
- 適合環境なし時の強制作成フロー + Dynamic Refresh
- 監査ログへの required/capability/mismatch/guard 記録

完了条件:
- AC-1〜AC-5 全充足
- T5-1〜T5-4 自動テスト追加・pass
- required/capability/mismatch/guard の監査レコードがスキーマ検証を通過（欠落0件）

### Phase C: Phase 6（Lifecycle Management）実装
実装対象:
- 専用 Environment Manager UI（既存画面へ責務混在させない）
- 複数選択削除 + 2段階確認
- 未使用判定（最終利用日時 + 利用回数 + 保護フラグ）
- dangling/unused image クリーンアップ
- 表示名/説明/タグ/分類/保護フラグ編集（内部ID不変）
- 部分失敗継続実行 + 結果分離表示
- 監査ログ（対象、成否、容量、理由）

完了条件:
- AC6-1〜AC6-7 全充足
- T6-1〜T6-6 自動テスト追加・pass
- 削除/編集/クリーンアップ操作の監査レコードがスキーマ検証を通過（欠落0件）

### Phase D: アーキテクチャ収束と負債返済
実装対象:
- `MainWindow` から業務処理を UseCase 群へ段階移管
- Port 未使用箇所の排除（境界バイパス禁止）
- すべての Port を `abc.ABC` または `typing.Protocol` で定義
- 循環依存の解消

完了条件:
- 依存方向違反 0 件
- UI 層の外部I/O直接呼び出し 0 件
- 主要 UseCase の単体テストで UI 非依存実行可能
- `docs/audit_report.md` で Architecture 分類の未解決 finding が 0 件

## 4. 実施順序（再発防止重視）
1. Phase A（設計固定）を完了するまで実装コード変更を最小化する。
2. Phase B を先行し、実行ガードと監査証跡の信頼性を確立する。
3. Phase C で破壊的操作を安全化し、運用負債を制御可能にする。
4. Phase D で UI 過密責務を恒久是正し、同型障害の再流入を防止する。

## 5. テスト・監査ゲート
- 必須機能ゲート: `pytest tests/` 全件 pass。
- 必須アーキテクチャゲート:
  - UI 層の禁止 API 呼び出し検出テスト
  - 依存方向違反検出テスト
  - Port の `abc.ABC` / `typing.Protocol` 準拠検証（具象直参照を fail）
  - 監査ログ必須スキーマ完全性テスト
  - UI シグナル/スロット命名規約検査（signal: 過去分詞、slot: 動詞）
- 必須ガバナンスゲート（EMCS定量評価）:
  - `M1: 依存違反件数` = 0 件で pass（証拠: 静的依存解析レポート）
  - `M2: UI層ロジック混入件数` = 0 件で pass（証拠: 禁止責務ルール検査）
  - `M3: 禁止API呼び出し件数` = 0 件で pass（証拠: ルールベースgrep/AST検査）
  - `M4: 循環依存件数` = 0 件で pass（証拠: 循環検出レポート）
  - `M5: REJECTテンプレート欠落項目数` = 0 件で pass（証拠: 監査レポートスキーマ検証）
  - Fail条件: `M1-M5` のいずれかが閾値超過なら `REJECT_TO_ARCHITECT` を返す。
- 必須再現性ゲート:
  - ログに `git_commit_hash` と image digest が存在
  - 相対パス以外を検出した場合 fail-fast
  - Dockerfile `FROM` がタグのみ（digestなし）の場合 fail
  - APTソースがEOL標準ミラーのままの場合 fail
  - `constraints.txt` 未使用の `pip install` を検出した場合 fail
  - 単一ステージでビルドツール同梱の実行イメージを検出した場合 fail

## 6. リスクと先回り策
- リスク: 既存 UI に残る隠れた業務ロジックが移管漏れする。
  - 対策: `MainWindow` のメソッド責務棚卸しを最初に実施し、移管チェックリスト化。
- リスク: 監査項目追加で実装速度が低下する。
  - 対策: 監査ログ生成を共通サービス化し、UseCase から統一利用。
- リスク: 部分失敗継続で状態不整合が発生する。
  - 対策: 対象単位のトランザクション境界と失敗時リカバリ手順を明示。

## 7. 完了定義（Definition of Done）
- Phase 5/6/6.1 の受け入れ基準と必須テストをすべて満たす。
- Post Mortem の RC-1/RC-2/RC-3 に対する恒久対策がコード・ドキュメント・CIゲートに反映済み。
- 監査で設計不備が検出された場合に `REJECT_TO_ARCHITECT` へ正しくルーティングされる。
- 実装結果が「動作する」だけでなく「監査可能・再現可能・再発防止可能」である。
