# Audit Report

## 1. pytest 実行結果
実行コマンド: `pytest tests/`

結果サマリ:
- collected: 63
- passed: 63
- failed: 0
- error: 0

抜粋ログ:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\dev\lcr
configfile: pyproject.toml
plugins: anyio-4.12.1
collected 63 items
...
============================= 63 passed in 2.01s ==============================
```

## 2. docs/reference_standards.md に基づく品質監査（src/・tests/・artifacts/）

### 2.1 適合事項
- `tests/` は全件Passで、最低限の回帰ゲートは満たしている。
- `artifacts/architecture_decoupling_assessment.md` と `artifacts/refactoring_proposal.md` は存在する。
- `artifacts/architecture_decoupling_assessment.md` 上で逆方向依存 0件・循環依存 0件を明示している。

### 2.2 違反事項（REJECT 根拠）

1. UI責務混在（Humble Object違反）
- 違反基準: `docs/reference_standards.md` セクション4「Humble Object パターンの適用」
- 根拠:
  - `artifacts/architecture_decoupling_assessment.md` にて、`src/lcr/ui/main_window.py` へ業務判断・監査整形・実行オーケストレーションが集中していると明記。
  - 同資料の違反一覧で `UI->Domain直参照` が6件列挙されている。
- 判定: 基準違反

2. クリーンアーキテクチャ依存方向の実運用未達
- 違反基準: `docs/reference_standards.md` セクション4「クリーンアーキテクチャと依存の方向」
- 根拠:
  - `artifacts/architecture_decoupling_assessment.md` に `UI->Domain直参照` 6件（`src/lcr/ui/main_window.py`）が明示されている。
- 判定: 基準違反

## 3. Phase 6.1 成果物・受け入れ基準確認（requirements.md）

### 3.1 成果物存在確認
- `artifacts/architecture_decoupling_assessment.md`: 存在
- `artifacts/refactoring_proposal.md`: 存在

### 3.2 AC6.1 適合確認
- AC6.1-1: 適合（`file path + 関数/クラス + 違反種別 + 根拠` の形式で記載あり）
- AC6.1-2: 適合（各違反への移管先/Port設計方針が記載あり）
- AC6.1-3: 適合（P0/P1/P2 優先度と順序あり）
- AC6.1-4: 適合（追加/更新テスト方針と判定指標あり）
- AC6.1-5: 適合（`UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数あり）
- AC6.1-6: 適合（変更影響テスト手順、期待影響範囲、合否条件あり）
- AC6.1-7: 適合（数値閾値を固定で明記）

補足:
- AC6.1 文書要件は満たすが、現状実測として `UI->Domain直参照 6件` が残存しており、参照基準（reference_standards）への実装適合は未達。

## 4. 最終判定
- pytest: PASS
- 基準適合: NG（UI責務混在・UI->Domain直参照）
- 総合判定: **REJECT_TO_IMPLEMENT**
