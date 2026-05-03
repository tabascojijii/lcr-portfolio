# Audit Report (Plan Validation)

## 判定
- 結果: **REJECT_TO_ARCHITECT**
- 対象: `docs/plan.md`
- 絶対基準: `docs/reference_standards.md`

## 指摘事項（重大度順）

1. **Data Integrity要件のハッシュ完全性が未充足（High）**
- 失敗箇所: `docs/plan.md` 2.1節「必須フィールド」「ハッシュ採取タイミング」
- 違反制約: `reference_standards.md` 3節「ハッシュによる改ざん検知」
- 観測証拠:
  - 基準は「**すべての**入出力データ、パラメータファイル、および実行ログ自体」にSHA-256適用を要求。
  - 計画は「入力・出力・**主要**パラメータ・実行ログ本体」と記述し、適用対象が限定語（主要）付きで網羅性が保証されていない。
- 修正ヒント:
  - 「主要」を削除し、`all_input_files / all_output_files / all_parameter_files / audit_log_record` を必須ハッシュ対象として明文化する。
  - 欠落検知テストを「対象件数一致（列挙件数とハッシュ件数の一致）」で仕様化する。
- 再検証条件:
  - 計画文面上でハッシュ対象が全件必須であること。
  - 監査ゲートに全件一致検証が追加されていること。
- ルーティング先: `REJECT_TO_ARCHITECT`

2. **UseCase層のQt依存禁止が明文化不足（High）**
- 失敗箇所: `docs/plan.md` 1節「非許可依存」
- 違反制約: `reference_standards.md` 4節「クリーンアーキテクチャと依存の方向」
- 観測証拠:
  - 基準は内側ビジネスルール（Entities/Use Cases）がQtに依存しないことを要求。
  - 計画の非許可依存には `Domain -> Qt` はあるが、`UseCase -> Qt` の禁止が明示されていない。
- 修正ヒント:
  - 非許可依存へ `UseCase -> Qt` を明示追加。
  - ゲートに「UseCase層のQt import検出 fail」を追加。
- 再検証条件:
  - 文書内で `UseCase -> Qt` 禁止が明記されること。
  - CI静的検査ルールに同制約が追加されること。
- ルーティング先: `REJECT_TO_ARCHITECT`

3. **Humble Object要件の「複雑計算/フォーマット処理移譲」が不足（Medium）**
- 失敗箇所: `docs/plan.md` 1節および2.2節のUI責務定義
- 違反制約: `reference_standards.md` 4節「Humble Object パターンの適用」
- 観測証拠:
  - 基準はViewから「複雑な計算やフォーマット処理」をPresenter/ViewModelへ移譲することを要求。
  - 計画では「判断・分岐・永続化・外部I/O禁止」はあるが、計算/フォーマット責務の禁止が明文化されていない。
- 修正ヒント:
  - `docs/allowed_ui_operations.md` に「UIでの計算・整形ロジック禁止」を明記。
  - 併せて検査観点（例: UIクラス内の変換/集計/整形関数を検出）を監査ゲート化する。
- 再検証条件:
  - UI責務制限に計算・整形の禁止が明文化されること。
  - 監査ゲートに当該検査が追加されること。
- ルーティング先: `REJECT_TO_ARCHITECT`

## 総括
- `docs/plan.md` は多くの基準を取り込んでいるが、上記3点は「絶対基準を満たすと断定できない」欠落であり、現時点では合格不可。
- 処方的修正を反映後、再監査を実施すること。