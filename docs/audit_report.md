# Audit Report — docs/roadmap.md

- **監査日**: 2026-05-03
- **監査者**: Auditor
- **対象文書**: `docs/roadmap.md`
- **判定**: **REJECT（ロードマップ修正指示）**
- **基準文書**: `docs/plan.md`、`docs/reference_standards.md`

---

## 監査スコープ

`reference_standards.md` の「§2 コンテナ構築」および「§3 データ完全性」に関連する、
`docs/roadmap.md` の作業順序・フェーズ分けを検証した。

---

## 指摘事項

### 【CRITICAL】違反1: M3d 前提条件と実装順序サマリーの矛盾（フェーズ整合性欠如）

**違反箇所**

- `docs/roadmap.md` — Milestone 3d 本文: "**前提**: Milestone 3a 完了"
- `docs/roadmap.md` — 実装順序サマリー依存関係図: `[M3c] → [M3d]`

**違反した制約**

`reference_standards.md` §2「ダイジェストによる完全固定」および「pip のデッドロック回避」は、
コンテナビルドパスを経由するすべての実装に適用される。
M3d（P2-2 Humble Object）は `generator.py` を呼び出す `Presenter.prepare_execution()` を新規作成するため、
この呼び出しパスにも M3b（P1-1 ダイジェスト固定・P1-3 constraints.txt）が先行して組み込まれていなければならない。

**問題の詳細**

M3d の本文が「前提: Milestone 3a 完了」のみを記載しているため、Implementer が本文のみを参照した場合、
M3d を M3b および M3c と並行して開始してもよいと誤解するリスクがある。

これにより以下の危険が生じる:

| リスク | 内容 |
|--------|------|
| データ完全性の空白期間 | P2-2 完了後・M3b 完了前の期間、Presenter が呼び出す `generator.py` はダイジェスト固定なし（P1-1 未適用）で Dockerfile を生成する。manifest に記録される `image_digest` は可変タグから生成されたイメージのものとなり、`reference_standards.md` §2「ダイジェストによる完全固定」に違反する |
| pip デッドロック回避未適用 | 同期間、Presenter が呼び出す Dockerfile テンプレートに `--constraint` が存在せず、EOL スタックビルドで pip バックトラッキングが発生しうる（§2「pip のデッドロック回避」違反） |
| 二重修正リスク | M3b を後から適用する際、P2-2 で新規作成した Presenter コードも修正が必要になり、実装コストが増加する |

**修正指示**

Milestone 3d の「前提」を以下のとおり修正し、実装順序サマリーの依存関係図と整合させること。

```
修正前:
前提: Milestone 3a 完了

修正後:
前提: Milestone 3c 完了
（根拠: P1-1 のダイジェスト固定・P1-3 の constraints.txt が generator.py に組み込まれた状態で
 P2-2 の Presenter を実装することで、コンテナビルドパス全体に §2 基準が適用される）
```

---

### 【CRITICAL】違反2: `git_commit: "unknown"` REJECT基準と plan.md 実装コードの矛盾（データ完全性規定の不整合）

**違反箇所**

- `docs/roadmap.md` — Milestone 3a「データ完全性ルール」: `git_commit: "sha" 形式の文字列。"unknown" は REJECT`
- `docs/plan.md` — P1-2 ヘルパー実装コード `_get_git_commit_hash()`:
  ```python
  except Exception:
      return "unknown"
  ```

**違反した制約**

`reference_standards.md` §3「環境とコードのハッシュ記録」:
> 実行ログには、コンテナイメージのダイジェスト値と、実行時のGitコミットハッシュ（`git rev-parse HEAD`）を**必ず記録**し、不変性を担保すること

「必ず記録」は例外発生時の `"unknown"` フォールバックを許容しない。ロードマップの REJECT 基準（`"unknown"` は REJECT）は §3 を正しく解釈しているが、plan.md の実装コードがこの基準を満たさない。

**問題の詳細**

Implementer が `docs/plan.md` の P1-2 実装コードをそのまま実装した場合、
`git rev-parse HEAD` が失敗する環境（git 未インストール、非 git ディレクトリ等）では
`execution_manifest.json` に `"git_commit": "unknown"` が記録される。

ロードマップの Auditor チェックは `"unknown"` を REJECT とするため、
plan.md の実装コードに従っても M3a の合格判定を得られない状態が生じている。
PM はロードマップで審査基準を厳格化したが、plan.md の実装コードを更新する修正タスクをロードマップに含めていない。

**修正指示**

Milestone 3a に以下のタスクを追加すること:

```
| 3a-5 | `_get_git_commit_hash()` | 例外発生時に "unknown" を返すフォールバックを削除し、
|      |                          | RuntimeError を raise するよう修正する。
|      |                          | git が利用不可な環境ではビルド前に明示的にエラーで停止させる。|
```

また、plan.md の P1-2 実装コードも同様に修正を要求する旨を Milestone 3a に明記すること。

---

## 問題なし確認項目

以下の点については `reference_standards.md` との整合を確認した。

| 項目 | 状態 | 確認内容 |
|------|------|---------|
| M3a（データ完全性）全体構成 | **PASS** | `execution_manifest.json`・サイドカー生成・相対パス要件がすべてカバーされている |
| M3b の内部順序（P1-1 → P1-3 → P1-4）| **PASS** | P1-4 が P1-3 の EOL 検出ロジックに依存することが明示されており、依存関係が正確 |
| M3c の前提（M3b 完了）| **PASS** | `multistage.Dockerfile.j2` にも P1-1 のダイジェスト固定が必要な点が明示されている |
| M3a → M3b の順序根拠 | **PASS** | 「移行期間中の実行も含め漏れなく証跡を残せる」根拠が明示されており、§3 に準拠 |
| M2（Phase 4 再検証）の前提 | **PASS** | M1 完了が前提とされており、後続 Milestone の安全性確認として適切に位置づけられている |
| データ完全性リスクマトリクス | **PASS** | §3 の全リスク（監査証跡欠落・ハッシュ未記録・サイドカー欠落・絶対パス混入）が網羅されている |

---

## 総合判定: REJECT

以下の2件の CRITICAL 指摘によりロードマップを差し戻す。

| No. | 違反種別 | 該当 Milestone | 違反した基準 |
|-----|---------|---------------|-------------|
| 1 | M3d 前提条件と依存関係図の矛盾（コンテナビルドパスに §2 が未適用のまま P2-2 実装が許容される） | Milestone 3d | `reference_standards.md` §2（ダイジェスト固定・pip デッドロック回避） |
| 2 | `git_commit: "unknown"` REJECT 基準と plan.md 実装コードの矛盾（REJECT 基準を満たせる実装タスクが欠如） | Milestone 3a | `reference_standards.md` §3（環境とコードのハッシュ必須記録） |

PM は上記修正指示に従ってロードマップを修正し、再提出すること。
