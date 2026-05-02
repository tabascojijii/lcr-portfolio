# Audit Report — docs/plan.md

- **監査日**: 2026-05-02
- **監査者**: Auditor
- **判定**: **REJECT（計画修正指示）**
- **基準文書**: `docs/reference_standards.md`, `docs/requirement.md`

---

## 前回 REJECT 指摘の解消確認

| 前回違反 | 解消確認 |
|---|---|
| 違反1: `execution_manifest.sha256` サイドカーファイル欠落 | ✅ P1-2 に `manifest_bytes` → `hashlib.sha256` → `.sha256` 書き出しが追加済み |
| 違反2: `_get_image_digest()` の `return "unknown"` と Auditor 基準「unknown は REJECT」の自己矛盾 | ✅ `return "unknown"` を削除し、`RuntimeError` を raise する仕様に統一済み |
| 違反3: `_hash_input_files()` の辞書キーへの相対パス変換未明示 | ✅ `rel_key = str(Path(f).relative_to(PROJECT_ROOT))` を明示し、Auditor 確認基準にもパス形式チェックを追加済み |

しかし、新たな §3 違反が 1 件、および §2 準拠の実施漏れリスクが 1 件確認されたため、REJECT とする。

---

## 違反 1（CRITICAL）— `_get_image_digest()` がローカルビルドイメージで常時 RuntimeError を発生させる

**違反した基準**: `reference_standards.md` §3「環境とコードのハッシュ記録」  
> 「実行ログには、コンテナイメージのダイジェスト値を必ず記録し、不変性を担保すること」

**状況**:  
`plan.md` § 3 P1-2 の `_get_image_digest()` は以下の実装を指示している:

```python
result = subprocess.run(
    ["docker", "image", "inspect", "--format={{index .RepoDigests 0}}", image],
    capture_output=True, text=True, check=True
)
digest = result.stdout.strip()
if not digest.startswith("sha256:"):
    raise RuntimeError(...)
```

`docker image inspect --format={{index .RepoDigests 0}}` は、イメージがレジストリへ push 済みの場合にのみ有効な `RepoDigests[0]` を取得する。**LCR の主要ワークフローはイメージをローカルでビルドするものであり、push されていないため `RepoDigests` は常に空リストとなる。** 結果として `result.stdout.strip()` は空文字列 `""` となり、`not "".startswith("sha256:")` は常に True → `RuntimeError` が必ず発生する。

これにより `prepare_run_config()` は全ビルドで例外を送出し、`execution_manifest.json` が一切生成されない。ALCOA++ 要件（§3）が**主要ユースケースで完全に機能しない**状態となる。

**修正ヒント**:  
ローカルビルドイメージにも対応するため、`RepoDigests[0]` ではなく **Image ID（`{{.Id}}`）** を使用すること。Image ID は `docker build` によって生成されたイメージに対して常に取得可能な sha256 ダイジェストであり、コンテンツアドレス指定によるイメージの不変性を担保できる。

```python
def _get_image_digest(image: str) -> str:
    """コンテナイメージの ID ダイジェストを取得する（ALCOA++ §3 準拠）
    
    RepoDigests（push 済みイメージのみ有効）ではなく Image ID を使用することで、
    ローカルビルドイメージにも対応する。
    """
    result = subprocess.run(
        ["docker", "image", "inspect", "--format={{.Id}}", image],
        capture_output=True, text=True, check=True
    )
    digest = result.stdout.strip()
    if not digest.startswith("sha256:"):
        raise RuntimeError(
            f"image_digest for '{image}' is not a valid sha256 digest: '{digest}'. "
            "Ensure the image exists locally (docker images)."
        )
    return digest
```

Auditor 確認基準の `image_digest` に関する記述は変更不要（`sha256:` で始まること、`unknown` は REJECT、という基準はそのまま維持可能）。

---

## 懸念事項 1（MEDIUM）— `constraints.txt` が EOL スタックで任意適用（非強制）

**関連基準**: `reference_standards.md` §2「pip のデッドロック回避」  
> 「古いパッケージの依存関係解決におけるバックトラッキング（無限ループ）を防ぐため、`constraints.txt` を用いて探索範囲を**厳格に制限すること**」

**状況**:  
P1-3 の実装仕様は `config.get("constraints_file")` が設定されている場合のみ `--constraint` を有効化する opt-in 方式となっている。標準は EOL パッケージに対して `constraints.txt` の使用を**義務付けている**が、現計画では定義者が `constraints_file` を設定しなければ EOL スタックでも制約なしでビルドが進行する。

**修正ヒント**:  
`generator.py` の `render_dockerfile()` 内で、EOL イメージ検出ロジック（P1-4 にて追加予定）と連動させ、EOL スタックビルド時には `constraints_file` の提供を必須とするか、またはデフォルトの `constraints.txt` を自動生成・適用する仕様を P1-3 に明記すること。少なくとも Auditor 確認基準に「EOL スタック（Python 2.7 / 3.5 / 3.6 等）のビルドで `--constraint` オプションが含まれること」を追加すること。

---

## PASS 項目（変更不要）

| 項目 | 評価 |
|---|---|
| P0-1〜P0-5 の各修正方針（具体的・処方的） | PASS |
| Phase 4 再検証シナリオ 3 件の定義（requirement.md 準拠） | PASS |
| EMCSモデルに基づく Auditor 判定基準テーブル（§5） | PASS |
| P1-1: `else` フォールバック削除・`ValueError` バリデーション・JSON 側 `sha256:` プレフィックス方針 | PASS |
| P1-2: `git_commit`, `source_hash`, `image_digest`, `input_file_hashes`, `execution_manifest.sha256` サイドカーの計画 | PASS（`_get_image_digest` 修正後） |
| P1-3: `constraints.txt` によるpipデッドロック回避メカニズム計画 | PASS（強制化懸念あり） |
| P1-4: EOL ビルド時アーカイブリポジトリ自動有効化計画 | PASS |
| P1-5: マルチステージビルド対応計画 | PASS |
| P2-1: `IContainerWorker(abc.ABC)` インターフェース定義計画 | PASS |
| P2-2: Humble Object 移譲先の明示・命名規則準拠の明記 | PASS |
| manifest 内パスの相対パス変換ロジック明示（`script_path`, `input_file_hashes` キー） | PASS |
| `execution_manifest.sha256` サイドカーによる改ざん検知 | PASS |

---

## 修正指示サマリー（Architect 向け）

| 優先度 | 指示 |
|---|---|
| **CRITICAL** | 違反1: `_get_image_digest()` の `--format={{index .RepoDigests 0}}` を `--format={{.Id}}` に変更し、ローカルビルドイメージで RuntimeError が発生しない仕様に修正すること。エラーメッセージも「push 済みイメージにのみ有効」ではなく「イメージが存在しない」旨に更新すること |
| **MEDIUM** | 懸念1: P1-3 の仕様に EOL スタックビルド時の `constraints.txt` 強制適用ロジックを追加するか、または Auditor 確認基準に EOL スタックでの `--constraint` 存在チェックを追記すること |
