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
============================= 63 passed in 1.88s ==============================
```

## 2. docs/reference_standards.md に基づく品質監査（src/・tests/・artifacts/）

### 2.1 適合事項
- `tests/` は全件Passで、テストゲートは通過。
- `artifacts/architecture_decoupling_assessment.md` と `artifacts/refactoring_proposal.md` は存在。
- `artifacts/architecture_decoupling_assessment.md` に逆方向依存 0件・循環依存 0件の明記あり。

### 2.2 違反事項（REJECT 根拠）

1. UI責務混在（Humble Object違反）
- 違反基準: `docs/reference_standards.md` セクション4「Humble Object パターンの適用」
- 根拠:
  - `artifacts/architecture_decoupling_assessment.md` に `UI->Domain直参照` 6件が記載。
  - `src/lcr/ui/main_window.py` で `container_manager` への直接依存が残存（例: L282, L464, L604, L1001, L1010）。
- 判定: 基準違反

2. 依存方向規約の未達（UI -> UseCase -> Domain の厳守違反）
- 違反基準: `docs/reference_standards.md` セクション4「クリーンアーキテクチャと依存の方向」
- 根拠:
  - `artifacts/architecture_decoupling_assessment.md` の違反一覧で `MainWindow._run_container` など UI からの業務判断/実行オーケストレーション保持を明示。
- 判定: 基準違反

## 3. Phase 6.1 成果物・受け入れ基準確認（docs/requirements.md）

### 3.1 成果物存在確認
- `artifacts/architecture_decoupling_assessment.md`: 存在
- `artifacts/refactoring_proposal.md`: 存在

### 3.2 AC6.1 適合確認
- AC6.1-1: 適合（`file path + 関数/クラス + 違反種別 + 根拠` 形式で列挙あり）
- AC6.1-2: 適合（改善方針・Port設計あり）
- AC6.1-3: 適合（P0/P1/P2 の優先度/順序あり）
- AC6.1-4: 適合（検証方法・追加テスト方針あり）
- AC6.1-5: 適合（`UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数あり）
- AC6.1-6: 適合（変更影響テスト手順あり）
- AC6.1-7: 適合（固定数値指標あり）

補足:
- Phase 6.1 の「成果物要件」は適合。
- ただし実装状態は `UI->Domain直参照 6件` が残っており、reference standards には未適合。

## 4. 最終判定
- pytest: PASS
- 基準適合: NG
- 総合判定: **REJECT_TO_IMPLEMENT**
