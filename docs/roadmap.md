# LCR Roadmap（PM）

## 0. 位置づけ
本ロードマップは `docs/reference_standards.md` を絶対基準として策定する。`docs/plan.md` は実装計画の詳細化ソースとして参照し、矛盾時は常に `reference_standards` を優先する。

## 1. 絶対遵守原則（Non-Negotiable）
1. 監査・実装ガバナンス
- Builder/Validator 分離を厳守する。
- 監査判定は要件と差分（Diff）に限定し、主観評価を禁止する。
- REJECT は処方的（失敗箇所・違反制約・修正指示）であることを必須化する。

2. Docker 再現性
- `FROM` はタグ禁止、`@sha256:` ダイジェスト固定を必須化する。
- EOL OS のAPTは `old-releases.ubuntu.com` / `archive.debian.org` へ切替える。
- `constraints.txt` により依存解決範囲を固定する。
- C/C++ビルド依存イメージはマルチステージビルドを強制する。

3. Data Integrity
- `container_image_digest` と `git_commit_hash` を必須記録する。
- 入出力・パラメータ・実行ログの SHA-256 記録を必須化する。
- 記録パスはプロジェクトルート基準の相対パスのみ許可する。

4. UI/アーキテクチャ
- Humble Object パターンを適用し、UI責務を最小化する。
- 依存方向は `UI -> UseCase -> Domain -> Infrastructure` のみ許可する。
- UseCase/Domain から Qt 依存を禁止する。
- 層間通信は `abc.ABC` または `typing.Protocol` を必須化する。
- Qt命名規約（Signal=過去分詞、Slot=動詞開始）違反は失敗扱いとする。

## 2. ロードマップ全体像
- Phase A: 6.51 ベースライン固定
- Phase B: 6.1 境界再配線（最優先）
- Phase C: Phase 5 Guardrails 固定
- Phase D: Phase 6 Lifecycle 固定
- Phase E: 6.2〜6.4 契約・回帰固定
- Phase F: 6.52 Logging 標準化
- Phase G: 6.53 Analyzer 境界分離
- Phase H: Docker再現性標準固定

順序原則:
1. Gate-S（構造）成立前に Gate-F（機能）合格のみで進捗化しない。
2. Phase B を最優先し、UI責務過多と Port バイパスを構造的に排除する。
3. Docker再現性とData Integrityはリリース直前ではなく並行実装で前倒し固定する。

## 3. フェーズ計画
### Phase A: 6.51 ベースライン固定
目的:
- 責務マップ、副作用インベントリ、現状テスト結果を証跡化する。

主要成果物:
- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_51_test_baseline.md`

完了条件:
- 対象/非対象境界が監査可能な形で固定されている。

### Phase B: 6.1 境界再配線（最優先）
目的:
- `MainWindow._run_container` と `MainWindow._show_create_env_dialog` の業務判断をUseCaseへ移管する。

主要施策:
- `RunPreparationUseCase` に実行可否判定を集約。
- `EnvironmentCreationProposalUseCase` に環境提案ロジックを集約。
- `LifecycleManagementUseCase` に削除/クリーンアップ判断を集約。

完了条件:
- UIからDomain/Infrastructure直接参照 0。
- Port未経由境界越え 0。
- 対象2関数のUI業務ロジック 0。

### Phase C: Phase 5 Guardrails 固定
目的:
- capability可視化と mismatch 時ハードガードを実装する。

完了条件:
- AC-1〜AC-5, T5-1〜T5-4 充足。

### Phase D: Phase 6 Lifecycle 固定
目的:
- 環境削除・クリーンアップ・監査記録を運用可能な形で固定する。

完了条件:
- AC6-1〜AC6-7, T6-1〜T6-6 充足。

### Phase E: 6.2〜6.4 契約・回帰固定
目的:
- DTO strict化、型検証、契約テストを固定する。

主要施策:
- Pydantic v2 strict を監査DTO→RuntimeDTO→環境DTOの順で導入。
- `mypy` を主ゲート化し `type: ignore` は理由コメント必須化。
- Port/DTO/Audit の contract test と golden regression 整備。

完了条件:
- AC6.2-1〜AC6.2-5, AC6.3-1〜AC6.3-4, AC6.4-1〜AC6.4-4 充足。

### Phase F: 6.52 Logging 標準化
目的:
- 対象コア領域の `print(` を除去し、例外経路のログレベルを統一する。

完了条件:
- AC6.52-1〜AC6.52-5 充足。

### Phase G: 6.53 Analyzer 境界分離
目的:
- `CodeAnalyzer` から直接 I/O を排除し、Port経由へ統一する。

主要施策:
- PyPI照会を `PackageLookupPort` 経由へ移管。
- mapping読込を Repository/Port 経由へ移管。

完了条件:
- AC6.53-1〜AC6.53-5 充足。

### Phase H: Docker再現性標準固定
目的:
- EOLスタックを含む全Dockerビルドの再現性を業界標準で固定する。

完了条件:
- ダイジェスト未固定 `FROM` = 0。
- EOL時APTアーカイブ未設定 = 0。
- `constraints.txt` 未使用ビルド = 0。
- C/C++ビルド依存でマルチステージ未適用 = 0。

証跡:
- `artifacts/docker_reproducibility_checklist.md`
- `artifacts/docker_digest_lock_evidence.md`
- `artifacts/docker_multistage_evidence.md`

## 4. 品質ゲート運用
### Gate-S（構造）
必須:
- UI->Domain直参照 = 0
- 逆方向依存 = 0
- 循環依存 = 0
- Portバイパス = 0
- 対象2関数UI業務ロジック = 0
- UseCase->Qt依存 = 0
- Domain->Qt依存 = 0
- Qt Signal命名違反 = 0
- Qt Slot命名違反 = 0

補助メトリクス（EMCS）:
- UI業務判断分岐上限
- UseCase複雑度上限
- SRP逸脱件数
- UI層外部I/O直呼び出し件数

### Gate-F（機能）
必須:
- `pytest tests/` 全件Pass
- Phase別必須テスト（T5/T6/T6.2/T6.3/T6.4/T6.51/T6.52/T6.53）Pass
- 監査ログ必須項目テスト Pass
- Docker再現性テスト Pass
- Data Integrity テスト（T-DI-1〜4）Pass
- Qt命名規約テスト（T-UI-NAME-1/2）Pass
- Qt非依存テスト（T-ARCH-QT-1/2）Pass

ゲート判定原則:
1. Gate-S fail は `REJECT_TO_ARCHITECT`。
2. Gate-F pass 単独は進捗扱いにしない。
3. 両ゲート同一リビジョンPassのみ Done 判定可能。

## 5. 監査証跡と運用成果物
必須成果物:
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/post_mortem_closure_checklist.md`
- `artifacts/audit_reject_template.md`
- `artifacts/data_integrity_field_matrix.md`
- Phase別成果物（6.51, 6.52, 6.53, Docker）

監査ログ入力制約:
- 許可入力: 要件文書 + 変更差分のみ
- 禁止入力: 実装者思考ログ、口頭説明、未証跡メモ

## 6. マイルストーン
1. M1（構造回復）
- Phase A-B 完了
- Gate-S 主要違反 0 化

2. M2（機能安定）
- Phase C-D 完了
- Phase 5/6 系受け入れ基準充足

3. M3（契約固定）
- Phase E-G 完了
- 型・契約・回帰・ログ標準化完了

4. M4（再現性監査完了）
- Phase H + Data Integrity 完了
- Gate-S/Gate-F 同一リビジョンPass

## 7. Definition of Done
1. Gate-S と Gate-F が同一リビジョンでPass。
2. post_mortem 指摘の責務移管が完了。
3. Phase 5, 6, 6.1〜6.4, 6.51, 6.52, 6.53 の受け入れ基準を満たす。
4. Docker再現性4要件を証跡付きで満たす。
5. Data Integrity 必須項目を自動テストで担保。
6. Qt命名規約とQt非依存が機械検証で violation 0。
