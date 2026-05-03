# Audit Report: docs/plan.md

## 監査判定
- 判定: **REJECT_TO_ARCHITECT**
- 根拠基準: `docs/reference_standards.md`（絶対基準）
- 対象: `docs/plan.md`

## 重大指摘（基準違反）

### 1) EOLスタックのコンテナ化・再現性標準の実装計画が欠落
- 失敗箇所: `docs/plan.md` 全体（Docker標準への明示的WBS/検証ゲート不在）
- 違反した制約:
  - `FROM` のSHA256ダイジェスト固定
  - EOL APTソースのアーカイブリポジトリ切替
  - `constraints.txt` によるpip探索制限
  - OpenCV等ビルド時のマルチステージビルド強制
- 客観根拠: 参照基準の第2章は「厳守」事項であり、計画に対応タスク・完了条件・検査条件が存在しない。
- 修正指示:
  - `plan.md` に Docker/EOL再現性の専用セクション（最低でもP0またはP1）を追加。
  - 各項目に「実装タスク」「静的確認方法」「CIゲート条件」を1:1で定義。
  - DoDに「Docker基準4項目の違反0件」を明記。

### 2) PyQt/PySide シグナル・スロット命名規則の監査条件が欠落
- 失敗箇所: `docs/plan.md` 4章/7章（命名規則の検証観点なし）
- 違反した制約:
  - シグナルは過去分詞形
  - スロットは動作動詞
- 客観根拠: 参照基準第4章はアーキテクチャ標準として必須だが、命名規約を検出・強制するルール/ゲートが計画に未定義。
- 修正指示:
  - Architecture Gateに命名規則チェックを追加（例: シグナル/スロット命名Lint）。
  - WBSに既存コードの命名是正タスクを追加。

### 3) Builder/Validator分離の運用手順が計画に未定義
- 失敗箇所: `docs/plan.md` 2章/4章/5章
- 違反した制約:
  - Builder/Validatorの分離（実装思考プロセスを共有せず、要件とDiffのみで監査）
- 客観根拠: REJECTルーティングはあるが、監査入力物の制限（要件+Diffのみ）や運用ガードが明文化されていない。
- 修正指示:
  - 監査プロセス定義を追加し、Auditor入力を「requirements + diff + test evidence」に限定。
  - CIまたは運用手順で分離を担保するチェックポイントを追加。

## 軽微指摘（改善推奨）
- `docs/plan.md` 7章に「監査適合: docs/audit_report.md相当」とあるが、監査観点の網羅定義が不足。章2/4のゲートに参照基準第2章・第4章命名規約を明示的にリンクさせること。

## 結論
- 本計画は、依存方向/Humble Object/Data Integrityの一部で高水準だが、`docs/reference_standards.md` の必須項目を全量満たしていない。
- したがって現時点の判定は **REJECT_TO_ARCHITECT** とする。