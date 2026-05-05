# Phase 6.53 Analyzer Failure Policy

- Port 未解決時は fail-fast で解析を停止する。
- 外部照会失敗時はエラー理由を監査ログへ記録する。
- UI は失敗理由表示のみを担当し、リトライ判断は UseCase 側に限定する。
