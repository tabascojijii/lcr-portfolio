# 監査報告書

判定: REJECT_TO_ARCHITECT

## 総評
`docs/plan.md` は Gate-S/Gate-F 分離、Port 強制、Docker 再現性、Data Integrity については高水準で具体化されている。一方で、`docs/reference_standards.md` の「絶対基準」を満たすには未固定の規約が残存しているため、現時点では承認不可。

## 指摘事項（重大度順）

1. **PyQt/PySide 命名規約（シグナル/スロット）が計画に固定化されていない**
- 失敗箇所: `docs/plan.md`（全体。UI設計規約セクションに未定義）
- 違反制約: `docs/reference_standards.md` 4章「シグナル・スロットの命名規則」
- 問題内容: 絶対基準では「シグナル=過去分詞形」「スロット=動詞」を必須としているが、計画内に受け入れ基準・検証方法・違反時の扱いが存在しない。
- 具体的修正指示:
  - `docs/plan.md` に命名規約固定セクションを追加する。
  - Gate-S に以下を追加する: 
    - `Qt signal naming violation = 0`
    - `Qt slot naming violation = 0`
  - Gate-F に命名規約検証テスト（例: `T-UI-NAME-1/2`）を追加する。
- 原因層: 設計
- 差し戻し先: `REJECT_TO_ARCHITECT`
- 再検証条件: 命名規約が「ルール・測定方法・合格条件・テストID」まで計画に明文化されていること。

2. **UseCase/Domain の Qt 非依存性を検証する明示ゲートが不足**
- 失敗箇所: `docs/plan.md` 2.1, 2.2, 4（境界再設計・品質ゲート）
- 違反制約: `docs/reference_standards.md` 4章「クリーンアーキテクチャと依存の方向」
- 問題内容: 計画は UI から Domain/Infra 直参照を禁じているが、内側レイヤー（Entities/UseCases）が Qt に依存しないことを直接検証する項目がない。
- 具体的修正指示:
  - Gate-S に以下を追加する:
    - `UseCase->Qt dependency = 0`
    - `Domain->Qt dependency = 0`
  - 依存検査ルール（import lint/AST 検査）と対象パスを計画へ明記する。
- 原因層: 設計
- 差し戻し先: `REJECT_TO_ARCHITECT`
- 再検証条件: 内側レイヤーの Qt 非依存が機械検証可能な形でゲート化されていること。

## 合否
- 結論: **問題あり（REJECT_TO_ARCHITECT）**
- 理由: 絶対基準のうち PyQt/PySide 規約の一部が計画上で未固定のため。
