# LCR - Legacy Code Reviver

> **"Resurrecting broken research code with absolute Data Integrity."**

LCR (Legacy Code Reviver) is a specialized execution engine designed to safely run "abandoned" research code (e.g., Python 2.7 + OpenCV 2.4 scripts) on modern systems without modification.

---
### 🛡️ プロジェクトの公開制限と位置付けについて (Disclosure)

> **注記：プロジェクトの公開制限について**
> 
> 私が並行して開発しているコアプロジェクト **『Maltilabeler』** は、1.3万行を超える規模であり、特定の研究ドメインにおける高度な機密性を含んでいます。プロフェッショナルとしての情報管理の観点から、コードの全容は非公開としております。
> 
> 本 **『LCR』** は、その開発過程で培ったアーキテクチャ設計能力を証明するための、**「汎用的かつ非侵入的なレガシー救済ソリューション」** として、その全容を公開（OSS化）しております。
---

## Key Features

- **Supply Chain Recovery**: Restore abandoned libraries (like OpenCV 2.4) using APT-based archive mapping.
- **Automatic Path Sanitization**: Detects and rewrites hardcoded absolute paths (e.g., `C:\Users\...`) to container-compatible paths on the fly.
- **Containerized Safety**: Execute legacy scripts in isolated Docker environments to prevent host pollution.
- **DI-First Architecture**: Strict separation of Read-Only inputs and Timestamped outputs, ensuring Data Integrity for pharmaceutical research.

## Quick Start

### Option 1: Running the Executable (Recommended for Demo)
If you have downloaded the packaged release, you can run LCR without a Python environment.
1. Ensure **Docker Desktop** is running.
2. Download and extract `LCR.zip` from the [Releases](https://github.com/tabascojijii/lcr-portfolio/releases) page.
3. Double-click `LCR.exe` within the extracted folder.

### Option 2: Running from Source (For Developers)
To set up a development environment:

#### Prerequisites
- Python 3.10+
- Docker Desktop

#### Installation
```bash
# Clone the repository
git clone [https://github.com/tabascojijii/lcr-portfolio.git](https://github.com/tabascojijii/lcr-portfolio.git)
cd lcr-portfolio

# Setup environment
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### Running the Application
```bash
python run_gui.py
```
This will launch the LCR Interface. Select your legacy script and execute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
