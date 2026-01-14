# LCR - Legacy Code Reviver

> **"Resurrecting broken research code with absolute Data Integrity."**

LCR (Legacy Code Reviver) is a professional execution engine designed to bridge the gap between "abandoned" research assets (e.g., Python 2.7 + OpenCV 2.4) and modern computational pipelines. It transforms technical debt into reproducible research assets in just 48 hours.

---

## 🛡️ Disclosure: Project Positioning

**Note on Public Access:** The core project I am currently developing, **"Maltilabeler"** (over 13k lines of code), involves high-stakes proprietary domain logic for biological research and remains private for confidentiality reasons.  

**LCR** is an open-source (OSS) demonstration of the architectural expertise and "non-invasive" integration strategies developed during the creation of Maltilabeler. It serves as a professional proof-of-concept for enterprise-grade legacy system revival.

---

## 🚀 Key Pillars of LCR

### 1. Environmental Time Travel (Supply Chain Recovery)
* **APT Archive Mapping:** Automatically restores abandoned libraries by mapping missing dependencies to historical APT archives.
* **Intelligent Dependency Discovery:** Features a built-in "Guessing" engine that utilizes the **PyPI API** to automatically identify and verify packages for unknown imports.

### 2. Audit-Ready Reproducibility (Data Integrity)
* **Automatic Source Snapshots:** Every execution triggers an automatic snapshot of the source code (`source_snapshot.py`), ensuring that the exact logic used for a result is preserved forever.
* **Portable Execution History:** History logs utilize **strict relative path conversion**, allowing entire project folders to be moved across different workstations without breaking the audit trail.

### 3. Enterprise-Grade Governance & Scalability
* **Enterprise Overlay Mapping:** Supports `enterprise.json` for deep-merging proprietary corporate libraries into the public LCR knowledge base without modifying the core engine.
* **Private Registry Support:** Seamlessly integrates with corporate private indices (e.g., Artifactory, Nexus) via custom `pip_config` injection.

---

## 🛠️ Architecture Overview

The system follows a DI-First (Data Integrity First) architecture, ensuring that legacy code runs in a "read-only" context regarding its source, while all outputs are timestamped and isolated.

```text
src/lcr/
├── core/
│   ├── container/      # Docker orchestration & Config generation
│   ├── detector/       # Script analysis & PyPI API Guessing
│   └── history/        # Portable Audit Trail management
├── ui/                 # Qt-based Interface (MainWindow & Env Dialog)
└── utils/              # Deployment helpers (sys.frozen path handling)

```

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
