# 監査レポート

監査日: 2026-05-04
監査対象: `src/`, `tests/`, `artifacts/`

## 1. pytest 実行結果

実行コマンド: `pytest tests/`

結果:
- `71 passed in 2.17s`
- Fail/Error 0件

判定:
- テストゲートは **Pass**。

## 2. `docs/reference_standards.md` 準拠確認

以下を基準照合した。
- 監査証跡系: `tests/test_audit_hash_evidence_use_case.py`, `tests/test_audit_metadata_reference_schema.py`, `tests/test_audit_metadata_service.py`, `tests/test_audit_metadata_use_case.py`
- Docker再現性系: `tests/test_dockerfile_digest_policy.py`
- UI/UseCase分離・命名規約系: `tests/test_ui_usecase_separation.py`, `tests/test_signal_slot_naming_use_case.py`, `tests/test_standards_traceability_use_case.py`
- Lifecycle/Guardrails系: `tests/test_runtime_guard_use_case.py`, `tests/test_environment_lifecycle_use_case.py`
- Phase 6.1疎結合評価系: `tests/test_phase61_decoupling_use_case.py`

確認結果:
- 基準違反を示す失敗テストは検出されず（上記を含め全件Pass）。
- `src/`・`tests/`・`artifacts/` の品質確認において、監査時点で **明示的な違反証跡なし**。

## 3. Phase 6.1 成果物と受け入れ基準適合

### 3.1 必須成果物の存在
- `artifacts/architecture_decoupling_assessment.md`: 存在確認済み
- `artifacts/refactoring_proposal.md`: 存在確認済み

### 3.2 `docs/requirements.md` Phase 6.1 AC 適合確認
- AC6.1-1: 主要違反の列挙形式（file path + class/function + 違反種別 + 根拠）を満たす記載あり（違反0件を明示）。
- AC6.1-2: 各違反カテゴリに対する改善方針（Port設計・移管先レイヤ）記載あり。
- AC6.1-3: P0/P1/P2 優先度と実施順序の記載あり。
- AC6.1-4: 追加/更新テスト戦略と判定指標の記載あり。
- AC6.1-5: importグラフ結果として `UI->Domain直参照` / `逆方向依存` / `循環依存` の一覧と件数記載あり（各0件）。
- AC6.1-6: 変更影響テスト手順（シナリオ、期待範囲、合否条件）記載あり。
- AC6.1-7: 数値合否指標（禁止依存0、循環依存0、UI層業務ロジック0、境界違反テスト100%）の固定値明記あり。

判定:
- Phase 6.1 受け入れ基準は監査時点で **適合**。

## 4. 指摘事項

- なし（pytest Failおよび基準違反の客観的証跡を検出せず）。

## 総合判定

- **AUDIT_PASS_IMPLEMENT**
