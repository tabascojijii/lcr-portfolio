# LCR Roadmap (PM)

## 0. Purpose and Scope
- 本ロードマップは `docs/reference_standards.md` を絶対基準として、`docs/plan.md` の実装計画を実行順序・検証ゲート・完了条件へ展開する。
- 対象フェーズは Phase 5、Phase 6、Phase 6.1。
- 成功条件は、機能提供完了ではなく「再現性・監査可能性・アーキテクチャ整合性」の同時達成とする。

## 1. Absolute Standards (Non-Negotiable)
- Builder と Validator の入力境界を分離し、Validator 入力は `requirements` と `diff` のみに限定する。
- REJECT は処方的出力（失敗箇所、違反制約、観測証拠、修正ヒント、再検証条件、ルーティング先）を必須とする。
- `Dockerfile` の `FROM` はタグ指定を禁止し、SHA256 ダイジェスト固定を必須とする。
- EOL OS のAPTソースはアーカイブリポジトリへリダイレクトする。
- pip依存解決は `constraints.txt` 適用を必須とする。
- ネイティブビルドはマルチステージビルドを必須とする。
- 監査証跡として `all_input_files`、`all_output_files`、`all_parameter_files`、`audit_log_record` の4区分ハッシュを全件記録する。
- 実行ログへ `container_image_digest` と `git_commit_hash` を必須記録する。
- ログ・設定・監査出力のパスはすべてプロジェクトルート相対パスとし、絶対パスを禁止する。
- 依存方向は `UI -> UseCase -> Domain`、`Infrastructure -> Domain`、`Infrastructure -> UseCase(Port実装限定)` のみ許可する。
- `UseCase -> Qt`、`Domain -> Qt`、`Domain -> Infrastructure`、`UseCase -> Infrastructure(具象)`、`UI -> Domain` を禁止する。
- 層間通信は `abc.ABC` または `typing.Protocol` 経由のみ許可する。
- UIは Humble Object を厳守し、業務判断・複雑計算・業務フォーマット・永続化・外部I/O・Docker操作を実装しない。
- Qt命名規約としてシグナルは過去分詞形、スロットは動詞始まりを必須とする。

## 2. Delivery Roadmap

### 2.1 Phase 0: Governance Baseline
実施項目:
- 監査ログスキーマを固定し、必須フィールド欠落をFail化する。
- 依存方向検査をCIへ組み込み、禁止依存をFail化する。
- UI責務検査をCIへ組み込み、Humble Object違反をFail化する。
- ハッシュ4区分完全性検査をCIへ組み込み、欠落および絶対パス検出をFail化する。
- Docker再現性検査（digest、EOL archive、constraints、multi-stage）をCIへ組み込む。
- Builder/Validator分離運用とREJECTテンプレート完全性をCIで検査する。
- 監査-計画整合チェックをCIへ組み込み、`docs/audit_report.md` と `docs/plan.md` の制約差分をFail化する。
- UI命名規約検査（signal/slot）をCIへ組み込む。

完了条件:
- 監査証跡必須項目欠落 0件。
- 依存方向違反 0件。
- UI責務違反 0件。
- ハッシュ4区分欠落 0件。
- Docker再現性違反 0件。
- 監査-計画制約差分 0件。

### 2.2 Phase 1: Phase 5 (Capability and Guard)
実施項目:
- Capability Mapping UseCase を実装し、knowledge由来（推定）と実績由来（実証）を併存管理する。
- required imports と環境capability差分を算出する Mismatch Guard UseCase を実装する。
- 差分1件以上時は Run をHard Guardで無効化し、不足理由・推奨環境・作成導線を提示する。
- 適合環境0件時に作成フローへ強制遷移し、作成後に再起動なしで一覧を動的更新する。

完了条件:
- Guard未発火漏れ 0件。
- Guardバイパス経路 0件。
- 作成導線欠落 0件。
- T5-1、T5-2、T5-3、T5-4 全Pass。

### 2.3 Phase 2: Phase 6 (Environment Lifecycle)
実施項目:
- Environment Manager専用UIを提供し、一覧、検索/フィルタ、複数選択、削除プレビューを実装する。
- 一括削除の2段階確認を実装し、対象単位の部分失敗継続を保証する。
- 未使用抽出を最終利用日時・利用回数・保護フラグで判定する。
- cleanup対象を dangling/unused image に限定し、build cache/volume を除外する。
- メタデータ編集（内部ID不変、表示名/説明/タグ/分類/保護フラグ）と入力バリデーションを実装する。

完了条件:
- 削除安全性違反 0件。
- 保護フラグ無視 0件。
- 部分失敗時の処理中断 0件。
- T6-1、T6-2、T6-3、T6-4、T6-5、T6-6 全Pass。

### 2.4 Phase 3: Phase 6.1 (Decoupling Deliverables)
実施項目:
- `artifacts/architecture_decoupling_assessment.md` を作成し、`file path + class/function + violation type + evidence` 形式で違反を列挙する。
- `artifacts/refactoring_proposal.md` を作成し、移管先レイヤ、必要Port、段階移行（P0/P1/P2）、検証方法を明記する。

完了条件:
- 違反証拠欠落 0件。
- 移行手順欠落 0件。
- AC6.1-1、AC6.1-2、AC6.1-3、AC6.1-4 充足。

## 3. Cross-Phase Gates
- Functional Gate: `pytest tests/` 全件Pass。
- Structural Gate: 依存方向違反0、Port未経由境界越え0、UI禁止行為0、Qt命名規約違反0。
- Audit Gate: ハッシュ4区分欠落0、相対パス違反0、`container_image_digest` 欠落0、`git_commit_hash` 欠落0。
- Governance Gate: Builder/Validator分離違反0、監査入力境界違反0、REJECT必須要素欠落0。
- Synchronization Gate: `docs/audit_report.md` と `docs/plan.md` の制約差分0、かつ計画更新日が監査更新日を超えた場合は監査再実行完了。

## 4. Execution Order
1. Phase 0 を完了し、監査・設計・再現性の固定ゲートを先行導入する。
2. Phase 1（Phase 5）を UseCase 主導で実装する。
3. Phase 2（Phase 6）を専用UI分離方針で実装する。
4. Phase 3（Phase 6.1）で違反可視化と移行計画を成果物化する。
5. 各Phaseは `Plan -> Functional -> Structural -> Audit -> Governance` の順にゲート通過を確認する。

## 5. Risk Controls
- RC-1（ハッシュ対象曖昧）: 4区分スキーマ固定と欠落Failで封じ込める。
- RC-2（UseCase->Qt逆流）: 明示禁止とCI静的検査Failで封じ込める。
- RC-3（UIロジック流入）: UI禁止行為検査とレビュー基準で封じ込める。
- 監査同期不整合: 監査-計画差分検査を常時実行し、差分発生時は実装ジョブ開始前に停止する。

## 6. Definition of Done
- Phase 5、Phase 6、Phase 6.1 の受け入れ基準を満たす。
- `docs/reference_standards.md` の絶対基準違反が0件である。
- EMCSメトリクス（依存方向、UI責務、複雑度、監査証跡、Docker再現性）が全て閾値内である。
- テスト、構造、監査、ガバナンス、同期の全ゲートが連続Passである。
- 最新 `docs/audit_report.md` と本ロードマップ運用前提が整合している。

## 7. Explicit Prohibitions
- 曖昧語（例: 主要、可能なら、必要に応じて）による基準緩和を禁止する。
- 設計違反を実装で迂回する運用を禁止する。
- 本作業において `git commit`、`git push`、`git merge`、`git rebase` を含むGit操作を実施しない。
