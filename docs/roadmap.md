# LCR ロードマップ（PM）

## 0. 基本方針（絶対基準）
本ロードマップは `docs/plan.md` と `docs/reference_standards.md` を同列の絶対基準として策定する。実装・運用は両基準を同時に満たすことを必須条件とし、片方のみの充足を許容しない。

非交渉ルール:
1. Builder/Validator 分離を維持し、監査は `requirements + diff` を一次入力として敵対的に実施する。
2. UI層は Humble Object を徹底し、業務ロジック・外部I/O・永続化判断を持たない。
3. クラス間通信は `abc.ABC` / `typing.Protocol` のインターフェース経由を強制する。
4. EOLコンテナ再現性は digest固定・アーカイブAPT・constraints・マルチステージを常時満たす。
5. 監査証跡は ALCOA++ 準拠で、Digest/Git Hash/相対パス/ハッシュ完全化を必須化する。

---

## 1. マイルストーン

### M1: ガバナンス固定（監査運用の先行確立）
目的: 要件逸脱と差し戻しループを予防する運用土台の固定。

実施項目:
- EMCS観点の監査チェックリストを成果物化
- REJECT時の処方的テンプレート（失敗箇所/違反制約/修正ヒント）標準化
- 監査入力制約（requirements + diff）をCI/運用手順へ明文化
- 差し戻し先規約を明文化（設計起因の構造違反は `REJECT_TO_ARCHITECT` を必須化）

完了条件:
- 監査手順書で Builder/Validator 分離が明文化済み
- REJECTメッセージ雛形が定義済み
- 監査入力制約違反 0
- `REJECT_TO_ARCHITECT` 判定漏れ 0

### M2: UI境界の構造是正（Clean Architecture + Humble Object）
目的: `main_window.py` を表示責務へ限定し、業務判断をUseCaseへ隔離。

実施項目:
- `_run_container` の判定系責務を `RunPreparationUseCase` へ移管
- `_show_create_env_dialog` の候補生成責務を `EnvironmentCreationProposalUseCase` へ移管
- UI->Domain/UI->Infrastructure の直接参照を排除

完了条件:
- UI層の業務ロジック主要導線 0
- UI->Domain 直参照 0
- Port/Interface 非経由呼び出し 0

### M3: インターフェース規律と型契約固定
目的: 実装の抜け漏れと暗黙契約を排除。

実施項目:
- Port群（EnvironmentCapability/Repository/ContainerRuntime/AuditLog/ImageCleanup/KnowledgeMapping）の契約明文化
- UI-Application、UI-Presenter、UseCase間、Domainサービス間の通信をProtocol/ABC化
- DTO strict化（Pydantic v2）と dict互換アダプタ整備

完了条件:
- 主要境界の具象直接依存 0
- DTOバリデーションfail-fast動作確認
- `Any` 無制限利用 0（境界契約上）

### M4: 品質ゲート定着（構造先行）
目的: 「テスト合格だが構造違反」を再発不能化。

実施項目:
- Gate-1（構造）をGate-2（機能）より先行
- Gate-1判定項目へ `逆方向依存 = 0` を明示し、未達時は停止
- PyQt命名規約チェック（signal過去分詞/slot動詞開始）を静的検査化
- 固定重点検査（`_run_container`/`_show_create_env_dialog`）を毎回実行
- Gate-2必須項目を固定運用:
  - `pytest tests/` 全件Pass
  - Phase別必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52）Pass
  - Digest/Gitコミットハッシュ記録の存在・形式テストPass
  - EOL再現性テスト（digest固定/アーカイブAPT/constraints/マルチステージ）Pass

完了条件:
- Gate-1未達で先行不可ルール運用 100%
- 命名規約違反 0
- 固定重点検査の未実施回 0
- Gate-2必須テスト未実施 0

### M5: 監査証跡の完全実装（Data Integrity）
目的: 法的証拠レベルの再現性と改ざん検知を担保。

実施項目:
- 実行ログへコンテナDigestと `git rev-parse HEAD` を記録
- ログ/設定/スクリプトの相対パス強制
- 入出力/パラメータ/実行ログへSHA-256適用

完了条件:
- Digest記録欠落 0
- Gitコミットハッシュ記録欠落 0
- 絶対パス混入 0
- ハッシュ未付与対象 0

### M6: EOLコンテナ再現性標準の実装完了
目的: Python2.7/OpenCV2.4系の再現可能ビルドを恒常運用化。

実施項目:
- `FROM` digest固定（タグ運用禁止）
- EOL OSのAPTをアーカイブリポジトリへ切替
- `constraints.txt` による依存解決範囲固定
- OpenCV等C++ビルドのマルチステージ化
- 上記4項目の静的検査 + 実ビルド検証をCIへ追加

完了条件:
- digest未固定 `FROM` 0
- EOL対象APTソース不備 0
- constraints未適用pip install 0
- 単一ステージのC++ビルド経路 0
- EOL再現性検証未実施 0

---

## 2. 実行順序（固定）
1. ガバナンス固定（M1）
2. UI境界是正（M2）
3. インターフェース/型契約固定（M3）
4. 構造先行ゲート運用定着（M4, Gate-1先行でGate-2を実施）
5. 監査証跡完全実装（M5）
6. EOL再現性実装と検証更新（M6）

順序逸脱は原則禁止。設計変更が必要な場合は実装継続より先に設計成果物を更新する。

---

## 3. KPI（定量管理）
- 構造KPI:
  - `UI->Domain直参照 = 0`
  - `Port/Interface非経由通信 = 0`
  - `逆方向依存 = 0`
  - `循環依存 = 0`
- 再現性KPI:
  - `digest未固定FROM = 0`
  - `constraints未適用ビルド = 0`
- 監査証跡KPI:
  - `Digest/Git Hash記録欠落 = 0`
  - `ハッシュ未付与監査対象 = 0`
- 運用KPI:
  - `Gate-1未達でGate-2へ進行した件数 = 0`
  - `処方的でないREJECT件数 = 0`

---

## 4. リスク管理
1. UI改修によるイベント配線破断
- 対応: UIは導線のみ変更し、責務移管はUseCase側で吸収。

2. 型厳格化に伴う既存dict経路の移行失敗
- 対応: DTOアダプタを先行導入し、段階的にstrict化。

3. EOL外部要因でビルド不安定化
- 対応: digest + archive + constraints + multistage の4点セットを単位運用し、部分適用を禁止。

---

## 5. Done条件
1. `reference_standards` の4領域（ガバナンス/Docker/Data Integrity/UI規約）すべてで違反0。
2. `plan.md` のPhase 5/6/6.1〜6.4/6.51/6.52要件が、上記絶対基準に整合して達成済み。
3. 固定重点検査（`_run_container` / `_show_create_env_dialog`）で責務ゼロ化を確認済み。
4. Gate-2必須項目（`pytest tests/`、T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52、Digest/Git hash記録テスト、EOL再現性テスト）が全てPass。
5. Gate-1先行運用と監査証跡更新が継続可能な手順として定着済み。

---

## 6. 必須成果物（`plan.md` 対応）
- `artifacts/architecture_decoupling_assessment.md`（M2/M3）
- `artifacts/refactoring_proposal.md`（M2/M3）
- `artifacts/phase_6_51_baseline_inventory.md`（M2着手前ベースライン）
- `artifacts/phase_6_51_test_baseline.md`（M2着手前ベースライン）
- `artifacts/phase_6_52_logging_migration_report.md`（M5）
- `artifacts/phase_6_52_print_elimination_evidence.md`（M5）
- `artifacts/post_mortem_closure_checklist.md`（M4/M5/M6統合）
  - 既知欠陥2点の解消判定
  - Gate-1/Gate-2独立運用の実行記録
  - 差し戻し先判定（Architect/Implementer）の根拠
