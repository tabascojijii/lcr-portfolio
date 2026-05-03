# LCR ロードマップ（Reference Standards 絶対準拠）

## 0. 位置づけ
本ロードマップは `docs/plan.md` と `docs/reference_standards.md` を同等の絶対基準として策定する。  
いずれか一方のみを優先して他方の拘束を弱める運用は禁止し、不足や不一致がある場合は双方を同時に満たすようにロードマップを拡張して裁定する。

## 1. 目標と完了条件
- 目標: Phase 5（Validation Guardrails）実装と、監査・再現性・UI境界・証跡要件の同時達成。
- 完了条件:
1. `reference_standards` の4章（監査ガバナンス / Docker再現性 / データ完全性 / UIアーキテクチャ）に違反0件。
2. `plan.md` の Gate A〜I 完了。
3. 監査必須キー欠落0件、層逆流0件、循環依存0件、SRP違反0件。
4. `pytest tests/` 全件Pass。

## 2. 絶対基準トレーサビリティ
- 監査ガバナンス（EMCS / Builder-Validator分離 / 処方的REJECT）を全Gateで必須適用。
- Docker再現性（digest固定 / APT archive / constraints / マルチステージ）をGate Bで実装し、以後の前提条件化。
- データ完全性（`image_digest`・`git_commit_hash`・相対パス・SHA256）をGate Gで実装し、監査成立条件に固定。
- UI標準（Humble Object / 依存方向 / Protocol/ABC / シグナル・スロット命名規約）をGate D,E,Hで拘束。

## 3. フェーズ別ロードマップ

### Phase 1: 監査設計固定（Gate A）
- スコープ:
1. 監査ログ最小スキーマADR確定。
2. 責務境界図（UI/UseCase/Domain/Infra）確定。
3. Validator入力境界（許可/禁止）定義。
4. EMCS監査票の客観指標・閾値定義。
5. 差し戻し分類（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）と、違反原因レイヤー（Requirement / Architecture / Implementation）記録要件の固定。
- 成果物:
1. ADR（監査スキーマ）
2. 境界仕様書
3. 監査チェックリスト
- REJECT条件:
1. スキーマ必須項目の未定義。
2. Builder/Validator分離不備。
3. REJECT分類または違反原因レイヤー記録要件の未定義。

### Phase 2: 再現性基盤実装（Gate B）
- スコープ:
1. `Dockerfile` の `FROM` digest固定。
2. EOL向けAPT archive切替。
3. `constraints.txt` 強制。
4. マルチステージビルド化。
- 成果物:
1. Docker構成一式
2. 静的検査ルール
3. ビルド検証証跡
- REJECT条件:
1. タグベースFROM。
2. constraints未適用。
3. 単一ステージでC/C++ビルド同居。

### Phase 3: 判定ロジック実装（Gate C, D）
- スコープ:
1. capability統合（推定/実証分離）。
2. required_imports差分判定。
3. Hard Guard（不足時Run無効）。
4. Protocol/ABC による層間契約固定。
- 成果物:
1. UseCase実装
2. Interface定義
3. DI配線
- REJECT条件:
1. UIで判定ロジックを実行。
2. 具象依存の直接参照。

### Phase 4: UI統合と強制作成フロー（Gate E, F）
- スコープ:
1. UIは入力受理・表示更新・イベント中継のみ。
2. 不足時の推奨環境提示。
3. 新規環境作成導線とDynamic Refresh。
- 成果物:
1. 画面遷移/表示更新実装
2. 新規環境作成フロー
- REJECT条件:
1. UIによるJSON直接編集。
2. ガード無視実行経路の存在。

### Phase 5: 監査証跡と命名規約ゲート（Gate G, H）
- スコープ:
1. 監査ログ最小スキーマ必須キーを固定し記録する（`required_imports`, `environment_capability`, `mismatch_result`, `guard_state`, `image_digest`, `git_commit_hash`, `input_sha256`, `output_sha256`, `parameter_sha256`, `log_sha256`, `relative_paths`）。
2. シグナル過去分詞・スロット動詞開始を静的検査で強制。
- 成果物:
1. 監査ログ実装
2. 命名規約チェッカー
3. CIゲート
- REJECT条件:
1. 監査必須キー欠落（1件でも監査不成立 / Fail）。
2. 命名規約違反1件以上。

### Phase 6: 統合検証・最終監査（Gate I）
- スコープ:
1. 機能テスト（T5-1〜T5-4）。
2. Docker準拠テスト（T5-D1〜D4）。
3. アーキテクチャ/監査/ガバナンステスト。
- 成果物:
1. テスト結果一式
2. EMCS評価結果
3. 最終監査票
- REJECT条件:
1. 閾値違反1件以上。
2. 監査者間判定差分あり。

## 4. マイルストーン
1. M1: Gate A完了（監査基準固定）
2. M2: Gate B完了（再現性基盤確立）
3. M3: Gate C〜F完了（機能成立）
4. M4: Gate G〜H完了（監査成立）
5. M5: Gate I完了（リリース判定可能）

## 5. ガバナンス運用ルール
- Auditorは主観評価を禁止し、EMCS客観指標のみで判定する。
- REJECT時は「違反箇所 / 違反基準 / 修正条件 / 再検証手順」を必須記載する。
- REJECTは以下に分類して記録する:
1. `REJECT_TO_ARCHITECT`（境界・契約・スキーマ・標準拘束違反）
2. `REJECT_TO_IMPLEMENT`（実装欠陥・テスト欠陥）
- 監査票には違反原因レイヤー（Requirement / Architecture / Implementation）を必須記録する。
- Validator入力は `requirements`・`reference_standards`・Diff・テスト証跡に限定し、実装者意図説明を遮断する。

## 6. 主要リスクと制御
- 推定capability誤判定:
  - 制御: 実証データ優先、推定/実証の明示分離。
- 層境界崩壊:
  - 制御: Protocol/ABC強制、依存方向テストをCIゲート化。
- 再現性逸脱:
  - 制御: Docker静的検査Fail-Fast。
- 監査証跡欠落:
  - 制御: 実行時スキーマ検証を必須化。

## 7. 実行上の厳守事項
- 本作業および後続作業で、`reference_standards` 違反は即時REJECTとする。
- Git操作（`git commit` など）は本依頼では実行しない。
