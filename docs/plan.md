# Implementation Plan (Architect)

## 0. Scope and Objective
- 本計画は `docs/core_philosophy.md`、`docs/requirements.md`、`docs/reference_standards.md` に完全準拠し、`docs/post_mortem.md` で特定された構造的欠陥を是正する。
- `docs/audit_report.md` の最新判定を実行前ゲートとして取り込み、PASS時も是正項目の恒久化を継続する。
- 2026-05-04時点の `docs/audit_report.md` は **PASS** であるため、新規是正ではなく「過去REJECT起因制約の固定化」と「監査-計画整合の継続検証」を目的化する。
- 対象は Phase 5 / Phase 6 / Phase 6.1。
- 成功条件は「機能実現」ではなく「監査可能性・再現可能性・疎結合性」の同時達成。
- 本計画に曖昧語（例: 主要、必要に応じて、可能なら）を使用しない。

## 1. Non-Negotiable Constraints (Audit Hard Gates)

### 1.1 Dependency Rule
- 許可依存:
  - `UI -> UseCase`
  - `UseCase -> Domain`
  - `Infrastructure -> Domain`
  - `Infrastructure -> UseCase`（UseCase/Domainで定義されたPort実装に限定）
- 禁止依存:
  - `UseCase -> Qt`（明示禁止）
  - `Domain -> Qt`
  - `Domain -> Infrastructure`
  - `UseCase -> Infrastructure`（具象直接依存禁止）
  - `UI -> Domain`（直接参照禁止）
- 境界越え通信は `abc.ABC` / `typing.Protocol` 経由のみ許可。

### 1.2 Humble Object Rule
- UI層（Window/Dialog/Widget）で以下を禁止:
  - 業務判断・業務分岐
  - 永続化処理、外部I/O、Docker操作
  - 複雑計算
  - 業務意味を持つフォーマット処理
- UI層の許可責務:
  - 入力受理
  - 表示更新
  - UseCase呼び出し

### 1.3 Data Integrity Rule
- ハッシュ対象は以下4区分を全件必須とする:
  - `all_input_files`
  - `all_output_files`
  - `all_parameter_files`
  - `audit_log_record`
- 実行ログ必須記録:
  - コンテナイメージダイジェスト
  - Gitコミットハッシュ（`git rev-parse HEAD`）
- パスは全てプロジェクトルート相対パス。絶対パスを検出した場合は fail-fast で処理中断。

### 1.4 Docker Reproducibility Rule
- `Dockerfile` の `FROM` はタグ指定を禁止し、SHA256ダイジェスト指定を必須とする。
- EOL OSのAPTソースはアーカイブリポジトリへリダイレクトを必須とする。
- pip依存解決は `constraints.txt` 適用を必須とし、無制約解決を禁止する。
- OpenCV等のネイティブビルドはマルチステージビルドを必須とする。

### 1.5 Audit Governance Separation Rule
- Builder（実装）とValidator（監査）は入力境界を分離する。
- Auditorの許可入力は `requirements` と `diff` のみとし、実装時の思考過程・内部メモへのアクセスを禁止する。
- REJECT時は「失敗箇所・違反制約・観測証拠・修正ヒント・再検証条件・ルーティング先」を必須出力とする。

### 1.6 Audit Synchronization Rule
- 監査結果は常に最新の `docs/audit_report.md` を正とし、過去のREJECT分析は再発防止制約として維持する。
- PASS判定時も、過去REJECT起因の制約（RC-1〜RC-3）は削除しない。
- 監査文書と計画文書に不整合がある場合は、実装着手前に `plan.md` を先に更新する。
- 監査が「重大指摘なし」の場合も、RC-1〜RC-3に対応する検査項目（ハッシュ4区分、`UseCase -> Qt` 禁止、UI複雑計算/業務フォーマット禁止）を縮退しない。
- 監査判定の更新日と計画更新日を比較し、計画更新日が新しい場合は監査再実行を必須とする。

## 2. Traceability Matrix (Requirement -> Implementation -> Test -> Gate)
- R5-1 (Capability Mapping):
  - 実装: Capability統合UseCase（knowledge=推定、execution=実証）
  - テスト: T5-1補助（表示ソース区別）、T5-2
  - ゲート: UIに推定/実証識別が存在
- R5-2 (Mismatch Guard):
  - 実装: required imports差分UseCase + Hard Guard
  - テスト: T5-1
  - ゲート: 差分1件以上でRun無効、強制実行経路0件
- R5-3 (Forced Creation Flow):
  - 実装: 適合環境なし時に作成ダイアログ遷移、初期候補自動投入、作成後Dynamic Refresh
  - テスト: T5-3, T5-4
  - ゲート: 再起動不要で実行可能化
- R6-1〜R6-6:
  - 実装: Environment Manager専用UI、2段階確認、一括削除継続、未使用抽出、メタ編集、監査ログ
  - テスト: T6-1〜T6-6
  - ゲート: 受け入れ基準AC6-1〜AC6-7一致
- Phase 6.1:
  - 実装: `artifacts/architecture_decoupling_assessment.md`、`artifacts/refactoring_proposal.md`
  - テスト: 境界違反検出テスト、依存グラフ検査
  - ゲート: AC6.1-1〜AC6.1-4一致

## 3. Execution Strategy
- 一括置換を禁止し、後方互換を保った段階移行を実施する。
- 各フェーズは以下の順で完了判定する:
  - Plan Gate（設計制約の明文化完了）
  - Functional Gate
  - Structural Gate
  - Audit Gate
- REJECTルーティング固定:
  - 設計不備: `REJECT_TO_ARCHITECT`
  - 実装不備: `REJECT_TO_IMPLEMENT`

## 4. Work Breakdown

### 4.1 P0: Governance Baseline (先行必須)
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

2. 依存方向検査のCI組み込み
- `UseCase -> Qt` を静的検査でFail。
- `UI -> Domain` 直接依存をFail。
- Port未経由の境界越えをFail。

3. UI責務検査のCI組み込み
- UI層におけるI/O直接実行をFail。
- UI層における複雑計算/業務フォーマット処理をFail。

4. ハッシュ全件性検査のCI組み込み
- 4区分のいずれか欠落時にFail。
- 絶対パス検出時にFail。

5. Docker再現性検査のCI組み込み
- `FROM` のダイジェスト固定違反をFail。
- EOL向けAPTアーカイブ未設定をFail。
- `constraints.txt` 未使用のpip解決をFail。
- マルチステージビルド未適用をFail。

6. 監査分離運用の固定
- 監査ジョブは `requirements` と `diff` のみを入力として実行する。
- 実装ジョブ成果物への付加情報は監査入力へ渡さない。
- REJECTテンプレート必須項目欠落時は監査ジョブをFail。

8. 監査-計画整合チェックのCI組み込み
- `docs/audit_report.md` と `docs/plan.md` の制約差分を機械的に検査する。
- 差分が1件以上ある場合は実装ジョブ開始前にFail。
- PASS判定の有無に関わらず、差分検査は常時実行する。

7. UI命名規約検査のCI組み込み
- シグナル名は過去分詞形（例: `*Changed`, `*Completed`）以外をFail。
- スロット名は動詞始まり（例: `update_*`, `load_*`, `apply_*`）以外をFail。

### 4.2 P1: Phase 5 Implementation
1. Capability Mapping UseCase
- import名基準でcapabilityを構築。
- knowledge由来（推定）と実績由来（実証）を同時保持。

2. Mismatch Guard UseCase
- required importsとの差分を算出。
- 差分が1件以上なら `Run` を無効化。
- 警告モデルに不足一覧・不足理由・推奨環境・作成導線を格納。

3. Forced Creation Flow
- 適合環境0件時は作成ダイアログへ遷移。
- 初期候補は `user_knowledge.json` 優先、不足分は既定候補で補完。
- 作成完了イベントで一覧再読込し、即時実行可能状態へ遷移。

### 4.3 P1: Phase 6 Implementation
1. Environment Manager専用ダイアログ
- 一覧、検索/フィルタ、複数選択、削除プレビュー（件数/対象名/容量）を提供。

2. 一括削除
- 対象は定義JSON + Docker image。
- 2段階確認未完了では削除処理開始禁止。
- 対象単位で独立実行し、失敗時も残件継続。

3. 未使用抽出
- 最終利用日時 + 利用回数 + 保護フラグで判定。
- 保護フラグ対象は候補除外。

4. クリーンアップ
- dangling / unused image のみ対象。
- build cache / volume は対象外。

5. メタデータ編集
- 内部ID不変。
- 表示名/説明/タグ/分類/保護フラグを編集可能。
- 空値・長さ・禁止文字のバリデーションを適用。

### 4.4 P2: Phase 6.1 Deliverables
1. `artifacts/architecture_decoupling_assessment.md`
- 違反を `file path + class/function + violation type + evidence` 形式で列挙。

2. `artifacts/refactoring_proposal.md`
- 各違反の移管先レイヤ、必要Port、段階移行（P0/P1/P2）、検証法を定義。

## 5. Verification Plan

### 5.1 Functional Tests
- 必須: `pytest tests/` 全件Pass。
- 最低追加:
  - T5-1 Guard発火テスト
  - T5-2 適合環境実行テスト
  - T5-3 強制作成導線テスト
  - T5-4 作成後即時反映テスト
  - T6-1 2段階確認ガードテスト
  - T6-2 未使用判定テスト
  - T6-3 部分失敗継続テスト
  - T6-4 メタ編集/内部ID不変テスト
  - T6-5 クリーンアップ範囲テスト
  - T6-6 監査ログ完全性テスト

### 5.2 Structural Tests
- 依存方向違反0件（`UseCase -> Qt` 含む）。
- UI禁止行為違反0件（業務判断/I-O/複雑計算/業務フォーマット）。
- Port未経由境界越え0件。
- シグナル/スロット命名規約違反0件。

### 5.4 Objective Audit Metrics (EMCS)
- M1: 依存方向違反件数
  - 測定: 静的依存解析
  - 閾値: 0件
  - 判定: 1件以上でREJECT
- M2: SRP違反件数（UIクラス）
  - 測定: UIクラス内の業務判断/永続化/I-O/複雑計算/業務フォーマット検出
  - 閾値: 0件
  - 判定: 1件以上でREJECT
- M3: 複雑度超過件数（UseCase/Domain）
  - 測定: サイクロマティック複雑度
  - 閾値: 10超の関数 0件
  - 判定: 1件以上でREJECT
- M4: 監査証跡欠落件数
  - 測定: ハッシュ4区分 + digest + git hash + 相対パスの欠落検査
  - 閾値: 0件
  - 判定: 1件以上でREJECT
- M5: Docker再現性違反件数
  - 測定: ダイジェスト固定 / APTアーカイブ / constraints / マルチステージの4項目検査
  - 閾値: 0件
  - 判定: 1件以上でREJECT

### 5.3 Audit Tests
- ハッシュ4区分の欠落0件。
- パス相対化違反0件。
- image digest / git hash 欠落0件。

## 6. Risk Elimination (Post Mortem Direct Actions)
- RC-1（ハッシュ対象曖昧）対策:
  - 全件必須4区分をスキーマに固定し、欠落時Fail。
- RC-2（UseCase->Qt 禁止不足）対策:
  - 明示禁止 + CI検査 + 違反時マージ不可。
- RC-3（UI計算/整形の流入）対策:
  - UI禁止行為として明文化 + 検査ゲート化。
- 監査同期不整合対策:
  - `audit_report.md` の判定と `plan.md` 制約セットの差分をレビューし、差分が1件でもあれば実装着手を停止する。
- ループ再発防止:
  - 設計不備は実装工程へ送らず `REJECT_TO_ARCHITECT` へ直送。

## 7. Definition of Done
- Phase 5/6/6.1 の受け入れ基準を満たす。
- 1章のHard Constraint違反が0件。
- `pytest tests/` 全件Pass。
- 監査で `REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT` 要因が0件。
- 監査証跡に再現性必須情報（hash4区分、digest、git hash、相対パス）が欠落しない。
- Docker再現性4要件（ダイジェスト固定、APTアーカイブ、constraints、マルチステージ）が全件充足。
- 監査運用でBuilder/Validator分離が維持され、入力境界違反が0件。
- EMCSメトリクス（M1-M5）が全て閾値内。
- PyQt/PySideシグナル・スロット命名規約違反が0件。
- 最新 `docs/audit_report.md` と `docs/plan.md` の制約整合差分が0件。

## 8. Explicit Prohibition
- 本作業中の `git commit` を禁止する。
