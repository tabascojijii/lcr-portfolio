# 監査報告書

- 監査日: 2026-05-04
- 監査対象: `src/`, `tests/`
- 監査基準: `docs/reference_standards.md`

## 1. pytest 実行結果
実行コマンド: `pytest tests/`

結果:
- `collected 40 items`
- `40 passed in 1.61s`
- エラーログ: なし

## 2. 基準適合性チェック結果

### 2.1 監査・ガバナンス標準
- 自動テストは全件成功しており、差し戻しを要する失敗ログは検出されない。

### 2.2 Docker再現性標準
- `FROM ...@sha256:<64hex>` 形式の固定化を確認（例: `src/lcr/core/container/images/Dockerfile.lcr_py27_cv_apt` 先頭行）。
- EOL向けアーカイブリポジトリ設定を確認（`archive.debian.org` 使用）。
- ダイジェスト形式検証テストが成功（`tests/test_dockerfile_digest_policy.py`）。

### 2.3 データ完全性・監査証跡
- SHA-256ハッシュ記録ロジックを確認（`src/lcr/core/audit/metadata_service.py`）。
- 監査メタデータ整合性テストが成功（`tests/test_audit_metadata_service.py`, `tests/test_audit_metadata_reference_schema.py`）。

### 2.4 PyQt/PySideアーキテクチャ標準
- UI層とユースケース層分離テストが成功（`tests/test_ui_usecase_separation.py`）。
- Protocolベースのポート定義を確認（`src/lcr/ui/ports.py`）。

## 3. 指摘事項
- なし（pytest失敗なし、基準違反なし）。

## 4. 最終判定
- `AUDIT_PASS_IMPLEMENT`
