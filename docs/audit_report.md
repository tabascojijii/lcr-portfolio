# 監査レポート

## 1) pytest 実行結果
実行コマンド: `pytest tests/`

結果サマリ:
- `29 passed in 1.55s`
- 失敗テスト: なし

## 2) reference_standards 準拠監査結果（src/・tests/）

結論:
- **REJECT**（テストはPassだが、規約違反あり）

### 指摘1: ベースイメージのダイジェスト固定が実質的に無効
- 違反基準: `docs/reference_standards.md` セクション2「ダイジェストによる完全固定」
- 根拠:
  - [src/lcr/core/container/images/Dockerfile.py27_cv](/C:/dev/lcr/src/lcr/core/container/images/Dockerfile.py27_cv:1)
  - [src/lcr/core/container/images/Dockerfile.py36_ds](/C:/dev/lcr/src/lcr/core/container/images/Dockerfile.py36_ds:1)
  - [src/lcr/core/container/definitions/py36_ml.json](/C:/dev/lcr/src/lcr/core/container/definitions/py36_ml.json:3)
- 事象:
  - `@sha256:000000...0000`（全ゼロ）のプレースホルダが多数使用されている。
  - 形式上は `sha256` だが、実在イメージの不変参照になっておらず、再現性保証を満たさない。
- 修正指示:
  - 実在する `RepoDigest` を `docker image inspect` 等で取得し、全定義を実ダイジェストへ置換すること。
  - 生成時バリデーションを「`@sha256:` を含む」だけでなく、全ゼロ値禁止・64hex妥当性・存在確認へ強化すること。

### 指摘2: UI層にビジネスロジックが混在（Humble Object違反）
- 違反基準: `docs/reference_standards.md` セクション4
  - 「Humble Object パターンの適用」
  - 「クリーンアーキテクチャと依存の方向」
- 根拠:
  - [src/lcr/ui/create_env_dialog.py](/C:/dev/lcr/src/lcr/ui/create_env_dialog.py:374)
  - [src/lcr/ui/create_env_dialog.py](/C:/dev/lcr/src/lcr/ui/create_env_dialog.py:392)
  - [src/lcr/ui/create_env_dialog.py](/C:/dev/lcr/src/lcr/ui/create_env_dialog.py:461)
  - [src/lcr/ui/main_window.py](/C:/dev/lcr/src/lcr/ui/main_window.py:368)
  - [src/lcr/ui/main_window.py](/C:/dev/lcr/src/lcr/ui/main_window.py:812)
- 事象:
  - UIクラス内で依存解決・レガシーピン適用・APT補正・定義保存・Dockerfile生成・ビルド起動まで実施しており、表示層が業務ロジックを保持している。
- 修正指示:
  - `Presenter`/`UseCase` 層へロジックを分離し、Dialog/MainWindow は入出力とイベント転送のみに限定すること。
  - UIからは抽象インターフェース経由で実行し、テスト可能な形で依存注入すること。

## 3) 監査判定
- 判定: **REJECT_TO_IMPLEMENT**
- 理由: テストは全件Passだが、参照規約（特にコンテナ再現性・UIアーキテクチャ）に対する重大違反を確認。
