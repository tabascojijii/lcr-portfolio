# 監査報告書（Roadmap 検証）

## 判定
REJECT_TO_PM

## 監査基準
- `docs/plan.md`（絶対基準）
- `docs/reference_standards.md`（絶対基準）

## 指摘事項

### 1. 監査証跡の必須記録項目が欠落
- 失敗箇所（file path + セクション）:
  - `docs/roadmap.md` セクション「5. 監査証跡と運用成果物 / 監査ログ入力制約」
- 違反制約:
  - `docs/plan.md` 5.1「Builder/Validator 分離の運用固定（監査入力制約）」で必須とされる以下が未記載。
  - 要件版識別子（例: `docs/requirements.md@<hash or revision>`）
  - Diff識別子（例: `PR#xx / commit range / patch hash`）
  - 判定時刻と判定者ロール（Validator）
- 具体的修正指示:
  - `docs/roadmap.md` の監査ログ入力制約に、上記3項目を「監査証跡への必須記録」として明記すること。
- 原因層（設計/実装）:
  - 設計
- 差し戻し先:
  - `REJECT_TO_PM`
- 再検証条件:
  - 監査証跡の必須記録3項目が `docs/roadmap.md` に明示され、`docs/plan.md` 5.1 と整合していること。

### 2. Gate-S の固定検査仕様が不十分（機械検証条件の欠落）
- 失敗箇所（file path + セクション）:
  - `docs/roadmap.md` セクション「4. 品質ゲート運用 / Gate-S（構造）」
- 違反制約:
  - `docs/plan.md` 4章で固定される以下の機械検証仕様が未記載。
  - 検査対象パス固定（UI: `src/lcr/ui` / UseCase: `src/lcr/core/use_cases` / Domain: `src/lcr/core/domain`）
  - `PyQt*` / `PySide*` import を UseCase/Domain で検出時 fail とするASTルール
  - Qt命名規約違反のAST検出 fail ルール
  - 例外を `artifacts/qt_naming_exceptions.md` 理由付き記載時のみ許可する条件
- 具体的修正指示:
  - `docs/roadmap.md` Gate-S に、上記4点を「固定ルール」として追記すること。
- 原因層（設計/実装）:
  - 設計
- 差し戻し先:
  - `REJECT_TO_PM`
- 再検証条件:
  - Gate-S の検査対象・検出方式・例外条件が `docs/plan.md` 4章と同等の粒度で明記されていること。

### 3. Port 契約の固定対象がロードマップから欠落
- 失敗箇所（file path + セクション）:
  - `docs/roadmap.md` セクション「1. 絶対遵守原則 / 4. UI/アーキテクチャ」および全体
- 違反制約:
  - `docs/plan.md` 2.2 で必須Portとして固定される以下が未定義。
  - `EnvironmentCapabilityPort`
  - `EnvironmentRepositoryPort`
  - `ContainerRuntimePort`
  - `AuditLogPort`
  - `ImageCleanupPort`
  - `KnowledgeMappingPort`
  - `PackageLookupPort`
- 具体的修正指示:
  - `docs/roadmap.md` に必須Port一覧を明示し、未充足をGate-S失敗として扱う方針を追加すること。
- 原因層（設計/実装）:
  - 設計
- 差し戻し先:
  - `REJECT_TO_PM`
- 再検証条件:
  - 必須Port一覧と、インターフェース経由強制ルールが `docs/plan.md` 2.2 と整合すること。

## 総括
`docs/roadmap.md` は大枠の方向性は整合しているが、`docs/plan.md` の固定仕様（監査証跡必須記録、Gate-S機械検証仕様、必須Port固定）の一部が欠落しているため、現時点では基準未達。