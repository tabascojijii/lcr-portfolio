# Audit Report — docs/plan.md

- **監査日**: 2026-05-02
- **監査者**: Auditor
- **判定**: **REJECT（計画修正指示）**
- **基準文書**: `docs/reference_standards.md`, `docs/requirement.md`

---

## 判定根拠サマリー

`docs/plan.md` は `reference_standards.md` で義務付けられた複数の基準を「現状分析」では列挙しながら、**修正計画（Step 3）から脱落させている**。また、実装仕様に技術的誤りが存在する。以下 5 件の違反により REJECT とする。

---

## 違反 1 — `constraints.txt` 計画の完全欠落【CRITICAL】

**違反した基準**: `reference_standards.md` §2「pipのデッドロック回避」  
> 「`constraints.txt` を用いて探索範囲を厳格に制限すること」

**状況**: `plan.md` § 1.3 の現状分析で `constraints.txt` が **未実装** と正しく認識されているにもかかわらず、§ 2（問題分類）・§ 3（フェーズ別実装計画）の両方に **一切の修正タスクが存在しない**。既知の基準違反が意図的に先送りされている。

**修正ヒント**:  
Step 3 に `P1-3: constraints.txt によるpipデッドロック回避` を追加し、`base.Dockerfile.j2` テンプレートおよび `generator.py` での生成ロジックに `--constraint /app/constraints.txt` を組み込む計画を記述すること。Auditor確認基準は「生成済みDockerfileに`--constraint`オプションが含まれること」とすること。

---

## 違反 2 — Dockerfile ダイジェスト実装仕様の技術的誤り【CRITICAL】

**違反した基準**: `reference_standards.md` §2「ダイジェストによる完全固定」  
> 「必ずSHA256ダイジェストを使用し、ベースイメージの不変性を保証すること」

**状況 A — 二重 `sha256:` プレフィックス**:  
`plan.md` § 3 P1-1 の JSON 定義例が `"digest": "sha256:c1234..."` であるにもかかわらず、Jinja2 テンプレートが `FROM {{ base_image }}@sha256:{{ base_image_digest }}` となっている。これを展開すると `FROM python:2.7-slim@sha256:sha256:c1234...` となり Docker が拒否する無効な Dockerfile が生成される。

**状況 B — フォールバック許容による「必ず」要件違反**:  
```dockerfile
{% if base_image_digest %}
FROM {{ base_image }}@sha256:{{ base_image_digest }}
{% else %}
FROM {{ base_image }}   ← 可変タグでのビルドを黙認
{% endif %}
```
`else` 分岐の存在が「必ず SHA256 ダイジェストを使用する」という絶対要件と矛盾する。ダイジェストが未定義のイメージはビルド前のバリデーションでエラーを起こすべきである。

**修正ヒント**:  
- JSON には `sha256:` プレフィックスを含まないハッシュ値のみ格納する（例: `"digest": "c1234..."`）か、テンプレートを `FROM {{ base_image }}@{{ base_image_digest }}` に変更する（JSON 側に `sha256:` を含める）。どちらか一方に統一すること。  
- `{% else %}` フォールバックを削除し、`base_image_digest` が空の場合は `generator.py` 内でビルド前バリデーションエラーを raise するよう仕様を改める。

---

## 違反 3 — ALCOA++ 監査証跡にコンテナイメージダイジェストが欠落【HIGH】

**違反した基準**: `reference_standards.md` §3「環境とコードのハッシュ記録」  
> 「実行ログには、コンテナイメージのダイジェスト値と、実行時のGitコミットハッシュを必ず記録すること」

**状況**: `plan.md` § 3 P1-2 の `execution_manifest.json` 仕様には `"image": config["image"]`（タグ名のみ）が含まれるが、**イメージのダイジェスト値が含まれていない**。タグは可変であり、同一タグが異なるイメージを指す可能性があるため、タグのみの記録では再現性は保証されない。  

また、§3 は「すべての入出力データ、パラメータファイル、および実行ログ自体に暗号学的ハッシュ関数を適用」することを要求しているが、計画は入力スクリプトのハッシュのみを対象としており、入力データファイルおよびパラメータファイルのハッシュ計算が計画に含まれていない。

**修正ヒント**:  
- `manifest["image_digest"]` に `docker image inspect --format='{{index .RepoDigests 0}}'` の出力を格納するステップを P1-2 の仕様に追加する。  
- 少なくとも実行スクリプトと入力データファイル（存在する場合）の SHA-256 を manifest に含める方針を計画に明記すること。  
- Auditor 確認基準に `execution_manifest.json` に `image_digest` フィールドが含まれることを追加すること。

---

## 違反 4 — §2 の「アーカイブリポジトリ」・「マルチステージビルド」が現状評価・計画から完全欠落【HIGH】

**違反した基準**: `reference_standards.md` §2  
> 「アーカイブ・リポジトリへのリダイレクト」「マルチステージビルドの強制」

**状況**: `plan.md` § 1.3 の準拠状況テーブルには `FROM` ダイジェスト固定と `constraints.txt` のみが掲載され、§2 で明示的に要求されている以下の 2 基準の評価が存在しない:  
- `old-releases.ubuntu.com` / `archive.debian.org` への APT ソース書き換え  
- OpenCV 等 C++ ライブラリのマルチステージビルド（ビルド環境と実行環境の分離）  

LCR の主目的が「Python 2.7 / OpenCV 2.4 等の EOL スタックのコンテナ化」であることを踏まえると、これらの未評価は重大な監査漏れである。

**修正ヒント**:  
- § 1.3 の準拠状況テーブルに上記 2 基準の行を追加し、現状を調査・記録すること。  
- 「未実装」または「未確認」の場合は P1 または P2 タスクとして Step 3 に追加する。既に実装済みであれば「実装済」とし Auditor 確認基準を明示すること。

---

## 違反 5 — §4「シグナル・スロット命名規則」の評価欠落【MEDIUM】

**違反した基準**: `reference_standards.md` §4「シグナル・スロットの命名規則」  
> 「シグナルは過去分詞形、スロットは動作を示す動詞を使用し一貫性のある命名を行うこと」

**状況**: `plan.md` § 1.3 の準拠状況テーブルに命名規則の評価項目が存在しない。現在 `ContainerWorker.log_updated` Signal は §4 準拠だが、他のシグナル・スロットの命名に関する評価が行われていない。Humble Object 適用（P2-2）でシグナル・スロットを新規追加する際に命名規則違反が発生するリスクがある。

**修正ヒント**:  
- § 1.3 に「シグナル・スロット命名規則（§4）」の行を追加し、既存コードを調査して準拠状況を記録すること。  
- P2-2 の Presenter 実装仕様に「新規追加するシグナル・スロットは §4 命名規則に準拠すること」を明記し、Auditor 確認基準に命名チェックを追加すること。

---

## 修正が不要な点（PASS 項目）

以下は計画として適切に記述されている：

| 項目 | 評価 |
|---|---|
| P0-1〜P0-5 の各修正方針（具体的・処方的） | PASS |
| Phase 4 再検証シナリオ 3 件の定義（requirement.md 準拠） | PASS |
| EMCSモデルに基づく Auditor 判定基準テーブル（§5） | PASS |
| `IContainerWorker(abc.ABC)` インターフェース計画（§4準拠） | PASS |
| Humble Object 移譲先（`MainWindowPresenter`）の明示 | PASS |
| ALCOA++ `git_commit` + `source_hash` の記録計画（§3 部分準拠） | PASS |

---

## 修正指示サマリー（Architect 向け）

| 優先度 | 指示 |
|---|---|
| CRITICAL | 違反1: Step 3 に P1-3 として `constraints.txt` タスクを追加せよ |
| CRITICAL | 違反2: P1-1 の JSON/テンプレートのダイジェスト形式統一と `else` フォールバック削除を仕様に反映せよ |
| HIGH | 違反3: P1-2 の manifest 仕様に `image_digest` フィールドと入力ファイルハッシュを追加せよ |
| HIGH | 違反4: §1.3 にアーカイブリポジトリ・マルチステージビルドの評価行を追加し、未実装なら Step 3 にタスク化せよ |
| MEDIUM | 違反5: §1.3 にシグナル・スロット命名規則の評価を追加し、P2-2 の仕様に命名規約準拠を明記せよ |
