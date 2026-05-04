# Audit Report (2026-05-04)

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **64 passed, 0 failed**
- 所要時間: 1.99s

## 2. `docs/reference_standards.md` 準拠監査（`src/`・`tests/`・`artifacts/`）

### 2.1 合格項目
- Dockerfile の `FROM` は確認範囲で digest 固定（`@sha256:`）を満たしている。
- `pytest tests/` 全件Pass（テストゲート要件を満たす）。
- `artifacts/architecture_decoupling_assessment.md` と `artifacts/refactoring_proposal.md` は存在する。

### 2.2 指摘事項（違反）
1. **Port未使用 / 境界バイパス呼び出し**
- ファイル: `src/lcr/ui/workers.py:15`
- 根拠: `from lcr.core.container.worker import ContainerExecutionService`
- 内容: UI層が UseCase/Port を経由せず、実行サービスへ直接依存している。
- 該当基準:
  - `docs/reference_standards.md` 4章「クリーンアーキテクチャと依存の方向」
  - `docs/reference_standards.md` 4章「インターフェースによる規律」
  - `docs/requirements.md` Phase 6.1 検証観点「Port未使用または境界バイパス呼び出し」
- 影響: UI責務の肥大化とテスト容易性低下（差し替え不能点の増加）を招く。
- 修正指示:
  - `ContainerExecutionService` 直接参照を廃止し、`ExecutionGatewayPort` 等の抽象Portを `ui/ports.py` 経由で注入すること。
  - `ContainerWorker` は Qt シグナル中継専用に限定し、業務オーケストレーションは UseCase へ移管すること。

2. **成果物と実装実態の不整合（監査証跡品質違反）**
- ファイル: `artifacts/architecture_decoupling_assessment.md`
- 根拠: 当該成果物は「違反 0件」と記載しているが、上記 2.2-1 の境界バイパスが実在する。
- 該当基準:
  - `docs/requirements.md` Phase 6.1 AC6.1-1（主要違反の列挙）
  - `docs/requirements.md` Phase 6.1 検証観点（Port未使用/境界バイパス）
- 影響: Phase 6.1 の受け入れ判定に必要な客観性が不足し、監査トレーサビリティが損なわれる。
- 修正指示:
  - `architecture_decoupling_assessment.md` に当該違反を `file path + class/function + 違反種別 + 根拠` 形式で追記すること。
  - 再測定時の抽出ルールに「UI->Infrastructure 直参照」を明示し、件数を固定指標として再掲すること。

## 3. Phase 6.1 受け入れ基準適合判定
- AC6.1-1: **未達**（主要違反の列挙が実態と不一致）
- AC6.1-2: **未達**（上記違反に対する改善方針の明示不足）
- AC6.1-3〜AC6.1-7: 文書上は記載あり。ただし AC6.1-1/2 未達のため総合不合格。

## 4. 総合判定
- **REJECT_TO_IMPLEMENT**
- 理由: テストはPassだが、基準違反（Port未使用/境界バイパス）および Phase 6.1 成果物の実態不整合を確認。
