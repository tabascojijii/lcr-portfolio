# 監査レポート

- 監査日時: 2026-05-03 (Asia/Tokyo)
- 実行コマンド: `pytest tests/`
- 対象基準: `docs/reference_standards.md`
- 判定: **REJECT**

## 1. pytest実行結果

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\dev\lcr
configfile: pyproject.toml
plugins: anyio-4.12.1
collected 27 items

...（中略）...

============================= 27 passed in 1.62s ==============================
```

- テスト結果: 27件すべてPass

## 2. 基準照合による違反事項

### 違反1: Docker `FROM` のダイジェスト完全固定違反（Reference Standards 2項）

基準では `FROM` 句で可変タグではなく SHA256 ダイジェスト固定が必須。
以下はタグ指定のみ、またはダイジェスト不在の `FROM` を確認。

- `src/lcr/core/container/images/Dockerfile.3.10test3:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.3.10test4:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.3.10test5:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.3.10test6:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.3.10test7:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.3.10fot_test:1` -> `FROM python:3.10-slim`
- `src/lcr/core/container/images/Dockerfile.py36_ds:1` -> `FROM python:3.6-slim-buster`
- `src/lcr/core/container/images/Dockerfile.lcr_py27_cv_apt:1` -> `FROM debian:stretch-slim`
- `src/lcr/core/container/images/Dockerfile.py27_cv:1` -> `FROM python:2.7-slim-stretch`
- `src/core/container/images/Dockerfile.py27_cv2:1` -> `FROM python:2.7-slim-stretch`

#### 修正指示

- すべての `FROM` を `image:tag@sha256:<実在digest>` 形式へ置換すること。
- テンプレート生成系（`src/lcr/core/container/templates/base.Dockerfile.j2`）から出力される成果物も同一規約で自動検証すること。

### 違反2: UI層へのビジネスロジック集中（Reference Standards 4項: Humble Object / 依存方向）

基準ではViewはロジック最小化が必要だが、`MainWindow` に監査メタデータ計算やGit/Docker情報取得などの非UI責務が実装されている。

- `src/lcr/ui/main_window.py:1003` `_append_audit_metadata`
- `src/lcr/ui/main_window.py:1019` `_resolve_image_digest`
- `src/lcr/ui/main_window.py:1031` `_resolve_git_commit_hash`
- `src/lcr/ui/main_window.py:1042` `_sha256_file`

#### 修正指示

- 上記処理を `core` 層のサービス（例: `AuditMetadataService`）へ移譲し、UIは結果表示のみ行う構造へ分離すること。
- UI層が `subprocess` やファイルハッシュ計算の詳細を持たないようにすること。

## 3. 総合判定

- pytest: Pass
- 規約適合: **不適合（上記違反あり）**

したがって監査判定は **REJECT_TO_IMPLEMENT**。
