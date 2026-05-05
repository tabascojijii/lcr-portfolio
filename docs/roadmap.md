# LCR Roadmap (Reference Standards Absolute)

## 0. 前提（絶対基準）
本ロードマップは `docs/reference_standards.md` を唯一の絶対基準として策定する。  
`docs/plan.md` は実行順序・対象範囲・成果物定義の具体化に使用するが、基準の優先順位は常に `reference_standards` を上位とする。

## 1. 目的
- 監査差し戻し反復（構造不適合ループ）の再発防止
- EOL スタック実行の再現性 100% 達成
- ALCOA++ 準拠の監査証跡を同一リビジョンで成立
- UI から業務ロジックを分離し、テスタブルなアーキテクチャへ固定

## 2. 非交渉の完了条件（DoD）
以下をすべて満たさない限り完了としない。

1. Gate-S（構造）Pass
2. Gate-F（機能）Pass
3. UI->Domain 直参照 0 件
4. Port バイパス 0 件
5. `MainWindow._run_container` / `_show_create_env_dialog` から業務判断排除完了
6. 監査証跡必須項目の完全記録（digest / git hash / I/O hash / relative path）
7. Docker 再現性要件（`FROM @sha256`、EOL archive、`constraints.txt`、マルチステージ）達成
8. Qt 命名規約違反 0 件（Signal=過去分詞、Slot=動詞開始）
9. Builder/Validator 分離運用の監査記録が存在

## 3. マイルストーン

### M1: ガバナンス固定（Week 1）
目標:
- EMCS による客観監査運用の固定
- Builder/Validator 分離の監査フロー確立
- REJECT の処方的フォーマット（違反箇所・制約・最小修正）適用

主要成果物:
- `artifacts/audit_reject_template.md`
- `artifacts/post_mortem_closure_checklist.md`（RC-1〜RC-3 閉塞欄を含む）
- `artifacts/emcs_metrics_report.md`（初期ベースライン）

ゲート:
- Gate-S: 判定ロジックと Fail 条件の実装・文書化完了

### M2: 構造是正（Week 2-3）
目標:
- UI 依存方向違反の根絶
- MainWindow の責務分離
- Port 契約の内側定義・外側実装を固定

実装焦点:
- `RunPreparationUseCase`
- `EnvironmentCreationProposalUseCase`
- `LifecycleManagementUseCase`
- 必須 Port 群（EnvironmentCapability/Repository、ContainerRuntime、AuditLog、ImageCleanup、KnowledgeMapping、PackageLookup）

主要成果物:
- `artifacts/architecture_decoupling_assessment.md`
- `artifacts/refactoring_proposal.md`
- `artifacts/phase_6_51_baseline_inventory.md`

ゲート:
- Gate-S: `UI->Domain` 直参照 0、逆依存 0、循環依存 0、Port 未経由 0

### M3: 実行ガードとライフサイクル完成（Week 4）
目標:
- mismatch 時 Run 無効化（Hard Guard）
- 適合環境なし時の強制作成導線
- Environment Manager UI と一括削除 2 段階確認

主要成果物:
- `artifacts/phase_6_51_test_baseline.md`
- ライフサイクル関連の契約テスト・統合テスト結果

ゲート:
- Gate-F: `pytest tests/` 全件 Pass、フェーズ必須テスト Pass

### M4: 型・契約・再現性固定（Week 5）
目標:
- DTO 境界の Pydantic v2 strict 化
- mypy gate 常設
- 監査ログ完全性の機械検証
- Docker 再現性要件の最終固定

主要成果物:
- Port/DTO/Audit 契約テスト一式
- 監査証跡検証レポート（hash・relative path・git hash）

ゲート:
- Gate-S/Gate-F 同時 Pass

### M5: 仕上げと再発防止クローズ（Week 6）
目標:
- 副作用分離完了（print 排除、Analyzer/Container の Port 化）
- ContainerManager 薄化
- RC-1〜RC-3 再発防止証跡の確定

主要成果物:
- `artifacts/qt_naming_inventory.md`
- `artifacts/post_mortem_closure_checklist.md` 完成版
- 最終 `artifacts/emcs_metrics_report.md`

ゲート:
- DoD 9 項目の同一リビジョン充足

## 4. フェーズ実行順（固定）
以下の順序を変更しない。

1. Phase 6.51 ベースライン固定
2. Phase 6.1 構造違反除去（最優先）
3. Phase 5 実行ガード完成
4. Phase 6 ライフサイクル管理完成
5. Phase 6.2〜6.4 型・契約・回帰固定
6. Phase 6.52〜6.56 副作用分離・責務分割仕上げ

## 5. 品質ゲート運用

### Gate-S（構造）
Fail 条件（1件でも Fail）:
- UI->Domain direct import
- 逆方向依存
- 循環依存
- Port 未経由呼び出し
- MainWindow 重点 2 メソッドへの業務判断残存
- UI 層から Qt 以外の外側依存規約違反
- Qt 命名規約違反
- EMCS 閾値超過

### Gate-F（機能）
Pass 条件:
- `pytest tests/` 全件 Pass
- フェーズ必須テスト群 Pass
- 監査ログ完全性 Pass

### EMCS 閾値（機械判定）
- E: UI メソッド行数 <= 60、分岐数 <= 5
- M: `UI->Domain` 0、逆依存 0、循環依存 0、Port bypass 0
- C: UseCase/Orchestrator 複雑度 <= 10
- S: 監査必須キー欠落 0、相対パス違反 0

## 6. リスクと停止条件
停止して Architect 再設計へ戻す条件:

1. 同一構造違反で 2 回連続 REJECT
2. Gate-F Pass かつ Gate-S Fail
3. UI 責務違反の再流入検知
4. Port 追加なしで UI 境界越え回避を試行

主要リスクと対策:
- リスク: 実装先行で境界逸脱  
  対策: M2 完了前に機能拡張を凍結
- リスク: EOL 依存の取得不安定  
  対策: archive リダイレクトと constraints を CI 検証に組み込み
- リスク: 監査ログ欠落  
  対策: 必須キー欠落を Gate-F Fail に直結

## 7. 役割責任（RACI）
- Architect: 境界設計、Port 定義、修正戦略確定（A/R）
- PM: マイルストーン進行、ゲート運用管理、停止判断（A/R）
- Implementer: 設計確定範囲の実装とテスト（R）
- Auditor: EMCS 客観監査、処方的 REJECT、差し戻し先明記（A/R）

## 8. 進捗管理KPI
- 構造KPI: `UI->Domain` 直参照件数、Port bypass 件数、循環依存件数
- 品質KPI: Gate-S Pass 率、Gate-F Pass 率、再監査率
- 再現性KPI: digest 固定率、hash 記録完全率、relative path 準拠率
- 運用品質KPI: REJECT の処方的記述充足率、原因層誤判定率

## 9. レビュー運用ルール
- 監査入力は「要件定義 + 生成差分 + テスト結果」のみ
- 実装者の思考過程・下書き・補助メモは監査入力から除外
- 違反監査は無効化し、差分限定条件で再監査

## 10. 運用メモ
- 本ロードマップ更新時は、`docs/reference_standards.md` との整合差分を明示する。
- 整合差分が解消されるまで新規フェーズ開始を禁止する。
