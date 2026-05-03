# LCR Roadmap（PM）

## 0. 目的と絶対基準
- 本ロードマップの絶対基準は `docs/reference_standards.md` とする。
- 必須要求入力は `docs/requirement.md` とし、要求充足を判定軸に含める。
- 実行計画は `docs/plan.md` に準拠し、本基準・要求入力に適合する形で実行順序と完了条件へ展開する。
- 監査（Auditor）は基準逸脱を不許容とし、各マイルストーンで REJECT/ACCEPT 判定可能な証跡を必須化する。

## 1. ロードマップ全体像
1. Phase 1: 現状診断とギャップ確定
2. Phase 2: アーキテクチャ是正設計
3. Phase 3: Phase 4機能実装（Self-Learning Loop）
4. Phase 4: 再現性・監査証跡の実装固定
5. Phase 5: テスト・監査ゲート
6. Phase 6: リリース判定

## 2. フェーズ別計画

### Phase 1（Week 1）: 現状診断とギャップ確定
**目標**
- `docs/plan.md` の対象（Knowledge Update / Real-time Feedback / Dynamic Refresh）について、基準書観点の適合性を確定する。

**主要タスク**
- Self-Learning Loop 関連コードの責務分解（View / Presenter / UseCase / Infra）
- 3再検証シナリオの現状再実行と失敗条件の記録
- 基準違反一覧の作成（違反条項、影響度、再現手順、修正方針案）

**受け入れ基準（Gate-1）**
- すべての違反が `reference_standards.md` の条項番号にマッピング済み
- Builder/Validator分離で第三者が差分のみから再判定可能な記録形式である
- EMCS客観評価メトリクス初期値を記録済みである（採取タイミング: Phase 1）
  - SRP違反件数（閾値: 0件）
  - 高複雑度関数件数（閾値: サイクロマティック複雑度 > 10 を 0件）
  - 依存方向違反件数（閾値: 内側レイヤーから Qt 依存 0件）
  - REJECT理由カテゴリ別件数（閾値: 未分類 0件）
  - 証跡保存先: `artifacts/audit/phase1_emcs_metrics.md`, `artifacts/audit/reject_log_phase1.json`

### Phase 2（Week 2）: アーキテクチャ是正設計
**目標**
- UI汚染を除去し、実装前に依存方向と責務境界を固定する。

**主要タスク**
- Humble Object 適用: View からロジック排除
- Clean Architecture 準拠: Qt依存を外側レイヤーに隔離
- `abc.ABC` / `typing.Protocol` による境界インターフェース定義
- シグナル/スロット命名規約の統一（シグナル過去分詞、スロット動詞）

**受け入れ基準（Gate-2）**
- UI層の主要ロジックが UseCase/Presenter に移譲されている
- 依存方向違反（内側→Qt）が0件
- インターフェース経由でユースケース単体テスト可能

### Phase 3（Week 3-4）: Phase 4機能実装（Self-Learning Loop）
**目標**
- 要求3機能を、基準準拠で実装完了する。

**主要タスク**
- Knowledge Update:
  - ビルド成功時に「ユーザー承認済み」インポート名↔パッケージ名のみ `library.json` / `user_knowledge.json` へ追記
- Real-time Feedback:
  - Dockerビルドログの非同期ストリーミング表示（UIフリーズ防止）
- Dynamic Refresh:
  - 新規作成環境をUI一覧へ即時反映し、再起動なしで実行可能化
- 異常系:
  - 失敗/キャンセル/中断時の安全停止と状態整合性維持

**受け入れ基準（Gate-3）**
- 3機能が正常系で動作し、既知回帰（ID消失・`custom-env`化け）を再発しない
- 異常系でクラッシュしない
- REJECT時に修正指示可能な粒度で変更理由・影響範囲を提示可能

### Phase 4（Week 4）: 再現性・監査証跡の実装固定
**目標**
- EOL技術スタックでもビルド再現性と法的証拠レベルの追跡性を担保する。

**主要タスク**
- Docker再現性固定:
  - `FROM` digest固定
  - EOL向け archive リポジトリへの切替
  - `constraints.txt` による依存探索制御
  - OpenCV等のマルチステージビルド化
- 監査証跡実装:
  - ログへコンテナdigestと実行時コミットハッシュ記録
  - パスをプロジェクトルート相対で統一
  - 入出力・パラメータ・実行ログへSHA-256付与

**受け入れ基準（Gate-4）**
- 同一入力でビルド/実行結果を再現可能
- 監査ログに必須項目欠損がない
- ハッシュ照合で改ざん検知可能

### Phase 5（Week 5）: テスト・監査ゲート
**目標**
- 要件充足と基準準拠をテスト証跡で確定する。

**主要タスク**
- `pytest tests/` 全件実行
- 再検証3シナリオの合否判定
- 非機能検証（UI応答性、ログ完走、異常系安全停止）
- 要件→実装→テストのトレーサビリティ表作成

**受け入れ基準（Gate-5）**
- `pytest tests/` 全件Pass
- 再検証3シナリオ合格
- 重大違反0件で Auditor が差分のみから判定可能

### Phase 6（Week 6）: リリース判定
**目標**
- 監査提出パッケージを確定し、出荷可否を決定する。

**主要タスク**
- 監査エビデンス一式の最終整備
- 未達項目の有無判定（未達時は処方的な是正計画を添付）
- PM/Architect/Implementer/Auditor 合同レビュー

**受け入れ基準（Final Gate）**
- `docs/reference_standards.md` 重大違反0
- `docs/plan.md` 対象機能の完了証跡が揃っている
- 再現手順、ログ、ハッシュを第三者が検証可能

## 3. 管理指標（KPI/KGI）
- KGI-1: 基準重大違反件数 = 0
- KGI-2: 再検証シナリオ合格率 = 100%
- KGI-3: 監査必須ログ項目充足率 = 100%
- KGI-4: EMCS閾値違反件数 = 0（評価時点: Phase 5 Gate）
- KPI-1: REJECT後の再提出リードタイム（中央値）
- KPI-2: UI層ロジック残存件数
- KPI-3: 再現不能ビルド発生率
- KPI-4: SRP違反件数（閾値: 0、採取: Phase 1/5、保存: `artifacts/audit/phase1_emcs_metrics.md`, `artifacts/audit/phase5_emcs_metrics.md`）
- KPI-5: 高複雑度関数件数（閾値: 複雑度 > 10 を 0、採取: Phase 1/5、保存: `artifacts/audit/phase1_emcs_metrics.md`, `artifacts/audit/phase5_emcs_metrics.md`）
- KPI-6: 依存方向違反件数（閾値: 0、採取: Phase 1/5、保存: `artifacts/audit/phase1_emcs_metrics.md`, `artifacts/audit/phase5_emcs_metrics.md`）
- KPI-7: REJECT理由カテゴリ別件数（閾値: 未分類 0、採取: Phase 1/5、保存: `artifacts/audit/reject_log_phase1.json`, `artifacts/audit/reject_log_phase5.json`）

## 4. リスクとエスカレーション
- リスク: EOL依存取得の不安定化
  - 対応: archive固定、constraints厳格化、失敗時の代替ミラー定義
- リスク: UIへのロジック逆流
  - 対応: PRレビューで責務境界チェックリストを必須化
- リスク: 監査ログ欠損
  - 対応: 必須項目未記録時はジョブ失敗とするガード実装

## 5. トレーサビリティ（基準書対応）
- 監査/ガバナンス標準（基準書1章）
  - Phase 1, 5, 6 で Builder/Validator分離、処方的REJECT運用を担保
  - EMCS客観評価（SRP違反件数、高複雑度関数件数、依存方向違反件数、REJECT理由カテゴリ別件数）を Phase 1/5 で採取し、`artifacts/audit/` 配下へ保存
- Docker再現性標準（基準書2章）
  - Phase 4 で digest固定、archive化、constraints、マルチステージを実装
- データ完全性（基準書3章）
  - Phase 4, 5 で digest/commit hash/SHA-256/相対パスを検証
- PyQt/PySide標準（基準書4章）
  - Phase 2, 3 で Humble Object、Clean Architecture、Interface規律、命名規約を担保
