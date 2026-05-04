# LCR 実装計画（Architect）

- 作成日: 2026-05-04
- 参照: `docs/core_philosophy.md`, `docs/requirements.md`, `docs/reference_standards.md`, `docs/post_mortem.md`
- 目的: UI疎結合・監査可能性・安全性を満たしつつ、過去の監査ループ要因を構造的に除去する。

## 1. 計画の前提（失敗分析の反映）

本計画は以下を絶対条件として開始する。

1. 設計課題は実装へ押し戻さない（Architect責務で境界を先に固定）。
2. `pytest` 合格と構造準拠を独立ゲート化する。
3. UIからDomainへの直接参照を「禁止ルール」ではなく「経路設計」で不可能化する。
4. `MainWindow` は Humble Object とし、判断・分岐・永続化・外部I/Oを持たせない。

## 2. 最終達成指標（固定KPI）

### 2.1 構造KPI（必達）

- `UI->Domain` 直参照: 0件
- 逆方向依存（内側→外側）: 0件
- 循環依存: 0件
- `MainWindow` の業務ロジックメソッド: 0件（イベント中継のみ）
- Port未経由の境界越え: 0件

### 2.2 品質KPI（必達）

- `pytest tests/`: 全件Pass
- `mypy`（Phase 6.3対象範囲）: 0 error
- DTO境界（Phase 6.2）での型違反既知残: 0件

### 2.3 監査KPI（必達）

- 監査ログに required imports / capability / mismatch / guard発火状態を100%記録
- 削除・編集・クリーンアップ操作で required監査項目欠落0件
- 相対パス違反0件、ハッシュ対象欠落0件

## 3. ターゲットアーキテクチャ

依存方向は `UI -> UseCase -> Domain -> Infrastructure` に固定する。

- UI層:
  - 入力受付、表示更新、2段階確認ダイアログ表示のみ。
  - UseCase呼び出しは Facade/Controller（Application層）経由。
- UseCase/Application層:
  - 判定、ユースケース制御、トランザクション境界、エラー整形。
  - Port Interface 以外で Infrastructure を参照しない。
- Domain層:
  - 判定規則（未使用判定、ガード判定、メタデータ不変条件）を純粋ロジックで保持。
- Infrastructure層:
  - Docker・ファイルI/O・監査ログ永続化の実装。

## 4. 重点是正対象（Post Mortem直結）

### 4.1 `MainWindow._run_container` の責務移管

- 移管先: `RunContainerUseCase`（新設または既存強化）
- UIに残す処理:
  - ユーザー操作イベント受信
  - 実行可否の表示反映
  - 結果通知表示
- UseCaseへ移す処理:
  - required imports抽出結果との照合
  - capability mismatch判定
  - 実行ガード発火判断
  - 監査記録指示

### 4.2 `MainWindow._show_create_env_dialog` の境界統制

- 移管先: `CreateEnvironmentFlowUseCase`
- UIはダイアログ表示と入力値受け渡しのみ。
- 環境候補生成、knowledge参照、作成後の再評価トリガはUseCase側で実施。
- 環境作成完了後の再起動不要反映（Dynamic Refresh）をUseCase完了条件に含める。

## 5. フェーズ別実行計画

### Phase A: 設計固定（着手前ゲート）

1. 依存方向図・責務表・Port一覧を `artifacts/refactoring_proposal.md` に確定。
2. 違反一覧（file/class/function/違反種別/根拠）を `artifacts/architecture_decoupling_assessment.md` に確定。
3. 変更影響テスト仕様（UI変更時/Domain変更時）を定義。

完了条件:
- AC6.1-1〜AC6.1-7 を文書上で満たす。
- 実装者レビュー前に Architect 承認済み状態にする。

### Phase B: 境界リファクタ（最優先）

1. `MainWindow` から業務判断分岐を除去。
2. UseCase/Facade 経由呼び出しへ置換。
3. Port未経由呼び出しを全面排除。
4. importグラフを再測定し、禁止依存ゼロ化を確認。

完了条件:
- 構造KPIを全達成。
- 監査での差し戻し理由（UI責務混在/Port未経由）が再発しない。

### Phase C: Phase 5要件の実装完了

1. capability mapping（推定/実証の明示）
2. mismatch時のHard Guard（Run無効化）
3. 適合環境なし時の強制作成導線
4. 監査ログへの必須項目記録

完了条件:
- AC-1〜AC-5, T5-1〜T5-4 を満たす。

### Phase D: Phase 6要件の実装完了

1. Environment Manager導入
2. 一括削除2段階確認
3. 未使用判定（最終利用日時+利用回数+保護フラグ）
4. dangling/unused imageクリーンアップ
5. メタデータ編集（内部ID不変）
6. 部分失敗継続と結果分離表示
7. 監査ログ完全化

完了条件:
- AC6-1〜AC6-7, T6-1〜T6-6 を満たす。

### Phase E: Phase 6.2/6.3 型ゲート導入

1. DTOをA→B→C順でPydantic v2化（strict + fail-fast）
2. dict互換アダプタで段階移行
3. mypyゲート導入（Port/UseCase公開API型を必須化）
4. `type: ignore` 理由必須化・`Any`増加監視

完了条件:
- AC6.2-1〜AC6.2-5, T6.2-1〜T6.2-5
- AC6.3-1〜AC6.3-4, T6.3-1〜T6.3-4

## 6. 品質ゲート運用（ループ防止）

ゲートを次の2系統に分離し、両方合格まで次工程へ進めない。

1. 機能ゲート:
- `pytest tests/` 全件Pass
- 受け入れ基準（AC）達成

2. 構造ゲート:
- importグラフ検証（禁止依存/循環依存0件）
- UI責務監査（業務ロジック0件）
- Port経由率100%

差し戻し規約:
- 構造ゲート失敗時は `REJECT_TO_ARCHITECT`（設計是正）
- 機能ゲート失敗時は `REJECT_TO_IMPLEMENT`（実装是正）

## 7. 実装順序（クリティカルパス）

1. Phase A（設計固定）
2. Phase B（境界リファクタ）
3. Phase C（Validation Guardrails）
4. Phase D（Lifecycle Management）
5. Phase E（Type Safety + Static Gate）

理由:
- 先に境界を固定しない限り、後続機能は再び `MainWindow` へ逆流して監査ループを再発させるため。

## 8. リスクと対策

- リスク1: UI改修時に業務ロジックが再混入
  - 対策: UI層 lint/レビュー項目に「判断分岐の禁止」を明示
- リスク2: DTO導入時の既存経路破壊
  - 対策: 互換アダプタを先行し、段階切替フラグで移行
- リスク3: 監査ログ項目の欠落
  - 対策: 監査DTOの必須フィールド化 + 欠落時fail-fast

## 9. 完了定義（DoD）

以下をすべて満たしたとき完了とする。

1. 全AC/全必須テスト項目がPass。
2. 構造KPI・品質KPI・監査KPIが全達成。
3. 監査で REJECT 理由が再発していない。
4. 証跡（評価レポート、リファクタ計画、テスト結果、importグラフ結果）が更新済み。
