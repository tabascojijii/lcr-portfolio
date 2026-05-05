# Audit Report (2026-05-06)

## 1) Pytest結果
- 実行コマンド: `pytest tests/`
- 結果: **77 passed** / 0 failed / 0 skipped
- 結論: テストゲートは合格。

## 2) `docs/reference_standards.md` 準拠監査（`src/`・`tests/`・`artifacts/`）
- 監査標準1（監査ガバナンス）: 監査証跡としてテスト結果および要件照合結果を記録。
- 監査標準2（Docker再現性）: 関連テスト（`tests/test_dockerfile_digest_policy.py`）がPassしており、違反は検出されない。
- 監査標準3（データ完全性）: 関連テスト（監査メタデータ/ハッシュ証跡系）がPassしており、違反は検出されない。
- 監査標準4（UI分離/Humble Object/依存方向）: 関連テスト（UI-UseCase分離、境界違反、命名規約等）がPassしており、違反は検出されない。
- 指摘事項: **なし**（本監査範囲で規約違反を確認できず）。

## 3) Phase 6.1 成果物存在・受け入れ基準適合
- 成果物存在確認:
  - `artifacts/architecture_decoupling_assessment.md`: 存在
  - `artifacts/refactoring_proposal.md`: 存在
- 要件参照元: `docs/requirements.md` の「Phase 6.1: Architecture Decoupling Assessment & Refactoring Proposal」

### AC6.1 適合判定
- AC6.1-1: 適合（違反列挙フォーマット定義および結果記載あり。現状違反0件）
- AC6.1-2: 適合（Port設計・移管先レイヤ・インターフェース方針あり）
- AC6.1-3: 適合（P0/P1/P2 の優先度と実施順序あり）
- AC6.1-4: 適合（追加/更新テスト方針と判定指標あり）
- AC6.1-5: 適合（`UI->Domain直参照` / 逆方向依存 / 循環依存 の一覧と件数あり）
- AC6.1-6: 適合（変更影響テスト手順、期待影響範囲、合否条件あり）
- AC6.1-7: 適合（禁止依存0件・循環依存0件・UI業務ロジック0件・境界違反テスト100%を数値固定）

## 4) 総合判定
- 判定: **PASS**
- 差し戻し要因（pytestエラー/基準違反）: **なし**
