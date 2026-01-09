# Legacy Code Reviver: System Overview

## 1. プロジェクトの目的
研究現場に埋もれている「古い環境でしか動かないコード」を、コードを一切改変せずに、現代の環境上で Docker コンテナを通じて安全・簡便に実行する。

## 2. コア・アーキテクチャ
本プロジェクトは、LCR の「外部プロセス制御ロジック」を継承し、以下の3層構造で構築される。

- **Analysis Layer**: AST解析およびAI（LLM）を用いて、コードの推定年代と入出力仕様を特定。
- **Orchestration Layer**: Docker SDK/CLI を用い、特定された年代に最適なコンテナイメージを動的に配備・実行。
- **Interface Layer**: 実行ログのリアルタイム表示と、ホスト・コンテナ間のファイル同期管理。

## 3. 処理フロー


```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Detector as 年代判定エンジン(AST/AI)
    participant Manager as Container Manager
    participant Docker as Docker Container

    User->>Detector: コードを投入
    Detector->>Detector: 構文解析・シグネチャ照合
    Detector-->>User: 推定環境（例: Python 2.7 + OpenCV 2.4）を提案
    User->>Manager: 実行指示
    Manager->>Docker: ボリュームマウント & 実行
    Docker-->>Manager: 標準出力 (stdout)
    Manager-->>User: ログをリアルタイム表示