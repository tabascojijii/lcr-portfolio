# LCR 実装計画（Architect / Structural Recovery Plan）

## 0. 読み込み結果と前提
- 読み込み完了:
  - `docs/requirements.md`
  - `docs/reference_standards.md`
  - `docs/post_mortem.md`（存在確認済み）
- 指定ファイル `docs/core_philosophy.md` は現時点で存在しない。
- したがって本計画は、`requirements.md` と `reference_standards.md` を上位拘束条件として策定する。
- 本計画の最優先目的は、`post_mortem.md` で特定された構造欠陥（RC-1〜RC-3）を先に閉じ、実装ループ再発を防止すること。

## 1. 設計原則（最上位拘束）
1. 要件拘束: Phase 5 Validation Guardrails（R5-1〜R5-3, AC-1〜AC-5）を完全充足する。
2. 規約拘束: `reference_standards.md` の以下を必須適用。
   - Humble Object + Clean Architecture（UIとUseCase分離）
   - Data Integrity（ハッシュ証跡・相対パス・不変参照）
   - 処方的エラーハンドリング（監査可能な失敗理由）
3. 再発防止拘束: 実装着手前に「監査スキーマ」「責務境界」「許可API」を固定し、未固定なら実装禁止。

## 2. Post Mortem 起点の是正方針

### RC-1 対策: 監査ログ最小スキーマ未固定
- 実装前に以下の必須スキーマを確定し、ADRとして保存する。
  - `required_imports`（抽出結果）
  - `environment_capability`（推定/実証の区別付き）
  - `mismatch_result`（不足 import, 理由, 推奨環境）
  - `guard_state`（Run無効化発火状態）
  - `image_digest`（使用コンテナ）
  - `git_commit_hash`（`git rev-parse HEAD`）
  - `input/output/parameter/log_sha256`
  - `relative_paths`（全参照をプロジェクト相対で記録）
- 未記録項目が1つでもある実行は「監査不成立」として失敗扱いにする。

### RC-2 対策: UI / UseCase 境界不備
- `MainWindow` から判定ロジックを排除し、UseCaseへ移管する。
- 境界を次の3層で固定する。
  - View: 表示・イベント受理・状態反映のみ（Humble Object）
  - UseCase: required imports抽出、capability照合、guard判定、推奨環境選定
  - Infra: knowledge読込、実績読込、監査ログ永続化
- UIから直接呼べる操作を許可リスト化し、禁止API（例: UIから直接JSON更新/監査書込）を明記する。

### RC-3 対策: 差し戻し経路不整合
- 監査観点に「違反レイヤー」フィールドを導入。
  - Requirement / Architecture / Implementation
- 失敗分類を2系統化。
  - `REJECT_TO_ARCHITECT`: 境界・契約・スキーマ不備
  - `REJECT_TO_IMPLEMENT`: 実装欠陥・テスト欠陥
- 監査テンプレートに「処方的修正指示（違反箇所・制約根拠・修正条件）」を必須化する。

## 3. 実装スコープ（Phase 5）

### 3.1 R5-1 Environment Capability Mapping
- import名単位で capability を生成。
- データ源を統合:
  - `user_knowledge.json`（推定）
  - 実行実績（実証）
- UI表示は「推定/実証」を視覚的に区別。

### 3.2 R5-2 ミスマッチ検知とHard Guard
- スクリプト解析で `required_imports` を抽出。
- 選択環境 capability と差分計算。
- 差分1件以上で `Run` を強制無効化。
- 警告UIに必須表示:
  - 不足 import 一覧
  - 不足理由（未対応/未検証）
  - 推奨環境
  - 新規環境作成導線
- ガード無視実行は未実装（禁止）を維持。

### 3.3 R5-3 強制作成フロー
- 適合環境なし時は新規作成ダイアログへ遷移。
- 不足 import から package候補を自動補完。
  - 第一候補: `user_knowledge.json`
  - 補完候補: 既定ルール
- 作成後は再起動なしで即時選択・実行可能化（Dynamic Refresh）。

## 4. 実装順序（ゲート付き）
1. Gate A: 設計確定
   - 監査スキーマ定義
   - 責務境界図
   - 許可/禁止APIリスト
2. Gate B: ドメイン実装
   - capability統合、差分判定、推奨環境ロジック
3. Gate C: UI接続
   - Viewは表示更新のみ
   - Hard Guard と警告表示の反映
4. Gate D: 作成フロー接続
   - 不足importの候補投入
   - 作成完了後の即時反映
5. Gate E: 監査証跡実装
   - 必須スキーマ項目の全記録
6. Gate F: テストと監査
   - 自動テスト + トレーサビリティ検証

## 5. テスト計画（必須）
- `pytest tests/` 全件Passをリリース前提条件とする。
- 追加必須テスト:
  - T5-1: ミスマッチ時にRun無効化
  - T5-2: 適合時にRun有効化
  - T5-3: 適合環境なしで作成導線遷移
  - T5-4: 作成後の即時実行可能化
- 追加アーキテクチャテスト:
  - UI層がUseCaseを介さず判定ロジックへ直接アクセスしないこと
  - 監査ログ必須項目欠落時に実行失敗すること
- 監査性テスト:
  - `required_imports` / `environment_capability` / `mismatch_result` / `guard_state` 記録確認
  - ハッシュ整合性（log自体のsha256含む）

## 6. 成果物定義
- `docs/architecture/`:
  - 監査ログスキーマ定義
  - 責務境界図
  - UI許可/禁止API表
- `src/`:
  - UseCase層の判定・ガード実装
  - UI接続（表示専念）
  - 作成フロー即時反映
- `tests/`:
  - R5 系4本 + 境界/監査性テスト
- `docs/`:
  - 要件-実装-テスト トレーサビリティ表

## 7. 完了条件（Definition of Done）
1. AC-1〜AC-5 をすべて満たす。
2. `pytest tests/` 全件Pass。
3. `reference_standards.md` 重大違反 0 件。
4. `post_mortem.md` のRC-1〜RC-3に対応する再発防止エビデンスを提出できる。
5. 監査で `REJECT_TO_ARCHITECT`/`REJECT_TO_IMPLEMENT` の判定根拠を追跡可能。

## 8. リスク管理
- リスク: capability推定誤りで誤ガード。
  - 対策: 推定/実証ラベルを分離し、実証データ優先で判定。
- リスク: UIへのロジック逆流。
  - 対策: PRレビューで「UIロジック混入チェックリスト」を必須化。
- リスク: 監査ログ欠損。
  - 対策: 書込前バリデータで必須項目を強制検証。

## 9. 注記
- 本タスクでは `git commit` は実施しない（禁止要件遵守）。
