# LCR 実装計画（Architect / Structural Recovery Plan v4）

## 0. 読み込み結果
- 読み込み完了:
  - `docs/requirements.md`
  - `docs/reference_standards.md`
  - `docs/post_mortem.md`
- `docs/core_philosophy.md` は現時点で存在しないため、上記3文書を拘束条件として計画を策定する。

## 1. 目的と完了定義
- 目的: Phase 5（Validation Guardrails）を実装しつつ、`post_mortem.md` の構造欠陥（RC-1〜RC-3）を再発不能な形で解消する。
- 完了定義:
  1. AC-1〜AC-5 達成。
  2. `pytest tests/` 全件Pass。
  3. 監査スキーマ必須項目充足率100%。
  4. UI/UseCase/Infra の依存方向違反0件。
  5. REJECT分類（Architect/Implement）の運用証跡を残す。

## 2. 設計原則（拘束）
- `reference_standards.md` を「推奨」ではなく「Fail条件付き必須」として適用する。
- Humble Object を徹底し、UIは表示とイベント中継のみに限定する。
- 判定ロジック・監査ロジック・永続化ロジックを UseCase/Domain/Infra に分離する。
- 監査証跡は ALCOA++ 準拠で、ハッシュと再現性情報を必須記録する。

## 3. Post Mortem 対応（RC別）

### RC-1 対応: 監査ログ最小スキーマ未固定
- 実装前に監査ログスキーマを固定（ADR化）する。
- 必須キー:
  - `required_imports`
  - `environment_capability`（`estimated` / `proven` 区分）
  - `mismatch_result`（不足import、理由、推奨環境）
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
  - Infra: knowledge/read-write、実績記録、監査ログ保存、Docker連携。
- UI禁止事項:
  - JSON直接編集
  - 監査ログ直接書き込み
  - Docker実行直接呼び出し
- 層間通信は `Protocol` / `ABC` を必須化する。

### RC-3 対応: 差し戻し経路不整合
- 監査票に「違反原因レイヤー（Requirement / Architecture / Implementation）」を必須追加。
- 判定系統を分離:
  - `REJECT_TO_ARCHITECT`: 境界・契約・スキーマ違反
  - `REJECT_TO_IMPLEMENT`: 実装欠陥・テスト欠陥
- REJECT時は処方的指示（違反箇所、根拠、修正条件、再検証手順）を必須化する。

## 4. Phase 5 実装計画

### 4.1 R5-1 Environment Capability Mapping
- import名単位で capability を算出する（package名基準は不可）。
- データ統合:
  - `user_knowledge.json`（推定）
  - 実行成功実績（実証）
- UI表示は推定/実証を明示分離する。

### 4.2 R5-2 ミスマッチ検知とHard Guard
- `required_imports` と選択環境 capability の差分を算出。
- 差分が1件以上なら `Run` 無効化（Hard Guard）。
- 警告UIに以下を必須表示:
  - 不足import一覧
  - 不足理由（未対応/未検証）
  - 推奨環境
  - 新規環境作成導線
- ガード無視実行は実装しない。

### 4.3 R5-3 強制作成フロー
- 適合環境が無い場合は新規環境作成ダイアログへ誘導。
- 初期候補パッケージ:
  - 第一候補: `user_knowledge.json`
  - 補完: 既定マッピングルール
- 作成完了後、再起動なしで即時選択・実行可能化（Dynamic Refresh）。

## 5. 実装ゲート（着手順）
1. Gate A: 監査スキーマADR、責務境界図、UI許可/禁止API、監査票拡張を文書確定。
2. Gate B: UseCase（capability統合・差分判定・推奨環境選定）実装。
3. Gate C: Interface（Protocol/ABC）導入とDI配線。
4. Gate D: UI接続（Humble Object維持、表示/遷移のみ）。
5. Gate E: 強制作成フロー実装とDynamic Refresh接続。
6. Gate F: 監査証跡実装（ハッシュ・digest・commit hash・相対パス）。
7. Gate G: テスト追加・監査証跡検証・最終監査。

## 6. テスト計画
- 機能テスト:
  - T5-1 ミスマッチ時Run無効化
  - T5-2 一致時Run有効化
  - T5-3 適合環境なし時の作成導線遷移
  - T5-4 作成直後の即時実行
- アーキテクチャテスト:
  - UIからUseCase/Infra具象直接依存0件
  - Interface非経由呼び出し0件
- 監査証跡テスト:
  - 必須キー欠落0件
  - ハッシュ整合性（入出力・パラメータ・ログ）
- 補助テスト:
  - 推定/実証ラベル表示整合
  - 部分失敗時のログ完全性

## 7. リスクと制御
- 推定capability誤判定:
  - 実証データ優先、推定/実証を分離表示。
- UIへのロジック再流入:
  - UI禁止APIチェックとレビューゲートで遮断。
- 監査欠落:
  - 実行時スキーマバリデータを必須化。

## 8. 実行上の禁止事項
- 本タスクでは `git commit` を実施しない（明示禁止要件）。
