# LCR Roadmap (PM)

## 0. 目的と適用範囲
- 本ロードマップは `docs/reference_standards.md` を絶対基準として、`docs/plan.md` の実装方針をプロダクト推進用に時系列化したものである。
- 対象範囲は Phase 5, Phase 6, Phase 6.1。
- 成果基準は「機能実装完了」ではなく「監査で再現可能性・完全性・設計整合性を証明できる状態」。

## 1. 絶対準拠原則（Non-Negotiable）
- Builder/Validator 分離を維持し、Validator は `requirements + diff` のみで判定する。
- REJECT は処方的（違反箇所、違反制約、根拠、修正ヒント、再検証条件、ルーティング先）でなければならない。
- `Dockerfile` の `FROM` はタグ禁止、SHA256 ダイジェスト固定を必須とする。
- EOL OS はAPTソースをアーカイブ系（Ubuntu: `old-releases.ubuntu.com` / Debian: `archive.debian.org`）へ切替する。
- pip依存解決は `constraints.txt` 適用を必須とする。
- C/C++ビルド系コンテナはマルチステージビルドを必須とする。
- 監査ログにはコンテナダイジェスト、Gitコミットハッシュ、全入出力・全パラメータ・監査ログ本体のハッシュを必須記録する。
- 記録パスはすべてプロジェクトルート相対パスとし、絶対パスを禁止する。
- UIはHumble Objectを厳守し、業務判断・複雑計算・業務フォーマット・直接I/Oを持たない。
- 依存方向は `UI -> UseCase -> Domain` を主軸とし、境界越えは `abc.ABC` / `typing.Protocol` のPort経由のみ許可する。
- Qt命名規約はシグナル過去分詞形、スロット動詞形を必須とする。

## 2. フェーズ別ロードマップ

## 2.1 Phase 0（ガバナンス基盤の固定）
- 監査スキーマを固定し、必須項目欠落をFailにする。
- アーキテクチャ静的検査を導入し、`UseCase -> Qt` 依存をFailにする。
- UI禁止行為検出ルールを導入し、Humble Object違反をFailにする。
- ハッシュ収集契約を「全件列挙」に統一し、曖昧語（主要/任意等）を排除する。

完了条件:
- 監査必須項目欠落 0件。
- 依存方向違反 0件。
- UI責務違反 0件。
- ハッシュ対象漏れ 0件。

## 2.2 Phase 1-A（Docker/EOL 再現性基盤）
- 全対象Dockerfileの `FROM` をダイジェスト形式へ更新する。
- EOL系DockerfileのAPT参照先をアーカイブリポジトリへ統一する。
- pip install手順へ `-c constraints.txt` を強制適用する。
- OpenCV等のビルド対象Dockerfileをbuilder/runtime分離のマルチステージ化する。

完了条件:
- タグ指定FROM 0件。
- EOL標準ミラー残存 0件。
- constraints未適用 0件。
- 単一ステージ違反 0件。

## 2.3 Phase 1-B（Phase 5: Validation Guardrails）
- capability推定（`user_knowledge.json`）と実証（実行実績）を統合するUseCaseを実装する。
- required imports と環境capability差分をUseCaseで算出する。
- 差分>0時は Run をHard Guardで無効化し、UIは理由表示と作成導線表示のみ行う。
- 適合環境なし時は新規環境作成フローへ強制誘導し、作成結果を再起動なしで反映する。

完了条件:
- ミスマッチ検知漏れ 0件。
- Guardバイパス経路 0件。
- UIでの業務判断実装 0件。
- Phase 5受け入れテスト（T5系）全Pass。

## 2.4 Phase 2（Phase 6: Lifecycle Management）
- Environment Manager専用UIを新設し、責務混在を回避する。
- 複数選択削除と2段階確認を実装し、部分失敗を分離表示する。
- 未使用抽出（最終利用日時・利用回数・保護フラグ）を実装する。
- cleanup対象を dangling/unused image に限定し、build cache/volume を除外する。
- rename/metadata編集（内部ID不変）と入力バリデーションを実装する。

完了条件:
- 誤削除/一括停止の安全性違反 0件。
- 保護フラグ無視 0件。
- 部分失敗時の結果混在 0件。
- Phase 6受け入れテスト（T6系）全Pass。

## 2.5 Phase 3（Phase 6.1: Decoupling Assessment）
- `artifacts/architecture_decoupling_assessment.md` を作成し、違反を `file path + class/function + violation type + evidence` 形式で列挙する。
- `artifacts/refactoring_proposal.md` を作成し、移管先レイヤ、Port設計、段階移行（P0/P1/P2）、検証方法を定義する。

完了条件:
- 違反一覧の根拠欠落 0件。
- リファクタ提案の移行手順欠落 0件。

## 3. 検証ゲート（各フェーズ共通）
- Functional Gate: `pytest tests/` 全件Pass。
- Structural Gate: 依存方向違反0、UI禁止行為0、Port未経由境界越え0、Qt命名規約違反0。
- Audit Gate: ハッシュ4区分欠落0、相対パス違反0、image digest/git hash欠落0。
- Governance Gate: Builder/Validator分離違反0、監査入力逸脱0、REJECT必須要素欠落0。

## 4. 実行順序
1. Phase 0（ガバナンス基盤固定）を先行。
2. Phase 1-A（Docker/EOL再現性）を実装し、ビルド再現性を安定化。
3. Phase 1-B（Phase 5）をUseCase中心で実装。
4. Phase 2（Phase 6）を専用UIで実装。
5. Phase 3（Phase 6.1）で違反の可視化と移行計画を確定。
6. 各ステップで Functional -> Structural -> Audit -> Governance の順にゲート通過を確認。

## 5. リスクと対策
- UIへのロジック再流入: UI静的検査とPRゲートでFail化。
- ハッシュ対象漏れ再発: 4区分未充足時に監査生成を即Fail。
- 依存逆流の潜在化: import検査をCI必須化し例外運用を禁止。
- Docker基準形骸化: digest/EOL/constraints/マルチステージを独立Failゲート化。
- 監査運用逸脱: 監査入力テンプレート固定、逸脱時は監査無効化。

## 6. Done定義
- Phase 5/6/6.1 の受け入れ基準を満たす。
- `docs/reference_standards.md` の必須規約違反が0。
- テスト、構造、監査、ガバナンスの全ゲートが連続でPass。
- 監査でREJECT要因が0。

## 7. 禁止事項
- 基準の曖昧語運用（例: 主要、可能なら、必要に応じて）を禁止する。
- 設計不備を実装で迂回することを禁止する。
- 本ロードマップ作成作業において Git コミット等のGit操作を行わない。
