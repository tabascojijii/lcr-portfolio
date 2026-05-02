# 監査レポート

## 1. pytest 実行結果
- 実行コマンド: `pytest tests/`
- 結果: **31 passed / 0 failed**
- 抜粋ログ:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\dev\lcr
collected 31 items
...
============================= 31 passed in 1.51s ==============================
```

## 2. 基準照合結果（docs/reference_standards.md）

### 判定: **REJECT**

テストは成功しているが、`2. EOLスタックのコンテナ化およびビルド再現性標準 (Docker)` の
**「FROM句はSHA256ダイジェストで完全固定」** に違反する実ファイルを確認したため不合格。

## 3. 指摘事項（違反基準と根拠）

1. **[重大] FROM句の完全固定違反（ダイジェスト未指定）**
- 違反基準: `docs/reference_standards.md` セクション2
  - 「`Dockerfile`の `FROM` 句には可変タグではなくSHA256ダイジェストを使用」
- 根拠ファイル:
  - `src/lcr/core/container/images/Dockerfile.3.6test4:1`
  - `src/lcr/core/container/images/Dockerfile.3.6test5:1`
  - `src/lcr/core/container/images/Dockerfile.3.6test6:1`
  - `src/lcr/core/container/images/Dockerfile.3.6_test1:1`
  - `src/lcr/core/container/images/Dockerfile.3.6_test2:1`
  - `src/lcr/core/container/images/Dockerfile.3.6_test3:1`
  - `src/lcr/core/container/images/Dockerfile.3.6_test4:1`
- 実際の記述: `FROM lcr-py36-ml-classic`
- 問題点: 参照先イメージがタグ相当の可変参照であり、不変性・再現性を保証できない。

## 4. 処方的修正指示

1. 上記Dockerfile群の `FROM lcr-py36-ml-classic` を、SHA256付きの不変参照へ置換すること。
2. 生成物を `src/` に残す運用であれば、生成時点でダイジェスト固定を強制する検証（CIテストまたは生成器のバリデーション）を追加すること。
3. 再発防止として、`src/lcr/core/container/images/` 配下を対象に `^FROM\s+.+@sha256:[0-9a-f]{64}` を必須とする静的チェックを追加すること。

## 5. 最終結論
- pytest: PASS
- 基準適合: **FAIL（Docker再現性基準違反）**
- 監査結論: **REJECT_TO_IMPLEMENT**
