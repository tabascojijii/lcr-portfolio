# 監査報告書（docs/plan.md 対象）

## 総合判定
REJECT（問題あり）

- 判定ステータス: `REJECT_TO_ARCHITECT`
- 理由: `docs/plan.md` は `docs/reference_standards.md` を絶対基準とした場合、必須拘束の一部を未充足。

## 指摘事項（重大度順）

### 1. 監査ガバナンス標準の定量評価要件が未定義（重大）
- 基準: `reference_standards.md` 1章「客観的アーキテクチャ評価 (EMCSモデル)」
- 現状: `plan.md` には「重大違反0件」「監査可能」等の文言はあるが、判定に用いる定量メトリクス（例: SRP違反判定条件、複雑度閾値、境界違反の検出規則）が未定義。
- 影響: 監査判定が実装者依存となり、客観性・再現性を欠く。
- 是正指示:
  - 監査メトリクスを明文化（例: 層間依存違反件数=0、UI層のドメイン直接参照=0、複雑度上限など）。
  - 各メトリクスに「測定方法」「Fail条件」「エビデンス出力先」を追加する。

### 2. Builder/Validator 分離の運用要件が計画に落ちていない（重大）
- 基準: `reference_standards.md` 1章「Builder/Validatorの分離」
- 現状: `plan.md` は差し戻し経路を定義しているが、監査時の入力制約（要件とDiffのみをレビュー対象とする運用）を明記していない。
- 影響: 監査の独立性が崩れ、サイレント逸脱の再発リスクが残る。
- 是正指示:
  - 監査プロセス定義に「Auditor入力境界（requirements + diff + test evidenceのみ）」を追加。
  - 監査テンプレートに「参照した入力一覧」欄を必須化。

### 3. Docker再現性標準（EOLスタック）への適合計画が欠落（重大）
- 基準: `reference_standards.md` 2章（digest固定、archive repo、constraints.txt、マルチステージ）
- 現状: `plan.md` にコンテナ再現性要件への言及がない。
- 影響: 環境再現性の不確実性が残り、要件の法的/監査的再現性を満たせない。
- 是正指示:
  - `Dockerfile` 方針を計画へ追加（`FROM@sha256` 必須、APT archive切替、`constraints.txt` 使用、multi-stage分離）。
  - 監査項目に「コンテナ再現性チェック」を追加。

### 4. PyQt/PySide インターフェース規律の必須項目が未充足（中）
- 基準: `reference_standards.md` 4章「インターフェースによる規律」
- 現状: `plan.md` はUI/UseCase分離を示すが、`abc.ABC` / `typing.Protocol` を用いた境界契約の実装方針が未記載。
- 影響: 層境界が規約ではなく慣習依存になり、将来的な逆流を防げない。
- 是正指示:
  - View-UseCase間、UseCase-Infra間のインターフェース定義方針を明記。
  - テストに「具象依存禁止（interface経由のみ）」検証を追加。

### 5. シグナル/スロット命名規則の適合確認項目がない（中）
- 基準: `reference_standards.md` 4章「シグナル・スロット命名規則」
- 現状: `plan.md` のUI接続計画に命名規約の適用/検証がない。
- 影響: UIイベント命名の一貫性が失われ、保守性と監査性が低下。
- 是正指示:
  - 命名規約（signal: 過去分詞、slot: 動詞）を実装規約として追記。
  - Lint/レビュー観点に命名チェックを追加。

## 適合している点
- Data Integrity の主要要件（`image_digest`、`git_commit_hash`、相対パス、SHA-256記録）は計画に具体化されている。
- Hard Guard、ミスマッチ検知、作成導線、テスト計画は要件駆動で整理されている。
- 処方的修正指示の方向性（違反箇所・制約根拠・修正条件）は計画に含まれる。

## 結論
`docs/plan.md` は部分的に高品質だが、絶対基準である `docs/reference_standards.md` に対して重大な未充足が残るため、現時点では承認不可。判定は `REJECT_TO_ARCHITECT` とする。
