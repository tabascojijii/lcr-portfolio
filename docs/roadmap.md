# LCR Roadmap（Reference Standards Absolute Baseline）

- 作成日: 2026-05-04
- 参照: `docs/plan.md`, `docs/reference_standards.md`
- 基本方針: `docs/reference_standards.md` を絶対基準とし、本ロードマップ内の全タスク・全ゲートは当該基準に従属する。

## 0. Absolute Compliance Charter

以下のいずれかに違反した時点で、当該フェーズは即時 `REJECT` とし、次フェーズ進行を禁止する。

1. Docker再現性4要件（digest固定 / EOL archive切替 / constraints適用 / マルチステージ）
2. Data Integrity要件（相対パス / 入出力+パラメータ+ログ本体ハッシュ / `image_digest` + `git_commit` 記録）
3. PyQt/PySide設計要件（Humble Object / 依存方向固定 / インターフェース経由 / 命名規約）
4. 監査ガバナンス要件（Builder/Validator分離 / EMCS客観評価 / 処方的REJECT）

## 1. Roadmap Objectives

1. 設計不備を実装で吸収しない工程へ移行する。
2. UI汚染・境界越え・監査欠落の再発を構造的に不可能化する。
3. EOLスタックを監査可能かつ再現可能な形で固定する。

## 2. Fixed KPIs（Exit Criteria）

### 2.1 Structure KPIs

- `UI -> Domain` 直接依存: 0件
- Port未経由の境界越え: 0件
- 逆方向依存（内側 -> 外側）: 0件
- 循環依存: 0件
- `MainWindow` の業務ロジック保持: 0件
- Qtシグナル命名規約違反（過去分詞形以外）: 0件
- Qtスロット命名規約違反（動詞開始以外）: 0件
- `CC > 10`: 0件
- `LOC > 80`: 0件

### 2.2 Quality KPIs

- `pytest tests/` 全件Pass
- DTO strict/fail-fast違反: 0件
- `mypy` エラー: 0件
- 理由なき `type: ignore`: 0件

### 2.3 Audit KPIs

- 相対パス違反: 0件
- ハッシュ対象欠落（入力/出力/パラメータ/ログ本体）: 0件
- `image_digest` 記録欠落: 0件
- `git_commit` 記録欠落: 0件
- ハッシュ再計算不一致: 0件

### 2.4 Docker/EOL KPIs

- `FROM` タグ使用: 0件（`@sha256:` 必須）
- EOL APT未切替: 0件
- `constraints.txt` 未適用ビルド: 0件
- C/C++単一ステージビルド: 0件

## 3. Phase Plan

### Phase A: Architecture Lock

目的: UI責務分離と依存方向の固定。

実施:
1. `MainWindow` を Humble Object 化（イベント中継/表示更新のみ）
2. 実行導線を `RunContainerUseCase` に集約
3. 環境作成導線を `CreateEnvironmentFlowUseCase` に集約
4. UIから実装型直参照を除去し、Port経由へ統一
5. シグナル/スロット命名規約を全体是正

完了条件:
1. Structure KPIs 全達成
2. `_run_container` / `_show_create_env_dialog` から業務判断除去

### Phase B: Reproducible Build Lock

目的: EOLビルド再現性を監査前提で固定。

実施:
1. 全 `Dockerfile` の `FROM` を digest固定
2. EOL APTソースを `old-releases` / `archive.debian.org` へ統一
3. `constraints.txt` を必須入力化（未適用はFail）
4. C/C++依存（例: OpenCV）をマルチステージ化

完了条件:
1. Docker/EOL KPIs 全達成

### Phase C: Phase 5 Guardrails

目的: ミスマッチ実行を事前遮断。

実施:
1. capability mapping（推定/実証）可視化
2. required imports差分検知
3. mismatch時Run無効化
4. 適合環境が無い場合の作成導線
5. 作成後Dynamic Refresh
6. 監査ログへ判定根拠を記録

完了条件:
1. AC-1〜AC-5
2. T5-1〜T5-4 Pass

### Phase D: Phase 6 Lifecycle

目的: 安全で追跡可能な環境整理。

実施:
1. Environment Manager実装
2. 2段階確認付き一括削除
3. 未使用判定（最終利用/回数/保護フラグ）
4. dangling/unused image cleanup
5. メタ情報編集（内部ID不変）
6. 部分失敗継続と結果分離表示
7. 監査ログ完全記録（対象/時刻/成否/容量/理由）

完了条件:
1. AC6-1〜AC6-7
2. T6-1〜T6-6 Pass

### Phase E: Type Safety & Static Gate

目的: 実行時・静的解析の二重ゲート化。

実施:
1. DTOを段階的にPydantic v2へ移行
2. strict + fail-fast を強制
3. 境界にdict互換アダプタ配置
4. `mypy` をCI必須ゲート化
5. `Any` / `type: ignore` の理由管理と増加監視

完了条件:
1. AC6.2-1〜AC6.2-5 / T6.2-1〜T6.2-5
2. AC6.3-1〜AC6.3-4 / T6.3-1〜T6.3-4

### Phase F: Contract & Regression Hardening

目的: 将来変更時の品質逆流防止。

実施:
1. Port contract test
2. DTO/Audit schema contract test
3. Golden regression（Run/Build/Lifecycle/Audit）

完了条件:
1. AC6.4-1〜AC6.4-4
2. T6.4-1〜T6.4-4 Pass

## 4. Governance Gates

### 4.1 Functional Gate

- 該当フェーズのACを満たす
- 必須テスト（`pytest`, `mypy`, contract, regression）が全Pass

### 4.2 Structural Gate

- Structure KPIs 全達成
- UI責務混在再発 0件
- Port bypass 0件

### 4.3 Audit Integrity Gate

- ハッシュ対象4区分を全生成
- 保存先 `artifacts/audit/hashes/` 固定
- 命名規約 `<run_id>_<target_kind>_<relative_path_normalized>.sha256`
- 再計算一致を全件確認

### 4.4 Governance Gate

- Builder/Validator分離チェックが `Yes`
- 監査入力が「要件仕様 + Diff + テスト結果」のみ
- REJECT時に処方的指示が記録されている

### 4.5 Stop Rules

1. いずれかのゲートFailで次フェーズ進行禁止
2. 構造ゲートFail時は実装停止し、Architect是正を先行
3. Docker/EOL 4要件の1件Failで全実装停止
4. 監査データ完全性未達で即Fail-fast

## 5. Mandatory Artifacts

各フェーズ完了時に以下を更新・保存する。

1. `artifacts/architecture_decoupling_assessment.md`
2. `artifacts/refactoring_proposal.md`
3. `artifacts/traceability_matrix.md`
4. `artifacts/audit/hashes/*.sha256`
5. フェーズ別テスト証跡（pytest/mypy/contract/regression）
6. Docker/EOL検証証跡（digest, APT, constraints, multi-stage）

## 6. RACI（Execution Accountability）

- PM: 本ロードマップ運用、ゲート進行判定、差し戻し経路管理
- Architect: 境界設計、Port定義、構造違反是正案作成
- Implementer: フェーズ単位実装、テスト実行、証跡生成
- Auditor: absolute baseline準拠監査、EMCS評価、処方的REJECT発行

## 7. Definition of Done

以下をすべて満たした時のみ完了。

1. Phase A〜F の完了条件達成
2. Fixed KPIs（Structure/Quality/Audit/Docker-EOL）全達成
3. Mandatory Artifacts 最新化
4. 全フェーズでBuilder/Validator分離 `Yes`
5. `docs/reference_standards.md` 逸脱 0件
