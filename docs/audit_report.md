# Audit Report

## 1) Pytest Result
- Command: `pytest tests/`
- Result: **32 passed / 0 failed**
- Runtime: 1.57s

## 2) Reference Standards Compliance Check (docs/reference_standards.md)

### Finding A (Critical): Relative-path portability standard violated
- Standard: `3. データ完全性と監査証跡` の「相対パスによるポータビリティ: すべて相対パスで記述すること」
- Evidence:
  - `src/lcr/core/history/manager.py:150-154`
  - `_to_relative()` が、プロジェクトルート外のパスに対して絶対パスをそのまま返却する実装になっている。
- Impact:
  - 他環境での再検証時に履歴データの移植性を損ない、監査証跡の一貫性が崩れる。
- Prescriptive fix:
  - 履歴に保存するパス形式を強制的に相対表現へ正規化する（例: プロジェクト外は保存拒否、または `external/...` の管理下に変換）。
  - 少なくとも「絶対パスを許容する分岐」を削除し、監査対象データでは常に相対化を保証する。

### Finding B (Critical): Tamper-detection scope is incomplete
- Standard: `3. データ完全性と監査証跡` の「すべての入出力データ、パラメータファイル、および実行ログ自体にハッシュ適用」
- Evidence:
  - `src/lcr/core/audit/metadata_service.py:9-15` で収集しているのは `image_digest`, `git_commit_hash`, `script_sha256`, `script_path_rel` のみ。
  - 入力データ、出力成果物、実行ログ本体のハッシュ採取・記録処理が存在しない。
- Impact:
  - 生成物・ログの改ざん検知ができず、ALCOA++準拠の監査証跡として不十分。
- Prescriptive fix:
  - 実行前後で対象アーティファクト（入力、出力、ログ、主要パラメータ）を列挙し、SHA-256を計算して監査メタデータへ保存する。
  - 監査レコードに「対象ファイル一覧 + 各ハッシュ + 集約ハッシュ」を追加する。

### Finding C (Major): Humble Object pattern violation in UI layer
- Standard: `4. PyQt / PySide モダンUIアーキテクチャ標準` の「Viewは複雑ロジックを持たない」
- Evidence:
  - `src/lcr/ui/main_window.py:448-517` (`_show_create_env_dialog`) で解析・推薦・定義合成ロジックをUIクラスが直接実行。
  - `src/lcr/ui/main_window.py:619-760` (`_run_container`) で互換性判定・選択理由構築・JITビルド分岐などの業務ロジックをUIに保持。
- Impact:
  - UIテストが重くなり、ビジネスロジックの単体検証容易性と保守性が低下。
- Prescriptive fix:
  - 上記ロジックをUseCase/Presenterへ移し、`MainWindow` は入力収集・表示更新・イベント配線のみ担当する。
  - UI層はDTOを受け取るだけの構造に再編し、分岐判定をドメインサービスへ集約する。

## 3) Verdict
- Pytestは全件Passだが、上記基準違反（Critical 2件, Major 1件）により **REJECT**。
- Final status string: `REJECT_TO_IMPLEMENT`
