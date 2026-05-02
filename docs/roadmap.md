# LCR 実装ロードマップ (PM Plan)

- **作成日**: 2026-05-02
- **作成者**: PM
- **参照**: `docs/plan.md` (Architect)、`docs/reference_standards.md`
- **重点方針**: データ完全性・監査証跡の実装漏れを防ぐため、依存関係と検証タイミングを明確化した作業順序を定める

---

## ロードマップ全体像

```
Milestone 1  テスト全件 PASS（P0）
     ↓
Milestone 2  Phase 4 機能再検証（既存実装の安全性確認）
     ↓
Milestone 3a データ完全性・監査証跡（P1-2）  ← 最優先
     ↓
Milestone 3b ビルド再現性（P1-1 → P1-3 → P1-4）
     ↓
Milestone 3c ビルド最適化（P1-5）
     ↓
Milestone 3d アーキテクチャ品質（P2-1 → P2-2）
```

---

## Milestone 1: テスト全件 PASS（P0）

**担当**: Implementer  
**ブロッカー**: 全後続 Milestone の前提条件  
**合格判定**: Auditor — `pytest tests/ -v` にて `0 FAILED, 0 ERROR`

### タスク一覧（依存なし、並行実施可）

| タスク | 対象ファイル | 修正内容 |
|--------|-------------|---------|
| P0-1 | `tests/test_dialog_reason_display.py` | 冒頭に `pytest.importorskip("PySide6.QtWidgets", ...)` を追加しヘッドレス環境でスキップ |
| P0-3 | `tests/test_button_states.py` | 同上（P0-1 と同一パターン） |
| P0-2 | `tests/test_analyzer.py` | `def test_file(...)` → `def _analyze_file(...)` にリネーム（pytest fixture 誤検知を排除） |
| P0-5 | `tests/test_synthesis_intelligence.py` | `synthesize_definition_config(analysis, "lcr-py36-ml-classic")` → `"py36-ds"` に修正（ルールID不一致の解消） |
| P0-4 | `library.json` または `analyzer.py` | `requests` に `pip: ["requests"]` を追加するか `apt-first` 優先ロジックを修正 |

### Auditor チェック（Milestone 1 完了条件）

- [ ] `pytest tests/ -v` → **0 FAILED, 0 ERROR**
- [ ] SKIPPED は `pytest.importorskip` によるヘッドレス環境スキップのみ

---

## Milestone 2: Phase 4 機能再検証

**担当**: Implementer  
**前提**: Milestone 1 完了  
**合格判定**: Auditor — manual シナリオ 3 件 + 追加自動テスト PASS

### 目的

既存の Phase 4 実装（Knowledge Update・Real-time Feedback・Dynamic Refresh）に対し、  
ID消失・フリーズ・ロールバックの各障害シナリオを自動テストで補強する。  
本 Milestone を先行させることで、後続 Milestone のデータ完全性実装が既存機能を破壊していないことを検証可能にする。

### タスク一覧

| タスク | 詳細 |
|--------|------|
| 2-a manual 検証 | シナリオ1: 既存環境IDでビルド → IDが `custom-env` に化けないこと |
| 2-b manual 検証 | シナリオ2: 新規環境作成後 → 再起動なしでコンボボックスに即時反映 |
| 2-c manual 検証 | シナリオ3: Stop押下または意図的失敗 → クラッシュなし・`rollback_definition()` 動作 |
| 2-d 自動テスト追加 | `tests/test_user_knowledge.py` に atomic write・キャッシュ無効化・ロールバックの単体テストを追加 |

### Auditor チェック（Milestone 2 完了条件）

- [ ] manual シナリオ 1〜3 すべて合格
- [ ] `test_save_user_knowledge_atomic` PASSED
- [ ] `test_metadata_cache_invalidation` PASSED
- [ ] `test_rollback_definition` PASSED

---

## Milestone 3a: データ完全性・監査証跡 — ALCOA++ manifest（P1-2）

**担当**: Implementer  
**前提**: Milestone 2 完了  
**合格判定**: Auditor — manifest ファイルの存在・内容・サイドカー整合性を検証  
**優先根拠**: `reference_standards.md` §3 の核心要件。最小変更で最大のコンプライアンス価値を提供する。Milestone 3b（ダイジェスト固定）より先に実施することで、移行期間中の実行も含め漏れなく証跡を残せる。

### タスク一覧

| タスク | 対象 | 内容 |
|--------|------|------|
| 3a-1 | `ContainerManager.prepare_run_config()` | `execution_manifest.json` を出力ディレクトリに書き出す（`timestamp`, `git_commit`, `source_hash`, `image`, `image_digest`, `script_path`, `input_file_hashes`） |
| 3a-2 | 同上 | `execution_manifest.sha256` サイドカーファイルを生成（改ざん検知要件） |
| 3a-3 | パス正規化 | `script_path` および `input_file_hashes` のキーをプロジェクトルートからの**相対パス**で記録 |
| 3a-4 | ヘルパー実装 | `_get_git_commit_hash()`, `_get_image_digest()`, `_hash_input_files()` を実装 |

### データ完全性ルール（逸脱は REJECT）

| フィールド | 要件 |
|-----------|------|
| `git_commit` | `sha` 形式の文字列。`"unknown"` は REJECT |
| `image_digest` | `sha256:` で始まるダイジェスト値。`"unknown"` は REJECT |
| `source_hash` | スクリプト内容の SHA-256 |
| `input_file_hashes` | 入力ファイルが存在する場合、全ファイルの SHA-256 を含む |
| `script_path` / `input_file_hashes` キー | すべて相対パス（絶対パスは REJECT） |
| `execution_manifest.sha256` | manifest ファイルの SHA-256 と一致する（不一致は REJECT） |

### Auditor チェック（Milestone 3a 完了条件）

- [ ] 実行後 `data/results/<timestamp>/execution_manifest.json` が存在する
- [ ] `git_commit`, `source_hash`, `image_digest` フィールドがすべて存在する
- [ ] `image_digest` が `sha256:` で始まる（`unknown` は REJECT）
- [ ] 入力ファイルが存在する場合 `input_file_hashes` に各ファイルの SHA-256 が含まれる
- [ ] `execution_manifest.sha256` が同ディレクトリに存在し、内容が manifest の SHA-256 と一致する
- [ ] `script_path` および `input_file_hashes` のキーがすべて相対パスである

---

## Milestone 3b: ビルド再現性（P1-1 → P1-3 → P1-4）

**担当**: Implementer  
**前提**: Milestone 3a 完了（manifest で image_digest が記録されていることで、ダイジェスト固定の効果を即座に監査証跡で確認できる）  
**合格判定**: Auditor — 生成 Dockerfile の内容検査

### 実施順序と根拠

```
P1-1（ダイジェスト固定）→ P1-3（constraints.txt）→ P1-4（アーカイブリポジトリ）
```

- P1-1 を先行させることで、Milestone 3a の manifest に記録される `image_digest` が再現性を持つ
- P1-3 は EOL スタックビルドの信頼性向上。P1-4 の前提（EOL パターン判定ロジックを共用）
- P1-4 は P1-3 の EOL 検出ロジック（`EOL_IMAGE_PATTERNS`）に依存するため後続

### P1-1: Dockerfile `FROM` ダイジェスト固定

| タスク | 対象 | 内容 |
|--------|------|------|
| 1-1-a | `library.json` | `_meta.golden_images` に各ベースイメージの `digest` フィールドを追加 |
| 1-1-b | `base.Dockerfile.j2` | `FROM {{ base_image }}@{{ base_image_digest }}` に変更、`{% else %}` フォールバックを**削除** |
| 1-1-c | `generator.py` | `render_dockerfile()` が `base_image_digest` を自動解決。未設定時は `ValueError` を raise |

**REJECT 基準**: `FROM` 行にダイジェストがない、または `{% else %}` フォールバックが存在する

### P1-3: `constraints.txt` による pip デッドロック回避

| タスク | 対象 | 内容 |
|--------|------|------|
| 1-3-a | `generator.py` | `constraints_file` をビルドコンテキストにコピーし `use_constraints=True` をセット |
| 1-3-b | `base.Dockerfile.j2` | `{% if use_constraints %}` で `COPY constraints.txt` と `--constraint` オプションを追加 |
| 1-3-c | `generator.py` | EOL イメージ（`python:2.*`, `python:3.5.*`, `python:3.6.*`）かつ `constraints_file` 未設定時に `ValueError` を raise |

**REJECT 基準**: `pip install` に `--constraint` がない、または EOL スタックで未設定時に `ValueError` が出ない

### P1-4: アーカイブリポジトリ EOL ビルド時自動有効化

| タスク | 対象 | 内容 |
|--------|------|------|
| 1-4-a | `generator.py` | `EOL_IMAGE_PATTERNS` でベースイメージ判定し `use_archive_repo=True` をデフォルトセット |
| 1-4-b | 検証 | Python 2.7 ベースイメージで生成された Dockerfile に `archive.debian.org` が含まれることを確認 |

**REJECT 基準**: EOL スタックビルドの Dockerfile に `archive.debian.org` 設定がない

### Auditor チェック（Milestone 3b 完了条件）

- [ ] 生成 Dockerfile の `FROM` 行に `@sha256:` が含まれる（P1-1）
- [ ] `base_image_digest` 未設定時に `generator.py` が `ValueError` を raise（P1-1）
- [ ] `{% else %}` フォールバック分岐が存在しない（P1-1）
- [ ] `pip install` コマンドに `--constraint` オプションが含まれる（P1-3）
- [ ] EOL スタックで `constraints_file` 未設定時に `ValueError` が送出される（P1-3）
- [ ] Python 2.7 ベースイメージのビルドで `archive.debian.org` ソース設定が生成される（P1-4）

---

## Milestone 3c: ビルド最適化 — マルチステージビルド（P1-5）

**担当**: Implementer  
**前提**: Milestone 3b 完了（P1-1 のダイジェスト固定が `multistage.Dockerfile.j2` にも適用されるため）  
**合格判定**: Auditor — 生成 Dockerfile の構造検査

### タスク一覧

| タスク | 対象 | 内容 |
|--------|------|------|
| 1-5-a | `library.json` | `golden_images` に `multi_stage: true` フラグを追加（OpenCV 等） |
| 1-5-b | `multistage.Dockerfile.j2` | `AS builder` / `COPY --from=builder` を持つ専用テンプレートを新規作成 |
| 1-5-c | `generator.py` | `config.get("multi_stage")` が真の場合に `multistage.Dockerfile.j2` を選択 |

**REJECT 基準**: OpenCV を含む定義のビルドで `COPY --from=builder` が使用されていない

### Auditor チェック（Milestone 3c 完了条件）

- [ ] OpenCV 含む定義のビルドで生成 Dockerfile に `AS builder` と `COPY --from=builder` が含まれる

---

## Milestone 3d: アーキテクチャ品質（P2-1 → P2-2）

**担当**: Implementer  
**前提**: Milestone 3a 完了（P2-1 のインターフェース定義が先行することで P2-2 の Humble Object リファクタが型安全に行える）  
**合格判定**: Auditor — コードレビュー + 命名規則チェック

### P2-1: `IContainerWorker` インターフェース定義

| タスク | 対象 | 内容 |
|--------|------|------|
| 2-1-a | `src/lcr/core/interface.py` | `IContainerWorker(abc.ABC)` を定義（`start()`, `stop()` 抽象メソッド） |
| 2-1-b | `ContainerWorker` | `QThread` に加え `IContainerWorker` を継承 |

**REJECT 基準**: `ContainerWorker` が `abc.ABC` または `Protocol` を継承していない

### P2-2: Humble Object パターン（規模大・慎重に実施）

| タスク | 対象 | 内容 |
|--------|------|------|
| 2-2-a | `src/lcr/presenter/main_window_presenter.py` | `MainWindowPresenter` を新規作成。`prepare_execution()`, `on_execution_finished()` を実装 |
| 2-2-b | `MainWindow._run_container()` | Docker コマンド構築・`subprocess.run`・`prepare_run_config()` 呼び出しを Presenter に移譲 |
| 2-2-c | `MainWindow._on_worker_finished()` | History 保存ロジックを Presenter に移譲 |
| 2-2-d | シグナル・スロット命名 | 新規シグナルは過去分詞形（例: `execution_started`）、新規スロットは動作動詞形（例: `update_status`）に準拠 |

**REJECT 基準**:
- `MainWindow` が `subprocess.run` を直接呼び出している
- P2-2 追加シグナルが過去分詞形でない、またはスロットが動作動詞形でない

### Auditor チェック（Milestone 3d 完了条件）

- [ ] `ContainerWorker` が `IContainerWorker(abc.ABC)` を実装している（P2-1）
- [ ] `MainWindow` が `subprocess.run` を直接呼び出していない（P2-2）
- [ ] P2-2 追加シグナルがすべて過去分詞形である（P2-2）
- [ ] P2-2 追加スロットがすべて動作動詞形である（P2-2）

---

## 実装順序サマリーと依存関係

```
[M1] P0-1, P0-2, P0-3, P0-4, P0-5（並行可）
      → Auditor: pytest 0 FAILED, 0 ERROR
           ↓
[M2] Phase 4 再検証（2-a〜2-d）
      → Auditor: manual 3 件 + 自動テスト PASS
           ↓
[M3a] P1-2 ALCOA++ manifest 記録（最優先・最小変更・最大価値）
      ┌─ _get_git_commit_hash()
      ├─ _get_image_digest()
      ├─ _hash_input_files()
      ├─ execution_manifest.json 書き出し（相対パス厳守）
      └─ execution_manifest.sha256 サイドカー生成
      → Auditor: manifest 存在・全フィールド・sha256 整合確認
           ↓
[M3b] P1-1 → P1-3 → P1-4（順序依存あり）
      P1-1: Dockerfile ダイジェスト固定（else フォールバック削除 + ValueError）
      P1-3: constraints.txt 組み込み（EOL スタックは必須化）
      P1-4: EOL ビルド時 archive.debian.org 自動有効化
      → Auditor: 生成 Dockerfile の構造検査
           ↓
[M3c] P1-5 マルチステージビルド（multistage.Dockerfile.j2 新規作成）
      → Auditor: AS builder / COPY --from=builder 確認
           ↓
[M3d] P2-1 → P2-2（順序依存あり）
      P2-1: IContainerWorker インターフェース定義
      P2-2: MainWindowPresenter による Humble Object 化（規模大）
      → Auditor: コードレビュー + 命名規則チェック
```

---

## データ完全性リスクマトリクス

以下のリスクは Auditor が REJECT 判定時に必ず指摘すること。

| リスク | 発生箇所 | REJECT 条件 | 対応 Milestone |
|--------|---------|------------|----------------|
| 監査証跡欠落 | `prepare_run_config()` | `execution_manifest.json` 不存在 | M3a |
| ハッシュ未記録 | manifest | `git_commit` / `source_hash` / `image_digest` のいずれかが欠落 | M3a |
| サイドカー欠落 | 出力ディレクトリ | `execution_manifest.sha256` 不存在 | M3a |
| 絶対パス混入 | manifest のパス値 | `script_path` または `input_file_hashes` キーが絶対パス | M3a |
| ビルド非再現 | Dockerfile `FROM` | ダイジェスト未固定・可変タグのみ | M3b（P1-1） |
| pip ループ | Dockerfile `pip install` | `--constraint` 欠落（特に EOL スタック） | M3b（P1-3） |
| ビルドツール混入 | 実行イメージ | `COPY --from=builder` 未使用（C++ ライブラリ） | M3c（P1-5） |
| ロジック汚染 | `MainWindow` | `subprocess.run` 直接呼び出し | M3d（P2-2） |

---

## 注意事項

1. **各 Milestone は Auditor の PASS 判定後に次 Milestone に進むこと。** 判定なしで先行してはならない。
2. **M3a（ALCOA++ manifest）は M3b より必ず先行する。** M3b のダイジェスト固定後に manifest を確認することで、監査証跡とビルド再現性の整合を検証できる。
3. **P2-2 は規模が大きいため、Implementer は差分を小さく保ちレビュー可能な単位で提出すること。**
4. **REJECT 時は** 違反箇所・違反した制約・修正ヒントを含む処方的メッセージを返すこと（`reference_standards.md` §1 準拠）。
