# LCR 実装計画（Architect / Structural Recovery Plan v5）

## 0. 読み込み結果
- 読み込み完了:
  - `docs/core_philosophy.md`
  - `docs/requirements.md`
  - `docs/reference_standards.md`
  - `docs/post_mortem.md`
  - `docs/audit_report.md`
- 本計画は上記5文書を拘束条件として策定する。

## 1. 目的と完了定義
- 目的: Phase 5（Validation Guardrails）を実装しつつ、`post_mortem.md` の構造欠陥（RC-1〜RC-3）と `audit_report.md` の重大指摘を同時に解消する。
- 完了定義:
  1. AC-1〜AC-5 達成。
  2. `pytest tests/` 全件Pass。
  3. 監査スキーマ必須項目充足率100%。
  4. UI/UseCase/Domain/Infra の依存方向違反0件。
  5. Docker再現性4要件の静的検査・実行検証・証跡記録が全てPass。
  6. EMCS監査票に基づく判定再現性（監査者差分0）を確認。

## 2. 設計原則（Fail条件付き拘束）
- `reference_standards.md` は推奨ではなく「違反時Fail」の絶対基準として適用する。
- Humble Object を徹底し、UIは入力受理・表示更新・イベント中継に限定する。
- 判定ロジック・監査ロジック・永続化ロジックを UseCase/Domain/Infra に分離する。
- 監査証跡は ALCOA++ 準拠で、ハッシュと再現性情報を必須記録する。
- 危険操作はデフォルト禁止とし、明示解除時のみ許可する。
- Qt命名規約を絶対拘束とする:
  - シグナル名は過去分詞形（例: `dataChanged`）に限定する。
  - スロット名は動詞開始（例: `update_display`）に限定する。

## 3. Post Mortem 対応（RC別）

### RC-1 対応: 監査ログ最小スキーマ未固定
- 実装前に監査ログ最小スキーマをADRで固定する。
- 必須キー:
  - `required_imports`
  - `environment_capability`（`estimated` / `proven`）
  - `mismatch_result`（不足import、不足理由、推奨環境）
  - `guard_state`
  - `image_digest`
  - `git_commit_hash`
  - `input_sha256` / `output_sha256` / `parameter_sha256` / `log_sha256`
  - `relative_paths`
- スキーマ欠落時は実行成功扱いにしない（監査不成立）。

### RC-2 対応: UI/UseCase 境界不備
- 責務境界を固定:
  - UI: 入力受理、表示更新、シグナル発火のみ。
  - UseCase: import抽出、capability統合、差分判定、ガード判定、推奨環境選定。
  - Domain: 判定規約、不足理由分類、ガード決定ルール。
  - Infra: knowledge/read-write、実績記録、監査ログ保存、Docker連携。
- UI禁止事項:
  - JSON直接編集
  - 監査ログ直接書き込み
  - Docker実行直接呼び出し
- UIイベント契約固定:
  - UI層のシグナル/スロット命名は Qt命名規約（過去分詞/動詞開始）に強制準拠。
  - 命名規約違反のイベント定義はレビューで受理しない。
- 層間通信は `Protocol` / `ABC` を必須化する。

### RC-3 対応: 差し戻し経路不整合
- 監査票に「違反原因レイヤー（Requirement / Architecture / Implementation）」を必須追加。
- 判定系統を分離:
  - `REJECT_TO_ARCHITECT`: 境界・契約・スキーマ・標準拘束違反
  - `REJECT_TO_IMPLEMENT`: 実装欠陥・テスト欠陥
- REJECT時は処方的指示（違反箇所、根拠、修正条件、再検証手順）を必須化する。

## 4. 監査報告の是正反映（必須）

### 4.1 Docker再現性4要件の固定（Critical対応）
- 実装拘束:
  - `Dockerfile` の `FROM` はタグ禁止、SHA256ダイジェストのみ許可。
  - EOL OS使用時はAPTソースをアーカイブへリダイレクト。
  - pip解決は `constraints.txt` 指定を必須化。
  - OpenCV等C/C++ビルドを含む環境はマルチステージビルドを必須化。
- テスト拘束:
  - `Dockerfile` 静的検査: digest固定、マルチステージ構成、タグ使用0件。
  - ビルド検証: APTソース切替、`constraints.txt` 適用ログ確認。
- 監査証跡拘束:
  - `image_digest`、ビルド設定証跡、依存固定ファイルハッシュを監査ログへ記録。

### 4.2 EMCS客観メトリクス定義（Major対応）
- 監査票に以下を固定:
  - 指標: SRP違反件数、循環依存件数、層逆流件数、複雑度閾値超過件数、監査キー欠落件数。
  - 閾値:
    - SRP違反 0件
    - 循環依存 0件
    - 層逆流 0件
    - 主要UseCaseの循環的複雑度 <= 10
    - 監査必須キー欠落 0件
  - REJECT条件: 上記のいずれか1件でも閾値違反でREJECT。

### 4.3 Builder/Validator分離運用（Major対応）
- Validator入力境界を運用要件として固定:
  - 許可入力: `requirements`、`reference_standards`、差分（Diff）、テスト証跡。
  - 禁止入力: 実装者の意図説明、未確定メモ、口頭補足。
- 監査実行時に「入力境界チェックリスト」の記録を必須化する。

### 4.4 PyQt/PySide 命名規約ゲート（Major対応）
- 実装拘束:
  - シグナルは過去分詞形（`*Changed`, `*Completed`, `*Started` など）を必須とする。
  - スロットは動詞開始（`update_*`, `load_*`, `refresh_*`, `handle_*` など）を必須とする。
- 検証拘束:
  - 静的検査または同等の自動チェックを導入し、命名規約違反をCIで検知する。
  - レビュー・チェックリストに「シグナル/スロット命名規約準拠」を必須項目として追加する。
- REJECT条件:
  - 命名規約違反が1件でも検出された場合は Fail とし、`REJECT` 判定とする。

## 5. Phase 5 実装計画

### 5.1 R5-1 Environment Capability Mapping
- import名単位で capability を算出する（package名基準は不可）。
- データ統合:
  - `user_knowledge.json`（推定）
  - 実行成功実績（実証）
- UI表示は推定/実証を明示分離する。

### 5.2 R5-2 ミスマッチ検知とHard Guard
- `required_imports` と選択環境 capability の差分を算出。
- 差分が1件以上なら `Run` 無効化（Hard Guard）。
- 警告UIに以下を必須表示:
  - 不足import一覧
  - 不足理由（未対応/未検証）
  - 推奨環境
  - 新規環境作成導線
- ガード無視実行は実装しない。

### 5.3 R5-3 強制作成フロー
- 適合環境が無い場合は新規環境作成ダイアログへ誘導。
- 初期候補パッケージ:
  - 第一候補: `user_knowledge.json`
  - 補完: 既定マッピングルール
- 作成完了後、再起動なしで即時選択・実行可能化（Dynamic Refresh）。

## 6. 実装ゲート（着手順）
1. Gate A: 監査スキーマADR、責務境界図、UI許可/禁止API、EMCS監査票、Validator入力境界定義を文書確定。
2. Gate B: Docker準拠ゲート実装（digest/apt archive/constraints/multistage）と静的検査導入。
3. Gate C: UseCase実装（capability統合・差分判定・推奨環境選定）。
4. Gate D: Interface（Protocol/ABC）導入とDI配線。
5. Gate E: UI接続（Humble Object維持、表示/遷移のみ）。
6. Gate F: 強制作成フロー実装とDynamic Refresh接続。
7. Gate G: 監査証跡実装（ハッシュ・digest・commit hash・相対パス）。
8. Gate H: 命名規約ゲート実装（シグナル過去分詞/スロット動詞開始の静的検査 + レビュー項目化）。
9. Gate I: テスト追加・EMCS評価・最終監査。

## 7. テスト計画
- 機能テスト:
  - T5-1 ミスマッチ時Run無効化
  - T5-2 一致時Run有効化
  - T5-3 適合環境なし時の作成導線遷移
  - T5-4 作成直後の即時実行
- Docker準拠テスト:
  - T5-D1 `Dockerfile` digest固定検査（タグ使用禁止）
  - T5-D2 マルチステージ検査（ビルド/実行ステージ分離）
  - T5-D3 APTアーカイブ切替検証
  - T5-D4 `constraints.txt` 適用検証
- アーキテクチャテスト:
  - UIからUseCase/Infra具象直接依存0件
  - Interface非経由呼び出し0件
  - 層逆流0件
  - T5-A1 シグナル命名規約テスト（過去分詞形以外をFail）
  - T5-A2 スロット命名規約テスト（動詞開始以外をFail）
- 監査証跡テスト:
  - 必須キー欠落0件
  - ハッシュ整合性（入出力・パラメータ・ログ）
  - `image_digest` / `git_commit_hash` 記録確認
- ガバナンステスト:
  - EMCS閾値判定の再現性確認
  - Validator入力境界違反検知

## 8. リスクと制御
- 推定capability誤判定:
  - 実証データ優先、推定/実証を分離表示。
- UIへのロジック再流入:
  - UI禁止APIチェックとレビューゲートで遮断。
- Docker再現性逸脱:
  - 静的検査をCI必須ゲート化し、違反時は即Fail。
- 監査欠落:
  - 実行時スキーマバリデータを必須化。

## 9. 実行上の禁止事項
- 本タスクでは `git commit` を実施しない（明示禁止要件）。
