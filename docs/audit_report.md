# 監査報告書（Auditor）

## 判定
REJECT_TO_ARCHITECT

## 総評
`docs/plan.md` は UI責務分離・監査ログ・ゲート設計の方向性は妥当だが、絶対基準 `docs/reference_standards.md` に定義された**必須技術要件の一部が計画に明示されていない**。本監査は「計画の完全準拠性」を判定対象とするため、設計不備として差し戻す。

## 指摘事項（重大度順）

### 1) EOLコンテナ再現性標準の必須項目が計画に未固定（Critical）
- 失敗箇所: `docs/plan.md` 全体（Docker/EOL再現性の実装規約が不在）
- 違反した制約: `docs/reference_standards.md` セクション2
  - `FROM` のSHA256ダイジェスト固定
  - EOL向けAPTアーカイブリポジトリへのリダイレクト
  - `constraints.txt` によるpip依存解決範囲固定
  - OpenCV等を想定したマルチステージビルド強制
- 根拠: planには image digest の「ログ記録」はあるが、**ビルド手順そのものの固定要件**（上記4点）が実装計画/ゲートとして定義されていない。
- 修正指示:
  1. Phase A成果物に `docs/container_reproducibility_policy.md` を追加し、4要件を非交渉ルールとして明記する。
  2. Phase B/C/D とは独立に、CIゲートへ以下を追加する。
     - Dockerfile `FROM` がタグのみの場合 fail
     - APTソースがEOL標準ミラーのままなら fail
     - `constraints.txt` 未使用のpip installを fail
     - 単一ステージでビルドツール同梱実行イメージを fail

### 2) インターフェース規律（abc/Protocol）の強制が不足（High）
- 失敗箇所: `docs/plan.md` 2.2, 3, 5
- 違反した制約: `docs/reference_standards.md` セクション4「インターフェースによる規律」
- 根拠: planでは Port名は列挙されるが、`abc.ABC` / `typing.Protocol` による**形式的な実装規約と検証方法**が定義されていない。
- 修正指示:
  1. Phase Aの境界ドキュメントに「PortはABCまたはProtocolで定義する」ことを明文化。
  2. アーキテクチャゲートに「具象依存の直接参照検出（Port未経由）」を追加。

### 3) シグナル/スロット命名規約の監査項目欠落（Medium）
- 失敗箇所: `docs/plan.md` 5（テスト・監査ゲート）
- 違反した制約: `docs/reference_standards.md` セクション4「シグナル・スロット命名規則」
- 根拠: planのUI関連ゲートは責務/依存のみで、命名規約（signal: 過去分詞、slot: 動詞）を検証対象に含めていない。
- 修正指示:
  1. UI静的検査ルールを追加し、命名逸脱を fail 対象化。
  2. `docs/allowed_ui_operations.md` に命名規約節を追加。

## 適合確認（参考）
- `git_commit_hash` / image digest のログ記録方針: あり（plan 2.1, 5）
- ALCOA++志向の監査ログ完全性テスト: あり（plan 2.1, 5）
- UI Humble Object /依存方向の方針: あり（plan 1, 2.2, 5）
- REJECTルーティング定義: あり（plan 2.3, 7）

## 最終要求
上記 1)〜3) を `docs/plan.md` に反映し、特に 1) の4必須要件を**実装計画とCIゲートの両方**に落とし込んだ改訂版を再提出すること。