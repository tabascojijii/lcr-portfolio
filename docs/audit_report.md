# Audit Report (2026-05-04)

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **64 passed / 0 failed / 0 error**
- 要件 `pytest tests/` 全件Pass: **適合**

## 2. 参照基準 `docs/reference_standards.md` に基づく検証

### 2.1 `src/` の検証
- **違反1**
  - file: `src/lcr/ui/main_window.py`
  - function/class: `MainWindow._run_container`
  - 違反種別: UI責務混在（Humble Object 原則違反リスク）
  - 根拠: 実行前確認ダイアログ分岐・JIT作成導線制御がUIメソッドに残存し、UseCaseへの責務移譲が未完了。
- **違反2**
  - file: `src/lcr/ui/main_window.py`
  - function/class: `MainWindow._show_create_env_dialog`
  - 違反種別: Port未使用（境界バイパス）
  - 根拠: `EnvironmentCreationDialog` へ `ContainerManager` を直接受け渡し。

### 2.2 `tests/` の検証
- 自動テスト群は存在し、`pytest tests/` は全件Pass。
- ただし Phase 6.1 の数値合否指標（禁止依存0件等）達成を裏付ける状態としては、`src/` 側違反が残るため未達。

### 2.3 `artifacts/` の検証
- `artifacts/architecture_decoupling_assessment.md`: **存在**
- `artifacts/refactoring_proposal.md`: **存在**

## 3. `requirements.md` Phase 6.1 受け入れ基準適合性

### 3.1 適合
- AC6.1-1: 主要違反を `file path + 関数/クラス + 違反種別 + 根拠` で列挙: **適合**
- AC6.1-2: 改善方針（移管先レイヤ/IF方針）: **適合**
- AC6.1-3: P0/P1/P2 優先度と実施順序: **適合**
- AC6.1-4: 検証方法（テスト/指標）: **適合**
- AC6.1-5: importグラフ結果（一覧と件数）: **適合**
- AC6.1-6: 変更影響テスト手順: **適合**

### 3.2 不適合
- **AC6.1-7: 合否指標の数値固定を実測で満たすこと**
  - 基準: 禁止依存0件、循環依存0件、UI層業務ロジック0件、境界テスト100% Pass
  - 実測/記載:
    - UI->Domain直参照: **2件**（0件基準を未達）
  - 判定: **不適合**

## 4. 総合判定
- pytest: Pass
- ただし `reference_standards` 違反（UI責務混在/Port未使用）および Phase 6.1 AC6.1-7 未達あり。
- **監査判定: REJECT_TO_IMPLEMENT**
