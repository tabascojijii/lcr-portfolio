# 監査レポート（docs/plan.md 対象）

- 監査日: 2026-05-04
- 監査基準: `docs/reference_standards.md`（絶対基準）
- 監査対象: `docs/plan.md`
- 総合判定: **REJECT_TO_ARCHITECT**

## 1. 重大指摘（基準逸脱）

### 指摘1: Builder/Validator分離の運用要件が計画に未定義
- 該当基準: 1章「Builder/Validatorの分離」
- 事実:
  - `docs/plan.md` には、構造ゲート・機能ゲート・差し戻し区分はあるが、
    「実装役と思考プロセスを共有せず、要件と差分のみで敵対的レビューする運用」を強制する工程定義が存在しない。
- 影響:
  - 監査の独立性が担保されず、サイレント逸脱や甘い判定の再発リスクが残る。
- 是正指示:
  1. `6. ゲート運用` に「監査入力を要件＋Diffに限定」「実装時の思考ログ/補足説明を監査入力に使わない」ルールを明記する。
  2. フェーズ完了条件へ「Builder/Validator分離チェック（Yes/No）」を追加し、Noなら自動Failにする。

### 指摘2: PyQt/PySideシグナル・スロット命名規則の検証ゲートが未定義
- 該当基準: 4章「シグナル・スロットの命名規則」
- 事実:
  - `docs/plan.md` はHumble Object/依存方向/Portを扱っている一方、
    シグナルは過去分詞形、スロットは動詞、という命名規律の検証項目がKPI・ゲート・証跡テンプレートに存在しない。
- 影響:
  - UIイベント境界の一貫性が崩れ、保守性低下とレビュー漏れを招く。
- 是正指示:
  1. 構造KPIに「命名規則違反件数 0件（signal=過去分詞, slot=動詞）」を追加する。
  2. 監査証跡テンプレートに命名規則チェック結果を追加する。

## 2. 適合している点（抜粋）
- EMCS志向の客観指標（CC/LOC/依存違反）をKPI化している。
- REJECT区分（`REJECT_TO_ARCHITECT` / `REJECT_TO_IMPLEMENT`）を工程ルールに組み込み済み。
- Docker/EOL 4要件（digest固定、archive切替、constraints、マルチステージ）を明確に拘束している。
- Data Integrity（相対パス、ハッシュ対象、`image_digest`/`git_commit`）をゲート化している。

## 3. 最終結論
`docs/plan.md` は基準の多くを満たすが、**絶対基準の必須運用要件が未定義のため不合格**。
判定は **REJECT_TO_ARCHITECT** とする。
