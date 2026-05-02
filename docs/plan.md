# LCR 実装計画（Architect）

- 作成日: 2026-05-03
- 作成者: Architect
- 対象: Phase 4 再検証および規約準拠実装
- 参照: `docs/requirement.md`, `docs/reference_standards.md`
- 注記: 指示にある `docs/core_philosophy.md` と `docs/requirements.md` はリポジトリ内に存在しないため、実在する要件文書 `docs/requirement.md` を正式参照として計画化する。

## 1. 目標

1. Phase 4（Self-Learning Loop）の再検証を最優先で実施し、合格基準を根拠付きで満たす。  
2. `docs/reference_standards.md` の必須規約（Docker再現性、監査証跡、Humble Object、インターフェース規律）に準拠した実装に収束させる。  
3. 最終判定条件として `pytest tests/` 全件 Pass を達成する。

## 2. 完了条件（Definition of Done）

1. `pytest tests/` が `FAILED=0 / ERROR=0`。  
2. 再検証シナリオ3件がすべて合格。  
3. 監査証跡（実行ログ、ハッシュ、検証記録）が相対パス運用で再現可能。  
4. UI層に業務ロジックが残留せず、依存方向が内側（UseCase/Domain）へ向く。

## 3. 要件トレーサビリティ

### 3.1 requirement.md 由来

1. テスト成果物を `tests/` に実装し、再検証シナリオを自動化可能な粒度へ分解する。  
2. Phase 4 の3機能を検証する。
- Knowledge Update: 承認済み import/package 対応が `library.json` / `user_knowledge.json` へ追記される。  
- Real-time Feedback: Dockerビルド進捗がGUIコンソールに継続表示される。  
- Dynamic Refresh: 新規環境作成後に再起動なしでUI反映・実行可能。  
3. 合格基準（ID保持、ログ完走、知識発動、即時実行、クラッシュなし）を監査チェック項目へ直結させる。

### 3.2 reference_standards.md 由来

1. Docker再現性: `FROM` digest固定、EOLリポジトリ切替、constraints強制、必要時マルチステージ。  
2. データ完全性: `git_commit`、`image_digest`、入出力ハッシュ、ログハッシュの記録。  
3. GUI設計: Humble Object 徹底、Presenter/UseCase分離、`abc.ABC`/`Protocol` で境界定義。  
4. 監査運用: 客観メトリクスで判定し、REJECT時は違反箇所・根拠・修正指示を必須化。

## 4. 実装フェーズ

### Phase A: ベースライン評価

1. 現行 `pytest tests/` を実行し、失敗を分類（テスト不備、実装不備、設計不備）。  
2. Phase 4 関連コード（知識更新、ビルドログ連携、UI更新）の実装位置と依存関係を棚卸し。  
3. 監査証跡用にベースライン結果を保存。

### Phase B: P0 是正（全テストPass回復）

1. 既存失敗テストを修正し、期待値と実装仕様を一致させる。  
2. テスト不能箇所は依存分離（モック可能化、I/F導入）で単体検証可能にする。  
3. `pytest tests/` 緑化を最短で達成し、Phase 4 再検証の前提を確立する。

### Phase C: Phase 4 再検証実装・検証

1. 遺産救済テスト: 既存環境（例: `3.10test5`）再構築時にIDが維持されることを確認。  
2. 新規作成即時反映: 作成直後にUI一覧へ反映し、そのまま実行できることを確認。  
3. 失敗/キャンセル安全性: 異常系でクラッシュしないこと、停止・ロールバック動作を確認。  
4. 上記を `tests/` へ反映し、回帰試験化する。

### Phase D: 規約準拠強化

1. Docker生成系に digest 必須バリデーションを導入（タグのみ指定を禁止）。  
2. EOL定義に archive repo / constraints 適用を強制。  
3. OpenCV等ビルド定義は multi-stage テンプレートへ統一。  
4. 実行マニフェストへ `git_commit`、`image_digest`、各種SHA-256を出力。  
5. UIから業務処理を分離し、Presenter/UseCase経由へ再配線。

## 5. 検証計画

1. 自動検証: `pytest tests/`、Phase 4 回帰テスト、Dockerfile生成テスト、監査証跡生成テスト。  
2. 手動検証: GUI上のリアルタイムログ、即時反映、キャンセル時安定性の確認。  
3. 監査判定: 規約違反ゼロ、再検証シナリオ全合格、再現性証跡の欠落なし。

## 6. 主要成果物

1. `docs/plan.md`（本書）  
2. `src/` 修正差分（Phase 4 と規約準拠）  
3. `tests/` 追加・修正（再検証シナリオを含む）  
4. 監査エビデンス（pytest結果、再検証結果、ハッシュ付き実行記録）

## 7. リスクと先行対策

1. 旧環境データ形式差異でID保持が崩れるリスク。  
対策: 既存定義ファイル読み込み時の互換レイヤーと回帰テストを追加する。  
2. GUIテストの環境依存リスク。  
対策: Presenter中心の単体試験へ寄せ、GUI層は最小の統合試験に限定する。  
3. EOL依存の取得失敗リスク。  
対策: archive repo と constraints を定義テンプレートに組み込み、未設定時は明示エラーにする。
