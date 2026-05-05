# 実装計画（Architect）

## 0. 文書目的
本計画は `docs/core_philosophy.md`・`docs/requirements.md`・`docs/reference_standards.md`・`docs/post_mortem.md` を統合し、Phase 6.1 で発生した「監査差し戻し反復（構造不適合ループ）」を再発不能化するための設計主導計画である。

適用範囲:
- Phase 5
- Phase 6
- Phase 6.1〜6.4
- Phase 6.51〜6.56

## 1. 失敗分析起点の設計制約（破ってはならない制約）
`docs/post_mortem.md` の RC-1〜RC-3 を、以下の制約として固定する。

1. RC-1 対策（境界強制）
- 依存方向は `UI -> UseCase -> Domain` を許可し、Infrastructure は外側実装層として内側（UseCase/Domain）が定義した Port に依存して実装する。
- `Domain` は `Infrastructure` を import してはならない（0件固定、違反は Gate-S Fail）。
- `Port/Repository` の **定義主体は内側（UseCase/Domain）**、**実装主体は Infrastructure** に固定する。
- UI から Domain 直接参照は 0 件を固定目標ではなく「ビルド失敗条件」にする。
- UI から外部I/O（file/network/subprocess）実行を禁止し、Port/Gateway/Repository 経由のみ許可。

2. RC-2 対策（差し戻し先誤り防止）
- 監査所見に `原因層: 設計 or 実装` を必須記載。
- 設計起因の不適合は `REJECT_TO_ARCHITECT` を強制。
- 同一理由が2回連続で再発した場合、実装継続を停止し設計レビューへ強制遷移。

3. RC-3 対策（品質ゲート混線防止）
- Gate-S（構造）と Gate-F（機能）を独立運用。
- Gate-S 未達なら Gate-F 合格でも進行禁止。

## 2. アーキテクチャ固定仕様

### 2.1 UI責務の固定
UI は以下のみ許可:
- 入力受理
- 表示更新
- ユーザー確認（2段階確認含む）

UI で禁止:
- 業務判断（ランタイム判定・不足依存判定・削除対象判定）
- 永続化処理
- 直接 subprocess 呼び出し

### 2.2 MainWindow 是正対象（最優先）
- `MainWindow._run_container`
- `MainWindow._show_create_env_dialog`

責務移管先:
- `RunPreparationUseCase`
- `EnvironmentCreationProposalUseCase`
- `LifecycleManagementUseCase`

完了条件:
- 上記2メソッドから業務分岐・データ加工・環境判定ロジックが消失していること。

### 2.3 Port 契約
必須Port:
- `EnvironmentCapabilityPort`
- `EnvironmentRepositoryPort`
- `ContainerRuntimePort`
- `AuditLogPort`
- `ImageCleanupPort`
- `KnowledgeMappingPort`
- `PackageLookupPort`

契約規則:
- `Protocol` または `ABC` を使用。
- 公開メソッドの引数/戻り値型を必須化。
- DTO境界は Pydantic v2 strict を必須化。

## 3. フェーズ実行順（固定）

1. Phase 6.51 ベースライン固定
- 責務マップ・副作用インベントリ・対象範囲固定。

2. Phase 6.1 構造違反除去（最優先）
- UI->Domain 直参照 0 件。
- Port バイパス 0 件。

3. Phase 5 実行ガード完成
- mismatch 時 Run 無効化（Hard Guard）。
- 適合環境なし時の強制作成導線。

4. Phase 6 ライフサイクル管理完成
- Environment Manager 専用UI。
- 一括削除2段階確認。
- 部分失敗継続。

5. Phase 6.2〜6.4 型・契約・回帰固定
- Pydantic strict。
- mypy gate。
- Port/DTO/Audit 契約テスト。

6. Phase 6.52〜6.56 副作用分離・責務分割仕上げ
- `print` 排除。
- Analyzer/Container の副作用 Port 化。
- ContainerManager 薄化。

## 4. 品質ゲート（必須）

### 4.1 Gate-S（構造）
Fail条件（1件でもあれば失敗）:
- UI->Domain direct import
- 逆方向依存
- 循環依存
- Port未経由呼び出し
- `MainWindow._run_container` に業務判断残存
- `MainWindow._show_create_env_dialog` に業務判断残存
- UI層からQt以外の外側依存規約違反
- PyQt/PySide 命名規約違反（Signal が過去分詞形でない、Slot が動詞開始でない）
- EMCSメトリクス閾値超過（下記 4.3 を参照）

Gate-S は `REJECT_TO_ARCHITECT` 判定を返す。

### 4.2 Gate-F（機能）
Pass条件:
- `pytest tests/` 全件Pass
- 各フェーズ必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51〜）Pass
- 監査ログ完全性（相対パス + ハッシュ）Pass

### 4.3 EMCS 客観メトリクス（Gate-S判定基準）
測定対象とFail条件:
- E（Encapsulation/SRP）:
  - UI層メソッド行数上限 60 行。超過1件でFail。
  - UI層メソッドの分岐数（`if/for/while/match`）上限 5。超過1件でFail。
- M（Modularity/Dependency）:
  - `UI->Domain` 直参照 0 件固定。1件でもFail。
  - 逆方向依存 0 件、循環依存 0 件。1件でもFail。
  - Port未経由境界越え 0 件。1件でもFail。
- C（Complexity）:
  - UseCase/Orchestrator のサイクロマティック複雑度上限 10。超過1件でFail。
- S（Safety/Auditability）:
  - 監査必須キー欠落 0 件。
  - 相対パス違反 0 件。
  - 上記いずれか1件でもFail。

判定運用:
- Gate-S は定量閾値に基づく機械判定を優先し、主観裁量での合格を禁止する。
- 閾値超過時は Auditor が `違反メトリクス/実測値/閾値/修正最小単位` を必須記録する。

## 5. 監査証跡の固定要件

監査ログ必須項目:
- `container_image_digest`
- `git_commit_hash`
- `input_sha256`
- `output_sha256`
- `parameter_sha256`
- `execution_log_sha256`
- `path_mode`（relative 強制結果）

Gitハッシュ記録方式（固定）:
- `git_commit_hash` は必ず `git rev-parse HEAD` の実行結果を記録する。
- 取得失敗時は監査ログを不完全として Gate-F Fail にする。

Docker再現性必須:
- `FROM @sha256` 固定
- EOL apt archive 利用
- `constraints.txt` 使用
- マルチステージビルド

## 6. 実行停止条件（ループ防止）
以下のいずれかで実装を停止し、Architect 再設計へ戻す。

1. 同一構造違反で2回連続REJECT
2. Gate-FはPassだがGate-SがFail
3. UI責務違反の再流入を検知
4. Port追加なしにUIの境界越えを回避しようとしている

## 7. 役割分担（責任境界）

Architect:
- 境界設計、Port定義、移管順序、完了条件を確定。
- 構造違反時の修正戦略を提示。

Implementer:
- Architect の固定設計に従って実装。
- 設計未確定領域には着手しない。

Auditor:
- EMCS観点で客観評価。
- REJECT時は「違反箇所・違反規約・最小修正指示・原因層・差し戻し先」を必須記載。
- レビュー入力は「要件定義 + 生成差分（Diff） + テスト結果」のみに限定し、Implementerの思考過程・補助メモ・下書きの参照を禁止する。
- 上記入力制約違反があった監査は無効とし、差分限定条件で再監査する。

## 8. 成果物（最低限）
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`
- `artifacts/post_mortem_closure_checklist.md`
- `artifacts/audit_reject_template.md`
- `artifacts/qt_naming_inventory.md`
- `artifacts/emcs_metrics_report.md`

`post_mortem_closure_checklist.md` 必須項目:
- RC-1〜RC-3 閉塞証跡
- Gate-S/Gate-F 独立運用記録
- REJECT先判定記録（Architect/Implementer）

`qt_naming_inventory.md` 必須項目:
- 既存Signal/Slot名の棚卸し一覧（ファイル、識別子、判定）
- 命名規約違反一覧と修正方針
- 「違反0件」到達証跡

## 9. Definition of Done
以下を同一リビジョンで満たした場合のみ完了。

1. Gate-S Pass
2. Gate-F Pass
3. `MainWindow._run_container` / `_show_create_env_dialog` の責務移管完了
4. UI->Domain 直参照 0 件
5. Port バイパス 0 件
6. 監査証跡（相対パス・ハッシュ・digest・git hash）完全
7. post_mortem 再発防止証跡が成果物として保存済み
8. PyQt/PySide 命名規約違反 0 件（Signal過去分詞、Slot動詞）
9. Builder/Validator 分離運用（差分限定レビュー）が監査記録で確認可能
