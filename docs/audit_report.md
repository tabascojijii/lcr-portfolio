# Audit Report

## 1) pytest 実行結果

実行コマンド: `pytest tests/`

結果:
- `36 passed in 1.46s`
- Fail/ERROR はなし

## 2) 基準照合結果（docs/reference_standards.md vs src/, tests/）

判定: **PASS（基準違反なし）**

確認内容:
- Docker再現性基準（2章）
  - `base_image` のダイジェスト固定を `render_dockerfile` で強制し、テストで検証済み。
  - マルチステージビルド（`AS builder` / `AS runtime`）と `constraints.txt` 利用をテンプレートとテストで確認。
  - アーカイブリポジトリ切替ロジック（`archive.debian.org`）をテンプレートで確認。
- Data Integrity基準（3章）
  - 監査メタデータに `image_digest` / `git_commit_hash` / `script_sha256` / `param_hash` / `input_hashes` / `output_hashes` / `log_hash` が実装済み。
  - 相対パス正規化・絶対パス拒否（`script_path_rel`）および UseCase 側の相対化処理をテストで確認。
- UIアーキテクチャ基準（4章）
  - UI層とユースケース層の分離（UseCase経由での実行準備）をテストで確認。
  - `typing.Protocol` によるポート定義を確認。

## 3) 総合判定

- pytest: Pass
- 規約準拠: Pass

最終判定: **AUDIT_PASS_IMPLEMENT**
