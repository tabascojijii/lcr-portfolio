# Audit Report — docs/plan.md

- **監査日**: 2026-05-02
- **監査者**: Auditor
- **判定**: **REJECT（計画修正指示）**
- **基準文書**: `docs/reference_standards.md`, `docs/requirement.md`

---

## 前回 REJECT 指摘の解消確認

前回監査（同日）で指摘した 5 件の違反（violations 1〜5）はすべて解消済みと確認した。

| 前回違反 | 解消確認 |
|---|---|
| 違反1: `constraints.txt` 計画欠落 | ✅ P1-3 として Step 3 に追加済み |
| 違反2: ダイジェスト形式の技術的誤り | ✅ `else` フォールバック削除・`ValueError` バリデーション・JSON側 `sha256:` プレフィックス方針を明記 |
| 違反3: ALCOA++ manifest への `image_digest` 欠落 | ✅ `_get_image_digest()` ヘルパーと `input_file_hashes` を追加 |
| 違反4: アーカイブリポジトリ・マルチステージビルド評価欠落 | ✅ § 1.3 に評価行追加、P1-4 / P1-5 としてタスク化 |
| 違反5: シグナル・スロット命名規則の評価欠落 | ✅ § 1.3 に評価行追加、P2-2 仕様に命名規則準拠を明記 |

しかし、今回の計画に新たな §3 違反が 3 件確認されたため、REJECT とする。

---

## 判定根拠サマリー

`reference_standards.md` §3「データ完全性と監査証跡」は ALCOA++ 原則に基づく 3 つの独立した要件を義務付けている。現行の `plan.md` P1-2 はそのうち 2 つを満たさず、さらに実装仕様内に自己矛盾（Violation B）が存在する。

---

## 違反 1 — 実行ログ自体のハッシュ化が計画に存在しない【HIGH】

**違反した基準**: `reference_standards.md` §3「ハッシュによる改ざん検知」  
> 「すべての入出力データ、パラメータファイル、**および実行ログ自体**に暗号学的ハッシュ関数（SHA-256等）を適用し、改ざんを検知可能な状態にすること」

**状況**:  
`plan.md` § 3 P1-2 は `execution_manifest.json` を書き出す実装を定義しているが、**manifest ファイル自体のハッシュを外部に記録するステップが存在しない**。manifest はビルド完了後に任意に書き換えられてもシステムが検知できず、「改ざんを検知可能な状態」という要件を満たさない。

標準は「入力データ・パラメータ・実行ログの三者すべて」のハッシュ化を要求している。入力ファイルと環境パラメータ（git_commit, image_digest）は計画されているが、ログ自体（manifest）のハッシュ化は計画から完全に脱落している。

**修正ヒント**:  
`prepare_run_config()` の `execution_manifest.json` 書き出し直後に、manifest の SHA-256 を算出して `execution_manifest.sha256` サイドカーファイルとして同一ディレクトリに保存するステップを P1-2 の仕様に追加すること。実装例：

```python
manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode()
manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
(host_output_dir / "execution_manifest.sha256").write_text(
    f"{manifest_hash}  execution_manifest.json\n"
)
```

Auditor 確認基準に「実行後、`execution_manifest.sha256` が同ディレクトリに存在し、その内容が manifest ファイルの SHA-256 と一致すること」を追加すること。

---

## 違反 2 — `_get_image_digest()` のサイレント失敗が REJECT 基準と自己矛盾【MEDIUM】

**違反した基準**: `reference_standards.md` §3「環境とコードのハッシュ記録」  
> 「実行ログには、コンテナイメージのダイジェスト値を必ず記録し、不変性を担保すること」

**状況**:  
`plan.md` § 3 P1-2 の `_get_image_digest()` ヘルパーは `except Exception: return "unknown"` でサイレントに失敗し、`image_digest` フィールドを `"unknown"` で埋めることを許容している。一方で、**同じ P1-2 の Auditor 確認基準には「`image_digest` が `sha256:` で始まるダイジェスト値であること（`unknown` は REJECT）」** と記載されている。

つまり計画が **「unknownが許容される実装仕様」と「unknownはREJECT」という Auditor 基準を同一のタスク内に共存させており自己矛盾**している。`docker image inspect` が失敗した場合は、サイレントに `"unknown"` を記録するのではなく、ビルドを中止するか警告を raise すべきである。

**修正ヒント**:  
`_get_image_digest()` の `except` ブロックを `return "unknown"` ではなく `raise RuntimeError(...)` に変更するか、呼び出し元で `"unknown"` の場合に `ValueError` を raise してビルドを中断する仕様に変更すること。計画の実装仕様と Auditor 確認基準を一致させること。

---

## 違反 3 — `_hash_input_files()` の辞書キーに相対パス保証がない【MEDIUM】

**違反した基準**: `reference_standards.md` §3「相対パスによるポータビリティ」  
> 「ログファイルやスクリプト内のパス指定は、他環境での検証可能性を維持するため、すべてプロジェクトルートからの相対パスで記述すること」

**状況**:  
`plan.md` § 3 P1-2 の `_hash_input_files()` ヘルパーは `hashes[str(f)] = ...` のように `f` を文字列化したものを辞書キーとする。`f` が `Path` オブジェクトの場合、絶対パス（例: `C:\dev\lcr\data\input.csv`）がそのまま `execution_manifest.json` に記録される。  

`"script_path"` にはコメントで `# プロジェクトルートからの相対パス` と記載されているが、変換ロジックが示されていない。他の環境で manifest を参照した際にパスが無効となり、再現性検証が不可能になる。

**修正ヒント**:  
`_hash_input_files()` の辞書キーおよび `manifest["script_path"]` の値は、`Path(f).relative_to(PROJECT_ROOT)` を用いてプロジェクトルートからの相対パスに変換する実装を P1-2 の仕様に明示すること。また Auditor 確認基準に「`execution_manifest.json` 内のすべてのパス値が相対パスであること」を追加すること。

---

## 修正が不要な点（PASS 項目）

| 項目 | 評価 |
|---|---|
| P0-1〜P0-5 の各修正方針（具体的・処方的） | PASS |
| Phase 4 再検証シナリオ 3 件の定義（requirement.md 準拠） | PASS |
| EMCSモデルに基づく Auditor 判定基準テーブル（§5） | PASS |
| P1-1: `else` フォールバック削除・`ValueError` バリデーション | PASS |
| P1-2: `git_commit`, `source_hash`, `input_file_hashes` の計画 | PASS |
| P1-3: `constraints.txt` によるpipデッドロック回避計画 | PASS |
| P1-4: EOL ビルド時アーカイブリポジトリ自動有効化計画 | PASS |
| P1-5: マルチステージビルド対応計画 | PASS |
| P2-1: `IContainerWorker(abc.ABC)` インターフェース定義計画 | PASS |
| P2-2: Humble Object 移譲先の明示・命名規則準拠の明記 | PASS |

---

## 修正指示サマリー（Architect 向け）

| 優先度 | 指示 |
|---|---|
| HIGH | 違反1: P1-2 に `execution_manifest.sha256` サイドカーファイル書き出しステップを追加せよ。Auditorチェックリスト § 4.3 に確認項目を追加すること |
| MEDIUM | 違反2: `_get_image_digest()` の `return "unknown"` を `raise RuntimeError(...)` に変更するか、呼び出し元で unknown を検出して中断する仕様に統一せよ。Auditor 基準と実装仕様の矛盾を解消すること |
| MEDIUM | 違反3: `_hash_input_files()` と `script_path` にプロジェクトルート相対パス変換ロジック（`Path.relative_to(PROJECT_ROOT)`）を仕様に明示し、Auditor 確認基準にパス形式チェックを追加せよ |
