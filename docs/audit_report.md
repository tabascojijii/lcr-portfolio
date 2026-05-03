# Audit Report

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **43 passed / 0 failed**
- 所要時間: 1.45s

## 2. 基準照合 (docs/reference_standards.md)

### 2.1 監査・ガバナンス標準
- テスト失敗なし。主要な品質ゲート（Docker digest policy、UI/usecase separation、audit metadata整合性）を `tests/` で確認。

### 2.2 Docker 再現性標準
- `tests/test_dockerfile_digest_policy.py` により `src/lcr/core/container/images/Dockerfile.*` の `FROM ...@sha256:<64hex>` を検証。
- `src/lcr/core/container/templates/base.Dockerfile.j2` で `constraints.txt` を `pip install -c` に適用。
- EOL向けAPTリダイレクト（`archive.debian.org`）をテンプレート/生成Dockerfileで確認。

### 2.3 データ完全性・監査証跡
- `src/lcr/core/audit/metadata_service.py` で以下を確認:
  - `git rev-parse HEAD` によるコミットハッシュ採取
  - `image_digest` 採取
  - script/parameter/input/output/log の SHA-256 記録
  - `script_path_rel` 等の相対パス正規化（絶対パス・`..` を拒否）

### 2.4 PyQt/PySide アーキテクチャ標準
- `src/lcr/ui/ports.py` で `typing.Protocol` によるインターフェース分離を確認。
- `tests/test_ui_usecase_separation.py` で UI が build preparation use case を経由することを検証。

## 3. 指摘事項
- **なし**（pytest失敗なし、参照基準に対する重大違反は確認されず）

## 4. 監査判定
- **AUDIT_PASS_IMPLEMENT**
