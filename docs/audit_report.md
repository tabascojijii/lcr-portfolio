# Audit Report

## 1) Pytest 実行結果
実行コマンド: `pytest tests/`

結果:
- `25 passed in 1.47s`
- Fail/ERROR は検出されず

## 2) docs/reference_standards.md 準拠監査（src/・tests/）

### 重大違反（REJECT根拠）
1. **[標準2] Docker `FROM` のダイジェスト固定違反**
- 規約: `FROM` は可変タグではなく `@sha256:` を必須化
- 実装:
  - `src/lcr/core/container/templates/base.Dockerfile.j2:1` → `FROM {{ base_image }}`（ダイジェスト制約なし）
  - `src/lcr/core/container/manager.py:54` → `python:2.7-slim`
  - `src/lcr/core/container/manager.py:74` → `python:3.10-slim`
  - `src/lcr/core/container/definitions/py27_cv_apt.json:3` → `debian:stretch-slim`
  - `src/lcr/core/container/definitions/3.10test6.json:3` ほか多数 → `python:3.10-slim`
- 判定: **違反**

2. **[標準2] pip 依存解決の `constraints.txt` 未適用**
- 規約: 旧パッケージのバックトラッキング回避のため `constraints.txt` による制約必須
- 実装:
  - `src/lcr/core/container/templates/base.Dockerfile.j2` の `pip install` に `-c constraints.txt` 相当なし
  - リポジトリ内に `constraints*.txt` が存在しない（`rg --files -g "*constraints*.txt"` 結果なし）
- 判定: **違反**

3. **[標準2] マルチステージビルド未実装**
- 規約: C/C++系（OpenCV等）を含む場合、ビルド環境と実行環境の分離を強制
- 実装:
  - `src/lcr/core/container/templates/base.Dockerfile.j2` は単一 `FROM` のみ（builder/runtime 分離なし）
- 判定: **違反**

4. **[標準3] 監査証跡（環境/コードハッシュ）未記録**
- 規約: 実行ログにコンテナイメージダイジェストと Git コミットハッシュ記録必須
- 実装:
  - `src/lcr/ui/main_window.py` の実行ログ出力（例: `:843`）に digest/hash 記録なし
  - `git rev-parse HEAD` 実行や保存処理が `src/` 内に存在しない（検索結果なし）
- 判定: **違反**

### 品質上の追加懸念（規約1の客観評価観点）
- `src/lcr/ui/main_window.py` に重複実装が存在し、保守性・誤動作リスクが高い
  - import重複: `Path` (13,17), `CodeAnalyzer` (28,30), `ContainerManager` (29,31)
  - 代入重複: `self.worker = None` (54,55)
  - UI追加重複: `env_layout.addWidget(self.version_label)` (143,146), `self.results_layout.addWidget(self.res_scroll)` (223,226)
  - メソッド二重定義: `_refresh_env_list` (277,290), `_show_create_env_dialog` (470,1124)
- 判定: テストは通るが、品質規約の厳格運用上は是正対象

## 3) 総合判定
- pytest: PASS
- 規約準拠: **FAIL（重大違反あり）**
- 最終判定: **REJECT_TO_IMPLEMENT**
