# LCR 実装計画 (Architect Plan)

- 作成日: 2026-05-03
- 作成者: Architect
- 対象: Phase 4 再検証 + 業界標準準拠実装
- 参照: `docs/requirement.md`, `docs/reference_standards.md`
- 注記: 指定の `docs/core_philosophy.md` と `docs/requirements.md` はリポジトリ上に存在せず、要件文書は `docs/requirement.md` を採用した。

## 1. 目的と完了条件

### 1.1 目的
- Phase 4（Self-Learning Loop）の再検証を最優先で実施し、根拠付きで合格を示す。
- `reference_standards.md` の必須規約（Docker再現性、ALCOA++、Humble Object、IF規律）を実装に反映する。
- 監査可能な成果（コード差分、テスト結果、実行ログ）を揃える。

### 1.2 完了条件（DoD）
- `pytest tests/ -v` が `FAILED=0 / ERROR=0`。
- Phase 4 再検証 3シナリオ（遺産救済・即時反映・失敗/キャンセル安全性）合格。
- 生成 Dockerfile が digest 固定・EOL対策・constraints・必要時マルチステージを満たす。
- 実行結果に `execution_manifest.json` と `execution_manifest.sha256` を出力し、追跡可能性を満たす。

## 2. 規約マッピング（実装必須）

### 2.1 ガバナンス（§1）
- Builder/Validator分離を前提に、監査は差分とテスト結果を元に客観判定する。
- REJECT 時は違反箇所・違反規約・修正指示を必ず提示する。

### 2.2 Docker再現性（§2）
- `FROM` はタグ禁止、`@sha256:` digest を必須化。
- EOL イメージは archive リポジトリ設定を自動適用。
- `pip install` は `constraints.txt` を必須適用（特に EOL）。
- C/C++ ビルドを伴う定義はマルチステージ化。

### 2.3 データ完全性（§3）
- 実行ログに `git_commit`, `image_digest`, `source_hash` を記録。
- 入出力/パラメータ/manifest に SHA-256 を付与。
- 記録パスはプロジェクトルートからの相対パスで統一。

### 2.4 UIアーキテクチャ（§4）
- MainWindow は UI 操作に限定（Humble Object）。
- Docker実行準備・業務ロジックは Presenter/UseCase 側へ移譲。
- `abc.ABC` または `typing.Protocol` で境界IFを明示。
- シグナル/スロット命名は規約準拠（過去分詞/動詞）。

## 3. 実装フェーズ

### Phase A: ベースライン確認
1. 既存テスト実行: `pytest tests/ -v`。
2. 失敗を以下に分類してチケット化。
- GUI依存クラッシュ（ヘッドレス非対応）
- テスト定義ミス（fixture誤解釈等）
- ロジック不整合（package解決、rule ID誤用）
3. 監査用に失敗ログを保存（相対パス）。

### Phase B: P0修正（全テスト通過）
1. GUI依存テストに `pytest.importorskip("PySide6.QtWidgets")` を適用。
2. pytest に誤収集されるヘルパー関数の命名修正（`test_` 接頭辞除去）。
3. package 解決ロジックと期待値を整合（`requests` の pip 解決を保証）。
4. ルール参照テストは image tag ではなく rule ID を使用。
5. 再実行で `FAILED=0 / ERROR=0` を確認。

### Phase C: Phase 4 再検証（最優先要件）
1. 遺産救済: 既存環境 ID を保持したまま再構築成功を確認。
2. 即時反映: 新規作成後に UI リストへ即時反映、再起動不要を確認。
3. 失敗/キャンセル: 停止・失敗時のクラッシュなし、ロールバック実行を確認。
4. 自動テスト追加。
- `save_user_knowledge` のアトミック書き込み
- メタデータキャッシュ無効化
- `rollback_definition` の整合性

### Phase D: 規約準拠実装（P1/P2）
1. Digest固定。
- `library.json` 等メタデータに `base_image_digest` を保持。
- digest 未設定時は生成時 `ValueError` で停止（可変タグ禁止）。
2. EOL対策。
- EOL判定時 `use_archive_repo=True` を自動化。
- EOLで `constraints.txt` 未提供なら `ValueError`。
3. マルチステージ。
- OpenCV 等を含む定義は builder/runtime 分離テンプレートを使用。
4. ALCOA++ manifest。
- `execution_manifest.json` に `git_commit`, `image_digest`, `source_hash`, `input_file_hashes` を記録。
- `execution_manifest.sha256` を同ディレクトリ出力。
5. Humble Object。
- MainWindow の `subprocess.run`/Docker構築ロジックを Presenter へ移譲。
- Worker IF を `IContainerWorker` として抽象化。

## 4. 検証計画

### 4.1 自動検証
- `pytest tests/ -v`
- 追加ユニットテスト（knowledge更新、rollback、manifest生成）
- Dockerfile 生成テスト。
  - `FROM ...@sha256:` を含む
  - EOL時 archive repo を含む
  - `pip install --constraint` を含む
  - multi-stage で `COPY --from=builder` を含む

### 4.2 手動検証
- GUI実行でリアルタイムログ表示・フリーズなしを確認。
- 新規環境即時反映と即時実行可を確認。
- 失敗/キャンセル時にクラッシュなし、ロールバック発動を確認。

### 4.3 監査判定（REJECT条件）
- テスト失敗が1件でも残る。
- digest固定未実施または可変タグ fallback が残る。
- manifest の必須項目不足、またはパスが絶対パス。
- MainWindow が依然として業務ロジックを直接保持。

## 5. 成果物

- `docs/plan.md`（本計画）
- テスト修正・追加（`tests/`）
- 規約準拠実装（`src/` + Dockerfile テンプレート）
- 監査証跡（pytest結果、再検証結果、manifestサンプル）

## 6. 実施順序

1. Baseline テスト実行
2. P0修正でテスト全件通過
3. Phase 4 再検証（手動+自動）
4. P1/P2 実装
5. 総合再テスト
6. 監査判定用エビデンス提出
