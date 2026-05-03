# 監査レポート

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **37 passed, 0 failed**
- 実行ログ要約:
  - collected 37 items
  - `tests/test_atomic_build.py` ほか全テスト成功
  - `============================= 37 passed in 1.69s ==============================`

## 2. reference_standards 適合性監査（src/ と tests/）

### 2.1 コンテナ再現性標準（Digest固定・Archive repo・constraints・マルチステージ）
- `FROM` のDigest固定:
  - 生成済み Dockerfile 群で `@sha256:<64hex>` を使用していることを確認。
  - `src/lcr/core/container/generator.py` の `_validate_digest_pinned_image` でDigest形式を強制していることを確認。
- Archive repository:
  - `src/lcr/core/container/templates/base.Dockerfile.j2` で `archive.debian.org` を使用する分岐を確認。
- constraints.txt:
  - テンプレート内 `pip install -c /tmp/build/constraints.txt` を確認。
  - `generator.py` で `constraints.txt` を生成していることを確認。
- マルチステージビルド:
  - `base.Dockerfile.j2` が `AS builder` / `AS runtime` の2段構成であることを確認。

### 2.2 データ完全性・監査証跡
- `src/lcr/core/audit/metadata_service.py` にて以下を確認:
  - `git rev-parse HEAD` によるコミットハッシュ取得
  - `sha256` による script/params/input/output/log のハッシュ記録
  - 相対パス正規化 (`_normalize_relative_path`) と絶対パス拒否
- 対応テスト:
  - `tests/test_audit_metadata_service.py`
  - `tests/test_audit_metadata_reference_schema.py`
  - 上記はいずれも pass。

### 2.3 UIアーキテクチャ分離
- `tests/test_ui_usecase_separation.py` が pass しており、UI/UseCase 分離の回帰は検出されず。

## 3. 指摘事項
- **重大/軽微ともに指摘なし。**
- 判定に影響する pytest 失敗、または `docs/reference_standards.md` からの明確な逸脱は確認されなかった。

## 4. 最終判定
- **AUDIT_PASS_IMPLEMENT**
