# 監査報告書（Auditor）

- 監査日: 2026-05-03
- 監査対象: `docs/plan.md`
- 絶対基準: `docs/reference_standards.md`（全章）
- 監査結論: **REJECT（差し戻し）**

## 指摘事項（重大度順）

1. **[重大] 監査ガバナンス要件の具体化不足（EMCS客観メトリクス未定義）**  
該当箇所: `docs/plan.md` 3.2-4, 5-3  
根拠: `reference_standards.md` 1章では、Auditor判定は「客観的メトリクス（例: SRP違反、複雑度超過）」に基づくことを必須化している。  
問題: 計画書は「客観メトリクスで判定」と記載するのみで、閾値・評価軸・判定条件（例: 複雑度上限、依存違反検出条件、UI層ロジック判定基準）が未定義。監査の再現性が不足。  
修正指示: 監査チェックリストを定量化し、最低でも以下をDoDに明記すること。  
- レイヤ依存違反: `UI -> Domain` 逆流0件  
- UI層ロジック違反: Presenter/UseCase以外での業務処理0件  
- 複雑度や責務違反の閾値（使用ツールと基準値）  
- REJECT判定トリガー（違反1件以上でFail等）

2. **[重大] Builder/Validator分離運用が計画に組み込まれていない**  
該当箇所: `docs/plan.md` 全体（監査実施体制の記述不足）  
根拠: `reference_standards.md` 1章「Builder/Validatorの分離」は必須。  
問題: 計画は実装・検証・監査を同一フローで記述しており、誰がどの入力（要件/差分のみ）で監査するかが不明。分離不備はサイレント逸脱を許す。  
修正指示: 監査フェーズに「Validator入力を requirement + diff + test evidence のみに限定」「実装思考ログ非参照」を明記すること。

3. **[重大] 監査証跡のハッシュ鎖要件が不足（ログ自体のハッシュ明記不足）**  
該当箇所: `docs/plan.md` 3.2-2, 4-Phase D-4  
根拠: `reference_standards.md` 3章は「入出力、パラメータ、実行ログ自体」にSHA-256適用を必須化。  
問題: 計画は「各種SHA-256」を示すが、ログ本体・パラメータファイル・ハッシュ計算対象一覧が明文化されていない。実装時に漏れが発生しうる。  
修正指示: 監査証跡スキーマを明示し、最低限 `input_hash`, `output_hash`, `param_hash`, `log_hash`, `image_digest`, `git_commit` を必須フィールドとして定義すること。

4. **[中] PyQt/PySide命名規約の検証計画欠落**  
該当箇所: `docs/plan.md` 3.2-3, 5章  
根拠: `reference_standards.md` 4章はシグナル/スロット命名規則（過去分詞/動詞）を明示。  
問題: Humble ObjectとI/F分離は記載されるが、命名規約の適合確認が検証項目に入っていない。  
修正指示: 静的チェックまたはレビュー観点として、シグナル/スロット命名検証を監査項目へ追加すること。

5. **[中] Docker規約の「適用条件」が曖昧**  
該当箇所: `docs/plan.md` 3.2-1, 4-Phase D-2/3  
根拠: `reference_standards.md` 2章は digest固定・archive repo切替・constraints・multi-stageを強制。  
問題: 計画内に「必要時マルチステージ」とあり、適用判定が実装者裁量。OpenCV等C++ビルド時は必須であり、条件分岐定義が必要。  
修正指示: 「C/C++コンパイルを伴う全Dockerfileはmulti-stage必須」などの強制条件を明文化すること。

## 総合判定

`docs/plan.md` は基準への準拠意思は示しているが、`docs/reference_standards.md` が要求する**監査再現性・分離統制・証跡完全性の定義粒度**に未達。  
したがって現時点では **REJECT_TO_ARCHITECT** と判定する。

## 是正後の再提出条件

1. 監査メトリクスを定量閾値付きで明文化。  
2. Builder/Validator分離運用をプロセスとして追記。  
3. 監査証跡スキーマ（必須ハッシュ項目）を明示。  
4. シグナル/スロット命名規約の検証項目を追加。  
5. multi-stage適用条件を強制ルールとして明記。
