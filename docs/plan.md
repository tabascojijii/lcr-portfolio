# LCR 実装計画（Architect / Structural Recovery Plan v3）

## 0. 読み込み結果と前提
- 読み込み完了:
  - `docs/requirements.md`
  - `docs/reference_standards.md`
  - `docs/post_mortem.md`
  - `docs/audit_report.md`
- 指定された `docs/core_philosophy.md` は現時点で存在しないため、`requirements.md` / `reference_standards.md` / `post_mortem.md` / `audit_report.md` を拘束条件として計画を再構成する。
- `docs/audit_report.md` の判定は **AUDIT_PASS_PLAN（重大指摘なし）**。したがって本改訂の主目的は「監査指摘対応」ではなく、`post_mortem.md` の RC-1〜RC-3 をプロセス/設計に埋め込み、再発を構造的に封じること。

## 1. 最上位拘束
1. 要件拘束:
   - Phase 5 Validation Guardrails（R5-1〜R5-3, AC-1〜AC-5）を充足する。
   - `requirements.md` 記載の共通必須条件（`pytest tests/` 全件Pass、規約準拠）を充足する。
2. 規約拘束:
   - `reference_standards.md` 1章〜4章を「推奨」ではなく「Fail条件付き必須」として扱う。
3. 再発防止拘束:
   - 監査スキーマ、責務境界、監査メトリクス、監査入力境界、Interface契約を設計成果物として固定するまで実装着手禁止。

## 2. Post Mortem 対応（RC-1〜RC-3）

### 2.1 RC-1: 監査ログ最小スキーマ未固定
- 監査ログ必須スキーマを ADR で固定する。
  - `required_imports`
  - `environment_capability`（推定/実証ラベル付き）
  - `mismatch_result`（不足 import、理由、推奨環境）
  - `guard_state`
  - `image_digest`
  - `git_commit_hash`
  - `input_sha256` / `output_sha256` / `parameter_sha256` / `log_sha256`
  - `relative_paths`
- 欠落項目が1つでもある実行は「監査不成立」として失敗扱いにする。

### 2.2 RC-2: UI/UseCase 境界未固定
- 層責務を固定する。
  - View: 入力受付、表示更新、シグナル中継のみ
  - UseCase: import抽出、差分判定、ガード判定、推奨環境決定
  - Infra: knowledge/実績永続化、監査ログ保存、コンテナ実行連携
- `MainWindow` からドメイン判定ロジックと永続化処理を排除する。
- UI許可API/禁止API一覧を作成し、UIからの直接JSON操作・監査ログ書込・Docker呼出を禁止する。

### 2.3 RC-3: 差し戻し経路不整合
- 監査票に「違反原因レイヤー」を必須化（Requirement/Architecture/Implementation）。
- 判定を2系統化する。
  - `REJECT_TO_ARCHITECT`: 契約、境界、スキーマ、規約違反
  - `REJECT_TO_IMPLEMENT`: 実装欠陥、テスト欠陥
- REJECT時は処方的指示（違反箇所、根拠規約、修正条件、再検証手順）を必須化する。

## 3. audit_report を踏まえた監査ベースライン固定

### 3.1 EMCS定量メトリクス（PASS維持条件）
- M1 層間依存違反件数:
  - 定義: UI層からDomain/Infra具象への直接参照件数
  - 測定: 静的解析（importルール）+ レビュー
  - Fail条件: 1件以上
  - エビデンス: `docs/audit/evidence/dependency_report.md`
- M2 SRP逸脱:
  - 定義: 単一クラスに「表示 + 判定 + 永続化 + 実行制御」が同居
  - 測定: 責務マトリクス表
  - Fail条件: 1クラスでも4責務同居
  - エビデンス: `docs/audit/evidence/srp_matrix.md`
- M3 複雑度:
  - 定義: UI層メソッドの分岐複雑度
  - 測定: lizard/radon等
  - Fail条件: UI層メソッドで CC > 10
  - エビデンス: `docs/audit/evidence/complexity.txt`
- M4 監査スキーマ充足率:
  - 定義: 必須キー充足率
  - 測定: 実行後バリデータ
  - Fail条件: 100%未満
  - エビデンス: `docs/audit/evidence/audit_schema_check.json`

### 3.2 Builder/Validator 分離（PASS維持条件）
- Auditor入力境界を固定:
  - 許可入力: requirements、reference standards、対象Diff、テスト証跡
  - 禁止入力: Builderの思考ログ、未承認メモ、口頭補足
- 監査テンプレートに「参照入力一覧」欄を必須化する。

### 3.3 Docker再現性標準（PASS維持条件）
- EOLスタック用コンテナ規約を実装計画へ編入する。
  - `FROM <image>@sha256:<digest>` を必須化
  - APTソースを archive/old-releases に固定
  - `constraints.txt` による依存解決範囲固定
  - マルチステージで build/runtime を分離
- 監査項目として「コンテナ再現性チェック」を追加する。

### 3.4 Interface規律（PASS維持条件）
- View-UseCase 間、UseCase-Infra 間は `abc.ABC` または `typing.Protocol` 経由に限定する。
- 具象クラスの直接newを禁止し、Composition Root で注入する。
- テストに「具象依存禁止」チェックを追加する。

### 3.5 Signal/Slot命名規約（PASS維持条件）
- Signal: 過去分詞（例: `capabilityUpdated`）
- Slot: 動詞開始（例: `update_capability_display`）
- レビュー観点とLint観点に命名検査を追加する。

## 4. 実装スコープ（Phase 5）

### 4.1 R5-1 Environment Capability Mapping
- import名単位で capability を構築する。
- データ源:
  - `user_knowledge.json`（推定）
  - 実行実績ストア（実証）
- UIで推定/実証を明示区分する。

### 4.2 R5-2 ミスマッチ検知とHard Guard
- `required_imports` と選択環境 capability の差分を計算する。
- 差分1件以上なら `Run` を無効化する（Hard Guard）。
- 警告UIに不足import、理由、推奨環境、作成導線を表示する。
- ガード回避実行は許可しない。

### 4.3 R5-3 強制作成フロー
- 適合環境がない場合は作成ダイアログへ強制誘導する。
- 不足importからpackage候補を自動投入する。
  - 第一候補: `user_knowledge.json`
  - 補完: 既定マッピングルール
- 作成完了後はDynamic Refreshで即時実行可能化する。

## 5. 実装順序（Gate方式）
1. Gate A（設計固定）:
   - 監査スキーマ、責務境界、許可/禁止API、EMCSメトリクス、監査入力境界を文書化
2. Gate B（Domain/UseCase）:
   - capability統合、差分判定、推奨環境ロジック
3. Gate C（Interface導入）:
   - Protocol/ABC 境界契約導入、DI配線
4. Gate D（UI接続）:
   - Humble Object維持で表示反映のみ実装
5. Gate E（強制作成フロー）:
   - 候補投入と即時反映
6. Gate F（監査証跡 + Docker再現性）:
   - スキーマ記録、コンテナ再現性要件反映
7. Gate G（テスト/監査）:
   - pytest、アーキテクチャ監査、証跡出力

## 6. テスト計画
- 機能テスト（必須）:
  - T5-1 ミスマッチ時Run無効化
  - T5-2 適合時Run有効化
  - T5-3 適合環境なし時の作成導線遷移
  - T5-4 作成後即時実行可能化
- アーキテクチャテスト（必須）:
  - UIからUseCase/Infra具象への直接依存が0件
  - Interface経由以外の層間呼出が0件
  - Signal/Slot命名規約違反が0件
- 監査証跡テスト（必須）:
  - 必須スキーマキー充足率100%
  - `log_sha256` を含むハッシュ整合性
- 再現性テスト（必須）:
  - Docker digest固定
  - archive repo設定
  - constraints適用
  - multi-stage分離

## 7. 成果物
- `docs/architecture/`:
  - 監査ログスキーマADR
  - 責務境界図
  - UI許可/禁止API表
  - Interface契約一覧（Protocol/ABC）
- `docs/audit/`:
  - 監査テンプレート（参照入力一覧付き）
  - EMCSメトリクス定義と証跡出力先定義
- `src/`:
  - UseCase判定/ガード
  - Interface境界
  - UI接続
  - 作成フロー
- `tests/`:
  - 機能、境界、命名、証跡、再現性テスト

## 8. 完了条件（Definition of Done）
1. AC-1〜AC-5 を満たす。
2. `pytest tests/` 全件Pass。
3. EMCSメトリクス Fail条件が全て0件。
4. `reference_standards.md` 1章〜4章に対する重大違反0件。
5. `post_mortem.md` RC-1〜RC-3 の再発防止証跡を提示可能。
6. 監査票で `REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT` の判定根拠を追跡可能。

## 9. リスクと制御
- リスク: 推定capabilityの誤判定
  - 制御: 実証データ優先、推定/実証ラベル分離
- リスク: UIへのロジック逆流
  - 制御: importルール監視 + SRPマトリクスレビュー
- リスク: 監査項目欠落
  - 制御: 実行前後バリデータで必須項目強制
- リスク: EOLコンテナの再現不能化
  - 制御: digest固定 + archive repo + constraints + multi-stage

## 10. 注記
- 本タスクでは `git commit` を実施しない（禁止要件遵守）。
