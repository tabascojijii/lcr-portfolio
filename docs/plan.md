# Implementation Plan (Architect)

## 0. Mission
- 本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md`、`docs/post_mortem.md` を統合した実装計画である。
- 目的は Phase 5 / Phase 6 / Phase 6.1 を、監査可能性・再現可能性・疎結合性の3条件を同時満足して完了させること。
- 本計画の最優先は「過去の構造的欠陥（RC-1〜RC-3）の再発防止」であり、機能追加はその後に従属する。
- `docs/audit_report.md` が PASS であっても、RC-1〜RC-3 の再流入防止を目的に本計画の Hard Constraints と検証ゲートは緩和しない（監査結果は最低条件であり、免除条件ではない）。

## 1. Post Mortem Driven Hard Constraints

### 1.1 RC-1: Data Integrity 全件固定
- ハッシュ対象は次の4区分を全件必須とし、1件欠落で Fail とする。
  - `all_input_files`
  - `all_output_files`
  - `all_parameter_files`
  - `audit_log_record`
- 実行ログには次を必須記録する。
  - `container_image_digest`
  - `git_commit_hash`（`git rev-parse HEAD`）
- パスは全てプロジェクトルート相対パス。絶対パス検出時は fail-fast。

### 1.2 RC-2: Dependency Boundary 固定
- 許可依存方向は `UI -> UseCase -> Domain`。
- `Infrastructure` は `UseCase/Domain` で定義された Port を実装する方向のみ許可。
- 次を明示禁止とする。
  - `UseCase -> Qt`
  - `Domain -> Qt`
  - `Domain -> Infrastructure`
  - `UI -> Domain`（直接参照）
  - `UseCase -> Infrastructure`（具象直接依存）
- 境界越え通信は `abc.ABC` / `typing.Protocol` の Port 経由のみ許可。

### 1.3 RC-3: Humble Object 行為禁止 固定
- UIクラス（Window/Dialog/Widget）は次を禁止。
  - 業務判断・業務分岐
  - 永続化処理・外部I/O・Docker操作
  - 複雑計算
  - 業務意味を持つフォーマット処理
- UIクラスは次のみ許可。
  - 入力受理
  - 表示更新
  - UseCase呼び出し

### 1.4 RC-4: Signal/Slot Naming 固定
- PyQt/PySide の命名規約を必須化し、逸脱は Fail とする。
  - シグナル名: 過去分詞形（例: `dataChanged`）
  - スロット名: 動作を示す動詞（例: `update_display`）
- 命名規約はレビュー観点ではなく機械検証対象とし、CI/Lintで検出する。

## 2. Architecture and Reproducibility Rules

### 2.1 Docker 再現性
- `Dockerfile` の `FROM` は SHA256 ダイジェスト固定必須（タグ指定禁止）。
- EOL OS は APT をアーカイブリポジトリへリダイレクト必須。
- pip依存解決は `constraints.txt` 必須。
- OpenCV等のネイティブビルドはマルチステージビルド必須。

### 2.2 監査運用分離
- Builder と Validator を入力境界で分離する。
- Auditor は `requirements` と `diff` のみを入力にする。
- REJECT出力必須項目:
  - 失敗箇所
  - 違反制約
  - 観測証拠
  - 修正ヒント
  - 再検証条件
  - ルーティング先（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）

## 3. Requirement Traceability Matrix
- R5-1: Capability Mapping
  - 実装: import名基準の capability 統合 UseCase（knowledge=推定、execution=実証）
  - テスト: capability表示の推定/実証識別テスト
- R5-2: Mismatch Guard
  - 実装: required imports 差分 UseCase、差分1件以上で `Run` 無効
  - テスト: mismatch時 `Run` 無効、強制実行不可
- R5-3: Forced Creation
  - 実装: 適合環境0件で作成ダイアログ遷移、候補自動投入、作成後即時反映
  - テスト: 導線遷移、反映後再起動不要実行
- R6-1〜R6-6
  - 実装: Environment Manager専用UI、2段階確認、一括削除継続、未使用抽出、メタ編集、監査ログ
  - テスト: T6-1〜T6-6
- Phase 6.1
  - 成果物: `artifacts/architecture_decoupling_assessment.md`、`artifacts/refactoring_proposal.md`
  - 検証: importグラフ、禁止依存件数、循環依存件数、変更影響テスト

## 4. Execution Plan (Order is Mandatory)

### P0: Governance Baseline（実装前必須）
1. 監査ログスキーマ固定
- 必須フィールド:
  - `operation_type`
  - `timestamp`
  - `targets`
  - `result`
  - `released_size`
  - `reason`
  - `required_imports`
  - `environment_capability`
  - `mismatch_result`
  - `guard_triggered`
  - `hashes.all_input_files`
  - `hashes.all_output_files`
  - `hashes.all_parameter_files`
  - `hashes.audit_log_record`
  - `container_image_digest`
  - `git_commit_hash`
2. 依存方向CIゲート追加（`UseCase -> Qt` 含む禁止依存）
3. UI責務CIゲート追加（業務判断/I-O/複雑計算/業務フォーマット禁止）
4. ハッシュ全件性CIゲート追加（4区分欠落・絶対パスをFail）
5. Docker再現性CIゲート追加（digest/APT archive/constraints/multi-stage）
6. 監査入力境界ゲート追加（Builder/Validator分離）
7. 監査テンプレート必須項目チェック追加（欠落時 Fail）
8. Signal/Slot命名CIゲート追加（Signal=過去分詞、Slot=動詞）
9. 実装着手前アーキテクト確認を追加（以下が1件でも未充足なら着手禁止）
  - RC-1: hash4区分の全件定義が plan / schema / test で一致
  - RC-2: 禁止依存（`UseCase -> Qt` 含む）が lint / test / review checklist で一致
  - RC-3: UI禁止行為（複雑計算・業務フォーマット含む）が静的検査ルール化済み
  - 監査ルーティング分離（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）がテンプレート化済み

### P1: Phase 5 実装
1. Capability Mapping UseCase 実装
2. Mismatch Guard UseCase 実装
3. Forced Creation Flow 実装
4. 監査ログ連携（required imports/capability/mismatch/guard）

### P2: Phase 6 実装
1. Environment Manager ダイアログ実装
2. 2段階確認付き一括削除実装（部分失敗継続）
3. 未使用抽出ロジック実装（最終利用日時+利用回数+保護フラグ）
4. dangling/unused image のみクリーンアップ実装
5. メタデータ編集実装（内部ID不変）
6. 削除/編集/クリーンアップ監査ログ実装

### P3: Phase 6.1 成果物作成
1. `artifacts/architecture_decoupling_assessment.md`
- `file path + class/function + violation type + evidence` 形式で違反列挙
- `UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数を提示
2. `artifacts/refactoring_proposal.md`
- P0/P1/P2優先度で段階移行計画
- Port設計、移管先レイヤ、後方互換維持策、テスト戦略、リスク対策を提示

## 5. Verification Plan

### 5.1 Functional Gate
- 必須: `pytest tests/` 全件Pass
- 最低追加テスト:
  - T5-1 mismatch時 `Run` 無効化
  - T5-2 適合時 `Run` 有効 + 実行可能
  - T5-3 適合環境なし時 作成導線遷移
  - T5-4 作成後即時反映
  - T6-1 2段階確認未完了時 削除不可
  - T6-2 未使用判定（日時+回数+保護フラグ）
  - T6-3 一括削除部分失敗継続
  - T6-4 編集時 内部ID不変
  - T6-5 クリーンアップ対象限定（dangling/unusedのみ）
  - T6-6 監査ログ完全性

### 5.2 Structural Gate
- 禁止依存0件（`UseCase -> Qt` を含む）
- UI禁止行為0件（業務判断/I-O/複雑計算/業務フォーマット）
- Port未経由境界越え0件
- 循環依存0件
- Signal/Slot命名規約違反0件（Signal=過去分詞、Slot=動詞）

### 5.3 Audit Gate
- ハッシュ4区分欠落0件
- 相対パス違反0件
- `container_image_digest` 欠落0件
- `git_commit_hash` 欠落0件
- REJECTテンプレート必須項目欠落0件

### 5.4 Objective Metrics (EMCS)
- M1: 依存方向違反件数 = 0
- M2: UI SRP違反件数 = 0
- M3: 複雑度超過（CC > 10）件数 = 0
- M4: 監査証跡欠落件数 = 0
- M5: Docker再現性違反件数 = 0
- M6: Signal/Slot命名規約違反件数 = 0

## 6. Loop Prevention Protocol
- 設計不備を検出した場合は `REJECT_TO_ARCHITECT` に固定し、実装工程へ送らない。
- 実装不備を検出した場合は `REJECT_TO_IMPLEMENT` に固定する。
- `docs/plan.md` と監査基準に差分がある限り実装着手を禁止する。
- PASS時も RC-1〜RC-3 の制約を削除・緩和しない。
- Auditor が「指摘なし（PASS）」を返した場合でも、直近の post mortem 起因制約（RC-1〜RC-3）に関する非回帰確認を毎回実施する。
- 非回帰確認で1件でも未充足があれば、監査総合判定に関わらず `REJECT_TO_ARCHITECT` として設計へ差し戻す。

## 7. Definition of Done
- Phase 5 / Phase 6 / Phase 6.1 の受け入れ基準を満たす。
- Section 1〜2 の Hard Constraints 違反が0件。
- `pytest tests/` 全件Pass。
- EMCS（M1〜M6）全て閾値内。
- Signal/Slot命名規約違反0件（Signal=過去分詞、Slot=動詞）。
- 監査証跡（hash4区分、digest、git hash、相対パス）が全件充足。
- Builder/Validator分離の入力境界違反0件。

## 8. Explicit Prohibition
- 本作業では `git commit` を実行しない。
