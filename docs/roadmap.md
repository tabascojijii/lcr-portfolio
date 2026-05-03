# LCR ロードマップ（PM版 / Reference Standards完全準拠）

## 0. 目的と適用範囲
本ロードマップは、`docs/reference_standards.md` を絶対基準として、`docs/plan.md` を実行可能な工程に再編したものである。  
すべてのフェーズは、基準逸脱時に即時停止し、`REJECT_TO_ARCHITECT` または `REJECT_TO_IMPLEMENT` の処方的差し戻しを行う。

## 1. 最上位原則（非交渉）
1. `reference_standards.md` 第1章〜第4章の違反は1件でも不合格。
2. Builder/Validator分離を維持し、監査入力は「要件・差分・証跡」のみ。
3. 監査ログは必須スキーマ100%充足を達成するまで実装完了と見なさない。
4. UIはHumble Objectを維持し、判定ロジック/永続化/実行制御を保持しない。
5. EOLスタックの再現性はDocker digest固定・archive repo・constraints・multi-stageを必須とする。

## 2. マイルストーン

### M0: ガバナンス固定（Week 1）
- 目的: 監査と設計の失敗条件を先に固定し、手戻りを防止。
- 成果物:
  - 監査ログ最小スキーマADR（required_imports, environment_capability, mismatch_result, guard_state, image_digest, git_commit_hash, input/output/parameter/log sha256, relative_paths）
  - 監査テンプレート（参照入力一覧、違反レイヤー分類、処方的REJECT文面）
  - EMCS評価表（M1〜M4の測定方法とFail条件）
- ゲート:
  - 監査票で `REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT` 判定ルールが追跡可能
  - 必須スキーマ欠落時に「監査不成立」を返せる

### M1: 境界契約と責務分離（Week 1-2）
- 目的: RC-2再発防止（UI/UseCase/Infra責務混在の排除）。
- 成果物:
  - 責務境界図（View / UseCase / Infra）
  - UI許可API・禁止API一覧（直接JSON操作、監査ログ書込、Docker呼出を禁止）
  - `abc.ABC` / `typing.Protocol` 契約一覧
  - Composition Rootでの依存注入設計
- ゲート:
  - UI→UseCase/Infra具象の直接依存0件
  - Interface経由以外の層間呼出0件

### M2: Phase 5コア実装（Week 2-3）
- 目的: R5-1〜R5-3を規約準拠で実装。
- スコープ:
  - R5-1: import単位 capability 構築（推定/実証を明示）
  - R5-2: required_imports差分検知、Hard GuardでRun無効化
  - R5-3: 適合環境なし時の強制作成フロー、候補自動投入、作成後Dynamic Refresh
- ゲート:
  - ミスマッチ時にガード回避実行不可
  - 警告UIに不足import・理由・推奨環境・作成導線を表示

### M3: 監査証跡と再現性実装（Week 3）
- 目的: 第2章・第3章の完全実装。
- 成果物:
  - Docker再現性設定（digest固定、archive sources、constraints、multi-stage）
  - ALCOA++準拠ログ（image digest, git hash, 相対パス, SHA-256群）
  - 監査スキーマバリデータ
- ゲート:
  - スキーマ充足率100%
  - 改ざん検知ハッシュ全項目が検証可能

### M4: テスト・監査・受け入れ（Week 4）
- 目的: 要件と規約の合格証跡を確定。
- 必須テスト:
  - 機能: T5-1〜T5-4
  - アーキテクチャ: 依存違反0、具象依存禁止、Signal/Slot命名違反0
  - 監査証跡: 必須キー100%、`log_sha256` 整合性
  - 再現性: Docker4要件の検証
- 完了ゲート:
  - `pytest tests/` 全件Pass
  - EMCS Fail条件 0件
  - `reference_standards.md` 重大違反 0件

## 3. 実行順序（Gate Sequence）
1. Gate A: 監査スキーマ・EMCS・監査入力境界の文書固定
2. Gate B: UseCase判定（capability統合・差分検知・推奨環境決定）
3. Gate C: Interface導入（Protocol/ABC + DI配線）
4. Gate D: UI接続（Humble Object維持、表示反映のみ）
5. Gate E: 強制作成フロー（候補投入 + Dynamic Refresh）
6. Gate F: 監査証跡 + Docker再現性要件反映
7. Gate G: テスト・監査・証跡出力

## 4. KPI / 監査メトリクス
- M1 層間依存違反件数: 0件（Fail: 1件以上）
- M2 SRP逸脱クラス数: 0件（Fail: 1件以上）
- M3 UI層CC超過: 0件（Fail: CC > 10）
- M4 監査スキーマ充足率: 100%（Fail: 100%未満）

## 5. リスク管理
- 推定capability誤判定
  - 制御: 実証データ優先、推定/実証ラベル分離
- UIへのロジック逆流
  - 制御: importルール監視、責務マトリクスレビュー
- 監査項目欠落
  - 制御: 実行前後バリデータで必須項目を強制
- EOL依存解決不安定化
  - 制御: constraints固定、archive repo固定、digest固定

## 6. Definition of Done
1. AC-1〜AC-5充足。
2. `pytest tests/` 全件Pass。
3. EMCS（M1〜M4）Fail条件0件。
4. `reference_standards.md` 第1章〜第4章の重大違反0件。
5. RC-1〜RC-3の再発防止証跡を提示可能。
6. 監査票で差し戻し根拠（Requirement/Architecture/Implementation）が追跡可能。
