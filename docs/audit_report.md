# Audit Report

## 1. Pytest結果
- 実行コマンド: `pytest tests/`
- 結果: **PASS**
- サマリ: `59 passed in 1.84s`

## 2. 参照基準 (`docs/reference_standards.md`) 照合

### 2.1 違反事項
1. `src/lcr/ui/main_window.py:609` (`MainWindow._run_container`)
- 違反基準: **4. PyQt/PySide モダンUIアーキテクチャ標準**
- 違反内容: UI層が `prepare_execution` 後の実行制御、イメージ存在判定、再ビルド分岐、`container_manager.get_docker_run_args(...)` 呼び出しを直接保持。
- 根拠: Humble Object 原則（UIは表示更新中心）と依存方向規律に反し、業務判断・外部I/OオーケストレーションがUIへ混在。

2. `src/lcr/ui/main_window.py:924` (`MainWindow._build_audit_metadata`)
- 違反基準: **4. PyQt/PySide モダンUIアーキテクチャ標準**
- 違反内容: UI層が監査メタデータの構築/出力責務を保持。
- 根拠: 監査整形責務はUseCase/Domain側へ分離すべき。

3. `src/lcr/ui/main_window.py:1043` (`MainWindow._execute_save_and_build`)
- 違反基準: **4. PyQt/PySide モダンUIアーキテクチャ標準**
- 違反内容: 環境定義保存後の再読込、選択更新、ビルド起動の業務オーケストレーションをUIが実装。
- 根拠: UI責務混在（業務制御の過多）。

### 2.2 判定
- `tests/` は全件Passだが、`src/` は上記のUI責務混在により基準未達。
- `artifacts/` の評価文書は存在するが、下記Phase 6.1受け入れ基準で不足あり。

## 3. Phase 6.1 受け入れ基準適合性 (`docs/requirements.md`)

### 3.1 成果物の存在
- `artifacts/architecture_decoupling_assessment.md`: 存在確認済み
- `artifacts/refactoring_proposal.md`: 存在確認済み

### 3.2 AC適合確認
- AC6.1-1: 適合（違反を `file path + 関数/クラス + 違反種別 + 根拠` 形式で列挙）
- AC6.1-2: 概ね適合（移管先/Port方針あり）
- AC6.1-3: 適合（P0/P1/P2の優先度・順序あり）
- AC6.1-4: 適合（テスト戦略の記載あり）
- AC6.1-5: 適合（`UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧・件数あり）
- AC6.1-6: **不適合**（変更影響テストの実施手順: 変更シナリオ・期待影響範囲・合否条件が明記不足）
- AC6.1-7: **不適合**（合否指標の数値固定値が未定義。例: 禁止依存0件、UI層業務ロジック0件等の閾値未記載）

## 4. 最終判定
- 判定: **REJECT_TO_IMPLEMENT**
- 理由:
  - `docs/reference_standards.md` に対する `src/` のUI責務混在違反を確認。
  - Phase 6.1 受け入れ基準 AC6.1-6 / AC6.1-7 未充足を確認。
